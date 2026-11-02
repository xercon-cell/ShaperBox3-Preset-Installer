# -*- coding: utf-8 -*-
"""
ShaperBox 3 Universal Preset Installer (GUI)
Modern Dark Theme Edition
Supports .fxp and .fst preset files.
"""
import os
import sys
import pathlib
import sqlite3
import shutil
import datetime
import zlib
import struct
import hashlib
import tkinter as tk
from tkinter import filedialog, messagebox

ZIP_PREFIX = b"#zip#\x00"
EXPECTED_FX_ID = "CGL3"

# --- Цветовая палитра (Dark Theme / Studio Style) ---
BG_COLOR = "#18181b"       # Глубокий темно-серый фон
CARD_COLOR = "#27272a"     # Цвет блоков / полей ввода
TEXT_COLOR = "#f4f4f5"     # Основной белый текст
MUTED_TEXT = "#a1a1aa"     # Второстепенный серый текст
ACCENT_COLOR = "#10b981"   # Стильный изумрудно-зеленый (акцент)
ACCENT_HOVER = "#059669"   # Цвет при наведении на кнопку
BORDER_COLOR = "#3f3f46"   # Цвет границ

def parse_preset_file(file_path):
    data = pathlib.Path(file_path).read_bytes()
    ext = pathlib.Path(file_path).suffix.lower()
    
    if ext == ".fxp":
        if len(data) < 28 or data[:4] != b"CcnK":
            raise ValueError("Not a valid .fxp file")
        magic = data[8:12]
        fx_id = data[16:20].decode("latin-1", "ignore")
        if fx_id != EXPECTED_FX_ID:
            raise ValueError("Invalid plugin ID")
        if magic == b"FBCh":
            size = struct.unpack(">i", data[156:160])[0]
            start = 160
        elif magic == b"FPCh":
            size = struct.unpack(">i", data[56:60])[0]
            start = 60
        else:
            raise ValueError("Unknown format")
        chunk = data[start:start + size]
        
    elif ext == ".fst":
        idx = data.find(ZIP_PREFIX)
        if idx == -1:
            idx = data.find(b"CGL3")
            if idx == -1:
                raise ValueError("No ShaperBox data found in .fst")
            idx -= 4
        chunk = data[idx:]
        if not chunk.startswith(ZIP_PREFIX):
            p_zip = chunk.find(ZIP_PREFIX)
            if p_zip != -1:
                chunk = chunk[p_zip:]
            else:
                raise ValueError("Corrupted FST chunk")
    else:
        raise ValueError("Unsupported format")

    version, program_name = inspect_state(chunk)
    return chunk, version, program_name

def read_root_props(dec):
    props = {}
    try:
        pos = dec.index(b"\x00") + 1
        def cint(p):
            first = dec[p]; p += 1
            if first == 0: return 0, p
            n = first & 0x7F
            val = int.from_bytes(dec[p:p+n], "little")
            p += n
            return (-val if first & 0x80 else val), p
        count, pos = cint(pos)
        for _ in range(min(count, 64)):
            end = dec.index(b"\x00", pos)
            name = dec[pos:end].decode("utf-8", "replace")
            pos = end + 1
            n, pos = cint(pos)
            val = None
            if n > 0:
                marker = dec[pos]; body = dec[pos+1:pos+n]
                if marker == 5: val = body.split(b"\x00", 1)[0].decode("utf-8", "replace")
                elif marker == 1: val = struct.unpack("<i", body[:4])[0]
                elif marker == 6: val = struct.unpack("<q", body[:8])[0]
                pos += n
            props[name] = val
    except Exception:
        pass
    return props

def inspect_state(chunk):
    if not chunk.startswith(ZIP_PREFIX): 
        raise ValueError("Missing #zip# header")
    unpacker = zlib.decompressobj()
    dec = unpacker.decompress(chunk[len(ZIP_PREFIX):])
    props = read_root_props(dec)
    return int(props.get("version", 71)), str(props.get("ProgramName") or "")

def md5_hex(data):
    try: return hashlib.md5(data, usedforsecurity=False).hexdigest()
    except TypeError: return hashlib.md5(data).hexdigest()

class ShaperBoxInstallerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ShaperBox 3 Preset Installer")
        self.root.geometry("540x380")
        self.root.resizable(False, False)
        self.root.configure(bg=BG_COLOR)

        # Главный контейнер с отступами
        main_frame = tk.Frame(root, bg=BG_COLOR)
        main_frame.pack(fill="both", expand=True, padx=35, pady=30)

        # Заголовок
        tk.Label(main_frame, text="ShaperBox 3 Installer", font=("Segoe UI", 18, "bold"), 
                 bg=BG_COLOR, fg=TEXT_COLOR).pack(anchor="w")
        
        tk.Label(main_frame, text="Universal batch importer for .fxp and .fst presets", font=("Segoe UI", 10), 
                 bg=BG_COLOR, fg=MUTED_TEXT).pack(anchor="w", pady=(2, 20))

        # Поле выбора папки
        tk.Label(main_frame, text="Select Preset Folder:", font=("Segoe UI", 10, "bold"), 
                 bg=BG_COLOR, fg=TEXT_COLOR).pack(anchor="w", pady=(0, 5))

        path_frame = tk.Frame(main_frame, bg=BG_COLOR)
        path_frame.pack(fill="x", pady=(0, 25))

        self.path_entry = tk.Entry(path_frame, font=("Segoe UI", 10), bg=CARD_COLOR, fg=TEXT_COLOR, 
                                   insertbackground=TEXT_COLOR, relief="flat", highlightthickness=1,
                                   highlightbackground=BORDER_COLOR, highlightcolor=ACCENT_COLOR)
        self.path_entry.pack(side="left", fill="x", expand=True, ipady=8, ipadx=5, padx=(0, 10))

        browse_btn = tk.Button(path_frame, text="Browse", font=("Segoe UI", 9, "bold"), bg=CARD_COLOR, fg=TEXT_COLOR,
                               activebackground=BORDER_COLOR, activeforeground=TEXT_COLOR, relief="flat",
                               command=self.browse_folder, cursor="hand2", width=10)
        browse_btn.pack(side="right", ipady=7)

        # Главная кнопка установки
        self.install_btn = tk.Button(main_frame, text="INSTALL TO SHAPERBOX 3", font=("Segoe UI", 11, "bold"),
                                     bg=ACCENT_COLOR, fg="#ffffff", activebackground=ACCENT_HOVER, activeforeground="#ffffff",
                                     relief="flat", command=self.run_install, cursor="hand2", height=2)
        self.install_btn.pack(fill="x", pady=(0, 15))

        # Статус бар
        self.status_label = tk.Label(main_frame, text="Ready (.fxp & .fst supported)", font=("Segoe UI", 9, "italic"), 
                                     bg=BG_COLOR, fg=MUTED_TEXT)
        self.status_label.pack(anchor="w")

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, folder)

    def run_install(self):
        bank_path = self.path_entry.get().strip()
        if not bank_path or not pathlib.Path(bank_path).is_dir():
            messagebox.showerror("Error", "Please select a valid preset folder!")
            return

        appdata = os.environ.get("APPDATA")
        if not appdata:
            messagebox.showerror("Error", "Could not locate system APPDATA directory.")
            return
        
        data_dir = pathlib.Path(appdata) / "Cableguys" / "ShaperBox3"
        db_path = data_dir / "presets.db"
        if not db_path.is_file():
            messagebox.showerror("Error", f"ShaperBox 3 database not found at:\n{db_path}")
            return

        files = []
        for ext in ("*.fxp", "*.fst"):
            files.extend(pathlib.Path(bank_path).rglob(ext))

        if not files:
            messagebox.showwarning("Warning", "No .fxp or .fst files found in the selected directory!")
            return

        self.status_label.config(text="Installing presets...", fg=ACCENT_COLOR)
        self.root.update()

        try:
            script_dir = pathlib.Path(__file__).resolve().parent
            backup_dir = script_dir / "backups"
            backup_dir.mkdir(parents=True, exist_ok=True)
            stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = backup_dir / f"presets_{stamp}.db"
            shutil.copy2(str(db_path), str(backup_path))

            conn = sqlite3.connect(str(db_path))
            existing = set(r[0] for r in conn.execute("SELECT hash FROM presets"))
            
            added_count = 0
            for f in files:
                try:
                    chunk, version, program_name = parse_preset_file(f)
                    h = md5_hex(chunk)
                    if h in existing: continue

                    name = f.stem[:64]
                    
                    target = data_dir / h[0] / h[1] / (h + ".dat")
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(chunk)

                    conn.execute("INSERT INTO presets(hash, name, author, liked, version, custom) VALUES (?,?,?,?,?,?)",
                                 (h, name, "", "0", version, ""))
                    
                    rows = [("new__begin", "presets", h, "", "", "", 0)]
                    for col, val in (("liked", "0"), ("author", ""), ("custom", ""), ("name", name), ("version", str(version))):
                        rows.append(("new__part", "presets", h, "", col, val, 0))
                    rows.append(("new__end", "presets", h, "", "", "", 0))
                    conn.executemany('INSERT INTO queue(command, table_name, row_key, row_subkey, "column", value, state) VALUES (?,?,?,?,?,?,?)', rows)
                    
                    existing.add(h)
                    added_count += 1
                except Exception:
                    continue

            conn.commit()
            conn.close()

            self.status_label.config(text="Installation completed successfully!", fg=ACCENT_COLOR)
            messagebox.showinfo("Success!", f"Successfully installed {added_count} new presets (.fxp / .fst)!\nYou can now open your DAW.")

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred during installation:\n{e}")
            self.status_label.config(text="Installation failed", fg="#ef4444")

if __name__ == "__main__":
    root = tk.Tk()
    app = ShaperBoxInstallerApp(root)
    root.mainloop()