# LabJack T4 TTL 트리거 유틸리티

try:
    import ljm
    _LJM_AVAILABLE = True
except ImportError:
    _LJM_AVAILABLE = False


_LATCH_CIO_STATE = 1  # CIO0 HIGH → Rising Edge latch


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

# 라운드 식별 트리거 (21–40: round 1–20, 41: 전체 종료)
# 라운드 전환 시점에 별도 전송 → EEG 소프트웨어가 라운드 경계를 인식.
TRIG_ROUND_1          = 21
TRIG_ROUND_2          = 22
TRIG_ROUND_3          = 23
TRIG_ROUND_4          = 24
TRIG_ROUND_5          = 25
TRIG_ROUND_6          = 26
TRIG_ROUND_7          = 27
TRIG_ROUND_8          = 28
TRIG_ROUND_9          = 29
TRIG_ROUND_10         = 30
TRIG_ROUND_11         = 31
TRIG_ROUND_12         = 32
TRIG_ROUND_13         = 33
TRIG_ROUND_14         = 34
TRIG_ROUND_15         = 35
TRIG_ROUND_16         = 36
TRIG_ROUND_17         = 37
TRIG_ROUND_18         = 38
TRIG_ROUND_19         = 39
TRIG_ROUND_20         = 40
TRIG_ROUND_DONE       = 41   # 전체 라운드 종료


# ============================================================================
# 라운드별 동적 트리거
# ============================================================================

def get_round_trig(round_num: int) -> int:
    """Return the round-identifier trigger code for round_num (1–20)."""
    if not 1 <= round_num <= 20:
        raise ValueError(f"round_num must be 1–20, got {round_num}")
    return 20 + round_num


# ============================================================================
# 프레임 로그 (페이지/액션별 신호 기록)
# ============================================================================

frame_log: list[dict] = []


def _log_frame(page: str, action: str, trig_code: int, round_num: int):
    """
    Record a frame-level trigger event.
    Round 1 sets full_recovery=True — keeps enough detail to reconstruct all EEG epochs.
    """
    frame_log.append({
        "round":         round_num,
        "page":          page,
        "action":        action,
        "trig":          trig_code,
        "full_recovery": round_num == 1,
    })


# ============================================================================
# 연결 관리
# ============================================================================

def init_labjack(device: str = "T4",
                 connection: str = "USB",
                 identifier: str = "ANY") -> int | None:
    if not _LJM_AVAILABLE:
        print("[LabJack] ljm 라이브러리를 찾을 수 없습니다. 트리거가 비활성화됩니다.")
        return None
    try:
        handle = ljm.openS(device, connection, identifier)
        names  = ["EIO_DIRECTION", "EIO_STATE", "CIO_DIRECTION", "CIO_STATE"]
        ljm.eWriteNames(handle, len(names), names, [0xFF, 0, 0x0F, 0])
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
# 트리거 전송 (포토다이오드 동기화)
# ============================================================================

def set_trigger(handle: int | None, code: int, *,
                round_num: int = 1, page: str = "", action: str = ""):
    if handle is None:
        return
    if page or action:
        _log_frame(page, action, code, round_num)
    ljm.eWriteNames(handle, 2, ["EIO_STATE", "CIO_STATE"],
                    [float(code), float(_LATCH_CIO_STATE)])


def reset_trigger(handle: int | None):
    if handle is None:
        return
    try:
        ljm.eWriteNames(handle, 2, ["EIO_STATE", "CIO_STATE"], [0.0, 0.0])
    except Exception as e:
        print(f"[LabJack] 리셋 오류: {e}")
