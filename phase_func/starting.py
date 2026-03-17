# 시작 화면

import sys
from pathlib import Path
from psychopy import event

try:
	from ..config import KEY_EXIT, TEXT_COLOR
except ImportError:
	sys.path.insert(0, str(Path(__file__).parent.parent))
	from config import KEY_EXIT, TEXT_COLOR


def run_starting_phase(win, ui_elements):
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

	ui_elements.instruction_text.draw()
	ui_elements.message_text.draw()
	win.flip()

	keys = event.waitKeys(keyList=['space', KEY_EXIT])
	if keys and KEY_EXIT in keys:
		return 'exit'
	# 위치 복원
	ui_elements.instruction_text.pos = orig_instruction_pos
	ui_elements.message_text.pos = orig_message_pos

	print("  ✓ 시작 화면 표시 완료")
	return 'continue'
