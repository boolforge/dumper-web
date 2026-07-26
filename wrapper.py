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

    def detect_format(self):
        try:
            with open(self.iso_path, "rb") as f:
                # 1. Check for 3DO Opera FS (Block 0)
                f.seek(0)
                if f.read(7) == b'\x01ZZZZZ\x01':
                    self.format = "3do"
                    return "3DO Opera FS"
                
                f.seek(16)
                if f.read(7) == b'\x01ZZZZZ\x01':
                    self.format = "3do_raw"
                    self.sector_size = 2352
                    self.data_offset = 16
                    return "3DO Opera FS (RAW)"

                # 2. Check for ISO9660 (Standard Mode 1)
                f.seek(0x8000)
                if f.read(6) == b'\x01CD001':
                    self.format = "iso9660"
                    return "Standard ISO9660 (PC/Sega CD/Saturn)"

                # 3. Check for PSX / Saturn (Mode 2 XA RAW)
                f.seek(37632 + 24)
                if f.read(6) == b'\x01CD001':
                    self.format = "iso9660_xa"
                    self.sector_size = 2352
                    self.data_offset = 24
                    return "Console ISO9660 (PSX/Saturn RAW)"

                # 4. Check for CD-i (Green Book)
                f.seek(0x8000 + 8)
                if f.read(4) == b'CD-I':
                    self.format = "cdi"
                    return "Philips CD-i (Green Book)"

            return "Unknown Format"
        except: return "Detection Failed"

    def extract(self):
        if self.format.startswith("3do"):
            opera = OperaFS(self.iso_path, self.output_dir)
            if self.format == "3do_raw":
                opera.block_size = 2352
                opera.sector_offset = 16
            opera.extract()
            return True
        elif self.format == "cdi":
            cdi = CDiParser(self.iso_path, self.output_dir)
            cdi.extract()
            return True
        elif self.format == "iso9660_xa":
            print("Extracting Console ISO9660 (XA Mode 2)...")
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
    def __init__(self, iso_path, output_dir):
        self.iso_path = iso_path
        self.output_dir = output_dir
        self.block_size = 2048
        self.sector_offset = 0

    def extract(self):
        with open(self.iso_path, "rb") as f:
            f.seek(self.sector_offset + 104)
            root_block = struct.unpack(">I", f.read(4))[0]
            self._extract_node(f, root_block, self.output_dir)

    def _extract_node(self, f, block, current_out):
        if not os.path.exists(current_out): os.makedirs(current_out, exist_ok=True)
        f.seek(block * self.block_size + self.sector_offset)
        dir_header = f.read(20)
        if len(dir_header) < 20: return
        num_entries = struct.unpack(">I", dir_header[16:20])[0]
        for i in range(num_entries):
            f.seek(block * self.block_size + self.sector_offset + 20 + (i * 72))
            entry_data = f.read(72)
            if len(entry_data) < 72: break
            flags = struct.unpack(">I", entry_data[0:4])[0]
            offset = struct.unpack(">I", entry_data[16:20])[0]
            size = struct.unpack(">I", entry_data[20:24])[0]
            name = entry_data[32:64].split(b'\x00')[0].decode('ascii', 'ignore').strip()
            if not name or name in ['.', '..']: continue
            target = os.path.join(current_out, name)
            if bool(flags & 0x02): self._extract_node(f, offset, target)
            else:
                f.seek(offset * self.block_size + self.sector_offset)
                with open(target, "wb") as out_f: out_f.write(f.read(size))

class CDiParser:
    """Minimalist Philips CD-i Green Book Parser"""
    def __init__(self, iso_path, output_dir):
        self.iso_path = iso_path
        self.output_dir = output_dir
        self.block_size = 2048

    def extract(self):
        print("Commencing CD-i Green Book Ritual...")
        with open(self.iso_path, "rb") as f:
            # CD-i Root is usually in the PVD at sector 16
            f.seek(16 * 2048 + 156)
            root_record = f.read(34)
            extent = struct.unpack("<I", root_record[2:6])[0]
            size = struct.unpack("<I", root_record[10:14])[0]
            self._extract_dir(f, extent, size, self.output_dir)

    def _extract_dir(self, f, extent, size, current_out):
        if not os.path.exists(current_out): os.makedirs(current_out, exist_ok=True)
        f.seek(extent * 2048)
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
                if file_flags & 0x02: # Directory
                    # Need to be careful with recursion in CD-i
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
        base_dir = '/home/pyodide'
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
                filename = result # Use the temp Mode 1 ISO

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
