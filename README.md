# Chicken Task

카드 매칭 기반의 인지과학/신경과학 실험용 게임

PsychoPy로 구현되었으며,
EyeLink 아이트래커 및 LabJack T4를 통한 생리신호 동기화

---

# 개요

참가자(닭)는 운동장 보드의 조건 카드를 참고하여 메인 덱에서 일치하는 카드를 선택
NPC(문어)가 동시에 덱 카드를 선택하며, 토큰(추격/도주)을 통해 추격-도주 상호작용이 발생.
적응형 NPC AI, 순차 메모리, 보너스 점수 시스템 등을 통해 난이도가 동적으로 조절.

---

# 주요 기능

- 카드 매칭: 색상(3) × 모양(3) × 숫자(3) 조건 카드를 기반으로 메인 덱 카드 선택

- 추격/도주 토큰: 참가자가 chase 또는 flight 토큰을 선택하여 NPC와 상호작용

- 적응형 NPC AI: 참가자의 성취 수준을 실시간으로 추정하여 NPC 정답률 동적 조정

- 순차 메모리(Sequential Memory): 일정 점수 이상 시 발동, 연속된 조건에 순서대로 카드를 매칭해야 보너스 이동

- 보너스 슬롯: 라운드별 고정/랜덤 보너스 칸 배치, 해당 칸 도착 시 점수 2배

- 난이도 자동 스케일: 덱 열 수 및 배치 방식(factorization/random) 8단계 선형 진행

- EyeLink 연동: AOI(Area of Interest) 기반 시선 이벤트 기록 및 LabJack TTL 트리거 전송

- 데이터 자동 저장: 세션/시행/시선 이벤트를 CSV·JSON 형식으로 자동 저장

---

# 프로젝트 구조

```
chicken_task_first/
├── main.py                   # 게임 진입점
├── config.py                 # 모든 설정 상수 (화면, 타이밍, 점수, AI 등)
├── initiate.py               # EyeLink·LabJack 초기화
├── set_up.py                 # 세션 설정 헬퍼
│
├── game_func/                # 게임 핵심 로직
│   ├── game_state.py         # 통합 게임 상태 관리
│   ├── board_class.py        # 조건 보드 (운동장)
│   ├── deck_class.py         # 메인 덱
│   ├── token_class.py        # 토큰 관리 (chase / flight / octopus)
│   └── npc_ai.py             # NPC(문어) 적응형 AI
│
├── phase_func/               # 게임 진행 단계 (phase)
│   ├── starting.py           # 게임 모드 선택 화면
│   ├── tutorial.py           # 튜토리얼
│   ├── token_selection.py    # 토큰 선택 (chase / flight)
│   ├── game_play.py          # 메인 플레이 루프
│   ├── feedback.py           # 피드백 표시
│   └── ending.py             # 종료 화면
│
├── view_func/                # 렌더링
│   ├── board_renderer.py     # 보드 카드 렌더링
│   ├── deck_renderer.py      # 덱 카드 렌더링
│   ├── token_renderer.py     # 토큰 렌더링
│   ├── ui_elements.py        # HUD, 점수판, 닉네임 등 UI
│   └── frame_marker.py       # 포토다이오드 마커 (이벤트 후 N 프레임 동안 흰 사각형 표시)
│
├── eye_func/                 # EyeLink 아이트래커 연동
│   ├── aoi_manager.py        # AOI 정의 및 시선 이벤트 관리
│   └── EyeLinkCoreGraphicsPsychoPy.py
│
├── save_func/                # 데이터 저장
│   ├── session_saver.py      # session.json (세션 메타데이터)
│   ├── trial_saver.py        # trials.csv (시행별 결과)
│   └── gaze_event_saver.py   # gaze_events.csv (시선 AOI 이벤트)
│
├── utils/                    # 유틸리티
│   ├── card_matcher.py       # 카드 속성 일치 판정
│   ├── labjack_triggers.py   # LabJack T4 TTL 트리거
│   ├── timer.py              # 게임 타이머
│   ├── helpers.py            # 공통 유틸
│   └── validators.py         # 입력 검증
│
├── stimuli/                  # 이미지 자극
│   ├── main_cards/           # 메인 덱 카드 (색×모양×숫자, 27종)
│   ├── condition_cards/      # 조건 카드 (색/모양/숫자 각 3종)
│   ├── tokens/               # 토큰 이미지 (chase, flight, octopus)
│   ├── selection/            # 게임 모드 선택 화면 미리보기
│   └── ui/                   # 카드 뒷면 등 UI 이미지
│
├── sounds/                   # 효과음
│   ├── correct.wav / error.wav / flip.wav
│   ├── win.wav / lose.wav
│   └── npc_flip.wav 등
│
├── Data/                     # 실험 결과 (자동 생성)
│   └── {subject_id}_{YYYYMMDD_HHMMSS}/
│       ├── session.json
│       ├── trials.csv
│       └── gaze_events.csv
│
├── pylink/                   # SR Research PyLink 라이브러리 (내장)
└── requirements.txt
```

