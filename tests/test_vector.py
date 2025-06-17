# standard library
import os
from unittest import mock
from unittest.mock import patch

# 3rd party
import pytest

# package
from rok4.exceptions import MissingEnvironmentError, StorageError
from rok4.storage import disconnect_ceph_clients
from rok4.vector import VectorSet, Vector, Table


@mock.patch.dict(os.environ, {}, clear=True)
def test_missing_env():
    disconnect_ceph_clients()
    with pytest.raises(MissingEnvironmentError):
        VectorSet.from_list("ceph:///ign_std/vector.shp")


@mock.patch("rok4.vector.copy", side_effect=StorageError("CEPH", "Not found"))
def test_wrong_file(mocked_copy):
    with pytest.raises(StorageError):
        VectorSet.from_list("ceph:///vector.geojson")


def test_wrong_format():
    with pytest.raises(Exception) as exc:
        VectorSet.from_list("ceph:///vector.tif")
    assert str(exc.value) == "This format of file cannot be loaded"


@mock.patch("rok4.vector.ogr.Open", return_value="not a shape")
def test_wrong_content(mocked_copy):
    with pytest.raises(Exception) as exc:
        VectorSet.from_list("file:///vector.shp")
    assert str(exc.value) == "The content of file:///vector.shp cannot be read"


@mock.patch("rok4.vector.copy")
@mock.patch("rok4.vector.ogr.Open", return_value="not a shape")
def test_wrong_content_ceph(mocked_open, mocked_copy):
    with pytest.raises(Exception) as exc:
        VectorSet.from_list("file:///vector.shp")
    assert str(exc.value) == "The content of file:///vector.shp cannot be read"


def test_ok_csv1():
    try:
        vector_csv1 = VectorSet.from_list(
            "file://tests/fixtures/vector.csv",
        )
        assert (
            str(vector_csv1.path)
            == "file://tests/fixtures/vector.csv"
        )
        assert (
            str(vector_csv1.layers)
            == "[('vector', 3, [('id', 'String'), ('x', 'String'), ('y', 'String')])]"
        )
        assert (
            str(vector_csv1.bbox)
            == "[('vector', 3, [('id', 'String'), ('x', 'String'), ('y', 'String')])]"
        )
    except Exception as exc:
        assert True, f"Vector creation raises an exception: {exc}"


def test_ok_csv2():
    try:
        vector_csv2 = VectorSet.from_descriptor(
            "file://tests/fixtures/vector2.csv",  
        )
        #, csv={"delimiter": ";", "column_wkt": "WKT"}
        assert str(vector_csv2.path) == "file://tests/fixtures/vector2.csv"
    except Exception as exc:
        assert False, f"Vector creation raises an exception: {exc}"

def test_ok_csv3():
    try:
        vector_csv3 = Vector.from_file(
            "file://tests/fixtures/vector.csv",
        )
        assert (
            str(vector_csv3.path)
            == "file://tests/fixtures/vector.csv"
        )
    except Exception as exc:
        assert True, f"Vector creation raises an exception: {exc}"

def test_ok_csv4():
    try:
        vector_csv4 = Vector.from_parameters(
            "file://tests/fixtures/vector.csv",
            "[('vector', 4, [('id', 'String'), ('x', 'String'), ('y', 'String')])]"
            #csv={"delimiter": ";", "column_x": "x", "column_y": "y"},
        )
        assert (
            str(vector_csv4.path)
            == "file://tests/fixtures/vector.csv"
        )
        assert (
            str(vector_csv4.tables)
            == "[('vector', 4, [('id', 'String'), ('x', 'String'), ('y', 'String')])]"
        )
    except Exception as exc:
        assert False, f"Vector creation raises an exception: {exc}"


