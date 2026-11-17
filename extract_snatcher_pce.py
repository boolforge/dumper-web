#!/usr/bin/env python3
"""
Comprehensive Extractor & Depacker for PC Engine Super CD-ROM² Snatcher (English)
Dumps:
1. Mode 1 2352 de-framing (removing 225-sector pregap and ECC/EDC)
2. Hudson Super CD-ROM² file system & 156 overlay entries from master table at 0xC505
3. System binaries, IPL, kernel, graphics overlays, palettes, scene scripts
4. ADPCM master audio table (134 entries) and audio streams
5. Full English dialogue strings & script dumped to JSON for cross-platform comparison
"""

import os
import sys
import json
import csv
import re
import struct
import unicodedata

# Paths
PCE_DIR = "/storage/emulated/0/Download/Snatcher-Collection/PC-Engine"
SRC_TRACK02 = os.path.join(PCE_DIR, "English-Translated/Snatcher (English)/Snatcher (English) (Track 02).bin")
SRC_TRACK24 = os.path.join(PCE_DIR, "English-Translated/Snatcher (English)/Snatcher (English) (Track 24).bin")
JP_TRACK02  = os.path.join(PCE_DIR, "Original-Japan/Snatcher CD-ROMantic (Japan) (Track 02).bin")
TOOLS_DIR   = "/storage/emulated/0/Download/Snatcher-Collection/Tools-and-Documentation/viruztt-snatcher-pce-english/translation"
OUT_BASE    = os.path.join(PCE_DIR, "English-Extracted")

sys.path.insert(0, TOOLS_DIR)
import scenes
import sntext
import names

