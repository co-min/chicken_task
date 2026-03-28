# 종료 화면

import sys
from pathlib import Path
from psychopy import visual, event

try:
	from ..config import TEXT_COLOR, GOLD, ORANGE_RED
	from ..view_func.frame_marker import blink_frame_marker, trigger_frame_marker
except ImportError:
	sys.path.insert(0, str(Path(__file__).parent.parent))
	from config import TEXT_COLOR, GOLD, ORANGE_RED
	from view_func.frame_marker import blink_frame_marker, trigger_frame_marker


def _determine_winner(game_state):
	"""누적 점수로 최종 승자 결정. (문자열, 색상) 반환."""
	u = game_state.user_score
	p = game_state.pc_score
	if u > p:
		return "사용자 승리!", GOLD
	elif p > u:
		return "문어 승리...", ORANGE_RED
	else:
		return "무승부!", [200, 200, 200]


def run_ending_phase(win, ui_elements, game_state, result):
	"""
	게임 종료 화면.

	Args:
		result: 'timeout' (10분 경과) 또는 'exit' (중단)
	"""
	# ── 결과 메시지 결정 ──
	if result == 'timeout':
		winner_msg, winner_color = _determine_winner(game_state)
		ui_elements.instruction_text.text = "게임 종료 — 최종 결과"
		ui_elements.message_text.text = winner_msg
		ui_elements.message_text.color = winner_color
	else:  # 'exit' 또는 기타 중단
		ui_elements.instruction_text.text = "게임 중단"
		ui_elements.message_text.text = "게임을 중단했습니다"
		ui_elements.message_text.color = [255, 255, 0]

	# ── 통계 텍스트 ──
	u_score = game_state.user_score
	p_score = game_state.pc_score
	u_catch = game_state.user_catch_count
	p_catch = game_state.pc_catch_count

	stats_lines = (
		f"내 점수: {u_score}점   |   문어 점수: {p_score}점\n\n"
		f"문어 잡기: {u_catch}회       잡힌 횟수: {p_catch}회\n\n"
		f"총 라운드: {game_state.current_round}/{game_state.total_rounds}   "
		f"총 턴: {game_state.turn_count}\n"
		f"사용자 이동: {game_state.user_move_count}회   "
		f"PC 이동: {game_state.pc_move_count}회   "
		f"총 시행: {len(game_state.trial_history)}회"
	)

	stats_text = visual.TextStim(
		win=win,
		text=stats_lines,
		pos=(0, 30),
		height=26,
		color=TEXT_COLOR,
		colorSpace='rgb255',
	)

	exit_text = visual.TextStim(
		win=win,
		text="아무 키나 눌러 종료하세요",
		pos=(0, -350),
		height=24,
		color=[255, 255, 255],
		colorSpace='rgb255',
	)

	ui_elements.instruction_text.draw()
	ui_elements.message_text.draw()
	stats_text.draw()
	exit_text.draw()
	trigger_frame_marker()   # 이벤트: 게임 종료 화면 표시
	blink_frame_marker(win)
	win.flip()
	event.waitKeys()

	# 콘솔 출력
	print(f"  ✓ 종료 화면 — 유저:{u_score}점 / PC:{p_score}점 "
		  f"(잡기:{u_catch} / 잡힘:{p_catch})")
