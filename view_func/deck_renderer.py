# view_func/deck_renderer.py
# 메인 덱 조합 카드 렌더링

from psychopy import visual
import os
from config import (
    DECK_LEFT_EDGE, BOARD_DECK_TOP_MARGIN,
    DECK_CARD_WIDTH, DECK_CARD_HEIGHT, DECK_CARD_SPACING,
    WIDTH, HEIGHT,
    HIGHLIGHT_COLOR, HIGHLIGHT_WIDTH
)

# 이미지 경로
STIMULI_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'stimuli')
MAIN_CARDS_DIR = os.path.join(STIMULI_DIR, 'main_cards')
UI_DIR = os.path.join(STIMULI_DIR, 'ui')


class DeckRenderer:
    """메인 덱 조합 카드를 화면에 렌더링하는 클래스"""
    
    def __init__(self, win, deck):
        """
        Args:
            win: PsychoPy window 객체
            deck: MainDeck 인스턴스
        """
        self.win = win
        self.deck = deck
        
        # 카드 비주얼 요소 생성
        self.card_backs = []    # 카드 뒷면 이미지
        self.card_fronts = []   # 카드 앞면 이미지
        self.highlights = []    # 하이라이트 테두리
        
        self._create_visuals()
    
    def _create_visuals(self):
        """모든 카드의 비주얼 요소를 생성"""
        # 뒷면 이미지 경로
        card_back_path = os.path.join(UI_DIR, 'card_back.png')
        
        for row in range(self.deck.rows):
            row_backs = []
            row_fronts = []
            row_highlights = []
            
            for col in range(self.deck.cols):
                # 화면 좌표 계산
                x = self._get_card_x(col)
                y = self._get_card_y(row)
                
                # 카드 뒷면 이미지
                back = visual.ImageStim(
                    win=self.win,
                    image=card_back_path,
                    pos=(x, y),
                    size=(DECK_CARD_WIDTH, DECK_CARD_HEIGHT)
                )
                row_backs.append(back)
                
                # 카드 앞면 이미지
                card = self.deck.get_card(row, col)
                front_path = self._get_card_image_path(card)
                
                front = visual.ImageStim(
                    win=self.win,
                    image=front_path,
                    pos=(x, y),
                    size=(DECK_CARD_WIDTH, DECK_CARD_HEIGHT)
                )
                row_fronts.append(front)
                
                # 하이라이트
                highlight = visual.Rect(
                    win=self.win,
                    width=DECK_CARD_WIDTH + HIGHLIGHT_WIDTH * 2,
                    height=DECK_CARD_HEIGHT + HIGHLIGHT_WIDTH * 2,
                    pos=(x, y),
                    fillColor=None,
                    lineColor=HIGHLIGHT_COLOR,
                    lineWidth=HIGHLIGHT_WIDTH,
                    colorSpace='rgb255',
                    autoDraw=False
                )
                row_highlights.append(highlight)
            
            self.card_backs.append(row_backs)
            self.card_fronts.append(row_fronts)
            self.highlights.append(row_highlights)
    
    def _get_card_x(self, col):
        """카드의 x 좌표 계산 (PsychoPy 좌표계)"""
        left_x = DECK_LEFT_EDGE + col * (DECK_CARD_WIDTH + DECK_CARD_SPACING)
        center_x = left_x + DECK_CARD_WIDTH / 2
        return center_x - WIDTH / 2
    
    def _get_card_y(self, row):
        """카드의 y 좌표 계산 (PsychoPy 좌표계)"""
        top_y = BOARD_DECK_TOP_MARGIN + row * (DECK_CARD_HEIGHT + DECK_CARD_SPACING)
        center_y = top_y + DECK_CARD_HEIGHT / 2
        return HEIGHT / 2 - center_y
    
    def _get_card_image_path(self, card):
        """
        카드에 맞는 이미지 파일 경로 반환
        
        Args:
            card: {'color': str, 'shape': str, 'number': int}
        
        Returns:
            이미지 파일 경로
        """
        color = card['color']
        shape = card['shape']
        number = card['number']
        
        filename = f"{color}_{shape}_{number}.png"
        return os.path.join(MAIN_CARDS_DIR, filename)
    
    def refresh(self):
        """덱 재셔플 후 각 위치의 카드 앞면 이미지를 갱신"""
        for row in range(self.deck.rows):
            for col in range(self.deck.cols):
                card = self.deck.get_card(row, col)
                front_path = self._get_card_image_path(card)
                self.card_fronts[row][col].image = front_path

    def update_deck(self, new_deck):
        """
        advance_round() 이후 덱이 교체될 때 호출.
        self.deck 참조를 갱신하고, 크기가 변경된 경우 비주얼을 전체 재생성한다.

        [왜 필요한가]
        DeckRenderer는 __init__에서 deck 참조를 self.deck에 저장한다.
        advance_round()가 game_state.deck을 새 MainDeck 객체로 교체하면
        game_state.deck과 self.deck이 서로 다른 객체를 가리키게 된다.
        이 상태에서:
          - game_state.deck.flip_card()  → NEW deck의 face_up 변경
          - draw()의 self.deck.is_face_up() → OLD deck 조회 → 항상 False
          결과: 카드를 클릭해도 화면에 앞면이 표시되지 않음 (flip 불가)

        난이도 업으로 deck_cols가 변경된 경우 (4→5, 5→6):
          card_backs / card_fronts / highlights 배열이 구버전 크기로 남아
          draw()에서 IndexError 또는 새 카드가 화면에 표시되지 않는 문제도 발생한다.

        [언제 호출해야 하는가]
        advance_round() 직후, 다음 win.flip() 전에 호출.
        크기가 바뀌지 않은 라운드에서도 호출해도 무방하다.

        Args:
            new_deck: advance_round() 이후의 game_state.deck
        """
        size_changed = (new_deck.rows != self.deck.rows or
                        new_deck.cols != self.deck.cols)

        self.deck = new_deck

        if size_changed:
            # 카드 수가 변경된 경우: 비주얼 전체 재생성
            self.card_backs.clear()
            self.card_fronts.clear()
            self.highlights.clear()
            self._create_visuals()
        else:
            # 카드 수는 동일하고 내용만 바뀐 경우: 앞면 이미지만 갱신
            self.refresh()

    def draw(self, highlighted_pos=None):
        """
        덱을 화면에 그리기
        
        Args:
            highlighted_pos: 하이라이트할 위치 (row, col) 튜플 또는 None
        """
        for row in range(self.deck.rows):
            for col in range(self.deck.cols):
                is_face_up = self.deck.is_face_up(row, col)
                
                if is_face_up:
                    # 앞면 그리기
                    self.card_fronts[row][col].draw()
                else:
                    # 뒷면 그리기
                    self.card_backs[row][col].draw()
                
                # 하이라이트 그리기
                if highlighted_pos and highlighted_pos == (row, col):
                    self.highlights[row][col].draw()
    
    def get_clicked_position(self, mouse_pos):
        """
        마우스 클릭 위치에 해당하는 카드 위치 반환
        
        Args:
            mouse_pos: (x, y) 마우스 좌표 (PsychoPy 좌표계)
        
        Returns:
            (row, col) 튜플 또는 None
        """
        mx, my = mouse_pos
        
        for row in range(self.deck.rows):
            for col in range(self.deck.cols):
                rect = self.card_backs[row][col]
                
                if rect.contains((mx, my)):
                    return (row, col)
        
        return None

