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

try:
    from ..view_func.frame_marker import blink_frame_marker, trigger_frame_marker
    from ..sounds import load_sounds, play as sound_play
    from ..utils.labjack_triggers import (set_trigger, reset_trigger,
                                           TRIG_TRIAL_START, TRIG_TRIAL_END,
                                           TRIG_CARD_CLICK, TRIG_CARD_FLIP_USER, TRIG_CARD_FLIP_PC,
                                           TRIG_FEEDBACK_SUCCESS, TRIG_FEEDBACK_FAILURE, TRIG_FEEDBACK_TIMEOUT,
                                           TRIG_SEQ_ACTIVATE, TRIG_SEQ_ALL_SUCCESS, TRIG_SEQ_FAILURE)
    from ..save_func.trial_saver import save_trial
    from ..utils.frame_drop_log import FrameDropLogger
except ImportError:
    from view_func.frame_marker import blink_frame_marker, trigger_frame_marker
    from sounds import load_sounds, play as sound_play
    from utils.labjack_triggers import (set_trigger, reset_trigger,
                                        TRIG_TRIAL_START, TRIG_TRIAL_END,
                                        TRIG_CARD_CLICK, TRIG_CARD_FLIP_USER, TRIG_CARD_FLIP_PC,
                                        TRIG_FEEDBACK_SUCCESS, TRIG_FEEDBACK_FAILURE, TRIG_FEEDBACK_TIMEOUT,
                                        TRIG_SEQ_ACTIVATE, TRIG_SEQ_ALL_SUCCESS, TRIG_SEQ_FAILURE)
    from save_func.trial_saver import save_trial
    from utils.frame_drop_log import FrameDropLogger


START_CUE_DURATION = 0.5


