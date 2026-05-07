import logging
import sys
from pathlib import Path

try:
    from ..config import (
        TURN_TIME_LIMIT, DEFAULT_GAME_MODE, GAME_MODES, GAME_TIME_LIMIT,
        TOTAL_ROUNDS, ROUND_TURN_LIMITS,
        DIFFICULTY_SEQUENCE, DIFFICULTY_SCORE_THRESHOLD,
        BONUS_SEQUENCE,
    )
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from config import (
        TURN_TIME_LIMIT, DEFAULT_GAME_MODE, GAME_MODES, GAME_TIME_LIMIT,
        TOTAL_ROUNDS, ROUND_TURN_LIMITS,
        DIFFICULTY_SEQUENCE, DIFFICULTY_SCORE_THRESHOLD,
        BONUS_SEQUENCE,
    )

from game_func.board_class import ConditionBoard
from game_func.deck_class import MainDeck
from game_func.token_class import TokenManager
from game_func.npc_ai import NPCAI
from game_func.score_system import ScoreSystem
from game_func.adaptive_system import AdaptiveSystem
from game_func.seq_memory import SeqMemory
from game_func.turn_executor import TurnExecutor
from utils.timer import GameTimer
from utils.events import RoundEvent
from utils.helpers import deep_merge

_log = logging.getLogger(__name__)

# All token names in canonical order; used wherever we need to iterate over tokens.
_TOKEN_NAMES = ('chase', 'flight', 'octopus')


