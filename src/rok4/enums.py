#! python3  # noqa: E265

# standard lib
from enum import Enum


class PyramidType(Enum):
    """Pyramid's data type"""

    RASTER = "RASTER"
    VECTOR = "VECTOR"


class StorageType(Enum):
    """Matrice de correspondance entre type de stockage et protocole."""

    CEPH = "ceph://"
    FILE = "file://"
    HTTP = "http://"
    HTTPS = "https://"
    S3 = "s3://"
