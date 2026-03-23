import sys
from utils import remove_all_white_symbols


def zad3_a():
    if_previous_akapit = False
    akapit_count = 0
    has_data = False
    for line in sys.stdin:
        line = remove_all_white_symbols(line)
        if len(line) != 0:
            has_data = True
        if line == "":
            if not if_previous_akapit:
                akapit_count += 1
            if_previous_akapit = True
        else:
            if_previous_akapit = False

    if not has_data:
        raise Exception("No data found")

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

