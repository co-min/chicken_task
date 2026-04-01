# 튜토리얼

import sys
from pathlib import Path
from psychopy import event, visual

try:
	from ..config import KEY_EXIT, TEXT_COLOR, SCORE_MATCH, SCORE_COMBO_BONUS, SCORE_SPEED_MAX, SCORE_SPEED_MIN, SCORE_STEAL, SCORE_PENALTY, SCORE_CATCH_BONUS, SCORE_CAUGHT_PENALTY, SCORE_PC_CATCH_BONUS
	from ..view_func.frame_marker import blink_frame_marker, trigger_frame_marker
except ImportError:
	sys.path.insert(0, str(Path(__file__).parent.parent))
	from config import KEY_EXIT, TEXT_COLOR, SCORE_MATCH, SCORE_COMBO_BONUS, SCORE_SPEED_MAX, SCORE_SPEED_MIN, SCORE_STEAL, SCORE_PENALTY, SCORE_CATCH_BONUS, SCORE_CAUGHT_PENALTY, SCORE_PC_CATCH_BONUS
	from view_func.frame_marker import blink_frame_marker, trigger_frame_marker


def _show_score_rubric(win, ui_elements, key_exit):
	"""
	점수 제공 기준판 화면을 표시하고 키 입력을 기다린다.

	Returns:
		bool: True면 계속, False면 종료
	"""
	rubric_title = visual.TextStim(
		win=win,
		text="점수 기준표",
		pos=(0, 320),
		height=36,
		color=[255, 220, 60],
		colorSpace='rgb255',
		bold=True,
	)

	rubric_header = visual.TextStim(
		win=win,
		text="상황                                    점수",
		pos=(0, 240),
		height=22,
		color=[200, 200, 200],
		colorSpace='rgb255',
		bold=True,
	)

	divider = visual.Line(
		win=win,
		start=(-340, 220),
		end=(340, 220),
		lineColor=[180, 180, 180],
		lineWidth=1,
		colorSpace='rgb255',
		fillColor=None,
	)

	rubric_rows = [
		(f"카드 매칭 성공",                    f"+{SCORE_MATCH}점",       [120, 220, 120]),
		(f"연속 성공 콤보 보너스",              f"+{SCORE_COMBO_BONUS}점",  [120, 220, 120]),
		(f"빠른 판단 보너스",                  f"+{SCORE_SPEED_MIN}~{SCORE_SPEED_MAX}점", [120, 220, 120]),
		(f"NPC 카드 탈취 성공",                f"+{SCORE_STEAL}점",        [120, 200, 255]),
		(f"문어 잡기 성공  (Chase)",           f"+{SCORE_CATCH_BONUS}점",  [120, 200, 255]),
		(f"오답 선택",                         f"{SCORE_PENALTY}점",       [255, 140, 140]),
		(f"문어에게 잡힘  (Flight)",           f"{SCORE_CAUGHT_PENALTY}점",[255, 140, 140]),
		(f"문어가 Flight 닭 잡기 (문어 점수)", f"+{SCORE_PC_CATCH_BONUS}점",[200, 150, 255]),
	]

	row_stims = []
	row_start_y = 180
	row_gap = 48
	for i, (label, score, color) in enumerate(rubric_rows):
		y = row_start_y - i * row_gap
		label_stim = visual.TextStim(
			win=win,
			text=label,
			pos=(-170, y),
			height=20,
			color=TEXT_COLOR,
			colorSpace='rgb255',
			anchorHoriz='center',
		)
		score_stim = visual.TextStim(
			win=win,
			text=score,
			pos=(270, y),
			height=20,
			color=color,
			colorSpace='rgb255',
			bold=True,
			anchorHoriz='center',
		)
		row_stims.append((label_stim, score_stim))

	nav_text = visual.TextStim(
		win=win,
		text="스페이스바로 게임 시작 / ESC로 종료",
		pos=(0, -410),
		height=20,
		color=[180, 180, 180],
		colorSpace='rgb255',
	)

	rubric_title.draw()
	rubric_header.draw()
	divider.draw()
	for label_stim, score_stim in row_stims:
		label_stim.draw()
		score_stim.draw()
	nav_text.draw()
	trigger_frame_marker()
	blink_frame_marker(win)
	win.flip()

	keys = event.waitKeys(keyList=['space', key_exit])
	return not (keys and key_exit in keys)


def run_tutorial_phase(win, ui_elements):
	"""
	튜토리얼 화면.
	  1페이지: 게임 설명
	  2페이지: 점수 기준표

	Returns:
		str: 'continue' 또는 'exit'
	"""
	# 원래 위치 저장
	orig_instruction_pos = ui_elements.instruction_text.pos
	orig_message_pos = ui_elements.message_text.pos

	# ── 1페이지: 게임 설명 ──
	ui_elements.instruction_text.text = "게임 설명"
	ui_elements.message_text.text = (
		"1) 닭을 선택하세요 (Chase / Flight)\n"
		"2) 조건에 맞는 카드를 찾으세요\n"
		"3) 실패하면 문어 차례로 넘어갑니다\n\n"
		"스페이스바로 다음 / ESC로 종료"
	)
	ui_elements.message_text.color = TEXT_COLOR
	ui_elements.timer_text.text = ""
	ui_elements.score_text.text = ""

	ui_elements.instruction_text.pos = (0, 150)
	ui_elements.message_text.pos = (0, -50)

	ui_elements.instruction_text.draw()
	ui_elements.message_text.draw()
	trigger_frame_marker()   # 이벤트: 튜토리얼 1페이지 표시
	blink_frame_marker(win)
	win.flip()

	event.clearEvents()

	keys = event.waitKeys(keyList=['space', KEY_EXIT])

	# 텍스트 초기화 후 위치 복원
	ui_elements.instruction_text.text = ""
	ui_elements.message_text.text = ""
	ui_elements.instruction_text.pos = orig_instruction_pos
	ui_elements.message_text.pos = orig_message_pos

	if keys and KEY_EXIT in keys:
		return 'exit'

	# ── 2페이지: 점수 기준표 ──
	if not _show_score_rubric(win, ui_elements, KEY_EXIT):
		return 'exit'

	return 'continue'