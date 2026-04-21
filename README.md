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

- 난이도 자동 스케일: 덱 열 수 및 배치 방식(factorization/random) 6단계 선형 진행

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
│   └── frame_marker.py       # 프레임 마커 (EEG 동기화용)
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

| 항목 변수 | 기본값 |
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
  ③ 5ms 대기
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
| `EIO_INHIBIT` | 0 | EIO 출력 활성화 (기본값이지만 명시적 설정) |
| `EIO_DIRECTION` | 0xFF | EIO0–7 전부 출력 모드 |
| `EIO_STATE` | 0 | 초기값 LOW |
| `CIO_INHIBIT` | 0 | CIO 출력 활성화 |
| `CIO_DIRECTION` | 0x0F | CIO0–3 출력 모드 |
| `CIO_STATE` | 0 | latch 초기값 LOW |

## 트리거 코드북

실험 중 발생하는 각 이벤트와 대응 코드입니다.  
EEG 분석 시 이 코드북을 참조하여 타임스탬프를 이벤트로 변환합니다.

| 이벤트                       | 트리거 코드 | 전송 시점                        | 구현 위치                |
| ---------------------------- | ----------- | -------------------------------- | ------------------------ |
| 사용자 카드 클릭 (운동 반응) | 100         | 마우스 클릭 감지 즉시 (flip 전)  | `game_play.py`           |
| 사용자 카드 뒤집기 visual onset | 101      | `win.flip()` 반환 직후           | `game_play.py`           |
| PC 카드 뒤집기 visual onset  | 102         | `win.flip()` 반환 직후           | `game_play.py`           |
| 닭 선택 – chase              | 110         | 버튼 클릭 감지 즉시              | `token_selection.py`     |
| 닭 선택 – flight             | 111         | 버튼 클릭 감지 즉시              | `token_selection.py`     |
| 시행 시작                    | 200         | `win.flip()` VSync 시점 (callOnFlip) | `game_play.py`       |
| 시행 종료                    | 201         | 결과 처리 직후 즉시              | `game_play.py`           |
| 피드백 성공 (FRN/P300 onset) | 210         | `win.flip()` VSync 시점 (callOnFlip) | `feedback.py`        |
| 피드백 실패 (FRN/P300 onset) | 211         | `win.flip()` VSync 시점 (callOnFlip) | `feedback.py`        |
| 피드백 타임아웃              | 212         | `win.flip()` VSync 시점 (callOnFlip) | `feedback.py`        |
| 순차 메모리 활성화           | 220         | 활성화 판정 즉시                 | `game_play.py`           |
| 순차 메모리 스텝 성공        | 221         | (미사용, 예약)                   | —                        |
| 순차 메모리 전체 성공        | 222         | `win.flip()` VSync 시점 (callOnFlip) | `feedback.py`        |
| 순차 메모리 실패             | 223         | `win.flip()` VSync 시점 (callOnFlip) | `feedback.py`        |
| 보드/덱 카드 AOI 진입        | 10–66       | EyeLink 시선 hit 감지 직후       | `aoi_manager.py`         |

## TTL 전송 방식

**callOnFlip 방식** (200, 210–212, 220–223)  
PsychoPy `win.callOnFlip(send_trigger_async, ...)` 으로 VSync 직후 EIO + CIO0(latch)를 HIGH로 설정하고, `_deferred_lj_reset()` 으로 5ms 후 CIO0 LOW → EIO 0 순으로 리셋합니다. 화면 갱신과 정확히 동기화해야 하는 이벤트에 사용합니다.

**post-VSync 즉시 전송 방식** (101, 102)  
`win.flip()` 반환 직후 `send_trigger_async()` 를 호출합니다. `callOnFlip` 큐에 TRIAL_START(200)가 이미 등록되어 있을 수 있어 충돌을 피하기 위해 이 방식을 사용합니다.

**즉시 블로킹 전송 방식** (100, 110, 111)  
`send_trigger()` 로 EIO HIGH + CIO0 HIGH → 5ms busy-wait → CIO0 LOW → EIO 0 을 한 번에 처리합니다. 닭 선택이나 카드 클릭처럼 flip 타이밍과 무관한 운동/의사결정 반응 onset에 사용합니다.
