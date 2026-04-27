# ==================== SCREEN SETTINGS ====================
WIDTH = 1920 # 화면 너비
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
TOTAL_CARDS = BOARD_ROWS * BOARD_COLS

BOARD_DECK_CENTER_GAP = 80    # 보드↔덱 사이 여백
BOARD_DECK_TOP_MARGIN = 120   # 상단 HUD 아래 여백

BOARD_CARD_WIDTH = 56
BOARD_CARD_HEIGHT = 79
BOARD_CARD_SPACING = 5

BOARD_TOTAL_WIDTH = BOARD_COLS * BOARD_CARD_WIDTH + (BOARD_COLS - 1) * BOARD_CARD_SPACING
BOARD_LEFT_EDGE = 2
BOARD_TOP_MARGIN = BOARD_DECK_TOP_MARGIN

DECK_CARD_WIDTH = 86
DECK_CARD_HEIGHT = 127
DECK_CARD_SPACING = 17

DECK_LEFT_EDGE = BOARD_LEFT_EDGE + BOARD_TOTAL_WIDTH + BOARD_DECK_CENTER_GAP
DECK_TOP_MARGIN = BOARD_DECK_TOP_MARGIN

# ==================== TOKEN SETTINGS ====================
TOKEN_SIZE = 43


# ==================== CARD ATTRIBUTES ====================
COLORS = ['red', 'green', 'blue']
SHAPES = ['square', 'triangle', 'circle']
NUMBERS = [1, 2, 3]

# ==================== TIMING SETTINGS ====================
TURN_TIME_LIMIT = 15
CARD_FLIP_DURATION = 0.5
FEEDBACK_DURATION = 0.3
TRIAL_INTERVAL = 0.5
CATCH_RESET_PREP_DURATION = 0.5
GAME_TIME_LIMIT = 1800

# ==================== ROUND SETTINGS ====================
TOTAL_ROUNDS = 0
ROUND_BREAK_DURATION = 10
ROUND_TURN_LIMITS = [15, 12, 10]

# ==================== PROGRESS BAR ====================
PROGRESS_BAR_WIDTH  = 700     # px (기준 해상도 기준)
PROGRESS_BAR_HEIGHT = 16      # px
PROGRESS_BAR_Y_FROM_TOP = 55  # 화면 상단에서 바 중심까지 거리 (px)
PROGRESS_BAR_COLOR_FULL = [0, 210, 90]    # 초록 (>50%)
PROGRESS_BAR_COLOR_WARN = [255, 165, 0]   # 주황 (25~50%)
PROGRESS_BAR_COLOR_CRIT = [230, 40,  40]  # 빨강 (<25%)
PROGRESS_BAR_BG_COLOR   = [55,  55,  55]  # 배경

# ==================== DIFFICULTY SETTINGS ====================
# 이번 라운드 점수 >= 임계값이면 다음 라운드에서 난이도 1단계 업
DIFFICULTY_SCORE_THRESHOLD = 500

# Sequential Memory
# threshold 150 점 이상이면 seqential memory 요소가 추가됨
# 특정 점수 이상이면 타겟이 {target, target+1} or {target, target+1, target+2}
# 연속된 조건에 순서대로 메인덱 카드 뒤집기
# 하나라도 실패 시, 제자리. 성공하면 그만큼 이동함. 


# 6단계 선형 난이도 시퀀스 (deck_rows=3 고정, deck_cols·layout_mode만 변경)
DIFFICULTY_SEQUENCE = [
    {'deck_cols': 4, 'layout_mode': 'factorization'},  # 0단계: 12장 factorization
    {'deck_cols': 4, 'layout_mode': 'random'},          # 1단계: 12장 random
    {'deck_cols': 5, 'layout_mode': 'factorization'},  # 2단계: 15장 factorization
    {'deck_cols': 5, 'layout_mode': 'random'},          # 3단계: 15장 random
    {'deck_cols': 6, 'layout_mode': 'factorization'},  # 4단계: 18장 factorization
    {'deck_cols': 6, 'layout_mode': 'random'},          # 5단계: 18장 random
]

# ==================== BONUS SETTINGS ====================
BONUS_SEQUENCE = [
    {'bonus_mode': 'none'},
    {'bonus_mode': 'fixed', 'bonus_slots': [6, 12, 18]},
    {'bonus_mode': 'fixed', 'bonus_slots': [6, 12, 18]},
    {'bonus_mode': 'fixed', 'bonus_slots': [6, 12, 18]},
    {'bonus_mode': 'random', 'bonus_count': 3},
    {'bonus_mode': 'random', 'bonus_count': 3},
]

BONUS_SCORE_MULTIPLIER = 2
BONUS_BORDER_COLOR = [255, 215, 0]
BONUS_BORDER_WIDTH = 3
BONUS_LABEL_COLOR = [255, 215, 0]