---

# 설치

# 요구 사항

- Python 3.11 (PsychoPy가 3.12 이상 미지원)
- Windows 10/11 권장

# 실행

```bash
1. python set_up.py 실행
2. chicken_env\Scripts\activate
3. python main.py
4. 피험자 ID 입력 (예: `P001`).
5. 데이터는 `Data/{subject_id}_{timestamp}/` 에 자동 저장
```

# (선택) EyeLink 설치

```bash
pip install eye_func/psychopy_eyetracker_sr_research-0.0.5-py3-none-any.whl
```

---

# 설정 (`config.py`)

| 항목 | 변수 | 기본값 |
| --- | --- | --- |
| 화면 해상도 자동 감지 | `AUTO_DETECT_WINDOW_SIZE` | `True` |
| 전체화면 | `FULLSCREEN` | `True` |
| 창 모드 강제 | `FORCE_WINDOWED_MODE` | `False` |
| EyeLink 사용 | `USE_EYELINK` | `0` |
| LabJack T4 사용 | `USE_LABJACK` | `1` |
| 턴 제한 시간 (초) | `TURN_TIME_LIMIT` | `15` |
| 게임 총 제한 시간 (초) | `GAME_TIME_LIMIT` | `1800` |

---

# 게임 흐름

```
게임 모드 선택 → 튜토리얼 → [토큰 선택 → 카드 매칭 → 피드백] × N → 종료
```

1. 연습게임
2. 토큰 선택: 매 라운드 시작 시 chase(추격) 또는 flight(도주) 선택
3. 카드 매칭: 보드의 조건 카드를 보고 메인 덱에서 일치하는 카드를 제한 시간 내에 선택
4. NPC 경쟁: 문어(NPC)가 덱 카드를 선택 — 적응형 AI가 참가자 수준에 맞게 정답률 조절
5. 피드백: 성공/실패/타임아웃 결과와 점수 표시
6. catch 이벤트: 토큰 위치에 따라 추격/피포획 이벤트 발생, 보너스 및 패널티

---

# 렌더링 루프 구조

모든 게임 상태에서 `win.flip()`이 매 프레임(60 Hz, 16.67 ms) 호출되는 **per-frame 루프**로 구현되어 있습니다.

```
while True:                          # 게임 메인 루프
    [입력 처리]                       # 키보드 / 마우스 polling
    [게임 상태 업데이트]
    [자극 draw]
    blink_frame_marker(win)          # 포토다이오드 마커 카운터 +1 및 draw
    [win.callOnFlip(set_trigger) 등록]  # VSync onset TTL이 필요한 프레임에만
    win.flip()                       # VSync 동기화, callOnFlip 콜백 실행
    aoi_manager.update()             # AOI 시선 이벤트 업데이트 (flip 직후)
    [win.callOnFlip(reset_trigger) 등록]  # TTL reset을 다음 flip에 예약
```

애니메이션·대기 구간도 동일한 패턴으로 처리합니다.

```python
deadline = core.getTime() + duration
while core.getTime() < deadline:
    draw_everything()
    blink_frame_marker(win)
    win.flip()                       # VSync가 16.67 ms 주기를 보장
```

이를 통해 다음 구간에서도 프레임이 끊기지 않습니다.

