import argparse
import json

import preprocessing.config as config
import preprocessing.preprocessing as pipeline
from preprocessing.config import WindowConfig

def main():
    parser = argparse.ArgumentParser(description="Module 2 telemetry preprocessing")
    parser.add_argument(
        "--fixed-window", type=int,
        default=config.WINDOW_CONFIG.fixed_window_seconds,
        help="Fixed window size in seconds.",
    )
    parser.add_argument(
        "--session-gap", type=int,
        default=config.WINDOW_CONFIG.session_gap_seconds,
        help="Maximum inactivity gap in a session, in seconds.",
    )
    args = parser.parse_args()

    if args.fixed_window <= 0 or args.session_gap <= 0:
        raise SystemExit("Window values must be greater than zero.")

    config.WINDOW_CONFIG = WindowConfig(
        fixed_window_seconds=args.fixed_window,
        session_gap_seconds=args.session_gap,
    )
    pipeline.WINDOW_CONFIG = config.WINDOW_CONFIG

    print(json.dumps(pipeline.run_all_sources(), indent=2))

if __name__ == "__main__":
    main()
