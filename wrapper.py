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
        import runpy
        # We need to call the internal punyencode/decode_string functions
        # The easiest way without refactoring is to use the 'str' command logic
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        
        # dumper-companion.py is already in the path
        sys.argv = ['dumper-companion.py', 'str', input_str]
        runpy.run_path('dumper-companion.py', run_name='__main__')
        
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
        base_dir = os.getcwd()
        script_path = os.path.join(base_dir, 'dumper-companion.py')
        output_dir = os.path.join(base_dir, 'virtual_out')
        
        # 1. Clean environment
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        os.makedirs(output_dir, exist_ok=True)
        
        # 2. Locate script
        if not os.path.exists(script_path):
            possible_paths = ['/home/pyodide/dumper-companion.py', '/dumper-companion.py']
            for p in possible_paths:
                if os.path.exists(p):
                    script_path = p
                    break
        
        # 3. Build Arguments
        args = ['dumper-companion.py', command]
        
        for arg in extra_args_list:
            if arg.startswith('--'):
                args.extend(shlex.split(arg))
            else:
                args.append(arg)

        # 4. Add Positional Arguments
        if command in ['iso', 'createmacfonts']:
            args.extend([filename, output_dir])
        elif command in ['probe', 'dir', 'str']:
            args.append(filename)
        
        sys.argv = args
        
        print(f"Executing: {' '.join(sys.argv)}")
        print("-" * 40)
        
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
