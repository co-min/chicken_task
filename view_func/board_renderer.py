# view_func/board_renderer.py
# 운동장 조건 카드 보드 렌더링

from psychopy import visual
import os
from config import (
    BOARD_ROWS, BOARD_COLS,
    BOARD_LEFT_MARGIN, BOARD_TOP_MARGIN,
    BOARD_CARD_WIDTH, BOARD_CARD_HEIGHT, BOARD_CARD_SPACING,
    WIDTH, HEIGHT,
    COLOR_RGB,
    TEXT_SIZE,
    HIGHLIGHT_COLOR, HIGHLIGHT_WIDTH
)
from utils.card_matcher import get_condition_text

# 이미지 경로
STIMULI_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'stimuli')
CONDITION_CARDS_DIR = os.path.join(STIMULI_DIR, 'condition_cards')


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
        self.card_images = []  # 카드 이미지
        self.highlights = []   # 하이라이트 테두리
        
        self._create_visuals()
    
    def _create_visuals(self):
        """모든 카드의 비주얼 요소를 생성"""
        for row in range(BOARD_ROWS):
            row_images = []
            row_highlights = []
            
            for col in range(BOARD_COLS):
                # 화면 좌표 계산 (PsychoPy는 중앙이 원점)
                x = self._get_card_x(col)
                y = self._get_card_y(row)
                
                # 조건에 맞는 이미지 파일 경로 가져오기
                condition = self.board.get_condition(row, col)
                image_path = self._get_condition_image_path(condition)
                
                # 카드 이미지
                card_image = visual.ImageStim(
                    win=self.win,
                    image=image_path,
                    pos=(x, y),
                    size=(BOARD_CARD_WIDTH, BOARD_CARD_HEIGHT)
                )
                row_images.append(card_image)
                
                # 하이라이트 (평소에는 안 보임)
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
                row_highlights.append(highlight)
            
            self.card_images.append(row_images)
            self.highlights.append(row_highlights)
    
    def _get_card_x(self, col):
        """
        카드의 x 좌표 계산 (PsychoPy 좌표계)
        
        Args:
            col: 열 인덱스 (0-8)
        
        Returns:
            x 좌표 (픽셀, 중앙 기준)
        """
        left_x = BOARD_LEFT_MARGIN + col * (BOARD_CARD_WIDTH + BOARD_CARD_SPACING)
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
        top_y = BOARD_TOP_MARGIN + row * (BOARD_CARD_HEIGHT + BOARD_CARD_SPACING)
        center_y = top_y + BOARD_CARD_HEIGHT / 2
        # PsychoPy는 위쪽이 양수, 아래쪽이 음수 (반전)
        return HEIGHT / 2 - center_y
    
    def _get_condition_image_path(self, condition):
        """
        조건에 맞는 이미지 파일 경로 반환
        
        Args:
            condition: {'type': str, 'value': str/int}
        
        Returns:
            이미지 파일 경로
        """
        cond_type = condition['type']
        cond_value = condition['value']
        
        if cond_type == 'color':
            filename = f"color_{cond_value}.png"
        elif cond_type == 'shape':
            filename = f"shape_{cond_value}.png"
        else:  # number
            filename = f"number_{cond_value}.png"
        
        return os.path.join(CONDITION_CARDS_DIR, filename)
    
    def draw(self, highlighted_pos=None):
        """
        보드를 화면에 그리기
        
        Args:
            highlighted_pos: 하이라이트할 위치 (row, col) 튜플 또는 None
        """
        for row in range(BOARD_ROWS):
            for col in range(BOARD_COLS):
                # 카드 이미지 그리기
                self.card_images[row][col].draw()
                
                # 하이라이트 그리기 (해당 위치인 경우만)
                if highlighted_pos and highlighted_pos == (row, col):
                    self.highlights[row][col].draw()
    
    def get_clicked_position(self, mouse_pos):
        """
        마우스 클릭 위치에 해당하는 카드 위치 반환
        
        Args:
            mouse_pos: (x, y) 마우스 좌표 (PsychoPy 좌표계)
        
        Returns:
            (row, col) 튜플 또는 None (클릭이 카드 밖인 경우)
        """
        mx, my = mouse_pos
        
        for row in range(BOARD_ROWS):
            for col in range(BOARD_COLS):
                image = self.card_images[row][col]
                
                # 카드 영역 체크 (contains() 메서드 사용)
                if image.contains((mx, my)):
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
    from game_func.board_class import ConditionBoard
    from set_opts.set_visual_opt import set_visual_opt
    
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
