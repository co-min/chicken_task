# 시작 화면

import sys
from pathlib import Path
from psychopy import event

try:
	from ..config import KEY_EXIT
except ImportError:
	sys.path.insert(0, str(Path(__file__).parent.parent))
	from config import KEY_EXIT


def run_starting_phase(win, ui_elements):
	"""
	시작 안내 화면 표시.

	Returns:
		str: 'continue' 또는 'exit'
	"""
	ui_elements.instruction_text.text = "Chicken Task 게임에 오신 것을 환영합니다!"
	ui_elements.message_text.text = "스페이스바를 눌러 게임을 시작하세요"
	ui_elements.message_text.color = [0, 255, 0]
	ui_elements.timer_text.text = ""
	ui_elements.score_text.text = ""

	ui_elements.instruction_text.draw()
	ui_elements.message_text.draw()
	win.flip()

	keys = event.waitKeys(keyList=['space', KEY_EXIT])
	if keys and KEY_EXIT in keys:
		return 'exit'

	print("  ✓ 시작 화면 표시 완료")
	return 'continue'
