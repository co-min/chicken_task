# 연습 게임 (Practice Game)
# 본 게임 전 규칙을 익히기 위한 간단한 연습 모드
#
# 흐름:
#   1. 안내 화면
#   2. 일반 연습 (PRACTICE_TRIALS 회): 닭 선택 → 카드 1장 선택 → 피드백
#   3. [PRACTICE_SEQ_TRIALS > 0] 순서 기억 연습 안내
#   4. 순서 기억 연습 (PRACTICE_SEQ_TRIALS 회): 닭 선택 → 카드 N장 순서대로 선택 → 피드백
#   5. 완료 화면

import sys
from pathlib import Path
from psychopy import visual, core, event

try:
    from ..config import (
        KEY_EXIT, TEXT_COLOR, TEXT_SIZE,
        CARD_FLIP_DURATION, FEEDBACK_DURATION, TRIAL_INTERVAL,
        WIDTH, HEIGHT,
        DECK_LEFT_EDGE, BOARD_DECK_TOP_MARGIN,
        DECK_CARD_WIDTH, DECK_CARD_HEIGHT, DECK_CARD_SPACING,
        BUTTON_COLOR_NORMAL, BUTTON_COLOR_SELECTED,
        CHASE_BUTTON_POS, FLIGHT_BUTTON_POS,
        TOKEN_BUTTON_WIDTH, TOKEN_BUTTON_HEIGHT,
        PURPLE, DARK_GREY, GOLD, WHITE,
        PRACTICE_TRIALS, PRACTICE_SEQ_TRIALS, PRACTICE_SEQ_STEPS,
    )
    from ..view_func.frame_marker import blink_frame_marker, trigger_frame_marker
    from ..sounds import load_sounds, play as sound_play
    from ..utils.timer import checked_wait
    from ..utils.card_matcher import check_match
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from config import (
        KEY_EXIT, TEXT_COLOR, TEXT_SIZE,
        CARD_FLIP_DURATION, FEEDBACK_DURATION, TRIAL_INTERVAL,
        WIDTH, HEIGHT,
        DECK_LEFT_EDGE, BOARD_DECK_TOP_MARGIN,
        DECK_CARD_WIDTH, DECK_CARD_HEIGHT, DECK_CARD_SPACING,
        BUTTON_COLOR_NORMAL, BUTTON_COLOR_SELECTED,
        CHASE_BUTTON_POS, FLIGHT_BUTTON_POS,
        TOKEN_BUTTON_WIDTH, TOKEN_BUTTON_HEIGHT,
        PURPLE, DARK_GREY, GOLD, WHITE,
        PRACTICE_TRIALS, PRACTICE_SEQ_TRIALS, PRACTICE_SEQ_STEPS,
    )
    from view_func.frame_marker import blink_frame_marker, trigger_frame_marker
    from sounds import load_sounds, play as sound_play
    from utils.timer import checked_wait
    from utils.card_matcher import check_match


# ==================== 내부 헬퍼 ====================

def _reset_for_next_trial(game_state):
    """
    한 시행이 끝난 후 다음 시행을 위해 game_state를 안전하게 초기화.

    문제: user_click_card 실패/타임아웃 시 end_user_turn()이 내부 호출되어
         current_turn = TURN_PC 로 바뀐다. 이 상태로 다음 시행을 시작하면
         user_click_card가 'error'를 반환해 두 번째 시행부터 동작하지 않는다.
    해결: 시행 종료마다 current_turn을 TURN_USER 로 강제 복원.
    """
    game_state.selected_token = None
    game_state.current_turn   = game_state.TURN_USER
    game_state.phase          = game_state.PHASE_TOKEN_SELECTION
    game_state.timer.stop()
    game_state.deactivate_seq_memory()


