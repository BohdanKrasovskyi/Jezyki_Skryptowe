import sys
from utils import remove_extra_spaces

def extract_content(input_stream):
    state = "PREAMBLE"
    line_count = 0
    empty_lines_in_a_row = 0
    buffer = ""

    #jezeli mamy informacje o wydaniu-konczymy dzialanie
    for line in sys.stdin:
        if "-----" in line:
            break

    #usuwamy nadmiarowe spacje i biale znaki z obecnej linii
        cleaned_line = remove_extra_spaces(line)

        if state == "PREAMBLE":
            line_count += 1
            if cleaned_line == "": #liczymy puste linie pod rząd
                empty_lines_in_a_row += 1
            else:
                empty_lines_in_a_row = 0

            buffer += cleaned_line + "\n" #dodajemy do buffera w razie, gdyby nie było preambuły

            if empty_lines_in_a_row >= 2:
                state = "BODY"
                buffer = "" #usuwamy preambułe
                continue

            if line_count == 10: #jeżeli przez 10 linii nie było 2 pustych-wypisujemy tekst z bufora
                state = "BODY"
                try:
                    print(buffer, end="")
                except BrokenPipeError:
                    sys.exit(0)
                buffer = ""
                continue

        elif state == "BODY":
            try:
                print(cleaned_line) #jezeli jesteśmy w tekście, wypisujemy
            except BrokenPipeError:
                sys.exit(0)

    #zabezpieczenie przed krótkim tekstem (< 10 linii) bez preambuły
    if state == "PREAMBLE" and buffer != "":
        try:
            print(buffer, end="")
        except BrokenPipeError:
            sys.exit(0)

def main():
    #polskie znaki
    sys.stdin.reconfigure(encoding='utf-8')
    sys.stdout.reconfigure(encoding='utf-8')
    extract_content(sys.stdin)

if __name__ == "__main__":
    main()


