# ТвойMeet — запуск на Mac

---

## Вариант А — через терминал (для проверки)

### 1. Установи ffmpeg

```bash
brew install ffmpeg
```

Нет Homebrew? Сначала установи: https://brew.sh

### 2. Создай окружение и установи пакеты

```bash
cd путь/до/папки
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Запусти

```bash
python3 transcriber.py
```

---

## Вариант Б — собери .app (без терминала навсегда)

После того как Вариант А заработал, выполни один раз:

```bash
# Скачай ffmpeg для Mac
brew install ffmpeg
cp $(which ffmpeg) ./ffmpeg

# Собери .app с ffmpeg внутри
source .venv/bin/activate
pip install pyinstaller
pyinstaller --noconfirm --windowed --name "TvoyMeet" \
  --add-data ".venv/lib/python*/site-packages/customtkinter:customtkinter" \
  --add-data ".venv/lib/python*/site-packages/tkinterdnd2:tkinterdnd2" \
  --add-binary "ffmpeg:." \
  transcriber.py
```

Готовый `.app` появится в папке `dist/TvoyMeet.app`.

Перетащи его в `/Applications` — запускается как обычное приложение, ffmpeg внутри.

### Если Mac заблокировал приложение

Apple блокирует неподписанные приложения. Чтобы открыть первый раз:

```
Правая кнопка на TvoyMeet.app → Открыть → Открыть
```

Один раз подтвердить, дальше открывается как обычно.

---

## Можно ли отдать .app другу?

Да. Заархивируй `TvoyMeet.app` и отправь. Другу не нужно ничего устанавливать:

- Python внутри ✓
- ffmpeg внутри ✓
- Whisper скачается сам при первом запуске (~150 МБ для turbo)

---

## Что нужно иметь

- Python 3.10+: https://www.python.org/downloads/
- ffmpeg (шаг 1 выше)
- Интернет при первом запуске — Whisper скачает модель
