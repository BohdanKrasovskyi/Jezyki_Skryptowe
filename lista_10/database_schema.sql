PRAGMA foreign_keys = ON;

CREATE TABLE stations (
    station_id INTEGER PRIMARY KEY AUTOINCREMENT,
    station_name TEXT UNIQUE NOT NULL
);

CREATE TABLE rentals (
    rental_id INTEGER PRIMARY KEY,
    bike_number INTEGER NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    rental_station_id INTEGER,
    return_station_id INTEGER,
    duration INTEGER NOT NULL,

    FOREIGN KEY (rental_station_id) REFERENCES stations (station_id) ON DELETE SET NULL,
    FOREIGN KEY (return_station_id) REFERENCES stations (station_id) ON DELETE SET NULL
);