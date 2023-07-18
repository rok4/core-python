from rok4.utils import *
from rok4.exceptions import *

import pytest
import os
from osgeo import gdal, osr
import math
import random

from unittest.mock import *
from unittest import mock


def test_srs_to_spatialreference_ignf_ok():
    try:
        sr = srs_to_spatialreference("IGNF:LAMB93")
        sr = srs_to_spatialreference("ignf:lamb93")
    except Exception as exc:
        assert False, f"SpatialReference creation raises an exception: {exc}"


def test_srs_to_spatialreference_epsg_ok():
    try:
        sr = srs_to_spatialreference("EPSG:3857")
        sr = srs_to_spatialreference("epsg:3857")
    except Exception as exc:
        assert False, f"SpatialReference creation raises an exception: {exc}"


def test_srs_to_spatialreference_ignf_nok():
    with pytest.raises(Exception):
        sr = srs_to_spatialreference("IGNF:TOTO")


def test_srs_to_spatialreference_epsg_nok():
    with pytest.raises(Exception):
        sr = srs_to_spatialreference("EPSG:123456")


def test_bbox_to_geometry_ok():
    try:
        geom = bbox_to_geometry((0, 0, 5, 10))
        assert geom.Area() == 50
    except Exception as exc:
        assert False, f"Geometry creation from bbox raises an exception: {exc}"


def test_reproject_bbox_ok():
    try:
        bbox = reproject_bbox((-90, -180, 90, 180), "EPSG:4326", "EPSG:3857")
        assert bbox[0] == -20037508.342789244
        bbox = reproject_bbox((43, 3, 44, 4), "EPSG:4326", "IGNF:WGS84G")
        assert bbox[0] == 3
    except Exception as exc:
        assert False, f"Bbox reprojection raises an exception: {exc}"


def test_reproject_point_ok():
    try:
        sr_4326 = srs_to_spatialreference("EPSG:4326")
        sr_3857 = srs_to_spatialreference("EPSG:3857")
        sr_ignf = srs_to_spatialreference("IGNF:WGS84G")
        x, y = reproject_point((43, 3), sr_4326, sr_3857)

        assert math.isclose(x, 333958.4723798207, rel_tol=1e-5)
        assert math.isclose(y, 5311971.846945471, rel_tol=1e-5)

        x, y = reproject_point((43, 3), sr_4326, sr_ignf)
        assert (x, y) == (3, 43)

        bbox = reproject_bbox((43, 3, 44, 4), "EPSG:4326", "IGNF:WGS84G")
        assert bbox[0] == 3
    except Exception as exc:
        assert False, f"Bbox reprojection raises an exception: {exc}"


# Tests for the rok4.Utils.compute_bbox function.


def test_compute_bbox_epsg_3857_ok():
    try:
        mocked_datasource = MagicMock(gdal.Dataset)
        random.seed()

        image_size = (random.randint(1, 1000), random.randint(1, 1000))
        mocked_datasource.RasterXSize = image_size[0]
        mocked_datasource.RasterYSize = image_size[1]

        transform_tuple = (
            random.uniform(-10000000.0, 10000000.0),
            random.uniform(-10000, 10000),
            random.uniform(-10000, 10000),
            random.uniform(-10000000.0, 10000000.0),
            random.uniform(-10000, 10000),
            random.uniform(-10000, 10000),
        )
        mocked_datasource.GetGeoTransform = Mock(return_value=transform_tuple)
        mocked_spatial_ref = MagicMock(osr.SpatialReference)
        mocked_spatial_ref.GetDataAxisToSRSAxisMapping = Mock(return_value=[1, 2])
        mocked_datasource.GetSpatialRef = Mock(return_value=mocked_spatial_ref)

        x_range = (
            transform_tuple[0],
            transform_tuple[0]
            + image_size[0] * transform_tuple[1]
            + image_size[1] * transform_tuple[2],
        )
        y_range = (
            transform_tuple[3],
            transform_tuple[3]
            + image_size[0] * transform_tuple[4]
            + image_size[1] * transform_tuple[5],
        )

        expected = (min(x_range), min(y_range), max(x_range), max(y_range))
        result = compute_bbox(mocked_datasource)
        assert math.isclose(result[0], expected[0], rel_tol=1e-5)
        assert math.isclose(result[1], expected[1], rel_tol=1e-5)
        assert math.isclose(result[2], expected[2], rel_tol=1e-5)
        assert math.isclose(result[3], expected[3], rel_tol=1e-5)
        mocked_datasource.GetSpatialRef.assert_called_once()
        mocked_spatial_ref.GetDataAxisToSRSAxisMapping.assert_called()
    except Exception as exc:
        assert False, f"Bbox computation raises an exception: {exc}"


