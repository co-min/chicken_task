"""
게임 플레이 메인 루프.

라운드 전환, 턴 전환만 담당하고,
실제 턴 로직은 UserTurnMachine / PCTurnMachine 에 위임한다.
"""

import sys
from pathlib import Path
from psychopy import event

try:
    from ..sounds import load_sounds
    from ..utils.frame_drop_log import FrameDropLogger
    from ..phase_func.user_turn import UserTurnMachine
    from ..phase_func.pc_turn import PCTurnMachine
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from sounds import load_sounds
    from utils.frame_drop_log import FrameDropLogger
    from phase_func.user_turn import UserTurnMachine
    from phase_func.pc_turn import PCTurnMachine


def run_game_play_phase(win, game_state, ui_elements, board_renderer, deck_renderer,
                        token_renderer, aoi_manager=None, labjack_handle=None,
                        save_paths=None, subject_id=''):
    """
    Returns:
        'timeout' : 전체 게임 라운드(20라운드) 종료
        'exit'    : 사용자가 ESC 입력
    """
    mouse  = event.Mouse(win=win)
    sounds = load_sounds()
    fdl    = (FrameDropLogger(save_paths['frame_drops'])
              if (save_paths and save_paths.get('frame_drops')) else None)

    # TurnStateMachine 공통 인자
    deps = dict(
        win=win, gs=game_state, ui=ui_elements,
        board_r=board_renderer, deck_r=deck_renderer, token_r=token_renderer,
        aoi=aoi_manager, ljack=labjack_handle,
        save_paths=save_paths, subject_id=subject_id, sounds=sounds, fdl=fdl,
    )

    while True:
        if game_state.is_game_time_expired():
            print("[GAME END] 20라운드 완료!")
            return 'timeout'

        # ── 턴 실행 ──────────────────────────────────────────────────────────
        if game_state.current_turn == game_state.TURN_USER:
            result = UserTurnMachine(**deps, mouse=mouse).run()
            if result == 'exit':
                return 'exit'
        elif game_state.current_turn == game_state.TURN_PC:
            PCTurnMachine(**deps).run()
