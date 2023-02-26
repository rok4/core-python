#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 18 12:04:07 2023

@author: cpeutin
"""
from rok4.Vector import Vector
from rok4.Exceptions import *
from rok4.Storage import disconnect_ceph_clients

import pytest
import os
from unittest.mock import *
from unittest import mock


@mock.patch.dict(os.environ, {}, clear=True)
def test_missing_env():
    disconnect_ceph_clients()
    with pytest.raises(MissingEnvironmentError):
        vector = Vector("ceph:///ign_std/vector.shp")

@mock.patch('rok4.Vector.copy', side_effect=StorageError('FILE', 'Not found'))
def test_wrong_file(mocked_copy):
    with pytest.raises(StorageError):
        vector = Vector("file:///vector.shp")

@mock.patch('rok4.Vector.get_data_str', return_value="x1;y1\n no_coor;no_coor")
def test_wrong_column_point1(mocked_get_data_str):
    with pytest.raises(Exception) as exc:
        vector = Vector("file:///vector.csv" , ";", "x", "y")
    assert str(exc.value) == "x is not a column of the CSV"
    mocked_get_data_str.assert_called_once_with("file:///vector.csv")

@mock.patch('rok4.Vector.get_data_str', return_value="x;y1\n no_coor;no_coor")
def test_wrong_column_point2(mocked_get_data_str):
    with pytest.raises(Exception) as exc:
        vector = Vector("file:///vector.csv" , ";", "x", "y")
    assert str(exc.value) == "y is not a column of the CSV"
    mocked_get_data_str.assert_called_once_with("file:///vector.csv")

@mock.patch('rok4.Vector.get_data_str', return_value="x;y\n no_coor;no_coor")
def test_wrong_data_column_point(mocked_get_data_str):
    with pytest.raises(Exception) as exc:
        vector = Vector("file:///vector.csv" , ";", "x", "y")
    assert str(exc.value) == "x or y contains data which are not coordinates"
    mocked_get_data_str.assert_called_once_with("file:///vector.csv")

@mock.patch('rok4.Vector.get_data_str', return_value="WKT\n no_coor")
def test_wrong_data_column_WKT(mocked_get_data_str):
    with pytest.raises(Exception) as exc:
        vector = Vector("file:///vector.csv" , ";", column_WKT="WKT")
    assert str(exc.value) == "WKT contains data which are not WKT"
    mocked_get_data_str.assert_called_once_with("file:///vector.csv")

def test_wrong_format():
    with pytest.raises(Exception) as exc:
        vector = Vector("file:///vector.tif")
    assert str(exc.value) == "This format of file cannot be loaded"

@mock.patch('rok4.Vector.copy')
@mock.patch('rok4.Vector.ogr.Open', return_value="not a shape")
def test_wrong_content(mocked_open, mocked_copy):
    with pytest.raises(Exception) as exc:
        vector = Vector("file:///vector.shp")
    assert str(exc.value) == "The content of file:///vector.shp cannot be read"

@mock.patch('rok4.Vector.get_data_str', return_value="id;x;y\n 1;20000;50000")
def test_ok_csv1(mocked_get_data_str) :
    try :
        vector_csv1 = Vector("file:///vector.csv" , ";", "x", "y")
        assert str(vector_csv1.layers) == "[('vector', 1, [('id', 'String'), ('x', 'String'), ('y', 'String')])]"
        mocked_get_data_str.assert_called_once_with("file:///vector.csv")
    except Exception as exc:
        assert False, f"Vector creation raises an exception: {exc}"

@mock.patch('rok4.Vector.get_data_str', return_value="id;WKT\n 1;POINT(1 1)")
def test_ok_csv2(mocked_get_data_str) :
    try :
        vector_csv2 = Vector("file:///vector.csv" , ";", column_WKT="WKT")
        assert str(vector_csv2.layers) == "[('vector', 1, [('id', 'String'), ('WKT', 'String')])]"
        mocked_get_data_str.assert_called_once_with("file:///vector.csv")
    except Exception as exc:
        assert False, f"Vector creation raises an exception: {exc}"

def test_ok_geojson() :
    try :
        vector = Vector("file://tests/fixtures/vector.geojson")
        assert str(vector.layers) == "[('vector', 1, [('id', 'String'), ('id_fantoir', 'String'), ('numero', 'Integer'), ('rep', 'String'), ('nom_voie', 'String'), ('code_postal', 'Integer'), ('code_insee', 'Integer'), ('nom_commune', 'String'), ('code_insee_ancienne_commune', 'String'), ('nom_ancienne_commune', 'String'), ('x', 'Real'), ('y', 'Real'), ('lon', 'Real'), ('lat', 'Real'), ('type_position', 'String'), ('alias', 'String'), ('nom_ld', 'String'), ('libelle_acheminement', 'String'), ('nom_afnor', 'String'), ('source_position', 'String'), ('source_nom_voie', 'String'), ('certification_commune', 'Integer'), ('cad_parcelles', 'String')])]"
    except Exception as exc:
        assert False, f"Vector creation raises an exception: {exc}"

def test_ok_gpkg() :
    try :
        vector = Vector("file://tests/fixtures/vector.gpkg")
        assert str(vector.layers) == "[('Table1', 2, [('id', 'String')]), ('Table2', 2, [('id', 'Integer'), ('nom', 'String')])]"
    except Exception as exc:
        assert False, f"Vector creation raises an exception: {exc}"

def test_ok_shp() :
    try :
        vector = Vector("file://tests/fixtures/ARRONDISSEMENT.shp")
        assert str(vector.layers) == "[('ARRONDISSEMENT', 14, [('ID', 'String'), ('NOM', 'String'), ('INSEE_ARR', 'String'), ('INSEE_DEP', 'String'), ('INSEE_REG', 'String'), ('ID_AUT_ADM', 'String'), ('DATE_CREAT', 'String'), ('DATE_MAJ', 'String'), ('DATE_APP', 'Date'), ('DATE_CONF', 'Date')])]"
    except Exception as exc:
        assert False, f"Vector creation raises an exception: {exc}"
