#! python3  # noqa: E265

# standard lib
from enum import Enum


class PyramidType(Enum):
    """Pyramid's data type"""

    RASTER = "RASTER"
    VECTOR = "VECTOR"


class SlabType(Enum):
    """Slab's type"""

    DATA = "DATA"  # Slab of data, raster or vector
    MASK = "MASK"  # Slab of mask, only for raster pyramid, image with one band : 0 is nodata, other values are data


class StorageType(Enum):
    """Matrice de correspondance entre type de stockage et protocole."""

    CEPH = "ceph://"
    FILE = "file://"
    HTTP = "http://"
    HTTPS = "https://"
    S3 = "s3://"
