import os

from config import USE_EYELINK, USE_LABJACK, EYELINK_IP

if USE_EYELINK:
    import pylink
    from eye_func.EyeLinkCoreGraphicsPsychoPy import EyeLinkCoreGraphicsPsychoPy

if USE_LABJACK:
    from utils.labjack_triggers import init_labjack


def initiate_eyelink(win, save_directory):
    """
    EyeLink 연결 및 캘리브레이션 초기화.

    Returns:
        el_tracker: pylink.EyeLink 객체, 또는 None
    """
    print("Checking for EyeLink tracker connection...")

    try:
        if USE_EYELINK == 0:
            return None
        el_tracker = pylink.EyeLink(EYELINK_IP)
    except (RuntimeError, ModuleNotFoundError):
        print("⚠ EyeLink tracker not detected. EyeLink functionality will be disabled.")
        return None

    print("EyeLink tracker detected. Initializing...")
    os.makedirs(save_directory, exist_ok=True)

    edf_name = "test.edf"
    try:
        el_tracker.openDataFile(edf_name)
    except RuntimeError as err:
        print("ERROR: ", err)
        if el_tracker.isConnected():
            el_tracker.close()

    preamble_text = "RECORDED BY %s" % os.path.basename(__file__)
    el_tracker.sendCommand("add_file_preamble_text '%s'" % preamble_text)
    el_tracker.setOfflineMode()

    vstr = el_tracker.getTrackerVersionString()
    eyelink_ver = int(vstr.split()[-1].split('.')[0])
    print("Running experiment on %s, version %d" % (vstr, eyelink_ver))

    el_tracker.sendCommand("file_event_filter = LEFT,RIGHT,FIXATION,SACCADE,BLINK,MESSAGE,BUTTON")
    el_tracker.sendCommand("file_sample_data  = LEFT,RIGHT,GAZE,AREA,GAZERES,STATUS")

    scn_width, scn_height = win.size
    el_tracker.sendCommand(f"screen_pixel_coords = 0 0 {scn_width-1} {scn_height-1}")
    el_tracker.sendMessage(f"DISPLAY_COORDS 0 0 {scn_width-1} {scn_height-1}")

    try:
        print("Starting EyeLink calibration on monitor...")
        genv = EyeLinkCoreGraphicsPsychoPy(el_tracker, win)
        pylink.openGraphicsEx(genv)
        print("Calibration in progress...")
        el_tracker.doTrackerSetup()
        print("Calibration complete.")
    except Exception as e:
        print(f"⚠ EyeLink calibration skipped: {e}")

    return el_tracker


def initiate_labjack():
    """
    LabJack T4에 연결하고 핸들을 반환합니다.
    USE_LABJACK=0 이거나 연결 실패 시 None을 반환합니다.
    """
    if not USE_LABJACK:
        return None

    print("LabJack T4 연결 시도...")
    handle = init_labjack()
    if handle is None:
        print("⚠ LabJack T4 연결 실패. 트리거가 비활성화됩니다.")
    else:
        print("[OK] LabJack T4 연결 완료")
    return handle
