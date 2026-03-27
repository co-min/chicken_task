# Phase 1 + : GamePlay
# 게임 플레이 단계 - 사용자와 PC가 교대로 카드를 선택하며 게임 진행

import sys
from pathlib import Path
from psychopy import core, event

try:
    from ..config import (
        KEY_EXIT, CARD_FLIP_DURATION,
        FEEDBACK_DURATION, TRIAL_INTERVAL, PC_THINK_TIME,
        WIDTH, HEIGHT, TEXT_COLOR,
        DECK_LEFT_EDGE, BOARD_DECK_TOP_MARGIN,
        DECK_CARD_WIDTH, DECK_CARD_HEIGHT, DECK_CARD_SPACING,
        PURPLE, DARK_GREY
    )
    from ..phase_func.token_selection import run_token_selection_phase
    from ..phase_func.feedback import run_feedback_phase
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from config import (
        KEY_EXIT, CARD_FLIP_DURATION,
        FEEDBACK_DURATION, TRIAL_INTERVAL, PC_THINK_TIME,
        WIDTH, HEIGHT, TEXT_COLOR,
        DECK_LEFT_EDGE, BOARD_DECK_TOP_MARGIN,
        DECK_CARD_WIDTH, DECK_CARD_HEIGHT, DECK_CARD_SPACING,
        PURPLE, DARK_GREY
    )
    from phase_func.token_selection import run_token_selection_phase
    from phase_func.feedback import run_feedback_phase

try:
    from ..view_func.frame_marker import blink_frame_marker, trigger_frame_marker
except ImportError:
    from view_func.frame_marker import blink_frame_marker, trigger_frame_marker


START_CUE_DURATION = 0.8


def run_game_play_phase(win, game_state, ui_elements, board_renderer, deck_renderer,
                        token_renderer, aoi_manager=None):
    """
    Phase 1+: 게임 플레이 단계
    사용자와 PC가 교대로 턴을 진행하며 게임을 플레이

    턴 시스템:
    - 사용자 턴: 닭 선택 → 카드 선택 → 성공(계속)/실패(PC 턴)
    - PC 턴: AI 카드 선택 (60% 정답률) → 성공(계속)/실패(사용자 턴)

    Args:
        win: PsychoPy window 객체
        game_state: GameState 인스턴스
        ui_elements: UIElements 인스턴스
        board_renderer: BoardRenderer 인스턴스
        deck_renderer: DeckRenderer 인스턴스
        token_renderer: TokenRenderer 인스턴스
        aoi_manager: AOIManager 인스턴스 (선택, None 이면 AOI 추적 비활성화)

    Returns:
        str: 게임 종료 이유 ('victory', 'defeat', 'exit')
    """
    
    # 마우스 객체
    mouse = event.Mouse(win=win)
    
    # 게임 메인 루프
    while True:
        # 게임 종료 확인
        if game_state.phase == game_state.PHASE_VICTORY:
            print("[GAME END] 플레이어 승리!")
            return 'victory'
        elif game_state.phase == game_state.PHASE_DEFEAT:
            print("[GAME END] 문어 승리 (플레이어 패배)")
            return 'defeat'
        elif game_state.is_game_time_expired():
            print("[GAME END] 전체 게임 시간 초과!")
            return 'timeout'
        
        # 현재 턴 확인 및 실행
        if game_state.current_turn == game_state.TURN_USER:
            # 사용자 턴 실행
            result = _run_user_turn(win, game_state, ui_elements, board_renderer,
                                   deck_renderer, token_renderer, mouse, aoi_manager)
            
            if result == 'exit':
                return 'exit'
            elif result == 'game_end':
                # 게임 종료 (승리 또는 패배)
                continue
            elif result == 'continue':
                # 사용자 턴 종료 → PC 턴으로 전환됨
                print(f"[TURN SWITCH] 사용자 → 문어 (턴 {game_state.turn_count})")
            
        elif game_state.current_turn == game_state.TURN_PC:
            # PC 턴 실행
            result = _run_pc_turn(win, game_state, ui_elements, board_renderer,
                                 deck_renderer, token_renderer)
            
            if result == 'game_end':
                # 게임 종료 (승리 또는 패배)
                continue
            elif result == 'continue':
                # PC 턴 종료 → 사용자 턴으로 전환됨
                print(f"[TURN SWITCH] 문어 → 사용자 (턴 {game_state.turn_count})")
        
        # 프레임 대기
        core.wait(0.005)


