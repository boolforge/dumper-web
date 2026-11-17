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

def launch_direct(port_id, port_name):
    print(f"\n[DIRECT LAUNCH] Starting {port_name} ({port_id})...")
    # Launch directly bypassing launcher GUI entirely via ScummVM explicit target argument
    cmd = f"/system/bin/am force-stop org.scummvm.scummvm.debug && /system/bin/logcat -c && /system/bin/am start -n org.scummvm.scummvm.debug/org.scummvm.scummvm.SplashActivity --es commandline '{port_id}'"
    sh(cmd)
    
    # Wait for surface render
    time.sleep(2)
    # Dismiss any transparent system IME or gesture coach overlay
    sh("input keyevent 4") # BACK key (dismisses software keyboard cleanly without moving cursor)
    time.sleep(0.5)
    sh("input tap 720 1600") # Dismiss gesture guide
    time.sleep(1)
    
    out_img = f"/storage/emulated/0/Download/test_{port_id}.png"
    sh(f"/system/bin/screencap -p {out_img}")
    print(f"Captured screenshot: {out_img}")
    
    logs = sh("logcat -d | grep -i -E 'scummvm|snatcher' | tail -n 25")
    print("Logs:")
    print(logs)

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "snatcher-psx"
    launch_direct(target, target)