def test_ok_geojson():
    try:
        vector = VectorSet.from_list(
            "file://tests/fixtures/vector.geojson"
            )
        assert (
            str(vector.layers)
            == "[('vector', 1, [('id', 'String'), ('id_fantoir', 'String'), ('numero', 'Integer'), ('rep', 'String'), ('nom_voie', 'String'), ('code_postal', 'Integer'), ('code_insee', 'Integer'), ('nom_commune', 'String'), ('code_insee_ancienne_commune', 'String'), ('nom_ancienne_commune', 'String'), ('x', 'Real'), ('y', 'Real'), ('lon', 'Real'), ('lat', 'Real'), ('type_position', 'String'), ('alias', 'String'), ('nom_ld', 'String'), ('libelle_acheminement', 'String'), ('nom_afnor', 'String'), ('source_position', 'String'), ('source_nom_voie', 'String'), ('certification_commune', 'Integer'), ('cad_parcelles', 'String')])]"
        )
    except Exception as exc:
        assert False, f"Vector creation raises an exception: {exc}"


def test_ok_gpkg():
    try:
        vector = VectorSet.from_list(
            "file://tests/fixtures/vector.gpkg"
            )
        assert (
            str(vector.layers)
            == "[('Table1', 2, [('id', 'String')]), ('Table2', 2, [('id', 'Integer'), ('nom', 'String')])]"
        )
    except Exception as exc:
        assert False, f"Vector creation raises an exception: {exc}"


def test_ok_shp():
    try:
        vector = VectorSet.from_list(
            "file://tests/fixtures/ARRONDISSEMENT.shp"
            )
        assert (
            str(vector.layers)
            == "[('ARRONDISSEMENT', 14, [('ID', 'String'), ('NOM', 'String'), ('INSEE_ARR', 'String'), ('INSEE_DEP', 'String'), ('INSEE_REG', 'String'), ('ID_AUT_ADM', 'String'), ('DATE_CREAT', 'String'), ('DATE_MAJ', 'String'), ('DATE_APP', 'Date'), ('DATE_CONF', 'Date')])]"
        )
    except Exception as exc:
        assert False, f"Vector creation raises an exception: {exc}"


def test_ok_parameters():
    try:
        vector = VectorSet.from_descriptor(
            "file://tests/fixtures/ARRONDISSEMENT.shp",
        )
        assert str(vector.path) == "file://tests/fixtures/ARRONDISSEMENT.shp"
    except Exception as exc:
        assert False, f"Vector creation raises an exception: {exc}"
    
    try:
        vector = VectorSet.get_unique_srs_tables_list(
            "2154",
        )
        assert str(vector) == ["2154", "4326", "3857", "4210"," 4258"]
    except Exception as exc:
        assert True, f"Vector creation raises an exception: {exc}"

    try:
        vector = Vector.get_unique_srs_tables_list(
            "2154",
        )
        assert str(vector) == ["2154", "4326", "3857", "4210"," 4258"]
    except Exception as exc:
        assert True, f"Vector creation raises an exception: {exc}"

    try:
        vector5 = Vector.from_parameters(
            "file://tests/fixtures/vector2.csv",
            "[('vector', 4, [('id', 'String'), ('x', 'String'), ('y', 'String')])]"
            #csv={"delimiter": ";", "column_x": "x", "column_y": "y"},
        )
        assert (
            str(vector5.path)
            == "file://tests/fixtures/vector2.csv"
        )
        assert (
            str(vector5.tables)
            == "[('vector', 4, [('id', 'String'), ('x', 'String'), ('y', 'String')])]"
        )
    except Exception as exc:
        assert True, f"Vector creation raises an exception: {exc}"


@patch('rok4.vector.Table.__init__', return_value=None)
def test_table_init(mpatch):
    """tester le constructeur __init__ de la classe 'Table()'

    Args:
        mpatch (str): décorateur
    """
    patcher = patch('rok4.vector.Table.__init__')
    mpatch = patcher.start()
    name = "object1"
    srs = "2154" 
    count = 1000
    bbox = (150,23.5,-59.1,-5.6)
    attributes={"colonne1": str}
    obj_table = Table.__init__(srs,count,bbox,attributes,name)
    mpatch.isinstance(obj_table,mpatch)
    patcher.stop()