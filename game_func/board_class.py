# board_class.py
# Chicken Task - Condition Board (운동장 조건 카드)
# 9가지 조건 × 3회 반복 = 27장, 항상 앞면

import random
import sys
from pathlib import Path

# 상대 import (모듈로 import될 때) 또는 절대 import (직접 실행될 때)
try:
    from ..config import BOARD_ROWS, BOARD_COLS, COLORS, SHAPES, NUMBERS
except ImportError:
    # 직접 실행할 때: 부모 디렉토리를 sys.path에 추가
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from config import BOARD_ROWS, BOARD_COLS, COLORS, SHAPES, NUMBERS


class ConditionBoard:
    """
    운동장 조건 카드 보드
    - 3행 × 9열 = 27장
    - 각 카드는 단일 조건 1개 (색상/모양/숫자)
    - 9가지 조건 × 3회 반복
    - 항상 앞면 보임
    - 순환 경로: 1-1 → 1-9 → 2-1 → 2-9 → 3-1 → 3-9 → 1-1
    """
    
    def __init__(self):
        """운동장 보드 초기화"""
        self.rows = BOARD_ROWS  # 3
        self.cols = BOARD_COLS  # 9
        self.total_cards = self.rows * self.cols  # 27
        
        # 조건 카드 풀 생성 및 셔플
        self.conditions = self._create_conditions()
        self.board = self._shuffle_and_layout()
    
    def _create_conditions(self):
        """
        27개 조건 생성: 9가지 × 3회
        
        Returns:
            list: 조건 딕셔너리 리스트
                  [{'type': 'color', 'value': 'red'}, ...]
        """
        conditions = []
        
        # 색상 조건 (3가지 × 3회 = 9장)
        for color in COLORS:
            for _ in range(3):
                conditions.append({
                    'type': 'color',
                    'value': color
                })
        
        # 모양 조건 (3가지 × 3회 = 9장)
        for shape in SHAPES:
            for _ in range(3):
                conditions.append({
                    'type': 'shape',
                    'value': shape
                })
        
        # 숫자 조건 (3가지 × 3회 = 9장)
        for number in NUMBERS:
            for _ in range(3):
                conditions.append({
                    'type': 'number',
                    'value': number
                })
        
        return conditions
    
    def _shuffle_and_layout(self):
        """
        조건을 섞어서 3×9 보드에 배치
        
        Returns:
            list: 2D 배열 [row][col]
        """
        # 셔플
        shuffled = self.conditions.copy()
        random.shuffle(shuffled)
        
        # 2D 배열로 변환
        board = []
        idx = 0
        for row in range(self.rows):
            row_cards = []
            for col in range(self.cols):
                row_cards.append(shuffled[idx])
                idx += 1
            board.append(row_cards)
        
        return board
    
    def get_condition(self, row, col):
        """
        특정 위치의 조건 가져오기
        
        Args:
            row (int): 행 (0-2)
            col (int): 열 (0-8)
        
        Returns:
            dict: 조건 {'type': ..., 'value': ...} 또는 None
        """
        if 0 <= row < self.rows and 0 <= col < self.cols:
            return self.board[row][col]
        return None
    
    def get_next_position(self, current_row, current_col):
        """
        순환 경로에서 다음 위치 계산
        1-1 → 1-9 → 2-1 → 2-9 → 3-1 → 3-9 → 1-1 (순환)
        
        Args:
            current_row (int): 현재 행
            current_col (int): 현재 열
        
        Returns:
            tuple: (next_row, next_col)
        """
        next_col = current_col + 1
        next_row = current_row
        
        # 열 끝에 도달하면 다음 행으로
        if next_col >= self.cols:
            next_col = 0
            next_row = current_row + 1
        
        # 마지막 행 끝에 도달하면 처음으로 순환
        if next_row >= self.rows:
            next_row = 0
        
        return (next_row, next_col)
    
    def get_all_conditions(self):
        """
        모든 조건을 평탄화된 리스트로 반환
        
        Returns:
            list: 27개 조건 [row0_col0, row0_col1, ...]
        """
        flat = []
        for row in range(self.rows):
            for col in range(self.cols):
                flat.append(self.board[row][col])
        return flat
    
    def print_board(self):
        """보드 출력 (디버깅용)"""
        print("=" * 80)
        print("운동장 조건 카드 보드 (Condition Board)")
        print("=" * 80)
        
        for row in range(self.rows):
            print(f"\n행 {row + 1}:")
            for col in range(self.cols):
                condition = self.board[row][col]
                ctype = condition['type']
                cvalue = condition['value']
                print(f"  [{row},{col}] {ctype}:{cvalue}", end="  ")
            print()
        
        print("=" * 80)


# ==================== 테스트 코드 ====================
if __name__ == "__main__":
    print("\n### ConditionBoard 테스트 ###\n")
    
    # 보드 생성
    board = ConditionBoard()
    board.print_board()
    
    # 조건 가져오기 테스트
    print("\n### get_condition 테스트 ###")
    print(f"[0,0]: {board.get_condition(0, 0)}")
    print(f"[1,4]: {board.get_condition(1, 4)}")
    print(f"[2,8]: {board.get_condition(2, 8)}")
    
    # 다음 위치 계산 테스트
    print("\n### 순환 경로 테스트 ###")
    test_positions = [
        (0, 0),   # 1-1 → 1-2
        (0, 8),   # 1-9 → 2-1
        (1, 8),   # 2-9 → 3-1
        (2, 8),   # 3-9 → 1-1 (순환)
    ]
    
    for pos in test_positions:
        next_pos = board.get_next_position(pos[0], pos[1])
        print(f"{pos} → {next_pos}")
    
    # 조건 분포 확인
    print("\n### 조건 분포 확인 ###")
    all_conds = board.get_all_conditions()
    
    color_count = {}
    shape_count = {}
    number_count = {}
    
    for cond in all_conds:
        if cond['type'] == 'color':
            key = cond['value']
            color_count[key] = color_count.get(key, 0) + 1
        elif cond['type'] == 'shape':
            key = cond['value']
            shape_count[key] = shape_count.get(key, 0) + 1
        elif cond['type'] == 'number':
            key = cond['value']
            number_count[key] = number_count.get(key, 0) + 1
    
    print(f"색상 (각 3회): {color_count}")
    print(f"모양 (각 3회): {shape_count}")
    print(f"숫자 (각 3회): {number_count}")
    
    print("\n[OK] ConditionBoard 테스트 완료!")
