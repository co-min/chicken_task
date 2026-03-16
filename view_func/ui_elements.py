# view_func/ui_elements.py
# UI 요소 렌더링 (타이머, 점수, 텍스트, 버튼 등)

from psychopy import visual
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(__file__, '..', '..')))
from config import (
    WIDTH, HEIGHT,
    TEXT_COLOR, TEXT_SIZE,
    BUTTON_COLOR_NORMAL, BUTTON_COLOR_HOVER, BUTTON_COLOR_SELECTED,
    TOKEN_BUTTON_WIDTH, TOKEN_BUTTON_HEIGHT, TOKEN_BUTTON_TEXT_HEIGHT,
    CHASE_BUTTON_POS, FLIGHT_BUTTON_POS, TOKEN_BUTTON_LINE_WIDTH
)


class UIElements:
    """게임 UI 요소를 관리하는 클래스"""
    
    def __init__(self, win):
        """
        Args:
            win: PsychoPy window 객체
        """
        self.win = win
        
        # UI 요소들
        self.timer_text = None
        self.score_text = None
        self.message_text = None
        self.instruction_text = None
        self.token_choice_buttons = {}
        
        self._create_ui_elements()
    
    def _create_ui_elements(self):
        """모든 UI 요소 생성"""
        # 타이머 (상단 중앙) - 화면에 맞춤
        self.timer_text = visual.TextStim(
            win=self.win,
            text="00:15",
            pos=(0, HEIGHT / 2 - 100),
            height=50,
            color=TEXT_COLOR,
            colorSpace='rgb255',
            bold=True
        )
        
        # 점수 (상단 왼쪽)
        self.score_text = visual.TextStim(
            win=self.win,
            text="점수: 0",
            pos=(-WIDTH / 2 + 200, HEIGHT / 2 - 100),
            height=38,
            color=TEXT_COLOR,
            colorSpace='rgb255'
        )
        
        # 메시지 (화면 중앙)
        self.message_text = visual.TextStim(
            win=self.win,
            text="",
            pos=(0, -300),
            height=24,
            color=[255, 255, 0],  # 노란색 (강조)
            colorSpace='rgb255',
            bold=True
        )
        
        # 안내 문구 (하단)
        self.instruction_text = visual.TextStim(
            win=self.win,
            text="",
            pos=(0, -HEIGHT / 2 + 120),
            height=30,
            color=TEXT_COLOR,
            colorSpace='rgb255'
        )
        
        # 토큰 선택 버튼들 (Chase / Flight)
        # Chase 버튼 (왼쪽)
        self.token_choice_buttons['chase'] = {
            'rect': visual.Rect(
                win=self.win,
                width=TOKEN_BUTTON_WIDTH,
                height=TOKEN_BUTTON_HEIGHT,
                pos=CHASE_BUTTON_POS,
                fillColor=BUTTON_COLOR_NORMAL,
                lineColor=[255, 255, 255],
                lineWidth=TOKEN_BUTTON_LINE_WIDTH,
                colorSpace='rgb255'
            ),
            'text': visual.TextStim(
                win=self.win,
                text="CHASE\n(문어를 쫓는 닭)",
                pos=CHASE_BUTTON_POS,
                height=TOKEN_BUTTON_TEXT_HEIGHT,
                color=[255, 255, 255],
                colorSpace='rgb255'
            )
        }
        
        # Flight 버튼 (오른쪽)
        self.token_choice_buttons['flight'] = {
            'rect': visual.Rect(
                win=self.win,
                width=TOKEN_BUTTON_WIDTH,
                height=TOKEN_BUTTON_HEIGHT,
                pos=FLIGHT_BUTTON_POS,
                fillColor=BUTTON_COLOR_NORMAL,
                lineColor=[255, 255, 255],
                lineWidth=TOKEN_BUTTON_LINE_WIDTH,
                colorSpace='rgb255'
            ),
            'text': visual.TextStim(
                win=self.win,
                text="FLIGHT\n(도망치는 닭)",
                pos=FLIGHT_BUTTON_POS,
                height=TOKEN_BUTTON_TEXT_HEIGHT,
                color=[255, 255, 255],
                colorSpace='rgb255'
            )
        }
    
    def draw_timer(self, time_str):
        """
        타이머 표시
        
        Args:
            time_str: 시간 문자열 (예: "00:15")
        """
        self.timer_text.text = time_str
        self.timer_text.draw()
    
    def draw_score(self, user_score, pc_score):
        """
        점수 표시
        
        Args:
            user_score: 유저 점수
            pc_score: PC 점수
        """
        self.score_text.text = f"유저: {user_score}점 | PC: {pc_score}점"
        self.score_text.draw()
    
    def draw_message(self, message):
        """
        화면 중앙에 메시지 표시
        
        Args:
            message: 표시할 메시지
        """
        if message:
            self.message_text.text = message
            self.message_text.draw()
    
    def draw_instruction(self, instruction):
        """
        하단에 안내 문구 표시
        
        Args:
            instruction: 안내 문구
        """
        if instruction:
            self.instruction_text.text = instruction
            self.instruction_text.draw()
    
    def draw_token_choice_buttons(self, hovered=None, selected=None):
        """
        토큰 선택 버튼 그리기
        
        Args:
            hovered: 마우스가 올려진 버튼 ('chase' 또는 'flight')
            selected: 선택된 버튼 ('chase' 또는 'flight')
        """
        for token_name, button in self.token_choice_buttons.items():
            # 버튼 색상 결정
            if selected == token_name:
                button['rect'].fillColor = BUTTON_COLOR_SELECTED
            elif hovered == token_name:
                button['rect'].fillColor = BUTTON_COLOR_HOVER
            else:
                button['rect'].fillColor = BUTTON_COLOR_NORMAL
            
            button['rect'].draw()
            button['text'].draw()
    
    def get_hovered_button(self, mouse_pos):
        """
        마우스가 올려진 버튼 확인
        
        Args:
            mouse_pos: (x, y) 마우스 좌표
        
        Returns:
            'chase', 'flight', 또는 None
        """
        for token_name, button in self.token_choice_buttons.items():
            if button['rect'].contains(mouse_pos):
                return token_name
        return None
    
    def draw_turn_indicator(self, turn):
        """
        현재 턴 표시 (상단 오른쪽)
        
        Args:
            turn: 'user' 또는 'pc'
        """
        turn_text = visual.TextStim(
            win=self.win,
            text=f"{'사용자' if turn == 'user' else '문어'} 턴",
            pos=(WIDTH / 2 - 120, HEIGHT / 2 - 70),
            height=30,
            color=[255, 200, 0] if turn == 'user' else [200, 0, 255],
            colorSpace='rgb255',
            bold=True
        )
        turn_text.draw()
    
    def draw_phase_title(self, phase_name):
        """
        페이즈 제목 표시 (상단)
        
        Args:
            phase_name: 페이즈 이름
        """
        phase_text = visual.TextStim(
            win=self.win,
            text=phase_name,
            pos=(0, HEIGHT / 2 - 35),
            height=36,
            color=TEXT_COLOR,
            colorSpace='rgb255',
            bold=True
        )
        phase_text.draw()


