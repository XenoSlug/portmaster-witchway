#!/usr/bin/env python3
"""
patch_witchway.py - Prepares game.port for WitchWay from the Windows purchase
Usage: python3 patch_witchway.py [path to WitchWay.exe or WitchWay zip]
"""
import sys, os, struct, zipfile, tempfile, shutil, subprocess

def main():
    if len(sys.argv) < 2:
        src = "WitchWay.exe"
        if not os.path.exists(src):
            for candidate in ["WitchWay 1-12 WIN .zip", "../WitchWay 1-12 WIN .zip", "assets/WitchWay.exe"]:
                if os.path.exists(candidate):
                    src = candidate
                    break
    else:
        src = sys.argv[1]

    if not os.path.exists(src):
        print(f"Error: file '{src}' not found!")
        sys.exit(1)

    print(f"Processing: {src}")
    with tempfile.TemporaryDirectory() as tmpdir:
        exe_path = src
        if src.lower().endswith(".zip"):
            print("Extracting zip...")
            with zipfile.ZipFile(src, "r") as z:
                z.extractall(tmpdir)
            for root, _, files in os.walk(tmpdir):
                for f in files:
                    if f.lower() == "witchway.exe":
                        exe_path = os.path.join(root, f)
                        break

        with open(exe_path, "rb") as f:
            data = f.read()

        cab_pos = data.find(b"MSCF")
        cab_out = os.path.join(tmpdir, "cab_out")
        os.makedirs(cab_out, exist_ok=True)

        if cab_pos != -1:
            cab_file = os.path.join(tmpdir, "witchway.cab")
            with open(cab_file, "wb") as cf:
                cf.write(data[cab_pos:])
            print(f"Extracting CAB ({len(data)-cab_pos} bytes)...")
            res = subprocess.run(["tar", "-xf", cab_file, "-C", cab_out], capture_output=True)
            if res.returncode != 0:
                subprocess.run(["bsdtar", "-xf", cab_file, "-C", cab_out], check=True)

        inner_exe = os.path.join(cab_out, "WitchWay.exe")
        if not os.path.exists(inner_exe):
            inner_exe = exe_path

        with open(inner_exe, "rb") as tf:
            tdata = tf.read()

        pos = 0
        extracted = False
        while True:
            idx = tdata.find(b"FORM", pos)
            if idx == -1: break
            if tdata[idx+8:idx+12] == b"GEN8":
                form_size = struct.unpack("<I", tdata[idx+4:idx+8])[0] + 8
                with open(os.path.join(cab_out, "game.droid"), "wb") as df:
                    df.write(tdata[idx:idx+form_size])
                print(f"Extracted game.droid ({form_size} bytes)")
                extracted = True
                break
            pos = idx + 4

        if not extracted and len(tdata) > 4832208:
            form_size = struct.unpack("<I", tdata[4832208+4:4832208+8])[0] + 8
            with open(os.path.join(cab_out, "game.droid"), "wb") as df:
                df.write(tdata[4832208:4832208+form_size])
            print("Extracted game.droid using standard offset!")
            extracted = True

        if not extracted:
            print("Failed to extract data.win / game.droid!")
            sys.exit(1)

        out_zip = "game.port"
        print(f"Building {out_zip}...")
        with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_STORED) as zf:
            zf.write(os.path.join(cab_out, "game.droid"), "game.droid")
            for item in os.listdir(cab_out):
                if item.startswith("mus") and item.endswith(".ogg") or item == "audiogroup1.dat" or item.endswith(".ini"):
                    zf.write(os.path.join(cab_out, item), item)
                    print(f"  Added {item}")

        print(f"Done! Created '{out_zip}' ({os.path.getsize(out_zip)} bytes).")

if __name__ == "__main__":
    main()
