import sys

from utils import remove_extra_spaces

MAX_SENTENCES = 20

def zad3_i():
    sentence = ""
    answer = ""
    max_sentences = MAX_SENTENCES
    for line in sys.stdin:
        line = remove_extra_spaces(line)
        if line == "" and sentence != "":
            if max_sentences > 0:
                answer += sentence + '\n'
                sentence = ""
                max_sentences -= 1
            else:
                return answer

        for char in line:
            if char == '.' or char == '?' or char == '!' or char == "…":
                if max_sentences > 0:
                    answer += sentence + char + '\n'
                    sentence = ""
                    max_sentences -= 1
                else:
                    return answer
            else:
                sentence += char

    return answer

def main():
    sys.stdin.reconfigure(encoding='utf-8')
    sys.stdout.reconfigure(encoding='utf-8')
    try:
        print(zad3_i())
    except BrokenPipeError:
        sys.exit(0)
    finally:
        sys.stdout.close()

if __name__ == '__main__':
    main()