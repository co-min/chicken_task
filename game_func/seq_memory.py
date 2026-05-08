import random
import sys
from pathlib import Path

from ..config import (
        SEQ_MEMORY_SCORE_THRESHOLD, SEQ_MEMORY_PC_THRESHOLD,
        SEQ_MEMORY_TRIGGER_PROB, SEQ_MEMORY_MIN_STEPS, SEQ_MEMORY_MAX_STEPS,
        )


class SeqMemory:
    def __init__(self):
        self.active = False
        self.targets = []
        self.step = 0
        self.is_pc = False
        self.skip_on_switch = False

    @property
    def current_target(self):
        if not self.active or self.step >= len(self.targets):
            return None
        return self.targets[self.step]

    def deactivate(self):
        self.active = False
        self.targets = []
        self.step = 0
        self.is_pc = False

    def advance(self):
        self.step += 1
        return self.step >= len(self.targets)

    def _compute_targets(self, token_name, n_steps, tokens):
        all_pos = tokens.get_all_positions()
        occupied = {pos for name, pos in all_pos.items() if name != token_name}
        token = tokens.get_token(token_name)

        if not token:
            return []
        targets = []
        pos = tokens.get_next_position(token.get_position())

        while pos is not None and len(targets) < n_steps:
            if pos in occupied:
                next_pos = tokens.get_next_position(pos)
                if next_pos is not None and next_pos not in occupied:
                    targets.append(next_pos)
                break
            targets.append(pos)
            pos = tokens.get_next_position(pos)

        return targets

    def try_activate_user(self, round_score, selected_token, tokens):
        if self.active:
            return True
        if self.skip_on_switch:
            self.skip_on_switch = False
            print("[SEQ MEMORY] token_switched 직후 → 이번 시도 발동 억제")
            return False
        if round_score < SEQ_MEMORY_SCORE_THRESHOLD or random.random() >= SEQ_MEMORY_TRIGGER_PROB:
            return False
        if selected_token is None:
            return False
        n = random.randint(SEQ_MEMORY_MIN_STEPS, SEQ_MEMORY_MAX_STEPS)
        targets = self._compute_targets(selected_token, n, tokens)
        if len(targets) < 2:
            return False
        self.targets = targets
        self.step = 0
        self.active = True
        self.is_pc = False
        # print(f"[SEQ MEMORY] 사용자 발동! {len(targets)}칸 순차 타겟: {targets}")
        return True

    def summarize_trials(self, trial_history: list) -> dict:
        """Aggregate sequential-memory statistics from trial_history."""
        seq_trials = [t for t in trial_history if t.get('seq_memory_step') is not None]
        user_seq   = [t for t in seq_trials if t.get('token') != 'octopus']
        pc_seq     = [t for t in seq_trials if t.get('token') == 'octopus']

        def _activations(trials):
            return sum(1 for t in trials if t.get('seq_memory_step', -1) == 0)

        def _all_success(trials):
            return sum(
                1 for t in trials
                if t.get('is_match') and
                   t.get('seq_memory_step', -1) == (t.get('seq_memory_total', 0) - 1)
            )

        def _step_fail(trials):
            return sum(1 for t in trials if not t.get('is_match'))

        return {
            'user_activations':      _activations(user_seq),
            'user_all_success':      _all_success(user_seq),
            'user_step_fail':        _step_fail(user_seq),
            'user_total_seq_trials': len(user_seq),
            'pc_activations':        _activations(pc_seq),
            'pc_all_success':        _all_success(pc_seq),
            'pc_step_fail':          _step_fail(pc_seq),
            'pc_total_seq_trials':   len(pc_seq),
        }

    def try_activate_pc(self, pc_round_score, tokens):
        if self.active:
            return True
        if pc_round_score < SEQ_MEMORY_PC_THRESHOLD or random.random() >= SEQ_MEMORY_TRIGGER_PROB:
            return False
        n = random.randint(SEQ_MEMORY_MIN_STEPS, SEQ_MEMORY_MAX_STEPS)
        targets = self._compute_targets('octopus', n, tokens)
        if len(targets) < 2:
            return False
        self.targets = targets
        self.step = 0
        self.active = True
        self.is_pc = True
        # print(f"[SEQ MEMORY] PC 발동! {len(targets)}칸 순차 타겟: {targets}")
        return True
