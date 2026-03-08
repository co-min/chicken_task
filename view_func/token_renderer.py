# view_func/token_renderer.py
# 토큰(Chase, Octopus, Flight) 렌더링

from psychopy import visual
import os
from config import (
    BOARD_LEFT_MARGIN, BOARD_TOP_MARGIN,
    BOARD_CARD_WIDTH, BOARD_CARD_HEIGHT, BOARD_CARD_SPACING,
    WIDTH, HEIGHT,
    TOKEN_SIZE
)

# 이미지 경로
STIMULI_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'stimuli')
TOKENS_DIR = os.path.join(STIMULI_DIR, 'tokens')


class TokenRenderer:
    """3개 토큰(Chase, Octopus, Flight)을 화면에 렌더링하는 클래스"""
    
    def __init__(self, win, token_manager):
        """
        Args:
            win: PsychoPy window 객체
            token_manager: TokenManager 인스턴스
        """
        self.win = win
        self.token_manager = token_manager
        
        # 토큰 비주얼 요소
        self.chase_stim = None
        self.octopus_stim = None
        self.flight_stim = None
        
        self._create_visuals()
    
    def _create_visuals(self):
        """토큰 비주얼 생성"""
        # Chase (위쪽 닭) - 이미지
        self.chase_stim = visual.ImageStim(
            win=self.win,
            image=os.path.join(TOKENS_DIR, 'chase.png'),
            size=(TOKEN_SIZE, TOKEN_SIZE)
        )
        
        # Octopus (PC 문어) - 이미지
        self.octopus_stim = visual.ImageStim(
            win=self.win,
            image=os.path.join(TOKENS_DIR, 'octopus.png'),
            size=(TOKEN_SIZE, TOKEN_SIZE)
        )
        
        # Flight (아래쪽 닭) - 이미지
        self.flight_stim = visual.ImageStim(
            win=self.win,
            image=os.path.join(TOKENS_DIR, 'flight.png'),
            size=(TOKEN_SIZE, TOKEN_SIZE)
        )
    
    def _get_card_center(self, row, col):
        """
        특정 카드 위치의 중심 좌표 반환
        
        Args:
            row, col: 카드 위치
        
        Returns:
            (x, y) 좌표 (PsychoPy 좌표계)
        """
        left_x = BOARD_LEFT_MARGIN + col * (BOARD_CARD_WIDTH + BOARD_CARD_SPACING)
        center_x = left_x + BOARD_CARD_WIDTH / 2
        x = center_x - WIDTH / 2
        
        top_y = BOARD_TOP_MARGIN + row * (BOARD_CARD_HEIGHT + BOARD_CARD_SPACING)
        center_y = top_y + BOARD_CARD_HEIGHT / 2
        y = HEIGHT / 2 - center_y
        
        return (x, y)
    
    def draw(self):
        """토큰들을 화면에 그리기"""
        # 각 토큰의 현재 위치 가져오기
        chase_pos = self.token_manager.get_token('chase').get_position()
        octopus_pos = self.token_manager.get_token('octopus').get_position()
        flight_pos = self.token_manager.get_token('flight').get_position()
        
        # Chase 그리기
        if chase_pos:
            x, y = self._get_card_center(chase_pos[0], chase_pos[1])
            self.chase_stim.pos = (x, y)
            self.chase_stim.draw()
        
        # Octopus 그리기
        if octopus_pos:
            x, y = self._get_card_center(octopus_pos[0], octopus_pos[1])
            self.octopus_stim.pos = (x, y)
            self.octopus_stim.draw()
        
        # Flight 그리기
        if flight_pos:
            x, y = self._get_card_center(flight_pos[0], flight_pos[1])
            self.flight_stim.pos = (x, y)
            self.flight_stim.draw()
    
    def draw_with_animation(self, progress=1.0):
        """
        애니메이션 진행률에 따라 그리기
        
        Args:
            progress: 0.0 (시작) ~ 1.0 (완료)
                      향후 애니메이션 구현 시 사용
        """
        # 현재는 일반 draw()와 동일 (향후 확장 가능)
        self.draw()


# 테스트 코드
if __name__ == "__main__":
    # 경고 억제
    import warnings
    warnings.filterwarnings('ignore')
    from psychopy import logging
    logging.console.setLevel(logging.ERROR)
    
    from psychopy import core
    from game_func.token_class import TokenManager
    from game_func.board_class import ConditionBoard
    from view_func.board_renderer import BoardRenderer
    from set_opts.set_visual_opt import set_visual_opt
    
    print("\n### TokenRenderer 테스트 ###\n")
    
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
    
    # 보드 및 토큰 생성
    board = ConditionBoard()
    token_manager = TokenManager()
    
    # 렌더러 생성
    board_renderer = BoardRenderer(win, board)
    token_renderer = TokenRenderer(win, token_manager)
    
    # 타이틀
    title = visual.TextStim(
        win=win,
        text="토큰 렌더링 (SPACE로 이동, ESC로 종료)",
        pos=(0, HEIGHT / 2 - 70),
        height=40,
        color=[255, 255, 255],
        colorSpace='rgb255'
    )
    
    # 상태 텍스트
    status_text = visual.TextStim(
        win=win,
        text="",
        pos=(0, HEIGHT / 2 - 125),
        height=32,
        color=[255, 255, 255],
        colorSpace='rgb255'
    )
    
    print("렌더링 시작...")
    print("SPACE 키를 눌러 토큰을 이동시키세요.")
    print("ESC 키를 눌러 종료하세요.\n")
    
    # 초기 상태 출력
    token_manager.print_status()
    
    # 메인 루프
    move_count = 0
    
    while True:
        # 키보드 체크
        keys = visual.event.getKeys(['escape', 'space'])
        
        if 'escape' in keys:
            break
        
        if 'space' in keys:
            # 모든 토큰 이동
            token_manager.move_all_tokens()
            move_count += 1
            
            print(f"\n=== 이동 {move_count}회 ===")
            token_manager.print_status()
            
            # 게임 종료 체크
            if token_manager.check_victory():
                print("🎉 승리! Chase가 Octopus를 잡았습니다!")
            elif token_manager.check_defeat():
                print("😢 패배! Octopus가 Flight를 잡았습니다!")
        
        # 상태 텍스트 업데이트
        chase_pos = token_manager.get_token('chase').get_position()
        octopus_pos = token_manager.get_token('octopus').get_position()
        flight_pos = token_manager.get_token('flight').get_position()
        
        status_text.text = f"Chase: {chase_pos} | Octopus: {octopus_pos} | Flight: {flight_pos}"
        
        # 화면 그리기
        title.draw()
        status_text.draw()
        board_renderer.draw(highlighted_pos=None)
        token_renderer.draw()
        win.flip()
    
    win.close()
    core.quit()
    
    print("\n[OK] TokenRenderer 테스트 완료!")
