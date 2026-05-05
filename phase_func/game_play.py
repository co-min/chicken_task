import sys
from pathlib import Path
from psychopy import core, event

try:
    from ..config import (
        KEY_EXIT, CARD_FLIP_DURATION,
        FEEDBACK_DURATION, TRIAL_INTERVAL, PC_THINK_TIME,
        WIDTH, HEIGHT, TEXT_COLOR,
        DECK_LEFT_EDGE, BOARD_DECK_TOP_MARGIN,
        DECK_CARD_WIDTH, DECK_CARD_HEIGHT, DECK_CARD_SPACING,
        PURPLE, DARK_GREY, GOLD, ORANGE_RED, ROUND_BREAK_DURATION,
        SCORE_CATCH_BONUS, SCORE_CAUGHT_PENALTY,
        CATCH_RESET_PREP_DURATION,
    )
    from ..phase_func.token_selection import run_token_selection_phase
    from ..phase_func.feedback import run_feedback_phase
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from config import (
        KEY_EXIT, CARD_FLIP_DURATION,
        FEEDBACK_DURATION, TRIAL_INTERVAL, PC_THINK_TIME,
        WIDTH, HEIGHT, TEXT_COLOR,
        DECK_LEFT_EDGE, BOARD_DECK_TOP_MARGIN,
        DECK_CARD_WIDTH, DECK_CARD_HEIGHT, DECK_CARD_SPACING,
        PURPLE, DARK_GREY, GOLD, ORANGE_RED, ROUND_BREAK_DURATION,
        SCORE_CATCH_BONUS, SCORE_CAUGHT_PENALTY,
        CATCH_RESET_PREP_DURATION,
    )
    from phase_func.token_selection import run_token_selection_phase
    from phase_func.feedback import run_feedback_phase

try:
    from ..view_func.frame_marker import blink_frame_marker, trigger_frame_marker
    from ..sounds import load_sounds, play as sound_play
    from ..utils.labjack_triggers import (send_trigger, set_trigger, reset_trigger,
                                           TRIG_TRIAL_START, TRIG_TRIAL_END,
                                           TRIG_CARD_CLICK, TRIG_CARD_FLIP_USER, TRIG_CARD_FLIP_PC,
                                           TRIG_FEEDBACK_SUCCESS, TRIG_FEEDBACK_FAILURE, TRIG_FEEDBACK_TIMEOUT,
                                           TRIG_SEQ_ACTIVATE, TRIG_SEQ_ALL_SUCCESS, TRIG_SEQ_FAILURE)
    from ..save_func.trial_saver import save_trial
    from ..utils.frame_drop_log import FrameDropLogger
except ImportError:
    from view_func.frame_marker import blink_frame_marker, trigger_frame_marker
    from sounds import load_sounds, play as sound_play
    from utils.labjack_triggers import (send_trigger, set_trigger, reset_trigger,
                                        TRIG_TRIAL_START, TRIG_TRIAL_END,
                                        TRIG_CARD_CLICK, TRIG_CARD_FLIP_USER, TRIG_CARD_FLIP_PC,
                                        TRIG_FEEDBACK_SUCCESS, TRIG_FEEDBACK_FAILURE, TRIG_FEEDBACK_TIMEOUT,
                                        TRIG_SEQ_ACTIVATE, TRIG_SEQ_ALL_SUCCESS, TRIG_SEQ_FAILURE)
    from save_func.trial_saver import save_trial
    from utils.frame_drop_log import FrameDropLogger


START_CUE_DURATION = 0.5


def _ljack(handle, code):
    send_trigger(handle, code)


def _flip_trigger(win, handle, code):
    if handle:
        win.callOnFlip(set_trigger, handle, code)


def _flip_reset(win, handle):
    if handle:
        win.callOnFlip(reset_trigger, handle)


def _edf_msg(aoi_manager, message: str):
    """EyeLink EDF 파일에 타임스탬프 메시지를 기록한다."""
    if aoi_manager and aoi_manager.el_tracker:
        aoi_manager.el_tracker.sendMessage(message)



