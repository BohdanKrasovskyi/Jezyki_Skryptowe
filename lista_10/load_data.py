import sys
import csv
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from create_database import Stations, Rentals

def load_data(path, db_name):
    db_filename = f"{db_name}.sqlite3"

    engine = create_engine(f"sqlite:///{db_filename}")
    Session = sessionmaker(bind=engine)
    session = Session()

    unique_station_names = set()

    with open(path, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['Stacja wynajmu'] and row['Stacja wynajmu'].strip() != 'Poza stacją':
                unique_station_names.add(row['Stacja wynajmu'].strip())
            if row['Stacja zwrotu'] and row['Stacja zwrotu'].strip() != 'Poza stacją':
                unique_station_names.add(row['Stacja zwrotu'].strip())

    existing_stations = session.scalars(select(Stations)).all()
    station_cache = {s.station_name: s.station_id for s in existing_stations}

    new_stations_to_add = []
    for name in unique_station_names:
        if name not in station_cache:
            new_stations_to_add.append(Stations(station_name=name))

    if new_stations_to_add:
        print(f"Znaleziono {len(new_stations_to_add)} nowych stacji. Dodawanie do bazy.")
        session.add_all(new_stations_to_add)
        session.commit()

        for s in new_stations_to_add:
            station_cache[s.station_name] = s.station_id

    existing_ids = set(session.scalars(select(Rentals.rental_id)).all())

    with open(path, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if int(row['UID wynajmu']) in existing_ids:
                continue

            start_name = row['Stacja wynajmu'].strip() if row['Stacja wynajmu'] else None
            end_name = row['Stacja zwrotu'].strip() if row['Stacja zwrotu'] else None

            start_id = station_cache.get(start_name)
            end_id = station_cache.get(end_name)

            rental = Rentals(
                rental_id=int(row['UID wynajmu']),
                bike_number=int(row['Numer roweru']),
                start_time=row['Data wynajmu'],
                end_time=row['Data zwrotu'],
                rental_station_id=start_id,
                return_station_id=end_id,
                duration=int(row['Czas trwania'])
            )
            session.add(rental)

        session.commit()
        print(f"Dodano obiekty do bazy '{db_name}'")
        session.close()

def main():
    if len(sys.argv) < 3:
        print("Błąd: Niepoprawna liczba argumentów!")
        print("Użycie: python load_data.py <plik_historii.csv> <nazwa_bazy>")
        sys.exit(1)

    csv_path = sys.argv[1]
    db_name = sys.argv[2]

    try:
        load_data(csv_path, db_name)
    except FileNotFoundError:
        print(f"Błąd: Nie znaleziono pliku CSV pod ścieżką: {csv_path}")
    except Exception as e:
        print(f"Wystąpił nieoczekiwany błąd podczas ładowania danych: {e}")

if __name__ == "__main__":
    main()