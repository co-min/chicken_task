# validators.py
# Chicken Task - Input Validation (키/마우스 검증)
# Phase 4 상호작용 단계의 입력 검증

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(__file__, '..', '..')))

from config import (
    KEY_CHASE, KEY_FLIGHT, KEY_CONFIRM, KEY_EXIT,
    DECK_LEFT_MARGIN, DECK_TOP_MARGIN, DECK_CARD_WIDTH, DECK_CARD_HEIGHT, DECK_CARD_SPACING,
    BOARD_LEFT_MARGIN, BOARD_TOP_MARGIN, BOARD_CARD_WIDTH, BOARD_CARD_HEIGHT, BOARD_CARD_SPACING,
    BOARD_ROWS, BOARD_COLS,
    TOKEN_BUTTON_WIDTH, TOKEN_BUTTON_HEIGHT, CHASE_BUTTON_POS, FLIGHT_BUTTON_POS
)
from utils.helpers import clamp


# ==================== 키보드 입력 검증 ====================

def validate_key_press(keys, allowed_keys):
    """
    키 입력이 허용된 키 목록에 있는지 검증
    
    Args:
        keys (list): 눌린 키 목록 (event.getKeys() 결과)
        allowed_keys (list): 허용된 키 목록
    
    Returns:
        str or None: 유효한 키가 있으면 해당 키, 없으면 None
    
    Examples:
        >>> validate_key_press(['up', 'space'], ['up', 'down'])
        'up'
        >>> validate_key_press(['space'], ['up', 'down'])
        None
    """
    if not keys:
        return None
    
    for key in keys:
        if key in allowed_keys:
            return key
    
    return None


def is_token_selection_key(key):
    """
    토큰 선택 키인지 확인 (Phase 0용)
    
    Args:
        key (str): 키 이름
    
    Returns:
        str or None: 'chase' 또는 'flight', 유효하지 않으면 None
    """
    if key == KEY_CHASE:
        return 'chase'
    elif key == KEY_FLIGHT:
        return 'flight'
    return None


def is_confirm_key(key):
    """
    확인 키인지 검증 (ENTER)
    
    Args:
        key (str): 키 이름
    
    Returns:
        bool: 확인 키이면 True
    """
    return key == KEY_CONFIRM


def is_exit_key(key):
    """
    종료 키인지 검증 (ESCAPE)
    
    Args:
        key (str): 키 이름
    
    Returns:
        bool: 종료 키이면 True
    """
    return key == KEY_EXIT


def validate_game_play_keys(keys):
    """
    게임 플레이 중 유효한 키 검증 (Phase 1+)
    
    Args:
        keys (list): 눌린 키 목록
    
    Returns:
        dict: {'key': 키 이름, 'action': 액션 타입}
        - 'exit': 게임 종료
        - 'reset': 게임 리셋 (선택적)
        - None: 유효하지 않은 키
    """
    if not keys:
        return None
    
    # 종료 키
    if KEY_EXIT in keys:
        return {'key': KEY_EXIT, 'action': 'exit'}
    
    # 추가 액션 키 (필요시 확장)
    if 'r' in keys:
        return {'key': 'r', 'action': 'reset'}
    
    if 'p' in keys:
        return {'key': 'p', 'action': 'pc_turn'}
    
    return None


# ==================== 마우스 입력 검증 ====================

def is_point_in_rect(point, rect_pos, rect_width, rect_height):
    """
    점이 사각형 내부에 있는지 검증
    
    Args:
        point (tuple): (x, y) 좌표
        rect_pos (tuple): 사각형 중심 (x, y)
        rect_width (float): 사각형 너비
        rect_height (float): 사각형 높이
    
    Returns:
        bool: 내부에 있으면 True
    """
    x, y = point
    rect_x, rect_y = rect_pos
    
    left = rect_x - rect_width / 2
    right = rect_x + rect_width / 2
    bottom = rect_y - rect_height / 2
    top = rect_y + rect_height / 2
    
    return left <= x <= right and bottom <= y <= top


