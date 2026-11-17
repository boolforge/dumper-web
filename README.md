# ScummVM Dumper Companion Web Edition

Browser-based WebAssembly deployment of ScummVM's official `dumper-companion.py` disc preservation utility.

Runs entirely client-side via Pyodide (`v0.25.0`) WebAssembly in standard web browsers with zero server-side uploads or external dependencies.

---

## Key Features

- **Multi-File Staging & Drag-and-Drop:**
  Select or drag & drop multiple files simultaneously (`.cue` + `.bin`, `.bin.ecm`, `.img`, `.mds`). All companion tracks are automatically staged into Pyodide virtual memory, and the primary descriptor file is automatically selected.

- **ScummVM AudioCDManager CDDA Compatibility:**
  Dumps Red Book audio tracks to standard WAV format and automatically synthesizes ScummVM-compatible aliases:
  - 0-indexed music stream (`track01.wav` for CDDA audio track 2)
  - 1-indexed CD track number (`track02.wav`)
  - Canonical full filenames (`<cue_stem>_track_02.wav`)
  This guarantees immediate compatibility with ScummVM engines relying on `AudioCDManager` (such as the Snatcher engine).

- **Native ECM (Error Code Modeler) Support:**
  Integrated pure-Python UNECM decoder supporting Mode 1, Mode 2 Form 1, Mode 2 Form 2, and literal sectors. Supports direct ISO sector streaming from ECM containers without requiring multi-hundred-megabyte intermediate raw files in memory.

- **Resilient CUE Companion Resolution:**
  Resolves case discrepancies, Windows path backslashes, track number conventions (`Track 01`), `.ecm` / `.bin.ecm` extensions, and single-candidate directory fallbacks.

- **Comprehensive Disc Architecture Support:**
  - **PlayStation / Sega CD / PC Engine CD:** CUE/BIN, CloneCD CCD/IMG, and Alcohol 120% MDS/MDF.
  - **Panasonic 3DO:** Full OperaFS filesystem extraction and multi-track detection.
  - **Macintosh HFS / HFS+:** Classic Mac disc images (`.dsk`, `.img`, `.iso`, `.toast`) and MacBinary encoding.
  - **Hybrid Discs:** Simultaneous extraction of dual HFS and ISO9660 partitions.

- **Zero Data Leakage:**
  All sector parsing, ISO9660 reading, and ZIP creation execute locally inside the browser WebAssembly environment.

---

## Snatcher (Sega CD & PlayStation) Preservation

This tool is optimized for preparing game media for ScummVM's Snatcher engine (`engines/snatcher`, merged in upstream ScummVM master):

1. **Sega CD Snatcher:**
   - Drop `Snatcher (Sega CD) (U)-redump.cue` alongside `Snatcher (Sega CD) (U)-redump.bin`.
   - The extractor parses Track 01 (ISO9660) and outputs all required game resource files (`DATA_B0.BIN`, `SP05.BIN`, etc.).
   - All 20 Red Book CDDA audio tracks (Tracks 02–21) are extracted to WAV and aliased as `track01.wav` through `track20.wav`, ready for ScummVM's audio subsystem.

2. **PlayStation Snatcher:**
   - Drop `Snatcher (Japan) [SLPS-00154].cue` alongside `Track 01.bin.ecm`.
   - The tool automatically matches the companion ECM image, decompresses the Mode 2 Form 1 sectors on the fly, and generates the ISO9660 artifact containing `SLPS_001.54` and directory trees.

---

## Quickstart

Run a lightweight static HTTP server in the repository root:

```bash
# Python 3
python3 -m http.server 8000
```

Open `http://127.0.0.1:8000` in any modern web browser.

---

## Command Line Usage

`dumper-companion.py` can also be executed directly via Python:

```bash
# Extract files from CUE sheet to output directory
python3 dumper-companion.py iso game.cue output_dir/

# Probe disc filesystem and metadata
python3 dumper-companion.py probe game.iso

# Decompress ECM disc image to raw BIN
python3 dumper-companion.py unecm input.bin.ecm output.bin
```

---

## License

GPLv2+ (consistent with ScummVM and `dumper-companion.py`).
See [ScummVM](https://www.scummvm.org/) for licensing terms.