def _is_over_button(mouse_pos, button_pos):
    """마우스가 버튼 위에 있는지 확인."""
    left   = button_pos[0] - TOKEN_BUTTON_WIDTH  / 2
    right  = button_pos[0] + TOKEN_BUTTON_WIDTH  / 2
    top    = button_pos[1] + TOKEN_BUTTON_HEIGHT / 2
    bottom = button_pos[1] - TOKEN_BUTTON_HEIGHT / 2
    return left <= mouse_pos[0] <= right and bottom <= mouse_pos[1] <= top


def _get_clicked_card(mouse_pos, deck_rows, deck_cols):
    """마우스 클릭 위치에서 덱 카드 (row, col) 반환. 없으면 None."""
    screen_x = mouse_pos[0] + WIDTH / 2
    screen_y = HEIGHT / 2 - mouse_pos[1]
    for row in range(deck_rows):
        for col in range(deck_cols):
            left   = DECK_LEFT_EDGE + col * (DECK_CARD_WIDTH  + DECK_CARD_SPACING)
            right  = left + DECK_CARD_WIDTH
            top    = BOARD_DECK_TOP_MARGIN + row * (DECK_CARD_HEIGHT + DECK_CARD_SPACING)
            bottom = top + DECK_CARD_HEIGHT
            if left <= screen_x <= right and top <= screen_y <= bottom:
                return (row, col)
    return None


def _find_correct_card(game_state, target_pos=None):
    """
    target_pos(보드 위치)의 조건과 일치하는 덱 카드 위치를 반환.
    target_pos=None이면 현재 선택 토큰의 타겟 위치를 사용.
    없으면 None.
    """
    if target_pos is None:
        condition = game_state.get_target_condition()
    else:
        condition = game_state.board.get_condition(target_pos[0], target_pos[1])
    if condition is None:
        return None
    deck = game_state.deck
    for row in range(deck.rows):
        for col in range(deck.cols):
            card = deck.get_card(row, col)
            if card and check_match(condition, card):
                return (row, col)
    return None


# ==================== 화면 렌더링 ====================

def _draw_game_screen(win, ui_elements, board_renderer, deck_renderer,
                      token_renderer, game_state, target_pos,
                      seq_cells=None, done_cells=None,
                      hint_pos=None, draw_message=False):
    """
    연습 게임 공통 화면 렌더러.

    Args:
        seq_cells  : 순서 기억 모드에서 전체 타겟 목록 [(row,col), ...]
        done_cells : 이미 완료된 타겟 목록
        hint_pos   : 금색 테두리로 강조할 덱 카드 위치
        draw_message: True면 message_text를 어두운 배경 위에 그린다
    """
    board_renderer.draw(target_pos, seq_cells=seq_cells, done_cells=done_cells)
    deck_renderer.draw()

    if hint_pos is not None:
        _draw_hint_highlight(win, hint_pos)

    token_renderer.draw()
    ui_elements.timer_text.draw()
    ui_elements.score_text.draw()
    ui_elements.instruction_text.draw()
    ui_elements.update_ranking(game_state.user_score, game_state.pc_score)
    ui_elements.draw_ranking()

    if draw_message:
        msg_pos = ui_elements.message_text.pos
        bg = visual.Rect(
            win=win, width=520, height=52,
            pos=msg_pos,
            fillColor=[20, 20, 20], lineColor=[80, 80, 80],
            lineWidth=1, colorSpace='rgb255',
        )
        bg.draw()
        ui_elements.message_text.draw()


def _draw_hint_highlight(win, hint_pos):
    """정답 카드 위치에 금색 테두리 오버레이를 그린다."""
    row, col = hint_pos
    left = DECK_LEFT_EDGE + col * (DECK_CARD_WIDTH  + DECK_CARD_SPACING)
    top  = BOARD_DECK_TOP_MARGIN + row * (DECK_CARD_HEIGHT + DECK_CARD_SPACING)
    cx = left + DECK_CARD_WIDTH  / 2 - WIDTH  / 2
    cy = HEIGHT / 2 - (top + DECK_CARD_HEIGHT / 2)
    visual.Rect(
        win=win,
        width=DECK_CARD_WIDTH + 8, height=DECK_CARD_HEIGHT + 8,
        pos=(cx, cy),
        lineColor=GOLD, fillColor=None,
        lineWidth=5, colorSpace='rgb255', units='pix',
    ).draw()


