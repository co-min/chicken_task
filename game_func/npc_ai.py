# npc_ai.py
# Chicken Task - NPC AI Module
# PC (Octopus) AI 로직 - 60% 정답률 알고리즘

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
    
    - 60% 정답률로 카드 선택
    - 타겟 조건에 맞는 카드 또는 틀린 카드를 전략적으로 선택
    """
    
    def __init__(self, success_rate=PC_SUCCESS_RATE):
        """
        NPC AI 초기화
        
        Args:
            success_rate (float): 정답 확률 (0.0 ~ 1.0, 기본값 0.6)
        """
        self.success_rate = success_rate
    
    def select_card(self, deck, condition):
        """
        PC가 선택할 카드 좌표 결정
        
        Args:
            deck: MainDeck 객체
            condition: 타겟 조건 (dict: {'color', 'shape', 'number'})
        
        Returns:
            tuple: (card_pos, is_match) - 선택한 카드 위치와 매칭 여부
        """
        # 60% 확률로 정답 선택, 40% 확률로 오답 선택
        should_succeed = random.random() < self.success_rate
        
        # 조건에 맞는 카드 또는 맞지 않는 카드 찾기
        matching_cards = self._find_cards_by_match(deck, condition, match=should_succeed)
        
        if matching_cards:
            card_pos = random.choice(matching_cards)
        else:
            # fallback: 랜덤 선택
            card_pos = self._select_random_card(deck)
        
        return (card_pos, should_succeed)
    
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
