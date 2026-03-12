#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Phase 5 통합 테스트: 실제 게임 플레이
- 닭 선택 단계 (token_selection)
- 게임 플레이 단계 (game_play)
- 사용자 vs PC 턴제 진행

테스트 항목:
1. 사용자 턴: 닭 선택 → 카드 선택 → 성공/실패
2. PC 턴: 자동 카드 선택 → 성공/실패
3. 턴 전환 및 타이머 관리
4. 승리/패배 조건

조작 방법:
- 닭 선택: UP(Chase) / DOWN(Flight) 키 또는 마우스 클릭
- 선택 확정: ENTER
- 카드 선택: 메인 덱 카드 마우스 클릭
- ESC: 게임 종료

실행 방법:
  python test_phase5.py

또는:
  cd chicken_task_first
  python test_phase5.py

게임 규칙:
  - 사용자가 턴을 시작할 때 Chase 또는 Flight 닭을 선택합니다
  - 선택한 닭으로 조건 카드에 맞는 메인 덱 카드를 찾아 클릭합니다
  - 성공하면 닭이 이동하고 다음 타겟으로 계속 진행합니다 (같은 닭 유지)
  - 실패하면 PC 턴으로 넘어갑니다
  - PC도 같은 방식으로 플레이하며, 60% 확률로 정답을 선택합니다
  - 먼저 9번째 칸(결승선)에 도착하는 쪽이 승리합니다
