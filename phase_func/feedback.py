# 피드백

from psychopy import core


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
):
	"""공통 피드백 화면을 렌더링하고 지정 시간만큼 대기한다."""
	ui_elements.message_text.text = message
	ui_elements.message_text.color = color

	board_renderer.draw(highlighted_pos)
	deck_renderer.draw()
	token_renderer.draw()
	ui_elements.timer_text.draw()
	ui_elements.score_text.draw()
	ui_elements.message_text.draw()
	ui_elements.instruction_text.draw()
	win.flip()
	core.wait(duration)