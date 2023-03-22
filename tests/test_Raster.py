"""Describes unit tests for the rok4.Raster module."""

from rok4.Raster import ColorFormat, Raster, _compute_bbox, _compute_format
from rok4.Storage import StorageType

from osgeo import gdal
import random

import pytest
from unittest.mock import *
from unittest import mock, TestCase, skip

class TestComputeBbox(TestCase):
    """Test class for the rok4.Raster._compute_bbox function."""

    def test_nominal(self):
        mocked_datasource = MagicMock(gdal.Dataset)
        random.seed()

        image_size = (
            random.randint(1, 1000),
            random.randint(1, 1000)
        )
        mocked_datasource.RasterXSize = image_size[0]
        mocked_datasource.RasterYSize = image_size[1]

        transform_tuple = (
            random.uniform(-10000000.0, 10000000.0),
            random.uniform(-10000, 10000),
            random.uniform(-10000, 10000),
            random.uniform(-10000000.0, 10000000.0),
            random.uniform(-10000, 10000),
            random.uniform(-10000, 10000)
        )
        mocked_datasource.GetGeoTransform = Mock(return_value = transform_tuple)

        x_range = (
            transform_tuple[0],
            transform_tuple[0] + image_size[0] * transform_tuple[1] + image_size[1] * transform_tuple[2]
        )
        y_range = (
            transform_tuple[3],
            transform_tuple[3] + image_size[0] * transform_tuple[4] + image_size[1] * transform_tuple[5]
        )

        expected = (
            min(x_range),
            min(y_range),
            max(x_range),
            max(y_range)
        )
        result = _compute_bbox(mocked_datasource)
        assert expected == result


