import os
from unittest import mock
from unittest.mock import *

from rok4.enums import PyramidType
from rok4.exceptions import *
from rok4.layer import Layer


@mock.patch.dict(os.environ, {}, clear=True)
@mock.patch(
    "rok4.layer.get_data_str",
    return_value='{"pyramids" : [{"bottom_level" : "10","top_level" : "10","path" : "s3://pyramids/SCAN1000.json"}],"title" : "SCAN1000","bbox":{"east": 11.250000000000997,"west": -5.624999999999043,"north": 52.48278022207774,"south": 40.9798980696195},"styles" : ["normal","hypso"],"abstract" : "Diffusion de la donnée BDORTHO","resampling" : "linear","keywords" : ["PM","TIFF_JPG_UINT8"]}',
)
@mock.patch("rok4.layer.Pyramid.from_descriptor")
@mock.patch("rok4.layer.put_data_str", return_value=None)
def test_descriptor_ok(mocked_put_data_str, mocked_pyramid_class, mocked_get_data_str):
    tms_instance = MagicMock()
    tms_instance.srs = "EPSG:3857"

    level_instance = MagicMock()
    level_instance.id = 10
    level_instance.resolution = 1

    pyramid_instance = MagicMock()
    pyramid_instance.raster_specifications = {
        "channels": 3,
        "nodata": "255,255,255",
        "photometric": "rgb",
        "interpolation": "bicubic",
    }
    pyramid_instance.format = "TIFF_JPG_UINT8"
    pyramid_instance.tms = tms_instance
    pyramid_instance.descriptor = "s3://pyramids/SCAN1000.json"
    pyramid_instance.get_levels.return_value = [level_instance]
    mocked_pyramid_class.return_value = pyramid_instance

    try:
        layer = Layer.from_descriptor("s3://layers/SCAN1000.json")
        assert layer.type == PyramidType.RASTER
        mocked_get_data_str.assert_called_once_with("s3://layers/SCAN1000.json")

        layer.write_descriptor("s3://layers_backup/")
        mocked_put_data_str.assert_called_once_with(
            '{"title": "SCAN1000", "abstract": "Diffusion de la donn\\u00e9e BDORTHO", "keywords": ["PM", "TIFF_JPG_UINT8"], "wmts": {"authorized": true}, "tms": {"authorized": true}, "bbox": {"south": 40.9798980696195, "west": -5.624999999999043, "north": 52.48278022207774, "east": 11.250000000000997}, "pyramids": [{"bottom_level": "10", "top_level": "10", "path": "s3://pyramids/SCAN1000.json"}], "wms": {"authorized": true, "crs": ["CRS:84", "IGNF:WGS84G", "EPSG:3857", "EPSG:4258", "EPSG:4326"]}, "styles": ["normal", "hypso"], "resampling": "linear"}',
            "s3://layers_backup/SCAN1000.json",
        )
    except Exception as exc:
        assert False, f"Layer creation from descriptor raises an exception: {exc}"


@mock.patch("rok4.layer.Pyramid.from_descriptor")
@mock.patch("rok4.layer.reproject_bbox", return_value=(0, 0, 100, 100))
@mock.patch("rok4.layer.put_data_str", return_value=None)
def test_parameters_vector_ok(
    mocked_put_data_str, mocked_utils_reproject_bbox, mocked_pyramid_class
):
    tms_instance = MagicMock()
    tms_instance.srs = "EPSG:3857"

    level_instance = MagicMock()
    level_instance.id = 10
    level_instance.resolution = 1
    level_instance.bbox = (0, 0, 100000, 100000)

    pyramid_instance = MagicMock()
    pyramid_instance.format = "TIFF_PBF_MVT"
    pyramid_instance.tms = tms_instance
    pyramid_instance.descriptor = "file:///home/ign/pyramids/SCAN1000.json"
    pyramid_instance.get_levels.return_value = [level_instance]
    mocked_pyramid_class.return_value = pyramid_instance

    try:
        layer = Layer.from_parameters(
            [
                {
                    "path": "file:///home/ign/pyramids/SCAN1000.json",
                    "bottom_level": "10",
                    "top_level": "10",
                }
            ],
            "layername",
            title="title",
            abstract="abstract",
        )
        assert layer.type == PyramidType.VECTOR
        assert layer.geobbox == (0, 0, 100, 100)
        layer.write_descriptor("file:///home/ign/layers/")
        mocked_put_data_str.assert_called_once_with(
            '{"title": "title", "abstract": "abstract", "keywords": ["VECTOR", "layername"], "wmts": {"authorized": true}, "tms": {"authorized": true}, "bbox": {"south": 0, "west": 0, "north": 100, "east": 100}, "pyramids": [{"bottom_level": "10", "top_level": "10", "path": "file:///home/ign/pyramids/SCAN1000.json"}]}',
            "file:///home/ign/layers/layername.json",
        )

    except Exception as exc:
        assert False, f"Layer creation from parameters raises an exception: {exc}"


@mock.patch("rok4.layer.Pyramid.from_descriptor")
@mock.patch("rok4.layer.reproject_bbox", return_value=(0, 0, 100, 100))
@mock.patch("rok4.layer.put_data_str", return_value=None)
def test_parameters_raster_ok(
    mocked_put_data_str, mocked_utils_reproject_bbox, mocked_pyramid_class
):
    tms_instance = MagicMock()
    tms_instance.srs = "EPSG:3857"

    level_instance = MagicMock()
    level_instance.id = 10
    level_instance.resolution = 1
    level_instance.bbox = (0, 0, 100000, 100000)

    pyramid_instance = MagicMock()
    pyramid_instance.format = "TIFF_ZIP_FLOAT32"
    pyramid_instance.raster_specifications = {
        "channels": 1,
        "nodata": "-99999",
        "photometric": "gray",
        "interpolation": "nn",
    }
    pyramid_instance.tms = tms_instance
    pyramid_instance.bottom_level.id = "10"
    pyramid_instance.top_level.id = "10"
    pyramid_instance.descriptor = "file:///home/ign/pyramids/RGEALTI.json"
    pyramid_instance.get_levels.return_value = [level_instance]
    mocked_pyramid_class.return_value = pyramid_instance

    try:
        layer = Layer.from_parameters(
            [{"path": "file:///home/ign/pyramids/RGEALTI.json"}],
            "layername",
            title="title",
            abstract="abstract",
        )
        assert layer.type == PyramidType.RASTER
        assert layer.geobbox == (0, 0, 100, 100)
        layer.write_descriptor("file:///home/ign/layers/")
        mocked_put_data_str.assert_called_once_with(
            '{"title": "title", "abstract": "abstract", "keywords": ["RASTER", "layername"], "wmts": {"authorized": true}, "tms": {"authorized": true}, "bbox": {"south": 0, "west": 0, "north": 100, "east": 100}, "pyramids": [{"bottom_level": "10", "top_level": "10", "path": "file:///home/ign/pyramids/RGEALTI.json"}], "wms": {"authorized": true, "crs": ["CRS:84", "IGNF:WGS84G", "EPSG:3857", "EPSG:4258", "EPSG:4326"]}, "styles": ["normal"], "resampling": "nn"}',
            "file:///home/ign/layers/layername.json",
        )

    except Exception as exc:
        assert False, f"Layer creation from parameters raises an exception: {exc}"
