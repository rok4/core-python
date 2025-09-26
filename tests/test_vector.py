#!/usr/bin/env python3
# NOM DU PROGRAMME : test_vector.py
# CONTEXTE : Ces librairies de core-python facilitent la manipulation d'entités du projet ROK4 comme
# les Tile Matrix Sets, les pyramides ou encore les couches, ainsi que la manipulation des stockages associés.
# BUT DU PROGRAMME : écrire les tests unitaires et les tests d'intégration pour le module de chargement des données
# vecteur 'vector.py'
# ENTREES : les classes 'VectorSet()', 'Vector()' et 'Table()' du module 'vector.py'

import builtins
import json

# standard library
import os
from json.decoder import JSONDecodeError
from pathlib import Path
from unittest.mock import Mock, mock_open, patch

# 3rd party
import pytest  # type: ignore

# local : autres librairies de rok4
from rok4.storage import get_osgeo_path

# import des classes de la librairie 'vector' de rok4 pour lesquelles on doit tester leurs fonctions
from rok4.vector import Table, Vector, VectorSet


def test_if_filelisttxt_exists() -> None:
    vectorset = VectorSet()
    pathtofilelist = "data/filelist.txt"
    with patch.object(Path, "exists", return_value=True) as mocked_path_exists:
        vectorset.from_list(pathtofilelist)
    mocked_path_exists.assert_not_called()


def test_if_filelisttxt_is_a_file() -> None:
    vectorset = VectorSet()
    pathtofilelist = "data/filelist.txt"
    with patch.object(Path, "is_file", return_value=True) as mocked_is_file:
        vectorset.from_list(pathtofilelist)
    mocked_is_file.assert_not_called()


def test_if_filelisttxt_is_readable() -> None:
    vectorset = VectorSet()
    pathtofilelist = "data/filelist.txt"
    file_txt_not_readable = "not_readable.txt"
    with patch("os.access", return_value=True) as mocked_is_readable:
        with pytest.raises(Exception):
            vectorset.from_list(file_txt_not_readable)
    mocked_is_readable.assert_not_called()
    assert os.access(pathtofilelist, os.R_OK)
    assert not os.access(file_txt_not_readable, os.R_OK)


def test_if_filelisttxt_not_exists_by_mocking_exists_function() -> None:
    vectorset = VectorSet()
    file_txt_not_exists = "not_exists.txt"
    with patch.object(Path, "exists", retun_value=False) as mocked_file_txt_not_exists:
        with pytest.raises(Exception):
            vectorset.from_list(file_txt_not_exists)
    mocked_file_txt_not_exists.assert_not_called()


@patch.dict(os.environ, {}, clear=True)
def test_filelistpath_is_ok_by_equals_assertion() -> None:
    """tester que la méthode 'get_osgeo_path()' de 'Storage()' a bien le chemin défini donnant accès
    au jeu de données vecteur"""
    try:
        path = get_osgeo_path("data/filelist.txt")
        assert path == "data/filelist.txt"
    except Exception as exc:
        assert False, f" the path of vector set from list {path} is not defined {exc}"


@patch.dict(os.environ, {}, clear=True)
def test_geojson_file_path_is_ok_by_equals_assertion() -> None:
    """tester que la méthode 'get_osgeo_path()' de 'Storage()' a bien le chemin défini donnant accès
    au jeu de données vecteur"""
    try:
        geojson_file_path = get_osgeo_path("data/states.geojson")
        assert geojson_file_path == "data/states.geojson"
    except Exception as exc:
        assert (
            False
        ), f" the path of vector geojson file from file {geojson_file_path} is not defined {exc}"


@patch.dict(os.environ, {}, clear=True)
def test_gpkg_file_path_is_ok_by_equals_assertion() -> None:
    """tester que la méthode 'get_osgeo_path()' de 'Storage()' a bien le chemin défini donnant accès
    au jeu de données vecteur"""
    try:
        gpkg_file_path = get_osgeo_path("data/martinique.gpkg")
        assert gpkg_file_path == "data/martinique.gpkg"
    except Exception as exc:
        assert (
            False
        ), f" the path of vector geopackage file from file {gpkg_file_path} is not defined {exc}"


