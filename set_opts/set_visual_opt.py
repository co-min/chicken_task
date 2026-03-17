# set_opts/set_visual_opt.py
# Visual options setup

from config import (
    WIDTH,
    HEIGHT,
    BG_COLOR,
    FULLSCREEN,
    AUTO_DETECT_WINDOW_SIZE,
    FORCE_WINDOWED_MODE,
    MONITOR_NAME,
)

def set_visual_opt():
    """
    Set visual options for the experiment
    
    Returns:
        dict: Visual options including window size, colors, etc.
    """
    visual_opt = {
        'win_size': [WIDTH, HEIGHT],
        'bg_color': BG_COLOR,
        'fullscreen': FULLSCREEN,
        'auto_detect_window_size': AUTO_DETECT_WINDOW_SIZE,
        'force_windowed_mode': FORCE_WINDOWED_MODE,
        'units': 'pix',
        'color_space': 'rgb255',
        'allow_gui': False,
        'check_timing': False,
        'screen': 0,  # 기본 모니터
        'monitor_name': MONITOR_NAME,
        'pos': None   # None으로 설정하면 중앙 배치
    }
    
    return visual_opt
