import os
import sys
import json
import subprocess
from datetime import datetime

from utils import *


def convert_with_ffmpeg(input_path, output_path):
    cmd = ["ffmpeg","-y","-loglevel", "error","-i", input_path, output_path]
    print(f"[INFO] Uruchamiam: {' '.join(cmd)}")

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"[ERROR] Błąd ffmpeg: {result.stderr}")
        return False

    return True


def convert_with_magick(input_path, output_path):
    cmd = ["magick", input_path, output_path]
    print(f"[INFO] Uruchamiam: {' '.join(cmd)}")

    result = 1
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(e)

    if result.returncode != 0:
        print(f"[ERROR] Błąd magick: {result.stderr}")
        return False

    return True


def load_history(history_path):
    if os.path.exists(history_path):
        with open(history_path, "r", encoding="utf-8") as f:
            print(f"[INFO] Wczytano historię: {history_path}")
            return json.load(f)
    print("[INFO] Brak pliku historii, tworzę nową.")
    return []


def save_history(history_path, history):
    with open(history_path, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
    print(f"[INFO] Zapisano historię: {history_path}")


def main():
    args = parse_args()

    output_dir = get_output_dir()
    history_path = os.path.join(output_dir, "history.json")
    history = load_history(history_path)

    media_files = find_media_files(args.directory)
    fmt = f".{args.format.lower()}"

    if fmt not in VIDEO_AUDIO_EXTENSIONS and fmt not in IMAGE_EXTENSIONS and fmt != ".-":
        print(f"[ERROR] Format nie jest dozwolony - {args.format}")
        sys.exit(1)

    if not media_files:
        print("[WARNING] Nie znaleziono plików multimedialnych.")
        sys.exit(0)

    for filepath, file_type in media_files:

        if file_type == "video_audio":
            if fmt == ".-" or fmt in IMAGE_EXTENSIONS:
                fmt = ".mp4"
            if fmt not in VIDEO_AUDIO_EXTENSIONS:
                print(f"[WARNING] Brak konwersji z video/audio do tego formatu. Pomijam plik: {filepath}")
                success = False
                tool_used = "-"
            else:
                output_path = make_output_filename(filepath, fmt, output_dir)
                print(f"[INFO] Konwertuję: {filepath} → {output_path}")
                success = convert_with_ffmpeg(filepath, output_path)
                tool_used = "ffmpeg"
        else:
            if fmt == ".-" or fmt in VIDEO_AUDIO_EXTENSIONS:
                fmt = ".jpg"
            if fmt not in IMAGE_EXTENSIONS:
                print(f"[WARNING] Brak konwersji z image do tego formatu. Pomijam plik: {filepath}")
                success = False
                tool_used = "-"
            else:
                output_path = make_output_filename(filepath, fmt, output_dir)
                print(f"[INFO] Konwertuję: {filepath} → {output_path}")
                success = convert_with_magick(filepath, output_path)
                tool_used = "magick"

        entry = {
            "datetime": datetime.now().isoformat(),
            "source": filepath,
            "output_format": args.format,
            "output_path": output_path if success else None,
            "tool": tool_used,
            "success": success,
        }

        history.append(entry)

        if success:
            print(f"[INFO] OK: {os.path.basename(filepath)}")
        else:
            print(f"[ERROR] BŁĄD: {os.path.basename(filepath)}")

    save_history(history_path, history)
    print(f"[INFO] Historia zapisana w: {history_path}")


if __name__ == "__main__":
    main()