@patch.dict(os.environ, {}, clear=True)
def test_shp_file_path_is_ok_by_equals_assertion() -> None:
    """tester que la méthode 'get_osgeo_path()' de 'Storage()' a bien le chemin défini donnant accès
    au jeu de données vecteur"""
    try:
        shp_file_path = get_osgeo_path("data/TM_WORLD_BORDERS-0.3.shp")
        assert shp_file_path == "data/TM_WORLD_BORDERS-0.3.shp"
    except Exception as exc:
        assert (
            False
        ), f" the path of vector shapefile from file {shp_file_path} is not defined {exc}"


@patch.dict(
    os.environ,
    {"ROK4_S3_URL": "https://a,https://b", "ROK4_S3_SECRETKEY": "a,b", "ROK4_S3_KEY": "a,b"},
    clear=True,
)
def test_get_osgeo_path_for_s3_vector_object_is_ok() -> None:
    """tester que la méthode 'get_osgeo_path()' récupère bien le chemin donnant l'accès
    à l'objet vecteur du bucket S3'
    """
    try:
        path = get_osgeo_path("s3://bucket@b/to/object.ext")
        assert path == "/vsis3/bucket/to/object.ext"
    except Exception as exc:
        assert False, f"S3 osgeo path raises an exception: {exc}"


@patch("builtins.open", new_callable=mock_open, read_data="fake.geojson")
def test_by_mocking_open_function_with_a_not_valid_geojson(mocked_file_geojson_not_valid) -> None:
    vectorset = VectorSet()
    assert open("path/to/open").read() == "fake.geojson"
    with pytest.raises(Exception):
        vectorset.from_list(mocked_file_geojson_not_valid)
    mocked_file_geojson_not_valid.assert_called()


@patch("builtins.open", new_callable=mock_open, read_data="fake.gpkg")
def test_by_mocking_open_function_with_a_not_valid_gpkg(mocked_file_gpkg_not_valid) -> None:
    vectorset = VectorSet()
    assert open("path/to/open").read() == "fake.gpkg"
    with pytest.raises(Exception):
        vectorset.from_list(mocked_file_gpkg_not_valid)
    mocked_file_gpkg_not_valid.assert_called()


@patch("builtins.open", new_callable=mock_open, read_data="fake.shp")
def test_by_mocking_open_function_with_a_not_valid_shp(mocked_file_shp_not_valid) -> None:
    vectorset = VectorSet()
    assert open("path/to/open").read() == "fake.shp"
    with pytest.raises(Exception):
        vectorset.from_list(mocked_file_shp_not_valid)
    mocked_file_shp_not_valid.assert_called()


@patch("builtins.open", new_callable=mock_open, read_data="fake.s3_vector_object")
def test_by_mocking_open_function_with_a_not_valid_vector_object(
    mocked_file_s3_vector_object_not_valid,
) -> None:
    vectorset = VectorSet()
    assert open("path/to/open").read() == "fake.s3_vector_object"
    with pytest.raises(Exception):
        vectorset.from_list(mocked_file_s3_vector_object_not_valid)
    mocked_file_s3_vector_object_not_valid.assert_called()


@patch.object(builtins, "open", new_callable=mock_open, read_data="data/states.geojson")
@patch.object(
    builtins, "open", new_callable=mock_open, read_data="data/TM_WORLD_BORDERS-0.3.shp"
)
@patch.object(builtins, "open", new_callable=mock_open, read_data="data/martinique.gpkg")
def test_reading_vector_files_by_mocking_open_function_all_parameters_ok(
    mocked_file_open_geojson, mocked_file_open_shp, mocked_file_open_gpkg
) -> None:
    output_geojson = mocked_file_open_geojson().read()
    mocked_file_open_geojson.assert_called_once_with()
    output_shp = mocked_file_open_shp().read()
    mocked_file_open_shp.assert_called_once_with()
    output_gpkg = mocked_file_open_gpkg().read()
    mocked_file_open_gpkg.assert_called_once_with()
    # Vérifier que le contenu lu n'est pas vide
    assert output_geojson != ""
    assert output_shp != ""
    assert output_gpkg != ""
    # Vérifier que le contenu lu est de type str
    assert isinstance(output_geojson, str)
    assert isinstance(output_shp, str)
    assert isinstance(output_gpkg, str)
    # Vérifier que le contenu lu est de type str
    assert all(isinstance(item, str) for item in output_geojson)
    assert all(isinstance(item, str) for item in output_shp)
    assert all(isinstance(item, str) for item in output_gpkg)
    # Vérifier que le contenu lu est de type str
    assert isinstance(output_geojson, str)
    assert isinstance(output_shp, str)
    assert isinstance(output_gpkg, str)
    # Vérifier que le contenu lu est égal à ["data/states.geojson","data/TM_WORLD_BORDERS-0.3.shp","data/martinique.gpkg"]
    expected_output = [
        "data/states.geojson",
        "data/TM_WORLD_BORDERS-0.3.shp",
        "data/martinique.gpkg",
    ]
    # Vérifier que le contenu lu est égal à expected_output
    assert output_geojson == expected_output[2]
    assert output_shp == expected_output[1]
    assert output_gpkg == expected_output[0]


