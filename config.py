# config.py
# Chicken Task - Configuration File
# All game constants and settings

# ==================== SCREEN SETTINGS ====================
WIDTH = 1100 # 화면 너비
HEIGHT = 1080 # 화면 높이
BG_COLOR = [128, 128, 128]  # RGB 0-255 (gray)
FULLSCREEN = True
AUTO_DETECT_WINDOW_SIZE = True   # True면 화면 해상도를 감지해서 창 크기 자동 보정
FORCE_WINDOWED_MODE = False       # True면 full screen 대신 창 모드로 강제 실행

# PsychoPy monitor profile (임시 monitor 경고 방지)
MONITOR_NAME = 'chicken_task_monitor'
MONITOR_WIDTH_CM = 60.0          # 물리적 모니터 가로 길이(cm)
MONITOR_DISTANCE_CM = 60.0       # 눈-모니터 거리(cm)

# ==================== BOARD SETTINGS ====================
BOARD_ROWS = 3
BOARD_COLS = 9
TOTAL_CARDS = BOARD_ROWS * BOARD_COLS  # 레거시 기본(모드 선택 전) 카드 수

# Layout - 보드/덱 위치 (1100x1080 기준, AUTO_DETECT_WINDOW_SIZE=True 시 자동 스케일)
#
# 설계 원칙:
#   1) 덱 총 height = 보드 총 height  →  deck_h = (5×board_h + 2×sp) / 3
#   2) 덱 가로세로 비율 = 0.68 (deck_w = deck_h × 0.68)
#   3) 카드 간격 확장 (아이트래커 AOI 분리)
#   4) 레이아웃은 auto-scale 후 화면 가운데 정렬
#
# 기준 검증 (1100×1080, sp=5):
#   board_h=73, deck_h=(5×73+2×5)/3=125, deck_w=125×0.68=85
#   board: 9×52+8×5=508,  deck: 6×85+5×5=535,  gap=50
#   총: 2+508+50+535+2=1097 ≤ 1100 ✓
#   board height: 5×73+4×5=385,  deck height: 3×125+2×5=385 ✓ (동일)
BOARD_DECK_CENTER_GAP = 50    # 보드↔덱 사이 여백 (아이트래커 기준)
BOARD_DECK_TOP_MARGIN = 120   # 상단 HUD 아래 여백 (HUD 텍스트 겹침 방지)

# 보드 카드 크기 (비율 52:73 = 0.712 ≈ 원본 68:95)
BOARD_CARD_WIDTH = 52
BOARD_CARD_HEIGHT = 73
BOARD_CARD_SPACING = 5        # 아이트래커 AOI 분리용 간격

BOARD_TOTAL_WIDTH = BOARD_COLS * BOARD_CARD_WIDTH + (BOARD_COLS - 1) * BOARD_CARD_SPACING
BOARD_LEFT_EDGE = 2           # 운동장 보드 왼쪽 시작 위치 (화면 좌측 기준 px)
BOARD_LEFT_MARGIN = BOARD_LEFT_EDGE  # 레거시 alias
BOARD_TOP_MARGIN = BOARD_DECK_TOP_MARGIN
BOARD_Y_OFFSET = 0

# 덱 카드 크기 (비율 85:125 = 0.68 ✓, 총 height = 보드 총 height)
DECK_CARD_WIDTH = 85
DECK_CARD_HEIGHT = 125
DECK_CARD_SPACING = 5         # 아이트래커 AOI 분리용 간격

DECK_TOTAL_WIDTH = BOARD_COLS * DECK_CARD_WIDTH + (BOARD_COLS - 1) * DECK_CARD_SPACING
DECK_LEFT_EDGE = BOARD_LEFT_EDGE + BOARD_TOTAL_WIDTH + BOARD_DECK_CENTER_GAP  # = 2+508+50=560
DECK_LEFT_MARGIN = DECK_LEFT_EDGE  # 레거시 alias
DECK_TOP_MARGIN = BOARD_DECK_TOP_MARGIN
DECK_X_OFFSET = 0

# ==================== TOKEN SETTINGS ====================
TOKEN_SIZE = 43  # pixels (보드 카드 73px 기준, 56×73/95≈43)


