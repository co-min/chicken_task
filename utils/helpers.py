# helpers.py
# Chicken Task - General Helper Functions (일반 헬퍼 함수)

import random
from datetime import datetime


def get_timestamp():
    """
    현재 타임스탬프 문자열 반환
    
    Returns:
        str: "YYYY-MM-DD_HH-MM-SS" 형식
    """
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def position_to_index(row, col, cols):
    """
    2D 위치를 1D 인덱스로 변환
    
    Args:
        row (int): 행
        col (int): 열
        cols (int): 열 개수
    
    Returns:
        int: 1D 인덱스
    """
    return row * cols + col


def index_to_position(index, cols):
    """
    1D 인덱스를 2D 위치로 변환
    
    Args:
        index (int): 1D 인덱스
        cols (int): 열 개수
    
    Returns:
        tuple: (row, col)
    """
    row = index // cols
    col = index % cols
    return (row, col)


def get_circular_distance(pos1, pos2, rows, cols):
    """
    순환 경로에서 두 위치 간 거리 계산
    
    Args:
        pos1 (tuple): 위치1 (row, col)
        pos2 (tuple): 위치2 (row, col)
        rows (int): 행 개수
        cols (int): 열 개수
    
    Returns:
        int: pos1에서 pos2까지의 칸 수
    """
    total_positions = rows * cols
    
    idx1 = position_to_index(pos1[0], pos1[1], cols)
    idx2 = position_to_index(pos2[0], pos2[1], cols)
    
    # 순환 경로에서 앞으로 가는 거리
    if idx2 >= idx1:
        distance = idx2 - idx1
    else:
        distance = (total_positions - idx1) + idx2
    
    return distance


def shuffle_with_seed(items, seed=None):
    """
    시드를 사용한 셔플 (재현 가능)
    
    Args:
        items (list): 셔플할 리스트
        seed (int, optional): 랜덤 시드
    
    Returns:
        list: 셔플된 새 리스트 (원본 보존)
    """
    shuffled = items.copy()
    
    if seed is not None:
        random.seed(seed)
    
    random.shuffle(shuffled)
    
    return shuffled


def clamp(value, min_value, max_value):
    """
    값을 범위 내로 제한
    
    Args:
        value (float): 값
        min_value (float): 최소값
        max_value (float): 최대값
    
    Returns:
        float: 제한된 값
    """
    return max(min_value, min(value, max_value))


def format_duration(seconds):
    """
    초를 사람이 읽기 쉬운 형식으로 변환
    
    Args:
        seconds (float): 시간 (초)
    
    Returns:
        str: "1m 23s" 또는 "45s" 형식
    """
    if seconds < 60:
        return f"{int(seconds)}초"
    else:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}분 {secs}초"


def validate_position(row, col, rows, cols):
    """
    위치가 유효한지 검증
    
    Args:
        row (int): 행
        col (int): 열
        rows (int): 행 개수
        cols (int): 열 개수
    
    Returns:
        bool: True=유효, False=무효
    """
    return 0 <= row < rows and 0 <= col < cols


# ==================== 테스트 코드 ====================
if __name__ == "__main__":
    print("\n### 헬퍼 함수 테스트 ###\n")
    
    # 타임스탬프
    print(f"타임스탬프: {get_timestamp()}")
    
    # 위치 변환
    print("\n### 위치 변환 ###")
    print(f"(0,0) → 인덱스 {position_to_index(0, 0, 9)}")
    print(f"(0,8) → 인덱스 {position_to_index(0, 8, 9)}")
    print(f"(2,8) → 인덱스 {position_to_index(2, 8, 9)}")
    
    print(f"인덱스 0 → {index_to_position(0, 9)}")
    print(f"인덱스 8 → {index_to_position(8, 9)}")
    print(f"인덱스 26 → {index_to_position(26, 9)}")
    
    # 순환 거리
    print("\n### 순환 거리 ###")
    pos1 = (0, 0)  # 1-1
    pos2 = (0, 5)  # 1-6
    dist = get_circular_distance(pos1, pos2, 3, 9)
    print(f"{pos1}에서 {pos2}까지: {dist}칸")
    
    pos1 = (2, 8)  # 3-9 (마지막)
    pos2 = (0, 2)  # 1-3
    dist = get_circular_distance(pos1, pos2, 3, 9)
    print(f"{pos1}에서 {pos2}까지: {dist}칸 (순환)")
    
    # 셔플
    print("\n### 시드 셔플 ###")
    items = [1, 2, 3, 4, 5]
    shuffled1 = shuffle_with_seed(items, seed=42)
    shuffled2 = shuffle_with_seed(items, seed=42)
    print(f"원본: {items}")
    print(f"셔플1 (seed=42): {shuffled1}")
    print(f"셔플2 (seed=42): {shuffled2}")
    print(f"재현 가능? {shuffled1 == shuffled2}")
    
    # Clamp
    print("\n### Clamp ###")
    print(f"clamp(5, 0, 10) = {clamp(5, 0, 10)}")
    print(f"clamp(-5, 0, 10) = {clamp(-5, 0, 10)}")
    print(f"clamp(15, 0, 10) = {clamp(15, 0, 10)}")
    
    # 시간 형식
    print("\n### 시간 형식 ###")
    print(f"45초: {format_duration(45)}")
    print(f"83초: {format_duration(83)}")
    print(f"125초: {format_duration(125)}")
    
    # 위치 검증
    print("\n### 위치 검증 ###")
    print(f"(0,0) 유효 (3x9)? {validate_position(0, 0, 3, 9)}")
    print(f"(2,8) 유효 (3x9)? {validate_position(2, 8, 3, 9)}")
    print(f"(3,9) 유효 (3x9)? {validate_position(3, 9, 3, 9)}")
    
    print("\n[OK] helpers 테스트 완료!")
