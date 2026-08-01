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
    print("=== Hiroyasu YSF → CHIRP CSV ===")

    if len(sys.argv) < 2:
        print("Drag and drop a YSF file onto this script.")
        input("Press ENTER to exit...")
        sys.exit(1)

    ysf_in = sys.argv[1]
    print(f"Input file: {ysf_in}")

    base = os.path.basename(ysf_in)
    name_no_ext = os.path.splitext(base)[0]

    scripts_dir = Path("scripts")
    print(f"Scripts directory: {scripts_dir.resolve()}")

    # Validate core scripts
    needed = ["YSF_to_HiroyasuCSV.py", "HiroyasuCSV_to_ChirpCSV.py"]
    for sc in needed:
        full = scripts_dir / sc
        print(f"Checking: {full}")
        if not full.exists():
            print(f"❌ ERROR: File not found: {full}")
            input("Press ENTER to exit...")
            sys.exit(1)

    inter_csv = f"{name_no_ext}.csv"

    print(f"\n✔ Decoding YSF → Hiroyasu CSV: {inter_csv}")
    run(["python", str(scripts_dir / "YSF_to_HiroyasuCSV.py"), ysf_in, inter_csv])

    print("✔ Converting Hiroyasu CSV → CHIRP CSV ...")
    run(["python", str(scripts_dir / "HiroyasuCSV_to_ChirpCSV.py"), inter_csv])

    final_csv = f"CHIRP_CSV_{name_no_ext}.csv"

    if Path("CHIRPCSV.csv").exists():
        print("✔ Renaming CHIRPCSV.csv →", final_csv)
        Path("CHIRPCSV.csv").rename(final_csv)
    else:
        print("❌ ERROR: CHIRPCSV.csv was not generated.")
        input("Press ENTER to exit...")
        sys.exit(1)

    # Delete intermediate file
    if Path(inter_csv).exists():
        print("🗑 Removing intermediate file:", inter_csv)
        Path(inter_csv).unlink()

    print("\n=== DONE ===")
    print("Generated file:", final_csv)
    input("Press ENTER to finish...")

if __name__ == "__main__":
    main()
