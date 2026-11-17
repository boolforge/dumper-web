import struct
import os
import re

def decompile_snatcher_bytecode(bin_path, out_cpp_path, func_name):
    if not os.path.exists(bin_path):
        print(f"[ERR] File not found: {bin_path}")
        return

    with open(bin_path, "rb") as f:
        data = f.read()

    lines = []
    lines.append("// =================================================================")
    lines.append(f"// High-Level Native Decompiled Scene: {os.path.basename(bin_path)}")
    lines.append("// Target: Native C++ Engine (ScummVM Snatcher VM compatible)")
    lines.append("// =================================================================\n")
    lines.append('#include "snatcher/script.h"')
    lines.append('#include "snatcher/snatcher.h"')
    lines.append('#include "snatcher/ui.h"\n')
    lines.append("namespace Snatcher {")
    lines.append(f"void {func_name}(ScriptEngine *vm, ScriptContext *ctx) {{")

    pc = 0
    total = len(data)
    indent = "    "

    while pc < total - 4:
        op = data[pc]

        # Text strings
        if 0x20 <= op <= 0x7E:
            end = pc
            while end < total and (0x20 <= data[end] <= 0x7E or data[end] in [0x0A, 0x0D, 0x24, 0xC3, 0xA1, 0xA9, 0xAD, 0xB3, 0xBA, 0xB1]):
                end += 1
            if end - pc >= 4:
                txt = data[pc:end].decode("latin1", "replace").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r")
                lines.append(f'{indent}vm->displayText("{txt}");')
                pc = end
                continue

        # Common VM opcodes
        if op == 0x00:
            pc += 1
        elif op == 0x01:
            speaker = data[pc+1] if pc+1 < total else 0
            lines.append(f"{indent}vm->setSpeakerPortrait(0x{speaker:02X});")
            pc += 2
        elif op == 0x02:
            num_choices = data[pc+1] if pc+1 < total else 0
            lines.append(f"{indent}ctx->menuChoice = vm->showChoiceMenu({num_choices});")
            pc += 2
        elif op == 0x04 and pc + 3 <= total:
            target = struct.unpack(">H", data[pc+1:pc+3])[0]
            lines.append(f"{indent}goto label_0x{target:04X};")
            pc += 3
        elif op == 0x05 and pc + 4 <= total:
            flag = data[pc+1]
            target = struct.unpack(">H", data[pc+2:pc+4])[0]
            lines.append(f"{indent}if (ctx->getFlag({flag})) goto label_0x{target:04X};")
            pc += 4
        elif op == 0x06 and pc + 2 <= total:
            flag = data[pc+1]
            lines.append(f"{indent}ctx->setFlag({flag}, true);")
            pc += 2
        elif op == 0x07 and pc + 2 <= total:
            flag = data[pc+1]
            lines.append(f"{indent}ctx->setFlag({flag}, false);")
            pc += 2
        elif op == 0x09 and pc + 2 <= total:
            sfx = data[pc+1]
            lines.append(f"{indent}vm->playSoundEffect(0x{sfx:02X});")
            pc += 2
        elif op == 0x0B and pc + 2 <= total:
            track = data[pc+1]
            lines.append(f"{indent}vm->playMusicTrack({track});")
            pc += 2
        elif op == 0x0E and pc + 2 <= total:
            scene_id = data[pc+1]
            lines.append(f"{indent}vm->loadScene(0x{scene_id:02X});")
            lines.append(f"{indent}return;")
            pc += 2
        else:
            pc += 1

    lines.append("}")
    lines.append("} // namespace Snatcher\n")

    with open(out_cpp_path, "w", encoding="utf-8") as out_f:
        out_f.write("\n".join(lines))
    print(f"[OK] Generated Native C++ Logic: {out_cpp_path} ({len(lines)} lines)")

def main():
    out_native = "/storage/emulated/0/Download/Snatcher-Collection/Native-Engine-CPP"
    os.makedirs(out_native, exist_ok=True)

    decompile_snatcher_bytecode(
        "/storage/emulated/0/Download/Snatcher-Collection/SegaCD/Spanish-Translation/Extracted-Files/SP00.BIN",
        os.path.join(out_native, "scene_sp00_title_spanish.cpp"),
        "scene_sp00_title"
    )

    decompile_snatcher_bytecode(
        "/storage/emulated/0/Download/Snatcher-Collection/SegaCD/Spanish-Translation/Extracted-Files/SP05.BIN",
        os.path.join(out_native, "scene_sp05_investigation_spanish.cpp"),
        "scene_sp05_investigation"
    )

    decompile_snatcher_bytecode(
        "/storage/emulated/0/Download/Snatcher-Collection/SegaCD/Original-USA/SP05.BIN",
        os.path.join(out_native, "scene_sp05_investigation_usa.cpp"),
        "scene_sp05_investigation_usa"
    )

if __name__ == "__main__":
    main()
