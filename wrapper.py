import sys
import os
import io
import traceback
import runpy
import shutil

def process_task(command, filename, extra_args=""):
    old_stdout, old_stderr = sys.stdout, sys.stderr
    captured_output = io.StringIO()
    sys.stdout = sys.stderr = captured_output

    try:
        base_dir = os.getcwd()
        script_path = os.path.join(base_dir, 'dumper-companion.py')
        output_dir = os.path.join(base_dir, 'virtual_out')
        
        # Prepare environment
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        os.makedirs(output_dir, exist_ok=True)
        
        if not os.path.exists(script_path):
            if os.path.exists('/home/pyodide/dumper-companion.py'):
                script_path = '/home/pyodide/dumper-companion.py'
            elif os.path.exists('/dumper-companion.py'):
                script_path = '/dumper-companion.py'
            else:
                raise FileNotFoundError("Could not find dumper-companion.py script.")

        # Build Arguments
        # Basic: dumper-companion.py <command> <input> <output>
        args = ['dumper-companion.py', command]
        
        # Handle extra arguments if provided
        if extra_args:
            import shlex
            args.extend(shlex.split(extra_args))
            
        # Add input and output (most commands follow this pattern)
        if command in ['iso', 'createmacfonts']:
            args.extend([filename, output_dir])
        elif command in ['probe', 'dir']:
            args.append(filename)
        
        sys.argv = args
        
        print(f"Executing: {' '.join(sys.argv)}")
        print("-" * 30)
        
        runpy.run_path(script_path, run_name='__main__')
        
    except SystemExit as e:
        if e.code != 0 and e.code is not None:
            print(f"\n[Process exited with code {e.code}]")
    except Exception:
        print("\n[FATAL ERROR]")
        traceback.print_exc()
    finally:
        sys.stdout, sys.stderr = old_stdout, old_stderr
        return captured_output.getvalue()
