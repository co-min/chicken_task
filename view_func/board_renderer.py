# view_func/board_renderer.py
# 운동장 조건 카드 보드 렌더링

from psychopy import visual
import os
from config import (
    BOARD_LEFT_EDGE, BOARD_DECK_TOP_MARGIN,
    BOARD_CARD_WIDTH, BOARD_CARD_HEIGHT, BOARD_CARD_SPACING,
    WIDTH, HEIGHT,
    HIGHLIGHT_COLOR, HIGHLIGHT_WIDTH,
    BONUS_BORDER_COLOR, BONUS_BORDER_WIDTH, BONUS_LABEL_COLOR, TEXT_SIZE,
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
        self.card_images = {}   # {(row, col): ImageStim}
        self.highlights = {}    # {(row, col): Rect}  — 타겟 하이라이트
        self.bonus_borders = {} # {(row, col): Rect}  — 보너스 칸 금색 테두리
        self.bonus_labels = {}  # {(row, col): TextStim} — "×2" 레이블

        self._create_visuals()
    
    def _create_visuals(self):
        """모든 카드의 비주얼 요소를 생성"""
        _label_h = max(8, round(TEXT_SIZE * 0.45))  # "×2" 레이블 높이

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

            # 타겟 하이라이트 (기존)
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

            # 보너스 칸 금색 테두리
            bonus_border = visual.Rect(
                win=self.win,
                width=BOARD_CARD_WIDTH + BONUS_BORDER_WIDTH * 2,
                height=BOARD_CARD_HEIGHT + BONUS_BORDER_WIDTH * 2,
                pos=(x, y),
                fillColor=None,
                lineColor=BONUS_BORDER_COLOR,
                lineWidth=BONUS_BORDER_WIDTH,
                colorSpace='rgb255',
                autoDraw=False
            )
            self.bonus_borders[(row, col)] = bonus_border

            # 보너스 칸 "×2" 레이블 (카드 우상단 모서리)
            label_x = x + BOARD_CARD_WIDTH / 2 - _label_h * 0.6
            label_y = y + BOARD_CARD_HEIGHT / 2 - _label_h * 0.6
            bonus_label = visual.TextStim(
                win=self.win,
                text='×2',
                pos=(label_x, label_y),
                height=_label_h,
                color=BONUS_LABEL_COLOR,
                colorSpace='rgb255',
                bold=True,
                autoDraw=False
            )
            self.bonus_labels[(row, col)] = bonus_label
    
    def _get_card_x(self, col):
        """카드의 x 좌표 계산 (PsychoPy 좌표계)"""
        left_x = BOARD_LEFT_EDGE + col * (BOARD_CARD_WIDTH + BOARD_CARD_SPACING)
        center_x = left_x + BOARD_CARD_WIDTH / 2
        return center_x - WIDTH / 2
    
    def _get_card_y(self, row):
        """카드의 y 좌표 계산 (PsychoPy 좌표계)"""
        top_y = BOARD_DECK_TOP_MARGIN + row * (BOARD_CARD_HEIGHT + BOARD_CARD_SPACING)
        center_y = top_y + BOARD_CARD_HEIGHT / 2
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
    
    def update_board(self, new_board):
        """
        advance_round() 후 새 ConditionBoard 참조로 교체 및 비주얼 갱신.
        deck_renderer.update_deck()과 동일한 패턴.
        이 메서드를 호출하지 않으면 board_renderer.board가 구 객체를 가리켜
        화면 조건과 game_state 조건이 불일치하여 정답 카드를 뒤집어도 실패 처리된다.
        """
        self.board = new_board
        self.refresh()

    def refresh(self):
        """보드 재셔플 후 각 위치의 조건 이미지 및 보너스 표시를 갱신"""
        for pos in self.board.track_positions:
            row, col = pos
            condition = self.board.get_condition(row, col)
            image_path = self._get_condition_image_path(condition)
            self.card_images[pos].image = image_path
            # 보너스 여부는 draw()에서 매 프레임 조건을 읽어 판단하므로 별도 처리 불필요

    def draw(self, highlighted_pos=None):
        """
        보드를 화면에 그리기

        렌더링 순서 (z-order):
          1. 카드 이미지
          2. 보너스 금색 테두리 + "×2" 레이블  ← 카드 위
          3. 타겟 하이라이트                    ← 최상단 (보너스 테두리 위)

        Args:
            highlighted_pos: 하이라이트할 위치 (row, col) 튜플 또는 None
        """
        for pos in self.board.track_positions:
            self.card_images[pos].draw()

            # 보너스 칸: 금색 테두리 + "×2" 레이블
            condition = self.board.get_condition(pos[0], pos[1])
            if condition and condition.get('bonus') == 'double_score':
                self.bonus_borders[pos].draw()
                self.bonus_labels[pos].draw()

            # 타겟 하이라이트 (보너스 테두리보다 위에 그려서 명확히 구분)
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
