# ID Photo Maker

A simple, lightweight Python application to create official French Passport/ID photos (35x45mm) at home.

![ID Photo Maker Screenshot](https://via.placeholder.com/800x600?text=Application+Screenshot)

## Features

*   **Official Dimensions:** Ensures photos match the 35x45mm standard.
*   **Face Guides:** Overlays Cyan (Min) and Red (Max) face height guides (32-36mm) for compliance.
*   **Interactive Tools:**
    *   **Zoom:** Scroll or use slider.
    *   **Rotate:** Slider (-45° to +45°) and +90° button.
    *   **Move:** Drag to position.
*   **Print Ready:** Generates a 10x15cm (4x6") JPEG with **6 photos** tiled, ready for standard photo printing.

## Requirements

*   Linux (tested), Windows, or macOS.
*   Python 3.
*   `tkinter` (usually installed with Python).

## Download
**[Click here to download the latest version for Windows, Linux, and macOS](https://github.com/Djkawada/IDPhotoMaker/releases)**

*   **Windows:** Download `id_photo_maker.exe`
*   **Linux:** Download `id_photo_maker`
*   **macOS:** Download `id_photo_maker`

## Manual Installation (Source)

### Linux (Automatic Script)

1.  Clone this repository:
    ```bash
    git clone https://github.com/Djkawada/IDPhotoMaker.git
    cd IDPhotoMaker
    ```
2.  Run the install script:
    ```bash
    chmod +x install.sh
    ./install.sh
    ```
3.  Launch **ID Photo Maker** from your app menu.

### Manual / Other OS

1.  Install Python dependencies:
    ```bash
    pip install Pillow
    ```
2.  Run the script:
    ```bash
    python3 id_photo_maker.py
    ```

## Usage

1.  **Load:** Click "Load Image" to select a photo.
2.  **Adjust:**
    *   Zoom and Drag to frame the head.
    *   Rotate to straighten if needed.
    *   **Crucial:** Ensure the face height (Chin to Top of Skull) is **larger than the Cyan oval** and **smaller than the Red oval**.
3.  **Save:** Click "Save Printable Sheet".
4.  **Print:** Print the resulting 10x15cm image on photo paper at 100% scale (borderless).

## License

MIT License.
