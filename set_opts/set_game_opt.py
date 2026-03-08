# set_opts/set_game_opt.py
# Game options setup

from config import (
    PC_SUCCESS_RATE, 
    TURN_TIME_LIMIT, 
    CARD_FLIP_DURATION,
    USE_PRACTICE,
    PRACTICE_TRIALS
)

def set_game_opt():
    """
    Set game options
    
    Returns:
        dict: Game options including difficulty, timing, etc.
    """
    game_opt = {
        'pc_success_rate': PC_SUCCESS_RATE,
        'turn_time_limit': TURN_TIME_LIMIT,
        'card_flip_duration': CARD_FLIP_DURATION,
        'use_practice': USE_PRACTICE,
        'practice_trials': PRACTICE_TRIALS
    }
    
    return game_opt
