# python3 lis_to_csv.py --input-dir . --output-dir .
import argparse
import csv
import math
import re
import sys
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import List, Tuple


Event = Tuple[datetime, float, float, float, float]
EVENT_HEADER = re.compile(r"^\s*1\s+1\s+\d+(?:\.\d+)?\s+NLL\s+INST\s*$")


def read_events(path: Path) -> Tuple[List[Event], int]:
    events = []
    skipped_events = 0

    with path.open("r", encoding="utf-8-sig") as lis_file:
        lines = enumerate(lis_file, start=1)
        for line_number, line in lines:
            if not EVENT_HEADER.fullmatch(line):
                continue

            try:
                metadata_line_number, metadata_line = next(lines)
            except StopIteration:
                skipped_events += 1
                print(
                    f"{path}:{line_number}: skipped event; missing location record",
                    file=sys.stderr,
                )
                continue

            fields = metadata_line.split()
            if len(fields) != 13:
                skipped_events += 1
                print(
                    f"{path}:{metadata_line_number}: skipped event; expected "
                    f"13 location fields, got {len(fields)}",
                    file=sys.stderr,
                )
                continue

            try:
                seconds = Decimal(fields[8])
                if (
                    not seconds.is_finite()
                    or not Decimal("0") <= seconds < Decimal("61")
                ):
                    raise ValueError(f"seconds value out of range: {fields[8]}")

                event_time = datetime.strptime(
                    " ".join(fields[3:8]), "%Y %m %d %H %M"
                ) + timedelta(seconds=float(seconds))
                latitude = float(fields[0])
                longitude = float(fields[1])
                depth_km = float(fields[2])
                magnitude = float(fields[12])
                if not all(
                    math.isfinite(value)
                    for value in (latitude, longitude, depth_km)
                ):
                    raise ValueError("location is not finite")
            except (InvalidOperation, OverflowError, ValueError) as exc:
                skipped_events += 1
                print(
                    f"{path}:{metadata_line_number}: skipped invalid event "
                    f"({exc}): {metadata_line.rstrip()}",
                    file=sys.stderr,
                )
                continue

            events.append(
                (event_time, magnitude, latitude, longitude, depth_km)
            )

    return events, skipped_events


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Convert NonLinLoc .lis catalogues into the shared event CSV format."
        )
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        required=True,
        help="Folder containing the .lis catalogue files",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Folder for the separate CSV files (default: the input folder)",
    )
    args = parser.parse_args()

    if not args.input_dir.is_dir():
        parser.error(f"not a folder: {args.input_dir}")

    lis_files = sorted(
        (
            path for path in args.input_dir.iterdir()
            if path.is_file() and path.suffix.lower() == ".lis"
        ),
        key=lambda path: path.name.lower(),
    )
    if not lis_files:
        parser.error(f"no .lis files found in {args.input_dir}")

    output_dir = args.output_dir or args.input_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    total_events = 0
    total_skipped = 0
    for lis_path in lis_files:
        events, skipped_events = read_events(lis_path)
        events.sort(key=lambda event: event[0])
        output_path = output_dir / f"{lis_path.stem}.csv"

        with output_path.open("w", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(
                [
                    "index",
                    "event_time",
                    "magnitude",
                    "latitude",
                    "longitude",
                    "depth_km",
                ]
            )

            for index, (
                event_time,
                magnitude,
                latitude,
                longitude,
                depth_km,
            ) in enumerate(events, start=1):
                writer.writerow(
                    [
                        index,
                        event_time.isoformat(),
                        magnitude,
                        latitude,
                        longitude,
                        depth_km,
                    ]
                )

        total_events += len(events)
        total_skipped += skipped_events
        print(
            f"Wrote {len(events)} events from {lis_path} to {output_path}; "
            f"skipped {skipped_events} malformed event(s)"
        )

    print(
        f"Wrote {total_events} events from {len(lis_files)} separate CSV file(s); "
        f"skipped {total_skipped} malformed event(s)"
    )


if __name__ == "__main__":
    main()
