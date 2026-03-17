import sys

from utils import remove_extra_spaces


def zad3_h():
    sentence = ""
    answer = ""
    for line in sys.stdin:
        line = remove_extra_spaces(line)

        for char in line:
            if char == '.' or char == "…":
                sentence = ""
            elif char == '!' or char == '?' and sentence != "":
                answer += sentence + char + '\n'
                sentence = ""
            else:
                sentence += char

    return answer


def main():
    sys.stdin.reconfigure(encoding='utf-8')
    sys.stdout.reconfigure(encoding='utf-8')
    try:
        print(zad3_h())
    except BrokenPipeError:
        sys.exit(0)
    finally:
        sys.stdout.close()

if __name__ == '__main__':
    main()