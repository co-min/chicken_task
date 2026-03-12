# main.py
# Chicken Task - Main Game Entry Point
# 통합 테스트 및 게임 실행

import sys
from pathlib import Path
from psychopy import visual, core, event

# 프로젝트 모듈 import
from config import (
    WIDTH, HEIGHT, BG_COLOR, FULLSCREEN,
    KEY_EXIT, TEXT_COLOR
)
from game_func.game_state import GameState
from view_func.board_renderer import BoardRenderer
from view_func.deck_renderer import DeckRenderer
from view_func.token_renderer import TokenRenderer
from view_func.ui_elements import UIElements
from phase_func.game_play import run_game_play_phase


def main():
    """
    메인 게임 실행 함수
    
    게임 흐름:
    1. 윈도우 및 게임 컴포넌트 초기화
    2. 게임 시작
    3. 게임 플레이 루프
    4. 게임 종료 및 결과 표시
    5. 정리
    """
    
    # ==================== 1. 윈도우 생성 ====================
    print("\n" + "=" * 60)
    print("Chicken Task - 게임 시작")
    print("=" * 60 + "\n")
    
    print("[1/5] PsychoPy 윈도우 생성 중...")
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
    print("\n[2/5] 게임 컴포넌트 초기화 중...")
    
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
    
    # ==================== 3. 게임 시작 ====================
    print("\n[3/5] 게임 시작...")
    game_state.start_game()
    print("  ✓ 게임 상태: 시작 완료")
    print(f"  ✓ Phase: {game_state.phase}")
    
    # 시작 안내 화면
    _show_start_screen(win, ui_elements)
    
    # ==================== 4. 게임 플레이 루프 ====================
    print("\n[4/5] 게임 플레이 시작...")
    print("-" * 60)
    
    result = run_game_play_phase(
        win, game_state, ui_elements,
        board_renderer, deck_renderer, token_renderer
    )
    
    print("-" * 60)
    print(f"  ✓ 게임 플레이 종료 (결과: {result})")
    
    # ==================== 5. 게임 종료 처리 ====================
    print("\n[5/5] 게임 종료 처리...")
    
    # 종료 화면 표시
    _show_end_screen(win, ui_elements, game_state, result)
    
    # 게임 요약 출력
    print("\n### 게임 요약 ###")
    summary = game_state.get_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    print(f"\n총 시행 수: {len(game_state.trial_history)}")
    print(f"사용자 이동 수: {game_state.user_move_count}")
    print(f"PC 이동 수: {game_state.pc_move_count}")
    
    # ==================== 6. 정리 ====================
    print("\n윈도우 종료 중...")
    win.close()
    core.quit()
    
    print("\n" + "=" * 60)
    print("게임 종료")
    print("=" * 60 + "\n")


def _show_start_screen(win, ui_elements):
    """
    게임 시작 안내 화면
    
    Args:
        win: PsychoPy window 객체
        ui_elements: UIElements 인스턴스
    """
    # 안내 문구
    ui_elements.instruction_text.text = "Chicken Task 게임에 오신 것을 환영합니다!"
    ui_elements.message_text.text = "스페이스바를 눌러 게임을 시작하세요"
    ui_elements.message_text.color = [0, 255, 0]  # 초록색
    
    # 타이머와 점수는 감춤
    ui_elements.timer_text.text = ""
    ui_elements.score_text.text = ""
    
    # 화면 그리기
    ui_elements.instruction_text.draw()
    ui_elements.message_text.draw()
    win.flip()
    
    # 스페이스바 대기
    event.waitKeys(keyList=['space', KEY_EXIT])
    
    print("  ✓ 시작 화면 표시 완료")


def _show_end_screen(win, ui_elements, game_state, result):
    """
    게임 종료 화면
    
    Args:
        win: PsychoPy window 객체
        ui_elements: UIElements 인스턴스
        game_state: GameState 인스턴스
        result: 게임 종료 이유 ('victory', 'defeat', 'exit')
    """
    # 결과에 따른 메시지
    if result == 'victory':
        ui_elements.instruction_text.text = "🎉 승리! 🎉"
        ui_elements.message_text.text = "Chase가 Octopus를 잡았습니다!"
        ui_elements.message_text.color = [0, 255, 0]  # 초록색
    elif result == 'defeat':
        ui_elements.instruction_text.text = "💀 패배 💀"
        ui_elements.message_text.text = "Octopus가 Flight를 잡았습니다..."
        ui_elements.message_text.color = [255, 0, 0]  # 빨간색
    else:  # exit
        ui_elements.instruction_text.text = "게임 종료"
        ui_elements.message_text.text = "게임을 중단했습니다"
        ui_elements.message_text.color = [255, 255, 0]  # 노란색
    
    # 통계 정보
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
    
    # 종료 안내
    exit_text = visual.TextStim(
        win=win,
        text="아무 키나 눌러 종료하세요",
        pos=(0, -350),
        height=24,
        color=[255, 255, 255],
        colorSpace='rgb255'
    )
    
    # 화면 그리기
    ui_elements.instruction_text.draw()
    ui_elements.message_text.draw()
    stats_text.draw()
    exit_text.draw()
    win.flip()
    
    # 키 대기
    event.waitKeys()
    
    print("  ✓ 종료 화면 표시 완료")


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