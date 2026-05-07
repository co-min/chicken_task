import sys
from pathlib import Path

try:
    from utils.helpers import clamp
    from utils.card_matcher import check_match
    from ..config import (
        USER_WINDOW_SIZE, MIN_USER_TRIALS_FOR_ADAPT, USER_EWMA_ALPHA,
        KNOWLEDGE_EXIST_W, KNOWLEDGE_DENSITY_W,
        SKILL_EWMA_W, SKILL_RECENT_W, SKILL_SPEED_W,
        ESTIMATED_SKILL_W, ESTIMATED_KNOWLEDGE_W, ESTIMATED_NOVELTY_W,
        SURGE_BASE_W, SURGE_SPEED_W, SURGE_CONSECUTIVE_BONUS,
        MISS_PENALTY_PER_STREAK, MISS_PENALTY_MAX_STREAK,
        MEMORY_CONFIDENCE_INIT, MEMORY_CONFIDENCE_INCREMENT,
        TURN_TIME_LIMIT, NPC_EDGE_OVER_USER,
        ADAPTIVE_ALPHA_UP, ADAPTIVE_ALPHA_DOWN,
        MAX_RATE_STEP_UP, MAX_RATE_STEP_DOWN, SURGE_BONUS_SCALE, NPC_RATE_MAX,
    )
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from utils.helpers import clamp
    from utils.card_matcher import check_match
    from config import (
        USER_WINDOW_SIZE, MIN_USER_TRIALS_FOR_ADAPT, USER_EWMA_ALPHA,
        KNOWLEDGE_EXIST_W, KNOWLEDGE_DENSITY_W,
        SKILL_EWMA_W, SKILL_RECENT_W, SKILL_SPEED_W,
        ESTIMATED_SKILL_W, ESTIMATED_KNOWLEDGE_W, ESTIMATED_NOVELTY_W,
        SURGE_BASE_W, SURGE_SPEED_W, SURGE_CONSECUTIVE_BONUS,
        MISS_PENALTY_PER_STREAK, MISS_PENALTY_MAX_STREAK,
        MEMORY_CONFIDENCE_INIT, MEMORY_CONFIDENCE_INCREMENT,
        TURN_TIME_LIMIT, NPC_EDGE_OVER_USER,
        ADAPTIVE_ALPHA_UP, ADAPTIVE_ALPHA_DOWN,
        MAX_RATE_STEP_UP, MAX_RATE_STEP_DOWN, SURGE_BONUS_SCALE, NPC_RATE_MAX,
    )


