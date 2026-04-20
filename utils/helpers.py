# helpers.py
# Chicken Task - General Helper Functions (일반 헬퍼 함수)

import random
from datetime import datetime


def get_timestamp():
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def position_to_index(row, col, cols):
    # 2D to 1D
    return row * cols + col


def index_to_position(index, cols):
    # 1D to 2D
    row = index // cols
    col = index % cols
    return (row, col)


def get_circular_distance(pos1, pos2, rows, cols):
    # 순환 경로에서 두 위치 간 거리 계산
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
    shuffled = items.copy()
    
    if seed is not None:
        random.seed(seed)
    
    random.shuffle(shuffled)
    
    return shuffled


def clamp(value, min_value, max_value):
    return max(min_value, min(value, max_value))


def format_duration(seconds):
    if seconds < 60:
        return f"{int(seconds)}초"
    else:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}분 {secs}초"


def validate_position(row, col, rows, cols):
    return 0 <= row < rows and 0 <= col < cols
