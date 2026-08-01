import csv
import sys
import os

CHIRP_HEADER = [
    "Location","Name","Frequency","Duplex","Offset","Tone",
    "rToneFreq","cToneFreq","DtcsCode","DtcsPolarity","RxDtcsCode",
    "CrossMode","Mode","TStep","Skip","Power","Comment",
    "URCALL","RPT1CALL","RPT2CALL","DVCODE"
]

def is_off(x: str) -> bool:
    x = x.strip().upper()
    return x == "" or x == "OFF"

def is_dcs(x: str) -> bool:
    x = x.strip().upper()
    if not x.startswith("D"):
        return False
    if len(x) < 5:
        return False
    mid = x[1:4]
    suf = x[4]
    return mid.isdigit() and suf in ("N", "I")

def is_ctcss(x: str) -> bool:
    x = x.strip().upper()
    if is_off(x):
        return False
    if x.startswith("D"):
        return False
    return "." in x  # e.g., 67.0, 136.5

def parse_dcs(x: str):
    x = x.strip().upper()
    if not is_dcs(x):
        return None, None
    code = x[1:4]
    suf = x[4]
    pol = "NN" if suf == "N" else "NR"
    return code, pol

def power_to_chirp(pwr: str) -> str:
    p = pwr.strip().lower()
    if p == "high":
        return "5.0W"
    return "1.0W"

def bandwidth_to_mode(bw: str) -> str:
    b = bw.strip().lower()
    if b == "narrow":
        return "NFM"
    return "FM"

