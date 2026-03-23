import datetime
import sys
from enum import IntEnum
import datetime
import ipaddress
from http import HTTPStatus #statusy http do filtrowania listy
from collections import Counter
import os

class Log_Idxs(IntEnum):
    TS = 0      #Znacznik czasu
    UID = 1     #Identyfikator sesji
    ORIG_H = 2  #IP klienta
    ORIG_P = 3  #Port klienta
    RESP_H = 4  #IP serwera
    RESP_P = 5  #Port serwera
    METHOD = 6  #Metoda HTTP
    HOST = 7    #Host
    URI = 8     #Ścieżka URI
    STATUS = 9  #Kod statusu

#funkcja do bezpiecznego konwertowania na int
def safe_int(field):
    if field is not None:
        return int(field)
    else: return None

def read_log(input_stream):
    list_of_tuples = []
    for line in input_stream:
        if not line.strip(): #jezeli linia jest pusta
            continue
        else:
            line = line.rstrip('\r\n').split("\t")
            line = [None if field == "-" else field for field in line]

        my_tuple = (
            datetime.datetime.fromtimestamp (float(line[0])),
            line[1],
            line[2],
            safe_int(line[3]),
            line[4],
            safe_int(line[5]),
            line[7],
            line[8],
            line[9],
            safe_int(line[14]),
        )
        list_of_tuples.append(my_tuple)
    return list_of_tuples

#ZAD2
def sort_log(log, index):
    try:
        #funckja pomocnicza-zamienia None na -1 lub ""
        def safe_key(tup):
            val = tup[index]
            if val is None:
                if index in (Log_Idxs.ORIG_P, Log_Idxs.RESP_P, Log_Idxs.STATUS):
                    return -1
                else: return ""
            return val
        return sorted(log, key=safe_key) #sortujemy według indeksu, bez wartości None
    except IndexError:
        print(f"Błąd: Indeks {index} wykracza poza rozmiar krotki!")
        return []
    except TypeError:
        print(f"Błąd: Nieprawidłowy typ argumentu")
        return []

#ZAD3
def get_entries_by_code(log, code):
    try:
        valid_status = HTTPStatus(code) #rzuca ValueError
    except ValueError:
        print(f"Błąd: '{code}' nie jest poprawnym statusem HTTP!")
        return []
    return [entry for entry in log if entry[Log_Idxs.STATUS] == code]

#ZAD4
def get_entries_by_addr(log, addr):
    is_ip_format = all(c.isdigit() or c == '.' for c in addr)

    if is_ip_format:
        try:
            ipaddress.ip_address(addr) #rzuca ValueError
        except ValueError:
            print(f"Błąd: '{addr}' nie jest poprawnym adresem IP")
            return []
    return [
        entry for entry in log
        if entry[Log_Idxs.ORIG_H] == addr or entry[Log_Idxs.HOST] == addr
    ]

#ZAD5
def get_failed_reads(log, merge=False):
    if merge:
        return [
            entry for entry in log
            if entry[Log_Idxs.STATUS] is not None and entry[Log_Idxs.STATUS] // 100 in (4,5)
        ]
    else:
        list_4xx = []
        list_5xx = []
        for entry in log:
            status = entry[Log_Idxs.STATUS]

            if status is not None:
                first_digit = status // 100
                if first_digit == 4:
                    list_4xx.append(entry)
                elif first_digit == 5:
                    list_5xx.append(entry)

        return list_4xx, list_5xx

#ZAD6
def get_entries_by_extension(log, ext):
    normalized_ext = ext if ext.startswith('.') else f".{ext}" #przyjmuje "jpg" albo ".jpg"

    return [
        entry for entry in log
        if entry[Log_Idxs.URI] is not None #sciezka istnieje
           and entry[Log_Idxs.URI].split('?')[0].endswith(normalized_ext) #czesc przed parametrami '?' zawiera rozszerzenie
    ]

#ZAD7
def get_top_ips(log, n=10):
    ips = [entry[Log_Idxs.ORIG_H] for entry in log if entry[Log_Idxs.ORIG_H] is not None] #tworzymy liste ip
    return Counter(ips).most_common(n) #wyciągamy n najczęściej występujących

#ZAD8
def get_unique_methods(log):
    #set nie pozwala na duplikaty, więc dodajemy wszystko, co nie jest puste
    unique_methods_set = {
        entry[Log_Idxs.METHOD]
        for entry in log
        if entry[Log_Idxs.METHOD] is not None
    }
    return list(unique_methods_set)

#ZAD9
def get_entries_in_time_range(log, start, end):
    if start > end:
        print(f"Błąd: Czas początkowy ({start}) jest późniejszy niż czas końcowy ({end})!")
        return []
    try:
        time_of_start = datetime.datetime.fromtimestamp(start)
        time_of_end = datetime.datetime.fromtimestamp(end)
    except (TypeError, ValueError, OverflowError):
        print(f"Błąd: Nieprawidłowy format czasu!")
        return []
    return [
        entry for entry in log
        if entry[Log_Idxs.TS] is not None and time_of_start <= entry[Log_Idxs.TS] < time_of_end
    ]

#ZAD10
def count_by_method(log):
    methods = [entry[Log_Idxs.METHOD] for entry in log if entry[Log_Idxs.METHOD] is not None]
    return dict(Counter(methods))

#ZAD11
def get_top_uris(log, n=10):
    uris = [entry[Log_Idxs.URI] for entry in log if entry[Log_Idxs.URI] is not None] #tworzymy liste URI
    return Counter(uris).most_common(n) #wyciągamy n najczęściej występujących

#ZAD12
def count_status_classes(log):
    status_counts = {'2xx': 0, '3xx': 0, '4xx': 0, '5xx': 0}
    for entry in log:
        status = entry[Log_Idxs.STATUS]

        if status is not None:
            first_digit = status // 100 #pierwsza cyfra statusu
            group_key = f"{first_digit}xx" #2xx, 3xx itd

            if group_key in status_counts:
                status_counts[group_key] += 1 #zliczamy statusy
    return status_counts

#ZAD19
def get_extension_stats(log):
    extensions = []
    for entry in log:
        uri = entry[Log_Idxs.URI]
        if uri is not None:
            clean_uri = uri.split('?')[0] #odcinamy wszystko po znaku zapytania
            _, ext = os.path.splitext(clean_uri) #oddzielenie rozszerzenia od reszty
            #jezeli istnieje rozszerzenie
            if ext:
                clean_ext = ext[1:].lower() #standaryzujemy
                extensions.append(clean_ext)
    return dict(Counter(extensions))

def main():
    read_log(sys.stdin)

if __name__ == "__main__":
    main()

