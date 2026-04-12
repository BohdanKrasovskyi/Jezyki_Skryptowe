import re
from pathlib import Path
import logging
from data_manager import parse_stations

def task_a(stations_data : dict):
    data_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    dates = []

    for data in stations_data.values():
        start = data.get("Data uruchomienia", "").strip()
        end = data.get("Data zamknięcia", "").strip()

        if data_pattern.match(start):
            dates.append(start)
        if data_pattern.match(end):
            dates.append(end)

    return dates

def task_b(stations_data : dict):
    coord_pattern = re.compile(r"\b\d+\.\d{6}\b")
    coordinates = []

    for data in stations_data.values():
        for value in data.values():
            if isinstance(value, str):
                matches = coord_pattern.findall(value)
                coordinates.extend(matches)

    return coordinates

def task_c(stations_data : dict):
    pattern = re.compile(r"^[^-]+-[^-]+$")
    two_part_stations = []
    for data in stations_data.values():
        name = data.get("Nazwa stacji", "").strip()
        if pattern.match(name):
            two_part_stations.append(name)

    return two_part_stations

def task_d(stations_data : dict):
    space_pattern = re.compile(r" ")
    diacritics_pattern = re.compile(r"[ąćęłńóśźżĄĆĘŁŃÓŚŹŻ]")
    mapping = {
        'ą': 'a', 'ć': 'c', 'ę': 'e', 'ł': 'l', 'ń': 'n', 'ó': 'o', 'ś': 's', 'ź': 'z', 'ż': 'z',
        'Ą': 'A', 'Ć': 'C', 'Ę': 'E', 'Ł': 'L', 'Ń': 'N', 'Ó': 'O', 'Ś': 'S', 'Ź': 'Z', 'Ż': 'Z'
    }

    cleaned_names = []
    for data in stations_data.values():
        name = data.get("Nazwa stacji", "").strip()
        if name:
            no_space_name = space_pattern.sub("_", name)
            clean_name = diacritics_pattern.sub(lambda match: mapping[match.group()], no_space_name)
            cleaned_names.append(clean_name)

    return cleaned_names

def task_e (stations_data : dict):
    mob_pattern = re.compile(r"MOB$")

    all_true = True
    mob_found = 0

    for code, data in stations_data.items():
        if mob_pattern.search(code):
            mob_found += 1
            type = data.get("Rodzaj stacji", "")
            if not re.search(r"(?i)mobilna", type):
                logging.warning(f"Zad 4E: Stacja {code} ma rodzaj '{type}', a powinna być mobilna!")
                all_true = False

    if mob_found == 0:
        print("Nie znaleziono żadnych stacji kończących się na MOB.")
    elif all_true:
        print(f"Zweryfikowano pomyślnie. Wszystkie znalezione stacje ({mob_found}) to stacje mobilne.")
    else:
        print("Weryfikacja nie powiodła się. Niektóre stacje MOB nie są mobilne.")


def task_f(stations_data: dict):
    split_pattern = re.compile(r"\s+-\s+")
    three_part_locations = []

    for data in stations_data.values():
        name = data.get("Nazwa stacji", "").strip()
        parts = split_pattern.split(name)

        if len(parts) == 3:
            three_part_locations.append(name)

    print(f"Znaleziono {len(three_part_locations)} lokalizacji. Przykłady: {three_part_locations[:5]}")
    return three_part_locations


def task_g(stations_data: dict):
    pattern = re.compile(r",.*\b(?:ul\.|al\.)")
    matching_locations = []

    for data in stations_data.values():
        address = data.get("Nazwa stacji", "")
        if pattern.search(address):
            matching_locations.append(address)

    print(f"Znaleziono {len(matching_locations)} lokalizacji. Przykłady: {matching_locations[:5]}")
    return matching_locations


if __name__ == "__main__":
    stations_file = Path("stacje.csv")

    try:
        data = parse_stations(stations_file)

        print("=" * 50)
        print("TEST ZADAŃ (A - G)")
        print("=" * 50)

        # Test A
        print("\n--- Podpunkt A: Wyodrębnianie dat ---")
        wynik_a = task_a(data)
        print(f"Znaleziono {len(wynik_a)} dat. Pierwsze 5: {wynik_a[:5]}")

        # Test B
        print("\n--- Podpunkt B: Wyciąganie współrzędnych ---")
        wynik_b = task_b(data)
        print(f"Znaleziono {len(wynik_b)} współrzędnych. Pierwsze 5: {wynik_b[:5]}")

        # Test C
        print("\n--- Podpunkt C: Nazwy 2-członowe ---")
        wynik_c = task_c(data)
        print(f"Znaleziono {len(wynik_c)} stacji. Pierwsze 5: {wynik_c[:5]}")

        # Test D
        print("\n--- Podpunkt D: Zamiana spacji i znaków diakrytycznych ---")
        wynik_d = task_d(data)
        print(f"Przetworzono {len(wynik_d)} nazw. Pierwsze 5: {wynik_d[:5]}")

        # Test E
        print("\n--- Podpunkt E: Weryfikacja stacji MOB ---")
        task_e(data)

        # Test F
        print("\n--- Podpunkt F: Lokalizacje 3-członowe ---")
        task_f(data)

        # Test G
        print("\n--- Podpunkt G: Przecinek i ul./al. ---")
        task_g(data)

        print("\n" + "=" * 50)
        print(" TESTOWANIE ZAKOŃCZONE")
        print("=" * 50)

    except FileNotFoundError:
        logging.error(f"Nie znaleziono pliku metadanych: {stations_file}")
    except Exception as e:
        logging.error(f"Wystąpił nieoczekiwany błąd w głównym bloku wykonawczym: {e}")