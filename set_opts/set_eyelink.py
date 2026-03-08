# set_opts/set_eyelink.py
# EyeLink eye tracker options setup

from config import WIDTH, HEIGHT

def set_eye_opt():
    """
    Set EyeLink eye tracking options
    
    Returns:
        dict: Eye tracking options
    """
    eye_opt = {
        'screen_width': WIDTH,
        'screen_height': HEIGHT,
        'sample_rate': 1000,
        'track_eyes': 'RIGHT'
    }
    
    return eye_opt
