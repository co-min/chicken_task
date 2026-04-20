"""
calibrate_time_drop.py
======================
포토다이오드(LabJack T4 AIN0)로 TTL 전송 시각과 실제 픽셀 발광 시각의
차이(time drop)를 측정하는 독립 실행 스크립트.

사용법:
    python calibrate_time_drop.py

준비물:
    - 포토다이오드를 화면 좌하단 (FRAME_MARKER_POS 위치)에 부착
    - 포토다이오드 출력선을 LabJack T4 AIN0 핀에 연결

결과:
    - 평균 / 표준편차 / 최소 / 최대 time drop 출력
    - config.py에 기록할 DISPLAY_OFFSET_S 값 제안
"""

import time
import sys
from pathlib import Path

import numpy as np
from psychopy import visual, core, event

sys.path.insert(0, str(Path(__file__).parent))
from config import (
    BG_COLOR, MONITOR_NAME,
    FRAME_MARKER_SIZE,
)
from utils.labjack_triggers import (
    init_labjack, close_labjack,
    send_trigger_async, reset_trigger,
    _LJM_AVAILABLE,
)

# ── 캘리브레이션 파라미터 ──────────────────────────────────────────────
N_TRIALS          = 50       # 측정 반복 횟수
ITI_S             = 0.6      # 시행 간 간격 (초) — 포토다이오드 복귀 대기
TTL_CODE          = 255      # 캘리브레이션용 트리거 코드
PD_CHANNEL        = "AIN0"   # 포토다이오드 연결 LabJack 채널
PD_THRESHOLD_V    = 1.5      # 포토다이오드 감지 전압 임계값 (V)
PD_TIMEOUT_S      = 0.200    # 포토다이오드 감지 타임아웃 (초)
MARKER_FRAMES     = 4        # 마커 표시 프레임 수 (frame_marker.py 기본값과 동일)

# ── LabJack 임포트 ─────────────────────────────────────────────────────
if _LJM_AVAILABLE:
    import ljm
else:
    ljm = None


def _read_pd(handle) -> float:
    """AIN0 전압 읽기 (V). LabJack 미연결 시 0 반환."""
    if handle is None or ljm is None:
        return 0.0
    try:
        return ljm.eReadName(handle, PD_CHANNEL)
    except Exception:
        return 0.0


def _wait_pd_onset(handle, timeout_s: float) -> float | None:
    """
    포토다이오드가 PD_THRESHOLD_V를 초과할 때까지 busy-wait.

    Returns
    -------
    float | None
        감지 시각(time.perf_counter()), 타임아웃 시 None.
    """
    deadline = time.perf_counter() + timeout_s
    while time.perf_counter() < deadline:
        if _read_pd(handle) > PD_THRESHOLD_V:
            return time.perf_counter()
    return None


def _wait_pd_off(handle, timeout_s: float = 0.5):
    """포토다이오드가 꺼질 때까지 대기 (다음 시행 전 복귀 확인)."""
    deadline = time.perf_counter() + timeout_s
    while time.perf_counter() < deadline:
        if _read_pd(handle) < PD_THRESHOLD_V * 0.5:
            return
    print("[경고] 포토다이오드가 꺼지지 않음 — 부착 위치 확인 필요")


def _make_window():
    """캘리브레이션용 PsychoPy 창 생성."""
    from psychopy import monitors
    mon = monitors.Monitor(MONITOR_NAME)
    win = visual.Window(
        fullscr=True,
        color=[c / 127.5 - 1 for c in BG_COLOR],
        units='pix',
        monitor=mon,
        allowGUI=False,
    )
    return win


