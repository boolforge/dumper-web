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


def package_artifacts(source_dir="/home/pyodide/virtual_out", subpath="", output_zip="/home/pyodide/scummvm_dump.zip"):
    """Package extracted artifacts (or subpath) into a DEFLATE-compressed ZIP.

    Iterates through the target hierarchy sequentially to keep memory usage O(1)
    relative to total archive size, preventing browser WebAssembly out-of-memory errors.
    """
    import zipfile

    base_dir = os.getcwd()
    src = source_dir if os.path.isabs(source_dir) else os.path.join(base_dir, source_dir)
    target = os.path.join(src, subpath) if subpath else src

    if not os.path.exists(target):
        raise FileNotFoundError(f"Target path does not exist: {target}")

    out_zip = output_zip if os.path.isabs(output_zip) else os.path.join(base_dir, output_zip)
    if os.path.exists(out_zip):
        os.remove(out_zip)

    count = 0
    with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        if os.path.isfile(target):
            zf.write(target, os.path.basename(target))
            count = 1
        else:
            for root, dirs, files in os.walk(target):
                for file in files:
                    abs_path = os.path.join(root, file)
                    rel_path = os.path.relpath(abs_path, target)
                    zf.write(abs_path, rel_path)
                    count += 1

    size = os.path.getsize(out_zip)
    return {"count": count, "size": size, "path": out_zip}


def get_extracted_summary(source_dir="/home/pyodide/virtual_out"):
    """Inspect the extracted directory hierarchy and return structural statistics."""
    base_dir = os.getcwd()
    src = source_dir if os.path.isabs(source_dir) else os.path.join(base_dir, source_dir)
    if not os.path.exists(src):
        return {"items": [], "file_count": 0, "total_bytes": 0}

    items = []
    total_files = 0
    total_bytes = 0

    for entry in sorted(os.listdir(src)):
        entry_path = os.path.join(src, entry)
        if os.path.isdir(entry_path):
            folder_files = 0
            folder_bytes = 0
            for root, dirs, files in os.walk(entry_path):
                folder_files += len(files)
                for f in files:
                    folder_bytes += os.path.getsize(os.path.join(root, f))
            total_files += folder_files
            total_bytes += folder_bytes
            items.append({
                "name": entry,
                "is_dir": True,
                "file_count": folder_files,
                "bytes": folder_bytes
            })
        else:
            f_size = os.path.getsize(entry_path)
            total_files += 1
            total_bytes += f_size
            items.append({
                "name": entry,
                "is_dir": False,
                "file_count": 1,
                "bytes": f_size
            })

    return {
        "items": items,
        "file_count": total_files,
        "total_bytes": total_bytes
    }


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
