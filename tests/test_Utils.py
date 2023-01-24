from rok4.Utils import *
from rok4.Exceptions import *

import pytest
import os

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
    except Exception as exc:
        assert False, f"Bbox reprojection raises an exception: {exc}"
