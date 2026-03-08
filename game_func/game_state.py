# game_state.py
# Chicken Task - Game State Management (게임 상태 관리)
# 모든 게임 로직 통합

import time
import random
import sys
from pathlib import Path

try:
    from game_func.board_class import ConditionBoard
    from game_func.deck_class import MainDeck
    from game_func.token_class import TokenManager
    from utils.timer import GameTimer
    from utils.card_matcher import check_match
    from ..config import TURN_TIME_LIMIT, PC_SUCCESS_RATE, PC_THINK_TIME
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from game_func.board_class import ConditionBoard
    from game_func.deck_class import MainDeck
    from game_func.token_class import TokenManager
    from utils.timer import GameTimer
    from utils.card_matcher import check_match
    from config import TURN_TIME_LIMIT, PC_SUCCESS_RATE, PC_THINK_TIME


class GameState:
    """
    게임 상태 통합 관리
    - 운동장 보드, 메인 덱, 토큰 관리
    - 게임 흐름 제어 (phase, turn)
    - 타이머 관리
    - 승리/패배 체크
    """
    
    # 게임 Phase
    PHASE_NOT_STARTED = 'not_started'
    PHASE_TOKEN_SELECTION = 'token_selection'  # Phase 0: 닭 선택
    PHASE_GAME_PLAY = 'game_play'              # Phase 1+: 게임 플레이
    PHASE_VICTORY = 'victory'
    PHASE_DEFEAT = 'defeat'
    
    # 턴 타입
    TURN_USER = 'user'
    TURN_PC = 'pc'
    
    def __init__(self):
        """게임 상태 초기화"""
        # 게임 컴포넌트
        self.board = ConditionBoard()
        self.deck = MainDeck()
        self.tokens = TokenManager()
        
        # 게임 상태
        self.phase = self.PHASE_NOT_STARTED
        self.current_turn = self.TURN_USER
        self.selected_token = None  # 'chase' 또는 'flight'
        
        # 타이머
        self.timer = GameTimer(time_limit=TURN_TIME_LIMIT)
        
        # 게임 기록
        self.turn_count = 0
        self.user_move_count = 0
        self.pc_move_count = 0
        self.trial_history = []  # 시행 결과 리스트
    
    def start_game(self):
        """게임 시작"""
        self.phase = self.PHASE_TOKEN_SELECTION
        self.current_turn = self.TURN_USER
        self.turn_count = 1
        print("게임 시작! 닭을 선택하세요 (Chase 또는 Flight)")
    
    def select_token(self, token_name):
        """
        토큰 선택 (Phase 0)
        
        Args:
            token_name (str): 'chase' 또는 'flight'
        
        Returns:
            bool: 성공 여부
        """
        if self.phase != self.PHASE_TOKEN_SELECTION:
            return False
        
        if token_name not in ['chase', 'flight']:
            return False
        
        self.selected_token = token_name
        return True
    
    def confirm_selection(self):
        """
        선택 확정 및 타이머 시작 (enter 키)
        
        Returns:
            bool: 성공 여부
        """
        if self.phase != self.PHASE_TOKEN_SELECTION:
            return False
        
        if self.selected_token is None:
            return False
        
        # 게임 플레이 단계로 전환
        self.phase = self.PHASE_GAME_PLAY
        self.timer.start()
        
        print(f"턴 {self.turn_count} 시작! 타이머: {TURN_TIME_LIMIT}초")
        return True
    
    def get_target_position(self):
        """
        현재 선택된 토큰의 타겟 위치
        
        Returns:
            tuple: (row, col) 또는 None
        """
        if self.selected_token is None:
            return None
        
        return self.tokens.get_target_position(self.selected_token)
    
    def get_target_condition(self):
        """
        현재 선택된 토큰의 타겟 조건
        
        Returns:
            dict: 조건 또는 None
        """
        target_pos = self.get_target_position()
        if target_pos is None:
            return None
        
        return self.board.get_condition(target_pos[0], target_pos[1])
    
    def user_click_card(self, card_row, card_col):
        """
        사용자가 메인 카드 클릭
        
        Args:
            card_row (int): 카드 행
            card_col (int): 카드 열
        
        Returns:
            str: 결과 ('success', 'failure', 'timeout', 'error')
        """
        if self.phase != self.PHASE_GAME_PLAY:
            return 'error'
        
        if self.current_turn != self.TURN_USER:
            return 'error'
        
        # 타이머 확인
        if self.timer.is_expired():
            print("시간 초과!")
            self.end_user_turn()
            return 'timeout'
        
        # 카드 뒤집기
        self.deck.flip_card(card_row, card_col)
        
        # 매칭 확인
        card = self.deck.get_card(card_row, card_col)
        condition = self.get_target_condition()
        is_match = check_match(condition, card)
        
        # 기록
        trial = {
            'turn': self.turn_count,
            'token': self.selected_token,
            'target_pos': self.get_target_position(),
            'condition': condition,
            'selected_card_pos': (card_row, card_col),
            'selected_card': card,
            'is_match': is_match,
            'elapsed_time': self.timer.get_elapsed()
        }
        self.trial_history.append(trial)
        
        if is_match:
            # 성공: 토큰 이동 + 타이머 리셋
            target_pos = self.get_target_position()
            self.tokens.move_token(self.selected_token, target_pos)
            self.user_move_count += 1
            
            print(f"성공! {self.selected_token}가 {target_pos}로 이동")
            
            # 승패 확인
            if self.check_game_end():
                return 'game_end'
            
            # 타이머 리셋 + 다음 시도
            self.timer.reset()
            self.phase = self.PHASE_TOKEN_SELECTION
            self.selected_token = None
            
            return 'success'
        else:
            # 실패: 턴 종료
            print("실패! 턴 종료")
            self.end_user_turn()
            return 'failure'
    
    def end_user_turn(self):
        """사용자 턴 종료 → PC 턴 시작"""
        self.timer.stop()
        self.current_turn = self.TURN_PC
        self.phase = self.PHASE_GAME_PLAY
        print("사용자 턴 종료. PC 차례")
    
    def pc_turn_step(self):
        """
        PC 턴 1회 시도
        
        Returns:
            str: 결과 ('success', 'failure')
        """
        if self.current_turn != self.TURN_PC:
            return 'error'
        
        # PC 생각 시간
        time.sleep(PC_THINK_TIME)
        
        # 타겟 확인
        target_pos = self.tokens.get_target_position('octopus')
        condition = self.board.get_condition(target_pos[0], target_pos[1])
        
        # PC 카드 선택 (60% 정답률)
        if random.random() < PC_SUCCESS_RATE:
            # 정답 선택
            selected_pos = self._pc_select_matching_card(condition)
        else:
            # 오답 선택
            selected_pos = self._pc_select_non_matching_card(condition)
        
        # 카드 뒤집기
        self.deck.flip_card(selected_pos[0], selected_pos[1])
        card = self.deck.get_card(selected_pos[0], selected_pos[1])
        
        # 매칭 확인
        is_match = check_match(condition, card)
        
        # 기록
        trial = {
            'turn': self.turn_count,
            'token': 'octopus',
            'target_pos': target_pos,
            'condition': condition,
            'selected_card_pos': selected_pos,
            'selected_card': card,
            'is_match': is_match,
            'elapsed_time': 0
        }
        self.trial_history.append(trial)
        
        if is_match:
            # 성공: 문어 이동
            self.tokens.move_token('octopus', target_pos)
            self.pc_move_count += 1
            print(f"PC 성공! Octopus가 {target_pos}로 이동")
            
            # 승패 확인
            if self.check_game_end():
                return 'game_end'
            
            return 'success'
        else:
            # 실패: PC 턴 종료
            print("PC 실패! 턴 종료")
            self.end_pc_turn()
            return 'failure'
    
    def _pc_select_matching_card(self, condition):
        """PC가 조건에 맞는 카드 선택"""
        matching = []
        for row in range(self.deck.rows):
            for col in range(self.deck.cols):
                card = self.deck.get_card(row, col)
                if check_match(condition, card):
                    matching.append((row, col))
        
        if matching:
            return random.choice(matching)
        else:
            return self._pc_select_random_card()
    
    def _pc_select_non_matching_card(self, condition):
        """PC가 조건에 맞지 않는 카드 선택"""
        non_matching = []
        for row in range(self.deck.rows):
            for col in range(self.deck.cols):
                card = self.deck.get_card(row, col)
                if not check_match(condition, card):
                    non_matching.append((row, col))
        
        if non_matching:
            return random.choice(non_matching)
        else:
            return self._pc_select_random_card()
    
    def _pc_select_random_card(self):
        """PC가 랜덤 카드 선택 (fallback)"""
        row = random.randint(0, self.deck.rows - 1)
        col = random.randint(0, self.deck.cols - 1)
        return (row, col)
    
    def end_pc_turn(self):
        """PC 턴 종료 → 사용자 턴 시작"""
        self.current_turn = self.TURN_USER
        self.phase = self.PHASE_TOKEN_SELECTION
        self.turn_count += 1
        print(f"PC 턴 종료. 사용자 차례 (턴 {self.turn_count})")
    
    def check_game_end(self):
        """
        게임 종료 조건 확인
        
        Returns:
            bool: True=게임 종료
        """
        if self.tokens.check_victory():
            self.phase = self.PHASE_VICTORY
            print("🎉 승리! Chase가 Octopus를 잡았습니다!")
            return True
        
        if self.tokens.check_defeat():
            self.phase = self.PHASE_DEFEAT
            print("💀 패배! Octopus가 Flight를 잡았습니다!")
            return True
        
        return False
    
    def update(self, current_time):
        """
        게임 상태 업데이트 (매 프레임 호출)
        
        Args:
            current_time (float): 현재 시각
        """
        # 덱 타이머 업데이트 (5초 후 자동 숨김)
        self.deck.update_timers(current_time)
        
        # 사용자 턴 타이머 확인
        if self.phase == self.PHASE_GAME_PLAY and self.current_turn == self.TURN_USER:
            if self.timer.is_expired():
                print("시간 초과! 사용자 턴 종료")
                self.end_user_turn()
    
    def reset(self):
        """게임 리셋"""
        self.board = ConditionBoard()
        self.deck = MainDeck()
        self.tokens.reset_all()
        
        self.phase = self.PHASE_NOT_STARTED
        self.current_turn = self.TURN_USER
        self.selected_token = None
        
        self.timer.stop()
        
        self.turn_count = 0
        self.user_move_count = 0
        self.pc_move_count = 0
        self.trial_history = []
        
        print("게임 리셋 완료")
    
    def get_summary(self):
        """
        게임 요약 정보
        
        Returns:
            dict: 요약 정보
        """
        return {
            'phase': self.phase,
            'turn': self.current_turn,
            'turn_count': self.turn_count,
            'user_moves': self.user_move_count,
            'pc_moves': self.pc_move_count,
            'total_trials': len(self.trial_history),
            'token_positions': self.tokens.get_all_positions()
        }


# ==================== 테스트 코드 ====================
if __name__ == "__main__":
    print("\n### GameState 테스트 ###\n")
    
    # 게임 생성
    game = GameState()
    
    # 게임 시작
    game.start_game()
    print(f"Phase: {game.phase}")
    
    # 토큰 선택
    game.select_token('chase')
    game.confirm_selection()
    print(f"Phase: {game.phase}")
    print(f"타겟 위치: {game.get_target_position()}")
    print(f"타겟 조건: {game.get_target_condition()}")
    
    # 요약 정보
    print("\n### 게임 요약 ###")
    summary = game.get_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    print("\n[OK] GameState 테스트 완료!")
