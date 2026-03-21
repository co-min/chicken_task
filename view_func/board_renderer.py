# view_func/board_renderer.py
# 운동장 조건 카드 보드 렌더링

from psychopy import visual
import os
from config import (
    BOARD_DECK_CENTER_GAP,
    BOARD_Y_OFFSET,
    BOARD_CARD_WIDTH, BOARD_CARD_HEIGHT, BOARD_CARD_SPACING,
    CHASE_BUTTON_POS, TOKEN_BUTTON_HEIGHT,
    WIDTH, HEIGHT,
    HIGHLIGHT_COLOR, HIGHLIGHT_WIDTH
)

# 이미지 경로
STIMULI_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'stimuli')
CONDITION_CARDS_DIR = os.path.join(STIMULI_DIR, 'condition_cards')
CARD_BACK_PATH = os.path.join(STIMULI_DIR, 'ui', 'card_back.png')


class BoardRenderer:
    """운동장 조건 카드 보드를 화면에 렌더링하는 클래스"""
    
    def __init__(self, win, board):
        """
        Args:
            win: PsychoPy window 객체
            board: ConditionBoard 인스턴스
        """
        self.win = win
        self.board = board
        
        # 카드 비주얼 요소 생성
        self.card_images = {}  # {(row, col): ImageStim}
        self.highlights = {}   # {(row, col): Rect}
        
        self._create_visuals()
    
    def _create_visuals(self):
        """모든 카드의 비주얼 요소를 생성"""
        for row, col in self.board.track_positions:
            x = self._get_card_x(col)
            y = self._get_card_y(row)

            condition = self.board.get_condition(row, col)
            image_path = self._get_condition_image_path(condition)

            card_image = visual.ImageStim(
                win=self.win,
                image=image_path,
                pos=(x, y),
                size=(BOARD_CARD_WIDTH, BOARD_CARD_HEIGHT)
            )
            self.card_images[(row, col)] = card_image

            highlight = visual.Rect(
                win=self.win,
                width=BOARD_CARD_WIDTH + HIGHLIGHT_WIDTH * 2,
                height=BOARD_CARD_HEIGHT + HIGHLIGHT_WIDTH * 2,
                pos=(x, y),
                fillColor=None,
                lineColor=HIGHLIGHT_COLOR,
                lineWidth=HIGHLIGHT_WIDTH,
                colorSpace='rgb255',
                autoDraw=False
            )
            self.highlights[(row, col)] = highlight
    
    def _get_card_x(self, col):
        """
        카드의 x 좌표 계산 (PsychoPy 좌표계)
        
        Args:
            col: 열 인덱스 (0-8)
        
        Returns:
            x 좌표 (픽셀, 중앙 기준)
        """
        board_total_width = self.board.cols * BOARD_CARD_WIDTH + (self.board.cols - 1) * BOARD_CARD_SPACING
        left_margin = (WIDTH / 2) - (BOARD_DECK_CENTER_GAP / 2) - board_total_width
        left_x = left_margin + col * (BOARD_CARD_WIDTH + BOARD_CARD_SPACING)
        center_x = left_x + BOARD_CARD_WIDTH / 2
        # PsychoPy는 중앙이 (0, 0)이므로 변환
        return center_x - WIDTH / 2
    
    def _get_card_y(self, row):
        """
        카드의 y 좌표 계산 (PsychoPy 좌표계)
        
        Args:
            row: 행 인덱스 (0-2)
        
        Returns:
            y 좌표 (픽셀, 중앙 기준)
        """
        board_total_height = self.board.rows * BOARD_CARD_HEIGHT + (self.board.rows - 1) * BOARD_CARD_SPACING
        button_top_psy = CHASE_BUTTON_POS[1] + (TOKEN_BUTTON_HEIGHT / 2)
        button_top_screen = (HEIGHT / 2) - button_top_psy
        play_area_bottom_screen = max(0, button_top_screen - 20)
        top_margin = max(0, (play_area_bottom_screen - board_total_height) / 2 + BOARD_Y_OFFSET)
        top_y = top_margin + row * (BOARD_CARD_HEIGHT + BOARD_CARD_SPACING)
        center_y = top_y + BOARD_CARD_HEIGHT / 2
        # PsychoPy는 위쪽이 양수, 아래쪽이 음수 (반전)
        return HEIGHT / 2 - center_y
    
    def _get_condition_image_path(self, condition):
        """
        조건에 맞는 이미지 파일 경로 반환
        단일 속성 카드(type/value) 사용
        
        Args:
            condition: {'type': 'color'|'shape'|'number', 'value': str|int}
        
        Returns:
            이미지 파일 경로
        """
        if condition is None:
            return CARD_BACK_PATH

        cond_type = condition.get('type')
        cond_value = condition.get('value')

        if cond_type == 'color':
            filename = f"color_{cond_value}.png"
        elif cond_type == 'shape':
            filename = f"shape_{cond_value}.png"
        elif cond_type == 'number':
            filename = f"number_{cond_value}.png"
        else:
            return CARD_BACK_PATH
        
        return os.path.join(CONDITION_CARDS_DIR, filename)
    
    def draw(self, highlighted_pos=None):
        """
        보드를 화면에 그리기
        
        Args:
            highlighted_pos: 하이라이트할 위치 (row, col) 튜플 또는 None
        """
        for pos in self.board.track_positions:
            self.card_images[pos].draw()

            if highlighted_pos and highlighted_pos == pos:
                self.highlights[pos].draw()
    
    def get_clicked_position(self, mouse_pos):
        """
        마우스 클릭 위치에 해당하는 카드 위치 반환
        
        Args:
            mouse_pos: (x, y) 마우스 좌표 (PsychoPy 좌표계)
        
        Returns:
            (row, col) 튜플 또는 None (클릭이 카드 밖인 경우)
        """
        mx, my = mouse_pos
        
        for pos in self.board.track_positions:
            image = self.card_images[pos]

            if image.contains((mx, my)):
                return pos
        
        return None


# 테스트 코드
if __name__ == "__main__":
    # 경고 억제
    import warnings
    warnings.filterwarnings('ignore')
    from psychopy import logging
    logging.console.setLevel(logging.ERROR)
    
    from psychopy import core
    from game_func.board_class import ConditionBoard
    from set_opts.set_visual_opt import set_visual_opt
    from utils.card_matcher import get_condition_text
    
    print("\n### BoardRenderer 테스트 ###\n")
    
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
    
    # 보드 생성
    board = ConditionBoard()
    
    # 렌더러 생성
    renderer = BoardRenderer(win, board)
    
    # 타이틀 텍스트
    title = visual.TextStim(
        win=win,
        text="운동장 조건 카드 보드 (클릭하여 테스트, ESC로 종료)",
        pos=(0, HEIGHT / 2 - 70),
        height=40,
        color=[255, 255, 255],
        colorSpace='rgb255'
    )
    
    # 마우스 생성
    mouse = visual.event.Mouse(win=win)
    
    print("렌더링 시작...")
    print("마우스로 카드를 클릭하면 하이라이트됩니다.")
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
                condition = board.get_condition(pos[0], pos[1])
                print(f"클릭: {pos}, 조건: {get_condition_text(condition)}")
            
            # 더블 클릭 방지
            core.wait(0.2)
        
        # 화면 그리기
        title.draw()
        renderer.draw(highlighted_pos=highlighted)
        win.flip()
    
    win.close()
    core.quit()
    
    print("[OK] BoardRenderer 테스트 완료!")
