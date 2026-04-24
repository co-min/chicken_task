from psychopy import visual, core, event
from labjack import ljm
from photodiode import PhotoDiodeMarker

# -------------------------------
# 1. LabJack 연결
# -------------------------------
try:
    handle = ljm.openS("T4", "ANY", "ANY")
    print("LabJack connected")
except:
    handle = None
    print("⚠ LabJack not found (TTL disabled)")

# -------------------------------
# 2. PsychoPy 창
# -------------------------------
win = visual.Window([800, 600])
text = visual.TextStim(win, text="Press Z to send TTL\nPress ESC to quit")
photodiode = PhotoDiodeMarker(win)

# -------------------------------
# 3. TTL 함수
# -------------------------------
def send_ttl(handle, duration=0.01):  # 10ms
    if handle is None:
        return
    ljm.eWriteName(handle, "EIO0", 1)   # HIGH
    core.wait(duration)
    ljm.eWriteName(handle, "EIO0", 0)   # LOW

# -------------------------------
# 4. 메인 루프
# -------------------------------
while True:
    keys = event.getKeys()

    # 종료
    if "escape" in keys:
        break

    # Z 키 → TTL
    if "z" in keys:
        print("Z pressed → TTL sent")
        send_ttl(handle)
        photodiode.trigger() # event = current -> 현재 프레임 시간 저장

    text.draw()
    photodiode.update() # current += 1, draw 직전에 update() 
    photodiode.draw() # rendering of white rectangle
    win.flip() # 실제 화면 표시 -> latency 후 




# -------------------------------
# 종료
# -------------------------------
win.close()
core.quit()