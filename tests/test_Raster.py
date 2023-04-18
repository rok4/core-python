"""Describes unit tests for the rok4.Raster module."""

from rok4.Raster import Raster, RasterSet
from rok4.Utils import ColorFormat

import math
import random

import pytest
from unittest import mock, TestCase
from unittest.mock import *


# rok4.Raster.Raster class tests

class TestRasterFromFile(TestCase):
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
    @mock.patch('rok4.Raster.compute_format', return_value=ColorFormat.UINT8)
    @mock.patch('rok4.Raster.gdal.Open')
    @mock.patch('rok4.Raster.compute_bbox')
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
        assert math.isclose(raster_object.bbox[0], self.bbox[0], rel_tol=1e-5)
        assert math.isclose(raster_object.bbox[1], self.bbox[1], rel_tol=1e-5)
        assert math.isclose(raster_object.bbox[2], self.bbox[2], rel_tol=1e-5)
        assert math.isclose(raster_object.bbox[3], self.bbox[3], rel_tol=1e-5)
        assert raster_object.bands == 3
        mocked_compute_format.assert_called_once()
        assert raster_object.format == ColorFormat.UINT8
        assert raster_object.dimensions == self.image_size

    @mock.patch('rok4.Raster.get_osgeo_path')
    @mock.patch('rok4.Raster.compute_format', return_value=ColorFormat.UINT8)
    @mock.patch('rok4.Raster.gdal.IdentifyDriver')
    @mock.patch('rok4.Raster.gdal.Open')
    @mock.patch('rok4.Raster.compute_bbox')
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
        assert math.isclose(raster_object.bbox[0], self.bbox[0], rel_tol=1e-5)
        assert math.isclose(raster_object.bbox[1], self.bbox[1], rel_tol=1e-5)
        assert math.isclose(raster_object.bbox[2], self.bbox[2], rel_tol=1e-5)
        assert math.isclose(raster_object.bbox[3], self.bbox[3], rel_tol=1e-5)
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


class TestRasterFromParameters(TestCase):
    """Test class for the rok4.Raster.Raster.from_parameters(**kwargs) class constructor."""

    def test_image(self):
        """Test case: parameters describing an image without mask"""

        i_path = "file:///path/to/image.tif"
        i_bbox = (-5.4, 41.3, 9.8, 51.3)
        i_bands = 4
        i_format = ColorFormat.UINT8
        i_dimensions = (1920, 1080)

        result = Raster.from_parameters(path=i_path, bbox=i_bbox, bands=i_bands, format=i_format, dimensions=i_dimensions)

        assert result.path == i_path
        assert math.isclose(result.bbox[0], i_bbox[0], rel_tol=1e-5)
        assert math.isclose(result.bbox[1], i_bbox[1], rel_tol=1e-5)
        assert math.isclose(result.bbox[2], i_bbox[2], rel_tol=1e-5)
        assert math.isclose(result.bbox[3], i_bbox[3], rel_tol=1e-5)
        assert result.bands == i_bands
        assert result.format == i_format
        assert result.dimensions == i_dimensions
        assert result.mask is None

    def test_image_and_mask(self):
        """Test case: parameters describing an image with mask"""

        i_path = "file:///path/to/image.tif"
        i_mask = "file:///path/to/image.msk"
        i_bbox = (-5.4, 41.3, 9.8, 51.3)
        i_bands = 4
        i_format = ColorFormat.UINT8
        i_dimensions = (1920, 1080)

        result = Raster.from_parameters(path=i_path, bbox=i_bbox, bands=i_bands, format=i_format, dimensions=i_dimensions, mask=i_mask)

        assert result.path == i_path
        assert math.isclose(result.bbox[0], i_bbox[0], rel_tol=1e-5)
        assert math.isclose(result.bbox[1], i_bbox[1], rel_tol=1e-5)
        assert math.isclose(result.bbox[2], i_bbox[2], rel_tol=1e-5)
        assert math.isclose(result.bbox[3], i_bbox[3], rel_tol=1e-5)
        assert result.bands == i_bands
        assert result.format == i_format
        assert result.dimensions == i_dimensions
        assert result.mask == i_mask
    

# rok4.Raster.RasterSet class tests

class TestRasterSetFromList(TestCase):
    """Test class for the rok4.Raster.RasterSet.from_list(path, srs) class constructor."""

    @mock.patch('rok4.Raster.get_osgeo_path')
    @mock.patch('rok4.Raster.Raster.from_file')
    def test_ok_at_least_3_files(self, mocked_from_file, mocked_get_osgeo_path):
        """Test case: list of 3 or more valid image files"""

        file_number = random.randint(3, 100)
        file_list = []
        for n in range(0, file_number, 1):
            file_list.append(f"s3://test_bucket/image_{n+1}.tif")
        file_list_string = '\n'.join(file_list)
        mocked_open = mock_open(read_data = file_list_string)

        list_path = "s3://test_bucket/raster_set.list"
        list_local_path = "/tmp/raster_set.list"
        
        mocked_get_osgeo_path.return_value = list_local_path

        raster_list = []
        expected_colors = []
        for n in range(0, file_number, 1):
            raster = MagicMock(Raster)
            raster.path = file_list[n]
            raster.bbox = (-0.75 + math.floor(n/3), -1.33 + n - 3 * math.floor(n/3), 0.25 + math.floor(n/3), -0.33 +  n - 3 * math.floor(n/3))
            raster.format = random.choice([ColorFormat.BIT, ColorFormat.UINT8, ColorFormat.FLOAT32])
            if raster.format == ColorFormat.BIT:
                raster.bands = 1
            else:
                raster.bands = random.randint(1, 4)
            
            color_dict = {'bands': raster.bands, 'format': raster.format}
            if color_dict not in expected_colors:
                expected_colors.append(color_dict)

            raster_list.append(raster)

        mocked_from_file.side_effect = raster_list

        srs = "EPSG:4326"
        with mock.patch('rok4.Raster.open', mocked_open):
            result = RasterSet.from_list(list_path, srs)

        assert result.srs == srs
        mocked_get_osgeo_path.assert_called_once_with(list_path)
        mocked_open.assert_called_once_with(file=list_local_path, mode='r')
        assert result.raster_list == raster_list
        assert math.isclose(result.bbox[0], -0.75, rel_tol=1e-5)
        assert math.isclose(result.bbox[1], -1.33, rel_tol=1e-5)
        assert math.isclose(result.bbox[2], 0.25 + math.floor((file_number-1)/3), rel_tol=1e-5)
        assert math.isclose(result.bbox[3], 1.67, rel_tol=1e-5)
        assert result.colors == expected_colors





        









