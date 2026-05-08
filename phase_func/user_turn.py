"""
사용자 턴 상태기계.

상태 전이:
  TRIAL_INIT → WAIT_INPUT → CARD_FLIPPING
                               ├─ step_success  → WAIT_INPUT  (seq 중간 스텝)
                               ├─ success/all_success → FEEDBACK → TRIAL_INTERVAL → START_CUE → TRIAL_INIT
                               └─ failure        → FEEDBACK → (턴 종료)
  WAIT_INPUT ─ timeout → FEEDBACK → (턴 종료)
"""

import sys
from pathlib import Path
from psychopy import core, event

try:
    from ..config import (
        KEY_EXIT, CARD_FLIP_DURATION, FEEDBACK_DURATION, TRIAL_INTERVAL,
        PURPLE, DARK_GREY, GOLD, SCORE_CATCH_BONUS,
    )
    from ..view_func.frame_marker import blink_frame_marker, trigger_frame_marker
    from ..sounds import play as sound_play
    from ..labjack_func.labjack_triggers import (
        TRIG_TRIAL_START, TRIG_TRIAL_END, TRIG_CARD_CLICK, TRIG_CARD_FLIP_USER,
        TRIG_FEEDBACK_SUCCESS, TRIG_FEEDBACK_FAILURE, TRIG_FEEDBACK_TIMEOUT,
        TRIG_SEQ_ALL_SUCCESS, TRIG_SEQ_FAILURE,
    )
    from ..phase_func.turn_machine import (
        TurnStateMachine, draw_game_screen, get_clicked_card, run_round_break)
    from ..phase_func.token_selection import run_token_selection_phase
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from config import (
        KEY_EXIT, CARD_FLIP_DURATION, FEEDBACK_DURATION, TRIAL_INTERVAL,
        PURPLE, DARK_GREY, GOLD, SCORE_CATCH_BONUS,
    )
    from view_func.frame_marker import blink_frame_marker, trigger_frame_marker
    from sounds import play as sound_play
    from chicken_task_first.labjack_func.labjack_triggers import (
        TRIG_TRIAL_START, TRIG_TRIAL_END, TRIG_CARD_CLICK, TRIG_CARD_FLIP_USER,
        TRIG_FEEDBACK_SUCCESS, TRIG_FEEDBACK_FAILURE, TRIG_FEEDBACK_TIMEOUT,
        TRIG_SEQ_ALL_SUCCESS, TRIG_SEQ_FAILURE,
    )
    from phase_func.turn_machine import (
        TurnStateMachine, draw_game_screen, get_clicked_card, run_round_break)
    from phase_func.token_selection import run_token_selection_phase

START_CUE_DURATION = 0.5