# ==================== CARD ATTRIBUTES ====================
# 기본 27가지 조건: 색상(3) × 모양(3) × 숫자(3)
# 각 GAME_MODE에서는 이 중 부분집합을 선택해서 사용
COLORS = ['red', 'green', 'blue']
SHAPES = ['square', 'triangle', 'circle']
NUMBERS = [1, 2, 3]

# Color mapping for display (RGB 0-255)
COLOR_RGB = {
    'red': [255, 0, 0],
    'blue': [0, 0, 255],
    'green': [0, 200, 0]
}

# ==================== TIMING SETTINGS ====================
TURN_TIME_LIMIT = 15          # 초 (매 시도마다 리셋)
CARD_FLIP_DURATION = 2       # 초 (카드 앞면 노출 시간)
FEEDBACK_DURATION = 0.5       # 초 (피드백 표시 시간)
TRIAL_INTERVAL = 1          # 초 (시행 간 간격)
TOKEN_TIME_WAIT = 1

# ==================== PC AI SETTINGS ====================
# 레거시 기본 정답률(모드 선택 전). 실제 게임 실행 시에는 mode 기반 deck 크기로 재계산됨.
PC_SUCCESS_RATE = 1 / TOTAL_CARDS
PC_THINK_TIME = 1.8           # 초 (PC 선택까지 대기 시간)

# ==================== VISUAL SETTINGS ====================
# Highlight colors
HIGHLIGHT_COLOR = [0, 255, 200]  # Mint color for target
HIGHLIGHT_WIDTH = 4              # Border width

# Text settings
TEXT_COLOR = [0, 0, 0]     # Black
TEXT_SIZE = 28                   # 1080x1080 화면에 맞춤

# Button colors
BUTTON_COLOR_NORMAL = [100, 100, 100]
BUTTON_COLOR_HOVER = [150, 150, 150]
BUTTON_COLOR_SELECTED = [0, 200, 200]  # Mint

# Token choice button settings (Chase / Flight)
TOKEN_BUTTON_WIDTH = 300
TOKEN_BUTTON_HEIGHT = 95
TOKEN_BUTTON_TEXT_HEIGHT = 30
CHASE_BUTTON_POS = (-170, -430)      # (x, y)
FLIGHT_BUTTON_POS = (170, -430)      # (x, y)
TOKEN_BUTTON_LINE_WIDTH = 4
MESSAGE_Y_OFFSET = -70  # 메시지 문구 위치 (+면 위, -면 아래) → 버튼과 같은 y 레벨

# ==================== KEY MAPPINGS ====================
KEY_CHASE = 'left'            # chase 선택 (왼쪽 버튼)
KEY_FLIGHT = 'right'          # flight 선택 (오른쪽 버튼)
KEY_EXIT = 'escape'           # 게임 종료


# ==================== EXPERIMENT SETTINGS ====================
USE_PRACTICE = 1              # 0: 연습 없음, 1: 연습 있음
PRACTICE_TRIALS = 1           # 연습 시행 수

# ==================== EYE TRACKING ====================
USE_EYELINK = 0               # 0: 미사용, 1: 사용

# ==================== LABJACK T4 ====================
USE_LABJACK = 0               # 0: 미사용, 1: 사용

# ==================== AOI (Area of Interest) ====================
# AOI 진입으로 인정하기 위한 최소 시선 체류 시간 (초)
AOI_DWELL_THRESHOLD = 0.1

# LabJack TTL 트리거 펄스 지속 시간 (초)
# AOIManager 가 비블로킹 방식으로 이 시간 이후 자동 리셋함
AOI_TRIGGER_PULSE_S = 0.005

# EIO_STATE 트리거 코드 기준값
#   보드 카드 AOI 진입: AOI_TRIGGER_BOARD_OFFSET + position_index  (예: 10~33)
#   덱  카드 AOI 진입: AOI_TRIGGER_DECK_OFFSET  + position_index  (예: 40~66)
#   값 0 은 "리셋/무신호" 로 예약됨
AOI_TRIGGER_BOARD_OFFSET = 10
AOI_TRIGGER_DECK_OFFSET  = 40

# ==================== DATA SAVING ====================
SAVE_FRAME_LOG = True         # 프레임별 로그 저장 여부
SAVE_GAME_STATE = True        # 게임 상태 스냅샷 저장 여부

# ==================== DEBUG SETTINGS ====================
DEBUG_MODE = False            # True: 디버그 정보 표시
SHOW_TIMER = True             # 타이머 표시 여부
AUTO_HIDE_CARDS = True        # 카드 자동 뒷면 복구 여부

