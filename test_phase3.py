#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Phase 3 통합 테스트: 기본 시각화 및 렌더링
- 우선순위 5: 옵션 설정 (set_opts/)
- 우선순위 6: 기본 렌더링 (view_func/)

테스트 항목:
1. 운동장 보드 렌더링 (condition cards)
2. 메인 덱 렌더링 (main cards)
3. 토큰 렌더링 (chase, octopus, flight)
4. UI 요소 렌더링 (타이머, 점수, 메시지, 버튼)

조작 방법:
- 마우스 좌클릭: 운동장 카드 하이라이트 / 메인 덱 카드 뒤집기
- SPACE: 모든 토큰 1칸 이동
- UP/DOWN: Chase/Flight 버튼 선택
- T: 타이머 시작/정지
- M: 메시지 표시 테스트
- R: 게임 상태 리셋
- ESC: 종료
"""

# PsychoPy 경고 메시지 억제 (폰트 로딩 경고 등)
import warnings
warnings.filterwarnings('ignore')

# PsychoPy 로거 설정 (WARNING 메시지 숨김)
from psychopy import logging
logging.console.setLevel(logging.ERROR)  # ERROR 이상만 표시

from psychopy import visual, event, core
import time

# 옵션 설정
from set_opts.set_visual_opt import set_visual_opt
from set_opts.set_device_opt import set_device_opt
from set_opts.set_game_opt import set_game_opt

# 게임 객체
from game_func.board_class import ConditionBoard
from game_func.deck_class import MainDeck
from game_func.token_class import TokenManager

# 렌더러
from view_func.board_renderer import BoardRenderer
from view_func.deck_renderer import DeckRenderer
from view_func.token_renderer import TokenRenderer
from view_func.ui_elements import UIElements

# 설정
from config import WIDTH, HEIGHT, TURN_TIME_LIMIT


class Phase3Tester:
    """Phase 3 통합 테스트 클래스"""
    
    def __init__(self):
        print("\n" + "="*60)
        print("Phase 3 통합 테스트: 기본 시각화 및 렌더링")
        print("="*60)
        
        # 옵션 설정
        self.visual_opt = set_visual_opt()
        self.device_opt = set_device_opt()
        self.game_opt = set_game_opt()
        
        # 테스트용 풀스크린 비활성화
        self.visual_opt['fullscreen'] = False
        
        print("\n[1/4] 옵션 설정 완료")
        print(f"  - 화면 크기: {self.visual_opt['win_size']}")
        print(f"  - 배경색: {self.visual_opt['bg_color']}")
        print(f"  - 마우스: {self.device_opt['use_mouse']}")
        print(f"  - 턴 제한: {self.game_opt['turn_time_limit']}초")
        
        # PsychoPy 윈도우 생성 (화면 중앙 배치)
        self.win = visual.Window(
            size=self.visual_opt['win_size'],
            color=self.visual_opt['bg_color'],
            fullscr=self.visual_opt['fullscreen'],
            units=self.visual_opt['units'],
            colorSpace=self.visual_opt['color_space'],
            allowGUI=True,
            pos=self.visual_opt.get('pos'),
            screen=self.visual_opt.get('screen', 0)
        )
        
        # 마우스
        self.mouse = event.Mouse(win=self.win, visible=self.device_opt['mouse_visible'])
        
        print("\n[2/4] PsychoPy 윈도우 생성 완료")
        
        # 게임 객체 생성
        self.board = ConditionBoard()
        self.deck = MainDeck()
        self.token_manager = TokenManager()
        
        print("\n[3/4] 게임 객체 생성 완료")
        print(f"  - 운동장 보드: {self.board.rows}행 × {self.board.cols}열")
        print(f"  - 메인 덱: {len(self.deck.cards)}장")
        print(f"  - 토큰: Chase, Octopus, Flight")
        
        # 렌더러 생성
        self.board_renderer = BoardRenderer(self.win, self.board)
        self.deck_renderer = DeckRenderer(self.win, self.deck)
        self.token_renderer = TokenRenderer(self.win, self.token_manager)
        self.ui = UIElements(self.win)
        
        print("\n[4/4] 렌더러 생성 완료")
        print("  - BoardRenderer (운동장 보드)")
        print("  - DeckRenderer (메인 덱)")
        print("  - TokenRenderer (토큰)")
        print("  - UIElements (UI 요소)")
        
        # 테스트 상태
        self.highlighted_board_pos = None
        self.highlighted_deck_pos = None
        self.selected_token = None
        self.user_score = 0
        self.pc_score = 0
        self.timer_running = False
        self.timer_start = None
        self.remaining_time = TURN_TIME_LIMIT
        self.show_message = False
        self.message_text = ""
        self.current_turn = 'user'
        
        print("\n" + "="*60)
        print("테스트 시작!")
        print("="*60)
        self._print_instructions()
    
    def _print_instructions(self):
        """조작 방법 출력"""
        print("\n[조작 방법]")
        print("  마우스 좌클릭: 카드 선택/뒤집기")
        print("  SPACE: 모든 토큰 1칸 이동")
        print("  UP/DOWN: Chase/Flight 버튼 선택")
        print("  T: 타이머 시작/정지")
        print("  M: 메시지 표시 테스트")
        print("  R: 게임 상태 리셋")
        print("  S: 점수 증가 테스트")
        print("  ESC: 종료")
        print()
    
    def _get_time_string(self):
        """타이머 문자열 생성"""
        if self.timer_running and self.timer_start:
            elapsed = time.time() - self.timer_start
            self.remaining_time = max(0, TURN_TIME_LIMIT - elapsed)
        
        minutes = int(self.remaining_time // 60)
        seconds = int(self.remaining_time % 60)
        return f"{minutes:02d}:{seconds:02d}"
    
    def _handle_mouse_click(self):
        """마우스 클릭 처리"""
        if self.mouse.getPressed()[0]:
            mouse_pos = self.mouse.getPos()
            
            # 운동장 보드 클릭 체크
            board_pos = self.board_renderer.get_clicked_position(mouse_pos)
            if board_pos:
                self.highlighted_board_pos = board_pos
                condition = self.board.get_condition(board_pos[0], board_pos[1])
                print(f"[Board] 클릭: {board_pos}, 조건: {condition}")
                core.wait(0.2)  # 더블 클릭 방지
                return
            
            # 메인 덱 클릭 체크
            deck_pos = self.deck_renderer.get_clicked_position(mouse_pos)
            if deck_pos:
                self.highlighted_deck_pos = deck_pos
                
                # 카드 뒤집기
                if self.deck.is_face_up(deck_pos[0], deck_pos[1]):
                    self.deck.hide_card(deck_pos[0], deck_pos[1])
                    print(f"[Deck] 카드 {deck_pos} 뒷면으로")
                else:
                    self.deck.flip_card(deck_pos[0], deck_pos[1])
                    card = self.deck.get_card(deck_pos[0], deck_pos[1])
                    print(f"[Deck] 카드 {deck_pos} 앞면으로: {card}")
                
                core.wait(0.2)
                return
            
            # 토큰 버튼 클릭 체크
            hovered_button = self.ui.get_hovered_button(mouse_pos)
            if hovered_button:
                self.selected_token = hovered_button
                print(f"[UI] 버튼 선택: {hovered_button}")
                core.wait(0.2)
    
    def _handle_keyboard(self):
        """키보드 입력 처리"""
        keys = event.getKeys(['escape', 'space', 'up', 'down', 't', 'm', 'r', 's'])
        
        if 'escape' in keys:
            return False  # 종료
        
        if 'space' in keys:
            # 모든 토큰 이동
            self.token_manager.move_all_tokens()
            print("[Token] 모든 토큰 1칸 이동")
            self.token_manager.print_status()
            
            # 승패 체크
            if self.token_manager.check_victory():
                print("🎉 승리! Chase가 Octopus를 잡았습니다!")
                self.show_message = True
                self.message_text = "승리! Chase가 Octopus를 잡았습니다!"
            elif self.token_manager.check_defeat():
                print("😢 패배! Octopus가 Flight를 잡았습니다!")
                self.show_message = True
                self.message_text = "패배! Octopus가 Flight를 잡았습니다!"
        
        if 'up' in keys:
            self.selected_token = 'chase'
            print("[UI] Chase 버튼 선택")
        
        if 'down' in keys:
            self.selected_token = 'flight'
            print("[UI] Flight 버튼 선택")
        
        if 't' in keys:
            # 타이머 토글
            if self.timer_running:
                self.timer_running = False
                print("[Timer] 타이머 정지")
            else:
                self.timer_running = True
                self.timer_start = time.time()
                self.remaining_time = TURN_TIME_LIMIT
                print("[Timer] 타이머 시작")
        
        if 'm' in keys:
            # 메시지 토글
            self.show_message = not self.show_message
            if self.show_message:
                self.message_text = "테스트 메시지입니다!"
                print("[UI] 메시지 표시")
            else:
                print("[UI] 메시지 숨김")
        
        if 'r' in keys:
            # 리셋
            self.board = ConditionBoard()
            self.deck = MainDeck()
            self.token_manager = TokenManager()
            
            self.board_renderer = BoardRenderer(self.win, self.board)
            self.deck_renderer = DeckRenderer(self.win, self.deck)
            self.token_renderer = TokenRenderer(self.win, self.token_manager)
            
            self.highlighted_board_pos = None
            self.highlighted_deck_pos = None
            self.selected_token = None
            self.user_score = 0
            self.pc_score = 0
            self.timer_running = False
            self.remaining_time = TURN_TIME_LIMIT
            self.show_message = False
            
            print("\n[Reset] 게임 상태 리셋 완료\n")
        
        if 's' in keys:
            # 점수 증가 테스트
            if self.current_turn == 'user':
                self.user_score += 1
                self.current_turn = 'pc'
            else:
                self.pc_score += 1
                self.current_turn = 'user'
            print(f"[Score] 유저: {self.user_score}, PC: {self.pc_score}")
        
        return True  # 계속
    
    def _render_frame(self):
        """한 프레임 렌더링"""
        # 배경 클리어
        self.win.clearBuffer()
        
        # 1. 페이즈 제목
        self.ui.draw_phase_title("Phase 3: 기본 시각화 테스트")
        
        # 2. 타이머
        time_str = self._get_time_string()
        self.ui.draw_timer(time_str)
        
        # 3. 점수
        self.ui.draw_score(self.user_score, self.pc_score)
        
        # 4. 턴 표시
        self.ui.draw_turn_indicator(self.current_turn)
        
        # 5. 운동장 보드
        self.board_renderer.draw(highlighted_pos=self.highlighted_board_pos)
        
        # 6. 메인 덱
        self.deck_renderer.draw(highlighted_pos=self.highlighted_deck_pos)
        
        # 7. 토큰
        self.token_renderer.draw()
        
        # 8. 메시지 (선택적)
        if self.show_message:
            self.ui.draw_message(self.message_text)
        
        # 9. 안내 문구
        instruction = "마우스: 클릭 | SPACE: 토큰이동 | T: 타이머 | M: 메시지 | S: 점수 | R: 리셋 | ESC: 종료"
        self.ui.draw_instruction(instruction)
        
        # 10. 토큰 버튼 (하단에 작게 표시)
        mouse_pos = self.mouse.getPos()
        hovered_button = self.ui.get_hovered_button(mouse_pos)
        # 버튼은 필요할 때만 그리도록 (여기선 생략 가능)
        
        # 화면 업데이트
        self.win.flip()
    
    def run(self):
        """테스트 메인 루프"""
        try:
            while True:
                # 키보드 입력 처리
                if not self._handle_keyboard():
                    break
                
                # 마우스 클릭 처리
                self._handle_mouse_click()
                
                # 화면 렌더링
                self._render_frame()
                
                # 타이머 종료 체크
                if self.timer_running and self.remaining_time <= 0:
                    self.timer_running = False
                    self.show_message = True
                    self.message_text = "시간 초과!"
                    print("[Timer] 시간 초과!")
        
        except KeyboardInterrupt:
            print("\n\n[중단] 사용자가 테스트를 중단했습니다.")
        
        finally:
            self._cleanup()
    
    def _cleanup(self):
        """정리 작업"""
        print("\n" + "="*60)
        print("테스트 종료")
        print("="*60)
        print("\n[결과 요약]")
        print(f"  최종 점수: 유저 {self.user_score}점 | PC {self.pc_score}점")
        print(f"  토큰 위치:")
        print(f"    - Chase: {self.token_manager.get_token('chase').get_position()}")
        print(f"    - Octopus: {self.token_manager.get_token('octopus').get_position()}")
        print(f"    - Flight: {self.token_manager.get_token('flight').get_position()}")
        print()
        
        self.win.close()
        core.quit()


def main():
    """메인 함수"""
    tester = Phase3Tester()
    tester.run()


if __name__ == "__main__":
    main()
