# Experiment phase functions

from .tutorial import run_tutorial_phase
from .game_play import run_game_play_phase
from .ending import run_ending_phase
from ..config import USE_PRACTICE
from ..phase_func_practice import run_practice_game


def run_all_phases(
	win,
	game_state,
	ui_elements,
	board_renderer,
	deck_renderer,
	token_renderer,
	aoi_manager=None,
	labjack_handle=None,
	save_paths=None,
	subject_id='',
):

	if aoi_manager is not None:
		aoi_manager.board = game_state.board
		aoi_manager.deck  = game_state.deck
		aoi_manager._build_aois()
		print(f"  - AOI 테이블 재구성: {len(aoi_manager.aois)}개")

	print("[3/4] 튜토리얼 phase...")
	tutorial_result = run_tutorial_phase(win, ui_elements)
	if tutorial_result == 'exit':
		run_ending_phase(win, ui_elements, game_state, 'exit')
		return 'exit'

	if USE_PRACTICE:
		print("[3.5/4] 연습 게임 phase...")
		practice_result = run_practice_game(
			win, game_state, ui_elements,
			board_renderer, deck_renderer, token_renderer,
		)
		if practice_result == 'exit':
			run_ending_phase(win, ui_elements, game_state, 'exit')
			return 'exit'
		# 연습 후 game_state 초기화 (점수·타이머 리셋)
		game_state.__init__(selected_mode_id=game_state.selected_mode_id)
		board_renderer.board = game_state.board
		board_renderer.card_images = {}
		board_renderer.highlights = {}
		board_renderer._create_visuals()
		deck_renderer.deck = game_state.deck
		deck_renderer.card_backs = []
		deck_renderer.card_fronts = []
		deck_renderer.highlights = []
		deck_renderer._create_visuals()
		token_renderer.token_manager = game_state.tokens
		token_renderer.token_stims = {}
		token_renderer._create_visuals()
		if aoi_manager is not None:
			aoi_manager.board = game_state.board
			aoi_manager.deck  = game_state.deck
			aoi_manager._build_aois()

	print("[4/4] 게임 플레이 phase...")
	game_state.start_game()

	# EyeLink 레코딩 시작 + AOI 등록
	if aoi_manager is not None and aoi_manager.el_tracker is not None:
		aoi_manager.el_tracker.setOfflineMode()
		aoi_manager.el_tracker.startRecording(1, 1, 1, 1)
		aoi_manager.el_tracker.sendMessage("TRIAL_START game_play")
		aoi_manager.register_with_eyelink()

	result = run_game_play_phase(
		win,
		game_state,
		ui_elements,
		board_renderer,
		deck_renderer,
		token_renderer,
		aoi_manager=aoi_manager,
		labjack_handle=labjack_handle,
		save_paths=save_paths,
		subject_id=subject_id,
	)

	# EyeLink 레코딩 종료
	if aoi_manager is not None and aoi_manager.el_tracker is not None:
		aoi_manager.end_trial(0.0)
		aoi_manager.el_tracker.stopRecording()
		aoi_manager.el_tracker.sendMessage("TRIAL_END")

	run_ending_phase(win, ui_elements, game_state, result)
	return result