@patch("builtins.open", new_callable=mock_open, read_data="data/filelist_not_valid.txt")
def test_if_listtxtpath_is_not_ok_by_mocking_open_function_with_a_not_valid_filelist(
    mocked_file,
) -> None:
    vectorset = VectorSet()
    with pytest.raises(Exception):
        vectorset.from_list(mocked_file)
        assert isinstance(vectorset.from_list(mocked_file), list)
        assert len(vectorset.from_list(mocked_file)) == 3
        assert all(isinstance(item, Vector) for item in vectorset.from_list(mocked_file))
    mocked_file.assert_not_called()


@patch("builtins.open", new_callable=mock_open, read_data="data/filelist.txt")
def test_if_filelist_txt_is_ok_by_mocking_open_function_with_a_valid_filelist(mocked_file) -> None:
    assert open("path/to/open").read() == "data/filelist.txt"
    mocked_file.assert_called_with("path/to/open")


def test_bad_json() -> None:
    vectorset = VectorSet()
    path_to_descriptor_file = "data/vectorset.json"
    bad_json = {
        "path": "my_path",
        "table": "my_table",
        "data": [
            {
                "type": "shp",
            },
            {
                "type": "object",
            },
        ],
    }
    with patch("json.loads", return_value=bad_json) as mocked_get_bad_json:
        with pytest.raises(Exception):
            output = vectorset.from_descriptor(path_to_descriptor_file)
            assert json.loads(path_to_descriptor_file) == output
    mocked_get_bad_json.assert_called()


def test_missing_vector_keys() -> None:
    vectorset = VectorSet()
    descriptor_file_with_missing_keys = [
        {
            "path": "file://./data/martinique.gpkg",
        }
    ]
    REQUIRED_VECTOR_KEYS = ["path", "tables"]
    with patch(
        "rok4.vector.VectorSet.from_descriptor",
        return_value="[{'path': 'file://./data/martinique.gpkg',}]",
    ) as mocked_missing_vector_keys:
        vectorset.from_descriptor(descriptor_file_with_missing_keys)
        assert "tables" not in descriptor_file_with_missing_keys
    mocked_missing_vector_keys.call_count == 2
    mocked_missing_vector_keys.call_args(REQUIRED_VECTOR_KEYS[0], REQUIRED_VECTOR_KEYS[1])


def test_if_descriptor_exists() -> None:
    vectorset = VectorSet()
    path = "data/vectorset.json"
    with patch.object(Path, "exists", return_value=True) as mocked_path_exists:
        vectorset.from_descriptor(path)
        assert isinstance(vectorset.from_descriptor(path), VectorSet)
    mocked_path_exists.assert_not_called()


def test_if_descriptor_is_a_file() -> None:
    vectorset = VectorSet()
    path = "data/vectorset.json"
    with patch.object(Path, "is_file", return_value=True) as mocked_is_file:
        vectorset.from_descriptor(path)
        assert isinstance(vectorset.from_descriptor(path), VectorSet)
    mocked_is_file.assert_not_called()


def test_if_descriptor_is_readable() -> None:
    vectorset = VectorSet()
    path = "data/vectorset.json"
    file_descriptor_not_readable = "descriptor_not_readable.json"
    with patch("os.access", return_value=True) as mocked_is_readable:
        with pytest.raises(Exception):
            vectorset.from_descriptor(file_descriptor_not_readable)
    mocked_is_readable.assert_not_called()
    assert os.access(path, os.R_OK)
    assert not os.access(file_descriptor_not_readable, os.R_OK)


