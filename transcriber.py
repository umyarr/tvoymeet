import json
import os
import platform
import subprocess
import sys
import threading
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk
from PIL import Image

_DND = sys.platform != 'darwin'
if _DND:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    _extra_base: tuple = (TkinterDnD.DnDWrapper,)
else:
    _extra_base = ()


def _ffmpeg() -> str:
    if getattr(sys, 'frozen', False):
        ext = '.exe' if platform.system() == 'Windows' else ''
        candidate = Path(sys._MEIPASS) / f'ffmpeg{ext}'
        if candidate.exists():
            return str(candidate)
    return 'ffmpeg'


def _load_icon(size: tuple[int, int]) -> "ctk.CTkImage | None":
    for name in ("tvoymeet_app_icon_1781528482998.jpg", "icon.ico"):
        p = Path(__file__).parent / name
        if p.exists():
            try:
                img = Image.open(p).convert("RGBA")
                return ctk.CTkImage(light_image=img, dark_image=img, size=size)
            except Exception:
                pass
    return None


ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

C_PRIMARY  = "#5447A2"
C_PRIM_H   = "#453891"
C_ACCENT   = "#8479C4"
C_AMBER    = "#D4A043"
C_AMBER_H  = "#BE8F38"
C_GREEN    = "#47A877"
C_GREEN_H  = "#3C8F62"
C_YTDL     = "#E06B6B"
C_YTDL_H   = "#C85C5C"
C_BG       = "#F9F8FF"
C_CARD     = "#FFFFFF"
C_SEP      = "#EAE7F8"
C_DROPBG   = "#F2F0FC"
C_DROPBRD  = "#C8C1EC"
C_GRAY     = "#7B7D8C"
C_TEXT     = "#231F20"

WHISPER_MODELS = ["turbo", "large-v3", "medium", "small", "base", "tiny"]
LANGUAGES      = ["ru", "en", "auto"]
BITRATES       = ["64k", "48k", "96k", "128k"]

APP_VERSION  = "1.0.5"
GITHUB_REPO  = "umyarr/tvoymeet"