class GameState:
    """Central game-state orchestrator.

    Owns all sub-systems (board, deck, tokens, score, AI …) and exposes a
    single, stable public API consumed by phase, view, and save modules.
    """

    # ── phase constants ───────────────────────────────────────────────────────
    PHASE_NOT_STARTED     = 'not_started'
    PHASE_TOKEN_SELECTION = 'token_selection'
    PHASE_GAME_PLAY       = 'game_play'
    PHASE_VICTORY         = 'victory'
    PHASE_DEFEAT          = 'defeat'

    # ── turn constants ────────────────────────────────────────────────────────
    TURN_USER = 'user'
    TURN_PC   = 'pc'

    def __init__(self, selected_mode_id=None):
        self.available_modes  = GAME_MODES
        self.selected_mode_id = selected_mode_id or DEFAULT_GAME_MODE
        self.selected_mode    = self.available_modes.get(
            self.selected_mode_id, self.available_modes[DEFAULT_GAME_MODE]
        )

        self.difficulty_index = 0
        self._init_subsystems()
        self._init_state()
        _log.info("[MODE] selected=%s, profile=%s", self.selected_mode_id, self.selected_mode)

    # ── initialisation helpers ────────────────────────────────────────────────

    def _init_subsystems(self):
        """Build all stateful sub-systems. Call after mode/difficulty are set."""
        self.board  = self._build_board_for_round(1)
        self.deck   = self._build_deck_for_difficulty()
        self.tokens = TokenManager(mode_profile=self.selected_mode, board=self.board)

        self.base_random_rate = 1.0 / max(1, self.deck.rows * self.deck.cols)
        self.npc_ai   = NPCAI(success_rate=self.base_random_rate)
        self.score    = ScoreSystem()
        self.adaptive = AdaptiveSystem(self.base_random_rate)
        self.seq_mem  = SeqMemory()
        self._turns   = TurnExecutor(self)

        self.timer      = GameTimer(time_limit=ROUND_TURN_LIMITS[0])
        self.game_timer = GameTimer(time_limit=GAME_TIME_LIMIT)

    def _init_state(self):
        """Initialise volatile game-state counters. Called from __init__ only."""
        self.phase          = self.PHASE_NOT_STARTED
        self.current_turn   = self.TURN_USER
        self.selected_token = None

        self.current_round        = 1
        self.total_rounds         = TOTAL_ROUNDS
        self.turn_time_limit      = self._turn_limit_for_round(1)
        self.timer.time_limit     = self.turn_time_limit

        self.turn_count                   = 0
        self.user_move_count              = 0
        self.pc_move_count                = 0
        self.trial_history                = []
        self.trial_id                     = 0
        self.round_event_history          = []
        self.conjunctive_round_count      = 0
        self.current_trial_start_psychopy = 0.0
        self._round_start_score           = 0
        self._pc_round_start_score        = 0

    # ── sub-system property delegation (backward compatibility) ───────────────

    @property
    def user_score(self):       return self.score.user_score
    @property
    def pc_score(self):         return self.score.pc_score
    @property
    def user_combo(self):       return self.score.user_combo
    @property
    def pc_combo(self):         return self.score.pc_combo
    @property
    def user_catch_count(self): return self.score.user_catch_count
    @property
    def pc_catch_count(self):   return self.score.pc_catch_count

    @property
    def user_seen_cards(self):    return self.adaptive.user_seen_cards
    @property
    def npc_seen_cards(self):     return self.adaptive.npc_seen_cards
    @property
    def user_accuracy_ewma(self): return self.adaptive.user_accuracy_ewma

    @property
    def seq_memory_active(self):  return self.seq_mem.active
    @property
    def seq_memory_targets(self): return self.seq_mem.targets
    @property
    def seq_memory_step(self):    return self.seq_mem.step
    @property
    def seq_memory_is_pc(self):   return self.seq_mem.is_pc

    # ── round-score properties ────────────────────────────────────────────────

    @property
    def round_score(self):
        return self.score.user_score - self._round_start_score

    @property
    def pc_round_score(self):
        return self.score.pc_score - self._pc_round_start_score

    @property
    def cumulative_score(self):
        return self.score.user_score

    # ── backward-compat alias for round_count_ ────────────────────────────────

    @property
    def round_count_(self):
        return self.conjunctive_round_count

    @round_count_.setter
    def round_count_(self, value):
        self.conjunctive_round_count = value

    # ── difficulty / builder helpers ──────────────────────────────────────────

    def _get_bonus_profile(self, round_num: int) -> dict:
        idx = min(round_num - 1, len(BONUS_SEQUENCE) - 1)
        return BONUS_SEQUENCE[idx]

    def _turn_limit_for_round(self, round_num: int) -> int:
        return ROUND_TURN_LIMITS[min(round_num - 1, len(ROUND_TURN_LIMITS) - 1)]

    def _score_threshold(self) -> int:
        """Round 1 threshold is 0 (always advance); scales up each subsequent round."""
        return 0 if self.current_round == 1 else DIFFICULTY_SCORE_THRESHOLD + (self.current_round - 2) * 5

    def _frame_log_level(self) -> int:
        """DEBUG on round 1 for full-state capture; INFO thereafter to reduce noise."""
        return logging.DEBUG if self.current_round == 1 else logging.INFO

    def _build_board_for_round(self, round_num: int) -> ConditionBoard:
        bonus_cfg = self._get_bonus_profile(round_num)
        _log.debug("[BONUS] round=%d, mode=%s", round_num, bonus_cfg.get('bonus_mode', 'none'))
        return ConditionBoard(mode_profile=deep_merge(self.selected_mode, bonus_cfg))

    def _build_deck_for_difficulty(self) -> MainDeck:
        diff = DIFFICULTY_SEQUENCE[self.difficulty_index]
        _log.debug(
            "[DIFFICULTY] index=%d, cols=%s, layout=%s",
            self.difficulty_index, diff['deck_cols'], diff['layout_mode'],
        )
        return MainDeck(
            mode_profile={**self.selected_mode, 'deck_rows': 3, **diff},
            layout_mode=diff['layout_mode'],
        )

    def get_next_trial_id(self) -> int:
        self.trial_id += 1
        return self.trial_id

    # ── mode selection ────────────────────────────────────────────────────────

    def set_selected_mode(self, selected_mode_id: str) -> None:
        if selected_mode_id in self.available_modes:
            self.selected_mode_id = selected_mode_id
            self.selected_mode    = self.available_modes[selected_mode_id]
        else:
            self.selected_mode_id = DEFAULT_GAME_MODE
            self.selected_mode    = self.available_modes[DEFAULT_GAME_MODE]

        self.difficulty_index   = 0
        self._round_start_score = 0
        self.current_round      = 1
        self.board  = self._build_board_for_round(1)
        self.deck   = self._build_deck_for_difficulty()
        self.tokens = TokenManager(mode_profile=self.selected_mode, board=self.board)
        self.base_random_rate = 1.0 / max(1, self.deck.rows * self.deck.cols)
        self.adaptive.reset(self.base_random_rate)
        self.npc_ai.set_success_rate(self.base_random_rate)
        _log.info("[MODE] updated=%s", self.selected_mode_id)

    # ── round management ──────────────────────────────────────────────────────

    def _make_round_event(self, event_type: str, note: str = '') -> RoundEvent:
        return RoundEvent(
            event_type=event_type,
            round_num=self.current_round,
            user_score=self.score.user_score,
            pc_score=self.score.pc_score,
            token_positions=dict(self.tokens.get_all_positions()),
            difficulty_index=self.difficulty_index,
            note=note,
        )

    def _append_round_event(self, event_type: str, note: str = '') -> None:
        self.round_event_history.append(self._make_round_event(event_type, note))

    def _get_all_deck_cards(self) -> list:
        return [card for row in self.deck.deck for card in row]

    def _reset_round_board_state(self, reshuffle_board: bool = True) -> None:
        if reshuffle_board:
            self.board.reshuffle()
        self.deck.face_up     = self.deck._initialize_face_states()
        self.deck.flip_timers = {}
        for name in _TOKEN_NAMES:
            self.tokens.reset_token_position(name)
        self.adaptive.clear()
        self.seq_mem.deactivate()
        if self.conjunctive_round_count >= 3:
            self.board.apply_conjunctive_conditions(self._get_all_deck_cards())

    def advance_round(self) -> None:
        prev = self.difficulty_index
        if self.round_score >= self._score_threshold():
            self.difficulty_index = min(self.difficulty_index + 1, len(DIFFICULTY_SEQUENCE) - 1)
            if self.difficulty_index > prev:
                self.conjunctive_round_count = 0
                _log.info("[DIFFICULTY] up: %d → %d (round_score=%d)",
                          prev, self.difficulty_index, self.round_score)
            else:
                self.conjunctive_round_count += 1
                _log.info("[CONJUNCTIVE] max difficulty; conjunctive_round_count=%d",
                          self.conjunctive_round_count)
        else:
            self.conjunctive_round_count += 1
            _log.info("[CONJUNCTIVE] conjunctive_round_count=%d (triggers in %d more)",
                      self.conjunctive_round_count,
                      max(0, 3 - self.conjunctive_round_count))

        self._round_start_score    = self.score.user_score
        self._pc_round_start_score = self.score.pc_score
        self.current_round += 1
        self.board = self._build_board_for_round(self.current_round)
        if self.difficulty_index > prev:
            self.deck = self._build_deck_for_difficulty()

        self._reset_round_board_state(reshuffle_board=False)

        self.turn_time_limit  = self._turn_limit_for_round(self.current_round)
        self.timer.time_limit = self.turn_time_limit
        _log.info("[ROUND %d] start — difficulty=%d, turn_limit=%ds",
                  self.current_round, self.difficulty_index, self.turn_time_limit)
        self._append_round_event('round_advance')

    # ── game flow ─────────────────────────────────────────────────────────────

    def start_game(self) -> None:
        self.phase        = self.PHASE_TOKEN_SELECTION
        self.current_turn = self.TURN_USER
        self.turn_count   = 1
        _log.info("Game started — awaiting token selection.")
        self._append_round_event('game_start')

    def select_token(self, token_name: str) -> bool:
        if self.phase != self.PHASE_TOKEN_SELECTION or token_name not in ('chase', 'flight'):
            return False
        self.selected_token = token_name
        return True

    def confirm_selection(self) -> bool:
        if self.phase != self.PHASE_TOKEN_SELECTION or self.selected_token is None:
            return False
        self.phase = self.PHASE_GAME_PLAY
        self.timer.start()
        if not self.game_timer.is_running:
            self.game_timer.start()
        _log.info("Turn %d started — time limit: %ds", self.turn_count, TURN_TIME_LIMIT)
        return True

    def get_target_position(self):
        return self.tokens.get_target_position(self.selected_token) if self.selected_token else None

    def get_target_condition(self):
        pos = self.get_target_position()
        return self.board.get_condition(pos[0], pos[1]) if pos else None

    def is_game_time_expired(self) -> bool:
        return self.total_rounds > 0 and self.current_round > self.total_rounds

    def is_round_time_expired(self) -> bool:
        return False  # round transitions are driven by catch events only

    def get_game_time_remaining(self) -> float:
        return self.game_timer.get_remaining()

    def get_round_time_remaining(self) -> float:
        return self.get_game_time_remaining()

    # ── sequential memory wrappers ────────────────────────────────────────────

    def deactivate_seq_memory(self) -> None:
        self.seq_mem.deactivate()

    def try_activate_seq_memory(self) -> bool:
        return self.seq_mem.try_activate_user(self.round_score, self.selected_token, self.tokens)

    def try_activate_pc_seq_memory(self) -> bool:
        return self.seq_mem.try_activate_pc(self.pc_round_score, self.tokens)

    def get_seq_memory_current_target(self):
        return self.seq_mem.current_target

    # ── turn execution delegation (TurnExecutor) ──────────────────────────────

    def user_click_card(self, card_row, card_col, defer_success_move=False):
        return self._turns.user_click_card(card_row, card_col, defer_success_move)

    def complete_user_success_move(self):
        return self._turns.complete_user_success_move()

    def check_seq_memory_card(self, card_row, card_col) -> str:
        return self._turns.check_seq_memory_card(card_row, card_col)

    def complete_seq_memory_move(self) -> str:
        return self._turns.complete_seq_memory_move()

    def pc_turn_step(self, defer_success_move=False):
        return self._turns.pc_turn_step(defer_success_move)

    def complete_pc_success_move(self):
        return self._turns.complete_pc_success_move()

    def check_pc_seq_memory_card(self) -> tuple:
        return self._turns.check_pc_seq_memory_card()

    def complete_pc_seq_memory_move(self) -> str:
        return self._turns.complete_pc_seq_memory_move()

    def end_user_turn(self):
        return self._turns.end_user_turn()

    def end_pc_turn(self):
        return self._turns.end_pc_turn()

    def check_catch_event(self):
        return self._turns.check_catch_event()

    # ── update / reset ────────────────────────────────────────────────────────

    def update(self, current_time) -> None:
        self.deck.update_timers(current_time)
        _log.log(
            self._frame_log_level(),
            "[FRAME] round=%d, phase=%s, turn=%s, token=%s",
            self.current_round, self.phase, self.current_turn, self.selected_token,
        )
        if self.phase == self.PHASE_GAME_PLAY and self.current_turn == self.TURN_USER:
            if self.timer.is_expired():
                _log.info("Turn timer expired — ending user turn.")
                self.end_user_turn()

    def reset(self) -> None:
        self.board  = ConditionBoard(mode_profile=self.selected_mode)
        self.deck   = MainDeck(mode_profile=self.selected_mode)
        self.tokens = TokenManager(mode_profile=self.selected_mode, board=self.board)
        self.timer.stop()
        self.game_timer.stop()
        self.score.reset()
        self.adaptive.reset(self.base_random_rate)
        self.seq_mem.deactivate()
        self.npc_ai.set_success_rate(self.base_random_rate)

        self.phase             = self.PHASE_NOT_STARTED
        self.current_turn      = self.TURN_USER
        self.selected_token    = None
        self.current_round     = 1
        self.total_rounds      = TOTAL_ROUNDS
        self.turn_time_limit   = ROUND_TURN_LIMITS[0]
        self.timer.time_limit  = self.turn_time_limit
        self.turn_count            = 0
        self.user_move_count       = 0
        self.pc_move_count         = 0
        self.trial_history         = []
        self.round_event_history   = []
        self._pc_round_start_score = 0
        _log.info("Game reset.")

    # ── summary ───────────────────────────────────────────────────────────────

    def get_seq_memory_summary(self) -> dict:
        return self.seq_mem.summarize_trials(self.trial_history)

    def get_summary(self) -> dict:
        return {
            'phase':                self.phase,
            'turn':                 self.current_turn,
            'turn_count':           self.turn_count,
            'selected_mode_id':     self.selected_mode_id,
            'selected_mode':        self.selected_mode,
            'current_round':        self.current_round,
            'total_rounds':         self.total_rounds,
            'round_count_':         self.conjunctive_round_count,
            'conjunctive_active':   self.conjunctive_round_count >= 3,
            'round_time_remaining': round(self.get_round_time_remaining(), 1),
            'user_score':           self.score.user_score,
            'pc_score':             self.score.pc_score,
            'user_combo':           self.score.user_combo,
            'pc_combo':             self.score.pc_combo,
            'user_catch_count':     self.score.user_catch_count,
            'pc_catch_count':       self.score.pc_catch_count,
            'game_time_remaining':  round(self.get_game_time_remaining(), 1),
            'user_moves':           self.user_move_count,
            'pc_moves':             self.pc_move_count,
            'total_trials':         len(self.trial_history),
            'user_seen_cards':      len(self.adaptive.user_seen_cards),
            'npc_seen_cards':       len(self.adaptive.npc_seen_cards),
            'npc_success_rate':     round(self.npc_ai.success_rate, 4),
            'token_positions':      self.tokens.get_all_positions(),
            'seq_memory':           self.get_seq_memory_summary(),
        }
