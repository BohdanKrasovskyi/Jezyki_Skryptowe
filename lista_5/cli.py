"""
  python cli.py --type SO2 --freq 24g --start 2023-01-01 --end 2023-12-31 random-station
  python cli.py --type SO2 --freq 24g  --start 2023-03-01 --end 2023-06-30 stats --station PmLebaRabka1
  python cli.py --type NO2  --freq 1g --start 2023-01-01 --end 2023-12-31 anomalies
"""

import argparse
import logging
import random
import re
import statistics
import sys
from datetime import datetime
from pathlib import Path

from data_manager import (parse_stations,parse_measurements,group_measurement_files_by_key,)
from anomaly import Measurement, detect_anomalies

class _MaxLevelFilter(logging.Filter):
    def __init__(self, max_level: int):
        super().__init__()
        self.max_level = max_level

    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno <= self.max_level


def setup_logging() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    fmt = logging.Formatter("%(asctime)s [%(levelname)-8s] %(message)s",
                             datefmt="%Y-%m-%d %H:%M:%S")

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.DEBUG)
    stdout_handler.addFilter(_MaxLevelFilter(logging.WARNING))
    stdout_handler.setFormatter(fmt)

    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(logging.ERROR)
    stderr_handler.setFormatter(fmt)

    root.addHandler(stdout_handler)
    root.addHandler(stderr_handler)

_VALID_TYPE_RE = re.compile(r"^[A-Za-z][A-Za-z0-9.]*$")

_VALID_FREQ_RE = re.compile(r"^\d+g$", re.IGNORECASE)


def validate_date(value: str) -> datetime:
    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"Invalid date '{value}'. Expected format: YYYY-MM-DD"
        )


def validate_type(value: str) -> str:
    if not _VALID_TYPE_RE.match(value):
        raise argparse.ArgumentTypeError(
            f"Invalid measurement type '{value}'. "
            "Use alphanumeric names (e.g. PM2.5, PM10, SO2, NO2, CO, O3)."
        )
    return value


def validate_freq(value: str) -> str:
    if not _VALID_FREQ_RE.match(value):
        raise argparse.ArgumentTypeError(
            f"Invalid frequency '{value}'. Expected pattern: <digits>g (e.g. 1g, 24g)."
        )
    return value.lower()

def load_measurements_for_params(type_: str, freq: str, data_dir: Path) -> dict[str, list[dict]]:
    grouped = group_measurement_files_by_key(data_dir)
    combined: dict[str, list[dict]] = {}
    found_any = False

    for (year, mtype, mfreq), path in grouped.items():
        if mtype.upper() == type_.upper() and mfreq.lower() == freq.lower():
            found_any = True
            data = parse_measurements(path)
            for code, records in data.items():
                combined.setdefault(code, []).extend(records)

    if not found_any:
        logging.warning(
            f"No measurement files found for type='{type_}', freq='{freq}' "
            f"in '{data_dir}'. "
            "Check that the data directory contains matching CSV files."
        )

    return combined


def filter_by_date( records: list[dict], start: datetime, end: datetime) -> list[dict]:
    result = []
    for r in records:
        try:
            t = datetime.strptime(r["time"][:10], "%Y-%m-%d")
            if start <= t <= end:
                result.append(r)
        except (ValueError, KeyError):
            logging.debug(f"Pominięto rekord z nieparsowanym czasem: {r.get('time', '?')}")
    return result

def cmd_random_station(args: argparse.Namespace,stations_data: dict,data_dir: Path) -> None:
    all_measurements = load_measurements_for_params(args.type, args.freq, data_dir)
    if not all_measurements:
        logging.warning(
            f"No measurement data available for type='{args.type}', freq='{args.freq}'."
        )
        return

    eligible: list[str] = []
    for code, records in all_measurements.items():
        if filter_by_date(records, args.start, args.end):
            eligible.append(code)

    if not eligible:
        logging.warning(
            f"No stations have '{args.type}' measurements (freq={args.freq}) "
            f"in the range {args.start.date()} – {args.end.date()}."
        )
        return

    code = random.choice(eligible)
    station = stations_data.get(code)

    if station is None:
        logging.warning(
            f"Station '{code}' was found in measurements but has no entry in the "
            "stations metadata file."
        )
        print(f"Station: {code}  (no metadata available)")
        return

    name     = station.get("Nazwa stacji", "N/A").strip()
    address  = station.get("Adres",        "N/A").strip()
    city     = station.get("Miejscowość",  "N/A").strip()
    voiv     = station.get("Województwo",  "N/A").strip()

    print(f"Station:   {name}")
    print(f"Code:      {code}")
    print(f"Address:   {address}, {city}")
    print(f"Province:  {voiv}")