def validate_deck_click(mouse_pos, deck_rows=3, deck_cols=9):
    """
    마우스 클릭이 메인 덱 영역 내인지 검증 및 위치 반환
    
    Args:
        mouse_pos (tuple): 마우스 위치 (x, y)
        deck_rows (int): 덱 행 수
        deck_cols (int): 덱 열 수
    
    Returns:
        tuple or None: (row, col) 위치, 유효하지 않으면 None
        - row: 0-based 행 인덱스
        - col: 0-based 열 인덱스
    """
    x, y = mouse_pos
    
    # 카드 간격 포함한 총 크기
    card_total_width = DECK_CARD_WIDTH + DECK_CARD_SPACING
    card_total_height = DECK_CARD_HEIGHT + DECK_CARD_SPACING
    
    # 좌측 상단 기준 좌표로 변환 (PsychoPy는 중앙이 (0, 0))
    # 화면 중심 기준 -> 픽셀 기준 변환
    from config import WIDTH, HEIGHT
    pixel_x = x + WIDTH / 2
    pixel_y = HEIGHT / 2 - y
    
    # 덱 영역 기준 상대 좌표
    rel_x = pixel_x - DECK_LEFT_MARGIN
    rel_y = pixel_y - DECK_TOP_MARGIN
    
    # 범위 검사
    if rel_x < 0 or rel_y < 0:
        return None
    
    # 클릭한 카드의 행/열 계산
    col = int(rel_x / card_total_width)
    row = int(rel_y / card_total_height)
    
    # 인덱스 범위 검사
    if row < 0 or row >= deck_rows or col < 0 or col >= deck_cols:
        return None
    
    # 카드 내부 클릭인지 확인 (간격이 아닌 카드 영역)
    card_x = rel_x % card_total_width
    card_y = rel_y % card_total_height
    
    if card_x > DECK_CARD_WIDTH or card_y > DECK_CARD_HEIGHT:
        return None  # 간격 클릭
    
    return (row, col)


def validate_board_click(mouse_pos, board_rows=BOARD_ROWS, board_cols=BOARD_COLS):
    """
    마우스 클릭이 보드 영역 내인지 검증 및 위치 반환
    
    Args:
        mouse_pos (tuple): 마우스 위치 (x, y)
        board_rows (int): 보드 행 수
        board_cols (int): 보드 열 수
    
    Returns:
        tuple or None: (row, col) 위치, 유효하지 않으면 None
    """
    x, y = mouse_pos
    
    # 카드 간격 포함한 총 크기
    card_total_width = BOARD_CARD_WIDTH + BOARD_CARD_SPACING
    card_total_height = BOARD_CARD_HEIGHT + BOARD_CARD_SPACING
    
    # 좌측 상단 기준 좌표로 변환
    from config import WIDTH, HEIGHT
    pixel_x = x + WIDTH / 2
    pixel_y = HEIGHT / 2 - y
    
    # 보드 영역 기준 상대 좌표
    rel_x = pixel_x - BOARD_LEFT_MARGIN
    rel_y = pixel_y - BOARD_TOP_MARGIN
    
    # 범위 검사
    if rel_x < 0 or rel_y < 0:
        return None
    
    # 클릭한 카드의 행/열 계산
    col = int(rel_x / card_total_width)
    row = int(rel_y / card_total_height)
    
    # 인덱스 범위 검사
    if row < 0 or row >= board_rows or col < 0 or col >= board_cols:
        return None
    
    # 카드 내부 클릭인지 확인
    card_x = rel_x % card_total_width
    card_y = rel_y % card_total_height
    
    if card_x > BOARD_CARD_WIDTH or card_y > BOARD_CARD_HEIGHT:
        return None  # 간격 클릭
    
    return (row, col)


def validate_button_click(mouse_pos, button_name):
    """
    토큰 선택 버튼 클릭 검증 (Phase 0용)
    
    Args:
        mouse_pos (tuple): 마우스 위치 (x, y)
        button_name (str): 'chase' 또는 'flight'
    
    Returns:
        bool: 해당 버튼 내부 클릭이면 True
    """
    if button_name == 'chase':
        button_pos = CHASE_BUTTON_POS
    elif button_name == 'flight':
        button_pos = FLIGHT_BUTTON_POS
    else:
        return False
    
    return is_point_in_rect(
        mouse_pos,
        button_pos,
        TOKEN_BUTTON_WIDTH,
        TOKEN_BUTTON_HEIGHT
    )


def get_clicked_button(mouse_pos):
    """
    클릭된 버튼 식별 (Phase 0용)
    
    Args:
        mouse_pos (tuple): 마우스 위치 (x, y)
    
    Returns:
        str or None: 'chase' 또는 'flight', 없으면 None
    """
    if validate_button_click(mouse_pos, 'chase'):
        return 'chase'
    elif validate_button_click(mouse_pos, 'flight'):
        return 'flight'
    return None


# ==================== 게임 상태 검증 ====================

def validate_phase_transition(current_phase, requested_action):
    """
    현재 페이즈에서 요청한 액션이 유효한지 검증
    
    Args:
        current_phase (str): 현재 게임 페이즈
        requested_action (str): 요청 액션
            - 'select_token': 토큰 선택
            - 'confirm_selection': 선택 확정
            - 'click_card': 카드 클릭
            - 'pc_turn': PC 턴
    
    Returns:
        bool: 유효하면 True
    """
    # Phase별 허용 액션
    valid_actions = {
        'not_started': [],
        'token_selection': ['select_token', 'confirm_selection'],
        'game_play': ['click_card', 'pc_turn'],
        'victory': [],
        'defeat': []
    }
    
    return requested_action in valid_actions.get(current_phase, [])


