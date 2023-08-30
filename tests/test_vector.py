import os
from unittest import mock
from unittest.mock import *

import pytest

from rok4.exceptions import *
from rok4.storage import disconnect_ceph_clients
from rok4.vector import *


@mock.patch.dict(os.environ, {}, clear=True)
def test_missing_env():
    disconnect_ceph_clients()
    with pytest.raises(MissingEnvironmentError):
        vector = Vector.from_file("ceph:///ign_std/vector.shp")


@mock.patch("rok4.vector.copy", side_effect=StorageError("CEPH", "Not found"))
def test_wrong_file(mocked_copy):
    with pytest.raises(StorageError):
        vector = Vector.from_file("ceph:///vector.geojson")


def test_wrong_format():
    with pytest.raises(Exception) as exc:
        vector = Vector.from_file("ceph:///vector.tif")
    assert str(exc.value) == "This format of file cannot be loaded"


@mock.patch("rok4.vector.ogr.Open", return_value="not a shape")
def test_wrong_content(mocked_copy):
    with pytest.raises(Exception) as exc:
        vector = Vector.from_file("file:///vector.shp")
    assert str(exc.value) == "The content of file:///vector.shp cannot be read"


@mock.patch("rok4.vector.copy")
@mock.patch("rok4.vector.ogr.Open", return_value="not a shape")
def test_wrong_content_ceph(mocked_open, mocked_copy):
    with pytest.raises(Exception) as exc:
        vector = Vector.from_file("file:///vector.shp")
    assert str(exc.value) == "The content of file:///vector.shp cannot be read"


def test_ok_csv1():
    try:
        vector_csv1 = Vector.from_file(
            "file://tests/fixtures/vector.csv",
            csv={"delimiter": ";", "column_x": "x", "column_y": "y"},
        )
        assert (
            str(vector_csv1.layers)
            == "[('vector', 3, [('id', 'String'), ('x', 'String'), ('y', 'String')])]"
        )
    except Exception as exc:
        assert False, f"Vector creation raises an exception: {exc}"


def test_ok_csv2():
    try:
        vector_csv2 = Vector.from_file(
            "file://tests/fixtures/vector2.csv", csv={"delimiter": ";", "column_wkt": "WKT"}
        )
        assert str(vector_csv2.layers) == "[('vector2', 1, [('id', 'String'), ('WKT', 'String')])]"
    except Exception as exc:
        assert False, f"Vector creation raises an exception: {exc}"


def test_ok_geojson():
    try:
        vector = Vector.from_file("file://tests/fixtures/vector.geojson")
        assert (
            str(vector.layers)
            == "[('vector', 1, [('id', 'String'), ('id_fantoir', 'String'), ('numero', 'Integer'), ('rep', 'String'), ('nom_voie', 'String'), ('code_postal', 'Integer'), ('code_insee', 'Integer'), ('nom_commune', 'String'), ('code_insee_ancienne_commune', 'String'), ('nom_ancienne_commune', 'String'), ('x', 'Real'), ('y', 'Real'), ('lon', 'Real'), ('lat', 'Real'), ('type_position', 'String'), ('alias', 'String'), ('nom_ld', 'String'), ('libelle_acheminement', 'String'), ('nom_afnor', 'String'), ('source_position', 'String'), ('source_nom_voie', 'String'), ('certification_commune', 'Integer'), ('cad_parcelles', 'String')])]"
        )
    except Exception as exc:
        assert False, f"Vector creation raises an exception: {exc}"


def test_ok_gpkg():
    try:
        vector = Vector.from_file("file://tests/fixtures/vector.gpkg")
        assert (
            str(vector.layers)
            == "[('Table1', 2, [('id', 'String')]), ('Table2', 2, [('id', 'Integer'), ('nom', 'String')])]"
        )
    except Exception as exc:
        assert False, f"Vector creation raises an exception: {exc}"


def test_ok_shp():
    try:
        vector = Vector.from_file("file://tests/fixtures/ARRONDISSEMENT.shp")
        assert (
            str(vector.layers)
            == "[('ARRONDISSEMENT', 14, [('ID', 'String'), ('NOM', 'String'), ('INSEE_ARR', 'String'), ('INSEE_DEP', 'String'), ('INSEE_REG', 'String'), ('ID_AUT_ADM', 'String'), ('DATE_CREAT', 'String'), ('DATE_MAJ', 'String'), ('DATE_APP', 'Date'), ('DATE_CONF', 'Date')])]"
        )
    except Exception as exc:
        assert False, f"Vector creation raises an exception: {exc}"


def test_ok_parameters():
    try:
        vector = Vector.from_parameters(
            "file://tests/fixtures/ARRONDISSEMENT.shp",
            (1, 2, 3, 4),
            [
                (
                    "ARRONDISSEMENT",
                    14,
                    [
                        ("ID", "String"),
                        ("NOM", "String"),
                        ("INSEE_ARR", "String"),
                        ("INSEE_DEP", "String"),
                        ("INSEE_REG", "String"),
                        ("ID_AUT_ADM", "String"),
                        ("DATE_CREAT", "String"),
                        ("DATE_MAJ", "String"),
                        ("DATE_APP", "Date"),
                        ("DATE_CONF", "Date"),
                    ],
                )
            ],
        )
        assert str(vector.path) == "file://tests/fixtures/ARRONDISSEMENT.shp"
    except Exception as exc:
        assert False, f"Vector creation raises an exception: {exc}"