def test_compute_bbox_epsg_4326_ok():
    try:
        mocked_datasource = MagicMock(gdal.Dataset)
        random.seed()

        image_size = (random.randint(1, 1000), random.randint(1, 1000))
        mocked_datasource.RasterXSize = image_size[0]
        mocked_datasource.RasterYSize = image_size[1]

        transform_tuple = (
            random.uniform(-10000000.0, 10000000.0),
            random.uniform(-10000, 10000),
            random.uniform(-10000, 10000),
            random.uniform(-10000000.0, 10000000.0),
            random.uniform(-10000, 10000),
            random.uniform(-10000, 10000),
        )
        mocked_datasource.GetGeoTransform = Mock(return_value=transform_tuple)
        mocked_spatial_ref = MagicMock(osr.SpatialReference)
        mocked_spatial_ref.GetDataAxisToSRSAxisMapping = Mock(return_value=[2, 1])
        mocked_datasource.GetSpatialRef = Mock(return_value=mocked_spatial_ref)

        x_range = (
            transform_tuple[0],
            transform_tuple[0]
            + image_size[0] * transform_tuple[1]
            + image_size[1] * transform_tuple[2],
        )
        y_range = (
            transform_tuple[3],
            transform_tuple[3]
            + image_size[0] * transform_tuple[4]
            + image_size[1] * transform_tuple[5],
        )

        expected = (min(y_range), min(x_range), max(y_range), max(x_range))
        result = compute_bbox(mocked_datasource)
        assert math.isclose(result[0], expected[0], rel_tol=1e-5)
        assert math.isclose(result[1], expected[1], rel_tol=1e-5)
        assert math.isclose(result[2], expected[2], rel_tol=1e-5)
        assert math.isclose(result[3], expected[3], rel_tol=1e-5)
        mocked_datasource.GetSpatialRef.assert_called_once()
        mocked_spatial_ref.GetDataAxisToSRSAxisMapping.assert_called()
    except Exception as exc:
        assert False, f"Bbox computation raises an exception: {exc}"


def test_compute_bbox_no_srs_ok():
    try:
        mocked_datasource = MagicMock(gdal.Dataset)
        random.seed()

        image_size = (random.randint(1, 1000), random.randint(1, 1000))
        mocked_datasource.RasterXSize = image_size[0]
        mocked_datasource.RasterYSize = image_size[1]

        transform_tuple = (
            random.uniform(-10000000.0, 10000000.0),
            random.uniform(-10000, 10000),
            random.uniform(-10000, 10000),
            random.uniform(-10000000.0, 10000000.0),
            random.uniform(-10000, 10000),
            random.uniform(-10000, 10000),
        )
        mocked_datasource.GetGeoTransform = Mock(return_value=transform_tuple)
        mocked_datasource.GetSpatialRef = Mock(return_value=None)

        x_range = (
            transform_tuple[0],
            transform_tuple[0]
            + image_size[0] * transform_tuple[1]
            + image_size[1] * transform_tuple[2],
        )
        y_range = (
            transform_tuple[3],
            transform_tuple[3]
            + image_size[0] * transform_tuple[4]
            + image_size[1] * transform_tuple[5],
        )

        expected = (min(x_range), min(y_range), max(x_range), max(y_range))
        result = compute_bbox(mocked_datasource)
        assert math.isclose(result[0], expected[0], rel_tol=1e-5)
        assert math.isclose(result[1], expected[1], rel_tol=1e-5)
        assert math.isclose(result[2], expected[2], rel_tol=1e-5)
        assert math.isclose(result[3], expected[3], rel_tol=1e-5)
        mocked_datasource.GetSpatialRef.assert_called_once()
    except Exception as exc:
        assert False, f"Bbox computation raises an exception: {exc}"


# Tests for the rok4.Utils.compute_format function.


@mock.patch("rok4.Utils.gdal.Info")
@mock.patch("rok4.Utils.gdal.GetColorInterpretationName", return_value="Palette")
@mock.patch("rok4.Utils.gdal.GetDataTypeSize", return_value=8)
@mock.patch("rok4.Utils.gdal.GetDataTypeName", return_value="Byte")
def test_compute_format_bit_ok(
    mocked_GetDataTypeName, mocked_GetDataTypeSize, mocked_GetColorInterpretationName, mocked_Info
):
    try:
        mocked_datasource = MagicMock(gdal.Dataset)

        mocked_datasource.RasterCount = 1
        mocked_Info.return_value = """Driver: GTiff/GeoTIFF
Size is 10000, 10000
Image Structure Metadata:
  COMPRESSION=PACKBITS
  INTERLEAVE=BAND
  MINISWHITE=YES
"""

        result = compute_format(mocked_datasource)
        assert result == ColorFormat.BIT
        mocked_GetDataTypeName.assert_called()
        mocked_GetDataTypeSize.assert_called()
        mocked_GetColorInterpretationName.assert_called()
        mocked_Info.assert_called()
    except Exception as exc:
        assert False, f"Color format computation raises an exception: {exc}"


