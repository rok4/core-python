from rok4.TileMatrixSet import TileMatrixSet
from rok4.Exceptions import *

import pytest
import os
from unittest.mock import *
from unittest import mock

@mock.patch.dict(os.environ, {}, clear=True)
def test_missing_env():
    with pytest.raises(MissingEnvironmentError):
        tms = TileMatrixSet("tms")

@mock.patch.dict(os.environ, {"ROK4_TMS_DIRECTORY": "file:///path/to"}, clear=True)
@mock.patch('rok4.TileMatrixSet.get_data_str', side_effect=StorageError('FILE', 'Not found'))
def test_wrong_file(mocked_get_data_str):
    with pytest.raises(StorageError):
        tms = TileMatrixSet("tms")

@mock.patch.dict(os.environ, {"ROK4_TMS_DIRECTORY": "file:///path/to"}, clear=True)
@mock.patch('rok4.TileMatrixSet.get_data_str', return_value='"crs":"EPSG:3857","orderedAxes":["X","Y"],"id":"PM"}')
def test_bad_json(mocked_get_data_str):
    with pytest.raises(FormatError) as exc:
        tms = TileMatrixSet("tms")
    mocked_get_data_str.assert_called_once_with('file:///path/to/tms.json')

@mock.patch.dict(os.environ, {"ROK4_TMS_DIRECTORY": "file:///path/to"}, clear=True)
@mock.patch('rok4.TileMatrixSet.get_data_str', return_value='{"tileMatrices":[{"id":"0","tileWidth":256,"scaleDenominator":559082264.028718,"matrixWidth":1,"cellSize":156543.033928041,"matrixHeight":1,"tileHeight":256,"pointOfOrigin":[-20037508.3427892,20037508.3427892]}],"crs":"EPSG:3857","orderedAxes":["X","Y"]}')
def test_missing_id(mocked_get_data_str):
    with pytest.raises(MissingAttributeError) as exc:
        tms = TileMatrixSet("tms")
    assert str(exc.value) == "Missing attribute 'id' in 'file:///path/to/tms.json'"
    mocked_get_data_str.assert_called_once_with('file:///path/to/tms.json')

@mock.patch.dict(os.environ, {"ROK4_TMS_DIRECTORY": "file:///path/to"}, clear=True)
@mock.patch('rok4.TileMatrixSet.get_data_str', return_value='{"tileMatrices":[{"id":"0","tileWidth":256,"scaleDenominator":559082264.028718,"matrixWidth":1,"cellSize":156543.033928041,"matrixHeight":1,"tileHeight":256,"pointOfOrigin":[-20037508.3427892,20037508.3427892]}],"orderedAxes":["X","Y"],"id":"PM"}')
def test_missing_crs(mocked_get_data_str):
    with pytest.raises(MissingAttributeError) as exc:
        tms = TileMatrixSet("tms")
    assert str(exc.value) == "Missing attribute 'crs' in 'file:///path/to/tms.json'"
    mocked_get_data_str.assert_called_once_with('file:///path/to/tms.json')


@mock.patch.dict(os.environ, {"ROK4_TMS_DIRECTORY": "file:///path/to"}, clear=True)
@mock.patch('rok4.TileMatrixSet.get_data_str', return_value='{"crs":"epsg:123456","orderedAxes":["X","Y"],"tileMatrices":[{"id":"0","tileWidth":256,"scaleDenominator":559082264.028718,"matrixWidth":1,"cellSize":156543.033928041,"matrixHeight":1,"tileHeight":256,"pointOfOrigin":[-20037508.3427892,20037508.3427892]}],"orderedAxes":["X","Y"],"id":"PM"}')
def test_wrong_crs(mocked_get_data_str):
    with pytest.raises(Exception) as exc:
        tms = TileMatrixSet("tms")
    assert str(exc.value) == "Wrong attribute 'crs' ('epsg:123456') in 'file:///path/to/tms.json', not recognize by OSR"
    mocked_get_data_str.assert_called_once_with('file:///path/to/tms.json')

@mock.patch.dict(os.environ, {"ROK4_TMS_DIRECTORY": "file:///path/to"}, clear=True)
@mock.patch('rok4.TileMatrixSet.get_data_str', return_value='{"crs":"epsg:4326","orderedAxes":["Lat","Lon"],"tileMatrices":[{"id":"0","tileWidth":256,"scaleDenominator":559082264.028718,"matrixWidth":1,"cellSize":156543.033928041,"matrixHeight":1,"tileHeight":256,"pointOfOrigin":[-20037508.3427892,20037508.3427892]}],"id":"PM"}')
def test_wrong_axes_order(mocked_get_data_str):
    with pytest.raises(Exception) as exc:
        tms = TileMatrixSet("tms")
    assert str(exc.value) == "TMS 'file:///path/to/tms.json' own invalid axes order : only X,Y or Lon,Lat are handled"
    mocked_get_data_str.assert_called_once_with('file:///path/to/tms.json')

