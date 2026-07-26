import sys
import os
import io
import traceback
import runpy
import shutil
import struct

class UniversalCDHandler:
    """Universal Console CD Handler for ScummVM Dumper Web"""
    def __init__(self, iso_path, output_dir):
        self.iso_path = iso_path
        self.output_dir = output_dir
        self.sector_size = 2048
        self.data_offset = 0
        self.format = "unknown"
        self.file_size = os.path.getsize(iso_path)

    def detect_format(self):
        try:
            with open(self.iso_path, "rb") as f:
                # 1. Check for 3DO Opera FS (Block 0)
                f.seek(0)
                if f.read(7) == b'\x01ZZZZZ\x01':
                    self.format = "3do"
                    self.sector_size = 2048
                    self.data_offset = 0
                    return "3DO Opera FS"
                
                # 2. Check for 3DO RAW (PVD at sector 16)
                f.seek(16 * 2352)
                if f.read(7) == b'\x01ZZZZZ\x01':
                    self.format = "3do_raw"
                    self.sector_size = 2352
                    self.data_offset = 16
                    return "3DO Opera FS (RAW)"

                # 3. Check for ISO9660 (Standard Mode 1)
                f.seek(16 * 2048)
                if f.read(6) == b'\x01CD001':
                    self.format = "iso9660"
                    return "Standard ISO9660"

                # 4. Check for Console ISO9660 (PSX/Saturn RAW)
                f.seek(16 * 2352 + 24)
                if f.read(6) == b'\x01CD001':
                    self.format = "iso9660_xa"
                    self.sector_size = 2352
                    self.data_offset = 24
                    return "Console ISO9660 (PSX/Saturn RAW)"

                # 5. Check for CD-i (Green Book)
                f.seek(16 * 2048 + 8)
                if f.read(4) == b'CD-I':
                    self.format = "cdi"
                    return "Philips CD-i (Green Book)"

            return "Unknown Format"
        except: return "Detection Failed"

    def extract(self):
        if self.format.startswith("3do"):
            opera = OperaFS(self.iso_path, self.output_dir)
            opera.block_size = self.sector_size
            opera.sector_offset = self.data_offset
            opera.extract()
            return True
        elif self.format == "cdi":
            cdi = CDiParser(self.iso_path, self.output_dir)
            cdi.extract()
            return True
        elif self.format == "iso9660_xa":
            return self._extract_xa_to_mode1()
        return False

    def _extract_xa_to_mode1(self):
        temp_iso = os.path.join(os.path.dirname(self.iso_path), "temp_mode1.iso")
        print(f"Converting XA RAW to Mode 1 for the Oracle...")
        with open(self.iso_path, "rb") as fin, open(temp_iso, "wb") as fout:
            while True:
                sector = fin.read(self.sector_size)
                if not sector: break
                fout.write(sector[self.data_offset : self.data_offset + 2048])
        return temp_iso

class OperaFS:
    """Robust 3DO Opera FileSystem Parser with Overflow Protection"""
    def __init__(self, iso_path, output_dir):
        self.iso_path = iso_path
        self.output_dir = output_dir
        self.block_size = 2048
        self.sector_offset = 0
        self.file_size = os.path.getsize(iso_path)

    def extract(self):
        with open(self.iso_path, "rb") as f:
            # Root block is at offset 104 of the Volume Label
            f.seek(self.sector_offset + 104)
            root_block = struct.unpack(">I", f.read(4))[0]
            print(f"Manifesting Root Oracle at block {root_block}...")
            self._extract_node(f, root_block, self.output_dir)

    def _extract_node(self, f, block, current_out):
        if not os.path.exists(current_out): os.makedirs(current_out, exist_ok=True)
        
        # Security check to prevent OverflowError
        pos = block * self.block_size + self.sector_offset
        if pos >= self.file_size:
            print(f"!! The Oracle warns: Block {block} is beyond the horizon. Skipping.")
            return

        f.seek(pos)
        dir_header = f.read(20)
        if len(dir_header) < 20: return
        
        # Offset 16 is the directory size in bytes, NOT the number of entries
        dir_size = struct.unpack(">I", dir_header[16:20])[0]
        
        # Each entry is 72 bytes. We skip the 20-byte header.
        entries_count = (dir_size - 20) // 72
        if entries_count > 1000: # Sanity check
             print("!! The Oracle senses a corrupted directory structure. Limiting extraction.")
             entries_count = 1000

        for i in range(entries_count):
            entry_pos = pos + 20 + (i * 72)
            if entry_pos + 72 > self.file_size: break
            
            f.seek(entry_pos)
            entry_data = f.read(72)
            if len(entry_data) < 72: break
            
            flags = struct.unpack(">I", entry_data[0:4])[0]
            offset = struct.unpack(">I", entry_data[16:20])[0]
            size = struct.unpack(">I", entry_data[20:24])[0]
            name = entry_data[32:64].split(b'\x00')[0].decode('ascii', 'ignore').strip()
            
            if not name or name in ['.', '..']: continue
            
            target = os.path.join(current_out, name)
            if bool(flags & 0x02): # Directory
                self._extract_node(f, offset, target)
            else: # File
                file_pos = offset * self.block_size + self.sector_offset
                if file_pos + size <= self.file_size:
                    f.seek(file_pos)
                    with open(target, "wb") as out_f:
                        out_f.write(f.read(size))
                else:
                    print(f"!! Skipping artifact '{name}': out of bounds.")

