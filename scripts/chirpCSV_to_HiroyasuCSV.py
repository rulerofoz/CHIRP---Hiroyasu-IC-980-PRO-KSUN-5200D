import csv
import sys
import os

# -------------------------
# Helpers
# -------------------------

def chirp_power_to_hiro(p):
    p = p.strip().lower()
    try:
        if float(p.replace("w","")) >= 4:
            return "High"
    except:
        pass
    return "Low"

def chirp_bw_to_hiro(m):
    m = m.strip().upper()
    if m == "NFM":
        return "Narrow"
    return "Wide"

def build_dcs(code, pol):
    if not code or not pol:
        return "OFF"
    suf = "N" if pol == "NN" else "I"
    return f"D{code}{suf}"

def safe_get(row, *keys):
    for k in keys:
        if k in row and row[k].strip() != "":
            return row[k].strip()
    return ""


# -------------------------
# Main conversion
# -------------------------

def convert_row(row):

    name = safe_get(row, "Name", "Etiqueta", "Nombre")

    freq = float(safe_get(row, "Frequency", "Frecuencia"))

    duplex = safe_get(row, "Duplex", "Desplazamiento", "Shift")
    offset = float(safe_get(row, "Offset", "Desvío", "Shift Amt") or 0)

    mode = safe_get(row, "Mode", "Modo")

    tone_mode = safe_get(row, "Tone", "Tono", "Tone Mode")

    rTone = safe_get(row, "rToneFreq", "ToneFreq", "Tono TX", "rTone")
    cTone = safe_get(row, "cToneFreq", "cTone", "Tono RX", "CTONE")

    dtcs_code = safe_get(row, "DtcsCode", "DCS", "DCS Code")
    dtcs_pol  = safe_get(row, "DtcsPolarity", "Polarity", "Polaridad")
    dtcs_rx   = safe_get(row, "RxDtcsCode", "DCS RX", "Código DCS RX")

    crossmode = safe_get(row, "CrossMode", "Modo Cruzado")

    power = safe_get(row, "Power", "Potencia")

    # =============================
    # RX/TX FREQUENCIES
    # =============================

    rx = f"{freq:.5f}"
    d = duplex.strip().lower()

    if d == "+":
        tx = f"{freq + offset:.5f}"
    elif d == "-":
        tx = f"{freq - offset:.5f}"
    elif d == "split":
        # In CHIRP, with "split", Offset is actually the TX frequency
        tx = f"{offset:.5f}"
    elif d == "off":
        # Duplex is off, set TX column to strictly 0
        tx = "0"
    else:
        tx = f"{freq:.5f}"

    # =============================
    # TONE LOGIC
    # =============================

    tone_rx = "OFF"
    tone_tx = "OFF"

    # --- TSQL ---
    if tone_mode == "TSQL":
        # CHIRP stores the TSQL tone in cToneFreq
        tone_rx = cTone
        tone_tx = cTone

    # --- TONE ---
    elif tone_mode == "Tone":
        # Transmit tone only. RX gets OFF, TX gets the tone.
        tone_rx = "OFF"
        tone_tx = rTone

    # --- DTCS ---
    elif tone_mode == "DTCS":
        dcs_val = build_dcs(dtcs_code, dtcs_pol)
        tone_rx = dcs_val
        tone_tx = dcs_val

    # --- CROSS ---
    elif tone_mode == "Cross":
        cm = crossmode.strip()

        if cm == "->Tone":
            tone_rx = cTone
            tone_tx = "OFF"

        elif cm == "Tone->":
            tone_rx = "OFF"
            tone_tx = rTone

        elif cm == "Tone->Tone":
            tone_rx = cTone
            tone_tx = rTone

        elif cm == "->DTCS":
            dcs_val = build_dcs(dtcs_rx, dtcs_pol)  # uses RX
            tone_rx = dcs_val
            tone_tx = "OFF"

        elif cm == "DTCS->":
            dcs_val = build_dcs(dtcs_code, dtcs_pol)  # uses TX
            tone_rx = "OFF"
            tone_tx = dcs_val

        elif cm == "DTCS->DTCS":
            dtx = build_dcs(dtcs_code, dtcs_pol)
            drx = build_dcs(dtcs_rx, dtcs_pol)
            tone_rx = drx
            tone_tx = dtx

        elif cm == "DTCS->Tone":
            dcs_val = build_dcs(dtcs_code, dtcs_pol)
            tone_rx = cTone
            tone_tx = dcs_val

        elif cm == "Tone->DTCS":
            dcs_val = build_dcs(dtcs_rx, dtcs_pol)
            tone_rx = dcs_val
            tone_tx = rTone

        else:
            tone_rx = "OFF"
            tone_tx = "OFF"

    # =============================
    # POWER & BANDWIDTH
    # =============================
    pwr_hiro = chirp_power_to_hiro(power)
    bw_hiro = chirp_bw_to_hiro(mode)

    # =============================
    # OUTPUT
    # =============================
    return [
        rx, tx, tone_rx, tone_tx,
        pwr_hiro,
        bw_hiro,
        "ADD", "OFF", "OFF", "OFF", "OFF",
        name
    ]


# -------------------------
# MAIN — DRAG & DROP READY
# -------------------------

def main():
    if len(sys.argv) < 2:
        print("Drag and drop a CSV file onto this script.")
        sys.exit(1)

    infile = sys.argv[1]

    base = os.path.basename(infile)
    name_no_ext = os.path.splitext(base)[0]
    outfile = f"HIROYASU_CSV_{name_no_ext}.csv"

    with open(infile, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    out_rows = [convert_row(r) for r in rows]

    with open(outfile, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(out_rows)

    print(f"✔ File generated: {outfile}")


if __name__ == "__main__":
    main()
