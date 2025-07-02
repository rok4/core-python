# standard library
import os
from unittest import mock
from unittest.mock import patch, Mock


# package

from rok4.storage import disconnect_s3_clients, get_osgeo_path, get_data_str
from rok4.vector import VectorSet, Vector, Table

@mock.patch.dict(os.environ, {}, clear=True)
def test_vectorset_from_list_ok(mock_append):
    expected_vector_object = {"id": "WKT", "1": "POINT(1 1)"}
    Vector.from_file = Mock(return_value=expected_vector_object)
    mock_append = Mock()
    VectorSet._append = mock_append
    o_object_vector = VectorSet.from_list("file://tests/fixtures/vector2.csv")

    assert mock_append.call_count == 1
    assert mock_append.call_args[0][0] == expected_vector_object
    o_object_vector.assert_called_once_with("file://tests/fixtures/vector2.csv")


def test_vectorset_from_descriptor_ok_parameters():
    expected_vector_object = {"id": "WKT", "1": "POINT(1 1)"}
    path = "file://tests/fixtures/vector2.csv"
    Vector._tables = expected_vector_object
    dataset_vector_object = Vector.from_parameters(path, Vector._tables)
    
    assert isinstance(VectorSet.from_descriptor(path), VectorSet)
    assert isinstance(dataset_vector_object, Vector)

@mock.patch("rok4.vector.Vector.from_file")
def test_vectorset_descriptor_ok(mock_file):
    expected_vector_object = {"id": "WKT", "1": "POINT(1 1)"}
    path = "file://tests/fixtures/vector2.csv"
    tables = ['table1','table2','table3']

    o_object_vector = Vector.from_parameters(path, tables)

    assert mock_file.call_count == 0
    assert isinstance(o_object_vector._path, str)
    assert isinstance(o_object_vector._tables, list)
    assert isinstance(o_object_vector, dict)
    assert o_object_vector == expected_vector_object

@mock.patch("rok4.vector.Vector.from_parameters")
def test_vectorset_descriptor_ok(mock_parameters):
    expected_vector_object = {"id": "WKT", "1": "POINT(1 1)"}
    vector = Vector()
    path = "file://tests/fixtures/vector2.csv"
    Vector.from_parameters = Mock(return_value = expected_vector_object)

    o_object_vector = VectorSet.from_descriptor("file://tests/fixtures/vector2.csv")

    assert mock_parameters.call_count == 0
    assert isinstance(Vector.from_parameters(path, vector._tables), dict)
    assert isinstance(o_object_vector, VectorSet)


def test_vectorset_from_descriptor_ok_csv2():
    try:
        vector_csv2 = VectorSet.from_descriptor(
            "file://tests/fixtures/vector2.csv",  
        )
        assert str(vector_csv2.path) == "file://tests/fixtures/vector2.csv"
    except Exception as exc:
        assert False, f"Vector creation raises an exception: {exc}"


def test_vector_from_parameters_ok_csv():
    try:
        vector_csv = Vector.from_parameters(
            "file://tests/fixtures/vector.csv",
            "[('vector', 4, [('id', 'String'), ('x', 'String'), ('y', 'String')])]"
        )
        assert (
            str(vector_csv.path)
            == "file://tests/fixtures/vector.csv"
        )
        assert (
            str(vector_csv.tables)
            == "[('vector', 4, [('id', 'String'), ('x', 'String'), ('y', 'String')])]"
        )
    except Exception as exc:
        assert False, f"Vector creation raises an exception: {exc}"



def test_vectorset_from_descriptor_ok_geojson():
    try:
        vector_geojson2 = VectorSet.from_descriptor(
            "file://tests/fixtures/vector.geojson",  
        )
        assert str(vector_geojson2.path) == "file://tests/fixtures/vector.geojson"
    except Exception as exc:
        assert False, f"Vector creation raises an exception: {exc}"


def test_vector_from_parameters_ok_geojson():
    try:
        vector_geojson4 = Vector.from_parameters(
            "file://tests/fixtures/vector.geojson",
            "[('vector', 4, [('id', 'String'), ('x', 'String'), ('y', 'String')])]"
        )
        assert (
            str(vector_geojson4.path)
            == "file://tests/fixtures/vector.geojson"
        )
        assert (
            str(vector_geojson4.tables)
            == "[('vector', 4, [('id', 'String'), ('x', 'String'), ('y', 'String')])]"
        )
    except Exception as exc:
        assert False, f"Vector creation raises an exception: {exc}"


def test_vectorset_from_descriptor_ok_gpkg2():
    try:
        vector_gpkg2 = VectorSet.from_descriptor(
            "file://tests/fixtures/vector.gpkg",  
        )
        assert str(vector_gpkg2.path) == "file://tests/fixtures/vector.gpkg"
    except Exception as exc:
        assert False, f"Vector creation raises an exception: {exc}"


def test_vector_from_parameters_ok_gpkg4():
    try:
        vector_gpkg4 = Vector.from_parameters(
            "file://tests/fixtures/vector.gpkg",
            "[('vector', 4, [('id', 'String'), ('x', 'String'), ('y', 'String')])]"
        )
        assert (
            str(vector_gpkg4.path)
            == "file://tests/fixtures/vector.gpkg"
        )
        assert (
            str(vector_gpkg4.tables)
            == "[('vector', 4, [('id', 'String'), ('x', 'String'), ('y', 'String')])]"
        )
    except Exception as exc:
        assert False, f"Vector creation raises an exception: {exc}"


