"""
frame_drop_log.py
=================
sEEG 분석용 프레임 드랍 로거.

60 Hz 기준 프레임 간격(16.67 ms)보다 FRAME_DROP_THRESHOLD_MS 이상 길게 걸린 flip을
CSV에 즉시 append한다. 세션 도중 크래시가 나도 기존 행은 보존된다.

CSV 컬럼
--------
psychopy_t    : win.flip() 반환 직후 core.getTime() 값 (EDF/trials.csv 병합 기준)
inter_flip_ms : 직전 flip으로부터 경과 시간 (ms)
drop_ms       : inter_flip_ms - 16.67 ms (기대값 초과분)
drop_index    : 세션 내 드랍 누적 번호 (1부터)
trial_id      : 드랍 발생 시점의 trial_id (알 수 없으면 빈 문자열)
context       : 렌더링 컨텍스트 (예: 'user_render', 'pc_think', 'feedback')
"""
import time
import csv
from pathlib import Path

FRAME_DROP_THRESHOLD_MS = 25.0        # 1.5 × 16.67 ms: 이 이상이면 1프레임 드랍으로 기록
_EXPECTED_FRAME_MS      = 1000.0 / 60.0   # 16.666... ms


class FrameDropLogger:
    def __init__(self, log_path: str):
        self.log_path = log_path
        self._last_perf_t: float | None = None
        self._drop_count: int = 0
        Path(log_path).parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, 'w', newline='', encoding='utf-8') as f:
            csv.writer(f).writerow(
                ['psychopy_t', 'inter_flip_ms', 'drop_ms', 'drop_index', 'trial_id', 'context']
            )
        print(f"[FrameDropLogger] 초기화 완료: {log_path}")

    def after_flip(self, psychopy_t: float, trial_id=None, context: str = '') -> None:
        """win.flip() 반환 직후에 호출.

        직전 after_flip() 호출 대비 경과 시간이 FRAME_DROP_THRESHOLD_MS를 넘으면
        콘솔 경고를 출력하고 CSV에 즉시 기록한다.

        Parameters
        ----------
        psychopy_t : core.getTime() 값 — EDF/trials.csv 와 병합할 기준 타임스탬프.
        trial_id   : 현재 시행 ID (None 허용).
        context    : 호출 위치를 나타내는 짧은 문자열.
        """
        now = time.perf_counter()
        if self._last_perf_t is not None:
            inter_ms = (now - self._last_perf_t) * 1000.0
            if inter_ms > FRAME_DROP_THRESHOLD_MS:
                self._drop_count += 1
                drop_ms = inter_ms - _EXPECTED_FRAME_MS
                print(
                    f"[FRAME DROP #{self._drop_count}] {inter_ms:.2f} ms "
                    f"(+{drop_ms:.2f} ms)  trial={trial_id}  ctx={context}"
                )
                with open(self.log_path, 'a', newline='', encoding='utf-8') as f:
                    csv.writer(f).writerow([
                        f'{psychopy_t:.6f}',
                        f'{inter_ms:.3f}',
                        f'{drop_ms:.3f}',
                        self._drop_count,
                        trial_id if trial_id is not None else '',
                        context,
                    ])
        self._last_perf_t = now

    def reset(self) -> None:
        """알려진 렌더링 중단 구간 직후에 호출해 false positive를 방지한다.

        예: deferred TTL reset (5 ms busy-wait), core.wait(), 피드백 대기 등
        이전 flip 시각을 지워 다음 after_flip()이 간격을 계산하지 않도록 한다.
        """
        self._last_perf_t = None
