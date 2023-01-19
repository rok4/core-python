#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 18 12:04:07 2023

@author: cpeutin
"""
from rok4.Vector import Vector
from rok4.Exceptions import *

import pytest
import os
from unittest.mock import *
from unittest import mock

@mock.patch.dict(os.environ, {}, clear=True)
def test_missing_env():
    with pytest.raises(MissingEnvironmentError):
        vector = Vector("ceph://vector.shp")

@mock.patch('rok4.Vector.copy', side_effect=StorageError('FILE', 'Not found'))
def test_wrong_file(mocked_copy):
    with pytest.raises(StorageError):
        vector = Vector("file:///vector.shp")

@mock.patch('rok4.Vector.get_data_str', return_value="column_1;column_2\n no_coor;no_coor")
def test_wrong_column_point(mocked_get_data_str):
    with pytest.raises(Exception):
        vector = Vector("file:///vector.csv" , ";", "x", "y")
    assert str(exc.value) == "'x' or 'y' contains data which are not coordinates"
    mocked_get_data_str.assert_called_once_with("file:///vector.shp")

@mock.patch('rok4.Vector.get_data_str', return_value="column_WKT\n no_coor")
def test_wrong_column_WKT(mocked_get_data_str):
    with pytest.raises(Exception):
        vector = Vector("file:///vector.csv" , ";", column_WKT="WKT")
    assert str(exc.value) == "'WKT' contains data which are not WKT"
    mocked_get_data_str.assert_called_once_with("file:///vector.shp")

def test_wrong_format():
    with pytest.raises(Exception):
        vector = Vector("file:///vector.tif")
    assert str(exc.value) == "This format of file cannot be loaded"

@mock.patch('rok4.Vector.copy', return_value="not a shape")
def test_wrong_content(mocked_copy):
    with pytest.raises(Exception):
        vector = Vector("file:///vector.shp")
    assert str(exc.value) == "The content of 'file:///vector.shp' cannot be read"
    mocked_copy.assert_called_once_with("file:///vector.shp")

@mock.patch('rok4.Vector.copy', return_value='{"type": "FeatureCollection","name": "Arrondissement","crs": { "type": "name", "properties": { "name": "urn:ogc:def:crs:EPSG::2154" } },"features": [{ "type": "Feature", "properties": { "ID": "ARRONDIS0000002150000279", "NOM": "Gex", "INSEE_ARR": "3", "INSEE_DEP": "01", "INSEE_REG": "84", "ID_AUT_ADM": "SURFACTI0000000008683448", "DATE_CREAT": "2018-11-24 00:00:00", "DATE_MAJ": "2019-02-13 14:32:06", "DATE_APP": null, "DATE_CONF": null }, "geometry": { "type": "Point", "coordinates": [923395, 6561814]}}]}')
@mock.patch('rok4.Vector.get_data_str', return_value="id;x;y\n 1;20000;50000")
def test_ok(mocked_copy, mocked_get_data_str) :
    try :
        vector = Vector("file:///vector.geojson")
        assert vector.layers is [('Arrondissement', 1, [('ID', 'String'), ('NOM', 'String'), ('INSEE_ARR', 'String'), ('INSEE_DEP', 'String'), ('INSEE_REG', 'String'), ('ID_AUT_ADM', 'String'), ('DATE_CREAT', 'DateTime'), ('DATE_MAJ', 'DateTime'), ('DATE_APP', 'String'), ('DATE_CONF', 'String')])]
        vector_csv1 = Vector("file:///vector.csv" , ";", "x", "y")
        assert vector_csv1.layers is [('vector', 1, [('id', 'String'), ('x', 'String'), ('y', 'String')])]
        mocked_copy.assert_called_once_with("file:///vector.geojson")
        mocked_copy.assert_called_once_with("file:///vector.csv")
    except Exception as exc:
        assert False, f"Vector creation raises an exception: {exc}"
