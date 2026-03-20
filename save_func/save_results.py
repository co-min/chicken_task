"""
save_results.py
===============
실험 전체의 결과를 요약하여 CSV 파일로 저장합니다.
프레임별 상세 로그(save_frame_log.py)와 달리, 각 trial의 핵심 정보만 간결하게 정리하여 하나의 CSV 파일로 저장합니다:
- 각 시행(trial)별 한 행
- subject_id, trial_number, token, target_position, selected_position, is_match, elapsed_time 등 핵심 정보만 포함

주요 기능:
- 게임 플레이 완료 후 전체 trial 결과 저장
- 각 trial의 핵심 정보 추출 및 정리
- 활동 통계 (총 시행 수, 정답률 등) 추가 기록
- 타임스탐프 포함한 파일명
"""

import csv
import sys
from pathlib import Path
from datetime import datetime

try:
    from ..config import SAVE_RESULTS
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from config import SAVE_RESULTS


def _ensure_save_dir(save_dir):
    """저장 폴더 생성 (없으면 생성)"""
    if save_dir is None:
        save_dir = Path.cwd() / "results"
    else:
        save_dir = Path(save_dir)
    
    save_dir.mkdir(parents=True, exist_ok=True)
    return save_dir


def _get_timestamp_str():
    """현재 시간을 파일명 형식으로 반환 (YYYYMMDD_HHMMSS)"""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _format_position(pos):
    """위치 정보를 문자열로 포맷 (row, col) -> 'R1C2' 형식"""
    if pos is None:
        return ''
    row, col = pos
    return f"R{row+1}C{col+1}"


def _format_card(card):
    """카드 정보를 문자열로 포맷
    
    Args:
        card (dict): {'color': str, 'shape': str, 'number': int}
    
    Returns:
        str: "red_square_2" 형식
    """
    if card is None:
        return ''
    return f"{card.get('color', '')}_{card.get('shape', '')}_{card.get('number', '')}"


def _format_condition(condition):
    """조건 정보를 문자열로 포맷
    
    Args:
        condition (dict): {'color': str, 'shape': str, 'number': int, 'attr': str}
    
    Returns:
        str: "red" (단일 속성 조건)
    """
    if condition is None:
        return ''
    
    # 조건은 color/shape/number 중 하나만 가짐
    if condition.get('color'):
        return condition['color']
    elif condition.get('shape'):
        return condition['shape']
    elif condition.get('number'):
        return str(condition['number'])
    return ''


def _calculate_statistics(trial_history):
    """시행 기록으로부터 통계 계산
    
    Args:
        trial_history (list): 모든 시행 기록 리스트
    
    Returns:
        dict: 통계 정보
    """
    if not trial_history:
        return {
            'total_trials': 0,
            'correct_trials': 0,
            'accuracy': 0.0,
            'user_trials': 0,
            'user_correct': 0,
            'user_accuracy': 0.0,
            'pc_trials': 0,
            'pc_correct': 0,
            'pc_accuracy': 0.0,
            'total_elapsed_time': 0.0,
            'avg_elapsed_time': 0.0,
        }
    
    # 전체 통계
    total_trials = len(trial_history)
    correct_trials = sum(1 for t in trial_history if t.get('is_match'))
    accuracy = (correct_trials / total_trials) if total_trials > 0 else 0.0
    
    # 사용자 시행 (chase, flight)
    user_trials = [t for t in trial_history if t.get('token') in ('chase', 'flight')]
    user_correct = sum(1 for t in user_trials if t.get('is_match'))
    user_accuracy = (user_correct / len(user_trials)) if user_trials else 0.0
    
    # PC 시행 (octopus)
    pc_trials = [t for t in trial_history if t.get('token') == 'octopus']
    pc_correct = sum(1 for t in pc_trials if t.get('is_match'))
    pc_accuracy = (pc_correct / len(pc_trials)) if pc_trials else 0.0
    
    # 시간 통계
    total_elapsed_time = sum(t.get('elapsed_time', 0.0) for t in trial_history)
    user_elapsed_time = sum(t.get('elapsed_time', 0.0) for t in user_trials)
    avg_elapsed_time = (user_elapsed_time / len(user_trials)) if user_trials else 0.0
    
    return {
        'total_trials': total_trials,
        'correct_trials': correct_trials,
        'accuracy': accuracy,
        'user_trials': len(user_trials),
        'user_correct': user_correct,
        'user_accuracy': user_accuracy,
        'pc_trials': len(pc_trials),
        'pc_correct': pc_correct,
        'pc_accuracy': pc_accuracy,
        'total_elapsed_time': total_elapsed_time,
        'avg_elapsed_time': avg_elapsed_time,
    }


