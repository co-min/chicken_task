from psychopy import visual
from ..config import FRAME_MARKER_POS, FRAME_MARKER_SIZE, FRAME_MARKER_DURATION


_current_frame = 0
_event_frame = -(FRAME_MARKER_DURATION + 1)

_marker_rect = None
_marker_win  = None
_marker_pos  = None


def trigger_frame_marker():
    global _event_frame, _current_frame
    _event_frame = _current_frame


def blink_frame_marker(win):
    global _current_frame
    _current_frame += 1
    if _current_frame - _event_frame < FRAME_MARKER_DURATION:
        if FRAME_MARKER_POS is None:
            w, h = win.size
            pos = (
                -w // 2 + FRAME_MARKER_SIZE[0] // 2,
                -h // 2 + FRAME_MARKER_SIZE[1] // 2,
            )
        else:
            pos = FRAME_MARKER_POS
        draw_white_marker(win, pos, FRAME_MARKER_SIZE)


def draw_white_marker(win, pos, size):
    global _marker_rect, _marker_win, _marker_pos
    if _marker_rect is None or _marker_win is not win or _marker_pos != pos:
        _marker_rect = visual.Rect(
            win,
            width=size[0],          
            height=size[1],         
            fillColor='white',      
            lineColor='white',      
            pos=pos,                
            units='pix'             
        )
        _marker_win = win
        _marker_pos = pos

    _marker_rect.draw()
    