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
        
        # In Pyodide we use absolute paths for consistency
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
        # Use absolute paths in Pyodide environment
        base_dir = '/home/pyodide'
        script_path = os.path.join(base_dir, 'dumper-companion.py')
        output_dir = os.path.join(base_dir, 'virtual_out')
        
        # 1. Clean and prepare output directory
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        os.makedirs(output_dir, exist_ok=True)
        
        # 2. Verify script existence
        if not os.path.exists(script_path):
            print(f"!! CRITICAL: Script not found at {script_path}")
            # Try to find it in the current dir as fallback
            if os.path.exists('dumper-companion.py'):
                script_path = os.path.abspath('dumper-companion.py')
            else:
                raise FileNotFoundError(f"dumper-companion.py not found in /home/pyodide or current directory.")
        
        # 3. Build Arguments
        # sys.argv[0] is the script name, then command, then flags, then files
        args = ['dumper-companion.py', command]
        
        # Add flags from UI (extra_args_list is a list of strings like ['--japanese', '--encoding', 'mac_roman'])
        args.extend(extra_args_list)

        # 4. Add Positional Arguments based on command
        if command in ['iso', 'createmacfonts']:
            # For extraction: <cmd> <input_file> <output_dir>
            args.extend([filename, output_dir])
        elif command in ['probe', 'dir', 'str']:
            # For inspection: <cmd> <input_file/dir>
            args.append(filename)
        
        sys.argv = args
        
        print(f"Running Command: {' '.join(sys.argv)}")
        print("-" * 50)
        
        # 5. Execute Ritual
        runpy.run_path(script_path, run_name='__main__')
        
    except SystemExit as e:
        if e.code != 0 and e.code is not None:
            print(f"\n[The ritual was interrupted with code {e.code}]")
    except Exception:
        print("\n[THE ORACLE HAS ENCOUNTERED A VISION ERROR]")
        traceback.print_exc()
    finally:
        sys.stdout, sys.stderr = old_stdout, old_stderr
        return captured_output.getvalue()
