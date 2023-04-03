from rok4.Utils import *
from rok4.Exceptions import *

import pytest
import os
import math

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
        geom = bbox_to_geometry((0,0,5,10))
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
        x,y = reproject_point((43, 3), sr_4326, sr_3857)

        assert math.isclose(x, 333958.4723798207, rel_tol=1e-5)
        assert math.isclose(y, 5311971.846945471, rel_tol=1e-5)

        x,y = reproject_point((43, 3), sr_4326, sr_ignf)
        assert (x,y) == (3, 43)

        bbox = reproject_bbox((43, 3, 44, 4), "EPSG:4326", "IGNF:WGS84G")
        assert bbox[0] == 3
    except Exception as exc:
        assert False, f"Bbox reprojection raises an exception: {exc}"