def _run_user_turn(win, game_state, ui_elements, board_renderer, deck_renderer,
                   token_renderer, mouse, aoi_manager=None):
    """
    사용자 턴 실행

    흐름:
    1. 닭 선택 단계 (선택되지 않았을 경우)
    2. 카드 선택 루프 (같은 닭으로 계속 시도)
       - 성공: 타이머 리셋 후 다음 타겟으로 계속
       - 실패/타임아웃: 턴 종료 → PC 턴으로 전환

    Returns:
        str: 'exit' (게임 종료), 'game_end' (승패 결정), 'continue' (턴 종료 → PC 턴)
    """
    
    # 1. 닭 선택 단계 (토큰이 선택되지 않았을 때만)
    if game_state.selected_token is None:
        print(f"[USER TURN] 닭 선택 단계 (턴 {game_state.turn_count})")
        selected = run_token_selection_phase(win, game_state, ui_elements, 
                                            board_renderer, deck_renderer, token_renderer)
        
        if selected == 'exit':
            return 'exit'
        
        # 선택 확정 및 타이머 시작
        game_state.confirm_selection()
        print(f"[USER TURN] {game_state.selected_token.upper()} 선택, 카드 선택 시작")
    
    # 2. 카드 선택 루프 (같은 토큰으로 계속 진행)
    while game_state.phase == game_state.PHASE_GAME_PLAY and \
          game_state.current_turn == game_state.TURN_USER:
        
        # 타겟 위치 업데이트 (매 루프마다)
        target_pos = game_state.get_target_position()
        
        # 사용자 턴 HUD 업데이트
        ui_elements.set_user_turn_hud(
            selected_token=game_state.selected_token,
            turn_count=game_state.turn_count,
            timer_display_text=game_state.timer.get_display_text(),
        )
        
        # 시간 초과 확인
        if game_state.timer.is_expired():
            print(f"[USER TURN] 타임아웃! 턴 종료")
            run_feedback_phase(
                win,
                ui_elements,
                board_renderer,
                deck_renderer,
                token_renderer,
                message="시간 초과",
                color=DARK_GREY,
                duration=FEEDBACK_DURATION,
                highlighted_pos=None,
            )
            
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
            card_pos = _get_clicked_card(mouse_pos, game_state.deck.rows, game_state.deck.cols)
            
            if card_pos is not None:
                card_row, card_col = card_pos
                
                # 카드 선택 처리
                result = game_state.user_click_card(card_row, card_col, defer_success_move=True)
                print(f"[USER TURN] 카드 선택: {card_pos}, 결과: {result}")
                
                # 카드 뒤집기 애니메이션 (game_state.user_click_card에서 이미 flip 수행됨)
                _draw_game_screen(win, ui_elements, board_renderer, deck_renderer, token_renderer, game_state, target_pos)
                trigger_frame_marker()   # 이벤트: 사용자 카드 뒤집기
                blink_frame_marker(win)
                win.flip()
                core.wait(CARD_FLIP_DURATION)
                
                # 결과 처리
                if result == 'success':
                    run_feedback_phase(
                        win,
                        ui_elements,
                        board_renderer,
                        deck_renderer,
                        token_renderer,
                        message="성공",
                        color=PURPLE,
                        duration=FEEDBACK_DURATION,
                        highlighted_pos=None,
                    )

                    # 성공 피드백 이후 토큰 이동
                    move_result = game_state.complete_user_success_move()
                    
                    # 카드 뒤로 감추기 (hide_card 사용)
                    game_state.deck.hide_card(card_row, card_col)

                    if move_result == 'game_end':
                        game_state.selected_token = None
                        return 'game_end'
                    
                    # 모든 피드백이 끝난 뒤 타이머 리셋
                    core.wait(TRIAL_INTERVAL)
                    _show_start_cue(
                        win,
                        ui_elements,
                        board_renderer,
                        deck_renderer,
                        token_renderer,
                        game_state=game_state,
                        selected_token=game_state.selected_token,
                        turn_count=game_state.turn_count,
                        timer_display_text=game_state.timer.get_display_text(),
                        target_pos=game_state.get_target_position(),
                    )
                    game_state.timer.reset()
                    print(f"[USER TURN] 성공, 타이머 리셋, 다음 타겟으로 계속")
                    # 계속 루프를 진행하여 다음 타겟으로
                    continue
                
                elif result == 'failure':
                    run_feedback_phase(
                        win,
                        ui_elements,
                        board_renderer,
                        deck_renderer,
                        token_renderer,
                        message="실패",
                        color=DARK_GREY,
                        duration=FEEDBACK_DURATION,
                        highlighted_pos=None,
                    )
                    
                    # 카드 뒤로 감추기 (hide_card 사용)
                    game_state.deck.hide_card(card_row, card_col)
                    
                    # 턴 종료 (end_user_turn에서 selected_token 리셋됨)
                    print(f"[USER TURN] 실패, 턴 종료")
                    return 'continue'
                
                elif result == 'game_end':
                    # 게임 종료
                    game_state.selected_token = None
                    return 'game_end'
                
                # 클릭 후 버튼이 떼어지기를 기다림
                while mouse.getPressed()[0]:
                    pass
        
        # 화면 그리기 (타겟 하이라이트 포함)
        _draw_game_screen(win, ui_elements, board_renderer, deck_renderer, token_renderer, game_state, target_pos)
        blink_frame_marker(win)
        win.flip()

        # AOI 시선 추적 업데이트 (flip 직후 호출하여 프레임 타임스탬프와 동기화)
        if aoi_manager:
            aoi_manager.update(core.getTime())

        core.wait(0.016)

    return 'continue'


