import struct
import csv
import sys
from decimal import Decimal
from pathlib import Path

# ---------------------------------------------------
# CONSTANTS
# ---------------------------------------------------
BASE_OFFSET  = 1440
CHANNEL_SIZE = 76
MAX_CHANNELS = 240    # always 240 memory channels on the radio


# ---------------------------------------------------
# AUTO-SELECT BASE DEPENDING ON NUMBER OF CHANNELS
# ---------------------------------------------------
def get_base_file(csv_rows_count):
    """
    Returns the corresponding baseN.ysf file.
    Example: if there are 85 rows → base85.ysf
    """
    base_name = f"base{csv_rows_count}.ysf"

    # ⬇️ Minimal change: search inside the "bases" subfolder
    path = Path("bases") / base_name

    if not path.exists():
        print(f"❌ ERROR: File {base_name} not found inside 'bases' folder")
        sys.exit(1)

    print(f"✔ Using base file: {base_name}")
    return path.read_bytes()


# ---------------------------------------------------
# CTCSS / DCS TABLES
# ---------------------------------------------------
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
CTCSS_ENCODE = {v:k for k,v in CTCSS_VALUES.items()}

def load_dcs():
    return {
        "023":10259,"025":10261,"026":10262,"031":10265,"032":10266,
        "036":10270,"043":10275,"047":10279,"051":10281,"053":10283,
        "054":10284,"065":10293,"071":10297,"072":10298,"073":10299,
        "074":10300,"114":10316,"115":10317,"116":10318,"122":10322,
        "125":10325,"131":10329,"132":10330,"134":10332,"143":10339,
        "145":10341,"152":10346,"155":10349,"156":10350,"162":10354,
        "165":10357,"172":10362,"174":10364,"205":10373,"212":10378,
        "223":10387,"225":10389,"226":10390,"243":10403,"244":10404,
        "245":10405,"246":10406,"251":10409,"252":10410,"255":10413,
        "261":10417,"263":10419,"265":10421,"266":10422,"271":10425,
        "274":10428,"306":10438,"311":10441,"315":10445,"325":10453,
        "331":10457,"332":10458,"343":10467,"346":10470,"351":10473,
        "356":10474,"364":10482,"365":10483,"371":10486,"411":10516,
        "412":10517,"413":10518,"423":10520,"431":10521,"432":10522,
        "445":10534,"446":10535,"452":10542,"454":10545,"455":10546,
        "462":10554,"464":10556,"465":10557,"466":10558,"503":10582,
        "506":10590,"516":10594,"523":10599,"526":10602,"532":10606,
        "546":10618,"565":10633,"606":10640,"612":10643,"624":10652,
        "627":10657,"631":10659,"632":10660,"645":10661,"654":10668,
        "662":10691,"664":10698,"703":10707,"712":10713,"723":10714,
        "731":10716,"732":10723,"734":10724,"743":10731,"754":10732,
    }

DCS_ENCODE = load_dcs()


# ---------------------------------------------------
# TONE ENCODING
# ---------------------------------------------------
def encode_tone(t: str) -> bytes:
    if not t or t.upper()=="OFF":
        return b"\x00\x00\x00\x00"
    t=t.strip()

    # DCS
    if t.startswith("D") and (t.endswith("N") or t.endswith("I")):
        body = t[1:-1]
        mode = t[-1]
        flag = 2 if mode=="N" else 3
        if body.isdigit():
            code = DCS_ENCODE.get(body, int(body))
            return struct.pack("<HBx", code, flag)

    # CTCSS
    if t in CTCSS_ENCODE:
        code = CTCSS_ENCODE[t]
        return struct.pack("<HBx", code, 1)

    return b"\x00\x00\x00\x00"


# ---------------------------------------------------
# EMPTY CHANNEL BLOCK
# ---------------------------------------------------
def empty_channel_block():
    return b"\x00" * CHANNEL_SIZE


# ---------------------------------------------------
# ENCODER
# ---------------------------------------------------
def encode(template: bytes, rows, out_path: str):
    data = bytearray(template)

    for ch in range(MAX_CHANNELS):
        off = BASE_OFFSET + ch * CHANNEL_SIZE

        if ch >= len(rows):
            data[off:off+CHANNEL_SIZE] = empty_channel_block()
            continue

        r = rows[ch]
        rx_str = r[0] if len(r) > 0 else ""

        if rx_str.strip() in ("", "0", "0.0", "0.00000"):
            data[off:off+CHANNEL_SIZE] = empty_channel_block()
            continue

        blk = bytearray(CHANNEL_SIZE)

        # Frequencies
        rx = int(Decimal(r[0]) * 1_000_000)
        tx = int(Decimal(r[1]) * 1_000_000)

        blk[0:4]   = struct.pack("<I", rx)
        blk[14:18] = struct.pack("<I", tx)

        # Tones
        blk[28:32] = encode_tone(r[2])
        blk[41:45] = encode_tone(r[3])

        # Flags
        power   = r[4].lower()
        bw      = r[5].lower()
        scan    = r[6].upper()
        busy    = r[7].upper()
        special = r[8]
        comp    = r[9].upper()
        scramble= r[10]
        name    = r[11]

        # Byte 57
        b57 = 0
        if busy == "DQT": 
            b57 |= 0x08
        elif busy == "CAT": 
            b57 |= 0x10
        blk[57] = b57

        # Byte 58
        b58 = 0
        if power == "high": b58 |= 0x20
        if bw == "wide":    b58 |= 0x10
        if scan == "ADD":   b58 |= 0x80
        if special.upper().startswith("SPECIAL"):
            n = int(special.split()[-1])
            if n & 1: b58 |= 0x04
            if n & 2: b58 |= 0x08
        if comp == "ON": b58 |= 0x02
        blk[58] = b58

        # Scramble
        if scramble.lower().startswith("scramble"):
            blk[59] = int(scramble.replace("scramble", ""))
        else:
            blk[59] = 0

        # Name
        blk[61:71] = name[:10].encode("ascii", "ignore").ljust(10, b"\x00")

        data[off:off+CHANNEL_SIZE] = blk

    Path(out_path).write_bytes(data)
    print("✔ YSF generated:", out_path)


# ---------------------------------------------------
# MAIN
# ---------------------------------------------------
def main():
    if len(sys.argv) < 2:
        print("Drag and drop a CSV file onto this script to run it.")
        sys.exit(1)

    # CSV passed via drag & drop
    csv_file = sys.argv[1]

    # Auto-generate output name:
    #   channels.csv → channels.ysf
    out_file = str(Path(csv_file).with_suffix(".ysf"))

    print(f"✔ CSV detected: {csv_file}")
    print(f"✔ YSF file to generate: {out_file}")

    # Load CSV
    with open(csv_file, newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))

    # Load correct base file
    base_bytes = get_base_file(len(rows))

    # Generate YSF
    encode(base_bytes, rows, out_file)


if __name__ == "__main__":
    main()
