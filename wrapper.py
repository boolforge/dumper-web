import sys
import io
import traceback
import runpy

def process_file(*args):
    old_stdout, old_stderr = sys.stdout, sys.stderr
    captured_output = io.StringIO()
    sys.stdout = sys.stderr = captured_output

    try:
        sys.argv = ['dumper-companion.py'] + list(args)
        print(f"Starting processing with args: {sys.argv[1:]}")
        runpy.run_path('dumper-companion.py', run_name='__main__')
    except SystemExit as e:
        print(f"Script exited with code: {e.code}")
    except Exception:
        print("Fatal Error during execution:")
        traceback.print_exc()
    finally:
        sys.stdout, sys.stderr = old_stdout, old_stderr
        return captured_output.getvalue()
