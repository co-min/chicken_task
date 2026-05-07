import atexit
import csv
import json
import os

# ── trials.csv 컬럼 ──────────────────────────────────────────────────────────
_HEADERS = [
    # 식별자
    'trial_id',             # EDF·LabJack·CSV 병합 공통 키
    'subject_id',
    'game_mode',
    'round_num',
    'turn_num',
    'actor',                # 'chase' | 'flight' | 'octopus'
    # 조건
    'condition_type',       # 'color' | 'shape' | 'number' | 'conjunctive'
    'condition_value',
    'target_pos_row',       # 운동장 보드 타겟 위치
    'target_pos_col',
    # 선택 카드
    'selected_card_color',
    'selected_card_shape',
    'selected_card_number',
    'selected_card_row',    # 메인 덱 위치
    'selected_card_col',
    # 결과
    'result_type',          # 'success'|'failure'|'seq_step_success'|'seq_all_success'|'seq_failure'
    'is_match',             # 1 = 정답, 0 = 오답
    'elapsed_time',         # 반응 시간(초)
    'cumulative_user_score',
    'cumulative_pc_score',
    'user_combo',           # 시행 시점 사용자 연속 성공 횟수
    'npc_success_rate',     # 시행 시점 NPC 적응형 성공률
    # 토큰 위치 (시행 직전)
    'user_token_row',       # 유저가 선택한 토큰 행 (PC 턴은 빈칸)
    'user_token_col',
    'pc_token_row',         # 문어(octopus) 행
    'pc_token_col',
    # Sequential Memory
    'is_seq_memory',        # 1 = seq_memory 모드 trial, 0 = 일반 trial
    'seq_memory_step',      # 현재 스텝 인덱스 (0-based), 일반 trial은 빈칸
    'seq_memory_total',     # 전체 순차 타겟 수, 일반 trial은 빈칸
    'seq_memory_targets',   # 전체 타겟 시퀀스: "(r0,c0),(r1,c1),..." 일반은 빈칸
    # 타임스탬프
    'trial_start_time',     # EDF TRIAL_START 직후 core.getTime() — EDF-CSV 정렬 동기점
    'timestamp',            # UNIX epoch (time.time()) — 카드 클릭 시각
]

# ── round_events.csv 컬럼 ────────────────────────────────────────────────────
_ROUND_EVENT_HEADERS = [
    'event_type',       # 'game_start' | 'user_catch' | 'npc_catch' | 'round_advance'
    'round_num',
    'timestamp',        # UNIX epoch
    'user_score',
    'pc_score',
    'chase_row',        # 이벤트 직전 chase 위치
    'chase_col',
    'flight_row',
    'flight_col',
    'octopus_row',
    'octopus_col',
    'difficulty_index',
    'note',
]

# ── 버퍼 (trials.csv 전용; 라운드 이벤트는 즉시 기록) ───────────────────────
_buffers: dict = {}
FLUSH_EVERY = 10


def _flush_buffer(file_path: str):
    rows = _buffers.pop(file_path, [])
    if not rows:
        return
    with open(file_path, 'a', newline='', encoding='utf-8') as f:
        csv.DictWriter(f, fieldnames=_HEADERS).writerows(rows)


def _atexit_flush():
    for fp in list(_buffers.keys()):
        _flush_buffer(fp)


atexit.register(_atexit_flush)


# ── 초기화 ───────────────────────────────────────────────────────────────────

def init_trial_file(save_dir: str, subject_id: str) -> str:
    path = os.path.join(save_dir, 'trials.csv')
    with open(path, 'w', newline='', encoding='utf-8') as f:
        csv.DictWriter(f, fieldnames=_HEADERS).writeheader()
    _buffers[path] = []
    print(f"[TrialSaver] trials 초기화: {path}")
    return path


def init_round_events_file(save_dir: str) -> str:
    path = os.path.join(save_dir, 'round_events.csv')
    with open(path, 'w', newline='', encoding='utf-8') as f:
        csv.DictWriter(f, fieldnames=_ROUND_EVENT_HEADERS).writeheader()
    print(f"[TrialSaver] round_events 초기화: {path}")
    return path


# ── 저장 ─────────────────────────────────────────────────────────────────────

