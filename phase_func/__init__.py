# Experiment phase functions

from .starting import run_starting_phase
from .tutorial import run_tutorial_phase
from .game_play import run_game_play_phase
from .ending import run_ending_phase


def run_all_phases(
	win,
	game_state,
	ui_elements,
	board_renderer,
	deck_renderer,
	token_renderer,
):
	"""
	전체 phase 실행 오케스트레이터.

	Returns:
		str: 최종 결과 ('victory', 'defeat', 'exit')
	"""
	print("\n[3/5] 시작 phase...")
	start_result = run_starting_phase(win, ui_elements)
	if start_result == 'exit':
		run_ending_phase(win, ui_elements, game_state, 'exit')
		return 'exit'

	print("[4/5] 튜토리얼 phase...")
	tutorial_result = run_tutorial_phase(win, ui_elements)
	if tutorial_result == 'exit':
		run_ending_phase(win, ui_elements, game_state, 'exit')
		return 'exit'

	print("[5/5] 게임 플레이 phase...")
	game_state.start_game()
	result = run_game_play_phase(
		win,
		game_state,
		ui_elements,
		board_renderer,
		deck_renderer,
		token_renderer,
	)

	run_ending_phase(win, ui_elements, game_state, result)
	return result
