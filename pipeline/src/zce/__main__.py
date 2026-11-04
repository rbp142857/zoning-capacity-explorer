"""Command-line entry point.

    uv run python -m zce download pasadena
    uv run python -m zce clean pasadena
    uv run python -m zce capacity pasadena
    uv run python -m zce export pasadena
    uv run python -m zce golden pasadena
    uv run python -m zce validate pasadena
    uv run python -m zce all pasadena
    uv run python -m zce accuracy                     (all cities)
    uv run python -m zce release                      (all cities)
    uv run python -m zce study studies/some_file.yaml

The Makefile at the repo root wraps these.
"""

import argparse

from zce.config import load_city


def main() -> None:
    parser = argparse.ArgumentParser(prog="zce", description="Zoning Capacity Explorer pipeline")
    parser.add_argument("step", choices=["download", "clean", "capacity", "export", "golden", "validate", "all", "waves", "accuracy", "release", "study"])
    parser.add_argument("city", nargs="?", default="pasadena", help="city id (a folder name under cities/), or for `study`, a scenario file")
    parser.add_argument("--only", nargs="*", help="download only these sources")
    args = parser.parse_args()

    if args.step == "waves":  # county-wide planning report, not a per-city step
        from zce.waves import write_ranking

        write_ranking()
        return
    if args.step == "accuracy":
        from zce.accuracy import write_accuracy

        write_accuracy()
        return
    if args.step == "release":
        from zce.release import write_release

        write_release()
        return
    if args.step == "study":
        from zce.study import write_study

        write_study(args.city)
        return

    city = load_city(args.city)

    # Imports are inside the branches so `download` does not need to load
    # GeoPandas, which is slow to import.
    if args.step in ("download", "all"):
        from zce.download import download_city

        download_city(city, only=args.only)
    if args.step in ("clean", "all"):
        from zce.clean import clean_city

        clean_city(city)
    if args.step in ("capacity", "all"):
        from zce.capacity_step import run_capacity

        run_capacity(city)
    if args.step in ("export", "all"):
        from zce.export_web import export_city

        export_city(city)
    if args.step in ("golden", "all"):
        from zce.golden import write_golden

        write_golden(city.id)
    if args.step in ("validate", "all"):
        from zce.validate import validate_city

        validate_city(city)


if __name__ == "__main__":
    main()
