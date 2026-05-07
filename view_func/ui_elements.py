# view_func/ui_elements.py
# UI element rendering (timer, score, text, buttons, ranking, overlays)

import sys, os, random
from psychopy import visual

sys.path.insert(0, os.path.abspath(os.path.join(__file__, '..', '..')))
from config import (
    WIDTH, HEIGHT,
    TEXT_COLOR, TEXT_SIZE,
    BUTTON_COLOR_NORMAL, BUTTON_COLOR_HOVER, BUTTON_COLOR_SELECTED,
    TOKEN_BUTTON_WIDTH, TOKEN_BUTTON_HEIGHT, TOKEN_BUTTON_TEXT_HEIGHT,
    MESSAGE_Y_OFFSET,
    CHASE_BUTTON_POS, FLIGHT_BUTTON_POS, TOKEN_BUTTON_LINE_WIDTH, PURPLE, WHITE,
    PROGRESS_BAR_WIDTH, PROGRESS_BAR_HEIGHT, PROGRESS_BAR_Y_FROM_TOP,
    PROGRESS_BAR_COLOR_FULL, PROGRESS_BAR_COLOR_WARN, PROGRESS_BAR_COLOR_CRIT,
    PROGRESS_BAR_BG_COLOR,
)

_FALLBACK_NAMES = ["토끼", "여우", "다람쥐", "오리", "강아지"]

# ── Scale factor (TEXT_SIZE / 28 baseline) ────────────────────────────────────
_S = TEXT_SIZE / 28

# ── HUD text / bar sizes ──────────────────────────────────────────────────────
_TIMER_H      = max(12, round(22 * _S))
_ROUND_H      = max(10, round(22 * _S))
_SCORE_H      = max(10, round(20 * _S))
_BAR_H        = max(6,  round(PROGRESS_BAR_HEIGHT * _S))
_BAR_INNER_W  = max(200, round((PROGRESS_BAR_WIDTH - 140) * _S))
_BAR_SIDE_PAD = max(20, round(55 * _S))
_MSG_H        = max(10, round(15 * _S))
_START_CUE_H  = max(20, round(90 * _S))
_INSTR_H      = max(10, round(25 * _S))
_CUE_BG_W     = max(200, round(320 * _S))
_CUE_BG_H     = max(80,  round(160 * _S))

# ── Round-break overlay sizes ─────────────────────────────────────────────────
_BREAK_BG_W    = max(300, round(500 * _S))
_BREAK_BG_H    = max(100, round(170 * _S))
_BREAK_TITLE_H = max(16,  round(30  * _S))
_BREAK_SUB_H   = max(11,  round(20  * _S))
_BREAK_LINE_GAP = max(10, round(18  * _S))

# ── HUD row Y positions ───────────────────────────────────────────────────────
_HUD_ROW1_Y  = HEIGHT / 2 - round(22 * _S)
_HUD_BAR_Y   = HEIGHT / 2 - round(PROGRESS_BAR_Y_FROM_TOP * _S)
_HUD_SCORE_Y = HEIGHT / 2 - round(88 * _S)

# ── Ranking panel sizes ───────────────────────────────────────────────────────
_R_PAD       = max(8,  round(10 * _S))
_R_TITLE_H   = max(9,  round(11 * _S))
_R_ENTRY_H   = max(7,  round(9  * _S))
_R_ROW_PITCH = max(14, round(_R_ENTRY_H * 1.8))
_N_ENTRIES   = 7

# ── Named colors ──────────────────────────────────────────────────────────────
_COLOR_MSG        = [255, 255, 0]
_COLOR_BTN_LINE   = [255, 255, 255]
_COLOR_BREAK_BG   = [30, 30, 30]
_COLOR_BREAK_BD   = [200, 200, 200]
_COLOR_BREAK_TTL  = [255, 220, 60]
_COLOR_BREAK_SUB  = [200, 200, 200]
_COLOR_RANK_BG    = [20, 20, 40]
_COLOR_RANK_BD    = [80, 130, 220]
_COLOR_RANK_TTL   = [100, 190, 255]
_COLOR_RANK_DIV   = [80, 130, 220]
_COLOR_RANK_USER  = [255, 230, 50]
_COLOR_RANK_PC    = [100, 220, 255]
_COLOR_RANK_NORM  = [210, 210, 210]

