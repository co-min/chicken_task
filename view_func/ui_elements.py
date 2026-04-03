# view_func/ui_elements.py
# UI 요소 렌더링 (타이머, 점수, 텍스트, 버튼 등)

from psychopy import visual
import sys, os
import random
import requests
sys.path.insert(0, os.path.abspath(os.path.join(__file__, '..', '..')))
from config import (
    WIDTH, HEIGHT,
    TEXT_COLOR, TEXT_SIZE,
    BUTTON_COLOR_NORMAL, BUTTON_COLOR_HOVER, BUTTON_COLOR_SELECTED,
    TOKEN_BUTTON_WIDTH, TOKEN_BUTTON_HEIGHT, TOKEN_BUTTON_TEXT_HEIGHT,
    MESSAGE_Y_OFFSET,
    CHASE_BUTTON_POS, FLIGHT_BUTTON_POS, TOKEN_BUTTON_LINE_WIDTH, PURPLE, WHITE,
    TOTAL_ROUNDS,
    PROGRESS_BAR_WIDTH, PROGRESS_BAR_HEIGHT, PROGRESS_BAR_Y_FROM_TOP,
    PROGRESS_BAR_COLOR_FULL, PROGRESS_BAR_COLOR_WARN, PROGRESS_BAR_COLOR_CRIT,
    PROGRESS_BAR_BG_COLOR,
)

_FALLBACK_NAMES = ["토끼", "여우", "다람쥐", "오리", "강아지"]


def fetch_random_nicknames(count=5):
    """
    rivestsoft 무료 API로 랜덤 한국어 닉네임 count개를 생성한다.
    API 호출 실패 시 _FALLBACK_NAMES 로 대체한다.
    """
    names = []
    for i in range(count):
        try:
            res = requests.post(
                'https://www.rivestsoft.com/nickname/getRandomNickname.ajax',
                data={'lang': 'ko'},
                timeout=3,
            )
            res.raise_for_status()
            name = res.json().get('data', _FALLBACK_NAMES[i % len(_FALLBACK_NAMES)])
            names.append(name)
            print(f"  [닉네임 API] {i + 1}번째: {name}")
        except Exception as e:
            fallback = _FALLBACK_NAMES[i % len(_FALLBACK_NAMES)]
            names.append(fallback)
            print(f"  [닉네임 API] {i + 1}번째 실패({e}) → fallback: {fallback}")
    return names


# 설계 기준(TEXT_SIZE=28) 대비 스케일 → 모든 텍스트 크기에 적용
_S = TEXT_SIZE / 28
_TIMER_H       = max(12, round(22 * _S))   # 기존 45 → 22 (HUD 재배치로 축소)
_ROUND_H       = max(10, round(22 * _S))   # 라운드 표시
_SCORE_H       = max(10, round(20 * _S))   # 점수 텍스트
_BAR_H         = max(6,  round(PROGRESS_BAR_HEIGHT * _S))
# 바 양쪽에 레이블("턴") + 숫자("15s") 공간 확보 — 실제 바는 이 너비 사용
_BAR_INNER_W   = max(200, round((PROGRESS_BAR_WIDTH - 140) * _S))
_BAR_SIDE_PAD  = max(20, round(55 * _S))   # 바 끝 ~ 레이블 중심 거리
_MSG_H         = max(10, round(15 * _S))
_START_CUE_H   = max(20, round(90 * _S))
_INSTR_H       = max(10, round(25 * _S))
_TURN_H        = max(10, round(20 * _S))
_PHASE_H       = max(12, round(36 * _S))
_CUE_BG_W      = max(200, round(320 * _S))
_CUE_BG_H      = max(80,  round(160 * _S))

# 우측 하단 랭킹 패널
_RANK_PANEL_W   = max(160, round(190 * _S))
_RANK_PANEL_H   = max(150, round(180 * _S))
_RANK_TITLE_H   = max(9,   round(12  * _S))
_RANK_ENTRY_H   = max(7,   round(10  * _S))
_RANK_ENTRY_GAP = max(3,   round(5   * _S))

# 라운드 휴식 오버레이
_BREAK_BG_W    = max(300, round(500 * _S))
_BREAK_BG_H    = max(100, round(170 * _S))
_BREAK_TITLE_H = max(16,  round(30  * _S))   # "라운드 N 완료!"
_BREAK_SUB_H   = max(11,  round(20  * _S))   # "N초 후 라운드 N+1 시작"
_BREAK_LINE_GAP = max(10, round(18  * _S))   # 제목↔부제 간격

