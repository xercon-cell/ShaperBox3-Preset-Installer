# ShaperBox 3 Universal Preset Installer 🎛️

A professional standalone GUI tool to easily import external `.fxp` and FL Studio `.fst` preset banks into **Cableguys ShaperBox 3** on Windows.

## ⚠️ The Problem
ShaperBox 3 does not read plain preset files from folders directly. Instead, it stores user presets inside a local SQLite database (`%APPDATA%\Cableguys\ShaperBox3\presets.db`) using custom-hashed `.dat` payloads and binary queue states. Doing this manually is tedious and frustrating.

## ✨ Features
* **Universal Support:** Automatically parses and converts both `.fxp` banks and FL Studio `.fst` state files.
* **Smart Duplicate Prevention:** Skips presets that already exist in your database using MD5 hashing.
* **Automatic Backups:** Safely creates a timestamped backup of your `presets.db` before making any changes.
* **Modern Studio GUI:** Clean dark-mode interface designed for a seamless user experience.
* **Batch Import:** Instantly processes dozens or hundreds of presets in a single click.

## 🚀 How to Use
1. Download the latest `sb3_gui_installer.exe` from the **Releases** section.
2. Run the application.
3. Click **Browse** and select the folder containing your `.fxp` or `.fst` presets (subfolders are scanned automatically).
4. Click **INSTALL TO SHAPERBOX 3**.
5. Open your DAW — all new presets will instantly appear under the **MY PRESETS** tab in ShaperBox 3!

## 🛠️ Built With
* Python / Tkinter
* PyInstaller (compiled to a standalone `.exe`)