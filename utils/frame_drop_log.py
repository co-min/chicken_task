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
        self._last_perf_t = None
