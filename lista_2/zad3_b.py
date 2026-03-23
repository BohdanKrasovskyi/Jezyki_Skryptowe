import sys
from utils import remove_all_white_symbols


def zad3_b():
    char_count = 0
    has_data = False
    for line in sys.stdin:
        line = remove_all_white_symbols(line)
        if line != "":
            has_data = True
        char_count += len(line)

    if not has_data:
        raise Exception("No data found")
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

