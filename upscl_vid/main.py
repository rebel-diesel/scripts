import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
INPUT_DIR = BASE_DIR / "input"
VIDEO_EXTENSIONS = {".mp4", ".avi", ".mkv", ".mov", ".webm", ".mpeg", ".mpg"}

SCRIPTS = [
    "upscale.py",
    "restore.py",
    "combine.py"
]

def run_script(script_name, video_path):
    print(f"\n=== ⏳ {script_name} для {video_path.name} ===")
    subprocess.run(["python", script_name, str(video_path)], check=True)
    print(f"=== ✅ Готово: {script_name} ({video_path.name}) ===")

def main():
    video_files = [
        file for file in INPUT_DIR.iterdir()
        if file.is_file() and file.suffix.lower() in VIDEO_EXTENSIONS
    ]

    if not video_files:
        print("⚠️ Нет видео в input/")
        return

    for video_path in video_files:
        for script in SCRIPTS:
            path = BASE_DIR / script
            if path.exists():
                run_script(script, video_path)
            else:
                print(f"⚠️ Пропущен (не найден): {script}")

if __name__ == "__main__":
    main()
