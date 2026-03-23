import sys

from utils import remove_extra_spaces, count_words_in_sentence

MAXIMUM_WORDS = 4

def zad3_g():
    sentence = ""
    answer = ""
    for line in sys.stdin:
        line = remove_extra_spaces(line)
        if line == "" and sentence != "":
            if count_words_in_sentence(sentence) <= MAXIMUM_WORDS:
                answer += sentence + '\n'
            sentence = ""

        for char in line:
            if char == '.' or char == '?' or char == '!' or char == "…":
                if count_words_in_sentence(sentence) <= MAXIMUM_WORDS and sentence != "":
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
        print(zad3_g())
    except BrokenPipeError:
        sys.exit(0)
    finally:
        sys.stdout.close()

if __name__ == '__main__':
    main()