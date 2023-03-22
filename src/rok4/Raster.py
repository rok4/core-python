"""Provide functions to read information on raster data from file path or object path

The module contains the following class :

    - 'Raster' - Structure describing raster data.

"""

import re
import tempfile
from enum import Enum

from osgeo import ogr, gdal

from rok4.Storage import exists, get_infos_from_path, copy, StorageType, get_osgeo_path

# Enable GDAL/OGR exceptions
ogr.UseExceptions()

class ColorFormat(Enum):
    BIT = 1
    UINT8 = 8
    FLOAT32 = 32


class Raster():
    """A structure describing raster data

    Attributes :
        path (str): path to the file/object (ex: file:///path/to/image.tif or s3://bucket/path/to/image.tif)
        bbox (Tuple[float, float, float, float]): bounding rectange in the data projection
        bands (int): number of color bands (or channels)
        format (ColorFormat): numeric variable format for color values. Bit depth, as bits per channel, can be derived from it.
        mask (str): path to the associated mask file or object, if any, or None (same path as the image, but with a ".msk" extension and TIFF format. ex: file:///path/to/image.msk or s3://bucket/path/to/image.msk)
        dimensions (Tuple[int, int]): image width and height expressed in pixels
    """

    @classmethod
    def from_file(cls, path: str) -> 'Raster':
        """Creates a Raster object from an image

        Args:
            path (str): path to the image file/object

        Raises:
            RuntimeError: raised by OGR/GDAL if anything goes wrong
            MissingEnvironmentError: Missing object storage informations
            StorageError: Storage read issue

        Returns:
            Raster: a Raster instance
        """

        if not exists(path):
            raise Exception(f"No file or object found at path '{path}'.")

        self = cls()

        work_image_path = get_osgeo_path(path)

        image_datasource = gdal.Open(work_image_path)
        self.path = path

        path_pattern = re.compile('(/[^/]+?)[.][a-zA-Z0-9_-]+$')
        mask_path = path_pattern.sub('\\1.msk', path)

        if exists(mask_path):            
            work_mask_path = get_osgeo_path(mask_path)
            mask_driver = gdal.IdentifyDriver(work_mask_path).ShortName
            if 'GTiff' != mask_driver:
                raise Exception(f"Mask file '{mask_path}' is not a TIFF image. (GDAL driver : '{mask_driver}'")

            self.mask = mask_path
        else:
            self.mask = None

        self.bbox = _compute_bbox(image_datasource)
        self.bands = image_datasource.RasterCount
        self.format = _compute_format(image_datasource, path)
        self.dimensions = (image_datasource.RasterXSize, image_datasource.RasterYSize)

        return self

    @classmethod
    def from_parameters(cls, mask=None, **kwargs):
        """Creates a Raster object from key/value parameters

        Args:
            **path (str): path to the file/object (ex: file:///path/to/image.tif or s3://bucket/path/to/image.tif)
            **bbox (Tuple[float, float, float, float]): bounding rectange in the data projection
            **bands (int): number of color bands (or channels)
            **format (ColorFormat): numeric variable format for color values. Bit depth, as bits per channel, can be derived from it.
            **mask (str, optionnal): path to the associated mask file or object, if any, or None (same path as the image, but with a ".msk" extension and TIFF format. ex: file:///path/to/image.msk or s3://bucket/path/to/image.msk)
            **dimensions (Tuple[int, int]): image width and height expressed in pixels

        Raises:
            KeyError: a mandatory argument is missing

        Returns:
            Raster: a Raster instance
        """

        self = cls()
            
        self.path = kwargs["path"]
        self.mask = mask
        self.bbox = kwargs["bbox"]
        self.bands = kwargs["bands"]
        self.format = kwargs["format"]
        self.dimensions = kwargs["dimensions"]

        return self


def _compute_bbox(source_dataset: gdal.Dataset) -> tuple:
    """Image boundingbox computing method

    Args:
        source_dataset (gdal.Dataset): Dataset object created from the raster image

    Raises:
        AttributeError: source_dataset is not a gdal.Dataset instance.
        Exception: The dataset does not contain transform data.
    """

    transform_vector = source_dataset.GetGeoTransform()

    if transform_vector is None:
        raise Exception(f"No transform vector found in the dataset created from the following file : {source_dataset.GetFileList()[0]}")

    width = source_dataset.RasterXSize
    height = source_dataset.RasterYSize

    x_range = (
        transform_vector[0],
        transform_vector[0] + width * transform_vector[1] + height * transform_vector[2]
    )

    y_range = (
        transform_vector[3],
        transform_vector[3] + width * transform_vector[4] + height * transform_vector[5]
    )

    bbox = (
            min(x_range),
            min(y_range),
            max(x_range),
            max(y_range)
    )

    return bbox


def _compute_format(dataset: gdal.Dataset, path=None) -> ColorFormat:
    """Image color format computing method

    Args:
        dataset (gdal.Dataset): Dataset object created from the raster image
        path (str): path to the original file/object (optionnal)

    Raises:
        AttributeError: source_dataset is not a gdal.Dataset instance.
        Exception: Image has no color band or its color format is unsupported.
    """

    format = None

    if path is None:
        path = dataset.GetFileList()[0]

    if dataset.RasterCount < 1:
        raise Exception(f"Image {path} contains no color band.")
    
    band_1_datatype = dataset.GetRasterBand(1).DataType
    band_1_color_interpretation = dataset.GetRasterBand(1).GetRasterColorInterpretation()
    compression_regex_match = re.search(r'COMPRESSION\s*=\s*PACKBITS', gdal.Info(dataset))

    if gdal.GetDataTypeName(band_1_datatype) == "Byte" and gdal.GetDataTypeSize(band_1_datatype) == 8 and compression_regex_match and band_1_color_interpretation is not None and gdal.GetColorInterpretationName(band_1_color_interpretation) == "Palette":
        format = ColorFormat.BIT
    elif gdal.GetDataTypeName(band_1_datatype) == "Byte" and gdal.GetDataTypeSize(band_1_datatype) == 8:
        format = ColorFormat.UINT8
    elif gdal.GetDataTypeName(band_1_datatype) == "Float32" and gdal.GetDataTypeSize(band_1_datatype) == 32:
        format = ColorFormat.FLOAT32
    else:
        raise Exception(f"Unsupported color format for image {path} : '{gdal.GetDataTypeName(band_1_datatype)}' ({gdal.GetDataTypeSize(band_1_datatype)} bits)")

    return format
