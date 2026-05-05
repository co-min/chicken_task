try:
    import pylink
    _PYLINK_AVAILABLE = True
except ImportError:
    _PYLINK_AVAILABLE = False

try:
    from ..save_func.gaze_event_saver import save_gaze_event
    _GAZE_SAVER_AVAILABLE = True
except ImportError:
    try:
        from save_func.gaze_event_saver import save_gaze_event
        _GAZE_SAVER_AVAILABLE = True
    except ImportError:
        _GAZE_SAVER_AVAILABLE = False

try:
    from ..config import (
        WIDTH, HEIGHT,
        BOARD_LEFT_EDGE, BOARD_DECK_TOP_MARGIN,
        BOARD_CARD_WIDTH, BOARD_CARD_HEIGHT, BOARD_CARD_SPACING,
        DECK_LEFT_EDGE,
        DECK_CARD_WIDTH, DECK_CARD_HEIGHT, DECK_CARD_SPACING,
        AOI_DWELL_THRESHOLD,
        AOI_TRIGGER_BOARD_OFFSET,
        AOI_TRIGGER_DECK_OFFSET,
    )
except ImportError:
    from config import (
        WIDTH, HEIGHT,
        BOARD_LEFT_EDGE, BOARD_DECK_TOP_MARGIN,
        BOARD_CARD_WIDTH, BOARD_CARD_HEIGHT, BOARD_CARD_SPACING,
        DECK_LEFT_EDGE,
        DECK_CARD_WIDTH, DECK_CARD_HEIGHT, DECK_CARD_SPACING,
        AOI_DWELL_THRESHOLD,
        AOI_TRIGGER_BOARD_OFFSET,
        AOI_TRIGGER_DECK_OFFSET,
    )


# ============================================================================
# AOI 사각형 헬퍼
# ============================================================================

def _board_aoi_rect(row: int, col: int) -> tuple:
    """보드 카드 (row, col)의 AOI 사각형 (left, top, right, bottom) 반환 (픽셀)."""
    left   = BOARD_LEFT_EDGE + col * (BOARD_CARD_WIDTH  + BOARD_CARD_SPACING)
    top    = BOARD_DECK_TOP_MARGIN + row * (BOARD_CARD_HEIGHT + BOARD_CARD_SPACING)
    right  = left + BOARD_CARD_WIDTH
    bottom = top  + BOARD_CARD_HEIGHT
    return left, top, right, bottom


def _deck_aoi_rect(row: int, col: int) -> tuple:
    """덱 카드 (row, col)의 AOI 사각형 (left, top, right, bottom) 반환 (픽셀)."""
    left   = DECK_LEFT_EDGE + col * (DECK_CARD_WIDTH  + DECK_CARD_SPACING)
    top    = BOARD_DECK_TOP_MARGIN + row * (DECK_CARD_HEIGHT + DECK_CARD_SPACING)
    right  = left + DECK_CARD_WIDTH
    bottom = top  + DECK_CARD_HEIGHT
    return left, top, right, bottom


def _point_in_rect(px: int, py: int, rect: tuple) -> bool:
    """픽셀 점 (px, py)이 rect (l, t, r, b) 안에 있으면 True."""
    l, t, r, b = rect
    return l <= px <= r and t <= py <= b


def psychopy_to_pixel(psychopy_x: float, psychopy_y: float) -> tuple:
    return int(psychopy_x + WIDTH / 2), int(HEIGHT / 2 - psychopy_y)


# ============================================================================
# AOIManager
# ============================================================================