def _run_pc_turn(win, game_state, ui_elements, board_renderer, deck_renderer, token_renderer):
    """
    PC 턴 실행 (NPC AI 사용)
    
    흐름:
    1. NPC AI가 카드 선택 (60% 정답률)
    2. 카드 뒤집기 애니메이션
    3. 결과 판정 표시
    4. 성공 시: 토큰 이동 애니메이션 → 다음 타겟으로 계속
       실패 시: 턴 종료 → 사용자 턴으로 전환
    
    Returns:
        str: 'game_end' (승패 결정), 'continue' (턴 종료 → 사용자 턴)
    """
    
    # PC 턴 루프 (성공 시 계속 진행)
    while game_state.current_turn == game_state.TURN_PC:
        print(f"[문어] Octopus 카드 선택 시작 (턴 {game_state.turn_count})")
        
        # PC 타겟 위치 확인
        pc_target_pos = game_state.tokens.get_target_position('octopus')
        
        # PC 턴 HUD 업데이트
        ui_elements.set_pc_turn_hud(
            turn_count=game_state.turn_count,
            target_pos=pc_target_pos,
            timer_label="문어 턴",
        )
        
        # 타겟 하이라이트와 함께 화면 그리기
        _draw_game_screen(win, ui_elements, board_renderer, deck_renderer, token_renderer, game_state, pc_target_pos)
        trigger_frame_marker()   # 이벤트: PC 턴 시작
        blink_frame_marker(win)
        win.flip()

        # PC 생각 시간
        core.wait(PC_THINK_TIME)
        
        # PC 카드 선택 및 실행 (NPC AI 사용, result와 card_pos 반환)
        result, card_pos = game_state.pc_turn_step(defer_success_move=True)
        print(f"[PC TURN] 카드 선택: {card_pos}, 결과: {result}")
        
        # 1단계: 카드 뒤집기 애니메이션 (타겟 하이라이트 유지)
        # ui_elements.message_text.text = f"문어가 ({card_pos[0]}, {card_pos[1]}) 카드 선택"
        _draw_game_screen(win, ui_elements, board_renderer, deck_renderer, token_renderer, game_state, pc_target_pos)
        trigger_frame_marker()   # 이벤트: PC 카드 뒤집기
        blink_frame_marker(win)
        win.flip()
        core.wait(CARD_FLIP_DURATION)
        
        # 2단계: 결과 판정 표시
        if result == 'success':
            feedback_message = "문어 성공"
            feedback_color = PURPLE
        elif result == 'failure':
            feedback_message = "문어 실패"
            feedback_color = DARK_GREY
        elif result == 'game_end':
            feedback_message = ""
            feedback_color = [0, 0, 0]

        run_feedback_phase(
            win,
            ui_elements,
            board_renderer,
            deck_renderer,
            token_renderer,
            message=feedback_message,
            color=feedback_color,
            duration=FEEDBACK_DURATION,
            highlighted_pos=pc_target_pos,
        )
        
        # 3단계: 결과에 따른 처리
        if result == 'success':
            move_result = game_state.complete_pc_success_move()

            # 카드 숨기고 토큰 위치 업데이트된 화면 표시
            game_state.deck.hide_card(card_pos[0], card_pos[1])

            if move_result == 'game_end':
                return 'game_end'

            run_feedback_phase(
                win,
                ui_elements,
                board_renderer,
                deck_renderer,
                token_renderer,
                message="",
                color=PURPLE,
                duration=FEEDBACK_DURATION,
                highlighted_pos=None,
            )
            
            # 계속 PC 턴 진행 (루프 계속)
            print(f"[문어] 성공, 다음 타겟으로 계속")
            core.wait(TRIAL_INTERVAL)
            continue
            
        elif result == 'failure':
            # 실패 시 카드 숨기기
            game_state.deck.hide_card(card_pos[0], card_pos[1])
            run_feedback_phase(
                win,
                ui_elements,
                board_renderer,
                deck_renderer,
                token_renderer,
                message="",
                color=DARK_GREY,
                duration=FEEDBACK_DURATION,
                highlighted_pos=None,
            )
            
            # PC 턴 종료 (사용자 턴으로 전환됨)
            print(f"[문어] 실패, 턴 종료")
            return 'continue'
        
        elif result == 'game_end':
            # 게임 종료
            return 'game_end'
    
    return 'continue'


