# deck_class.py
# Chicken Task - Main Card Deck (메인 카드 덱)
# 난이도별 카드 수(12/15/18장) 및 배치 방식(factorization/random) 지원

import random
import time
import sys
from collections import defaultdict
from pathlib import Path

try:
    from ..config import BOARD_ROWS, BOARD_COLS, COLORS, SHAPES, NUMBERS, CARD_FLIP_DURATION
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from config import BOARD_ROWS, BOARD_COLS, COLORS, SHAPES, NUMBERS, CARD_FLIP_DURATION


class MainDeck:

    def __init__(self, mode_profile=None, layout_mode='random'):
        self.mode_profile = mode_profile or {}
        self.layout_mode = layout_mode
        self.rows = int(self.mode_profile.get('deck_rows', BOARD_ROWS))
        self.cols = int(self.mode_profile.get('deck_cols', BOARD_COLS))
        self.total_cards = self.rows * self.cols

        # 카드 배치 생성
        self.deck = self._build_deck()

        # 카드 상태 관리 (뒷면=False, 앞면=True)
        self.face_up = self._initialize_face_states()

        # 플립 타이머 (카드가 앞면으로 뒤집힌 시각)
        self.flip_timers = {}  

    # ------------------------------------------------------------------
    # 덱 생성
    # ------------------------------------------------------------------

    def _build_deck(self):
        if self.layout_mode == 'factorization':
            return self._factorization_layout()
        return self._random_layout()

    def _random_layout(self):
        colors  = self.mode_profile.get('colors',  COLORS)
        shapes  = self.mode_profile.get('shapes',  SHAPES)
        numbers = self.mode_profile.get('numbers', NUMBERS)

        base_cards = [
            {'color': c, 'shape': s, 'number': n}
            for c in colors for s in shapes for n in numbers
        ]

        if self.total_cards > len(base_cards):
            raise ValueError(
                f"덱 크기({self.total_cards})가 가능한 조합 수({len(base_cards)})를 초과합니다. "
                f"colors({len(colors)}) × shapes({len(shapes)}) × numbers({len(numbers)}) = {len(base_cards)}"
            )

        # greedy seed selection
        uncovered_colors  = set(colors)
        uncovered_shapes  = set(shapes)
        uncovered_numbers = set(numbers)

        pool = base_cards.copy()
        random.shuffle(pool)
        seed_cards = []

        while (uncovered_colors or uncovered_shapes or uncovered_numbers) and pool:
            # 미커버 조건을 가장 많이 충족하는 카드를 탐욕적으로 선택
            best_score = -1
            best_candidates = []
            for card in pool:
                score = (
                    (card['color']  in uncovered_colors)  +
                    (card['shape']  in uncovered_shapes)  +
                    (card['number'] in uncovered_numbers)
                )
                if score > best_score:
                    best_score = score
                    best_candidates = [card]
                elif score == best_score:
                    best_candidates.append(card)

            chosen = random.choice(best_candidates)
            seed_cards.append(chosen)
            pool.remove(chosen)
            uncovered_colors.discard(chosen['color'])
            uncovered_shapes.discard(chosen['shape'])
            uncovered_numbers.discard(chosen['number'])

        if len(seed_cards) > self.total_cards:
            raise ValueError(
                f"조건 커버리지 보장에 필요한 최소 카드 수({len(seed_cards)})가 "
                f"덱 크기({self.total_cards})를 초과합니다."
            )

        # 나머지 슬롯을 pool에서 무작위로 채움
        filler = random.sample(pool, self.total_cards - len(seed_cards))
        sampled = seed_cards + filler
        random.shuffle(sampled)

        deck = []
        idx = 0
        for row in range(self.rows):
            row_cards = []
            for col in range(self.cols):
                row_cards.append(sampled[idx])
                idx += 1
            deck.append(row_cards)
        return deck

    def _factorization_layout(self):
        colors  = self.mode_profile.get('colors',  COLORS)
        shapes  = self.mode_profile.get('shapes',  SHAPES)
        numbers = self.mode_profile.get('numbers', NUMBERS)

        # 각 (color, shape) 쌍의 슬롯 목록 수집
        pair_slots = defaultdict(list)  # (color, shape) -> [(row, col), ...]
        for row in range(self.rows):
            color = colors[row % len(colors)]
            for col in range(self.cols):
                shape = shapes[col % len(shapes)]
                pair_slots[(color, shape)].append((row, col))

        # 각 숫자가 덱에 최소 1장 포함되도록 페어별로 숫자 강제 배정
        # pairs_list에서 len(numbers)개 페어를 골라 각각 다른 숫자를 반드시 포함하도록 지정
        pairs_list = list(pair_slots.keys())
        random.shuffle(pairs_list)
        numbers_to_force = list(numbers)
        random.shuffle(numbers_to_force)
        forced_number_by_pair = {
            pair: num
            for pair, num in zip(pairs_list, numbers_to_force)
        }

        # (color, shape) 쌍별로 number 할당 (중복 없이, 강제 숫자 우선 포함)
        slot_number = {}  # (row, col) -> number
        for (color, shape), slots in pair_slots.items():
            need = len(slots)
            if need > len(numbers):
                raise ValueError(
                    f"({color}, {shape}) 슬롯 수({need})가 "
                    f"사용 가능한 numbers 수({len(numbers)})를 초과합니다. "
                    f"deck_cols를 줄이거나 numbers를 늘려주세요."
                )
            forced = forced_number_by_pair.get((color, shape))
            if forced is not None:
                # 강제 숫자를 포함하여 need장 할당 (중복 없이)
                other = [n for n in numbers if n != forced]
                fill = random.sample(other, need - 1)
                assigned = [forced] + fill
                random.shuffle(assigned)
            else:
                assigned = random.sample(numbers, need)
            for slot, number in zip(slots, assigned):
                slot_number[slot] = number

        # 2D 배열 생성
        deck = []
        for row in range(self.rows):
            color = colors[row % len(colors)]
            row_cards = []
            for col in range(self.cols):
                shape  = shapes[col % len(shapes)]
                number = slot_number[(row, col)]
                row_cards.append({'color': color, 'shape': shape, 'number': number})
            deck.append(row_cards)
        return deck
    
    def _initialize_face_states(self):
        """
        모든 카드를 뒷면으로 초기화
        
        Returns:
            list: 2D 배열 [row][col] - False=뒷면, True=앞면
        """
        states = []
        for row in range(self.rows):
            row_states = [False] * self.cols  # 모두 뒷면
            states.append(row_states)
        return states
    
    def get_card(self, row, col):
        """
        특정 위치의 카드 가져오기
        
        Args:
            row (int): 행 (0-2)
            col (int): 열 (0-8)
        
        Returns:
            dict: 카드 {'color': ..., 'shape': ..., 'number': ...} 또는 None
        """
        if 0 <= row < self.rows and 0 <= col < self.cols:
            return self.deck[row][col]
        return None
    
    def is_face_up(self, row, col):
        """
        카드가 앞면인지 확인
        
        Args:
            row (int): 행
            col (int): 열
        
        Returns:
            bool: True=앞면, False=뒷면
        """
        if 0 <= row < self.rows and 0 <= col < self.cols:
            return self.face_up[row][col]
        return False
    
    def flip_card(self, row, col):
        """
        카드를 앞면으로 뒤집고 타이머 시작
        
        Args:
            row (int): 행
            col (int): 열
        
        Returns:
            bool: 성공 여부
        """
        if 0 <= row < self.rows and 0 <= col < self.cols:
            self.face_up[row][col] = True
            self.flip_timers[(row, col)] = time.time()
            return True
        return False
    
    def hide_card(self, row, col):
        """
        카드를 뒷면으로 되돌림
        
        Args:
            row (int): 행
            col (int): 열
        """
        if 0 <= row < self.rows and 0 <= col < self.cols:
            self.face_up[row][col] = False
            if (row, col) in self.flip_timers:
                del self.flip_timers[(row, col)]
    
    def reshuffle(self):
        """
        덱을 재생성하여 재배치
        - 토큰 위치 초기화 이벤트 후 호출
        - layout_mode 유지, 카드 구성은 새로 샘플/배치
        - 모든 카드를 뒷면으로 초기화하고 타이머 초기화
        """
        self.deck = self._build_deck()
        self.face_up = self._initialize_face_states()
        self.flip_timers = {}

    def face_up_snapshot(self) -> str:
        """카드 클릭 직전 face_up 상태를 row-major 0/1 문자열로 반환.
        예) 3×4 덱에서 (0,2), (1,0)만 앞면이면 → '0,0,1,0,1,0,0,0,0,0,0,0'
        """
        parts = []
        for row in self.face_up:
            for val in row:
                parts.append('1' if val else '0')
        return ','.join(parts)

    def update_timers(self, current_time):
        """
        플립 타이머 업데이트 - 5초 지난 카드 자동 숨김
        
        Args:
            current_time (float): 현재 시각 (time.time())
        
        Returns:
            list: 자동 숨김된 카드 위치 [(row, col), ...]
        """
        auto_hidden = []
        
        # 각 플립된 카드 확인
        for (row, col), flip_time in list(self.flip_timers.items()):
            elapsed = current_time - flip_time
            
            # 5초 경과 시 자동 숨김
            if elapsed >= CARD_FLIP_DURATION:
                self.hide_card(row, col)
                auto_hidden.append((row, col))
        
        return auto_hidden
    