def _ljack(win, handle, code):
    if handle:
        set_trigger(handle, code)
        win.callOnFlip(reset_trigger, handle)


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
    Non-blocking 프레임 머신 기반 사용자 턴 제어.

    상태 전이:
      TRIAL_INIT → WAIT_INPUT → CARD_FLIPPING
                                  ├─ step_success        → WAIT_INPUT  (seq 중간 스텝)
                                  ├─ success/all_success → FEEDBACK → TRIAL_INTERVAL → START_CUE → TRIAL_INIT
                                  └─ failure             → FEEDBACK → (턴 종료)
      WAIT_INPUT ─ timeout      → FEEDBACK → (턴 종료)
    """

    # 1. 닭 선택 단계 (토큰이 선택되지 않았을 때만)
    if game_state.selected_token is None:
        print(f"[USER TURN] 닭 선택 단계 (턴 {game_state.turn_count})")
        selected = run_token_selection_phase(win, game_state, ui_elements,
                                            board_renderer, deck_renderer, token_renderer,
                                            sounds=sounds, labjack_handle=labjack_handle)
        if selected == 'exit':
            return 'exit'
        if not game_state.confirm_selection():
            return 'continue'
        print(f"[USER TURN] {game_state.selected_token.upper()} 선택, 카드 선택 시작")

    # ── 상태기계 초기화 ────────────────────────────────────────────────────
    _sub_phase        = 'TRIAL_INIT'
    _trial_id         = None
    _pre_flip_lj_code = 0       # 다음 flip 에 callOnFlip 으로 전송할 TTL 코드

    # 클릭/결과 공유 변수 (WAIT_INPUT → CARD_FLIPPING → FEEDBACK)
    result         = None
    card_row       = None
    card_col       = None
    was_seq_memory = False

    # 피드백 공유 변수 (CARD_FLIPPING/WAIT_INPUT → FEEDBACK)
    _feedback_msg        = ''
    _feedback_color      = DARK_GREY
    _feedback_code       = 0
    _feedback_is_success = False
    _feedback_is_timeout = False
    _edf_result_str      = ''
    deadline             = 0.0

    # ── [Main User Turn Loop] ──────────────────────────────────────────────
    while game_state.phase == game_state.PHASE_GAME_PLAY and \
          game_state.current_turn == game_state.TURN_USER:

        current_time = core.getTime()

        # [A] 타겟 위치 결정
        target_pos = (game_state.get_seq_memory_current_target()
                      if game_state.seq_memory_active
                      else game_state.get_target_position())

        # [B] 상태 머신 ─────────────────────────────────────────────────────

        # ── 1. 새 시행 초기화 ──────────────────────────────────────────────
        if _sub_phase == 'TRIAL_INIT':
            _trial_id = game_state.get_next_trial_id()
            game_state.try_activate_seq_memory()

            if aoi_manager:
                aoi_manager.current_trial_id = _trial_id
                aoi_manager.is_seq_memory    = game_state.seq_memory_active
                aoi_manager.seq_memory_step  = (game_state.seq_memory_step
                                                if game_state.seq_memory_active else None)
            if game_state.seq_memory_active:
                trigger_frame_marker()

            _edf_msg(aoi_manager,
                     f"TRIAL_START {_trial_id} USER"
                     f" ROUND {game_state.current_round}"
                     f" TURN {game_state.turn_count}"
                     + (f" SEQ_MEMORY step 0/{len(game_state.seq_memory_targets)}"
                        if game_state.seq_memory_active else ""))
            game_state.current_trial_start_psychopy = core.getTime()
            _pre_flip_lj_code = TRIG_TRIAL_START
            game_state.timer.reset()
            _sub_phase = 'WAIT_INPUT'

        # ── 2. 입력 대기 ───────────────────────────────────────────────────
        elif _sub_phase == 'WAIT_INPUT':
            if game_state.timer.is_expired():
                print(f"[USER TURN] 타임아웃!")
                sound_play(sounds, 'error')
                _timeout_str = "seq_timeout" if game_state.seq_memory_active else "timeout"
                _edf_msg(aoi_manager, f"TRIAL_END {_trial_id} MATCH 0 RESULT {_timeout_str}")
                _feedback_msg        = "시간 초과"
                _feedback_color      = DARK_GREY
                _feedback_code       = TRIG_FEEDBACK_TIMEOUT
                _feedback_is_success = False
                _feedback_is_timeout = True
                deadline             = current_time + FEEDBACK_DURATION
                _pre_flip_lj_code    = _feedback_code
                _sub_phase           = 'FEEDBACK'

            elif mouse.getPressed()[0]:
                card_pos = _get_clicked_card(mouse.getPos(), game_state.deck.rows,
                                             game_state.deck.cols)
                if card_pos is not None:
                    card_row, card_col = card_pos

                    # 클릭 onset 트리거 (VSync 전 즉시 전송)
                    _ljack(win, labjack_handle, TRIG_CARD_CLICK)

                    was_seq_memory = game_state.seq_memory_active
                    if was_seq_memory:
                        result = game_state.check_seq_memory_card(card_row, card_col)
                        print(f"[USER TURN][SEQ {game_state.seq_memory_step}/"
                              f"{len(game_state.seq_memory_targets)}] "
                              f"카드={card_pos}, 결과={result}")
                    else:
                        result = game_state.user_click_card(card_row, card_col,
                                                            defer_success_move=True)
                        print(f"[USER TURN] 카드={card_pos}, 결과={result}")

                    if save_paths and game_state.trial_history:
                        save_trial(save_paths['trial'], game_state.trial_history[-1],
                                   game_state, subject_id)

                    sound_play(sounds, 'flip')
                    trigger_frame_marker()
                    _pre_flip_lj_code = TRIG_CARD_FLIP_USER
                    deadline           = current_time + CARD_FLIP_DURATION
                    _sub_phase         = 'CARD_FLIPPING'

        # ── 3. 카드 뒤집기 대기 ────────────────────────────────────────────
        elif _sub_phase == 'CARD_FLIPPING':
            if current_time >= deadline:

                if result == 'step_success':
                    # seq 중간 스텝 성공: 피드백 없이 다음 스텝으로
                    step_now   = game_state.seq_memory_step
                    step_total = len(game_state.seq_memory_targets)
                    game_state.deck.hide_card(card_row, card_col)
                    _trial_id = game_state.get_next_trial_id()
                    if aoi_manager:
                        aoi_manager.current_trial_id = _trial_id
                        aoi_manager.is_seq_memory    = True
                        aoi_manager.seq_memory_step  = game_state.seq_memory_step
                    _edf_msg(aoi_manager,
                             f"TRIAL_START {_trial_id} USER"
                             f" ROUND {game_state.current_round}"
                             f" TURN {game_state.turn_count}"
                             f" SEQ_MEMORY step {step_now}/{step_total}")
                    game_state.current_trial_start_psychopy = core.getTime()
                    _pre_flip_lj_code = TRIG_TRIAL_START
                    _sub_phase        = 'WAIT_INPUT'

                elif result in ('success', 'all_success'):
                    sound_play(sounds, 'correct')
                    if result == 'all_success':
                        step_total      = len(game_state.seq_memory_targets)
                        _feedback_msg   = f"순차 {step_total}/{step_total} 완료!  {step_total}칸 이동!"
                        _feedback_color = GOLD
                        _feedback_code  = TRIG_SEQ_ALL_SUCCESS
                    else:
                        _feedback_msg   = "성공"
                        _feedback_color = PURPLE
                        _feedback_code  = TRIG_FEEDBACK_SUCCESS
                    _feedback_is_success = True
                    _feedback_is_timeout = False
                    deadline             = current_time + FEEDBACK_DURATION
                    _pre_flip_lj_code    = _feedback_code
                    _sub_phase           = 'FEEDBACK'

                else:  # failure
                    sound_play(sounds, 'error')
                    if was_seq_memory:
                        _feedback_msg   = "순차 실패 - 이동 없음"
                        _feedback_color = DARK_GREY
                        _feedback_code  = TRIG_SEQ_FAILURE
                        _edf_result_str = 'seq_failure'
                    else:
                        _feedback_msg   = "실패"
                        _feedback_color = DARK_GREY
                        _feedback_code  = TRIG_FEEDBACK_FAILURE
                        _edf_result_str = 'failure'
                    _edf_msg(aoi_manager,
                             f"TRIAL_END {_trial_id} MATCH 0 RESULT {_edf_result_str}")
                    _feedback_is_success = False
                    _feedback_is_timeout = False
                    deadline             = current_time + FEEDBACK_DURATION
                    _pre_flip_lj_code    = _feedback_code
                    _sub_phase           = 'FEEDBACK'

        # ── 4. 피드백 ──────────────────────────────────────────────────────
        elif _sub_phase == 'FEEDBACK':
            if current_time >= deadline:
                if _feedback_is_success:
                    if result == 'all_success':
                        move_result = game_state.complete_seq_memory_move()
                        edf_result  = 'seq_all_success'
                    else:
                        move_result = game_state.complete_user_success_move()
                        edf_result  = 'success'
                    game_state.deck.hide_card(card_row, card_col)

                    # 잡기 이벤트 (예외적 분기 — 짧은 블로킹 허용)
                    if move_result == 'user_caught_npc':
                        board_renderer.refresh()
                        deck_renderer.refresh()
                        sound_play(sounds, 'win')
                        _catch_end = core.getTime() + FEEDBACK_DURATION * 2
                        while core.getTime() < _catch_end:
                            _draw_game_screen(win, ui_elements, board_renderer,
                                              deck_renderer, token_renderer,
                                              game_state, highlighted_pos=None)
                            ui_elements.draw_feedback_message(
                                f"문어를 잡았다!  +{SCORE_CATCH_BONUS}점", GOLD)
                            blink_frame_marker(win)
                            win.flip()
                            if fdl:
                                fdl.after_flip(core.getTime(), trial_id=_trial_id,
                                               context='catch_feedback')
                            if aoi_manager:
                                aoi_manager.update(core.getTime())
                        _show_reset_prep_cue(win, ui_elements, board_renderer,
                                             deck_renderer, token_renderer,
                                             game_state, fdl=fdl)
                        _edf_msg(aoi_manager,
                                 f"TRIAL_END {_trial_id} MATCH 1 RESULT user_caught_npc")
                        _ljack(win, labjack_handle, TRIG_TRIAL_END)
                        game_state.advance_round()
                        board_renderer.update_board(game_state.board)
                        deck_renderer.update_deck(game_state.deck)
                        if aoi_manager:
                            aoi_manager.update_deck(game_state.deck)
                        game_state.selected_token = None
                        game_state.timer.reset()
                        game_state.phase = game_state.PHASE_TOKEN_SELECTION
                        print(f"[ROUND ADVANCE] 잡기(사용자) → 라운드 {game_state.current_round} 시작")
                        _run_round_break(win, ui_elements, board_renderer,
                                         deck_renderer, token_renderer, game_state, fdl=fdl)
                        return 'continue'

                    _edf_msg(aoi_manager,
                             f"TRIAL_END {_trial_id} MATCH 1 RESULT {edf_result}")
                    _ljack(win, labjack_handle, TRIG_TRIAL_END)
                    deadline   = current_time + TRIAL_INTERVAL
                    _sub_phase = 'TRIAL_INTERVAL'

                else:  # failure 또는 timeout
                    # failure: 카드 숨기기 + TRIG_TRIAL_END / timeout: 두 가지 모두 생략
                    if not _feedback_is_timeout:
                        game_state.deck.hide_card(card_row, card_col)
                        _ljack(win, labjack_handle, TRIG_TRIAL_END)
                    print(f"[USER TURN] {'타임아웃' if _feedback_is_timeout else '실패'}, 턴 종료")
                    game_state.end_user_turn()
                    return 'continue'

        # ── 5. 시행 간 간격 ────────────────────────────────────────────────
        elif _sub_phase == 'TRIAL_INTERVAL':
            if current_time >= deadline:
                deadline = current_time + START_CUE_DURATION
                sound_play(sounds, 'qbeep')
                trigger_frame_marker()
                if fdl:
                    fdl.reset()
                _sub_phase = 'START_CUE'

        # ── 6. 시작 큐 ─────────────────────────────────────────────────────
        elif _sub_phase == 'START_CUE':
            if current_time >= deadline:
                game_state.timer.reset()
                _sub_phase = 'TRIAL_INIT'

        # [C] 공통 렌더링 ────────────────────────────────────────────────────
        ui_elements.set_user_turn_hud(
            selected_token=game_state.selected_token,
            turn_count=game_state.turn_count,
            timer_display_text=game_state.timer.get_display_text(),
        )

        # 피드백 중에는 타겟 하이라이트 없음 (원본 run_feedback_phase 동작과 동일)
        _render_target = None if _sub_phase == 'FEEDBACK' else target_pos
        _draw_game_screen(win, ui_elements, board_renderer, deck_renderer,
                          token_renderer, game_state, _render_target)

        # 오버레이: 게임 화면 위에 렌더링 (나중에 draw 된 항목이 앞에 표시됨)
        if _sub_phase == 'FEEDBACK':
            ui_elements.draw_feedback_message(_feedback_msg, _feedback_color)
        elif _sub_phase == 'START_CUE':
            ui_elements.draw_start_cue("시작!")

        blink_frame_marker(win)

        # 예약된 TTL 트리거: 이번 flip 직전에 callOnFlip 으로 전송
        _queued = bool(_pre_flip_lj_code and labjack_handle)
        if _queued:
            _flip_trigger(win, labjack_handle, _pre_flip_lj_code)
            _pre_flip_lj_code = 0

        win.flip()

        # [D] 사후 처리
        if fdl:
            fdl.after_flip(core.getTime(), trial_id=_trial_id, context=_sub_phase)
        if aoi_manager:
            aoi_manager.update(core.getTime())
        if _queued:
            _flip_reset(win, labjack_handle)

        if KEY_EXIT in event.getKeys():
            return 'exit'

    return 'continue'


def _run_pc_turn(win, game_state, ui_elements, board_renderer, deck_renderer, token_renderer,
                 aoi_manager=None, labjack_handle=None, save_paths=None, subject_id='', sounds=None,
                 fdl=None):
    """
    Non-blocking 프레임 머신 기반 PC 턴 제어.

    상태 전이:
      TRIAL_INIT → PC_THINK → CARD_FLIPPING
                                ├─ step_success        → PC_THINK (seq 다음 스텝)
                                ├─ success/all_success → FEEDBACK → TRIAL_INTERVAL → TRIAL_INIT
                                └─ failure             → FEEDBACK → (턴 종료)
    """

    # ── 상태기계 초기화 ────────────────────────────────────────────────────
    _sub_phase        = 'TRIAL_INIT'
    _pc_trial_id      = None
    _pre_flip_lj_code = 0       # 다음 flip 에 callOnFlip 으로 전송할 TTL 코드
    _is_seq_continue  = False   # step_success 이후 seq 연속 스텝 여부
    pc_target_pos     = None

    # 카드 실행 결과 공유 변수 (PC_THINK → CARD_FLIPPING → FEEDBACK)
    result          = None
    card_pos        = None
    _checked_as_pc_seq = False

    # 피드백 공유 변수 (CARD_FLIPPING → FEEDBACK)
    _feedback_msg          = ''
    _feedback_color        = DARK_GREY
    _feedback_code         = 0
    _feedback_is_success   = False
    _feedback_highlighted  = None   # 피드백 중 하이라이트할 위치
    _edf_result_str        = ''
    deadline               = 0.0

    # ── [Main PC Turn Loop] ────────────────────────────────────────────────
    while game_state.current_turn == game_state.TURN_PC:

        current_time = core.getTime()

        # [A] 타겟 위치 결정 (매 프레임 갱신)
        if game_state.seq_memory_active:
            pc_target_pos = game_state.get_seq_memory_current_target()
        else:
            pc_target_pos = game_state.tokens.get_target_position('octopus')

        # [B] 상태 머신 ─────────────────────────────────────────────────────

        # ── 1. 새 시행 초기화 (think 시작 프레임) ─────────────────────────
        if _sub_phase == 'TRIAL_INIT':
            print(f"[문어] 카드 선택 시작 (턴 {game_state.turn_count})")
            trigger_frame_marker()          # 이벤트: PC 턴 시작
            _pre_flip_lj_code = TRIG_TRIAL_START
            deadline  = current_time + PC_THINK_TIME
            _sub_phase = 'PC_THINK'

        # ── 2. PC 생각 시간 ────────────────────────────────────────────────
        elif _sub_phase == 'PC_THINK':
            if current_time >= deadline:
                _pc_trial_id     = game_state.get_next_trial_id()
                _was_pc_seq      = game_state.seq_memory_active

                if not _is_seq_continue:
                    game_state.try_activate_pc_seq_memory()
                    if game_state.seq_memory_active and not _was_pc_seq:
                        _ljack(win, labjack_handle, TRIG_SEQ_ACTIVATE)
                    if game_state.seq_memory_active:
                        pc_target_pos = game_state.get_seq_memory_current_target()

                _is_seq_continue = False    # 다음 스텝을 위해 리셋

                if aoi_manager:
                    aoi_manager.current_trial_id = _pc_trial_id
                    aoi_manager.is_seq_memory    = game_state.seq_memory_active
                    aoi_manager.seq_memory_step  = (game_state.seq_memory_step
                                                    if game_state.seq_memory_active else None)

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

                print(f"[PC TURN] 카드={card_pos}, 결과={result}")

                if save_paths and game_state.trial_history:
                    save_trial(save_paths['trial'], game_state.trial_history[-1],
                               game_state, subject_id)

                sound_play(sounds, 'npc_flip')
                trigger_frame_marker()      # 이벤트: PC 카드 뒤집기
                _pre_flip_lj_code = TRIG_CARD_FLIP_PC
                deadline  = current_time + CARD_FLIP_DURATION
                _sub_phase = 'CARD_FLIPPING'

        # ── 3. 카드 뒤집기 대기 ────────────────────────────────────────────
        elif _sub_phase == 'CARD_FLIPPING':
            if current_time >= deadline:

                if result == 'step_success':
                    # seq 중간 스텝 성공: 피드백 없이 다음 스텝으로
                    step_now   = game_state.seq_memory_step
                    step_total = len(game_state.seq_memory_targets)
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
                             f" SEQ_MEMORY step {step_now}/{step_total}")
                    game_state.current_trial_start_psychopy = core.getTime()
                    pc_target_pos     = game_state.get_seq_memory_current_target()
                    _pre_flip_lj_code = TRIG_TRIAL_START
                    _is_seq_continue  = True
                    deadline   = current_time + PC_THINK_TIME
                    _sub_phase = 'PC_THINK'

                elif result in ('success', 'all_success'):
                    sound_play(sounds, 'correct')
                    if result == 'all_success':
                        step_total      = len(game_state.seq_memory_targets)
                        _feedback_msg   = f"문어 순차 {step_total}칸 완료!"
                        _feedback_color = GOLD
                        _feedback_code  = TRIG_SEQ_ALL_SUCCESS
                    else:
                        _feedback_msg   = "문어 성공"
                        _feedback_color = PURPLE
                        _feedback_code  = 0
                    _feedback_is_success  = True
                    _feedback_highlighted = pc_target_pos
                    deadline              = current_time + FEEDBACK_DURATION
                    _pre_flip_lj_code     = _feedback_code
                    _sub_phase            = 'FEEDBACK'

                else:  # failure
                    sound_play(sounds, 'error')
                    if _checked_as_pc_seq:
                        _feedback_msg   = "문어 순차 실패"
                        _feedback_color = DARK_GREY
                        _feedback_code  = TRIG_SEQ_FAILURE
                        _edf_result_str = 'seq_failure'
                    else:
                        _feedback_msg   = "문어 실패"
                        _feedback_color = DARK_GREY
                        _feedback_code  = 0
                        _edf_result_str = 'failure'
                    _edf_msg(aoi_manager,
                             f"TRIAL_END {_pc_trial_id} MATCH 0 RESULT {_edf_result_str}")
                    _feedback_is_success  = False
                    _feedback_highlighted = pc_target_pos
                    deadline              = current_time + FEEDBACK_DURATION
                    _pre_flip_lj_code     = _feedback_code
                    _sub_phase            = 'FEEDBACK'

        # ── 4. 피드백 ──────────────────────────────────────────────────────
        elif _sub_phase == 'FEEDBACK':
            if current_time >= deadline:
                if _feedback_is_success:
                    if result == 'all_success':
                        move_result = game_state.complete_pc_seq_memory_move()
                        edf_result  = 'seq_all_success'
                    else:
                        move_result = game_state.complete_pc_success_move()
                        edf_result  = 'success'
                    if card_pos:
                        game_state.deck.hide_card(card_pos[0], card_pos[1])

                    # 잡기 이벤트 (예외적 분기 — 짧은 블로킹 허용)
                    if move_result == 'npc_caught_user':
                        board_renderer.refresh()
                        deck_renderer.refresh()
                        sound_play(sounds, 'lose')
                        _catch_end = core.getTime() + FEEDBACK_DURATION * 2
                        while core.getTime() < _catch_end:
                            _draw_game_screen(win, ui_elements, board_renderer,
                                              deck_renderer, token_renderer,
                                              game_state, highlighted_pos=None)
                            ui_elements.draw_feedback_message(
                                f"잡혔다!  {SCORE_CAUGHT_PENALTY}점", ORANGE_RED)
                            blink_frame_marker(win)
                            win.flip()
                            if fdl:
                                fdl.after_flip(core.getTime(), trial_id=_pc_trial_id,
                                               context='catch_feedback')
                            if aoi_manager:
                                aoi_manager.update(core.getTime())
                        _show_reset_prep_cue(win, ui_elements, board_renderer,
                                             deck_renderer, token_renderer,
                                             game_state, fdl=fdl)
                        edf_result = 'seq_npc_caught_user' if result == 'all_success' else 'npc_caught_user'
                        _edf_msg(aoi_manager,
                                 f"TRIAL_END {_pc_trial_id} MATCH 1 RESULT {edf_result}")
                        _ljack(win, labjack_handle, TRIG_TRIAL_END)
                        game_state.advance_round()
                        board_renderer.update_board(game_state.board)
                        deck_renderer.update_deck(game_state.deck)
                        if aoi_manager:
                            aoi_manager.update_deck(game_state.deck)
                        print(f"[ROUND ADVANCE] 잡기(문어) → 라운드 {game_state.current_round} 시작")
                        game_state.end_pc_turn()
                        _run_round_break(win, ui_elements, board_renderer,
                                         deck_renderer, token_renderer, game_state, fdl=fdl)
                        print(f"[문어] flight 잡음! PC 턴 종료 → 사용자 턴")
                        return 'continue'

                    _edf_msg(aoi_manager,
                             f"TRIAL_END {_pc_trial_id} MATCH 1 RESULT {edf_result}")
                    _ljack(win, labjack_handle, TRIG_TRIAL_END)
                    print(f"[문어] 성공({result}), 다음 타겟으로 계속")
                    deadline   = current_time + TRIAL_INTERVAL
                    _sub_phase = 'TRIAL_INTERVAL'

                else:  # failure
                    if card_pos:
                        game_state.deck.hide_card(card_pos[0], card_pos[1])
                    _ljack(win, labjack_handle, TRIG_TRIAL_END)
                    print(f"[문어] {'순차 ' if _checked_as_pc_seq else ''}실패, 턴 종료")
                    game_state.end_pc_turn()
                    return 'continue'

        # ── 5. 시행 간 간격 ────────────────────────────────────────────────
        elif _sub_phase == 'TRIAL_INTERVAL':
            if current_time >= deadline:
                _sub_phase = 'TRIAL_INIT'

        # [C] 공통 렌더링 ────────────────────────────────────────────────────
        ui_elements.set_pc_turn_hud(
            turn_count=game_state.turn_count,
            target_pos=pc_target_pos,
            timer_label="문어 턴",
        )

        # 피드백 중에는 저장된 하이라이트 위치 사용 (타겟이 이미 이동했을 수 있음)
        _render_target = _feedback_highlighted if _sub_phase == 'FEEDBACK' else pc_target_pos
        _draw_game_screen(win, ui_elements, board_renderer, deck_renderer,
                          token_renderer, game_state, _render_target)

        # 오버레이: 게임 화면 위에 렌더링
        if _sub_phase == 'FEEDBACK':
            ui_elements.draw_feedback_message(_feedback_msg, _feedback_color)

        blink_frame_marker(win)

        # 예약된 TTL 트리거: 이번 flip 직전에 callOnFlip 으로 전송
        _queued = bool(_pre_flip_lj_code and labjack_handle)
        if _queued:
            _flip_trigger(win, labjack_handle, _pre_flip_lj_code)
            _pre_flip_lj_code = 0

        win.flip()

        # [D] 사후 처리
        if fdl:
            fdl.after_flip(core.getTime(), trial_id=_pc_trial_id, context=_sub_phase)
        if aoi_manager:
            aoi_manager.update(core.getTime())
        if _queued:
            _flip_reset(win, labjack_handle)

    return 'continue'


def _run_round_break(win, ui_elements, board_renderer, deck_renderer, token_renderer, game_state,
                     fdl=None):
    """
    라운드 간 휴식 화면 표시 (ROUND_BREAK_DURATION 초 카운트다운).
    """
    if fdl:
        fdl.reset()
    completed_round = game_state.current_round - 1
    next_round      = game_state.current_round
    _break_end      = core.getTime() + ROUND_BREAK_DURATION
    while core.getTime() < _break_end:
        remaining = max(1, int(_break_end - core.getTime()) + 1)
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
