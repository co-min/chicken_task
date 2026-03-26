# 튜토리얼

import sys
from pathlib import Path
from psychopy import event

try:
	from ..config import KEY_EXIT, TEXT_COLOR
except ImportError:
	sys.path.insert(0, str(Path(__file__).parent.parent))
	from config import KEY_EXIT, TEXT_COLOR


def run_tutorial_phase(win, ui_elements):
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

	ui_elements.instruction_text.draw()
	ui_elements.message_text.draw()
	win.flip()

	keys = event.waitKeys(keyList=['space', KEY_EXIT])

	# 텍스트 초기화 후 위치 복원
	ui_elements.instruction_text.text = ""
	ui_elements.message_text.text = ""
	ui_elements.instruction_text.pos = orig_instruction_pos
	ui_elements.message_text.pos = orig_message_pos

	if keys and KEY_EXIT in keys:
		return 'exit'
	return 'continue'