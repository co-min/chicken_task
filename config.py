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
TOTAL_CARDS = 27  # 3 x 9

# Layout margins - 보드/덱을 화면 중앙 기준으로 좌우 배치
BOARD_DECK_CENTER_GAP = 20
BOARD_DECK_TOP_MARGIN = 250

# 카드 크기
BOARD_CARD_WIDTH = 80
BOARD_CARD_HEIGHT = 110

BOARD_CARD_SPACING = 1.5

BOARD_TOTAL_WIDTH = BOARD_COLS * BOARD_CARD_WIDTH + (BOARD_COLS - 1) * BOARD_CARD_SPACING
BOARD_LEFT_MARGIN = (WIDTH // 2) - BOARD_DECK_CENTER_GAP // 2 - BOARD_TOTAL_WIDTH
BOARD_TOP_MARGIN = BOARD_DECK_TOP_MARGIN

# Deck position (right side) - 1080x1080 화면 최적화
DECK_CARD_WIDTH = 80
DECK_CARD_HEIGHT = 110
DECK_CARD_SPACING = 1.5

DECK_TOTAL_WIDTH = BOARD_COLS * DECK_CARD_WIDTH + (BOARD_COLS - 1) * DECK_CARD_SPACING
DECK_LEFT_MARGIN = (WIDTH // 2) + BOARD_DECK_CENTER_GAP // 2
DECK_TOP_MARGIN = BOARD_DECK_TOP_MARGIN

# ==================== TOKEN SETTINGS ====================
# Initial positions (0-indexed: row, col)
CHASE_START_POS = (0, 0)      # 1행 1열 (문어를 쫓는 닭)
OCTOPUS_START_POS = (1, 0)    # 2행 1열 (PC)
FLIGHT_START_POS = (2, 0)     # 3행 1열 (문어로부터 도망치는 닭)

TOKEN_SIZE = 56  # pixels (1080x1080 화면에 맞춤)


# ==================== CARD ATTRIBUTES ====================
# 9가지 조건 (각 3번 반복 = 27장)
COLORS = ['red', 'blue', 'green']
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
PC_SUCCESS_RATE = 0.6         # 60% 정답 확률
PC_THINK_TIME = 1           # 초 (PC 선택까지 대기 시간)

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
CHASE_BUTTON_POS = (-170, -160)      # (x, y)
FLIGHT_BUTTON_POS = (170, -160)      # (x, y)
TOKEN_BUTTON_LINE_WIDTH = 4

# ==================== KEY MAPPINGS ====================
KEY_CHASE = 'left'            # chase 선택 (왼쪽 버튼)
KEY_FLIGHT = 'right'          # flight 선택 (오른쪽 버튼)
KEY_CONFIRM = 'return'        # 선택 확정
KEY_EXIT = 'escape'           # 게임 종료


# ==================== EXPERIMENT SETTINGS ====================
USE_PRACTICE = 1              # 0: 연습 없음, 1: 연습 있음
PRACTICE_TRIALS = 1           # 연습 시행 수

# ==================== EYE TRACKING ====================
USE_EYELINK = 0               # 0: 미사용, 1: 사용

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