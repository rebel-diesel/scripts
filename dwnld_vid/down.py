import os
import subprocess
from yt_dlp import YoutubeDL

FFMPEG_PATH = os.path.join("input", "ffmpeg.exe")
OUTPUT_DIR = "output"

def ensure_output_dir():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

def extract_audio_from_video(video_path: str, audio_path: str):
    command = [
        FFMPEG_PATH,
        "-i", video_path,
        "-vn",
        "-acodec", "mp3",
        "-ab", "192k",
        "-ar", "44100",
        "-y",
        audio_path
    ]
    subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def download_video_and_extract_audio(url: str, is_tiktok=False):
    ensure_output_dir()

    video_template = os.path.join(OUTPUT_DIR, "%(title).80s.%(ext)s")

    ydl_opts = {
        "outtmpl": video_template,
        "ffmpeg_location": FFMPEG_PATH,
        "merge_output_format": "mp4",
        "quiet": False,
        "noplaylist": True,
    }

    if not is_tiktok:
        ydl_opts["format"] = "bestvideo+bestaudio/best"

    try:
        print(f"\nСкачиваю видео: {url}")
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

        downloaded_video = ydl.prepare_filename(info)
        audio_path = downloaded_video.rsplit(".", 1)[0] + ".audio.mp3"
        print("Извлекаю аудио...")
        extract_audio_from_video(downloaded_video, audio_path)

        print("Готово\n")

    except Exception as e:
        print(f"Ошибка при обработке {url}: {e}")

def download_from_url(url: str):
    if "tiktok.com" in url:
        download_video_and_extract_audio(url, is_tiktok=True)
    elif "youtube.com" in url or "youtu.be" in url:
        download_video_and_extract_audio(url, is_tiktok=False)
    else:
        print(f"Неизвестный источник: {url}")