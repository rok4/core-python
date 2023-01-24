"""Describes unit tests for the rok4.Raster module."""

from rok4.Raster import *
from rok4.Storage import StorageType

import pytest
from unittest.mock import *
from unittest import mock, TestCase, skip

class TestConstructorCommon(TestCase):
    """Test class for the rok4.Raster.Raster(path) class constructor, for any storage type."""

    def test_empty(self):
        """Test case : Constructor called without the expected path argument."""

        with pytest.raises(TypeError):
            Raster()


    @mock.patch('rok4.Raster.exists', return_value=False)
    def test_image_not_found(self, mocked_exists):
        """Test case : Constructor called on a path matching no file or object."""

        path = "file:///home/user/image.tif"

        with pytest.raises(Exception):
            Raster(path)

        mocked_exists.assert_called_once_with(path)



class TestConstructorFile(TestCase):
    """Test class for the rok4.Raster.Raster(path) class constructor, used with file storage."""

    def setUp(self):
        self.path = {
            'protocol': 'file://',
            'base_location': '/home/user',
            'base_name': 'image',
            'image': {},
            'mask': {}
        }
        self.path['image']['system'] = f"{self.path['base_location']}/{self.path['base_name']}.tif"
        self.path['mask']['system'] = f"{self.path['base_location']}/{self.path['base_name']}.msk"
        self.path['image']['full'] = f"{self.path['protocol']}{self.path['image']['system']}"
        self.path['mask']['full'] = f"{self.path['protocol']}{self.path['mask']['system']}"
        
        self.get_infos_from_path = (StorageType.FILE, self.path['image']['system'], self.path['base_location'], self.path['base_name'])


    @mock.patch('rok4.Raster.get_infos_from_path')
    @mock.patch('rok4.Raster.gdal.Open')
    @mock.patch('rok4.Raster._compute_samples', return_value=3)
    @mock.patch('rok4.Raster._compute_bbox', return_value=[-5.4, 41.3, 9.8, 51.3])
    @mock.patch('rok4.Raster.exists', side_effect=[True, False])
    def test_image(self, mocked_exists, mocked_compute_bbox, mocked_compute_samples, mocked_gdal_open, mocked_get_infos_from_path):
        """Test case : Constructor called nominally on an image without mask."""

        mocked_get_infos_from_path.return_value = self.get_infos_from_path

        raster_object = Raster( self.path['image']['full'] )

        mocked_exists.assert_has_calls([ call(self.path['image']['full']), call(self.path['mask']['full']) ])
        mocked_get_infos_from_path.assert_called_once_with( self.path['image']['full'] )
        mocked_gdal_open.assert_called_once_with( self.path['image']['system'] )
        assert raster_object.path == self.path['image']['full']
        assert raster_object.mask is None

        mocked_compute_bbox.assert_called_once()
        assert raster_object.bbox == [-5.4, 41.3, 9.8, 51.3]

        mocked_compute_samples.assert_called_once()
        assert raster_object.samples == 3


    @mock.patch('rok4.Raster.ogr.GetDriverByName')
    @mock.patch('rok4.Raster.get_infos_from_path')
    @mock.patch('rok4.Raster.gdal.Open')
    @mock.patch('rok4.Raster._compute_samples', return_value=3)
    @mock.patch('rok4.Raster._compute_bbox', return_value=[-5.4, 41.3, 9.8, 51.3])
    @mock.patch('rok4.Raster.exists', side_effect=[True, True])
    def test_image_and_mask(self, mocked_exists, mocked_compute_bbox, mocked_compute_samples, mocked_gdal_open, mocked_get_infos_from_path, mocked_get_driver):
        """Test case : Constructor called nominally on an image with mask."""

        mocked_get_infos_from_path.return_value = self.get_infos_from_path
        # This next line emulates the return of ogr.GetDriverByName()
        # TODO : manage to implent this using unittest.mock
        mocked_get_driver.return_value = type('', (object,), {'Open': mocked_gdal_open})

        raster_object = Raster(self.path['image']['full'])

        mocked_exists.assert_has_calls([ call(self.path['image']['full']), call(self.path['mask']['full']) ])
        mocked_get_infos_from_path.assert_called_once_with(self.path['image']['full'])
        mocked_get_driver.assert_called_once_with('GTiff')
        mocked_gdal_open.assert_has_calls([ call(self.path['image']['system']), call(self.path['mask']['system']) ])
        assert raster_object.path == self.path['image']['full']
        assert raster_object.mask == self.path['mask']['full']

        mocked_compute_bbox.assert_called_once()
        assert raster_object.bbox == [-5.4, 41.3, 9.8, 51.3]

        mocked_compute_samples.assert_called_once()
        assert raster_object.samples == 3


    @mock.patch('rok4.Raster.get_infos_from_path')
    @mock.patch('rok4.Raster.gdal.Open', side_effect=RuntimeError)
    @mock.patch('rok4.Raster.exists', side_effect=[True, False])
    def test_unsupported_image_format(self, mocked_exists, mocked_gdal_open, mocked_get_infos_from_path):
        """Test case : Constructor called on an unsupported 'image' file or object."""

        mocked_get_infos_from_path.return_value = self.get_infos_from_path

        with pytest.raises(RuntimeError):
            Raster(self.path['image']['full'])

        mocked_exists.assert_called_once_with(self.path['image']['full'])
        mocked_gdal_open.assert_called_once_with(self.path['image']['system'])


    @mock.patch('rok4.Raster.ogr.GetDriverByName')
    @mock.patch('rok4.Raster.get_infos_from_path')
    @mock.patch('rok4.Raster.gdal.Open', side_effect=[None, RuntimeError])
    @mock.patch('rok4.Raster.exists', side_effect=[True, True])
    def test_unsupported_mask_format(self, mocked_exists, mocked_gdal_open, mocked_get_infos_from_path, mocked_get_driver):
        """Test case : Constructor called on an unsupported mask file or object."""

        mocked_get_infos_from_path.return_value = self.get_infos_from_path
        # This next line emulates the return of ogr.GetDriverByName()
        # TODO : manage to implent this using unittest.mock
        mocked_get_driver.return_value = type('', (object,), {'Open': mocked_gdal_open})

        with pytest.raises(RuntimeError):
            Raster(self.path['image']['full'])      

        mocked_exists.assert_has_calls([call(self.path['image']['full']), call(self.path['mask']['full'])])
        mocked_get_driver.assert_called_once_with('GTiff')
        mocked_gdal_open.assert_has_calls([ call(self.path['image']['system']), call(self.path['mask']['system']) ])



