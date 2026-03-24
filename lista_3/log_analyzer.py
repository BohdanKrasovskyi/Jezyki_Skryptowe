import datetime
import sys
from enum import IntEnum
import datetime
import ipaddress
from http import HTTPStatus #statusy http do filtrowania listy
from collections import Counter, defaultdict
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
    if isinstance(start, (int, float)):
        start = datetime.datetime.fromtimestamp(start)
    if isinstance(end, (int, float)):
        end = datetime.datetime.fromtimestamp(end)

    if start > end:
        print(f"Błąd: Czas początkowy ({start}) jest późniejszy niż czas końcowy ({end})!")
        return []

    return [
        entry for entry in log
        if entry[Log_Idxs.TS] is not None and start <= entry[Log_Idxs.TS] < end
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

#ZAD13
def entry_to_dict(entry):
    if entry is None:
        return None

    #Musi byc 10 elementow
    entry = list(entry) + [None] * (10 - len(entry))

    return {
        "ts": entry[Log_Idxs.TS],
        "uid": entry[Log_Idxs.UID],
        "orig_h": entry[Log_Idxs.ORIG_H],
        "orig_p": entry[Log_Idxs.ORIG_P],
        "resp_h": entry[Log_Idxs.RESP_H],
        "resp_p": entry[Log_Idxs.RESP_P],
        "method": entry[Log_Idxs.METHOD],
        "host": entry[Log_Idxs.HOST],
        "uri": entry[Log_Idxs.URI],
        "status": entry[Log_Idxs.STATUS],
    }

#ZAD14
def log_to_dict(log):
    session_log = {}
    for entry in log:
        entry_dict = entry_to_dict(entry)
        uid = entry_dict.get("uid", "unknown")

        if uid not in session_log:
            session_log[uid] = []

        entry_dict.pop("uid", None)
        session_log[uid].append(entry_dict)

    return session_log

#ZAD15
def print_dict_entry_dates(log_dict):
    for uid, entries in log_dict.items():
        if not entries:
            continue

        ips_and_hosts = set()
        first_timestamp = entries[0].get("ts")
        last_timestamp = entries[0].get("ts")
        method_counts = Counter()
        count_2xx = 0

        for e in entries:
            if e.get("orig_h"):
                ips_and_hosts.add(e["orig_h"])
            if e.get("host"):
                ips_and_hosts.add(e["host"])

            timestamp = e.get("ts")
            if timestamp is not None:
                if timestamp < first_timestamp:
                    first_timestamp = timestamp
                if timestamp > last_timestamp:
                    last_timestamp = timestamp

            method = e.get("method")
            if method:
                method_counts[method] += 1

            status = e.get("status")
            try:
                valid_status = HTTPStatus(status)  # rzuca ValueError
                if status and 200 <= status < 300:
                    count_2xx += 1
            except (TypeError, ValueError):
                print(f"Błąd: '{status}' nie jest poprawnym statusem HTTP!")

        num_requests = len(entries)

        method_percent = {m : f"{(c / num_requests) * 100:.2f}%" for m, c in method_counts.items()}
        if num_requests > 0:
            ratio_2xx = f"{(count_2xx / num_requests) * 100:.2f}%"
        else:
            ratio_2xx = "Nie ma żadnych żądań"

        print(f"UID: {uid}")
        print(f"Adresy IP / hosty: {', '.join(ips_and_hosts)}")
        print(f"Liczba żądań: {num_requests}")
        print(f"Zakres dat: {first_timestamp} — {last_timestamp}")
        print(f"Procentowy udział metod HTTP: {method_percent}")
        print(f"Stosunek liczby kodów 2xx do wszystkich: {ratio_2xx}")
        print("-"*50)

#ZAD16
def most_active_session(log_dict):
    most_active_uid = None
    max_requests = 0
    for uid, entries in log_dict.items():
        if len(entries) > max_requests:
            most_active_uid = uid
            max_requests = len(entries)

    return most_active_uid

#ZAD17
def get_session_paths(log):
    session_paths = {}
    for entry in log:
        uid = entry[Log_Idxs.UID]
        uri = entry[Log_Idxs.URI]

        if uid is None or uri is None:
            continue

        if uid not in session_paths:
            session_paths[uid] = []
        session_paths[uid].append(uri)

    return session_paths

#ZAD18
def detect_sus(log, threshold, procent404 = 0.3, second_between_requests = 1, procent_of_fast_requests = 0.3):
    ip_data = dict()

    for entry in log:
        ip = entry[Log_Idxs.ORIG_H]
        status = entry[Log_Idxs.STATUS]
        ts = entry[Log_Idxs.TS]

        if not ip:
            continue

        try:
            ipaddress.ip_address(ip) #rzuca ValueError
        except ValueError:
            print(f"Błąd: '{ip}' nie jest poprawnym adresem IP")

        if ip not in ip_data:
            ip_data[ip] = {"count": 0,"errors_404": 0,"timestamps": []}

        ip_data[ip]["count"] += 1

        if status == 404:
            ip_data[ip]["errors_404"] += 1

        if ts:
            ip_data[ip]["timestamps"].append(ts)

    suspicious_ips = []
    for ip, data in ip_data.items():
        if data["count"] >= threshold:
            suspicious_ips.append(ip)
            continue

        if data["errors_404"] > data["count"] * procent404:
            suspicious_ips.append(ip)
            continue

        fast_requests = 0
        times = sorted(data["timestamps"])
        for i in range(1, len(times)):
            delta = (times[i] - times[i - 1]).total_seconds()
            if delta < second_between_requests:
                fast_requests += 1

        if fast_requests > procent_of_fast_requests * data["count"]:
            suspicious_ips.append(ip)

    return suspicious_ips



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

#ZAD20
def analyze_log(log, how_many_stats = 5):
    ip_counts = Counter()
    uri_counts = Counter()
    method_counts = Counter()
    error_counts = 0
    status_classes = {"2xx" : 0, "3xx" : 0, "4xx" : 0, "5xx" : 0}

    for entry in log:
        ip = entry[Log_Idxs.ORIG_H]
        uri = entry[Log_Idxs.URI]
        method = entry[Log_Idxs.METHOD]
        status = entry[Log_Idxs.STATUS]
        if ip is not None:
            try:
                ipaddress.ip_address(ip)
                ip_counts[ip] += 1
            except ValueError:
                print(f"Błąd: '{ip}' nie jest poprawnym adresem IP")
        if uri is not None:
            uri_counts[uri] += 1
        if method is not None:
            method_counts[method] += 1
        if status is not None:
            try:
                valid_status = HTTPStatus(status)
                if status >= 400:
                    error_counts += 1
                group = f"{status // 100}xx"
                if group in status_classes:
                    status_classes[group] += 1
            except ValueError:
                print(f"Błąd: '{status}' nie jest poprawnym statusem HTTP!")

    result = {
            "top_ips" : ip_counts.most_common(how_many_stats),
            "top_uris" : uri_counts.most_common(how_many_stats),
            "method_distribution" : dict(method_counts),
            "error_count" : error_counts,
            "status_classes" : status_classes,
            "unique_ips" : len(ip_counts),
            "unique_uris" : len(uri_counts),
        }

    return result

def main():
    read_log(sys.stdin)

if __name__ == "__main__":
    main()

