import os
import argparse
from EQTransformer.utils.downloader import makeStationList, downloadMseeds


def parse_args():
    parser = argparse.ArgumentParser(
        description="Download station list and continuous MiniSEED data for EQTransformer."
    )
    parser.add_argument("--client", default="SCEDC", help="FDSN client name, e.g. SCEDC or IRIS")
    parser.add_argument("--min-lat", type=float, default=35.50, help="Minimum latitude")
    parser.add_argument("--max-lat", type=float, default=35.60, help="Maximum latitude")
    parser.add_argument("--min-lon", type=float, default=-117.80, help="Minimum longitude")
    parser.add_argument("--max-lon", type=float, default=-117.40, help="Maximum longitude")
    parser.add_argument("--start-time", default="2019-09-01 00:00:00.00", help="Start time in YYYY-MM-DD hh:mm:ss.ff format")
    parser.add_argument("--end-time", default="2019-09-03 00:00:00.00", help="End time in YYYY-MM-DD hh:mm:ss.ff format")
    parser.add_argument(
        "--channels",
        nargs="*",
        default=["HHZ", "HHN", "HHE"],
        help="Channel codes to request, e.g. HHZ HHN HHE",
    )
    parser.add_argument("--station-list", default="station_list.json", help="Path to save station_list.json")
    parser.add_argument("--output-dir", default="downloads_mseeds", help="Directory to save downloaded MiniSEED data")
    parser.add_argument("--chunk-size", type=int, default=1, help="Chunk size for downloadMseeds")
    parser.add_argument("--n-processor", type=int, default=2, help="Number of download workers")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    station_list_path = args.station_list
    if not os.path.dirname(station_list_path):
        station_list_path = os.path.join(".", station_list_path)

    os.makedirs(os.path.dirname(station_list_path) or ".", exist_ok=True)
    os.makedirs(args.output_dir, exist_ok=True)

    print("Making station list...")
    makeStationList(
        json_path=station_list_path,
        client_list=[args.client],
        min_lat=args.min_lat,
        max_lat=args.max_lat,
        min_lon=args.min_lon,
        max_lon=args.max_lon,
        start_time=args.start_time,
        end_time=args.end_time,
        channel_list=args.channels,
        filter_network=[],
        filter_station=[],
    )

    print("Downloading MiniSEED data...")
    downloadMseeds(
        client_list=[args.client],
        stations_json=args.station_list,
        output_dir=args.output_dir,
        start_time=args.start_time,
        end_time=args.end_time,
        min_lat=args.min_lat,
        max_lat=args.max_lat,
        min_lon=args.min_lon,
        max_lon=args.max_lon,
        chunk_size=args.chunk_size,
        channel_list=args.channels,
        n_processor=args.n_processor,
    )

    print("Done. Then run: python3 test-eqt.py")
