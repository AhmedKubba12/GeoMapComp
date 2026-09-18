"""GeoMapComp: scalable comparison of region-based geo-maps on Apache Spark.

This package accompanies the paper:

    Ali Alsalama, Ahmed Kubba, Ahmed Ba Matraf and Osman Abul,
    "Scalable Approximate Computing for Efficient Search in Satellite
    Remote Sensing Products Using Apache Spark", 2025 International
    Conference on Intelligent Digitization of Systems and Services (IDSS).

It converts raster remote-sensing products into compact, geohash-indexed
vector representations and searches a collection of candidate raster
samples for the one most similar to a reference map, using statistical
distance metrics (RMSE, MAPE, Jensen-Shannon divergence and
Kullback-Leibler divergence). The search is distributed across Spark
workers.
"""

from .geohash_utils import encode_geohash
from .raster import dataframe_generator, geohash_mismatch_fixer, extract_geohash_key
from .metrics import (
    rmse_calculator,
    mape_calculator,
    jensen_shannon_divergence_calculator,
    kullback_leibler_divergence_calculator,
    METRICS,
)
from .spark_search import process_sample_partition, run_search

__all__ = [
    "encode_geohash",
    "dataframe_generator",
    "geohash_mismatch_fixer",
    "extract_geohash_key",
    "rmse_calculator",
    "mape_calculator",
    "jensen_shannon_divergence_calculator",
    "kullback_leibler_divergence_calculator",
    "METRICS",
    "process_sample_partition",
    "run_search",
]

__version__ = "1.0.0"
