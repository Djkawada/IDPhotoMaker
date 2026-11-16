# ID Photo Maker

![Version](https://img.shields.io/github/v/release/Djkawada/IDPhotoMaker?include_prereleases&style=flat-square&color=blue)
![License](https://img.shields.io/github/license/Djkawada/IDPhotoMaker?style=flat-square&color=orange)
![Downloads](https://img.shields.io/github/downloads/Djkawada/IDPhotoMaker/total?style=flat-square&color=brightgreen)
![Python](https://img.shields.io/github/languages/top/Djkawada/IDPhotoMaker?style=flat-square)

A lightweight Python application with a modern dark UI to create official French Passport/ID photos (35×45 mm at 300 DPI) at home.

## Features

* **Official Dimensions:** Outputs exact 35×45 mm (413×531 px @ 300 DPI) photos on a 10×15 cm (4×6") sheet with **6 photos**.
* **EXIF Auto-Orientation & White Padding:** Automatically rotates smartphone photos using EXIF metadata and pads out-of-bounds/transparent regions with white instead of black.
* **Face Compliance Guides:** Cyan (32 mm min) and Red (36 mm max) face-height ovals with center alignment line.
* **Interactive Tools:** Drag to position, mouse-wheel/slider zoom (10–400%), fine rotation (-45° to +45°), ±90° rotate, reset, clear slot, and **10×15 Sheet Preview** before saving as JPEG or PNG.

## Requirements

* Linux, Windows, or macOS
* Python 3 + `tkinter` + `Pillow`

## Download

**[Download the latest release for Windows, Linux, and macOS](https://github.com/Djkawada/IDPhotoMaker/releases)**

## Manual Installation (Source)

### Linux (Automatic Script)
```bash
git clone https://github.com/Djkawada/IDPhotoMaker.git
cd IDPhotoMaker
chmod +x install.sh
./install.sh
```

### Manual / Other OS
```bash
pip install -r requirements.txt
python3 id_photo_maker.py
```

## License

MIT License — see [LICENSE](LICENSE).
