# main.py
# Chicken Task - Main Game Entry Point
# 통합 테스트 및 게임 실행

import sys
from psychopy import visual, core

# 프로젝트 모듈 import
from config import (
    WIDTH, HEIGHT, BG_COLOR, FULLSCREEN
)
from game_func.game_state import GameState
from view_func.board_renderer import BoardRenderer
from view_func.deck_renderer import DeckRenderer
from view_func.token_renderer import TokenRenderer
from view_func.ui_elements import UIElements
from phase_func import run_all_phases


def main():
    """
    메인 게임 실행 함수
    
    게임 흐름:
    1. 윈도우 및 게임 컴포넌트 초기화
    2. phase 오케스트레이터 실행
    3. 결과 요약 및 정리
    """
    
    # ==================== 1. 윈도우 생성 ====================
    print("\n" + "=" * 60)
    print("Chicken Task - 게임 시작")
    print("=" * 60 + "\n")
    
    print("[1/4] PsychoPy 윈도우 생성 중...")
    win = visual.Window(
        size=[WIDTH, HEIGHT],
        color=[c / 255 for c in BG_COLOR],  # PsychoPy는 -1~1 범위로 정규화
        colorSpace='rgb',
        fullscr=FULLSCREEN,
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
    
    # ==================== 3. phase 실행 ====================
    print("\n[3/4] phase 실행 시작...")
    print("-" * 60)

    result = run_all_phases(
        win, game_state, ui_elements,
        board_renderer, deck_renderer, token_renderer
    )

    print("-" * 60)
    print(f"  ✓ phase 실행 종료 (결과: {result})")

    # ==================== 4. 결과 요약 ====================
    print("\n[4/4] 게임 결과 요약...")
    
    # 게임 요약 출력
    print("\n### 게임 요약 ###")
    summary = game_state.get_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    print(f"\n총 시행 수: {len(game_state.trial_history)}")
    print(f"사용자 이동 수: {game_state.user_move_count}")
    print(f"PC 이동 수: {game_state.pc_move_count}")
    
    # ==================== 정리 ====================
    print("\n윈도우 종료 중...")
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