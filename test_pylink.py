import pylink
from psychopy import visual, core, event, gui
import os
import sys
from config import EYELINK_IP

# --- 1. 실험 설정 및 더미 모드 여부 결정 ---
exp_info = {'dummy_mode': False}
dlg = gui.DlgFromDict(dictionary=exp_info, title='EyeLink Test')
if not dlg.OK:
    core.quit()
dummy_mode = exp_info['dummy_mode']
edf_fname = "TEST.EDF"  # EDF 파일명은 8자 이내(확장자 제외)

# --- 2. EyeLink 연결 설정 ---
try:
    if not dummy_mode:
        tk = pylink.EyeLink(EYELINK_IP)
    else:
        tk = pylink.EyeLink(None)
except AttributeError:
    print("\n[오류] 'pylink' 모듈에서 'EyeLink' 속성을 찾을 수 없습니다.")
    print("이 오류는 SR-Research의 공식 EyeLink 라이브러리가 아닌 다른 라이브러리가 설치되었을 때 발생합니다.")
    print("\n[해결 방법]")
    print("1. 현재 가상환경에서 잘못 설치된 'pylink'를 제거하세요: pip uninstall pylink")
    print("2. SR-Research 지원 사이트에서 EyeLink Developer's Kit를 다운로드하여, 그 안에 포함된 'pylink' 폴더를 가상환경의 site-packages에 복사하세요.")
    core.quit()
    sys.exit()
except RuntimeError as e:
    print(f"EyeLink 연결 실패: {e}")
    core.quit()
    sys.exit()

# --- 3. PsychoPy 윈도우 설정 ---
# EyeLink는 픽셀 단위를 기본으로 사용하므로 'pix' 권장. 두 번째 모니터(인덱스 1)에 표시
win = visual.Window([1024, 768], fullscr=False, screen=2, monitor='testMonitor', units='pix')

# --- 4. EyeLink 그래픽 및 보정 설정 ---
# PsychoPy 화면에 보정 타겟을 그리기 위한 설정
from eye_func.EyeLinkCoreGraphicsPsychoPy import EyeLinkCoreGraphicsPsychoPy
genv = EyeLinkCoreGraphicsPsychoPy(tk, win)
pylink.openGraphicsEx(genv)

# 데이터 파일 오픈 (최대 8글자)
tk.openDataFile(edf_fname)

# --- 5. 보정(Calibration) 실행 ---
# 실행 후 Enter를 눌러 보정 화면으로 진입, 마우스(더미)나 시선으로 타겟 클릭
tk.doTrackerSetup()

# --- 6. 실험 루틴 시작 ---
# 기록 시작 (샘플 데이터와 이벤트 데이터 모두 기록)
tk.startRecording(1, 1, 1, 1)
pylink.pumpDelay(100) # 안정화를 위한 짧은 대기

# 자극 준비 (고정된 타겟과 시선 커서)
target = visual.Circle(win, radius=20, lineColor='white', fillColor='red', units='pix')
gaze_cursor = visual.Circle(win, radius=10, fillColor='blue', units='pix')
msg = visual.TextStim(win, text="시선으로 파란 점을 움직여 보세요. (종료: ESC)", pos=(0, 200))

# 10초간 시선 추적 테스트 루프
trial_timer = core.CountdownTimer(10)
tk.sendMessage("TRIAL_START") # EDF 파일에 마커 기록

while trial_timer.getTime() > 0:
    # ESC 누르면 종료
    if 'escape' in event.getKeys():
        tk.sendMessage("TRIAL_SKIPPED")
        break

    # 실시간 시선 좌표 가져오기
    dt = tk.getNewestSample()
    if dt is not None:
        gaze_pos = dt.getGaze() # (x, y) 튜플 또는 (pylink.MISSING_DATA, pylink.MISSING_DATA)
        # 유효한 좌표인지 확인
        if gaze_pos[0] != pylink.MISSING_DATA and gaze_pos[1] != pylink.MISSING_DATA:
            # EyeLink(좌상단 0,0) -> PsychoPy(중앙 0,0) 좌표 변환
            draw_x = gaze_pos[0] - (win.size[0] / 2)
            draw_y = (win.size[1] / 2) - gaze_pos[1]
            gaze_cursor.pos = (draw_x, draw_y)
    
    msg.draw()
    target.draw()
    gaze_cursor.draw()
    win.flip()

tk.sendMessage("TRIAL_END")

# --- 7. 종료 및 파일 전송 ---
tk.stopRecording()

if tk.isConnected() and not dummy_mode:
    tk.closeDataFile()
    # 데이터 저장 폴더 생성
    data_path = os.path.join(os.path.dirname(__file__), 'Data')
    os.makedirs(data_path, exist_ok=True)
    dest_fname = os.path.join(data_path, edf_fname)
    
    print(f"EDF 파일 수신 중... -> {dest_fname}")
    try:
        tk.receiveDataFile(edf_fname, dest_fname)
        print("파일 수신 완료.")
    except RuntimeError as e:
        print(f"파일 수신 실패: {e}")

tk.close()
win.close()
core.quit()