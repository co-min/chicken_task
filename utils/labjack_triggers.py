# utils/labjack_triggers.py
# LabJack T4 연결 및 TTL 트리거 유틸리티
#
# 사용법 예시:
#   handle = init_labjack()
#   send_trigger(handle, code=10)   # 10ms 블로킹 펄스
#   close_labjack(handle)
#
# 트리거 코드 규약 (config.py AOI_TRIGGER_* 상수와 연동):
#   0        : 리셋 / 무신호
#   10 ~ 33  : 보드 카드 AOI 진입 (AOI_TRIGGER_BOARD_OFFSET + position_index)
#   40 ~ 66  : 덱 카드  AOI 진입 (AOI_TRIGGER_DECK_OFFSET  + position_index)
#   100      : 사용자 덱 카드 클릭 (game_play.py 에서 직접 호출)
#   200      : 시행 시작 (TRIAL_START)
#   201      : 시행 종료 (TRIAL_END)
#   210      : 피드백 — 일반 성공 (FRN/P300 onset)
#   211      : 피드백 — 일반 실패
#   212      : 피드백 — 타임아웃
#   220      : Sequential Memory 활성화 onset (즉시 전송, VSync 불필요)
#   221      : Sequential Memory 스텝 성공 피드백
#   222      : Sequential Memory 전체 성공 피드백
#   223      : Sequential Memory 실패 피드백 

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
    """
    LabJack T4에 연결하고 핸들을 반환합니다.

    Parameters
    ----------
    device : str
        장치 유형. 기본값 "T4".
    connection : str
        연결 방식. "USB" | "ETHERNET" | "ANY". 기본값 "USB".
    identifier : str
        장치 식별자 (시리얼 번호 또는 "ANY"). 기본값 "ANY".

    Returns
    -------
    int | None
        성공하면 핸들 정수, 실패하면 None.
    """
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
    """
    LabJack 연결을 안전하게 종료합니다.
    종료 전 EIO_STATE 를 0으로 리셋합니다.
    """
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
    """
    LabJack T4 EIO 포트로 TTL 트리거 펄스를 전송합니다 (블로킹).

    Parameters
    ----------
    handle : int | None
        init_labjack() 에서 반환한 핸들. None 이면 아무것도 하지 않습니다.
    code : int
        0–255 범위의 8비트 트리거 코드. EIO0(LSB)~EIO7(MSB) 에 출력됩니다.
    pulse_s : float
        펄스 지속 시간(초). 기본 5ms.

    Notes
    -----
    time.sleep() 은 Windows OS 스케줄러 영향으로 수 ms~수십 ms 오차가 발생합니다.
    대신 perf_counter 기반 busy-wait 을 사용해 정밀도를 높이고,
    실제 펄스 폭이 허용 오차(_PULSE_TOLERANCE_S)를 초과하면 경고를 출력합니다.
    """
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
    """
    EIO_STATE 를 즉시 설정합니다 (비블로킹).
    리셋은 AOIManager 또는 호출자가 직접 처리해야 합니다.
    """
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
