import csv
import re
from pathlib import Path
from datetime import datetime
from TimeSeries import TimeSeries
from data_manager import parse_measurements

class Measurements:
    def __init__(self, directory_path: str):
        self.directory_path = Path(directory_path)
        self._file_metadata = {}
        self._loaded_data = {}
        self.build_index()


    def build_index(self):
        pattern = re.compile(r"^(\d{4})_([a-zA-Z0-9()_]+)_([a-zA-Z0-9]+)\.csv$")

        for file_path in self.directory_path.iterdir():
            if file_path.is_file():
                match = pattern.match(file_path.name)

                if match:
                    year, indicator, frequency = match.groups()

                    with file_path.open(encoding="utf-8") as file:
                        reader = csv.reader(file)
                        stations = []
                        unit = ""

                        for line_idx, row in enumerate(reader):
                            if line_idx == 1:
                                stations = [code.strip() for code in row[1:] if code.strip()]
                            elif line_idx == 4:
                                if len(row) > 1:
                                    unit = row[1].strip()
                            elif line_idx > 4: #przerywamy, żeby nie ładować pomiarów
                                break

                    self._file_metadata[file_path] = {
                        "indicator": indicator,
                        "freq": frequency,
                        "stations": stations,
                        "unit": unit
                    }

    def __len__(self):
        total_series = sum(len(meta["stations"]) for meta in self._file_metadata.values())
        return total_series

    def __contains__(self, parameter_name : str) -> bool:
        return any(meta["indicator"] == parameter_name for meta in self._file_metadata.values())

    def _load_file(self, file_path: Path):
        if file_path not in self._loaded_data:
            self._loaded_data[file_path] = parse_measurements(file_path)


    def _create_time_series(self, file_path: Path, station_code : str) -> TimeSeries:
        meta = self._file_metadata[file_path]
        measurements_dict = self._loaded_data[file_path]

        station_data = measurements_dict.get(station_code, [])

        list_of_dates = []
        measurements_values = []

        for record in station_data:
            dt = datetime.strptime(record["time"], "%m/%d/%y %H:%M")
            list_of_dates.append(dt.date())
            measurements_values.append(record["value"])

        return TimeSeries(
            name_of_indicator=meta["indicator"],
            code_of_station=station_code,
            averaging_time=meta["freq"],
            list_of_dates=list_of_dates,
            measurement=measurements_values,
            unit_of_measurement=meta["unit"]
        )

    def get_by_parameter(self, param_name : str) -> list[TimeSeries]:
        result = []
        for file_path, meta in self._file_metadata.items():
            if meta["indicator"] == param_name:
                self._load_file(file_path)

                for station in meta["stations"]:
                    result.append(self._create_time_series(file_path, station))

        return result

    def get_by_station(self, station_code : str) -> list[TimeSeries]:
        result = []
        for file_path, meta in self._file_metadata.items():
            if station_code in meta["stations"]:
                self._load_file(file_path)
                result.append(self._create_time_series(file_path, station_code))

        return result


    def detect_all_anomalies(self, validators : list['SeriesValidator'], preload: bool = False) -> dict:
        results = {}

        if preload:
            for file_path in self._file_metadata.keys():
                self._load_file(file_path)

        series_to_validate = []

        for file_path, meta in self._file_metadata.items():
            if not preload and file_path not in self._loaded_data:
                continue

            for station in meta["stations"]:
                series = self._create_time_series(file_path, station)
                series_to_validate.append(series)

        for series in series_to_validate:
            for validator in validators:
                anomalies = validator.analyze(series)

                if anomalies:
                    key = f"{series.name_of_indicator} ({series.code_of_station})"

                    if key not in results:
                        results[key] = []

                    results[key].extend(anomalies)

        return results


if __name__ == "__main__":
    DIRECTORY_WITH_CSV = "data"

    # ---------------------------------------------------------
    print("\n[Inicjalizacja obiektu (__init__)]")
    # 1. Poprawne dane
    try:
        pomiary = Measurements(DIRECTORY_WITH_CSV)
        print(f"Obiekt Measurements poprawnie zainicjalizowany. {pomiary}")
    except Exception as e:
        print(f"BŁĄD: {e}")

    #Zły typ danych
    try:
        zle_pomiary = Measurements(12345)
    except TypeError:
        print(f"BŁĄD: Wprowadzono zły typ danych")


    print("\n[Metoda __len__]")
    #poprawne dane
    print(f"Łączna liczba obiektów do załadowania to: {len(pomiary)}")

    print("\n[Metoda __contains__]")
    #wartośc isntieje
    print(f"Czy 'SO2' jest w danych? {'SO2' in pomiary}")

    #wartość nie istnieje w danych
    print(f"Czy 'abc' jest w danych? {'abc' in pomiary}")

    # ---------------------------------------------------------
    print("\n[Metoda get_by_station]")
    #poprawne
    serie_sniezka = pomiary.get_by_station("DsSniezkaObs")
    print(f"Znaleziono {len(serie_sniezka)} serii dla stacji 'DsSniezkaObs'")

    #stacja nie istnieje
    puste_serie = pomiary.get_by_station("BrakTakiejStacji")
    print(f"Szukamy nieistniejącej stacji: {len(puste_serie)}, {puste_serie}")

    #podajemy None
    try:
        zle_szukanie = pomiary.get_by_station(None)
        print(f"Dla None -> {zle_szukanie}")
    except Exception as e:
        print(e)

    # ---------------------------------------------------------
    print("\n[Metoda get_by_parameter]")
    #poprawne dane
    serie_so2 = pomiary.get_by_parameter("SO2")
    print(f"Znaleziono {len(serie_so2)} serii dla parametru 'SO2'.")

    #parametr nie istnieje
    serie_puste_param = pomiary.get_by_parameter("abc")
    print(f"Dla nieistniejącego parametru: {serie_puste_param}")



