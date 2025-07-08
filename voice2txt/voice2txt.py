import os
import subprocess
import warnings
from pathlib import Path
from datetime import datetime, timezone
from faster_whisper import WhisperModel
import threading
import time

warnings.filterwarnings("ignore", category=UserWarning, module="ctranslate2")

# ===================== Настройки путей =====================
BASE_DIR = Path(__file__).resolve().parent
INPUT_VOICE_DIR = BASE_DIR / "input" / "voices"
OUTPUT_BASE_DIR = BASE_DIR / "output"
OUTPUT_WAV_DIR = OUTPUT_BASE_DIR / "wav"
OUTPUT_TXT_DIR = OUTPUT_BASE_DIR / "txt"
OUTPUT_LOG_FILE = OUTPUT_BASE_DIR / "log.txt"
FFMPEG_PATH = BASE_DIR / "input" / "ffmpeg.exe"


# ===================== Получает дату и время записи из метаданных m4a-файлов =====================
def get_recording_timestamp(file_path):
    command = [
        str(FFMPEG_PATH),
        "-i", str(file_path),
        "-f", "ffmetadata", "-"
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    for line in result.stderr.splitlines():
        if "creation_time" in line:
            try:
                date_str = line.strip().split(":", 1)[1].strip()
                utc_dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                local_dt = utc_dt.astimezone()  # автоопределение часового пояса
                return local_dt.strftime("%Y%m%d_%H%M%S")
            except Exception:
                pass
    return None


# ===================== Переименовывает все .m4a файлы =====================
def rename_files_with_timestamp():
    for file in INPUT_VOICE_DIR.glob("*.m4a"):
        timestamp = get_recording_timestamp(file) or "unknown"
        new_name = f"{timestamp}_{file.name}"
        new_path = file.with_name(new_name)
        if not new_path.exists():
            file.rename(new_path)
            write_log(f"Переименован: {file.name} → {new_name}")


# ===================== Конвертация m4a -> wav =====================
def convert_m4a_to_wav(input_path, output_path):
    command = [
        str(FFMPEG_PATH),
        "-i", str(input_path),
        "-ac", "1",
        "-ar", "16000",
        str(output_path)
    ]
    subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


# ===================== Распознавание речи =====================
def transcribe_audio(wav_path, model, current, total):
    done = False

    def spinner():
        symbols = ['|', '/', '-', '\\']
        i = 0
        while not done:
            print(f"\rРаспознаю {current}/{total}... {symbols[i % len(symbols)]}", end="", flush=True)
            i += 1
            time.sleep(0.2)
        print(f"\rГотово: {current}/{total} записей обработано.      ")

    spinner_thread = threading.Thread(target=spinner)
    spinner_thread.start()

    try:
        segments, _ = model.transcribe(str(wav_path))
        return " ".join([seg.text.strip() for seg in segments])
    finally:
        done = True
        spinner_thread.join()


# ===================== Запись лога =====================
def write_log(message):
    with open(OUTPUT_LOG_FILE, "a", encoding="utf-8") as log_file:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_file.write(f"[{timestamp}] {message}\n")


# ===================== Главный запуск =====================
def run_voice2txt():
    OUTPUT_WAV_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_TXT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    rename_files_with_timestamp()
    audio_files = list(INPUT_VOICE_DIR.glob("*.m4a"))

    model = WhisperModel("base", compute_type="int8")

    total = len(audio_files)
    for idx, file in enumerate(audio_files, start=1):
        wav_file = OUTPUT_WAV_DIR / (file.stem + ".wav")
        txt_file = OUTPUT_TXT_DIR / (file.stem + ".txt")

        write_log(f"Конвертация {file.name} → {wav_file.name}")
        convert_m4a_to_wav(file, wav_file)

        write_log(f"Распознавание {wav_file.name}")
        text = transcribe_audio(wav_file, model, idx, total)

        with open(txt_file, "w", encoding="utf-8") as f:
            f.write(text)

        write_log(f"Готово: {txt_file.name}\n")
