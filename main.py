# main.py
# Chicken Task - Main Game Entry Point
# 통합 테스트 및 게임 실행

import os
import sys
import tkinter as tk
from datetime import datetime
from psychopy import visual, core, logging, monitors

# 프로젝트 모듈 import
from config import (
    WIDTH,
    HEIGHT,
    BG_COLOR,
    FULLSCREEN,
    AUTO_DETECT_WINDOW_SIZE,
    FORCE_WINDOWED_MODE,
    MONITOR_NAME,
    MONITOR_WIDTH_CM,
    MONITOR_DISTANCE_CM,
    USE_EYELINK,
    USE_LABJACK,
)
from game_func.game_state import GameState
from view_func.board_renderer import BoardRenderer
from view_func.deck_renderer import DeckRenderer
from view_func.token_renderer import TokenRenderer
from view_func.ui_elements import UIElements
from phase_func import run_all_phases
from eye_func.aoi_manager import AOIManager
from utils.labjack_triggers import close_labjack
from save_func import init_session, finalize_session, init_trial_file, init_gaze_file

if USE_EYELINK:
    import pylink
    from eye_func.EyeLinkCoreGraphicsPsychoPy import EyeLinkCoreGraphicsPsychoPy
    from initiate import initiate_eyelink

if USE_LABJACK:
    from initiate import initiate_labjack


# Font Manager 등 콘솔 warning 출력 축소
logging.console.setLevel(logging.ERROR)


def _detect_screen_size(fallback_size):
    """Detect current screen size on Windows and fall back safely if unavailable."""
    try:
        root = tk.Tk()
        root.withdraw()
        size = [root.winfo_screenwidth(), root.winfo_screenheight()]
        root.destroy()
        return size
    except Exception:
        return list(fallback_size)


def _build_monitor_profile(screen_size):
    """Create a monitor profile to avoid temporary monitor warnings."""
    monitor = monitors.Monitor(
        MONITOR_NAME,
        width=MONITOR_WIDTH_CM,
        distance=MONITOR_DISTANCE_CM,
    )
    monitor.setSizePix(screen_size)
    return monitor


def _get_subject_id() -> str:
    """콘솔에서 피험자 ID를 입력받는다."""
    while True:
        subject_id = input("피험자 ID 입력 (예: P001): ").strip()
        if subject_id:
            return subject_id
        print("ID를 입력해주세요.")