class CDiParser:
    def __init__(self, iso_path, output_dir):
        self.iso_path = iso_path
        self.output_dir = output_dir
        self.file_size = os.path.getsize(iso_path)

    def extract(self):
        print("Commencing CD-i Green Book Ritual...")
        with open(self.iso_path, "rb") as f:
            f.seek(16 * 2048 + 156)
            root_record = f.read(34)
            extent = struct.unpack("<I", root_record[2:6])[0]
            size = struct.unpack("<I", root_record[10:14])[0]
            self._extract_dir(f, extent, size, self.output_dir)

    def _extract_dir(self, f, extent, size, current_out):
        if not os.path.exists(current_out): os.makedirs(current_out, exist_ok=True)
        pos_in_file = extent * 2048
        if pos_in_file >= self.file_size: return
        
        f.seek(pos_in_file)
        dir_data = f.read(size)
        pos = 0
        while pos < len(dir_data):
            rec_len = dir_data[pos]
            if rec_len == 0: break
            
            extent_loc = struct.unpack("<I", dir_data[pos+2:pos+6])[0]
            data_len = struct.unpack("<I", dir_data[pos+10:pos+14])[0]
            file_flags = dir_data[pos+25]
            name_len = dir_data[pos+32]
            name = dir_data[pos+33:pos+33+name_len].decode('ascii', 'ignore').split(';')[0]
            
            if name and name not in ['\x00', '\x01']:
                target = os.path.join(current_out, name)
                if file_flags & 0x02:
                    curr_pos = f.tell()
                    self._extract_dir(f, extent_loc, data_len, target)
                    f.seek(curr_pos)
                else:
                    curr_pos = f.tell()
                    f.seek(extent_loc * 2048)
                    with open(target, "wb") as out_f: out_f.write(f.read(data_len))
                    f.seek(curr_pos)
            pos += rec_len

def translate_string(input_str):
    try:
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        script_path = '/home/pyodide/dumper-companion.py'
        sys.argv = ['dumper-companion.py', 'str', input_str]
        runpy.run_path(script_path, run_name='__main__')
        result = sys.stdout.getvalue().strip()
        sys.stdout = old_stdout
        return result
    except: return "Error decoding"

def process_task_advanced(command, filename, extra_args_list):
    old_stdout, old_stderr = sys.stdout, sys.stderr
    captured_output = io.StringIO()
    sys.stdout = sys.stderr = captured_output
    try:
        # Detect environment: Pyodide usually has /home/pyodide, sandbox has /home/ubuntu
        base_dir = '/home/pyodide' if os.path.exists('/home/pyodide') else os.getcwd()
        script_path = os.path.join(base_dir, 'dumper-companion.py')
        output_dir = os.path.join(base_dir, 'virtual_out')
        if os.path.exists(output_dir): shutil.rmtree(output_dir)
        os.makedirs(output_dir, exist_ok=True)
        
        handler = UniversalCDHandler(filename, output_dir)
        fmt_name = handler.detect_format()
        print(f"The Oracle perceives: {fmt_name}")
        
        if command == 'iso':
            result = handler.extract()
            if result is True:
                print(f"\n✅ {fmt_name} Extraction Complete.")
                return captured_output.getvalue()
            elif isinstance(result, str):
                filename = result

        args = ['dumper-companion.py', command]
        args.extend(extra_args_list)
        if command in ['iso', 'createmacfonts']:
            args.extend([filename, output_dir])
        elif command in ['probe', 'dir', 'str']:
            args.append(filename)
        
        sys.argv = args
        print(f"Invoking ScummVM Ritual: {' '.join(sys.argv)}")
        runpy.run_path(script_path, run_name='__main__')
        
    except Exception:
        print("\n[THE ORACLE HAS ENCOUNTERED A VISION ERROR]")
        traceback.print_exc()
    finally:
        sys.stdout, sys.stderr = old_stdout, old_stderr
        return captured_output.getvalue()
