#! python3  # noqa: E265

# standard lib
from enum import Enum


class StorageType(Enum):
    """Matrice de correspondance entre type de stockage et protocole."""

    CEPH = "ceph://"
    FILE = "file://"
    HTTP = "http://"
    HTTPS = "https://"
    S3 = "s3://"