@patch("json.loads", return_value=dict({"the_data": "This is fake data"}))
def test_descriptor_is_not_valid_with_a_fake_file_path(mocked_json_loads) -> None:
    vectorset = VectorSet()
    path_to_fake_descriptor = "/non_exists/fake_descriptor.json"
    mocked_json_loads.side_effect = json.loads(JSONDecodeError("JSON", path_to_fake_descriptor, 1))
    with pytest.raises(Exception):
        vectorset.from_descriptor(path_to_fake_descriptor)
    mocked_json_loads.assert_called_once()


@patch.object(
    VectorSet, "srs", return_value=["EPSG:4326", "EPSG:3857", "EPSG:4559"]
)
def test_by_mocking_get_uniq_srs_tables_list_the_result_is_ok(mocked_get_srs) -> None:
    vectorset = VectorSet()
    result = vectorset.srs()
    assert result == ["EPSG:4326", "EPSG:3857", "EPSG:4559"]
    mocked_get_srs.assert_called_once()



def test_vector_files_all_are_ok() -> None:
    """tester que les fichiers vecteurs (geojson, geopackage et shapefile) existent bien,
    sont bien des fichiers et sont bien lisibles
    """
    vectorset = VectorSet()
    # on teste pour le fichier *.geojson
    # si le fichier geojson existe bien
    pathtofilegeojson = "data/states.geojson"
    with patch.object(Path, "exists", return_value=True) as mocked_path_exists:
        with pytest.raises(Exception):
            vectorset.from_list(pathtofilegeojson)
    mocked_path_exists.assert_not_called()

    # si le fichier geojson est bien un fichier
    vectorset = VectorSet()
    with patch.object(Path, "is_file", return_value=True) as mocked_is_file:
        with pytest.raises(Exception):
            vectorset.from_list(pathtofilegeojson)
    mocked_is_file.assert_not_called()

    # si le fichier geojson est bien lisible
    vectorset = VectorSet()
    file_geojson_not_readable = "not_readable.geojson"
    with patch("os.access", return_value=True) as mocked_is_readable:
        with pytest.raises(Exception):
            vectorset.from_list(file_geojson_not_readable)
    mocked_is_readable.assert_not_called()
    assert os.access(pathtofilegeojson, os.R_OK)

    # on teste pour le fichier *.geopackage
    # si le fichier geopackage existe bien
    vectorset = VectorSet()
    pathtofilegeopackage = "data/martinique.gpkg"
    with patch.object(Path, "exists", return_value=True) as mocked_path_exists:
        with pytest.raises(Exception):
            vectorset.from_list(pathtofilegeopackage)
    mocked_path_exists.assert_not_called()

    # si le fichier geopackage est bien un fichier
    vectorset = VectorSet()
    with patch.object(Path, "is_file", return_value=True) as mocked_is_file:
        with pytest.raises(Exception):
            vectorset.from_list(pathtofilegeopackage)
    mocked_is_file.assert_not_called()

    # si le fichier geopackage est bien lisible
    vectorset = VectorSet()
    file_gpkg_not_readable = "not_readable.gpkg"
    with patch("os.access", return_value=True) as mocked_is_readable:
        with pytest.raises(Exception):
            vectorset.from_list(file_gpkg_not_readable)
    mocked_is_readable.assert_not_called()
    assert os.access(pathtofilegeopackage, os.R_OK)

    # on teste pour le fichier *.shapefile
    # si le fichier shapefile existe bien
    vectorset = VectorSet()
    pathtofileshapefile = "data/TM_WORLD_BORDERS-0.3.shp"
    with patch.object(Path, "exists", return_value=True) as mocked_path_exists:
        with pytest.raises(Exception):
            vectorset.from_list(pathtofileshapefile)
    mocked_path_exists.assert_not_called()

    # si c'est bien un fichier
    vectorset = VectorSet()
    with patch.object(Path, "is_file", return_value=True) as mocked_is_file:
        with pytest.raises(Exception):
            vectorset.from_list(pathtofileshapefile)
    mocked_is_file.assert_not_called()

    # si le fichier shapefile est bien lisible
    vectorset = VectorSet()
    file_shp_not_readable = "not_readable.shp"
    with patch("os.access", return_value=True) as mocked_is_readable:
        with pytest.raises(Exception):
            vectorset.from_list(file_shp_not_readable)
    mocked_is_readable.assert_not_called()
    assert os.access(pathtofileshapefile, os.R_OK)