@mock.patch.dict(os.environ, {"ROK4_TMS_DIRECTORY": "file:///path/to"}, clear=True)
@mock.patch('rok4.TileMatrixSet.get_data_str', return_value='{"crs":"EPSG:3857","orderedAxes":["X","Y"],"id":"PM"}')
def test_missing_levels(mocked_get_data_str):
    with pytest.raises(MissingAttributeError) as exc:
        tms = TileMatrixSet("tms")
    assert str(exc.value) == "Missing attribute 'tileMatrices' in 'file:///path/to/tms.json'"
    mocked_get_data_str.assert_called_once_with('file:///path/to/tms.json')

@mock.patch.dict(os.environ, {"ROK4_TMS_DIRECTORY": "file:///path/to"}, clear=True)
@mock.patch('rok4.TileMatrixSet.get_data_str', return_value='{"tileMatrices":[],"crs":"EPSG:3857","orderedAxes":["X","Y"],"id":"PM"}')
def test_no_levels(mocked_get_data_str):
    with pytest.raises(Exception) as exc:
        tms = TileMatrixSet("tms")
    assert str(exc.value) == "TMS 'file:///path/to/tms.json' has no level"
    mocked_get_data_str.assert_called_once_with('file:///path/to/tms.json')

@mock.patch.dict(os.environ, {"ROK4_TMS_DIRECTORY": "file:///path/to"}, clear=True)
@mock.patch('rok4.TileMatrixSet.get_data_str', return_value='{"tileMatrices":[{"tileWidth":256,"scaleDenominator":559082264.028718,"matrixWidth":1,"cellSize":156543.033928041,"matrixHeight":1,"tileHeight":256,"pointOfOrigin":[-20037508.3427892,20037508.3427892]}],"orderedAxes":["X","Y"],"id":"PM","crs":"EPSG:3857"}')
def test_wrong_level(mocked_get_data_str):
    with pytest.raises(MissingAttributeError) as exc:
        tms = TileMatrixSet("tms")
    assert str(exc.value) == "Missing attribute tileMatrices[].'id' in 'file:///path/to/tms.json'"
    mocked_get_data_str.assert_called_once_with('file:///path/to/tms.json')

@mock.patch.dict(os.environ, {"ROK4_TMS_DIRECTORY": "file:///path/to"}, clear=True)
@mock.patch('rok4.TileMatrixSet.get_data_str', return_value='{"tileMatrices":[{"id":"level_0","tileWidth":256,"scaleDenominator":559082264.028718,"matrixWidth":1,"cellSize":156543.033928041,"matrixHeight":1,"tileHeight":256,"pointOfOrigin":[-20037508.3427892,20037508.3427892]}],"crs":"EPSG:3857","orderedAxes":["X","Y"],"id":"PM"}')
def test_wrong_level_id(mocked_get_data_str):
    with pytest.raises(Exception) as exc:
        tms = TileMatrixSet("tms")

    assert str(exc.value) == "TMS file:///path/to/tms.json owns a level whom id contains an underscore (level_0)"
    mocked_get_data_str.assert_called_once_with('file:///path/to/tms.json')

@mock.patch.dict(os.environ, {"ROK4_TMS_DIRECTORY": "file:///path/to"}, clear=True)
@mock.patch('rok4.TileMatrixSet.get_data_str', return_value='{"tileMatrices":[{"id":"0","tileWidth":256,"scaleDenominator":559082264.028718,"matrixWidth":1,"cellSize":156543.033928041,"matrixHeight":1,"tileHeight":256,"pointOfOrigin":[-20037508.3427892,20037508.3427892]}],"crs":"EPSG:3857","orderedAxes":["X","Y"],"id":"PM"}')
def test_ok(mocked_get_data_str):
    try:
        tms = TileMatrixSet("tms")
        assert tms.get_level("0") is not None
        assert tms.get_level("4") is None
        mocked_get_data_str.assert_called_once_with('file:///path/to/tms.json')
    except Exception as exc:
        assert False, f"'TileMatrixSet creation raises an exception: {exc}"
