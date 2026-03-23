import sys

from utils import remove_extra_spaces

def zad3_d():
    max_length = 0
    answer_sentence = ""
    sentence = ""

    has_data = False
    for line in sys.stdin:
        line = remove_extra_spaces(line)
        if line != "":
            has_data = True
        if line == "" and sentence != "":
            if len(sentence) > max_length:
                max_length = len(sentence)
                answer_sentence = sentence
            sentence = ""

        for char in line:
            if char == '.' or char == '?' or char == '!' or char == "…":
                if len(sentence) > max_length:
                    max_length = len(sentence)
                    answer_sentence = sentence + char
                sentence = ""
            else:
                sentence += char

    if not has_data:
        raise Exception("No data found")
    if answer_sentence == "":
        raise Exception("Nie ma takich zdan!")

    return answer_sentence

def main():
    sys.stdin.reconfigure(encoding='utf-8')
    sys.stdout.reconfigure(encoding='utf-8')
    try:
        print(zad3_d())
    except BrokenPipeError:
        sys.exit(0)
    finally:
        sys.stdout.close()

if __name__ == '__main__':
    main()
