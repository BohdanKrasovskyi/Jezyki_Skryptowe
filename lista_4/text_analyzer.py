import sys
import json
import string
from collections import Counter

def analyze_file(file_path, return_full = False):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        char_count = len(text)
        line_count = len(text.splitlines())

        raw_words = text.split()
        cleaned_words = []
        for word in raw_words:
            clean_w = word.strip(string.punctuation).lower()
            if clean_w:
                cleaned_words.append(clean_w)

        word_count = len(cleaned_words)

        chars_no_space = [c for c in text if not c.isspace()]

        char_counter = Counter(chars_no_space)
        word_counter = Counter(cleaned_words)

        if chars_no_space:
            most_common_char = char_counter.most_common(1)[0][0]
        else:
            most_common_char = None

        if cleaned_words:
            most_common_word = word_counter.most_common(1)[0][0]
        else:
            most_common_word = None

        result = {
            "file_path": file_path,
            "char_count": char_count,
            "word_count": word_count,
            "line_count": line_count,
            "most_common_char": most_common_char,
            "most_common_word": most_common_word,
        }

        if return_full:
            result["char_counts"] = dict(char_counter)
            result["word_counts"] = dict(word_counter)

        return result

    except FileNotFoundError:
        return {"Error": f"File not found: {file_path}"}
    except Exception as e:
        return {"Error": str(e)}

def main():
    show_full_stats = "--full" in sys.argv

    file_path = sys.stdin.readline().strip()

    if not file_path:
        print(json.dumps({"Error": "No file path provided"})) #konwersja string na json
        sys.exit(1)

    stats = analyze_file(file_path, return_full = show_full_stats)
    print(json.dumps(stats, indent=2))

if __name__ == "__main__":
    main()