def run_game_play_phase(win, game_state, ui_elements, board_renderer, deck_renderer,
                        token_renderer, aoi_manager=None, labjack_handle=None,
                        save_paths=None, subject_id=''):
    """
    Args:
        win: PsychoPy window 객체
        game_state: GameState
        ui_elements: UIElements
        board_renderer: BoardRenderer
        deck_renderer: DeckRenderer
        token_renderer: TokenRenderer
        aoi_manager: AOIManager (선택, None 이면 EyeLink AOI 추적 비활성화)
        labjack_handle: LabJack T4 핸들 (선택, None 이면 트리거 비활성화)

    Returns:
        str: 게임 종료 이유 ('victory', 'defeat', 'exit')
    """

    # 마우스 객체
    mouse = event.Mouse(win=win)

    # 사운드 로드
    sounds = load_sounds()

    fdl = FrameDropLogger(save_paths['frame_drops']) if (save_paths and save_paths.get('frame_drops')) else None

    # 게임 메인 루프
    while True:
        # 라운드/게임 종료 확인
        if game_state.is_round_time_expired():
            if not game_state.is_game_time_expired():

                # 아직 게임 시간 남음 → 다음 라운드 시작
                game_state.advance_round()
                board_renderer.update_board(game_state.board)
                deck_renderer.update_deck(game_state.deck)
                if aoi_manager:
                    aoi_manager.update_deck(game_state.deck)
                _run_round_break(win, ui_elements, board_renderer, deck_renderer,
                                 token_renderer, game_state, fdl=fdl)
            else:
                print("[GAME END] 게임 시간(30분) 완료!")
                return 'timeout'

        # 현재 턴 확인 및 실행
        if game_state.current_turn == game_state.TURN_USER:
            # 사용자 턴 실행
            result = _run_user_turn(win, game_state, ui_elements, board_renderer,
                                   deck_renderer, token_renderer, mouse, aoi_manager,
                                   labjack_handle=labjack_handle,
                                   save_paths=save_paths, subject_id=subject_id,
                                   sounds=sounds, fdl=fdl)

            if result == 'exit':
                return 'exit'
            elif result == 'continue':
                # 사용자 턴 종료 → PC 턴으로 전환됨
                print(f"[TURN SWITCH] 사용자 → 문어 (턴 {game_state.turn_count})")

        elif game_state.current_turn == game_state.TURN_PC:
            # PC 턴 실행
            result = _run_pc_turn(win, game_state, ui_elements, board_renderer,
                                 deck_renderer, token_renderer,
                                 aoi_manager=aoi_manager,
                                 labjack_handle=labjack_handle,
                                 save_paths=save_paths, subject_id=subject_id,
                                 sounds=sounds, fdl=fdl)

            if result == 'continue':
                # PC 턴 종료 → 사용자 턴으로 전환됨
                print(f"[TURN SWITCH] 문어 → 사용자 (턴 {game_state.turn_count})")