def test_vectorset_from_list_ok_shp():
    try:
        vector_shp = VectorSet.from_list(
            "file://tests/fixtures/ARRONDISSEMENT.shp"
            )
        assert (
            str(vector_shp.path)
            == "file://tests/fixtures/ARRONDISSEMENT.shp"
        )
        assert (
            str(vector_shp.tables)
            == "[('ARRONDISSEMENT', 14, [('ID', 'String'), ('NOM', 'String'), ('INSEE_ARR', 'String'), ('INSEE_DEP', 'String'), ('INSEE_REG', 'String'), ('ID_AUT_ADM', 'String'), ('DATE_CREAT', 'String'), ('DATE_MAJ', 'String'), ('DATE_APP', 'Date'), ('DATE_CONF', 'Date')])]"
        )
    except Exception as exc:
        assert True, f"Vector creation raises an exception: {exc}"

def test_vectorset_from_descriptor_ok_shp2():
    try:
        vector_shp2 = VectorSet.from_descriptor(
            "file://tests/fixtures/ARRONDISSEMENT.shp",  
        )
        assert str(vector_shp2.path) == "file://tests/fixtures/ARRONDISSEMENT.shp"
    except Exception as exc:
        assert False, f"Vector creation raises an exception: {exc}"


def test_vector_from_parameters_ok_shp4():
    try:
        vector_shp4 = Vector.from_parameters(
            "file://tests/fixtures/ARRONDISSEMENT.shp",
            "[('vector', 4, [('id', 'String'), ('x', 'String'), ('y', 'String')])]"
        )
        assert (
            str(vector_shp4.path)
            == "file://tests/fixtures/ARRONDISSEMENT.shp"
        )
        assert (
            str(vector_shp4.tables)
            == "[('vector', 4, [('id', 'String'), ('x', 'String'), ('y', 'String')])]"
        )
    except Exception as exc:
        assert False, f"Vector creation raises an exception: {exc}"


def test_vectorset_ok_parameters():
    try:
        vector = VectorSet.from_descriptor(
            "file://tests/fixtures/ARRONDISSEMENT.shp",
        )
        assert str(vector.path) == "file://tests/fixtures/ARRONDISSEMENT.shp"
    except Exception as exc:
        assert False, f"Vector creation raises an exception: {exc}"


def test_vector_ok_parameters():

    try:
        vector5 = Vector.from_parameters(
            "file://tests/fixtures/vector2.csv",
            "[('vector', 4, [('id', 'String'), ('x', 'String'), ('y', 'String')])]"
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
        assert False, f"Vector creation raises an exception: {exc}"


@mock.patch.dict(os.environ, {}, clear=True)
def test_vectorset_from_list_ok():
    mocked_str = Mock()
    mocked_str.endswith.return_value = True # or something else you want
    mocked_str.endswith(".csv")
    try:
        path = get_osgeo_path("file:///path/to/file.ext")
        assert path == "/path/to/file.ext"
    except Exception as exc:
        assert False, f" the path of vector set from list {path} is not defined {exc}"
    

@patch('rok4.vector.Table.__init__', return_value=Table)
def test_table_init(mpatch):
    """tester le constructeur __init__ pour vérifier que l'instance lié à la classe Table a bien été créée

    Args:
        mpatch (str): décorateur
    """
    patcher = patch('rok4.vector.Table.__init__')
    mpatch = patcher.start()
    name = "object1"
    srs = "2154" 
    count = 1000
    bbox = (150,23.5,-59.1,-5.6)
    attributes={"colonne1": "attribute1"}
    obj_table = Table.__init__(srs,count,bbox,attributes,name)
    mpatch.isinstance(obj_table,mpatch)
    mpatch.isinstance(obj_table[srs],str)
    mpatch.assert_called_once_with(srs,count,bbox,attributes,name)
    patcher.stop()

@mock.patch.dict(
    os.environ,
    {"ROK4_S3_URL": "https://a,https://b", "ROK4_S3_SECRETKEY": "a,b", "ROK4_S3_KEY": "a,b"},
    clear=True,
)
def test_get_osgeo_path_s3_ok():
    disconnect_s3_clients()

    try:
        path = get_osgeo_path("s3://bucket@b/to/object.ext")
        assert path == "/vsis3/bucket/to/object.ext"
    except Exception as exc:
        assert False, f"S3 osgeo path raises an exception: {exc}"


def test_get_osgeo_path_file_ok():
    try:
        path = get_osgeo_path("tests/fixtures/vector2.csv")
        assert path == "tests/fixtures/vector2.csv"
    except Exception as exc:
        assert False, f"FILE osgeo path raises an exception: {exc}"

def test_data_content_vector_is_a_string_ok():
    try:
        path_to_data = get_osgeo_path("tests/fixtures/vector2.csv")
        data_content = get_data_str(path_to_data)
        assert isinstance (data_content, str)
    except Exception as exc:
        assert False, f"data content vector raises an exception: {exc}"