class App(ctk.CTk, *_extra_base):
    def __init__(self):
        super().__init__()
        if _DND:
            self.TkdndVersion = TkinterDnD._require(self)
        self.title("ТвойMeet")
        self.geometry("640x940")
        self.resizable(True, True)
        self.minsize(600, 500)
        self.configure(fg_color=C_BG)

        self.source_file:    str | None = None
        self.processed_file: str | None = None
        self.output_dir:     str | None = None
        self.json_path:      str | None = None
        self._busy:          bool = False

        self._build_ui()
        threading.Thread(target=self._check_update_bg, daemon=True).start()

    # ── UI ──────────────────────────────────────────────────────────────────

    def _build_ui(self):
        # ── Header ──────────────────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color=C_PRIMARY, corner_radius=0, height=80)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        left = ctk.CTkFrame(header, fg_color="transparent")
        left.pack(side="left", padx=22, pady=16)

        icon_img = _load_icon((48, 48))
        if icon_img:
            ctk.CTkLabel(left, image=icon_img, text="").pack(side="left", padx=(0, 12))

        ctk.CTkLabel(
            left, text="ТвойMeet",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color="#FFFFFF",
        ).pack(side="left")

        ctk.CTkLabel(
            header, text="транскрибация аудио и видео",
            font=ctk.CTkFont(size=13),
            text_color="#C0B8FF",
        ).pack(side="right", padx=22, pady=28)

        # ── Scrollable content ───────────────────────────────────────────────
        s = ctk.CTkScrollableFrame(self, fg_color=C_BG, scrollbar_button_color=C_DROPBRD)
        s.pack(fill="both", expand=True)
        self._s = s

        # ── Card 1: Источник ─────────────────────────────────────────────────
        c1 = self._card(s)
        self._card_title(c1, "1", "Источник")

        if _DND:
            self.drop_frame = ctk.CTkFrame(
                c1, fg_color=C_DROPBG, corner_radius=8,
                border_width=1, border_color=C_DROPBRD, height=120,
            )
            self.drop_frame.pack(fill="x", pady=(0, 10))
            self.drop_frame.pack_propagate(False)

            drop_inner = ctk.CTkFrame(self.drop_frame, fg_color="transparent")
            drop_inner.place(relx=0.5, rely=0.5, anchor="center")

            self.drop_label = ctk.CTkLabel(
                drop_inner,
                text="Перетащи файл сюда",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color=C_ACCENT,
            )
            self.drop_label.pack()
            ctk.CTkLabel(drop_inner, text="или", font=ctk.CTkFont(size=11),
                         text_color=C_GRAY).pack(pady=2)
            ctk.CTkButton(
                drop_inner, text="Выбрать на диске", command=self._open_file,
                fg_color=C_ACCENT, hover_color=C_PRIM_H,
                font=ctk.CTkFont(size=12, weight="bold"),
                width=150, height=30, corner_radius=6,
            ).pack()

            self.drop_label.drop_target_register(DND_FILES)
            self.drop_label.dnd_bind("<<Drop>>", self._on_drop)
            self.drop_frame.drop_target_register(DND_FILES)
            self.drop_frame.dnd_bind("<<Drop>>", self._on_drop)
        else:
            self.drop_label = None
            _btn_frame = ctk.CTkFrame(
                c1, fg_color=C_DROPBG, corner_radius=8,
                border_width=1, border_color=C_DROPBRD, height=80,
            )
            _btn_frame.pack(fill="x", pady=(0, 10))
            _btn_frame.pack_propagate(False)
            ctk.CTkButton(
                _btn_frame, text="Выбрать файл на диске", command=self._open_file,
                fg_color=C_ACCENT, hover_color=C_PRIM_H,
                font=ctk.CTkFont(size=13, weight="bold"),
                width=200, height=40, corner_radius=6,
            ).place(relx=0.5, rely=0.5, anchor="center")

        self.file_label = ctk.CTkLabel(
            c1, text="Файл не выбран",
            text_color=C_GRAY, font=ctk.CTkFont(size=12),
        )
        self.file_label.pack(anchor="w", pady=(0, 12))

        ctk.CTkLabel(c1, text="Или вставь ссылку для скачивания:",
                     text_color=C_GRAY, font=ctk.CTkFont(size=11)).pack(anchor="w", pady=(0, 4))

        yt_row = ctk.CTkFrame(c1, fg_color="transparent")
        yt_row.pack(fill="x")
        self.yt_entry = ctk.CTkEntry(
            yt_row, placeholder_text="https://...",
            fg_color=C_CARD, border_color=C_DROPBRD, text_color=C_TEXT, height=34,
        )
        self.yt_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self._btn_ytdlp = ctk.CTkButton(
            yt_row, text="Скачать", command=self._run_ytdlp,
            fg_color=C_YTDL, hover_color=C_YTDL_H, width=100, height=34, corner_radius=6,
        )
        self._btn_ytdlp.pack(side="left")

        yt_mode_row = ctk.CTkFrame(c1, fg_color="transparent")
        yt_mode_row.pack(anchor="w", pady=(6, 0))
        self.yt_mode = ctk.StringVar(value="audio")
        ctk.CTkRadioButton(
            yt_mode_row, text="Только аудио (mp3)", variable=self.yt_mode, value="audio",
            fg_color=C_ACCENT, hover_color=C_PRIM_H, text_color=C_TEXT,
        ).pack(side="left", padx=(0, 20))
        ctk.CTkRadioButton(
            yt_mode_row, text="Видео (mp4)", variable=self.yt_mode, value="video",
            fg_color=C_ACCENT, hover_color=C_PRIM_H, text_color=C_TEXT,
        ).pack(side="left")

        # ── Card 2: FFmpeg ───────────────────────────────────────────────────
        c2 = self._card(s)
        self._card_title(c2, "2", "FFmpeg — извлечение аудио")

        r1 = ctk.CTkFrame(c2, fg_color="transparent")
        r1.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(r1, text="Битрейт:", text_color=C_TEXT,
                     font=ctk.CTkFont(size=12, weight="bold")).pack(side="left")
        self.bitrate_var = ctk.StringVar(value="64k")
        ctk.CTkOptionMenu(
            r1, values=BITRATES, variable=self.bitrate_var, width=90, height=32,
            fg_color=C_CARD, button_color=C_ACCENT, button_hover_color=C_PRIM_H,
            text_color=C_TEXT, dropdown_text_color=C_TEXT, corner_radius=6,
        ).pack(side="left", padx=(8, 24))
        ctk.CTkLabel(r1, text="Формат:", text_color=C_TEXT,
                     font=ctk.CTkFont(size=12, weight="bold")).pack(side="left")
        self.audio_fmt_var = ctk.StringVar(value="mp3")
        ctk.CTkOptionMenu(
            r1, values=["mp3", "wav"], variable=self.audio_fmt_var, width=90, height=32,
            fg_color=C_CARD, button_color=C_ACCENT, button_hover_color=C_PRIM_H,
            text_color=C_TEXT, dropdown_text_color=C_TEXT, corner_radius=6,
        ).pack(side="left", padx=8)

        cut_row = ctk.CTkFrame(c2, fg_color="transparent")
        cut_row.pack(fill="x", pady=(0, 8))
        self.cut_mode = ctk.StringVar(value="full")
        ctk.CTkRadioButton(
            cut_row, text="Весь файл", variable=self.cut_mode, value="full",
            command=self._toggle_cut, fg_color=C_ACCENT, hover_color=C_PRIM_H, text_color=C_TEXT,
        ).pack(side="left", padx=(0, 24))
        ctk.CTkRadioButton(
            cut_row, text="Только фрагмент", variable=self.cut_mode, value="fragment",
            command=self._toggle_cut, fg_color=C_ACCENT, hover_color=C_PRIM_H, text_color=C_TEXT,
        ).pack(side="left")

        self.cut_frame = ctk.CTkFrame(c2, fg_color="transparent")
        self.cut_frame.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(self.cut_frame, text="От:", text_color=C_TEXT,
                     font=ctk.CTkFont(size=12)).pack(side="left")
        self.start_entry = ctk.CTkEntry(
            self.cut_frame, placeholder_text="00:00:00", width=105, height=32,
            border_color=C_DROPBRD, fg_color=C_CARD, text_color=C_TEXT, corner_radius=6,
        )
        self.start_entry.pack(side="left", padx=(8, 20))
        ctk.CTkLabel(self.cut_frame, text="До:", text_color=C_TEXT,
                     font=ctk.CTkFont(size=12)).pack(side="left")
        self.end_entry = ctk.CTkEntry(
            self.cut_frame, placeholder_text="00:18:00", width=105, height=32,
            border_color=C_DROPBRD, fg_color=C_CARD, text_color=C_TEXT, corner_radius=6,
        )
        self.end_entry.pack(side="left", padx=8)
        self._toggle_cut()

        self._btn_ffmpeg = ctk.CTkButton(
            c2, text="Обработать FFmpeg", command=self._run_ffmpeg,
            fg_color=C_AMBER, hover_color=C_AMBER_H,
            text_color="#1a1a1a", font=ctk.CTkFont(size=13, weight="bold"),
            height=38, corner_radius=8,
        )
        self._btn_ffmpeg.pack(fill="x")

        # ── Card 3: Whisper ──────────────────────────────────────────────────
        c3 = self._card(s)
        self._card_title(c3, "3", "Whisper — транскрибация")

        r2 = ctk.CTkFrame(c3, fg_color="transparent")
        r2.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(r2, text="Модель:", text_color=C_TEXT,
                     font=ctk.CTkFont(size=12, weight="bold")).pack(side="left")
        self.model_var = ctk.StringVar(value="turbo")
        ctk.CTkOptionMenu(
            r2, values=WHISPER_MODELS, variable=self.model_var, width=120, height=32,
            fg_color=C_CARD, button_color=C_ACCENT, button_hover_color=C_PRIM_H,
            text_color=C_TEXT, dropdown_text_color=C_TEXT, corner_radius=6,
        ).pack(side="left", padx=(8, 24))
        ctk.CTkLabel(r2, text="Язык:", text_color=C_TEXT,
                     font=ctk.CTkFont(size=12, weight="bold")).pack(side="left")
        self.lang_var = ctk.StringVar(value="ru")
        ctk.CTkOptionMenu(
            r2, values=LANGUAGES, variable=self.lang_var, width=90, height=32,
            fg_color=C_CARD, button_color=C_ACCENT, button_hover_color=C_PRIM_H,
            text_color=C_TEXT, dropdown_text_color=C_TEXT, corner_radius=6,
        ).pack(side="left", padx=8)

        ctk.CTkLabel(c3, text="Форматы вывода:", text_color=C_TEXT,
                     font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(0, 6))
        fmt_row = ctk.CTkFrame(c3, fg_color="transparent")
        fmt_row.pack(fill="x", pady=(0, 10))
        self.fmt_vars: dict[str, ctk.BooleanVar] = {}
        for fmt in ["txt", "json", "srt", "vtt", "tsv"]:
            v = ctk.BooleanVar(value=(fmt in {"txt", "json", "srt"}))
            self.fmt_vars[fmt] = v
            ctk.CTkCheckBox(
                fmt_row, text=fmt, variable=v, width=68,
                fg_color=C_ACCENT, hover_color=C_PRIM_H,
                checkmark_color="#FFFFFF", text_color=C_TEXT, corner_radius=4,
            ).pack(side="left", padx=4)

        self._btn_whisper = ctk.CTkButton(
            c3, text="Транскрибировать", command=self._run_whisper,
            fg_color=C_ACCENT, hover_color=C_PRIM_H,
            font=ctk.CTkFont(size=13, weight="bold"),
            height=38, corner_radius=8,
        )
        self._btn_whisper.pack(fill="x")

        # ── MD button ────────────────────────────────────────────────────────
        md_wrap = ctk.CTkFrame(s, fg_color="transparent")
        md_wrap.pack(fill="x", padx=16, pady=8)
        ctk.CTkButton(
            md_wrap, text="Редактировать промпт для LLM",
            command=self._edit_prompt_template,
            fg_color=C_CARD, hover_color=C_SEP,
            border_width=1, border_color=C_DROPBRD,
            text_color=C_GRAY, font=ctk.CTkFont(size=12),
            height=32, corner_radius=8,
        ).pack(fill="x", pady=(0, 6))
        ctk.CTkButton(
            md_wrap, text="Собрать .md для LLM",
            command=self._build_md,
            fg_color=C_GREEN, hover_color=C_GREEN_H,
            font=ctk.CTkFont(size=14, weight="bold"),
            height=46, corner_radius=10,
        ).pack(fill="x")

        # ── Card 4: Лог ──────────────────────────────────────────────────────
        c4 = self._card(s)
        self._card_title(c4, "4", "Лог работы")
        self.log_box = ctk.CTkTextbox(
            c4, height=150,
            font=ctk.CTkFont(family="Courier New", size=11),
            fg_color="#F4F3FC", border_color=C_SEP, border_width=1,
            text_color=C_TEXT, state="disabled", corner_radius=6,
        )
        self.log_box.pack(fill="x")

        ctk.CTkFrame(s, height=16, fg_color=C_BG).pack()

    def _card(self, parent) -> ctk.CTkFrame:
        card = ctk.CTkFrame(
            parent, fg_color=C_CARD, corner_radius=12,
            border_width=1, border_color=C_SEP,
        )
        card.pack(fill="x", padx=16, pady=8, ipady=2)
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=20, pady=14)
        return inner

    def _card_title(self, parent, number: str, text: str):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(anchor="w", pady=(0, 12))
        ctk.CTkLabel(
            frame, text=f"{number}. {text}",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=C_PRIMARY,
        ).pack(anchor="w")
        ctk.CTkFrame(frame, height=2, width=60, fg_color=C_ACCENT).pack(anchor="w", pady=(3, 0))

    # ── Helpers ─────────────────────────────────────────────────────────────

    def _log(self, msg: str):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def _log_replace_last(self, msg: str):
        self.log_box.configure(state="normal")
        self.log_box.delete("end-1l", "end")
        self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def _set_busy(self, busy: bool):
        self._busy = busy
        state = "disabled" if busy else "normal"
        self._btn_ffmpeg.configure(state=state)
        self._btn_whisper.configure(state=state)
        self._btn_ytdlp.configure(state=state)

    def _toggle_cut(self):
        s = "normal" if self.cut_mode.get() == "fragment" else "disabled"
        self.start_entry.configure(state=s)
        self.end_entry.configure(state=s)

    # ── File input ──────────────────────────────────────────────────────────

    def _on_drop(self, event):
        path = event.data.strip().strip("{}")
        self._set_file(path)

    def _open_file(self):
        path = filedialog.askopenfilename(
            filetypes=[
                ("Медиафайлы", "*.mp4 *.mkv *.avi *.mov *.mp3 *.wav *.m4a *.flac *.ogg *.webm"),
                ("Все файлы", "*.*"),
            ]
        )
        if path:
            self._set_file(path)

    def _set_file(self, path: str):
        self.source_file    = path
        self.processed_file = None
        self.json_path      = None
        name = Path(path).name
        self.file_label.configure(text=name, text_color=C_GREEN)
        if self.drop_label:
            self.drop_label.configure(text=f"✓  {name}", text_color=C_GREEN)
        self._log(f"> Файл: {path}")

    # ── yt-dlp ──────────────────────────────────────────────────────────────

    def _run_ytdlp(self):
        url = self.yt_entry.get().strip()
        if not url:
            self._log("! Вставь ссылку")
            return
        if self._busy:
            return
        self._set_busy(True)
        threading.Thread(target=self._ytdlp_worker, args=(url,), daemon=True).start()

    def _ytdlp_worker(self, url: str):
        out_dir = Path.home() / "Downloads"
        out_tpl = str(out_dir / "source.%(ext)s")
        if self.yt_mode.get() == "video":
            cmd = ["yt-dlp", "-f", "bv*+ba/b", "--newline", "-o", out_tpl, url]
            ext, label = "mp4", "видео"
        else:
            cmd = ["yt-dlp", "-x", "--audio-format", "mp3", "--audio-quality", "5", "--newline", "-o", out_tpl, url]
            ext, label = "mp3", "аудио"
        self._log(f"> yt-dlp: скачиваю {label}...")
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace",
        )
        last_was_progress = False
        for line in proc.stdout:
            line = line.rstrip()
            if not line:
                continue
            is_progress = line.startswith("[download]") and "%" in line
            if is_progress and last_was_progress:
                self._log_replace_last(line)
            else:
                self._log(line)
            last_was_progress = is_progress
        proc.wait()
        if proc.returncode == 0:
            files = sorted(out_dir.glob(f"*.{ext}"), key=lambda f: f.stat().st_mtime, reverse=True)
            if files:
                self._set_file(str(files[0]))
                self._log(f"✓ Скачано: {files[0].name}")
            else:
                self._log("! Файл не найден после скачивания")
        else:
            self._log("! Ошибка yt-dlp")
        self.after(0, self._set_busy, False)

    # ── FFmpeg ──────────────────────────────────────────────────────────────

    def _run_ffmpeg(self):
        if not self.source_file:
            self._log("! Выбери файл или скачай по ссылке")
            return
        if self._busy:
            return
        self._set_busy(True)
        threading.Thread(target=self._ffmpeg_worker, daemon=True).start()

    def _ffmpeg_worker(self):
        src     = Path(self.source_file)
        fmt     = self.audio_fmt_var.get()
        bitrate = self.bitrate_var.get()
        out     = src.parent / f"{src.stem}_audio.{fmt}"
        cmd = [_ffmpeg(), "-y"]
        if self.cut_mode.get() == "fragment":
            start = self.start_entry.get().strip() or "00:00:00"
            end   = self.end_entry.get().strip()
            cmd  += ["-ss", start]
            if end:
                cmd += ["-to", end]
        cmd += ["-i", str(src), "-vn"]
        cmd += ["-c:a", "libmp3lame", "-b:a", bitrate] if fmt == "mp3" else ["-c:a", "pcm_s16le"]
        cmd.append(str(out))
        self._log("> FFmpeg запущен...")
        res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if res.returncode == 0:
            self.processed_file = str(out)
            self._log(f"✓ Аудио готово: {out.name}")
        else:
            self._log("! Ошибка FFmpeg:\n" + "\n".join(res.stderr.splitlines()[-8:]))
        self.after(0, self._set_busy, False)

    # ── Whisper ─────────────────────────────────────────────────────────────

    def _run_whisper(self):
        target = self.processed_file or self.source_file
        if not target:
            self._log("! Сначала выбери файл")
            return
        if self._busy:
            return
        self._set_busy(True)
        threading.Thread(target=self._whisper_worker, args=(target,), daemon=True).start()

    def _whisper_worker(self, audio_path: str):
        try:
            from faster_whisper import WhisperModel
        except ImportError:
            self._log("! faster-whisper не установлен: pip install faster-whisper")
            return
        model_name = self.model_var.get()
        lang = self.lang_var.get() or None
        if lang == "auto":
            lang = None
        audio   = Path(audio_path)
        out_dir = audio.parent / f"transcripts_{audio.stem}"
        out_dir.mkdir(exist_ok=True)
        self.output_dir = str(out_dir)
        self._log(f"> Загружаю модель {model_name}... (первый раз — скачивается)")
        try:
            model = WhisperModel(model_name, device="cpu", compute_type="int8")
            self._log(f"> Транскрибирую: {audio.name}")
            segs_raw, info = model.transcribe(audio_path, language=lang, beam_size=5)
            segs, texts = [], []
            for seg in segs_raw:
                t = seg.text.strip()
                segs.append({"start": seg.start, "end": seg.end, "text": t})
                texts.append(t)
                self._log(f"  [{seg.start:.0f}s] {t[:70]}")
            base     = out_dir / audio.stem
            selected = {f for f, v in self.fmt_vars.items() if v.get()}
            if "txt" in selected:
                (base.with_suffix(".txt")).write_text("\n".join(texts), encoding="utf-8")
            json_data = {"language": info.language, "duration": info.duration,
                         "text": " ".join(texts), "segments": segs}
            if "json" in selected:
                jf = base.with_suffix(".json")
                jf.write_text(json.dumps(json_data, ensure_ascii=False, indent=2), encoding="utf-8")
                self.json_path = str(jf)
            if "srt" in selected:
                lines = []
                for i, seg in enumerate(segs, 1):
                    lines += [str(i), f"{_srt_t(seg['start'])} --> {_srt_t(seg['end'])}", seg["text"], ""]
                (base.with_suffix(".srt")).write_text("\n".join(lines), encoding="utf-8")
            if "vtt" in selected:
                lines = ["WEBVTT", ""]
                for seg in segs:
                    lines += [f"{_vtt_t(seg['start'])} --> {_vtt_t(seg['end'])}", seg["text"], ""]
                (base.with_suffix(".vtt")).write_text("\n".join(lines), encoding="utf-8")
            if "tsv" in selected:
                lines = ["start\tend\ttext"] + [
                    f"{seg['start']:.3f}\t{seg['end']:.3f}\t{seg['text']}" for seg in segs]
                (base.with_suffix(".tsv")).write_text("\n".join(lines), encoding="utf-8")
            self._log(f"✓ Готово → {out_dir}")
        except Exception as e:
            self._log(f"! Ошибка Whisper: {e}")
        self.after(0, self._set_busy, False)

    # ── Auto-update ─────────────────────────────────────────────────────────

    def _check_update_bg(self):
        try:
            import urllib.request, json as _json
            url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
            req = urllib.request.Request(url, headers={"User-Agent": "TvoyMeet"})
            with urllib.request.urlopen(req, timeout=8) as r:
                data = _json.loads(r.read())
            tag = data.get("tag_name", "")
            if _is_newer(tag, APP_VERSION):
                assets = {a["name"]: a["browser_download_url"] for a in data.get("assets", [])}
                key = "TvoyMeet-mac.zip" if sys.platform == "darwin" else "TvoyMeetInstaller.exe"
                dl_url = assets.get(key)
                if dl_url:
                    self.after(0, self._show_update_dialog, tag, dl_url)
        except Exception:
            pass

    def _show_update_dialog(self, version: str, url: str):
        from tkinter import messagebox
        if messagebox.askyesno("Обновление", f"Доступна версия {version}.\nУстановить сейчас?"):
            threading.Thread(target=self._install_update, args=(url,), daemon=True).start()

    def _install_update(self, url: str):
        import tempfile, urllib.request as _ureq
        tmp_dir = Path(tempfile.mkdtemp())
        dest = tmp_dir / url.split("/")[-1]
        self._log("> Скачиваю обновление...")
        def reporthook(count, block, total):
            if total > 0:
                pct = min(100, int(count * block * 100 / total))
                self._log_replace_last(f"> Скачиваю обновление... {pct}%")
        _ureq.urlretrieve(url, dest, reporthook)
        self._log("> Устанавливаю...")
        if sys.platform == "darwin":
            self._install_mac(dest, tmp_dir)
        else:
            self._install_windows(dest)

    def _install_mac(self, zip_path: Path, tmp_dir: Path):
        import zipfile
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(tmp_dir)
        new_app = tmp_dir / "TvoyMeet.app"
        if not new_app.exists():
            self._log("! Не найдено TvoyMeet.app в архиве")
            return
        if not getattr(sys, "frozen", False):
            self._log("! Автообновление работает только в собранном приложении")
            return
        current_app = Path(sys.executable).parents[2]
        script = tmp_dir / "update.sh"
        script.write_text(
            f"#!/bin/bash\n"
            f"while kill -0 {os.getpid()} 2>/dev/null; do sleep 0.3; done\n"
            f'rm -rf "{current_app}"\n'
            f'cp -R "{new_app}" "{current_app}"\n'
            f'codesign --force --deep --sign - "{current_app}"\n'
            f'open "{current_app}"\n',
            encoding="utf-8",
        )
        script.chmod(0o755)
        subprocess.Popen(["bash", str(script)], close_fds=True)
        self.after(0, self.destroy)

    def _install_windows(self, exe_path: Path):
        subprocess.Popen([str(exe_path)], creationflags=0x00000008)
        self.after(0, self.destroy)

    # ── MD builder ──────────────────────────────────────────────────────────

    def _edit_prompt_template(self):
        path = _prompt_template_path()
        if not path.exists():
            path.write_text(_default_prompt_header(), encoding='utf-8')
        if sys.platform == 'darwin':
            subprocess.Popen(['open', '-e', str(path)])
        else:
            subprocess.Popen(['notepad', str(path)])
        self._log(f"> Открыт редактор: {path.name}")

    def _build_md(self):
        json_p = self.json_path
        if not json_p and self.output_dir:
            found = list(Path(self.output_dir).glob("*.json"))
            if found:
                json_p = str(found[0])
        if not json_p:
            self._log("! Нет JSON — сначала транскрибируй")
            return
        try:
            data      = json.loads(Path(json_p).read_text(encoding="utf-8"))
            base_name = Path(json_p).stem
            language  = data.get("language", "unknown")
            segments  = data.get("segments", [])
            full_text = data.get("text", "").strip()
            duration  = float(segments[-1].get("end", 0)) if segments else 0
            out_dir   = Path(json_p).parent

            transcript_md = _build_transcript_md(base_name, language, duration, segments)
            report_md     = _build_report_md(base_name, language, duration, segments, full_text)
            prompt_md     = _get_prompt_template() + report_md

            (out_dir / f"{base_name}_transcript.md").write_text(transcript_md, encoding='utf-8')
            (out_dir / f"{base_name}_report.md").write_text(report_md, encoding='utf-8')
            (out_dir / f"{base_name}_prompt_for_llm.md").write_text(prompt_md, encoding='utf-8')

            self._log(f"✓ Готово: 3 файла → {out_dir.name}/")
        except Exception as e:
            self._log(f"! Ошибка: {e}")


