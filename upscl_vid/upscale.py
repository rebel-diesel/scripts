import sys
import subprocess
from pathlib import Path
from datetime import datetime

# ===================== Параметры =====================
BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
FFMPEG_PATH = BASE_DIR / "driver" / "ffmpeg.exe"
LOG_FILE = OUTPUT_DIR / "log.txt"


# ===================== Утилиты =====================

def log(msg: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8-sig") as f:
        f.write(f"[{timestamp}] {msg}\n")
    print(msg)


def extract_frames(video_path: Path, frames_dir: Path):
    frames_dir.mkdir(parents=True, exist_ok=True)
    command = [
        str(FFMPEG_PATH),
        "-i", str(video_path),
        str(frames_dir / "frame_%06d.png")
    ]
    subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


# ===================== Основная логика =====================

def main():
    if len(sys.argv) < 2:
        print("❌ Не передан путь к видео.")
        return

    video_path = Path(sys.argv[1])
    if not video_path.exists():
        print(f"❌ Файл не найден: {video_path}")
        return

    video_name = video_path.stem
    output_subdir = OUTPUT_DIR / video_name
    frames_dir = output_subdir / "frames"
    restored_dir = output_subdir / "frames_restored"

    if frames_dir.exists() and any(frames_dir.iterdir()):
        log(f"Пропущено (кадры уже извлечены): {video_path.name}")
        return

    log(f"Начало извлечения: {video_path.name}")
    extract_frames(video_path, frames_dir)
    restored_dir.mkdir(parents=True, exist_ok=True)
    log(f"Готово: кадры извлечены → {frames_dir}")


