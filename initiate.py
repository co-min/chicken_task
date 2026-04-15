# initiate.py
# Chicken Task - Initialization functions

import os
import sys
import platform
from datetime import datetime

from set_opts.set_device_opt import set_device_opt
from set_opts.set_visual_opt import set_visual_opt
from set_opts.set_game_opt import set_game_opt
from config import USE_EYELINK, USE_LABJACK, EYELINK_IP

if USE_EYELINK:
    from set_opts.set_eyelink import set_eye_opt
    import pylink
    from eye_func.EyeLinkCoreGraphicsPsychoPy import EyeLinkCoreGraphicsPsychoPy

if USE_LABJACK:
    from utils.labjack_triggers import init_labjack, close_labjack

def define_save_directory(base_dir, subject_id):
    """
    Define and create save directory for the subject
    
    Args:
        base_dir (str): Base directory path
        subject_id (str): Subject ID
        
    Returns:
        str: Save directory path
    """
    save_dir = os.path.join(base_dir, 'Data', subject_id)
    os.makedirs(save_dir, exist_ok=True)
    print(f"Save directory: {save_dir}")
    return save_dir

def initiate():
    """
    Initialize Chicken Task environment
    
    Returns:
        tuple: (visual_opt, device_opt, game_opt, save_directory)
    """
    print("=" * 60)
    print("Chicken Task - Working Memory & Decision Making")
    print("=" * 60)
    print()
    
    # Get current folder
    current_folder = os.path.dirname(os.path.abspath(__file__))
    print(f"Current folder: {current_folder}")
    
    # Detect OS
    os_name = platform.system()
    if os_name == 'Darwin':  # macOS
        print("Running on macOS")
        username = os.getenv('USER')
    elif os_name == 'Windows':
        print("Running on Windows")
        username = os.getenv('USERNAME')
    else:
        print("Running on unknown OS")
        username = "UNKNOWN"
    
    print(f"User: {username}")
    print()
    
    # Get subject ID
    while True:
        subject_id = input("Enter subject ID: ").strip()
        if subject_id:
            break
        print("Subject ID cannot be empty. Please try again.")
    
    print(f"Subject ID: {subject_id}")
    print()
    
    # Define save directory
    save_directory = define_save_directory(current_folder, subject_id)
    
    # Set options
    print("Loading options...")
    visual_opt = set_visual_opt()
    device_opt = set_device_opt()
    game_opt = set_game_opt()
    
    print(f"Visual options loaded: {visual_opt['win_size']}")
    print(f"Device options loaded: Mouse={device_opt.get('use_mouse', True)}")
    print(f"Game options loaded: PC success rate={game_opt.get('pc_success_rate', 0.6)}")
    print()
    
    print("[OK] Initialization complete!")
    print("=" * 60)
    print()
    
    return visual_opt, device_opt, game_opt, save_directory

def initiate_eyelink(win, save_directory, edf_name="test.edf"):
    """
    Initialize EyeLink connection and calibration.

    Args:
        win: PsychoPy window object
        save_directory (str): Directory to save EDF files
        edf_name (str, optional): Name of EDF file. Default is "test.edf".

    Returns:
        el_tracker: pylink.EyeLink object if connected, otherwise None
    """
    print("Checking for EyeLink tracker connection...")

    try:
        # Try to connect to EyeLink
        if USE_EYELINK == 0:
            el_tracker = None  # Skip connection when disabled
        else:
            el_tracker = pylink.EyeLink(EYELINK_IP)
    except (RuntimeError, ModuleNotFoundError):
        print("⚠ EyeLink tracker not detected. EyeLink functionality will be disabled.")
        return None

    print("EyeLink tracker detected. Initializing...")

    os.makedirs(save_directory, exist_ok=True)

    edf_name = "test.edf"

    # EyeLink configuration
    if el_tracker:
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

        # Send screen resolution info from PsychoPy window
        scn_width, scn_height = win.size

        el_tracker.sendCommand(f"screen_pixel_coords = 0 0 {scn_width-1} {scn_height-1}")
        el_tracker.sendMessage(f"DISPLAY_COORDS 0 0 {scn_width-1} {scn_height-1}")

        # === Calibration (safe for multi-monitor setups) ===
        try:
            print("Starting EyeLink calibration on monitor...")
            
            print(el_tracker.isConnected())
            genv = EyeLinkCoreGraphicsPsychoPy(el_tracker, win)
            print(genv)
            pylink.openGraphicsEx(genv)
            print("Calibration in progress...")

            el_tracker.doTrackerSetup()  # Defaults to primary monitor if None
            print("Calibration complete.")
        except Exception as e:
            print(f"⚠ EyeLink calibration skipped: {e}")
        
    else:
        print("EyeLink not detected.")

    return el_tracker


def initiate_labjack():
    """
    LabJack T4에 연결하고 핸들을 반환합니다.
    USE_LABJACK=0 이거나 연결 실패 시 None을 반환합니다.

    Returns
    -------
    int | None
        LabJack 핸들 (ljm.openS 반환값), 또는 None
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