class AdaptiveSystem:
    """사용자 수행 추적 및 NPC 난이도 적응 시스템."""

    def __init__(self, base_random_rate):
        self.base_random_rate = base_random_rate
        self.npc_rate_min = base_random_rate
        self.npc_rate_max = NPC_RATE_MAX
        self.user_accuracy_ewma = base_random_rate
        self.user_seen_cards = {}   # {pos: {card, seen_count, last_seen_turn, confidence}}
        self.npc_seen_cards = {}
        self.user_choice_count = 0
        self.user_repeat_count = 0
        self.user_last_selected_pos = None

    # ── 관찰 기록 ─────────────────────────────────────────────────────────────

    def record_user(self, pos, card, is_match, turn_count):
        self.user_choice_count += 1
        if self.user_last_selected_pos == pos:
            self.user_repeat_count += 1
        self.user_last_selected_pos = pos
        self._record(self.user_seen_cards, pos, card, turn_count)
        self.user_accuracy_ewma = (
            (1 - USER_EWMA_ALPHA) * self.user_accuracy_ewma + USER_EWMA_ALPHA * (1.0 if is_match else 0.0)
        )

    def record_npc(self, pos, card, turn_count):
        self._record(self.npc_seen_cards, pos, card, turn_count)

    def _record(self, store, pos, card, turn_count):
        info = store.get(pos)
        if info is None:
            store[pos] = {'card': card, 'seen_count': 1,
                          'last_seen_turn': turn_count, 'confidence': MEMORY_CONFIDENCE_INIT}
            return
        info['card'] = card
        info['seen_count'] += 1
        info['last_seen_turn'] = turn_count
        info['confidence'] = clamp(info['confidence'] + MEMORY_CONFIDENCE_INCREMENT, 0.0, 1.0)

    # ── NPC 메모리 컨텍스트 ───────────────────────────────────────────────────

    def build_memory_context(self, turn_count):
        merged = {}
        for source, store in (('user', self.user_seen_cards), ('npc', self.npc_seen_cards)):
            for pos, info in store.items():
                entry = merged.get(pos)
                if entry is None:
                    merged[pos] = {
                        'pos': pos, 'card': info.get('card'),
                        'confidence': float(info.get('confidence', MEMORY_CONFIDENCE_INIT)),
                        'seen_count': int(info.get('seen_count', 1)),
                        'last_seen_turn': int(info.get('last_seen_turn', turn_count)),
                        'source': source,
                    }
                    continue
                entry['card'] = info.get('card', entry['card'])
                entry['confidence'] = max(entry['confidence'],
                                          float(info.get('confidence', MEMORY_CONFIDENCE_INIT)))
                entry['seen_count'] += int(info.get('seen_count', 1))
                entry['last_seen_turn'] = max(entry['last_seen_turn'],
                                              int(info.get('last_seen_turn', turn_count)))
                if entry['source'] != source:
                    entry['source'] = 'both'
        return {'entries': list(merged.values()), 'current_turn': turn_count, 'recency_window': 6}

    def get_hint_pos(self, condition, trial_history):
        """직전 사용자 카드가 현재 조건 정답이면 해당 위치 반환."""
        for trial in reversed(trial_history):
            if trial.get('token') not in ('chase', 'flight'):
                continue
            card = trial.get('selected_card')
            if card is None:
                return None
            return trial.get('selected_card_pos') if check_match(condition, card) else None
        return None

    def get_npc_failed_pos(self, trial_history):
        for trial in reversed(trial_history):
            if trial.get('token') != 'octopus':
                continue
            return None if trial.get('is_match') else trial.get('selected_card_pos')
        return None

    def get_known_wrong(self, condition):
        wrong = set()
        for store in (self.user_seen_cards, self.npc_seen_cards):
            for pos, info in store.items():
                card = info.get('card')
                if card and not check_match(condition, card):
                    wrong.add(pos)
        return list(wrong)

    # ── 사용자 성공 확률 추정 ─────────────────────────────────────────────────

    def _recent_user_trials(self, trial_history):
        trials = [t for t in trial_history if t.get('token') in ('chase', 'flight')]
        return trials[-USER_WINDOW_SIZE:]

    def _knowledge_score(self, condition):
        if condition is None or not self.user_seen_cards:
            return 0.0
        total = len(self.user_seen_cards)
        matches = sum(1 for info in self.user_seen_cards.values()
                      if check_match(condition, info['card']))
        return clamp(
            KNOWLEDGE_EXIST_W * (1.0 if matches > 0 else 0.0) + KNOWLEDGE_DENSITY_W * (matches / total),
            0.0, 1.0,
        )

    def _miss_streak(self, trial_history):
        streak = 0
        for t in reversed(self._recent_user_trials(trial_history)):
            if t.get('is_match'):
                break
            streak += 1
        return streak

    def estimate_user_prob(self, condition, trial_history):
        recent = self._recent_user_trials(trial_history)
        if len(recent) < MIN_USER_TRIALS_FOR_ADAPT:
            return self.base_random_rate

        recent_acc = sum(1 for t in recent if t.get('is_match')) / len(recent)
        mean_elapsed = sum(t.get('elapsed_time', TURN_TIME_LIMIT) for t in recent) / len(recent)
        speed = clamp(1.0 - mean_elapsed / TURN_TIME_LIMIT, 0.0, 1.0)
        skill = SKILL_EWMA_W * self.user_accuracy_ewma + SKILL_RECENT_W * recent_acc + SKILL_SPEED_W * speed
        knowledge = self._knowledge_score(condition)
        novelty = 1.0 - (self.user_repeat_count / self.user_choice_count
                         if self.user_choice_count > 0 else 0.0)
        miss_penalty = MISS_PENALTY_PER_STREAK * min(self._miss_streak(trial_history),
                                                      MISS_PENALTY_MAX_STREAK)

        surge = 0.0
        last = next((t for t in reversed(trial_history)
                     if t.get('token') in ('chase', 'flight')), None)
        if last and last.get('is_match'):
            last_speed = clamp(1.0 - last.get('elapsed_time', TURN_TIME_LIMIT) / TURN_TIME_LIMIT,
                               0.0, 1.0)
            surge += SURGE_BONUS_SCALE * (SURGE_BASE_W + SURGE_SPEED_W * last_speed)
            if len(recent) >= 2 and recent[-2].get('is_match'):
                surge += SURGE_CONSECUTIVE_BONUS

        estimated = (ESTIMATED_SKILL_W * skill + ESTIMATED_KNOWLEDGE_W * knowledge
                     + ESTIMATED_NOVELTY_W * novelty + surge - miss_penalty)
        return clamp(estimated, self.npc_rate_min, self.npc_rate_max)

    def update_npc_rate(self, npc_ai, condition, trial_history):
        target = clamp(
            self.estimate_user_prob(condition, trial_history) + NPC_EDGE_OVER_USER,
            self.npc_rate_min, self.npc_rate_max,
        )
        current = npc_ai.success_rate
        alpha = ADAPTIVE_ALPHA_UP if target >= current else ADAPTIVE_ALPHA_DOWN
        max_step = MAX_RATE_STEP_UP if target >= current else MAX_RATE_STEP_DOWN
        delta = clamp((1 - alpha) * current + alpha * target - current, -max_step, max_step)
        npc_ai.set_success_rate(current + delta)

    # ── 초기화 ────────────────────────────────────────────────────────────────

    def clear(self):
        self.user_seen_cards.clear()
        self.npc_seen_cards.clear()

    def reset(self, base_random_rate=None):
        if base_random_rate is not None:
            self.base_random_rate = base_random_rate
            self.npc_rate_min = base_random_rate
        self.user_accuracy_ewma = self.base_random_rate
        self.clear()
        self.user_choice_count = 0
        self.user_repeat_count = 0
        self.user_last_selected_pos = None
