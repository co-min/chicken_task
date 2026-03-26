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
    MESSAGE_Y_OFFSET,
    CHASE_BUTTON_POS, FLIGHT_BUTTON_POS, TOKEN_BUTTON_LINE_WIDTH,PURPLE,WHITE,
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
        self.start_cue_background = None
        self.start_cue_text = None
        self.token_choice_buttons = {}
        
        self._create_ui_elements()
        self._user_message_height = self.message_text.height
        self._user_instruction_height = self.instruction_text.height
        self._pc_text_scale = 0.8
    
    def _create_ui_elements(self):
        """모든 UI 요소 생성"""
        message_base_y = -360 + MESSAGE_Y_OFFSET

        # 타이머 (상단 중앙) - 화면에 맞춤
        self.timer_text = visual.TextStim(
            win=self.win,
            text="00:15",
            pos=(0, HEIGHT / 2 - 40),
            height=45,
            color=TEXT_COLOR,
            colorSpace='rgb255',
            bold=True
        )
        
        # 점수 (상단 왼쪽)
        self.score_text = visual.TextStim(
            win=self.win,
            text="점수: 0",
            pos=(-WIDTH / 2 + 200, HEIGHT / 2 - 100),
            height=30,
            color=TEXT_COLOR,
            colorSpace='rgb255'
        )
        
        # 메시지 (화면 중앙)
        self.message_text = visual.TextStim(
            win=self.win,
            text="",
            pos=(0, message_base_y),
            height=24,
            color=[255, 255, 0],  # 노란색 (강조)
            colorSpace='rgb255',
            bold=True
        )

        self.start_cue_background = visual.Rect(
            win=self.win,
            width=320,
            height=160,
            pos=(0, 0),
            fillColor=WHITE,
            lineColor=WHITE,
            colorSpace='rgb255'
        )

        self.start_cue_text = visual.TextStim(
            win=self.win,
            text="",
            pos=(0, 0),
            height=90,
            color=PURPLE,
            colorSpace='rgb255',
            bold=True
        )
        
        # 안내 문구 (하단)
        instruction_gap = 14
        instruction_y = message_base_y - (self.message_text.height / 2) - instruction_gap - (25 / 2) - 60
        self.instruction_text = visual.TextStim(
            win=self.win,
            text="",
            pos=(0, instruction_y),
            height=25,
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
        self.score_text.text = f"내 점수: {user_score}점 | 문어 점수: {pc_score}점"
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

    def draw_start_cue(self, message="시작!"):
        """화면 중앙에 큰 시작 신호를 표시"""
        self.start_cue_text.text = message
        self.start_cue_background.draw()
        self.start_cue_text.draw()

    def set_user_turn_hud(self, selected_token, turn_count, timer_display_text):
        """사용자 턴 HUD 텍스트/색상 갱신"""
        self.message_text.height = self._user_message_height
        self.instruction_text.height = self._user_instruction_height
        self.message_text.text = selected_token.upper()
        self.message_text.color = TEXT_COLOR
        self.timer_text.text = timer_display_text

    def set_pc_turn_hud(self, turn_count, target_pos, timer_label="문어 턴"):
        """PC 턴 HUD 텍스트/색상 갱신"""
        self.message_text.height = self._user_message_height * self._pc_text_scale
        self.instruction_text.height = self._user_instruction_height * self._pc_text_scale
        self.message_text.text = ""
        self.message_text.color = TEXT_COLOR
        self.timer_text.text = ""
    
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
            pos=(WIDTH / 2 - 120, HEIGHT / 2 - 30),
            height=20,
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