# ==================== GAME STATE ====================
TOTAL_SCORE = 0               # 전체 점수 (게임 중 업데이트)


# game_play.py의 run_feedback_phase 색상
PURPLE = [180, 0, 255]
DARK_GREY = [105, 105, 105]
WHITE=[255,255,255]


# ==================== GAME MODE SELECTION (PHASE 1) ====================
DEFAULT_GAME_MODE = 'selection1'

# 각 게임 모드는 3×3×3 조건 풀에서 선택적으로 부분집합을 사용
GAME_MODES = {
    'selection1': {
        'mode_id': 'selection1',
        'display_name': '선택 1',
        'track_length': 24,
        'board_rows': 5,
        'board_cols': 9,
        'deck_rows': 3,
        'deck_cols': 6,
        'token_count': 3,
        'ruleset_id': 'rules_3token',
        'preview_image': 'selection/selection1.png',
        'colors': ['red', 'green', 'blue'],        # 사용할 색상
        'shapes': ['square', 'triangle', 'circle'],  # 사용할 모양
        'numbers': [1, 2, 3],                          # 사용할 숫자
    },
    'selection2': {
        'mode_id': 'selection2',
        'display_name': '선택 2',
        'track_length': 24,
        'board_rows': 5,
        'board_cols': 9,
        'deck_rows': 3,
        'deck_cols': 6,
        'token_count': 3,
        'ruleset_id': 'rules_3token',
        'preview_image': 'selection/selection2.png',
        'colors': ['red', 'green', 'blue'],        # 사용할 색상
        'shapes': ['square', 'triangle', 'circle'],  # 사용할 모양
        'numbers': [1, 2],                          # 사용할 숫자
    },


    # selection3, 4는 나중에 추가
    # 예: 'colors': ['red', 'blue'], 'shapes': ['rectangle', 'circle'], 'numbers': [1, 2, 3]
}

FRAME_MARKER_POS = (-850, -520)      # 좌하단 구석 (units='pix')
FRAME_MARKER_SIZE = (20, 30)        # (width, height)
FRAME_MARKER_DURATION = 4           # 이벤트 발생 후 마커를 표시할 프레임 수 (약 3~5프레임)



# ==================== AUTO SCREEN SCALE ====================