def test_if_vectorset_get_an_uniq_srs_list_by_mocking_add_function() -> None:
    expected_srs_tables_list = ["EPSG:4326", "EPSG:3857", "EPSG:4559"]
    mocked_add = Mock(return_value=expected_srs_tables_list)
    mocked_add.patch(
        "VectorSet.srs",
        new_callable=mocked_add.PropertyMock,
        return_value=["EPSG:4326", "EPSG:3857", "EPSG:4559"],
    )
    assert mocked_add.return_value == expected_srs_tables_list
    mocked_add.call_count == 3


def test_if_vector_get_an_uniq_srs_list_by_mocking_add_function() -> None:
    expected_srs_tables_set = {"EPSG:4326"}
    mocked_add = Mock(return_value=expected_srs_tables_set)
    mocked_add.patch(
        "Vector.srs",
        new_callable=mocked_add.PropertyMock,
        return_value={"EPSG:4326"},
    )
    assert mocked_add.return_value == expected_srs_tables_set
    mocked_add.call_count == 1


@patch.object(
    VectorSet, "srs", return_value=["EPSG:4326", "EPSG:3857", "EPSG:4559"]
)
def test_vectorset_get_uniq_srs_tables_list_mocked(mocked_get_srs) -> None:
    vectorset = VectorSet()
    result = vectorset.srs()
    assert isinstance(vectorset.srs(), list)
    assert result == ["EPSG:4326", "EPSG:3857", "EPSG:4559"]
    mocked_get_srs.assert_called()


@patch.object(Vector, "srs", return_value=["EPSG:4326"])
def test_vector_get_uniq_srs_tables_list_mocked(mocked_get_srs) -> None:
    vector = Vector()
    result = vector.srs()
    assert isinstance(vector.srs(), list)
    assert result == ["EPSG:4326"]
    mocked_get_srs.assert_called()


def test_vector_ok_from_file() -> None:
    """tester que les attributs path et tables renvoyés par la méthode 'from_file()' de 'Vector()' sont
    bien des chaînes de caractères en partant d'un fichier d'entrée d'extension *.geojson, *.gpkg et *.shp
    """
    path_geojson = "data/states.geojson"
    tables_geojson = [
        {
            "name": "states",
            "count": 52,
            "srs": "EPSG:3857",
            "bbox": [-19951818.272319775, 2017836.357428821, -7254560.414595957, 11553642.98126969],
            "geometry_columns": ["geom"],
            "attributes": {
                "id": "String",
                "STATE_ABBR": "String",
                "STATE_NAME": "String",
                "AREA_LAND": "Real",
                "AREA_WATER": "Real",
                "PERSONS": "Integer",
                "MALE": "Integer",
                "FEMALE": "Integer",
            },
        }
    ]
    path_gpkg = "data/martinique.gpkg"
    tables_gpkg = [
        {
            "name": "arrondissement",
            "count": 4,
            "srs": "EPSG:4559",
            "bbox": [690574.399999426, 1592426.09999943, 736126.499998242, 1645659.8],
            "geometry_columns": ["geom"],
            "attributes": {
                "fid": "Integer",
                "id": "Integer",
                "id_geofla": "String",
                "code_arr": "String",
                "code_chf": "String",
                "nom_chf": "String",
                "x_chf_lieu": "Integer",
                "y_chf_lieu": "Integer",
                "x_centroid": "Integer",
                "y_centroid": "Integer",
                "code_dept": "String",
                "nom_dept": "String",
                "code_reg": "String",
                "nom_reg": "String",
            },
        },
        {
            "name": "departement",
            "count": 1,
            "srs": "EPSG:4559",
            "bbox": [690574.399999426, 1592426.09999943, 736126.499998242, 1645659.8],
            "geometry_columns": ["geom"],
            "attributes": {
                "fid": "Integer",
                "id": "Integer",
                "id_geofla": "String",
                "code_dept": "String",
                "nom_dept": "String",
                "code_chf": "String",
                "nom_chf": "String",
                "x_chf_lieu": "Integer",
                "y_chf_lieu": "Integer",
                "x_centroid": "Integer",
                "y_centroid": "Integer",
                "code_reg": "String",
                "nom_reg": "String",
            },
        },
    ]
    path_shp = "data/TM_WORLD_BORDERS-0.3.shp"
    tables_shp = [
        {
            "name": "TM_WORLD_BORDERS-0.3",
            "count": 246,
            "srs": "EPSG:4326",
            "bbox": (-179.99999999999997, 180.0, -90.0, 83.62359600000008),
            "geometry_columns": ["geom"],
            "attributes": {
                "FIPS": "String",
                "ISO2": "String",
                "ISO3": "String",
                "UN": "Integer",
                "NAME": "String",
                "AREA": "Integer",
                "POP2005": "Integer64",
                "REGION": "Integer",
                "SUBREGION": "Integer",
                "LON": "Real",
                "LAT": "Real",
            },
        }
    ]

    vector = Vector()

    # tester si la méthode from_parameters renvoient bien des tables de données vecteur
    tables_geojson = vector.from_parameters(path_geojson, tables_geojson)
    tables_gpkg = vector.from_parameters(path_gpkg, tables_gpkg)
    tables_shp = vector.from_parameters(path_shp, tables_shp)

    # tester si la méthode from_file retourne bien une instance de Vector
    vector_geojson = vector.from_file(path_geojson)
    vector_gpkg = vector.from_file(path_gpkg)
    vector_shp = vector.from_file(path_shp)

    # tester si l'objet retourné est bien une instance de Vector
    assert isinstance(vector_geojson, Vector)
    assert isinstance(vector_gpkg, Vector)
    assert isinstance(vector_shp, Vector)


