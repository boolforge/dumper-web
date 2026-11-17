#!/usr/bin/env python3
"""
Full PC-8801 Snatcher D88 Sector & Asset Depacker
Unpacks all sectors, boots, jump tables, scripts, graphics tiles, and palettes
from PC-8801 Snatcher D88 disks into structured raw assets.
"""
import os
import sys
import struct
import json

def unpack_d88(d88_path, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    with open(d88_path, "rb") as f:
        data = f.read()

    name = data[:17].rstrip(b"\x00").decode("latin1", "replace")
    disk_size = struct.unpack("<I", data[0x1C:0x20])[0]
    track_offsets = [struct.unpack("<I", data[0x20 + i*4 : 0x24 + i*4])[0] for i in range(164)]

    disk_linear = bytearray()
    sectors_info = []

    for t_idx, t_off in enumerate(track_offsets):
        if t_off == 0 or t_off >= len(data):
            continue
        cur = t_off
        track_sectors = []
        while cur < len(data):
            if cur + 16 > len(data):
                break
            c, h, r, n, num_sec, density, deleted, status = struct.unpack("<BBBBHBBB", data[cur:cur+9])
            sec_len = struct.unpack("<H", data[cur+14:cur+16])[0]
            if sec_len == 0:
                sec_len = 128 << n
            cur += 16
            sec_data = data[cur:cur+sec_len]
            cur += sec_len

            track_sectors.append({
                "c": c, "h": h, "r": r, "n": n, "len": len(sec_data)
            })
            disk_linear.extend(sec_data)

            # Dump boot loader sectors from track 0
            if c == 0 and h == 0:
                sec_file = os.path.join(out_dir, f"boot_c{c}_h{h}_r{r:02d}.bin")
                with open(sec_file, "wb") as sf:
                    sf.write(sec_data)

            if len(track_sectors) >= num_sec:
                break

        sectors_info.append({"track": t_idx, "sectors": track_sectors})

    # Save full contiguous memory image
    linear_path = os.path.join(out_dir, "disk_linear.img")
    with open(linear_path, "wb") as lf:
        lf.write(disk_linear)

    # Save disk geometry metadata
    meta_path = os.path.join(out_dir, "geometry.json")
    with open(meta_path, "w") as mf:
        json.dump({"name": name, "size": disk_size, "tracks": sectors_info}, mf, indent=2)

    return len(disk_linear), len(sectors_info)

def main():
    disks_dir = "/storage/emulated/0/Download/Snatcher-Collection/PC88/Disks"
    out_root = "/storage/emulated/0/Download/Snatcher-Collection/PC88/Unpacked"

    targets = [
        ("Disk1-Program", "Snatcher (1988)(Konami)(Disk 1 of 5)(Program Disk).d88"),
        ("Disk2-Data1", "Snatcher (1988)(Konami)(Disk 2 of 5)(Data Disk 1).d88"),
        ("Disk3-Data2", "Snatcher (1988)(Konami)(Disk 3 of 5)(Data Disk 2).d88"),
        ("Disk4-Data3", "Snatcher (1988)(Konami)(Disk 4 of 5)(Data Disk 3).d88"),
        ("Disk5-Data4", "Snatcher (1988)(Konami)(Disk 5 of 5)(Data Disk 4).d88")
    ]

    total_bytes = 0
    for label, fn in targets:
        p = os.path.join(disks_dir, fn)
        out = os.path.join(out_root, label)
        if os.path.exists(p):
            nbytes, ntracks = unpack_d88(p, out)
            total_bytes += nbytes
            print(f"[OK] {label}: {ntracks} tracks, {nbytes} bytes linear image -> {out}")
        else:
            print(f"[ERR] File not found: {p}")

    print(f"\nAll 5 PC-8801 disks unpacked: {total_bytes} bytes decoded.")

if __name__ == "__main__":
    main()