@mock.patch("rok4.Utils.gdal.Info")
@mock.patch("rok4.Utils.gdal.GetColorInterpretationName")
@mock.patch("rok4.Utils.gdal.GetDataTypeSize", return_value=8)
@mock.patch("rok4.Utils.gdal.GetDataTypeName", return_value="Byte")
def test_compute_format_uint8_ok(
    mocked_GetDataTypeName, mocked_GetDataTypeSize, mocked_GetColorInterpretationName, mocked_Info
):
    try:
        mocked_datasource = MagicMock(gdal.Dataset)

        band_number = random.randint(1, 4)
        mocked_datasource.RasterCount = band_number
        band_name = None
        if band_number == 1 or band_number == 2:
            band_name = "Gray"
        elif band_number == 3 or band_number == 4:
            band_name = "Red"
        mocked_GetColorInterpretationName.return_value = band_name
        mocked_Info.return_value = """Driver: GTiff/GeoTIFF
Size is 10000, 10000
Metadata:
  AREA_OR_POINT=Area
Image Structure Metadata:
  INTERLEAVE=BAND
"""

        result = compute_format(mocked_datasource)

        assert result == ColorFormat.UINT8
        mocked_GetDataTypeName.assert_called()
        mocked_GetDataTypeSize.assert_called()
        mocked_GetColorInterpretationName.assert_called()
        mocked_Info.assert_called()
    except Exception as exc:
        assert False, f"Color format computation raises an exception: {exc}"


@mock.patch("rok4.Utils.gdal.Info")
@mock.patch("rok4.Utils.gdal.GetColorInterpretationName")
@mock.patch("rok4.Utils.gdal.GetDataTypeSize", return_value=32)
@mock.patch("rok4.Utils.gdal.GetDataTypeName", return_value="Float32")
def test_compute_format_float32_ok(
    mocked_GetDataTypeName, mocked_GetDataTypeSize, mocked_GetColorInterpretationName, mocked_Info
):
    try:
        mocked_datasource = MagicMock(gdal.Dataset)

        band_number = random.randint(1, 4)
        mocked_datasource.RasterCount = band_number
        band_name = None
        if band_number == 1 or band_number == 2:
            band_name = "Gray"
        elif band_number == 3 or band_number == 4:
            band_name = "Red"
        mocked_GetColorInterpretationName.return_value = band_name
        mocked_Info.return_value = """Driver: GTiff/GeoTIFF
Size is 10000, 10000
Metadata:
  AREA_OR_POINT=Area
Image Structure Metadata:
  INTERLEAVE=BAND
"""

        result = compute_format(mocked_datasource)

        assert result == ColorFormat.FLOAT32
        mocked_GetDataTypeName.assert_called()
        mocked_GetDataTypeSize.assert_called()
        mocked_GetColorInterpretationName.assert_called()
        mocked_Info.assert_called()
    except Exception as exc:
        assert False, f"Color format computation raises an exception: {exc}"


@mock.patch("rok4.Utils.gdal.Info")
@mock.patch("rok4.Utils.gdal.GetColorInterpretationName")
@mock.patch("rok4.Utils.gdal.GetDataTypeSize", return_value=16)
@mock.patch("rok4.Utils.gdal.GetDataTypeName", return_value="UInt16")
def test_compute_format_unsupported_nok(
    mocked_GetDataTypeName, mocked_GetDataTypeSize, mocked_GetColorInterpretationName, mocked_Info
):
    try:
        mocked_datasource = MagicMock(gdal.Dataset)

        band_number = random.randint(1, 4)
        mocked_datasource.RasterCount = band_number
        band_name = None
        if band_number == 1 or band_number == 2:
            band_name = "Gray"
        elif band_number == 3 or band_number == 4:
            band_name = "Red"
        mocked_GetColorInterpretationName.return_value = band_name
        mocked_Info.return_value = """Driver: GTiff/GeoTIFF
Size is 10000, 10000
Metadata:
  AREA_OR_POINT=Area
Image Structure Metadata:
  INTERLEAVE=BAND
"""

        with pytest.raises(Exception):
            compute_format(mocked_datasource)

        mocked_GetDataTypeName.assert_called()
        mocked_GetDataTypeSize.assert_called()
        mocked_GetColorInterpretationName.assert_called()
        mocked_Info.assert_called()
    except Exception as exc:
        assert False, f"Color format computation raises an exception: {exc}"


@mock.patch("rok4.Utils.gdal.Info")
@mock.patch("rok4.Utils.gdal.GetColorInterpretationName")
@mock.patch("rok4.Utils.gdal.GetDataTypeSize", return_value=16)
@mock.patch("rok4.Utils.gdal.GetDataTypeName", return_value="UInt16")
def test_compute_format_no_band_nok(
    mocked_GetDataTypeName, mocked_GetDataTypeSize, mocked_GetColorInterpretationName, mocked_Info
):
    try:
        mocked_datasource = MagicMock(gdal.Dataset)

        mocked_datasource.RasterCount = 0

        with pytest.raises(Exception):
            compute_format(mocked_datasource)

        mocked_GetDataTypeName.assert_not_called()
        mocked_GetDataTypeSize.assert_not_called()
        mocked_GetColorInterpretationName.assert_not_called()
        mocked_Info.assert_not_called()
    except Exception as exc:
        assert False, f"Color format computation raises an exception: {exc}"
