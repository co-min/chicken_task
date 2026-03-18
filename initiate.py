# initiate.py
# Chicken Task - Initialization functions

import os
import sys
import platform
from datetime import datetime

from .set_opts.set_device_opt import set_device_opt
from .set_opts.set_visual_opt import set_visual_opt
from .set_opts.set_game_opt import set_game_opt
from .config import USE_EYELINK

if USE_EYELINK:
    from .set_opts.set_eyelink import set_eye_opt
    import pylink
    from .eye_func.EyeLinkCoreGraphicsPsychoPy import EyeLinkCoreGraphicsPsychoPy

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

def initiate_eyelink(win, subject_id, save_dir=None):
    """
    Initialize EyeLink eye tracker (optional)
    
    Args:
        win: PsychoPy window
        subject_id (str): Subject ID
        save_dir (str, optional): Local directory for EDF download target
        
    Returns:
        tuple: (tracker, genv) or (None, None) if not used
    """
    if not USE_EYELINK:
        return None, None
    
    print("Initializing EyeLink...")
    
    try:
        # Connect to EyeLink
        tracker = pylink.EyeLink("100.1.1.1")

        # EyeLink host EDF name
        edf_fname = subject_id[:8] + ".edf"

        # If not provided, keep EDF output under project Data/<subject_id>
        if save_dir is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            save_dir = define_save_directory(base_dir, subject_id)

        # set_eyelink.py에서 set_eye_opt 호출 -> 설정 및 보정 처리
        # Configure tracker, open EDF, and run calibration in one place
        tracker = set_eye_opt(tracker, save_dir=save_dir, edf_name=edf_fname, win=win)
        if tracker is None:
            raise RuntimeError("EyeLink setup failed")
        
        # Set up graphics environment
        genv = EyeLinkCoreGraphicsPsychoPy(tracker, win)
        pylink.openGraphicsEx(genv)
        
        print("[OK] EyeLink initialized successfully")
        return tracker, genv
        
    except Exception as e:
        print(f"[ERROR] EyeLink initialization failed: {e}")
        print("Continuing without eye tracking...")
        return None, None

if __name__ == "__main__":
    # Test initialization
    visual_opt, device_opt, game_opt, save_dir = initiate()
    print("\nTest complete!")
    print(f"Save directory: {save_dir}")