def _show_feedback(win, ui_elements, board_renderer, deck_renderer,
                   token_renderer, game_state, message, color,
                   target_pos=None, hint_pos=None,
                   seq_cells=None, done_cells=None, duration_mult=3):
    """피드백 메시지를 표시하고 잠시 대기."""
    ui_elements.message_text.text  = message
    ui_elements.message_text.color = color
    _draw_game_screen(win, ui_elements, board_renderer, deck_renderer,
                      token_renderer, game_state, target_pos,
                      seq_cells=seq_cells, done_cells=done_cells,
                      hint_pos=hint_pos, draw_message=True)
    blink_frame_marker(win)
    win.flip()
    checked_wait(FEEDBACK_DURATION * duration_mult,
                 label=f"practice_feedback('{message}')")


def _show_info_panel(win, title_text, body_text, nav_text,
                     title_color=None, body_color=None):
    """
    어두운 패널 위에 제목/본문/탐색 텍스트를 표시하고 Space/ESC 대기.

    Returns:
        str: 'continue' 또는 'exit'
    """
    title_color = title_color or [255, 220, 60]
    body_color  = body_color  or [230, 230, 230]

    panel = visual.Rect(
        win=win, width=780, height=560, pos=(0, 40),
        fillColor=[25, 25, 25], lineColor=[100, 100, 100],
        lineWidth=2, colorSpace='rgb255',
    )
    title = visual.TextStim(
        win=win, text=title_text, pos=(0, 270), height=30,
        color=title_color, colorSpace='rgb255', bold=True,
    )
    body = visual.TextStim(
        win=win, text=body_text, pos=(0, 60), height=22,
        color=body_color, colorSpace='rgb255', wrapWidth=720,
    )
    nav = visual.TextStim(
        win=win, text=nav_text, pos=(0, -220), height=18,
        color=[160, 160, 160], colorSpace='rgb255',
    )

    panel.draw()
    title.draw()
    body.draw()
    nav.draw()
    blink_frame_marker(win)
    win.flip()

    event.clearEvents()
    keys = event.waitKeys(keyList=['space', KEY_EXIT])
    return 'exit' if (keys and KEY_EXIT in keys) else 'continue'


# ==================== 닭 선택 단계 ====================

def _run_token_selection(win, game_state, ui_elements,
                         board_renderer, deck_renderer, token_renderer,
                         label, sounds):
    """
    닭 선택 단계 (Chase / Flight).

    Args:
        label: HUD 안내 문구에 표시할 시행 레이블 (예: "일반 2/3")
    Returns:
        str: 선택된 토큰 ('chase' / 'flight') 또는 'exit'
    """
    mouse = event.Mouse(win=win)

    orig_instruction_pos = ui_elements.instruction_text.pos
    orig_message_pos     = ui_elements.message_text.pos

    button_top = CHASE_BUTTON_POS[1] + TOKEN_BUTTON_HEIGHT / 2
    ui_elements.instruction_text.pos = (0, button_top + 25)
    ui_elements.message_text.pos     = (0, button_top + 60)
    ui_elements.instruction_text.text = f"[연습 {label}] 닭을 선택하세요"
    ui_elements.message_text.text     = ""
    ui_elements.instruction_text.height   = 20
    ui_elements.timer_text.text       = ""
    ui_elements.score_text.text       = ""

    def _cleanup():
        ui_elements.instruction_text.text = ""
        ui_elements.message_text.text     = ""
        ui_elements.instruction_text.pos  = orig_instruction_pos
        ui_elements.message_text.pos      = orig_message_pos

    while True:
        mouse_pos = mouse.getPos()
        hovering  = None

        for token_name, btn_pos in [('chase', CHASE_BUTTON_POS),
                                    ('flight', FLIGHT_BUTTON_POS)]:
            if _is_over_button(mouse_pos, btn_pos):
                hovering = token_name
                if mouse.getPressed()[0]:
                    game_state.select_token(token_name)
                    game_state.confirm_selection()
                    sound_play(sounds, 'type')
                    while mouse.getPressed()[0]:
                        core.wait(0.01)
                    _cleanup()
                    return token_name

        keys = event.getKeys()
        if KEY_EXIT in keys:
            _cleanup()
            return 'exit'

        # 화면 그리기
        board_renderer.draw()
        deck_renderer.draw()
        token_renderer.draw()
        for key in ('chase', 'flight'):
            btn = ui_elements.token_choice_buttons[key]
            btn['rect'].fillColor = [150, 150, 150] if hovering == key else BUTTON_COLOR_NORMAL
            btn['rect'].lineWidth = 4 if hovering == key else 2
            btn['rect'].draw()
            btn['text'].draw()
        ui_elements.instruction_text.draw()
        ui_elements.message_text.draw()
        ui_elements.update_ranking(game_state.user_score, game_state.pc_score)
        ui_elements.draw_ranking()
        blink_frame_marker(win)
        win.flip()
        core.wait(0.016)


