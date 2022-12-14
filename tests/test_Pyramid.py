from rok4.Pyramid import *
from rok4.TileMatrixSet import TileMatrixSet
from rok4.Storage import StorageType
from rok4.Exceptions import *

import pytest
import os
from unittest.mock import *
from unittest import mock

@mock.patch('rok4.Pyramid.get_data_str', side_effect=StorageError('FILE', 'Not found'))
def test_wrong_file(mocked_get_data_str):
    with pytest.raises(StorageError):
        pyramid = Pyramid.from_descriptor("file:///pyramid.json")

@mock.patch('rok4.Pyramid.get_data_str', return_value='{"format": "TIFF_PBF_MVT","levels":[{"id": "100","tables":')
def test_bad_json(mocked_get_data_str):
    with pytest.raises(FormatError) as exc:
        pyramid = Pyramid.from_descriptor("file:///pyramid.json")

    assert str(exc.value) == "Expected format JSON to read 'file:///pyramid.json' : Expecting value: line 1 column 59 (char 58)"
    mocked_get_data_str.assert_called_once_with('file:///pyramid.json')

@mock.patch('rok4.Pyramid.get_data_str', return_value='{"format": "TIFF_PBF_MVT","levels":[]}')
def test_missing_tms(mocked_get_data_str):
    with pytest.raises(MissingAttributeError) as exc:
        pyramid = Pyramid.from_descriptor("file:///pyramid.json")

    assert str(exc.value) == "Missing attribute 'tile_matrix_set' in 'file:///pyramid.json'"
    mocked_get_data_str.assert_called_once_with('file:///pyramid.json')


@mock.patch.dict(os.environ, {}, clear=True)
@mock.patch('rok4.Pyramid.get_data_str', return_value='{"format": "TIFF_PBF_MVT","levels":[{}], "tile_matrix_set": "PM"}')
@mock.patch('rok4.Pyramid.TileMatrixSet', side_effect=StorageError('FILE', 'TMS not found'))
def test_wrong_tms(mocked_tms_constructor, mocked_get_data_str):
    with pytest.raises(StorageError) as exc:
        pyramid = Pyramid.from_descriptor("file:///pyramid.json")

    assert str(exc.value) == "Issue occured using a FILE storage : TMS not found"
    mocked_tms_constructor.assert_called_once_with('PM')
    mocked_get_data_str.assert_called_once_with('file:///pyramid.json')


@mock.patch.dict(os.environ, {}, clear=True)
@mock.patch('rok4.Pyramid.get_data_str', return_value='{"format": "TIFF_JPG_UINT8","levels":[{"tiles_per_height":16,"tile_limits":{"min_col":0,"max_row":15,"max_col":15,"min_row":0},"storage":{"image_directory":"SCAN1000/DATA/0","path_depth":2,"type":"FILE"},"tiles_per_width":16,"id":"unknown"}], "tile_matrix_set": "PM"}')
@mock.patch('rok4.Pyramid.TileMatrixSet')
def test_wrong_level(mocked_tms_class, mocked_get_data_str):
    
    tms_instance = MagicMock()
    tms_instance.get_level.return_value = None
    tms_instance.name = "PM"
    mocked_tms_class.return_value = tms_instance

    with pytest.raises(Exception) as exc:
        pyramid = Pyramid.from_descriptor("file:///pyramid.json")
    
    mocked_tms_class.assert_called_once_with('PM')
    mocked_get_data_str.assert_called_once_with('file:///pyramid.json')
    tms_instance.get_level.assert_called_once_with('unknown')
    assert str(exc.value) == "Pyramid file:///pyramid.json owns a level with the ID 'unknown', not defined in the TMS 'PM'"


@mock.patch.dict(os.environ, {}, clear=True)
@mock.patch('rok4.Pyramid.get_data_str', return_value='{"format": "TIFF_JPG_UINT8","levels":[{"tiles_per_height":16,"tile_limits":{"min_col":0,"max_row":15,"max_col":15,"min_row":0},"storage":{"image_directory":"SCAN1000/DATA/0","path_depth":2,"type":"FILE"},"tiles_per_width":16,"id":"0"}], "tile_matrix_set": "PM"}')
@mock.patch('rok4.Pyramid.TileMatrixSet')
def test_raster_missing_raster_specifications(mocked_tms_class, mocked_get_data_str):

    with pytest.raises(MissingAttributeError) as exc:
        pyramid = Pyramid.from_descriptor("file:///pyramid.json")

    assert str(exc.value) == "Missing attribute 'raster_specifications' in 'file:///pyramid.json'"
    mocked_get_data_str.assert_called_once_with('file:///pyramid.json')

