import os
import json
import re

root = "/storage/emulated/0/Download/Snatcher-Collection"
corpus_dir = os.path.join(root, "Universal-Script-Corpus")
os.makedirs(corpus_dir, exist_ok=True)

stats = {}

# 1. Sega CD Spanish
scd_es_path = os.path.join(root, "SegaCD", "Spanish-Translation", "sega_cd_spanish_dialogue.json")
if os.path.exists(scd_es_path):
    with open(scd_es_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        total = sum(len(v) for v in data.values())
        stats["Sega CD (Spanish)"] = {"modules": len(data), "lines": total}

# 2. Sega CD USA
scd_en_dir = os.path.join(root, "SegaCD", "Original-USA")
scd_en_lines = 0
scd_en_data = {}
for i in range(39):
    fn = f"SP{i:02d}.BIN"
    p = os.path.join(scd_en_dir, fn)
    if os.path.exists(p):
        with open(p, "rb") as f:
            raw = f.read()
            s = [x.decode("latin1") for x in re.findall(b"[\x20-\x7e]{4,}", raw) if " " in x.decode("latin1")]
            scd_en_data[fn] = s
            scd_en_lines += len(s)
stats["Sega CD (USA English)"] = {"modules": len(scd_en_data), "lines": scd_en_lines}

# 3. PC Engine
pce_path = os.path.join(root, "PC-Engine", "English-Extracted", "dialogue", "snatcher_pce_dialogue_all.json")
if os.path.exists(pce_path):
    with open(pce_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        stats["PC Engine Super CD (English)"] = {"modules": 33, "lines": len(data)}

# 4. PlayStation 1
ps1_path = os.path.join(root, "PlayStation", "English-Translated", "ps1_english_dialogue.json")
if os.path.exists(ps1_path):
    with open(ps1_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        total = sum(len(v) for v in data.values())
        stats["PlayStation 1 (English v1.5.1)"] = {"modules": len(data), "lines": total}

# 5. Sega Saturn
sat_path = os.path.join(root, "Sega-Saturn", "Extracted-Files", "dialogue", "saturn_english_script.json")
if os.path.exists(sat_path):
    with open(sat_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        line_count = len(data) if isinstance(data, list) else sum(len(v) for v in data.values())
        stats["Sega Saturn (English)"] = {"modules": 1, "lines": line_count}

# 6. PC-8801
pc88_dir = os.path.join(root, "PC88", "Extracted-Assets")
pc88_lines = 0
if os.path.exists(pc88_dir):
    for d in os.listdir(pc88_dir):
        sp = os.path.join(pc88_dir, d, "strings.json")
        if os.path.exists(sp):
            with open(sp, "r", encoding="utf-8") as f:
                lines = json.load(f)
                pc88_lines += len(lines)
stats["PC-8801 mkIISR (Japanese)"] = {"modules": 5, "lines": pc88_lines}

summary_file = os.path.join(corpus_dir, "corpus_summary.json")
with open(summary_file, "w", encoding="utf-8") as f:
    json.dump(stats, f, indent=2)

print("=====================================================================")
print("UNIVERSAL SNATCHER MULTIPLATFORM CORPUS SUMMARY")
print("=====================================================================")
grand_total = 0
for plat, info in stats.items():
    m_count = info["modules"]
    l_count = info["lines"]
    grand_total += l_count
    print(f"  {plat:35}: {m_count:4d} modules | {l_count:6d} dialogue lines")
print("---------------------------------------------------------------------")
print(f"  TOTAL ALIGNED MULTIPLATFORM STRINGS: {grand_total} lines")
print("=====================================================================")
