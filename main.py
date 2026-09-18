"""Command-line entry point for the GeoMapComp distributed search.

Example:
    python main.py \
        --samples-path ./data/samples \
        --reference-path ./data/AQ_NYC_Reference.tiff \
        --metric RMSE \
        --workers 3

Paths are supplied as arguments (or environment variables), so the code runs
anywhere Spark and GDAL are installed -- no Google Colab or Drive required.
"""

import argparse
import logging
import os

from pyspark.sql import SparkSession

from src.geomapcomp import run_search
from src.geomapcomp.geohash_utils import DEFAULT_PRECISION
from src.geomapcomp.metrics import METRICS


def parse_args():
    parser = argparse.ArgumentParser(
        description="Distributed best-matching raster search on Apache Spark."
    )
    parser.add_argument(
        "--samples-path",
        default=os.environ.get("GEOMAPCOMP_SAMPLES_PATH"),
        help="Directory of candidate sample rasters "
             "(or set GEOMAPCOMP_SAMPLES_PATH).",
    )
    parser.add_argument(
        "--reference-path",
        default=os.environ.get("GEOMAPCOMP_REFERENCE_PATH"),
        help="Path to the reference raster product "
             "(or set GEOMAPCOMP_REFERENCE_PATH).",
    )
    parser.add_argument(
        "--metric",
        default="RMSE",
        choices=list(METRICS.keys()),
        help="Similarity metric to minimize (default: RMSE).",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=3,
        help="Number of Spark partitions / logical workers (default: 3).",
    )
    parser.add_argument(
        "--precision",
        type=int,
        default=DEFAULT_PRECISION,
        help=f"Geohash precision (default: {DEFAULT_PRECISION}).",
    )
    parser.add_argument(
        "--executor-memory",
        default="2g",
        help="spark.executor.memory setting (default: 2g).",
    )
    args = parser.parse_args()

    if not args.samples_path or not args.reference_path:
        parser.error(
            "--samples-path and --reference-path are required "
            "(or set the GEOMAPCOMP_SAMPLES_PATH / GEOMAPCOMP_REFERENCE_PATH "
            "environment variables)."
        )
    return args


def build_spark(num_workers, executor_memory):
    return (
        SparkSession.builder
        .appName("GeoMapComp Distributed Raster Search")
        .master(f"local[{num_workers}]")
        .config("spark.executor.memory", executor_memory)
        .getOrCreate()
    )


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    args = parse_args()

    spark = build_spark(args.workers, args.executor_memory)
    try:
        result = run_search(
            spark,
            samples_path=args.samples_path,
            reference_path=args.reference_path,
            metric=args.metric,
            num_workers=args.workers,
            precision=args.precision,
        )
    finally:
        spark.stop()

    print("\nPer-worker best samples:")
    for name, value in result["per_worker"]:
        print(f"  {name}: {value}")
    print(f"\nOverall best sample: {result['best_sample']}")
    print(f"{result['metric']} value: {result['metric_value']}")
    print(f"Execution time: {result['execution_time']:.2f} seconds")


if __name__ == "__main__":
    main()
