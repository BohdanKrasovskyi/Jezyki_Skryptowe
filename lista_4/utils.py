import os
import sys
import argparse

VIDEO_AUDIO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".mov", ".mp3", ".wav", ".flac", ".ogg"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"}


def get_output_dir():
    out_dir = os.environ.get("CONVERTED_DIR", os.path.join(os.getcwd(), "converted"))

    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    return out_dir


def find_media_files(directory):
    if not os.path.isdir(directory):
        print(f"[ERROR] Katalog nie istnieje: {directory}")
        sys.exit(1)

    results = []

    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)

        if not os.path.isfile(filepath):
            continue

        ext = os.path.splitext(filename)[1].lower()

        if ext in VIDEO_AUDIO_EXTENSIONS:
            results.append((filepath, "video_audio"))

        elif ext in IMAGE_EXTENSIONS:
            results.append((filepath, "image"))

    return results


def make_output_filename(original_path, output_format, output_dir):
    from datetime import datetime

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    base = os.path.splitext(os.path.basename(original_path))[0]

    new_name = f"{timestamp}-{base}.{output_format.lstrip('.')}"
    full_path = os.path.join(output_dir, new_name)

    return full_path


def parse_args():
    parser = argparse.ArgumentParser(description="Konwersja plików multimedialnych")
    parser.add_argument("directory", help="Katalog z plikami do konwersji")
    parser.add_argument("--format", default="-", help="Format wyjściowy (domyślnie: mp4)")
    return parser.parse_args()