class AOIManager:
    def __init__(self, board, deck, el_tracker=None):
        self.board      = board
        self.deck       = deck
        self.el_tracker = el_tracker

        # 데이터 저장 (main.py에서 주입)
        self.gaze_file:        str | None = None   # gaze_events.csv 경로
        self.subject_id:       str        = ''
        self.current_trial_id: int        = 0      # game_play.py에서 갱신

        # Sequential Memory 상태 (game_play.py에서 trial_id 갱신 시 함께 갱신)
        self.is_seq_memory:    bool      = False   # 현재 trial이 seq_memory 모드인지
        self.seq_memory_step:  int | None = None   # 현재 스텝 인덱스 (일반 trial은 None)

        # AOI 테이블: aoi_id → {'type', 'pos', 'rect', 'trigger_code'}
        self.aois: dict = {}
        self._build_aois()

        # 시선 상태
        self._current_aoi: str | None = None
        self._entry_time:  dict       = {}   # {aoi_id: entry_timestamp}

        print(f"[AOI] {len(self.aois)}개 AOI 초기화 완료 "
              f"(EyeLink={'ON' if el_tracker else 'OFF'})")

    # ------------------------------------------------------------------ #
    #  AOI 테이블 구성
    # ------------------------------------------------------------------ #

    def _build_aois(self):
        # 보드 카드 (운동장 트랙 24개)
        for idx, (row, col) in enumerate(self.board.track_positions):
            aoi_id = f"board_{row}_{col}"
            self.aois[aoi_id] = {
                'type':         'board',
                'pos':          (row, col),
                'rect':         _board_aoi_rect(row, col),
                'trigger_code': AOI_TRIGGER_BOARD_OFFSET + idx,  # 예: 10–33
            }

        # 덱 카드 (메인 덱)
        for row in range(self.deck.rows):
            for col in range(self.deck.cols):
                idx    = row * self.deck.cols + col
                aoi_id = f"deck_{row}_{col}"
                self.aois[aoi_id] = {
                    'type':         'deck',
                    'pos':          (row, col),
                    'rect':         _deck_aoi_rect(row, col),
                    'trigger_code': AOI_TRIGGER_DECK_OFFSET + idx,  # 예: 40–57
                }

    def update_deck(self, new_deck):
        prev_cols = self.deck.cols
        self.deck = new_deck

        # 기존 덱 AOI만 제거 (보드 AOI는 변경되지 않으므로 유지)
        self.aois = {k: v for k, v in self.aois.items() if v['type'] != 'deck'}

        # 새 deck 크기 기준으로 덱 AOI 재빌드
        for row in range(self.deck.rows):
            for col in range(self.deck.cols):
                idx    = row * self.deck.cols + col
                aoi_id = f"deck_{row}_{col}"
                self.aois[aoi_id] = {
                    'type':         'deck',
                    'pos':          (row, col),
                    'rect':         _deck_aoi_rect(row, col),
                    'trigger_code': AOI_TRIGGER_DECK_OFFSET + idx,
                }

        # 현재 시선이 제거된 덱 AOI 안에 있을 수 있으므로 상태 초기화
        if self._current_aoi and self._current_aoi.startswith('deck_'):
            self._current_aoi = None
        self._entry_time = {
            k: v for k, v in self._entry_time.items()
            if not k.startswith('deck_')
        }

        print(f"[AOI] 덱 AOI 재빌드 완료: {prev_cols}열 → {self.deck.cols}열 "
              f"(덱 AOI {self.deck.rows * self.deck.cols}개, "
              f"전체 AOI {len(self.aois)}개)")

    # ------------------------------------------------------------------ #
    #  EyeLink DataViewer 등록
    # ------------------------------------------------------------------ #

    def register_with_eyelink(self):
        if not self.el_tracker:
            return

        for i, (aoi_id, aoi) in enumerate(self.aois.items(), start=1):
            l, t, r, b = aoi['rect']
            self.el_tracker.sendMessage(
                f"!V IAREA RECTANGLE {i} {l} {t} {r} {b} {aoi_id}"
            )

        print(f"[AOI] EyeLink에 {len(self.aois)}개 INTEREST_AREA 등록 완료")

    # ------------------------------------------------------------------ #
    #  매 프레임 업데이트 (핵심 메서드)
    # ------------------------------------------------------------------ #

    def update(self, current_time: float):
        # 시선 좌표 획득
        gaze_px = self._get_gaze_pixel()
        if gaze_px is None:
            # 시선 데이터 없음 (깜빡임, 이탈 등) → 현재 AOI 이탈 처리
            if self._current_aoi:
                self._on_exit(self._current_aoi, current_time)
                self._current_aoi = None
            return None, None

        # Hit test
        hit = self._hit_test(*gaze_px)

        # AOI 전환 감지
        if hit != self._current_aoi:
            if self._current_aoi:
                self._on_exit(self._current_aoi, current_time)
            if hit:
                self._on_enter(hit, current_time)
            self._current_aoi = hit

        return hit, (self.aois[hit] if hit else None)

    # ------------------------------------------------------------------ #
    #  시행 종료 클린업
    # ------------------------------------------------------------------ #

    def end_trial(self, current_time: float):
        """
        시행 종료 시 호출.
        현재 AOI 이탈 처리 및 내부 상태 초기화.
        """
        if self._current_aoi:
            self._on_exit(self._current_aoi, current_time)
            self._current_aoi = None
        self._entry_time.clear()

    # ------------------------------------------------------------------ #
    #  상태 조회
    # ------------------------------------------------------------------ #

    @property
    def current_aoi_id(self) -> str | None:
        """현재 시선이 머무는 AOI id (없으면 None)."""
        return self._current_aoi

    def get_dwell_time(self, aoi_id: str, current_time: float) -> float:
        """지정한 AOI에 시선이 머문 누적 시간(초) 반환."""
        entry = self._entry_time.get(aoi_id)
        return (current_time - entry) if entry is not None else 0.0

    def is_fixating(self, aoi_id: str, current_time: float) -> bool:
        """지정한 AOI에 AOI_DWELL_THRESHOLD 이상 시선이 머물고 있으면 True."""
        return self.get_dwell_time(aoi_id, current_time) >= AOI_DWELL_THRESHOLD

    def get_all_rects(self) -> dict:
        """
        {aoi_id: (left, top, right, bottom)} 전체 AOI 사각형 반환.
        디버그 시각화에 사용할 수 있습니다.
        """
        return {k: v['rect'] for k, v in self.aois.items()}

    # ------------------------------------------------------------------ #
    #  Internal: EyeLink 시선 획득
    # ------------------------------------------------------------------ #

    def _get_gaze_pixel(self) -> tuple | None:
        """
        EyeLink에서 최신 시선 위치를 픽셀 좌표로 반환합니다.
        EyeLink 좌표계는 이미 화면 픽셀 기준(좌상단 원점)입니다.

        Returns
        -------
        (px, py) : tuple[int, int] | None
        """
        if not self.el_tracker or not _PYLINK_AVAILABLE:
            return None

        sample = self.el_tracker.getNewestSample()
        if sample is None:
            return None

        gaze = None
        # 오른쪽 눈 우선
        if sample.isRightSample():
            eye = sample.getRightEye()
            if eye:
                gaze = eye.getGaze()
        # 오른쪽 눈 없으면 왼쪽 눈
        if gaze is None and sample.isLeftSample():
            eye = sample.getLeftEye()
            if eye:
                gaze = eye.getGaze()

        if gaze is None:
            return None

        gx, gy = gaze
        # MISSING_DATA 값 필터링 (EyeLink MISSING_DATA = 1e8)
        if gx > 1e7 or gy > 1e7:
            return None

        return int(gx), int(gy)

    # ------------------------------------------------------------------ #
    #  Internal: Hit test
    # ------------------------------------------------------------------ #

    def _hit_test(self, px: int, py: int) -> str | None:
        """픽셀 좌표 (px, py)가 속하는 AOI id를 반환합니다."""
        for aoi_id, aoi in self.aois.items():
            if _point_in_rect(px, py, aoi['rect']):
                return aoi_id
        return None

    # ------------------------------------------------------------------ #
    #  Internal: 진입 / 이탈 이벤트
    # ------------------------------------------------------------------ #

    def _on_enter(self, aoi_id: str, t: float):
        """AOI 진입 처리: 타임스탬프 기록, EyeLink 메시지, CSV 저장."""
        self._entry_time[aoi_id] = t

        if self.el_tracker:
            self.el_tracker.sendMessage(f"GAZE_ENTER {aoi_id} {t:.4f}")

        if _GAZE_SAVER_AVAILABLE and self.gaze_file:
            aoi = self.aois[aoi_id]
            save_gaze_event(
                self.gaze_file, self.subject_id,
                self.current_trial_id, 'enter',
                aoi_id, aoi, t,
                is_seq_memory=self.is_seq_memory,
                seq_memory_step=self.seq_memory_step,
            )

    def _on_exit(self, aoi_id: str, t: float):
        """AOI 이탈 처리: 체류 시간 계산, EyeLink 메시지, CSV 저장."""
        dwell = self.get_dwell_time(aoi_id, t)

        if self.el_tracker:
            self.el_tracker.sendMessage(
                f"GAZE_EXIT {aoi_id} DWELL {dwell:.4f}"
            )

        if _GAZE_SAVER_AVAILABLE and self.gaze_file:
            aoi = self.aois.get(aoi_id, {})
            save_gaze_event(
                self.gaze_file, self.subject_id,
                self.current_trial_id, 'exit',
                aoi_id, aoi, t, dwell_time=dwell,
                is_seq_memory=self.is_seq_memory,
                seq_memory_step=self.seq_memory_step,
            )

        self._entry_time.pop(aoi_id, None)

