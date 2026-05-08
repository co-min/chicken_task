import json
import os
from datetime import datetime


def init_session(
    save_dir: str,
    subject_id: str,
    use_eyelink: bool,
    use_labjack: bool,
) -> str:

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
