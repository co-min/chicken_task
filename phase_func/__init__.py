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
	aoi_manager=None,
):
	"""
	전체 phase 실행 오케스트레이터.

	Args:
		aoi_manager: AOIManager 인스턴스 (선택). None 이면 AOI 추적 비활성화.

	Returns:
		str: 최종 결과 ('victory', 'defeat', 'exit')
	"""
	print("\n[3/5] 시작 phase...")
	start_result, selected_mode_id = run_starting_phase(win, ui_elements)
	if start_result == 'exit':
		run_ending_phase(win, ui_elements, game_state, 'exit')
		return 'exit'

	if selected_mode_id is not None:
		game_state.set_selected_mode(selected_mode_id)
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
		print(f"  - 시작 모드 선택: {selected_mode_id}")

		# 게임 모드가 결정된 후 AOI 테이블 재구성 (보드/덱 크기가 확정됨)
		if aoi_manager is not None:
			aoi_manager.board = game_state.board
			aoi_manager.deck  = game_state.deck
			aoi_manager._build_aois()
			print(f"  - AOI 테이블 재구성: {len(aoi_manager.aois)}개")

	print("[4/5] 튜토리얼 phase...")
	tutorial_result = run_tutorial_phase(win, ui_elements)
	if tutorial_result == 'exit':
		run_ending_phase(win, ui_elements, game_state, 'exit')
		return 'exit'

	print("[5/5] 게임 플레이 phase...")
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
	)

	# EyeLink 레코딩 종료
	if aoi_manager is not None and aoi_manager.el_tracker is not None:
		aoi_manager.end_trial(0.0)
		aoi_manager.el_tracker.stopRecording()
		aoi_manager.el_tracker.sendMessage("TRIAL_END")

	run_ending_phase(win, ui_elements, game_state, result)
	return result