# ==================== 일반 연습: 카드 선택 ====================

def _run_normal_card_selection(win, game_state, ui_elements,
                               board_renderer, deck_renderer, token_renderer,
                               sounds):
    """
    일반 연습 카드 선택 단계.
    - 시간 제한 없음
    - 오답 시 정답 카드 힌트(금색 테두리) 표시

    Returns:
        str: 'correct' | 'incorrect' | 'exit'
    """
    mouse      = event.Mouse(win=win)
    target_pos = game_state.get_target_position()

    ui_elements.set_user_turn_hud(
        selected_token=game_state.selected_token,
        turn_count=game_state.turn_count,
        timer_display_text="",
    )

    while True:
        keys = event.getKeys()
        if KEY_EXIT in keys:
            return 'exit'

        if mouse.getPressed()[0]:
            mouse_pos = mouse.getPos()
            card_pos  = _get_clicked_card(mouse_pos,
                                          game_state.deck.rows,
                                          game_state.deck.cols)
            if card_pos is not None:
                card_row, card_col = card_pos

                # defer_success_move=True: 성공 시 토큰 이동을 호출자가 직접 처리
                # → end_user_turn()이 내부 호출되지 않으므로 current_turn이 유지됨
                result = game_state.user_click_card(
                    card_row, card_col, defer_success_move=True)
                sound_play(sounds, 'flip')

                # 카드 뒤집기 화면
                _draw_game_screen(win, ui_elements, board_renderer, deck_renderer,
                                  token_renderer, game_state, target_pos)
                blink_frame_marker(win)
                win.flip()
                checked_wait(CARD_FLIP_DURATION, label="practice_card_flip")

                if result == 'success':
                    sound_play(sounds, 'correct')
                    _show_feedback(win, ui_elements, board_renderer, deck_renderer,
                                   token_renderer, game_state,
                                   message="정답!  잘 하셨어요 :)",
                                   color=PURPLE, target_pos=None)
                    # 토큰 이동 (성공 처리)
                    move_result = game_state.complete_user_success_move()
                    game_state.deck.hide_card(card_row, card_col)
                    if move_result == 'user_caught_npc':
                        board_renderer.refresh()
                        deck_renderer.refresh()
                    return 'correct'

                elif result == 'failure':
                    sound_play(sounds, 'error')
                    correct_pos = _find_correct_card(game_state)
                    _show_feedback(win, ui_elements, board_renderer, deck_renderer,
                                   token_renderer, game_state,
                                   message="틀렸어요.  정답 카드를 확인하세요!",
                                   color=DARK_GREY,
                                   target_pos=target_pos,
                                   hint_pos=correct_pos)
                    game_state.deck.hide_card(card_row, card_col)
                    return 'incorrect'

                # 클릭 해제 대기
                while mouse.getPressed()[0]:
                    core.wait(0.01)

        _draw_game_screen(win, ui_elements, board_renderer, deck_renderer,
                          token_renderer, game_state, target_pos)
        blink_frame_marker(win)
        win.flip()
        core.wait(0.016)


