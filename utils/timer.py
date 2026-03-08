# timer.py
# Chicken Task - Timer Management (타이머 관리)
# 15초 타이머, 성공 시 리셋 기능

import time


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


# ==================== 테스트 코드 ====================
if __name__ == "__main__":
    import time
    
    print("\n### GameTimer 테스트 ###\n")
    
    # 타이머 생성 (테스트용 5초)
    timer = GameTimer(time_limit=5.0)
    print(f"초기 상태: running={timer.is_running}, expired={timer.is_expired()}")
    print(f"표시 텍스트: {timer.get_display_text()}")
    
    # 타이머 시작
    print("\n타이머 시작...")
    timer.start()
    print(f"running={timer.is_running}")
    
    # 2초 대기
    time.sleep(2.0)
    print(f"\n2초 경과:")
    print(f"  경과 시간: {timer.get_elapsed():.2f}초")
    print(f"  남은 시간: {timer.get_remaining():.2f}초")
    print(f"  표시 텍스트: {timer.get_display_text()}")
    print(f"  만료? {timer.is_expired()}")
    
    # 리셋 테스트
    print("\n타이머 리셋...")
    timer.reset()
    print(f"리셋 후 경과 시간: {timer.get_elapsed():.2f}초")
    
    # 만료까지 대기
    print("\n만료까지 대기...")
    while not timer.is_expired():
        time.sleep(0.5)
        print(f"  {timer.get_display_text()}", end="\r")
    
    print(f"\n타이머 만료! 경과 시간: {timer.get_elapsed():.2f}초")
    
    # StopWatch 테스트
    print("\n### StopWatch 테스트 ###\n")
    
    sw = StopWatch()
    sw.start()
    print("스톱워치 시작...")
    
    time.sleep(1.5)
    print(f"경과 시간: {sw.get_elapsed():.2f}초")
    
    sw.stop()
    print("스톱워치 정지")
    
    print("\n[OK] timer 테스트 완료!")