# ==================== SEQUENTIAL MEMORY SETTINGS ====================
SEQ_MEMORY_SCORE_THRESHOLD = 100
SEQ_MEMORY_PC_THRESHOLD    = 100
SEQ_MEMORY_TRIGGER_PROB    = 0.20
SEQ_MEMORY_MIN_STEPS       = 2
SEQ_MEMORY_MAX_STEPS       = 3
SEQ_MEMORY_BORDER_COLOR    = [0, 255, 200]
SEQ_MEMORY_BORDER_WIDTH    = 5

# ==================== SCORE SETTINGS ====================
SCORE_MATCH = 10
SCORE_COMBO_BONUS = 20
SCORE_SPEED_MAX = 15
SCORE_SPEED_MIN = 1
SCORE_STEAL = 20
SCORE_PENALTY = -5
SCORE_CATCH_BONUS = 20
SCORE_CAUGHT_PENALTY = -15
SCORE_PC_CATCH_BONUS = 15

# ==================== PC AI SETTINGS ====================
PC_SUCCESS_RATE = 1 / TOTAL_CARDS
PC_THINK_TIME = 1.8

# ==================== VISUAL SETTINGS ====================
HIGHLIGHT_COLOR = [100, 180, 255]
HIGHLIGHT_WIDTH = 4

TEXT_COLOR = [0, 0, 0]
TEXT_SIZE = 28

BUTTON_COLOR_NORMAL = [100, 100, 100]
BUTTON_COLOR_HOVER = [150, 150, 150]
BUTTON_COLOR_SELECTED = [0, 200, 200]

TOKEN_BUTTON_WIDTH = 300
TOKEN_BUTTON_HEIGHT = 95
TOKEN_BUTTON_TEXT_HEIGHT = 30
CHASE_BUTTON_POS = (-170, -430)
FLIGHT_BUTTON_POS = (170, -430)
TOKEN_BUTTON_LINE_WIDTH = 4
MESSAGE_Y_OFFSET = -70

# ==================== KEY MAPPINGS ====================
KEY_CHASE = 'left'
KEY_FLIGHT = 'right'
KEY_EXIT = 'escape'


# ==================== EXPERIMENT SETTINGS ====================
USE_PRACTICE = 0
PRACTICE_TRIALS = 3
PRACTICE_SEQ_TRIALS = 2
PRACTICE_SEQ_STEPS = 2

# ==================== EYE TRACKING ====================
USE_EYELINK = 0
EYELINK_IP  = "100.1.1.1"

# ==================== LABJACK T4 ====================
USE_LABJACK = 1

# ==================== AOI (Area of Interest) ====================
AOI_DWELL_THRESHOLD = 0.1
AOI_TRIGGER_PULSE_S = 0.005
AOI_TRIGGER_BOARD_OFFSET = 10
AOI_TRIGGER_DECK_OFFSET  = 40


# game_play.py의 run_feedback_phase 색상
PURPLE = [180, 0, 255]
DARK_GREY = [105, 105, 105]
WHITE = [255, 255, 255]
GOLD = [255, 200, 0]          # 잡기 성공 피드백
ORANGE_RED = [255, 70, 0]     # 잡힘 패널티 피드백


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

FRAME_MARKER_POS = None              # None → 실행 시 win.size 기준으로 자동 계산 (좌하단)
FRAME_MARKER_SIZE = (20, 30)        # (width, height)
FRAME_MARKER_DURATION = 4           # 이벤트 발생 후 마커를 표시할 프레임 수 (약 3~5프레임)



# ==================== AUTO SCREEN SCALE ====================