# ==================== 순서 기억 연습: seq_memory ====================

def _activate_practice_seq_memory(game_state, n_steps):
    """
    연습용으로 seq_memory를 강제 활성화.
    게임 점수 조건 없이 n_steps 만큼의 타겟을 설정.

    Returns:
        bool: 활성화 성공 여부
    """
    targets = game_state._compute_seq_targets(game_state.selected_token, n_steps)
    if len(targets) < 1:
        return False
    game_state.seq_memory_targets = targets
    game_state.seq_memory_step    = 0
    game_state.seq_memory_active  = True
    game_state.seq_memory_is_pc   = False
    print(f"[PRACTICE SEQ] {len(targets)}칸 순차 타겟 활성화: {targets}")
    return True


def _run_seq_card_selection(win, game_state, ui_elements,
                            board_renderer, deck_renderer, token_renderer,
                            sounds):
    """
    순서 기억 연습 카드 선택 단계.
    - 전체 타겟을 보드에 동시 강조
    - 순서대로 정답 카드 선택
    - 오답/순서 틀림 → 현재 스텝의 정답 힌트 표시 후 시행 종료
    - 전체 성공 → 토큰 점프 이동

    Returns:
        str: 'all_correct' | 'partial' | 'exit'
    """
    mouse = event.Mouse(win=win)

    seq_cells  = list(game_state.seq_memory_targets)   # 전체 타겟
    done_cells = []                                      # 완료된 타겟

    ui_elements.set_user_turn_hud(
        selected_token=game_state.selected_token,
        turn_count=game_state.turn_count,
        timer_display_text="",
    )

    while game_state.seq_memory_active:
        current_target = game_state.get_seq_memory_current_target()
        step_idx       = game_state.seq_memory_step
        total_steps    = len(seq_cells)

        keys = event.getKeys()
        if KEY_EXIT in keys:
            return 'exit'

        if mouse.getPressed()[0]:
            mouse_pos = mouse.getPos()
            card_pos  = _get_clicked_card(mouse_pos,
                                          game_state.deck.rows,
                                          game_state.deck.cols)
            if card_pos is not None:
                card_row, card_col = card_pos
                result = game_state.check_seq_memory_card(card_row, card_col)
                sound_play(sounds, 'flip')

                # 카드 뒤집기 화면
                _draw_game_screen(win, ui_elements, board_renderer, deck_renderer,
                                  token_renderer, game_state,
                                  target_pos=current_target,
                                  seq_cells=seq_cells,
                                  done_cells=done_cells)
                blink_frame_marker(win)
                win.flip()
                checked_wait(CARD_FLIP_DURATION, label="practice_seq_flip")

                if result == 'step_success':
                    sound_play(sounds, 'correct')
                    done_cells.append(current_target)
                    game_state.deck.hide_card(card_row, card_col)
                    # 짧은 성공 피드백 후 다음 스텝으로
                    _show_feedback(win, ui_elements, board_renderer, deck_renderer,
                                   token_renderer, game_state,
                                   message=f"스텝 {step_idx + 1}/{total_steps}  맞아요!",
                                   color=PURPLE,
                                   target_pos=game_state.get_seq_memory_current_target(),
                                   seq_cells=seq_cells,
                                   done_cells=done_cells,
                                   duration_mult=2)

                elif result == 'all_success':
                    sound_play(sounds, 'correct')
                    done_cells.append(current_target)
                    game_state.deck.hide_card(card_row, card_col)
                    _show_feedback(win, ui_elements, board_renderer, deck_renderer,
                                   token_renderer, game_state,
                                   message=f"전체 {total_steps}칸 순서 완벽!  토큰 이동!",
                                   color=GOLD,
                                   target_pos=None,
                                   seq_cells=seq_cells,
                                   done_cells=done_cells,
                                   duration_mult=4)
                    move_result = game_state.complete_seq_memory_move()
                    if move_result == 'user_caught_npc':
                        board_renderer.refresh()
                        deck_renderer.refresh()
                    return 'all_correct'

                elif result == 'failure':
                    sound_play(sounds, 'error')
                    # 현재 스텝의 정답 카드 힌트
                    hint = _find_correct_card(game_state, target_pos=current_target)
                    _show_feedback(win, ui_elements, board_renderer, deck_renderer,
                                   token_renderer, game_state,
                                   message=f"틀렸어요.  {step_idx + 1}번째 정답 카드를 확인하세요!",
                                   color=DARK_GREY,
                                   target_pos=current_target,
                                   seq_cells=seq_cells,
                                   done_cells=done_cells,
                                   hint_pos=hint,
                                   duration_mult=4)
                    game_state.deck.hide_card(card_row, card_col)
                    return 'partial'

                while mouse.getPressed()[0]:
                    core.wait(0.01)

        # 매 프레임 렌더
        _draw_game_screen(win, ui_elements, board_renderer, deck_renderer,
                          token_renderer, game_state,
                          target_pos=current_target,
                          seq_cells=seq_cells,
                          done_cells=done_cells)
        blink_frame_marker(win)
        win.flip()
        core.wait(0.016)

    return 'all_correct'   # seq_memory가 비활성화됐다면 완료로 처리


