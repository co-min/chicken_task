# Chicken Task 게임 실행 가이드

## 실행 방법

### 1. 가상환경 활성화

```powershell
.\chicken_env\Scripts\Activate.ps1
```

또는 cmd에서:

```cmd
.\chicken_env\Scripts\activate.bat
```

### 2. 게임 실행

```powershell
python main.py
```

## 게임 조작법

### Phase 0: 닭 선택

- **↑ (위쪽 화살표)**: Chase 선택 (문어를 쫓는 닭)
- **↓ (아래쪽 화살표)**: Flight 선택 (문어로부터 도망치는 닭)
- **Enter**: 선택 확정 및 게임 시작

### Phase 1+: 게임 플레이

- **마우스 클릭**: 메인 덱에서 카드 선택
- **ESC**: 게임 종료

## 게임 규칙

1. **목표**:
   - Chase로 Octopus를 잡으면 승리
   - Octopus가 Flight를 잡으면 패배

2. **턴 시스템**:
   - 사용자 턴: 닭 선택 → 조건에 맞는 카드 클릭
   - PC 턴: AI가 자동으로 Octopus 이동 (60% 정답률)

3. **타이머**: 각 카드 선택마다 15초 제한
   - 성공 시: 타이머 리셋, 같은 닭으로 계속 진행
   - 실패 시: 턴 종료, 상대방 턴으로 전환

4. **카드 매칭**:
   - 색상(빨강/파랑/초록), 모양(사각형/삼각형/원), 숫자(1/2/3) 조합
   - 타겟 조건에 정확히 맞는 카드를 선택해야 함

## 문제 해결

### ImportError: psychopy 모듈을 찾을 수 없음

```powershell
pip install psychopy
```

### 이미지 파일을 찾을 수 없음

- `stimuli/` 폴더에 다음 이미지들이 있는지 확인:
  - `condition_cards/`: 조건 카드 이미지
  - `main_cards/`: 메인 덱 카드 이미지
  - `tokens/`: 토큰 이미지 (chase.png, octopus.png, flight.png)
  - `ui/`: UI 요소 (card_back.png)

### 화면이 너무 크거나 작음

`config.py`에서 다음 설정 조정:

```python
WIDTH = 1100
HEIGHT = 1080
FULLSCREEN = False  # 전체화면 비활성화
```

## 디버그 모드

`config.py`에서 디버그 설정 변경:

```python
DEBUG_MODE = True  # 디버그 정보 표시
SHOW_TIMER = True  # 타이머 표시
```

## 데이터 저장

게임 종료 후 `game_state.trial_history`에 모든 시행 데이터가 저장됩니다:

- 턴 번호
- 선택한 토큰
- 타겟 조건 및 위치
- 선택한 카드 및 위치
- 매칭 성공/실패
- 경과 시간
