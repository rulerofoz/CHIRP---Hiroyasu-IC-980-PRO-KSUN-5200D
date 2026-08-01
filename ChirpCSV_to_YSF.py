import os
import sys
import subprocess
from pathlib import Path

def run(cmd):
    print(f"→ Running: {' '.join(cmd)}")
    p = subprocess.run(cmd)
    if p.returncode != 0:
        print("❌ ERROR running command")
        sys.exit(1)

def main():
    print("=== CHIRP CSV → YSF ===")

    if len(sys.argv) < 2:
        print("Drag and drop a CHIRP CSV file onto this script.")
        input("Press ENTER to exit...")
        sys.exit(1)

    chirp_csv = sys.argv[1]
    print(f"Received file: {chirp_csv}")

    base = os.path.basename(chirp_csv)
    name_no_ext = os.path.splitext(base)[0]

    scripts_dir = Path("scripts")
    print(f"Scripts directory: {scripts_dir.resolve()}")

    needed = ["chirpCSV_to_HiroyasuCSV.py", "HiroyasuCSV_to_YSF.py"]
    for sc in needed:
        full = scripts_dir / sc
        print(f"Checking: {full}")
        if not full.exists():
            print(f"❌ ERROR: File not found: {full}")
            input("Press ENTER to exit...")
            sys.exit(1)

    inter_csv = f"HIROYASU_CSV_{name_no_ext}.csv"

    print(f"\n✔ Converting CHIRP CSV → Hiroyasu CSV: {inter_csv}")
    run(["python", str(scripts_dir / "chirpCSV_to_HiroyasuCSV.py"), chirp_csv])

    print("✔ Generating YSF ...")
    run(["python", str(scripts_dir / "HiroyasuCSV_to_YSF.py"), inter_csv])

    generated = Path(inter_csv).with_suffix(".ysf")
    final_ysf = f"YSF_{name_no_ext}.ysf"

    print("Looking for generated file:", generated)

    if generated.exists():
        print("✔ Renaming:", generated, "→", final_ysf)
        generated.rename(final_ysf)
    else:
        print("❌ ERROR: The YSF file was not generated:", generated)
        input("Press ENTER to exit...")
        sys.exit(1)

    # delete intermediate files
    if Path(inter_csv).exists():
        print("🗑 Removing intermediate file:", inter_csv)
        Path(inter_csv).unlink()

    leftover = Path(f"{inter_csv}.ysf")
    if leftover.exists():
        print("🗑 Removing leftover file:", leftover)
        leftover.unlink()

    print("\n=== DONE ===")
    print("Generated file:", final_ysf)
    input("Press ENTER to finish...")

if __name__ == "__main__":
    main()
