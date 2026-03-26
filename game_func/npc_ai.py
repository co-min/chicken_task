# npc_ai.py
# Chicken Task - NPC AI Module
# PC (Octopus) AI 로직 - 동적 정답률 알고리즘

import random
import sys
from pathlib import Path

try:
    from ..utils.card_matcher import check_match
    from ..config import PC_SUCCESS_RATE
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from utils.card_matcher import check_match
    from config import PC_SUCCESS_RATE


class NPCAI:
    """
    NPC (Octopus) 인공지능 클래스
    
    - 설정된 정답률로 카드 선택
    - 타겟 조건에 맞는 카드 또는 틀린 카드를 전략적으로 선택
    """
    
    def __init__(self, success_rate=PC_SUCCESS_RATE):
        """
        NPC AI 초기화
        
        Args:
            success_rate (float): 정답 확률 (0.0 ~ 1.0, 기본값 1/deck)
        """
        self.success_rate = self._clamp_rate(success_rate)
        self.last_effective_success_rate = self.success_rate
        # 메모리는 참고만 하도록 비율 제어
        self.reference_min_prob = 0.33
        self.reference_max_prob = 0.72
        self.reference_base_prob = 0.50
        self.recent_hint_follow_prob = 0.60
        self.context_blend_ratio = 0.55
        self.turn_max_rate_swing = 0.12
        self.player_parity_bias = 0.17
        self.min_edge_over_user = 0.02
        self.max_edge_over_user = 0.06

    def set_success_rate(self, success_rate, sync_effective=False):
        """
        NPC 정답 확률 동적 업데이트

        Args:
            success_rate (float): 새 정답 확률 (0.0 ~ 1.0)
            sync_effective (bool): True면 last_effective_success_rate도 동기화
        """
        self.success_rate = self._clamp_rate(success_rate)
        if sync_effective:
            self.last_effective_success_rate = self.success_rate

    def _resolve_dynamic_tuning(self, memory_context):
        """
        최근 사용자 로그 기반으로 턴별 튜닝 파라미터 계산.
        Returns:
            tuple: (blend_ratio, max_rate_swing)
        """
        blend_ratio = self.context_blend_ratio
        max_rate_swing = self.turn_max_rate_swing

        if not memory_context:
            return (blend_ratio, max_rate_swing)

        trials_count = int(memory_context.get('user_recent_trials_count', 0) or 0)
        variability = memory_context.get('user_performance_variability')
        trend_score = memory_context.get('user_trend_score')
        target_rate = memory_context.get('npc_target_success_rate')

        if trials_count < 3:
            blend_ratio -= 0.20
            max_rate_swing -= 0.03
        elif trials_count < 6:
            blend_ratio -= 0.10
            max_rate_swing -= 0.02

        if variability is not None:
            variability = self._clamp_rate(variability, 0.0, 1.0)
            # 로그 변동성이 낮을수록 사용자 수준을 더 빠르게 추종
            blend_ratio += 0.08 * (0.5 - variability)
            max_rate_swing += 0.05 * (0.5 - variability)

        if trend_score is not None:
            trend_score = self._clamp_rate(trend_score, -1.0, 1.0)
            # 최근 급상승/급하락이면 반응 속도를 조금 높임
            blend_ratio += 0.03 * trend_score
            max_rate_swing += 0.03 * abs(trend_score)

        if target_rate is not None:
            target_rate = self._clamp_rate(target_rate, 0.0, 1.0)
            distance = abs(target_rate - self.last_effective_success_rate)
            max_rate_swing += 0.25 * distance

        blend_ratio = self._clamp_rate(blend_ratio, 0.40, 0.78)
        max_rate_swing = self._clamp_rate(max_rate_swing, 0.04, 0.16)
        return (blend_ratio, max_rate_swing)

    def _resolve_effective_success_rate(self, memory_context):
        """
        이번 턴의 유효 정답률 계산.
        - game_state에서 전달한 사용자 수행 추정치가 있으면 우선 반영
        - 턴 간 급격한 점프를 제한해 체감 난이도 안정화
        """
        effective_rate = self.success_rate
        blend_ratio, max_rate_swing = self._resolve_dynamic_tuning(memory_context)
        min_rate = 0.0
        max_rate = 1.0

        if memory_context:
            min_rate = self._clamp_rate(memory_context.get('npc_rate_min', 0.0), 0.0, 1.0)
            max_rate = self._clamp_rate(memory_context.get('npc_rate_max', 1.0), min_rate, 1.0)

            target_rate = memory_context.get('npc_target_success_rate')
            if target_rate is not None:
                target_rate = self._clamp_rate(target_rate, min_rate, max_rate)
                effective_rate = (
                    (1.0 - blend_ratio) * effective_rate
                    + (blend_ratio * target_rate)
                )

            # 최근 사용자 정확도/실력값을 소폭 반영해 체감 동기화 강화
            user_skill = memory_context.get('user_skill_score')
            if user_skill is not None:
                user_skill = self._clamp_rate(user_skill, 0.0, 1.0)
                effective_rate += 0.04 * (user_skill - 0.5)

            recent_user_accuracy = memory_context.get('recent_user_accuracy')
            if recent_user_accuracy is not None:
                recent_user_accuracy = self._clamp_rate(recent_user_accuracy, 0.0, 1.0)
                effective_rate += 0.02 * (recent_user_accuracy - 0.5)

            # 사용자와 비슷하거나 약간 우위 성능을 유지하기 위한 완만한 보정
            effective_rate += self.player_parity_bias
            if target_rate is not None:
                trials_count = int(memory_context.get('user_recent_trials_count', 0) or 0)
                edge_scale = self._clamp_rate((trials_count - 3) / 8.0, 0.0, 1.0)
                edge = self.min_edge_over_user + ((self.max_edge_over_user - self.min_edge_over_user) * edge_scale)
                parity_floor = self._clamp_rate(target_rate + edge, min_rate, max_rate)
                effective_rate = max(effective_rate, parity_floor)

        # 턴마다 변동폭을 제한해 급격한 난이도 출렁임 방지
        delta = effective_rate - self.last_effective_success_rate
        if delta > max_rate_swing:
            effective_rate = self.last_effective_success_rate + max_rate_swing
        elif delta < -max_rate_swing:
            effective_rate = self.last_effective_success_rate - max_rate_swing

        effective_rate = self._clamp_rate(effective_rate, min_rate, max_rate)
        self.last_effective_success_rate = effective_rate
        return effective_rate

    def _clamp_rate(self, value, min_rate=0.0, max_rate=1.0):
        """확률 값을 안전한 범위로 제한."""
        return max(min_rate, min(max_rate, float(value)))
    
    def select_card(self, deck, condition, memory_context=None):
        """
        PC가 선택할 카드 좌표 결정
        
        Args:
            deck: MainDeck 객체
            condition: 타겟 조건 (dict: {'color', 'shape', 'number'})
            memory_context (dict or None): 문어의 관찰 메모리 컨텍스트
        
        Returns:
            tuple: (card_pos, is_match) - 선택한 카드 위치와 실제 매칭 여부
        """
        effective_rate = self._resolve_effective_success_rate(memory_context)

        # 이번 턴 유효 정답률에 따라 정답/오답 모드 결정
        should_succeed = random.random() < effective_rate

        avoid_positions = set()
        if memory_context and not should_succeed:
            recent_failed_pos = memory_context.get('recent_npc_failed_pos')
            if recent_failed_pos is not None:
                avoid_positions.add(tuple(recent_failed_pos))

        # 조건에 맞는 카드 또는 맞지 않는 카드 찾기
        matching_cards = self._find_cards_by_match(deck, condition, match=should_succeed)
        filtered_matching_cards = self._filter_positions(matching_cards, avoid_positions)
        if filtered_matching_cards:
            matching_cards = filtered_matching_cards

        # 직전 사용자 카드가 현재 타겟 정답이면, 성공 모드에서 우선 참고
        if memory_context and should_succeed:
            hint_pos = memory_context.get('recent_user_hint_pos')
            if hint_pos and hint_pos in matching_cards and random.random() < self.recent_hint_follow_prob:
                return (hint_pos, True)

        # 메모리 기반 후보는 "참고"만 하고, 항상 따르지 않도록 혼합 선택
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
                user_skill = memory_context.get('user_skill_score') if memory_context else None
                if user_skill is not None:
                    user_skill = self._clamp_rate(user_skill, 0.0, 1.0)
                    reference_prob += 0.12 * (user_skill - 0.5)
                    reference_prob = self._clamp_rate(
                        reference_prob,
                        self.reference_min_prob,
                        self.reference_max_prob,
                    )
                if not should_succeed:
                    # 실패 모드에서는 메모리 맹종을 줄이고 탐색 비중을 높임
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
            # fallback: 랜덤 선택
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
        return self._clamp_rate(reference_prob, self.reference_min_prob, self.reference_max_prob)

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
        """
        메모리에서 조건에 맞는/맞지 않는 카드 후보 추출.

        Returns:
            list: [{'pos': (row, col), 'weight': float}, ...]
        """
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

            confidence = self._clamp_rate(entry.get('confidence', 0.5), 0.0, 1.0)
            last_seen_turn = int(entry.get('last_seen_turn', current_turn))
            age = max(0, current_turn - last_seen_turn)
            recency = max(0.0, 1.0 - (age / recency_window))
            seen_count = max(1, int(entry.get('seen_count', 1)))
            seen_bonus = min(1.0, seen_count / 3.0)

            weight = (0.6 * confidence) + (0.3 * recency) + (0.1 * seen_bonus)
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
        """
        조건에 맞는/맞지 않는 카드 찾기 (통합 메서드)
        
        Args:
            deck: MainDeck 객체
            condition: 타겟 조건
            match (bool): True면 조건 맞는 카드, False면 맞지 않는 카드
        
        Returns:
            list: [(row, col), ...] 카드 위치 리스트
        """
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
        """
        랜덤 카드 선택 (fallback)
        
        Args:
            deck: MainDeck 객체
        
        Returns:
            tuple: (row, col) 랜덤 카드 위치
        """
        row = random.randint(0, deck.rows - 1)
        col = random.randint(0, deck.cols - 1)
        return (row, col)


