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
    """
    core.wait(duration) 을 실행하고 실제 경과 시간을 측정
    실제 경과 시간이 기대값과 tolerance_s 이상 차이가 나면 경고 출력

    Parameters
    ----------
    duration : float
        기대 대기 시간 (초).
    label : str
        로그 메시지에 표시할 식별자 (어떤 wait 인지 구분용).
    tolerance_s : float
        허용 오차 (초). 기본 5 ms.
    """
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
    """
    게임 타이머
    - Phase 0 (token_selection): 제한시간 없음
    - Phase 1+ (game_play): 15초 제한, 성공 시 리셋
    """
    
    def __init__(self, time_limit=15.0):
        """
        타이머 초기화
        
        Args:
            time_limit (float): 제한 시간 (초)
        """
        self.time_limit = time_limit
        self.start_time = None
        self.is_running = False
    
    def start(self):
        """타이머 시작"""
        self.start_time = time.time()
        self.is_running = True
    
    def stop(self):
        """타이머 정지"""
        self.is_running = False
        self.start_time = None
    
    def reset(self):
        """타이머 리셋 (다시 시작)"""
        if self.is_running:
            self.start()  # 현재 시각으로 재설정
    
    def get_elapsed(self):
        """
        경과 시간 반환
        
        Returns:
            float: 경과 시간 (초)
        """
        if not self.is_running or self.start_time is None:
            return 0.0
        
        return time.time() - self.start_time
    
    def get_remaining(self):
        """
        남은 시간 반환
        
        Returns:
            float: 남은 시간 (초), 음수 가능
        """
        if not self.is_running:
            return self.time_limit
        
        elapsed = self.get_elapsed()
        remaining = self.time_limit - elapsed
        
        return max(0.0, remaining)
    
    def is_expired(self):
        """
        시간 초과 여부 확인
        
        Returns:
            bool: True=시간 초과
        """
        if not self.is_running:
            return False
        
        return self.get_elapsed() >= self.time_limit
    
    def get_display_text(self):
        """
        화면 표시용 시간 문자열 반환
        
        Returns:
            str: "MM:SS" 형식 (예: "00:15", "00:07")
        """
        remaining = self.get_remaining()
        
        minutes = int(remaining // 60)
        seconds = int(remaining % 60)
        
        return f"{minutes:02d}:{seconds:02d}"


class StopWatch:
    """
    스톱워치 (경과 시간 측정용)
    """
    
    def __init__(self):
        """스톱워치 초기화"""
        self.start_time = None
        self.is_running = False
    
    def start(self):
        """스톱워치 시작"""
        self.start_time = time.time()
        self.is_running = True
    
    def stop(self):
        """스톱워치 정지"""
        self.is_running = False
    
    def reset(self):
        """스톱워치 리셋"""
        self.start_time = None
        self.is_running = False
    
    def get_elapsed(self):
        """
        경과 시간 반환
        
        Returns:
            float: 경과 시간 (초)
        """
        if self.start_time is None:
            return 0.0
        
        if self.is_running:
            return time.time() - self.start_time
        else:
            return 0.0