"""

# PsychoPy 경고 메시지 억제
import warnings
warnings.filterwarnings('ignore')

from psychopy import logging
logging.console.setLevel(logging.ERROR)

from psychopy import visual, core
import sys
import os

# 경로 설정
sys.path.insert(0, os.path.dirname(__file__))

# 옵션 설정
from set_opts.set_visual_opt import set_visual_opt

# 게임 객체
from game_func.game_state import GameState

# 렌더러
from view_func.board_renderer import BoardRenderer
from view_func.deck_renderer import DeckRenderer
from view_func.token_renderer import TokenRenderer
from view_func.ui_elements import UIElements

# Phase 함수
from phase_func.game_play import run_game_play_phase


def check_prerequisites():
    """게임 실행 전 필수 요소 확인"""
    print("\n[사전 체크] 필수 파일 및 폴더 확인 중...")
    
    issues = []
    
    # 1. 이미지 폴더 확인
    stimuli_dir = os.path.join(os.path.dirname(__file__), 'stimuli')
    if not os.path.exists(stimuli_dir):
        issues.append(f"❌ stimuli 폴더가 없습니다: {stimuli_dir}")
    else:
        print(f"  ✓ stimuli 폴더 존재")
        
        # 하위 폴더들
        required_dirs = ['condition_cards', 'main_cards', 'tokens', 'ui']
        for dir_name in required_dirs:
            dir_path = os.path.join(stimuli_dir, dir_name)
            if os.path.exists(dir_path):
                print(f"  ✓ {dir_name} 폴더 존재")
            else:
                issues.append(f"❌ {dir_name} 폴더가 없습니다")
    
    # 2. 설정 파일 확인
    config_path = os.path.join(os.path.dirname(__file__), 'config.py')
    if os.path.exists(config_path):
        print(f"  ✓ config.py 존재")
    else:
        issues.append(f"❌ config.py 파일이 없습니다")
    
    if issues:
        print("\n경고: 일부 파일이 누락되었습니다:")
        for issue in issues:
            print(f"  {issue}")
        print("\n이미지가 없으면 오류가 발생할 수 있습니다.")
        print("계속하시겠습니까? (Enter를 눌러 계속)")
        input()
    else:
        print("  ✓ 모든 필수 요소 확인 완료\n")


def main():
    """Phase 5 테스트 메인 함수"""
    
    print("\n" + "="*70)
    print(" "*20 + "Phase 5 통합 테스트")
    print(" "*15 + "실제 게임 플레이 - 사용자 vs PC")
    print("="*70)
    
    # 사전 체크
    check_prerequisites()
    
    # 1. 옵션 설정
    print("\n[1/5] 옵션 설정 중...")
    visual_opt = set_visual_opt()
    visual_opt['fullscreen'] = False  # 테스트용 창모드
    print("  ✓ 화면 설정 완료")
    
    # 2. PsychoPy 윈도우 생성
    print("\n[2/5] PsychoPy 윈도우 생성 중...")
    win = visual.Window(
        size=visual_opt['win_size'],
        color=visual_opt['bg_color'],
        fullscr=visual_opt['fullscreen'],
        units=visual_opt['units'],
        colorSpace=visual_opt['color_space'],
        allowGUI=True,
        pos=visual_opt.get('pos'),
        screen=visual_opt.get('screen', 0)
    )
    print(f"  ✓ 윈도우 생성 완료 ({visual_opt['win_size'][0]}x{visual_opt['win_size'][1]})")
    
    # 3. 게임 상태 초기화
    print("\n[3/5] 게임 상태 초기화 중...")
    game_state = GameState()
    game_state.start_game()
    print("  ✓ GameState 생성 완료")
    print(f"  - 운동장 보드: {game_state.board.rows}행 × {game_state.board.cols}열")
    print(f"  - 메인 덱: {len(game_state.deck.cards)}장")
    print(f"  - 토큰: Chase, Octopus, Flight")
    
    # 4. 렌더러 생성
    print("\n[4/5] 렌더러 생성 중...")
    board_renderer = BoardRenderer(win, game_state.board)
    deck_renderer = DeckRenderer(win, game_state.deck)
    token_renderer = TokenRenderer(win, game_state.tokens)
    ui_elements = UIElements(win)
    print("  ✓ 모든 렌더러 생성 완료")
    
    # 5. 게임 시작 안내
    print("\n[5/5] 게임 준비 완료!")
    print("\n" + "="*70)
    print("게임 규칙:")
    print("  1. 사용자 턴 시작 시 닭(Chase/Flight)을 선택합니다")
    print("  2. 선택한 닭으로 성공할 때까지 계속 플레이합니다")
    print("  3. 실패 시 PC 턴으로 넘어갑니다")
    print("  4. PC도 같은 규칙으로 플레이합니다")
    print("  5. 먼저 결승선에 도착하는 쪽이 승리합니다")
    print("\n조작 방법:")
    print("  - 닭 선택: ↑/↓ 키 또는 마우스 클릭")
    print("  - 선택 확정: Enter")
    print("  - 카드 선택: 메인 덱 카드 클릭")
    print("  - 게임 종료: ESC")
    print("="*70)
    print("\n게임을 시작합니다...\n")
    
    core.wait(2)  # 2초 대기
    
    try:
        # 게임 플레이 시작
        result = run_game_play_phase(
            win=win,
            game_state=game_state,
            ui_elements=ui_elements,
            board_renderer=board_renderer,
            deck_renderer=deck_renderer,
            token_renderer=token_renderer
        )
        
        # 결과 처리
        print("\n" + "="*70)
        if result == 'victory':
            print(" "*25 + "🎉 승리! 🎉")
            print(" "*20 + "축하합니다! 당신이 이겼습니다!")
            
            # 승리 화면 표시
            ui_elements.message_text.text = "승리!"
            ui_elements.message_text.color = [0, 255, 0]
            ui_elements.instruction_text.text = "축하합니다! ESC를 눌러 종료하세요"
            
            board_renderer.draw()
            deck_renderer.draw()
            token_renderer.draw()
            ui_elements.message_text.draw()
            ui_elements.instruction_text.draw()
            win.flip()
            
            core.wait(3)
            
        elif result == 'defeat':
            print(" "*25 + "😢 패배 😢")
            print(" "*18 + "PC가 승리했습니다. 다시 도전하세요!")
            
            # 패배 화면 표시
            ui_elements.message_text.text = "패배..."
            ui_elements.message_text.color = [255, 0, 0]
            ui_elements.instruction_text.text = "PC가 이겼습니다. ESC를 눌러 종료하세요"
            
            board_renderer.draw()
            deck_renderer.draw()
            token_renderer.draw()
            ui_elements.message_text.draw()
            ui_elements.instruction_text.draw()
            win.flip()
            
            core.wait(3)
            
        elif result == 'exit':
            print(" "*22 + "게임 종료")
            print(" "*18 + "사용자가 게임을 종료했습니다")
        
        # 게임 통계 출력
        print("\n게임 통계:")
        print(f"  - 총 턴 수: {game_state.turn_count}")
        print(f"  - 사용자 이동 횟수: {game_state.user_move_count}")
        print(f"  - PC 이동 횟수: {game_state.pc_move_count}")
        print(f"  - 총 시행 횟수: {len(game_state.trial_history)}")
        
        # 각 토큰 위치
        print("\n최종 토큰 위치:")
        print(f"  - Chase: {game_state.tokens.chase.get_position()}")
        print(f"  - Octopus: {game_state.tokens.octopus.get_position()}")
        print(f"  - Flight: {game_state.tokens.flight.get_position()}")
        
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n오류 발생: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 윈도우 닫기
        win.close()
        core.quit()
        print("테스트 종료\n")


if __name__ == "__main__":
    main()