# ── Pure functions ────────────────────────────────────────────────────────────

def _is_newer(remote: str, current: str) -> bool:
    def parse(v):
        return tuple(int(x) for x in v.lstrip("v").split(".") if x.isdigit())
    try:
        return parse(remote) > parse(current)
    except Exception:
        return False


def _srt_t(s: float) -> str:
    h   = int(s // 3600)
    m   = int((s % 3600) // 60)
    sec = s % 60
    return f"{h:02d}:{m:02d}:{int(sec):02d},{round((sec % 1) * 1000):03d}"


def _vtt_t(s: float) -> str:
    return _srt_t(s).replace(",", ".")


def build_ffmpeg_cmd(src: str, fmt: str, bitrate: str,
                     cut: bool, start: str, end: str) -> list[str]:
    out = str(Path(src).parent / f"{Path(src).stem}_audio.{fmt}")
    cmd = [_ffmpeg(), "-y"]
    if cut:
        cmd += ["-ss", start or "00:00:00"]
        if end:
            cmd += ["-to", end]
    cmd += ["-i", src, "-vn"]
    cmd += ["-c:a", "libmp3lame", "-b:a", bitrate] if fmt == "mp3" else ["-c:a", "pcm_s16le"]
    cmd.append(out)
    return cmd


def _format_time(seconds: float) -> str:
    total = int(seconds)
    return f"{total // 3600:02d}:{(total % 3600) // 60:02d}:{total % 60:02d}"


def _prompt_template_path() -> Path:
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent / 'prompt_template.txt'
    return Path(__file__).parent / 'prompt_template.txt'


def _default_prompt_header() -> str:
    return """\
Ты редактор, смысловой аналитик и сборщик сильных идей.

Перед тобой транскрипт аудио или видео.

Твоя задача — НЕ делать учебный тест, НЕ делать формальный отчёт и НЕ превращать материал в школьный конспект.

Твоя задача — забрать из материала всё самое ценное, живое и сильное:
- идеи
- инсайты
- удачные формулировки
- смыслы
- тезисы
- цитаты
- то, что можно использовать дальше

# Требуемая структура

## 1. Главное в одном абзаце
Сформулируй, о чём это аудио на самом деле.
Не пересказывай механически. Дай смысловую суть.

## 2. Самые сильные идеи
Выдели 10–15 главных идей.
Не иди подряд по транскрипту.
Выбирай только то, что имеет смысловую ценность.

У каждой идеи:
- короткий заголовок
- объяснение
- таймкод, если он есть в транскрипте

## 3. Сильные формулировки
Вытащи яркие, точные, необычные или полезные формулировки.

Разделяй:
- точная цитата
- смысловая формулировка

Если фраза распознана плохо, помечай:
[требует проверки по аудио]

## 4. Что можно использовать дальше

### Для поста
Что можно превратить в пост или короткую публикацию.

### Для выступления
Что можно использовать в речи, лекции, презентации.

### Для методички
Что можно превратить в материал, инструкцию, упражнение или объяснение.

### Для обсуждения с командой
Что можно вынести на командное обсуждение.

### Для личной рефлексии
Что стоит сохранить как мысль для себя.

## 5. Смысловая карта материала
Покажи, как разворачивается мысль:

```text
проблема → ключевые идеи → поворотные мысли → выводы
```

## 6. Неочевидные инсайты
Выдели то, что не лежит на поверхности, но может быть важным.

## 7. Жёсткая выжимка
Сделай 7 пунктов, которые точно стоит сохранить.

## 8. Что можно выкинуть
Кратко укажи, какие части материала выглядят техническими, проходными, повторяющимися или малозначимыми.

# Правила

- Не делай тестовые вопросы.
- Не делай задания ради заданий.
- Не делай школьный конспект.
- Не добавляй искусственную методическую структуру, если её нет в материале.
- Не выдумывай факты.
- Не добавляй того, чего нет в транскрипте.
- Не исправляй смысл.
- Если транскрипт распознан криво, восстанавливай смысл осторожно.
- Пиши живо, но структурно.
- Главная цель: сохранить самое ценное из аудио.
- Формат строго Markdown.
- Пиши на русском языке.

# Исходный материал

"""


def _get_prompt_template() -> str:
    p = _prompt_template_path()
    return p.read_text(encoding='utf-8') if p.exists() else _default_prompt_header()


def _build_transcript_md(base_name: str, language: str, duration: float, segments: list) -> str:
    lines = [
        f"# Транскрипт: {base_name}", "",
        "## Метаданные", "",
        f"- Язык: `{language}`",
        f"- Длительность: `{_format_time(duration)}`",
        f"- Количество сегментов: `{len(segments)}`", "",
        "## Транскрипт с таймкодами", "",
    ]
    current_minute = None
    for seg in segments:
        start = float(seg.get("start", 0))
        text  = seg.get("text", "").strip()
        if not text:
            continue
        minute = int(start // 60)
        if minute != current_minute:
            current_minute = minute
            lines += ["", f"### {_format_time(start)}", ""]
        lines.append(text)
    return "\n".join(lines)


def _build_report_md(base_name: str, language: str, duration: float, segments: list, full_text: str) -> str:
    lines = [
        f"# Отчёт: {base_name}", "",
        "## Метаданные", "",
        f"- Язык: `{language}`",
        f"- Длительность: `{_format_time(duration)}`",
        f"- Количество сегментов: `{len(segments)}`", "",
        "## Супер краткое содержание", "",
        "> Здесь будет саммари после обработки через LLM.", "",
        "## Саммари по темам", "",
        "> Здесь будут смысловые блоки после обработки через LLM.", "",
        "## Ключевые идеи", "",
        "> Здесь будут ключевые идеи после обработки через LLM.", "",
        "## Практические выводы", "",
        "> Здесь будут практические выводы после обработки через LLM.", "",
        "## Задачи / действия", "",
        "> Здесь будут задания и действия после обработки через LLM.", "",
        "## Цитаты и сильные формулировки", "",
        "> Здесь будут цитаты после обработки через LLM.", "",
        "## Полный текст", "",
        full_text, "",
        "## Транскрипт с таймкодами", "",
    ]
    current_minute = None
    for seg in segments:
        start = float(seg.get("start", 0))
        text  = seg.get("text", "").strip()
        if not text:
            continue
        minute = int(start // 60)
        if minute != current_minute:
            current_minute = minute
            lines += ["", f"### {_format_time(start)}", ""]
        lines.append(text)
    return "\n".join(lines)


if __name__ == "__main__":
    app = App()
    app.mainloop()
