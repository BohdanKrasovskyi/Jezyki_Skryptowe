import sys
import os
import time
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description="Uproszczony tail")
    parser.add_argument("file", nargs="?", default=None,help="Ścieżka do pliku (opcjonalna)")
    parser.add_argument("--lines", type=int, default=10,help="Liczba ostatnich linii do wypisania (domyślnie 10)")
    parser.add_argument("--follow", action="store_true",help="Czekaj na nowe linie (jak tail -f)")
    return parser.parse_args()


def read_lines_from_file(filepath):
    if not os.path.exists(filepath):
        print(f"Błąd: plik '{filepath}' nie istnieje.")
        sys.exit(1)
    with open(filepath, "r", encoding="utf-8") as f:
        return f.readlines()


def read_lines_from_stdin():
    return sys.stdin.readlines()


def print_last_n_lines(lines, n):
    for line in lines[-n:]:
        print(line, end="")


def follow_file(args):
    with open(args.file, "r", encoding="utf-8") as f:
        lines = f.readlines()

        for line in lines[-args.lines:]:
            print(line, end="")
        print()
        f.seek(0, os.SEEK_END)

        while True:
            line = f.readline()
            if line:
                print(line, end="")
            else:
                time.sleep(0.1)

def main():
    args = parse_args()

    if args.lines <= 0:
        print("Błąd: --lines musi być liczbą dodatnią.")
        sys.exit(1)

    if args.file is not None:
        if args.follow:
            follow_file(args)
        else:
            lines = read_lines_from_file(args.file)
            print_last_n_lines(lines, args.lines)
    else:
        if args.follow:
            print("Błąd: --follow wymaga podania pliku.")
            sys.exit(1)
        lines =  sys.stdin.readlines()
        print_last_n_lines(lines, args.lines)


if __name__ == "__main__":
    main()