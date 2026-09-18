"""Distributed search for the best-matching raster sample on Apache Spark.

The reference DataFrame and the geohash precision are broadcast to every
worker. Sample raster paths are partitioned across the workers; each worker
vectorizes its samples, aligns them with the reference map and keeps the one
minimizing the chosen metric. The driver then reduces the per-worker winners
to a single overall best sample.
"""

import logging
import os
import time

from osgeo import gdal

from .geohash_utils import DEFAULT_PRECISION
from .metrics import METRICS
from .raster import dataframe_generator, extract_geohash_key, geohash_mismatch_fixer

logger = logging.getLogger(__name__)


def process_sample_partition(
    sample_paths_iter, reference_df_broadcast, precision_broadcast, metric="RMSE"
):
    """Find the best sample within a single Spark partition.

    Args:
        sample_paths_iter: Iterator over sample raster file paths.
        reference_df_broadcast: Broadcast of the reference DataFrame.
        precision_broadcast: Broadcast of the geohash precision.
        metric: Metric name (see :data:`geomapcomp.metrics.METRICS`).

    Returns:
        A ``(best_sample_name, best_metric_value)`` tuple. Lower is better,
        so an empty partition returns ``(None, inf)``.
    """
    reference_df = reference_df_broadcast.value
    precision = precision_broadcast.value

    metric_fn = METRICS.get(metric)
    if metric_fn is None:
        logger.warning("Unknown metric '%s'; defaulting to RMSE", metric)
        metric_fn = METRICS["RMSE"]

    best_sample = None
    best_value = float("inf")  # Lower is better for every supported metric.

    for sample_path in sample_paths_iter:
        sample_name = os.path.basename(sample_path)
        try:
            sample_image = gdal.Open(sample_path)
            if sample_image is None:
                logger.warning("Failed to open sample image: %s", sample_path)
                continue

            sample_df = dataframe_generator(sample_image, precision)
            sample_df, ref_df_copy = geohash_mismatch_fixer(
                sample_df, reference_df.copy()
            )

            metric_value = metric_fn(sample_df, ref_df_copy)

            if metric_value < best_value:
                best_value = metric_value
                best_sample = sample_name

            sample_image = None  # Release the GDAL handle.
        except Exception as exc:  # noqa: BLE001 - keep the worker alive
            logger.error("Error processing sample %s: %s", sample_path, exc)

    return (best_sample, best_value) if best_sample else (None, float("inf"))


def run_search(
    spark,
    samples_path,
    reference_path,
    metric="RMSE",
    num_workers=3,
    precision=DEFAULT_PRECISION,
):
    """Run the full distributed best-sample search.

    Args:
        spark: An active :class:`pyspark.sql.SparkSession`.
        samples_path: Directory containing candidate sample rasters.
        reference_path: Path to the reference raster product.
        metric: Metric name to minimize.
        num_workers: Number of partitions / logical workers.
        precision: Geohash precision.

    Returns:
        A dict with ``best_sample``, ``metric``, ``metric_value``,
        ``per_worker`` and ``execution_time`` keys.
    """
    start_time = time.time()
    sc = spark.sparkContext

    logger.info("Loading reference image from %s", reference_path)
    reference_image = gdal.Open(reference_path)
    if reference_image is None:
        raise ValueError(f"Failed to open reference image: {reference_path}")

    # Derived for parity with the original pipeline (band-4 encoding key).
    try:
        extract_geohash_key(reference_image)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not extract encoding key from band 4: %s", exc)

    logger.info("Vectorizing reference image")
    reference_df = dataframe_generator(reference_image, precision)

    reference_df_broadcast = sc.broadcast(reference_df)
    precision_broadcast = sc.broadcast(precision)

    logger.info("Listing sample rasters in %s", samples_path)
    sample_paths = [
        os.path.join(samples_path, f) for f in sorted(os.listdir(samples_path))
    ]
    if not sample_paths:
        raise ValueError(f"No sample rasters found in: {samples_path}")

    sample_paths_rdd = sc.parallelize(sample_paths, num_workers)

    logger.info("Searching %d samples across %d workers with metric %s",
                len(sample_paths), num_workers, metric)
    per_worker = sample_paths_rdd.mapPartitions(
        lambda paths: [
            process_sample_partition(
                paths, reference_df_broadcast, precision_broadcast, metric
            )
        ]
    ).collect()

    overall_best = min(per_worker, key=lambda x: x[1])

    reference_df_broadcast.unpersist()
    precision_broadcast.unpersist()

    execution_time = time.time() - start_time
    logger.info(
        "Best sample: %s (%s = %s) in %.2fs",
        overall_best[0], metric, overall_best[1], execution_time,
    )

    return {
        "best_sample": overall_best[0],
        "metric": metric,
        "metric_value": overall_best[1],
        "per_worker": per_worker,
        "execution_time": execution_time,
    }
