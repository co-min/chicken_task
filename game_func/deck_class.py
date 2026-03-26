# deck_class.py
# Chicken Task - Main Card Deck (메인 카드 덱)
# 27가지 조합, 뒷면 시작, 5초 노출

import random
import time
import sys
from pathlib import Path

try:
    from ..config import BOARD_ROWS, BOARD_COLS, COLORS, SHAPES, NUMBERS, CARD_FLIP_DURATION
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from config import BOARD_ROWS, BOARD_COLS, COLORS, SHAPES, NUMBERS, CARD_FLIP_DURATION


class MainDeck:
    """
    메인 카드 덱
    - 3행 × 9열 = 27장
    - 각 카드는 3가지 속성 조합 (색상 + 모양 + 숫자)
    - 27가지 조합 모두 포함 (3×3×3)
    - 뒷면으로 시작
    - 클릭 시 5초간 앞면 노출 → 자동 뒷면 복구
    """
    
    def __init__(self, mode_profile=None):
        """메인 덱 초기화"""
        self.mode_profile = mode_profile or {}
        self.rows = int(self.mode_profile.get('deck_rows', BOARD_ROWS))
        self.cols = int(self.mode_profile.get('deck_cols', BOARD_COLS))
        self.total_cards = self.rows * self.cols
        
        # 카드 조합 생성 및 셔플
        self.cards = self._create_cards()
        self.deck = self._shuffle_and_layout()
        
        # 카드 상태 관리 (뒷면=False, 앞면=True)
        self.face_up = self._initialize_face_states()
        
        # 플립 타이머 (카드가 앞면으로 뒤집힌 시각)
        self.flip_timers = {}  # {(row, col): flip_time}
    
    def _create_cards(self):
        """
        GAME_MODE 설정에 따른 카드 생성
        각 모드에서 지정한 색상/모양/숫자의 조합만 사용
        
        기본: 색상(3) × 모양(3) × 숫자 개수 형태
        
        Returns:
            list: 카드 딕셔너리 리스트
                  [{'color': 'red', 'shape': 'square', 'number': 1}, ...]
        """
        # 모드 프로필에서 사용할 속성 가져오기
        colors = self.mode_profile.get('colors', COLORS)
        shapes = self.mode_profile.get('shapes', SHAPES)
        numbers = self.mode_profile.get('numbers', NUMBERS)
        
        # 모든 조합 생성
        base_cards = []
        for color in colors:
            for shape in shapes:
                for number in numbers:
                    base_cards.append({
                        'color': color,
                        'shape': shape,
                        'number': number
                    })

        # total_cards만큼 중복 없이 랜덤 샘플
        if self.total_cards > len(base_cards):
            raise ValueError(
                f"덱 크기({self.total_cards})가 가능한 조합 수({len(base_cards)})를 초과합니다. "
                f"colors({len(colors)}) × shapes({len(shapes)}) × numbers({len(numbers)}) = {len(base_cards)}"
            )

        return random.sample(base_cards, self.total_cards)
    
    def _shuffle_and_layout(self):
        """
        카드를 섞어서 3×9 덱에 배치
        
        Returns:
            list: 2D 배열 [row][col]
        """
        # 셔플
        shuffled = self.cards.copy()
        random.shuffle(shuffled)
        
        # 2D 배열로 변환
        deck = []
        idx = 0
        for row in range(self.rows):
            row_cards = []
            for col in range(self.cols):
                row_cards.append(shuffled[idx])
                idx += 1
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
    


# ==================== 테스트 코드 ====================
if __name__ == "__main__":
    import time

    print("\n### MainDeck 테스트 ###\n")

    # 덱 생성
    deck = MainDeck()

    # 카드 가져오기 테스트
    print("### get_card 테스트 ###")
    print(f"[0,0]: {deck.get_card(0, 0)}")
    print(f"[1,4]: {deck.get_card(1, 4)}")
    print(f"[2,8]: {deck.get_card(2, 8)}")

    # 조합 확인
    print("\n### 카드 조합 확인 ###")
    all_cards = [deck.get_card(r, c) for r in range(deck.rows) for c in range(deck.cols)]
    print(f"총 카드 수: {len(all_cards)}")
    unique_cards = set(f"{c['color']}-{c['shape']}-{c['number']}" for c in all_cards)
    print(f"고유 조합 수: {len(unique_cards)} (27개여야 함)")

    # 플립 메커니즘 테스트
    print("\n### 플립 메커니즘 테스트 ###")
    print(f"[0,0] 앞면? {deck.is_face_up(0, 0)}")
    deck.flip_card(0, 0)
    print(f"플립 후 [0,0] 앞면? {deck.is_face_up(0, 0)}")

    # 5초 경과 시뮬레이션
    print("\n5초 경과 시뮬레이션...")
    current_time = time.time() + 5.1
    auto_hidden = deck.update_timers(current_time)
    print(f"자동 숨김된 카드: {auto_hidden}")
    print(f"[0,0] 앞면? {deck.is_face_up(0, 0)}")

    print("\n[OK] MainDeck 테스트 완료!")
