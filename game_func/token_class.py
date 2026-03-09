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
    
    def check_catch(self, chaser_name, prey_name):
        """
        잡기 조건 확인 (추월 판정)
        
        조건: chaser가 prey의 바로 다음 위치에 도달 (1칸 추월)
        
        Note: 턴제 게임에서 get_target_position()이 다른 토큰을 건너뛰므로,
              두 토큰이 같은 위치에 있는 상황은 발생하지 않음.
        
        Args:
            chaser_name (str): 쫓는 토큰 ('chase' 또는 'octopus')
            prey_name (str): 쫓기는 토큰 ('octopus' 또는 'flight')
        
        Returns:
            bool: True=잡기 성공 (추월)
        
        Examples:
            Chase(1,1), Octopus(1,0) → Chase가 Octopus의 다음 위치 → True
            Chase(0,8), Octopus(1,0) → 아직 추월 안 함 → False
        """
        chaser = self.get_token(chaser_name)
        prey = self.get_token(prey_name)
        
        if not chaser or not prey:
            return False
        
        chaser_pos = chaser.get_position()
        prey_pos = prey.get_position()
        
        # chaser가 prey의 바로 다음 위치 (1칸 추월)
        prey_next = self.get_next_position(prey_pos)
        return chaser_pos == prey_next
    
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
    print("\n" + "="*60)
    print("TokenManager 테스트")
    print("="*60)
    
    # 토큰 관리자 생성
    tm = TokenManager()
    print("\n[1단계] 초기 상태")
    tm.print_status()
    
    # 순환 경로 테스트
    print("\n[2단계] 순환 경로 테스트")
    print("-" * 60)
    test_positions = [
        ((0, 0), (0, 1), "1행 1열 → 1행 2열"),
        ((0, 8), (1, 0), "1행 9열 → 2행 1열 (행 넘김)"),
        ((1, 8), (2, 0), "2행 9열 → 3행 1열 (행 넘김)"),
        ((2, 8), (0, 0), "3행 9열 → 1행 1열 (순환!)"),
    ]
    
    all_passed = True
    for pos, expected, desc in test_positions:
        result = tm.get_next_position(pos)
        status = "✓" if result == expected else "✗"
        if result != expected:
            all_passed = False
        print(f"{status} {pos} → {result} ({desc})")
    
    if all_passed:
        print("✓ 순환 경로 테스트 통과!")
    
    # 타겟 위치 테스트
    print("\n[3단계] 타겟 위치 계산 테스트 (초기 상태)")
    print("-" * 60)
    print("모두 (1,4)에서 시작 - 겹치므로 건너뛰기 발생")
    print(f"Chase 타겟:   {tm.get_target_position('chase')} (다음 칸에 Octopus/Flight → 건너뜀)")
    print(f"Octopus 타겟: {tm.get_target_position('octopus')} (다음 칸에 Chase/Flight → 건너뜀)")
    print(f"Flight 타겟:  {tm.get_target_position('flight')} (다음 칸에 Chase/Octopus → 건너뜀)")
    
    # 토큰 분리 후 타겟 테스트
    print("\n[4단계] 토큰 분리 후 타겟 계산")
    print("-" * 60)
    tm.move_token('chase', (0, 2))
    tm.move_token('octopus', (1, 5))
    tm.move_token('flight', (2, 7))
    tm.print_status()
    print(f"\nChase (0,2) 타겟:   {tm.get_target_position('chase')} (바로 앞 비어있음)")
    print(f"Octopus (1,5) 타겟: {tm.get_target_position('octopus')} (바로 앞 비어있음)")
    print(f"Flight (2,7) 타겟:  {tm.get_target_position('flight')} (바로 앞 비어있음)")
    
    # 잡기 시나리오 테스트
    print("\n[5단계] 잡기 조건 테스트 - 추월 전")
    print("-" * 60)
    tm.chase.move_to(0, 8)
    tm.octopus.move_to(1, 0)
    tm.flight.move_to(2, 0)
    tm.print_status()
    
    print(f"\n현재 상황:")
    print(f"  Chase (0,8), Octopus (1,0)")
    print(f"  Chase의 다음 위치: {tm.get_next_position((0,8))} = Octopus 위치")
    print(f"  → Chase가 Octopus의 다음 위치는 아님")
    print(f"\n승리? {tm.check_victory()} (예상: False)  ← 아직 추월 안 함")
    print(f"패배? {tm.check_defeat()} (예상: False)")
    
    # Chase가 타겟으로 이동 → 승리
    print("\n[6단계] Chase 이동 → 추월 성공!")
    print("-" * 60)
    chase_target = tm.get_target_position('chase')
    print(f"Chase의 타겟: {chase_target} (Octopus(1,0) 건너뛰어 그 앞)")
    tm.move_token('chase', chase_target)
    tm.print_status()
    
    print(f"\n현재 상황:")
    print(f"  Chase (1,1), Octopus (1,0)")
    print(f"  Chase = Octopus의 다음 위치 {tm.get_next_position((1,0))}")
    print(f"  → Chase가 Octopus를 추월했음!")
    print(f"\n승리? {tm.check_victory()} (예상: True)  ← 추월 성공! 🎉")
    
    # Octopus가 Flight 추월 테스트
    print("\n[7단계] Octopus → Flight 추월 테스트")
    print("-" * 60)
    tm.octopus.move_to(2, 1)
    tm.flight.move_to(2, 0)
    tm.print_status()
    
    print(f"\n현재 상황:")
    print(f"  Octopus (2,1), Flight (2,0)")
    print(f"  Octopus = Flight의 다음 위치 {tm.get_next_position((2,0))}")
    print(f"  패배? {tm.check_defeat()} (예상: True) ← 추월! 💀")
    
    # 순환 경로 추월 테스트
    print("\n[8단계] 순환 경로 추월 테스트")
    print("-" * 60)
    tm.chase.move_to(0, 0)
    tm.octopus.move_to(2, 8)
    tm.print_status()
    print(f"\n현재 상황:")
    print(f"  Chase (0,0), Octopus (2,8) - 마지막 칸")
    print(f"  Octopus의 다음 위치: {tm.get_next_position((2,8))} = (0,0)")
    print(f"  Chase = Octopus의 다음 위치")
    print(f"  승리? {tm.check_victory()} (예상: True) ← 순환 경로 추월! 🎉")
    
    print("\n" + "="*60)
    print("✓ TokenManager 모든 테스트 완료!")
    print("="*60)
