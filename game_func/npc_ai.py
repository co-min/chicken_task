# npc_ai.py
import random
import sys
from pathlib import Path

try:
    from ..utils.card_matcher import check_match
    from ..utils.helpers import clamp
    from ..config import (PC_SUCCESS_RATE,
                          NPC_REFERENCE_MIN_PROB, NPC_REFERENCE_MAX_PROB, NPC_REFERENCE_BASE_PROB,
                          NPC_HINT_FOLLOW_PROB)
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from utils.card_matcher import check_match
    from utils.helpers import clamp
    from config import (PC_SUCCESS_RATE,
                        NPC_REFERENCE_MIN_PROB, NPC_REFERENCE_MAX_PROB, NPC_REFERENCE_BASE_PROB,
                        NPC_HINT_FOLLOW_PROB)


class NPCAI:

    def __init__(self, success_rate=PC_SUCCESS_RATE):
        """
        NPC AI 초기화

        Args:
            success_rate (float): 정답 확률 (0.0 ~ 1.0, 기본값 1/deck)
        """
        self.success_rate        = clamp(success_rate, 0.0, 1.0)
        self.reference_min_prob  = NPC_REFERENCE_MIN_PROB
        self.reference_max_prob  = NPC_REFERENCE_MAX_PROB
        self.reference_base_prob = NPC_REFERENCE_BASE_PROB
        self.hint_follow_prob    = NPC_HINT_FOLLOW_PROB

    def set_success_rate(self, success_rate):
        # game_state에서 호출
        self.success_rate = clamp(success_rate, 0.0, 1.0)

    def select_card(self, deck, condition, memory_context=None):
        should_succeed = random.random() < self.success_rate

        avoid_positions = set() # 직전 실패 위치 회피
        if memory_context and not should_succeed:
            recent_failed_pos = memory_context.get('recent_npc_failed_pos')
            if recent_failed_pos is not None:
                avoid_positions.add(tuple(recent_failed_pos))

        matching_cards = self._find_cards_by_match(deck, condition, match=should_succeed)
        filtered_matching_cards = self._filter_positions(matching_cards, avoid_positions)
        if filtered_matching_cards:
            matching_cards = filtered_matching_cards

        # 직전 사용자 카드가 현재 타겟 정답이면 성공 모드에서 우선 참고
        if memory_context and should_succeed:
            hint_pos = memory_context.get('recent_user_hint_pos')
            if hint_pos and hint_pos in matching_cards and random.random() < self.hint_follow_prob:
                return (hint_pos, True)

        # 메모리 기반 후보와 랜덤 후보를 혼합 선택
        if memory_context and matching_cards:
            memory_candidates = self._find_memory_candidates(
                memory_context,
                condition,
                match=should_succeed,
            )
            if avoid_positions:
                memory_candidates = [
                    c for c in memory_candidates
                    if c['pos'] not in avoid_positions
                ]
            if memory_candidates:
                reference_prob = self._estimate_reference_probability(memory_candidates)
                if not should_succeed:
                    reference_prob = min(reference_prob, 0.4)
                card_pos = self._choose_mixed_candidate(
                    memory_candidates,
                    matching_cards,
                    reference_prob,
                )
                selected_card = deck.get_card(card_pos[0], card_pos[1])
                actual_match = check_match(condition, selected_card)
                return (card_pos, actual_match)

        if matching_cards:
            card_pos = random.choice(matching_cards)
            actual_match = should_succeed
        else:
            card_pos = self._select_random_card(deck)
            fallback_card = deck.get_card(card_pos[0], card_pos[1])
            actual_match = check_match(condition, fallback_card)

        return (card_pos, actual_match)

    def _filter_positions(self, positions, avoid_positions):
        """회피해야 할 위치를 제외한 후보 목록 반환."""
        if not avoid_positions:
            return positions
        return [pos for pos in positions if pos not in avoid_positions]

    def _estimate_reference_probability(self, memory_candidates):
        """
        메모리 후보 품질에 따라 참고 비율 계산.
        - 사용자 관찰만 있는 정보는 덜 신뢰
        - npc/both 정보 비중이 높을수록 참고 비율 상승
        """
        if not memory_candidates:
            return self.reference_min_prob

        avg_weight = sum(c['weight'] for c in memory_candidates) / len(memory_candidates)
        npc_like_ratio = (
            sum(1 for c in memory_candidates if c.get('source') in ('npc', 'both'))
            / len(memory_candidates)
        )

        reference_prob = (
            self.reference_base_prob
            + 0.20 * (avg_weight - 0.5)
            + 0.15 * (npc_like_ratio - 0.5)
        )
        return clamp(reference_prob, self.reference_min_prob, self.reference_max_prob)

    def _choose_mixed_candidate(self, memory_candidates, all_candidates, reference_prob):
        """
        메모리 후보와 비메모리 후보를 섞어서 선택.
        """
        memory_positions = {c['pos'] for c in memory_candidates}
        non_memory_candidates = [pos for pos in all_candidates if pos not in memory_positions]

        use_reference = random.random() < reference_prob
        if use_reference or not non_memory_candidates:
            return self._weighted_choice(memory_candidates)
        return random.choice(non_memory_candidates)

    def _find_memory_candidates(self, memory_context, condition, match=True):
        entries = memory_context.get('entries', [])
        current_turn = memory_context.get('current_turn', 0)
        recency_window = max(1, int(memory_context.get('recency_window', 6)))

        candidates = []
        for entry in entries:
            card = entry.get('card')
            if card is None:
                continue

            is_match = check_match(condition, card)
            if is_match != match:
                continue

            confidence = clamp(entry.get('confidence', 0.5), 0.0, 1.0)
            last_seen_turn = int(entry.get('last_seen_turn', current_turn))
            age = max(0, current_turn - last_seen_turn)
            recency = max(0.0, 1.0 - (age / recency_window))
            seen_count = max(1, int(entry.get('seen_count', 1)))
            seen_bonus = min(1.0, seen_count / 3.0)

            weight = (0.55 * confidence) + (0.35 * recency) + (0.1 * seen_bonus)
            if weight > 0.0:
                candidates.append({
                    'pos': entry['pos'],
                    'weight': weight,
                    'source': entry.get('source', 'user'),
                })

        return candidates

    def _weighted_choice(self, candidates):
        """가중치 기반 랜덤 선택 (사람 같은 비결정성 유지)."""
        total = sum(c['weight'] for c in candidates)
        if total <= 0:
            return random.choice(candidates)['pos']

        pick = random.random() * total
        upto = 0.0
        for candidate in candidates:
            upto += candidate['weight']
            if upto >= pick:
                return candidate['pos']
        return candidates[-1]['pos']
    
    def _find_cards_by_match(self, deck, condition, match=True):
        cards = []
        
        for row in range(deck.rows):
            for col in range(deck.cols):
                card = deck.get_card(row, col)
                is_match = check_match(condition, card)
                
                # match 파라미터에 따라 조건 판단
                if is_match == match:
                    cards.append((row, col))
        
        return cards
    
    def _select_random_card(self, deck):
        row = random.randint(0, deck.rows - 1)
        col = random.randint(0, deck.cols - 1)
        return (row, col)



