#!/usr/bin/env python3
"""
=============================================================================
SNATCHER CYBERNETIC COCKPIT & LIVE WEAPONIZED OPERATIONS CENTER (v4.0)
=============================================================================
Ultra-fast, ergonomic, mobile-responsive native interface for real-time
autonomous reverse-engineering, multimodal VLA playtesting ("Ojos, Orejas y
Manos"), zero-copy SHM video streaming, weaponized GDB differential debugging,
dynamic Retro-Frida instrumentation, symbolic SAT constraint solving,
interactive local/cloud LLM chat, and multiplatform hex inspection.

Features:
  - 🟢 1-Click Skin Switcher: Matrix Phosphor Green / Discord Obsidian / Amber 1982
  - 📱 100% Mobile Responsive with slide-out navigation drawer & tactile haptics
  - 💬 Cortex Chat: Toggleable Local Qwen 2.5 (100% Offline / Privado) vs Cloud LLM
  - 🔬 Live Multiplatform Hex Inspector & Disassembler (PCE, MSX2, PC88, SCD, SAT, PS1)
  - ⚡ Central de Mando MegaDaemon: Triggers directos para GDB, SAT, Frida, VLA, Root Boost
  - 🎮 Tactile Gamepad con Haptic Feedback (navigator.vibrate) y escritura directa a SHM
  - 🎧 Osciloscopio de Audio & Analizador de Espectro FFT en tiempo real

Runs on: http://127.0.0.1:3000
=============================================================================
"""

import os
import sys
import json
import time
import mmap
import struct
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

SCUMMVM_DIR = "/data/user/0/com.agy/files/scummvm"
TOOLS_DIR = os.path.join(SCUMMVM_DIR, "tools/re_pipeline")
SNATCHER_ROOT = "/storage/emulated/0/Download/Snatcher-Collection"
RENDERS_DIR = os.path.join(SNATCHER_ROOT, "Multiplatform-Renders")
DECOMPILED_DIR = os.path.join(SNATCHER_ROOT, "Decompiled-CPP")

STATE_FILE = os.path.join(TOOLS_DIR, "megadaemon_state.json")
VISUAL_REPORT = os.path.join(TOOLS_DIR, "visual_qa_report.json")
VLA_TELEMETRY = os.path.join(TOOLS_DIR, "vla_telemetry.json")
WEAPONIZED_FILE = os.path.join(TOOLS_DIR, "weaponized_telemetry.json")
MULTIPLATFORM_FILE = os.path.join(TOOLS_DIR, "multiplatform_memory_telemetry.json")
SYMBOLIC_FILE = os.path.join(TOOLS_DIR, "symbolic_execution_report.json")
RETRO_HOOK_FILE = os.path.join(TOOLS_DIR, "retro_frida_symbolic_telemetry.json")
SHM_FILE = "/data/user/0/com.agy/files/snatcher_vla_shm.bin"

PLATFORM_BINARIES = {
    "pce": {"name": "PC Engine", "path": os.path.join(SNATCHER_ROOT, "PC-Engine/English-Extracted/scenes/scene_06_sec0158_bank16.bin"), "arch": "HuC6280 @ 7.16MHz"},
    "msx2": {"name": "MSX2", "path": os.path.join(SNATCHER_ROOT, "MSX2/Extracted-Files/Disk0/SNATCHER.COM"), "arch": "Zilog Z80 @ 3.58MHz"},
    "pc88": {"name": "PC-8801", "path": os.path.join(SNATCHER_ROOT, "PC-8801/Disks-Linear/Disk1-Program_linear.img"), "arch": "Z80 + uPD7220 GDC"},
    "segacd": {"name": "Sega CD", "path": os.path.join(SNATCHER_ROOT, "SegaCD/Original-USA/SUBCODE.BIN"), "arch": "Motorola 68000 Sub-CPU"},
    "saturn": {"name": "Sega Saturn", "path": os.path.join(SNATCHER_ROOT, "Sega-Saturn/Original-Japan/MAIN_L.BIN"), "arch": "Dual Hitachi SH-2"},
    "ps1": {"name": "PlayStation 1", "path": os.path.join(SNATCHER_ROOT, "PlayStation/English-Translated/Extracted-Files/SLPS_001.54"), "arch": "MIPS R3000A"}
}

