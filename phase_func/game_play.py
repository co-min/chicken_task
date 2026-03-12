# Phase 1 + : GamePlay
# 게임 플레이 단계 - 사용자와 PC가 교대로 카드를 선택하며 게임 진행

import sys
from pathlib import Path
from psychopy import visual, core, event
import time

try:
    from ..config import (
        KEY_EXIT, TURN_TIME_LIMIT, CARD_FLIP_DURATION,
        FEEDBACK_DURATION, TRIAL_INTERVAL, PC_THINK_TIME,
        WIDTH, HEIGHT, TEXT_COLOR,
        DECK_LEFT_MARGIN, DECK_TOP_MARGIN,
        DECK_CARD_WIDTH, DECK_CARD_HEIGHT, DECK_CARD_SPACING
    )
    from ..phase_func.token_selection import run_token_selection_phase
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from config import (
        KEY_EXIT, TURN_TIME_LIMIT, CARD_FLIP_DURATION,
        FEEDBACK_DURATION, TRIAL_INTERVAL, PC_THINK_TIME,
        WIDTH, HEIGHT, TEXT_COLOR,
        DECK_LEFT_MARGIN, DECK_TOP_MARGIN,
        DECK_CARD_WIDTH, DECK_CARD_HEIGHT, DECK_CARD_SPACING
    )
    from phase_func.token_selection import run_token_selection_phase


def run_game_play_phase(win, game_state, ui_elements, board_renderer, deck_renderer, token_renderer):
    """
    Phase 1+: 게임 플레이 단계
    사용자와 PC가 교대로 턴을 진행하며 게임을 플레이
    
    Args:
        win: PsychoPy window 객체
        game_state: GameState 인스턴스
        ui_elements: UIElements 인스턴스
        board_renderer: BoardRenderer 인스턴스
        deck_renderer: DeckRenderer 인스턴스
        token_renderer: TokenRenderer 인스턴스
    
    Returns:
        str: 게임 종료 이유 ('victory', 'defeat', 'exit')
    """
    
    # 마우스 객체
    mouse = event.Mouse(win=win)
    
    # 게임 메인 루프
    while True:
        # 게임 종료 확인
        if game_state.phase == game_state.PHASE_VICTORY:
            return 'victory'
        elif game_state.phase == game_state.PHASE_DEFEAT:
            return 'defeat'
        
        # 현재 턴 확인
        if game_state.current_turn == game_state.TURN_USER:
            # 사용자 턴
            result = _run_user_turn(win, game_state, ui_elements, board_renderer, 
                                   deck_renderer, token_renderer, mouse)
            
            if result == 'exit':
                return 'exit'
            elif result == 'game_end':
                # 게임 종료 (승리 또는 패배)
                continue
            
        elif game_state.current_turn == game_state.TURN_PC:
            # PC 턴
            result = _run_pc_turn(win, game_state, ui_elements, board_renderer,
                                 deck_renderer, token_renderer)
            
            if result == 'game_end':
                # 게임 종료 (승리 또는 패배)
                continue
        
        # 프레임 대기
        core.wait(0.016)


