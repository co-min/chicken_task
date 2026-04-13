# config.py
# Chicken Task - Configuration File
# All game constants and settings

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
TOTAL_CARDS = BOARD_ROWS * BOARD_COLS  # 레거시 기본(모드 선택 전) 카드 수

# Layout - 보드/덱 위치 (1100x1080 기준값, AUTO_DETECT_WINDOW_SIZE=True 시 자동 스케일)
#
# 설계 원칙:
#   1) 덱 총 height = 보드 총 height  →  deck_h = (board_total_h - 2×deck_sp) / 3
#   2) 덱 가로세로 비율 = 0.68 (deck_w = deck_h × 0.68)
#   3) 덱 카드는 작게 + 간격 넓게 → EyeLink AOI 충분한 분리
#   4) 레이아웃은 auto-scale 후 화면 가운데 정렬, 좌우 각 50px 여백 확보
BOARD_DECK_CENTER_GAP = 80    # 보드↔덱 사이 여백 (EyeLink AOI 분리 기준)
BOARD_DECK_TOP_MARGIN = 120   # 상단 HUD 아래 여백 (HUD 텍스트 겹침 방지)

# 보드 카드 크기 (비율 56:79 = 0.709 ≈ 원본 68:95)
BOARD_CARD_WIDTH = 56
BOARD_CARD_HEIGHT = 79
BOARD_CARD_SPACING = 5        # 아이트래커 AOI 분리용 간격

BOARD_TOTAL_WIDTH = BOARD_COLS * BOARD_CARD_WIDTH + (BOARD_COLS - 1) * BOARD_CARD_SPACING
BOARD_LEFT_EDGE = 2           # 운동장 보드 왼쪽 시작 위치 (화면 좌측 기준 px)
BOARD_LEFT_MARGIN = BOARD_LEFT_EDGE  # 레거시 alias
BOARD_TOP_MARGIN = BOARD_DECK_TOP_MARGIN
BOARD_Y_OFFSET = 0

# 덱 카드 크기 (비율 86:127 ≈ 0.68 ✓, 총 height = 보드 총 height, 간격 넓혀 EyeLink AOI 분리)
# 3×127 + 2×17 = 415 = board 총 height (5×79+4×5=415) ✓
DECK_CARD_WIDTH = 86
DECK_CARD_HEIGHT = 127
DECK_CARD_SPACING = 17        # 아이트래커 AOI 분리용 간격

DECK_TOTAL_WIDTH = BOARD_COLS * DECK_CARD_WIDTH + (BOARD_COLS - 1) * DECK_CARD_SPACING
DECK_LEFT_EDGE = BOARD_LEFT_EDGE + BOARD_TOTAL_WIDTH + BOARD_DECK_CENTER_GAP  # = 2+544+80=626 (auto-scale 후 재계산됨)
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
FEEDBACK_DURATION = 0.3       # 초 (피드백 표시 시간)
TRIAL_INTERVAL = 1          # 초 (시행 간 간격)
TOKEN_TIME_WAIT = 1
CATCH_RESET_PREP_DURATION = 1  # 초 (잡기 이벤트 후 토큰 위치 초기화 유예 시간)
GAME_TIME_LIMIT = 1800         # 초 (전체 게임 제한 시간, 30분)

# ==================== ROUND SETTINGS ====================
# 라운드 제한 없음 — 잡기(catch) 이벤트마다 라운드 증가, 30분 게임 시간 내 무제한
TOTAL_ROUNDS = 0
ROUND_BREAK_DURATION = 10      # 초 (라운드 간 휴식 시간)
# 라운드별 턴 제한 시간 (1→5라운드, 1초씩 감소)
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
# 라운드별 보너스 모드 시퀀스 (current_round-1 로 인덱싱, 초과분은 마지막 항목 재사용)
#
# bonus_mode 값:
#   'none'  — 보너스 없음 (초반: 순수 인지 능력 측정)
#   'fixed' — 트랙 인덱스 bonus_slots에 '점수 2배' 고정 배치 (중반)
#   'random'— 트랙 내 bonus_count칸을 무작위로 '점수 2배' 배치 (후반)

BONUS_SEQUENCE = [
    {'bonus_mode': 'none'},                                    # 라운드 1: 보너스 없음
    {'bonus_mode': 'fixed', 'bonus_slots': [6, 12, 18]},       # 라운드 2: 고정 슬롯
    {'bonus_mode': 'fixed', 'bonus_slots': [6, 12, 18]},      # 라운드 3: 고정 슬롯
    {'bonus_mode': 'fixed', 'bonus_slots': [6, 12, 18]},      # 라운드 4: 고정 슬롯
    {'bonus_mode': 'random', 'bonus_count': 3},               # 라운드 5: 랜덤 3칸
    {'bonus_mode': 'random', 'bonus_count': 3},                # 라운드 6+: 랜덤 3칸
]

