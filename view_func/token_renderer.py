from psychopy import visual
import os
from config import (
    BOARD_LEFT_EDGE, BOARD_DECK_TOP_MARGIN,
    BOARD_CARD_WIDTH, BOARD_CARD_HEIGHT, BOARD_CARD_SPACING,
    WIDTH, HEIGHT,
    TOKEN_SIZE
)

# img path
STIMULI_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'stimuli')
TOKENS_DIR = os.path.join(STIMULI_DIR, 'tokens')


class TokenRenderer:

    def __init__(self, win, token_manager):
        self.win = win
        self.token_manager = token_manager
        
        # token visual
        self.token_stims = {}
        
        self._create_visuals()
    
    def _create_visuals(self):
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
        left_x = BOARD_LEFT_EDGE + col * (BOARD_CARD_WIDTH + BOARD_CARD_SPACING)
        center_x = left_x + BOARD_CARD_WIDTH / 2
        x = center_x - WIDTH / 2

        top_y = BOARD_DECK_TOP_MARGIN + row * (BOARD_CARD_HEIGHT + BOARD_CARD_SPACING)
        center_y = top_y + BOARD_CARD_HEIGHT / 2
        y = HEIGHT / 2 - center_y

        return (x, y)
    
    def draw(self):
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
        self.draw()

