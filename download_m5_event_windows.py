from __future__ import annotations

import argparse
from pathlib import Path

from obspy import UTCDateTime
from obspy.clients.fdsn import Client


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Download earthquake catalog."
    )
    parser.add_argument(
        "--event-client",
        default="USGS",
        help="FDSN client for the earthquake catalog, e.g. USGS or IRIS",
    )
    parser.add_argument("--start-time", required=True, help="Catalog start time, e.g. 2010-01-01")
    parser.add_argument("--end-time", required=True, help="Catalog end time, e.g. 2011-01-01")
    parser.add_argument("--min-magnitude", type=float, default=3.0, help="Minimum earthquake magnitude")
    parser.add_argument("--min-lat", type=float, default=None, help="Optional minimum latitude for catalog/station search")
    parser.add_argument("--max-lat", type=float, default=None, help="Optional maximum latitude for catalog/station search")
    parser.add_argument("--min-lon", type=float, default=None, help="Optional minimum longitude for catalog/station search")
    parser.add_argument("--max-lon", type=float, default=None, help="Optional maximum longitude for catalog/station search")
    parser.add_argument(
        "--catalog-output",
        default="output.csv",
        help="Optional CSV summary of the filtered catalog",
    )
    return parser


def event_origin_time(event) -> UTCDateTime:
    origin = event.preferred_origin() or (event.origins[0] if event.origins else None)
    if origin is None:
        raise ValueError("Event has no origin time")
    return origin.time


def event_magnitude(event) -> float:
    magnitude = event.preferred_magnitude() or (event.magnitudes[0] if event.magnitudes else None)
    if magnitude is None or magnitude.mag is None:
        return float("nan")
    return float(magnitude.mag)


def safe_event_name(event_time: UTCDateTime, magnitude: float, index: int) -> str:
    return f"event_{index:04d}_{event_time.strftime('%Y%m%dT%H%M%S')}_M{magnitude:.1f}".replace("/", "_")


def main() -> None:
    args = build_parser().parse_args()
    event_client = Client(args.event_client)

    start_time = UTCDateTime(args.start_time)
    end_time = UTCDateTime(args.end_time)

    event_kwargs = {
        "starttime": start_time,
        "endtime": end_time,
        "minmagnitude": args.min_magnitude,
    }
    if args.min_lat is not None:
        event_kwargs["minlatitude"] = args.min_lat
    if args.max_lat is not None:
        event_kwargs["maxlatitude"] = args.max_lat
    if args.min_lon is not None:
        event_kwargs["minlongitude"] = args.min_lon
    if args.max_lon is not None:
        event_kwargs["maxlongitude"] = args.max_lon

    catalog = event_client.get_events(**event_kwargs)
    filtered_events = []
    for event in catalog:
        magnitude = event_magnitude(event)
        if magnitude >= args.min_magnitude:
            filtered_events.append((event, magnitude, event_origin_time(event)))

    if not filtered_events:
        print("No events found matching the criteria.")
        return

    with open(args.catalog_output, "w", encoding="utf-8") as handle:
        handle.write("index,event_time,magnitude,latitude,longitude,depth_km\n")
        for index, (event, magnitude, origin_time) in enumerate(filtered_events, start=1):
            origin = event.preferred_origin() or event.origins[0]
            latitude = origin.latitude if origin and origin.latitude is not None else ""
            longitude = origin.longitude if origin and origin.longitude is not None else ""
            depth_km = (origin.depth / 1000.0) if origin and origin.depth is not None else ""
            handle.write(
                f"{index},{origin_time.isoformat()},{magnitude},{latitude},{longitude},{depth_km}\n"
            )

    print(f"Catalog summary written to: {args.catalog_output}")


if __name__ == "__main__":
    main()