def _run_user_turn(win, game_state, ui_elements, board_renderer, deck_renderer,
                   token_renderer, mouse, aoi_manager=None, labjack_handle=None,
                   save_paths=None, subject_id='', sounds=None, fdl=None):
    """
    사용자 턴 실행

    흐름:
    1. 닭 선택 단계 (선택되지 않았을 경우)
    2. 카드 선택 루프 (같은 닭으로 계속 시도)
       - 성공: 타이머 리셋 후 다음 타겟으로 계속
       - 실패/타임아웃: 턴 종료 → PC 턴으로 전환

    Returns:
        str: 'exit' (게임 종료), 'game_end' (승패 결정), 'continue' (턴 종료 → PC 턴)
    """

    # 1. 닭 선택 단계 (토큰이 선택되지 않았을 때만)
    if game_state.selected_token is None:
        print(f"[USER TURN] 닭 선택 단계 (턴 {game_state.turn_count})")
        selected = run_token_selection_phase(win, game_state, ui_elements,
                                            board_renderer, deck_renderer, token_renderer,
                                            sounds=sounds,
                                            labjack_handle=labjack_handle)

        if selected == 'exit':
            return 'exit'

        # 선택 확정 및 타이머 시작
        if not game_state.confirm_selection():
            return 'continue'
        print(f"[USER TURN] {game_state.selected_token.upper()} 선택, 카드 선택 시작")

    # 2. 카드 선택 루프 (같은 토큰으로 계속 진행)
    _trial_active = False  # True인 동안은 TRIAL_START를 중복 전송하지 않는다
    _trial_id = None
    _pre_flip_lj_code = 0   # win.flip() 직전에 전송할 TTL 코드 (0 = 없음)
    while game_state.phase == game_state.PHASE_GAME_PLAY and \
          game_state.current_turn == game_state.TURN_USER:

        # 타겟 위치 업데이트: seq_memory 활성 시 현재 step 타겟, 아니면 일반 타겟
        if game_state.seq_memory_active:
            target_pos = game_state.get_seq_memory_current_target()
        else:
            target_pos = game_state.get_target_position()

        # 새 시도 시작: EDF + LabJack에 TRIAL_START 전송
        if not _trial_active:
            _trial_id = game_state.get_next_trial_id()
            # 순차 메모리 발동 시도 (첫 번째 시도 시작 시에만 체크)
            game_state.try_activate_seq_memory()
            if aoi_manager:
                aoi_manager.current_trial_id = _trial_id
                aoi_manager.is_seq_memory    = game_state.seq_memory_active
                aoi_manager.seq_memory_step  = (game_state.seq_memory_step
                                                if game_state.seq_memory_active else None)
            if game_state.seq_memory_active:
                trigger_frame_marker()   # 이벤트: seq_memory 활성화
            _edf_msg(aoi_manager,
                     f"TRIAL_START {_trial_id} USER"
                     f" ROUND {game_state.current_round}"
                     f" TURN {game_state.turn_count}"
                     + (f" SEQ_MEMORY step 0/{len(game_state.seq_memory_targets)}"
                        if game_state.seq_memory_active else ""))
            game_state.current_trial_start_psychopy = core.getTime()
            _pre_flip_lj_code = TRIG_TRIAL_START
            _trial_active = True

        # 사용자 턴 HUD 업데이트
        ui_elements.set_user_turn_hud(
            selected_token=game_state.selected_token,
            turn_count=game_state.turn_count,
            timer_display_text=game_state.timer.get_display_text(),
        )

        # 시간 초과 확인
        if game_state.timer.is_expired():
            print(f"[USER TURN] 타임아웃! 턴 종료")
            sound_play(sounds, 'error')
            run_feedback_phase(
                win,
                ui_elements,
                board_renderer,
                deck_renderer,
                token_renderer,
                message="시간 초과",
                color=DARK_GREY,
                duration=FEEDBACK_DURATION,
                highlighted_pos=None,
                labjack_handle=labjack_handle,
                trigger_code=TRIG_FEEDBACK_TIMEOUT,
                frame_drop_logger=fdl,
            )

            # 시행 종료 마킹 (seq_memory 도중 타임아웃이면 seq_timeout으로 구별)
            _timeout_result = "seq_timeout" if game_state.seq_memory_active else "timeout"
            _edf_msg(aoi_manager, f"TRIAL_END {_trial_id} MATCH 0 RESULT {_timeout_result}")

            # 턴 종료 (end_user_turn 내부에서 deactivate_seq_memory + selected_token 리셋됨)
            game_state.end_user_turn()

            return 'continue'

        # 키보드 입력 확인 (ESC)
        keys = event.getKeys()
        if KEY_EXIT in keys:
            return 'exit'

        # 마우스 클릭 확인
        if mouse.getPressed()[0]:  # 왼쪽 버튼
            mouse_pos = mouse.getPos()

            # 클릭한 카드 위치 확인
            card_pos = _get_clicked_card(mouse_pos, game_state.deck.rows, game_state.deck.cols)

            if card_pos is not None:
                card_row, card_col = card_pos

                # 덱 카드 클릭 즉시 트리거 (운동 반응 onset — flip 전에 전송)
                _ljack(labjack_handle, TRIG_CARD_CLICK)

                # ── 카드 선택 처리 (seq_memory 활성 여부에 따라 분기) ──
                was_seq_memory = game_state.seq_memory_active
                if was_seq_memory:
                    result = game_state.check_seq_memory_card(card_row, card_col)
                    print(f"[USER TURN][SEQ {game_state.seq_memory_step}/{len(game_state.seq_memory_targets)}] "
                          f"카드 선택: {card_pos}, 결과: {result}")
                else:
                    result = game_state.user_click_card(card_row, card_col, defer_success_move=True)
                    print(f"[USER TURN] 카드 선택: {card_pos}, 결과: {result}")

                # 시행 결과 즉시 CSV에 기록 (크래시 안전)
                if save_paths and game_state.trial_history:
                    save_trial(save_paths['trial'], game_state.trial_history[-1],
                               game_state, subject_id)

                # 카드 뒤집기 애니메이션 (flip은 check_seq_memory_card / user_click_card 내부에서 수행됨)
                sound_play(sounds, 'flip')
                _draw_game_screen(win, ui_elements, board_renderer, deck_renderer, token_renderer, game_state, target_pos)
                trigger_frame_marker()   # 이벤트: 사용자 카드 뒤집기
                blink_frame_marker(win)
                _flip_trigger(win, labjack_handle, TRIG_CARD_FLIP_USER)
                win.flip()
                if fdl:
                    fdl.after_flip(core.getTime(), trial_id=_trial_id, context='user_card_flip')
                _flip_reset(win, labjack_handle)
                _flip_deadline = core.getTime() + CARD_FLIP_DURATION
                while core.getTime() < _flip_deadline:
                    _draw_game_screen(win, ui_elements, board_renderer, deck_renderer,
                                      token_renderer, game_state, target_pos)
                    blink_frame_marker(win)
                    win.flip()
                    if fdl:
                        fdl.after_flip(core.getTime(), trial_id=_trial_id, context='user_card_flip')
                    if aoi_manager:
                        aoi_manager.update(core.getTime())

                # ── seq_memory step_success: 피드백 없이 다음 스텝으로 계속 ──
                if result == 'step_success':
                    step_now  = game_state.seq_memory_step       # 방금 완료된 step (이미 +1됨)
                    step_total = len(game_state.seq_memory_targets)
                    game_state.deck.hide_card(card_row, card_col)
                    # 다음 스텝: trial_id 갱신, _trial_active 유지
                    _trial_id = game_state.get_next_trial_id()
                    if aoi_manager:
                        aoi_manager.current_trial_id = _trial_id
                        aoi_manager.is_seq_memory    = True
                        aoi_manager.seq_memory_step  = game_state.seq_memory_step
                    _edf_msg(aoi_manager,
                             f"TRIAL_START {_trial_id} USER"
                             f" ROUND {game_state.current_round}"
                             f" TURN {game_state.turn_count} SEQ_MEMORY step {step_now}/{step_total}")
                    game_state.current_trial_start_psychopy = core.getTime()
                    _pre_flip_lj_code = TRIG_TRIAL_START
                    target_pos = game_state.get_seq_memory_current_target()
                    continue

                # ── seq_memory all_success 또는 일반 success ──
                if result in ('all_success', 'success'):
                    sound_play(sounds, 'correct')

                    if result == 'all_success':
                        # 순차 메모리 전체 성공 → 토큰 점프 이동
                        step_total = len(game_state.seq_memory_targets)
                        run_feedback_phase(
                            win, ui_elements, board_renderer, deck_renderer, token_renderer,
                            message=f"순차 {step_total}/{step_total} 완료!  {step_total}칸 이동!",
                            color=GOLD,
                            duration=FEEDBACK_DURATION,
                            highlighted_pos=None,
                            labjack_handle=labjack_handle,
                            trigger_code=TRIG_SEQ_ALL_SUCCESS,
                            frame_drop_logger=fdl,
                        )
                        move_result = game_state.complete_seq_memory_move()
                    else:
                        # 일반 성공
                        run_feedback_phase(
                            win, ui_elements, board_renderer, deck_renderer, token_renderer,
                            message="성공",
                            color=PURPLE,
                            duration=FEEDBACK_DURATION,
                            highlighted_pos=None,
                            labjack_handle=labjack_handle,
                            trigger_code=TRIG_FEEDBACK_SUCCESS,
                            frame_drop_logger=fdl,
                        )
                        move_result = game_state.complete_user_success_move()

                    # 카드 뒤로 감추기
                    game_state.deck.hide_card(card_row, card_col)

                    # 잡기 이벤트: 문어를 잡았을 때 추가 피드백 + 라운드 갱신
                    if move_result == 'user_caught_npc':
                        board_renderer.refresh()
                        deck_renderer.refresh()
                        sound_play(sounds, 'win')
                        run_feedback_phase(
                            win, ui_elements, board_renderer, deck_renderer, token_renderer,
                            message=f"문어를 잡았다!  +{SCORE_CATCH_BONUS}점",
                            color=GOLD,
                            duration=FEEDBACK_DURATION * 2,
                            highlighted_pos=None,
                            frame_drop_logger=fdl,
                        )
                        _show_reset_prep_cue(win, ui_elements, board_renderer, deck_renderer,
                                             token_renderer, game_state, fdl=fdl)
                        _edf_msg(aoi_manager, f"TRIAL_END {_trial_id} MATCH 1 RESULT user_caught_npc")
                        _ljack(labjack_handle, TRIG_TRIAL_END)
                        _trial_active = False
                        game_state.advance_round()
                        board_renderer.update_board(game_state.board)
                        deck_renderer.update_deck(game_state.deck)
                        if aoi_manager:
                            aoi_manager.update_deck(game_state.deck)
                        game_state.selected_token = None
                        game_state.timer.reset()
                        game_state.phase = game_state.PHASE_TOKEN_SELECTION
                        print(f"[ROUND ADVANCE] 잡기(사용자) → 라운드 {game_state.current_round} 시작")
                        _run_round_break(win, ui_elements, board_renderer, deck_renderer,
                                         token_renderer, game_state, fdl=fdl)
                        return 'continue'

                    # 시행 종료 마킹
                    edf_result = 'seq_all_success' if result == 'all_success' else 'success'
                    _edf_msg(aoi_manager, f"TRIAL_END {_trial_id} MATCH 1 RESULT {edf_result}")
                    _trial_active = False

                    # 타이머 리셋 후 다음 타겟 계속
                    _interval_deadline = core.getTime() + TRIAL_INTERVAL
                    while core.getTime() < _interval_deadline:
                        _draw_game_screen(win, ui_elements, board_renderer, deck_renderer,
                                          token_renderer, game_state,
                                          game_state.get_target_position())
                        blink_frame_marker(win)
                        win.flip()
                        if fdl:
                            fdl.after_flip(core.getTime(), trial_id=_trial_id, context='trial_interval')
                        if aoi_manager:
                            aoi_manager.update(core.getTime())
                    _show_start_cue(
                        win, ui_elements, board_renderer, deck_renderer, token_renderer,
                        game_state=game_state,
                        selected_token=game_state.selected_token,
                        turn_count=game_state.turn_count,
                        timer_display_text=game_state.timer.get_display_text(),
                        target_pos=game_state.get_target_position(),
                        sounds=sounds,
                        fdl=fdl,
                    )
                    game_state.timer.reset()
                    print(f"[USER TURN] 성공({move_result}), 타이머 리셋, 다음 타겟으로 계속")
                    continue

                elif result == 'failure':
                    sound_play(sounds, 'error')
                    # was_seq_memory: check_seq_memory_card 내부에서 이미 deactivate되어
                    #                 game_state.seq_memory_active는 이 시점에 False이므로
                    #                 카드 선택 전에 저장한 was_seq_memory로 판별한다.
                    if was_seq_memory:
                        fail_msg    = "순차 실패 - 이동 없음"
                        fail_code   = TRIG_SEQ_FAILURE
                        fail_result = "seq_failure"
                    else:
                        fail_msg    = "실패"
                        fail_code   = TRIG_FEEDBACK_FAILURE
                        fail_result = "failure"
                    run_feedback_phase(
                        win, ui_elements, board_renderer, deck_renderer, token_renderer,
                        message=fail_msg,
                        color=DARK_GREY,
                        duration=FEEDBACK_DURATION,
                        highlighted_pos=None,
                        labjack_handle=labjack_handle,
                        trigger_code=fail_code,
                        frame_drop_logger=fdl,
                    )
                    game_state.deck.hide_card(card_row, card_col)
                    _edf_msg(aoi_manager, f"TRIAL_END {_trial_id} MATCH 0 RESULT {fail_result}")
                    _ljack(labjack_handle, TRIG_TRIAL_END)
                    print(f"[USER TURN] {'순차 ' if was_seq_memory else ''}실패, 턴 종료")
                    return 'continue'

                # # 클릭 후 버튼이 떼어지기를 기다림
                # while mouse.getPressed()[0]:
                #     core.wait(0.01)

        # 화면 그리기 (타겟 하이라이트 포함)
        _draw_game_screen(win, ui_elements, board_renderer, deck_renderer, token_renderer, game_state, target_pos)
        blink_frame_marker(win)
        # TRIG_TRIAL_START: 시행 첫 프레임 flip 시 전송 → callOnFlip으로 VSync에 정확히 동기화
        _queued_trigger = bool(_pre_flip_lj_code and labjack_handle)
        if _queued_trigger:
            _flip_trigger(win, labjack_handle, _pre_flip_lj_code)
            _pre_flip_lj_code = 0
        win.flip()

        if fdl:
            fdl.after_flip(core.getTime(), trial_id=_trial_id, context='user_render')

        # AOI 시선 추적 업데이트 (VSync 직후 타임스탬프로 동기화)
        if aoi_manager:
            aoi_manager.update(core.getTime())

        # 트리거가 전송된 경우 다음 flip에서 리셋
        if _queued_trigger:
            _flip_reset(win, labjack_handle)

    return 'continue'


