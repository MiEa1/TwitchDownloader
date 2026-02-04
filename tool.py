#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import sys
import json
import platform
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from colorama import Fore, Style, init
import tkinter as tk
from tkinter import messagebox

# ================= 初始化 =================

init(autoreset=True)

APP_DIR = Path(__file__).parent
CONFIG_FILE = APP_DIR / "config.json"
ARCHIVE_FILE = APP_DIR / "downloaded.txt"
RETRIES = 3

# Windows 通知
if platform.system() == "Windows":
    try:
        from win10toast import ToastNotifier
    except ImportError:
        ToastNotifier = None

# ================= 日志 =================

def log(tag, color, msg):
    print(f"{color}[{tag}]{Style.RESET_ALL} {msg}")

def info(msg): log("INFO", Fore.CYAN, msg)
def ok(msg):   log("OK",   Fore.GREEN, msg)
def warn(msg): log("WARN", Fore.YELLOW, msg)
def err(msg):  log("ERR",  Fore.RED, msg)

# ================= 系统通知 =================

def system_notify(title: str, msg: str):
    system = platform.system()
    try:
        if system == "Windows" and ToastNotifier:
            toaster = ToastNotifier()
            toaster.show_toast(title, msg, duration=5, threaded=True)
        elif system == "Linux":
            subprocess.run(["notify-send", title, msg])
        elif system == "Darwin":
            subprocess.run([
                "osascript",
                "-e",
                f'display notification "{msg}" with title "{title}"'
            ])
    except Exception:
        pass

def popup_alert(title: str, msg: str):
    def _show():
        root = tk.Tk()
        root.withdraw()
        messagebox.showinfo(title, msg)
        root.destroy()
    threading.Thread(target=_show, daemon=True).start()

# ================= 配置 =================

def load_config():
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            warn("配置文件损坏，已忽略")
    return {}

def save_config(cfg):
    CONFIG_FILE.write_text(
        json.dumps(cfg, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    ok("配置已保存")

# ================= 选择下载目录 =================

def choose_download_dir(cfg):
    if "download_dir" in cfg:
        info(f"检测到上次下载路径：\n{cfg['download_dir']}")
        use = input("是否继续使用该路径？[Y/n]： ").strip().lower()
        if use in ("", "y", "yes"):
            return Path(cfg["download_dir"])

    path = input("请输入下载目录（如 D:\\TwitchDownloads）： ").strip()
    if not path:
        err("下载目录不能为空")
        sys.exit(1)

    dl_dir = Path(path)
    dl_dir.mkdir(parents=True, exist_ok=True)

    remember = input("是否记住该路径？[y/N]： ").strip().lower()
    if remember in ("y", "yes"):
        cfg["download_dir"] = str(dl_dir)

    return dl_dir

# ================= 并发线程数 =================

def choose_workers(cfg):
    default = cfg.get("max_workers", 2)
    val = input(f"请输入并发线程数（建议 1~4，默认 {default}）： ").strip()
    workers = int(val) if val.isdigit() and int(val) > 0 else default

    remember = input("是否记住该线程数？[y/N]： ").strip().lower()
    if remember in ("y", "yes"):
        cfg["max_workers"] = workers

    return workers

# ================= 质量选择 =================

QUALITY_MAP = {
    "1": ("原画质 / Source", "best"),
    "2": ("1080p", "bestvideo[height<=1080]+bestaudio/best"),
    "3": ("720p",  "bestvideo[height<=720]+bestaudio/best"),
    "4": ("480p",  "bestvideo[height<=480]+bestaudio/best"),
    "5": ("仅音频", "bestaudio"),
}

def choose_quality():
    info("请选择下载质量：")
    for k, (name, _) in QUALITY_MAP.items():
        print(f"  {k}) {name}")

    while True:
        c = input("请输入编号 [1-5]： ").strip()
        if c in QUALITY_MAP:
            ok(f"已选择：{QUALITY_MAP[c][0]}")
            return QUALITY_MAP[c][1]
        warn("无效输入")

# ================= 输入 URL =================

def get_urls():
    info("请输入 Twitch 视频 / 直播链接（一行一个，q 结束）：")
    urls = []
    while True:
        line = input("> ").strip()
        if not line or line.lower() == "q":
            break
        if not line.startswith("http"):
            warn("无效链接，已忽略")
            continue
        urls.append(line)
    return urls

# ================= 下载 =================

def download(url, fmt, dl_dir):
    out_tpl = dl_dir / "%(uploader)s_%(upload_date)s_%(title)s.%(ext)s"

    cmd = [
        "yt-dlp",
        url,
        "-f", fmt,
        "--merge-output-format", "mp4",
        "--concurrent-fragments", "8",
        "--retries", "10",
        "--fragment-retries", "10",
        "--newline",
        "--progress",
        "--download-archive", str(ARCHIVE_FILE),
        "-o", str(out_tpl),
    ]

    for i in range(1, RETRIES + 1):
        try:
            info(f"开始下载（第 {i} 次）")
            info(url)
            subprocess.run(cmd, check=True)
            ok("下载完成")
            return
        except subprocess.CalledProcessError:
            warn("下载失败，重试中")

    err("多次失败，已跳过")

# ================= 主流程 =================

def main():
    cfg = load_config()

    dl_dir = choose_download_dir(cfg)
    workers = choose_workers(cfg)
    fmt = choose_quality()
    urls = get_urls()

    if not urls:
        warn("未输入任何链接，退出")
        return

    save_config(cfg)

    info(f"下载目录：{dl_dir}")
    info(f"并发线程：{workers}")
    info(f"任务数量：{len(urls)}")

    with ThreadPoolExecutor(max_workers=workers) as pool:
        tasks = [pool.submit(download, u, fmt, dl_dir) for u in urls]
        for _ in as_completed(tasks):
            pass

    title = "Twitch 下载完成"
    msg = f"完成 {len(urls)} 个任务\n保存路径：\n{dl_dir}"
    system_notify(title, msg)
    popup_alert(title, msg)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Fore.RED}用户中断，退出{Style.RESET_ALL}")
        sys.exit(1)
