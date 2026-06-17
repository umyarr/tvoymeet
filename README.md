# ТвойMeet

Транскрибация аудио и видео прямо на компьютере. Без облаков. Без подписок.

![ТвойMeet](tvoymeet_app_icon_1781528482998.jpg)

## Что умеет

- Перетащить файл или вставить ссылку (YouTube, VK, Rutube и др.)
- Извлечь аудио через FFmpeg с обрезкой по времени
- Транскрибировать через Whisper локально (модели от tiny до large-v3)
- Сохранить результат в txt, json, srt, vtt, tsv
- Собрать `.md` с транскриптом и промптом для LLM

## Скачать

Смотри раздел [Releases](../../releases) — там готовые сборки:

- `TvoyMeet-mac.zip` — приложение для macOS
- `TvoyMeetInstaller.exe` — установщик для Windows

### Первый запуск на macOS

macOS блокирует приложения без подписи Apple. Два способа обойти:

**Способ 1 — через Терминал** (надёжнее):
```bash
xattr -cr ~/Downloads/TvoyMeet.app
open ~/Downloads/TvoyMeet.app
```

**Способ 2 — через Finder**:
Правый клик на `TvoyMeet.app` → **Открыть** → **Открыть** в диалоге.

## Запуск из исходников

```bash
git clone https://github.com/umyarr/tvoymeet
cd tvoymeet
python -m venv .venv
# Windows:
.venv\Scripts\activate.bat
# Mac/Linux:
source .venv/bin/activate

pip install -r requirements.txt
python transcriber.py
```

Нужен ffmpeg в системе или рядом с `transcriber.py`.

## Стек

- [customtkinter](https://github.com/TomSchimansky/CustomTkinter) — интерфейс
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) — транскрибация
- [tkinterdnd2](https://github.com/pmgagne/tkinterdnd2) — drag & drop (только Windows)
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) — скачивание по ссылке
- PyInstaller — сборка в .exe / .app
