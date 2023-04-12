"""Provide functions to read information on raster data from file path or object path

The module contains the following class :

    - 'Raster' - Structure describing raster data.

"""

import re
from enum import Enum

from osgeo import ogr, gdal
from typing import Tuple

from rok4.Storage import exists, get_osgeo_path
from rok4.Utils import ColorFormat, compute_bbox,compute_format

# Enable GDAL/OGR exceptions
ogr.UseExceptions()


class Raster:
    """A structure describing raster data

    Attributes :
        path (str): path to the file/object (ex: file:///path/to/image.tif or s3://bucket/path/to/image.tif)
        bbox (Tuple[float, float, float, float]): bounding rectange in the data projection
        bands (int): number of color bands (or channels)
        format (ColorFormat): numeric variable format for color values. Bit depth, as bits per channel, can be derived from it.
        mask (str): path to the associated mask file or object, if any, or None (same path as the image, but with a ".msk" extension and TIFF format. ex: file:///path/to/image.msk or s3://bucket/path/to/image.msk)
        dimensions (Tuple[int, int]): image width and height expressed in pixels
    """

    def __init__(self) -> None:
        self.bands = None
        self.bbox = (None, None, None, None)
        self.dimensions = (None, None)
        self.format = None
        self.mask = None
        self.path = None

    @classmethod
    def from_file(cls, path: str) -> 'Raster':
        """Creates a Raster object from an image

        Args:
            path (str): path to the image file/object

        Examples:

            Loading informations from a file stored raster TIFF image

                from rok4.Raster import Raster

                try:
                    raster = Raster.from_file("file:///data/images/SC1000_TIFF_LAMB93_FXX/SC1000_0040_6150_L93.tif")

                except Exception as e:
                    print(f"Cannot load information from image : {e}")

        Raises:
            RuntimeError: raised by OGR/GDAL if anything goes wrong
            NotImplementedError: Storage type not handled

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

        self.bbox = compute_bbox(image_datasource)
        self.bands = image_datasource.RasterCount
        self.format = compute_format(image_datasource, path)
        self.dimensions = (image_datasource.RasterXSize, image_datasource.RasterYSize)

        return self

    @classmethod
    def from_parameters(cls, path: str, bands: int, bbox: Tuple[float, float, float, float], dimensions: Tuple[int, int], format: ColorFormat, mask: str = None) -> 'Raster':
        """Creates a Raster object from parameters

        Args:
            path (str): path to the file/object (ex: file:///path/to/image.tif or s3://bucket/path/to/image.tif)
            bands (int): number of color bands (or channels)
            bbox (Tuple[float, float, float, float]): bounding rectange in the data projection
            dimensions (Tuple[int, int]): image width and height expressed in pixels
            format (ColorFormat): numeric variable format for color values. Bit depth, as bits per channel, can be derived from it.
            mask (str, optionnal): path to the associated mask file or object, if any, or None (same path as the image, but with a ".msk" extension and TIFF format. ex: file:///path/to/image.msk or s3://bucket/path/to/image.msk)

        Examples:

            Loading informations from parameters, related to a TIFF main image coupled to a TIFF mask image

                from rok4.Raster import Raster

                try:
                    raster = Raster.from_parameters(path="file:///data/images/SC1000_TIFF_LAMB93_FXX/SC1000_0040_6150_L93.tif", mask="file:///data/images/SC1000_TIFF_LAMB93_FXX/SC1000_0040_6150_L93.msk", bands=3, format=ColorFormat.UINT8, dimensions=(2000, 2000), bbox=(40000.000, 5950000.000, 240000.000, 6150000.000))

                except Exception as e:
                    print(f"Cannot load information from parameters : {e}")

        Raises:
            KeyError: a mandatory argument is missing

        Returns:
            Raster: a Raster instance
        """

        self = cls()
            
        self.path = path
        self.bands = bands
        self.bbox = bbox
        self.dimensions = dimensions
        self.format = format
        self.mask = mask

        return self
