#!/usr/bin/env python3
"""
patch_witchway.py - Prepares game.port for WitchWay from any purchase (itch.io, Steam, Humble)
Supports: WitchWay.exe, WitchWay zip, data.win, loose files, or game.droid
"""
import sys, os, struct, zipfile, tempfile, shutil, subprocess, glob

def find_files(search_dir, pattern):
    matches = []
    for root, _, files in os.walk(search_dir):
        for f in files:
            if pattern.startswith("*") and pattern.endswith("*"):
                if pattern[1:-1].lower() in f.lower():
                    matches.append(os.path.join(root, f))
            elif pattern.startswith("*"):
                if f.lower().endswith(pattern[1:].lower()):
                    matches.append(os.path.join(root, f))
            elif pattern.endswith("*"):
                if f.lower().startswith(pattern[:-1].lower()):
                    matches.append(os.path.join(root, f))
            else:
                if f.lower() == pattern.lower():
                    matches.append(os.path.join(root, f))
    return matches

def extract_form_gen8(data):
    """Dynamically locates GameMaker FORM...GEN8 chunk and returns exact payload"""
    pos = 0
    while True:
        idx = data.find(b"FORM", pos)
        if idx == -1:
            break
        if len(data) >= idx + 12 and data[idx+8:idx+12] == b"GEN8":
            chunk_size = struct.unpack("<I", data[idx+4:idx+8])[0] + 8
            if idx + chunk_size <= len(data):
                return data[idx:idx+chunk_size]
        pos = idx + 4
    return None

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    gamedir = os.path.abspath(os.path.join(script_dir, ".."))
    assets_dir = os.path.join(gamedir, "assets")
    target_port = os.path.join(gamedir, "game.port")

    print(f"=== WitchWay Asset Preparation ===")
    print(f"Game directory: {gamedir}")
    print(f"Assets directory: {assets_dir}")

    # If game.port already exists and is valid (>5MB), nothing to do
    if os.path.exists(target_port) and os.path.getsize(target_port) > 5000000:
        try:
            with zipfile.ZipFile(target_port, "r") as z:
                if "game.droid" in z.namelist():
                    print(f"Valid game.port already exists ({os.path.getsize(target_port)} bytes).")
                    return 0
        except Exception:
            pass

    with tempfile.TemporaryDirectory(prefix="witchway_patch_") as tmpdir:
        # 1. Unpack any zip or 7z files found in assets or gamedir
        archives = []
        for d in [assets_dir, gamedir]:
            if os.path.exists(d):
                for f in os.listdir(d):
                    fp = os.path.join(d, f)
                    if os.path.isfile(fp) and (f.lower().endswith(".zip") or f.lower().endswith(".7z") or f.lower().endswith(".rar")):
                        archives.append(fp)

        for arch in archives:
            print(f"Extracting archive: {arch}")
            if arch.lower().endswith(".zip"):
                try:
                    with zipfile.ZipFile(arch, "r") as z:
                        z.extractall(tmpdir)
                except Exception as e:
                    print(f"Warning extracting {arch} with zipfile: {e}")
            # Try 7zzs if available
            sevenzip = os.path.join(gamedir, "tools", "7zzs")
            if os.path.exists(sevenzip) and os.access(sevenzip, os.X_OK):
                subprocess.run([sevenzip, "x", arch, f"-o{tmpdir}", "-y"], capture_output=True)

        # 2. Look for existing data.win or game.droid directly
        search_dirs = [assets_dir, tmpdir, gamedir]
        droid_bytes = None

        for d in search_dirs:
            for fname in ["data.win", "game.droid", "data.droid"]:
                matches = find_files(d, fname)
                if matches:
                    print(f"Found GameMaker data file: {matches[0]}")
                    with open(matches[0], "rb") as f:
                        droid_bytes = f.read()
                    break
            if droid_bytes:
                break

        # 3. If no loose data.win, extract from WitchWay.exe
        if not droid_bytes:
            exe_matches = []
            for d in search_dirs:
                exe_matches.extend(find_files(d, "*witchway*.exe"))
                exe_matches.extend(find_files(d, "*.exe"))

            # Deduplicate preserving order
            unique_exes = []
            for ep in exe_matches:
                if ep not in unique_exes and os.path.isfile(ep):
                    unique_exes.append(ep)

            for ep in unique_exes:
                print(f"Inspecting executable: {ep}")
                with open(ep, "rb") as f:
                    edata = f.read()

                # Check if executable has an embedded CAB
                mscf_idx = edata.find(b"MSCF")
                if mscf_idx != -1:
                    print(f"Found embedded CAB at offset {mscf_idx} in {ep}")
                    cab_file = os.path.join(tmpdir, "inner.cab")
                    cab_dir = os.path.join(tmpdir, "cab_extracted")
                    os.makedirs(cab_dir, exist_ok=True)
                    with open(cab_file, "wb") as cf:
                        cf.write(edata[mscf_idx:])
                    # Try extracting cab with 7zzs or tar
                    sevenzip = os.path.join(gamedir, "tools", "7zzs")
                    if os.path.exists(sevenzip) and os.access(sevenzip, os.X_OK):
                        subprocess.run([sevenzip, "x", cab_file, f"-o{cab_dir}", "-y"], capture_output=True)
                    subprocess.run(["tar", "-xf", cab_file, "-C", cab_dir], capture_output=True)

                    # Look inside cab_dir for data.win or exe
                    for cn in ["data.win", "game.droid"]:
                        c_matches = find_files(cab_dir, cn)
                        if c_matches:
                            with open(c_matches[0], "rb") as f:
                                droid_bytes = f.read()
                            break

                    if not droid_bytes:
                        c_exes = find_files(cab_dir, "*.exe")
                        for ce in c_exes:
                            with open(ce, "rb") as f:
                                cdata = f.read()
                            droid_bytes = extract_form_gen8(cdata)
                            if droid_bytes:
                                print(f"Extracted game.droid from inner exe: {ce}")
                                break

                if droid_bytes:
                    break

                # Extract FORM...GEN8 directly from executable
                droid_bytes = extract_form_gen8(edata)
                if droid_bytes:
                    print(f"Extracted game.droid directly from {ep} ({len(droid_bytes)} bytes)")
                    break

                # Fallback: check standard offset if present
                if len(edata) > 4832208 + 12 and edata[4832208+8:4832208+12] == b"GEN8":
                    fsize = struct.unpack("<I", edata[4832208+4:4832208+8])[0] + 8
                    droid_bytes = edata[4832208:4832208+fsize]
                    print(f"Extracted game.droid via standard offset ({len(droid_bytes)} bytes)")
                    break

        if not droid_bytes:
            print("ERROR: Could not locate or extract GameMaker data (data.win / game.droid)!")
            return 1

        # 4. Collect audio and config files (audiogroup*.dat, mus*.ogg, *.ogg, *.ini)
        audio_files = {}
        for d in search_dirs:
            for root, _, files in os.walk(d):
                for f in files:
                    fl = f.lower()
                    if fl.startswith("mus") and (fl.endswith(".ogg") or fl.endswith(".wav")):
                        audio_files[f] = os.path.join(root, f)
                    elif fl == "audiogroup1.dat" or fl.startswith("audiogroup"):
                        audio_files[f] = os.path.join(root, f)
                    elif fl.endswith(".ini") or fl.endswith(".ogg"):
                        audio_files[f] = os.path.join(root, f)

        # 5. Assemble game.port
        print(f"Assembling {target_port} with {len(audio_files)} companion files...")
        temp_port = os.path.join(tmpdir, "game.port.tmp")
        with zipfile.ZipFile(temp_port, "w", compression=zipfile.ZIP_STORED) as zf:
            zf.writestr("game.droid", droid_bytes)
            for fname, fpath in audio_files.items():
                try:
                    zf.write(fpath, fname)
                    print(f"  Added {fname} ({os.path.getsize(fpath)} bytes)")
                except Exception as e:
                    print(f"  Warning adding {fname}: {e}")

        # Atomic move to final destination
        if os.path.exists(target_port):
            os.remove(target_port)
        shutil.move(temp_port, target_port)

        port_size = os.path.getsize(target_port)
        print(f"Successfully generated {target_port} ({port_size} bytes)!")
        return 0

if __name__ == "__main__":
    sys.exit(main())
