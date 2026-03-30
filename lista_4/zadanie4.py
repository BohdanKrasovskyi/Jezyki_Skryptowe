import sys
import os
import subprocess
import json
from collections import Counter

def main():
    if len(sys.argv) < 2:
        print("Usage: python zadanie4.py <path>")
        sys.exit(1)

    target_dir = sys.argv[1]
    if not os.path.isdir(target_dir):
        print(f"Error: {target_dir} is not a directory")
        sys.exit(1)

    total_files = 0
    total_chars_count = 0
    total_words_count = 0
    total_lines_count = 0

    #liczniki na globalne statystyki
    global_char_counter = Counter()
    global_word_counter = Counter()

    for filename in os.listdir(target_dir):
        file_path = os.path.join(target_dir, filename)

        if os.path.isfile(file_path):
            try:
                process = subprocess.run(
                    [sys.executable, 'text_analyzer.py', '--full'],
                    input = file_path + '\n',
                    capture_output = True,
                    text = True,
                    encoding = 'utf-8',
                )

                if process.returncode != 0:
                    error_msg = process.stderr.strip() if process.stderr else "Unknown error"
                    print(f"Warning: Skipped a file '{filename}' (Error: {error_msg})")
                    continue

                result = json.loads(process.stdout)

                if "Error" in result:
                    print(f"Warning: Skipped a file '{filename}' ({result['Error']})")
                    continue

                total_files += 1
                total_chars_count += result.get("char_count", 0)
                total_words_count += result.get("word_count", 0)
                total_lines_count += result.get("line_count", 0)

                global_char_counter.update(result.get("char_counts", {}))
                global_word_counter.update(result.get("word_counts", {}))

            except Exception as e:
                print(f"Warning: {file_path}: {e}")

    most_common_char = global_char_counter.most_common(1)[0][0] if global_char_counter else None
    most_common_word = global_word_counter.most_common(1)[0][0] if global_word_counter else None

    summary = {
        "total_files": total_files,
        "total_chars_count": total_chars_count,
        "total_lines_count": total_lines_count,
        "total_words_count": total_words_count,
        "most_common_char": most_common_char,
        "most_common_word": most_common_word,
    }

    print(json.dumps(summary, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()


