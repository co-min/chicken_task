import sys
import subprocess
import os
import shutil

VENV_DIR = "chicken_env"
REQUIREMENTS_FILE = "requirements.txt"
EYETRACKER_WHL_PATH =  os.path.join("eye_func", "psychopy_eyetracker_sr_research-0.0.5-py3-none-any.whl")
PYTHON_REQUIRED = (3, 10)

def find_python310():
    """Find Python 3.10 executable path on Windows"""
    candidates = [
        r"C:\Python310\python.exe",
        os.path.join(os.environ.get("LOCALAPPDATA", ""), r"Programs\Python\Python310\python.exe"),
        os.path.join(os.environ.get("PROGRAMFILES", ""), r"Python310\python.exe"),
        os.path.join(os.environ.get("PROGRAMFILES(X86)", ""), r"Python310\python.exe"),
    ]
    
    # Look for Python from PATH
    try:
        output = subprocess.check_output("where python", shell=True, text=True)
        for line in output.splitlines():
            candidates.append(line.strip())
    except subprocess.CalledProcessError:
        pass

    for path in candidates:
        if os.path.exists(path):
            try:
                ver_output = subprocess.check_output([path, "--version"], text=True).strip()
                if f"Python {PYTHON_REQUIRED[0]}.{PYTHON_REQUIRED[1]}" in ver_output:
                    return path
            except Exception:
                continue

    # Ask user manually if not found
    while True:
        user_input = input("Please enter the path to Python 3.10: ").strip('"')
        if os.path.exists(user_input):
            try:
                ver_output = subprocess.check_output([user_input, "--version"], text=True).strip()
                if f"Python {PYTHON_REQUIRED[0]}.{PYTHON_REQUIRED[1]}" in ver_output:
                    return user_input
            except Exception:
                pass
        print("Invalid Python 3.10 path. Please try again.")

def create_virtualenv(python_exe):
    """Create virtual environment with the specified python executable"""
    if os.path.exists(VENV_DIR):
        print(f"[INFO] Virtual environment '{VENV_DIR}' already exists. Removing and recreating it.")
        shutil.rmtree(VENV_DIR)
    print(f"[INFO] Creating Python 3.10 virtual environment... ({VENV_DIR})")
    subprocess.check_call([python_exe, "-m", "venv", VENV_DIR])

def install_requirements():
    """Install packages into the virtual environment"""
    pip_path = os.path.join(VENV_DIR, "Scripts", "pip.exe") if os.name == "nt" else os.path.join(VENV_DIR, "bin", "pip")
    python_path = os.path.join(VENV_DIR, "Scripts", "python.exe") if os.name == "nt" else os.path.join(VENV_DIR, "bin", "python")
    
    print("[INFO] Upgrading pip...")
    subprocess.check_call([python_path, "-m", "pip", "install", "--upgrade", "pip"])

    if os.path.exists(REQUIREMENTS_FILE):
        print(f"[INFO] Installing packages from {REQUIREMENTS_FILE}...")
        subprocess.check_call([pip_path, "install", "-r", REQUIREMENTS_FILE])
    else:
        print(f"[WARNING] {REQUIREMENTS_FILE} not found. Skipping package installation.")

    # Install EyeLink PsychoPy extension (.whl)
    if os.path.exists(EYETRACKER_WHL_PATH):
        print(f"[INFO] Installing EyeLink PsychoPy extension ({EYETRACKER_WHL_PATH})...")
        subprocess.check_call([pip_path, "install", EYETRACKER_WHL_PATH])
    else:
        print(f"[WARNING] EyeLink wheel file not found: {EYETRACKER_WHL_PATH}. Skipping installation.")

if __name__ == "__main__":
    python310_exe = find_python310()
    print(f"[INFO] Python 3.10 executable found: {python310_exe}")

    create_virtualenv(python310_exe)
    install_requirements()
    
    print("\n" + "="*60)
    print("[OK] Environment setup complete!")
    print("="*60)
    print(f"\nTo activate the virtual environment, run:")
    if os.name == "nt":
        print(f"  {VENV_DIR}\\Scripts\\activate")
    else:
        print(f"  source {VENV_DIR}/bin/activate")
    print(f"\nThen run the game:")
    print(f"  python main.py")
    print("="*60)