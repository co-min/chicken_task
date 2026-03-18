import os


def set_eye_opt(el_tracker, save_dir, edf_name="test.edf", win=None):
    if el_tracker is None: # tracker가 없으면 종료
        print("⚠ EyeLink tracker not connected. Calibration skipped.")
        return None

    # save_dir 존재하도록 설정
    os.makedirs(save_dir, exist_ok=True)

    # EDF file setting
    try:
        el_tracker.openDataFile(edf_name)
        el_tracker.sendCommand("file_event_filter = LEFT,RIGHT,FIXATION,SACCADE,BLINK,MESSAGE,BUTTON")
        el_tracker.sendCommand("file_sample_data  = LEFT,RIGHT,GAZE,AREA,GAZERES,STATUS")
    except Exception as exc:
        print(f"⚠ EyeLink file setup failed: {exc}")
        return None

    if win:
        scn_width, scn_height = win.size
    else:
        scn_width, scn_height = (1920, 1080)

    # tracker에 표시 좌표 전달: screen_pixel_coords와 DISPLAY_COORDS 동기화
    try:
        el_tracker.sendCommand(f"screen_pixel_coords = 0 0 {scn_width-1} {scn_height-1}")
        el_tracker.sendMessage(f"DISPLAY_COORDS 0 0 {scn_width-1} {scn_height-1}")
    except Exception as exc:
        print(f"⚠ EyeLink display coordinate setup failed: {exc}")
        return None

    # Calibration 
    try:
        el_tracker.doTrackerSetup()
    except Exception as exc:
        print(f"⚠ EyeLink calibration skipped: {exc}")
        return None

    # 로컬 대상 경로 안내: 이후 receiveDataFile 시 사용할 경로를 로그로 확인 가능
    local_edf_path = os.path.join(save_dir, os.path.basename(edf_name))
    print(f"EyeLink EDF host file: {edf_name}")
    print(f"EyeLink EDF local target: {local_edf_path}")

    return el_tracker