# 테스트 코드
if __name__ == "__main__":
    # 경고 억제
    import warnings
    warnings.filterwarnings('ignore')
    from psychopy import logging
    logging.console.setLevel(logging.ERROR)
    
    from psychopy import core
    from set_opts.set_visual_opt import set_visual_opt
    import time
    
    print("\n### UIElements 테스트 ###\n")
    
    # 윈도우 생성
    visual_opt = set_visual_opt()
    visual_opt['fullscreen'] = False
    
    win = visual.Window(
        size=visual_opt['win_size'],
        color=visual_opt['bg_color'],
        fullscr=visual_opt['fullscreen'],
        units=visual_opt['units'],
        colorSpace=visual_opt['color_space'],
        allowGUI=True,
        pos=visual_opt.get('pos'),
        screen=visual_opt.get('screen', 0)
    )
    
    # UI 요소 생성
    ui = UIElements(win)
    
    # 마우스 생성
    mouse = visual.event.Mouse(win=win)
    
    print("렌더링 시작...")
    print("마우스를 버튼에 올리거나 클릭하세요.")
    print("ESC 키를 눌러 종료하세요.\n")
    
    # 테스트 변수
    score = 0
    start_time = time.time()
    selected_token = None
    
    # 메인 루프
    while True:
        # 키보드 체크
        keys = visual.event.getKeys(['escape'])
        if 'escape' in keys:
            break
        
        # 타이머 계산
        elapsed = time.time() - start_time
        remaining = max(0, 15 - elapsed)
        time_str = f"{int(remaining // 60):02d}:{int(remaining % 60):02d}"
        
        # 마우스 위치 체크
        mouse_pos = mouse.getPos()
        hovered = ui.get_hovered_button(mouse_pos)
        
        # 마우스 클릭 체크
        if mouse.getPressed()[0] and hovered:
            selected_token = hovered
            print(f"선택: {selected_token}")
            core.wait(0.2)  # 더블 클릭 방지
        
        # UI 그리기
        ui.draw_phase_title("토큰 선택 단계")
        ui.draw_timer(time_str)
        ui.draw_score(score, 0)
        ui.draw_turn_indicator('user')
        ui.draw_instruction("왼쪽 또는 오른쪽 닭을 선택하세요 (ESC: 종료)")
        
        if selected_token:
            ui.draw_message(f"{selected_token.upper()} 선택됨!")
        
        ui.draw_token_choice_buttons(hovered=hovered, selected=selected_token)
        
        win.flip()
    
    win.close()
    core.quit()
    
    print("\n[OK] UIElements 테스트 완료!")
