# eye_func/aoi_manager.py
# AOI (Area of Interest) Manager for the Chicken Task eye-tracking experiment
#
# 역할
# ----
#   1. 카드 배치 상수로부터 보드(24개) + 덱(최대 27개) AOI 사각형을 계산
#   2. EyeLink DataViewer 용 INTEREST_AREA 메시지를 시행 시작마다 전송
#   3. 매 프레임 EyeLink 최신 시선 샘플을 받아 어느 카드를 보고 있는지 판단
#   4. AOI 진입/이탈 시 EyeLink 메시지 + LabJack T4 디지털 트리거 전송
#
# 좌표계
# ------
#   PsychoPy  : 화면 중앙 원점, y-위 방향 (렌더러가 사용)
#   Screen px : 좌상단 원점, y-아래 방향 (EyeLink & 이 모듈이 사용)
#
#   변환:  pixel_x = psychopy_x + WIDTH/2
#          pixel_y = HEIGHT/2  - psychopy_y

try:
    import pylink
    _PYLINK_AVAILABLE = True
except ImportError:
    _PYLINK_AVAILABLE = False

try:
    import ljm as _ljm
    _LJM_AVAILABLE = True
except ImportError:
    _LJM_AVAILABLE = False

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
        AOI_TRIGGER_PULSE_S,
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
        AOI_TRIGGER_PULSE_S,
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
    """
    PsychoPy 중심 좌표계 → 화면 픽셀 좌표계 변환.

    Parameters
    ----------
    psychopy_x, psychopy_y : float
        PsychoPy 좌표 (화면 중앙 = 0,0)

    Returns
    -------
    (pixel_x, pixel_y) : tuple[int, int]
        화면 좌상단 기준 픽셀 좌표
    """
    return int(psychopy_x + WIDTH / 2), int(HEIGHT / 2 - psychopy_y)


# ============================================================================
# AOIManager
# ============================================================================

class AOIManager:
    """
    Chicken Task AOI 관리자.

    Parameters
    ----------
    board : ConditionBoard
        현재 게임 보드 (track_positions 순회용)
    deck : MainDeck
        현재 게임 덱 (rows, cols 속성 사용)
    el_tracker : pylink.EyeLink | None
        EyeLink 트래커 객체. None 이면 시선 추적 비활성화.
    labjack_handle : int | None
        ljm.openS() 로 얻은 LabJack T4 핸들. None 이면 트리거 비활성화.
    """

    def __init__(self, board, deck, el_tracker=None, labjack_handle=None):
        self.board          = board
        self.deck           = deck
        self.el_tracker     = el_tracker
        self.labjack_handle = labjack_handle

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

        # LabJack TTL 펄스 자동 리셋 타이머
        self._trigger_reset_at: float | None = None

        print(f"[AOI] {len(self.aois)}개 AOI 초기화 완료 "
              f"(EyeLink={'ON' if el_tracker else 'OFF'}, "
              f"LabJack={'ON' if labjack_handle else 'OFF'})")

    # ------------------------------------------------------------------ #
    #  AOI 테이블 구성
    # ------------------------------------------------------------------ #

    def _build_aois(self):
        """보드 & 덱의 모든 카드 위치로 AOI 테이블을 구성합니다."""
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
        """
        난이도 변경으로 deck 크기(deck_cols)가 바뀔 때 호출.
        덱 AOI 테이블을 새 deck 기준으로 재빌드한다.

        [왜 필요한가]
        AOIManager는 초기화 시 _build_aois()를 한 번만 호출하여
        self.deck.rows / self.deck.cols 기준으로 AOI 항목을 생성한다.
        난이도 업 시 advance_round()가 새 MainDeck 객체(deck_cols 변경)를
        생성하지만, AOIManager.aois 테이블은 그대로이므로:
          - 새로 생긴 열(col)의 카드에 해당하는 AOI가 존재하지 않음
          - 해당 카드에 시선이 닿아도 hit_test에서 None 반환
          - gaze_events.csv 누락, EyeLink INTEREST_AREA 미등록,
            LabJack 트리거 미발송

        [언제 호출해야 하는가]
        advance_round() 직후, 다음 시행의 register_with_eyelink() 전에 호출.
        deck_cols가 바뀌지 않은 라운드에서도 호출해도 무방하다.

        Parameters
        ----------
        new_deck : MainDeck
            advance_round() 이후의 game_state.deck.
        """
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
        """
        EyeLink DataViewer 용 INTEREST_AREA 메시지를 EDF에 기록합니다.
        각 시행(trial) 시작 직후, startRecording() 이후에 한 번 호출하세요.

        EyeLink DataViewer IAREA 포맷:
            !V IAREA RECTANGLE {index} {x1} {y1} {x2} {y2} {label}
            (x1,y1 = 좌상단, x2,y2 = 우하단, 픽셀)
        """
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
        """
        매 프레임 호출.
        EyeLink에서 최신 시선 샘플을 읽어 AOI를 판단하고,
        진입·이탈 이벤트(EyeLink 메시지 + LabJack 트리거)를 처리합니다.

        Parameters
        ----------
        current_time : float
            현재 시각 (psychopy.core.getTime() 반환값)

        Returns
        -------
        (aoi_id, aoi_info) : tuple[str | None, dict | None]
            현재 시선이 위치한 AOI 정보. 어느 AOI에도 없으면 (None, None).
        """
        # LabJack TTL 펄스 자동 리셋
        if (self._trigger_reset_at is not None
                and current_time >= self._trigger_reset_at):
            self._reset_labjack()
            self._trigger_reset_at = None

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
        """AOI 진입 처리: 타임스탬프 기록, EyeLink 메시지, LabJack 트리거, CSV 저장."""
        self._entry_time[aoi_id] = t

        if self.el_tracker:
            self.el_tracker.sendMessage(f"GAZE_ENTER {aoi_id} {t:.4f}")

        aoi = self.aois[aoi_id]
        self._send_labjack_trigger(aoi['trigger_code'], t)

        if _GAZE_SAVER_AVAILABLE and self.gaze_file:
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

    # ------------------------------------------------------------------ #
    #  Internal: LabJack T4 TTL 트리거
    # ------------------------------------------------------------------ #

    def _send_labjack_trigger(self, code: int, current_time: float):
        """
        LabJack T4의 EIO 포트(EIO0–EIO7)로 디지털 TTL 트리거를 전송합니다.
        AOI_TRIGGER_PULSE_S 후에 자동으로 EIO_STATE = 0 으로 리셋됩니다.

        EIO_STATE 는 8비트 값으로, EIO0(LSB) ~ EIO7(MSB) 를 제어합니다.
        trigger_code 값이 EIO 핀에 직접 출력됩니다.
        """
        if not self.labjack_handle or not _LJM_AVAILABLE:
            return
        try:
            _ljm.eWriteName(self.labjack_handle, "EIO_STATE", int(code))
            self._trigger_reset_at = current_time + AOI_TRIGGER_PULSE_S
        except Exception as e:
            print(f"[LabJack] EIO 트리거 전송 오류 (code={code}): {e}")

    def _reset_labjack(self):
        """EIO_STATE 를 0으로 리셋합니다 (TTL 펄스 종료)."""
        if not self.labjack_handle or not _LJM_AVAILABLE:
            return
        try:
            _ljm.eWriteName(self.labjack_handle, "EIO_STATE", 0)
        except Exception as e:
            print(f"[LabJack] EIO 리셋 오류: {e}")
