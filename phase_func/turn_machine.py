"""
공통 베이스: User/PC 턴 상태기계가 공유하는 헬퍼 함수 + 베이스 클래스.

헬퍼 함수
  draw_game_screen   : 매 프레임 전체 화면 렌더링
  get_clicked_card   : 마우스 위치 → 카드 (row, col) 변환
  run_round_break    : 라운드 간 휴식 화면
  show_reset_prep_cue: 잡기 이벤트 후 위치 초기화 유예 화면

TurnStateMachine
  공통 트리거 / EDF / 저장 / flip / 잡기 이벤트 처리
"""

import sys
from pathlib import Path
from psychopy import core

try:
    from ..config import (
        WIDTH, HEIGHT, TEXT_COLOR,
        DECK_LEFT_EDGE, BOARD_DECK_TOP_MARGIN,
        DECK_CARD_WIDTH, DECK_CARD_HEIGHT, DECK_CARD_SPACING,
        FEEDBACK_DURATION, ROUND_BREAK_DURATION, CATCH_RESET_PREP_DURATION,
        DARK_GREY,
    )
    from ..view_func.frame_marker import blink_frame_marker, trigger_frame_marker
    from ..sounds import play as sound_play
    from ..labjack_func.labjack_triggers import set_trigger, reset_trigger, TRIG_TRIAL_END
    from ..save_func.trial_saver import save_trial
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from config import (
        WIDTH, HEIGHT, TEXT_COLOR,
        DECK_LEFT_EDGE, BOARD_DECK_TOP_MARGIN,
        DECK_CARD_WIDTH, DECK_CARD_HEIGHT, DECK_CARD_SPACING,
        FEEDBACK_DURATION, ROUND_BREAK_DURATION, CATCH_RESET_PREP_DURATION,
        DARK_GREY,
    )
    from view_func.frame_marker import blink_frame_marker, trigger_frame_marker
    from sounds import play as sound_play
    from chicken_task_first.labjack_func.labjack_triggers import set_trigger, reset_trigger, TRIG_TRIAL_END
    from save_func.trial_saver import save_trial


# ── 헬퍼 함수 ────────────────────────────────────────────────────────────────

def draw_game_screen(win, ui, board_r, deck_r, token_r, gs=None, highlighted_pos=None):
    seq_cells  = gs.seq_memory_targets if (gs and gs.seq_memory_active) else None
    done_cells = gs.seq_memory_targets[:gs.seq_memory_step] if seq_cells else None
    board_r.draw(highlighted_pos, seq_cells=seq_cells, done_cells=done_cells)
    deck_r.draw()
    token_r.draw()
    if gs is not None:
        bar_ratio = gs.timer.get_remaining() / max(1, gs.timer.time_limit)
        ui.set_round_display(gs.current_round, gs.total_rounds)
        ui.draw_progress_bar(bar_ratio)
        ui.draw_score(gs.round_score, gs.pc_round_score)
        ui.update_ranking(gs.user_score, gs.pc_score)
    else:
        ui.draw_progress_bar()
        ui.score_text.draw()
    ui.draw_ranking()
    ui.timer_text.draw()
    ui.round_text.draw()
    ui.message_text.draw()
    ui.instruction_text.draw()


def get_clicked_card(mouse_pos, deck_rows, deck_cols):
    sx = mouse_pos[0] + WIDTH / 2
    sy = HEIGHT / 2 - mouse_pos[1]
    for row in range(deck_rows):
        for col in range(deck_cols):
            left   = DECK_LEFT_EDGE + col * (DECK_CARD_WIDTH + DECK_CARD_SPACING)
            top    = BOARD_DECK_TOP_MARGIN + row * (DECK_CARD_HEIGHT + DECK_CARD_SPACING)
            if left <= sx <= left + DECK_CARD_WIDTH and top <= sy <= top + DECK_CARD_HEIGHT:
                return (row, col)
    return None


def run_round_break(win, ui, board_r, deck_r, token_r, gs, fdl=None):
    if fdl:
        fdl.reset()
    completed, nxt = gs.current_round - 1, gs.current_round
    end_time = core.getTime() + ROUND_BREAK_DURATION
    while core.getTime() < end_time:
        remaining = max(1, int(end_time - core.getTime()) + 1)
        draw_game_screen(win, ui, board_r, deck_r, token_r, gs)
        ui.draw_round_break(completed, nxt, remaining)
        blink_frame_marker(win)
        win.flip()
        if fdl:
            fdl.after_flip(core.getTime(), context='round_break')