def _run_user_turn(win, game_state, ui_elements, board_renderer, deck_renderer, 
                   token_renderer, mouse):
    """
    사용자 턴 실행
    
    Returns:
        str: 'exit' (게임 종료), 'game_end' (승패 결정), 'continue' (계속 진행)
    """
    
    # 1. 닭 선택 단계 (토큰이 선택되지 않았을 때만)
    if game_state.selected_token is None:
        selected = run_token_selection_phase(win, game_state, ui_elements, 
                                            board_renderer, deck_renderer, token_renderer)
        
        if selected == 'exit':
            return 'exit'
        
        # 선택 확정 및 타이머 시작
        game_state.confirm_selection()
    
    # 2. 카드 선택 루프 (같은 토큰으로 계속 진행)
    while game_state.phase == game_state.PHASE_GAME_PLAY and \
          game_state.current_turn == game_state.TURN_USER:
        
        # 타겟 위치 업데이트 (매 루프마다)
        target_pos = game_state.get_target_position()
        
        # 안내 문구 업데이트
        ui_elements.instruction_text.text = f"메인 덱에서 조건에 맞는 카드를 클릭하세요 (턴 {game_state.turn_count})"
        ui_elements.message_text.text = f"{game_state.selected_token.upper()} 닭을 조종 중..."
        
        # 타이머 업데이트
        elapsed = game_state.timer.get_elapsed()
        remaining = max(0, TURN_TIME_LIMIT - elapsed)
        ui_elements.timer_text.text = f"{int(remaining):02d}:{int((remaining % 1) * 100):02d}"
        
        # 시간 초과 확인
        if game_state.timer.is_expired():
            ui_elements.message_text.text = "시간 초과! 턴 종료"
            ui_elements.message_text.color = [255, 0, 0]  # 빨간색
            
            _draw_game_screen(win, ui_elements, board_renderer, deck_renderer, token_renderer, None)
            win.flip()
            core.wait(FEEDBACK_DURATION)
            
            # 턴 종료 (end_user_turn에서 selected_token 리셋됨)
            game_state.end_user_turn()
            
            return 'continue'
        
        # 키보드 입력 확인 (ESC)
        keys = event.getKeys()
        if KEY_EXIT in keys:
            return 'exit'
        
        # 마우스 클릭 확인
        if mouse.getPressed()[0]:  # 왼쪽 버튼
            mouse_pos = mouse.getPos()
            
            # 클릭한 카드 위치 확인
            card_pos = _get_clicked_card(mouse_pos)
            
            if card_pos is not None:
                card_row, card_col = card_pos
                
                # 카드 선택 처리
                result = game_state.user_click_card(card_row, card_col)
                
                # 카드 뒤집기 애니메이션 (game_state.user_click_card에서 이미 flip 수행됨)
                _draw_game_screen(win, ui_elements, board_renderer, deck_renderer, token_renderer, target_pos)
                win.flip()
                core.wait(CARD_FLIP_DURATION)
                
                # 결과 처리
                if result == 'success':
                    ui_elements.message_text.text = "성공! 닭이 이동했습니다"
                    ui_elements.message_text.color = [0, 255, 0]  # 초록색
                    
                    _draw_game_screen(win, ui_elements, board_renderer, deck_renderer, token_renderer, None)
                    win.flip()
                    core.wait(FEEDBACK_DURATION)
                    
                    # 카드 뒤로 감추기 (hide_card 사용)
                    game_state.deck.hide_card(card_row, card_col)
                    
                    # 다음 타겟 위치로 계속 진행 (루프 계속)
                    core.wait(TRIAL_INTERVAL)
                    # 계속 루프를 진행하여 다음 타겟으로
                    continue
                
                elif result == 'failure':
                    ui_elements.message_text.text = "실패! 턴 종료"
                    ui_elements.message_text.color = [255, 0, 0]  # 빨간색
                    
                    _draw_game_screen(win, ui_elements, board_renderer, deck_renderer, token_renderer, None)
                    win.flip()
                    core.wait(FEEDBACK_DURATION)
                    
                    # 카드 뒤로 감추기 (hide_card 사용)
                    game_state.deck.hide_card(card_row, card_col)
                    
                    # 턴 종료 (end_user_turn에서 selected_token 리셋됨)
                    
                    return 'continue'
                
                elif result == 'game_end':
                    # 게임 종료
                    game_state.selected_token = None
                    return 'game_end'
                
                # 클릭 후 버튼이 떼어지기를 기다림
                while mouse.getPressed()[0]:
                    pass
        
        # 화면 그리기 (타겟 하이라이트 포함)
        _draw_game_screen(win, ui_elements, board_renderer, deck_renderer, token_renderer, target_pos)
        win.flip()
        core.wait(0.016)
    
    return 'continue'