def validate_turn(current_turn, player_type):
    """
    현재 턴에서 해당 플레이어가 행동할 수 있는지 검증
    
    Args:
        current_turn (str): 현재 턴 ('user' 또는 'pc')
        player_type (str): 플레이어 타입 ('user' 또는 'pc')
    
    Returns:
        bool: 행동 가능하면 True
    """
    return current_turn == player_type


def validate_time_remaining(timer):
    """
    남은 시간이 있는지 검증
    
    Args:
        timer: GameTimer 객체
    
    Returns:
        bool: 시간이 남아있으면 True
    """
    return timer.get_remaining() > 0


# ==================== 호버 검증 (UI용) ====================

def get_hovered_button(mouse_pos):
    """
    마우스가 어느 버튼 위에 있는지 확인 (hover 상태)
    
    Args:
        mouse_pos (tuple): 마우스 위치 (x, y)
    
    Returns:
        str or None: 'chase' 또는 'flight', 없으면 None
    """
    return get_clicked_button(mouse_pos)


def get_hovered_deck_card(mouse_pos):
    """
    마우스가 어느 덱 카드 위에 있는지 확인 (hover 상태)
    
    Args:
        mouse_pos (tuple): 마우스 위치 (x, y)
    
    Returns:
        tuple or None: (row, col) 위치, 없으면 None
    """
    return validate_deck_click(mouse_pos)


def get_hovered_board_card(mouse_pos):
    """
    마우스가 어느 보드 카드 위에 있는지 확인 (hover 상태)
    
    Args:
        mouse_pos (tuple): 마우스 위치 (x, y)
    
    Returns:
        tuple or None: (row, col) 위치, 없으면 None
    """
    return validate_board_click(mouse_pos)


# ==================== 통합 검증 함수 ====================

def validate_user_input(keys, mouse_pressed, mouse_pos, game_state):
    """
    사용자 입력을 통합 검증하고 액션 반환
    
    Args:
        keys (list): 눌린 키 목록
        mouse_pressed (list): 마우스 버튼 상태 [left, middle, right]
        mouse_pos (tuple): 마우스 위치 (x, y)
        game_state: GameState 객체
    
    Returns:
        dict or None: 액션 정보
            - 'type': 액션 타입 ('key', 'mouse', 'none')
            - 'action': 구체적인 액션
            - 'data': 추가 데이터
    """
    # 종료 키 우선 처리
    if keys and KEY_EXIT in keys:
        return {
            'type': 'key',
            'action': 'exit',
            'data': None
        }
    
    # Phase별 검증
    phase = game_state.phase
    
    # Phase 0: 토큰 선택
    if phase == 'token_selection':
        # 키보드 입력
        if keys:
            for key in keys:
                token = is_token_selection_key(key)
                if token:
                    return {
                        'type': 'key',
                        'action': 'select_token',
                        'data': token
                    }
                
                if is_confirm_key(key):
                    return {
                        'type': 'key',
                        'action': 'confirm_selection',
                        'data': None
                    }
        
        # 마우스 클릭
        if mouse_pressed[0]:  # 좌클릭
            button = get_clicked_button(mouse_pos)
            if button:
                return {
                    'type': 'mouse',
                    'action': 'select_token',
                    'data': button
                }
    
    # Phase 1+: 게임 플레이
    elif phase == 'game_play':
        # 유저 턴인지 확인
        if not validate_turn(game_state.current_turn, 'user'):
            return None
        
        # 시간 체크
        if not validate_time_remaining(game_state.timer):
            return {
                'type': 'system',
                'action': 'timeout',
                'data': None
            }
        
        # 마우스 클릭
        if mouse_pressed[0]:  # 좌클릭
            deck_pos = validate_deck_click(mouse_pos)
            if deck_pos:
                return {
                    'type': 'mouse',
                    'action': 'click_card',
                    'data': deck_pos
                }
        
        # 디버그 키
        if keys:
            key_action = validate_game_play_keys(keys)
            if key_action:
                return {
                    'type': 'key',
                    'action': key_action['action'],
                    'data': None
                }
    
    return None


# ==================== 유틸리티 함수 ====================
# clamp() 함수는 helpers.py에서 import하여 사용

def distance(point1, point2):
    """
    두 점 사이의 거리 계산
    
    Args:
        point1 (tuple): 첫 번째 점 (x, y)
        point2 (tuple): 두 번째 점 (x, y)
    
    Returns:
        float: 거리
    """
    import math
    return math.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)