def show_reset_prep_cue(win, ui, board_r, deck_r, token_r, gs, fdl=None):
    if fdl:
        fdl.reset()
    ui.message_text.text  = "준비..."
    ui.message_text.color = TEXT_COLOR
    draw_game_screen(win, ui, board_r, deck_r, token_r, gs)
    trigger_frame_marker()
    blink_frame_marker(win)
    win.flip()
    if fdl:
        fdl.after_flip(core.getTime(), context='catch_prep')
    end_time = core.getTime() + CATCH_RESET_PREP_DURATION
    while core.getTime() < end_time:
        draw_game_screen(win, ui, board_r, deck_r, token_r, gs)
        blink_frame_marker(win)
        win.flip()
        if fdl:
            fdl.after_flip(core.getTime(), context='catch_prep')


# ── 베이스 클래스 ─────────────────────────────────────────────────────────────

class TurnStateMachine:
    """User/PC 턴 상태기계의 공통 베이스."""

    def __init__(self, win, gs, ui, board_r, deck_r, token_r,
                 aoi=None, ljack=None, save_paths=None, subject_id='', sounds=None, fdl=None):
        self.win, self.gs, self.ui         = win, gs, ui
        self.board_r, self.deck_r, self.token_r = board_r, deck_r, token_r
        self.aoi, self.ljack               = aoi, ljack
        self.save_paths, self.subject_id   = save_paths, subject_id
        self.sounds, self.fdl              = sounds, fdl

        self._sub_phase     = 'TRIAL_INIT'
        self._pre_flip_code = 0
        self.deadline       = 0.0
        self.result         = None
        self.trial_id       = None

    # ── 트리거 ───────────────────────────────────────────────────────────────

    def _trigger(self, code):
        """즉시 전송 + 다음 flip에 reset 예약."""
        if self.ljack and code:
            set_trigger(self.ljack, code)
            self.win.callOnFlip(reset_trigger, self.ljack)

    def _schedule(self, code):
        """다음 flip 시점에 트리거 예약."""
        self._pre_flip_code = code

    def _flush_and_flip(self, context):
        """예약 트리거 전송 → flip → 사후처리."""
        queued = bool(self._pre_flip_code and self.ljack)
        if queued:
            self.win.callOnFlip(set_trigger, self.ljack, self._pre_flip_code)
            self._pre_flip_code = 0
        self.win.flip()
        if self.fdl:
            self.fdl.after_flip(core.getTime(), trial_id=self.trial_id, context=context)
        if self.aoi:
            self.aoi.update(core.getTime())
        if queued and self.ljack:
            self.win.callOnFlip(reset_trigger, self.ljack)

    # ── EDF / 저장 ───────────────────────────────────────────────────────────

    def _edf(self, msg):
        if self.aoi and self.aoi.el_tracker:
            self.aoi.el_tracker.sendMessage(msg)

    def _save_trial(self):
        if self.save_paths and self.gs.trial_history:
            save_trial(self.save_paths['trial'], self.gs.trial_history[-1],
                       self.gs, self.subject_id)

    # ── 잡기 이벤트 (User/PC 공통) ───────────────────────────────────────────

    def _show_catch_feedback(self, msg, color, sound_key, edf_result):
        """잡기 피드백 루프 → EDF 기록 → 라운드 전환."""
        self.board_r.refresh()
        self.deck_r.refresh()
        sound_play(self.sounds, sound_key)
        end_time = core.getTime() + FEEDBACK_DURATION * 2
        while core.getTime() < end_time:
            draw_game_screen(self.win, self.ui, self.board_r, self.deck_r, self.token_r, self.gs)
            self.ui.draw_feedback_message(msg, color)
            blink_frame_marker(self.win)
            self.win.flip()
            if self.fdl:
                self.fdl.after_flip(core.getTime(), trial_id=self.trial_id,
                                    context='catch_feedback')
            if self.aoi:
                self.aoi.update(core.getTime())
        show_reset_prep_cue(self.win, self.ui, self.board_r, self.deck_r, self.token_r,
                            self.gs, fdl=self.fdl)
        self._edf(f"TRIAL_END {self.trial_id} MATCH 1 RESULT {edf_result}")
        self._trigger(TRIG_TRIAL_END)
        self.gs.advance_round()
        self.board_r.update_board(self.gs.board)
        self.deck_r.update_deck(self.gs.deck)
        if self.aoi:
            self.aoi.update_deck(self.gs.deck)
