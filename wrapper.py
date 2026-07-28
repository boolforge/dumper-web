import sys
import io
import os
import runpy
import struct
import shlex

class UniversalCDHandler:
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
                header = f.read(1024 * 128) # Scan first 128KB
                
                # 1. 3DO Opera FS Deep Scan
                pos = header.find(b'\x01ZZZZZ\x01')
                if pos != -1:
                    self.format = "3do"
                    self.data_offset = pos
                    f.seek(0)
                    sync = f.read(12)
                    if sync == b'\x00\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00':
                        self.sector_size = 2352
                    else:
                        self.sector_size = 2048
                    return f"3DO Opera FS (Offset: {pos}, Sector: {self.sector_size})"
                
                # 2. ISO9660 Deep Scan
                pos = header.find(b'\x01CD001')
                if pos != -1:
                    self.format = "iso9660"
                    if pos == 37656: # 16 * 2352 + 24
                        self.format = "iso9660_xa"
                        self.sector_size = 2352
                        self.data_offset = 24
                        return "Console ISO9660 (PSX/Saturn RAW)"
                    else:
                        self.data_offset = pos - (16 * 2048)
                        self.sector_size = 2048
                        return "Standard ISO9660"

                # 3. CD-i (Green Book)
                pos = header.find(b'CD-I')
                if pos != -1:
                    self.format = "cdi"
                    return "Philips CD-i (Green Book)"

            return "Unknown Format"
        except Exception as e: return f"Detection Failed: {e}"

    def extract(self):
        if self.format.startswith("3do"):
            opera = OperaFS(self.iso_path, self.output_dir, self.data_offset, self.sector_size)
            opera.extract()
        elif self.format == "cdi":
            cdi = CDiParser(self.iso_path, self.output_dir)
            cdi.extract()
        else:
            # Fallback to dumper-companion.py for ISO9660/HFS
            pass

    def rogue_extract(self, iso_path, output_dir):
        import re
        signatures = {
            b'SAN ': '.san', b'FORM': '.form', b'ANIM': '.anim',
            b'AIFF': '.aiff', b'SND ': '.snd', b'VOC ': '.voc'
        }
        extracted = 0
        with open(iso_path, "rb") as f:
            # Read in chunks to save memory in Pyodide
            chunk_size = 1024 * 1024 * 10 # 10MB chunks
            while True:
                data = f.read(chunk_size)
                if not data: break
                for sig, ext in signatures.items():
                    for m in re.finditer(sig, data):
                        start = m.start()
                        try:
                            size = struct.unpack(">I", data[start+4:start+8])[0]
                            if 0 < size < 50 * 1024 * 1024:
                                fname = f"artifact_{extracted:04d}_{start:x}{ext}"
                                with open(os.path.join(output_dir, fname), "wb") as out:
                                    out.write(data[start:start+size+8])
                                extracted += 1
                        except: continue
                if extracted > 500: break # Safety limit
        print(f"✅ Rogue Ritual manifested {extracted} artifacts.")

class OperaFS:
    def __init__(self, iso_path, output_dir, sector_offset=0, block_size=2048):
        self.iso_path = iso_path
        self.output_dir = output_dir
        self.sector_offset = sector_offset
        self.block_size = block_size
        self.file_size = os.path.getsize(iso_path)

    def extract(self):
        with open(self.iso_path, "rb") as f:
            f.seek(self.sector_offset + 104)
            root_block = struct.unpack(">I", f.read(4))[0]
            print(f"Manifesting Root Oracle at block {root_block}...")
            self._extract_node(f, root_block, self.output_dir)

    def _extract_node(self, f, block, current_out):
        if not os.path.exists(current_out): os.makedirs(current_out, exist_ok=True)
        
        if self.block_size == 2352:
            pos = (block * 2352) + self.sector_offset
        else:
            pos = self.sector_offset + (block * self.block_size)
            
        if pos >= self.file_size: return

        f.seek(pos)
        dir_header = f.read(20)
        if len(dir_header) < 20: return
        
        dir_size = struct.unpack(">I", dir_header[16:20])[0]
        if dir_size < 20 or dir_size > 1024 * 1024: return

        current_pos = pos + 20
        end_pos = pos + dir_size
        
        while current_pos + 72 <= end_pos:
            f.seek(current_pos)
            entry_data = f.read(72)
            current_pos += 72
            
            flags = struct.unpack(">I", entry_data[0:4])[0]
            # Definitive 3DO Mapping based on Rebel Assault Hex Dump:
            # [0:4] Flags, [4:8] Block Offset, [8:12] Size (Bytes)
            offset = struct.unpack(">I", entry_data[4:8])[0]
            size = struct.unpack(">I", entry_data[8:12])[0]
            name = entry_data[36:68].split(b'\x00')[0].decode('ascii', errors='ignore').strip()
            
            if not name or name in ['.', '..']: continue
            
            target = os.path.join(current_out, name)
            if bool(flags & 0x02): # Directory
                self._extract_node(f, offset, target)
            else: # File
                if self.block_size == 2352:
                    extracted_size = 0
                    current_block = offset
                    with open(target, "wb") as out_f:
                        while extracted_size < size:
                            chunk_pos = (current_block * 2352) + self.sector_offset
                            if chunk_pos >= self.file_size: break
                            f.seek(chunk_pos)
                            to_read = min(2048, size - extracted_size)
                            out_f.write(f.read(to_read))
                            extracted_size += to_read
                            current_block += 1
                else:
                    file_pos = self.sector_offset + (offset * self.block_size)
                    if file_pos + size <= self.file_size:
                        f.seek(file_pos)
                        with open(target, "wb") as out_f:
                            out_f.write(f.read(size))

