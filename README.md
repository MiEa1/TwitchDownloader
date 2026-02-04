# Twitch Downloader Tool

一个 **跨平台、交互式、可长期使用的 Twitch 下载工具**  
基于 `yt-dlp`，支持直播 / 回放 / 剪辑。

---

## ✨ 功能特性

- 运行时交互输入 Twitch 链接
- 运行时选择下载质量（Source / 1080p / 720p / 音频）
- 运行时选择下载路径（可记住）
- 运行时选择并发线程数（可记住）
- 多线程并发下载
- 原生实时进度条（yt-dlp）
- 防重复下载（download-archive）
- 下载完成后系统桌面通知 + 弹窗提醒
- Windows / Linux / macOS 支持

---

## 📦 安装依赖

```bash
pip install -r requirements.txt
