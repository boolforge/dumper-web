import sys
import os
import io
import traceback
import runpy
import shutil
import struct

class OperaFS:
    """Robust 3DO Opera FileSystem Parser based on Portfolio OS specs"""
    def __init__(self, iso_path, output_dir):
        self.iso_path = iso_path
        self.output_dir = output_dir
        self.block_size = 2048
        self.sector_offset = 0

    def detect(self):
        try:
            with open(self.iso_path, "rb") as f:
                # Try standard offset (2048)
                f.seek(0)
                sig = f.read(7)
                if sig == b'\x01ZZZZZ\x01':
                    self.block_size = 2048
                    self.sector_offset = 0
                    return True
                
                # Try RAW offset (2352) - Data usually starts at 16 or 24 bytes in
                f.seek(16)
                sig = f.read(7)
                if sig == b'\x01ZZZZZ\x01':
                    self.block_size = 2352
                    self.sector_offset = 16
                    return True
                
                return False
        except:
            return False

    def extract(self):
        print(f"Detected 3DO Opera FileSystem (Block Size: {self.block_size}).")
        with open(self.iso_path, "rb") as f:
            # Volume Header is in Block 0
            f.seek(self.sector_offset + 104)
            root_block = struct.unpack(">I", f.read(4))[0]
            root_size = struct.unpack(">I", f.read(4))[0]
            
            print(f"Manifesting Root Sanctum at block {root_block}...")
            self._extract_node(f, root_block, self.output_dir)

    def _extract_node(self, f, block, current_out):
        if not os.path.exists(current_out):
            os.makedirs(current_out, exist_ok=True)
            
        # Read Directory Header
        f.seek(block * self.block_size + self.sector_offset)
        dir_header = f.read(20)
        if len(dir_header) < 20: return
        
        # Directory Header Structure:
        # 0-3: anchor, 4-7: next_dir, 8-11: prev_dir, 12-15: first_free, 16-19: num_entries
        num_entries = struct.unpack(">I", dir_header[16:20])[0]
        
        # Entries start right after header (20 bytes)
        for i in range(num_entries):
            # Each entry is 72 bytes
            f.seek(block * self.block_size + self.sector_offset + 20 + (i * 72))
            entry_data = f.read(72)
            if len(entry_data) < 72: break
            
            flags = struct.unpack(">I", entry_data[0:4])[0]
            id = struct.unpack(">I", entry_data[4:8])[0]
            offset = struct.unpack(">I", entry_data[16:20])[0]
            size = struct.unpack(">I", entry_data[20:24])[0]
            # Name is at offset 32, max 32 chars
            name_bytes = entry_data[32:64].split(b'\x00')[0]
            try:
                name = name_bytes.decode('ascii', 'ignore').strip()
            except:
                name = f"unknown_{i}"
            
            if not name or name in ['.', '..']: continue
            
            target = os.path.join(current_out, name)
            is_dir = bool(flags & 0x02) # Directory flag in Opera FS
            
            if is_dir:
                print(f" -> Entering Chamber: {name}")
                self._extract_node(f, offset, target)
            else:
                print(f" -> Recovering Artifact: {name} ({size} bytes)")
                f.seek(offset * self.block_size + self.sector_offset)
                data = f.read(size)
                with open(target, "wb") as out_f:
                    out_f.write(data)

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
    except:
        return "Error decoding"

def process_task_advanced(command, filename, extra_args_list):
    old_stdout, old_stderr = sys.stdout, sys.stderr
    captured_output = io.StringIO()
    sys.stdout = sys.stderr = captured_output

    try:
        base_dir = '/home/pyodide'
        script_path = os.path.join(base_dir, 'dumper-companion.py')
        output_dir = os.path.join(base_dir, 'virtual_out')
        
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        os.makedirs(output_dir, exist_ok=True)
        
        # 3DO Detection Logic
        opera = OperaFS(filename, output_dir)
        if command == 'iso' and opera.detect():
            opera.extract()
            print("\n✅ Ritual of Opera FS Complete. All artifacts secured.")
            return captured_output.getvalue()

        # Fallback to ScummVM Dumper Companion
        if not os.path.exists(script_path):
            print(f"!! CRITICAL: The Sacred Script (dumper-companion.py) is missing at {script_path}")
            return captured_output.getvalue()
        
        args = ['dumper-companion.py', command]
        args.extend(extra_args_list)
        if command in ['iso', 'createmacfonts']:
            args.extend([filename, output_dir])
        elif command in ['probe', 'dir', 'str']:
            args.append(filename)
        
        sys.argv = args
        print(f"Informing the Oracle: {' '.join(sys.argv)}")
        print("-" * 50)
        runpy.run_path(script_path, run_name='__main__')
        
    except IndexError as e:
        if "list index out of range" in str(e):
            print("\n[THE ORACLE IS CONFUSED]")
            print("Error: No valid ISO9660 or HFS filesystem detected.")
            print("Hint: If this is a 3DO game, ensure the image is not corrupted.")
        else:
            traceback.print_exc()
    except Exception:
        print("\n[THE ORACLE HAS ENCOUNTERED A VISION ERROR]")
        traceback.print_exc()
    finally:
        sys.stdout, sys.stderr = old_stdout, old_stderr
        return captured_output.getvalue()
