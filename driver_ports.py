import subprocess, time, sys

PORTS = [
    ("snatcher-psx", "PlayStation 1 (Unpacked)"),
    ("snatcher-pce", "PC-Engine Super CD-ROM (Unpacked)"),
    ("snatcher-saturn", "Sega Saturn (Unpacked)"),
    ("snatcher-msx", "MSX2 (Unpacked)"),
    ("snatcher-pc88", "PC-8801 (Unpacked)")
]

def sh(cmd):
    res = subprocess.run(["rish", "-c", cmd], capture_output=True, text=True)
    return res.stdout.strip()

def check_and_handle_screen(port_id):
    # Check logcat for debugger drop
    logs = sh("logcat -d | grep -i -E 'scummvm|snatcher' | tail -n 20")
    if "Debugger started" in logs or "ERROR:" in logs:
        print(f"[{port_id}] Debugger trap detected! Auto-typing 'exit' to escape...")
        sh("input text 'exit'")
        time.sleep(0.5)
        sh("input keyevent 66") # ENTER
        time.sleep(1)

def run_port(port_id, port_name):
    print(f"\n==========================================")
    print(f"Testing port: {port_name} ({port_id})")
    print(f"==========================================")
    
    # 1. Stop and clean start
    sh(f"/system/bin/am force-stop org.scummvm.scummvm.debug && /system/bin/logcat -c && /system/bin/am start -n org.scummvm.scummvm.debug/org.scummvm.scummvm.SplashActivity")
    time.sleep(2)
    
    # 2. Dismiss Storage Notice if present
    sh("input tap 550 1900")
    time.sleep(1)
    
    # 3. Tap Start button in launcher (bottom right, coordinate calibrated at x=1200 y=3000)
    sh("input tap 1200 3000")
    time.sleep(2)
    
    # 4. Tap center to dismiss touch overlay
    sh("input tap 720 1600")
    time.sleep(1)
    
    # 5. Check if debugger appeared and automatically escape it
    check_and_handle_screen(port_id)
    
    # 6. Capture screen
    out_img = f"/storage/emulated/0/Download/test_{port_id}.png"
    sh(f"/system/bin/screencap -p {out_img}")
    print(f"Captured screenshot: {out_img}")
    
    # 7. Print latest logs
    res = sh("/system/bin/logcat -d | grep -i -E 'scummvm|snatcher' | tail -n 25")
    print("Execution logs:")
    print(res)

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "all"
    for pid, name in PORTS:
        if target == "all" or pid == target:
            run_port(pid, name)