class TestComputeFormat(TestCase):
    """Test class for the rok4.Raster._compute_format function."""

    def setUp(self) -> None:
        self.bit_gdalinfo = """Driver: GTiff/GeoTIFF
Size is 10000, 10000
Image Structure Metadata:
  COMPRESSION=PACKBITS
  INTERLEAVE=BAND
  MINISWHITE=YES
"""
        self.common_gdalinfo = """Driver: GTiff/GeoTIFF
Size is 10000, 10000
Metadata:
  AREA_OR_POINT=Area
Image Structure Metadata:
  INTERLEAVE=BAND
"""
        return super().setUp()

    @mock.patch('rok4.Raster.gdal.Info')
    @mock.patch('rok4.Raster.gdal.GetColorInterpretationName', return_value="Palette")
    @mock.patch('rok4.Raster.gdal.GetDataTypeSize', return_value=8)
    @mock.patch('rok4.Raster.gdal.GetDataTypeName', return_value="Byte")
    def test_bit(self, mocked_GetDataTypeName, mocked_GetDataTypeSize, mocked_GetColorInterpretationName, mocked_Info):
        mocked_datasource = MagicMock(gdal.Dataset)

        mocked_datasource.RasterCount = 1
        mocked_Info.return_value = self.bit_gdalinfo

        result = _compute_format(mocked_datasource)
        assert result == ColorFormat.BIT
        mocked_GetDataTypeName.assert_called()
        mocked_GetDataTypeSize.assert_called()
        mocked_GetColorInterpretationName.assert_called()
        mocked_Info.assert_called()

    @mock.patch('rok4.Raster.gdal.Info')
    @mock.patch('rok4.Raster.gdal.GetColorInterpretationName')
    @mock.patch('rok4.Raster.gdal.GetDataTypeSize', return_value=8)
    @mock.patch('rok4.Raster.gdal.GetDataTypeName', return_value="Byte")
    def test_uint8(self, mocked_GetDataTypeName, mocked_GetDataTypeSize, mocked_GetColorInterpretationName, mocked_Info):
        mocked_datasource = MagicMock(gdal.Dataset)
        
        band_number = random.randint(1, 4)
        mocked_datasource.RasterCount = band_number
        band_name = None
        if band_number == 1 or band_number == 2:
            band_name = "Gray"
        elif band_number == 3 or band_number == 4:
            band_name = "Red"
        mocked_GetColorInterpretationName.return_value = band_name
        mocked_Info.return_value = self.common_gdalinfo

        result = _compute_format(mocked_datasource)

        assert result == ColorFormat.UINT8
        mocked_GetDataTypeName.assert_called()
        mocked_GetDataTypeSize.assert_called()
        mocked_GetColorInterpretationName.assert_not_called()
        mocked_Info.assert_called()

    @mock.patch('rok4.Raster.gdal.Info')
    @mock.patch('rok4.Raster.gdal.GetColorInterpretationName')
    @mock.patch('rok4.Raster.gdal.GetDataTypeSize', return_value=32)
    @mock.patch('rok4.Raster.gdal.GetDataTypeName', return_value="Float32")
    def test_float32(self, mocked_GetDataTypeName, mocked_GetDataTypeSize, mocked_GetColorInterpretationName, mocked_Info):
        mocked_datasource = MagicMock(gdal.Dataset)
        
        band_number = random.randint(1, 4)
        mocked_datasource.RasterCount = band_number
        band_name = None
        if band_number == 1 or band_number == 2:
            band_name = "Gray"
        elif band_number == 3 or band_number == 4:
            band_name = "Red"
        mocked_GetColorInterpretationName.return_value = band_name
        mocked_Info.return_value = self.common_gdalinfo

        result = _compute_format(mocked_datasource)

        assert result == ColorFormat.FLOAT32
        mocked_GetDataTypeName.assert_called()
        mocked_GetDataTypeSize.assert_called()
        mocked_GetColorInterpretationName.assert_not_called()
        mocked_Info.assert_called()

    @mock.patch('rok4.Raster.gdal.Info')
    @mock.patch('rok4.Raster.gdal.GetColorInterpretationName')
    @mock.patch('rok4.Raster.gdal.GetDataTypeSize', return_value=16)
    @mock.patch('rok4.Raster.gdal.GetDataTypeName', return_value="UInt16")
    def test_unsupported(self, mocked_GetDataTypeName, mocked_GetDataTypeSize, mocked_GetColorInterpretationName, mocked_Info):
        mocked_datasource = MagicMock(gdal.Dataset)

        band_number = random.randint(1, 4)
        mocked_datasource.RasterCount = band_number
        band_name = None
        if band_number == 1 or band_number == 2:
            band_name = "Gray"
        elif band_number == 3 or band_number == 4:
            band_name = "Red"
        mocked_GetColorInterpretationName.return_value = band_name
        mocked_Info.return_value = self.common_gdalinfo

        with pytest.raises(Exception):
            _compute_format(mocked_datasource)
        
        mocked_GetDataTypeName.assert_called()
        mocked_GetDataTypeSize.assert_called()
        mocked_GetColorInterpretationName.assert_not_called()
        mocked_Info.assert_called()

    @mock.patch('rok4.Raster.gdal.Info')
    @mock.patch('rok4.Raster.gdal.GetColorInterpretationName')
    @mock.patch('rok4.Raster.gdal.GetDataTypeSize', return_value=16)
    @mock.patch('rok4.Raster.gdal.GetDataTypeName', return_value="UInt16")
    def test_no_band(self, mocked_GetDataTypeName, mocked_GetDataTypeSize, mocked_GetColorInterpretationName, mocked_Info):
        mocked_datasource = MagicMock(gdal.Dataset)

        mocked_datasource.RasterCount = 0

        with pytest.raises(Exception):
            _compute_format(mocked_datasource)

        mocked_GetDataTypeName.assert_not_called()
        mocked_GetDataTypeSize.assert_not_called()
        mocked_GetColorInterpretationName.assert_not_called()
        mocked_Info.assert_not_called()


