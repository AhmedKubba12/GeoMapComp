# GeoMapComp

**Scalable approximate computing for efficient search in satellite remote-sensing products, using Apache Spark.**

This repository contains the reference implementation for the paper:

> Ali Alsalama, Ahmed Kubba, Ahmed Ba Matraf, and Osman Abul.
> *Scalable Approximate Computing for Efficient Search in Satellite Remote Sensing Products Using Apache Spark.*
> 2025 International Conference on Intelligent Digitization of Systems and Services (IDSS).
> DOI: [10.1109/DSS67199.2025.11398180](https://doi.org/10.1109/DSS67199.2025.11398180)

## Overview

Remote-sensing products frequently produce region-based geo-maps (choropleth maps, heatmaps) that must be compared across time or across datasets. Comparing them means converting raster images into compact vector representations that preserve both spatial resolution and intensity, which is computationally intensive at scale.

GeoMapComp addresses this with a distributed pipeline on Apache Spark:

1. **Vectorization**: each raster is read band-by-band with GDAL and flattened into a tidy table of `(latitude, longitude, value)` rows.
2. **Geohash encoding**: coordinates are discretized into fixed-size geohash cells, giving spatial proxies that make two maps directly comparable cell-by-cell.
3. **Statistical comparison**: aligned maps are scored with a similarity metric: Root Mean Squared Error (RMSE), Mean Absolute Percentage Error (MAPE), Jensen–Shannon Divergence (JSD), or Kullback–Leibler Divergence (KLD).
4. **Distributed search**: candidate sample rasters are partitioned across Spark workers; each worker keeps its best-matching sample, and the driver reduces those to the single overall best match.

For every metric, **lower is better**, so the search minimizes.

## Repository structure

```
geomapcomp/
├── main.py                       # Command-line entry point
├── requirements.txt
├── CITATION.cff                  # How to cite this work
├── src/
│   └── geomapcomp/
│       ├── __init__.py
│       ├── geohash_utils.py      # Geohash encoding
│       ├── raster.py             # Raster -> geohash-indexed DataFrame
│       ├── metrics.py            # RMSE / MAPE / JSD / KLD
│       └── spark_search.py       # Distributed best-sample search
├── notebooks/
│   └── distributed_raster_search.ipynb   # Cleaned, path-configurable notebook
└── data/
    └── README.md                 # Where to place the reference & sample rasters
```

## Installation

```bash
git clone https://github.com/<your-username>/geomapcomp.git
cd geomapcomp

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

**GDAL note.** The `GDAL` Python bindings must match the GDAL system library. If `pip install GDAL` fails:

```bash
# Ubuntu / Debian
sudo apt-get install gdal-bin libgdal-dev
pip install GDAL==$(gdal-config --version)

# or with conda
conda install -c conda-forge gdal
```

## Data layout

The code expects a multi-band GeoTIFF reference product and a directory of candidate sample rasters. The band convention (from the paper's air-quality dataset) is:

| Band | Contents                         |
|------|----------------------------------|
| 1    | value (e.g. PM2.5)               |
| 2    | latitude                         |
| 3    | longitude                        |
| 4    | encoding-key layer (reference only) |

Place your data under `data/` (git-ignored) or point to it with arguments — see `data/README.md`.

## Usage

### Command line

```bash
python main.py \
    --samples-path ./data/samples \
    --reference-path ./data/AQ_NYC_Reference.tiff \
    --metric RMSE \
    --workers 3
```

Options:

| Flag | Default | Description |
|------|---------|-------------|
| `--samples-path` | `$GEOMAPCOMP_SAMPLES_PATH` | Directory of candidate sample rasters |
| `--reference-path` | `$GEOMAPCOMP_REFERENCE_PATH` | Reference raster product |
| `--metric` | `RMSE` | One of `RMSE`, `MAPE`, `Jensen_Shannon_Divergence`, `Kullback_Leibler_Divergence` |
| `--workers` | `3` | Spark partitions / logical workers |
| `--precision` | `7` | Geohash precision |
| `--executor-memory` | `2g` | `spark.executor.memory` |

Paths can also be supplied through the `GEOMAPCOMP_SAMPLES_PATH` and `GEOMAPCOMP_REFERENCE_PATH` environment variables, so nothing is hardcoded to Google Colab or Drive.

### As a library

```python
from pyspark.sql import SparkSession
from src.geomapcomp import run_search

spark = SparkSession.builder.master("local[3]").getOrCreate()
result = run_search(
    spark,
    samples_path="data/samples",
    reference_path="data/AQ_NYC_Reference.tiff",
    metric="RMSE",
    num_workers=3,
)
spark.stop()

print(result["best_sample"], result["metric_value"])
```

## Results reported in the paper

Running the search over the New York City air-quality samples with three workers produced, for each metric, the best-matching sample:

| Metric | Best sample | Value |
|--------|-------------|-------|
| RMSE | `AQ_NYC_sample_33.tiff` | 0.9393 |
| MAPE | `AQ_NYC_sample_44.tiff` | 9.164 |
| Jensen–Shannon Divergence | `AQ_NYC_sample_13.tiff` | 0.01474 |
| Kullback–Leibler Divergence | `AQ_NYC_sample_44.tiff` | 0.04428 |

(Exact values depend on the input rasters.)

## Citing

If you use this code, please cite the paper. See [`CITATION.cff`](CITATION.cff) or use the BibTeX entry below:

```bibtex
@inproceedings{alsalama2025geomapcomp,
  title     = {Scalable Approximate Computing for Efficient Search in Satellite Remote Sensing Products Using Apache Spark},
  author    = {Alsalama, Ali and Kubba, Ahmed and Ba Matraf, Ahmed and Abul, Osman},
  booktitle = {2025 International Conference on Intelligent Digitization of Systems and Services (IDSS)},
  year      = {2025},
  publisher = {IEEE},
  doi       = {10.1109/DSS67199.2025.11398180}
}
```

## Acknowledgements

Department of Computer Science, College of Computing and Informatics, University of Sharjah, United Arab Emirates.