def _create_save_dir(subject_id: str) -> str:
    """Data/{subject_id}_{yyyymmdd_HHMMSS}/ 디렉토리를 생성하고 경로를 반환한다."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Data')
    save_dir = os.path.join(base, f"{subject_id}_{timestamp}")
    os.makedirs(save_dir, exist_ok=True)
    return save_dir


def main():
    """
    메인 게임 실행 함수

    게임 흐름:
    1. 피험자 ID 입력 및 저장 디렉토리 생성
    2. 윈도우 및 게임 컴포넌트 초기화
    3. phase 오케스트레이터 실행
    4. 결과 요약 및 정리
    """

    print("\n" + "=" * 60)
    print("Chicken Task - 게임 시작")
    print("=" * 60 + "\n")

    # ==================== 0. 피험자 ID & 저장 디렉토리 ====================
    subject_id = _get_subject_id()
    save_dir   = _create_save_dir(subject_id)
    print(f"  저장 경로: {save_dir}\n")

    # ==================== 1. 윈도우 생성 ====================
    print("[1/4] PsychoPy 윈도우 생성 중...")

    screen_size = _detect_screen_size([WIDTH, HEIGHT]) if AUTO_DETECT_WINDOW_SIZE else [WIDTH, HEIGHT]
    win_size = [min(WIDTH, screen_size[0]), min(HEIGHT, screen_size[1])]
    is_fullscreen = FULLSCREEN and not FORCE_WINDOWED_MODE
    monitor_profile = _build_monitor_profile(screen_size)

    print(f"  - 화면 감지 해상도: {screen_size[0]} x {screen_size[1]}")
    print(f"  - 창 크기: {win_size[0]} x {win_size[1]} (fullscreen={is_fullscreen})")

    win = visual.Window(
        size=win_size,
        color=[c / 255 for c in BG_COLOR],  # PsychoPy는 -1~1 범위로 정규화
        colorSpace='rgb',
        fullscr=is_fullscreen,
        monitor=monitor_profile,
        units='pix',
        allowGUI=True  # 마우스 커서 표시
    )
    win.mouseVisible = True  # 마우스 커서 명시적으로 표시
    print("  ✓ 윈도우 생성 완료")

    # ==================== 2. 게임 컴포넌트 초기화 ====================
    print("\n[2/4] 게임 컴포넌트 초기화 중...")

    # 게임 상태
    game_state = GameState()
    print("  ✓ GameState 초기화 완료")

    # 렌더러들
    board_renderer = BoardRenderer(win, game_state.board)
    print("  ✓ BoardRenderer 초기화 완료")

    deck_renderer = DeckRenderer(win, game_state.deck)
    print("  ✓ DeckRenderer 초기화 완료")

    token_renderer = TokenRenderer(win, game_state.tokens)
    print("  ✓ TokenRenderer 초기화 완료")

    # UI 요소
    ui_elements = UIElements(win)
    print("  ✓ UIElements 초기화 완료")

    # EyeLink 초기화
    el_tracker = None
    if USE_EYELINK:
        el_tracker = initiate_eyelink(win, save_directory=save_dir)
        print(f"  {'✓' if el_tracker else '⚠'} EyeLink: {'연결됨' if el_tracker else '비활성화'}")

    # LabJack T4 초기화
    labjack_handle = None
    if USE_LABJACK:
        labjack_handle = initiate_labjack()
        print(f"  {'✓' if labjack_handle else '⚠'} LabJack T4: {'연결됨' if labjack_handle else '비활성화'}")

    # AOI 관리자 초기화
    aoi_manager = AOIManager(
        board=game_state.board,
        deck=game_state.deck,
        el_tracker=el_tracker,
        labjack_handle=labjack_handle,
    )
    print("  ✓ AOIManager 초기화 완료")

    # ==================== 저장 파일 초기화 ====================
    session_file = init_session(
        save_dir, subject_id,
        game_mode=game_state.selected_mode_id,
        use_eyelink=bool(el_tracker),
        use_labjack=bool(labjack_handle),
    )
    trial_file = init_trial_file(save_dir, subject_id)
    gaze_file  = init_gaze_file(save_dir, subject_id)

    # AOIManager에 gaze 저장 경로 주입
    aoi_manager.gaze_file  = gaze_file
    aoi_manager.subject_id = subject_id

    save_paths = {
        'session': session_file,
        'trial':   trial_file,
        'gaze':    gaze_file,
    }
    print("  ✓ 저장 파일 초기화 완료")

    # ==================== 3. phase 실행 ====================
    print("\n[3/4] phase 실행 시작...")
    print("-" * 60)

    result = run_all_phases(
        win, game_state, ui_elements,
        board_renderer, deck_renderer, token_renderer,
        aoi_manager=aoi_manager,
        save_paths=save_paths,
        subject_id=subject_id,
    )

    print("-" * 60)
    print(f"  ✓ phase 실행 종료 (결과: {result})")

    # ==================== 4. 결과 요약 ====================
    print("\n[4/4] 게임 결과 요약...")

    summary = game_state.get_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")

    print(f"\n총 시행 수: {len(game_state.trial_history)}")
    print(f"사용자 이동 수: {game_state.user_move_count}")
    print(f"PC 이동 수: {game_state.pc_move_count}")

    # 세션 JSON 최종 업데이트
    finalize_session(session_file, game_state, result)

    # ==================== 정리 ====================
    print("\n하드웨어 연결 종료 중...")
    close_labjack(labjack_handle)

    print("윈도우 종료 중...")
    win.close()
    core.quit()

    print("\n" + "=" * 60)
    print("게임 종료")
    print("=" * 60 + "\n")


# ==================== 메인 실행 ====================
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n게임이 중단되었습니다 (Ctrl+C)")
        core.quit()
    except Exception as e:
        print(f"\n\n오류 발생: {e}")
        import traceback
        traceback.print_exc()
        core.quit()
        sys.exit(1)