| 구간 | 지속 시간 |
| --- | --- |
| 카드 뒤집기 애니메이션 (사용자 / NPC) | `CARD_FLIP_DURATION` (0.5 s) |
| 피드백 표시 (성공 / 실패 / 타임아웃) | `FEEDBACK_DURATION` (0.3 s) |
| 시행 간 인터벌 | `TRIAL_INTERVAL` (0.5 s) |
| PC 생각 시간 | `PC_THINK_TIME` (1.0 s) |
| 시작 큐 ("시작!") | `START_CUE_DURATION` (0.5 s) |
| 잡기 이벤트 후 초기화 유예 | `CATCH_RESET_PREP_DURATION` (0.5 s) |
| 라운드 휴식 카운트다운 | `ROUND_BREAK_DURATION` × 1 s (10 s) |

> **VSync 타이밍**: `win.flip()`은 PsychoPy 기본 설정(`waitBlanking=True`)에서 VSync까지 블로킹합니다.
> 이미 16.67 ms 주기가 보장되므로 flip 이후 추가 `core.wait()`는 사용하지 않습니다.

---

## 데이터 출력

1. `session.json`

세션 메타데이터 및 최종 요약 (피험자 ID, 게임 모드, 하드웨어 설정, 최종 결과, 점수 요약 등)

2. `trials.csv`

시행별 상세 기록 (시도 번호, 선택 카드, 정오답, 반응 시간, 점수 등)

3. `gaze_events.csv`

EyeLink 연동 시 AOI 진입 이벤트 기록 (AOI 유형, 위치 인덱스, 체류 시간)

---

# 하드웨어 연동

# EyeLink (SR Research)

`config.py`에서 `USE_EYELINK = 1` 및 `EYELINK_IP` 설정 후 사용.

1. 보드/덱 카드 각각에 AOI가 자동 등록 2) 시선 진입 시 LabJack으로 TTL 트리거가 전송됩니다.

# LabJack T4

`config.py`에서 `USE_LABJACK = 1` 설정.  
시행 시작/종료, 닭 선택, 카드 클릭, 카드 뒤집기, 피드백, 순차 메모리 이벤트에 대응하는 TTL 코드가 전송됩니다.

## 핀 구성 (총 9라인)

| 핀 | 역할 | 설명 |
| --- | --- | --- |
| EIO0–EIO7 (8핀) | 트리거 코드 데이터 | 8비트 병렬 출력, 0–255 코드값 표현 |
| CIO0 (1핀) | Trigger latch (strobe) | Natus Quantum이 이 핀의 rising edge에서 EIO 데이터를 캡처 |

## Trigger Latch 동작 원리

EIO 8핀에 코드값을 세팅하는 것만으로는 Natus Quantum이 "언제 읽어야 하는지"를 알 수 없습니다.  
CIO0(latch) 핀의 `0→1` **rising edge**가 "지금 읽어라"는 신호 역할을 합니다.

```
매 트리거 전송 순서:
  ① EIO_STATE = code     (8비트 데이터 세팅)
  ② CIO0 = 1             (latch HIGH → Natus Quantum이 rising edge에서 EIO 캡처)
  ③ (펄스 유지)
  ④ CIO0 = 0             (latch LOW)
  ⑤ EIO_STATE = 0        (데이터 클리어)

타이밍 다이어그램:
  EIO 데이터:  0 ──[  code  ]── 0
  CIO0(latch): 0 ──[  HIGH  ]── 0
                    ↑
               rising edge에서
               Natus Quantum이 code값 캡처 → EEG 파일에 타임스탬프 기록
```

## 초기화 (`init_labjack`)

시작 시 다음 레지스터를 명시적으로 초기화합니다:

| 레지스터 | 값 | 이유 |
| --- | --- | --- |
| `EIO_DIRECTION` | 0xFF | EIO0–7 전부 출력 모드 |
| `EIO_STATE` | 0 | 초기값 LOW |
| `CIO_DIRECTION` | 0x0F | CIO0–3 출력 모드 |
| `CIO_STATE` | 0 | latch 초기값 LOW |

## 트리거 코드북

실험 중 발생하는 각 이벤트와 대응 코드입니다.  
EEG/sEEG 분석 시 이 코드북을 참조하여 타임스탬프를 이벤트로 변환합니다.

