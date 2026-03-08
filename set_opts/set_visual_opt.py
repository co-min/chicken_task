# set_opts/set_visual_opt.py
# Visual options setup

from config import WIDTH, HEIGHT, BG_COLOR, FULLSCREEN

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
        'units': 'pix',
        'color_space': 'rgb255',
        'allow_gui': False,
        'check_timing': False,
        'screen': 0,  # 기본 모니터
        'pos': None   # None으로 설정하면 중앙 배치
    }
    
    return visual_opt
