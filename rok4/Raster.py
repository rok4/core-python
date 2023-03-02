"""Provide functions to read information on raster data from file path or object path

The module contains the following class :

    - 'Raster' - Structure describing raster data.

"""

import re
import tempfile

from osgeo import ogr, gdal

from rok4.Storage import get_data_str, exists, get_infos_from_path, copy, StorageType

# Enable GDAL/OGR exceptions
ogr.UseExceptions()


class Raster():
    """A structure describing raster data

    Attributes :
        path (str): path to the file/object (ex: file:///path/to/image.tif or s3://bucket/path/to/image.tif)
        bbox (Tuple[float, float, float, float]): bounding rectange in the data projection
        samples (int): number of color channels
        mask (str): path to the associated mask file or object, if any, or None (same path as the image, but with a ".msk" extension and TIFF format. ex: file:///path/to/image.msk or s3://bucket/path/to/image.msk)
    """

    def __init__(self, path: str) -> None:
        """Basic constructor method

        Args:
            path (str): path to the file/object

        Raises:
            RuntimeError: raised by OGR/GDAL if anything goes wrong
            MissingEnvironmentError: Missing object storage informations
            StorageError: Storage read issue
        """

        if not exists(path):
            raise Exception(f"No file or object found at path '{path}'.")

        image_info = get_infos_from_path(path)

        tmp_image_file = None
        work_image_path = None
        if image_info[0] == StorageType.FILE:
            work_image_path = image_info[1]
        else:
            tmp_image_file = tempfile.NamedTemporaryFile(mode='r', delete=False)
            tmp_image_file.close()
            work_image_path = tmp_image_file.name
            copy(path, f"file://{work_image_path}")

        image_datasource = gdal.Open(work_image_path)
        self.path = path

        path_pattern = re.compile('(/[^/]+?)[.][a-zA-Z0-9_-]+$')
        mask_path = path_pattern.sub('\\1.msk', path)

        tmp_mask_file = None
        work_mask_path = None
        if exists(mask_path):
            if image_info[0] == StorageType.FILE:
                work_mask_path = path_pattern.sub('\\1.msk', image_info[1])
            else:
                tmp_mask_file = tempfile.NamedTemporaryFile(mode='r', delete=False)
                tmp_mask_file.close()
                work_mask_path = tmp_mask_file.name

                tmp_mask_file = None
                copy(mask_path, f"file://{work_mask_path}") 
            
            mask_driver = gdal.IdentifyDriver(work_mask_path).ShortName
            if 'GTiff' != mask_driver:
                raise Exception(f"Mask file '{mask_path}' is not a TIFF image. (GDAL driver : '{mask_driver}'")

            self.mask = mask_path
        else:
            self.mask = None

        self.bbox = _compute_bbox(image_datasource)
        self.samples = image_datasource.RasterCount

        tmp_image_file = None


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


