🌐 [English](../../README.md) | [Русский](../ru/README.md)

# TvoyMeet

本地音视频转录工具。无需云端。无需订阅。

![TvoyMeet](../../tvoymeet_app_icon_1781528482998.jpg)

## 功能

- 拖放文件或粘贴链接（YouTube、VK、Rutube 等）
- 通过 FFmpeg 提取音频，支持按时间裁剪
- 使用 Whisper 本地转录（模型从 tiny 到 large-v3）
- 导出为 txt、json、srt、vtt、tsv 格式
- 生成包含转录文本和 LLM 提示词的 `.md` 文件

## 下载

前往 [Releases](../../../releases) 获取预编译版本：

- `TvoyMeet-mac.zip` — macOS 应用
- `TvoyMeetInstaller.exe` — Windows 安装程序

### macOS 首次启动

macOS 会拦截未签名的应用。两种解决方法：

**方法 1 — 终端**（推荐）：
```bash
xattr -cr ~/Downloads/TvoyMeet.app
open ~/Downloads/TvoyMeet.app
```

**方法 2 — Finder**：
右键点击 `TvoyMeet.app` → **打开** → 在对话框中点击 **打开**。

## 从源码运行

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

需要在系统中安装 FFmpeg 或将其放在 `transcriber.py` 旁边。

## 技术栈

- [customtkinter](https://github.com/TomSchimansky/CustomTkinter) — UI 框架
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) — 语音转录
- [tkinterdnd2](https://github.com/pmgagne/tkinterdnd2) — 拖放支持（仅限 Windows）
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) — 链接下载
- PyInstaller — 打包为 .exe / .app