@mock.patch.dict(os.environ, {}, clear=True)
@mock.patch('rok4.Pyramid.get_data_str', return_value='{"format": "TIFF_PBF_MVT","levels":[{"tiles_per_height":16,"tile_limits":{"min_col":0,"max_row":15,"max_col":15,"min_row":0},"storage":{"image_directory":"SCAN1000/DATA/0","path_depth":2,"type":"FILE"},"tiles_per_width":16,"id":"0"}], "tile_matrix_set": "PM"}')
@mock.patch('rok4.Pyramid.TileMatrixSet', autospec=True)
def test_vector_missing_tables(mocked_tms_class, mocked_get_data_str):

    with pytest.raises(MissingAttributeError) as exc:
        pyramid = Pyramid.from_descriptor("file:///pyramid.json")

    assert str(exc.value) == "Missing attribute levels[].'tables' in 'file:///pyramid.json'"
    mocked_get_data_str.assert_called_once_with('file:///pyramid.json')

@mock.patch.dict(os.environ, {}, clear=True)
@mock.patch('rok4.Pyramid.get_data_str', return_value='{"raster_specifications":{"channels":3,"nodata":"255,0,0","photometric":"rgb","interpolation":"bicubic"}, "format": "TIFF_JPG_UINT8","levels":[{"tiles_per_height":16,"tile_limits":{"min_col":0,"max_row":15,"max_col":15,"min_row":0},"storage":{"image_prefix":"SCAN1000/DATA_0","pool_name":"pool1","type":"CEPH"},"tiles_per_width":16,"id":"0"}], "tile_matrix_set": "PM"}')
@mock.patch('rok4.Pyramid.TileMatrixSet')
def test_raster_ok(mocked_tms_class, mocked_get_data_str):

    try:
        pyramid = Pyramid.from_descriptor("ceph://pool1/sub/pyramid.json")
        assert pyramid.get_level("0") is not None
        assert pyramid.get_level("4") is None
        assert pyramid.name == "sub/pyramid"
        assert pyramid.storage_type == StorageType.CEPH
        assert pyramid.storage_root == "pool1"
        mocked_get_data_str.assert_called_once_with('ceph://pool1/sub/pyramid.json')

        clone = Pyramid.from_other(pyramid, "titi", {"type": "FILE", "root": "/data/ign"})
        assert clone.name == "titi"
        assert clone.storage_type == StorageType.FILE
        assert clone.storage_root == "/data/ign"
        assert clone.get_level("0") is not None
        assert clone.get_level("4") is None
    except Exception as exc:
        assert False, f"Pyramid creation raises an exception: {exc}"

@mock.patch.dict(os.environ, {}, clear=True)
@mock.patch('rok4.Pyramid.get_data_str', return_value='{"format": "TIFF_PBF_MVT","levels":[{"tiles_per_height":16,"tile_limits":{"min_col":0,"max_row":15,"max_col":15,"min_row":0},"storage":{"image_directory":"SCAN1000/DATA/0","path_depth":2,"type":"FILE"},"tiles_per_width":16,"id":"0","tables":[{"name":"table","geometry":"POINT","attributes":[{"type":"bigint","name":"fid","count":1531}]}]}], "tile_matrix_set": "PM"}')
@mock.patch('rok4.Pyramid.TileMatrixSet')
def test_vector_ok(mocked_tms_class, mocked_get_data_str):

    try:
        pyramid = Pyramid.from_descriptor("file:///pyramid.json")
        assert pyramid.get_level("0") is not None
        assert pyramid.get_level("4") is None
        assert pyramid.name == "pyramid"
        assert pyramid.storage_depth == 2
        assert pyramid.storage_type == StorageType.FILE
        mocked_get_data_str.assert_called_once_with('file:///pyramid.json')

        clone = Pyramid.from_other(pyramid, "toto", {"type": "S3", "root": "bucket"})
        assert clone.name == "toto"
        assert clone.storage_type == StorageType.S3
        assert clone.get_level("0") is not None
        assert clone.get_level("4") is None
    except Exception as exc:
        assert False, f"Pyramid creation raises an exception: {exc}"


def test_b36_path_decode():
    assert b36_path_decode("3E/42/01.tif") == (4032, 18217,)
    assert b36_path_decode("3E/42/01.TIFF") == (4032, 18217,)
    assert b36_path_decode("3E/42/01") == (4032, 18217,)

def test_b36_path_encode():
    assert b36_path_encode(4032, 18217, 2) == "3E/42/01.tif"
    assert b36_path_encode(14, 18217, 1) == "0E02/E1.tif"