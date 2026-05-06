# LabJack T4 TTL 트리거 유틸리티

try:
    import ljm
    _LJM_AVAILABLE = True
except ImportError:
    _LJM_AVAILABLE = False


# Trigger latch 핀: CIO0 (CIO_STATE 비트 0)
_LATCH_CIO_STATE = 1  # HIGH


# ============================================================================
# 트리거 코드 상수
# ============================================================================

TRIG_RESET            = 0

TRIG_CARD_CLICK       = 100   # 사용자 덱 카드 클릭 (운동 반응 onset)
TRIG_CARD_FLIP_USER   = 101   # 사용자 카드 뒤집기 visual onset
TRIG_CARD_FLIP_PC     = 102   # PC 카드 뒤집기 visual onset

TRIG_TOKEN_CHASE      = 110   # 닭 선택 – chase
TRIG_TOKEN_FLIGHT     = 111   # 닭 선택 – flight

TRIG_TRIAL_START      = 200
TRIG_TRIAL_END        = 201

TRIG_FEEDBACK_SUCCESS = 210   # 피드백: 성공 (FRN/P300 onset)
TRIG_FEEDBACK_FAILURE = 211   # 피드백: 실패
TRIG_FEEDBACK_TIMEOUT = 212   # 피드백: 타임아웃

TRIG_SEQ_ACTIVATE     = 220   # 순차 메모리 활성화 onset
TRIG_SEQ_STEP_SUCCESS = 221   # 순차 메모리 스텝 성공 피드백
TRIG_SEQ_ALL_SUCCESS  = 222   # 순차 메모리 전체 성공 피드백
TRIG_SEQ_FAILURE      = 223   # 순차 메모리 실패 피드백


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
        # info   = ljm.getHandleInfo(handle)
        # print(f"[LabJack] 연결 성공: {info}")

        # EIO 및 CIO 포트를 출력으로 설정하고 초기화
        names = ["EIO_DIRECTION", "EIO_STATE", "CIO_DIRECTION", "CIO_STATE"]
        values = [0xFF, 0, 0x0F, 0]

        ljm.eWriteNames(handle, len(names), names, values)

        print("[LabJack] EIO(데이터 8핀) + CIO0(trigger latch) 초기화 완료")
        return handle

    except Exception as e:
        print(f"[LabJack] 연결 실패: {e}")
        return None


def close_labjack(handle: int | None):
    if handle is None:
        return
    try:
        reset_trigger(handle)
        ljm.close(handle)
        print("[LabJack] 연결 종료")
    except Exception as e:
        print(f"[LabJack] 종료 오류: {e}")


# ============================================================================
# 트리거 전송(포토다이오드 동기화)
# ============================================================================

def set_trigger(handle: int | None, code: int):
    """
    EEG 동기화를 위한 하드웨어 트리거 설정

    동작 방식:
    - LJM API의 eWriteNames는 동기(Blocking) 방식으로 동작함.
    - USB 왕복(Round-trip) 완료 후 함수가 반환되므로(~1–4ms),
      반환 시점과 실제 하드웨어 신호 발생 시점이 밀접하게 동기화됨.
    - Non-blocking 방식보다 지터(Jitter)가 적어 정밀한 데이터 라벨링에 유리함.
    """
    # EIO_STATE에 코드 값, CIO_STATE를 HIGH(1.0)로 설정하여 Rising Edge 발생
    ljm.eWriteNames(handle, 2, ["EIO_STATE", "CIO_STATE"], [float(code), float(_LATCH_CIO_STATE)])


def reset_trigger(handle: int | None):
    """CIO0(latch)를 LOW로 내리고 EIO_STATE를 0으로 리셋합니다."""
    if handle is None:
        return
    try:
        ljm.eWriteNames(handle, 2, ["EIO_STATE", "CIO_STATE"], [0.0, 0.0])
    except Exception as e:
        print(f"[LabJack] 리셋 오류: {e}")


