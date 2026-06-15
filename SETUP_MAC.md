# ТвойMeet — запуск на Mac

## 1. Установи ffmpeg

```bash
brew install ffmpeg
```

Нет Homebrew? Сначала установи: https://brew.sh

## 2. Создай окружение и установи пакеты

```bash
cd путь/до/папки/ai-lab
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 3. Запусти

```bash
python3 transcriber.py
```

## Что нужно иметь

- Python 3.10 или новее: https://www.python.org/downloads/
- ffmpeg (шаг 1)
- Интернет при первом запуске — Whisper скачает модель (~150 МБ для turbo)
