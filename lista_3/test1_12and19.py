import sys

from log_analyzer import (
read_log, sort_log, get_entries_by_code, get_entries_by_addr, get_failed_reads, get_entries_by_extension, get_entries_in_time_range,
get_top_ips, get_unique_methods, count_by_method, get_top_uris, count_status_classes, get_extension_stats
)
from main import print_logs

def main():
    #Zad 1 - Wczytywanie logów
    parsed_log = read_log(sys.stdin)
    print("ZAD1: WCZYTANE LOGI - obsługa None, pominięcie pustej linii, konwersja typów:")
    print_logs(parsed_log, 8)

    #Zad2 - Sortowanie
    print("\nZAD2: POSORTOWANE LOGI: niepoprawny typ")
    sorted_logs = sort_log(parsed_log, "a")
    print_logs(sorted_logs, 8)

    #Zad3 - Filtrowanie po kodzie
    print("\nZAD3: LOGI Z DANYM KODEM HTTP: - obsługa błędnego kodu")
    logs_by_code = get_entries_by_code(parsed_log, 601)
    print_logs(logs_by_code, 8)

    # Zad4 - Szukanie po IP lub nazwie hosta
    print("\nZAD4: LOGI Z ADRESEM LUB NAZWĄ HOSTA '192.168.202.280' - obsługa błędnego adresu ip")
    logs_by_ip = get_entries_by_addr(parsed_log, "192.168.202.280")
    print_logs(logs_by_ip, 8)

    # Zad5 - Błędne logi
    failed_reads = get_failed_reads(parsed_log, merge=False)
    print("\nZAD5: BŁĘDNE LOGI (4xx i 5xx) - merge = False")
    print_logs(failed_reads, 8)

    # Zad6 - Szukanie po rozszerzeniu
    extension_reads = get_entries_by_extension(parsed_log, ".php")
    print("\nZAD6: LOGI Z ROZSZERZENIEM '.php' - poprawne rozpoznanie błędnego pliku .jpg")
    print_logs(extension_reads, 8)

    # Zad7 - Najczęstsze IP
    most_common_ips = get_top_ips(parsed_log, 10)
    print("\nZAD7: NAJCZĘSTSZE IP- obsługa (pominięcie) ip, które jest puste")
    print_logs(most_common_ips, 8)

    # Zad8 - Unikalne metody HTTP
    # Rzutujemy na listę w razie, gdyby funkcja zwracała zbiór (set), którego nie da się ciąć [:5]
    unique_methods = list(get_unique_methods(parsed_log))
    print("\nZAD8: UNIKALNE METODY HTTP - obsługa (pominięcie) metody, która jest pusta")
    print_logs(unique_methods, 8)

    # Zad9 - Logi z zakresu czasu
    print("\nZAD9: LOGI Z ZAKRESU CZASU - początek > koniec")
    entries_in_time_range = get_entries_in_time_range(parsed_log, 20, 10)
    print_logs(entries_in_time_range, 8)

    # Zad10 - Słownik metod HTTP
    dict_of_methods = count_by_method(parsed_log)
    print("\nZAD10: SŁOWNIK METOD HTTP")
    print(dict_of_methods)  # Cały słownik, print_logs by tu nie zadziałało

    # Zad11 - Najczęstsze URI
    most_common_uris = get_top_uris(parsed_log, 10)
    print("\nZAD11: NAJCZĘSTSZE URI Z TOP 10 (5 pierwszych)-obsługa None")
    print_logs(most_common_uris, 8)

    # Zad12 - Klasy kodów statusu
    status_nums = count_status_classes(parsed_log)
    print("\nZAD12: ZLICZONE KLASY KODÓW STATUSU (2xx, 3xx, 4xx, 5xx) - obsługa None - brak w słowniku")
    print(status_nums)  # Słownik

    # Zad19 - Statystyki rozszerzeń
    extension_stats = get_extension_stats(parsed_log)
    print("\nZAD19: STATYSTYKI ROZSZERZEŃ - osbługa wielkich liter 'GZ' oraz URI bez rozszerzenia - brak w słowniku")
    print(extension_stats)  # Słownik lub krotka

if __name__ == "__main__":
    main()