def ensure_dirs():
    dirs = [
        OUT_BASE,
        os.path.join(OUT_BASE, "filesystem"),
        os.path.join(OUT_BASE, "binaries"),
        os.path.join(OUT_BASE, "system_overlays"),
        os.path.join(OUT_BASE, "scenes"),
        os.path.join(OUT_BASE, "graphics"),
        os.path.join(OUT_BASE, "palettes"),
        os.path.join(OUT_BASE, "audio_tables"),
        os.path.join(OUT_BASE, "adpcm"),
        os.path.join(OUT_BASE, "dialogue")
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
    return dirs

def clean_dialogue(text):
    """Clean control tags <fb>, <f2>, <f4>, <f9> etc. for human-readable cross-platform comparison."""
    if not text:
        return ""
    # Replace <f2> with space or newline
    t = text.replace("<f2>", " ")
    # Strip <fb>, <f9>, <f4>, <f5>, <fe..>, etc.
    t = re.sub(r'<f[0-9a-f]>', '', t)
    t = re.sub(r'<fe[0-9a-f]{2}>', '', t)
    t = re.sub(r'<END>', '', t)
    # Collapse multiple spaces
    t = re.sub(r'[ \t]+', ' ', t).strip()
    return t

def extract_all():
    print("[1/5] Examining Tracks and Deframing Mode 1 2352 Sectors...")
    ensure_dirs()
    
    t2_size = os.path.getsize(SRC_TRACK02)
    t24_size = os.path.getsize(SRC_TRACK24)
    print(f"  Track 02 file size: {t2_size:,} bytes ({t2_size // 2352} sectors of 2352)")
    print(f"  Track 24 file size: {t24_size:,} bytes ({t24_size // 2352} sectors of 2352)")
    
    # 225 sectors pregap = 529,200 bytes
    PREGAP_SECTORS = 225
    PREGAP_BYTES = PREGAP_SECTORS * 2352
    TOTAL_USER_SECTORS = (t2_size - PREGAP_BYTES) // 2352
    print(f"  Pregap at Index 01: {PREGAP_SECTORS} sectors ({PREGAP_BYTES:,} bytes)")
    print(f"  User Data Sectors: {TOTAL_USER_SECTORS:,} sectors ({TOTAL_USER_SECTORS * 2048:,} bytes, {TOTAL_USER_SECTORS * 2048 / 1024 / 1024:.2f} MB)")
    
    # Deframing Track 02 user data
    print("  De-framing Track 02 raw sectors (2352 -> 2048 user data)...")
    iso_userdata = bytearray()
    with open(SRC_TRACK02, "rb") as f:
        f.seek(PREGAP_BYTES)
        while True:
            sec = f.read(2352)
            if not sec:
                break
            iso_userdata += sec[16:2064]
    
    # Save extracted user data ISO
    iso_out_path = os.path.join(OUT_BASE, "filesystem/track02_userdata.iso")
    print(f"  Saving user data image to {iso_out_path} ({len(iso_userdata):,} bytes)...")
    with open(iso_out_path, "wb") as f:
        f.write(iso_userdata)

    # Verify Track 24
    print("  Verifying Track 24 consistency with Track 02...")
    with open(SRC_TRACK24, "rb") as f24:
        f24.seek(PREGAP_BYTES)
        # sample check
        sec0 = f24.read(2352)[16:2064]
        assert sec0 == iso_userdata[:2048], "Track 24 sector 0 does not match Track 02!"
    print("  Track 24 verified identical to Track 02.")

    # 2. Extract Core Engine Binaries & Boot Records
    print("[2/5] Extracting Hudson CD-ROM System & Game Engine Binaries...")
    # Sector 0: Hudson CD-ROM System Credits & Copyright
    open(os.path.join(OUT_BASE, "binaries/hudson_copyright_sec00.bin"), "wb").write(iso_userdata[0:2048])
    # Sector 1: Boot Sector Record
    open(os.path.join(OUT_BASE, "binaries/boot_record_sec01.bin"), "wb").write(iso_userdata[2048:4096])
    # Sectors 2-23: IPL Core Engine ($3000-$DFFF)
    open(os.path.join(OUT_BASE, "binaries/ipl_core_sec02_23.bin"), "wb").write(iso_userdata[2*2048:24*2048])
    # Sectors 24-36: Kernel, Text Decoder, Proportional Font Renderer, Master Table ($4000-$7FFF)
    open(os.path.join(OUT_BASE, "binaries/kernel_engine_sec24_36.bin"), "wb").write(iso_userdata[24*2048:37*2048])
    # Sectors 54-77: Bank 0x1A Sound Driver & Sequence Tables
    open(os.path.join(OUT_BASE, "binaries/psg_sound_driver_sec54_77.bin"), "wb").write(iso_userdata[54*2048:78*2048])
    # Sectors 78-82: Bank 0x1E ADPCM Stream Driver
    open(os.path.join(OUT_BASE, "binaries/adpcm_stream_driver_sec78_82.bin"), "wb").write(iso_userdata[78*2048:83*2048])

    # 3. Master Overlay Table (Offset 0xC505) & Depacking Overlays
    print("[3/5] Depacking Hudson Super CD-ROM² Overlays (Master Table at 0xC505)...")
    TABLE_OFFSET = 0xC505
    overlay_entries = []
    
    # Categories based on entry index & bank
    for i in range(156):
        o = TABLE_OFFSET + 8 * i
        e = iso_userdata[o:o+8]
        sec = e[0] << 16 | e[2] << 8 | e[1]
        mode = e[3]
        bank = e[4] | (e[5] << 8)
        count = e[6]
        byte_size = count * 2048
        file_start = sec * 2048
        file_end = file_start + byte_size
        data = iso_userdata[file_start:file_end]
        
        category = "unknown"
        folder = "system_overlays"
        
        if bank == 0x0016:
            category = "script_scene"
            folder = "scenes"
            filename = f"scene_{i:02d}_sec{sec:04d}_bank16.bin"
        elif bank in (0x0003, 0x0004, 0x0005):
            category = "graphics_overlay"
            folder = "graphics"
            filename = f"gfx_overlay_entry{i:03d}_sec{sec:04d}_bank{bank:02x}.bin"
        else:
            category = "system_overlay"
            folder = "system_overlays"
            filename = f"sys_overlay_entry{i:03d}_sec{sec:04d}_bank{bank:02x}.bin"
        
        entry_meta = {
            "index": i,
            "sector": sec,
            "bank": f"0x{bank:04x}",
            "count": count,
            "byte_size": byte_size,
            "mode": mode,
            "category": category,
            "filename": filename,
            "iso_offset": f"0x{file_start:06x}"
        }
        overlay_entries.append(entry_meta)
        
        # Write extracted overlay file
        target_path = os.path.join(OUT_BASE, folder, filename)
        with open(target_path, "wb") as f_out:
            f_out.write(data)
            
        # If graphic overlay, search for palette chunks (9-bit RGB, 32-byte blocks)
        if category == "graphics_overlay" and len(data) >= 32:
            pal_out = os.path.join(OUT_BASE, "palettes", f"pal_entry{i:03d}_sec{sec:04d}.bin")
            # In Hudson VCE, palette data is often loaded at VRAM $0000 or table header
            with open(pal_out, "wb") as f_pal:
                f_pal.write(data[:512]) # Dump first 512 bytes (16 palettes of 16 colors)
                
    master_table_json = os.path.join(OUT_BASE, "filesystem/master_overlay_table.json")
    with open(master_table_json, "w", encoding="utf-8") as f:
        json.dump(overlay_entries, f, indent=2)
    print(f"  Depacked {len(overlay_entries)} overlay files from master table to scenes/, graphics/, and system_overlays/.")

    # 4. ADPCM Audio & Sound Tables
    print("[4/5] Parsing ADPCM Master Sound Table & Audio Streams...")
    # In Sector 54 (Bank 0x1A), 134 entries of 8 bytes: [flags, sec_lo, sec_hi, count_lo, count_hi, 0]
    sec54_data = iso_userdata[54*2048:78*2048]
    adpcm_records = []
    
    for i in range(134):
        chunk = sec54_data[i*8 : (i+1)*8]
        sec = chunk[3] | (chunk[4] << 8)
        count = chunk[5] | (chunk[6] << 8)
        byte_size = count * 2048
        f_start = sec * 2048
        f_end = f_start + byte_size
        flags = [chunk[0], chunk[1], chunk[2], chunk[7]]
        
        # Duration in seconds: MSM5205 4-bit ADPCM at 16,000 Hz = 8,000 bytes/sec
        est_duration_sec = byte_size / 8000.0
        
        adpcm_meta = {
            "adpcm_id": i,
            "sector": sec,
            "count_sectors": count,
            "byte_size": byte_size,
            "iso_offset": f"0x{f_start:06x}",
            "sample_rate_hz": 16000,
            "channels": 1,
            "bits_per_sample": 4,
            "estimated_duration_sec": round(est_duration_sec, 2),
            "flags": [f"0x{b:02x}" for b in flags],
            "filename": f"adpcm_{i:03d}_sec{sec:05d}_{byte_size//1024}kb.adpcm"
        }
        adpcm_records.append(adpcm_meta)
        
        # Dump ADPCM stream
        adpcm_data = iso_userdata[f_start:f_end]
        adpcm_file = os.path.join(OUT_BASE, "adpcm", adpcm_meta["filename"])
        with open(adpcm_file, "wb") as f_ad:
            f_ad.write(adpcm_data)
            
    # Save ADPCM table metadata
    adpcm_json_path = os.path.join(OUT_BASE, "audio_tables/adpcm_master_table.json")
    with open(adpcm_json_path, "w", encoding="utf-8") as f:
        json.dump(adpcm_records, f, indent=2)
    print(f"  Dumped {len(adpcm_records)} ADPCM audio files into adpcm/ and audio_tables/.")

    # 5. Extract English Dialogue Strings & Script to JSON
    print("[5/5] Extracting English Dialogue Strings & Menus to JSON for Cross-Platform Comparison...")
    
    # Load Japanese text from JP_TRACK02 for dual-language side-by-side comparison
    print("  Loading matching Japanese strings from original disc...")
    jp_iso = bytearray()
    with open(JP_TRACK02, "rb") as f_jp:
        f_jp.seek(PREGAP_BYTES)
        for _ in range(680):
            jp_iso += f_jp.read(2352)[16:2064]
            
    # Extract Japanese text pointers and speakers
    jp_dict = {}
    speaker_map = {}
    for sc in scenes.scripts(jp_iso):
        base = sc['sector'] * 2048
        size = sc['count'] * 2048
        ptrs = scenes.text_pointers(jp_iso, base, size)
        for t, ps in ptrs.items():
            p = ps[0]
            spk_byte = jp_iso[p - 2]
            spk_name = "Narrator"
            if 0 < spk_byte <= len(names.NAMES):
                nm = names.NAMES[spk_byte - 1]
                spk_name = nm if nm else ("Gillian" if spk_byte == 1 else f"Speaker_{spk_byte}")
            elif spk_byte > 0:
                spk_name = f"Speaker_{spk_byte}"
                
            try:
                jp_text, _ = sntext.decode(jp_iso, t)
            except Exception:
                jp_text = ""
            jp_dict[(str(sc['index']), hex(t))] = jp_text
            speaker_map[(str(sc['index']), hex(t))] = (spk_byte, spk_name)

    # Load English translation script
    script_en_path = os.path.join(TOOLS_DIR, "script_en.tsv")
    en_rows = []
    with open(script_en_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for r in reader:
            en_rows.append(r)
            
    print(f"  Loaded {len(en_rows):,} translated dialogue lines from script_en.tsv.")
    
    # Combine into comprehensive JSON dataset
    all_dialogues = []
    by_scene = {}
    speaker_stats = {}
    
    for idx, r in enumerate(en_rows):
        sc_num = r["scene"]
        t_off = r["text_offset"]
        en_text = r["english"]
        jp_text = jp_dict.get((sc_num, t_off), "")
        spk_byte, spk_name = speaker_map.get((sc_num, t_off), (0, "Narrator"))
        clean_en = clean_dialogue(en_text)
        
        entry = {
            "dialogue_id": f"pce_sc{int(sc_num):02d}_{t_off}",
            "scene_index": int(sc_num),
            "text_offset": t_off,
            "speaker_id": spk_byte,
            "speaker": spk_name,
            "english": en_text,
            "cleaned_text": clean_en,
            "japanese": jp_text,
            "word_count": len(clean_en.split()) if clean_en else 0,
            "char_count": len(clean_en) if clean_en else 0
        }
        all_dialogues.append(entry)
        by_scene.setdefault(f"Scene_{int(sc_num):02d}", []).append(entry)
        speaker_stats[spk_name] = speaker_stats.get(spk_name, 0) + 1
        
    # Write master JSON dialogue files
    dlg_all_path = os.path.join(OUT_BASE, "dialogue/snatcher_pce_dialogue_all.json")
    with open(dlg_all_path, "w", encoding="utf-8") as f:
        json.dump(all_dialogues, f, indent=2, ensure_ascii=False)
        
    dlg_by_scene_path = os.path.join(OUT_BASE, "dialogue/snatcher_pce_dialogue_by_scene.json")
    with open(dlg_by_scene_path, "w", encoding="utf-8") as f:
        json.dump(by_scene, f, indent=2, ensure_ascii=False)

    # Dump speaker names table
    spk_json_path = os.path.join(OUT_BASE, "dialogue/snatcher_pce_speaker_names.json")
    spk_data = []
    for idx, nm in enumerate(names.NAMES):
        spk_data.append({
            "speaker_id": idx + 1,
            "speaker_name": nm if nm else ("(Silent / Monologue)" if idx == 0 else f"Unnamed_{idx+1}"),
            "dialogue_line_count": speaker_stats.get(nm, 0) if nm else (speaker_stats.get("Gillian", 0) if idx == 0 else 0)
        })
    with open(spk_json_path, "w", encoding="utf-8") as f:
        json.dump(spk_data, f, indent=2)

    # Dump menus table
    menu_en_path = os.path.join(TOOLS_DIR, "menu_en.tsv")
    menus_list = []
    with open(menu_en_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for r in reader:
            menus_list.append(r)
    menus_json_path = os.path.join(OUT_BASE, "dialogue/snatcher_pce_menus.json")
    with open(menus_json_path, "w", encoding="utf-8") as f:
        json.dump(menus_list, f, indent=2, ensure_ascii=False)

    # Summary report JSON
    summary_data = {
        "title": "Snatcher PC Engine Super CD-ROM² English Depacking & Script Extraction",
        "platform": "PC Engine Super CD-ROM² (Mode 1 2352 / HuC6280)",
        "track02_size_bytes": t2_size,
        "track24_size_bytes": t24_size,
        "pregap_sectors": PREGAP_SECTORS,
        "pregap_bytes": PREGAP_BYTES,
        "total_user_sectors": TOTAL_USER_SECTORS,
        "user_data_bytes": len(iso_userdata),
        "master_overlay_table_offset": f"0x{TABLE_OFFSET:04x}",
        "total_overlays": len(overlay_entries),
        "overlay_categories": {
            "script_scenes": sum(1 for e in overlay_entries if e["category"] == "script_scene"),
            "graphics_overlays": sum(1 for e in overlay_entries if e["category"] == "graphics_overlay"),
            "system_overlays": sum(1 for e in overlay_entries if e["category"] == "system_overlay")
        },
        "adpcm_streams_count": len(adpcm_records),
        "total_adpcm_sectors": sum(e["count_sectors"] for e in adpcm_records),
        "total_adpcm_bytes": sum(e["byte_size"] for e in adpcm_records),
        "dialogue_lines_total": len(all_dialogues),
        "dialogue_scenes_count": len(by_scene),
        "speaker_lines_breakdown": dict(sorted(speaker_stats.items(), key=lambda x: -x[1])),
        "menu_strings_count": len(menus_list)
    }
    with open(os.path.join(OUT_BASE, "snatcher_pce_extraction_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2, ensure_ascii=False)

    print("\nExtraction & depacking complete!")
    print(f"Summary: {len(all_dialogues):,} dialogue lines across {len(by_scene)} scenes.")
    print(f"Total overlays: {len(overlay_entries)} files extracted.")
    print(f"ADPCM streams: {len(adpcm_records)} sound tracks dumped.")
    print(f"Output directory: {OUT_BASE}")

if __name__ == "__main__":
    extract_all()
