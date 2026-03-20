# 종료 화면

import sys
from pathlib import Path
from psychopy import visual, core, event

try:
	from ..config import TEXT_COLOR, FRAME_MARKER_POS, FRAME_MARKER_SIZE, SAVE_FRAME_LOG
	from ..view_func.frame_marker import draw_white_marker
	from ..save_func.save_frame_log import save_frame_log_ending
	from ..save_func.save_results import save_all_results
except ImportError:
	sys.path.insert(0, str(Path(__file__).parent.parent))
	from config import TEXT_COLOR, FRAME_MARKER_POS, FRAME_MARKER_SIZE, SAVE_FRAME_LOG
	from view_func.frame_marker import draw_white_marker
	from save_func.save_frame_log import save_frame_log_ending
	from save_func.save_results import save_all_results


def run_ending_phase(win, ui_elements, game_state, result, subject_id='default'):
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
	else:
		ui_elements.instruction_text.text = "게임 종료"
		ui_elements.message_text.text = "게임을 중단했습니다"
		ui_elements.message_text.color = [255, 255, 0]

	stats_text = visual.TextStim(
		win=win,
		text=f"총 턴 수: {game_state.turn_count}\n"
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

	# === 로깅 변수 초기화 ===
	frame_count = 0
	frame_log = []
	clock = core.Clock()
	prev_flip_time = None

	while True:
		ui_elements.instruction_text.draw()
		ui_elements.message_text.draw()
		stats_text.draw()
		exit_text.draw()
		draw_white_marker(win, FRAME_MARKER_POS, FRAME_MARKER_SIZE)
		win.flip()

		flip_time = clock.getTime()
		dt = 0.0 if prev_flip_time is None else (flip_time - prev_flip_time)
		prev_flip_time = flip_time

		if SAVE_FRAME_LOG:
			frame_log.append({
				'phase': 'ending',
				'frame_count': frame_count,
				'time': flip_time,
				'dt': dt,
				'marker_on': True,
			})
		frame_count += 1

		keys = event.getKeys()
		if keys:
			break

	if SAVE_FRAME_LOG:
		print(f"  - ending frame log: {len(frame_log)} frames")
		save_frame_log_ending(frame_log, subject_id)
	
	# 게임 결과 저장
	save_all_results(game_state, subject_id)

	print("  ✓ 종료 화면 표시 완료")