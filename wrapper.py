import sys
import io
import traceback
import runpy

def process_file(file_name):
    old_stdout, old_stderr = sys.stdout, sys.stderr
    captured_output = io.StringIO()
    sys.stdout = sys.stderr = captured_output

    try:
        sys.argv = ['dumper-companion.py', file_name]
        print(f"Starting processing for: {file_name}")
        runpy.run_path('dumper-companion.py', run_name='__main__')
    except SystemExit as e:
        print(f"Script exited with code: {e.code}")
    except Exception:
        print("Fatal Error during execution:")
        traceback.print_exc()
    finally:
        sys.stdout, sys.stderr = old_stdout, old_stderr
        return captured_output.getvalue()
