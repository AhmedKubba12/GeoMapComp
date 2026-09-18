"""Geohash encoding helpers.

Geohash encoding discretizes continuous geographic coordinates into
fixed-size rectangular cells, producing the spatial proxies that make two
raster maps comparable cell-by-cell.
"""

import pygeohash as pgh

# Geohash precision (number of characters). Precision 7 corresponds to
# cells of roughly 150 m x 150 m, matching the resolution used in the paper.
DEFAULT_PRECISION = 7


def encode_geohash(latitude, longitude, precision=DEFAULT_PRECISION):
    """Encode a (latitude, longitude) pair into a geohash string.

    Args:
        latitude: Latitude in decimal degrees.
        longitude: Longitude in decimal degrees.
        precision: Number of characters in the geohash (higher = finer).

    Returns:
        The geohash string for the coordinate.
    """
    return pgh.encode(latitude, longitude, precision)
