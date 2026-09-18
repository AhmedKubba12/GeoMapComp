"""Statistical similarity metrics for comparing two geo-maps.

Each metric takes two geohash-indexed DataFrames (see
:mod:`geomapcomp.raster`), aligns them on their shared ``Geohash`` column,
and returns a single scalar. For every metric a lower value means the maps
are more similar, so the search always minimizes.
"""

import numpy as np
import pandas as pd
from scipy.stats import entropy

from .raster import VALUE_COLUMN


def _merge(df1, df2):
    """Inner-join two DataFrames on their geohash cells."""
    return pd.merge(df1, df2, on="Geohash", suffixes=("_1", "_2"))


def rmse_calculator(df1, df2):
    """Root Mean Square Error between the aligned value columns."""
    merged = _merge(df1, df2)
    squared_diff = (merged[f"{VALUE_COLUMN}_1"] - merged[f"{VALUE_COLUMN}_2"]) ** 2
    return float(np.sqrt(squared_diff.mean()))


def mape_calculator(df1, df2):
    """Mean Absolute Percentage Error (as a percentage)."""
    merged = _merge(df1, df2)
    abs_pct_diff = np.abs(
        merged[f"{VALUE_COLUMN}_1"] - merged[f"{VALUE_COLUMN}_2"]
    ) / merged[f"{VALUE_COLUMN}_2"]
    return float(abs_pct_diff.mean() * 100)


def jensen_shannon_divergence_calculator(df1, df2):
    """Jensen-Shannon divergence between the two value distributions."""
    merged = _merge(df1, df2)
    p = (merged[f"{VALUE_COLUMN}_1"] + merged[f"{VALUE_COLUMN}_2"]) / 2
    jsd = (
        entropy(merged[f"{VALUE_COLUMN}_1"], p)
        + entropy(merged[f"{VALUE_COLUMN}_2"], p)
    ) / 2
    return float(jsd)


def kullback_leibler_divergence_calculator(df1, df2):
    """Kullback-Leibler divergence of df1's values relative to df2's."""
    merged = _merge(df1, df2)
    return float(entropy(merged[f"{VALUE_COLUMN}_1"], merged[f"{VALUE_COLUMN}_2"]))


# Registry so callers can select a metric by name.
METRICS = {
    "RMSE": rmse_calculator,
    "MAPE": mape_calculator,
    "Jensen_Shannon_Divergence": jensen_shannon_divergence_calculator,
    "Kullback_Leibler_Divergence": kullback_leibler_divergence_calculator,
}
