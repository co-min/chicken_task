# 피드백

from psychopy import core

import time

try:
	from ..view_func.frame_marker import blink_frame_marker, trigger_frame_marker
	from ..utils.labjack_triggers import send_trigger, send_trigger_async, reset_trigger
	from ..utils.timer import checked_wait
except ImportError:
	import sys
	from pathlib import Path
	sys.path.insert(0, str(Path(__file__).parent.parent))
	from view_func.frame_marker import blink_frame_marker, trigger_frame_marker
	from utils.labjack_triggers import send_trigger, send_trigger_async, reset_trigger
	from utils.timer import checked_wait

_TRIGGER_PULSE_S = 0.005  # TTL 펄스 폭 (send_trigger 기본값과 동일)


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
	frame_drop_logger=None,
):
	"""공통 피드백 화면을 렌더링하고 지정 시간만큼 대기한다.

	Args:
		labjack_handle: LabJack T4 핸들. None이면 트리거 비활성화.
		trigger_code: 피드백 onset에 전송할 TTL 코드.
		              210=성공, 211=실패, 212=타임아웃, 0=전송 안 함.
		frame_drop_logger: FrameDropLogger 인스턴스 (선택). 프레임 드랍 기록용.
	"""
	# 호출 전 게임 로직 처리 시간이 길 수 있으므로 기준점 초기화
	if frame_drop_logger:
		frame_drop_logger.reset()

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
	# sEEG 동기화: TTL을 flip 직전에 전송해 포토다이오드 ON보다 먼저 sEEG에 도착하도록 한다.
	# TTL–포토다이오드 오프셋이 일정해지므로 사후 보정이 가능하다.
	_send_trigger = labjack_handle is not None and bool(trigger_code)
	if _send_trigger:
		send_trigger_async(labjack_handle, trigger_code)
	win.flip()
	if frame_drop_logger:
		frame_drop_logger.after_flip(core.getTime(), context='feedback')

	# Deferred reset: flip 반환 후 5ms 펄스가 완료되도록 busy-wait 후 LOW 리셋.
	# checked_wait(duration) 보다 먼저 실행되므로 피드백 표시 시간에는 영향이 없다.
	if _send_trigger:
		_flip_perf_t = time.perf_counter()
		_deadline = _flip_perf_t + _TRIGGER_PULSE_S
		while time.perf_counter() < _deadline:
			pass
		reset_trigger(labjack_handle)

	_feedback_deadline = core.getTime() + duration
	while core.getTime() < _feedback_deadline:
		board_renderer.draw(highlighted_pos)
		deck_renderer.draw()
		token_renderer.draw()
		ui_elements.draw_persistent_hud()
		ui_elements.message_text.draw()
		ui_elements.instruction_text.draw()
		blink_frame_marker(win)
		win.flip()
		if frame_drop_logger:
			frame_drop_logger.after_flip(core.getTime(), context='feedback')

	# 피드백 종료 후 호출부의 게임 로직 처리 시간이 길 수 있으므로 기준점 초기화
	if frame_drop_logger:
		frame_drop_logger.reset()