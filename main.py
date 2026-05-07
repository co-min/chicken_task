import sys
from psychopy import core, logging

from config import USE_EYELINK, USE_LABJACK
from game_func.game_state import GameState
from view_func.board_renderer import BoardRenderer
from view_func.deck_renderer import DeckRenderer
from view_func.token_renderer import TokenRenderer
from view_func.ui_elements import UIElements, fetch_random_nicknames
from phase_func import run_all_phases
from eye_func.aoi_manager import AOIManager
from utils.labjack_triggers import close_labjack
from save_func import init_session, finalize_session, init_trial_file, init_gaze_file
from setup_utils import get_subject_id, create_save_dir, create_window

if USE_EYELINK:
    import pylink
    from eye_func.EyeLinkCoreGraphicsPsychoPy import EyeLinkCoreGraphicsPsychoPy
    from initiate import initiate_eyelink

if USE_LABJACK:
    from initiate import initiate_labjack

logging.console.setLevel(logging.ERROR)


def main():
    print("\n" + "=" * 60)
    print("Chicken Task")
    print("=" * 60 + "\n")

    subject_id = get_subject_id()
    save_dir = create_save_dir(subject_id)
    print(f"저장 경로: {save_dir}\n")

    win = create_window()

    game_state = GameState()
    board_renderer = BoardRenderer(win, game_state.board)
    deck_renderer = DeckRenderer(win, game_state.deck)
    token_renderer = TokenRenderer(win, game_state.tokens)
    ui_elements = UIElements(win, fake_player_names=fetch_random_nicknames(count=5))

    el_tracker = None
    if USE_EYELINK:
        el_tracker = initiate_eyelink(win, save_directory=save_dir)
        print(f"  {'✓' if el_tracker else '⚠'} EyeLink: {'연결됨' if el_tracker else '비활성화'}")

    labjack_handle = None
    if USE_LABJACK:
        labjack_handle = initiate_labjack()
        print(f"  {'✓' if labjack_handle else '⚠'} LabJack T4: {'연결됨' if labjack_handle else '비활성화'}")

    aoi_manager = AOIManager(
        board=game_state.board,
        deck=game_state.deck,
        el_tracker=el_tracker,
    )

    session_file = init_session(
        save_dir, subject_id,
        game_mode=game_state.selected_mode_id,
        use_eyelink=bool(el_tracker),
        use_labjack=bool(labjack_handle),
    )
    trial_file = init_trial_file(save_dir, subject_id)
    gaze_file = init_gaze_file(save_dir, subject_id)

    aoi_manager.gaze_file = gaze_file
    aoi_manager.subject_id = subject_id

    save_paths = {
        'session':     session_file,
        'trial':       trial_file,
        'gaze':        gaze_file,
        'frame_drops': f"{save_dir}/frame_drops.csv",
    }

    result = run_all_phases(
        win, game_state, ui_elements,
        board_renderer, deck_renderer, token_renderer,
        aoi_manager=aoi_manager,
        labjack_handle=labjack_handle,
        save_paths=save_paths,
        subject_id=subject_id,
    )

    for key, value in game_state.get_summary().items():
        print(f"  {key}: {value}")

    finalize_session(session_file, game_state, result)

    close_labjack(labjack_handle)
    win.close()
    core.quit()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n게임이 중단되었습니다 (Ctrl+C)")
        core.quit()
    except Exception as e:
        print(f"\n오류 발생: {e}")
        import traceback
        traceback.print_exc()
        core.quit()
        sys.exit(1)
