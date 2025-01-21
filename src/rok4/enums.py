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
    """Storage type and path's protocol"""

    CEPH = "ceph://"
    FILE = "file://"
    HTTP = "http://"
    HTTPS = "https://"
    S3 = "s3://"


class ColorFormat(Enum):
    """A color format enumeration.
    Except from "BIT", the member's name matches
      a common variable format name. The member's value is
      the allocated bit size associated to this format.
    """

    BIT = 1
    UINT8 = 8
    FLOAT32 = 32


class PyramidCompression(Enum):
    """Pyramid's data compression
    The member's name matches the compression in the pyramid's format.
    """

    NONE = "RAW"
    JPG = "JPG"
    JPG90 = "JPG90"
    PNG = "PNG"
    LZW = "LZW"
    ZIP = "ZIP"
    PKB = "PKB"
    PBF = "PBF"


class PyramidSampleFormat(Enum):
    """Pyramid's data compression
    The member's name matches the sample format in the pyramid's format.
    """

    NONE = "MVT"
    UINT8 = "UINT8"
    UINT16 = "UINT16"
    FLOAT32 = "FLOAT32"


class PyramidInterpolation(Enum):
    """Pyramid's data compression
    The member's name matches the interpolation in the pyramid's descriptor.
    """

    NEAREST_NEIGHBOUR = "nn"
    LINEAR = "linear"
    BICUBIC = "bicubic"
    LANCZOS = "lanczos"
