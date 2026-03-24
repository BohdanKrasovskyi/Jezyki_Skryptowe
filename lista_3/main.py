import sys
import datetime

from log_analyzer import (
    read_log, sort_log, get_entries_by_code, get_entries_by_addr, get_failed_reads,
    get_entries_by_extension, get_entries_in_time_range, get_top_ips, get_unique_methods,
    count_by_method, get_top_uris, count_status_classes, get_extension_stats,
    entry_to_dict, log_to_dict, print_dict_entry_dates, most_active_session,
    get_session_paths, detect_sus, analyze_log
)

def print_logs(logs, n):
    for entry in logs[:n]:
        print(entry)

def main():
    # Zad1 - Wczytywanie logów
    parsed_log = read_log(sys.stdin)
    print("ZAD1: WCZYTANE LOGI (5 pierwszych)")
    print_logs(parsed_log, 5)

    # Zad2 - Sortowanie
    sorted_logs = sort_log(parsed_log, 9)
    print("\nZAD2: POSORTOWANE LOGI według kodu statusu (5 pierwszych)")
    print_logs(sorted_logs, 5)

    # Zad3 - Filtrowanie po kodzie
    logs_by_code = get_entries_by_code(parsed_log, 401)
    print("\nZAD3: LOGI Z DANYM KODEM HTTP (5 pierwszych)")
    print_logs(logs_by_code, 5)

    # Zad4 - Szukanie po IP lub nazwie hosta
    logs_by_ip = get_entries_by_addr(parsed_log, "192.168.202.90")
    print("\nZAD4: LOGI Z ADRESEM '192.168.202.90' (5 pierwszych)")
    print_logs(logs_by_ip, 5)

    # Zad5 - Błędne logi
    failed_reads = get_failed_reads(parsed_log, merge=True)
    print("\nZAD5: BŁĘDNE LOGI 4xx i 5xx (5 pierwszych)")
    print_logs(failed_reads, 5)

    # Zad6 - Szukanie po rozszerzeniu
    extension_reads = get_entries_by_extension(parsed_log, ".html")
    print("\nZAD6: LOGI Z ROZSZERZENIEM '.html' (5 pierwszych)")
    print_logs(extension_reads, 5)

    # Zad7 - Najczęstsze IP
    most_common_ips = get_top_ips(parsed_log, 10)
    print("\nZAD7: NAJCZĘSTSZE IP TOP 10")
    print_logs(most_common_ips, 10)

    # Zad8 - Unikalne metody HTTP
    unique_methods = list(get_unique_methods(parsed_log))
    print("\nZAD8: UNIKALNE METODY HTTP")
    print(unique_methods)

    # Zad9 - Logi z zakresu czasu (float — konwersja do datetime odbywa się w funkcji)
    entries_in_time_range = get_entries_in_time_range(parsed_log, 0, 100.05)
    print("\nZAD9: LOGI Z ZAKRESU CZASU 0 - 100.05 (5 pierwszych)")
    print_logs(entries_in_time_range, 5)

    # Zad10 - Słownik metod HTTP
    dict_of_methods = count_by_method(parsed_log)
    print("\nZAD10: SŁOWNIK METOD HTTP")
    print(dict_of_methods)

    # Zad11 - Najczęstsze URI
    most_common_uris = get_top_uris(parsed_log, 10)
    print("\nZAD11: NAJCZĘSTSZE URI TOP 10")
    print_logs(most_common_uris, 10)

    # Zad12 - Klasy kodów statusu
    status_nums = count_status_classes(parsed_log)
    print("\nZAD12: KLASY KODÓW STATUSU")
    print(status_nums)

    # Zad13 - Zamień krotkę na słownik
    if len(parsed_log) > 0:
        out_dict = entry_to_dict(parsed_log[0])
    else:
        out_dict = None
    print("\nZAD13: ENTRY JAKO DICT")
    print(out_dict)

    # Zad14 - Zamień log na słownik sesji
    log_dict = log_to_dict(parsed_log)
    print("\nZAD14: LOG JAKO DICT (3 pierwsze sesje)")
    for uid, entries in list(log_dict.items())[:3]:
        print(f"  UID: {uid} — {len(entries)} wpisów")

    # Zad15 - Statystyki sesji (10 pierwsze)
    print("\nZAD15: STATYSTYKI SESJI (10 pierwsze)")
    limited_dict = dict(list(log_dict.items())[:10])
    print_dict_entry_dates(limited_dict)

    # Zad16 - Najaktywniejsza sesja

    active = most_active_session(log_dict)
    print("\nZAD16: NAJAKTYWNIEJSZA SESJA")
    if active is not None:
        print(f"  UID: {active}, liczba żądań: {len(log_dict[active])}")

    # Zad17 - Ścieżki sesji
    session_paths = get_session_paths(parsed_log)
    print("\nZAD17: ŚCIEŻKI SESJI (3 pierwsze)")
    for uid, paths in list(session_paths.items())[:3]:
        print(f"  UID: {uid} — {paths[:5]}")

    # Zad18 - Podejrzane IP
    suspicious = detect_sus(parsed_log, threshold=100)
    print("\nZAD18: PODEJRZANE IP (próg=100)")
    print_logs(suspicious, 10)

    # Zad19 - Statystyki rozszerzeń
    extension_stats = get_extension_stats(parsed_log)
    print("\nZAD19: STATYSTYKI ROZSZERZEŃ")
    print(extension_stats)

    # Zad20 - Mini analiza logu
    analysis = analyze_log(parsed_log)
    print("\nZAD20: MINI ANALIZA LOGU")
    print(f"  Najczęstsze IP:  {analysis['top_ips']}")
    print(f"  Najczęstsze URI: {analysis['top_uris']}")
    print(f"  Rozkład metod:   {analysis['method_distribution']}")
    print(f"  Liczba błędów:   {analysis['error_count']}")
    print(f"  Klasy statusów:  {analysis['status_classes']}")
    print(f"  Unikalne IP:     {analysis['unique_ips']}")
    print(f"  Unikalne URI:    {analysis['unique_uris']}")


if __name__ == "__main__":
    main()