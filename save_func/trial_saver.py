# save_func/trial_saver.py
# 트라이얼(카드 선택 시도)별 행동 데이터를 trials.csv에 기록한다.
#
# 호출 흐름
# ---------
#   세션 시작  → init_trial_file(save_dir, subject_id)  → file_path 저장
#   매 시행 후 → save_trial(file_path, trial_entry, game_state, subject_id)
#
# trials.csv 는 append 모드로 열리므로 실험 중 크래시가 나도
# 그 시점까지 기록된 데이터는 보존된다.

import csv
import os

# CSV 컬럼 순서 (분석 편의 기준으로 정렬)
_HEADERS = [
    # ── 식별자 ──────────────────────────────────────────────
    'trial_id',            # EDF·LabJack·CSV 병합 공통 키
    'subject_id',
    'game_mode',
    'round_num',
    'turn_num',
    'actor',               # 'chase' | 'flight' | 'octopus'
    # ── 조건 ────────────────────────────────────────────────
    'condition_type',      # 'color' | 'shape' | 'number'
    'condition_value',     # 'red' | 'square' | 1 | ...
    'target_pos_row',      # 운동장 보드 타겟 위치
    'target_pos_col',
    # ── 선택 카드 ────────────────────────────────────────────
    'selected_card_color',
    'selected_card_shape',
    'selected_card_number',
    'selected_card_row',   # 메인 덱 위치
    'selected_card_col',
    # ── 결과 ────────────────────────────────────────────────
    'is_match',            # 1 = 정답, 0 = 오답
    'elapsed_time',        # 반응 시간(초)
    'cumulative_user_score',
    'cumulative_pc_score',
    # ── Sequential Memory ────────────────────────────────────
    'is_seq_memory',       # 1 = seq_memory 모드 trial, 0 = 일반 trial
    'seq_memory_step',     # 현재 스텝 인덱스 (0-based), 일반 trial은 빈칸
    'seq_memory_total',    # 전체 순차 타겟 수, 일반 trial은 빈칸
    # ── 덱 가시 상태 ─────────────────────────────────────────
    'deck_face_up',        # 클릭 직전 face_up 스냅샷 (row-major, 0/1 쉼표 구분)
                           # 예) 3×4 덱: "0,0,1,0,1,0,0,0,0,0,0,0"
    # ── 타임스탬프 ───────────────────────────────────────────
    'trial_start_time',    # EDF TRIAL_START 직후 core.getTime() — EDF-CSV 정렬 동기점
    'timestamp',           # UNIX epoch (time.time()) — 카드 클릭 시각
]


def init_trial_file(save_dir: str, subject_id: str) -> str:
    """
    trials.csv 파일을 생성하고 헤더를 작성한다.

    Parameters
    ----------
    save_dir : str
        저장 디렉토리 경로 (존재해야 함).
    subject_id : str
        피험자 ID (파일명에는 포함되지 않지만 각 행에 기록됨).

    Returns
    -------
    str
        생성된 CSV 파일의 절대 경로.
    """
    path = os.path.join(save_dir, 'trials.csv')
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=_HEADERS)
        writer.writeheader()
    print(f"[TrialSaver] 초기화 완료: {path}")
    return path


def save_trial(file_path: str, trial_entry: dict, game_state, subject_id: str):
    """
    trial_history 항목 1개를 trials.csv에 append한다.

    Parameters
    ----------
    file_path : str
        init_trial_file() 이 반환한 CSV 경로.
    trial_entry : dict
        game_state.trial_history 의 마지막 항목.
        필수 키: trial_id, round, turn, token, condition, target_pos,
                 selected_card_pos, selected_card, is_match,
                 elapsed_time, timestamp
    game_state : GameState
        현재 게임 상태 (누적 점수 참조용).
    subject_id : str
        피험자 ID.
    """
    card      = trial_entry.get('selected_card') or {}
    card_pos  = trial_entry.get('selected_card_pos') or (None, None)
    target    = trial_entry.get('target_pos') or (None, None)
    condition = trial_entry.get('condition') or {}

    seq_step  = trial_entry.get('seq_memory_step', None)
    seq_total = trial_entry.get('seq_memory_total', None)

    row = {
        'trial_id':              trial_entry.get('trial_id', ''),
        'subject_id':            subject_id,
        'game_mode':             game_state.selected_mode_id,
        'round_num':             trial_entry.get('round', ''),
        'turn_num':              trial_entry.get('turn', ''),
        'actor':                 trial_entry.get('token', ''),
        'condition_type':        condition.get('type', ''),
        'condition_value':       condition.get('value', ''),
        'target_pos_row':        target[0] if target[0] is not None else '',
        'target_pos_col':        target[1] if target[1] is not None else '',
        'selected_card_color':   card.get('color', ''),
        'selected_card_shape':   card.get('shape', ''),
        'selected_card_number':  card.get('number', ''),
        'selected_card_row':     card_pos[0] if card_pos[0] is not None else '',
        'selected_card_col':     card_pos[1] if card_pos[1] is not None else '',
        'is_match':              int(bool(trial_entry.get('is_match', False))),
        'elapsed_time':          round(trial_entry.get('elapsed_time', 0.0), 4),
        'cumulative_user_score': game_state.user_score,
        'cumulative_pc_score':   game_state.pc_score,
        'is_seq_memory':         1 if seq_step is not None else 0,
        'seq_memory_step':       seq_step if seq_step is not None else '',
        'seq_memory_total':      seq_total if seq_total is not None else '',
        'deck_face_up':          trial_entry.get('deck_face_up', ''),
        'trial_start_time':      round(trial_entry.get('trial_start_time', 0.0), 6),
        'timestamp':             round(trial_entry.get('timestamp', 0.0), 6),
    }

    with open(file_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=_HEADERS)
        writer.writerow(row)