# ==================== 연습 게임 진입점 ====================

def run_practice_game(win, game_state, ui_elements,
                      board_renderer, deck_renderer, token_renderer):
    """
    연습 게임 메인 함수.

    Returns:
        str: 'continue' (연습 완료) 또는 'exit' (ESC 종료)
    """
    sounds = load_sounds()
    game_state.start_game()

    # ── 1. 안내 화면 ──
    result = _show_info_panel(
        win,
        title_text="연습 게임",
        body_text=(
            "본 게임 전 연습입니다.\n\n"
            "① Chase 또는 Flight 닭을 선택하세요\n"
            "② 운동장(보드)의 조건에 맞는 카드를\n"
            "   덱에서 클릭하세요\n"
            "③ 틀려도 괜찮아요 — 정답 위치를 알려드려요!"
        ),
        nav_text="스페이스바로 시작 / ESC로 건너뛰기",
    )
    if result == 'exit':
        return 'exit'

    # ── 2. 일반 연습 ──
    normal_correct = 0
    for trial_num in range(1, PRACTICE_TRIALS + 1):
        selected = _run_token_selection(
            win, game_state, ui_elements,
            board_renderer, deck_renderer, token_renderer,
            label=f"일반 {trial_num}/{PRACTICE_TRIALS}", sounds=sounds,
        )
        if selected == 'exit':
            return 'exit'

        trial_result = _run_normal_card_selection(
            win, game_state, ui_elements,
            board_renderer, deck_renderer, token_renderer,
            sounds=sounds,
        )
        if trial_result == 'exit':
            return 'exit'

        if trial_result == 'correct':
            normal_correct += 1

        _reset_for_next_trial(game_state)
        checked_wait(TRIAL_INTERVAL, label="practice_normal_interval")

    # ── 3. 순서 기억 연습 ──
    seq_correct = 0
    if PRACTICE_SEQ_TRIALS > 0:
        # 순서 기억 안내
        result = _show_info_panel(
            win,
            title_text="순서 기억 연습",
            body_text=(
                "이번에는 여러 칸을 순서대로 맞히는\n"
                "순서 기억 연습입니다.\n\n"
                "보드에 표시된 타겟을 순서대로 확인하고,\n"
                "각 타겟에 맞는 카드를 순서대로 선택하세요.\n\n"
                f"총 {PRACTICE_SEQ_STEPS}개의 카드를 순서대로 맞혀야 합니다."
            ),
            nav_text="스페이스바로 시작 / ESC로 건너뛰기",
            title_color=[0, 200, 255],
        )
        if result == 'exit':
            return 'exit'

        for seq_num in range(1, PRACTICE_SEQ_TRIALS + 1):
            selected = _run_token_selection(
                win, game_state, ui_elements,
                board_renderer, deck_renderer, token_renderer,
                label=f"순서 {seq_num}/{PRACTICE_SEQ_TRIALS}", sounds=sounds,
            )
            if selected == 'exit':
                return 'exit'

            # 강제로 seq_memory 활성화
            activated = _activate_practice_seq_memory(
                game_state, n_steps=PRACTICE_SEQ_STEPS)

            if not activated:
                # 타겟이 부족하면 일반 시행으로 대체
                trial_result = _run_normal_card_selection(
                    win, game_state, ui_elements,
                    board_renderer, deck_renderer, token_renderer,
                    sounds=sounds,
                )
                if trial_result == 'exit':
                    return 'exit'
            else:
                seq_result = _run_seq_card_selection(
                    win, game_state, ui_elements,
                    board_renderer, deck_renderer, token_renderer,
                    sounds=sounds,
                )
                if seq_result == 'exit':
                    return 'exit'
                if seq_result == 'all_correct':
                    seq_correct += 1

            _reset_for_next_trial(game_state)
            checked_wait(TRIAL_INTERVAL, label="practice_seq_interval")

    # ── 4. 완료 화면 ──
    return _show_completion(
        win, normal_correct, PRACTICE_TRIALS,
        seq_correct, PRACTICE_SEQ_TRIALS,
    )


