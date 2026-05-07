# timer.py
# Chicken Task - Timer Management (타이머 관리)
# 15초 타이머, 성공 시 리셋 기능

import time
from psychopy import core


# ---------------------------------------------------------------------------
# 타이밍 검사 유틸리티
# ---------------------------------------------------------------------------

# 대기 시간 허용 오차 (초). 이 값을 초과하면 TIMING MISMATCH 로그 출력.
WAIT_TOLERANCE_S = 0.005  # 5 ms


def checked_wait(duration: float, label: str = "wait", tolerance_s: float = WAIT_TOLERANCE_S):
    t_start = core.getTime()
    core.wait(duration)
    t_actual = core.getTime() - t_start
    
    if abs(t_actual - duration) > tolerance_s:
        print(
            f"[TIMING MISMATCH] {label}: "
            f"expected {duration * 1000:.2f} ms, "
            f"actual {t_actual * 1000:.2f} ms "
            f"(diff {(t_actual - duration) * 1000:+.2f} ms)"
        )


class GameTimer:
    
    def __init__(self, time_limit=15.0):
        self.time_limit = time_limit
        self.start_time = None
        self.is_running = False
    
    def start(self):
        self.start_time = time.time()
        self.is_running = True
    
    def stop(self):
        self.is_running = False
        self.start_time = None
    
    def reset(self):
        if self.is_running:
            self.start()  
    
    def get_elapsed(self):
        if not self.is_running or self.start_time is None:
            return 0.0
        
        return time.time() - self.start_time
    
    def get_remaining(self):
        if not self.is_running:
            return self.time_limit
        
        elapsed = self.get_elapsed()
        remaining = self.time_limit - elapsed
        
        return max(0.0, remaining)
    
    def is_expired(self):
        if not self.is_running:
            return False
        
        return self.get_elapsed() >= self.time_limit
    
    def get_display_text(self):
        remaining = self.get_remaining()
        
        minutes = int(remaining // 60)
        seconds = int(remaining % 60)
        
        return f"{minutes:02d}:{seconds:02d}"


class StopWatch:
    def __init__(self):
        self.start_time = None
        self.is_running = False
    
    def start(self):
        self.start_time = time.time()
        self.is_running = True
    
    def stop(self):
        self.is_running = False
    
    def reset(self):
        self.start_time = None
        self.is_running = False
    
    def get_elapsed(self):
        if self.start_time is None:
            return 0.0
        
        if self.is_running:
            return time.time() - self.start_time
        else:
            return 0.0

