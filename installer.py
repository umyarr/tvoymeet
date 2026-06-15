import os
import shutil
import sys
import threading
import winreg
from pathlib import Path
import customtkinter as ctk
from tkinter import filedialog

# ── palette ────────────────────────────────────────────────────────────────
C_PRIMARY = "#8479C4"
C_PRIM_H  = "#7268B3"
C_BG      = "#F9F8FF"
C_GREEN   = "#5BA87E"
C_GRAY    = "#AAAAAA"
C_TEXT    = "#2D2D2D"

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

DEFAULT_INSTALL = str(Path.home() / "AppData" / "Local" / "TvoyMeet")


def _bundle_dir() -> Path:
    """Return path to bundled TvoyMeet directory."""
    base = Path(sys._MEIPASS) if getattr(sys, "frozen", False) else Path(__file__).parent / "dist"
    return base / "TvoyMeet"


def _register_uninstall(exe_path: str, uninstall_cmd: str, install_dir: str) -> None:
    key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\TvoyMeet"
    try:
        key = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE)
        values = {
            "DisplayName":     "ТвойMeet",
            "DisplayVersion":  "1.0",
            "Publisher":       "ТвойMeet",
            "InstallLocation": install_dir,
            "DisplayIcon":     exe_path,
            "UninstallString": f'cmd /c "{uninstall_cmd}"',
            "NoModify":        1,
            "NoRepair":        1,
        }
        for name, val in values.items():
            if isinstance(val, int):
                winreg.SetValueEx(key, name, 0, winreg.REG_DWORD, val)
            else:
                winreg.SetValueEx(key, name, 0, winreg.REG_SZ, val)
        winreg.CloseKey(key)
    except Exception:
        pass  # registry write optional — doesn't block install


def _create_shortcut(target: str, shortcut_path: str, working_dir: str) -> None:
    """Create a .lnk shortcut using VBScript."""
    vbs = f"""
Set oWS = WScript.CreateObject("WScript.Shell")
sLinkFile = "{shortcut_path}"
Set oLink = oWS.CreateShortcut(sLinkFile)
oLink.TargetPath = "{target}"
oLink.WorkingDirectory = "{working_dir}"
oLink.Description = "ТвойMeet — транскрибация аудио и видео"
oLink.Save
"""
    vbs_path = Path(os.environ.get("TEMP", "C:/Temp")) / "create_shortcut.vbs"
    vbs_path.write_text(vbs, encoding="utf-8")
    os.system(f'cscript //nologo "{vbs_path}"')
    try:
        vbs_path.unlink()
    except Exception:
        pass


class InstallerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("ТвойMeet — Установка")
        self.geometry("520x400")
        self.resizable(False, False)
        self.configure(fg_color=C_BG)

        self._build_ui()

    def _build_ui(self):
        # ── header ──────────────────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color=C_PRIMARY, corner_radius=0, height=70)
        header.pack(fill="x")
        header.pack_propagate(False)

        ctk.CTkLabel(
            header,
            text="ТвойMeet",
            font=("Segoe UI", 26, "bold"),
            text_color="white",
        ).pack(side="left", padx=24, pady=16)

        ctk.CTkLabel(
            header,
            text="v1.0",
            font=("Segoe UI", 13),
            text_color="#D0CEFF",
        ).pack(side="left", pady=20)

        # ── body ─────────────────────────────────────────────────────────────
        body = ctk.CTkFrame(self, fg_color=C_BG, corner_radius=0)
        body.pack(fill="both", expand=True, padx=32, pady=20)

        ctk.CTkLabel(
            body,
            text="Транскрибация аудио и видео прямо на компьютере.\nБез облаков. Без подписок.",
            font=("Segoe UI", 13),
            text_color=C_TEXT,
            justify="left",
        ).pack(anchor="w", pady=(0, 20))

        # install path row
        ctk.CTkLabel(body, text="Папка установки:", font=("Segoe UI", 12, "bold"),
                     text_color=C_TEXT).pack(anchor="w")

        path_row = ctk.CTkFrame(body, fg_color=C_BG)
        path_row.pack(fill="x", pady=(4, 16))

        self._path_var = ctk.StringVar(value=DEFAULT_INSTALL)
        self._path_entry = ctk.CTkEntry(
            path_row, textvariable=self._path_var,
            font=("Segoe UI", 12), height=36, fg_color="white",
            border_color="#C8C4E8",
        )
        self._path_entry.pack(side="left", fill="x", expand=True)

        ctk.CTkButton(
            path_row, text="...", width=44, height=36,
            fg_color=C_PRIMARY, hover_color=C_PRIM_H,
            command=self._browse,
        ).pack(side="left", padx=(6, 0))

        # shortcut checkbox
        self._shortcut_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            body,
            text="Создать ярлык на рабочем столе",
            variable=self._shortcut_var,
            font=("Segoe UI", 12),
            text_color=C_TEXT,
            fg_color=C_PRIMARY,
            hover_color=C_PRIM_H,
            checkmark_color="white",
        ).pack(anchor="w", pady=(0, 20))

        # progress bar (hidden until install)
        self._progress = ctk.CTkProgressBar(body, fg_color="#E0DEFF", progress_color=C_PRIMARY)
        self._progress.set(0)
        self._progress.pack(fill="x", pady=(0, 8))
        self._progress.pack_forget()

        self._status = ctk.CTkLabel(body, text="", font=("Segoe UI", 11), text_color=C_GRAY)
        self._status.pack(anchor="w")

        # ── footer ───────────────────────────────────────────────────────────
        footer = ctk.CTkFrame(self, fg_color="#EEEAF8", corner_radius=0, height=56)
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)

        self._install_btn = ctk.CTkButton(
            footer,
            text="  Установить",
            font=("Segoe UI", 13, "bold"),
            height=36, width=160,
            fg_color=C_PRIMARY,
            hover_color=C_PRIM_H,
            command=self._start_install,
        )
        self._install_btn.pack(side="right", padx=20, pady=10)

        ctk.CTkButton(
            footer,
            text="Отмена",
            font=("Segoe UI", 12),
            height=36, width=100,
            fg_color="#D0CEFF",
            hover_color="#C0BEFF",
            text_color=C_PRIMARY,
            command=self.destroy,
        ).pack(side="right", pady=10)

    def _browse(self):
        chosen = filedialog.askdirectory(title="Выбрать папку установки")
        if chosen:
            self._path_var.set(str(Path(chosen) / "TvoyMeet"))

    def _start_install(self):
        self._install_btn.configure(state="disabled")
        self._progress.pack(fill="x", pady=(0, 8))
        self._progress.set(0)
        threading.Thread(target=self._install, daemon=True).start()

    def _install(self):
        try:
            dest = Path(self._path_var.get().strip())
            src = _bundle_dir()

            self._set_status("Подготовка…")
            self._progress.set(0.05)

            if dest.exists():
                shutil.rmtree(dest)
            dest.mkdir(parents=True, exist_ok=True)

            # Copy files
            entries = list(src.rglob("*"))
            total = max(len(entries), 1)
            for i, entry in enumerate(entries):
                rel = entry.relative_to(src)
                tgt = dest / rel
                if entry.is_dir():
                    tgt.mkdir(parents=True, exist_ok=True)
                else:
                    tgt.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(entry, tgt)
                self._progress.set(0.05 + 0.80 * (i + 1) / total)
                if i % 50 == 0:
                    self._set_status(f"Копирование… {i+1}/{total}")

            exe_path = dest / "TvoyMeet.exe"

            # Write uninstaller script
            self._set_status("Создание удалятора…")
            uninstall_bat = dest / "uninstall.bat"
            bat_lines = [
                "@echo off",
                "echo Удаление ТвойMeet...",
                'reg delete "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\TvoyMeet" /f >nul 2>&1',
                'del "%USERPROFILE%\\Desktop\\ТвойMeet.lnk" >nul 2>&1',
                "cd /d %TEMP%",
                f'rmdir /s /q "{dest}"',
            ]
            uninstall_bat.write_text("\r\n".join(bat_lines), encoding="cp866", errors="replace")

            # Register in Windows "Apps & features"
            self._set_status("Регистрация в системе…")
            self._progress.set(0.88)
            _register_uninstall(str(exe_path), str(uninstall_bat), str(dest))

            self._set_status("Создание ярлыка…")
            self._progress.set(0.93)

            if self._shortcut_var.get():
                desktop = Path(os.environ.get("USERPROFILE", "~")) / "Desktop"
                _create_shortcut(
                    str(exe_path),
                    str(desktop / "ТвойMeet.lnk"),
                    str(dest),
                )

            self._progress.set(1.0)
            self._set_status("Готово! ТвойMeet установлен.")
            self.after(0, self._show_success, str(exe_path))

        except Exception as e:
            self.after(0, self._set_status, f"Ошибка: {e}")
            self.after(0, lambda: self._install_btn.configure(state="normal"))

    def _set_status(self, text: str):
        self.after(0, lambda: self._status.configure(text=text))

    def _show_success(self, exe_path: str):
        self._install_btn.configure(
            text="Запустить ТвойMeet",
            state="normal",
            fg_color=C_GREEN,
            hover_color="#4A9A6E",
            command=lambda: self._launch_and_exit(exe_path),
        )

    def _launch_and_exit(self, exe_path: str):
        import subprocess
        subprocess.Popen([exe_path], creationflags=0x00000008)  # DETACHED_PROCESS
        self.destroy()


if __name__ == "__main__":
    app = InstallerApp()
    app.mainloop()
