from rok4.Pyramid import *
from rok4.TileMatrixSet import TileMatrixSet
from rok4.Storage import StorageType
from rok4.Utils import *
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
@mock.patch('rok4.Pyramid.get_data_str', return_value='{"format": "TIFF_JPG_UINT8","levels":[{"tiles_per_height":16,"tile_limits":{"min_col":0,"max_row":15,"max_col":15,"min_row":0},"storage":{"image_directory":"SCAN1000/DATA/0","path_depth":2,"type":"FILE"},"tiles_per_width":16,"id":"0"}], "tile_matrix_set": "PM"}')
@mock.patch('rok4.Pyramid.TileMatrixSet')
def test_raster_missing_raster_specifications(mocked_tms_class, mocked_get_data_str):

    with pytest.raises(MissingAttributeError) as exc:
        pyramid = Pyramid.from_descriptor("file:///pyramid.json")

    assert str(exc.value) == "Missing attribute 'raster_specifications' in 'file:///pyramid.json'"
    mocked_get_data_str.assert_called_once_with('file:///pyramid.json')


@mock.patch.dict(os.environ, {}, clear=True)
@mock.patch('rok4.Pyramid.get_data_str', return_value='{"raster_specifications":{"channels":3,"nodata":"255,0,0","photometric":"rgb","interpolation":"bicubic"}, "format": "TIFF_JPG_UINT8","levels":[{"tiles_per_height":16,"tile_limits":{"min_col":0,"max_row":15,"max_col":15,"min_row":0},"storage":{"image_directory":"SCAN1000/DATA/0","path_depth":2,"type":"FILE"},"tiles_per_width":16,"id":"unknown"}], "tile_matrix_set": "PM"}')
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
@mock.patch('rok4.Pyramid.put_data_str', return_value=None)
def test_raster_ok(mocked_put_data_str, mocked_tms_class, mocked_get_data_str):

    tms_instance = MagicMock()
    tms_instance.name = "PM"
    tms_instance.srs = "EPSG:3857"
    tms_instance.sr = sr_src = srs_to_spatialreference("EPSG:3857")

    tm_instance = MagicMock()
    tm_instance.id = "0"
    tm_instance.resolution = 1
    tm_instance.point_to_indices.return_value = (0,0,128,157)

    tms_instance.get_level.return_value = tm_instance

    mocked_tms_class.return_value = tms_instance

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
        assert clone.get_infos_from_slab_path("IMAGE/12/00/00/00.tif") == (SlabType.DATA, "12", 0, 0)
        assert clone.get_tile_indices(102458, 6548125, srs = "EPSG:3857") == ("0",0,0,128,157)
        assert clone.get_tile_indices(43, 2, srs = "EPSG:4326") == ("0",0,0,128,157)


        assert len(clone.get_levels()) == 1

        clone.write_descriptor()
        mocked_put_data_str.assert_called_once_with('{"tile_matrix_set": "PM", "format": "TIFF_JPG_UINT8", "levels": [{"id": "0", "tiles_per_width": 16, "tiles_per_height": 16, "tile_limits": {"min_col": 0, "max_row": 15, "max_col": 15, "min_row": 0}, "storage": {"type": "FILE", "image_directory": "titi/DATA/0", "path_depth": 2}}], "raster_specifications": {"channels": 3, "nodata": "255,0,0", "photometric": "rgb", "interpolation": "bicubic"}}', 'file:///data/ign/titi.json')
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

    with pytest.raises(Exception) as exc:
        pyramid.get_tile_data_raster("12", 5, 6)


@mock.patch.dict(os.environ, {}, clear=True)
@mock.patch('rok4.Pyramid.TileMatrixSet')
def test_tile_read_raster(mocked_tms_class):

    tms_instance = MagicMock()
    tms_instance.name = "UTM20W84MART_1M_MNT"
    tms_instance.srs = "IGNF:UTM20W84MART"
    
    tm_instance = MagicMock()
    tm_instance.id = "8"
    tm_instance.tile_size = (256,256)

    tms_instance.get_level.return_value = tm_instance

    mocked_tms_class.return_value = tms_instance

    try:
        pyramid = Pyramid.from_descriptor("file://tests/fixtures/TIFF_ZIP_FLOAT32.json")
        data = pyramid.get_tile_data_raster("8",2748,40537)

        assert data.shape == (256,256,1)
        assert data[128][128][0] == 447.25
    except Exception as exc:
        assert False, f"Pyramid raster tile read raises an exception: {exc}"



@mock.patch.dict(os.environ, {}, clear=True)
@mock.patch('rok4.Pyramid.TileMatrixSet')
def test_tile_read_vector(mocked_tms_class):

    tms_instance = MagicMock()
    tms_instance.name = "PM"
    tms_instance.srs = "EPSG:3857"
    
    tm_instance = MagicMock()
    tm_instance.id = "4"
    tm_instance.tile_size = (256,256)

    tms_instance.get_level.return_value = tm_instance

    mocked_tms_class.return_value = tms_instance

    try:
        pyramid = Pyramid.from_descriptor("file://tests/fixtures/TIFF_PBF_MVT.json")

        data = pyramid.get_tile_data_vector("4", 5, 5)
        assert data is None

        data = pyramid.get_tile_data_vector("4", 8, 5)
        assert type(data) is dict
        assert "ecoregions_3857" in data
    except Exception as exc:
        assert False, f"Pyramid vector tile read raises an exception: {exc}"

def test_b36_path_decode():
    assert b36_path_decode("3E/42/01.tif") == (4032, 18217,)
    assert b36_path_decode("3E/42/01.TIFF") == (4032, 18217,)
    assert b36_path_decode("3E/42/01") == (4032, 18217,)

def test_b36_path_encode():
    assert b36_path_encode(4032, 18217, 2) == "3E/42/01.tif"
    assert b36_path_encode(14, 18217, 1) == "0E02/E1.tif"