def convert_row(idx, row):

    rx_str = row[0].strip()
    tx_str = row[1].strip()
    tone_rx = row[2].strip()
    tone_tx = row[3].strip()
    pwr_raw = row[4].strip()
    bw_raw  = row[5].strip()
    name    = row[11].strip()

    # -------------------------------------------------------
    # FREQUENCIES
    # -------------------------------------------------------
    try:
        rx_f = float(rx_str)
        tx_f = float(tx_str)
    except:
        rx_f = tx_f = 0.0

    diff = abs(tx_f - rx_f)

    # -------------------------------------------------------
    # DUPLEX LOGIC (with SPLIT support)
    # -------------------------------------------------------
    if diff < 0.00001:
        # Simplex
        duplex = ""
        offset = "0.000000"

    elif diff > 10:
        # SPLIT (CHIRP uses TX as exact offset)
        duplex = "split"
        offset = f"{tx_f:.6f}"

    else:
        # Standard offset (+/-)
        if tx_f > rx_f:
            duplex = "+"
            off = tx_f - rx_f
        else:
            duplex = "-"
            off = rx_f - tx_f
        offset = f"{off:.6f}"

    freq_out = f"{rx_f:.6f}"

    # -------------------------------------------------------
    # FIXED CHIRP FIELDS
    # -------------------------------------------------------
    mode = bandwidth_to_mode(bw_raw)
    tstep = "5.00"
    skip = ""
    power = power_to_chirp(pwr_raw)
    comment = ur = rpt1 = rpt2 = dv = ""

    # -------------------------------------------------------
    # TONE DETECTION
    # -------------------------------------------------------
    off_rx = is_off(tone_rx)
    off_tx = is_off(tone_tx)
    ctcss_rx = is_ctcss(tone_rx)
    ctcss_tx = is_ctcss(tone_tx)
    dcs_rx = is_dcs(tone_rx)
    dcs_tx = is_dcs(tone_tx)

    tone = ""
    r_tone = ""
    c_tone = ""
    dtcs_code = ""
    dtcs_pol = ""
    dtcs_rx = ""
    crossmode = ""

    # ============================================================
    # 1) BOTH OFF → CHIRP DEFAULTS
    # ============================================================
    if off_rx and off_tx:
        tone = ""
        r_tone = "88.5"
        c_tone = "88.5"
        dtcs_code = "023"
        dtcs_pol = "NN"
        dtcs_rx = "023"
        crossmode = "Tone->Tone"

    # ============================================================
    # 2) BOTH CTCSS
    # ============================================================
    elif ctcss_rx and ctcss_tx:
        if tone_rx == tone_tx:
            tone = "TSQL"
            r_tone = tone_rx
            c_tone = tone_rx
            dtcs_code = "023"
            dtcs_pol = "NN"
            dtcs_rx = "023"
            crossmode = "Tone->Tone"
        else:
            tone = "Cross"
            r_tone = tone_tx
            c_tone = tone_rx
            dtcs_code = "023"
            dtcs_pol = "NN"
            dtcs_rx = "023"
            crossmode = "Tone->Tone"

    # ============================================================
    # 3) TX CTCSS, RX OFF → Tone
    # ============================================================
    elif ctcss_tx and off_rx:
        tone = "Tone"
        r_tone = tone_tx
        c_tone = "88.5"
        dtcs_code = "023"
        dtcs_pol = "NN"
        dtcs_rx = "023"
        crossmode = "Tone->Tone"

    # ============================================================
    # 4) RX CTCSS, TX OFF → ->Tone
    # ============================================================
    elif ctcss_rx and off_tx:
        tone = "Cross"
        r_tone = "88.5"
        c_tone = tone_rx
        dtcs_code = "023"
        dtcs_pol = "NN"
        dtcs_rx = "023"
        crossmode = "->Tone"

    # ============================================================
    # 5) BOTH DCS → DTCS
    # ============================================================
    elif dcs_rx and dcs_tx:
        if tone_rx == tone_tx:
            code, pol = parse_dcs(tone_rx)
            tone = "DTCS"
            r_tone = "88.5"
            c_tone = "88.5"
            dtcs_code = code or "023"
            dtcs_pol = pol or "NN"
            dtcs_rx = dtcs_code
            crossmode = "Tone->Tone"
        else:
            code_tx, pol_tx = parse_dcs(tone_tx)
            code_rx, pol_rx = parse_dcs(tone_rx)
            tone = "Cross"
            r_tone = "88.5"
            c_tone = "88.5"
            dtcs_code = code_tx
            dtcs_pol = pol_tx
            dtcs_rx = code_rx
            crossmode = "DTCS->DTCS"

    # ============================================================
    # 6) TX DCS, RX OFF → DTCS->
    # ============================================================
    elif dcs_tx and off_rx:
        code, pol = parse_dcs(tone_tx)
        tone = "Cross"
        r_tone = "88.5"
        c_tone = "88.5"
        dtcs_code = code
        dtcs_pol = pol
        dtcs_rx = code
        crossmode = "DTCS->"

    # ============================================================
    # 7) RX DCS, TX OFF → ->DTCS
    # ============================================================
    elif dcs_rx and off_tx:
        code, pol = parse_dcs(tone_rx)
        tone = "Cross"
        r_tone = "88.5"
        c_tone = "88.5"
        dtcs_code = code
        dtcs_pol = pol
        dtcs_rx = code
        crossmode = "->DTCS"

    # ============================================================
    # 8) MIXED CTCSS + DCS
    # ============================================================
    elif dcs_tx and ctcss_rx:
        code, pol = parse_dcs(tone_tx)
        tone = "Cross"
        r_tone = "88.5"
        c_tone = tone_rx
        dtcs_code = code
        dtcs_pol = pol
        dtcs_rx = "023"
        crossmode = "DTCS->Tone"

    elif ctcss_tx and dcs_rx:
        code, pol = parse_dcs(tone_rx)
        tone = "Cross"
        r_tone = tone_tx
        c_tone = "88.5"
        dtcs_code = "023"
        dtcs_pol = pol
        dtcs_rx = code
        crossmode = "Tone->DTCS"

    # ============================================================
    # 9) ANY OTHER CASE → CHIRP DEFAULTS
    # ============================================================
    else:
        tone = ""
        r_tone = "88.5"
        c_tone = "88.5"
        dtcs_code = "023"
        dtcs_pol = "NN"
        dtcs_rx = "023"
        crossmode = "Tone->Tone"

    return [
        str(idx), name, freq_out, duplex, offset,
        tone, r_tone, c_tone,
        dtcs_code, dtcs_pol, dtcs_rx,
        crossmode, mode, tstep, skip, power,
        comment, ur, rpt1, rpt2, dv
    ]


def main():
    if len(sys.argv) < 2:
        print("Drag and drop a Hiroyasu CSV file onto this script.")
        sys.exit(1)

    infile = sys.argv[1]
    outfile = "CHIRPCSV.csv"

    with open(infile, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        rows = list(reader)

    out_rows = [CHIRP_HEADER]

    for i, r in enumerate(rows):
        if not r or all(c.strip() == "" for c in r):
            continue
        out_rows.append(convert_row(i, r))

    with open(outfile, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(out_rows)

    print(f"✔ File generated: {outfile}")

if __name__ == "__main__":
    main()
