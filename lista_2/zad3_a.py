import sys
from utils import remove_all_white_symbols


def zad3_a():
    akapit_count = 0
    for line in sys.stdin:
        line = remove_all_white_symbols(line)
        if line == "":
            akapit_count += 1
    return akapit_count

def main():
    sys.stdin.reconfigure(encoding='utf-8')
    sys.stdout.reconfigure(encoding='utf-8')
    try:
        print(zad3_a())
    except BrokenPipeError:
        sys.exit(0)
    finally:
        sys.stdout.close()

if __name__ == "__main__":
    main()

