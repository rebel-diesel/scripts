import sys
from pathlib import Path
from datetime import datetime
from tqdm import tqdm
import torch
from mmedit.apis import init_model, restoration_inference
from huggingface_hub import hf_hub_download
from PIL import Image

# ===================== Параметры =====================
BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
LOG_FILE = OUTPUT_DIR / "log.txt"

# Hugging Face модель
HF_REPO = "TencentARC/RealBasicVSR_BDx4"
HF_FILENAME = "realbasicvsr_b4c1_g1k1_20210901-9bec9f0f.pth"


# ===================== Утилиты =====================

def log(msg: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8-sig") as f:
        f.write(f"[{timestamp}] {msg}\n")
    print(msg)


# ===================== Реставрация кадров =====================

def restore_frames(input_dir: Path, output_dir: Path, model):
    frame_paths = sorted(input_dir.glob("frame_*.png"))
    output_dir.mkdir(parents=True, exist_ok=True)

    for frame_path in tqdm(frame_paths, desc="🔧 Восстановление кадров", unit="кадр"):
        result = restoration_inference(model, str(frame_path))
        restored_img = result['output'].squeeze().permute(1, 2, 0).clamp(0, 1).cpu().numpy()
        img = Image.fromarray((restored_img * 255).astype("uint8"))
        output_path = output_dir / frame_path.name
        img.save(output_path)


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
    input_frames_dir = OUTPUT_DIR / video_name / "frames"
    output_frames_dir = OUTPUT_DIR / video_name / "frames_restored"

    if not input_frames_dir.exists():
        print(f"⚠️ Кадры не найдены: {input_frames_dir}")
        return

    log(f"Загрузка модели RealBasicVSR_BDx4...")
    model_path = hf_hub_download(repo_id=HF_REPO, filename=HF_FILENAME)

    config_path = str(Path(__file__).parent / "realbasicvsr_config.py")
    model = init_model(config_path, model_path, device='cuda' if torch.cuda.is_available() else 'cpu')

    log(f"Начало реставрации: {video_path.name}")
    restore_frames(input_frames_dir, output_frames_dir, model)
    log(f"Готово: восстановленные кадры → {output_frames_dir}")