def cmd_stats(args: argparse.Namespace,stations_data: dict,data_dir: Path) -> None:
    all_measurements = load_measurements_for_params(args.type, args.freq, data_dir)
    if not all_measurements:
        return

    if args.station not in all_measurements:
        logging.warning(
            f"Station '{args.station}' has no '{args.type}' data at frequency "
            f"'{args.freq}'. "
            "It may not measure this quantity, or the data file may be missing."
        )
        return

    records = filter_by_date(all_measurements[args.station], args.start, args.end)

    if not records:
        logging.warning(
            f"No '{args.type}' measurements for station '{args.station}' (freq={args.freq}) "
            f"in the range {args.start.date()} – {args.end.date()}."
        )
        return

    values = [r["value"] for r in records]
    mean   = statistics.mean(values)
    std    = statistics.stdev(values) if len(values) > 1 else 0.0

    station_name = stations_data.get(args.station, {}).get("Nazwa stacji", args.station)

    print(f"Station:   {station_name} ({args.station})")
    print(f"Type:      {args.type}  |  Frequency: {args.freq}")
    print(f"Period:    {args.start.date()} – {args.end.date()}")
    print(f"Readings:  {len(values)}")
    print(f"Mean:      {mean:.4f}")
    print(f"Std-dev:   {std:.4f}")

def cmd_anomalies(args: argparse.Namespace, data_dir: Path) -> None:
    all_measurements = load_measurements_for_params(args.type, args.freq, data_dir)
    if not all_measurements:
        return

    station_filter = getattr(args, "station", None)
    codes = [station_filter] if station_filter else list(all_measurements.keys())

    total_anomalies = 0

    for code in codes:
        if code not in all_measurements:
            logging.warning(
                f"Station '{code}' not found in '{args.type}' (freq={args.freq}) data."
            )
            continue

        records = filter_by_date(all_measurements[code], args.start, args.end)
        if not records:
            continue

        ms = [
            Measurement(
                time=r["time"],
                value=r["value"],
                station=code,
                quantity=args.type,
            )
            for r in records
        ]

        anomalies = detect_anomalies(
            ms,
            delta_threshold=args.delta_threshold,
            max_zero_streak=args.max_zero_streak,
        )

        if anomalies:
            total_anomalies += len(anomalies)
            print(f"\n[{code}]  {len(anomalies)} anomaly/anomalies detected:")
            for a in anomalies:
                print(f"  {a.measurement.time}  {a.reason}")

    if total_anomalies == 0:
        print("No anomalies detected for the given parameters.")
    else:
        print(f"\nTotal anomalies: {total_anomalies}")

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cli.py",
        description=(
            "Analyze GIOS air quality measurement data.\n\n"
            "Global arguments (--type, --freq, --start, --end) are required by "
            "every subcommand."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--stations",
        type=Path,
        default=Path("stacje.csv"),
        metavar="FILE",
        help="Path to stations metadata CSV (default: stacje.csv)",
    )
    parser.add_argument(
        "--data",
        type=Path,
        default=Path("data"),
        metavar="DIR",
        help="Directory with measurement CSV files (default: data/)",
    )
    parser.add_argument(
        "--type",
        required=True,
        type=validate_type,
        metavar="TYPE",
        help="Measured quantity, e.g. PM2.5, PM10, SO2, NO2, CO, O3",
    )
    parser.add_argument(
        "--freq",
        required=True,
        type=validate_freq,
        metavar="FREQ",
        help="Measurement frequency, e.g. 1g, 24g",
    )
    parser.add_argument(
        "--start",
        required=True,
        type=validate_date,
        metavar="YYYY-MM-DD",
        help="Start of the time range (inclusive)",
    )
    parser.add_argument(
        "--end",
        required=True,
        type=validate_date,
        metavar="YYYY-MM-DD",
        help="End of the time range (inclusive)",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser(
        "random-station",
        help="Print name and address of a random station with data in the given range",
    )
    stats_p = subparsers.add_parser(
        "stats",
        help="Compute mean and standard deviation for a specific station",
    )
    stats_p.add_argument(
        "--station",
        required=True,
        metavar="CODE",
        help="Station code, e.g. DsBogChop",
    )
    anom_p = subparsers.add_parser(
        "anomalies",
        help="Detect measurement anomalies (spikes, jumps, zero-streaks)",
    )
    anom_p.add_argument(
        "--station",
        default=None,
        metavar="CODE",
        help="Limit to a single station code (default: all stations)",
    )
    anom_p.add_argument(
        "--delta-threshold",
        type=float,
        default=200.0,
        dest="delta_threshold",
        metavar="N",
        help="Max allowed delta between consecutive readings (default: 200)",
    )
    anom_p.add_argument(
        "--max-zero-streak",
        type=int,
        default=5,
        dest="max_zero_streak",
        metavar="N",
        help="Max allowed consecutive zeros/None/negatives (default: 5)",
    )

    return parser

def main() -> None:
    setup_logging()
    parser = build_parser()
    args   = parser.parse_args()
    if args.start > args.end:
        parser.error(
            f"--start ({args.start.date()}) must not be after --end ({args.end.date()})"
        )

    if not args.stations.exists():
        logging.error(f"Stations file not found: {args.stations}")
        sys.exit(1)

    stations_data = parse_stations(args.stations)

    if not args.data.exists():
        logging.error(f"Data directory not found: {args.data}")
        sys.exit(1)

    if args.command == "random-station":
        cmd_random_station(args, stations_data, args.data)
    elif args.command == "stats":
        cmd_stats(args, stations_data, args.data)
    elif args.command == "anomalies":
        cmd_anomalies(args, args.data)


if __name__ == "__main__":
    main()