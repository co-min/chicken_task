"""
턴 실행 엔진 — GameState의 back-reference(self.gs)를 통해 상태에 접근한다.
사용자/PC 카드 선택, 이동, 순차 메모리, 잡기 이벤트, 턴 전환을 담당한다.
"""
import time
import weakref
import sys
from pathlib import Path

try:
    from utils.card_matcher import check_match
    from ..config import SCORE_CATCH_BONUS, SCORE_CAUGHT_PENALTY, SCORE_PC_CATCH_BONUS
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from utils.card_matcher import check_match
    from config import SCORE_CATCH_BONUS, SCORE_CAUGHT_PENALTY, SCORE_PC_CATCH_BONUS


class TurnExecutor:
    """GameState를 대신해 턴 실행 로직을 처리한다."""

    def __init__(self, gs):
        self._gs_ref = weakref.ref(gs)

    @property
    def gs(self):
        ref = self._gs_ref()
        if ref is None:
            raise RuntimeError("TurnExecutor: GameState has been garbage collected")
        return ref

    # ── 내부 헬퍼 ────────────────────────────────────────────────────────────

    def _snapshot(self):
        gs = self.gs
        all_pos  = gs.tokens.get_all_positions()
        user_pos = all_pos.get(gs.selected_token) if gs.selected_token else None
        return user_pos, all_pos.get('octopus')

    def _is_npc_steal(self, card):
        gs  = self.gs
        pos = gs.tokens.get_target_position('octopus')
        return pos is not None and check_match(gs.board.get_condition(pos[0], pos[1]), card)

    def _is_pc_steal(self, card):
        gs = self.gs
        if not gs.selected_token:
            return False
        pos = gs.tokens.get_target_position(gs.selected_token)
        return pos is not None and check_match(gs.board.get_condition(pos[0], pos[1]), card)

    def _is_double(self, target_pos):
        if target_pos is None:
            return False
        condition = self.gs.board.get_condition(target_pos[0], target_pos[1])
        return bool(condition and condition.get('bonus') == 'double_score')

    def _record_trial(self, token, target_pos, condition, card_pos, card,
                      is_match, result_type, elapsed, user_pos, pc_pos, **extra):
        gs = self.gs
        gs.trial_history.append({
            'trial_id':           gs.trial_id,
            'round':              gs.current_round,
            'turn':               gs.turn_count,
            'token':              token,
            'target_pos':         target_pos,
            'condition':          condition,
            'selected_card_pos':  card_pos,
            'selected_card':      card,
            'is_match':           is_match,
            'result_type':        result_type,
            'elapsed_time':       elapsed,
            'timestamp':          time.time(),
            'trial_start_time':   gs.current_trial_start_psychopy,
            'user_token_pos':     user_pos,
            'pc_token_pos':       pc_pos,
            'seq_memory_targets': None,
            'user_combo':         gs.score.user_combo,
            'npc_success_rate':   gs.npc_ai.success_rate,
            **extra,
        })

    def _npc_context(self, condition):
        gs  = self.gs
        ctx = gs.adaptive.build_memory_context(gs.turn_count)
        ctx['recent_user_hint_pos']  = gs.adaptive.get_hint_pos(condition, gs.trial_history)
        ctx['recent_npc_failed_pos'] = gs.adaptive.get_npc_failed_pos(gs.trial_history)
        ctx['known_wrong_positions'] = gs.adaptive.get_known_wrong(condition)
        return ctx

    def _flight_directly_behind_chase(self):
        gs         = self.gs
        flight_pos = gs.tokens.get_token('flight').get_position()
        chase_pos  = gs.tokens.get_token('chase').get_position()
        return gs.tokens.get_next_position(flight_pos) == chase_pos

    # ── 사용자 턴 ─────────────────────────────────────────────────────────────

    def user_click_card(self, card_row, card_col, defer_success_move=False):
        gs = self.gs
        if gs.phase != gs.PHASE_GAME_PLAY or gs.current_turn != gs.TURN_USER:
            return 'error'
        if gs.timer.is_expired():
            print("시간 초과!")
            self.end_user_turn()
            return 'timeout'

        elapsed          = gs.timer.get_elapsed()
        user_pos, pc_pos = self._snapshot()
        gs.deck.flip_card(card_row, card_col)
        card      = gs.deck.get_card(card_row, card_col)
        condition = gs.get_target_condition()
        is_match  = check_match(condition, card)

        self._record_trial(gs.selected_token, gs.get_target_position(), condition,
                           (card_row, card_col), card, is_match,
                           'success' if is_match else 'failure', elapsed, user_pos, pc_pos)
        gs.adaptive.record_user((card_row, card_col), card, is_match, gs.turn_count)

        if is_match:
            score = gs.score.add_user_match(elapsed, self._is_npc_steal(card),
                                             self._is_double(gs.get_target_position()))
            # print(f"성공! +{score}점 (콤보:{gs.score.user_combo}) → 누적:{gs.score.user_score}")
            return 'success' if defer_success_move else self.complete_user_success_move()
        else:
            gs.score.add_user_penalty()
            # print(f"실패! → 누적:{gs.score.user_score}")
            if not defer_success_move:
                self.end_user_turn()
            return 'failure'

    def complete_user_success_move(self):
        gs = self.gs
        if gs.selected_token is None:
            return 'error'
        moved      = gs.selected_token
        two_overtake = moved == 'chase' and gs.tokens.has_two_consecutive_obstacles('chase')
        target_pos = gs.get_target_position()
        is_conj    = (gs.board.get_condition(target_pos[0], target_pos[1]) or {}).get('type') == 'conjunctive'

        gs.tokens.move_token(moved, target_pos)
        gs.user_move_count += 1
        if is_conj:
            extra = gs.tokens.get_target_position(moved)
            gs.tokens.move_token(moved, extra)
            gs.user_move_count += 1
            print(f"[CONJUNCTIVE] 보너스 이동! {moved} → {extra}")

        if result := self.check_catch_event():
            return result
        if two_overtake:
            # print("[추월 승리] chase → octopus 추월! 승리!")
            return self._handle_user_caught_npc()
        if moved == 'flight' and self._flight_directly_behind_chase():
            gs.selected_token       = 'chase'
            gs.seq_mem.skip_on_switch = True
            # print("[전환] flight → chase로 선택 토큰 전환")
            return 'token_switched'
        return 'success'

    # ── 순차 메모리 (사용자) ──────────────────────────────────────────────────

    def check_seq_memory_card(self, card_row, card_col) -> str:
        gs     = self.gs
        target = gs.seq_mem.current_target
        if target is None:
            gs.seq_mem.deactivate()
            self.end_user_turn()
            return 'failure'

        condition        = gs.board.get_condition(*target)
        elapsed          = gs.timer.get_elapsed()
        user_pos, pc_pos = self._snapshot()
        gs.deck.flip_card(card_row, card_col)
        card             = gs.deck.get_card(card_row, card_col)
        is_match         = check_match(condition, card)
        step, total      = gs.seq_mem.step, len(gs.seq_mem.targets)
        rtype = 'seq_failure' if not is_match else ('seq_all_success' if step + 1 >= total else 'seq_step_success')

        self._record_trial(gs.selected_token, target, condition, (card_row, card_col), card,
                           is_match, rtype, elapsed, user_pos, pc_pos,
                           seq_memory_step=step, seq_memory_total=total,
                           seq_memory_targets=list(gs.seq_mem.targets))
        gs.adaptive.record_user((card_row, card_col), card, is_match, gs.turn_count)

        if not is_match:
            gs.score.add_user_penalty()
            gs.seq_mem.deactivate()
            return 'failure'

        gs.score.add_user_match(elapsed, is_steal=False, is_double_score=self._is_double(target))
        return 'all_success' if gs.seq_mem.advance() else 'step_success'

    def complete_seq_memory_move(self) -> str:
        gs = self.gs
        if not gs.seq_mem.targets:
            gs.seq_mem.deactivate()
            return 'success'
        final_pos, steps, moved = gs.seq_mem.targets[-1], len(gs.seq_mem.targets), gs.selected_token
        gs.tokens.move_token(moved, final_pos)
        gs.user_move_count += steps
        gs.seq_mem.deactivate()
        # print(f"[SEQ MEMORY] {moved} {steps}칸 점프 → {final_pos}")

        if result := self.check_catch_event():
            return result
        if moved == 'flight' and self._flight_directly_behind_chase():
            gs.selected_token       = 'chase'
            gs.seq_mem.skip_on_switch = True
            return 'token_switched'
        return 'success'

    # ── PC 턴 ─────────────────────────────────────────────────────────────────

    def pc_turn_step(self, defer_success_move=False):
        gs = self.gs
        if gs.current_turn != gs.TURN_PC:
            return ('error', None)

        target_pos           = gs.tokens.get_target_position('octopus')
        condition            = gs.board.get_condition(target_pos[0], target_pos[1])
        selected_pos, is_match = gs.npc_ai.select_card(
            gs.deck, condition, memory_context=self._npc_context(condition)
        )

        user_pos, pc_pos = self._snapshot()
        gs.deck.flip_card(selected_pos[0], selected_pos[1])
        card = gs.deck.get_card(selected_pos[0], selected_pos[1])

        self._record_trial('octopus', target_pos, condition, selected_pos, card,
                           is_match, 'success' if is_match else 'failure', 0, user_pos, pc_pos)
        gs.adaptive.record_npc(selected_pos, card, gs.turn_count)

        if is_match:
            score = gs.score.add_pc_match(self._is_pc_steal(card), self._is_double(target_pos))
            print(f"PC 성공! +{score}점 → 누적:{gs.score.pc_score}")
            return ('success', selected_pos) if defer_success_move else (self.complete_pc_success_move(), selected_pos)
        else:
            gs.score.add_pc_penalty()
            if not defer_success_move:
                self.end_pc_turn()
            return ('failure', selected_pos)

    def complete_pc_success_move(self):
        gs         = self.gs
        target_pos = gs.tokens.get_target_position('octopus')
        is_conj    = (gs.board.get_condition(target_pos[0], target_pos[1]) or {}).get('type') == 'conjunctive'
        gs.tokens.move_token('octopus', target_pos)
        gs.pc_move_count += 1
        if is_conj:
            extra = gs.tokens.get_target_position('octopus')
            gs.tokens.move_token('octopus', extra)
            gs.pc_move_count += 1
            print(f"[CONJUNCTIVE] PC 보너스 이동! octopus → {extra}")
        result = self.check_catch_event()
        return result if result else 'success'

    def check_pc_seq_memory_card(self) -> tuple:
        gs     = self.gs
        target = gs.seq_mem.current_target
        if target is None:
            gs.seq_mem.deactivate()
            self.end_pc_turn()
            return ('failure', None)

        condition            = gs.board.get_condition(*target)
        selected_pos, is_match = gs.npc_ai.select_card(
            gs.deck, condition, memory_context=self._npc_context(condition)
        )

        user_pos, pc_pos = self._snapshot()
        gs.deck.flip_card(selected_pos[0], selected_pos[1])
        card        = gs.deck.get_card(selected_pos[0], selected_pos[1])
        step, total = gs.seq_mem.step, len(gs.seq_mem.targets)
        rtype = 'seq_failure' if not is_match else ('seq_all_success' if step + 1 >= total else 'seq_step_success')

        self._record_trial('octopus', target, condition, selected_pos, card,
                           is_match, rtype, 0, user_pos, pc_pos,
                           seq_memory_step=step, seq_memory_total=total,
                           seq_memory_targets=list(gs.seq_mem.targets))
        gs.adaptive.record_npc(selected_pos, card, gs.turn_count)

        if not is_match:
            gs.score.add_pc_penalty()
            gs.seq_mem.deactivate()
            return ('failure', selected_pos)

        gs.score.add_pc_match(is_double_score=self._is_double(target))
        return (('all_success' if gs.seq_mem.advance() else 'step_success'), selected_pos)

    def complete_pc_seq_memory_move(self) -> str:
        gs = self.gs
        if not gs.seq_mem.targets:
            gs.seq_mem.deactivate()
            return 'success'
        final_pos, steps = gs.seq_mem.targets[-1], len(gs.seq_mem.targets)
        gs.tokens.move_token('octopus', final_pos)
        gs.pc_move_count += steps
        gs.seq_mem.deactivate()
        print(f"[SEQ MEMORY] octopus {steps}칸 점프 → {final_pos}")
        result = self.check_catch_event()
        return result if result else 'success'

    # ── 턴 전환 ───────────────────────────────────────────────────────────────

    def end_user_turn(self):
        gs = self.gs
        gs.timer.stop()
        gs.seq_mem.deactivate()
        gs.seq_mem.skip_on_switch = False
        gs.current_turn   = gs.TURN_PC
        gs.phase          = gs.PHASE_GAME_PLAY
        gs.selected_token = None
        pos = gs.tokens.get_target_position('octopus')
        if pos is not None:
            gs.adaptive.update_npc_rate(
                gs.npc_ai, gs.board.get_condition(pos[0], pos[1]), gs.trial_history,
            )
        print("사용자 턴 종료. PC 차례")

    def end_pc_turn(self):
        gs = self.gs
        gs.seq_mem.deactivate()
        gs.current_turn   = gs.TURN_USER
        gs.phase          = gs.PHASE_TOKEN_SELECTION
        gs.selected_token = None
        gs.turn_count    += 1
        print(f"PC 턴 종료. 사용자 차례 (턴 {gs.turn_count})")

    # ── 잡기 이벤트 ───────────────────────────────────────────────────────────

    def check_catch_event(self):
        gs = self.gs
        if gs.tokens.check_victory():
            return self._handle_user_caught_npc()
        if gs.tokens.check_defeat():
            return self._handle_npc_caught_user()
        return None

    def _handle_user_caught_npc(self):
        gs = self.gs
        gs.score.apply_user_catch()
        gs._append_round_event('user_catch', note=f'user_catch_count={gs.score.user_catch_count}')
        gs._reset_round_board_state()
        # print(f"[잡기] 사용자가 문어를 잡음! +{SCORE_CATCH_BONUS}점 | 누적:{gs.score.user_score}")
        return 'user_caught_npc'

    def _handle_npc_caught_user(self):
        gs = self.gs
        gs.score.apply_npc_catch()
        gs._append_round_event('npc_catch', note=f'pc_catch_count={gs.score.pc_catch_count}')
        gs._reset_round_board_state()
        # print(f"[잡기] 문어가 flight를 잡음! | 유저:{gs.score.user_score} | PC:{gs.score.pc_score}")
        return 'npc_caught_user'