def _apply_screen_scale():
    """
    실제 화면 해상도에 맞게 카드/레이아웃 크기를 자동 조정.
    기준 설계: WIDTH=1100, HEIGHT=1080.

    스케일 결정 원칙:
      - 수직(s_vert): 버튼 위치 고정 → 버튼 위 공간에 카드가 최대한 들어오도록
      - 수평(s_horiz): 화면 너비 기준 카드+보드+덱이 꽉 차도록
      - 균일 스케일(비율 유지): s = min(s_vert, s_horiz)
      - 레이아웃은 화면 가운데 정렬
    """
    global WIDTH, HEIGHT
    global BOARD_CARD_WIDTH, BOARD_CARD_HEIGHT, BOARD_CARD_SPACING
    global BOARD_TOTAL_WIDTH, BOARD_LEFT_EDGE, BOARD_LEFT_MARGIN, BOARD_TOP_MARGIN, BOARD_Y_OFFSET
    global BOARD_DECK_CENTER_GAP, BOARD_DECK_TOP_MARGIN
    global DECK_CARD_WIDTH, DECK_CARD_HEIGHT, DECK_CARD_SPACING
    global DECK_TOTAL_WIDTH, DECK_LEFT_EDGE, DECK_LEFT_MARGIN, DECK_TOP_MARGIN, DECK_X_OFFSET
    global TOKEN_SIZE, TEXT_SIZE, HIGHLIGHT_WIDTH

    try:
        import tkinter as _tk
        _r = _tk.Tk()
        _r.withdraw()
        actual_w = _r.winfo_screenwidth()
        actual_h = _r.winfo_screenheight()
        _r.destroy()
    except Exception:
        return

    _BOARD_ROWS_GAME = 5  # GAME_MODES 기준 보드 행 수 (selection1/2)
    _DECK_COLS_GAME  = 6  # GAME_MODES 기준 덱 열 수 (selection1/2)

    # 수직 스케일 한계: 버튼 고정 위치 기준 카드 영역 최대 높이
    # CHASE_BUTTON_POS[1]=-430 → 버튼 중심의 screen y = actual_h/2 + 430
    _btn_center_screen_y = actual_h / 2 + abs(CHASE_BUTTON_POS[1])
    _btn_top_y = _btn_center_screen_y - TOKEN_BUTTON_HEIGHT / 2 - 5  # 5px 안전 여유

    _design_card_area_h = (BOARD_DECK_TOP_MARGIN
                           + _BOARD_ROWS_GAME * BOARD_CARD_HEIGHT
                           + (_BOARD_ROWS_GAME - 1) * BOARD_CARD_SPACING)

    # 수평 스케일 한계: 좌우 2px 여백, 보드+간격+덱이 actual_w에 맞도록
    _deck_design_w = _DECK_COLS_GAME * DECK_CARD_WIDTH + (_DECK_COLS_GAME - 1) * DECK_CARD_SPACING
    _design_layout_w = BOARD_TOTAL_WIDTH + BOARD_DECK_CENTER_GAP + _deck_design_w

    s_vert  = _btn_top_y / _design_card_area_h
    s_horiz = (actual_w - 4) / _design_layout_w
    s = max(0.5, min(s_vert, s_horiz))

    # 카드 크기 스케일
    BOARD_CARD_WIDTH   = round(BOARD_CARD_WIDTH  * s)
    BOARD_CARD_HEIGHT  = round(BOARD_CARD_HEIGHT * s)
    BOARD_CARD_SPACING = max(2, round(BOARD_CARD_SPACING * s))
    BOARD_DECK_CENTER_GAP = round(BOARD_DECK_CENTER_GAP * s)
    BOARD_DECK_TOP_MARGIN = round(BOARD_DECK_TOP_MARGIN * s)

    DECK_CARD_WIDTH   = round(DECK_CARD_WIDTH  * s)
    DECK_CARD_HEIGHT  = round(DECK_CARD_HEIGHT * s)
    DECK_CARD_SPACING = max(3, round(DECK_CARD_SPACING * s))

    TOKEN_SIZE      = round(TOKEN_SIZE * s)
    TEXT_SIZE       = max(12, round(TEXT_SIZE * s))
    HIGHLIGHT_WIDTH = max(2, round(HIGHLIGHT_WIDTH * s))

    # WIDTH / HEIGHT를 실제 화면 해상도로 업데이트
    WIDTH  = actual_w
    HEIGHT = actual_h

    # 파생 상수 재계산 (레이아웃 가운데 정렬)
    BOARD_TOTAL_WIDTH = BOARD_COLS * BOARD_CARD_WIDTH + (BOARD_COLS - 1) * BOARD_CARD_SPACING
    _deck_actual_w    = _DECK_COLS_GAME * DECK_CARD_WIDTH + (_DECK_COLS_GAME - 1) * DECK_CARD_SPACING
    _total_layout     = BOARD_TOTAL_WIDTH + BOARD_DECK_CENTER_GAP + _deck_actual_w
    BOARD_LEFT_EDGE   = max(2, (WIDTH - _total_layout) // 2)
    BOARD_LEFT_MARGIN = BOARD_LEFT_EDGE
    BOARD_TOP_MARGIN  = BOARD_DECK_TOP_MARGIN
    BOARD_Y_OFFSET    = 0

    DECK_LEFT_EDGE   = BOARD_LEFT_EDGE + BOARD_TOTAL_WIDTH + BOARD_DECK_CENTER_GAP
    DECK_TOTAL_WIDTH = BOARD_COLS * DECK_CARD_WIDTH + (BOARD_COLS - 1) * DECK_CARD_SPACING
    DECK_LEFT_MARGIN = DECK_LEFT_EDGE
    DECK_TOP_MARGIN  = BOARD_DECK_TOP_MARGIN
    DECK_X_OFFSET    = 0

    print(f"[config] 화면 해상도 {actual_w}×{actual_h} 감지 → 스케일 {s:.3f} 적용")
    print(f"[config] 보드 카드 {BOARD_CARD_WIDTH}×{BOARD_CARD_HEIGHT}, 덱 카드 {DECK_CARD_WIDTH}×{DECK_CARD_HEIGHT}")
    print(f"[config] 레이아웃 너비 {_total_layout}px, BOARD_LEFT_EDGE={BOARD_LEFT_EDGE}px")


if AUTO_DETECT_WINDOW_SIZE:
    _apply_screen_scale()