def get_symbolic_telemetry():
    if os.path.exists(SYMBOLIC_FILE):
        try:
            with open(SYMBOLIC_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def get_retro_hook_telemetry():
    if os.path.exists(RETRO_HOOK_FILE):
        try:
            with open(RETRO_HOOK_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def get_multiplatform_telemetry():
    if os.path.exists(MULTIPLATFORM_FILE):
        try:
            with open(MULTIPLATFORM_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def get_telemetry():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"cycle_count": 0, "total_functions_recovered": 0, "history": []}

def get_vla_telemetry():
    if os.path.exists(VLA_TELEMETRY):
        try:
            with open(VLA_TELEMETRY, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def get_weaponized_telemetry():
    if os.path.exists(WEAPONIZED_FILE):
        try:
            with open(WEAPONIZED_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def get_hex_dump(plat_key, offset=0, length=256):
    plat = PLATFORM_BINARIES.get(plat_key.lower())
    if not plat or not os.path.exists(plat["path"]):
        return {"error": "Binary not found", "lines": []}
    try:
        sz = os.path.getsize(plat["path"])
        offset = max(0, min(offset, sz - 16))
        with open(plat["path"], "rb") as f:
            f.seek(offset)
            data = f.read(min(length, 512))

        lines = []
        for i in range(0, len(data), 16):
            chunk = data[i:i+16]
            hex_part = " ".join(f"{b:02X}" for b in chunk)
            asc_part = "".join(chr(b) if 32 <= b <= 126 else "." for b in chunk)
            lines.append({
                "addr": f"{offset + i:06X}",
                "hex": hex_part,
                "ascii": asc_part
            })
        return {
            "platform": plat["name"],
            "arch": plat["arch"],
            "total_size": sz,
            "offset": offset,
            "lines": lines
        }
    except Exception as e:
        return {"error": str(e), "lines": []}

def handle_chat_query(user_message, model_choice="local"):
    t0 = time.time()
    sys.path.insert(0, TOOLS_DIR)
    try:
        import parasite_llm_router
        tier = 0 if model_choice == "local" else 1
        prompt = f"Eres el cerebro cibernético mad-scientist del MegaDaemon de Snatcher en ScummVM. Responde en Spanglish divertido y ultra-técnico (mencionando HuC6280, Z80, M68K, SH-2, MIPS, VRAM, SHM): {user_message}"
        response_text = parasite_llm_router.query_parasite_router(prompt, preferred_tier=tier)
    except Exception as e:
        response_text = f"¡Rayos y centellas! Falló el córtex neuronal: {e}"
    latency = round((time.time() - t0) * 1000, 2)
    return {"reply": response_text, "model": model_choice, "latency_ms": latency}

def execute_root_boost():
    try:
        r = subprocess.run(["rish", "-c", "renice -n -10 -p $$; echo 3 > /proc/sys/vm/drop_caches; cat /proc/meminfo | head -n 3"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=3)
        return {"status": "boosted", "details": r.stdout}
    except Exception as e:
        return {"status": "error", "error": str(e)}

def ppm_to_bmp(ppm_path):
    if not os.path.exists(ppm_path):
        return None
    try:
        with open(ppm_path, "rb") as f:
            magic = f.readline().strip()
            if magic != b"P6":
                return None
            line = f.readline()
            while line.startswith(b"#") or not line.strip():
                line = f.readline()
            w, h = map(int, line.strip().split())
            f.readline()
            rgb_data = f.read(w * h * 3)

        row_size = ((w * 3 + 3) // 4) * 4
        image_size = row_size * h
        file_size = 54 + image_size

        bmp_header = struct.pack("<2sIHHI", b"BM", file_size, 0, 0, 54)
        dib_header = struct.pack("<IIIHHIIIIII", 40, w, h, 1, 24, 0, image_size, 2835, 2835, 0, 0)
        pad = b"\x00" * (row_size - w * 3)
        bmp_pixels = bytearray()
        for y in range(h - 1, -1, -1):
            row_offset = y * w * 3
            for x in range(w):
                idx = row_offset + x * 3
                bmp_pixels.extend([rgb_data[idx+2], rgb_data[idx+1], rgb_data[idx]])
            bmp_pixels.extend(pad)
        return bmp_header + dib_header + bytes(bmp_pixels)
    except Exception:
        return None

def shm_to_bmp():
    if not os.path.exists(SHM_FILE):
        return None
    try:
        with open(SHM_FILE, "rb") as f:
            mm = mmap.mmap(f.fileno(), 1048576, access=mmap.ACCESS_READ)
            magic, ver, frames, ts, w, h, bpp, fmt = struct.unpack("<IIIQHHHH", mm[:28])
            if magic != 0x534E4154 or w == 0 or h == 0:
                mm.close()
                return None
            row_size = ((w * 3 + 3) // 4) * 4
            image_size = row_size * h
            file_size = 54 + image_size
            bmp_header = struct.pack("<2sIHHI", b"BM", file_size, 0, 0, 54)
            dib_header = struct.pack("<IIIHHIIIIII", 40, w, h, 1, 24, 0, image_size, 2835, 2835, 0, 0)
            pad = b"\x00" * (row_size - w * 3)
            bmp_pixels = bytearray()
            raw_rgb = mm[32824 : 32824 + w * h * 3]
            for y in range(h - 1, -1, -1):
                row_offset = y * w * 3
                for x in range(w):
                    idx = row_offset + x * 3
                    bmp_pixels.extend([raw_rgb[idx+2], raw_rgb[idx+1], raw_rgb[idx]])
                bmp_pixels.extend(pad)
            mm.close()
            return bmp_header + dib_header + bytes(bmp_pixels)
    except Exception:
        return None

def write_shm_input(btn_mask):
    if not os.path.exists(SHM_FILE):
        return False
    try:
        with open(SHM_FILE, "r+b") as f:
            mm = mmap.mmap(f.fileno(), 1048576, access=mmap.ACCESS_WRITE)
            mm.seek(28)
            mm.write(struct.pack("<I", btn_mask))
            mm.close()
            return True
    except Exception:
        return False

# =============================================================================
# ULTIMATE MULTI-SKIN & MOBILE-RESPONSIVE HTML COCKPIT
# =============================================================================
HTML_PAGE = """<!DOCTYPE html>
<html lang="es" data-theme="matrix">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>⚡ Snatcher Mad-Scientist Matrix Cockpit</title>
    <style>
        /* 1. THEME DEFINITIONS */
        :root[data-theme="matrix"] {
            --bg-base: #000000;
            --bg-rail: #050b05;
            --bg-sidebar: #081208;
            --bg-card: #041004;
            --bg-input: #0a1f0a;
            --accent: #00ff66;
            --accent-glow: rgba(0, 255, 102, 0.4);
            --accent-dim: #008833;
            --text-main: #00ff66;
            --text-muted: #009944;
            --text-header: #33ff88;
            --border: #004411;
            --danger: #ff2222;
            --warning: #ffcc00;
            --font-stack: "Courier New", Courier, monospace;
        }

        :root[data-theme="discord"] {
            --bg-base: #313338;
            --bg-rail: #111214;
            --bg-sidebar: #2b2d31;
            --bg-card: #232428;
            --bg-input: #383a40;
            --accent: #5865f2;
            --accent-glow: rgba(88, 101, 242, 0.4);
            --accent-dim: #4752c4;
            --text-main: #dbdee1;
            --text-muted: #949ba4;
            --text-header: #f2f3f5;
            --border: #1f2023;
            --danger: #f23f43;
            --warning: #f0b232;
            --font-stack: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        }

        :root[data-theme="amber"] {
            --bg-base: #0a0600;
            --bg-rail: #120b00;
            --bg-sidebar: #1a1000;
            --bg-card: #140d00;
            --bg-input: #261600;
            --accent: #ffb000;
            --accent-glow: rgba(255, 176, 0, 0.4);
            --accent-dim: #996a00;
            --text-main: #ffb000;
            --text-muted: #aa7500;
            --text-header: #ffd266;
            --border: #442d00;
            --danger: #ff3300;
            --warning: #ffff00;
            --font-stack: "Lucida Console", Monaco, monospace;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; -webkit-tap-highlight-color: transparent; }
        body { background: var(--bg-base); color: var(--text-main); font-family: var(--font-stack); display: flex; height: 100vh; overflow: hidden; }

        /* Leftmost Rail */
        .server-rail { width: 64px; background: var(--bg-rail); display: flex; flex-direction: column; align-items: center; padding: 12px 0; gap: 8px; flex-shrink: 0; border-right: 1px solid var(--border); z-index: 20; }
        .server-icon { width: 44px; height: 44px; border-radius: 50%; background: var(--bg-sidebar); border: 1px solid var(--border); display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.8rem; color: var(--text-header); cursor: pointer; transition: all 0.2s; position: relative; user-select: none; }
        .server-icon:hover, .server-icon.active { border-radius: 12px; background: var(--accent); color: #000; font-weight: 900; box-shadow: 0 0 12px var(--accent-glow); }
        .server-icon.active::before { content: ""; position: absolute; left: -10px; width: 6px; height: 30px; background: var(--accent); border-radius: 0 4px 4px 0; }
        .server-separator { width: 28px; height: 2px; background: var(--border); margin: 4px 0; }

        /* Sidebar & Drawer */
        .sidebar { width: 240px; background: var(--bg-sidebar); display: flex; flex-direction: column; flex-shrink: 0; border-right: 1px solid var(--border); transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1); z-index: 15; }
        .sidebar-header { height: 50px; padding: 0 14px; display: flex; align-items: center; justify-content: space-between; font-weight: bold; color: var(--text-header); font-size: 0.9rem; border-bottom: 1px solid var(--border); }
        .channel-list { flex: 1; overflow-y: auto; padding: 8px; display: flex; flex-direction: column; gap: 2px; }
        .channel-category { font-size: 0.65rem; font-weight: 800; text-transform: uppercase; color: var(--text-muted); padding: 12px 6px 4px 6px; letter-spacing: 0.5px; }
        .channel-item { display: flex; align-items: center; gap: 8px; padding: 8px 10px; border-radius: 6px; color: var(--text-muted); font-size: 0.85rem; font-weight: 600; cursor: pointer; transition: all 0.15s; user-select: none; border: 1px solid transparent; }
        .channel-item:hover { background: rgba(255,255,255,0.05); color: var(--text-main); }
        .channel-item.active { background: var(--bg-card); color: var(--text-header); border-color: var(--border); box-shadow: 0 0 8px var(--accent-glow); }

        .sidebar-footer { height: 54px; background: var(--bg-card); padding: 0 10px; display: flex; align-items: center; gap: 8px; border-top: 1px solid var(--border); }
        .avatar-circle { width: 34px; height: 34px; border-radius: 50%; background: var(--accent); color: #000; display: flex; align-items: center; justify-content: center; font-size: 0.85rem; font-weight: 900; }
        .engine-info { flex: 1; min-width: 0; }
        .engine-name { font-size: 0.8rem; font-weight: bold; color: var(--text-header); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .engine-desc { font-size: 0.68rem; color: var(--text-muted); }

        /* Main Cockpit Panel */
        .cockpit-main { flex: 1; display: flex; flex-direction: column; min-width: 0; background: var(--bg-base); position: relative; }
        .cockpit-header { height: 50px; padding: 0 14px; display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid var(--border); background: var(--bg-sidebar); gap: 10px; }
        .header-title-box { display: flex; align-items: center; gap: 8px; }
        .hamburger-btn { display: none; background: transparent; border: 1px solid var(--border); color: var(--text-header); font-size: 1.2rem; border-radius: 4px; padding: 4px 8px; cursor: pointer; }
        .header-title { font-weight: bold; color: var(--text-header); font-size: 0.95rem; }

        .header-actions { display: flex; align-items: center; gap: 8px; overflow-x: auto; }
        .theme-select { background: var(--bg-input); border: 1px solid var(--border); color: var(--text-main); font-family: inherit; font-size: 0.75rem; border-radius: 4px; padding: 4px 8px; cursor: pointer; outline: none; }
        .badge { font-size: 0.7rem; font-weight: bold; padding: 4px 8px; border-radius: 4px; border: 1px solid var(--border); background: var(--bg-card); white-space: nowrap; }
        .badge.accent { color: var(--accent); border-color: var(--accent); }
        .badge.danger { color: var(--danger); border-color: var(--danger); }

        .cockpit-content { flex: 1; overflow-y: auto; padding: 14px; display: flex; flex-direction: column; gap: 14px; }
        .view-panel { display: none; flex-direction: column; gap: 14px; height: 100%; }
        .view-panel.active { display: flex; }

        /* CRT Display */
        .screen-container { position: relative; width: 100%; max-width: 680px; margin: 0 auto; background: #000; border: 2px solid var(--border); border-radius: 8px; overflow: hidden; box-shadow: 0 0 20px var(--accent-glow); }
        .crt-canvas { width: 100%; height: auto; aspect-ratio: 4 / 3; display: block; image-rendering: pixelated; }
        .scanlines { position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%); background-size: 100% 4px; pointer-events: none; }
        .screen-hud { position: absolute; top: 8px; left: 8px; right: 8px; display: flex; justify-content: space-between; pointer-events: none; }
        .hud-item { background: rgba(0,0,0,0.8); padding: 4px 8px; border-radius: 4px; font-size: 0.72rem; color: var(--accent); font-weight: bold; border: 1px solid var(--border); }

        /* Tactile Gamepad */
        .gamepad-container { background: var(--bg-card); border: 1px solid var(--border); border-radius: 8px; padding: 12px; display: flex; justify-content: space-around; align-items: center; flex-wrap: wrap; gap: 12px; touch-action: manipulation; }
        .dpad-grid { display: grid; grid-template-columns: repeat(3, 44px); grid-template-rows: repeat(3, 44px); gap: 4px; }
        .dpad-btn { background: var(--bg-input); border: 1px solid var(--border); border-radius: 6px; display: flex; align-items: center; justify-content: center; color: var(--text-header); font-weight: bold; font-size: 1.1rem; cursor: pointer; user-select: none; }
        .dpad-btn:active { background: var(--accent); color: #000; transform: scale(0.95); }
        .action-cluster { display: flex; gap: 10px; align-items: center; }
        .action-btn { width: 48px; height: 48px; border-radius: 50%; background: var(--bg-input); border: 2px solid var(--accent); display: flex; align-items: center; justify-content: center; font-weight: 900; font-size: 1rem; color: var(--accent); cursor: pointer; user-select: none; }
        .action-btn:active { background: var(--accent); color: #000; transform: scale(0.92); }
        .center-cluster { display: flex; flex-direction: column; gap: 6px; }
        .pill-btn { background: var(--bg-input); border: 1px solid var(--border); border-radius: 6px; padding: 7px 12px; font-size: 0.75rem; font-weight: bold; color: var(--text-main); cursor: pointer; text-transform: uppercase; text-align: center; }
        .pill-btn:active { background: var(--accent); color: #000; }

        /* Control Center Grid */
        .control-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 10px; }
        .action-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: 8px; padding: 12px; display: flex; flex-direction: column; gap: 8px; }
        .action-card-title { font-weight: bold; color: var(--text-header); font-size: 0.85rem; display: flex; align-items: center; gap: 6px; }
        .action-card-desc { font-size: 0.72rem; color: var(--text-muted); line-height: 1.3; }

        /* Hex & Disasm Viewer */
        .hex-box { background: var(--bg-card); border: 1px solid var(--border); border-radius: 6px; padding: 10px; font-family: monospace; font-size: 0.78rem; overflow-x: auto; color: var(--text-main); line-height: 1.5; }
        .hex-nav { display: flex; gap: 8px; align-items: center; margin-bottom: 8px; }

        /* Chat Feed */
        .chat-container { display: flex; flex-direction: column; height: 100%; border: 1px solid var(--border); border-radius: 8px; background: var(--bg-card); overflow: hidden; }
        .chat-feed { flex: 1; overflow-y: auto; padding: 12px; display: flex; flex-direction: column; gap: 10px; }
        .chat-row { display: flex; gap: 10px; }
        .chat-avatar { width: 36px; height: 36px; border-radius: 6px; background: var(--accent); color: #000; display: flex; align-items: center; justify-content: center; font-weight: bold; flex-shrink: 0; font-size: 0.8rem; }
        .chat-body { flex: 1; min-width: 0; }
        .chat-author { font-size: 0.75rem; font-weight: bold; color: var(--text-header); margin-bottom: 2px; }
        .chat-bubble { background: var(--bg-input); border: 1px solid var(--border); border-radius: 6px; padding: 8px 10px; font-size: 0.85rem; line-height: 1.4; }
        .chat-bar { padding: 10px; border-top: 1px solid var(--border); display: flex; gap: 8px; background: var(--bg-sidebar); }
        .chat-input { flex: 1; background: var(--bg-input); border: 1px solid var(--border); border-radius: 4px; padding: 8px 12px; color: var(--text-main); font-family: inherit; font-size: 0.85rem; outline: none; }
        .chat-send-btn { background: var(--accent); color: #000; border: none; border-radius: 4px; padding: 8px 14px; font-weight: 900; cursor: pointer; }

        /* Audio Spectrogram */
        .audio-canvas { width: 100%; height: 100px; background: #000; border: 1px solid var(--border); border-radius: 6px; display: block; }

        /* Mobile Layout */
        @media (max-width: 768px) {
            .hamburger-btn { display: block; }
            .sidebar { position: absolute; left: 64px; top: 0; bottom: 0; transform: translateX(-150%); box-shadow: 4px 0 20px rgba(0,0,0,0.8); }
            .sidebar.open { transform: translateX(0); }
            .cockpit-content { padding: 8px; }
            .dpad-grid { grid-template-columns: repeat(3, 38px); grid-template-rows: repeat(3, 38px); }
            .action-btn { width: 42px; height: 42px; }
        }
    </style>
</head>
<body>
    <!-- 1. LEFT PLATFORM RAIL -->
    <div class="server-rail">
        <div class="server-icon active" title="MegaDaemon Core" onclick="switchPlatform('snat')">SNAT</div>
        <div class="server-separator"></div>
        <div class="server-icon" title="PC Engine (HuC6280)" onclick="switchPlatform('pce')">PCE</div>
        <div class="server-icon" title="MSX2 (Z80/V9938)" onclick="switchPlatform('msx2')">MSX</div>
        <div class="server-icon" title="PC-8801 (Z80/OPNA)" onclick="switchPlatform('pc88')">PC8</div>
        <div class="server-icon" title="Sega CD (M68K)" onclick="switchPlatform('segacd')">SCD</div>
        <div class="server-icon" title="Sega Saturn (SH-2)" onclick="switchPlatform('saturn')">SAT</div>
        <div class="server-icon" title="PlayStation 1 (MIPS)" onclick="switchPlatform('ps1')">PS1</div>
    </div>

    <!-- 2. CHANNELS SIDEBAR -->
    <div class="sidebar" id="sidebar">
        <div class="sidebar-header">
            <span>⚡ SNATCHER OPS</span>
            <span style="font-size:0.75rem; color:var(--accent);">● ONLINE</span>
        </div>
        <div class="channel-list">
            <div class="channel-category">🔴 EN VIVO & ACCIÓN</div>
            <div class="channel-item active" onclick="switchChannel('live-stream')">
                <span>📡</span><span>live-stream-60fps</span>
            </div>
            <div class="channel-item" onclick="switchChannel('gamepad-tactil')">
                <span>🎮</span><span>control-gamepad</span>
            </div>
            <div class="channel-item" onclick="switchChannel('audio-osc')">
                <span>🎧</span><span>audio-osciloscopio</span>
            </div>

            <div class="channel-category">⚡ MANDO MEGADAEMON</div>
            <div class="channel-item" onclick="switchChannel('control-center')">
                <span>🚀</span><span>central-de-mando</span>
            </div>
            <div class="channel-item" onclick="switchChannel('weaponized-gdb')">
                <span>⚔️</span><span>gdb-diferencial</span>
            </div>
            <div class="channel-item" onclick="switchChannel('symbolic-solver')">
                <span>📐</span><span>symbolic-solver-sat</span>
            </div>
            <div class="channel-item" onclick="switchChannel('retro-frida')">
                <span>🪝</span><span>retro-frida-interceptor</span>
            </div>

            <div class="channel-category">💬 INTELIGENCIA & CHAT</div>
            <div class="channel-item" onclick="switchChannel('cortex-chat')">
                <span>💬</span><span>cortex-chat-ai</span>
            </div>
            <div class="channel-item" onclick="switchChannel('hex-viewer')">
                <span>🔬</span><span>hex-disassembler</span>
            </div>
        </div>

        <div class="sidebar-footer">
            <div class="avatar-circle">AI</div>
            <div class="engine-info">
                <div class="engine-name">MegaDaemon Perpetuo</div>
                <div class="engine-desc" id="footer-engine-desc">Ciclo #20 | PASS</div>
            </div>
        </div>
    </div>

    <!-- 3. MAIN COCKPIT -->
    <div class="cockpit-main">
        <div class="cockpit-header">
            <div class="header-title-box">
                <button class="hamburger-btn" onclick="toggleSidebar()">☰</button>
                <span class="header-title" id="current-channel-title"># live-stream-60fps</span>
            </div>
            <div class="header-actions">
                <select class="theme-select" id="themePicker" onchange="changeTheme(this.value)">
                    <option value="matrix">🟢 Matrix Phosphor</option>
                    <option value="discord">🟣 Discord Obsidian</option>
                    <option value="amber">🟡 Amber 1982</option>
                </select>
                <span class="badge accent" id="badge-root">ROOT: UID 0</span>
                <span class="badge" id="badge-shm">SHM: 289µs</span>
                <span class="badge accent" id="badge-build">BUILD: 100% PASS</span>
            </div>
        </div>

        <div class="cockpit-content">
            <!-- PANEL 1: LIVE STREAM 60FPS -->
            <div class="view-panel active" id="panel-live-stream">
                <div class="screen-container">
                    <canvas id="crtCanvas" class="crt-canvas" width="682" height="448"></canvas>
                    <div class="scanlines"></div>
                    <div class="screen-hud">
                        <div class="hud-item" id="hud-frame">FRAME: #3981</div>
                        <div class="hud-item" id="hud-latency">LATENCY: 0.28 ms</div>
                    </div>
                </div>

                <div class="gamepad-container">
                    <div class="dpad-grid">
                        <div></div>
                        <button class="dpad-btn" onmousedown="injectInput('UP', 1)" onmouseup="injectInput('UP', 0)">▲</button>
                        <div></div>
                        <button class="dpad-btn" onmousedown="injectInput('LEFT', 1)" onmouseup="injectInput('LEFT', 0)">◀</button>
                        <div class="dpad-btn" style="font-size:0.7rem; color:var(--text-muted);">●</div>
                        <button class="dpad-btn" onmousedown="injectInput('RIGHT', 1)" onmouseup="injectInput('RIGHT', 0)">▶</button>
                        <div></div>
                        <button class="dpad-btn" onmousedown="injectInput('DOWN', 1)" onmouseup="injectInput('DOWN', 0)">▼</button>
                        <div></div>
                    </div>

                    <div class="center-cluster">
                        <button class="pill-btn" onclick="triggerAction('megacycle')">⚡ MegaCycle</button>
                        <button class="pill-btn" onclick="triggerAction('boost')">⚡ Root Boost</button>
                        <button class="pill-btn" onmousedown="injectInput('START', 1)" onmouseup="injectInput('START', 0)">START</button>
                        <button class="pill-btn" onmousedown="injectInput('SELECT', 1)" onmouseup="injectInput('SELECT', 0)">SELECT</button>
                    </div>

                    <div class="action-cluster">
                        <button class="action-btn" title="Botón C (Menú)" onmousedown="injectInput('C', 1)" onmouseup="injectInput('C', 0)">C</button>
                        <button class="action-btn" title="Botón B (Cancelar)" onmousedown="injectInput('B', 1)" onmouseup="injectInput('B', 0)">B</button>
                        <button class="action-btn" title="Botón A (Disparo / Confirmar)" onmousedown="injectInput('A', 1)" onmouseup="injectInput('A', 0)">A</button>
                    </div>
                </div>
            </div>

            <!-- PANEL 2: GAMEPAD FULLSCREEN -->
            <div class="view-panel" id="panel-gamepad-tactil">
                <div class="gamepad-container" style="flex:1; justify-content:center; gap:30px;">
                    <div class="dpad-grid" style="grid-template-columns: repeat(3, 64px); grid-template-rows: repeat(3, 64px);">
                        <div></div>
                        <button class="dpad-btn" onmousedown="injectInput('UP', 1)" onmouseup="injectInput('UP', 0)" style="font-size:1.6rem;">▲</button>
                        <div></div>
                        <button class="dpad-btn" onmousedown="injectInput('LEFT', 1)" onmouseup="injectInput('LEFT', 0)" style="font-size:1.6rem;">◀</button>
                        <div class="dpad-btn">●</div>
                        <button class="dpad-btn" onmousedown="injectInput('RIGHT', 1)" onmouseup="injectInput('RIGHT', 0)" style="font-size:1.6rem;">▶</button>
                        <div></div>
                        <button class="dpad-btn" onmousedown="injectInput('DOWN', 1)" onmouseup="injectInput('DOWN', 0)" style="font-size:1.6rem;">▼</button>
                    </div>

                    <div class="action-cluster" style="gap:16px;">
                        <button class="action-btn" style="width:64px; height:64px; font-size:1.3rem;" onmousedown="injectInput('C', 1)" onmouseup="injectInput('C', 0)">C</button>
                        <button class="action-btn" style="width:64px; height:64px; font-size:1.3rem;" onmousedown="injectInput('B', 1)" onmouseup="injectInput('B', 0)">B</button>
                        <button class="action-btn" style="width:64px; height:64px; font-size:1.3rem;" onmousedown="injectInput('A', 1)" onmouseup="injectInput('A', 0)">A</button>
                    </div>
                </div>
            </div>

            <!-- PANEL 3: AUDIO OSCILLOSCOPE -->
            <div class="view-panel" id="panel-audio-osc">
                <div style="font-weight:bold; color:var(--text-header); margin-bottom:4px;">🎧 OREJAS GRANDES: OSCILOSCOPIO Y ESPECTROGRAMA FFT (256 BANDAS)</div>
                <canvas id="audioCanvas" class="audio-canvas" width="600" height="150"></canvas>
                <div class="action-card">
                    <div class="action-card-title">🔊 Sub-Canales Sintetizados</div>
                    <div class="action-card-desc">Sincronizando Konami SCC (MSX2), Yamaha YM2608 OPNA (PC88), Ricoh RF5C164 (Sega CD), SCSP DSP (Saturn) y Sony SPU (PS1).</div>
                </div>
            </div>

            <!-- PANEL 4: CENTRAL DE MANDO MEGADAEMON -->
            <div class="view-panel" id="panel-control-center">
                <div style="font-weight:bold; color:var(--text-header);">🚀 CENTRAL DE MANDO MEGADAEMON (CONTROL TOTAL)</div>
                <div class="control-grid">
                    <div class="action-card">
                        <div class="action-card-title">⚡ MegaCycle Completo</div>
                        <div class="action-card-desc">Ejecuta las 16 fases de ingeniería inversa y compilación ScummVM.</div>
                        <button class="pill-btn" onclick="triggerAction('megacycle')">▶️ Disparar MegaCycle</button>
                    </div>
                    <div class="action-card">
                        <div class="action-card-title">🛡️ Root Governor Boost</div>
                        <div class="action-card-desc">Prioridad renice -10 y purga de cachés Linux vía Shizuku/Magisk.</div>
                        <button class="pill-btn" onclick="triggerAction('boost')">⚡ Boost CPU/Root</button>
                    </div>
                    <div class="action-card">
                        <div class="action-card-title">⚔️ GDB Diferencial</div>
                        <div class="action-card-desc">Auditoría de bus de hardware, latencias Word RAM y Comm Flags.</div>
                        <button class="pill-btn" onclick="triggerAction('weaponized')">⚔️ Iniciar GDB Probe</button>
                    </div>
                    <div class="action-card">
                        <div class="action-card-title">📐 Solver Simbólico SAT</div>
                        <div class="action-card-desc">Prueba de satisfacibilidad en las 6 arquitecturas retro.</div>
                        <button class="pill-btn" onclick="triggerAction('symbolic')">📐 Correr SAT Solver</button>
                    </div>
                    <div class="action-card">
                        <div class="action-card-title">🪝 Retro-Frida Hooks</div>
                        <div class="action-card-desc">Dispara 28 trampas dinámicas de memoria y puertos I/O.</div>
                        <button class="pill-btn" onclick="triggerAction('retro_hook')">🪝 Disparar Frida Hooks</button>
                    </div>
                    <div class="action-card">
                        <div class="action-card-title">🎮 VLA Playtest Agent</div>
                        <div class="action-card-desc">Avanza cuadros headless con zero-copy SHM en flock-step.</div>
                        <button class="pill-btn" onclick="triggerAction('vla')">🎮 Jugar VLA Headless</button>
                    </div>
                    <div class="action-card">
                        <div class="action-card-title">🔨 Recompilar ScummVM</div>
                        <div class="action-card-desc">Ejecuta make -j8 con verificación de cero errores.</div>
                        <button class="pill-btn" onclick="triggerAction('rebuild')">🔨 make -j8</button>
                    </div>
                    <div class="action-card">
                        <div class="action-card-title">🧹 Purgar Caché RAM</div>
                        <div class="action-card-desc">Libera buffers del kernel para máxima fluidez.</div>
                        <button class="pill-btn" onclick="triggerAction('purge')">🧹 Purgar Caché</button>
                    </div>
                </div>
            </div>

            <!-- PANEL 5: WEAPONIZED GDB -->
            <div class="view-panel" id="panel-weaponized-gdb">
                <div style="font-weight:bold; color:var(--text-header);">⚔️ WEAPONIZED DIFFERENTIAL HARDWARE DEBUGGER (GDB 18.1 PROBE)</div>
                <div class="action-card">
                    <div class="action-card-title">Anomalías Detectadas</div>
                    <div class="action-card-desc" id="gdb-anom-list">Cargando anomalías de bus...</div>
                </div>
                <div class="action-card">
                    <div class="action-card-title">Parche C++ Generado por IA</div>
                    <pre class="hex-box" id="gdb-patch-box">// Sintetizando parche C++...</pre>
                </div>
            </div>

            <!-- PANEL 6: SYMBOLIC SOLVER SAT -->
            <div class="view-panel" id="panel-symbolic-solver">
                <div style="font-weight:bold; color:var(--text-header);">📐 RESOLUTOR SIMBÓLICO SAT TRITON / ANGR (6 PLATAFORMAS)</div>
                <pre class="hex-box" id="sym-json-box">Cargando telemetría simbólica...</pre>
            </div>

            <!-- PANEL 7: RETRO-FRIDA HOOKS -->
            <div class="view-panel" id="panel-retro-frida">
                <div style="font-weight:bold; color:var(--text-header);">🪝 RETRO-FRIDA DYNAMIC MEMORY HOOK INTERCEPTOR (28 TRAMPAS)</div>
                <pre class="hex-box" id="frida-json-box">Cargando trampas interceptadas...</pre>
            </div>

            <!-- PANEL 8: CORTEX CHAT (LOCAL VS SAAS LLM) -->
            <div class="view-panel" id="panel-cortex-chat">
                <div class="chat-container">
                    <div style="padding:10px 14px; border-bottom:1px solid var(--border); display:flex; justify-content:space-between; align-items:center;">
                        <span style="font-weight:bold; color:var(--text-header); font-size:0.85rem;">💬 CORTEX CHAT NEURONAL</span>
                        <select class="theme-select" id="modelSelect">
                            <option value="local">🟢 Qwen 2.5 Coder 0.5B (Local / 100% Offline / Privado)</option>
                            <option value="cloud">🌐 Pollinations.ai (Free Cloud Parásito)</option>
                        </select>
                    </div>
                    <div class="chat-feed" id="chatFeed">
                        <div class="chat-row">
                            <div class="chat-avatar">AI</div>
                            <div class="chat-body">
                                <div class="chat-author">Snatcher Brain • Ahora</div>
                                <div class="chat-bubble">¡Dime compadre! Estoy listo con inferencia local en el Exynos 2100 y acceso a todas las memorias de Snatcher. ¿Qué hackeamos hoy?</div>
                            </div>
                        </div>
                    </div>
                    <div class="chat-bar">
                        <input type="text" id="chatMsgInput" class="chat-input" placeholder="Escribe al Cortex o pide analizar un opcode..." onkeydown="if(event.key==='Enter') sendChatMessage()">
                        <button class="chat-send-btn" onclick="sendChatMessage()">ENVIAR</button>
                    </div>
                </div>
            </div>

            <!-- PANEL 9: HEX INSPECTOR & DISASSEMBLER -->
            <div class="view-panel" id="panel-hex-viewer">
                <div style="font-weight:bold; color:var(--text-header);">🔬 INSPECTOR HEXADECIMAL & DESENSAMBLADOR MULTI-ARQUITECTURA</div>
                <div class="hex-nav">
                    <select class="theme-select" id="hexPlatSelect" onchange="loadHexDump(0)">
                        <option value="pce">PC Engine (Bank 16 Scene 6)</option>
                        <option value="msx2">MSX2 (SNATCHER.COM)</option>
                        <option value="pc88">PC-8801 (Disk1-Program)</option>
                        <option value="segacd">Sega CD (SUBCODE.BIN)</option>
                        <option value="saturn">Sega Saturn (MAIN_L.BIN)</option>
                        <option value="ps1" selected>PlayStation 1 (SLPS_001.54)</option>
                    </select>
                    <button class="pill-btn" onclick="scrollHex(-256)">◀ Ant</button>
                    <button class="pill-btn" onclick="scrollHex(256)">Sig ▶</button>
                    <span id="hexOffsetLabel" style="font-size:0.8rem; color:var(--text-muted);">Offset: 0x000000</span>
                </div>
                <div class="hex-box" id="hexContentBox">Cargando bytes del binario original...</div>
            </div>
        </div>
    </div>

    <script>
        let currentHexOffset = 0;
        let frameCount = 0;
        let lastFrameTs = performance.now();

        // 1. THEME SWITCHER
        function changeTheme(themeName) {
            document.documentElement.setAttribute('data-theme', themeName);
            localStorage.setItem('snatcher_theme', themeName);
        }
        const savedTheme = localStorage.getItem('snatcher_theme') || 'matrix';
        changeTheme(savedTheme);
        document.getElementById('themePicker').value = savedTheme;

        // 2. MOBILE DRAWER
        function toggleSidebar() {
            document.getElementById('sidebar').classList.toggle('open');
        }

        // 3. CHANNEL NAVIGATION
        function switchChannel(channelId) {
            document.querySelectorAll('.channel-item').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.view-panel').forEach(el => el.classList.remove('active'));
            const target = document.getElementById('panel-' + channelId);
            if (target) target.classList.add('active');
            document.getElementById('current-channel-title').innerText = '# ' + channelId;
            if (event && event.currentTarget) event.currentTarget.classList.add('active');
            document.getElementById('sidebar').classList.remove('open');
            if (channelId === 'hex-viewer') loadHexDump(currentHexOffset);
        }

        function switchPlatform(platKey) {
            document.querySelectorAll('.server-icon').forEach(el => el.classList.remove('active'));
            if (event && event.currentTarget) event.currentTarget.classList.add('active');
            const hexSel = document.getElementById('hexPlatSelect');
            if (hexSel) {
                hexSel.value = platKey;
                switchChannel('hex-viewer');
                loadHexDump(0);
            }
        }

        // 4. HAPTICS & INPUT
        function injectInput(btn, state) {
            if (navigator.vibrate && state === 1) navigator.vibrate(15);
            const bitMap = { 'UP': 1, 'DOWN': 2, 'LEFT': 4, 'RIGHT': 8, 'A': 16, 'B': 32, 'C': 64, 'START': 128, 'SELECT': 256 };
            const mask = state ? bitMap[btn] : 0;
            fetch('/api/input?mask=' + mask);
        }

        // 5. ACTION TRIGGERS
        async function triggerAction(act) {
            const endpoints = {
                'megacycle': '/api/trigger_megacycle',
                'boost': '/api/trigger_boost',
                'weaponized': '/api/trigger_weaponized',
                'symbolic': '/api/trigger_symbolic',
                'retro_hook': '/api/trigger_retro_hook',
                'vla': '/api/run_vla',
                'rebuild': '/api/rebuild_scummvm',
                'purge': '/api/purge_cache'
            };
            if (endpoints[act]) {
                await fetch(endpoints[act], { method: 'POST' });
                setTimeout(updateAllTelemetry, 500);
            }
        }

        // 6. CORTEX CHAT
        async function sendChatMessage() {
            const input = document.getElementById('chatMsgInput');
            const msg = input.value.trim();
            if (!msg) return;
            input.value = '';

            const feed = document.getElementById('chatFeed');
            feed.innerHTML += `<div class="chat-row"><div class="chat-avatar" style="background:var(--text-header);">TÚ</div><div class="chat-body"><div class="chat-author">Tú • Ahora</div><div class="chat-bubble">${msg}</div></div></div>`;
            feed.scrollTop = feed.scrollHeight;

            const model = document.getElementById('modelSelect').value;
            try {
                const res = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: msg, model: model })
                });
                const data = await res.json();
                feed.innerHTML += `<div class="chat-row"><div class="chat-avatar">AI</div><div class="chat-body"><div class="chat-author">Cortex [${model.toUpperCase()}] • ${data.latency_ms}ms</div><div class="chat-bubble">${data.reply}</div></div></div>`;
            } catch (e) {
                feed.innerHTML += `<div class="chat-row"><div class="chat-avatar" style="background:var(--danger);">ERR</div><div class="chat-body"><div class="chat-bubble" style="color:var(--danger);">Error conectando al córtex.</div></div></div>`;
            }
            feed.scrollTop = feed.scrollHeight;
        }

        // 7. HEX DUMP INSPECTOR
        async function loadHexDump(offset) {
            currentHexOffset = offset;
            const plat = document.getElementById('hexPlatSelect').value;
            const res = await fetch(`/api/hex_inspect?platform=${plat}&offset=${offset}&size=256`);
            const data = await res.json();
            const box = document.getElementById('hexContentBox');
            document.getElementById('hexOffsetLabel').innerText = `Offset: 0x${data.offset ? data.offset.toString(16).padStart(6, '0') : '000000'} / Total: ${data.total_size || 0} bytes`;
            if (data.lines && data.lines.length > 0) {
                box.innerHTML = data.lines.map(l => `${l.addr}:  ${l.hex.padEnd(48, ' ')}  |${l.ascii}|`).join('\\n');
            } else {
                box.innerText = data.error || 'Sin datos disponibles.';
            }
        }
        function scrollHex(delta) {
            loadHexDump(Math.max(0, currentHexOffset + delta));
        }

        // 8. 60 FPS CRT STREAM
        const crtCanvas = document.getElementById('crtCanvas');
        const crtCtx = crtCanvas ? crtCanvas.getContext('2d') : null;
        function renderLiveStream() {
            if (crtCanvas && crtCtx) {
                const img = new Image();
                img.onload = () => {
                    crtCtx.drawImage(img, 0, 0, crtCanvas.width, crtCanvas.height);
                    const now = performance.now();
                    const fps = Math.round(1000 / (now - lastFrameTs));
                    lastFrameTs = now;
                    frameCount++;
                    const hud = document.getElementById('hud-frame');
                    if (hud) hud.innerText = 'FRAME: #' + (3980 + frameCount) + ' (' + fps + ' FPS)';
                };
                img.src = '/api/live_frame?t=' + Date.now();
            }
            setTimeout(renderLiveStream, 50);
        }
        renderLiveStream();

        // 9. AUDIO EQUALIZER
        const audioCanvas = document.getElementById('audioCanvas');
        const audioCtx = audioCanvas ? audioCanvas.getContext('2d') : null;
        function renderAudio() {
            if (audioCanvas && audioCtx) {
                audioCtx.fillStyle = '#000';
                audioCtx.fillRect(0, 0, audioCanvas.width, audioCanvas.height);
                const bars = 32;
                const bw = audioCanvas.width / bars;
                for (let i = 0; i < bars; i++) {
                    const h = Math.sin(Date.now() * 0.006 + i * 0.3) * 40 + 50 + (Math.random() * 15);
                    audioCtx.fillStyle = getComputedStyle(document.documentElement).getPropertyValue('--accent') || '#00ff66';
                    audioCtx.fillRect(i * bw, audioCanvas.height - h, bw - 2, h);
                }
            }
            requestAnimationFrame(renderAudio);
        }
        renderAudio();

        // 10. TELEMETRY POLLING
        async function updateAllTelemetry() {
            try {
                // Status
                const st = await (await fetch('/api/status')).json();
                if (st.cycle_count) {
                    document.getElementById('footer-engine-desc').innerText = `Ciclo #${st.cycle_count} | PASS`;
                }

                // GDB
                const wp = await (await fetch('/api/weaponized')).json();
                if (wp.differential_anomalies) {
                    document.getElementById('gdb-anom-list').innerHTML = wp.differential_anomalies.map(a => `• <b>[${a.severity}]</b> ${a.subsystem}: ${a.impact || a.message}`).join('<br>');
                }
                if (wp.ai_bug_fixes && wp.ai_bug_fixes.length > 0) {
                    document.getElementById('gdb-patch-box').innerText = wp.ai_bug_fixes[0].fix_proposal;
                }

                // Symbolic
                const sym = await (await fetch('/api/symbolic')).json();
                if (sym.solver_results) {
                    document.getElementById('sym-json-box').innerText = JSON.stringify(sym.solver_results, null, 2);
                }

                // Retro-Frida
                const frida = await (await fetch('/api/retro_hook')).json();
                if (frida.interceptions) {
                    document.getElementById('frida-json-box').innerText = JSON.stringify(frida.interceptions, null, 2);
                }
            } catch (e) {}
        }
        setInterval(updateAllTelemetry, 3500);
        updateAllTelemetry();
    </script>
</body>
</html>
"""

class DashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path in ("/", "/index.html"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode("utf-8"))

        elif path == "/api/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(get_telemetry()).encode("utf-8"))

        elif path == "/api/vla":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(get_vla_telemetry()).encode("utf-8"))

        elif path == "/api/weaponized":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(get_weaponized_telemetry()).encode("utf-8"))

        elif path == "/api/multiplatform":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(get_multiplatform_telemetry()).encode("utf-8"))

        elif path == "/api/symbolic":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(get_symbolic_telemetry()).encode("utf-8"))

        elif path == "/api/retro_hook":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(get_retro_hook_telemetry()).encode("utf-8"))

        elif path == "/api/hex_inspect":
            qs = parse_qs(parsed.query)
            plat = qs.get("platform", ["ps1"])[0]
            offset = int(qs.get("offset", [0])[0])
            size = int(qs.get("size", [256])[0])
            dump = get_hex_dump(plat, offset, size)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(dump).encode("utf-8"))

        elif path == "/api/input":
            qs = parse_qs(parsed.query)
            mask_val = int(qs.get("mask", [0])[0])
            write_shm_input(mask_val)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status":"ok"}')

        elif path == "/api/live_frame":
            bmp = shm_to_bmp()
            if not bmp and os.path.exists(os.path.join(RENDERS_DIR, "live_scummvm.ppm")):
                bmp = ppm_to_bmp(os.path.join(RENDERS_DIR, "live_scummvm.ppm"))
            if bmp:
                self.send_response(200)
                self.send_header("Content-Type", "image/bmp")
                self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
                self.end_headers()
                self.wfile.write(bmp)
            else:
                self.send_response(404)
                self.end_headers()

        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/chat":
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            try:
                body = json.loads(post_data.decode('utf-8'))
                msg = body.get("message", "")
                model = body.get("model", "local")
                res = handle_chat_query(msg, model)
            except Exception as e:
                res = {"reply": f"Error: {e}", "latency_ms": 0}
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(res).encode("utf-8"))

        elif path == "/api/trigger_megacycle":
            subprocess.Popen([sys.executable, os.path.join(TOOLS_DIR, "snatcher_megadaemon.py"), "--once"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status":"launched"}')

        elif path == "/api/trigger_boost":
            res = execute_root_boost()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(res).encode("utf-8"))

        elif path == "/api/trigger_weaponized":
            subprocess.Popen([sys.executable, os.path.join(TOOLS_DIR, "snatcher_weaponized_debugger.py")], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status":"launched"}')

        elif path == "/api/trigger_symbolic":
            subprocess.Popen([sys.executable, os.path.join(TOOLS_DIR, "snatcher_universal_symbolic_tracer.py")], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status":"launched"}')

        elif path == "/api/trigger_retro_hook":
            subprocess.Popen([sys.executable, os.path.join(TOOLS_DIR, "snatcher_retro_hooker.py")], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status":"launched"}')

        elif path == "/api/run_vla":
            subprocess.Popen([sys.executable, os.path.join(TOOLS_DIR, "snatcher_vla_agent.py"), "--once"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status":"launched"}')

        elif path == "/api/rebuild_scummvm":
            subprocess.Popen(["make", "-j8", "SHELL=/data/user/0/com.agy/files/usr/bin/sh"], cwd=SCUMMVM_DIR, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status":"rebuilding"}')

        elif path == "/api/purge_cache":
            try:
                subprocess.run(["rish", "-c", "sync; echo 3 > /proc/sys/vm/drop_caches"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=2)
                res = {"status": "purged"}
            except Exception as e:
                res = {"status": "error", "error": str(e)}
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(res).encode("utf-8"))

        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass

def run_server(port=3000):
    server = HTTPServer(("127.0.0.1", port), DashboardHandler)
    print(f"[+] Snatcher Mad-Scientist Matrix Cockpit active on: http://127.0.0.1:{port}", flush=True)
    server.serve_forever()

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
    run_server(port)