_MSG_BASE_Y = -360 + MESSAGE_Y_OFFSET


def fetch_random_nicknames(count=5):
    """Fetch Korean nicknames from API in parallel; falls back to _FALLBACK_NAMES on error."""
    import requests
    from concurrent.futures import ThreadPoolExecutor

    def _fetch_one(i):
        try:
            res = requests.post(
                'https://www.rivestsoft.com/nickname/getRandomNickname.ajax',
                data={'lang': 'ko'},
                timeout=3,
            )
            res.raise_for_status()
            name = res.json().get('data', _FALLBACK_NAMES[i % len(_FALLBACK_NAMES)])
            print(f"  [닉네임 API] {i + 1}번째: {name}")
            return name
        except Exception as e:
            fallback = _FALLBACK_NAMES[i % len(_FALLBACK_NAMES)]
            print(f"  [닉네임 API] {i + 1}번째 실패({e}) → fallback: {fallback}")
            return fallback

    with ThreadPoolExecutor(max_workers=count) as pool:
        return list(pool.map(_fetch_one, range(count)))


class UIElements:
    """Manages all in-game UI elements (HUD, overlays, buttons, ranking panel)."""

    def __init__(self, win, fake_player_names=None):
        self.win = win
        self.token_choice_buttons = {}
        self.ranking_entries = []

        names = (fake_player_names or _FALLBACK_NAMES)[:]
        raw_scores = sorted(random.sample(range(400, 1800), min(5, len(names))), reverse=True)
        self._fake_players = list(zip(names[:5], raw_scores))
        self._cumulative_user_score = 0

        # Progress bar render cache
        self._bar_max_width    = _BAR_INNER_W
        self._bar_left_edge    = -_BAR_INNER_W / 2
        self._cached_bar_ratio = 1.0
        self._cached_bar_color = PROGRESS_BAR_COLOR_FULL
        self._cached_bar_w     = _BAR_INNER_W
        self._cached_bar_x     = 0.0

        # Button fill-color cache (skip redundant GPU updates)
        self._btn_state = {}

        self._create_hud()
        self._create_overlays()
        self._create_token_buttons()
        self._create_ranking_panel()

        self._user_message_height     = self.message_text.height
        self._user_instruction_height = self.instruction_text.height
        self._pc_text_scale           = 0.8

    # ── Factory helpers ────────────────────────────────────────────────────────

    def _textstim(self, text, pos, height, color, **kw):
        return visual.TextStim(
            win=self.win, text=text, pos=pos,
            height=height, color=color, colorSpace='rgb255', **kw,
        )

    def _rectstim(self, width, height, pos, fill, line=None, **kw):
        line = fill if line is None else line
        return visual.Rect(
            win=self.win, width=width, height=height, pos=pos,
            fillColor=fill, lineColor=line, colorSpace='rgb255', **kw,
        )

    # ── Creation ───────────────────────────────────────────────────────────────

    def _create_hud(self):
        self.round_text = self._textstim(
            "라운드 1", (-WIDTH / 2 + round(90 * _S), _HUD_ROW1_Y),
            _ROUND_H, TEXT_COLOR, bold=True, anchorHoriz='left',
        )
        self.progress_bar_bg = self._rectstim(
            _BAR_INNER_W, _BAR_H, (0, _HUD_BAR_Y), PROGRESS_BAR_BG_COLOR,
        )
        self.progress_bar_fg = self._rectstim(
            _BAR_INNER_W, _BAR_H, (0, _HUD_BAR_Y), PROGRESS_BAR_COLOR_FULL,
        )
        self.timer_text = self._textstim(
            "15s", (_BAR_INNER_W / 2 + _BAR_SIDE_PAD, _HUD_BAR_Y),
            _TIMER_H, TEXT_COLOR, bold=True, anchorHoriz='left',
        )
        self.score_text = self._textstim(
            "내 점수: 0 | 문어: 0", (0, _HUD_SCORE_Y), _SCORE_H, TEXT_COLOR,
        )
        self.message_text = self._textstim(
            "", (0, _MSG_BASE_Y), _MSG_H, _COLOR_MSG, bold=True,
        )
        instr_y = (
            _MSG_BASE_Y
            - self.message_text.height / 2
            - round(14 * _S)
            - _INSTR_H / 2
            - round(60 * _S)
        )
        self.instruction_text = self._textstim(
            "", (0, instr_y), _INSTR_H, TEXT_COLOR,
        )

    def _create_overlays(self):
        self.start_cue_background = self._rectstim(_CUE_BG_W, _CUE_BG_H, (0, 0), WHITE)
        self.start_cue_text = self._textstim("", (0, 0), _START_CUE_H, PURPLE, bold=True)

        title_y = _BREAK_LINE_GAP // 2 + _BREAK_TITLE_H // 2
        sub_y   = -(_BREAK_LINE_GAP // 2 + _BREAK_SUB_H // 2)
        self.round_break_bg = self._rectstim(
            _BREAK_BG_W, _BREAK_BG_H, (0, 0),
            _COLOR_BREAK_BG, _COLOR_BREAK_BD, lineWidth=2,
        )
        self.round_break_title = self._textstim(
            "", (0, title_y), _BREAK_TITLE_H, _COLOR_BREAK_TTL, bold=True,
        )
        self.round_break_sub = self._textstim(
            "", (0, sub_y), _BREAK_SUB_H, _COLOR_BREAK_SUB,
        )

    def _make_button(self, pos, label):
        return {
            'rect': self._rectstim(
                TOKEN_BUTTON_WIDTH, TOKEN_BUTTON_HEIGHT, pos,
                BUTTON_COLOR_NORMAL, _COLOR_BTN_LINE, lineWidth=TOKEN_BUTTON_LINE_WIDTH,
            ),
            'text': self._textstim(label, pos, TOKEN_BUTTON_TEXT_HEIGHT, _COLOR_BTN_LINE),
        }

    def _create_token_buttons(self):
        self.token_choice_buttons = {
            'chase':  self._make_button(CHASE_BUTTON_POS,  "CHASE\n(문어를 쫓는 닭)"),
            'flight': self._make_button(FLIGHT_BUTTON_POS, "FLIGHT\n(도망치는 닭)"),
        }

    def _create_ranking_panel(self):
        win_w, win_h = self.win.size
        r_margin  = max(25, round(30 * _S))
        r_panel_w = min(max(180, round(205 * _S)), win_w // 4)
        content_h = (
            _R_PAD + _R_TITLE_H + _R_PAD + 2 + _R_PAD
            + _N_ENTRIES * _R_ROW_PITCH + _R_PAD
        )
        r_panel_h = min(content_h, win_h - 2 * r_margin)
        cx = win_w / 2 - r_panel_w / 2 - r_margin
        cy = -win_h / 2 + r_panel_h / 2 + r_margin

        self.ranking_bg = self._rectstim(
            r_panel_w, r_panel_h, (cx, cy),
            _COLOR_RANK_BG, _COLOR_RANK_BD, lineWidth=max(1, round(2 * _S)),
        )
        title_y = cy + r_panel_h / 2 - _R_PAD - _R_TITLE_H / 2
        self.ranking_title = self._textstim(
            "순위표 (누적 점수)", (cx, title_y), _R_TITLE_H, _COLOR_RANK_TTL,
            bold=True, wrapWidth=r_panel_w - _R_PAD * 2,
        )
        div_y = title_y - _R_TITLE_H / 2 - _R_PAD
        self.ranking_divider = self._rectstim(
            r_panel_w - _R_PAD * 2, 2, (cx, div_y), _COLOR_RANK_DIV,
        )

        entry_x       = cx - r_panel_w / 2 + _R_PAD
        first_entry_y = div_y - _R_PAD - _R_ROW_PITCH / 2
        self.ranking_entries = [
            self._textstim(
                "", (entry_x, first_entry_y - i * _R_ROW_PITCH),
                _R_ENTRY_H, _COLOR_RANK_NORM,
                anchorHoriz='left', wrapWidth=r_panel_w - _R_PAD * 2,
            )
            for i in range(_N_ENTRIES)
        ]

    # ── Public draw / update ───────────────────────────────────────────────────

    def draw_score(self, round_score, pc_score):
        self.score_text.text = f"이번 라운드: {round_score}점  |  문어: {pc_score}점"
        self.score_text.draw()

    def set_round_display(self, current_round, total_rounds=None):
        self.round_text.text = f"라운드 {current_round}"

    def draw_progress_bar(self, ratio=None):
        if ratio is not None:
            ratio = max(0.0, min(1.0, ratio))
            if ratio != self._cached_bar_ratio:
                self._cached_bar_ratio = ratio
                self._cached_bar_color = (
                    PROGRESS_BAR_COLOR_FULL if ratio > 0.5 else
                    PROGRESS_BAR_COLOR_WARN if ratio > 0.25 else
                    PROGRESS_BAR_COLOR_CRIT
                )
                self._cached_bar_w = max(2, round(self._bar_max_width * ratio))
                self._cached_bar_x = self._bar_left_edge + self._cached_bar_w / 2
                self.progress_bar_fg.width     = self._cached_bar_w
                self.progress_bar_fg.pos       = (self._cached_bar_x, self.progress_bar_fg.pos[1])
                self.progress_bar_fg.fillColor = self._cached_bar_color
                self.progress_bar_fg.lineColor = self._cached_bar_color

        self.progress_bar_bg.draw()
        self.progress_bar_fg.draw()

    def update_ranking(self, user_cumulative, pc_cumulative):
        self._cumulative_user_score = user_cumulative
        all_players = self._fake_players + [("나", user_cumulative), ("문어", pc_cumulative)]
        all_players.sort(key=lambda p: p[1], reverse=True)
        for i, entry in enumerate(self.ranking_entries):
            if i < len(all_players):
                name, score = all_players[i]
                entry.color = (
                    _COLOR_RANK_USER if name == "나"   else
                    _COLOR_RANK_PC   if name == "문어" else
                    _COLOR_RANK_NORM
                )
                entry.text = f"{i + 1}위  {name}  {score}점"
            else:
                entry.text = ""

    def draw_ranking(self):
        self.ranking_bg.draw()
        self.ranking_title.draw()
        self.ranking_divider.draw()
        for entry in self.ranking_entries:
            if entry.text:
                entry.draw()

    def draw_persistent_hud(self):
        self.round_text.draw()
        self.draw_progress_bar()
        self.timer_text.draw()
        self.score_text.draw()
        self.draw_ranking()

    def draw_start_cue(self, message="시작!"):
        self.start_cue_text.text = message
        self.start_cue_background.draw()
        self.start_cue_text.draw()

    def draw_feedback_message(self, msg, color):
        self.message_text.text  = msg
        self.message_text.color = color
        self.message_text.draw()

    def draw_round_break(self, current_round, next_round, remaining_sec):
        self.round_break_title.text = f"라운드 {current_round} 완료!"
        self.round_break_sub.text   = f"{remaining_sec}초 후 라운드 {next_round} 시작"
        self.round_break_bg.draw()
        self.round_break_title.draw()
        self.round_break_sub.draw()

    def set_user_turn_hud(self, selected_token, turn_count, timer_display_text):
        self.message_text.height     = self._user_message_height
        self.instruction_text.height = self._user_instruction_height
        self.message_text.text       = (selected_token or '').upper()
        self.message_text.color      = TEXT_COLOR
        self.timer_text.text         = timer_display_text

    def set_pc_turn_hud(self, turn_count, target_pos, timer_label="NPC"):
        self.message_text.height     = self._user_message_height * self._pc_text_scale
        self.instruction_text.height = self._user_instruction_height * self._pc_text_scale
        self.message_text.text       = ""
        self.message_text.color      = TEXT_COLOR
        self.timer_text.text         = ""

    def draw_token_choice_buttons(self, hovered=None, selected=None):
        for name, btn in self.token_choice_buttons.items():
            color = (
                BUTTON_COLOR_SELECTED if selected == name else
                BUTTON_COLOR_HOVER    if hovered  == name else
                BUTTON_COLOR_NORMAL
            )
            if self._btn_state.get(name) != color:
                btn['rect'].fillColor = color
                self._btn_state[name] = color
            btn['rect'].draw()
            btn['text'].draw()

    def get_hovered_button(self, mouse_pos):
        for name, btn in self.token_choice_buttons.items():
            if btn['rect'].contains(mouse_pos):
                return name
        return None