| 이벤트 | 트리거 코드 | 전송 시점 | 구현 위치 |
| --- | --- | --- | --- |
| 사용자 카드 클릭 (운동 반응) | 100 | 마우스 클릭 감지 즉시 (flip 무관) | `game_play.py` |
| 사용자 카드 뒤집기 visual onset | 101 | `win.callOnFlip` → VSync 시점 실행 | `game_play.py` |
| PC 카드 뒤집기 visual onset | 102 | `win.callOnFlip` → VSync 시점 실행 | `game_play.py` |
| 닭 선택 – chase | 110 | 버튼 클릭 감지 즉시 (flip 무관) | `token_selection.py` |
| 닭 선택 – flight | 111 | 버튼 클릭 감지 즉시 (flip 무관) | `token_selection.py` |
| 시행 시작 (사용자) | 200 | `win.callOnFlip` → VSync 시점 실행 | `game_play.py` |
| 시행 시작 (PC – think screen) | 200 | `win.callOnFlip` → VSync 시점 실행 | `game_play.py` |
| 시행 종료 | 201 | 결과 처리 직후 즉시 (flip 무관) | `game_play.py` |
| 피드백 성공 (FRN/P300 onset) | 210 | `win.callOnFlip` → VSync 시점 실행 | `feedback.py` |
| 피드백 실패 (FRN/P300 onset) | 211 | `win.callOnFlip` → VSync 시점 실행 | `feedback.py` |
| 피드백 타임아웃 | 212 | `win.callOnFlip` → VSync 시점 실행 | `feedback.py` |
| 순차 메모리 활성화 | 220 | 활성화 판정 즉시 (flip 무관) | `game_play.py` |
| 순차 메모리 스텝 성공 | 221 | (미사용, 예약) | — |
| 순차 메모리 전체 성공 | 222 | `win.callOnFlip` → VSync 시점 실행 | `feedback.py` |
| 순차 메모리 실패 | 223 | `win.callOnFlip` → VSync 시점 실행 | `feedback.py` |
| 보드/덱 카드 AOI 진입 | 10–66 | EyeLink 시선 hit 감지 직후 | `aoi_manager.py` |

## TTL 전송 방식

### callOnFlip 방식 (101, 102, 200, 210–212, 222–223)

`win.callOnFlip(set_trigger, handle, code)`를 `win.flip()` 직전에 등록합니다.
등록된 콜백은 `win.flip()` 내부의 VSync 시점에 실행됩니다.
TTL reset은 `win.flip()` 직후에 `win.callOnFlip(reset_trigger, handle)`으로 등록하여 다음 프레임의 VSync에서 실행됩니다.

```
draw_everything()
blink_frame_marker(win)
win.callOnFlip(set_trigger, handle, code)   ← 이번 VSync에 실행 예약
win.flip()           ← [VSync] → set_trigger 실행: EIO=code, CIO0=HIGH
                                → 화면에 자극 표시, 포토다이오드 ON
                                → USB 전송 ~1–4 ms → sEEG에 TTL 도달
win.callOnFlip(reset_trigger, handle)       ← 다음 VSync에 실행 예약

(다음 프레임)
win.flip()           ← [VSync] → reset_trigger 실행: CIO0=LOW, EIO=0
```

TTL 펄스 폭 ≈ 1 프레임 (~16.7 ms @ 60 Hz)

TTL과 포토다이오드 사이의 오프셋은 USB 전송 지연(~1–4 ms)에 의해 발생하며, 지터는 비교적 작고 일정합니다. 포토다이오드 타임스탬프를 기준으로 모든 시행의 onset을 일괄 보정할 수 있습니다.

### 즉시 블로킹 전송 방식 (100, 110, 111, 201, 220)

`send_trigger(handle, code)`를 호출합니다.  
EIO HIGH + CIO0 HIGH → 5 ms busy-wait → CIO0 LOW → EIO 0을 한 번에 처리합니다. 펄스 폭 = 5 ms.  
닭 선택, 카드 클릭, 시행 종료처럼 flip 타이밍과 무관한 이벤트에 사용합니다.
