# 튜토리얼

import sys
from pathlib import Path
from psychopy import core, event

try:
	from ..config import KEY_EXIT, TEXT_COLOR, FRAME_MARKER_POS, FRAME_MARKER_SIZE, SAVE_FRAME_LOG
	from ..view_func.frame_marker import draw_white_marker
	from ..save_func.save_frame_log import save_frame_log_tutorial
except ImportError:
	sys.path.insert(0, str(Path(__file__).parent.parent))
	from config import KEY_EXIT, TEXT_COLOR, FRAME_MARKER_POS, FRAME_MARKER_SIZE, SAVE_FRAME_LOG
	from view_func.frame_marker import draw_white_marker
	from save_func.save_frame_log import save_frame_log_tutorial


def run_tutorial_phase(win, ui_elements, subject_id='default'):
	"""
	간단 튜토리얼 화면.

	Returns:
		str: 'continue' 또는 'exit'
	"""
	# 원래 위치 저장
	orig_instruction_pos = ui_elements.instruction_text.pos
	orig_message_pos = ui_elements.message_text.pos

	ui_elements.instruction_text.text = "게임 설명"
	ui_elements.message_text.text = (
		"1) 닭을 선택하세요 (Chase / Flight)\n"
		"2) 조건에 맞는 카드를 찾으세요\n"
		"3) 실패하면 문어 차례로 넘어갑니다\n\n\n"
		"스페이스바로 계속 / ESC로 종료"
	)
	ui_elements.message_text.color=TEXT_COLOR
	ui_elements.timer_text.text = ""
	ui_elements.score_text.text = ""

	# 화면 중앙 정렬
	ui_elements.instruction_text.pos = (0, 150)
	ui_elements.message_text.pos = (0, -50)

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
				'phase': 'tutorial',
				'frame_count': frame_count,
				'time': flip_time,
				'dt': dt,
				'marker_on': True,
			})
		frame_count += 1

		keys = event.getKeys(keyList=['space', KEY_EXIT])
		if keys:
			break

	# 위치 복원
	ui_elements.instruction_text.pos = orig_instruction_pos
	ui_elements.message_text.pos = orig_message_pos

	if SAVE_FRAME_LOG:
		print(f"  - tutorial frame log: {len(frame_log)} frames")
		save_frame_log_tutorial(frame_log, subject_id)
	if keys and KEY_EXIT in keys:
		return 'exit'
	return 'continue'