def _run_pc_turn(win, game_state, ui_elements, board_renderer, deck_renderer, token_renderer,
                 aoi_manager=None, labjack_handle=None, save_paths=None, subject_id='', sounds=None,
                 fdl=None):

    # PC 턴 루프 (성공 시 계속 진행)
    while game_state.current_turn == game_state.TURN_PC:
        print(f"[문어] Octopus 카드 선택 시작 (턴 {game_state.turn_count})")

        # PC 타겟 위치 확인
        pc_target_pos = game_state.tokens.get_target_position('octopus')

        # PC 턴 HUD 업데이트
        ui_elements.set_pc_turn_hud(
            turn_count=game_state.turn_count,
            target_pos=pc_target_pos,
            timer_label="문어 턴",
        )

        # 타겟 하이라이트와 함께 화면 그리기 + TRIG_TRIAL_START pre-flip 전송
        _draw_game_screen(win, ui_elements, board_renderer, deck_renderer, token_renderer, game_state, pc_target_pos)
        trigger_frame_marker()   # 이벤트: PC 턴 시작
        blink_frame_marker(win)
        _flip_trigger(win, labjack_handle, TRIG_TRIAL_START)
        win.flip()
        if fdl:
            fdl.after_flip(core.getTime(), context='pc_think_start')
        _flip_reset(win, labjack_handle)
        if aoi_manager:
            aoi_manager.update(core.getTime())

        # PC 생각 시간
        _think_deadline = core.getTime() + PC_THINK_TIME
        while core.getTime() < _think_deadline:
            _draw_game_screen(win, ui_elements, board_renderer, deck_renderer,
                              token_renderer, game_state, pc_target_pos)
            blink_frame_marker(win)
            win.flip()
            if fdl:
                fdl.after_flip(core.getTime(), context='pc_think')
            if aoi_manager:
                aoi_manager.update(core.getTime())

        # PC 카드 선택 및 실행 (seq_memory 활성 여부에 따라 분기)
        _pc_trial_id = game_state.get_next_trial_id()

        # seq_memory 발동 시도 (매 PC 시도 시작 시)
        _was_pc_seq_active = game_state.seq_memory_active
        game_state.try_activate_pc_seq_memory()

        if aoi_manager:
            aoi_manager.current_trial_id = _pc_trial_id
            aoi_manager.is_seq_memory    = game_state.seq_memory_active
            aoi_manager.seq_memory_step  = (game_state.seq_memory_step
                                            if game_state.seq_memory_active else None)

        # 현재 타겟: seq_memory 활성이면 현재 step 타겟, 아니면 일반 타겟
        if game_state.seq_memory_active:
            pc_target_pos = game_state.get_seq_memory_current_target()
            if not _was_pc_seq_active:
                _ljack(labjack_handle, TRIG_SEQ_ACTIVATE)   # 신규 활성화 onset (즉시 전송)
        # else: 위에서 계산된 pc_target_pos 유지

        _seq_tag = (
            f" SEQ_MEMORY step {game_state.seq_memory_step}/{len(game_state.seq_memory_targets)}"
            if game_state.seq_memory_active else ""
        )
        _edf_msg(aoi_manager,
                 f"TRIAL_START {_pc_trial_id} PC"
                 f" ROUND {game_state.current_round}"
                 f" TURN {game_state.turn_count}"
                 + _seq_tag)
        game_state.current_trial_start_psychopy = core.getTime()

        _checked_as_pc_seq = game_state.seq_memory_active
        if _checked_as_pc_seq:
            result, card_pos = game_state.check_pc_seq_memory_card()
        else:
            result, card_pos = game_state.pc_turn_step(defer_success_move=True)

        print(f"[PC TURN] 카드 선택: {card_pos}, 결과: {result}")
        # 시행 결과 즉시 CSV에 기록 (크래시 안전)
        if save_paths and game_state.trial_history:
            save_trial(save_paths['trial'], game_state.trial_history[-1],
                       game_state, subject_id)

        # 1단계: 카드 뒤집기 애니메이션
        sound_play(sounds, 'npc_flip')
        _draw_game_screen(win, ui_elements, board_renderer, deck_renderer, token_renderer, game_state, pc_target_pos)
        trigger_frame_marker()   # 이벤트: PC 카드 뒤집기
        blink_frame_marker(win)
        _flip_trigger(win, labjack_handle, TRIG_CARD_FLIP_PC)
        win.flip()
        if fdl:
            fdl.after_flip(core.getTime(), trial_id=_pc_trial_id, context='pc_card_flip')
        _flip_reset(win, labjack_handle)
        _pc_flip_deadline = core.getTime() + CARD_FLIP_DURATION
        while core.getTime() < _pc_flip_deadline:
            _draw_game_screen(win, ui_elements, board_renderer, deck_renderer,
                              token_renderer, game_state, pc_target_pos)
            blink_frame_marker(win)
            win.flip()
            if fdl:
                fdl.after_flip(core.getTime(), trial_id=_pc_trial_id, context='pc_card_flip')
            if aoi_manager:
                aoi_manager.update(core.getTime())

        # 2단계: 기본 결과 피드백
        if result == 'failure':
            sound_play(sounds, 'error')
            run_feedback_phase(
                win, ui_elements, board_renderer, deck_renderer, token_renderer,
                message="문어 순차 실패" if _checked_as_pc_seq else "문어 실패",
                color=DARK_GREY,
                duration=FEEDBACK_DURATION, highlighted_pos=pc_target_pos,
                labjack_handle=labjack_handle,
                trigger_code=TRIG_SEQ_FAILURE if _checked_as_pc_seq else 0,
                frame_drop_logger=fdl,
            )
        elif result == 'step_success':
            pass  # 중간 스텝 성공은 피드백 없이 조용히 다음 스텝으로 진행
        else:  # 'success' or 'all_success'
            sound_play(sounds, 'correct')
            if result == 'all_success':
                step_total = len(game_state.seq_memory_targets)
                run_feedback_phase(
                    win, ui_elements, board_renderer, deck_renderer, token_renderer,
                    message=f"문어 순차 {step_total}칸 완료!",
                    color=GOLD,
                    duration=FEEDBACK_DURATION, highlighted_pos=pc_target_pos,
                    labjack_handle=labjack_handle,
                    trigger_code=TRIG_SEQ_ALL_SUCCESS,
                    frame_drop_logger=fdl,
                )
            else:
                run_feedback_phase(
                    win, ui_elements, board_renderer, deck_renderer, token_renderer,
                    message="문어 성공", color=PURPLE,
                    duration=FEEDBACK_DURATION, highlighted_pos=pc_target_pos,
                    frame_drop_logger=fdl,
                )

        # 3단계: 결과에 따른 처리
        if result == 'step_success':
            # 다음 스텝으로 계속: card_pos 카드 감추기, trial_id 갱신
            if card_pos:
                game_state.deck.hide_card(card_pos[0], card_pos[1])
            _pc_trial_id = game_state.get_next_trial_id()
            if aoi_manager:
                aoi_manager.current_trial_id = _pc_trial_id
                aoi_manager.is_seq_memory    = True
                aoi_manager.seq_memory_step  = game_state.seq_memory_step
            _edf_msg(aoi_manager,
                     f"TRIAL_START {_pc_trial_id} PC"
                     f" ROUND {game_state.current_round}"
                     f" TURN {game_state.turn_count}"
                     f" SEQ_MEMORY step {game_state.seq_memory_step}/{len(game_state.seq_memory_targets)}")
            game_state.current_trial_start_psychopy = core.getTime()
            pc_target_pos = game_state.get_seq_memory_current_target()
            # TRIG_TRIAL_START: 다음 step 첫 프레임 flip 직전에 전송
            _draw_game_screen(win, ui_elements, board_renderer, deck_renderer,
                              token_renderer, game_state, pc_target_pos)
            blink_frame_marker(win)
            _flip_trigger(win, labjack_handle, TRIG_TRIAL_START)
            win.flip()
            if fdl:
                fdl.after_flip(core.getTime(), trial_id=_pc_trial_id, context='pc_seq_think_start')
            _flip_reset(win, labjack_handle)
            if aoi_manager:
                aoi_manager.update(core.getTime())
            _seq_think_deadline = core.getTime() + PC_THINK_TIME
            while core.getTime() < _seq_think_deadline:
                _draw_game_screen(win, ui_elements, board_renderer, deck_renderer,
                                  token_renderer, game_state, pc_target_pos)
                blink_frame_marker(win)
                win.flip()
                if fdl:
                    fdl.after_flip(core.getTime(), trial_id=_pc_trial_id, context='pc_seq_think')
                if aoi_manager:
                    aoi_manager.update(core.getTime())
            continue

        if result in ('success', 'all_success'):
            if result == 'all_success':
                move_result = game_state.complete_pc_seq_memory_move()
            else:
                move_result = game_state.complete_pc_success_move()

            if card_pos:
                game_state.deck.hide_card(card_pos[0], card_pos[1])

            # 잡기 이벤트: 문어가 flight를 잡았을 때
            if move_result == 'npc_caught_user':
                board_renderer.refresh()
                deck_renderer.refresh()
                sound_play(sounds, 'lose')
                run_feedback_phase(
                    win, ui_elements, board_renderer, deck_renderer, token_renderer,
                    message=f"잡혔다!  {SCORE_CAUGHT_PENALTY}점",
                    color=ORANGE_RED,
                    duration=FEEDBACK_DURATION * 2,
                    highlighted_pos=None,
                    frame_drop_logger=fdl,
                )
                _show_reset_prep_cue(win, ui_elements, board_renderer, deck_renderer,
                                     token_renderer, game_state, fdl=fdl)
                edf_result = 'seq_npc_caught_user' if result == 'all_success' else 'npc_caught_user'
                _edf_msg(aoi_manager, f"TRIAL_END {_pc_trial_id} MATCH 1 RESULT {edf_result}")
                _ljack(labjack_handle, TRIG_TRIAL_END)
                game_state.advance_round()
                board_renderer.update_board(game_state.board)
                deck_renderer.update_deck(game_state.deck)
                if aoi_manager:
                    aoi_manager.update_deck(game_state.deck)
                print(f"[ROUND ADVANCE] 잡기(문어) → 라운드 {game_state.current_round} 시작")
                game_state.end_pc_turn()
                _run_round_break(win, ui_elements, board_renderer, deck_renderer,
                                 token_renderer, game_state, fdl=fdl)
                print(f"[문어] flight 잡음! PC 턴 종료 → 사용자 턴")
                return 'continue'

            # 일반/seq 성공: PC 턴 계속
            edf_result = 'seq_all_success' if result == 'all_success' else 'success'
            _edf_msg(aoi_manager, f"TRIAL_END {_pc_trial_id} MATCH 1 RESULT {edf_result}")
            _ljack(labjack_handle, TRIG_TRIAL_END)
            print(f"[문어] 성공({result}), 다음 타겟으로 계속")
            _pc_interval_deadline = core.getTime() + TRIAL_INTERVAL
            while core.getTime() < _pc_interval_deadline:
                _draw_game_screen(win, ui_elements, board_renderer, deck_renderer,
                                  token_renderer, game_state, pc_target_pos)
                blink_frame_marker(win)
                win.flip()
                if fdl:
                    fdl.after_flip(core.getTime(), trial_id=_pc_trial_id, context='trial_interval')
                if aoi_manager:
                    aoi_manager.update(core.getTime())
            continue

        elif result == 'failure':
            if card_pos:
                game_state.deck.hide_card(card_pos[0], card_pos[1])
            pc_fail_result = "seq_failure" if _checked_as_pc_seq else "failure"
            _edf_msg(aoi_manager, f"TRIAL_END {_pc_trial_id} MATCH 0 RESULT {pc_fail_result}")
            _ljack(labjack_handle, TRIG_TRIAL_END)
            print(f"[문어] {'순차 ' if _checked_as_pc_seq else ''}실패, 턴 종료")
            return 'continue'

    return 'continue'