# ==================== 완료 화면 ====================

def _show_completion(win, normal_correct, normal_total,
                     seq_correct, seq_total):
    """
    연습 완료 화면.

    Returns:
        str: 'continue' 또는 'exit'
    """
    normal_pct = int(normal_correct / max(1, normal_total) * 100)

    lines = [f"일반 연습  정답률:  {normal_correct} / {normal_total}  ({normal_pct}%)"]
    if seq_total > 0:
        seq_pct = int(seq_correct / max(1, seq_total) * 100)
        lines.append(f"순서 기억  정답률:  {seq_correct} / {seq_total}  ({seq_pct}%)")

    panel = visual.Rect(
        win=win, width=660, height=460, pos=(0, 60),
        fillColor=[25, 25, 25], lineColor=[100, 100, 100],
        lineWidth=2, colorSpace='rgb255',
    )
    title = visual.TextStim(
        win=win, text="연습 완료!", pos=(0, 230), height=36,
        color=[255, 220, 60], colorSpace='rgb255', bold=True,
    )
    score_stims = []
    for i, line in enumerate(lines):
        score_stims.append(visual.TextStim(
            win=win, text=line,
            pos=(0, 120 - i * 56), height=24,
            color=[173, 255, 47], colorSpace='rgb255', bold=True,
        ))
    body = visual.TextStim(
        win=win, text="이제 본 게임을 시작합니다.",
        pos=(0, -30), height=22,
        color=[230, 230, 230], colorSpace='rgb255',
    )
    nav = visual.TextStim(
        win=win, text="스페이스바로 계속 / ESC로 종료",
        pos=(0, -180), height=18,
        color=[160, 160, 160], colorSpace='rgb255',
    )

    panel.draw()
    title.draw()
    for s in score_stims:
        s.draw()
    body.draw()
    nav.draw()
    blink_frame_marker(win)
    win.flip()

    event.clearEvents()
    keys = event.waitKeys(keyList=['space', KEY_EXIT])
    return 'exit' if (keys and KEY_EXIT in keys) else 'continue'
