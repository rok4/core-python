"""Provide functions to read information on raster data from file path or object path

The module contains the following class :

    - 'Raster' - Structure describing raster data.

"""

import re
import tempfile
from enum import Enum

from osgeo import ogr, gdal

from rok4.Storage import exists, get_infos_from_path, copy, StorageType

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
            work_image_path = tmp_image_file.name # utiliser Storage.get_osgeo_path(real_path) quand disponible
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
                work_mask_path = tmp_mask_file.name # utiliser Storage.get_osgeo_path(real_path) quand disponible

                tmp_mask_file = None
                copy(mask_path, f"file://{work_mask_path}") 
            
            mask_driver = gdal.IdentifyDriver(work_mask_path).ShortName
            if 'GTiff' != mask_driver:
                raise Exception(f"Mask file '{mask_path}' is not a TIFF image. (GDAL driver : '{mask_driver}'")

            self.mask = mask_path
        else:
            self.mask = None

        self.bbox = _compute_bbox(image_datasource)
        self.bands = image_datasource.RasterCount
        self.format = _compute_format(image_datasource, path)

        # Pour l'obtenir sur un canal, deux méthodes (l'index du canal est compris entre 1 et RasterCount) :
        # - gdal.GetDataTypeName(image_datasource.GetRasterBand(index).DataType)
        # - gdal.GetDataTypeSize(image_datasource.GetRasterBand(index).DataType)
        # La première solution donne le nom, par exemple "Byte" pour un entier 8 bits.
        # La deuxième donne la taille en bits, "8" pour un entier 8 bits.
        # Se base sur l'enum GDALDataType
        # Les noms qui nous intéressent semblent être "Byte" pour "uint8", et "Float32" pour "float32".
        # Comment faire pour les images 1 bit ? Il me faudrait un exemple de fichier.
        # Exemple BDParcellaire fourni par Théo. tiffinfo détecte bien 1 canal 1 bit, mais gdal voit 1 canal 8 bits "Byte" avec palette 1 bit
        # gdal.GetColorInterpretationName(ds.GetRasterBand(1).GetRasterColorInterpretation()) = Palette
        # utiliser GetRasterColorInterpretation() et la fonction pour obtenir la compression ? (Celle-ci est "PACKBITS")

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


def _compute_format(dataset: gdal.Dataset, path=None) -> ColorFormat:
    """Image color format computing method

    Args:
        dataset (gdal.Dataset): Dataset object created from the raster image

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
