#!/usr/bin/env python3
"""Extract files from a raw CD image (2048/2352 bytes per sector) with an ISO9660 filesystem.

Supports MODE1/2048, MODE1/2352 (data at +16) and MODE2/2352 (data at +24).
Usage: python extract_raw_cd.py <image.bin> <output_dir> [--list]
"""
import os
import struct
import sys

SYNC = b"\x00\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00"


def detect_layout(f):
    """Return (sector_size, data_offset) by looking for the ISO9660 PVD at LBA 16."""
    for ssize, off in ((2048, 0), (2352, 16), (2352, 24)):
        f.seek(16 * ssize + off)
        if f.read(6) == b"\x01CD001":
            return ssize, off
    raise ValueError("No ISO9660 primary volume descriptor found at LBA 16")


class Image:
    def __init__(self, path):
        self.f = open(path, "rb")
        self.ssize, self.off = detect_layout(self.f)

    def read(self, lba, count=1):
        out = bytearray()
        for i in range(count):
            self.f.seek((lba + i) * self.ssize + self.off)
            out += self.f.read(2048)
        return bytes(out)

    def read_file(self, lba, size, dest):
        remaining = size
        with open(dest, "wb") as o:
            cur = lba
            while remaining > 0:
                n = min(remaining, 2048 * 256)
                sectors = (n + 2047) // 2048
                data = self.read(cur, sectors)[:n]
                o.write(data)
                cur += sectors
                remaining -= n


def parse_dir(img, lba, size):
    data = img.read(lba, (size + 2047) // 2048)
    pos = 0
    entries = []
    while pos < len(data):
        ln = data[pos]
        if ln == 0:
            pos = (pos // 2048 + 1) * 2048
            continue
        rec = data[pos:pos + ln]
        e_lba, = struct.unpack_from("<I", rec, 2)
        e_size, = struct.unpack_from("<I", rec, 10)
        flags = rec[25]
        nlen = rec[32]
        name = rec[33:33 + nlen]
        pos += ln
        if name in (b"\x00", b"\x01"):
            continue
        name = name.decode("ascii", "replace").split(";")[0]
        entries.append((name, e_lba, e_size, bool(flags & 2)))
    return entries


def walk(img, lba, size, base, out_dir, list_only, stats):
    for name, e_lba, e_size, is_dir in parse_dir(img, lba, size):
        rel = os.path.join(base, name)
        if is_dir:
            if not list_only:
                os.makedirs(os.path.join(out_dir, rel), exist_ok=True)
            walk(img, e_lba, e_size, rel, out_dir, list_only, stats)
        else:
            print(f"{e_lba:8d} {e_size:10d} {rel}")
            stats[0] += 1
            stats[1] += e_size
            if not list_only:
                dest = os.path.join(out_dir, rel)
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                img.read_file(e_lba, e_size, dest)


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 1
    img = Image(argv[1])
    pvd = img.read(16)
    root = pvd[156:190]
    r_lba, = struct.unpack_from("<I", root, 2)
    r_size, = struct.unpack_from("<I", root, 10)
    list_only = "--list" in argv
    os.makedirs(argv[2], exist_ok=True)
    stats = [0, 0]
    print(f"layout: sector={img.ssize} data_offset={img.off} root_lba={r_lba}")
    walk(img, r_lba, r_size, "", argv[2], list_only, stats)
    print(f"{stats[0]} files, {stats[1]} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
