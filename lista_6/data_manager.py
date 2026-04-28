import csv
import logging
from pathlib import Path
import re



def log_line_bytes(file):
    for line in file:
        size = len(line.encode('utf-8')) #zamianiemy na bajty i liczymy len()

        logging.debug(f"Przeczytano wiersz. Rozmiar {size} bajtów")
        yield line #zwracamy wiersz

#---------ZAD1---------------
def parse_stations(path: Path) -> dict:
    logging.info(f"Otwieranie pliku z metadanymi: {path}")
    stations = {}

    with path.open(encoding="utf-8") as file:

        reader = csv.DictReader(log_line_bytes(file)) #najpierw liczymy długość wiersza, potem przekazujemy readerowi
        for row in reader:
            code = row["Kod stacji"].strip()
            stations[code] = row

    logging.info(f"Zamknięto plik: {path}")
    return stations


def parse_measurements(path: Path) -> dict:
    logging.info(f"Otwieranie pliku z pomiarami: {path}")
    measurements = {}

    with path.open(encoding="utf-8") as file:
        reader = csv.reader(log_line_bytes(file))
        station_codes = []

        for line_idx, row in enumerate(reader):
            if not row:
                continue

            if line_idx == 0: #Nr 1,2,3... ignorujemy
                pass
            elif line_idx == 1: #Kod stacji
                station_codes = row[1:] #tworzymy liste z kodami stacji

                for code in station_codes:
                    code = code.strip()
                    if code:
                        measurements[code] = [] #kluczem jest kod stacji

            elif line_idx in [2,3,4,5]: #wiersze 2-5 ignorujemy
                pass

            else: #właściwe pomiary
                time_of_measurement = row[0].strip()
                values = row[1:]

                for col_idx, val in enumerate(values):
                    if col_idx < len(station_codes):
                        code = station_codes[col_idx].strip()
                        val = val.strip()

                        if code and val:
                            val = val.replace(",", ".")

                            try:
                                float_values = float(val)
                                measurements[code].append({
                                    "time": time_of_measurement,
                                    "value": float_values,
                                })
                            except ValueError:
                                logging.warning(
                                    f"Pominięto błędną wartość pomiaru '{val}' dla stacji {code} o czasie {time_of_measurement}")
                                pass

    logging.info(f"Zamknięto plik: {path}")
    return measurements

#-------------ZAD2----------------
def group_measurement_files_by_key(path: Path) -> dict:

    grouped_files = {}
    pattern = re.compile(r"^(\d{4})_([a-zA-Z0-9()_]+)_([a-zA-Z0-9]+)\.csv$") #(4cyfry)_(litery/cryfry/_/())_(litery/cyfry).csv

    for file_path in path.iterdir():
        if file_path.is_file():
            match = pattern.match(file_path.name)

            if match:
                key = match.groups()
                grouped_files[key] = file_path
            else:
                logging.warning(
                    f"Plik '{file_path.name}' nie pasuje do formatu nazewnictwa pomiarów i został pominięty.")

    return grouped_files

#--------------ZAD3-----------
def get_addresses(path : Path, city) -> list:
    addresses = []
    stations_data = parse_stations(path)

    address_pattern = re.compile(r"^(.*?)(?:\s+(\d\S*))?$")
    city_pattern = re.compile(rf"^{city}$", re.IGNORECASE)

    for code, data in stations_data.items():
        if city_pattern.match(data["Miejscowość"].strip()):
            voivodeship = data["Województwo"].strip()
            city = data["Miejscowość"].strip()
            address_raw = data["Adres"].strip()

            street = ""
            number = ""

            if address_raw:
                match = address_pattern.match(address_raw)
                if match:
                    street = match.group(1).strip() if match.group(1) else ""
                    number = match.group(2).strip() if match.group(2) else ""
                else:
                    street = address_raw

            addresses.append((voivodeship, city, street, number))

    if not addresses:
        logging.warning(f"Nie znaleziono żadnych adresów stacji dla miejscowości: {city}")

    return addresses


if __name__ == "__main__":
    stations = parse_stations(Path("stacje.csv"))
    print(list(stations.items())[:5])

    measurements = parse_measurements(Path("data/2023_SO2_24g.csv"))
    print(measurements["LbJarczWolaM"][:3])

    grouped_files = group_measurement_files_by_key(Path("data"))
    print(grouped_files)

    addresses = get_addresses(Path("stacje.csv"), "Wrocław")
    print(addresses)