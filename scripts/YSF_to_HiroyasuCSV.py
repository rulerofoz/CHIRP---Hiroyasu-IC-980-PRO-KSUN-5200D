import struct
import csv
import sys
from pathlib import Path

BASE_OFFSET  = 1440
CHANNEL_SIZE = 76
MAX_CHANNELS = 240

# ---------------- CTCSS ----------------
CTCSS_VALUES = {
    670:"67.0", 693:"69.3", 719:"71.9", 744:"74.4", 770:"77.0",
    797:"79.7", 825:"82.5", 854:"85.4", 885:"88.5", 915:"91.5",
    948:"94.8", 974:"97.4", 1000:"100.0", 1035:"103.5", 1072:"107.2",
    1109:"110.9", 1148:"114.8", 1188:"118.8", 1230:"123.0",
    1273:"127.3", 1318:"131.8", 1365:"136.5", 1413:"141.3",
    1462:"146.2", 1514:"151.4", 1567:"156.7", 1598:"159.8",
    1622:"162.2", 1655:"165.5", 1679:"167.9", 1713:"171.3",
    1738:"173.8", 1773:"177.3", 1799:"179.9", 1835:"183.5",
    1862:"186.2", 1899:"189.9", 1928:"192.8", 1966:"196.6",
    1995:"199.5", 2035:"203.5", 2065:"206.5", 2107:"210.7",
    2181:"218.1", 2257:"225.7", 2291:"229.1", 2336:"233.6",
    2418:"241.8", 2503:"250.3", 2541:"254.1",
}

# ---------------- DCS ----------------
DCS_MAP = {
    10259:"D023",10261:"D025",10262:"D026",10265:"D031",10266:"D032",
    10270:"D036",10275:"D043",10279:"D047",10281:"D051",10283:"D053",
    10284:"D054",10293:"D065",10297:"D071",10298:"D072",10299:"D073",
    10300:"D074",10316:"D114",10317:"D115",10318:"D116",10322:"D122",
    10325:"D125",10329:"D131",10330:"D132",10332:"D134",10339:"D143",
    10341:"D145",10346:"D152",10349:"D155",10350:"D156",10354:"D162",
    10357:"D165",10362:"D172",10364:"D174",10373:"D205",10378:"D212",
    10387:"D223",10389:"D225",10390:"D226",10403:"D243",10404:"D244",
    10405:"D245",10406:"D246",10409:"D251",10410:"D252",10413:"D255",
    10417:"D261",10419:"D263",10421:"D265",10422:"D266",10425:"D271",
    10428:"D274",10438:"D306",10441:"D311",10445:"D315",10453:"D325",
    10457:"D331",10458:"D332",10467:"D343",10470:"D346",10473:"D351",
    10474:"D356",10482:"D364",10483:"D365",10486:"D371",10516:"D411",
    10517:"D412",10518:"D413",10520:"D423",10521:"D431",10522:"D432",
    10534:"D445",10535:"D446",10542:"D452",10545:"D454",10546:"D455",
    10554:"D462",10556:"D464",10557:"D465",10558:"D466",10582:"D503",
    10590:"D506",10594:"D516",10599:"D523",10602:"D526",10606:"D532",
    10618:"D546",10633:"D565",10640:"D606",10643:"D612",10652:"D624",
    10657:"D627",10659:"D631",10660:"D632",10661:"D645",10668:"D654",
    10691:"D662",10698:"D664",10707:"D703",10713:"D712",10714:"D723",
    10716:"D731",10723:"D732",10724:"D734",10731:"D743",10732:"D754",
}


# ---------------- Helpers ----------------
def decode_freq(raw):
    return f"{raw/1_000_000:.5f}"


def decode_tone(b):
    code = int.from_bytes(b[:2], "little")
    flag = b[2]

    if (code == 0 and flag == 0) or code == 0xFFFF:
        return "OFF"

    if flag == 1:
        return CTCSS_VALUES.get(code, "OFF")

    if flag == 2:
        return DCS_MAP.get(code, f"D{code}") + "N"

    if flag == 3:
        return DCS_MAP.get(code, f"D{code}") + "I"

    return "OFF"


def decode_flags(b57, b58, b59):
    power = "High" if (b58 & 0x20) else "Low"
    bw    = "Wide" if (b58 & 0x10) else "Narrow"
    scan  = "ADD" if (b58 & 0x80) else "DEL"

    if b57 & 0x10:
        busy = "CAT"
    elif b57 & 0x08:
        busy = "DQT"
    else:
        busy = "OFF"

    # Special DCS
    spec_bits = ((b58 >> 2) & 0x01) | (((b58 >> 3) & 0x01) << 1)
    special = "OFF" if spec_bits == 0 else f"Special DCS {spec_bits}"

    comp = "ON" if (b58 & 0x02) else "OFF"

    scramble = f"scramble{b59}" if b59 > 0 else "OFF"

    return power, bw, scan, busy, special, comp, scramble


def decode_channel(block):

    rx_raw = struct.unpack("<I", block[0:4])[0]
    tx_raw = struct.unpack("<I", block[14:18])[0]

    rx = decode_freq(rx_raw)
    tx = decode_freq(tx_raw)

    tone_rx = decode_tone(block[28:32])
    tone_tx = decode_tone(block[41:45])

    # Correction: when TX is OFF but RX has tone → copy RX tone to TX
    if tone_tx == "OFF" and tone_rx != "OFF":
        tone_tx = tone_rx

    b57, b58, b59 = block[57], block[58], block[59]
    flags = decode_flags(b57, b58, b59)

    name = block[61:71].decode("ascii", "ignore").rstrip("\x00").strip()

    return [rx, tx, tone_rx, tone_tx, *flags, name]


def decode_file(infile, outfile="channels.csv"):

    with open(infile, "rb") as f:
        data = f.read()

    rows = []

    for i in range(MAX_CHANNELS):
        start = BASE_OFFSET + i * CHANNEL_SIZE
        block = data[start:start + CHANNEL_SIZE]

        if len(block) < CHANNEL_SIZE:
            break

        if all(b == 0xFF for b in block):
            break

        rows.append(decode_channel(block))

    # ---------------------------
    # WRITE ORIGINAL CSV OUTPUT
    # ---------------------------
    with open(outfile, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(rows)

    print("✔ CSV generated:", outfile)

    # ------------------------------------------------------
    # FINAL CLEAN-UP → REMOVE KNOWN EMPTY ROWS
    # ------------------------------------------------------
    TARGET_ROW = [
        "0.00000","0.00000","OFF","OFF","Low",
        "Narrow","DEL","OFF","OFF","OFF","OFF",""
    ]

    def rows_equal(r):
        r = (r + [""]*12)[:12]
        return r == TARGET_ROW

    cleaned = [r for r in rows if not rows_equal(r)]

    with open(outfile, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(cleaned)

    print("✔ Empty rows removed")
    print(f"  Final line count: {len(cleaned)}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python decoder.py input.YSF [output.csv]")
        sys.exit(1)

    infile = sys.argv[1]
    outfile = sys.argv[2] if len(sys.argv) >= 3 else "channels.csv"
    decode_file(infile, outfile)
