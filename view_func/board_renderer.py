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
    SEQ_MEMORY_BORDER_COLOR, SEQ_MEMORY_BORDER_WIDTH,
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
        self.card_images = {}     # {(row, col): ImageStim}
        self.highlights = {}      # {(row, col): Rect}  — 타겟 하이라이트
        self.seq_group_border = None  # Rect  — 순차 메모리 전체 타겟 묶음 테두리 (1개)
        self.seq_done_overlays = {}   # {(row, col): Rect}  — 완료된 순차 스텝 어두운 오버레이
        self.bonus_borders = {}   # {(row, col): Rect}  — 보너스 칸 금색 테두리
        self.bonus_labels = {}    # {(row, col): TextStim} — "×2" 레이블

        self._create_visuals()
    
    def _create_visuals(self):
        """모든 카드의 비주얼 요소를 생성"""
        _label_h = max(12, round(TEXT_SIZE * 0.5))  # "×2" 레이블 높이

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

            # 완료된 순차 스텝 어두운 오버레이
            done_overlay = visual.Rect(
                win=self.win,
                width=BOARD_CARD_WIDTH,
                height=BOARD_CARD_HEIGHT,
                pos=(x, y),
                fillColor=[0, 0, 0],
                lineColor=None,
                colorSpace='rgb255',
                opacity=0.55,
                autoDraw=False
            )
            self.seq_done_overlays[(row, col)] = done_overlay

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

        # 순차 메모리 전체 타겟을 감싸는 그룹 테두리 (위치·크기는 draw()에서 동적 업데이트)
        self.seq_group_border = visual.Rect(
            win=self.win,
            width=BOARD_CARD_WIDTH,
            height=BOARD_CARD_HEIGHT,
            pos=(0, 0),
            fillColor=None,
            lineColor=SEQ_MEMORY_BORDER_COLOR,
            lineWidth=SEQ_MEMORY_BORDER_WIDTH,
            colorSpace='rgb255',
            autoDraw=False
        )

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

    def draw(self, highlighted_pos=None, seq_cells=None, done_cells=None):
        """
        보드를 화면에 그리기

        렌더링 순서 (z-order):
          1. 카드 이미지
          2. 보너스 금색 테두리 + "×2" 레이블  ← 카드 위
          3. 완료된 순차 스텝 어두운 오버레이   ← 체크박스처럼 어둡게
          4. 순차 메모리 그룹 테두리 (전체 타겟을 하나로 묶음)
          5. 타겟 하이라이트 (노란색)            ← 최상단 (현재 스텝 강조)

        Args:
            highlighted_pos: 현재 타겟 위치 (row, col) 튜플 또는 None
            seq_cells: 순차 메모리 전체 타겟 위치 리스트 [(row,col), ...] 또는 None
            done_cells: 이미 완료된 순차 스텝 위치 리스트 [(row,col), ...] 또는 None
        """
        done_set = set(done_cells) if done_cells else set()

        for pos in self.board.track_positions:
            self.card_images[pos].draw()

            # 보너스 칸: 금색 테두리 + "×2" 레이블
            condition = self.board.get_condition(pos[0], pos[1])
            if condition and condition.get('bonus') == 'double_score':
                self.bonus_borders[pos].draw()
                self.bonus_labels[pos].draw()

            # 완료된 순차 스텝: 어두운 오버레이 (체크된 느낌)
            if pos in done_set:
                self.seq_done_overlays[pos].draw()

            # 타겟 하이라이트 (최상단 — 현재 스텝 강조)
            if highlighted_pos and highlighted_pos == pos:
                self.highlights[pos].draw()

        # 순차 메모리 전체 타겟을 하나의 박스 테두리로 묶어서 표시
        if seq_cells:
            pad = SEQ_MEMORY_BORDER_WIDTH + 4
            xs = [self._get_card_x(c) for _, c in seq_cells]
            ys = [self._get_card_y(r) for r, _ in seq_cells]
            min_x = min(xs) - BOARD_CARD_WIDTH  / 2 - pad
            max_x = max(xs) + BOARD_CARD_WIDTH  / 2 + pad
            min_y = min(ys) - BOARD_CARD_HEIGHT / 2 - pad
            max_y = max(ys) + BOARD_CARD_HEIGHT / 2 + pad
            self.seq_group_border.pos    = ((min_x + max_x) / 2, (min_y + max_y) / 2)
            self.seq_group_border.width  = max_x - min_x
            self.seq_group_border.height = max_y - min_y
            self.seq_group_border.draw()
    
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


