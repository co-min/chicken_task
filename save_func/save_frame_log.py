"""
save_frame_log.py
=================
실험의 다양한 단계(phase)에서 발생하는 프레임별 데이터를 CSV 파일로 저장합니다.
각 실험 단계마다 기록할 데이터가 다르므로, 단계별로 특화된 저장 함수를 제공합니다.

주요 기능:
- phase별 전문화된 CSV 저장 함수
- 프레임 타이밍 정보 기록 (시간 기반 동기화 지원)
- 마커 온/오프 상태 추적
- 실험 단계별 이벤트 정보 통합
"""

import csv
import sys
from pathlib import Path
from datetime import datetime

try:
    from ..config import SAVE_FRAME_LOG
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from config import SAVE_FRAME_LOG


def _ensure_save_dir(save_dir):
    """저장 폴더 생성 (없으면 생성)"""
    if save_dir is None:
        save_dir = Path.cwd() / "frame_logs"
    else:
        save_dir = Path(save_dir)
    
    save_dir.mkdir(parents=True, exist_ok=True)
    return save_dir


def _get_timestamp_str():
    """현재 시간을 파일명 형식으로 반환 (YYYYMMDD_HHMMSS)"""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


# ==================== STARTING PHASE ====================
def save_frame_log_starting(frame_log, subject_id, save_dir=None):
    """
    시작 화면 프레임 로그 저장
    
    Args:
        frame_log (list): 프레임 로그 리스트
        subject_id (str): 피험자 ID
        save_dir (Path or str): 저장 폴더 (None이면 기본값 사용)
    
    Returns:
        Path: 저장된 파일 경로
    """
    if not SAVE_FRAME_LOG or not frame_log:
        return None
    
    save_dir = _ensure_save_dir(save_dir)
    timestamp = _get_timestamp_str()
    filename = save_dir / f"{subject_id}_starting_{timestamp}.csv"
    
    fieldnames = ['frame_count', 'phase', 'time', 'dt', 'marker_on']
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for log_entry in frame_log:
            row = {
                'frame_count': log_entry.get('frame_count', 0),
                'phase': log_entry.get('phase', 'starting'),
                'time': log_entry.get('time', 0.0),
                'dt': log_entry.get('dt', 0.0),
                'marker_on': log_entry.get('marker_on', True),
            }
            writer.writerow(row)
    
    print(f"  ✓ Starting frame log saved: {filename} ({len(frame_log)} frames)")
    return filename


# ==================== TUTORIAL PHASE ====================
def save_frame_log_tutorial(frame_log, subject_id, save_dir=None):
    """
    튜토리얼 화면 프레임 로그 저장
    
    Args:
        frame_log (list): 프레임 로그 리스트
        subject_id (str): 피험자 ID
        save_dir (Path or str): 저장 폴더
    
    Returns:
        Path: 저장된 파일 경로
    """
    if not SAVE_FRAME_LOG or not frame_log:
        return None
    
    save_dir = _ensure_save_dir(save_dir)
    timestamp = _get_timestamp_str()
    filename = save_dir / f"{subject_id}_tutorial_{timestamp}.csv"
    
    fieldnames = ['frame_count', 'phase', 'time', 'dt', 'marker_on']
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for log_entry in frame_log:
            row = {
                'frame_count': log_entry.get('frame_count', 0),
                'phase': log_entry.get('phase', 'tutorial'),
                'time': log_entry.get('time', 0.0),
                'dt': log_entry.get('dt', 0.0),
                'marker_on': log_entry.get('marker_on', True),
            }
            writer.writerow(row)
    
    print(f"  ✓ Tutorial frame log saved: {filename} ({len(frame_log)} frames)")
    return filename


# ==================== TOKEN SELECTION PHASE ====================
def save_frame_log_token_selection(frame_log, subject_id, save_dir=None):
    """
    토큰 선택 화면 프레임 로그 저장
    
    Args:
        frame_log (list): 프레임 로그 리스트
        subject_id (str): 피험자 ID
        save_dir (Path or str): 저장 폴더
    
    Returns:
        Path: 저장된 파일 경로
    """
    if not SAVE_FRAME_LOG or not frame_log:
        return None
    
    save_dir = _ensure_save_dir(save_dir)
    timestamp = _get_timestamp_str()
    filename = save_dir / f"{subject_id}_token_selection_{timestamp}.csv"
    
    fieldnames = ['frame_count', 'phase', 'time', 'dt', 'marker_on']
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for log_entry in frame_log:
            row = {
                'frame_count': log_entry.get('frame_count', 0),
                'phase': log_entry.get('phase', 'token_selection'),
                'time': log_entry.get('time', 0.0),
                'dt': log_entry.get('dt', 0.0),
                'marker_on': log_entry.get('marker_on', True),
            }
            writer.writerow(row)
    
    print(f"  ✓ Token selection frame log saved: {filename} ({len(frame_log)} frames)")
    return filename


