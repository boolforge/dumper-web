import sys
import os
import io
import traceback
import runpy
import shutil
import struct

class OperaFS:
    """Minimalist 3DO Opera FileSystem Parser"""
    def __init__(self, iso_path, output_dir):
        self.iso_path = iso_path
        self.output_dir = output_dir
        self.block_size = 2048

    def is_3do(self):
        try:
            with open(self.iso_path, "rb") as f:
                sig = f.read(7)
                return sig == b'\x01ZZZZZ\x01'
        except:
            return False

    def extract(self):
        print("Detected 3DO Opera FileSystem. Commencing specialized ritual...")
        with open(self.iso_path, "rb") as f:
            # Volume Header (Block 0)
            f.seek(104)
            root_block = struct.unpack(">I", f.read(4))[0]
            root_size = struct.unpack(">I", f.read(4))[0]
            print(f"Root Directory found at block {root_block} ({root_size} bytes)")
            
            self._extract_dir(f, root_block, self.output_dir)

    def _extract_dir(self, f, block, current_out):
        if not os.path.exists(current_out):
            os.makedirs(current_out, exist_ok=True)
            
        f.seek(block * self.block_size)
        # Directory Header
        # 0x00: flags (4 bytes)
        # 0x04: first free byte (4 bytes)
        # 0x08: num entries (4 bytes)
        f.seek(8, 1) 
        num_entries = struct.unpack(">I", f.read(4))[0]
        
        entries = []
        for _ in range(num_entries):
            # Directory Entry
            entry_data = f.read(72) # Standard entry size
            if len(entry_data) < 72: break
            
            flags = struct.unpack(">I", entry_data[0:4])[0]
            id = struct.unpack(">I", entry_data[4:8])[0]
            offset = struct.unpack(">I", entry_data[16:20])[0]
            size = struct.unpack(">I", entry_data[20:24])[0]
            name = entry_data[32:64].split(b'\x00')[0].decode('ascii', 'ignore')
            
            if name and name not in ['.', '..']:
                entries.append({'name': name, 'offset': offset, 'size': size, 'is_dir': bool(flags & 0x02)})

        for entry in entries:
            target = os.path.join(current_out, entry['name'])
            if entry['is_dir']:
                print(f"Entering directory: {entry['name']}")
                self._extract_dir(f, entry['offset'], target)
            else:
                print(f"Extracting: {entry['name']} ({entry['size']} bytes)")
                f.seek(entry['offset'] * self.block_size)
                data = f.read(entry['size'])
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
        if command == 'iso' and opera.is_3do():
            opera.extract()
            print("\n✅ 3DO Extraction Complete.")
            return captured_output.getvalue()

        # Fallback to ScummVM Dumper Companion
        if not os.path.exists(script_path):
            print(f"!! CRITICAL: Script not found at {script_path}")
            return captured_output.getvalue()
        
        args = ['dumper-companion.py', command]
        args.extend(extra_args_list)
        if command in ['iso', 'createmacfonts']:
            args.extend([filename, output_dir])
        elif command in ['probe', 'dir', 'str']:
            args.append(filename)
        
        sys.argv = args
        print(f"Running Command: {' '.join(sys.argv)}")
        print("-" * 50)
        runpy.run_path(script_path, run_name='__main__')
        
    except IndexError as e:
        if "list index out of range" in str(e):
            print("\n[THE ORACLE IS CONFUSED]")
            print("Error: The dumper could not detect a valid ISO9660 or HFS filesystem.")
            print("Note: If this is a 3DO game, the experimental Opera FS parser should have caught it.")
        else:
            traceback.print_exc()
    except Exception:
        print("\n[THE ORACLE HAS ENCOUNTERED A VISION ERROR]")
        traceback.print_exc()
    finally:
        sys.stdout, sys.stderr = old_stdout, old_stderr
        return captured_output.getvalue()
