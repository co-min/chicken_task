import sys
import subprocess
import os
import shutil

VENV_DIR = "chicken_env"
REQUIREMENTS_FILE = "requirements.txt"
PYTHON_MIN_VERSION = (3, 11)  # 최소 버전
PYTHON_MAX_VERSION = (3, 11)  # 최대 버전 (psychopy는 아직 3.12+ 지원 안함)
PYTHON_PREFERRED_VERSION = (3, 11)  # 권장 버전

def find_python():
    """Find Python 3.11 executable path on Windows"""
    # Python 3.11 경로
    candidates = [
        r"C:\Python311\python.exe",
        os.path.join(os.environ.get("LOCALAPPDATA", ""), r"Programs\Python\Python311\python.exe"),
        os.path.join(os.environ.get("PROGRAMFILES", ""), r"Python311\python.exe"),
    ]
    
    # Look for Python from PATH
    try:
        output = subprocess.check_output("where python", shell=True, text=True)
        for line in output.splitlines():
            candidates.append(line.strip())
    except subprocess.CalledProcessError:
        pass

    # 버전 체크 함수
    def check_python_version(path):
        try:
            ver_output = subprocess.check_output([path, "--version"], text=True).strip()
            # Extract version (e.g., "Python 3.11.5" -> (3, 11, 5))
            version_str = ver_output.split()[1]
            major, minor = map(int, version_str.split('.')[:2])
            version = (major, minor)
            # Check if version is in acceptable range
            if version >= PYTHON_MIN_VERSION and version <= PYTHON_MAX_VERSION:
                return version, ver_output
            return None, ver_output
        except Exception:
            return None, None
    
    # 후보 경로에서 찾기 (3.11+ 우선)
    best_python = None
    best_version = None
    
    for path in candidates:
        if os.path.exists(path):
            version, ver_output = check_python_version(path)
            if version:
                # 3.11+ 발견 시 즉시 반환
                if version >= PYTHON_PREFERRED_VERSION:
                    print(f"[OK] Python {version[0]}.{version[1]} 발견")
                    return path
                # 첫 번째 유효한 버전 저장
                if not best_python:
                    best_python = path
                    best_version = version
    
    # 3.11 발견된 경우
    if best_python:
        print(f"[OK] Python {best_version[0]}.{best_version[1]} 발견")
        use_it = input("이 버전을 사용하시겠습니까? (y/n): ").strip().lower()
        if use_it == 'y':
            return best_python

    # Ask user manually if not found
    print(f"\nPython 3.11을 찾을 수 없습니다.")
    while True:
        user_input = input("Python 3.11 경로를 입력하세요: ").strip('"')
        if os.path.exists(user_input):
            version, ver_output = check_python_version(user_input)
            if version:
                print(f"[OK] {ver_output}")
                return user_input
            else:
                print(f"[ERROR] Python 3.11 버전이 필요합니다. 현재: {ver_output if ver_output else '알 수 없음'}")
        else:
            print("[ERROR] 파일을 찾을 수 없습니다. 다시 시도하세요.")

def create_virtualenv(python_exe):
    """Create virtual environment with the specified python executable"""
    print(f"\n가상환경 생성 중: {VENV_DIR}")
    
    # Verify Python version before creating venv
    ver_output = subprocess.check_output([python_exe, "--version"], text=True).strip()
    print(f"사용할 Python: {ver_output}")
    
    # Remove existing venv if exists
    if os.path.exists(VENV_DIR):
        print(f"기존 가상환경 제거 중...")
        shutil.rmtree(VENV_DIR)
    
    # Create new venv
    subprocess.check_call([python_exe, "-m", "venv", VENV_DIR])
    print(f"[OK] 가상환경 생성 완료: {VENV_DIR}")

def get_venv_python():
    """Get the python executable path in the virtual environment"""
    if sys.platform == "win32":
        return os.path.join(VENV_DIR, "Scripts", "python.exe")
    else:
        return os.path.join(VENV_DIR, "bin", "python")

def install_requirements():
    print(f"\n필수 패키지 설치 중: {REQUIREMENTS_FILE}")
    venv_python = get_venv_python()
    
    if not os.path.exists(venv_python):
        print(f"[ERROR] 가상환경 Python을 찾을 수 없습니다: {venv_python}")
        return False
    
    # Upgrade pip, setuptools, and wheel first
    print("pip, setuptools, wheel 업그레이드 중...")
    subprocess.check_call([venv_python, "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"])
    
    # Install requirements
    if os.path.exists(REQUIREMENTS_FILE):
        print("패키지 설치 중...")
        subprocess.check_call([venv_python, "-m", "pip", "install", "-r", REQUIREMENTS_FILE])
        print(f"[OK] 패키지 설치 완료")
        return True
    else:
        print(f"[ERROR] {REQUIREMENTS_FILE} 파일을 찾을 수 없습니다.")
        return False

def verify_installation():
    """Verify that PsychoPy is installed correctly"""
    print("\n설치 검증 중...")
    venv_python = get_venv_python()
    
    try:
        result = subprocess.check_output(
            [venv_python, "-c", "import psychopy; print(psychopy.__version__)"],
            text=True
        ).strip()
        print(f"[OK] PsychoPy 버전: {result}")
        return True
    except Exception as e:
        print(f"[ERROR] PsychoPy 검증 실패: {e}")
        return False

def main():
    # Step 1: Find Python 3.11
    print("\n[1/4] Python 3.11 찾는 중...")
    python_exe = find_python()
    print(f"[OK] Python 발견: {python_exe}")
    
    # Step 2: Create virtual environment
    print("\n[2/4] 가상환경 생성 중...")
    try:
        create_virtualenv(python_exe)
    except Exception as e:
        print(f"[ERROR] 가상환경 생성 실패: {e}")
        return
    
    # Step 3: Install requirements
    print("\n[3/4] 패키지 설치 중...")
    try:
        if not install_requirements():
            return
    except Exception as e:
        print(f"[ERROR] 패키지 설치 실패: {e}")
        return
    
    # Step 4: Verify installation
    print("\n[4/4] 설치 검증 중...")
    if verify_installation():
        print("\n" + "=" * 60)
        print("[OK] 환경 설정 완료!")
        print("=" * 60)
        print("\n실행 방법:")
        if sys.platform == "win32":
            print(f"  1. {VENV_DIR}\\Scripts\\activate")
        else:
            print(f"  1. source {VENV_DIR}/bin/activate")
        print("  2. python main.py")
        print()
    else:
        print("\n[ERROR] 설치 검증 실패")

if __name__ == "__main__":
    main()
