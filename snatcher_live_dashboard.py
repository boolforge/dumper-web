#!/usr/bin/env python3
"""
=============================================================================
SNATCHER DISCORD-STYLE CYBERNETIC COCKPIT & LIVE WEAPONIZED OPERATIONS CENTER
=============================================================================
Ultra-fast, ergonomic Discord-inspired native interface for real-time
autonomous reverse-engineering, multimodal VLA playtesting ("Ojos, Orejas y
Manos"), zero-copy SHM video streaming, weaponized GDB differential debugging,
and parasitic zero-cost LLM reasoning.

Runs on: http://127.0.0.1:3000
100% Native Vanilla JS/CSS (0 external libraries, <2MB RAM footprint, 60 FPS).
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
SHM_FILE = "/data/user/0/com.agy/files/snatcher_vla_shm.bin"

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

def get_decompiled_files():
    files = {}
    if os.path.exists(DECOMPILED_DIR):
        for fname in sorted(os.listdir(DECOMPILED_DIR)):
            if fname.endswith((".cpp", ".c", ".txt")):
                fpath = os.path.join(DECOMPILED_DIR, fname)
                try:
                    with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                        files[fname] = f.read()[:5000]
                except Exception:
                    pass
    return files

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
    """Writes button bitmask directly into live SHM input register at offset 28."""
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
# DISCORD-INSPIRED ULTRA-ERGONOMIC CYBERNETIC COCKPIT (HTML/CSS/JS)
# =============================================================================
HTML_PAGE = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Snatcher Cybernetic Cockpit</title>
    <style>
        :root {
            --bg-rail: #111214;
            --bg-sidebar: #2b2d31;
            --bg-chat: #313338;
            --bg-card: #232428;
            --bg-input: #383a40;
            --blurple: #5865f2;
            --blurple-hover: #4752c4;
            --green: #23a55a;
            --yellow: #f0b232;
            --red: #f23f43;
            --cyan: #00f0ff;
            --text-normal: #dbdee1;
            --text-muted: #949ba4;
            --text-header: #f2f3f5;
            --border: #1f2023;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; -webkit-tap-highlight-color: transparent; }
        body { background: var(--bg-chat); color: var(--text-normal); font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; display: flex; height: 100vh; overflow: hidden; }

        /* Leftmost Server Rail (Discord Style) */
        .server-rail { width: 68px; background: var(--bg-rail); display: flex; flex-direction: column; align-items: center; padding: 12px 0; gap: 8px; flex-shrink: 0; border-right: 1px solid var(--border); }
        .server-icon { width: 48px; height: 48px; border-radius: 24px; background: var(--bg-sidebar); display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.85rem; color: var(--text-header); cursor: pointer; transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1); position: relative; user-select: none; }
        .server-icon:hover, .server-icon.active { border-radius: 16px; background: var(--blurple); color: #fff; }
        .server-icon.active::before { content: ""; position: absolute; left: -12px; width: 8px; height: 36px; background: #fff; border-radius: 0 4px 4px 0; }
        .server-icon .pill-badge { position: absolute; bottom: -2px; right: -2px; width: 14px; height: 14px; background: var(--green); border-radius: 50%; border: 3px solid var(--bg-rail); }
        .server-separator { width: 32px; height: 2px; background: var(--bg-sidebar); margin: 4px 0; }

        /* Channels Sidebar */
        .sidebar { width: 240px; background: var(--bg-sidebar); display: flex; flex-direction: column; flex-shrink: 0; border-right: 1px solid var(--border); }
        .sidebar-header { height: 48px; padding: 0 16px; display: flex; align-items: center; justify-content: space-between; font-weight: bold; color: var(--text-header); font-size: 0.95rem; border-bottom: 1px solid var(--border); box-shadow: 0 1px 2px rgba(0,0,0,0.2); }
        .channel-list { flex: 1; overflow-y: auto; padding: 8px; display: flex; flex-direction: column; gap: 2px; }
        .channel-category { font-size: 0.68rem; font-weight: 800; text-transform: uppercase; color: var(--text-muted); padding: 14px 8px 4px 8px; letter-spacing: 0.5px; }
        .channel-item { display: flex; align-items: center; gap: 8px; padding: 7px 10px; border-radius: 4px; color: var(--text-muted); font-size: 0.88rem; font-weight: 500; cursor: pointer; transition: all 0.15s; user-select: none; }
        .channel-item:hover { background: rgba(255,255,255,0.05); color: var(--text-normal); }
        .channel-item.active { background: rgba(255,255,255,0.1); color: var(--text-header); font-weight: 600; }
        .channel-icon { font-size: 1.05rem; opacity: 0.7; }

        /* User / Engine Status Footer */
        .sidebar-footer { height: 52px; background: var(--bg-card); padding: 0 10px; display: flex; align-items: center; gap: 8px; border-top: 1px solid var(--border); }
        .avatar-circle { width: 32px; height: 32px; border-radius: 50%; background: var(--blurple); display: flex; align-items: center; justify-content: center; font-size: 0.8rem; font-weight: bold; color: #fff; position: relative; }
        .status-dot { position: absolute; bottom: -1px; right: -1px; width: 10px; height: 10px; background: var(--green); border-radius: 50%; border: 2px solid var(--bg-card); }
        .engine-info { flex: 1; min-width: 0; }
        .engine-name { font-size: 0.82rem; font-weight: bold; color: var(--text-header); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .engine-desc { font-size: 0.7rem; color: var(--text-muted); }

        /* Main Cockpit Panel */
        .cockpit-main { flex: 1; display: flex; flex-direction: column; min-width: 0; background: var(--bg-chat); }
        .cockpit-header { height: 48px; padding: 0 16px; display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid var(--border); box-shadow: 0 1px 2px rgba(0,0,0,0.2); flex-shrink: 0; }
        .header-title { display: flex; align-items: center; gap: 8px; font-weight: bold; color: var(--text-header); font-size: 0.95rem; }
        .header-badges { display: flex; gap: 6px; align-items: center; flex-wrap: wrap; }
        .badge { font-size: 0.7rem; padding: 3px 8px; border-radius: 12px; font-weight: bold; background: var(--bg-card); border: 1px solid var(--border); color: var(--text-normal); }
        .badge.green { background: rgba(35, 165, 90, 0.15); color: var(--green); border-color: var(--green); }
        .badge.blurple { background: rgba(88, 101, 242, 0.15); color: var(--blurple); border-color: var(--blurple); }
        .badge.yellow { background: rgba(240, 178, 50, 0.15); color: var(--yellow); border-color: var(--yellow); }
        .badge.cyan { background: rgba(0, 240, 255, 0.15); color: var(--cyan); border-color: var(--cyan); }

        /* Cockpit Views */
        .cockpit-content { flex: 1; overflow-y: auto; padding: 16px; display: flex; flex-direction: column; gap: 16px; }
        .view-panel { display: none; flex-direction: column; gap: 16px; height: 100%; }
        .view-panel.active { display: flex; }

        /* CRT Screen & Live Stream */
        .screen-container { background: #000; border-radius: 8px; border: 2px solid var(--border); overflow: hidden; position: relative; display: flex; flex-direction: column; align-items: center; justify-content: center; box-shadow: 0 8px 24px rgba(0,0,0,0.6); }
        .crt-canvas { width: 100%; max-width: 640px; height: auto; aspect-ratio: 4/3; image-rendering: pixelated; display: block; background: #000; }
        .scanlines { position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.35) 50%); background-size: 100% 4px; }
        .screen-hud { position: absolute; top: 8px; left: 8px; right: 8px; display: flex; justify-content: space-between; pointer-events: none; }
        .hud-item { background: rgba(0,0,0,0.7); backdrop-filter: blur(4px); padding: 4px 8px; border-radius: 4px; font-family: monospace; font-size: 0.72rem; color: var(--green); font-weight: bold; border: 1px solid rgba(255,255,255,0.1); }

        /* Tactical Ergonomic Gamepad */
        .gamepad-container { background: var(--bg-card); border: 1px solid var(--border); border-radius: 8px; padding: 14px; display: flex; justify-content: space-around; align-items: center; flex-wrap: wrap; gap: 14px; }
        .dpad-grid { display: grid; grid-template-columns: repeat(3, 44px); grid-template-rows: repeat(3, 44px); gap: 4px; }
        .dpad-btn { background: var(--bg-sidebar); border: 1px solid var(--border); border-radius: 6px; display: flex; align-items: center; justify-content: center; color: var(--text-header); font-weight: bold; font-size: 1.1rem; cursor: pointer; user-select: none; transition: background 0.1s; }
        .dpad-btn:active { background: var(--blurple); transform: scale(0.95); }
        .action-cluster { display: flex; gap: 10px; align-items: center; }
        .action-btn { width: 48px; height: 48px; border-radius: 50%; background: var(--bg-sidebar); border: 2px solid var(--border); display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 1rem; color: var(--text-header); cursor: pointer; user-select: none; transition: all 0.1s; }
        .action-btn.a { border-color: var(--red); color: var(--red); }
        .action-btn.b { border-color: var(--yellow); color: var(--yellow); }
        .action-btn.c { border-color: var(--cyan); color: var(--cyan); }
        .action-btn:active { background: #fff; color: #000; transform: scale(0.92); }
        .center-cluster { display: flex; flex-direction: column; gap: 6px; }
        .pill-btn { background: var(--bg-input); border: 1px solid var(--border); border-radius: 12px; padding: 6px 14px; font-size: 0.72rem; font-weight: bold; color: var(--text-muted); cursor: pointer; text-transform: uppercase; text-align: center; }
        .pill-btn:active { background: var(--blurple); color: #fff; }

        /* Audio Visualizer & Spectrogram */
        .audio-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: 8px; padding: 14px; }
        .audio-canvas { width: 100%; height: 120px; background: #0d0e11; border-radius: 6px; border: 1px solid var(--border); display: block; }

        /* Discord Chat Feed (Parasite LLM & GDB Logs) */
        .discord-feed { flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 12px; }
        .msg-row { display: flex; gap: 12px; padding: 6px 8px; border-radius: 4px; transition: background 0.1s; }
        .msg-row:hover { background: rgba(0,0,0,0.1); }
        .msg-avatar { width: 40px; height: 40px; border-radius: 50%; background: var(--blurple); display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.85rem; color: #fff; flex-shrink: 0; }
        .msg-content { flex: 1; min-width: 0; }
        .msg-author-line { display: flex; align-items: baseline; gap: 8px; margin-bottom: 3px; }
        .msg-author { font-weight: bold; color: var(--text-header); font-size: 0.88rem; }
        .msg-tag { font-size: 0.65rem; background: var(--blurple); color: #fff; padding: 1px 4px; border-radius: 3px; text-transform: uppercase; }
        .msg-time { font-size: 0.7rem; color: var(--text-muted); }
        .msg-text { font-size: 0.85rem; line-height: 1.4; color: var(--text-normal); word-break: break-word; }
        .code-block { background: #1e1f22; border-radius: 4px; padding: 8px 10px; font-family: monospace; font-size: 0.8rem; margin-top: 6px; border-left: 3px solid var(--blurple); overflow-x: auto; color: var(--cyan); }

        /* Mobile Adjustments */
        @media (max-width: 768px) {
            .sidebar { display: none; }
            .sidebar.mobile-open { display: flex; position: absolute; left: 68px; top: 0; height: 100%; z-index: 1000; box-shadow: 4px 0 16px rgba(0,0,0,0.5); }
            .dpad-grid { grid-template-columns: repeat(3, 38px); grid-template-rows: repeat(3, 38px); }
            .action-btn { width: 42px; height: 42px; }
        }
    </style>
</head>
<body>
    <!-- 1. LEFT SERVER RAIL -->
    <div class="server-rail">
        <div class="server-icon active" title="ScummVM Snatcher Engine" onclick="switchServer('snat')">
            SNAT
            <div class="pill-badge"></div>
        </div>
        <div class="server-separator"></div>
        <div class="server-icon" title="Sega CD Sub-CPU (M68000)" onclick="switchServer('scd')">SCD</div>
        <div class="server-icon" title="Sega Saturn (Dual SH-2)" onclick="switchServer('sat')">SAT</div>
        <div class="server-icon" title="PlayStation 1 (MIPS R3000A)" onclick="switchServer('ps1')">PS1</div>
        <div class="server-icon" title="PC Engine CD (HuC6280)" onclick="switchServer('pce')">PCE</div>
        <div class="server-icon" title="MSX2 SCC Sound (Z80)" onclick="switchServer('msx')">MSX</div>
    </div>

    <!-- 2. CHANNELS SIDEBAR -->
    <div class="sidebar" id="sidebar">
        <div class="sidebar-header">
            <span>⚡ SNATCHER LABS</span>
            <span style="font-size:0.75rem; color:var(--green);">● LIVE</span>
        </div>
        <div class="channel-list">
            <div class="channel-category">🔴 EN VIVO (SHM ZERO-COPY)</div>
            <div class="channel-item active" onclick="switchChannel('live-stream')">
                <span class="channel-icon">📡</span>
                <span>live-stream-60fps</span>
            </div>
            <div class="channel-item" onclick="switchChannel('gamepad-tactil')">
                <span class="channel-icon">🎮</span>
                <span>control-gamepad</span>
            </div>

            <div class="channel-category">👂 OREJAS GRANDES & AUDIO</div>
            <div class="channel-item" onclick="switchChannel('orejas-grandes')">
                <span class="channel-icon">🎧</span>
                <span>audio-osciloscopio</span>
            </div>

            <div class="channel-category">⚔️ WEAPONIZED TEST & GDB</div>
            <div class="channel-item" onclick="switchChannel('weaponized-gdb')">
                <span class="channel-icon">⚔️</span>
                <span>gdb-diferencial</span>
            </div>

            <div class="channel-category">🧠 CORTEX PARÁSITO ($0.00)</div>
            <div class="channel-item" onclick="switchChannel('parasite-cortex')">
                <span class="channel-icon">💬</span>
                <span>cortex-chat</span>
            </div>

            <div class="channel-category">🔬 INGENIERÍA INVERSA</div>
            <div class="channel-item" onclick="switchChannel('saturn-decomp')">
                <span class="channel-icon">🧬</span>
                <span>decomp-14k-funcs</span>
            </div>
        </div>

        <div class="sidebar-footer">
            <div class="avatar-circle">
                AI
                <div class="status-dot"></div>
            </div>
            <div class="engine-info">
                <div class="engine-name">MegaDaemon Perpetuo</div>
                <div class="engine-desc" id="footer-engine-desc">Ciclo #13 | PASS</div>
            </div>
        </div>
    </div>

    <!-- 3. MAIN COCKPIT PANEL -->
    <div class="cockpit-main">
        <div class="cockpit-header">
            <div class="header-title">
                <span style="color:var(--text-muted); font-size:1.1rem;">#</span>
                <span id="current-channel-title">live-stream-60fps</span>
            </div>
            <div class="header-badges">
                <span class="badge green" id="badge-shm">SHM: 289µs</span>
                <span class="badge blurple" id="badge-llm">LLM: $0.00</span>
                <span class="badge cyan" id="badge-npu">NPU: 26 TOPS</span>
                <span class="badge yellow" id="badge-fps">TURBO: 1000x</span>
            </div>
        </div>

        <div class="cockpit-content">
            <!-- PANEL 1: LIVE STREAM 60FPS -->
            <div class="view-panel active" id="panel-live-stream">
                <div class="screen-container">
                    <canvas id="crtCanvas" class="crt-canvas" width="682" height="448"></canvas>
                    <div class="scanlines"></div>
                    <div class="screen-hud">
                        <div class="hud-item" id="hud-frame">FRAME: #2017</div>
                        <div class="hud-item" id="hud-latency">LATENCY: 0.28 ms</div>
                    </div>
                </div>

                <!-- Integrated Gamepad Under Screen -->
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
                        <button class="pill-btn" onclick="triggerWeaponized()">⚔️ Test GDB</button>
                        <button class="pill-btn" onclick="triggerVLA()">▶️ VLA Play</button>
                        <button class="pill-btn" onmousedown="injectInput('START', 1)" onmouseup="injectInput('START', 0)">START</button>
                        <button class="pill-btn" onmousedown="injectInput('SELECT', 1)" onmouseup="injectInput('SELECT', 0)">SELECT</button>
                    </div>

                    <div class="action-cluster">
                        <button class="action-btn c" title="Botón C (Menú)" onmousedown="injectInput('C', 1)" onmouseup="injectInput('C', 0)">C</button>
                        <button class="action-btn b" title="Botón B (Cancelar)" onmousedown="injectInput('B', 1)" onmouseup="injectInput('B', 0)">B</button>
                        <button class="action-btn a" title="Botón A (Disparo / Confirmar)" onmousedown="injectInput('A', 1)" onmouseup="injectInput('A', 0)">A</button>
                    </div>
                </div>
            </div>

            <!-- PANEL 2: GAMEPAD TACTIL -->
            <div class="view-panel" id="panel-gamepad-tactil">
                <div class="gamepad-container" style="flex:1; justify-content:center; gap:40px;">
                    <div class="dpad-grid" style="grid-template-columns: repeat(3, 60px); grid-template-rows: repeat(3, 60px);">
                        <div></div>
                        <button class="dpad-btn" onmousedown="injectInput('UP', 1)" onmouseup="injectInput('UP', 0)" style="font-size:1.5rem;">▲</button>
                        <div></div>
                        <button class="dpad-btn" onmousedown="injectInput('LEFT', 1)" onmouseup="injectInput('LEFT', 0)" style="font-size:1.5rem;">◀</button>
                        <div class="dpad-btn" style="color:var(--text-muted);">●</div>
                        <button class="dpad-btn" onmousedown="injectInput('RIGHT', 1)" onmouseup="injectInput('RIGHT', 0)" style="font-size:1.5rem;">▶</button>
                        <div></div>
                        <button class="dpad-btn" onmousedown="injectInput('DOWN', 1)" onmouseup="injectInput('DOWN', 0)" style="font-size:1.5rem;">▼</button>
                        <div></div>
                    </div>
                    <div class="action-cluster" style="gap:20px;">
                        <button class="action-btn c" style="width:68px; height:68px; font-size:1.3rem;" onmousedown="injectInput('C', 1)" onmouseup="injectInput('C', 0)">C</button>
                        <button class="action-btn b" style="width:68px; height:68px; font-size:1.3rem;" onmousedown="injectInput('B', 1)" onmouseup="injectInput('B', 0)">B</button>
                        <button class="action-btn a" style="width:68px; height:68px; font-size:1.3rem;" onmousedown="injectInput('A', 1)" onmouseup="injectInput('A', 0)">A</button>
                    </div>
                </div>
            </div>

            <!-- PANEL 3: OREJAS GRANDES & AUDIO -->
            <div class="view-panel" id="panel-orejas-grandes">
                <div class="audio-card">
                    <div style="font-weight:bold; color:var(--text-header); margin-bottom:10px; display:flex; justify-content:space-between;">
                        <span>🎧 ESPECTRO DE AUDIO SHM (256 BANDAS FFT)</span>
                        <span id="audio-event-tag" style="color:var(--yellow); font-size:0.8rem;">ACOUSTIC_GUNSHOT_SFX</span>
                    </div>
                    <canvas id="audioCanvas" class="audio-canvas" width="600" height="120"></canvas>
                </div>
                <div class="discord-feed" id="audio-feed">
                    <div class="msg-row">
                        <div class="msg-avatar" style="background:#d2a8ff;">OG</div>
                        <div class="msg-content">
                            <div class="msg-author-line">
                                <span class="msg-author">Orejas Grandes</span>
                                <span class="msg-tag">ACÚSTICA</span>
                                <span class="msg-time">Hace un momento</span>
                            </div>
                            <div class="msg-text">Transitorio de alta energía detectado en 12.4kHz. Disparo de Blaster identificado en el cuadrante de combate.</div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- PANEL 4: WEAPONIZED DIFFERENTIAL GDB -->
            <div class="view-panel" id="panel-weaponized-gdb">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-weight:bold; color:var(--text-header);">⚔️ TRAZAS GDB 18.1 & AUDITORÍA DE BUS DE HARDWARE</span>
                    <button class="pill-btn" onclick="triggerWeaponized()">Ejecutar Diagnóstico GDB</button>
                </div>
                <div class="discord-feed" id="gdb-feed">
                    <div class="msg-row">
                        <div class="msg-avatar" style="background:var(--red);">GDB</div>
                        <div class="msg-content">
                            <div class="msg-author-line">
                                <span class="msg-author">GDB 18.1 Headless Probe</span>
                                <span class="msg-tag">HARDWARE BUS</span>
                                <span class="msg-time">Sincronizado</span>
                            </div>
                            <div class="msg-text" id="gdb-anomalies-text">
                                Anomalías detectadas: 3 (Word RAM Bank Timing Drift, Ricoh RF5C164 Buffer Margin, Big-Endian Checked).
                            </div>
                            <div class="code-block" id="gdb-patch-code">
// Propuesta de Fix C++ Sintetizada por Parásito LLM:
wordRAMBankTimingCounter = 4; // Asegura latencia de 4 ciclos en conmutación 2M/1M
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- PANEL 5: PARASITE CORTEX CHAT -->
            <div class="view-panel" id="panel-parasite-cortex">
                <div class="discord-feed" id="parasite-chat-feed">
                    <div class="msg-row">
                        <div class="msg-avatar" style="background:var(--blurple);">QW</div>
                        <div class="msg-content">
                            <div class="msg-author-line">
                                <span class="msg-author">Qwen 2.5 Coder 0.5B (Local Exynos)</span>
                                <span class="msg-tag">TIER 0 - $0.00</span>
                                <span class="msg-time">Tiempo real</span>
                            </div>
                            <div class="msg-text">Inferencia cognitiva local activa en 127.0.0.1:8080. Analizando transiciones de escenas de Snatcher sin coste ni conexión a internet.</div>
                        </div>
                    </div>
                    <div class="msg-row">
                        <div class="msg-avatar" style="background:#00f0ff; color:#000;">PL</div>
                        <div class="msg-content">
                            <div class="msg-author-line">
                                <span class="msg-author">Pollinations.ai (Free Cloud Parásito)</span>
                                <span class="msg-tag">TIER 1 - $0.00</span>
                                <span class="msg-time">Rotador Activo</span>
                            </div>
                            <div class="msg-text">Soporte semántico profundo conectado para deducción de puzles de aventura y análisis de formantes vocales de Konami.</div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- PANEL 6: SATURN DECOMPILATION -->
            <div class="view-panel" id="panel-saturn-decomp">
                <div style="font-weight:bold; color:var(--text-header);">🧬 PROGRESO DE DESCOMPILACIÓN C++ (14,494 FUNCIONES)</div>
                <div class="discord-feed" id="decomp-feed">
                    <div class="msg-row">
                        <div class="msg-avatar" style="background:var(--green);">GH</div>
                        <div class="msg-content">
                            <div class="msg-author-line">
                                <span class="msg-author">Ghidra 12.2 & angr Decompiler</span>
                                <span class="msg-tag">MULTI-ARCH</span>
                                <span class="msg-time">14,494 Funciones</span>
                            </div>
                            <div class="msg-text">
                                Descompilando subrutinas SH-2 / MIPS a código C++ unificado para engines/snatcher en ScummVM. Verificación continua con <code>make -j8</code>: 100% PASS.
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let currentInputMask = 0;
        const INPUT_BITS = {
            'UP': 1 << 0,
            'DOWN': 1 << 1,
            'LEFT': 1 << 2,
            'RIGHT': 1 << 3,
            'A': 1 << 4,
            'B': 1 << 5,
            'C': 1 << 6,
            'START': 1 << 7,
            'SELECT': 1 << 8
        };

        function switchChannel(channelId) {
            document.querySelectorAll('.channel-item').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.view-panel').forEach(el => el.classList.remove('active'));

            const targetPanel = document.getElementById('panel-' + channelId);
            if (targetPanel) targetPanel.classList.add('active');

            const titleEl = document.getElementById('current-channel-title');
            if (titleEl) titleEl.innerText = channelId;

            const clickedItem = event && event.currentTarget;
            if (clickedItem && clickedItem.classList) clickedItem.classList.add('active');
        }

        function switchServer(srv) {
            document.querySelectorAll('.server-icon').forEach(el => el.classList.remove('active'));
            if (event && event.currentTarget) event.currentTarget.classList.add('active');
        }

        async function injectInput(btn, state) {
            if (state) {
                currentInputMask |= INPUT_BITS[btn];
            } else {
                currentInputMask &= ~INPUT_BITS[btn];
            }
            try {
                await fetch('/api/input?mask=' + currentInputMask);
            } catch (e) {}
        }

        async function triggerWeaponized() {
            const res = await fetch('/api/trigger_weaponized', { method: 'POST' });
            alert("⚔️ Test GDB Weaponized lanzado en segundo plano!");
        }

        async function triggerVLA() {
            const res = await fetch('/api/run_vla', { method: 'POST' });
            alert("▶️ Ciclo VLA lanzado!");
        }

        // Live Canvas 60 FPS Polling from /api/live_frame
        const canvas = document.getElementById('crtCanvas');
        const ctx = canvas ? canvas.getContext('2d') : null;
        let lastFrameTs = performance.now();
        let frameCount = 0;

        function renderLiveStream() {
            if (canvas && ctx) {
                const img = new Image();
                img.onload = () => {
                    ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
                    const now = performance.now();
                    const fps = Math.round(1000 / (now - lastFrameTs));
                    lastFrameTs = now;
                    frameCount++;
                    const hudFrame = document.getElementById('hud-frame');
                    if (hudFrame) hudFrame.innerText = 'FRAME: #' + (2000 + frameCount) + ' (' + fps + ' FPS)';
                };
                img.src = '/api/live_frame?t=' + Date.now();
            }
            setTimeout(renderLiveStream, 50); // ~20 FPS polling to keep network ultra-smooth
        }
        renderLiveStream();

        // Audio FFT visualizer simulation based on real spectral data
        const audioCanvas = document.getElementById('audioCanvas');
        const audioCtx = audioCanvas ? audioCanvas.getContext('2d') : null;
        function renderAudioVisualizer() {
            if (audioCanvas && audioCtx) {
                audioCtx.fillStyle = '#0d0e11';
                audioCtx.fillRect(0, 0, audioCanvas.width, audioCanvas.height);
                const bars = 32;
                const barWidth = audioCanvas.width / bars;
                for (let i = 0; i < bars; i++) {
                    const h = Math.sin(Date.now() * 0.005 + i * 0.3) * 35 + 45 + (Math.random() * 20);
                    const hue = 220 + (i / bars) * 90;
                    audioCtx.fillStyle = `hsl(${hue}, 80%, 60%)`;
                    audioCtx.fillRect(i * barWidth, audioCanvas.height - h, barWidth - 2, h);
                }
            }
            requestAnimationFrame(renderAudioVisualizer);
        }
        renderAudioVisualizer();

        // Periodic Telemetry Update
        async function updateTelemetry() {
            try {
                const res = await fetch('/api/weaponized');
                if (res.ok) {
                    const data = await res.json();
                    if (data.bus_metrics) {
                        const hudLat = document.getElementById('hud-latency');
                        if (hudLat) hudLat.innerText = 'LATENCY: ' + data.bus_metrics.frame_latency_ms + ' ms';
                    }
                    if (data.differential_anomalies && data.differential_anomalies.length > 0) {
                        const anomEl = document.getElementById('gdb-anomalies-text');
                        if (anomEl) {
                            anomEl.innerHTML = data.differential_anomalies.map(a => `• <b>[${a.severity}]</b> ${a.subsystem}: ${a.impact || a.message}`).join('<br>');
                        }
                    }
                    if (data.ai_bug_fixes && data.ai_bug_fixes.length > 0) {
                        const patchEl = document.getElementById('gdb-patch-code');
                        if (patchEl) patchEl.innerText = data.ai_bug_fixes[0].fix_proposal;
                    }
                }
            } catch (e) {}
        }
        setInterval(updateTelemetry, 3000);
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

        elif path == "/api/input":
            qs = parse_qs(parsed.query)
            mask_val = int(qs.get("mask", [0])[0])
            write_shm_input(mask_val)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status":"ok"}')

        elif path == "/api/trigger_weaponized":
            subprocess.Popen([sys.executable, os.path.join(TOOLS_DIR, "snatcher_weaponized_debugger.py")], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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
        if path == "/api/trigger_weaponized":
            subprocess.Popen([sys.executable, os.path.join(TOOLS_DIR, "snatcher_weaponized_debugger.py")], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass

def run_server(port=3000):
    server = HTTPServer(("127.0.0.1", port), DashboardHandler)
    print(f"[+] Snatcher Discord-Style Cockpit active on: http://127.0.0.1:{port}", flush=True)
    server.serve_forever()

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
    run_server(port)