class TestConstructorObject(TestCase):
    """Test class for the rok4.Raster.Raster(path) class constructor, used with object storage."""

    def setUp(self):
        self.path = {
            'protocol': 's3://',
            'base_location': 'bucket',
            'base_name': 'basename',
            'image': {},
            'mask': {}
        }
        self.path['image']['system'] = f"{self.path['base_location']}/{self.path['base_name']}.tif"
        self.path['mask']['system'] = f"{self.path['base_location']}/{self.path['base_name']}.msk"
        self.path['image']['full'] = f"{self.path['protocol']}{self.path['image']['system']}"
        self.path['mask']['full'] = f"{self.path['protocol']}{self.path['mask']['system']}"

        self.get_infos_from_path = (StorageType.S3, self.path['image']['system'], self.path['base_location'], self.path['base_name'])

        self.tmp_path = {
            'image': {
                'system': '/tmp/tempimage'
            },
            'mask': {
                'system': '/tmp/tempmask'
            },
        }
        self.tmp_path['image']['full'] = f"file://{self.tmp_path['image']['system']}"
        self.tmp_path['mask']['full'] = f"file://{self.tmp_path['mask']['system']}"


    @mock.patch('rok4.Raster.copy')
    @mock.patch('rok4.Raster.tempfile.NamedTemporaryFile')
    @mock.patch('rok4.Raster.get_infos_from_path')
    @mock.patch('rok4.Raster.gdal.Open')
    @mock.patch('rok4.Raster._compute_samples', return_value=3)
    @mock.patch('rok4.Raster._compute_bbox', return_value=[-5.4, 41.3, 9.8, 51.3])
    @mock.patch('rok4.Raster.exists', side_effect=[True, False])
    def test_image(self, mocked_exists, mocked_compute_bbox, mocked_compute_samples, mocked_gdal_open, mocked_get_infos_from_path, mocked_create_temporary_file, mocked_copy):
        """Test case : Constructor called nominally on an image without mask."""
        
        mocked_get_infos_from_path.return_value = self.get_infos_from_path
        mocked_tmp_file_close = Mock()
        # This next line emulates the return of tempfile.NamedTemporaryFile()
        # TODO : manage to implent this using unittest.mock
        mocked_create_temporary_file.return_value = type('', (object,), {'name': self.tmp_path['image']['system'], 'close': mocked_tmp_file_close})

        raster_object = Raster(self.path['image']['full'])

        mocked_exists.assert_has_calls([call(self.path['image']['full']), call(self.path['mask']['full'])])
        mocked_get_infos_from_path.assert_called_once_with(self.path['image']['full'])
        mocked_create_temporary_file.assert_called_once_with(mode='r', delete=False)
        mocked_copy.assert_called_once_with(self.path['image']['full'], self.tmp_path['image']['full'])
        mocked_gdal_open.assert_called_once_with(self.tmp_path['image']['system'])
        assert raster_object.path == self.path['image']['full']
        assert raster_object.mask is None

        mocked_compute_bbox.assert_called_once()
        assert raster_object.bbox == [-5.4, 41.3, 9.8, 51.3]

        mocked_compute_samples.assert_called_once()
        assert raster_object.samples == 3


    @mock.patch('rok4.Raster.ogr.GetDriverByName')
    @mock.patch('rok4.Raster.copy')
    @mock.patch('rok4.Raster.tempfile.NamedTemporaryFile')
    @mock.patch('rok4.Raster.get_infos_from_path')
    @mock.patch('rok4.Raster.gdal.Open')
    @mock.patch('rok4.Raster._compute_samples', return_value=3)
    @mock.patch('rok4.Raster._compute_bbox', return_value=[-5.4, 41.3, 9.8, 51.3])
    @mock.patch('rok4.Raster.exists', side_effect=[True, True])
    def test_image_and_mask(self, mocked_exists, mocked_compute_bbox, mocked_compute_samples, mocked_gdal_open, mocked_get_infos_from_path, mocked_create_temporary_file, mocked_copy, mocked_get_driver):
        """Test case : Constructor called nominally on an image with mask."""
        
        mocked_get_infos_from_path.return_value = self.get_infos_from_path
        mocked_tmp_file_close = Mock()
        # This next instruction emulates the return of tempfile.NamedTemporaryFile()
        # TODO : manage to implent this using unittest.mock
        mocked_create_temporary_file.side_effect = [
            type('', (object,), {'name': self.tmp_path['image']['system'], 'close': mocked_tmp_file_close}),
            type('', (object,), {'name': self.tmp_path['mask']['system'], 'close': mocked_tmp_file_close})
        ]
        # This next line emulates the return of ogr.GetDriverByName()
        # TODO : manage to implent this using unittest.mock
        mocked_get_driver.return_value = type('', (object,), {'Open': mocked_gdal_open})

        raster_object = Raster(self.path['image']['full'])

        expected_copy_calls = [
            call(self.path['image']['full'], self.tmp_path['image']['full']),
            call(self.path['mask']['full'], self.tmp_path['mask']['full'])
        ]
        mocked_exists.assert_has_calls([call(self.path['image']['full']), call(self.path['mask']['full'])])
        mocked_get_infos_from_path.assert_called_once_with(self.path['image']['full'])
        mocked_create_temporary_file.assert_has_calls([call(mode='r', delete=False), call(mode='r', delete=False)])
        mocked_copy.assert_has_calls(expected_copy_calls)
        mocked_get_driver.assert_called_once_with('GTiff')
        mocked_gdal_open.assert_has_calls([ call(self.tmp_path['image']['system']), call(self.tmp_path['mask']['system']) ])
        assert raster_object.path == self.path['image']['full']
        assert raster_object.mask == self.path['mask']['full']

        mocked_compute_bbox.assert_called_once()
        assert raster_object.bbox == [-5.4, 41.3, 9.8, 51.3]

        mocked_compute_samples.assert_called_once()
        assert raster_object.samples == 3

    
    @mock.patch('rok4.Raster.copy')
    @mock.patch('rok4.Raster.tempfile.NamedTemporaryFile')
    @mock.patch('rok4.Raster.get_infos_from_path')
    @mock.patch('rok4.Raster.gdal.Open', side_effect=RuntimeError)
    @mock.patch('rok4.Raster.exists', side_effect=[True, False])
    def test_unsupported_image_format(self, mocked_exists, mocked_gdal_open, mocked_get_infos_from_path, mocked_create_temporary_file, mocked_copy):
        """Test case : Constructor called on an unsupported 'image' file or object."""
        
        mocked_get_infos_from_path.return_value = self.get_infos_from_path
        mocked_tmp_file_close = Mock()
        # This next line emulates the return of tempfile.NamedTemporaryFile()
        # TODO : manage to implent this using unittest.mock
        mocked_create_temporary_file.return_value = type('', (object,), {'name': self.tmp_path['image']['system'], 'close': mocked_tmp_file_close})

        with pytest.raises(RuntimeError):
            Raster(self.path['image']['full'])

        mocked_exists.assert_called_once_with(self.path['image']['full'])
        mocked_get_infos_from_path.assert_called_once_with(self.path['image']['full'])
        mocked_create_temporary_file.assert_called_once_with(mode='r', delete=False)
        mocked_copy.assert_called_once_with(self.path['image']['full'], self.tmp_path['image']['full'])
        mocked_gdal_open.assert_called_once_with(self.tmp_path['image']['system'])


    @mock.patch('rok4.Raster.ogr.GetDriverByName')
    @mock.patch('rok4.Raster.copy')
    @mock.patch('rok4.Raster.tempfile.NamedTemporaryFile')
    @mock.patch('rok4.Raster.get_infos_from_path')
    @mock.patch('rok4.Raster.gdal.Open', side_effect=[None, RuntimeError])
    @mock.patch('rok4.Raster.exists', side_effect=[True, True])
    def test_unsupported_mask_format(self, mocked_exists, mocked_gdal_open, mocked_get_infos_from_path, mocked_create_temporary_file, mocked_copy, mocked_get_driver):
        """Test case : Constructor called on an unsupported mask file or object."""
        
        mocked_get_infos_from_path.return_value = self.get_infos_from_path
        mocked_tmp_file_close = Mock()
        # This next instruction emulates the return of tempfile.NamedTemporaryFile()
        # TODO : manage to implent this using unittest.mock
        mocked_create_temporary_file.side_effect = [
            type('', (object,), {'name': self.tmp_path['image']['system'], 'close': mocked_tmp_file_close}),
            type('', (object,), {'name': self.tmp_path['mask']['system'], 'close': mocked_tmp_file_close})
        ]
        # This next line emulates the return of ogr.GetDriverByName()
        # TODO : manage to implent this using unittest.mock
        mocked_get_driver.return_value = type('', (object,), {'Open': mocked_gdal_open})

        with pytest.raises(RuntimeError):
            Raster(self.path['image']['full'])

        expected_copy_calls = [
            call(self.path['image']['full'], self.tmp_path['image']['full']),
            call(self.path['mask']['full'], self.tmp_path['mask']['full'])
        ]
        mocked_exists.assert_has_calls([call(self.path['image']['full']), call(self.path['mask']['full'])])
        mocked_get_infos_from_path.assert_called_once_with(self.path['image']['full'])
        mocked_create_temporary_file.assert_has_calls([call(mode='r', delete=False), call(mode='r', delete=False)])
        mocked_copy.assert_has_calls(expected_copy_calls)
        mocked_get_driver.assert_called_once_with('GTiff')
        mocked_gdal_open.assert_has_calls([ call(self.tmp_path['image']['system']), call(self.tmp_path['mask']['system']) ])



class TestComputeBbox(TestCase):
    """Test class for the rok4.Raster._compute_bbox function."""



class TestComputeSamples(TestCase):
    """Test class for the rok4.Raster._compute_samples function."""

