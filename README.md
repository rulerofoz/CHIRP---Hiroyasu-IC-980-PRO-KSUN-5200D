# CHIRP to Hiroyasu / KSUN CSV Converter Fork

This is a fork of the original work by **[lu7cgj](https://github.com/lu7cgj/CHIRP---Hiroyasu-IC-980-PRO-KSUN-5200D)**.

---

## What's New & Fixed in This Fork

* **Corrected Tone Processing:** Fixed the encoder logic to ensure transmit (`rToneFreq`) and receive (`cToneFreq`) sub-audible tones map accurately based on the channel's tone mode (supporting standard `Tone`, `TSQL`, and custom tone behaviors).
* **Duplex "Off" Handling:** Added proper condition checks so that when a channel's Duplex setting is set to **`off`**, the transmit frequency exports cleanly as `0` instead of forcing a calculated offset.

---

## Instructions

1. **Download:** Grab this entire repository and extract it to a folder on your computer.
2. **Install Python:** Ensure you have Python installed. *Tip: Make sure to check the box to **Add Python to PATH** during the installation setup.*
3. **Prepare Your Channels:** Create and export a new CSV file using [CHIRP](https://chirp.danplanet.com/). Keep your channel names to **10 characters or less** for best compatibility.
4. **Setup Files:** Place your exported CHIRP CSV file in the same folder next to the conversion script (`ChirpCSV_to_YSF.py`).
5. **Convert:** Simply **drag and drop** your CHIRP CSV file directly onto the `ChirpCSV_to_YSF.py` script.
6. **Done!** The script will generate a new CSV/YSF file in the folder, ready to be opened with the CPS software for your radio.

---

## Additional Resources

* **Radio CPS Software:** If you need the Programming Software (CPS), it can typically be found on the [ABBREE website](https://abbree.com/).
* **Archive Backup:** An archived backup copy is also hosted on the [Internet Archive for safe keeping](https://archive.org/details/sf-8118).