class TestFromFile(TestCase):
    """Test class for the rok4.Raster.Raster.from_file(path) class constructor."""

    def setUp(self):
        self.source_image_path = "file:///home/user/image.tif"
        self.source_mask_path = "file:///home/user/image.msk"
        self.osgeo_image_path = "file:///home/user/image.tif"
        self.osgeo_mask_path = "file:///home/user/image.msk"
        self.bbox = (-5.4, 41.3, 9.8, 51.3)
        self.image_size = (1920, 1080)
        return super().setUp()

    def test_empty(self):
        """Test case : Constructor called without the expected path argument."""

        with pytest.raises(TypeError):
            Raster.from_file()

    @mock.patch('rok4.Raster.exists', return_value=False)
    def test_image_not_found(self, mocked_exists):
        """Test case : Constructor called on a path matching no file or object."""

        with pytest.raises(Exception):
            Raster.from_file(self.source_image_path)

        mocked_exists.assert_called_once_with(self.source_image_path)

    @mock.patch('rok4.Raster.get_osgeo_path')
    @mock.patch('rok4.Raster._compute_format', return_value=ColorFormat.UINT8)
    @mock.patch('rok4.Raster.gdal.Open')
    @mock.patch('rok4.Raster._compute_bbox')
    @mock.patch('rok4.Raster.exists', side_effect=[True, False])
    def test_image(self, mocked_exists, mocked_compute_bbox, mocked_gdal_open, mocked_compute_format, mocked_get_osgeo_path):
        """Test case : Constructor called nominally on an image without mask."""

        mocked_compute_bbox.return_value = self.bbox
        mocked_gdal_open.return_value = type('', (object,), {'RasterCount': 3, 'RasterXSize': self.image_size[0], 'RasterYSize': self.image_size[1]})
        mocked_get_osgeo_path.return_value = self.osgeo_image_path

        raster_object = Raster.from_file( self.source_image_path )

        mocked_exists.assert_has_calls([ call(self.source_image_path), call(self.source_mask_path) ])
        mocked_get_osgeo_path.assert_called_once_with(self.source_image_path)
        mocked_gdal_open.assert_called_once_with( self.osgeo_image_path )
        assert raster_object.path == self.source_image_path
        assert raster_object.mask is None

        mocked_compute_bbox.assert_called_once()
        assert raster_object.bbox == self.bbox
        assert raster_object.bands == 3
        mocked_compute_format.assert_called_once()
        assert raster_object.format == ColorFormat.UINT8
        assert raster_object.dimensions == self.image_size

    @mock.patch('rok4.Raster.get_osgeo_path')
    @mock.patch('rok4.Raster._compute_format', return_value=ColorFormat.UINT8)
    @mock.patch('rok4.Raster.gdal.IdentifyDriver')
    @mock.patch('rok4.Raster.gdal.Open')
    @mock.patch('rok4.Raster._compute_bbox')
    @mock.patch('rok4.Raster.exists', side_effect=[True, True])
    def test_image_and_mask(self, mocked_exists, mocked_compute_bbox, mocked_gdal_open, mocked_identifydriver, mocked_compute_format, mocked_get_osgeo_path):
        """Test case : Constructor called nominally on an image with mask."""

        mocked_compute_bbox.return_value = self.bbox
        mocked_gdal_open.return_value = type('', (object,), {'RasterCount': 3, 'RasterXSize': self.image_size[0], 'RasterYSize': self.image_size[1]})
        mocked_get_osgeo_path.side_effect=[self.osgeo_image_path, self.osgeo_mask_path]
        # This next line emulates the return of gdal.IdentifyDriver()
        mocked_identifydriver.return_value = type('', (object,), {'ShortName': 'GTiff'})

        raster_object = Raster.from_file(self.source_image_path)

        mocked_exists.assert_has_calls([ call(self.source_image_path), call(self.source_mask_path) ])
        mocked_get_osgeo_path.assert_has_calls([ call(self.source_image_path), call(self.source_mask_path) ])
        mocked_identifydriver.assert_called_once_with(self.osgeo_mask_path)
        mocked_gdal_open.assert_called_once_with(self.osgeo_image_path)
        assert raster_object.path == self.source_image_path
        assert raster_object.mask == self.source_mask_path

        mocked_compute_bbox.assert_called_once()
        assert raster_object.bbox == self.bbox
        assert raster_object.bands == 3
        mocked_compute_format.assert_called_once()
        assert raster_object.format == ColorFormat.UINT8
        assert raster_object.dimensions == self.image_size

    @mock.patch('rok4.Raster.get_osgeo_path')
    @mock.patch('rok4.Raster.gdal.Open', side_effect=RuntimeError)
    @mock.patch('rok4.Raster.exists', side_effect=[True, False])
    def test_unsupported_image_format(self, mocked_exists, mocked_gdal_open, mocked_get_osgeo_path):
        """Test case : Constructor called on an unsupported 'image' file or object."""

        mocked_get_osgeo_path.return_value = self.osgeo_image_path

        with pytest.raises(RuntimeError):
            Raster.from_file(self.source_image_path)

        mocked_exists.assert_called_once_with(self.source_image_path)
        mocked_get_osgeo_path.assert_called_once_with(self.source_image_path)
        mocked_gdal_open.assert_called_once_with(self.osgeo_image_path)

    @mock.patch('rok4.Raster.get_osgeo_path')
    @mock.patch('rok4.Raster.gdal.IdentifyDriver')
    @mock.patch('rok4.Raster.gdal.Open', side_effect=None)
    @mock.patch('rok4.Raster.exists', side_effect=[True, True])
    def test_unsupported_mask_format(self, mocked_exists, mocked_gdal_open, mocked_identifydriver, mocked_get_osgeo_path):
        """Test case : Constructor called on an unsupported mask file or object."""

        mocked_get_osgeo_path.side_effect=[self.osgeo_image_path, self.osgeo_mask_path]
        # This next line emulates the return of gdal.IdentifyDriver()
        mocked_identifydriver.return_value = type('', (object,), {'ShortName': 'JPG'})

        with pytest.raises(Exception):
            Raster.from_file(self.source_image_path)      

        mocked_exists.assert_has_calls([ call(self.source_image_path), call(self.source_mask_path) ])
        mocked_get_osgeo_path.assert_has_calls([ call(self.source_image_path), call(self.source_mask_path) ])
        mocked_identifydriver.assert_called_once_with(self.osgeo_mask_path)
        mocked_gdal_open.assert_called_once_with(self.osgeo_image_path)


