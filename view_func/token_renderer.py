# view_func/token_renderer.py
# 토큰(Chase, Octopus, Flight) 렌더링

from psychopy import visual
import os
from config import (
    BOARD_LEFT_EDGE, BOARD_DECK_TOP_MARGIN,
    BOARD_CARD_WIDTH, BOARD_CARD_HEIGHT, BOARD_CARD_SPACING,
    WIDTH, HEIGHT,
    TOKEN_SIZE
)

# 이미지 경로
STIMULI_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'stimuli')
TOKENS_DIR = os.path.join(STIMULI_DIR, 'tokens')


class TokenRenderer:

    def __init__(self, win, token_manager):
        self.win = win
        self.token_manager = token_manager
        
        # 토큰 비주얼 요소
        self.token_stims = {}
        
        self._create_visuals()
    
    def _create_visuals(self):
        """토큰 비주얼 생성"""
        image_name_by_token = {
            'chase': 'chase.png',
            'octopus': 'octopus.png',
            'flight': 'flight.png',
        }

        for token_name in self.token_manager.tokens:
            file_name = image_name_by_token.get(token_name, 'octopus.png')
            self.token_stims[token_name] = visual.ImageStim(
                win=self.win,
                image=os.path.join(TOKENS_DIR, file_name),
                size=(TOKEN_SIZE, TOKEN_SIZE)
            )
    
    def _get_card_center(self, row, col):
        """특정 카드 위치의 중심 좌표 반환 (PsychoPy 좌표계)"""
        left_x = BOARD_LEFT_EDGE + col * (BOARD_CARD_WIDTH + BOARD_CARD_SPACING)
        center_x = left_x + BOARD_CARD_WIDTH / 2
        x = center_x - WIDTH / 2

        top_y = BOARD_DECK_TOP_MARGIN + row * (BOARD_CARD_HEIGHT + BOARD_CARD_SPACING)
        center_y = top_y + BOARD_CARD_HEIGHT / 2
        y = HEIGHT / 2 - center_y

        return (x, y)
    
    def draw(self):
        """토큰들을 화면에 그리기"""
        all_positions = self.token_manager.get_all_positions()
        for token_name, token_pos in all_positions.items():
            if token_pos is None:
                continue
            stim = self.token_stims.get(token_name)
            if stim is None:
                continue

            x, y = self._get_card_center(token_pos[0], token_pos[1])
            stim.pos = (x, y)
            stim.draw()
    
    def draw_with_animation(self, progress=1.0):
        """
        애니메이션 진행률에 따라 그리기
        
        Args:
            progress: 0.0 (시작) ~ 1.0 (완료)
                      향후 애니메이션 구현 시 사용
        """
        # 현재는 일반 draw()와 동일 (향후 확장 가능)
        self.draw()