def _run_round_break(win, ui_elements, board_renderer, deck_renderer, token_renderer, game_state,
                     fdl=None):
    """
    라운드 간 휴식 화면 표시 (ROUND_BREAK_DURATION 초 카운트다운).
    """
    if fdl:
        fdl.reset()
    # advance_round()가 이미 호출된 후이므로 current_round는 새 라운드 번호
    completed_round = game_state.current_round - 1
    next_round = game_state.current_round
    for remaining in range(ROUND_BREAK_DURATION, 0, -1):
        _second_deadline = core.getTime() + 1.0
        while core.getTime() < _second_deadline:
            _draw_game_screen(win, ui_elements, board_renderer, deck_renderer, token_renderer,
                              game_state, highlighted_pos=None)
            ui_elements.draw_round_break(completed_round, next_round, remaining)
            blink_frame_marker(win)
            win.flip()
            if fdl:
                fdl.after_flip(core.getTime(), context='round_break')


def _get_clicked_card(mouse_pos, deck_rows, deck_cols):
    screen_x = mouse_pos[0] + WIDTH / 2
    screen_y = HEIGHT / 2 - mouse_pos[1]

    for row in range(deck_rows):
        for col in range(deck_cols):
            left = DECK_LEFT_EDGE + col * (DECK_CARD_WIDTH + DECK_CARD_SPACING)
            right = left + DECK_CARD_WIDTH
            top = BOARD_DECK_TOP_MARGIN + row * (DECK_CARD_HEIGHT + DECK_CARD_SPACING)
            bottom = top + DECK_CARD_HEIGHT

            if left <= screen_x <= right and top <= screen_y <= bottom:
                return (row, col)

    return None