class TestFromParameters(TestCase):
    """Test class for the rok4.Raster.Raster.from_parameters(**kwargs) class constructor."""

    def test_image(self):
        i_path = "file:///path/to/image.tif"
        i_bbox = (-5.4, 41.3, 9.8, 51.3)
        i_bands = 4
        i_format = ColorFormat.UINT8
        i_dimensions = (1920, 1080)

        result = Raster.from_parameters(path=i_path, bbox=i_bbox, bands=i_bands, format=i_format, dimensions=i_dimensions)

        assert result.path == i_path
        assert result.bbox == i_bbox
        assert result.bands == i_bands
        assert result.format == i_format
        assert result.dimensions == i_dimensions
        assert result.mask is None

    def test_image_and_mask(self):
        i_path = "file:///path/to/image.tif"
        i_mask = "file:///path/to/image.msk"
        i_bbox = (-5.4, 41.3, 9.8, 51.3)
        i_bands = 4
        i_format = ColorFormat.UINT8
        i_dimensions = (1920, 1080)

        result = Raster.from_parameters(path=i_path, bbox=i_bbox, bands=i_bands, format=i_format, dimensions=i_dimensions, mask=i_mask)

        assert result.path == i_path
        assert result.bbox == i_bbox
        assert result.bands == i_bands
        assert result.format == i_format
        assert result.dimensions == i_dimensions
        assert result.mask == i_mask
    