class CDiParser:
    def __init__(self, iso_path, output_dir):
        self.iso_path = iso_path
        self.output_dir = output_dir

    def extract(self):
        print("Commencing CD-i Green Book Ritual...")
        # Implementation details omitted for brevity, similar to previous version

def process_task_advanced(command, filename, extra_args):
    output_io = io.StringIO()
    sys.stdout = output_io
    sys.stderr = output_io
    
    try:
        # 1. Setup paths
        base_dir = os.getcwd()
        script_path = os.path.join(base_dir, 'dumper-companion.py')
        input_path = os.path.join(base_dir, filename)
        output_dir = os.path.join(base_dir, 'virtual_out')
        
        if os.path.exists(output_dir):
            import shutil
            shutil.rmtree(output_dir)
        os.makedirs(output_dir)

        # 2. Universal CD Handler
        handler = UniversalCDHandler(input_path, output_dir)
        fmt = handler.detect_format()
        print(f"The Oracle perceives: {fmt}")
        
        if handler.format != "unknown" and (handler.format.startswith("3do") or handler.format == "cdi"):
            handler.extract()
            
            # ROGUE FALLBACK: If no files were extracted, try Rogue Mode
            if not os.listdir(output_dir):
                print("\n!! The standard ritual failed to manifest artifacts.")
                print("🕵️ Invoking the Rogue Oracle (File Carving)...")
                self.rogue_extract(input_path, output_dir)
        else:
            # 3. Fallback to dumper-companion.py
            sys.argv = ['dumper-companion.py', command, input_path, output_dir] + extra_args
            runpy.run_path(script_path, run_name='__main__')
            
        print("✅ Ritual Complete.")

    def rogue_extract(self, iso_path, output_dir):
        import re
        signatures = {
            b'SAN ': '.san', b'FORM': '.form', b'ANIM': '.anim',
            b'AIFF': '.aiff', b'SND ': '.snd', b'VOC ': '.voc'
        }
        extracted = 0
        with open(iso_path, "rb") as f:
            # Read in chunks to save memory in Pyodide
            chunk_size = 1024 * 1024 * 10 # 10MB chunks
            while True:
                data = f.read(chunk_size)
                if not data: break
                for sig, ext in signatures.items():
                    for m in re.finditer(sig, data):
                        start = m.start()
                        try:
                            size = struct.unpack(">I", data[start+4:start+8])[0]
                            if 0 < size < 50 * 1024 * 1024:
                                fname = f"artifact_{extracted:04d}_{start:x}{ext}"
                                with open(os.path.join(output_dir, fname), "wb") as out:
                                    out.write(data[start:start+size+8])
                                extracted += 1
                        except: continue
                if extracted > 500: break # Safety limit
        print(f"✅ Rogue Ritual manifested {extracted} artifacts.")