def _draw_game_screen(win, ui_elements, board_renderer, deck_renderer, token_renderer,
                      game_state=None, highlighted_pos=None):

    seq_cells  = game_state.seq_memory_targets if (game_state and game_state.seq_memory_active) else None
    done_cells = game_state.seq_memory_targets[:game_state.seq_memory_step] if seq_cells else None
    board_renderer.draw(highlighted_pos, seq_cells=seq_cells, done_cells=done_cells)
    deck_renderer.draw()
    token_renderer.draw()

    if game_state is not None:
        # 턴 제한시간 비율로 프로그레스 바 갱신
        bar_ratio = (game_state.timer.get_remaining()
                     / max(1, game_state.timer.time_limit))
        ui_elements.set_round_display(game_state.current_round, game_state.total_rounds)
        ui_elements.draw_progress_bar(bar_ratio)

        ui_elements.draw_score(game_state.round_score, game_state.pc_round_score)
        ui_elements.update_ranking(game_state.user_score, game_state.pc_score)
    else:
        ui_elements.draw_progress_bar()
        ui_elements.score_text.draw()

    ui_elements.draw_ranking()
    ui_elements.timer_text.draw()
    ui_elements.round_text.draw()
    ui_elements.message_text.draw()
    ui_elements.instruction_text.draw()


