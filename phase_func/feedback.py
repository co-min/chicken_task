# 피드백

from psychopy import core

try:
	from ..view_func.frame_marker import blink_frame_marker, trigger_frame_marker
	from ..utils.labjack_triggers import send_trigger
	from ..utils.timer import checked_wait
except ImportError:
	import sys
	from pathlib import Path
	sys.path.insert(0, str(Path(__file__).parent.parent))
	from view_func.frame_marker import blink_frame_marker, trigger_frame_marker
	from utils.labjack_triggers import send_trigger
	from utils.timer import checked_wait


def run_feedback_phase(
	win,
	ui_elements,
	board_renderer,
	deck_renderer,
	token_renderer,
	message,
	color,
	duration,
	highlighted_pos=None,
	labjack_handle=None,
	trigger_code=0,
):
	"""공통 피드백 화면을 렌더링하고 지정 시간만큼 대기한다.

	Args:
		labjack_handle: LabJack T4 핸들. None이면 트리거 비활성화.
		trigger_code: 피드백 onset에 전송할 TTL 코드.
		              210=성공, 211=실패, 212=타임아웃, 0=전송 안 함.
	"""
	ui_elements.message_text.text = message
	ui_elements.message_text.color = color

	board_renderer.draw(highlighted_pos)
	deck_renderer.draw()
	token_renderer.draw()
	ui_elements.draw_persistent_hud()   # 타이머·라운드·프로그레스 바·점수 (캐시 상태)
	ui_elements.message_text.draw()
	ui_elements.instruction_text.draw()
	trigger_frame_marker()   # 이벤트: 피드백 화면 표시 (성공/실패/타임아웃)
	blink_frame_marker(win)
	# 피드백 화면이 실제로 모니터에 표시되는 순간(VSync)에 맞춰 트리거 전송
	if labjack_handle is not None and trigger_code:
		win.callOnFlip(send_trigger, labjack_handle, trigger_code)
	win.flip()
	checked_wait(duration, label=f"feedback('{message}')")