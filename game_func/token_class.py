# token_class.py
# Chicken Task - Token Management (토큰 관리)
# chase, octopus, flight 토큰 관리 및 이동

import sys
from pathlib import Path

try:
    from ..config import BOARD_ROWS, BOARD_COLS, CHASE_START_POS, OCTOPUS_START_POS, FLIGHT_START_POS
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from config import BOARD_ROWS, BOARD_COLS, CHASE_START_POS, OCTOPUS_START_POS, FLIGHT_START_POS


class Token:
    """
    개별 토큰 클래스
    """
    
    def __init__(self, name, start_pos):
        """
        토큰 초기화
        
        Args:
            name (str): 토큰 이름 ('chase', 'octopus', 'flight')
            start_pos (tuple): 시작 위치 (row, col)
        """
        self.name = name
        self.start_pos = start_pos
        self.position = start_pos  # 현재 위치
        self.move_count = 0        # 이동 횟수
    
    def get_position(self):
        """현재 위치 반환"""
        return self.position
    
    def move_to(self, row, col):
        """
        지정된 위치로 이동
        
        Args:
            row (int): 행
            col (int): 열
        """
        self.position = (row, col)
        self.move_count += 1
    
    def reset(self):
        """시작 위치로 리셋"""
        self.position = self.start_pos
        self.move_count = 0
    
    def __str__(self):
        """문자열 표현"""
        return f"{self.name}@{self.position}"


class TokenManager:
    """
    토큰 관리자 - chase, octopus, flight 통합 관리
    순환 경로: 1-1 → 1-9 → 2-1 → 2-9 → 3-1 → 3-9 → 1-1
    """
    
    def __init__(self):
        """토큰 관리자 초기화"""
        # 3개 토큰 생성
        self.chase = Token('chase', CHASE_START_POS)
        self.octopus = Token('octopus', OCTOPUS_START_POS)
        self.flight = Token('flight', FLIGHT_START_POS)
        
        self.rows = BOARD_ROWS
        self.cols = BOARD_COLS
    
    def get_token(self, token_name):
        """
        토큰 가져오기
        
        Args:
            token_name (str): 'chase', 'octopus', 'flight'
        
        Returns:
            Token: 토큰 객체
        """
        if token_name == 'chase':
            return self.chase
        elif token_name == 'octopus':
            return self.octopus
        elif token_name == 'flight':
            return self.flight
        return None
    
    def get_all_positions(self):
        """
        모든 토큰 위치 반환
        
        Returns:
            dict: {토큰_이름: (row, col)}
        """
        return {
            'chase': self.chase.get_position(),
            'octopus': self.octopus.get_position(),
            'flight': self.flight.get_position()
        }
    
    def get_next_position(self, current_pos):
        """
        순환 경로에서 다음 위치 계산
        1-1 → 1-9 → 2-1 → 2-9 → 3-1 → 3-9 → 1-1
        
        Args:
            current_pos (tuple): 현재 위치 (row, col)
        
        Returns:
            tuple: 다음 위치 (row, col)
        """
        row, col = current_pos
        
        # 다음 칸으로 이동
        next_col = col + 1
        next_row = row
        
        # 열 끝에 도달하면 다음 행으로
        if next_col >= self.cols:
            next_col = 0
            next_row = row + 1
        
        # 마지막 행 끝에 도달하면 처음으로 순환
        if next_row >= self.rows:
            next_row = 0
        
        return (next_row, next_col)
    
    def get_target_position(self, token_name):
        """
        토큰의 타겟 위치 계산
        - 일반: 다음 칸
        - 잡기 상황: 다른 토큰이 다음 칸에 있으면 그 다음 칸
        
        Args:
            token_name (str): 'chase', 'octopus', 'flight'
        
        Returns:
            tuple: 타겟 위치 (row, col)
        """
        token = self.get_token(token_name)
        if not token:
            return None
        
        current_pos = token.get_position()
        target_pos = self.get_next_position(current_pos)
        
        # 다른 토큰이 타겟 위치에 있는지 확인
        all_positions = self.get_all_positions()
        
        for other_name, other_pos in all_positions.items():
            if other_name != token_name and other_pos == target_pos:
                # 다른 토큰이 있으면 그 다음 칸으로 (잡기 메커니즘)
                target_pos = self.get_next_position(target_pos)
                break
        
        return target_pos
    
    def move_token(self, token_name, target_pos):
        """
        토큰 이동
        
        Args:
            token_name (str): 'chase', 'octopus', 'flight'
            target_pos (tuple): 타겟 위치 (row, col)
        
        Returns:
            bool: 성공 여부
        """
        token = self.get_token(token_name)
        if token:
            token.move_to(target_pos[0], target_pos[1])
            return True
        return False
    
    def check_catch(self, chaser_name, target_name):
        """
        잡기 조건 확인
        - chaser의 다음 칸이 target 위치 (바로 뒤에 있음)
        - chaser와 target이 같은 위치 (같은 칸)
        - chaser가 target의 다음 칸 위치 (방금 건너뛰어 추월함)
        
        Args:
            chaser_name (str): 쫓는 토큰
            target_name (str): 쫓기는 토큰
        
        Returns:
            bool: True=잡기 조건 충족
        """
        chaser = self.get_token(chaser_name)
        target = self.get_token(target_name)
        
        if not chaser or not target:
            return False
        
        chaser_pos = chaser.get_position()
        target_pos = target.get_position()
        
        # 1. chaser의 다음 칸이 target 위치 (바로 뒤에서 잡으려는 상황)
        chaser_next = self.get_next_position(chaser_pos)
        if chaser_next == target_pos:
            return True
        
        # 2. chaser와 target이 같은 위치 (같은 칸에 있음)
        if chaser_pos == target_pos:
            return True
        
        # 3. chaser가 target의 다음 칸에 위치 (방금 건너뛰어 추월함)
        target_next = self.get_next_position(target_pos)
        if chaser_pos == target_next:
            return True
        
        return False
    
    def check_victory(self):
        """
        승리 조건: chase가 octopus 잡기
        
        Returns:
            bool: True=승리
        """
        return self.check_catch('chase', 'octopus')
    
    def check_defeat(self):
        """
        패배 조건: octopus가 flight 잡기
        
        Returns:
            bool: True=패배
        """
        return self.check_catch('octopus', 'flight')
    
    def reset_all(self):
        """모든 토큰 리셋"""
        self.chase.reset()
        self.octopus.reset()
        self.flight.reset()
    
    def print_status(self):
        """토큰 상태 출력 (디버깅용)"""
        print("=" * 60)
        print("토큰 상태 (Token Status)")
        print("=" * 60)
        print(f"Chase:   {self.chase.get_position()} (이동: {self.chase.move_count}회)")
        print(f"Octopus: {self.octopus.get_position()} (이동: {self.octopus.move_count}회)")
        print(f"Flight:  {self.flight.get_position()} (이동: {self.flight.move_count}회)")
        print("=" * 60)


