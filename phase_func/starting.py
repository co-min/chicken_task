# 시작 화면

import os
import sys
from pathlib import Path
from psychopy import event, visual, core

try:
	from ..config import KEY_EXIT, TEXT_COLOR, GAME_MODES, DEFAULT_GAME_MODE
except ImportError:
	sys.path.insert(0, str(Path(__file__).parent.parent))
	from config import KEY_EXIT, TEXT_COLOR, GAME_MODES, DEFAULT_GAME_MODE


def _build_mode_cards(win):
	"""시작 화면의 모드 선택 카드(이미지+이름) 비주얼 생성."""
	stimuli_dir = os.path.join(Path(__file__).parent.parent, 'stimuli')
	ordered_mode_ids = ['selection1', 'selection2']
	start_x = -195
	spacing_x = 260

	cards = []
	for idx, mode_id in enumerate(ordered_mode_ids):
		mode = GAME_MODES[mode_id]
		x = start_x + (idx * spacing_x)
		y = -120

		preview_rel_path = mode.get('preview_image', 'ui/card_back.png')
		preview_path = os.path.join(stimuli_dir, preview_rel_path)
		if not os.path.exists(preview_path):
			preview_path = os.path.join(stimuli_dir, 'ui', 'card_back.png')

		frame = visual.Rect(
			win=win,
			width=200,
			height=270,
			pos=(x, y),
			fillColor=[110, 110, 110],
			lineColor=[220, 220, 220],
			lineWidth=3,
			colorSpace='rgb255',
		)

		image = visual.ImageStim(
			win=win,
			image=preview_path,
			pos=(x, y + 30),
			size=(120, 160),
		)

		title = visual.TextStim(
			win=win,
			text=mode.get('display_name', mode_id),
			pos=(x, y - 75),
			height=34,
			color=[255, 255, 255],
			colorSpace='rgb255',
			bold=True,
		)

		subtitle = visual.TextStim(
			win=win,
			text=f"트랙 {mode.get('track_length', '-') }칸 / 토큰 {mode.get('token_count', '-') }개",
			pos=(x, y - 110),
			height=20,
			color=[230, 230, 230],
			colorSpace='rgb255',
		)

		cards.append({
			'mode_id': mode_id,
			'frame': frame,
			'image': image,
			'title': title,
			'subtitle': subtitle,
		})

	return cards


def run_starting_phase(win, ui_elements):
	"""
	시작 안내 화면 표시.

	Returns:
		tuple: (status, selected_mode_id)
			- ('continue', mode_id)
			- ('exit', None)
	"""
	mouse = event.Mouse(win=win)
	mode_cards = _build_mode_cards(win)

	# 원래 위치 저장
	orig_instruction_pos = ui_elements.instruction_text.pos
	orig_message_pos = ui_elements.message_text.pos

	ui_elements.instruction_text.text = "환영합니다!"
	ui_elements.message_text.text = "아래 카드 중 하나를 클릭해 시작하세요"
	ui_elements.message_text.color = TEXT_COLOR
	ui_elements.timer_text.text = ""
	ui_elements.score_text.text = ""

	# 화면 중앙 정렬
	ui_elements.instruction_text.pos = (0, 330)
	ui_elements.message_text.pos = (0, 280)

	selected_mode_id = None
	while True:
		mouse_pos = mouse.getPos()
		hovered_mode_id = None

		for card in mode_cards:
			if card['frame'].contains(mouse_pos):
				hovered_mode_id = card['mode_id']

		for card in mode_cards:
			if card['mode_id'] == hovered_mode_id:
				card['frame'].lineColor = [0, 255, 200]
				card['frame'].lineWidth = 6
			else:
				card['frame'].lineColor = [220, 220, 220]
				card['frame'].lineWidth = 3

		ui_elements.instruction_text.draw()
		ui_elements.message_text.draw()
		for card in mode_cards:
			card['frame'].draw()
			card['image'].draw()
			card['title'].draw()
			card['subtitle'].draw()
		win.flip()

		keys = event.getKeys(keyList=[KEY_EXIT])
		if keys and KEY_EXIT in keys:
			selected_mode_id = None
			status = 'exit'
			break

		if mouse.getPressed()[0] and hovered_mode_id is not None:
			selected_mode_id = hovered_mode_id
			status = 'continue'
			while mouse.getPressed()[0]:
				core.wait(0.01)
			break

		core.wait(0.016)

	if status == 'continue' and selected_mode_id is None:
		selected_mode_id = DEFAULT_GAME_MODE

	# 위치 복원
	ui_elements.instruction_text.pos = orig_instruction_pos
	ui_elements.message_text.pos = orig_message_pos

	if status == 'exit':
		return ('exit', None)

	print(f"  ✓ 시작 화면 표시 완료 (mode={selected_mode_id})")
	return ('continue', selected_mode_id)