BONUS_SCORE_MULTIPLIER = 2          # 보너스 칸 점수 배율 (현재 점수 × 2)
BONUS_SLOT_INDICES = [6, 12, 18]    # fixed 모드 기본 슬롯 인덱스 (참조용)
BONUS_BORDER_COLOR = [255, 215, 0]  # 보너스 칸 테두리 색 (금색)
BONUS_BORDER_WIDTH = 1              # 보너스 칸 테두리 두께 (px)
BONUS_LABEL_COLOR = [255, 215, 0]   # 보너스 칸 "×2" 레이블 색

# ==================== SEQUENTIAL MEMORY SETTINGS ====================
SEQ_MEMORY_SCORE_THRESHOLD = 50    # 사용자 라운드 점수 임계값 (이상이면 발동 가능)
SEQ_MEMORY_PC_THRESHOLD    = 200    # PC 라운드 점수 임계값
SEQ_MEMORY_TRIGGER_PROB    = 0.20   # 임계값 초과 시 새 시도마다 발동 확률
SEQ_MEMORY_MIN_STEPS       = 2      # 최소 순차 타겟 수
SEQ_MEMORY_MAX_STEPS       = 3      # 최대 순차 타겟 수
SEQ_MEMORY_BORDER_COLOR    = [0, 255, 200]  # 순차 타겟 테두리 색
SEQ_MEMORY_BORDER_WIDTH    = 5      # 순차 타겟 테두리 두께 (px)

# ==================== SCORE SETTINGS ====================
SCORE_MATCH = 10             # 카드 매칭 성공
SCORE_COMBO_BONUS = 20        # 연속 성공 콤보 추가 보너스
SCORE_SPEED_MAX = 15          # 빠른 판단 최대 점수
SCORE_SPEED_MIN = 1           # 빠른 판단 최소 점수
SCORE_STEAL = 20            # NPC 카드 탈취 보너스
SCORE_PENALTY = -5          # 오답 패널티
SCORE_CATCH_BONUS = 20       # 사용자가 문어를 잡을 때 (사용자 보너스)
SCORE_CAUGHT_PENALTY = -15   # 문어에게 잡힐 때 (사용자 패널티)
SCORE_PC_CATCH_BONUS = 15    # 문어가 flight를 잡을 때 (PC 보너스)

# ==================== PC AI SETTINGS ====================
# 레거시 기본 정답률(모드 선택 전). 실제 게임 실행 시에는 mode 기반 deck 크기로 재계산됨.
PC_SUCCESS_RATE = 1 / TOTAL_CARDS
PC_THINK_TIME = 1.8           # 초 (PC 선택까지 대기 시간)

# ==================== VISUAL SETTINGS ====================
# Highlight colors
HIGHLIGHT_COLOR = [100, 180, 255]  # Sky blue for current target
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
USE_PRACTICE = 0              # 0: 연습 없음, 1: 연습 있음 (phase_func_practice 미구현으로 비활성화)
PRACTICE_TRIALS = 1           # 연습 시행 수

# ==================== EYE TRACKING ====================
USE_EYELINK = 0               # 0: 미사용, 1: 사용
EYELINK_IP  = "100.1.1.1"    # EyeLink host PC IP 주소

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

    # 수평 스케일 한계: 좌우 각 50px 여백 확보, 보드+간격+덱이 actual_w-100에 맞도록
    _SCREEN_SIDE_MARGIN = 35  # 화면 경계에서 레이아웃까지 최소 여백 (px, 양쪽 각각)
    _deck_design_w = _DECK_COLS_GAME * DECK_CARD_WIDTH + (_DECK_COLS_GAME - 1) * DECK_CARD_SPACING
    _design_layout_w = BOARD_TOTAL_WIDTH + BOARD_DECK_CENTER_GAP + _deck_design_w

    s_vert  = _btn_top_y / _design_card_area_h
    s_horiz = (actual_w - _SCREEN_SIDE_MARGIN * 2) / _design_layout_w
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
    TEXT_SIZE       = max(10, round(TEXT_SIZE * s))
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
    print(f"[config] 보드 카드 {BOARD_CARD_WIDTH}×{BOARD_CARD_HEIGHT} sp={BOARD_CARD_SPACING}, 덱 카드 {DECK_CARD_WIDTH}×{DECK_CARD_HEIGHT} sp={DECK_CARD_SPACING}")
    print(f"[config] 레이아웃 너비 {_total_layout}px, BOARD_LEFT_EDGE={BOARD_LEFT_EDGE}px, 보드-덱 gap={BOARD_DECK_CENTER_GAP}px")


