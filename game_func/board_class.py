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
    
    def _apply_bonus_slots(self, cards):
        """
        완성된 카드 배열에 보너스 마킹을 추가한다.

        인접 중복 방지 로직은 cond_key() = (type, value) 만 비교하므로,
        bonus 키를 사후에 추가해도 셔플 제약과 완전히 독립된다.

        bonus_mode:
          'none'   — 아무 변경 없음
          'fixed'  — mode_profile['bonus_slots'] 인덱스에 bonus 마킹 (고정)
          'random' — mode_profile['bonus_count'] 개를 매 호출마다 랜덤 선택

        Args:
            cards: 1D 조건 딕셔너리 리스트 (셔플 완료 상태)

        Returns:
            list: bonus 키가 삽입된 새 리스트 (원본 딕셔너리 불변)
        """
        bonus_mode = self.mode_profile.get('bonus_mode', 'none')
        n = len(cards)
        if bonus_mode == 'none' or n == 0:
            return cards

        if bonus_mode == 'fixed':
            slots = set(
                s for s in self.mode_profile.get('bonus_slots', [])
                if 0 <= s < n
            )
        elif bonus_mode == 'random':
            count = min(self.mode_profile.get('bonus_count', 3), n)
            slots = set(random.sample(range(n), count))
        else:
            return cards

        result = []
        for i, card in enumerate(cards):
            if i in slots:
                result.append({**card, 'bonus': 'double_score'})
            else:
                result.append(card)

        slot_list = sorted(slots)
        print(f"[BONUS] mode={bonus_mode}, slots={slot_list}")
        return result

    def _shuffle_and_layout(self):
        """
        조건을 섞어서 1D 리스트로 반환 (track_positions 순서대로)
        - 순환 트랙 기준 인접 카드(마지막↔첫 카드 포함) 중복 금지
        - 셔플 완료 후 _apply_bonus_slots()로 보너스 마킹 추가
          (bonus 키는 인접 중복 판정에 사용되지 않으므로 제약 무영향)

        Returns:
            list: 1D 조건 리스트
        """
        cards = self.conditions[:self.track_length]
        if len(cards) <= 1:
            return self._apply_bonus_slots(cards)

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
                return self._apply_bonus_slots(shuffled)

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
                return self._apply_bonus_slots(arranged)

        raise ValueError("Failed to generate board without circular adjacent duplicate conditions.")
    
    def reshuffle(self):
        """
        조건 카드를 다시 셔플하여 보드를 재배치
        - 토큰 위치 초기화 이벤트 후 호출
        - 조건 종류는 동일하게 유지하되 순서만 다시 섞음
        """
        self.conditions = self._create_conditions()
        self.board = self._shuffle_and_layout()

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


