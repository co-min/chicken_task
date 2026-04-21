# Phase 0: Chicken Selection
# 사용자 턴 시작 시 어느 닭(Chase 또는 Flight)을 선택할지 결정하는 단계

import sys
from pathlib import Path
from psychopy import visual, core, event

try:
    from ..config import (
        WIDTH, HEIGHT, TEXT_COLOR, TEXT_SIZE,
        BUTTON_COLOR_NORMAL, BUTTON_COLOR_SELECTED,
        CHASE_BUTTON_POS, FLIGHT_BUTTON_POS,
        TOKEN_BUTTON_WIDTH, TOKEN_BUTTON_HEIGHT
    )
    from ..view_func.frame_marker import blink_frame_marker, trigger_frame_marker
    from ..sounds import play as sound_play
    from ..utils.labjack_triggers import send_trigger
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from config import (
        WIDTH, HEIGHT, TEXT_COLOR, TEXT_SIZE,
        BUTTON_COLOR_NORMAL, BUTTON_COLOR_SELECTED,
        CHASE_BUTTON_POS, FLIGHT_BUTTON_POS,
        TOKEN_BUTTON_WIDTH, TOKEN_BUTTON_HEIGHT
    )
    from view_func.frame_marker import blink_frame_marker, trigger_frame_marker
    from sounds import play as sound_play
    from utils.labjack_triggers import send_trigger

_LJ_TOKEN_CHASE  = 110
_LJ_TOKEN_FLIGHT = 111


def run_token_selection_phase(win, game_state, ui_elements, board_renderer, deck_renderer, token_renderer, sounds=None, labjack_handle=None):
    """
    Phase 0: 닭 선택 단계
    사용자가 Chase 또는 Flight 중 어떤 닭을 조종할지 선택
    
    Args:
        win: PsychoPy window 객체
        game_state: GameState 인스턴스
        ui_elements: UIElements 인스턴스
        board_renderer: BoardRenderer 인스턴스
        deck_renderer: DeckRenderer 인스턴스
        token_renderer: TokenRenderer 인스턴스
    
    Returns:
        str: 선택된 토큰 ('chase' 또는 'flight') 또는 'exit' (게임 종료)
    """
    
    # 마우스 객체
    mouse = event.Mouse(win=win)
    
    # 선택 상태
    selected_token = None  # 'chase' 또는 'flight'
    hovering = None  # 현재 마우스가 올라간 버튼

    # 토큰 선택 단계에서는 안내 문구를 버튼 위쪽으로 고정 배치
    original_instruction_pos = ui_elements.instruction_text.pos
    original_message_pos = ui_elements.message_text.pos
    button_top = CHASE_BUTTON_POS[1] + (TOKEN_BUTTON_HEIGHT / 2)
    ui_elements.instruction_text.pos = (0, button_top + 25)
    ui_elements.message_text.pos = (0, button_top + 60)
    ui_elements.instruction_text.text = "닭을 선택하세요"
    ui_elements.message_text.text = ""
    
    
    
    # 메인 루프
    while True:
        # 마우스 위치 확인
        mouse_pos = mouse.getPos()
        hovering = None
        
        # Chase 버튼 위에 있는지 확인
        if _is_mouse_over_button(mouse_pos, CHASE_BUTTON_POS, TOKEN_BUTTON_WIDTH, TOKEN_BUTTON_HEIGHT):
            hovering = 'chase'
            # 클릭 확인
            if mouse.getPressed()[0]:  # 왼쪽 버튼
                selected_token = 'chase'
                sound_play(sounds, 'type')
                game_state.select_token(selected_token)
                send_trigger(labjack_handle, _LJ_TOKEN_CHASE)
                trigger_frame_marker()   # 이벤트: 닭 선택 (Chase)
                while mouse.getPressed()[0]:
                    core.wait(0.01)
                ui_elements.instruction_text.text = ""
                ui_elements.message_text.text = ""
                ui_elements.instruction_text.pos = original_instruction_pos
                ui_elements.message_text.pos = original_message_pos
                return selected_token

        # Flight 버튼 위에 있는지 확인
        elif _is_mouse_over_button(mouse_pos, FLIGHT_BUTTON_POS, TOKEN_BUTTON_WIDTH, TOKEN_BUTTON_HEIGHT):
            hovering = 'flight'
            # 클릭 확인
            if mouse.getPressed()[0]:  # 왼쪽 버튼
                selected_token = 'flight'
                sound_play(sounds, 'type')
                game_state.select_token(selected_token)
                send_trigger(labjack_handle, _LJ_TOKEN_FLIGHT)
                trigger_frame_marker()   # 이벤트: 닭 선택 (Flight)
                while mouse.getPressed()[0]:
                    core.wait(0.01)
                ui_elements.instruction_text.text = ""
                ui_elements.message_text.text = ""
                ui_elements.instruction_text.pos = original_instruction_pos
                ui_elements.message_text.pos = original_message_pos
                return selected_token
        
        # 화면 그리기
        _draw_selection_screen(
            win, ui_elements, board_renderer, deck_renderer, token_renderer,
            selected_token, hovering, game_state
        )
        blink_frame_marker(win)
        win.flip()
        core.wait(0.016)  # ~60 FPS


