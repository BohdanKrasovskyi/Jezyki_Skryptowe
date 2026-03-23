import sys
from log_analyzer import (
read_log, sort_log, get_entries_by_code, get_entries_by_addr, get_failed_reads, get_entries_by_extension, get_entries_in_time_range,
get_top_ips, get_unique_methods, count_by_method, get_top_uris, count_status_classes, get_extension_stats
)

def print_logs(logs, n):
    for entry in logs[:n]:
        print(entry)

def main():
    #Zad 1 - Wczytywanie logów
    parsed_log = read_log(sys.stdin)
    print("ZAD1: WCZYTANE LOGI (5 pierwszych)")
    print_logs(parsed_log, 5)

    #Zad2 - Sortowanie
    sorted_logs = sort_log(parsed_log, 9)
    print("\nZAD2: POSORTOWANE LOGI według kodu statusu: (5 pierwszych)")
    print_logs(sorted_logs, 5)

    #Zad3 - Filtrowanie po kodzie
    logs_by_code = get_entries_by_code(parsed_log, 401)
    print("\nZAD3: LOGI Z DANYM KODEM HTTP: (5 pierwszych)")
    print_logs(logs_by_code, 5)

    # Zad4 - Szukanie po IP lub nazwie hosta
    logs_by_ip = get_entries_by_addr(parsed_log, "192.168.202.90")
    print("\nZAD4: LOGI Z ADRESEM LUB NAZWĄ HOSTA '192.168.202.90' (5 pierwszych)")
    print_logs(logs_by_ip, 5)

    # Zad5 - Błędne logi
    failed_reads = get_failed_reads(parsed_log, merge=True)
    print("\nZAD5: BŁĘDNE LOGI (4xx i 5xx) (5 pierwszych)")
    print_logs(failed_reads, 5)

    # Zad6 - Szukanie po rozszerzeniu
    extension_reads = get_entries_by_extension(parsed_log, ".html")
    print("\nZAD6: LOGI Z ROZSZERZENIEM '.html' (5 pierwszych)")
    print_logs(extension_reads, 5)

    # Zad7 - Najczęstsze IP
    most_common_ips = get_top_ips(parsed_log, 10)
    print("\nZAD7: NAJCZĘSTSZE IP Z TOP 10 (5 pierwszych)")
    print_logs(most_common_ips, 5)

    # Zad8 - Unikalne metody HTTP
    # Rzutujemy na listę w razie, gdyby funkcja zwracała zbiór (set), którego nie da się ciąć [:5]
    unique_methods = list(get_unique_methods(parsed_log))
    print("\nZAD8: UNIKALNE METODY HTTP (5 pierwszych)")
    print_logs(unique_methods, 5)

    # Zad9 - Logi z zakresu czasu
    entries_in_time_range = get_entries_in_time_range(parsed_log, 0, 100.05)
    print("\nZAD9: LOGI Z ZAKRESU CZASU 0 - 100.05 (5 pierwszych)")
    print_logs(entries_in_time_range, 5)

    # Zad10 - Słownik metod HTTP
    dict_of_methods = count_by_method(parsed_log)
    print("\nZAD10: SŁOWNIK METOD HTTP")
    print(dict_of_methods)  # Cały słownik, print_logs by tu nie zadziałało

    # Zad11 - Najczęstsze URI
    most_common_uris = get_top_uris(parsed_log, 10)
    print("\nZAD11: NAJCZĘSTSZE URI Z TOP 10 (5 pierwszych)")
    print_logs(most_common_uris, 5)

    # Zad12 - Klasy kodów statusu
    status_nums = count_status_classes(parsed_log)
    print("\nZAD12: ZLICZONE KLASY KODÓW STATUSU (2xx, 3xx, 4xx, 5xx)")
    print(status_nums)  # Słownik

    # Zad13 - Statystyki rozszerzeń
    extension_stats = get_extension_stats(parsed_log)
    print("\nZAD13: STATYSTYKI ROZSZERZEŃ")
    print(extension_stats)  # Słownik lub krotka

if __name__ == "__main__":
    main()
