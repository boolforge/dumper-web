import subprocess, time, os, re

def sh(cmd):
    res = subprocess.run(["rish", "-c", cmd], capture_output=True, text=True)
    return res.stdout.strip()

def capture():
    img_path = "/storage/emulated/0/Download/watcher_screen.png"
    sh(f"/system/bin/screencap -p {img_path}")
    return img_path

def get_window_focus():
    return sh("dumpsys window | grep -E 'mCurrentFocus|mFocusedApp'")

def dismiss_known_dialogs():
    # 1. Check if ScummVM is in foreground
    focus = get_window_focus()
    if "org.scummvm.scummvm.debug" not in focus:
        return False

    # 2. Check logcat for clues
    logs = sh("logcat -d | grep -i -E 'scummvm|dialog' | tail -n 20")
    
    # Tap OK button for Storage Access Framework / Dialog
    # Position: center-bottom of typical dialog (x=550 y=1960)
    sh("input tap 550 1960")
    time.sleep(0.5)
    # Tap center to dismiss tutorial overlays (x=720 y=1600)
    sh("input tap 720 1600")
    time.sleep(0.5)
    return True

print("Screen watcher initialized.")