def _apply_screen_scale():
    """실제 화면 해상도에 맞게 카드/레이아웃 크기를 자동 조정."""
    global WIDTH, HEIGHT
    global BOARD_CARD_WIDTH, BOARD_CARD_HEIGHT, BOARD_CARD_SPACING
    global BOARD_TOTAL_WIDTH, BOARD_LEFT_EDGE, BOARD_TOP_MARGIN
    global BOARD_DECK_CENTER_GAP, BOARD_DECK_TOP_MARGIN
    global DECK_CARD_WIDTH, DECK_CARD_HEIGHT, DECK_CARD_SPACING
    global DECK_LEFT_EDGE, DECK_TOP_MARGIN
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

    _BOARD_ROWS_GAME  = 5
    _DECK_COLS_GAME   = 6
    _SCREEN_SIDE_MARGIN = 35

    _btn_center_screen_y = actual_h / 2 + abs(CHASE_BUTTON_POS[1])
    _btn_top_y = _btn_center_screen_y - TOKEN_BUTTON_HEIGHT / 2 - 5

    _design_card_area_h = (BOARD_DECK_TOP_MARGIN
                           + _BOARD_ROWS_GAME * BOARD_CARD_HEIGHT
                           + (_BOARD_ROWS_GAME - 1) * BOARD_CARD_SPACING)

    _deck_design_w   = _DECK_COLS_GAME * DECK_CARD_WIDTH + (_DECK_COLS_GAME - 1) * DECK_CARD_SPACING
    _design_layout_w = BOARD_TOTAL_WIDTH + BOARD_DECK_CENTER_GAP + _deck_design_w

    s_vert  = _btn_top_y / _design_card_area_h
    s_horiz = (actual_w - _SCREEN_SIDE_MARGIN * 2) / _design_layout_w
    s = max(0.5, min(s_vert, s_horiz))

    BOARD_CARD_WIDTH      = round(BOARD_CARD_WIDTH  * s)
    BOARD_CARD_HEIGHT     = round(BOARD_CARD_HEIGHT * s)
    BOARD_CARD_SPACING    = max(2, round(BOARD_CARD_SPACING * s))
    BOARD_DECK_CENTER_GAP = round(BOARD_DECK_CENTER_GAP * s)
    BOARD_DECK_TOP_MARGIN = round(BOARD_DECK_TOP_MARGIN * s)

    DECK_CARD_WIDTH   = round(DECK_CARD_WIDTH  * s)
    DECK_CARD_HEIGHT  = round(DECK_CARD_HEIGHT * s)
    DECK_CARD_SPACING = max(3, round(DECK_CARD_SPACING * s))

    TOKEN_SIZE      = round(TOKEN_SIZE * s)
    TEXT_SIZE       = max(10, round(TEXT_SIZE * s))
    HIGHLIGHT_WIDTH = max(2, round(HIGHLIGHT_WIDTH * s))

    WIDTH  = actual_w
    HEIGHT = actual_h

    BOARD_TOTAL_WIDTH = BOARD_COLS * BOARD_CARD_WIDTH + (BOARD_COLS - 1) * BOARD_CARD_SPACING
    _deck_actual_w    = _DECK_COLS_GAME * DECK_CARD_WIDTH + (_DECK_COLS_GAME - 1) * DECK_CARD_SPACING
    _total_layout     = BOARD_TOTAL_WIDTH + BOARD_DECK_CENTER_GAP + _deck_actual_w
    BOARD_LEFT_EDGE   = max(2, (WIDTH - _total_layout) // 2)
    BOARD_TOP_MARGIN  = BOARD_DECK_TOP_MARGIN

    DECK_LEFT_EDGE  = BOARD_LEFT_EDGE + BOARD_TOTAL_WIDTH + BOARD_DECK_CENTER_GAP
    DECK_TOP_MARGIN = BOARD_DECK_TOP_MARGIN

    print(f"[config] {actual_w}×{actual_h} → scale {s:.3f}, "
          f"board {BOARD_CARD_WIDTH}×{BOARD_CARD_HEIGHT}, deck {DECK_CARD_WIDTH}×{DECK_CARD_HEIGHT}")


if AUTO_DETECT_WINDOW_SIZE:
    _apply_screen_scale()


# ==================== NPC AI PARAMETERS ====================
# 카드 선택 로직 (npc_ai.py)
NPC_REFERENCE_MIN_PROB   = 0.20   # 메모리 후보 참고 최솟값
NPC_REFERENCE_MAX_PROB   = 0.70   # 메모리 후보 참고 최댓값
NPC_REFERENCE_BASE_PROB  = 0.40   # 메모리 후보 참고 기본값
NPC_HINT_FOLLOW_PROB     = 0.60   # 사용자 힌트 추종 확률

# 적응형 난이도 조정 (game_state.py)
NPC_RATE_MAX              = 0.70   # NPC 정답률 상한
NPC_EDGE_OVER_USER        = 0.04   # 사용자 성공확률 대비 NPC 우위 마진
ADAPTIVE_ALPHA_UP         = 0.40   # 난이도 상승 EMA 속도
ADAPTIVE_ALPHA_DOWN       = 0.15   # 난이도 하강 EMA 속도
MAX_RATE_STEP_UP          = 0.12   # 턴당 최대 상승폭
MAX_RATE_STEP_DOWN        = 0.04   # 턴당 최대 하강폭
SURGE_BONUS_SCALE         = 0.20
USER_WINDOW_SIZE          = 10
MIN_USER_TRIALS_FOR_ADAPT = 3
USER_EWMA_ALPHA           = 0.2

# ==================== ALGORITHM WEIGHTS ====================
PERF_VARIABILITY_HIT_W     = 0.65
PERF_VARIABILITY_ELAPSED_W = 0.35

TREND_WEIGHT_RECENT  = 0.7
TREND_WEIGHT_PREV    = 0.3

KNOWLEDGE_EXIST_W   = 0.7
KNOWLEDGE_DENSITY_W = 0.3

SKILL_EWMA_W   = 0.7
SKILL_RECENT_W = 0.2
SKILL_SPEED_W  = 0.1

ESTIMATED_SKILL_W     = 0.55
ESTIMATED_KNOWLEDGE_W = 0.35
ESTIMATED_NOVELTY_W   = 0.10

SURGE_BASE_W  = 0.6
SURGE_SPEED_W = 0.4
SURGE_CONSECUTIVE_BONUS = 0.05

QUICK_SKILL_ACCURACY_W = 0.8
QUICK_SKILL_SPEED_W    = 0.2

MEMORY_CONFIDENCE_INIT      = 0.60
MEMORY_CONFIDENCE_INCREMENT = 0.10

MISS_PENALTY_PER_STREAK = 0.05
MISS_PENALTY_MAX_STREAK = 3