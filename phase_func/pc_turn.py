"""
PC(문어) 턴 상태기계.

상태 전이:
  TRIAL_INIT → PC_THINK → CARD_FLIPPING
                             ├─ step_success  → PC_THINK  (seq 다음 스텝)
                             ├─ success/all_success → FEEDBACK → TRIAL_INTERVAL → TRIAL_INIT
                             └─ failure        → FEEDBACK → (턴 종료)
"""

import sys
from pathlib import Path
from psychopy import core

try:
    from ..config import (
        PC_THINK_TIME, CARD_FLIP_DURATION, FEEDBACK_DURATION, TRIAL_INTERVAL,
        PURPLE, DARK_GREY, GOLD, ORANGE_RED, SCORE_CAUGHT_PENALTY,
    )
    from ..view_func.frame_marker import blink_frame_marker, trigger_frame_marker
    from ..sounds import play as sound_play
    from ..labjack_func.labjack_triggers import (
        TRIG_TRIAL_START, TRIG_TRIAL_END, TRIG_CARD_FLIP_PC,
        TRIG_SEQ_ACTIVATE, TRIG_SEQ_ALL_SUCCESS, TRIG_SEQ_FAILURE,
    )
    from ..phase_func.turn_machine import (
        TurnStateMachine, draw_game_screen, run_round_break)
except ImportError:
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from config import (
        PC_THINK_TIME, CARD_FLIP_DURATION, FEEDBACK_DURATION, TRIAL_INTERVAL,
        PURPLE, DARK_GREY, GOLD, ORANGE_RED, SCORE_CAUGHT_PENALTY,
    )
    from view_func.frame_marker import blink_frame_marker, trigger_frame_marker
    from sounds import play as sound_play
    from chicken_task_first.labjack_func.labjack_triggers import (
        TRIG_TRIAL_START, TRIG_TRIAL_END, TRIG_CARD_FLIP_PC,
        TRIG_SEQ_ACTIVATE, TRIG_SEQ_ALL_SUCCESS, TRIG_SEQ_FAILURE,
    )
    from phase_func.turn_machine import (
        TurnStateMachine, draw_game_screen, run_round_break)


