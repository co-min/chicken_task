# 시작 화면

import sys
from pathlib import Path
from psychopy import core, event

try:
	from ..config import KEY_EXIT, TEXT_COLOR, FRAME_MARKER_POS, FRAME_MARKER_SIZE, SAVE_FRAME_LOG
	from ..view_func.frame_marker import draw_white_marker
	from ..save_func.save_frame_log import save_frame_log_starting
except ImportError:
	sys.path.insert(0, str(Path(__file__).parent.parent))
	from config import KEY_EXIT, TEXT_COLOR, FRAME_MARKER_POS, FRAME_MARKER_SIZE, SAVE_FRAME_LOG
	from view_func.frame_marker import draw_white_marker
	from save_func.save_frame_log import save_frame_log_starting


def run_starting_phase(win, ui_elements, subject_id='default'):
	"""
	시작 안내 화면 표시.

	Returns:
		str: 'continue' 또는 'exit'
	"""

	# 원래 위치 저장
	orig_instruction_pos = ui_elements.instruction_text.pos
	orig_message_pos = ui_elements.message_text.pos

	ui_elements.instruction_text.text = "환영합니다!"
	ui_elements.message_text.text = "스페이스바를 눌러 게임을 시작하세요"
	ui_elements.message_text.color = TEXT_COLOR
	ui_elements.timer_text.text = ""
	ui_elements.score_text.text = ""

	# 화면 중앙 정렬
	ui_elements.instruction_text.pos = (0, 150)
	ui_elements.message_text.pos = (0, 30)

	# === 로깅 변수 초기화 ===
	frame_count = 0
	frame_log = []
	clock = core.Clock()
	prev_flip_time = None

	while True:
		ui_elements.instruction_text.draw()
		ui_elements.message_text.draw()
		draw_white_marker(win, FRAME_MARKER_POS, FRAME_MARKER_SIZE)
		win.flip()

		flip_time = clock.getTime()
		dt = 0.0 if prev_flip_time is None else (flip_time - prev_flip_time)
		prev_flip_time = flip_time

		if SAVE_FRAME_LOG:
			frame_log.append({
				'phase': 'starting',
				'frame_count': frame_count,
				'time': flip_time,
				'dt': dt,
				'marker_on': True,
			})
		frame_count += 1

		keys = event.getKeys(keyList=['space', KEY_EXIT])
		if keys:
			break

	if keys and KEY_EXIT in keys:
		if SAVE_FRAME_LOG:
			print(f"  - starting frame log: {len(frame_log)} frames")
			save_frame_log_starting(frame_log, subject_id)
		# 위치 복원
		ui_elements.instruction_text.pos = orig_instruction_pos
		ui_elements.message_text.pos = orig_message_pos
		return 'exit'
	# 위치 복원
	ui_elements.instruction_text.pos = orig_instruction_pos
	ui_elements.message_text.pos = orig_message_pos

	if SAVE_FRAME_LOG:
		print(f"  - starting frame log: {len(frame_log)} frames")
		save_frame_log_starting(frame_log, subject_id)
	print("  ✓ 시작 화면 표시 완료")
	return 'continue'