class UserTurnMachine(TurnStateMachine):
    """사용자 턴 상태기계."""

    def __init__(self, *args, mouse=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.mouse       = mouse
        self.card_row    = None
        self.card_col    = None
        self.was_seq     = False
        self._fb_msg     = ''
        self._fb_color   = DARK_GREY
        self._fb_code    = 0
        self._fb_success = False
        self._fb_timeout = False

    # ── 메인 루프 ────────────────────────────────────────────────────────────

    def run(self) -> str:
        if self.gs.selected_token is None:
            sel = run_token_selection_phase(
                self.win, self.gs, self.ui, self.board_r, self.deck_r, self.token_r,
                sounds=self.sounds, labjack_handle=self.ljack)
            if sel == 'exit':
                return 'exit'
            if not self.gs.confirm_selection():
                return 'continue'

        self._sub_phase = 'TRIAL_INIT'
        while (self.gs.phase == self.gs.PHASE_GAME_PLAY
               and self.gs.current_turn == self.gs.TURN_USER):
            now        = core.getTime()
            target_pos = (self.gs.get_seq_memory_current_target()
                          if self.gs.seq_memory_active
                          else self.gs.get_target_position())
            self._step(now)
            self._draw(target_pos)
            self._flush_and_flip(self._sub_phase)
            if KEY_EXIT in event.getKeys():
                return 'exit'
        return 'continue'

    # ── 상태 디스패치 ─────────────────────────────────────────────────────────

    def _step(self, now):
        dispatch = {
            'TRIAL_INIT':     self._init_trial,
            'WAIT_INPUT':     self._wait_input,
            'CARD_FLIPPING':  self._card_flipping,
            'FEEDBACK':       self._feedback,
            'TRIAL_INTERVAL': self._trial_interval,
            'START_CUE':      self._start_cue,
        }
        dispatch[self._sub_phase](now)

    def _draw(self, target_pos):
        self.ui.set_user_turn_hud(
            selected_token=self.gs.selected_token,
            turn_count=self.gs.turn_count,
            timer_display_text=self.gs.timer.get_display_text(),
        )
        render_target = None if self._sub_phase == 'FEEDBACK' else target_pos
        draw_game_screen(self.win, self.ui, self.board_r, self.deck_r, self.token_r,
                         self.gs, render_target)
        if self._sub_phase == 'FEEDBACK':
            self.ui.draw_feedback_message(self._fb_msg, self._fb_color)
        elif self._sub_phase == 'START_CUE':
            self.ui.draw_start_cue("시작!")
        blink_frame_marker(self.win)

    # ── 상태 핸들러 ───────────────────────────────────────────────────────────

    def _init_trial(self, now):
        self.trial_id = self.gs.get_next_trial_id()
        self.gs.try_activate_seq_memory()
        if self.aoi:
            self.aoi.current_trial_id = self.trial_id
            self.aoi.is_seq_memory    = self.gs.seq_memory_active
            self.aoi.seq_memory_step  = self.gs.seq_memory_step if self.gs.seq_memory_active else None
        if self.gs.seq_memory_active:
            trigger_frame_marker()
        seq_tag = (f" SEQ_MEMORY step 0/{len(self.gs.seq_memory_targets)}"
                   if self.gs.seq_memory_active else "")
        self._edf(f"TRIAL_START {self.trial_id} USER"
                  f" ROUND {self.gs.current_round} TURN {self.gs.turn_count}{seq_tag}")
        self.gs.current_trial_start_psychopy = core.getTime()
        self._schedule(TRIG_TRIAL_START)
        self.gs.timer.reset()
        self._sub_phase = 'WAIT_INPUT'

    def _wait_input(self, now):
        if self.gs.timer.is_expired():
            sound_play(self.sounds, 'error')
            timeout_str = "seq_timeout" if self.gs.seq_memory_active else "timeout"
            self._edf(f"TRIAL_END {self.trial_id} MATCH 0 RESULT {timeout_str}")
            self._set_feedback(False, True, "시간 초과", DARK_GREY, TRIG_FEEDBACK_TIMEOUT, now)
            return

        if not self.mouse.getPressed()[0]:
            return
        pos = get_clicked_card(self.mouse.getPos(), self.gs.deck.rows, self.gs.deck.cols)
        if pos is None:
            return

        self.card_row, self.card_col = pos
        self._trigger(TRIG_CARD_CLICK)
        self.was_seq = self.gs.seq_memory_active
        if self.was_seq:
            self.result = self.gs.check_seq_memory_card(self.card_row, self.card_col)
        else:
            self.result = self.gs.user_click_card(self.card_row, self.card_col,
                                                   defer_success_move=True)
        self._save_trial()
        sound_play(self.sounds, 'flip')
        trigger_frame_marker()
        self._schedule(TRIG_CARD_FLIP_USER)
        self.deadline   = now + CARD_FLIP_DURATION
        self._sub_phase = 'CARD_FLIPPING'

    def _card_flipping(self, now):
        if now < self.deadline:
            return
        if self.result == 'step_success':
            self._next_seq_step(now)
        elif self.result in ('success', 'all_success'):
            self._set_success_feedback(now)
        else:
            self._set_failure_feedback(now)

    def _next_seq_step(self, now):
        step_now, step_total = self.gs.seq_memory_step, len(self.gs.seq_memory_targets)
        self.gs.deck.hide_card(self.card_row, self.card_col)
        self.trial_id = self.gs.get_next_trial_id()
        if self.aoi:
            self.aoi.current_trial_id = self.trial_id
            self.aoi.is_seq_memory    = True
            self.aoi.seq_memory_step  = self.gs.seq_memory_step
        self._edf(f"TRIAL_START {self.trial_id} USER"
                  f" ROUND {self.gs.current_round} TURN {self.gs.turn_count}"
                  f" SEQ_MEMORY step {step_now}/{step_total}")
        self.gs.current_trial_start_psychopy = core.getTime()
        self._schedule(TRIG_TRIAL_START)
        self._sub_phase = 'WAIT_INPUT'

    def _set_success_feedback(self, now):
        sound_play(self.sounds, 'correct')
        if self.result == 'all_success':
            n = len(self.gs.seq_memory_targets)
            msg, color, code = f"순차 {n}/{n} 완료!  {n}칸 이동!", GOLD, TRIG_SEQ_ALL_SUCCESS
        else:
            msg, color, code = "성공", PURPLE, TRIG_FEEDBACK_SUCCESS
        self._set_feedback(True, False, msg, color, code, now)

    def _set_failure_feedback(self, now):
        sound_play(self.sounds, 'error')
        if self.was_seq:
            self._edf(f"TRIAL_END {self.trial_id} MATCH 0 RESULT seq_failure")
            msg, color, code = "순차 실패 - 이동 없음", DARK_GREY, TRIG_SEQ_FAILURE
        else:
            self._edf(f"TRIAL_END {self.trial_id} MATCH 0 RESULT failure")
            msg, color, code = "실패", DARK_GREY, TRIG_FEEDBACK_FAILURE
        self._set_feedback(False, False, msg, color, code, now)

    def _set_feedback(self, success, timeout, msg, color, code, now):
        self._fb_success, self._fb_timeout = success, timeout
        self._fb_msg, self._fb_color, self._fb_code = msg, color, code
        self._schedule(code)
        self.deadline   = now + FEEDBACK_DURATION
        self._sub_phase = 'FEEDBACK'

    def _feedback(self, now):
        if now < self.deadline:
            return
        if self._fb_success:
            self._on_success(now)
        else:
            self._on_failure()

    def _on_success(self, now):
        if self.result == 'all_success':
            move_result = self.gs.complete_seq_memory_move()
            edf_result  = 'seq_all_success'
        else:
            move_result = self.gs.complete_user_success_move()
            edf_result  = 'success'
        self.gs.deck.hide_card(self.card_row, self.card_col)

        if move_result == 'user_caught_npc':
            self._show_catch_feedback(
                f"문어를 잡았다!  +{SCORE_CATCH_BONUS}점", GOLD, 'win', 'user_caught_npc')
            self.gs.selected_token = None
            self.gs.timer.reset()
            self.gs.phase = self.gs.PHASE_TOKEN_SELECTION
            run_round_break(self.win, self.ui, self.board_r, self.deck_r, self.token_r,
                            self.gs, fdl=self.fdl)
            return  # while 조건(phase)이 바뀌어 루프 종료

        self._edf(f"TRIAL_END {self.trial_id} MATCH 1 RESULT {edf_result}")
        self._trigger(TRIG_TRIAL_END)
        self.deadline   = now + TRIAL_INTERVAL
        self._sub_phase = 'TRIAL_INTERVAL'

    def _on_failure(self):
        if not self._fb_timeout:
            self.gs.deck.hide_card(self.card_row, self.card_col)
            self._trigger(TRIG_TRIAL_END)
        self.gs.end_user_turn()  # 턴 종료 → while 조건(current_turn)이 바뀌어 루프 종료

    def _trial_interval(self, now):
        if now >= self.deadline:
            self.deadline   = now + START_CUE_DURATION
            sound_play(self.sounds, 'qbeep')
            trigger_frame_marker()
            if self.fdl:
                self.fdl.reset()
            self._sub_phase = 'START_CUE'

    def _start_cue(self, now):
        if now >= self.deadline:
            self.gs.timer.reset()
            self._sub_phase = 'TRIAL_INIT'