# ==================== 테스트 코드 ====================
if __name__ == "__main__":
    print("\n### NPCAI 테스트 ###\n")
    
    # 실제 게임 클래스 import
    from board_class import ConditionBoard
    from deck_class import MainDeck
    
    # NPC AI 생성
    npc = NPCAI(success_rate=0.6)
    
    # 실제 게임 보드 및 덱 생성
    board = ConditionBoard()
    deck = MainDeck()
    
    print("=== 실제 ConditionBoard와 MainDeck을 사용한 테스트 ===\n")
    
    # 여러 타겟 조건으로 테스트
    test_conditions = [
        board.get_condition(0, 0),  # 첫 번째 조건
        board.get_condition(1, 4),  # 중간 조건
        board.get_condition(2, 8),  # 마지막 조건
    ]
    
    correct_count = 0
    total_count = 0
    
    for idx, condition in enumerate(test_conditions):
        print(f"\n{'='*60}")
        print(f"테스트 세트 {idx+1}: 타겟 조건 = {condition}")
        print(f"목표 정답률: {npc.success_rate * 100}%")
        print(f"{'='*60}")
        
        # 10회 시도
        for i in range(10):
            card_pos, expected_match = npc.select_card(deck, condition)
            selected_card = deck.get_card(card_pos[0], card_pos[1])
            is_match = check_match(condition, selected_card)
            
            # 통계 업데이트
            total_count += 1
            if is_match:
                correct_count += 1
            
            match_text = '✓ 정답' if is_match else '✗ 오답'
            expected_text = '(예상됨)' if is_match == expected_match else '(예상 외)'
            print(f"  시도 {i+1}: {card_pos} → {selected_card} → {match_text} {expected_text}")
    
    # 전체 통계 출력
    print(f"\n{'='*60}")
    print("### 전체 결정 통계 ###")
    print(f"{'='*60}")
    print(f"정답 결정: {correct_count}")
    print(f"오답 결정: {total_count - correct_count}")
    print(f"총 결정 수: {total_count}")
    if total_count > 0:
        actual_rate = (correct_count / total_count) * 100
        target_rate = npc.success_rate * 100
        diff = actual_rate - target_rate
        print(f"목표 정답률: {target_rate:.1f}%")
        print(f"실제 정답률: {actual_rate:.1f}% (차이: {diff:+.1f}%)")
    
    print("\n[OK] NPCAI 테스트 완료!")
