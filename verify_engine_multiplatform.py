import os

collection_root = "/storage/emulated/0/Download/Snatcher-Collection"

platforms = [
    {
        "title": "Sega CD USA (Original)",
        "path": os.path.join(collection_root, "SegaCD", "Original-USA"),
        "key_file": "DATA_B0.BIN",
        "scene_file": "SP05.BIN",
        "type": "Sega CD Mode 1 ISO"
    },
    {
        "title": "Sega CD Spanish (Spatcher)",
        "path": os.path.join(collection_root, "SegaCD", "Spanish-Translation", "Extracted-Files"),
        "key_file": "DATA_B0.BIN",
        "scene_file": "SP05.BIN",
        "type": "Sega CD Spanish Mod"
    },
    {
        "title": "PlayStation 1 English v1.5.1",
        "path": os.path.join(collection_root, "PlayStation", "English-Translated", "Extracted-Files"),
        "key_file": "SLPS_001.54",
        "scene_file": os.path.join("DES", "CPT", "CPT_B000.BIN"),
        "type": "PSX Mode 2 XA Form 1/2"
    },
    {
        "title": "PlayStation 1 Spanish (ElOtroLado)",
        "path": os.path.join(collection_root, "PlayStation", "Spanish-Translation", "Extracted-Files"),
        "key_file": "SLPS_001.54",
        "scene_file": os.path.join("DES", "CPT", "CPT_B000.BIN"),
        "type": "PSX Spanish Translation"
    },
    {
        "title": "PlayStation 1 Uncensored Restoration",
        "path": os.path.join(collection_root, "PlayStation", "Uncensored-Restoration", "Extracted-Files"),
        "key_file": "SLPS_001.54",
        "scene_file": os.path.join("DES", "CPT", "CPT_B000.BIN"),
        "type": "PSX Uncensored Restored"
    },
    {
        "title": "PC Engine Super CD-ROM2 English",
        "path": os.path.join(collection_root, "PC-Engine", "English-Extracted"),
        "key_file": "snatcher_pce_extraction_summary.json",
        "scene_file": os.path.join("scenes", "scene_06_sec0158_bank16.bin"),
        "type": "Hudson Super CD-ROM2 Card 3.0"
    },
    {
        "title": "Sega Saturn English Translated",
        "path": os.path.join(collection_root, "Sega-Saturn", "English-Translated"),
        "key_file": "MAIN_L.BIN",
        "scene_file": "DATA.BIN",
        "type": "Saturn Dual SH-2 Disc Set"
    },
    {
        "title": "MSX2 English Translated",
        "path": os.path.join(collection_root, "MSX2", "English-Translated"),
        "key_file": "SNATCHER_EN.DSK",
        "scene_file": "DISK0.dsk",
        "type": "MSX2 Z80 + SCC Floppy / HardDisk"
    },
    {
        "title": "PC-8801 Japanese (Unpacked)",
        "path": os.path.join(collection_root, "PC88", "Unpacked", "Disk1-Program"),
        "key_file": "disk_linear.img",
        "scene_file": "boot_c0_h0_r01.bin",
        "type": "PC-8801 mkIISR Z80 OPN Floppy"
    }
]

print("=====================================================================")
print("SNATCHER MULTIPLATFORM ENGINE VERIFICATION TEST SUITE")
print("=====================================================================")

all_passed = True
for p in platforms:
    title_str = p["title"]
    type_str = p["type"]
    kf = os.path.join(p["path"], p["key_file"])
    sf = os.path.join(p["path"], p["scene_file"])
    
    kf_ok = os.path.exists(kf)
    sf_ok = os.path.exists(sf)
    
    if kf_ok and sf_ok:
        kf_sz = os.path.getsize(kf)
        sf_sz = os.path.getsize(sf)
        print(f"[PASS] {title_str:38} | {type_str:30}")
        print(f"       Signature : {p['key_file']} ({kf_sz} bytes)")
        print(f"       Scene     : {p['scene_file']} ({sf_sz} bytes)")
    else:
        all_passed = False
        print(f"[FAIL] {title_str:38} | Missing files: kf={kf_ok}, sf={sf_ok}")

print("=====================================================================")
if all_passed:
    print("STATUS: 100% OF SNATCHER PLATFORM PORTS VERIFIED & RESOLVABLE.")
else:
    print("STATUS: VERIFICATION ENCOUNTERED MISSING MODULES.")