def _show_start_cue(
    win,
    ui_elements,
    board_renderer,
    deck_renderer,
    token_renderer,
    game_state,
    selected_token,
    turn_count,
    timer_display_text,
    target_pos,
    sounds=None,
    fdl=None,
):
    """다음 시도를 시작하기 직전 문구 표시"""
    if fdl:
        fdl.reset()
    ui_elements.set_user_turn_hud(
        selected_token=selected_token,
        turn_count=turn_count,
        timer_display_text=timer_display_text,
    )
    _draw_game_screen(
        win,
        ui_elements,
        board_renderer,
        deck_renderer,
        token_renderer,
        game_state,
        target_pos,
    )
    sound_play(sounds, 'qbeep')
    ui_elements.draw_start_cue("시작!")
    trigger_frame_marker()   # 이벤트: 시행 시작 큐
    blink_frame_marker(win)
    win.flip()
    if fdl:
        fdl.after_flip(core.getTime(), context='start_cue')
    _cue_deadline = core.getTime() + START_CUE_DURATION
    while core.getTime() < _cue_deadline:
        _draw_game_screen(win, ui_elements, board_renderer, deck_renderer,
                          token_renderer, game_state, target_pos)
        ui_elements.draw_start_cue("시작!")
        blink_frame_marker(win)
        win.flip()
        if fdl:
            fdl.after_flip(core.getTime(), context='start_cue')


def _show_reset_prep_cue(win, ui_elements, board_renderer, deck_renderer, token_renderer, game_state,
                         fdl=None):
    """잡기 이벤트 후 토큰 위치 초기화 유예 시간.
    """
    if fdl:
        fdl.reset()
    ui_elements.message_text.text = "준비..."
    ui_elements.message_text.color = TEXT_COLOR
    _draw_game_screen(win, ui_elements, board_renderer, deck_renderer, token_renderer,
                      game_state, highlighted_pos=None)
    ui_elements.message_text.draw()
    trigger_frame_marker()   # 이벤트: 위치 초기화 유예 시작
    blink_frame_marker(win)
    win.flip()
    if fdl:
        fdl.after_flip(core.getTime(), context='catch_prep')
    _prep_deadline = core.getTime() + CATCH_RESET_PREP_DURATION
    while core.getTime() < _prep_deadline:
        _draw_game_screen(win, ui_elements, board_renderer, deck_renderer, token_renderer,
                          game_state, highlighted_pos=None)
        ui_elements.message_text.draw()
        blink_frame_marker(win)
        win.flip()
        if fdl:
            fdl.after_flip(core.getTime(), context='catch_prep')
