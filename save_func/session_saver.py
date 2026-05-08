# save_func/session_saver.py
# 세션 메타데이터와 게임 최종 요약을 session.json에 기록한다.
#
# 호출 흐름
# ---------
#   게임 시작 직후  → init_session(...)           → session_file 경로 저장
#   게임 종료 직전  → finalize_session(session_file, game_state, result)
#
# session.json 구조
# -----------------
#   {
#     "subject_id": "P001",
#     "session_start": "2026-03-31 14:30:00",
#     "session_end": null,          ← finalize_session 호출 시 채워짐
#     "game_mode": "selection1",
#     "hardware": {"use_eyelink": true, "use_labjack": false},
#     "outcome": null,              ← 'victory' | 'defeat' | 'timeout' | 'exit'
#     "summary": {                  ← game_state.get_summary() 결과
#       ...
#       "seq_memory": {             ← Sequential Memory 집계 (get_seq_memory_summary())
#         "user_activations": N,    ← 사용자 seq_memory 발동 횟수
#         "user_all_success": N,    ← 사용자 전체 성공 (n칸 점프) 횟수
#         "user_step_fail": N,      ← 사용자 스텝 실패 횟수
#         "user_total_seq_trials": N,
#         "pc_activations": N,
#         "pc_all_success": N,
#         "pc_step_fail": N,
#         "pc_total_seq_trials": N
#       }
#     },
#     "trial_count": 0,
#     "save_dir": "/path/to/Data/P001_20260331_143000"
#   }

import json
import os
from datetime import datetime


def init_session(
    save_dir: str,
    subject_id: str,
    use_eyelink: bool,
    use_labjack: bool,
) -> str:
    
    """
    Parameters
    ----------
    save_dir : str
        저장 디렉토리 경로 (존재해야 함).
    subject_id : str
        피험자 ID.
    use_eyelink : bool
        EyeLink 연결 여부.
    use_labjack : bool
        LabJack 연결 여부.

    Returns: str 생성된 session.json 파일의 절대 경로.
    """
    path = os.path.join(save_dir, 'session.json')

    data = {
        'subject_id':    subject_id,
        'session_start': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'session_end':   None,
        'hardware': {
            'use_eyelink': use_eyelink,
            'use_labjack': use_labjack,
        },
        'outcome':     None,
        'summary':     {},
        'trial_count': 0,
        'save_dir':    save_dir,
    }

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"[SessionSaver] 세션 시작 기록: {path}")
    return path


def finalize_session(session_file: str, game_state, outcome: str):
    if not os.path.exists(session_file):
        print(f"[SessionSaver] session.json 없음: {session_file}")
        return

    with open(session_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    summary = game_state.get_summary()

    # token_positions 는 tuple 키를 포함할 수 있어 JSON 직렬화 불가 → 문자열 변환
    if 'token_positions' in summary:
        summary['token_positions'] = {
            k: list(v) if isinstance(v, (tuple, list)) else v
            for k, v in summary['token_positions'].items()
        }

    data['session_end'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    data['outcome']     = outcome
    data['summary']     = summary
    data['trial_count'] = len(game_state.trial_history)
    data['game_mode']   = game_state.selected_mode_id

    with open(session_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"[SessionSaver] 세션 종료 기록 완료: {session_file}")