def _get_clicked_card(mouse_pos, deck_rows, deck_cols):
    """
    마우스 클릭 위치에서 카드 인덱스 계산

    Args:
        mouse_pos: (x, y) 마우스 좌표 (PsychoPy 좌표계)

    Returns:
        tuple: (row, col) 또는 None (클릭한 카드가 없음)
    """
    screen_x = mouse_pos[0] + WIDTH / 2
    screen_y = HEIGHT / 2 - mouse_pos[1]

    for row in range(deck_rows):
        for col in range(deck_cols):
            left = DECK_LEFT_EDGE + col * (DECK_CARD_WIDTH + DECK_CARD_SPACING)
            right = left + DECK_CARD_WIDTH
            top = BOARD_DECK_TOP_MARGIN + row * (DECK_CARD_HEIGHT + DECK_CARD_SPACING)
            bottom = top + DECK_CARD_HEIGHT

            if left <= screen_x <= right and top <= screen_y <= bottom:
                return (row, col)

    return None


def _draw_game_screen(win, ui_elements, board_renderer, deck_renderer, token_renderer,
                      game_state=None, highlighted_pos=None):
    """
    게임 화면 그리기

    Args:
        game_state: GameState 인스턴스 (점수 표시용, None이면 score_text 그대로 사용)
        highlighted_pos: 하이라이트할 보드 위치 (row, col) 또는 None
    """
    board_renderer.draw(highlighted_pos)
    deck_renderer.draw()
    token_renderer.draw()
    ui_elements.timer_text.draw()
    if game_state is not None:
        ui_elements.draw_score(game_state.user_score, game_state.pc_score)
    else:
        ui_elements.score_text.draw()
    ui_elements.message_text.draw()
    ui_elements.instruction_text.draw()


def _show_start_cue(
    win,
    ui_elements,
    board_renderer,
    deck_renderer,
    token_renderer,
    game_state,
    selected_token,
    turn_count,
    timer_display_text,
    target_pos,
):
    """다음 시도를 시작하기 직전에 큰 시작 문구를 잠깐 표시"""
    ui_elements.set_user_turn_hud(
        selected_token=selected_token,
        turn_count=turn_count,
        timer_display_text=timer_display_text,
    )
    _draw_game_screen(
        win,
        ui_elements,
        board_renderer,
        deck_renderer,
        token_renderer,
        game_state,
        target_pos,
    )
    ui_elements.draw_start_cue("시작!")
    trigger_frame_marker()   # 이벤트: 시행 시작 큐
    blink_frame_marker(win)
    win.flip()
    core.wait(START_CUE_DURATION)
