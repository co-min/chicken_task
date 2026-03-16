# 튜토리얼

import sys
from pathlib import Path
from psychopy import event

try:
	from ..config import KEY_EXIT
except ImportError:
	sys.path.insert(0, str(Path(__file__).parent.parent))
	from config import KEY_EXIT


def run_tutorial_phase(win, ui_elements):
	"""
	간단 튜토리얼 화면.

	Returns:
		str: 'continue' 또는 'exit'
	"""
	ui_elements.instruction_text.text = "튜토리얼"
	ui_elements.message_text.text = (
		"1) 닭을 선택하세요 (Chase / Flight)\n"
		"2) 조건에 맞는 카드를 찾으세요\n"
		"3) 실패하면 PC 차례로 넘어갑니다\n\n"
		"스페이스바로 계속 / ESC로 종료"
	)
	ui_elements.message_text.color = [255, 255, 255]
	ui_elements.timer_text.text = ""
	ui_elements.score_text.text = ""

	ui_elements.instruction_text.draw()
	ui_elements.message_text.draw()
	win.flip()

	keys = event.waitKeys(keyList=['space', KEY_EXIT])
	if keys and KEY_EXIT in keys:
		return 'exit'
	return 'continue'