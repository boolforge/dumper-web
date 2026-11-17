# dumper-companion backlog

Limitations found while unpacking every Snatcher port. Each item should land as one atomic commit with tests.

1. **Raw CD sectors in `iso`:** accept MODE1/2352 and MODE2/2352 (PS1, Saturn, PC Engine, Sega CD). `extract_raw_cd.py` is the prototype to fold in.
2. **CHD v5 reader:** pure-Python cdlz/cdzl/cdfl decoder so `.chd` and CHD embedded in `.cia` can be depacked without `chdman`.
3. **3DS `.cia` / NCCH / RomFS:** locate and extract embedded payloads (the Sega CD Spanish release).
4. **Non-FAT D88 (PC-8801):** read physical sector IDs, mixed geometry (track 0 = 16x256 B, others 5x1024 B), dump the raw linear image and per-track chunks.
5. **CUE/BIN multi-track:** handle CUE sheets, pregaps, audio tracks and PCE Super CD-ROM2 layout (ISO starts at a 225-sector pregap).
6. **Mode2 Form1/Form2 awareness:** keep XA Form2 streams (`.XA`, `.STR`) intact and report them.
7. **ECM input:** transparent `.ecm` decoding.
8. **xdelta/IPS/BPS patch application** with optional checksum bypass and a post-patch hash report.
9. **Output manifest:** emit `manifest.json` (path, LBA, size, MD5) per extraction.
10. **Tests:** pytest fixtures for each format above, with synthetic small images.
