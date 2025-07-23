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


def combine_frames_to_video(frames_dir: Path, output_video: Path, fps=25):
    command = [
        str(FFMPEG_PATH),
        "-y",
        "-framerate", str(fps),
        "-i", str(frames_dir / "frame_%06d.png"),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        str(output_video)
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
    input_dir = OUTPUT_DIR / video_name / "frames_restored"
    output_video = OUTPUT_DIR / video_name / "restored.mp4"

    if not input_dir.exists():
        print(f"⚠️ Кадры не найдены: {input_dir}")
        return

    log(f"Сборка видео из: {input_dir}")
    combine_frames_to_video(input_dir, output_video)
    log(f"Готово: сохранено видео → {output_video}")


if __name__ == "__main__":
    main()
