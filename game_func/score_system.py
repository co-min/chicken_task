import sys
from pathlib import Path

from utils.helpers import clamp
from ..config import (
        TURN_TIME_LIMIT, SCORE_MATCH, SCORE_COMBO_BONUS, SCORE_SPEED_MAX, SCORE_SPEED_MIN,
        SCORE_STEAL, SCORE_PENALTY, SCORE_CATCH_BONUS, SCORE_CAUGHT_PENALTY,
        SCORE_PC_CATCH_BONUS, BONUS_SCORE_MULTIPLIER,)


class ScoreSystem:
    """점수, 콤보, 잡기 횟수 상태 관리."""

    def __init__(self):
        self.user_score = 0
        self.pc_score = 0
        self.user_combo = 0
        self.pc_combo = 0
        self.user_catch_count = 0
        self.pc_catch_count = 0

    def speed_bonus(self, elapsed_time):
        ratio = 1.0 - clamp(elapsed_time / TURN_TIME_LIMIT, 0.0, 1.0)
        return max(SCORE_SPEED_MIN, round(SCORE_SPEED_MAX * ratio))

    def add_user_match(self, elapsed_time, is_steal=False, is_double_score=False):
        self.user_combo += 1
        score = SCORE_MATCH + self.speed_bonus(elapsed_time)
        if self.user_combo > 1:
            score += SCORE_COMBO_BONUS
        if is_steal:
            score += SCORE_STEAL
        if is_double_score:
            score *= BONUS_SCORE_MULTIPLIER
        self.user_score += score
        return score

    def add_user_penalty(self):
        self.user_combo = 0
        self.user_score += SCORE_PENALTY

    def add_pc_match(self, is_steal=False, is_double_score=False):
        self.pc_combo += 1
        score = SCORE_MATCH
        if self.pc_combo > 1:
            score += SCORE_COMBO_BONUS
        if is_steal:
            score += SCORE_STEAL
        if is_double_score:
            score *= BONUS_SCORE_MULTIPLIER
        self.pc_score += score
        return score

    def add_pc_penalty(self):
        self.pc_combo = 0
        self.pc_score += SCORE_PENALTY

    def apply_user_catch(self):
        self.user_catch_count += 1
        self.user_score += SCORE_CATCH_BONUS

    def apply_npc_catch(self):
        self.pc_catch_count += 1
        self.user_score += SCORE_CAUGHT_PENALTY
        self.pc_score += SCORE_PC_CATCH_BONUS
        self.user_combo = 0

    def reset(self):
        self.user_score = 0
        self.pc_score = 0
        self.user_combo = 0
        self.pc_combo = 0
        self.user_catch_count = 0
        self.pc_catch_count = 0