# ==================== MAIN GAME PLAY ====================
def save_game_results(game_state, subject_id, save_dir=None):
    """
    게임 플레이 완료 후 전체 trial 결과 저장
    
    Args:
        game_state (GameState): 게임 상태 객체
        subject_id (str): 피험자 ID
        save_dir (Path or str): 저장 폴더 (None이면 기본값 사용)
    
    Returns:
        Path: 저장된 파일 경로
    """
    if not SAVE_RESULTS:
        return None
    
    trial_history = game_state.trial_history
    if not trial_history:
        print("  ⚠ 시행 기록이 없습니다. 결과를 저장하지 않습니다.")
        return None
    
    save_dir = _ensure_save_dir(save_dir)
    timestamp = _get_timestamp_str()
    filename = save_dir / f"{subject_id}_results_{timestamp}.csv"
    
    # CSV 필드 정의
    fieldnames = [
        'trial_number',      # 시행 번호 (1부터 시작)
        'token',             # 사용된 토큰 (chase, flight, octopus)
        'target_condition',  # 목표 조건 (색상/모양/숫자 중 하나)
        'target_position',   # 목표 위치
        'selected_position', # 선택한 카드 위치
        'selected_card',     # 선택한 카드 (색상_모양_숫자)
        'is_match',          # 정답 여부 (True/False)
        'elapsed_time',      # 경과 시간 (초)
    ]
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for trial_idx, trial in enumerate(trial_history, start=1):
            row = {
                'trial_number': trial_idx,
                'token': trial.get('token', ''),
                'target_condition': _format_condition(trial.get('condition')),
                'target_position': _format_position(trial.get('target_pos')),
                'selected_position': _format_position(trial.get('selected_card_pos')),
                'selected_card': _format_card(trial.get('selected_card')),
                'is_match': trial.get('is_match', False),
                'elapsed_time': round(trial.get('elapsed_time', 0.0), 3),
            }
            writer.writerow(row)
    
    print(f"  ✓ Game results saved: {filename} ({len(trial_history)} trials)")
    return filename


def save_game_statistics(game_state, subject_id, save_dir=None):
    """
    게임 플레이의 통계 요약을 별도 파일로 저장
    
    Args:
        game_state (GameState): 게임 상태 객체
        subject_id (str): 피험자 ID
        save_dir (Path or str): 저장 폴더 (None이면 기본값 사용)
    
    Returns:
        Path: 저장된 파일 경로
    """
    if not SAVE_RESULTS:
        return None
    
    trial_history = game_state.trial_history
    stats = _calculate_statistics(trial_history)
    
    save_dir = _ensure_save_dir(save_dir)
    timestamp = _get_timestamp_str()
    filename = save_dir / f"{subject_id}_statistics_{timestamp}.csv"
    
    # 통계 정보를 key-value 쌍으로 저장
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Metric', 'Value'])
        writer.writerow(['Subject ID', subject_id])
        writer.writerow(['Timestamp', datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
        writer.writerow([])
        
        writer.writerow(['Total Trials', stats['total_trials']])
        writer.writerow(['Correct Trials', stats['correct_trials']])
        writer.writerow(['Overall Accuracy', f"{stats['accuracy']:.2%}"])
        writer.writerow([])
        
        writer.writerow(['User Trials (Chase/Flight)', stats['user_trials']])
        writer.writerow(['User Correct', stats['user_correct']])
        writer.writerow(['User Accuracy', f"{stats['user_accuracy']:.2%}"])
        writer.writerow([])
        
        writer.writerow(['PC Trials (Octopus)', stats['pc_trials']])
        writer.writerow(['PC Correct', stats['pc_correct']])
        writer.writerow(['PC Accuracy', f"{stats['pc_accuracy']:.2%}"])
        writer.writerow([])
        
        writer.writerow(['Total Elapsed Time (sec)', f"{stats['total_elapsed_time']:.3f}"])
        writer.writerow(['Avg Elapsed Time per User Trial (sec)', f"{stats['avg_elapsed_time']:.3f}"])
    
    print(f"  ✓ Statistics saved: {filename}")
    return filename


def save_all_results(game_state, subject_id, save_dir=None):
    """
    결과와 통계를 모두 저장하는 통합 함수
    
    Args:
        game_state (GameState): 게임 상태 객체
        subject_id (str): 피험자 ID
        save_dir (Path or str): 저장 폴더 (None이면 기본값 사용)
    
    Returns:
        dict: 저장된 파일 경로들 {'results': Path, 'statistics': Path}
    """
    results_file = save_game_results(game_state, subject_id, save_dir)
    statistics_file = save_game_statistics(game_state, subject_id, save_dir)
    
    return {
        'results': results_file,
        'statistics': statistics_file
    }
