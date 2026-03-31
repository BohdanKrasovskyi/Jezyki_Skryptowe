import sys

from utils import remove_extra_spaces, count_comas_in_sentence

MINIMUM_COMAS = 2

def zad3_f():
    sentence = ""
    for line in sys.stdin:
        line = remove_extra_spaces(line)
        if line == "" and sentence != "":
            if count_comas_in_sentence(sentence) >= MINIMUM_COMAS:
                return sentence
            sentence = ""

        for char in line:
            if char == '.' or char == '?' or char == '!' or char == "…":
                if count_comas_in_sentence(sentence) >= MINIMUM_COMAS:
                    return sentence
                sentence = ""
            else:
                sentence += char

    return ""

def main():
    sys.stdin.reconfigure(encoding='utf-8')
    sys.stdout.reconfigure(encoding='utf-8')
    try:
        print(zad3_f())
    except BrokenPipeError:
        sys.exit(0)
    finally:
        sys.stdout.close()

if __name__ == "__main__":
    main()