if AUTO_DETECT_WINDOW_SIZE:
    _apply_screen_scale()


# ==================== NPC AI TUNING PARAMETERS ====================
# npc_ai.py NPCAI 클래스 초기값 (튜닝)
NPC_REFERENCE_MIN_PROB   = 0.20   # 메모리 참고 최소 비율
NPC_REFERENCE_MAX_PROB   = 0.70   # 메모리 참고 최대 비율
NPC_REFERENCE_BASE_PROB  = 0.40   # 메모리 참고 기본 비율
NPC_HINT_FOLLOW_PROB     = 0.60   # 직전 사용자 힌트 따라가기 확률
NPC_CONTEXT_BLEND_RATIO  = 0.55   # 사용자 추정치 혼합 비율 (0=무시, 1=완전반영)
NPC_TURN_MAX_RATE_SWING  = 0.12   # 턴별 최대 정답률 변동폭 (급격한 출렁임 방지)
NPC_PLAYER_PARITY_BIAS   = 0.17   # 사용자 대비 우위 보정 기본값
NPC_MIN_EDGE_OVER_USER   = 0.02   # 사용자 대비 최소 우위
NPC_MAX_EDGE_OVER_USER   = 0.06   # 사용자 대비 최대 우위

# ==================== ADAPTIVE AI PARAMETERS ====================
# game_state.py GameState 초기값 (튜닝)
NPC_RATE_MAX              = 0.70   # NPC 최대 정답률 상한
ADAPTIVE_ALPHA_UP         = 0.40   # 정답률 상승 시 EWMA 알파 (빠른 추종)
ADAPTIVE_ALPHA_DOWN       = 0.15   # 정답률 하강 시 EWMA 알파 (느린 하강)
MAX_RATE_STEP_UP          = 0.12   # 단일 업데이트 최대 상승 폭
MAX_RATE_STEP_DOWN        = 0.04   # 단일 업데이트 최대 하강 폭
SURGE_BONUS_SCALE         = 0.20   # 사용자 급상승 보너스 스케일
USER_WINDOW_SIZE          = 10     # 최근 시행 분석 윈도우 크기 (시행 수)
MIN_USER_TRIALS_FOR_ADAPT = 3      # 적응 알고리즘 활성화 최소 시행 수
USER_EWMA_ALPHA           = 0.2    # 사용자 정확도 EWMA 알파

# ==================== ALGORITHM WEIGHTS ====================
# 수식 내 혼합 가중치 (합이 1.0인 쌍은 쌍으로 관리)
# 변동성 산출: 정확도 std × W_HIT + 시간 std × W_ELAPSED = 1.0
PERF_VARIABILITY_HIT_W     = 0.65
PERF_VARIABILITY_ELAPSED_W = 0.35

# 추세 산출: 최근 1단계 × W_RECENT + 이전 1단계 × W_PREV = 1.0
TREND_WEIGHT_RECENT  = 0.7
TREND_WEIGHT_PREV    = 0.3

# 조건 지식 점수: 일치 존재 여부 × W_EXIST + 일치 밀도 × W_DENSITY = 1.0
KNOWLEDGE_EXIST_W   = 0.7
KNOWLEDGE_DENSITY_W = 0.3

# 전역 실력 추정: EWMA × 0.7 + 최근정확도 × 0.2 + 속도 × 0.1 = 1.0
SKILL_EWMA_W   = 0.7
SKILL_RECENT_W = 0.2
SKILL_SPEED_W  = 0.1

# 성공확률 추정: 실력 × 0.55 + 지식 × 0.35 + 참신성 × 0.10 = 1.0
ESTIMATED_SKILL_W     = 0.55
ESTIMATED_KNOWLEDGE_W = 0.35
ESTIMATED_NOVELTY_W   = 0.10

# 급상승 보너스 산출: 기본 × 0.6 + 속도 × 0.4 = 1.0
SURGE_BASE_W  = 0.6
SURGE_SPEED_W = 0.4
SURGE_CONSECUTIVE_BONUS = 0.05   # 2연속 성공 추가 보너스

# 실력 점수 (빠른 산출용): 정확도 × 0.8 + 속도 × 0.2 = 1.0
QUICK_SKILL_ACCURACY_W = 0.8
QUICK_SKILL_SPEED_W    = 0.2

# 관찰 메모리 신뢰도
MEMORY_CONFIDENCE_INIT      = 0.60  # 첫 관찰 시 초기 신뢰도
MEMORY_CONFIDENCE_INCREMENT = 0.10  # 재관찰마다 신뢰도 증가량

# 연속 오답 패널티
MISS_PENALTY_PER_STREAK = 0.05  # 연속 오답 1회당 패널티
MISS_PENALTY_MAX_STREAK = 3     # 패널티가 적용되는 최대 연속 오답 수