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


# 테스트 코드
if __name__ == "__main__":
    # 경고 억제
    import warnings
    warnings.filterwarnings('ignore')
    from psychopy import logging
    logging.console.setLevel(logging.ERROR)
    
    from psychopy import core
    from game_func.deck_class import MainDeck
    from set_opts.set_visual_opt import set_visual_opt
    from utils.card_matcher import get_card_text
    
    print("\n### DeckRenderer 테스트 ###\n")
    
    # 윈도우 생성
    visual_opt = set_visual_opt()
    visual_opt['fullscreen'] = False  # 테스트용
    
    win = visual.Window(
        size=visual_opt['win_size'],
        color=visual_opt['bg_color'],
        fullscr=visual_opt['fullscreen'],
        units=visual_opt['units'],
        colorSpace=visual_opt['color_space'],
        allowGUI=True,
        pos=visual_opt.get('pos'),
        screen=visual_opt.get('screen', 0)
    )
    
    # 덱 생성
    deck = MainDeck()
    
    # 렌더러 생성
    renderer = DeckRenderer(win, deck)
    
    # 타이틀 텍스트
    title = visual.TextStim(
        win=win,
        text="메인 덱 (클릭하여 카드 뒤집기, ESC로 종료)",
        pos=(0, HEIGHT / 2 - 70),
        height=40,
        color=[255, 255, 255],
        colorSpace='rgb255'
    )
    
    # 마우스 생성
    mouse = visual.event.Mouse(win=win)
    
    print("렌더링 시작...")
    print("마우스로 카드를 클릭하면 뒤집힙니다.")
    print("ESC 키를 눌러 종료하세요.\n")
    
    # 메인 루프
    highlighted = None
    
    while True:
        # 키보드 체크
        keys = visual.event.getKeys(['escape'])
        if 'escape' in keys:
            break
        
        # 마우스 클릭 체크
        if mouse.getPressed()[0]:  # 왼쪽 버튼
            pos = renderer.get_clicked_position(mouse.getPos())
            if pos:
                highlighted = pos
                
                # 카드 뒤집기
                if deck.is_face_up(pos[0], pos[1]):
                    deck.hide_card(pos[0], pos[1])
                    print(f"카드 {pos} 뒷면으로")
                else:
                    deck.flip_card(pos[0], pos[1])
                    card = deck.get_card(pos[0], pos[1])
                    print(f"카드 {pos} 앞면으로: {get_card_text(card)}")
            
            # 더블 클릭 방지
            core.wait(0.2)
        
        # 화면 그리기
        title.draw()
        renderer.draw(highlighted_pos=highlighted)
        win.flip()
    
    win.close()
    core.quit()
    
    print("[OK] DeckRenderer 테스트 완료!")
