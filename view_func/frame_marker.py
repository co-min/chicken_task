"""
frame_marker.py
===============
화면에 흰색 사각형 마커를 그리는 기능을 제공
주로 시각 자극의 특정 영역을 강조하거나 표시하는 용도로 사용

주요 기능:
- 지정한 위치와 크기로 흰색 사각형 마커 그리기
- 테두리와 내부가 모두 흰색으로 채워진 사각형 생성
- 이벤트 기반 blink: 특정 이벤트 직후 FRAME_MARKER_DURATION 프레임 동안만 표시
"""
from psychopy import visual

try:
    from ..config import FRAME_MARKER_POS, FRAME_MARKER_SIZE, FRAME_MARKER_DURATION
except ImportError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from config import FRAME_MARKER_POS, FRAME_MARKER_SIZE, FRAME_MARKER_DURATION

# 누적 프레임 카운터 (blink_frame_marker 호출마다 +1)
_current_frame = 0
# 마지막 이벤트가 발생한 프레임 번호 (trigger_frame_marker()가 갱신)
# 초기값을 충분히 작게 설정해 게임 시작 전에는 마커가 보이지 않게 함
_event_frame = -(FRAME_MARKER_DURATION + 1)

# 싱글톤 Rect 캐시: (win 객체, pos, size) 조합이 같으면 재사용
# win이 바뀌면(새 창 생성 시) 자동으로 재생성됨
_marker_rect = None
_marker_win  = None
_marker_pos  = None


def trigger_frame_marker():
    """
    이벤트 발생 시점에 호출: 이후 FRAME_MARKER_DURATION 프레임 동안 마커를 표시한다.
    """
    global _event_frame, _current_frame
    _event_frame = _current_frame


def blink_frame_marker(win):
    """
    매 프레임 win.flip() 직전에 호출.
    trigger_frame_marker()가 불린 뒤 FRAME_MARKER_DURATION 프레임 이내일 때만
    흰색 마커를 버퍼에 그린다. 그 외 프레임은 아무것도 그리지 않는다.
    """
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
            width=size[0],          # 마커의 너비 (픽셀 단위)
            height=size[1],         # 마커의 높이 (픽셀 단위)
            fillColor='white',      # 사각형 내부를 흰색으로 채움
            lineColor='white',      # 사각형 테두리도 흰색으로 설정
            pos=pos,                # 화면 상의 위치 (x, y 좌표)
            units='pix'             # 좌표와 크기를 픽셀 단위로 지정
        )
        _marker_win = win
        _marker_pos = pos

    _marker_rect.draw()
    