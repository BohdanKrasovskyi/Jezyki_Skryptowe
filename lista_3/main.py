import sys
from log_analyzer import (
read_log, sort_log, get_entries_by_code, get_entries_by_addr, get_failed_reads, get_entries_by_extension, get_entries_in_time_range,
get_top_ips, get_unique_methods, count_by_method, get_top_uris, count_status_classes, get_extension_stats
)


def main():
    #Zad 1 - Wczytywanie logów
    parsed_log = read_log(sys.stdin)

    #Zad2 - Sortowanie
    sorted_logs = sort_log(parsed_log, 9)
    print("Posortowane logi \n")
    for entry in sorted_logs:
        print(entry)

    #Zad3 - Filtrowanie po kodzie
    logs_by_code = get_entries_by_code(parsed_log, 401)
    print("Logi z kodem HTTP: \n")
    for entry in logs_by_code:
        print(entry)

    #Zad4 - szukanie po ip lub nazwie hosta
    logs_by_ip = get_entries_by_addr(parsed_log, "google.com")
    print("Logi z ip albo nazwa hosta: \n")
    for entry in logs_by_ip:
        print(entry)

    #Zad5
    failed_reads = get_failed_reads(parsed_log, merge=True)
    print("Błędne logi: \n")
    for entry in failed_reads:
        print(entry)

    #Zad6
    extension_reads = get_entries_by_extension(parsed_log, ".html")
    print("Logi z rozszerzeniem: \n")
    for entry in extension_reads:
        print(entry)

    #Zad7
    most_common_ips = get_top_ips(parsed_log, 10)
    print("Najczęstsze ip: \n")
    for entry in most_common_ips:
        print(entry)

    #Zad8
    unique_methods = get_unique_methods(parsed_log)
    print("Użyte metody http: \n")
    for entry in unique_methods:
        print(entry)

    #Zad9
    entries_in_time_range = get_entries_in_time_range(parsed_log, 0, 100.05)
    print("Logi z zakresu czasu: \n")
    for entry in entries_in_time_range:
        print(entry)

    #Zad10
    dict_of_methods = count_by_method(parsed_log)
    print("Słownik metod: \n")
    print(dict_of_methods)

    #Zad11
    most_common_uris = get_top_uris(parsed_log, 10)
    print("Najczęstsze URI: \n")
    for entry in most_common_uris:
        print(entry)

    # Zad12
    status_nums = count_status_classes(parsed_log)
    print("Najczęstsze URI: \n")
    print(status_nums)

    # Zad13
    extenstion_stats = get_extension_stats(parsed_log)
    print("Statystyki rozszerzeń: \n")
    print(extenstion_stats)

if __name__ == "__main__":
    main()
