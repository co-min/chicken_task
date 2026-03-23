import ljm

try:
    handle = ljm.openS("T4", "USB", "ANY")
    info = ljm.getHandleInfo(handle)
    print("Connected:", info)
    voltage = ljm.eReadName(handle, "AIN0")
    print("AIN0 Voltage:", voltage)
finally:
    try:
        ljm.close(handle)
    except Exception:
        pass