def save_trial(file_path: str, trial_entry: dict, game_state, subject_id: str):
    card     = trial_entry.get('selected_card') or {}
    card_pos = trial_entry.get('selected_card_pos') or (None, None)
    target   = trial_entry.get('target_pos') or (None, None)
    cond     = trial_entry.get('condition') or {}

    seq_step    = trial_entry.get('seq_memory_step', None)
    seq_total   = trial_entry.get('seq_memory_total', None)
    raw_targets = trial_entry.get('seq_memory_targets') or []
    targets_str = ','.join(f'({r},{c})' for r, c in raw_targets) if raw_targets else ''

    user_pos = trial_entry.get('user_token_pos') or (None, None)
    pc_pos   = trial_entry.get('pc_token_pos')   or (None, None)

    row = {
        'trial_id':              trial_entry.get('trial_id', ''),
        'subject_id':            subject_id,
        'game_mode':             game_state.selected_mode_id,
        'round_num':             trial_entry.get('round', ''),
        'turn_num':              trial_entry.get('turn', ''),
        'actor':                 trial_entry.get('token', ''),
        'condition_type':        cond.get('type', ''),
        'condition_value':       cond.get('value', ''),
        'target_pos_row':        target[0] if target[0] is not None else '',
        'target_pos_col':        target[1] if target[1] is not None else '',
        'selected_card_color':   card.get('color', ''),
        'selected_card_shape':   card.get('shape', ''),
        'selected_card_number':  card.get('number', ''),
        'selected_card_row':     card_pos[0] if card_pos[0] is not None else '',
        'selected_card_col':     card_pos[1] if card_pos[1] is not None else '',
        'result_type':           trial_entry.get('result_type', ''),
        'is_match':              int(bool(trial_entry.get('is_match', False))),
        'elapsed_time':          round(trial_entry.get('elapsed_time', 0.0), 4),
        'cumulative_user_score': game_state.user_score,
        'cumulative_pc_score':   game_state.pc_score,
        'user_combo':            trial_entry.get('user_combo', ''),
        'npc_success_rate':      round(float(trial_entry.get('npc_success_rate', 0.0)), 4),
        'user_token_row':        user_pos[0] if user_pos[0] is not None else '',
        'user_token_col':        user_pos[1] if user_pos[1] is not None else '',
        'pc_token_row':          pc_pos[0] if pc_pos[0] is not None else '',
        'pc_token_col':          pc_pos[1] if pc_pos[1] is not None else '',
        'is_seq_memory':         1 if seq_step is not None else 0,
        'seq_memory_step':       seq_step if seq_step is not None else '',
        'seq_memory_total':      seq_total if seq_total is not None else '',
        'seq_memory_targets':    targets_str,
        'trial_start_time':      round(trial_entry.get('trial_start_time', 0.0), 6),
        'timestamp':             round(trial_entry.get('timestamp', 0.0), 6),
    }

    buf = _buffers.setdefault(file_path, [])
    buf.append(row)
    if len(buf) >= FLUSH_EVERY:
        _flush_buffer(file_path)


def flush_trials(file_path: str):
    """버퍼에 남은 모든 행을 즉시 CSV에 기록한다. 세션 종료 시 명시적으로 호출한다."""
    _flush_buffer(file_path)


def save_round_event(file_path: str, event_entry: dict):
    """
    round_event_history 항목 1개를 round_events.csv에 즉시 기록한다.

    Parameters
    ----------
    file_path : str      init_round_events_file() 이 반환한 CSV 경로.
    event_entry : dict   game_state.round_event_history 의 항목.
    """
    positions = event_entry.get('token_positions') or {}
    chase   = positions.get('chase')   or (None, None)
    flight  = positions.get('flight')  or (None, None)
    octopus = positions.get('octopus') or (None, None)

    row = {
        'event_type':       event_entry.get('event_type', ''),
        'round_num':        event_entry.get('round_num', ''),
        'timestamp':        round(event_entry.get('timestamp', 0.0), 6),
        'user_score':       event_entry.get('user_score', ''),
        'pc_score':         event_entry.get('pc_score', ''),
        'chase_row':        chase[0] if chase[0] is not None else '',
        'chase_col':        chase[1] if chase[1] is not None else '',
        'flight_row':       flight[0] if flight[0] is not None else '',
        'flight_col':       flight[1] if flight[1] is not None else '',
        'octopus_row':      octopus[0] if octopus[0] is not None else '',
        'octopus_col':      octopus[1] if octopus[1] is not None else '',
        'difficulty_index': event_entry.get('difficulty_index', ''),
        'note':             event_entry.get('note', ''),
    }
    with open(file_path, 'a', newline='', encoding='utf-8') as f:
        csv.DictWriter(f, fieldnames=_ROUND_EVENT_HEADERS).writerow(row)


def save_deck_layout(save_dir: str, round_num: int, difficulty_index: int, deck):
    """
    현재 덱 레이아웃을 deck_layouts.json에 누적 저장한다.
    세션 시작 및 난이도 변경(덱 재생성) 시 호출한다.

    Parameters
    ----------
    save_dir : str          저장 디렉토리 경로.
    round_num : int         현재 라운드 번호 (JSON 키에 포함).
    difficulty_index : int  현재 난이도 인덱스 (JSON 키에 포함).
    deck                    MainDeck 인스턴스 (deck.deck: 2D 카드 dict 리스트).
    """
    path = os.path.join(save_dir, 'deck_layouts.json')
    existing = {}
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                existing = json.load(f)
        except (json.JSONDecodeError, OSError):
            pass

    key = f'round_{round_num}_diff_{difficulty_index}'
    existing[key] = [
        [card if isinstance(card, dict) else vars(card) for card in row]
        for row in deck.deck
    ]

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)
    print(f"[TrialSaver] deck_layouts 저장: {key}")
