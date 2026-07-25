import sys
import os
import io
import traceback
import runpy
import shutil
import shlex

def translate_string(input_str):
    """Utility to translate between Punycode and real text using the script's logic"""
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
    """Universal bridge for all dumper-companion.py commands with full flag support"""
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
        
        if not os.path.exists(script_path):
            print(f"!! CRITICAL: Script not found at {script_path}")
            if os.path.exists('dumper-companion.py'):
                script_path = os.path.abspath('dumper-companion.py')
            else:
                raise FileNotFoundError(f"dumper-companion.py not found.")
        
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
            print("Error: The dumper could not detect a valid ISO9660 or HFS filesystem in this image.")
            print("\nPedagogical Note:")
            print("1. Ensure the file is a standard Data CD image (not a multi-track BIN/CUE with audio).")
            print("2. If it's a Macintosh image, it might be a raw dump without a partition map.")
            print("3. Try using the 'probe' command to see if the Oracle can find any clues.")
        else:
            traceback.print_exc()
    except SystemExit as e:
        if e.code != 0 and e.code is not None:
            print(f"\n[The ritual was interrupted with code {e.code}]")
    except Exception:
        print("\n[THE ORACLE HAS ENCOUNTERED A VISION ERROR]")
        traceback.print_exc()
    finally:
        sys.stdout, sys.stderr = old_stdout, old_stderr
        return captured_output.getvalue()