@patch("rok4.vector.Table.__init__", return_value=Table)
def test_table_init_returns_an_instance_of_table(mocked_patch) -> None:
    """tester le constructeur __init__ pour vérifier que l'instance lié à la
        classe Table a bien été créée

    Args:
        mocked_patch (str): décorateur
    """
    patcher = patch("rok4.vector.Table.__init__")
    mocked_patch = patcher.start()
    name = "object1"
    srs = "2154"
    count = 1000
    bbox = (150, 23.5, -59.1, -5.6)
    attributes = {
        "id": "String",
        "STATE_ABBR": "String",
        "STATE_NAME": "String",
        "AREA_LAND": "Real",
        "AREA_WATER": "Real",
        "PERSONS": "Integer",
        "MALE": "Integer",
        "FEMALE": "Integer",
    }
    geometry_columns = ["geom"]
    obj_table = Table.__init__(srs, count, bbox, attributes, name, geometry_columns)
    mocked_patch.isinstance(obj_table, mocked_patch)
    mocked_patch.isinstance(obj_table[name], str)
    mocked_patch.isinstance(obj_table[srs], str)
    mocked_patch.isinstance(obj_table[count], int)
    mocked_patch.isinstance(obj_table[bbox], tuple)
    mocked_patch.isinstance(obj_table[attributes], dict)
    mocked_patch.isinstance(obj_table[geometry_columns], list)
    mocked_patch.assert_called_once_with(srs, count, bbox, attributes, name, geometry_columns)
    patcher.stop()


def test_if_table_properties_are_all_ok() -> None:
    # Create a Table instance with sample data
    table = Table(
        name="test_table",
        geometry_columns=["id", "value"],
        bbox=(180.0, 2.0, 3.0, 4.0),
        srs="EPSG:2154",
        attributes={
            "id": "String",
            "STATE_ABBR": "String",
            "STATE_NAME": "String",
            "AREA_LAND": "Real",
            "AREA_WATER": "Real",
            "PERSONS": "Integer",
            "MALE": "Integer",
            "FEMALE": "Integer",
        },
        count=256,
    )

    # Test property 'name'
    assert table.name == "test_table"
    assert isinstance(table.name, str)

    # Test property 'columns'
    assert table.geometry_columns == ["id", "value"]
    assert isinstance(table.geometry_columns, list)

    # Test property 'bbox'
    assert table.bbox == (180.0, 2.0, 3.0, 4.0)
    assert isinstance(table.bbox, tuple)

    # Test property 'srs'
    assert table.srs == "EPSG:2154"
    assert isinstance(table.srs, str)

    # Test property 'attributes'
    assert table.attributes == {
        "id": "String",
        "STATE_ABBR": "String",
        "STATE_NAME": "String",
        "AREA_LAND": "Real",
        "AREA_WATER": "Real",
        "PERSONS": "Integer",
        "MALE": "Integer",
        "FEMALE": "Integer",
    }
    assert isinstance(table.attributes, dict)

    # Test property 'count'
    assert table.count == 256
    assert isinstance(table.count, int)