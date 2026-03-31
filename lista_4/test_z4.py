import subprocess
import sys
import os

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

TESTS_DIR = os.path.join(os.path.dirname(CURRENT_DIR), 'tests')

ANALYZER_PATH = os.path.join(CURRENT_DIR, 'text_analyzer.py')
ZADANIE4_PATH = os.path.join(CURRENT_DIR, 'zadanie4.py')


def run_analyzer_test(test_name, filename):
    file_path = os.path.join(TESTS_DIR, filename)

    print(f"\n--- TEST: {test_name} ---")
    print(f"Plik: {file_path}")

    try:
        result = subprocess.run(
            [sys.executable, ANALYZER_PATH],
            input=f"{file_path}\n",
            capture_output=True,
            text=True,
            encoding='utf-8'
        )

        if result.stdout:
            print(result.stdout.strip())
        if result.stderr:
            print("BŁĄD (stderr):", result.stderr.strip())
    except Exception as e:
        print(f"Błąd wykonania testu: {e}")


print("========================================")
print("TESTY DLA TEXT_ANALYZER.PY")
print("========================================")

run_analyzer_test("Zwykły plik tekstowy", "test.txt")
run_analyzer_test("Remis w statystykach", "tie.txt")
run_analyzer_test("Sama interpunkcja", "punctuation.txt")
run_analyzer_test("Tylko białe znaki", "space_and_enter_only.txt")
run_analyzer_test("Całkowicie pusty plik", "empty_file.txt")

run_analyzer_test("Logi serwerowe", "logs.log")
run_analyzer_test("Plik HTML", "html_file.html")

run_analyzer_test("Błędne kodowanie", "bad_encoding.txt")
run_analyzer_test("Plik binarny", "logo_python.png")
run_analyzer_test("Brak uprawnień do odczytu", "no_permission.txt")

print("TESTY DLA ZADANIA 4 (GŁÓWNY AGREGATOR)")

print("\n--- TEST 1: Zły katalog ---")
subprocess.run([sys.executable, ZADANIE4_PATH, 'zly/katalog'])

print("\n--- TEST 2: Brak argumentu ---")
subprocess.run([sys.executable, ZADANIE4_PATH])

print("\n--- TEST 3: Podano plik zamiast katalogu ---")
subprocess.run([sys.executable, ZADANIE4_PATH, ANALYZER_PATH])

print("\n--- TEST 4: Poprawne wywołanie na katalogu tests ---")
subprocess.run([sys.executable, ZADANIE4_PATH, TESTS_DIR])