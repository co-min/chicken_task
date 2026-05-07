import csv
import os

_HEADERS = [
    # ── 식별자 ──────────────────────────────────────────────
    'trial_id',            # trials.csv 와의 병합 키
    'subject_id',
    # ── 이벤트 ──────────────────────────────────────────────
    'event_type',          # 'enter' | 'exit'
    'aoi_id',              # 예: 'board_2_3', 'deck_1_4'
    'aoi_type',            # 'board' | 'deck'
    'aoi_row',
    'aoi_col',
    'labjack_trigger_code',  # 진입 시 전송한 TTL 코드 (이탈은 0)
    # ── Sequential Memory ────────────────────────────────────
    'is_seq_memory',       # 1 = seq_memory 모드 trial, 0 = 일반 trial
    'seq_memory_step',     # 현재 스텝 인덱스 (0-based), 일반 trial은 빈칸
    # ── 타이밍 ──────────────────────────────────────────────
    'psychopy_time',       # core.getTime() 기준
    'dwell_time',          # 이탈 시에만 기록 (진입은 0.0)
]


def init_gaze_file(save_dir: str, subject_id: str) -> str:
    path = os.path.join(save_dir, 'gaze_events.csv')
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=_HEADERS)
        writer.writeheader()
    print(f"[GazeSaver] 초기화 완료: {path}")
    return path


def save_gaze_event(
    file_path: str,
    subject_id: str,
    trial_id: int,
    event_type: str,
    aoi_id: str,
    aoi_info: dict,
    psychopy_time: float,
    dwell_time: float = 0.0,
    is_seq_memory: bool = False,
    seq_memory_step: int | None = None,
):
    pos = aoi_info.get('pos') or (None, None)

    row = {
        'trial_id':             trial_id,
        'subject_id':           subject_id,
        'event_type':           event_type,
        'aoi_id':               aoi_id,
        'aoi_type':             aoi_info.get('type', ''),
        'aoi_row':              pos[0] if pos[0] is not None else '',
        'aoi_col':              pos[1] if pos[1] is not None else '',
        'labjack_trigger_code': aoi_info.get('trigger_code', '') if event_type == 'enter' else 0,
        'is_seq_memory':        1 if is_seq_memory else 0,
        'seq_memory_step':      seq_memory_step if seq_memory_step is not None else '',
        'psychopy_time':        round(psychopy_time, 6),
        'dwell_time':           round(dwell_time, 6) if event_type == 'exit' else 0.0,
    }

    with open(file_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=_HEADERS)
        writer.writerow(row)
