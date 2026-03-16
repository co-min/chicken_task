# config.py
# Chicken Task - Configuration File
# All game constants and settings

# ==================== SCREEN SETTINGS ====================
WIDTH = 1100 # 화면 너비
HEIGHT = 1080 # 화면 높이
BG_COLOR = [128, 128, 128]  # RGB 0-255 (gray)
FULLSCREEN = True

# ==================== BOARD SETTINGS ====================
BOARD_ROWS = 3
BOARD_COLS = 9
TOTAL_CARDS = 27  # 3 x 9

# Board position (left side) - 1080x1080 화면 최적화
BOARD_LEFT_MARGIN = 10
BOARD_TOP_MARGIN = 250
BOARD_CARD_WIDTH = 50
BOARD_CARD_HEIGHT = 70
BOARD_CARD_SPACING = 5

# Deck position (right side) - 1080x1080 화면 최적화
DECK_LEFT_MARGIN = 580
DECK_TOP_MARGIN = 250
DECK_CARD_WIDTH = 50
DECK_CARD_HEIGHT = 70
DECK_CARD_SPACING = 5

# ==================== TOKEN SETTINGS ====================
# Initial positions (0-indexed: row, col)
CHASE_START_POS = (0, 0)      # 1행 1열 (문어를 쫓는 닭)
OCTOPUS_START_POS = (1, 0)    # 2행 1열 (PC)
FLIGHT_START_POS = (2, 0)     # 3행 1열 (문어로부터 도망치는 닭)

TOKEN_SIZE = 50  # pixels (1080x1080 화면에 맞춤)


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
CARD_FLIP_DURATION = 5        # 초 (카드 앞면 노출 시간)
FEEDBACK_DURATION = 0.5       # 초 (피드백 표시 시간)
TRIAL_INTERVAL = 0.5          # 초 (시행 간 간격)


# ==================== PC AI SETTINGS ====================
PC_SUCCESS_RATE = 0.6         # 60% 정답 확률
PC_THINK_TIME = 1           # 초 (PC 선택까지 대기 시간)

# ==================== VISUAL SETTINGS ====================
# Highlight colors
HIGHLIGHT_COLOR = [0, 255, 200]  # Mint color for target
HIGHLIGHT_WIDTH = 4              # Border width

# Text settings
TEXT_COLOR = [255, 255, 255]     # White
TEXT_SIZE = 28                   # 1080x1080 화면에 맞춤

# Button colors
BUTTON_COLOR_NORMAL = [100, 100, 100]
BUTTON_COLOR_HOVER = [150, 150, 150]
BUTTON_COLOR_SELECTED = [0, 200, 200]  # Mint

# Token choice button settings (Chase / Flight)
TOKEN_BUTTON_WIDTH = 250
TOKEN_BUTTON_HEIGHT = 100
TOKEN_BUTTON_TEXT_HEIGHT = 30
CHASE_BUTTON_POS = (0, -90)      # (x, y)
FLIGHT_BUTTON_POS = (0, -200)    # (x, y)
TOKEN_BUTTON_LINE_WIDTH = 4

# ==================== KEY MAPPINGS ====================
KEY_CHASE = 'up'              # chase 선택 (위쪽 닭)
KEY_FLIGHT = 'down'           # flight 선택 (아래쪽 닭)
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
