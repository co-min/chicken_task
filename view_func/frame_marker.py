"""
frame_marker.py
===============
이 모듈은 화면에 흰색 사각형 마커를 그리는 기능을 제공합니다.
주로 시각 자극의 특정 영역을 강조하거나 표시하는 용도로 사용됩니다.

주요 기능:
- 지정한 위치와 크기로 흰색 사각형 마커 그리기
- 테두리와 내부가 모두 흰색으로 채워진 사각형 생성
"""

# PsychoPy 라이브러리: 심리학 실험을 위한 파이썬 패키지
# visual 모듈은 화면에 시각적 자극(stimulus)을 그리는 기능을 제공
from psychopy import visual


def draw_white_marker(win, pos, size):
    """
    화면의 지정된 위치에 흰색 사각형 마커를 그립니다.
    
    이 함수는 시각 자극 실험에서 특정 영역을 표시하거나 강조할 때 사용됩니다.
    예를 들어, 참가자가 주시해야 할 위치를 표시하거나, 
    프레임 동기화를 위한 마커로 사용될 수 있습니다.
    
    Parameters:
    -----------
    win : psychopy.visual.Window
        PsychoPy 윈도우 객체 (그림을 그릴 화면)
        - psychopy에서 제공하는 Window 객체
        - 실험 자극이 표시되는 화면을 나타냄
        
    pos : tuple (x, y)
        마커를 그릴 위치의 좌표 (픽셀 단위)
        - (x, y) 형태의 튜플
        - 픽셀 좌표계 사용 (units='pix' 파라미터로 지정됨)
        
    size : tuple (width, height)
        마커의 크기 (너비, 높이) (픽셀 단위)
        - (width, height) 형태의 튜플
        - 픽셀 단위로 크기 지정
        
    Returns:
    --------
    None
        화면에 직접 그리며 반환값은 없음
        
    동작 방식:
    ----------
    1. visual.Rect로 사각형 마커 생성
    2. 테두리와 내부를 모두 흰색으로 설정
    3. marker.draw()로 화면에 마커 렌더링
    
    사용 예시:
    ----------
    Eye-tracking 실험에서 프레임 동기화를 위해 화면 모서리에 
    작은 흰색 마커를 그려서 비디오 프레임과 동기화하는 용도로 사용 가능
    """
    # psychopy.visual.Rect: 사각형 모양의 시각 자극 생성
    marker = visual.Rect(
        win,                    # 그림을 그릴 PsychoPy 윈도우 객체
        width=size[0],          # 마커의 너비 (픽셀 단위)
        height=size[1],         # 마커의 높이 (픽셀 단위)
        fillColor='white',      # 사각형 내부를 흰색으로 채움
        lineColor='white',      # 사각형 테두리도 흰색으로 설정
        pos=pos,                # 화면 상의 위치 (x, y 좌표)
        units='pix'             # 좌표와 크기를 픽셀 단위로 지정
    )
    
    # 생성된 마커를 화면 버퍼에 그림
    # 실제 화면에 표시되려면 win.flip()이 호출되어야 함
    marker.draw()
    