# ==================== GAME PLAY PHASE ====================
def save_frame_log_game_play(frame_log, subject_id, save_dir=None):
    """
    게임 플레이 프레임 로그 저장 (가장 복잡한 단계)
    
    게임 플레이 중 매 프레임마다 턴, 타겟, 마커 상태 등을 기록합니다.
    
    Args:
        frame_log (list): 프레임 로그 리스트
        subject_id (str): 피험자 ID
        save_dir (Path or str): 저장 폴더
    
    Returns:
        Path: 저장된 파일 경로
    """
    if not SAVE_FRAME_LOG or not frame_log:
        return None
    
    save_dir = _ensure_save_dir(save_dir)
    timestamp = _get_timestamp_str()
    filename = save_dir / f"{subject_id}_game_play_{timestamp}.csv"
    
    fieldnames = ['frame_count', 'phase', 'time', 'dt', 'marker_on', 'event_type']
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for log_entry in frame_log:
            row = {
                'frame_count': log_entry.get('frame_count', 0),
                'phase': log_entry.get('phase', 'game_play'),
                'time': log_entry.get('time', 0.0),
                'dt': log_entry.get('dt', 0.0),
                'marker_on': log_entry.get('marker_on', True),
                'event_type': log_entry.get('event_type', ''),
            }
            writer.writerow(row)
    
    print(f"  ✓ Game play frame log saved: {filename} ({len(frame_log)} frames)")
    return filename


# ==================== ENDING PHASE ====================
def save_frame_log_ending(frame_log, subject_id, save_dir=None):
    """
    종료 화면 프레임 로그 저장
    
    Args:
        frame_log (list): 프레임 로그 리스트
        subject_id (str): 피험자 ID
        save_dir (Path or str): 저장 폴더
    
    Returns:
        Path: 저장된 파일 경로
    """
    if not SAVE_FRAME_LOG or not frame_log:
        return None
    
    save_dir = _ensure_save_dir(save_dir)
    timestamp = _get_timestamp_str()
    filename = save_dir / f"{subject_id}_ending_{timestamp}.csv"
    
    fieldnames = ['frame_count', 'phase', 'time', 'dt', 'marker_on']
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for log_entry in frame_log:
            row = {
                'frame_count': log_entry.get('frame_count', 0),
                'phase': log_entry.get('phase', 'ending'),
                'time': log_entry.get('time', 0.0),
                'dt': log_entry.get('dt', 0.0),
                'marker_on': log_entry.get('marker_on', True),
            }
            writer.writerow(row)
    
    print(f"  ✓ Ending frame log saved: {filename} ({len(frame_log)} frames)")
    return filename


# ==================== UTILITY ====================
def save_all_frame_logs(frame_logs_dict, subject_id, save_dir=None):
    """
    모든 phase의 프레임 로그를 한 번에 저장
    
    Args:
        frame_logs_dict (dict): {'phase_name': frame_log_list} 형태의 딕셔너리
        subject_id (str): 피험자 ID
        save_dir (Path or str): 저장 폴더
    
    Returns:
        dict: {'phase_name': filepath} 저장 결과
    """
    results = {}
    
    if 'starting' in frame_logs_dict:
        results['starting'] = save_frame_log_starting(
            frame_logs_dict['starting'], subject_id, save_dir
        )
    
    if 'tutorial' in frame_logs_dict:
        results['tutorial'] = save_frame_log_tutorial(
            frame_logs_dict['tutorial'], subject_id, save_dir
        )
    
    if 'token_selection' in frame_logs_dict:
        results['token_selection'] = save_frame_log_token_selection(
            frame_logs_dict['token_selection'], subject_id, save_dir
        )
    
    if 'game_play' in frame_logs_dict:
        results['game_play'] = save_frame_log_game_play(
            frame_logs_dict['game_play'], subject_id, save_dir
        )
    
    if 'ending' in frame_logs_dict:
        results['ending'] = save_frame_log_ending(
            frame_logs_dict['ending'], subject_id, save_dir
        )
    
    return results