class PCTurnMachine(TurnStateMachine):
    """PC(문어) 턴 상태기계."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._is_seq_continue = False
        self.pc_target_pos    = None
        self.card_pos         = None
        self._checked_as_seq  = False
        self._fb_msg          = ''
        self._fb_color        = DARK_GREY
        self._fb_code         = 0
        self._fb_success      = False
        self._fb_highlighted  = None

    # ── 메인 루프 ────────────────────────────────────────────────────────────

    def run(self) -> str:
        self._sub_phase = 'TRIAL_INIT'
        while self.gs.current_turn == self.gs.TURN_PC:
            now = core.getTime()
            self.pc_target_pos = (self.gs.get_seq_memory_current_target()
                                  if self.gs.seq_memory_active
                                  else self.gs.tokens.get_target_position('octopus'))
            self._step(now)
            self._draw()
            self._flush_and_flip(self._sub_phase)
        return 'continue'

    # ── 상태 디스패치 ─────────────────────────────────────────────────────────

    def _step(self, now):
        dispatch = {
            'TRIAL_INIT':     self._init_trial,
            'PC_THINK':       self._pc_think,
            'CARD_FLIPPING':  self._card_flipping,
            'FEEDBACK':       self._feedback,
            'TRIAL_INTERVAL': self._trial_interval,
        }
        dispatch[self._sub_phase](now)

    def _draw(self):
        self.ui.set_pc_turn_hud(
            turn_count=self.gs.turn_count,
            target_pos=self.pc_target_pos,
            timer_label="문어 턴",
        )
        render_target = self._fb_highlighted if self._sub_phase == 'FEEDBACK' else self.pc_target_pos
        draw_game_screen(self.win, self.ui, self.board_r, self.deck_r, self.token_r,
                         self.gs, render_target)
        if self._sub_phase == 'FEEDBACK':
            self.ui.draw_feedback_message(self._fb_msg, self._fb_color)
        blink_frame_marker(self.win)

    # ── 상태 핸들러 ───────────────────────────────────────────────────────────

    def _init_trial(self, now):
        trigger_frame_marker()
        self._schedule(TRIG_TRIAL_START)
        self.deadline   = now + PC_THINK_TIME
        self._sub_phase = 'PC_THINK'

    def _pc_think(self, now):
        if now < self.deadline:
            return

        self.trial_id = self.gs.get_next_trial_id()
        was_seq = self.gs.seq_memory_active

        seq_just_activated = False
        if not self._is_seq_continue:
            self.gs.try_activate_pc_seq_memory()
            if self.gs.seq_memory_active and not was_seq:
                seq_just_activated = True
                self._schedule(TRIG_SEQ_ACTIVATE)
            if self.gs.seq_memory_active:
                self.pc_target_pos = self.gs.get_seq_memory_current_target()
        self._is_seq_continue = False

        if self.aoi:
            self.aoi.current_trial_id = self.trial_id
            self.aoi.is_seq_memory    = self.gs.seq_memory_active
            self.aoi.seq_memory_step  = self.gs.seq_memory_step if self.gs.seq_memory_active else None

        seq_tag = (f" SEQ_MEMORY step {self.gs.seq_memory_step}/{len(self.gs.seq_memory_targets)}"
                   if self.gs.seq_memory_active else "")
        self._edf(f"TRIAL_START {self.trial_id} PC"
                  f" ROUND {self.gs.current_round} TURN {self.gs.turn_count}{seq_tag}")
        self.gs.current_trial_start_psychopy = core.getTime()

        self._checked_as_seq = self.gs.seq_memory_active
        if self._checked_as_seq:
            self.result, self.card_pos = self.gs.check_pc_seq_memory_card()
        else:
            self.result, self.card_pos = self.gs.pc_turn_step(defer_success_move=True)

        self._save_trial()
        sound_play(self.sounds, 'npc_flip')
        trigger_frame_marker()
        if not seq_just_activated:
            self._schedule(TRIG_CARD_FLIP_PC)
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
        
        if self.card_pos:
            self.gs.deck.hide_card(self.card_pos[0], self.card_pos[1])
        self.trial_id = self.gs.get_next_trial_id()
        if self.aoi:
            self.aoi.current_trial_id = self.trial_id
            self.aoi.is_seq_memory    = True
            self.aoi.seq_memory_step  = self.gs.seq_memory_step

        self._edf(f"TRIAL_START {self.trial_id} PC"
                  f" ROUND {self.gs.current_round} TURN {self.gs.turn_count}"
                  f" SEQ_MEMORY step {step_now}/{step_total}")
        self.gs.current_trial_start_psychopy = core.getTime()
        self.pc_target_pos    = self.gs.get_seq_memory_current_target()
        self._schedule(TRIG_TRIAL_START)
        self._is_seq_continue = True
        self.deadline   = now + PC_THINK_TIME
        self._sub_phase = 'PC_THINK'

    def _set_success_feedback(self, now):
        sound_play(self.sounds, 'correct')
        if self.result == 'all_success':
            n = len(self.gs.seq_memory_targets)
            msg, color, code = f"문어 순차 {n}칸 완료!", GOLD, TRIG_SEQ_ALL_SUCCESS
        else:
            msg, color, code = "문어 성공", PURPLE, 0
        self._fb_msg, self._fb_color, self._fb_code = msg, color, code
        self._fb_success     = True
        self._fb_highlighted = self.pc_target_pos
        self._schedule(code)
        self.deadline   = now + FEEDBACK_DURATION
        self._sub_phase = 'FEEDBACK'

    def _set_failure_feedback(self, now):
        sound_play(self.sounds, 'error')
        if self._checked_as_seq:
            self._edf(f"TRIAL_END {self.trial_id} MATCH 0 RESULT seq_failure")
            msg, code = "문어 순차 실패", TRIG_SEQ_FAILURE
        else:
            self._edf(f"TRIAL_END {self.trial_id} MATCH 0 RESULT failure")
            msg, code = "문어 실패", 0
        self._fb_msg, self._fb_color, self._fb_code = msg, DARK_GREY, code
        self._fb_success     = False
        self._fb_highlighted = self.pc_target_pos
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
            move_result = self.gs.complete_pc_seq_memory_move()
            edf_result  = 'seq_all_success'
        else:
            move_result = self.gs.complete_pc_success_move()
            edf_result  = 'success'
        if self.card_pos:
            self.gs.deck.hide_card(self.card_pos[0], self.card_pos[1])

        if move_result == 'npc_caught_user':
            edf_result = 'seq_npc_caught_user' if self.result == 'all_success' else 'npc_caught_user'
            self._show_catch_feedback(
                f"잡혔다!  {SCORE_CAUGHT_PENALTY}점", ORANGE_RED, 'lose', edf_result)
            self.gs.end_pc_turn()
            run_round_break(self.win, self.ui, self.board_r, self.deck_r, self.token_r,
                            self.gs, fdl=self.fdl)
            return  # while 조건(current_turn)이 바뀌어 루프 종료

        self._edf(f"TRIAL_END {self.trial_id} MATCH 1 RESULT {edf_result}")
        self._trigger(TRIG_TRIAL_END)
        self.deadline   = now + TRIAL_INTERVAL
        self._sub_phase = 'TRIAL_INTERVAL'

    def _on_failure(self):
        if self.card_pos:
            self.gs.deck.hide_card(self.card_pos[0], self.card_pos[1])
        self._trigger(TRIG_TRIAL_END)
        self.gs.end_pc_turn()  # 턴 종료 → while 조건(current_turn)이 바뀌어 루프 종료

    def _trial_interval(self, now):
        if now >= self.deadline:
            self._sub_phase = 'TRIAL_INIT'