# ==================== 테스트 코드 ====================
if __name__ == "__main__":
    print("\n### TokenManager 테스트 ###\n")
    
    # 토큰 관리자 생성
    tm = TokenManager()
    tm.print_status()
    
    # 다음 위치 계산 테스트
    print("\n### 순환 경로 테스트 ###")
    test_positions = [
        (0, 0),   # 1-1 → 1-2
        (0, 8),   # 1-9 → 2-1
        (1, 8),   # 2-9 → 3-1
        (2, 8),   # 3-9 → 1-1 (순환)
    ]
    
    for pos in test_positions:
        next_pos = tm.get_next_position(pos)
        print(f"{pos} → {next_pos}")
    
    # 타겟 위치 테스트 (다른 토큰 건너뛰기)
    print("\n### 타겟 위치 테스트 (잡기 메커니즘) ###")
    print(f"Chase 타겟: {tm.get_target_position('chase')}")
    print(f"Octopus 타겟: {tm.get_target_position('octopus')}")
    print(f"Flight 타겟: {tm.get_target_position('flight')}")
    
    # 이동 테스트
    print("\n### 이동 테스트 ###")
    tm.move_token('chase', (0, 1))
    tm.move_token('octopus', (1, 1))
    tm.print_status()
    
    # 잡기 조건 테스트
    print("\n### 잡기 조건 테스트 ###")
    # Chase를 (0,8)로, Octopus를 (1,0)로 이동 → 잡기 가능
    tm.chase.move_to(0, 8)
    tm.octopus.move_to(1, 0)
    tm.print_status()
    
    print(f"\nChase가 Octopus 잡을 수 있음? {tm.check_victory()}")
    print(f"  → Chase(0,8) 다음 칸 = (1,0) = Octopus 위치")
    print(f"Octopus가 Flight 잡을 수 있음? {tm.check_defeat()}")
    
    # Chase가 이동하면 승리
    target = tm.get_target_position('chase')
    print(f"\nChase 타겟: {target} (Octopus 건너뛰어 (1,1))")
    tm.move_token('chase', target)
    tm.print_status()
    print(f"승리? {tm.check_victory()}")
    
    print("\n[OK] TokenManager 테스트 완료!")