def _compute_marker_pos(win) -> tuple[int, int]:
    """화면 좌하단 모서리 좌표 계산 (FRAME_MARKER_POS=None 대응)."""
    w, h = win.size
    margin_x = FRAME_MARKER_SIZE[0] // 2 + 5
    margin_y = FRAME_MARKER_SIZE[1] // 2 + 5
    return (-w // 2 + margin_x, -h // 2 + margin_y)


def run_calibration():
    print("=" * 56)
    print("  Time Drop 캘리브레이션")
    print("=" * 56)
    print(f"  포토다이오드 채널 : {PD_CHANNEL}")
    print(f"  감지 임계 전압    : {PD_THRESHOLD_V} V")
    print(f"  반복 횟수         : {N_TRIALS} 회")
    print("=" * 56)

    # ── LabJack 초기화 ─────────────────────────────────────────────
    handle = init_labjack()
    if handle is None:
        print("[오류] LabJack 연결 실패. 하드웨어를 확인하세요.")
        return

    # ── 초기 포토다이오드 전압 확인 ────────────────────────────────
    v0 = _read_pd(handle)
    print(f"\n현재 AIN0 전압: {v0:.3f} V")
    if v0 > PD_THRESHOLD_V:
        print("[경고] 마커가 없는데 전압이 높습니다. 포토다이오드 위치를 확인하세요.")
        input("계속하려면 Enter...")

    # ── PsychoPy 창 생성 ───────────────────────────────────────────
    win = _make_window()
    marker_pos = _compute_marker_pos(win)

    marker_rect = visual.Rect(
        win,
        width=FRAME_MARKER_SIZE[0],
        height=FRAME_MARKER_SIZE[1],
        fillColor='white',
        lineColor='white',
        pos=marker_pos,
        units='pix',
    )
    guide_text = visual.TextStim(
        win,
        text=(
            f"Time Drop 캘리브레이션 중...\n\n"
            f"포토다이오드가 화면 좌하단에 부착되어 있는지 확인하세요.\n"
            f"(위치: {marker_pos})\n\n"
            f"ESC: 중단"
        ),
        color='white',
        height=30,
        units='pix',
    )

    offsets   = []   # 측정된 time drop 목록 (초)
    timeouts  = 0    # 감지 실패 횟수

    print(f"\n측정 시작...\n")

    for trial in range(N_TRIALS):

        # ESC 체크
        if 'escape' in event.getKeys():
            print("\n[중단] ESC 키 입력")
            break

        # 배경 + 안내 텍스트 표시 (마커 없음)
        guide_text.text = (
            f"측정 중: {trial + 1} / {N_TRIALS}\n"
            f"성공: {len(offsets)}  타임아웃: {timeouts}"
        )
        guide_text.draw()
        win.flip()
        core.wait(ITI_S)

        # ── 마커 + TTL 동시 전송 ───────────────────────────────────
        # callOnFlip: VSync 직후 TTL HIGH
        win.callOnFlip(send_trigger_async, handle, TTL_CODE)

        # 마커를 버퍼에 그림
        for _ in range(MARKER_FRAMES):
            marker_rect.draw()
            win.flip()
            # 첫 flip에서만 TTL 시각 기록
            if _ == 0:
                ttl_t = time.perf_counter()
                # 포토다이오드 감지 시작 (flip 직후 즉시)
                pd_t = _wait_pd_onset(handle, PD_TIMEOUT_S)
            if _ == MARKER_FRAMES - 1:
                reset_trigger(handle)

        # 마커 소거
        win.flip()

        # ── 결과 기록 ──────────────────────────────────────────────
        if pd_t is not None:
            drop_ms = (pd_t - ttl_t) * 1000
            offsets.append(pd_t - ttl_t)
            print(f"  [{trial + 1:>3}] time drop: {drop_ms:+6.2f} ms")
        else:
            timeouts += 1
            print(f"  [{trial + 1:>3}] 타임아웃 (포토다이오드 미감지)")

        # 포토다이오드 꺼짐 대기
        _wait_pd_off(handle)

    # ── 결과 출력 ──────────────────────────────────────────────────
    win.close()
    close_labjack(handle)

    print("\n" + "=" * 56)
    if len(offsets) == 0:
        print("  [오류] 측정 성공 데이터 없음.")
        print("  포토다이오드 연결 및 부착 위치를 확인하세요.")
        return

    arr = np.array(offsets) * 1000  # ms 단위
    print(f"  측정 성공   : {len(offsets)} / {N_TRIALS} 회")
    print(f"  타임아웃    : {timeouts} 회")
    print(f"  ─────────────────────────────────────────────")
    print(f"  평균 time drop : {arr.mean():.2f} ms")
    print(f"  표준편차       : {arr.std():.2f} ms")
    print(f"  최소 / 최대    : {arr.min():.2f} ms / {arr.max():.2f} ms")
    print("=" * 56)

    offset_s = arr.mean() / 1000
    print(f"\n→ config.py에 아래 값을 추가하세요:\n")
    print(f"  DISPLAY_OFFSET_S = {offset_s:.4f}  # time drop 보정값 (포토다이오드 측정)")
    print()


if __name__ == "__main__":
    run_calibration()
