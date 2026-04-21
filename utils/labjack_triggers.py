# LabJack T4 TTL 트리거 유틸리티
#
# 트리거 코드 규약:
#   0        : 리셋 / 무신호
#   10 ~ 33  : 보드 카드 AOI 진입
#   40 ~ 66  : 덱 카드 AOI 진입
#   100      : 사용자 카드 클릭
#   200/201  : TRIAL_START / TRIAL_END
#   210~212  : 피드백 (성공 / 실패 / 타임아웃)
#   220~223  : Sequential Memory (활성화 / 스텝 성공 / 전체 성공 / 실패)

try:
    import ljm
    _LJM_AVAILABLE = True
except ImportError:
    _LJM_AVAILABLE = False

import time

# 펄스 타이밍 허용 오차 (초). 이 값을 초과하면 TIMING MISMATCH 로그 출력.
_PULSE_TOLERANCE_S = 0.001  # 1 ms


# ============================================================================
# 연결 관리
# ============================================================================

def init_labjack(device: str = "T4",
                 connection: str = "USB",
                 identifier: str = "ANY") -> int | None:
    # LabJack T4 연결
    if not _LJM_AVAILABLE:
        print("[LabJack] ljm 라이브러리를 찾을 수 없습니다. 트리거가 비활성화됩니다.")
        return None

    try:
        handle = ljm.openS(device, connection, identifier)
        info   = ljm.getHandleInfo(handle)
        print(f"[LabJack] 연결 성공: {info}")

        # EIO 핀을 출력 모드로 설정 (방향 레지스터 1 = 출력)
        ljm.eWriteName(handle, "EIO_DIRECTION", 0xFF)  # 모든 EIO 핀 출력
        ljm.eWriteName(handle, "EIO_STATE",     0)     # 초기값 0

        return handle

    except Exception as e:
        print(f"[LabJack] 연결 실패: {e}")
        return None


def close_labjack(handle: int | None):
    if handle is None or not _LJM_AVAILABLE:
        return
    try:
        ljm.eWriteName(handle, "EIO_STATE", 0)
        ljm.close(handle)
        print("[LabJack] 연결 종료")
    except Exception as e:
        print(f"[LabJack] 종료 오류: {e}")


# ============================================================================
# 트리거 전송
# ============================================================================

def send_trigger(handle: int | None, code: int, pulse_s: float = 0.005):
    """EIO 포트로 TTL 트리거 펄스 전송 (블로킹, perf_counter busy-wait)."""
    if handle is None or not _LJM_AVAILABLE:
        return
    try:
        t_start = time.perf_counter()
        print(f"[LabJack] SEND code={code} ({t_start:.4f}s)")
        ljm.eWriteName(handle, "EIO_STATE", int(code))
        # busy-wait: time.sleep() 대신 perf_counter 루프로 정밀 대기
        while time.perf_counter() - t_start < pulse_s:
            pass
        ljm.eWriteName(handle, "EIO_STATE", 0)
        t_actual = time.perf_counter() - t_start
        if abs(t_actual - pulse_s) > _PULSE_TOLERANCE_S:
            print(
                f"[TIMING MISMATCH] send_trigger code={code}: "
                f"expected {pulse_s * 1000:.2f} ms, "
                f"actual {t_actual * 1000:.2f} ms "
                f"(diff {(t_actual - pulse_s) * 1000:+.2f} ms)"
            )
    except Exception as e:
        print(f"[LabJack] 트리거 전송 오류 (code={code}): {e}")


def send_trigger_async(handle: int | None, code: int):
    """EIO_STATE 설정 (비블로킹). 리셋은 호출자가 처리."""
    if handle is None or not _LJM_AVAILABLE:
        return
    try:
        ljm.eWriteName(handle, "EIO_STATE", int(code))
    except Exception as e:
        print(f"[LabJack] 비동기 트리거 오류 (code={code}): {e}")


def reset_trigger(handle: int | None):
    """EIO_STATE 를 0으로 리셋합니다."""
    if handle is None or not _LJM_AVAILABLE:
        return
    try:
        ljm.eWriteName(handle, "EIO_STATE", 0)
    except Exception as e:
        print(f"[LabJack] 리셋 오류: {e}")