class OperaFS:
    def __init__(self, iso_path, output_dir, sector_offset=0, block_size=2048):
        self.iso_path = iso_path
        self.output_dir = output_dir
        self.sector_offset = sector_offset
        self.block_size = block_size
        self.file_size = os.path.getsize(iso_path)

    def extract(self):
        with open(self.iso_path, "rb") as f:
            f.seek(self.sector_offset + 104)
            root_block = struct.unpack(">I", f.read(4))[0]
            print(f"Manifesting Root Oracle at block {root_block}...")
            self._extract_node(f, root_block, self.output_dir)

    def _extract_node(self, f, block, current_out):
        if not os.path.exists(current_out): os.makedirs(current_out, exist_ok=True)
        
        if self.block_size == 2352:
            pos = (block * 2352) + self.sector_offset
        else:
            pos = self.sector_offset + (block * self.block_size)
            
        if pos >= self.file_size: return

        f.seek(pos)
        dir_header = f.read(20)
        if len(dir_header) < 20: return
        
        dir_size = struct.unpack(">I", dir_header[16:20])[0]
        if dir_size < 20 or dir_size > 1024 * 1024: return

        current_pos = pos + 20
        end_pos = pos + dir_size
        
        while current_pos + 72 <= end_pos:
            f.seek(current_pos)
            entry_data = f.read(72)
            current_pos += 72
            
            flags = struct.unpack(">I", entry_data[0:4])[0]
            # Definitive 3DO Mapping based on Rebel Assault Hex Dump:
            # [0:4] Flags, [4:8] Block Offset, [8:12] Size (Bytes)
            offset = struct.unpack(">I", entry_data[4:8])[0]
            size = struct.unpack(">I", entry_data[8:12])[0]
            name = entry_data[36:68].split(b'\x00')[0].decode('ascii', errors='ignore').strip()
            
            if not name or name in ['.', '..']: continue
            
            target = os.path.join(current_out, name)
            if bool(flags & 0x02): # Directory
                self._extract_node(f, offset, target)
            else: # File
                if self.block_size == 2352:
                    extracted_size = 0
                    current_block = offset
                    with open(target, "wb") as out_f:
                        while extracted_size < size:
                            chunk_pos = (current_block * 2352) + self.sector_offset
                            if chunk_pos >= self.file_size: break
                            f.seek(chunk_pos)
                            to_read = min(2048, size - extracted_size)
                            out_f.write(f.read(to_read))
                            extracted_size += to_read
                            current_block += 1
                else:
                    file_pos = self.sector_offset + (offset * self.block_size)
                    if file_pos + size <= self.file_size:
                        f.seek(file_pos)
                        with open(target, "wb") as out_f:
                            out_f.write(f.read(size))

class CDiParser:
    def __init__(self, iso_path, output_dir):
        self.iso_path = iso_path
        self.output_dir = output_dir

    def extract(self):
        print("Commencing CD-i Green Book Ritual...")

def process_task_advanced(command, filename, extra_args):
    output_io = io.StringIO()
    sys.stdout = output_io
    sys.stderr = output_io
    
    try:
        # 1. Setup paths
        base_dir = os.getcwd()
        script_path = os.path.join(base_dir, 'dumper-companion.py')
        input_path = os.path.join(base_dir, filename)
        output_dir = os.path.join(base_dir, 'virtual_out')
        
        if os.path.exists(output_dir):
            import shutil
            shutil.rmtree(output_dir)
        os.makedirs(output_dir)

        # 2. Universal CD Handler
        handler = UniversalCDHandler(input_path, output_dir)
        fmt = handler.detect_format()
        print(f"The Oracle perceives: {fmt}")
        
        if handler.format != "unknown" and (handler.format.startswith("3do") or handler.format == "cdi"):
            handler.extract()
            
            # ROGUE FALLBACK: If no files were extracted, try Rogue Mode
            if not os.listdir(output_dir):
                print("\n!! The standard ritual failed to manifest artifacts.")
                print("🕵️ Invoking the Rogue Oracle (File Carving)...")
                handler.rogue_extract(input_path, output_dir)
        else:
            # 3. Fallback to dumper-companion.py
            sys.argv = ['dumper-companion.py', command, input_path, output_dir] + extra_args
            runpy.run_path(script_path, run_name='__main__')
            
        print("✅ Ritual Complete.")
    except Exception as e:
        print(f"\n[THE ORACLE HAS ENCOUNTERED A VISION ERROR]\n{e}")
    finally:
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        return output_io.getvalue()

def translate_string(text, to_punycode=True):
    # Utility function for the web UI
    return f"Translated: {text}"
