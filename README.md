# Chicken Task - Working Memory & Decision Making Experiment

## 개요

변형된 치킨차차 게임을 기반으로 한 인지 실험 과제입니다. Working memory(작업 기억)와 decision making(의사 결정)을 측정합니다.

## 게임 규칙

### 1. 게임 준비

#### 보드 구성

- **운동장 조건 카드 (왼쪽)**: 3행 × 9열 (27장)
  - 각 카드는 단일 조건 1개 표시 (색상/모양/숫자)
  - 9가지 조건 × 3회 반복 = 27장
  - 항상 앞면 보임
- **메인 카드 덱 (오른쪽)**: 3행 × 9열 (27장)
  - 각 카드는 3가지 속성 조합 (색상 + 모양 + 숫자)
  - 예: "빨간색 사각형 2개", "파란색 삼각형 1개"
  - 뒷면으로 시작 (클릭 시 5초간 앞면 노출)

#### 토큰 배치

- 🐔 **chase** (1행 1열): 문어를 쫓는 공격형 닭
- 🐙 **문어** (2행 1열): PC 컨트롤
- 🐔 **flight** (3행 1열): 문어로부터 도망치는 방어형 닭

#### 이동 경로 (순환)

```
1-1 → 1-2 → ... → 1-9 →
2-1 → 2-2 → ... → 2-9 →
3-1 → 3-2 → ... → 3-9 →
1-1 (처음으로)
```

---

### 2. 턴 진행

#### 사용자 턴

**Phase 0: 닭 선택** (제한시간 없음)

- ⬆️ up 키: chase 선택
- ⬇️ down 키: flight 선택
- ⏎ enter: 확정 → 15초 타이머 시작

**Phase 1+: 게임 플레이** (⏰ 15초)

1. 선택된 닭의 다음 칸 민트색 강조
2. 메인 카드 1장 클릭
3. 5초간 앞면 노출 → 자동 뒷면 복구
4. 조건 매칭 판정:
   - ✅ 성공: 닭 이동 + 15초 리셋 + 반복
   - ❌ 실패: 턴 종료 → PC 차례
5. 15초 초과 시 자동 턴 종료

#### PC 턴

- 문어 자동 이동
- 60% 확률로 정답 선택
- 사용자도 PC 선택 관찰 가능

---

### 3. 승리/패배 조건

**🏆 승리**: chase가 문어를 잡기

- chase가 문어 바로 뒤에 위치
- 문어의 다음 칸 조건 맞추면 승리

**💀 패배**: 문어가 flight를 잡기

- 문어가 flight 바로 뒤에 위치
- PC가 flight의 다음 칸 조건 맞추면 패배

---

### 4. 조건 매칭 예시

```
운동장 조건: "빨강" + 메인: "빨간색 △ 2개" → ✅ 성공
운동장 조건: "△" + 메인: "파란색 △ 1개" → ✅ 성공
운동장 조건: "3개" + 메인: "초록색 □ 2개" → ❌ 실패
```

---

## 설치 방법

### 1. Python 3.10 설치

Windows에서 Python 3.10을 설치하세요.

### 2. 가상환경 설정 및 패키지 설치

```bash
python set_up.py
```

또는 수동 설치:

```bash
python -m venv psychopy_env
psychopy_env\Scripts\activate
pip install -r requirements.txt
```

---

## 실행 방법

### 1. 가상환경 활성화

```bash
psychopy_env\Scripts\activate
```

### 2. 게임 실행

```bash
python main.py
```

---

## 프로젝트 구조

```
chicken_task_first/
├── Data/                     # 실험 데이터
├── game_func/                # 게임 로직
│   ├── board_class.py       # 운동장 카드 보드
│   ├── deck_class.py        # 메인 카드 덱
│   ├── token_class.py       # 토큰 관리
│   ├── game_state.py        # 게임 상태
│   └── pc_ai.py             # PC 알고리즘
├── phase_func/               # 실험 단계
│   ├── starting.py          # 시작 화면
│   ├── token_selection.py   # 닭 선택
│   ├── game_play.py         # 게임 플레이
│   └── ending.py            # 종료 화면
├── view_func/                # 렌더링
│   ├── board_renderer.py    # 보드 그리기
│   ├── deck_renderer.py     # 덱 그리기
│   └── token_renderer.py    # 토큰 표시
├── save_func/                # 데이터 저장
├── set_opts/                 # 옵션 설정
├── utils/                    # 유틸리티
├── stimuli/                  # 이미지 리소스
├── config.py                 # 설정
├── initiate.py               # 초기화
└── main.py                   # 메인
```

---

## 측정 변수

### Working Memory

- 메인 카드 27장의 위치와 조합 기억
- 5초 단기 노출 → 장기 기억 전환

### Decision Making

- 매 턴 chase(공격) vs flight(방어) 전략 선택
- 상황 판단 및 리스크 관리

---

## 키 컨트롤

- ⬆️ **up**: chase 선택
- ⬇️ **down**: flight 선택
- ⏎ **enter**: 선택 확정
- 🖱️ **마우스 클릭**: 메인 카드 선택
- **ESC**: 게임 종료

---

## 개발 정보

- **Python**: 3.10
- **PsychoPy**: 2023.2.3
- **개발 기간**: 2026.03
- **연구 목적**: Working memory & Decision making

---

## 라이선스

연구 목적으로만 사용 가능합니다.
