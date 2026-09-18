# Data

This directory holds the raster inputs. The actual `.tiff` files are **not**
committed to the repository (they are git-ignored because they are large); add
them here yourself, or point the code at another location with the
`--reference-path` / `--samples-path` arguments.

Expected layout:

```
data/
├── AQ_NYC_Reference.tiff     # multi-band reference product
└── samples/                  # directory of candidate sample rasters
    ├── AQ_NYC_sample_1.tiff
    ├── AQ_NYC_sample_2.tiff
    └── ...
```

## Band convention

Each GeoTIFF is expected to store:

| Band | Contents                            |
|------|-------------------------------------|
| 1    | value (e.g. PM2.5)                  |
| 2    | latitude                            |
| 3    | longitude                           |
| 4    | encoding-key layer (reference only) |

Pixels whose bands are all zero are treated as no-data and dropped during
vectorization.
