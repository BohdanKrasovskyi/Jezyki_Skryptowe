import sys

from utils import remove_extra_spaces, count_special_words

MINIMUM_WORDS = 2
def zad3_j():
    sentence = ""
    answer = ""
    for line in sys.stdin:
        line = remove_extra_spaces(line)
        if line == "" and sentence != "":
            if count_special_words(sentence) >= MINIMUM_WORDS:
                answer += sentence + '\n'
            sentence = ""

        for char in line:
            if char == '.' or char == '?' or char == '!' or char == "…":
                if count_special_words(sentence) >= MINIMUM_WORDS:
                    answer += sentence + char + '\n'
                sentence = ""
            else:
                sentence += char

    if answer == "":
        raise Exception("Nie ma takich zdan!")
    return answer

def main():
    sys.stdin.reconfigure(encoding='utf-8')
    sys.stdout.reconfigure(encoding='utf-8')
    try:
        print(zad3_j())
    except BrokenPipeError:
        sys.exit(0)
    finally:
        sys.stdout.close()

if __name__ == '__main__':
    main()