def _run_pc_turn(win, game_state, ui_elements, board_renderer, deck_renderer, token_renderer):
    """
    PC 턴 실행
    PC도 성공 시 계속 시도하고, 실패 시 사용자 턴으로 전환
    
    Returns:
        str: 'game_end' (승패 결정), 'continue' (계속 진행)
    """
    
    # PC 턴 루프 (성공 시 계속 진행)
    while game_state.current_turn == game_state.TURN_PC:
        # 안내 문구 업데이트
        ui_elements.instruction_text.text = "PC가 카드를 선택하는 중..."
        ui_elements.message_text.text = "잠시만 기다려주세요"
        ui_elements.message_text.color = TEXT_COLOR
        ui_elements.timer_text.text = ""
        
        _draw_game_screen(win, ui_elements, board_renderer, deck_renderer, token_renderer, None)
        win.flip()
        
        # PC 생각 시간
        core.wait(PC_THINK_TIME)
        
        # PC 카드 선택 및 실행 (result와 card_pos 반환)
        result, card_pos = game_state.pc_turn_step()
        
        # 카드 뒤집기 애니메이션 표시
        _draw_game_screen(win, ui_elements, board_renderer, deck_renderer, token_renderer, None)
        win.flip()
        core.wait(CARD_FLIP_DURATION)
        
        if result == 'success':
            ui_elements.message_text.text = "PC 성공! 문어가 이동했습니다"
            ui_elements.message_text.color = [255, 100, 0]  # 주황색
            
            _draw_game_screen(win, ui_elements, board_renderer, deck_renderer, token_renderer, None)
            win.flip()
            core.wait(FEEDBACK_DURATION)
            
            # 카드 다시 뒤로 감추기 (hide_card 사용)
            game_state.deck.hide_card(card_pos[0], card_pos[1])
            
            # 계속 PC 턴 진행 (루프 계속)
            core.wait(TRIAL_INTERVAL)
            continue
            
        elif result == 'failure':
            ui_elements.message_text.text = "PC 실패! 턴 종료"
            ui_elements.message_text.color = [255, 255, 0]  # 노란색
            
            _draw_game_screen(win, ui_elements, board_renderer, deck_renderer, token_renderer, None)
            win.flip()
            core.wait(FEEDBACK_DURATION)
            
            # 카드 다시 뒤로 감추기 (hide_card 사용)
            game_state.deck.hide_card(card_pos[0], card_pos[1])
            
            # PC 턴 종료 (사용자 턴으로 전환됨)
            return 'continue'
        
        elif result == 'game_end':
            return 'game_end'
    
    return 'continue'


def _get_clicked_card(mouse_pos):
    """
    마우스 클릭 위치에서 카드 인덱스 계산
    
    Args:
        mouse_pos: (x, y) 마우스 좌표 (PsychoPy 좌표계)
    
    Returns:
        tuple: (row, col) 또는 None (클릭한 카드가 없음)
    """
    # PsychoPy 좌표를 화면 좌표로 변환
    screen_x = mouse_pos[0] + WIDTH / 2
    screen_y = HEIGHT / 2 - mouse_pos[1]
    
    # 덱 영역 확인
    for row in range(3):  # BOARD_ROWS
        for col in range(9):  # BOARD_COLS
            left = DECK_LEFT_MARGIN + col * (DECK_CARD_WIDTH + DECK_CARD_SPACING)
            right = left + DECK_CARD_WIDTH
            top = DECK_TOP_MARGIN + row * (DECK_CARD_HEIGHT + DECK_CARD_SPACING)
            bottom = top + DECK_CARD_HEIGHT
            
            if left <= screen_x <= right and top <= screen_y <= bottom:
                return (row, col)
    
    return None


def _draw_game_screen(win, ui_elements, board_renderer, deck_renderer, token_renderer, highlighted_pos=None):
    """
    게임 화면 그리기
    
    Args:
        highlighted_pos: 하이라이트할 보드 위치 (row, col) 또는 None
    """
    board_renderer.draw(highlighted_pos)
    deck_renderer.draw()
    token_renderer.draw()
    ui_elements.timer_text.draw()
    ui_elements.score_text.draw()
    ui_elements.message_text.draw()
    ui_elements.instruction_text.draw()
