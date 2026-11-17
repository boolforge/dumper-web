"""WebAssembly Python execution bridge for ScummVM Dumper Companion.

Interfaces browser JavaScript event handlers with dumper-companion.py running
inside Pyodide WebAssembly virtual environments.
"""

import sys
import io
import os
import runpy
import importlib.util

_dumper = None


def _get_dumper():
    """Lazily load and cache dumper-companion module.

    Registers the module in sys.modules prior to execution to support dataclass
    type introspection and relative lookups under Python 3.14.
    """
    global _dumper
    if _dumper is None:
        base_dir = os.getcwd()
        script_path = os.path.join(base_dir, "dumper-companion.py")
        if os.path.exists(script_path):
            spec = importlib.util.spec_from_file_location("dumper_companion", script_path)
            _dumper = importlib.util.module_from_spec(spec)
            sys.modules["dumper_companion"] = _dumper
            spec.loader.exec_module(_dumper)
    return _dumper


def process_task_advanced(command, filename, extra_args):
    """Execute dumper-companion CLI routine with captured I/O streams.

    Args:
        command: Subcommand string ('probe', 'iso', 'cue', 'ccd', 'mds', '3do', 'unecm', etc.).
        filename: Target media filename or path staged in Pyodide MEMFS.
        extra_args: List of optional CLI flags (--japanese, --forcemacbinary, etc.).

    Returns:
        Captured terminal stdout/stderr log output as a string.
    """
    import shutil

    output_io = io.StringIO()
    sys.stdout = output_io
    sys.stderr = output_io

    try:
        base_dir = os.getcwd()
        script_path = os.path.join(base_dir, "dumper-companion.py")
        input_path = filename if os.path.isabs(filename) else os.path.join(base_dir, filename)
        output_dir = os.path.join(base_dir, "virtual_out")

        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        os.makedirs(output_dir, exist_ok=True)

        if command == "createmacfonts":
            sys.argv = ["dumper-companion.py", "createmacfonts"]
        elif command == "probe":
            sys.argv = ["dumper-companion.py", "probe", input_path]
        elif command == "unecm":
            sys.argv = ["dumper-companion.py", "unecm", input_path]
        else:
            sys.argv = ["dumper-companion.py", command, input_path, output_dir] + extra_args

        runpy.run_path(script_path, run_name="__main__")
        print("✅ Ritual Complete.")
    except SystemExit as se:
        if se.code not in (0, None):
            print(f"\n[Command exited with status {se.code}]")
        else:
            print("✅ Ritual Complete.")
    except Exception as e:
        print(f"\n[THE ORACLE HAS ENCOUNTERED A VISION ERROR]\n{e}")
    finally:
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__

    return output_io.getvalue()


def translate_string(text, to_punycode=True):
    """Bidirectional converter between Punycode ASCII and Japanese Shift-JIS strings."""
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
