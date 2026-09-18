"""Raster -> geohash-indexed DataFrame conversion (vectorization).

A raster product is read band-by-band with GDAL and turned into a tidy
DataFrame of (latitude, longitude, value) rows, each tagged with a geohash
cell. Two such DataFrames can then be aligned on their geohash column and
compared with the statistical metrics in :mod:`geomapcomp.metrics`.

Band convention (as used in the paper's air-quality dataset):
    band 1 -> value (e.g. PM2.5)
    band 2 -> latitude
    band 3 -> longitude
    band 4 -> encoding key layer (reference image only)
"""

import numpy as np
import pandas as pd

from .geohash_utils import encode_geohash, DEFAULT_PRECISION

VALUE_COLUMN = "value"


def dataframe_generator(image, precision=DEFAULT_PRECISION):
    """Convert a GDAL raster image into a geohash-indexed DataFrame.

    Args:
        image: An open GDAL dataset (``osgeo.gdal.Dataset``).
        precision: Geohash precision to use for cell encoding.

    Returns:
        A DataFrame with columns ``latitude``, ``longitude``, ``value`` and
        ``Geohash``. Rows containing zeros (no-data) are dropped and
        duplicate geohash cells are removed.
    """
    value_band = image.GetRasterBand(1).ReadAsArray()
    latitude_band = image.GetRasterBand(2).ReadAsArray()
    longitude_band = image.GetRasterBand(3).ReadAsArray()

    # Flatten the raster grid into a column-oriented table in one vectorized
    # step (equivalent to the original nested Python loop, but far faster).
    df = pd.DataFrame(
        {
            "latitude": latitude_band.ravel(),
            "longitude": longitude_band.ravel(),
            VALUE_COLUMN: value_band.ravel(),
        }
    )

    # Treat exact zeros as no-data and drop them.
    df = df[(df != 0).all(axis=1)].reset_index(drop=True)

    # Tag every surviving pixel with its geohash cell.
    df["Geohash"] = df.apply(
        lambda r: encode_geohash(r["latitude"], r["longitude"], precision), axis=1
    )

    # Keep one representative pixel per cell.
    df = df.drop_duplicates(subset="Geohash").reset_index(drop=True)

    return df


def extract_geohash_key(reference_image):
    """Derive the encoding key from the reference image's 4th band.

    The reference product stores an encoding-key layer in band 4. The key is
    the smallest non-zero value in that layer. Kept for parity with the
    original pipeline; the geohash encoding itself does not depend on it.

    Args:
        reference_image: An open GDAL dataset for the reference product.

    Returns:
        The minimum non-zero value of band 4.
    """
    key_layer = reference_image.GetRasterBand(4).ReadAsArray()
    non_zero_values = key_layer[key_layer != 0]
    return float(np.min(np.unique(non_zero_values)))


def geohash_mismatch_fixer(df1, df2):
    """Align two DataFrames so they cover exactly the same geohash cells.

    Cells present in one DataFrame but missing from the other are added with
    zero values, so downstream metrics compare like-for-like cells.

    Args:
        df1: First geohash-indexed DataFrame.
        df2: Second geohash-indexed DataFrame.

    Returns:
        A tuple ``(df1, df2)`` covering the union of both cell sets.
    """
    geohashes_df1 = set(df1["Geohash"])
    geohashes_df2 = set(df2["Geohash"])

    missing_in_df1 = geohashes_df2 - geohashes_df1
    missing_in_df2 = geohashes_df1 - geohashes_df2

    missing_df1 = pd.DataFrame(
        {
            "Geohash": list(missing_in_df1),
            VALUE_COLUMN: [0] * len(missing_in_df1),
            "latitude": [0] * len(missing_in_df1),
            "longitude": [0] * len(missing_in_df1),
        }
    )
    df1 = pd.concat([df1, missing_df1], ignore_index=True)

    missing_df2 = pd.DataFrame(
        {
            "Geohash": list(missing_in_df2),
            VALUE_COLUMN: [0] * len(missing_in_df2),
            "latitude": [0] * len(missing_in_df2),
            "longitude": [0] * len(missing_in_df2),
        }
    )
    df2 = pd.concat([df2, missing_df2], ignore_index=True)

    return df1, df2
