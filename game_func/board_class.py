# board_class.py
import random
import sys
from collections import defaultdict
from pathlib import Path

try:
    from ..config import BOARD_ROWS, BOARD_COLS, COLORS, SHAPES, NUMBERS
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from config import BOARD_ROWS, BOARD_COLS, COLORS, SHAPES, NUMBERS


class ConditionBoard:
    
    def __init__(self, mode_profile=None):
        self.mode_profile = mode_profile or {}
        
        # mode_profile
        self.track_length = int(self.mode_profile.get('track_length', BOARD_ROWS * BOARD_COLS))
        self.rows = int(self.mode_profile.get('board_rows', BOARD_ROWS))
        self.cols = int(self.mode_profile.get('board_cols', BOARD_COLS))
        self.total_cards = self.track_length
        
        # track pool
        self.track_positions = self._generate_rectangular_track()
        
        self._track_index_by_pos = {pos: idx for idx, pos in enumerate(self.track_positions)}
        
        # condition pool
        self.conditions = self._create_conditions()
        self.board = self._shuffle_and_layout()
    
    def _generate_rectangular_track(self):
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

        # completive random
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
        self.conditions = self._create_conditions()
        self.board = self._shuffle_and_layout()

    def apply_conjunctive_conditions(self, deck_cards, count=3):
        n = len(self.board)
        if not deck_cards or count <= 0 or n == 0:
            return

        actual_count = min(count, len(deck_cards), n)
        sampled_cards = random.sample(deck_cards, actual_count)
        slot_indices = random.sample(range(n), actual_count)

        for idx, card in zip(slot_indices, sampled_cards):
            self.board[idx] = {
                'type': 'conjunctive',
                'color': card['color'],
                'shape': card['shape'],
                'number': card['number'],
            }

        print(f"[CONJUNCTIVE] {actual_count}개 조건 적용: "
              f"{[self.board[i] for i in slot_indices]}")

    def get_condition(self, row, col):
        pos = (row, col)
        if pos in self._track_index_by_pos:
            idx = self._track_index_by_pos[pos]
            return self.board[idx]
        return None


