# Sound effects
from psychopy import sound as psysound
from pathlib import Path

_DIR = Path(__file__).parent


def load_sounds():
    """
    게임에서 사용하는 사운드 파일을 로드하여 딕셔너리로 반환.

    Returns:
        dict: 사운드 이름 → psychopy.sound.Sound 객체
            - 'flip'     : 사용자 카드 뒤집기
            - 'npc_flip' : PC(문어) 카드 뒤집기
            - 'correct'  : 매칭 성공
            - 'error'    : 매칭 실패 / 타임아웃
            - 'qbeep'    : 시행 시작 큐 ("시작!")
            - 'type'     : 닭 선택 버튼 클릭
            - 'win'      : 문어를 잡았을 때 (user_caught_npc)
            - 'lose'     : 잡혔을 때 (npc_caught_user)
    """
    keys = ['flip', 'npc_flip', 'correct', 'error', 'qbeep', 'type', 'win', 'lose']
    sounds = {}
    for key in keys:
        path = _DIR / f'{key}.wav'
        try:
            sounds[key] = psysound.Sound(str(path), secs=-1)
        except Exception as e:
            print(f"[SOUND] '{key}.wav' 로드 실패: {e}")
            sounds[key] = None
    return sounds


def play(sounds, key):
    """
    사운드를 재생. 객체가 None이거나 오류 발생 시 조용히 무시.

    Args:
        sounds: load_sounds()가 반환한 딕셔너리
        key:    재생할 사운드 키 문자열
    """
    if sounds is None:
        return
    snd = sounds.get(key)
    if snd is None:
        return
    try:
        snd.stop()
        snd.play()
    except Exception as e:
        print(f"[SOUND] '{key}' 재생 실패: {e}")
