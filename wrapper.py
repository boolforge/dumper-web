import sys
import os
import io
import traceback
import runpy

def process_file(filename):
    old_stdout, old_stderr = sys.stdout, sys.stderr
    captured_output = io.StringIO()
    sys.stdout = sys.stderr = captured_output

    try:
        # Define paths explicitly for Pyodide environment
        # Pyodide typically works in /home/pyodide
        base_dir = os.getcwd()
        script_path = os.path.join(base_dir, 'dumper-companion.py')
        output_dir = os.path.join(base_dir, 'virtual_out')
        
        # Ensure output directory is clean
        if os.path.exists(output_dir):
            import shutil
            shutil.rmtree(output_dir)
        os.makedirs(output_dir, exist_ok=True)
        
        # Check if script exists
        if not os.path.exists(script_path):
            # Fallback: check root /
            if os.path.exists('/dumper-companion.py'):
                script_path = '/dumper-companion.py'
            else:
                raise FileNotFoundError(f"Could not find dumper-companion.py in {base_dir} or /")

        # Abstract the CLI: Inject the arguments dumper-companion.py expects
        sys.argv = ['dumper-companion.py', 'iso', filename, output_dir]
        
        print(f"Mounting virtual filesystem for {filename}...")
        print(f"Executing ScummVM dumper logic...")
        print(f"Targeting output to: {output_dir}")
        
        runpy.run_path(script_path, run_name='__main__')
        
    except SystemExit as e:
        if e.code != 0 and e.code is not None:
            print(f"Warning: Script exited with code {e.code}")
    except Exception:
        print("Fatal Error during extraction:")
        traceback.print_exc()
    finally:
        # Restore standard routing
        sys.stdout, sys.stderr = old_stdout, old_stderr
        return captured_output.getvalue()