# HUD 행별 Y 위치 (화면 상단 기준)
_HUD_ROW1_Y    = HEIGHT / 2 - round(22 * _S)   # 라운드 표시 + 턴 타이머
_HUD_BAR_Y     = HEIGHT / 2 - round(PROGRESS_BAR_Y_FROM_TOP * _S)  # 프로그레스 바
_HUD_SCORE_Y   = HEIGHT / 2 - round(88 * _S)   # 점수 표시


class UIElements:
    """게임 UI 요소를 관리하는 클래스"""
    
    def __init__(self, win, fake_player_names=None):
        """
        Args:
            win: PsychoPy window 객체
            fake_player_names: 가짜 플레이어 닉네임 리스트 (5개). None이면 fallback 사용.
        """
        self.win = win

        # UI 요소들
        self.timer_text = None
        
        self.score_text = None
        self.round_text = None
        self.progress_bar_bg = None
        self.progress_bar_fg = None
        self.message_text = None
        self.instruction_text = None
        self.start_cue_background = None
        self.start_cue_text = None
        self.round_break_bg = None
        self.round_break_title = None
        self.round_break_sub = None
        self.token_choice_buttons = {}

        # 랭킹 패널 요소
        self.ranking_bg = None
        self.ranking_title = None
        self.ranking_divider = None
        self.ranking_entries = []

        # 가짜 플레이어: [(이름, 점수), ...] — 게임 시작 전 고정
        names = (fake_player_names or _FALLBACK_NAMES)[:]
        raw_scores = sorted(random.sample(range(400, 1800), min(5, len(names))), reverse=True)
        self._fake_players = list(zip(names[:5], raw_scores))
        self._cumulative_user_score = 0

        # 프로그레스 바 내부 상태 (줄어든 _BAR_INNER_W 기준)
        self._bar_max_width = _BAR_INNER_W
        self._bar_left_edge = -_BAR_INNER_W / 2
        self._cached_bar_ratio = 1.0

        self._create_ui_elements()
        self._user_message_height = self.message_text.height
        self._user_instruction_height = self.instruction_text.height
        self._pc_text_scale = 0.8
    
    def _create_ui_elements(self):
        """모든 UI 요소 생성"""
        message_base_y = -360 + MESSAGE_Y_OFFSET

        # ── HUD 행 1: 라운드 표시 (왼쪽) + 턴 타이머 (오른쪽) ──
        # Row1 좌측: 라운드 표시
        self.round_text = visual.TextStim(
            win=self.win,
            text="라운드 1/5",
            pos=(-WIDTH / 2 + round(90 * _S), _HUD_ROW1_Y),
            height=_ROUND_H,
            color=TEXT_COLOR,
            colorSpace='rgb255',
            bold=True,
            anchorHoriz='left',
        )
        # ── HUD 행 2: 프로그레스 바 + 턴 타이머 숫자 ──
        
        # 중앙: 프로그레스 바 (_BAR_INNER_W 사용)
        self.progress_bar_bg = visual.Rect(
            win=self.win,
            width=_BAR_INNER_W,
            height=_BAR_H,
            pos=(0, _HUD_BAR_Y),
            fillColor=PROGRESS_BAR_BG_COLOR,
            lineColor=PROGRESS_BAR_BG_COLOR,
            colorSpace='rgb255',
        )
        self.progress_bar_fg = visual.Rect(
            win=self.win,
            width=_BAR_INNER_W,
            height=_BAR_H,
            pos=(0, _HUD_BAR_Y),
            fillColor=PROGRESS_BAR_COLOR_FULL,
            lineColor=PROGRESS_BAR_COLOR_FULL,
            colorSpace='rgb255',
        )
        # 우측: 턴 남은 시간 숫자 (프로그레스 바 바로 오른쪽)
        self.timer_text = visual.TextStim(
            win=self.win,
            text="15s",
            pos=(_BAR_INNER_W / 2 + _BAR_SIDE_PAD, _HUD_BAR_Y),
            height=_TIMER_H,
            color=TEXT_COLOR,
            colorSpace='rgb255',
            bold=True,
            anchorHoriz='left',
        )

        # ── HUD 행 3: 점수 (중앙) ──
        self.score_text = visual.TextStim(
            win=self.win,
            text="내 점수: 0 | 문어: 0",
            pos=(0, _HUD_SCORE_Y),
            height=_SCORE_H,
            color=TEXT_COLOR,
            colorSpace='rgb255',
        )

        # 메시지 (화면 중앙)
        self.message_text = visual.TextStim(
            win=self.win,
            text="",
            pos=(0, message_base_y),
            height=_MSG_H,
            color=[255, 255, 0],  # 노란색 (강조)
            colorSpace='rgb255',
            bold=True
        )

        self.start_cue_background = visual.Rect(
            win=self.win,
            width=_CUE_BG_W,
            height=_CUE_BG_H,
            pos=(0, 0),
            fillColor=WHITE,
            lineColor=WHITE,
            colorSpace='rgb255'
        )

        self.start_cue_text = visual.TextStim(
            win=self.win,
            text="",
            pos=(0, 0),
            height=_START_CUE_H,
            color=PURPLE,
            colorSpace='rgb255',
            bold=True
        )

        # 라운드 휴식 오버레이
        _title_y = _BREAK_LINE_GAP // 2 + _BREAK_TITLE_H // 2
        _sub_y   = -(_BREAK_LINE_GAP // 2 + _BREAK_SUB_H // 2)
        self.round_break_bg = visual.Rect(
            win=self.win,
            width=_BREAK_BG_W,
            height=_BREAK_BG_H,
            pos=(0, 0),
            fillColor=[30, 30, 30],
            lineColor=[200, 200, 200],
            lineWidth=2,
            colorSpace='rgb255',
        )
        self.round_break_title = visual.TextStim(
            win=self.win,
            text="",
            pos=(0, _title_y),
            height=_BREAK_TITLE_H,
            color=[255, 220, 60],
            colorSpace='rgb255',
            bold=True,
        )
        self.round_break_sub = visual.TextStim(
            win=self.win,
            text="",
            pos=(0, _sub_y),
            height=_BREAK_SUB_H,
            color=[200, 200, 200],
            colorSpace='rgb255',
        )

        # 안내 문구 (하단)
        instruction_gap = round(14 * _S)
        instruction_y = message_base_y - (self.message_text.height / 2) - instruction_gap - (_INSTR_H / 2) - round(60 * _S)
        self.instruction_text = visual.TextStim(
            win=self.win,
            text="",
            pos=(0, instruction_y),
            height=_INSTR_H,
            color=TEXT_COLOR,
            colorSpace='rgb255'
        )
        
        # 토큰 선택 버튼들 (Chase / Flight)
        # Chase 버튼 (왼쪽)
        self.token_choice_buttons['chase'] = {
            'rect': visual.Rect(
                win=self.win,
                width=TOKEN_BUTTON_WIDTH,
                height=TOKEN_BUTTON_HEIGHT,
                pos=CHASE_BUTTON_POS,
                fillColor=BUTTON_COLOR_NORMAL,
                lineColor=[255, 255, 255],
                lineWidth=TOKEN_BUTTON_LINE_WIDTH,
                colorSpace='rgb255'
            ),
            'text': visual.TextStim(
                win=self.win,
                text="CHASE\n(문어를 쫓는 닭)",
                pos=CHASE_BUTTON_POS,
                height=TOKEN_BUTTON_TEXT_HEIGHT,
                color=[255, 255, 255],
                colorSpace='rgb255'
            )
        }
        
        # Flight 버튼 (오른쪽)
        self.token_choice_buttons['flight'] = {
            'rect': visual.Rect(
                win=self.win,
                width=TOKEN_BUTTON_WIDTH,
                height=TOKEN_BUTTON_HEIGHT,
                pos=FLIGHT_BUTTON_POS,
                fillColor=BUTTON_COLOR_NORMAL,
                lineColor=[255, 255, 255],
                lineWidth=TOKEN_BUTTON_LINE_WIDTH,
                colorSpace='rgb255'
            ),
            'text': visual.TextStim(
                win=self.win,
                text="FLIGHT\n(도망치는 닭)",
                pos=FLIGHT_BUTTON_POS,
                height=TOKEN_BUTTON_TEXT_HEIGHT,
                color=[255, 255, 255],
                colorSpace='rgb255'
            )
        }

        # ── 우측 하단: 가짜 랭킹 패널 ──
        _rank_cx = WIDTH / 2 - _RANK_PANEL_W / 2 - round(15 * _S)
        _rank_cy = -HEIGHT / 2 + _RANK_PANEL_H / 2 + round(15 * _S)

        self.ranking_bg = visual.Rect(
            win=self.win,
            width=_RANK_PANEL_W,
            height=_RANK_PANEL_H,
            pos=(_rank_cx, _rank_cy),
            fillColor=[20, 20, 40],
            lineColor=[80, 130, 220],
            lineWidth=max(1, round(2 * _S)),
            colorSpace='rgb255',
        )
        _rank_title_y = _rank_cy + _RANK_PANEL_H / 2 - round(7 * _S) - _RANK_TITLE_H / 2
        self.ranking_title = visual.TextStim(
            win=self.win,
            text="순위표 (누적 점수)",
            pos=(_rank_cx, _rank_title_y),
            height=_RANK_TITLE_H,
            color=[100, 190, 255],
            colorSpace='rgb255',
            bold=True,
        )
        _rank_div_y = _rank_title_y - _RANK_TITLE_H / 2 - round(5 * _S)
        self.ranking_divider = visual.Rect(
            win=self.win,
            width=_RANK_PANEL_W - round(16 * _S),
            height=max(1, round(1 * _S)),
            pos=(_rank_cx, _rank_div_y),
            fillColor=[80, 130, 220],
            lineColor=[80, 130, 220],
            colorSpace='rgb255',
        )
        _entry_left_x = _rank_cx - _RANK_PANEL_W / 2 + round(8 * _S)
        _first_entry_y = _rank_div_y - round(5 * _S) - _RANK_ENTRY_H / 2
        for i in range(6):
            entry_y = _first_entry_y - i * (_RANK_ENTRY_H + _RANK_ENTRY_GAP)
            entry = visual.TextStim(
                win=self.win,
                text="",
                pos=(_entry_left_x, entry_y),
                height=_RANK_ENTRY_H,
                color=[210, 210, 210],
                colorSpace='rgb255',
                anchorHoriz='left',
            )
            self.ranking_entries.append(entry)
    
    def draw_timer(self, time_str):
        """
        타이머 표시
        
        Args:
            time_str: 시간 문자열 (예: "00:15")
        """
        self.timer_text.text = time_str
        self.timer_text.draw()
    
    def draw_score(self, round_score, pc_score):
        """라운드 점수 텍스트 업데이트 + 그리기."""
        self.score_text.text = f"이번 라운드: {round_score}점  |  문어: {pc_score}점"
        self.score_text.draw()

    def set_round_display(self, current_round, total_rounds=None):
        """라운드 텍스트 업데이트 (그리기는 draw_persistent_hud에서)."""
        self.round_text.text = f"라운드 {current_round}"

    def draw_progress_bar(self, ratio=None):
        """
        프로그레스 바 그리기.

        Args:
            ratio: 0.0~1.0 남은 시간 비율. None이면 캐시된 값 사용.
        """
        if ratio is not None:
            self._cached_bar_ratio = max(0.0, min(1.0, ratio))
        r = self._cached_bar_ratio

        # 색상 결정
        if r > 0.5:
            color = PROGRESS_BAR_COLOR_FULL
        elif r > 0.25:
            color = PROGRESS_BAR_COLOR_WARN
        else:
            color = PROGRESS_BAR_COLOR_CRIT

        # 전경 바 너비·위치 계산 (왼쪽 끝에서 오른쪽으로 줄어듦)
        bar_w = max(2, round(self._bar_max_width * r))
        bar_x = self._bar_left_edge + bar_w / 2

        self.progress_bar_bg.draw()
        self.progress_bar_fg.width = bar_w
        self.progress_bar_fg.pos = (bar_x, self.progress_bar_fg.pos[1])
        self.progress_bar_fg.fillColor = color
        self.progress_bar_fg.lineColor = color
        self.progress_bar_fg.draw()

    def update_ranking(self, cumulative_score):
        """누적 점수를 받아 랭킹 패널 텍스트를 갱신한다. 매 프레임 draw_ranking() 전에 호출."""
        self._cumulative_user_score = cumulative_score
        all_players = self._fake_players + [("나", cumulative_score)]
        all_players.sort(key=lambda x: x[1], reverse=True)
        rank_labels = ["1위", "2위", "3위", "4위", "5위", "6위"]
        for i, entry in enumerate(self.ranking_entries):
            if i < len(all_players):
                name, score = all_players[i]
                label = rank_labels[i] if i < len(rank_labels) else f"{i + 1}위"
                is_me = (name == "나")
                entry.text = f"{label}  {name}  {score}점"
                entry.color = [255, 230, 50] if is_me else [210, 210, 210]
            else:
                entry.text = ""

    def draw_ranking(self):
        """랭킹 패널(배경·타이틀·구분선·항목)을 그린다."""
        self.ranking_bg.draw()
        self.ranking_title.draw()
        self.ranking_divider.draw()
        for entry in self.ranking_entries:
            if entry.text:
                entry.draw()

    def draw_persistent_hud(self):
        """타이머·라운드·프로그레스 바·점수·랭킹을 캐시 상태로 일괄 그리기."""
        self.round_text.draw()
        self.draw_progress_bar()
        self.timer_text.draw()
        self.score_text.draw()
        self.draw_ranking()
    
    def draw_message(self, message):
        """
        화면 중앙에 메시지 표시
        
        Args:
            message: 표시할 메시지
        """
        if message:
            self.message_text.text = message
            self.message_text.draw()
    
    def draw_instruction(self, instruction):
        """
        하단에 안내 문구 표시
        
        Args:
            instruction: 안내 문구
        """
        if instruction:
            self.instruction_text.text = instruction
            self.instruction_text.draw()

    def draw_start_cue(self, message="시작!"):
        """화면 중앙에 큰 시작 신호를 표시"""
        self.start_cue_text.text = message
        self.start_cue_background.draw()
        self.start_cue_text.draw()

    def draw_round_break(self, current_round, next_round, remaining_sec):
        """라운드 휴식 오버레이: 어두운 패널 + 제목 + 카운트다운."""
        self.round_break_title.text = f"라운드 {current_round} 완료!"
        self.round_break_sub.text = f"{remaining_sec}초 후 라운드 {next_round} 시작"
        self.round_break_bg.draw()
        self.round_break_title.draw()
        self.round_break_sub.draw()

    def set_user_turn_hud(self, selected_token, turn_count, timer_display_text):
        """사용자 턴 HUD 텍스트/색상 갱신"""
        self.message_text.height = self._user_message_height
        self.instruction_text.height = self._user_instruction_height
        self.message_text.text = selected_token.upper()
        self.message_text.color = TEXT_COLOR
        self.timer_text.text = timer_display_text

    def set_pc_turn_hud(self, turn_count, target_pos, timer_label="문어 턴"):
        """PC 턴 HUD 텍스트/색상 갱신"""
        self.message_text.height = self._user_message_height * self._pc_text_scale
        self.instruction_text.height = self._user_instruction_height * self._pc_text_scale
        self.message_text.text = ""
        self.message_text.color = TEXT_COLOR
        self.timer_text.text = ""
    
    def draw_token_choice_buttons(self, hovered=None, selected=None):
        """
        토큰 선택 버튼 그리기
        
        Args:
            hovered: 마우스가 올려진 버튼 ('chase' 또는 'flight')
            selected: 선택된 버튼 ('chase' 또는 'flight')
        """
        for token_name, button in self.token_choice_buttons.items():
            # 버튼 색상 결정
            if selected == token_name:
                button['rect'].fillColor = BUTTON_COLOR_SELECTED
            elif hovered == token_name:
                button['rect'].fillColor = BUTTON_COLOR_HOVER
            else:
                button['rect'].fillColor = BUTTON_COLOR_NORMAL
            
            button['rect'].draw()
            button['text'].draw()
    
    def get_hovered_button(self, mouse_pos):
        """
        마우스가 올려진 버튼 확인
        
        Args:
            mouse_pos: (x, y) 마우스 좌표
        
        Returns:
            'chase', 'flight', 또는 None
        """
        for token_name, button in self.token_choice_buttons.items():
            if button['rect'].contains(mouse_pos):
                return token_name
        return None
    
    def draw_turn_indicator(self, turn):
        """
        현재 턴 표시 (상단 오른쪽)
        
        Args:
            turn: 'user' 또는 'pc'
        """
        turn_text = visual.TextStim(
            win=self.win,
            text=f"{'사용자' if turn == 'user' else '문어'} 턴",
            pos=(WIDTH / 2 - round(120 * _S), HEIGHT / 2 - round(30 * _S)),
            height=_TURN_H,
            color=[255, 200, 0] if turn == 'user' else [200, 0, 255],
            colorSpace='rgb255',
            bold=True
        )
        turn_text.draw()
    
    def draw_phase_title(self, phase_name):
        """
        페이즈 제목 표시 (상단)
        
        Args:
            phase_name: 페이즈 이름
        """
        phase_text = visual.TextStim(
            win=self.win,
            text=phase_name,
            pos=(0, HEIGHT / 2 - round(35 * _S)),
            height=_PHASE_H,
            color=TEXT_COLOR,
            colorSpace='rgb255',
            bold=True
        )
        phase_text.draw()


