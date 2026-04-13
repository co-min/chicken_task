# Game State Management 

import time
import random
import sys
from pathlib import Path

try:
    from game_func.board_class import ConditionBoard
    from game_func.deck_class import MainDeck
    from game_func.token_class import TokenManager
    from game_func.npc_ai import NPCAI
    from utils.timer import GameTimer
    from utils.card_matcher import check_match
    from utils.helpers import clamp
    from ..config import (TURN_TIME_LIMIT, PC_THINK_TIME, DEFAULT_GAME_MODE, GAME_MODES,
                          GAME_TIME_LIMIT, SCORE_MATCH, SCORE_COMBO_BONUS, SCORE_SPEED_MAX,
                          SCORE_SPEED_MIN, SCORE_STEAL, SCORE_PENALTY,
                          SCORE_CATCH_BONUS, SCORE_CAUGHT_PENALTY, SCORE_PC_CATCH_BONUS,
                          TOTAL_ROUNDS, ROUND_TURN_LIMITS,
                          DIFFICULTY_SEQUENCE, DIFFICULTY_SCORE_THRESHOLD,
                          BONUS_SEQUENCE, BONUS_SCORE_MULTIPLIER,
                          NPC_RATE_MAX, ADAPTIVE_ALPHA_UP, ADAPTIVE_ALPHA_DOWN,
                          MAX_RATE_STEP_UP, MAX_RATE_STEP_DOWN, SURGE_BONUS_SCALE,
                          USER_WINDOW_SIZE, MIN_USER_TRIALS_FOR_ADAPT, USER_EWMA_ALPHA,
                          PERF_VARIABILITY_HIT_W, PERF_VARIABILITY_ELAPSED_W,
                          TREND_WEIGHT_RECENT, TREND_WEIGHT_PREV,
                          KNOWLEDGE_EXIST_W, KNOWLEDGE_DENSITY_W,
                          SKILL_EWMA_W, SKILL_RECENT_W, SKILL_SPEED_W,
                          ESTIMATED_SKILL_W, ESTIMATED_KNOWLEDGE_W, ESTIMATED_NOVELTY_W,
                          SURGE_BASE_W, SURGE_SPEED_W, SURGE_CONSECUTIVE_BONUS,
                          QUICK_SKILL_ACCURACY_W, QUICK_SKILL_SPEED_W,
                        MEMORY_CONFIDENCE_INIT, MEMORY_CONFIDENCE_INCREMENT,
                        MISS_PENALTY_PER_STREAK, MISS_PENALTY_MAX_STREAK,
                        SEQ_MEMORY_SCORE_THRESHOLD, SEQ_MEMORY_PC_THRESHOLD,
                        SEQ_MEMORY_TRIGGER_PROB, SEQ_MEMORY_MIN_STEPS, SEQ_MEMORY_MAX_STEPS)
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from game_func.board_class import ConditionBoard
    from game_func.deck_class import MainDeck
    from game_func.token_class import TokenManager
    from game_func.npc_ai import NPCAI
    from utils.timer import GameTimer
    from utils.card_matcher import check_match
    from utils.helpers import clamp
    from config import (TURN_TIME_LIMIT, PC_THINK_TIME, DEFAULT_GAME_MODE, GAME_MODES,
                        GAME_TIME_LIMIT, SCORE_MATCH, SCORE_COMBO_BONUS, SCORE_SPEED_MAX,
                        SCORE_SPEED_MIN, SCORE_STEAL, SCORE_PENALTY,
                        SCORE_CATCH_BONUS, SCORE_CAUGHT_PENALTY, SCORE_PC_CATCH_BONUS,
                        TOTAL_ROUNDS, ROUND_TURN_LIMITS,
                        DIFFICULTY_SEQUENCE, DIFFICULTY_SCORE_THRESHOLD,
                        BONUS_SEQUENCE, BONUS_SCORE_MULTIPLIER,
                        NPC_RATE_MAX, ADAPTIVE_ALPHA_UP, ADAPTIVE_ALPHA_DOWN,
                        MAX_RATE_STEP_UP, MAX_RATE_STEP_DOWN, SURGE_BONUS_SCALE,
                        USER_WINDOW_SIZE, MIN_USER_TRIALS_FOR_ADAPT, USER_EWMA_ALPHA,
                        PERF_VARIABILITY_HIT_W, PERF_VARIABILITY_ELAPSED_W,
                        TREND_WEIGHT_RECENT, TREND_WEIGHT_PREV,
                        KNOWLEDGE_EXIST_W, KNOWLEDGE_DENSITY_W,
                        SKILL_EWMA_W, SKILL_RECENT_W, SKILL_SPEED_W,
                        ESTIMATED_SKILL_W, ESTIMATED_KNOWLEDGE_W, ESTIMATED_NOVELTY_W,
                        SURGE_BASE_W, SURGE_SPEED_W, SURGE_CONSECUTIVE_BONUS,
                        QUICK_SKILL_ACCURACY_W, QUICK_SKILL_SPEED_W,
                        MEMORY_CONFIDENCE_INIT, MEMORY_CONFIDENCE_INCREMENT,
                        MISS_PENALTY_PER_STREAK, MISS_PENALTY_MAX_STREAK,
                        SEQ_MEMORY_SCORE_THRESHOLD, SEQ_MEMORY_PC_THRESHOLD,
                        SEQ_MEMORY_TRIGGER_PROB, SEQ_MEMORY_MIN_STEPS, SEQ_MEMORY_MAX_STEPS)


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
    
    def __init__(self, selected_mode_id=None):
        """게임 상태 초기화"""
        self.available_modes = GAME_MODES
        self.selected_mode_id = selected_mode_id or DEFAULT_GAME_MODE
        self.selected_mode = self.available_modes.get(self.selected_mode_id, self.available_modes[DEFAULT_GAME_MODE])

        # 난이도 시스템
        self.difficulty_index = 0          # 현재 난이도 단계 (0~5)
        self._round_start_score = 0        # 라운드 시작 시 user_score 스냅샷

        # 게임 컴포넌트 (라운드 1 기준 보너스 설정으로 보드 생성)
        self.board = self._build_board_for_round(1)
        self.deck = self._build_deck_for_difficulty()
        self.tokens = TokenManager(mode_profile=self.selected_mode, board=self.board)

        # mode 기반 deck 크기 기준의 기본 랜덤 정답률
        self.base_random_rate = 1.0 / max(1, (self.deck.rows * self.deck.cols))
        self.npc_ai = NPCAI(success_rate=self.base_random_rate)  # NPC AI

        print(f"[MODE] selected={self.selected_mode_id}, profile={self.selected_mode}")

        # 자동 적응형 AI 상태 (config.py에서 튜닝)
        self.npc_rate_min = self.base_random_rate
        self.npc_rate_max = NPC_RATE_MAX
        self.adaptive_alpha_up = ADAPTIVE_ALPHA_UP
        self.adaptive_alpha_down = ADAPTIVE_ALPHA_DOWN
        self.max_rate_step_up = MAX_RATE_STEP_UP
        self.max_rate_step_down = MAX_RATE_STEP_DOWN
        self.surge_bonus_scale = SURGE_BONUS_SCALE
        self.user_window_size = USER_WINDOW_SIZE
        self.min_user_trials_for_adapt = MIN_USER_TRIALS_FOR_ADAPT

        # 사용자 수행/선택 패턴 추적
        self.user_accuracy_ewma = self.base_random_rate
        self.user_ewma_alpha = USER_EWMA_ALPHA
        self.user_seen_cards = {}  # {(row, col): {'card', 'seen_count', 'last_seen_turn', 'confidence'}}
        self.npc_seen_cards = {}   # {(row, col): {'card', 'seen_count', 'last_seen_turn', 'confidence'}}
        self.user_choice_count = 0
        self.user_repeat_count = 0
        self.user_last_selected_pos = None
        
        # 게임 상태
        self.phase = self.PHASE_NOT_STARTED
        self.current_turn = self.TURN_USER
        self.selected_token = None  # 'chase' 또는 'flight'
        
        # 라운드 시스템
        self.current_round = 1
        self.total_rounds = TOTAL_ROUNDS
        self.turn_time_limit = ROUND_TURN_LIMITS[0]  # 현재 라운드 턴 제한 시간

        # 타이머 (라운드 제한 없음 — 잡기 이벤트가 라운드 전환 트리거)
        self.timer = GameTimer(time_limit=self.turn_time_limit)   # 턴 타이머
        self.game_timer = GameTimer(time_limit=GAME_TIME_LIMIT)   # 전체 게임 타이머

        # 점수
        self.user_score = 0
        self.pc_score = 0
        self._pc_round_start_score = 0
        self.user_combo = 0      # 사용자 연속 성공 횟수
        self.pc_combo = 0        # PC 연속 성공 횟수

        # 잡기 기록
        self.user_catch_count = 0   # 사용자가 문어를 잡은 횟수
        self.pc_catch_count = 0     # 문어가 flight를 잡은 횟수

        # 게임 기록
        self.turn_count = 0
        self.user_move_count = 0
        self.pc_move_count = 0
        self.trial_history = []  # 시행 결과 리스트
        self.trial_id = 0        # EDF/LabJack 동기화용 단조 증가 시행 번호

        # Sequential Memory 상태
        self.seq_memory_active  = False  # 현재 순차 메모리 활성 여부
        self.seq_memory_targets = []     # [(row, col), ...] 순서대로
        self.seq_memory_step    = 0      # 현재 진행 단계 인덱스
        self.seq_memory_is_pc   = False  # PC 턴 순차 메모리 여부
        self.seq_memory_skip_on_switch = False  # token_switched 직후 한 번 발동 억제 플래그

    # ==================== 난이도 ====================

    @property
    def round_score(self):
        """이번 라운드에서 획득한 점수 (난이도 업 판단용)."""
        return self.user_score - self._round_start_score

    @property
    def pc_round_score(self):
        """문어(PC)가 이번 라운드에서 획득한 점수."""
        return self.pc_score - self._pc_round_start_score

    @property
    def cumulative_score(self):
        """누적 점수 (UI 표시용). user_score와 동일."""
        return self.user_score

    def _get_bonus_profile(self, round_num):
        """
        라운드 번호에 맞는 보너스 설정 딕셔너리를 반환.
        BONUS_SEQUENCE 범위를 초과하면 마지막 항목을 재사용한다.
        """
        idx = min(round_num - 1, len(BONUS_SEQUENCE) - 1)
        return BONUS_SEQUENCE[idx]

    def _build_board_for_round(self, round_num):
        """
        라운드 번호에 맞는 보너스 설정을 포함한 ConditionBoard 생성.
        mode_profile에 bonus_mode 등이 병합되어 ConditionBoard 내부에서
        _apply_bonus_slots()가 자동 호출된다.
        """
        bonus_cfg = self._get_bonus_profile(round_num)
        board_profile = {**self.selected_mode, **bonus_cfg}
        print(f"[BONUS] 라운드={round_num}, mode={bonus_cfg.get('bonus_mode', 'none')}")
        return ConditionBoard(mode_profile=board_profile)

    def _build_deck_for_difficulty(self):
        """현재 difficulty_index에 맞는 MainDeck 생성."""
        diff = DIFFICULTY_SEQUENCE[self.difficulty_index]
        mode_profile = {**self.selected_mode, 'deck_rows': 3, **diff}
        layout_mode = diff['layout_mode']
        print(f"[DIFFICULTY] index={self.difficulty_index}, "
              f"cols={diff['deck_cols']}, layout={layout_mode}")
        return MainDeck(mode_profile=mode_profile, layout_mode=layout_mode)

    def get_next_trial_id(self) -> int:
        """카드 선택 시도가 시작될 때마다 호출. 단조 증가하는 시행 번호 반환.
        EDF sendMessage 및 LabJack 트리거 코드의 공통 키로 사용한다."""
        self.trial_id += 1
        return self.trial_id

    def set_selected_mode(self, selected_mode_id):
        """시작 phase에서 선택된 모드 ID를 저장."""
        if selected_mode_id in self.available_modes:
            self.selected_mode_id = selected_mode_id
            self.selected_mode = self.available_modes[selected_mode_id]
        else:
            self.selected_mode_id = DEFAULT_GAME_MODE
            self.selected_mode = self.available_modes[DEFAULT_GAME_MODE]

        self.difficulty_index = 0
        self._round_start_score = 0
        self.current_round = 1
        self.board = self._build_board_for_round(1)
        self.deck = self._build_deck_for_difficulty()
        self.tokens = TokenManager(mode_profile=self.selected_mode, board=self.board)
        self.base_random_rate = 1.0 / max(1, (self.deck.rows * self.deck.cols))
        self.npc_rate_min = self.base_random_rate
        self.npc_ai.set_success_rate(self.base_random_rate, sync_effective=True)
        print(f"[MODE] updated={self.selected_mode_id}")

    def _get_recent_user_trials(self):
        """최근 사용자 시행만 추출 (PC 시행 제외)."""
        user_trials = [
            t for t in self.trial_history
            if t.get('token') in ('chase', 'flight')
        ]
        return user_trials[-self.user_window_size:]

    def _summarize_recent_user_performance(self, recent_trials):
        """최근 사용자 로그에서 정확도/변동성/추세 신호를 요약."""
        if not recent_trials:
            return {
                'count': 0,
                'accuracy': None,
                'variability': None,
                'trend_score': 0.0,
            }

        hits = [1.0 if trial.get('is_match') else 0.0 for trial in recent_trials]
        count = len(hits)
        accuracy = sum(hits) / count

        hit_variance = sum((hit - accuracy) ** 2 for hit in hits) / count
        hit_std = hit_variance ** 0.5

        elapsed_times = [trial.get('elapsed_time', TURN_TIME_LIMIT) for trial in recent_trials]
        normalized_elapsed = [clamp(t / TURN_TIME_LIMIT, 0.0, 1.0) for t in elapsed_times]
        mean_elapsed = sum(normalized_elapsed) / count
        elapsed_variance = sum((t - mean_elapsed) ** 2 for t in normalized_elapsed) / count
        elapsed_std = elapsed_variance ** 0.5

        variability = clamp((PERF_VARIABILITY_HIT_W * hit_std) + (PERF_VARIABILITY_ELAPSED_W * elapsed_std), 0.0, 1.0)

        trend_score = 0.0
        if count >= 2:
            trend_score = hits[-1] - hits[-2]
        if count >= 3:
            trend_score = (TREND_WEIGHT_RECENT * trend_score) + (TREND_WEIGHT_PREV * (hits[-2] - hits[-3]))
        trend_score = clamp(trend_score, -1.0, 1.0)

        return {
            'count': count,
            'accuracy': accuracy,
            'variability': variability,
            'trend_score': trend_score,
        }

    def _record_user_observation(self, pos, card, is_match):
        """사용자 카드 선택/관찰 히스토리 업데이트."""
        self.user_choice_count += 1
        if self.user_last_selected_pos == pos:
            self.user_repeat_count += 1
        self.user_last_selected_pos = pos

        self._record_observation(self.user_seen_cards, pos, card)

        hit = 1.0 if is_match else 0.0
        self.user_accuracy_ewma = ((1 - self.user_ewma_alpha) * self.user_accuracy_ewma) + (self.user_ewma_alpha * hit)

    def _record_npc_observation(self, pos, card):
        """문어가 직접 본 카드 정보 저장."""
        self._record_observation(self.npc_seen_cards, pos, card)

    def _record_observation(self, store, pos, card):
        """공통 관찰 메모리 업데이트."""
        seen_info = store.get(pos)
        if seen_info is None:
            store[pos] = {
                'card': card,
                'seen_count': 1,
                'last_seen_turn': self.turn_count,
                'confidence': MEMORY_CONFIDENCE_INIT,
            }
            return

        seen_info['card'] = card
        seen_info['seen_count'] += 1
        seen_info['last_seen_turn'] = self.turn_count
        seen_info['confidence'] = clamp(seen_info['confidence'] + MEMORY_CONFIDENCE_INCREMENT, 0.0, 1.0)

    def _build_npc_memory_context(self, condition=None):
        """
        사용자+문어 관찰 메모리를 통합하여 NPC 선택 컨텍스트 구성.
        """
        merged = {}

        for source, store in (('user', self.user_seen_cards), ('npc', self.npc_seen_cards)):
            for pos, info in store.items():
                existing = merged.get(pos)
                if existing is None:
                    merged[pos] = {
                        'pos': pos,
                        'card': info.get('card'),
                        'confidence': float(info.get('confidence', MEMORY_CONFIDENCE_INIT)),
                        'seen_count': int(info.get('seen_count', 1)),
                        'last_seen_turn': int(info.get('last_seen_turn', self.turn_count)),
                        'source': source,
                    }
                    continue

                existing['card'] = info.get('card', existing['card'])
                existing['confidence'] = max(existing['confidence'], float(info.get('confidence', MEMORY_CONFIDENCE_INIT)))
                existing['seen_count'] += int(info.get('seen_count', 1))
                existing['last_seen_turn'] = max(
                    existing['last_seen_turn'],
                    int(info.get('last_seen_turn', self.turn_count))
                )
                if existing['source'] != source:
                    existing['source'] = 'both'

        recent_trials = self._get_recent_user_trials()
        recent_summary = self._summarize_recent_user_performance(recent_trials)
        recent_user_accuracy = recent_summary['accuracy']

        user_skill_score = self._estimate_user_skill()
        if user_skill_score is None:
            user_skill_score = self.user_accuracy_ewma

        npc_target_success_rate = None
        if condition is not None:
            npc_target_success_rate = self._estimate_user_success_probability(condition)

        return {
            'entries': list(merged.values()),
            'current_turn': self.turn_count,
            'recency_window': 6,
            'recent_user_accuracy': recent_user_accuracy,
            'user_recent_trials_count': recent_summary['count'],
            'user_performance_variability': recent_summary['variability'],
            'user_trend_score': recent_summary['trend_score'],
            'user_skill_score': user_skill_score,
            'npc_target_success_rate': npc_target_success_rate,
            'npc_rate_min': self.npc_rate_min,
            'npc_rate_max': self.npc_rate_max,
        }

    def _get_recent_user_hint_pos(self, condition):
        """
        직전 사용자 카드가 현재 조건 정답이면 해당 위치를 힌트로 반환.
        """
        for trial in reversed(self.trial_history):
            if trial.get('token') not in ('chase', 'flight'):
                continue

            user_card = trial.get('selected_card')
            if user_card is None:
                return None

            if check_match(condition, user_card):
                return trial.get('selected_card_pos')
            return None

        return None

    def _get_recent_npc_failed_pos(self):
        """문어의 직전 오답 위치를 반환."""
        for trial in reversed(self.trial_history):
            if trial.get('token') != 'octopus':
                continue
            if not trial.get('is_match'):
                return trial.get('selected_card_pos')
            return None
        return None

    def _get_known_wrong_positions(self, condition):
        """현재 조건 기준으로 메모리상 오답으로 알려진 위치 목록."""
        known_wrong = set()
        for store in (self.user_seen_cards, self.npc_seen_cards):
            for pos, info in store.items():
                card = info.get('card')
                if card is None:
                    continue
                if not check_match(condition, card):
                    known_wrong.add(pos)
        return list(known_wrong)

    def _estimate_condition_knowledge(self, condition):
        """
        사용자가 현재 조건에 맞는 카드를 얼마나 알고 있는지 추정.

        Returns:
            float: 0.0~1.0 지식 점수
        """
        if condition is None or not self.user_seen_cards:
            return 0.0

        known_total = len(self.user_seen_cards)
        known_match_count = 0
        for info in self.user_seen_cards.values():
            if check_match(condition, info['card']):
                known_match_count += 1

        has_known_match = 1.0 if known_match_count > 0 else 0.0
        match_density = known_match_count / known_total

        # 일치 카드 존재 여부를 우선 반영하고, 밀도로 미세 조정
        return clamp((KNOWLEDGE_EXIST_W * has_known_match) + (KNOWLEDGE_DENSITY_W * match_density), 0.0, 1.0)

    def _get_recent_miss_streak(self):
        """최근 사용자 연속 오답 길이 계산."""
        streak = 0
        for trial in reversed(self._get_recent_user_trials()):
            if trial.get('is_match'):
                break
            streak += 1
        return streak

    def _get_last_user_trial(self):
        """가장 최근 사용자 시도 1개 반환."""
        for trial in reversed(self.trial_history):
            if trial.get('token') in ('chase', 'flight'):
                return trial
        return None

    def _estimate_user_success_probability(self, next_condition):
        """
        다음 시도에서 사용자가 정답을 맞출 확률 추정.

        사용자 정답률, 반응시간, 반복선택 성향, 관찰 카드 지식을 조합한다.
        """
        recent_trials = self._get_recent_user_trials()
        if len(recent_trials) < self.min_user_trials_for_adapt:
            return self.base_random_rate

        recent_accuracy = sum(1 for t in recent_trials if t.get('is_match')) / len(recent_trials)

        elapsed_times = [t.get('elapsed_time', TURN_TIME_LIMIT) for t in recent_trials]
        mean_elapsed = sum(elapsed_times) / len(elapsed_times)
        speed_score = clamp(1.0 - (mean_elapsed / TURN_TIME_LIMIT), 0.0, 1.0)

        global_skill = (SKILL_EWMA_W * self.user_accuracy_ewma) + (SKILL_RECENT_W * recent_accuracy) + (SKILL_SPEED_W * speed_score)
        knowledge_score = self._estimate_condition_knowledge(next_condition)

        repeat_rate = 0.0
        if self.user_choice_count > 0:
            repeat_rate = self.user_repeat_count / self.user_choice_count
        novelty_score = 1.0 - repeat_rate

        miss_streak = self._get_recent_miss_streak()
        miss_penalty = MISS_PENALTY_PER_STREAK * min(miss_streak, MISS_PENALTY_MAX_STREAK)

        # 사용자가 방금 잘한 턴을 빠르게 반영 (급상승 대응)
        surge_bonus = 0.0
        last_user_trial = self._get_last_user_trial()
        if last_user_trial is not None and last_user_trial.get('is_match'):
            last_elapsed = last_user_trial.get('elapsed_time', TURN_TIME_LIMIT)
            last_speed = clamp(1.0 - (last_elapsed / TURN_TIME_LIMIT), 0.0, 1.0)
            surge_bonus += self.surge_bonus_scale * (SURGE_BASE_W + SURGE_SPEED_W * last_speed)

            # 최근 2연속 성공이면 추가 가중
            recent_user_trials = self._get_recent_user_trials()
            if len(recent_user_trials) >= 2 and recent_user_trials[-2].get('is_match'):
                surge_bonus += SURGE_CONSECUTIVE_BONUS

        estimated = (
            (ESTIMATED_SKILL_W * global_skill)
            + (ESTIMATED_KNOWLEDGE_W * knowledge_score)
            + (ESTIMATED_NOVELTY_W * novelty_score)
            + surge_bonus
            - miss_penalty
        )
        return clamp(estimated, self.npc_rate_min, self.npc_rate_max)

    def _estimate_user_skill(self):
        """
        최근 사용자 정확도/속도를 기반으로 실력 점수 추정.

        Returns:
            float or None: 0.0~1.0 범위의 실력 점수, 데이터 부족 시 None
        """
        recent_trials = self._get_recent_user_trials()
        if len(recent_trials) < self.min_user_trials_for_adapt:
            return None

        correct_count = sum(1 for t in recent_trials if t.get('is_match'))
        accuracy = correct_count / len(recent_trials)

        elapsed_times = [t.get('elapsed_time', TURN_TIME_LIMIT) for t in recent_trials]
        mean_elapsed = sum(elapsed_times) / len(elapsed_times)
        speed_score = clamp(1.0 - (mean_elapsed / TURN_TIME_LIMIT), 0.0, 1.0)

        # 정확도 중심으로 점수 산출 (config.py QUICK_SKILL_*_W로 튜닝)
        return QUICK_SKILL_ACCURACY_W * accuracy + QUICK_SKILL_SPEED_W * speed_score

    def _update_adaptive_npc_rate(self):
        """다음 사용자 성공확률 추정치를 따라 NPC 정답률을 조정."""
        target_pos = self.tokens.get_target_position('octopus')
        if target_pos is None:
            return
        next_condition = self.board.get_condition(target_pos[0], target_pos[1])

        target_rate = self._estimate_user_success_probability(next_condition)

        current_rate = self.npc_ai.success_rate
        if target_rate >= current_rate:
            adaptive_alpha = self.adaptive_alpha_up
            max_rate_step = self.max_rate_step_up
        else:
            adaptive_alpha = self.adaptive_alpha_down
            max_rate_step = self.max_rate_step_down

        smoothed_rate = ((1 - adaptive_alpha) * current_rate) + (adaptive_alpha * target_rate)
        delta = smoothed_rate - current_rate
        delta = clamp(delta, -max_rate_step, max_rate_step)

        self.npc_ai.set_success_rate(current_rate + delta)
    
    # ==================== 점수 계산 ====================

    def _calculate_speed_bonus(self, elapsed_time):
        """경과 시간 기반 속도 보너스 계산 (SCORE_SPEED_MIN ~ SCORE_SPEED_MAX)."""
        ratio = 1.0 - clamp(elapsed_time / TURN_TIME_LIMIT, 0.0, 1.0)
        return max(SCORE_SPEED_MIN, round(SCORE_SPEED_MAX * ratio))

    def _is_npc_steal(self, selected_card):
        """사용자의 선택 카드가 NPC 타겟 조건과도 매칭되는지 확인 (탈취 여부)."""
        npc_target_pos = self.tokens.get_target_position('octopus')
        if npc_target_pos is None:
            return False
        npc_condition = self.board.get_condition(npc_target_pos[0], npc_target_pos[1])
        return check_match(npc_condition, selected_card)

    def _add_user_match_score(self, elapsed_time, is_steal):
        """사용자 성공 점수 계산 및 누적. 획득 점수를 반환."""
        self.user_combo += 1
        score = SCORE_MATCH
        score += self._calculate_speed_bonus(elapsed_time)
        if self.user_combo > 1:
            score += SCORE_COMBO_BONUS
        if is_steal:
            score += SCORE_STEAL

        # 보너스 칸 판정: 타겟 위치 조건 카드에 bonus='double_score'이면 배율 적용.
        # selected_token이 None인 경우(예: 토큰 선택 전 호출)는 안전하게 건너뜀.
        is_bonus = False
        if self.selected_token:
            target_pos = self.tokens.get_target_position(self.selected_token)
            if target_pos:
                condition = self.board.get_condition(target_pos[0], target_pos[1])
                if condition and condition.get('bonus') == 'double_score':
                    score *= BONUS_SCORE_MULTIPLIER
                    is_bonus = True
                    print(f"[BONUS] 보너스 칸 적중! ×{BONUS_SCORE_MULTIPLIER} → {score}점")

        self.user_score += score
        return score

    def _add_user_penalty_score(self):
        """사용자 오답 패널티 적용. 콤보 초기화."""
        self.user_combo = 0
        self.user_score += SCORE_PENALTY

    def _add_pc_match_score(self):
        """PC 성공 점수 계산 및 누적. 획득 점수를 반환."""
        self.pc_combo += 1
        score = SCORE_MATCH
        if self.pc_combo > 1:
            score += SCORE_COMBO_BONUS
        self.pc_score += score
        return score

    def _add_pc_penalty_score(self):
        """PC 오답 패널티 적용. 콤보 초기화."""
        self.pc_combo = 0
        self.pc_score += SCORE_PENALTY

    def is_round_time_expired(self):
        """라운드 제한 시간 없음 — 항상 False (라운드 전환은 잡기 이벤트로만 발생)."""
        return False

    def is_game_time_expired(self):
        """전체 게임 시간 초과 여부."""
        return self.game_timer.is_running and self.game_timer.is_expired()

    def get_round_time_remaining(self):
        """라운드 제한 없음 — 전체 게임 남은 시간을 반환."""
        return self.get_game_time_remaining()

    def get_game_time_remaining(self):
        """전체 게임 남은 시간 (초)."""
        return self.game_timer.get_remaining()

    def _reset_round_board_state(self, reshuffle_board=True):
        """
        라운드 공통 초기화: 보드·덱 재셔플, 토큰 위치 초기화, 관찰 메모리 클리어.
        라운드 전환 및 잡기 이벤트(잡거나 잡힐 때) 양쪽에서 호출된다.

        Args:
            reshuffle_board: False면 board.reshuffle()을 건너뜀.
                advance_round()에서는 _build_board_for_round()가 이미 새 보드를
                완전히 초기화했으므로 이중 셔플을 피하기 위해 False로 호출한다.
                잡기 이벤트에서는 보드 교체 없이 재셔플이 필요하므로 True(기본값).
        """
        if reshuffle_board:
            self.board.reshuffle()
        self.deck.reshuffle()
        self.tokens.reset_token_position('chase')
        self.tokens.reset_token_position('flight')
        self.tokens.reset_token_position('octopus')
        self.user_seen_cards.clear()
        self.npc_seen_cards.clear()
        self.deactivate_seq_memory()

    def advance_round(self):
        """
        다음 라운드 시작.
        1) 이번 라운드 점수로 난이도 업 여부 결정
        2) 새 난이도에 맞는 덱 먼저 생성 (참조 교체)
        3) 라운드 카운터 증가, 보드·토큰 초기화
        4) 타이머·턴 제한 갱신
        """
        # 1) 난이도 업 체크
        if self.round_score >= DIFFICULTY_SCORE_THRESHOLD:
            prev = self.difficulty_index
            self.difficulty_index = min(self.difficulty_index + 1, len(DIFFICULTY_SEQUENCE) - 1)
            if self.difficulty_index > prev:
                print(f"[DIFFICULTY] 업! {prev} → {self.difficulty_index} "
                      f"(라운드 점수={self.round_score})")

        # 라운드 점수 스냅샷 갱신 (다음 라운드 측정 기준)
        self._round_start_score = self.user_score
        self._pc_round_start_score = self.pc_score

        # 2) 라운드 카운터 증가 후, 새 보너스 설정 보드와 난이도 덱을 함께 교체.
        # 반드시 _reset_round_board_state() 호출 전에 교체해야
        # reshuffle()이 새 객체에 적용되고, 외부 참조와의 불일치가 방지된다.
        self.current_round += 1
        self.board = self._build_board_for_round(self.current_round)
        self.deck = self._build_deck_for_difficulty()

        # 3) 덱·토큰 초기화. board는 _build_board_for_round()에서 이미 완전 초기화됐으므로
        #    reshuffle_board=False로 이중 셔플을 방지한다.
        self._reset_round_board_state(reshuffle_board=False)

        # 4) 턴 제한 갱신 (game_timer는 계속 진행 중)
        idx = min(self.current_round - 1, len(ROUND_TURN_LIMITS) - 1)
        self.turn_time_limit = ROUND_TURN_LIMITS[idx]
        self.timer.time_limit = self.turn_time_limit
        print(f"[ROUND {self.current_round}] 시작! 난이도={self.difficulty_index}, "
              f"턴 제한={self.turn_time_limit}초")

        # [AOI 주의] deck_cols가 변경되었을 수 있으므로 호출 측에서 반드시 처리해야 한다:
        #   aoi_manager.update_deck(game_state.deck)
        # 이를 누락하면 새로 추가된 카드 열에 대한 AOI가 존재하지 않아
        # gaze_events.csv 누락, EyeLink INTEREST_AREA 미등록, LabJack 트리거 미발송이 발생한다.
        # 호출 위치: 이 함수 반환 직후, 다음 시행 register_with_eyelink() 전.

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
        if not self.game_timer.is_running:
            self.game_timer.start()

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
    
    def user_click_card(self, card_row, card_col, defer_success_move=False):
        """
        사용자가 메인 카드 클릭
        
        Args:
            card_row (int): 카드 행
            card_col (int): 카드 열
        
        Args:
            defer_success_move (bool): True면 성공 시 즉시 토큰 이동하지 않고 호출자가 후처리

        Returns:
            str: 결과 ('success', 'failure', 'timeout', 'error')
        """
        if self.phase != self.PHASE_GAME_PLAY:
            return 'error'
        
        if self.current_turn != self.TURN_USER:
            return 'error'
        
        # 타이머 확인 (15초 초과 시 턴 종료)
        if self.timer.is_expired():
            print("시간 초과!")
            self.end_user_turn()
            return 'timeout'
        
        # 현재까지 경과 시간 기록 (카드 뒤집기 전)
        elapsed_time = self.timer.get_elapsed()
        
        # 카드 뒤집기
        self.deck.flip_card(card_row, card_col)
        
        # 매칭 확인
        card = self.deck.get_card(card_row, card_col)
        condition = self.get_target_condition()
        is_match = check_match(condition, card)
        
        # 시행 기록 저장
        trial = {
            'trial_id': self.trial_id,       # EDF/LabJack 동기화 키
            'round': self.current_round,
            'turn': self.turn_count,
            'token': self.selected_token,
            'target_pos': self.get_target_position(),
            'condition': condition,
            'selected_card_pos': (card_row, card_col),
            'selected_card': card,
            'is_match': is_match,
            'elapsed_time': elapsed_time,    # 이번 시도에 걸린 시간
            'timestamp': time.time(),        # 절대 시각 (UNIX epoch)
        }
        self.trial_history.append(trial)
        self._record_user_observation((card_row, card_col), card, is_match)

        if is_match:
            is_steal = self._is_npc_steal(card)
            score_gained = self._add_user_match_score(elapsed_time, is_steal)
            steal_msg = " [NPC 탈취! +200]" if is_steal else ""
            print(f"성공! +{score_gained}점 (콤보:{self.user_combo}){steal_msg} → 누적:{self.user_score}")

            if defer_success_move:
                print("피드백 후 토큰 이동 예정")
                return 'success'

            # 성공: 토큰 이동
            move_result = self.complete_user_success_move()
            return move_result  # 'success', 'token_switched', 또는 'user_caught_npc'
        else:
            # 실패: 패널티 적용 후 턴 종료
            self._add_user_penalty_score()
            print(f"실패! {SCORE_PENALTY}점 → 누적:{self.user_score}")
            self.end_user_turn()
            return 'failure'

    def _is_flight_directly_behind_chase(self):
        """
        flight가 chase 바로 뒤에 위치하는지 확인.
        트랙 순서상 flight의 다음 칸이 chase인 경우 True.

        Returns:
            bool
        """
        flight_pos = self.tokens.get_token('flight').get_position()
        chase_pos = self.tokens.get_token('chase').get_position()
        return self.tokens.get_next_position(flight_pos) == chase_pos

    def complete_user_success_move(self):
        """
        사용자 성공 후 토큰 이동 및 승패 확인.

        flight 이동 후 chase 바로 뒤에 위치하게 되면
        자동으로 selected_token을 'chase'로 전환한다.

        chase 앞에 octopus와 flight가 연속으로 있을 때 chase가 이동하면
        맨 앞 flight의 타겟이 chase의 타겟이 되며, octopus를 추월한 것으로 승리.

        Returns:
            str: 'success', 'token_switched', 또는 'user_caught_npc'
        """
        if self.selected_token is None:
            return 'error'

        moved_token = self.selected_token

        # 이동 전에 2개 연속 장애물 추월 상황인지 확인 (chase 한정)
        two_obstacle_overtake = (
            moved_token == 'chase' and
            self.tokens.has_two_consecutive_obstacles('chase')
        )

        target_pos = self.get_target_position()
        self.tokens.move_token(moved_token, target_pos)
        self.user_move_count += 1

        print(f"성공! {moved_token}가 {target_pos}로 이동")

        # 잡기 이벤트 확인 (게임 종료 없이 점수/위치 처리)
        catch_result = self.check_catch_event()
        if catch_result:
            return catch_result  # 'user_caught_npc'

        # 2개 연속 장애물(octopus + flight)을 추월 → 승리
        if two_obstacle_overtake:
            print("[추월 승리] chase가 octopus를 추월하여 flight 앞으로 이동! 승리!")
            return self._handle_user_caught_npc()

        # flight 이동 후 chase 바로 뒤에 붙었는지 확인
        if moved_token == 'flight' and self._is_flight_directly_behind_chase():
            self.selected_token = 'chase'
            self.seq_memory_skip_on_switch = True  # 전환 직후 첫 시도에서 seq_memory 억제
            print(f"[전환] flight가 chase 바로 뒤에 위치 → 선택 닭을 chase로 전환")
            return 'token_switched'

        return 'success'

    # SEQUENTIAL MEMORY

    def deactivate_seq_memory(self):
        """순차 메모리 비활성화 및 상태 초기화."""
        self.seq_memory_active  = False
        self.seq_memory_targets = []
        self.seq_memory_step    = 0
        self.seq_memory_is_pc   = False

    def _compute_seq_targets(self, token_name: str, n_steps: int) -> list:
        """
        token_name 토큰의 현재 위치에서 n_steps칸 앞까지 순차 타겟 수집
        """
        all_positions = self.tokens.get_all_positions()
        occupied = {
            pos for name, pos in all_positions.items()
            if name != token_name
        }

        token = self.tokens.get_token(token_name)
        if not token:
            return []

        targets = []
        pos = self.tokens.get_next_position(token.get_position())

        while pos is not None and len(targets) < n_steps:
            if pos in occupied:
                # 차단 토큰 발견: 바로 다음 칸(+1)이 비어 있으면 마지막 타겟으로 추가 후 중단
                next_pos = self.tokens.get_next_position(pos)
                if next_pos is not None and next_pos not in occupied:
                    targets.append(next_pos)
                break
            targets.append(pos)
            pos = self.tokens.get_next_position(pos)

        return targets

    def try_activate_seq_memory(self) -> bool:
        """
        사용자 새 시도 시작 시 호출.
        round_score >= threshold + 확률 조건 충족 시 순차 메모리 활성화.
        이미 활성 중이면 True 반환 (재발동 없음).
        Returns: 활성화 여부
        """
        if self.seq_memory_active:
            return True
        # token_switched 직후 한 번은 seq_memory를 억제
        if self.seq_memory_skip_on_switch:
            self.seq_memory_skip_on_switch = False
            print("[SEQ MEMORY] token_switched 직후 → 이번 시도 발동 억제")
            return False
        if self.round_score < SEQ_MEMORY_SCORE_THRESHOLD:
            return False
        if random.random() >= SEQ_MEMORY_TRIGGER_PROB:
            return False
        if self.selected_token is None:
            return False

        n = random.randint(SEQ_MEMORY_MIN_STEPS, SEQ_MEMORY_MAX_STEPS)
        targets = self._compute_seq_targets(self.selected_token, n)
        if len(targets) < 2:
            return False

        self.seq_memory_targets = targets
        self.seq_memory_step    = 0
        self.seq_memory_active  = True
        self.seq_memory_is_pc   = False
        print(f"[SEQ MEMORY] 사용자 발동! {len(targets)}칸 순차 타겟: {targets}")
        return True

    def try_activate_pc_seq_memory(self) -> bool:
        """
        PC 새 시도 시작 시 호출.
        pc_round_score >= threshold + 확률 조건 충족 시 순차 메모리 활성화.
        Returns: 활성화 여부
        """
        if self.seq_memory_active:
            return True
        if self.pc_round_score < SEQ_MEMORY_PC_THRESHOLD:
            return False
        if random.random() >= SEQ_MEMORY_TRIGGER_PROB:
            return False

        n = random.randint(SEQ_MEMORY_MIN_STEPS, SEQ_MEMORY_MAX_STEPS)
        targets = self._compute_seq_targets('octopus', n)
        if len(targets) < 2:
            return False

        self.seq_memory_targets = targets
        self.seq_memory_step    = 0
        self.seq_memory_active  = True
        self.seq_memory_is_pc   = True
        print(f"[SEQ MEMORY] PC 발동! {len(targets)}칸 순차 타겟: {targets}")
        return True

    def get_seq_memory_current_target(self):
        """현재 처리해야 할 순차 타겟 위치 반환."""
        if not self.seq_memory_active or self.seq_memory_step >= len(self.seq_memory_targets):
            return None
        return self.seq_memory_targets[self.seq_memory_step]

    def check_seq_memory_card(self, card_row, card_col) -> str:
        """
        순차 메모리 모드에서 사용자 카드 클릭 처리.
        타이머는 리셋하지 않고 seq 전체를 하나의 타이머로 공유.
        Returns: 'step_success' | 'all_success' | 'failure'
        """
        current_target = self.get_seq_memory_current_target()
        if current_target is None:
            self.deactivate_seq_memory()
            self.end_user_turn()
            return 'failure'

        condition = self.board.get_condition(*current_target)
        elapsed   = self.timer.get_elapsed()

        self.deck.flip_card(card_row, card_col)
        card     = self.deck.get_card(card_row, card_col)
        is_match = check_match(condition, card)

        trial = {
            'trial_id':          self.trial_id,
            'round':             self.current_round,
            'turn':              self.turn_count,
            'token':             self.selected_token,
            'target_pos':        current_target,
            'condition':         condition,
            'selected_card_pos': (card_row, card_col),
            'selected_card':     card,
            'is_match':          is_match,
            'elapsed_time':      elapsed,
            'timestamp':         time.time(),
            'seq_memory_step':   self.seq_memory_step,
            'seq_memory_total':  len(self.seq_memory_targets),
        }
        self.trial_history.append(trial)
        self._record_user_observation((card_row, card_col), card, is_match)

        if not is_match:
            self._add_user_penalty_score()
            self.deactivate_seq_memory()
            self.end_user_turn()
            return 'failure'

        self._add_user_match_score(elapsed, is_steal=False)
        self.seq_memory_step += 1

        if self.seq_memory_step >= len(self.seq_memory_targets):
            return 'all_success'

        return 'step_success'

    def complete_seq_memory_move(self) -> str:
        """
        사용자 순차 메모리 전체 성공 후 토큰을 최종 타겟 위치로 점프 이동.
        Returns: 'user_caught_npc' | 'token_switched' | 'success'
        """
        if not self.seq_memory_targets:
            self.deactivate_seq_memory()
            return 'success'

        final_pos = self.seq_memory_targets[-1]
        steps     = len(self.seq_memory_targets)
        moved_token = self.selected_token

        self.tokens.move_token(moved_token, final_pos)
        self.user_move_count += steps
        self.deactivate_seq_memory()

        print(f"[SEQ MEMORY] {moved_token} {steps}칸 점프 → {final_pos}")

        catch_result = self.check_catch_event()
        if catch_result:
            return catch_result

        # flight가 chase 바로 뒤에 붙었는지 확인
        if moved_token == 'flight' and self._is_flight_directly_behind_chase():
            self.selected_token = 'chase'
            self.seq_memory_skip_on_switch = True  # 전환 직후 첫 시도에서 seq_memory 억제
            print(f"[전환] flight seq_memory 이동 후 chase 바로 뒤에 위치 → 선택 닭을 chase로 전환")
            return 'token_switched'

        return 'success'

    def check_pc_seq_memory_card(self) -> tuple:
        """
        순차 메모리 모드에서 PC 카드 선택 및 판정.
        Returns: (result, card_pos)
          result: 'step_success' | 'all_success' | 'failure'
        """
        current_target = self.get_seq_memory_current_target()
        if current_target is None:
            self.deactivate_seq_memory()
            self.end_pc_turn()
            return ('failure', None)

        condition = self.board.get_condition(*current_target)
        memory_context = self._build_npc_memory_context(condition)
        memory_context['recent_user_hint_pos']  = self._get_recent_user_hint_pos(condition)
        memory_context['recent_npc_failed_pos'] = self._get_recent_npc_failed_pos()
        memory_context['known_wrong_positions'] = self._get_known_wrong_positions(condition)

        selected_pos, is_match = self.npc_ai.select_card(
            self.deck, condition, memory_context=memory_context,
        )

        self.deck.flip_card(selected_pos[0], selected_pos[1])
        card = self.deck.get_card(selected_pos[0], selected_pos[1])

        trial = {
            'trial_id':          self.trial_id,
            'round':             self.current_round,
            'turn':              self.turn_count,
            'token':             'octopus',
            'target_pos':        current_target,
            'condition':         condition,
            'selected_card_pos': selected_pos,
            'selected_card':     card,
            'is_match':          is_match,
            'elapsed_time':      0,
            'timestamp':         time.time(),
            'seq_memory_step':   self.seq_memory_step,
            'seq_memory_total':  len(self.seq_memory_targets),
        }
        self.trial_history.append(trial)
        self._record_npc_observation(selected_pos, card)

        if not is_match:
            self._add_pc_penalty_score()
            self.deactivate_seq_memory()
            self.end_pc_turn()
            return ('failure', selected_pos)

        self._add_pc_match_score()
        self.seq_memory_step += 1

        if self.seq_memory_step >= len(self.seq_memory_targets):
            return ('all_success', selected_pos)

        return ('step_success', selected_pos)

    def complete_pc_seq_memory_move(self) -> str:
        """
        PC 순차 메모리 전체 성공 후 octopus를 최종 타겟 위치로 점프 이동.
        Returns: 'npc_caught_user' | 'success'
        """
        if not self.seq_memory_targets:
            self.deactivate_seq_memory()
            return 'success'

        final_pos = self.seq_memory_targets[-1]
        steps     = len(self.seq_memory_targets)

        self.tokens.move_token('octopus', final_pos)
        self.pc_move_count += steps
        self.deactivate_seq_memory()

        print(f"[SEQ MEMORY] octopus {steps}칸 점프 → {final_pos}")

        catch_result = self.check_catch_event()
        return catch_result if catch_result else 'success'

    def end_user_turn(self):
        """사용자 턴 종료 → PC 턴 시작"""
        self.timer.stop()
        self.deactivate_seq_memory()
        self.seq_memory_skip_on_switch = False  # 턴 종료 시 잔류 플래그 초기화
        self.current_turn = self.TURN_PC
        self.phase = self.PHASE_GAME_PLAY
        self.selected_token = None  # 다음 사용자 턴을 위해 리셋
        self._update_adaptive_npc_rate()
        print("사용자 턴 종료. PC 차례")
    
    def pc_turn_step(self, defer_success_move=False):
        """
        PC 턴 1회 시도

        Args:
            defer_success_move (bool): True면 성공 시 즉시 토큰 이동하지 않고 호출자가 후처리
        
        Returns:
            tuple: (result, card_pos) - result는 'success', 'failure', 'npc_caught_user', card_pos는 (row, col)
        """
        if self.current_turn != self.TURN_PC:
            return ('error', None)
        
        # 타겟 확인
        target_pos = self.tokens.get_target_position('octopus')
        condition = self.board.get_condition(target_pos[0], target_pos[1])
        memory_context = self._build_npc_memory_context(condition)
        memory_context['recent_user_hint_pos'] = self._get_recent_user_hint_pos(condition)
        memory_context['recent_npc_failed_pos'] = self._get_recent_npc_failed_pos()
        memory_context['known_wrong_positions'] = self._get_known_wrong_positions(condition)
        
        # NPC AI를 통해 카드 선택 (동적 확률 + 기억 기반)
        selected_pos, is_match = self.npc_ai.select_card(
            self.deck,
            condition,
            memory_context=memory_context,
        )
        
        # 카드 뒤집기
        self.deck.flip_card(selected_pos[0], selected_pos[1])
        card = self.deck.get_card(selected_pos[0], selected_pos[1])
        
        # 기록
        trial = {
            'trial_id': self.trial_id,       # EDF/LabJack 동기화 키
            'round': self.current_round,
            'turn': self.turn_count,
            'token': 'octopus',
            'target_pos': target_pos,
            'condition': condition,
            'selected_card_pos': selected_pos,
            'selected_card': card,
            'is_match': is_match,
            'elapsed_time': 0,
            'timestamp': time.time(),        # 절대 시각 (UNIX epoch)
        }
        self.trial_history.append(trial)
        self._record_npc_observation(selected_pos, card)
        
        if is_match:
            score_gained = self._add_pc_match_score()
            print(f"PC 성공! +{score_gained}점 (콤보:{self.pc_combo}) → 누적:{self.pc_score}")

            if defer_success_move:
                print("피드백 후 토큰 이동 예정")
                return ('success', selected_pos)

            # 성공: 문어 이동
            move_result = self.complete_pc_success_move()
            # move_result: 'success' 또는 'npc_caught_user'
            return (move_result, selected_pos)
        else:
            # 실패: PC 패널티 적용 후 턴 종료
            self._add_pc_penalty_score()
            print(f"PC 실패! {SCORE_PENALTY}점 → 누적:{self.pc_score}")
            self.end_pc_turn()
            return ('failure', selected_pos)

    def complete_pc_success_move(self):
        """
        PC 성공 후 토큰 이동 및 승패 확인

        Returns:
            str: 'success' 또는 'npc_caught_user'
        """
        target_pos = self.tokens.get_target_position('octopus')
        self.tokens.move_token('octopus', target_pos)
        self.pc_move_count += 1
        print(f"PC 성공! Octopus가 {target_pos}로 이동")

        # 잡기 이벤트 확인 (게임 종료 없이 점수/위치 처리)
        catch_result = self.check_catch_event()
        if catch_result:
            return catch_result  # 'npc_caught_user'

        return 'success'
    
    def end_pc_turn(self):
        """PC 턴 종료 → 사용자 턴 시작"""
        self.deactivate_seq_memory()
        self.current_turn = self.TURN_USER
        self.phase = self.PHASE_TOKEN_SELECTION
        self.selected_token = None  # 사용자가 다시 닭을 선택하도록
        self.turn_count += 1
        print(f"PC 턴 종료. 사용자 차례 (턴 {self.turn_count})")
    
    def check_catch_event(self):
        """
        잡기 이벤트 확인 및 처리. 게임을 종료하지 않고 점수/위치를 갱신한다.

        Returns:
            str or None: 'user_caught_npc', 'npc_caught_user', 또는 None
        """
        if self.tokens.check_victory():
            return self._handle_user_caught_npc()
        if self.tokens.check_defeat():
            return self._handle_npc_caught_user()
        return None

    def _handle_user_caught_npc(self):
        """사용자(chase)가 문어(octopus)를 잡았을 때 처리."""
        self.user_catch_count += 1
        self.user_score += SCORE_CATCH_BONUS
        self._reset_round_board_state()
        print(f"[잡기] 사용자가 문어를 잡음! +{SCORE_CATCH_BONUS}점 | "
              f"누적:{self.user_score} | 잡기횟수:{self.user_catch_count}")
        return 'user_caught_npc'

    def _handle_npc_caught_user(self):
        """문어(octopus)가 flight를 잡았을 때 처리."""
        self.pc_catch_count += 1
        self.user_score += SCORE_CAUGHT_PENALTY
        self.pc_score += SCORE_PC_CATCH_BONUS
        self.user_combo = 0   # 잡혔으므로 콤보 초기화
        self._reset_round_board_state()
        print(f"[잡기] 문어가 flight를 잡음! {SCORE_CAUGHT_PENALTY}점 | "
              f"유저:{self.user_score} | PC:{self.pc_score} | "
              f"PC잡기횟수:{self.pc_catch_count}")
        return 'npc_caught_user'
    
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
        self.board = ConditionBoard(mode_profile=self.selected_mode)
        self.deck = MainDeck(mode_profile=self.selected_mode)
        self.tokens = TokenManager(mode_profile=self.selected_mode, board=self.board)
        
        self.phase = self.PHASE_NOT_STARTED
        self.current_turn = self.TURN_USER
        self.selected_token = None
        
        self.current_round = 1
        self.total_rounds = TOTAL_ROUNDS
        self.turn_time_limit = ROUND_TURN_LIMITS[0]
        self.timer.time_limit = self.turn_time_limit
        self.timer.stop()
        self.game_timer.stop()

        self.user_score = 0
        self.pc_score = 0
        self._pc_round_start_score = 0
        self.user_combo = 0
        self.pc_combo = 0
        self.user_catch_count = 0
        self.pc_catch_count = 0

        self.turn_count = 0
        self.user_move_count = 0
        self.pc_move_count = 0
        self.trial_history = []
        self.user_accuracy_ewma = self.base_random_rate
        self.user_seen_cards = {}
        self.npc_seen_cards = {}
        self.user_choice_count = 0
        self.user_repeat_count = 0
        self.user_last_selected_pos = None
        self.npc_ai.set_success_rate(self.base_random_rate, sync_effective=True)
        
        print("게임 리셋 완료")
    
    def get_seq_memory_summary(self) -> dict:
        """
        trial_history로부터 Sequential Memory 통계를 집계한다.

        - 발동 횟수 기준: seq_memory_step == 0 인 trial (각 seq의 첫 번째 스텝)
        - 전체 성공 기준: seq_memory_step == seq_memory_total - 1 이면서 is_match == True
        - 실패 기준: is_match == False 인 seq trial
        """
        seq_trials = [t for t in self.trial_history
                      if t.get('seq_memory_step') is not None]
        user_seq   = [t for t in seq_trials if t.get('token') != 'octopus']
        pc_seq     = [t for t in seq_trials if t.get('token') == 'octopus']

        def _activations(trials):
            return sum(1 for t in trials if t.get('seq_memory_step', -1) == 0)

        def _all_success(trials):
            # 마지막 스텝(step == total-1)을 성공한 횟수
            return sum(
                1 for t in trials
                if t.get('is_match') and
                   t.get('seq_memory_step', -1) == (t.get('seq_memory_total', 0) - 1)
            )

        def _step_fail(trials):
            return sum(1 for t in trials if not t.get('is_match'))

        return {
            'user_activations':      _activations(user_seq),
            'user_all_success':      _all_success(user_seq),
            'user_step_fail':        _step_fail(user_seq),
            'user_total_seq_trials': len(user_seq),
            'pc_activations':        _activations(pc_seq),
            'pc_all_success':        _all_success(pc_seq),
            'pc_step_fail':          _step_fail(pc_seq),
            'pc_total_seq_trials':   len(pc_seq),
        }

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
            'selected_mode_id': self.selected_mode_id,
            'selected_mode': self.selected_mode,
            'current_round': self.current_round,
            'total_rounds': self.total_rounds,
            'round_time_remaining': round(self.get_round_time_remaining(), 1),
            'user_score': self.user_score,
            'pc_score': self.pc_score,
            'user_combo': self.user_combo,
            'pc_combo': self.pc_combo,
            'user_catch_count': self.user_catch_count,
            'pc_catch_count': self.pc_catch_count,
            'game_time_remaining': round(self.get_game_time_remaining(), 1),
            'user_moves': self.user_move_count,
            'pc_moves': self.pc_move_count,
            'total_trials': len(self.trial_history),
            'user_seen_cards': len(self.user_seen_cards),
            'npc_seen_cards': len(self.npc_seen_cards),
            'npc_success_rate': round(self.npc_ai.success_rate, 4),
            'token_positions': self.tokens.get_all_positions(),
            'seq_memory': self.get_seq_memory_summary(),
        }

