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
        # Create a virtual output directory
        output_dir = os.path.join(os.getcwd(), "virtual_out")
        os.makedirs(output_dir, exist_ok=True)
        
        # Abstract the CLI: Inject the arguments dumper-companion.py expects
        # Corrected command from 'extract' to 'iso' as per scummvm script help
        sys.argv = ['dumper-companion.py', 'iso', filename, output_dir]
        
        print(f"Mounting virtual filesystem for {filename}...")
        print(f"Executing ScummVM dumper logic with command: {' '.join(sys.argv[1:])}")
        
        runpy.run_path('dumper-companion.py', run_name='__main__')
        
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
