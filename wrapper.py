import sys
import io
import os
import runpy
import importlib.util

_dumper = None

def _get_dumper():
    global _dumper
    if _dumper is None:
        base_dir = os.getcwd()
        script_path = os.path.join(base_dir, 'dumper-companion.py')
        if os.path.exists(script_path):
            spec = importlib.util.spec_from_file_location("dumper_companion", script_path)
            _dumper = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(_dumper)
    return _dumper

def process_task_advanced(command, filename, extra_args):
    import shutil
    output_io = io.StringIO()
    sys.stdout = output_io
    sys.stderr = output_io
    
    try:
        base_dir = os.getcwd()
        script_path = os.path.join(base_dir, 'dumper-companion.py')
        input_path = os.path.join(base_dir, filename)
        output_dir = os.path.join(base_dir, 'virtual_out')
        
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        os.makedirs(output_dir)

        # Setup sys.argv depending on the command
        if command == 'createmacfonts':
            sys.argv = ['dumper-companion.py', 'createmacfonts']
        elif command == 'probe':
            sys.argv = ['dumper-companion.py', 'probe', input_path]
        else:
            sys.argv = ['dumper-companion.py', command, input_path, output_dir] + extra_args

        # Directly run dumper-companion.py
        runpy.run_path(script_path, run_name='__main__')

        print("✅ Ritual Complete.")
    except Exception as e:
        print(f"\n[THE ORACLE HAS ENCOUNTERED A VISION ERROR]\n{e}")
    finally:
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        return output_io.getvalue()

def translate_string(text, to_punycode=True):
    try:
        dumper = _get_dumper()
        if dumper is None:
            return "Vision clouded: dumper-companion.py not loaded yet."
        if text.startswith("xn--") or not to_punycode:
            return dumper.decode_string(text)
        else:
            return dumper.punyencode(text)
    except Exception as e:
        return f"Vision clouded: {e}"
