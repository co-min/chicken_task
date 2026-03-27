# 종료 화면

import sys
from pathlib import Path
from psychopy import visual, event

try:
	from ..config import TEXT_COLOR
	from ..view_func.frame_marker import blink_frame_marker, trigger_frame_marker
except ImportError:
	sys.path.insert(0, str(Path(__file__).parent.parent))
	from config import TEXT_COLOR
	from view_func.frame_marker import blink_frame_marker, trigger_frame_marker


def run_ending_phase(win, ui_elements, game_state, result):
	"""
	게임 종료 화면.

	Args:
		result: 'victory', 'defeat', 'exit'
	"""
	if result == 'victory':
		ui_elements.instruction_text.text = "Victory!"
		ui_elements.message_text.text = "Chase가 Octopus를 잡았습니다!"
		ui_elements.message_text.color = [0, 255, 0]
	elif result == 'defeat':
		ui_elements.instruction_text.text = "Defeat"
		ui_elements.message_text.text = "Octopus가 Flight를 잡았습니다..."
		ui_elements.message_text.color = [255, 0, 0]
	elif result == 'timeout':
		ui_elements.instruction_text.text = "시간 종료"
		ui_elements.message_text.text = "게임 제한 시간이 종료되었습니다"
		ui_elements.message_text.color = [255, 165, 0]
	else:
		ui_elements.instruction_text.text = "게임 종료"
		ui_elements.message_text.text = "게임을 중단했습니다"
		ui_elements.message_text.color = [255, 255, 0]

	stats_text = visual.TextStim(
		win=win,
		text=f"내 점수: {game_state.user_score}점  |  문어 점수: {game_state.pc_score}점\n\n"
			 f"총 턴 수: {game_state.turn_count}\n"
			 f"사용자 이동: {game_state.user_move_count}회\n"
			 f"PC 이동: {game_state.pc_move_count}회\n"
			 f"총 시행: {len(game_state.trial_history)}회",
		pos=(0, 0),
		height=28,
		color=TEXT_COLOR,
		colorSpace='rgb255'
	)

	exit_text = visual.TextStim(
		win=win,
		text="아무 키나 눌러 종료하세요",
		pos=(0, -350),
		height=24,
		color=[255, 255, 255],
		colorSpace='rgb255'
	)

	ui_elements.instruction_text.draw()
	ui_elements.message_text.draw()
	stats_text.draw()
	exit_text.draw()
	trigger_frame_marker()   # 이벤트: 게임 종료 화면 표시
	blink_frame_marker(win)
	win.flip()
	event.waitKeys()

	print("  ✓ 종료 화면 표시 완료")