def _is_mouse_over_button(mouse_pos, button_pos, button_width, button_height):
    """
    마우스가 버튼 위에 있는지 확인
    
    Args:
        mouse_pos: (x, y) 마우스 좌표
        button_pos: (x, y) 버튼 중심 좌표
        button_width: 버튼 너비
        button_height: 버튼 높이
    
    Returns:
        bool: 버튼 위에 있으면 True
    """
    left = button_pos[0] - button_width / 2
    right = button_pos[0] + button_width / 2
    top = button_pos[1] + button_height / 2
    bottom = button_pos[1] - button_height / 2
    
    return (left <= mouse_pos[0] <= right and 
            bottom <= mouse_pos[1] <= top)


def _draw_selection_screen(win, ui_elements, board_renderer, deck_renderer, token_renderer,
                           selected_token, hovering, game_state=None):
    """
    선택 화면 그리기
    
    Args:
        win: PsychoPy window
        ui_elements: UIElements 인스턴스
        board_renderer: BoardRenderer 인스턴스
        deck_renderer: DeckRenderer 인스턴스
        token_renderer: TokenRenderer 인스턴스
        selected_token: 선택된 토큰 ('chase', 'flight', None)
        hovering: 마우스가 올라간 버튼 ('chase', 'flight', None)
    """
    # 배경 보드 및 덱 그리기
    board_renderer.draw()
    deck_renderer.draw()
    token_renderer.draw()
    
    # Chase 버튼 그리기
    chase_button = ui_elements.token_choice_buttons['chase']
    
    # 버튼 색상 결정 (선택됨 > 마우스 오버 > 기본)
    if selected_token == 'chase':
        chase_button['rect'].fillColor = BUTTON_COLOR_SELECTED
        chase_button['rect'].lineWidth = 6
    elif hovering == 'chase':
        chase_button['rect'].fillColor = [150, 150, 150]
        chase_button['rect'].lineWidth = 4
    else:
        chase_button['rect'].fillColor = BUTTON_COLOR_NORMAL
        chase_button['rect'].lineWidth = 2
    
    chase_button['rect'].draw()
    chase_button['text'].draw()
    
    # Flight 버튼 그리기
    flight_button = ui_elements.token_choice_buttons['flight']
    
    # 버튼 색상 결정
    if selected_token == 'flight':
        flight_button['rect'].fillColor = BUTTON_COLOR_SELECTED
        flight_button['rect'].lineWidth = 6
    elif hovering == 'flight':
        flight_button['rect'].fillColor = [150, 150, 150]
        flight_button['rect'].lineWidth = 4
    else:
        flight_button['rect'].fillColor = BUTTON_COLOR_NORMAL
        flight_button['rect'].lineWidth = 2
    
    flight_button['rect'].draw()
    flight_button['text'].draw()
    
    # 안내 문구 및 메시지 그리기
    ui_elements.instruction_text.draw()
    ui_elements.message_text.draw()

    # 랭킹 패널: 누적 점수 갱신 후 표시
    if game_state is not None:
        ui_elements.update_ranking(game_state.user_score, game_state.pc_score)
    ui_elements.draw_ranking()