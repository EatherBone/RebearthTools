# Project Rebearth Mod Manager v1.0

![Version](https://img.shields.io/badge/version-1.0-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)

A simple tool for modifying and enhancing the visuals of **Project Rebearth**. This manager works by injecting custom JavaScript code directly into the game's Electron-based engine.

---

## Features

### Mod manager GUI
*   **Automatic ASAR Extraction**: Seamlessly unpacks game files to allow real-time code modifications.
*   **Binary Merger (Steam Fix)**: Automatically fixes Steamworks  dependencies errors.
*   **Integrated EXE Patcher**: Automatically replaces the original executable with a classic Electron version from the `assets` folder.
*   **One-Click Restore**: A built-in backup system that returns the game to its "Vanilla" state with a single click.
*   **Self-Extracting Assets**: Upon first launch, the EXE automatically extracts required resources (`icon.ico`, `project_rebearth.exe`) to the local directory.

### In-Game Panel
*   **FPS Counter**: A real-time frames-per-second display.
*   **Zen Mode**: Eliminates UI clutter, leaving only the essential stats bar visible.
*   **Ghost HUD**: Makes the interface transparent.
*   **Cinema Mode**: Adds cinematic black bars and hides the UI for beautiful panoramic views.
*   **Advanced Visual Filters**:
    *   *Vivid View*: High-contrast, saturated, vibrant colors.
    *   *Golden Hour*: Warm, sunset-style lighting.
    *   *Deep Night*: An immersive, atmospheric deep-blue night mode. And yea - it looks weird ik :D

---

## In-Game Hotkeys

| Key | Action |
|:---:|---|
| **H** | **Hide UI**: Toggle the entire interface on/off |
| **F** | **Zen Focus**: Hide everything except the resource bar |
| **T** | **Ghost HUD**: 85% transparency + click-through mode |
| **C** | **Cinema Bars**: Toggle cinematic letterboxing |
| **V** | **Vivid View**: Toggle enhanced color saturation |
| **G** | **Golden Hour**: Toggle warm sunset lighting |
| **N** | **Deep Night**: Toggle this weird filter |
| **M** | **Minimize**: Collapse/Expand the Mod Panel |

---

## Installation & Usage

1. Download the latest version from Releases.
2. Launch the program (No installation required).
3. Click **"Select Game Folder"** and point to the game's root directory (where the game EXE is located).
4. Click **"Install Mod Panel"**. The manager will automatically backup your files, unpack the ASAR, patch the EXE, and inject the code.
5. Click **"Launch Game"** or use Steam to open the game.

*To remove mods and return to the original version, simply click **"Uninstall (Restore)"**.*

---

## Building from Source

To make a build use **PyInstaller**.

1. **Install Dependencies**:
   ```bash
   pip install customtkinter pillow
   ```
2. **Prepare Files**: Ensure your project folder contains an `assets` directory with  `electron.exe` renamed into `project_rebearth.exe`.
3. **Run Build Command**:
   ```bash
   pyinstaller --noconsole --onefile --add-data "assets;assets" --icon="assets/icon.ico" --name "RebearthTools_v1.0" main.py
   ```

---


## Disclaimer
Using mods may result in unexpected game behavior. Im not responsible for any issues regarding gameplay stability. Use at your own risk.

---

**Developed with ❤️ by EatherBone**
