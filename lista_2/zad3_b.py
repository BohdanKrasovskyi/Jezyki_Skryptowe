import sys
from utils import remove_all_white_symbols


def zad3_b():
    char_count = 0
    for line in sys.stdin:
        line = remove_all_white_symbols(line)
        char_count += len(line)
    return char_count

def main():
    sys.stdin.reconfigure(encoding='utf-8')
    sys.stdout.reconfigure(encoding='utf-8')
    try:
        print(zad3_b())
    except BrokenPipeError:
        sys.exit(0)
    finally:
        sys.stdout.close()

if __name__ == "__main__":
    main()

