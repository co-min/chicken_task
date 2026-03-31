# save_func/gaze_event_saver.py
# AOI 시선 진입/이탈 이벤트를 gaze_events.csv에 기록한다.
#
# 역할
# ----
# EyeLink EDF 파일에는 GAZE_ENTER / GAZE_EXIT 메시지가 기록되지만,
# EDF → ASC 변환 없이도 Python에서 바로 분석할 수 있도록
# 동일한 이벤트를 CSV에도 병렬로 저장한다.
#
# 호출 흐름
# ---------
#   세션 시작         → init_gaze_file(save_dir, subject_id)  → file_path 저장
#   AOI 진입 시       → save_gaze_event(..., event_type='enter')
#   AOI 이탈 시       → save_gaze_event(..., event_type='exit', dwell_time=...)
#
# AOIManager와의 연동
# -------------------
# aoi_manager.gaze_file_path 속성에 file_path를 주입하면
# _on_enter / _on_exit 에서 직접 호출할 수 있다.
# (AOIManager 수정 없이 game_play.py 루프에서 호출해도 무방)

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
    # ── 타이밍 ──────────────────────────────────────────────
    'psychopy_time',       # core.getTime() 기준
    'dwell_time',          # 이탈 시에만 기록 (진입은 0.0)
]


def init_gaze_file(save_dir: str, subject_id: str) -> str:
    """
    gaze_events.csv 파일을 생성하고 헤더를 작성한다.

    Parameters
    ----------
    save_dir : str
        저장 디렉토리 경로.
    subject_id : str
        피험자 ID.

    Returns
    -------
    str
        생성된 CSV 파일의 절대 경로.
    """
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
):
    """
    AOI 진입·이탈 이벤트 1개를 gaze_events.csv에 append한다.

    Parameters
    ----------
    file_path : str
        init_gaze_file() 이 반환한 CSV 경로.
    subject_id : str
        피험자 ID.
    trial_id : int
        현재 시행 번호 (game_state.trial_id).
    event_type : str
        'enter' 또는 'exit'.
    aoi_id : str
        AOI 식별자. 예: 'deck_1_4'
    aoi_info : dict
        AOIManager.aois[aoi_id] 값.
        필수 키: 'type', 'pos', 'trigger_code'
    psychopy_time : float
        core.getTime() 반환값.
    dwell_time : float
        AOI에 머문 시간(초). 이탈 이벤트에만 의미 있음.
    """
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
        'psychopy_time':        round(psychopy_time, 6),
        'dwell_time':           round(dwell_time, 6) if event_type == 'exit' else 0.0,
    }

    with open(file_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=_HEADERS)
        writer.writerow(row)
