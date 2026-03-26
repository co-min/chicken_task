# board_class.py
# Chicken Task - Condition Board (운동장 조건 카드)
# 8가지 단일 조건 × 3회 반복 = 24장, 항상 앞면

import random
import math
import sys
from collections import defaultdict
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
    운동장 조건 카드 보드 (ㅁ자 형태 트랙)
    - 모드 기반 격자(기본 selection1/2: 5행 × 9열)에서 외곽 순환
    - 24칸 순환 트랙: 상단(9) → 우측(4) → 하단(8) → 좌측(3)
    - 각 카드는 단일 조건 1개 ({'type': ..., 'value': ...})
    - 8가지 조건(색상3+모양3+숫자2) × 3회 반복 = 24장
    - 항상 앞면 보임
    """
    
    def __init__(self, mode_profile=None):
        """운동장 보드 초기화"""
        self.mode_profile = mode_profile or {}
        
        # 모드 프로필에서 보드 설정 가져오기
        self.track_length = int(self.mode_profile.get('track_length', BOARD_ROWS * BOARD_COLS))
        self.rows = int(self.mode_profile.get('board_rows', BOARD_ROWS))
        self.cols = int(self.mode_profile.get('board_cols', BOARD_COLS))
        self.total_cards = self.track_length
        
        # ㅁ자 형태 순환 트랙 자동 생성
        self.track_positions = self._generate_rectangular_track()
        
        self._track_index_by_pos = {pos: idx for idx, pos in enumerate(self.track_positions)}
        
        # 조건 카드 풀 생성 및 셔플
        self.conditions = self._create_conditions()
        self.board = self._shuffle_and_layout()
    
    def _generate_rectangular_track(self):
        """
        ㅁ자 형태 순환 트랙 자동 생성 (외곽 테두리)
        상단 전체 → 우측 아래 → 하단 역순 → 좌측 위(모서리 제외)
        
        Returns:
            list: (row, col) 좌표 리스트
        """
        track = []
        
        # 상단 (좌→우): row 0, col 0 ~ cols-1
        for col in range(self.cols):
            if len(track) >= self.track_length:
                break
            track.append((0, col))
        
        # 우측 (상→하): col cols-1, row 1 ~ rows-1
        for row in range(1, self.rows):
            if len(track) >= self.track_length:
                break
            track.append((row, self.cols - 1))
        
        # 하단 (우→좌): row rows-1, col cols-2 ~ 0
        for col in range(self.cols - 2, -1, -1):
            if len(track) >= self.track_length:
                break
            track.append((self.rows - 1, col))
        
        # 좌측 (하→상): col 0, row rows-2 ~ 1 (모서리 제외)
        for row in range(self.rows - 2, 0, -1):
            if len(track) >= self.track_length:
                break
            track.append((row, 0))
        
        return track
    
    def _create_conditions(self):
        """
        GAME_MODE 설정에 따른 단일 조건 카드 생성
        - 색상 카드: {'type': 'color', 'value': ...}
        - 모양 카드: {'type': 'shape', 'value': ...}
        - 숫자 카드: {'type': 'number', 'value': ...}

        기본(selection1/2): 3 + 3 + 2 = 8가지 조건
        
        Returns:
            list: 조건 딕셔너리 리스트
        """
        # 모드 프로필에서 사용할 속성 가져오기
        colors = self.mode_profile.get('colors', COLORS)
        shapes = self.mode_profile.get('shapes', SHAPES)
        numbers = self.mode_profile.get('numbers', NUMBERS)
        
        # 단일 속성 조건 생성 (조합 카드가 아님)
        base_conditions = []
        for color in colors:
            base_conditions.append({'type': 'color', 'value': color})
        for shape in shapes:
            base_conditions.append({'type': 'shape', 'value': shape})
        for number in numbers:
            base_conditions.append({'type': 'number', 'value': number})

        if not base_conditions:
            return []

        # 완전 반복 횟수만큼 채우고, 나머지는 랜덤 샘플로 구성
        base_count = len(base_conditions)
        full_repeats = self.total_cards // base_count
        remainder = self.total_cards % base_count

        conditions = []
        for _ in range(full_repeats):
            conditions.extend(base_conditions)
        if remainder > 0:
            conditions.extend(random.sample(base_conditions, remainder))

        return conditions
    
    def _shuffle_and_layout(self):
        """
        조건을 섞어서 1D 리스트로 반환 (track_positions 순서대로)
        - 순환 트랙 기준 인접 카드(마지막↔첫 카드 포함) 중복 금지
        
        Returns:
            list: 1D 조건 리스트
        """
        cards = self.conditions[:self.track_length]
        if len(cards) <= 1:
            return cards

        def cond_key(condition):
            return (condition.get('type'), condition.get('value'))

        def has_circular_adjacent_duplicate(seq):
            seq_len = len(seq)
            for i in range(seq_len):
                if cond_key(seq[i]) == cond_key(seq[(i + 1) % seq_len]):
                    return True
            return False

        # 1) 빠른 확률적 시도: 대부분의 경우 매우 빠르게 성공
        max_random_attempts = 1000
        for _ in range(max_random_attempts):
            shuffled = cards.copy()
            random.shuffle(shuffled)
            if not has_circular_adjacent_duplicate(shuffled):
                return shuffled

        # 2) 확률적 시도가 모두 실패하면, 키 기준으로 안정 재배치 시도
        #    (분포에 따라 원형 인접 중복 제거가 수학적으로 불가능할 수 있음)
        buckets = defaultdict(list)
        for card in cards:
            buckets[cond_key(card)].append(card)

        key_counts = {k: len(v) for k, v in buckets.items()}
        n = len(cards)
        max_count = max(key_counts.values()) if key_counts else 0
        if max_count > n // 2:
            raise ValueError(
                "Cannot layout circular board without consecutive duplicate conditions "
                f"(max same condition count={max_count}, total={n})."
            )

        # 남은 수가 많은 조건 우선으로 배치 (동률은 랜덤)
        for _ in range(200):
            remaining = key_counts.copy()
            order = []

            for idx in range(n):
                prev_key = order[-1] if order else None
                first_key = order[0] if order else None

                candidates = []
                for key, cnt in remaining.items():
                    if cnt <= 0:
                        continue
                    if prev_key is not None and key == prev_key:
                        continue
                    if idx == n - 1 and first_key is not None and key == first_key:
                        continue
                    candidates.append((key, cnt))

                if not candidates:
                    order = []
                    break

                random.shuffle(candidates)
                candidates.sort(key=lambda x: x[1], reverse=True)
                chosen_key = candidates[0][0]
                order.append(chosen_key)
                remaining[chosen_key] -= 1

            if len(order) == n:
                arranged = []
                local_buckets = {k: v.copy() for k, v in buckets.items()}
                for key in order:
                    arranged.append(local_buckets[key].pop())
                return arranged

        raise ValueError("Failed to generate board without circular adjacent duplicate conditions.")
    
    def get_condition(self, row, col):
        """
        특정 위치(row, col)의 조건 가져오기
        
        Args:
            row (int): 행
            col (int): 열
        
        Returns:
            dict: 조건 또는 None (트랙에 없는 위치)
        """
        pos = (row, col)
        if pos in self._track_index_by_pos:
            idx = self._track_index_by_pos[pos]
            return self.board[idx]
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
        current_pos = (current_row, current_col)
        if current_pos not in self._track_index_by_pos:
            return self.track_positions[0]

        next_idx = (self._track_index_by_pos[current_pos] + 1) % len(self.track_positions)
        return self.track_positions[next_idx]
    
    def get_all_conditions(self):
        """
        모든 조건을 1D 리스트로 반환
        
        Returns:
            list: track_length개 조건
        """
        return self.board
    
    def print_board(self):
        """보드 출력 (디버깅용, ㅁ자 형태)"""
        print("=" * 80)
        print("운동장 조건 카드 보드 (ㅁ자 순환 트랙)")
        print("=" * 80)
        
        for idx, pos in enumerate(self.track_positions):
            row, col = pos
            condition = self.board[idx]
            cond_type = condition.get('type', '?')
            cond_value = condition.get('value', '?')
            
            # 행이 바뀔 때마다 줄바꿈
            if idx > 0 and pos[0] != self.track_positions[idx-1][0]:
                print()
            
            print(f"  [{row},{col}] {cond_type}:{cond_value}", end="  ")
        
        print("\n" + "=" * 80)


# ==================== 테스트 코드 ====================
if __name__ == "__main__":
    print("\n### ConditionBoard 테스트 ###\n")
    
    # 보드 생성
    board = ConditionBoard()
    board.print_board()
    
    # 조건 가져오기 테스트
    print("\n### get_condition 테스트 ###")
    print(f"[0,0]: {board.get_condition(0, 0)}")
    print(f"[1,8]: {board.get_condition(1, 8)}")
    print(f"[2,0]: {board.get_condition(2, 0)}")
    
    # 다음 위치 계산 테스트
    print("\n### 순환 경로 테스트 ###")
    test_positions = [
        (0, 0),   # 상단 시작
        (0, 8),   # 상단 끝
        (1, 8),   # 우측
        (2, 0),   # 좌측 끝
    ]
    
    for pos in test_positions:
        next_pos = board.get_next_position(pos[0], pos[1])
        print(f"{pos} → {next_pos}")
    
    # 조건 분포 확인
    print("\n### 조건 분포 확인 ###")
    all_conds = board.get_all_conditions()
    print(f"총 조건 수: {len(all_conds)}")
    
    type_count = {}
    value_count = {}
    
    for cond in all_conds:
        cond_type = cond.get('type')
        cond_value = cond.get('value')

        type_count[cond_type] = type_count.get(cond_type, 0) + 1
        value_count[cond_value] = value_count.get(cond_value, 0) + 1

    print(f"타입 분포: {type_count}")
    print(f"값 분포: {value_count}")
    
    print("\n[OK] ConditionBoard 테스트 완료!")
