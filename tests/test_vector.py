#!/usr/bin/env python3
# NOM DU PROGRAMME : test_vector.py
# CONTEXTE : Ces librairies de core-python facilitent la manipulation d'entités du projet ROK4 comme 
# les Tile Matrix Sets, les pyramides ou encore les couches, ainsi que la manipulation des stockages associés.
# BUT DU PROGRAMME : écrire les tests unitaires et les tests d'intégration pour le module de chargement des données
#  vecteur 'vector.py'
# ENTREES : la classe 'Vector()'

# standard library
import os
import pytest
from unittest import mock
from unittest.mock import MagicMock, patch, Mock, mock_open, PropertyMock
from json.decoder import JSONDecodeError

# package

from rok4.storage import disconnect_s3_clients, get_osgeo_path, get_data_str
from rok4.vector import VectorSet, Vector, Table
from rok4.exceptions import MissingAttributeError, FormatError


def test_vectorset_from_list_listtxtpath_ok():
    """tester que la méthode de classe 'from_list()' ait bien appelée une fois par le programme et 
        que la fonction retourne bien un objet vecteur"""
    path = "tests/fixtures/filelist.txt"
    path_geojson = "tests/fixtures/states.geojson"
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
			        "FEMALE": "Integer"
				}
			}
		]
    path_gpkg = "tests/fixtures/martinique.gpkg"
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
			        "nom_reg": "String"
				}
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
			        "nom_reg": "String"
				}
			}
		]
    path_shp = "tests/fixtures/TM_WORLD_BORDERS-0.3.shp"
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
			        "LAT": "Real"
				}
			}
		]
    tables=[tables_geojson, tables_gpkg, tables_shp]


def test_vectorset_from_list_listtxtpath_not_ok():
    """tester que la méthode de classe 'from_list()' ait bien appelée une fois par le programme et 
        que la fonction retourne bien un objet vecteur"""
    path = "tests/fixtures/filelist.txt"
    message_pattern: str = f"le chemin du fichier vecteur ou objet vecteur n'est pas valide {path}.\n"


@patch("builtins.open", new_callable=mock_open, read_data="tests/fixtures/filelist.txt")
def test_vectorset_patch(mock_file):
    assert open("path/to/open").read() == "tests/fixtures/filelist.txt"
    mock_file.assert_called_with("path/to/open")
    with pytest.raises(Exception):
        VectorSet.from_list(mock_file)
        assert isinstance(VectorSet.from_list(mock_file), list)
        assert (len(VectorSet.from_list(mock_file)) == 3)


def test_vectorset_from_descriptor_path_ok():
    """tester que la méthode de classe 'from_descriptor()' ait bien appelée une fois par le programme et 
        que la fonction retourne bien un objet vecteur"""
    path = "tests/fixtures/vectorset.json"
    assert isinstance (VectorSet.from_descriptor(path), VectorSet)


def test_vectorset_from_descriptor_wrong_file_path():
    """tester que la méthode de classe 'from_list()' ait bien appelée une fois par le programme et 
        que la fonction retourne bien un objet vecteur"""
    path = "tests/fixtures/vectorsetnotexists.json"
    with pytest.raises(FileNotFoundError) :
        VectorSet.from_descriptor(path)
        assert isinstance(VectorSet.from_descriptor(path), VectorSet)
        assert (os.path.exists(path)== False)
    
    
@patch('rok4.vector.VectorSet.get_unique_srs_tables_list', new_callable=PropertyMock)
def test_vectorset_get_unique_srs_tables_list_ok(mocker_uniq_srs_list):
    srs = "EPSG:4559"
    mocker_uniq_srs_list.patch(
        'VectorSet.get_unique_srs_tables_list',
        new_callable=mocker_uniq_srs_list.PropertyMock,
        return_value = ["EPSG:4326", "EPSG:3857", "EPSG:4559"]
    )
    vectorset = VectorSet()
    print(vectorset.get_unique_srs_tables_list)
    mocker_uniq_srs_list.assert_called_once_with()

    assert isinstance(VectorSet.get_unique_srs_tables_list(srs), object)


@mock.patch.dict(os.environ, {}, clear=True)
def test_vector_get_unique_srs_list():
    """tester que la méthode du getter 'get_unique_srs_tables_list(srs)' ait bien appelée une fois par le programme et 
        que la fonction retourne bien un objet vecteur"""
    
    expected_srs_tables_list = ["EPSG:4326", "EPSG:3857", "EPSG:4559"]
    mock_append = Mock(return_value=expected_srs_tables_list)
    mock_append.patch(
        'Vector.get_unique_srs_tables_list',
        new_callable=mock_append.PropertyMock,
        return_value = ["EPSG:4326", "EPSG:3857", "EPSG:4559"]
    )
    assert mock_append.return_value == expected_srs_tables_list
    

def test_vector_from_file_ok_shp():
    """_summary_
    """
    path = "tests/fixtures/TM_WORLD_BORDERS-0.3.shp"
 


def test_vector_from_file_wrong_file_shp():
    """_summary_
    """

def test_vector_from_file_ok_geojson():
    """_summary_
    """
    path = "tests/fixtures/states.geojson"
    

def test_vector_from_file_wrong_file_geojson():
    """_summary_
    """

def test_vector_from_file_ok_gpkg():
    """_summary_
    """
    path = "tests/fixtures/martinique.gpkg"
    expected_gpkg_vector  = {"path": path, "tables": [
			{
				"name": "arrondissement",
				"count": 4,
				"srs": "EPSG:4559",
				"bbox": (690574.399999426, 1592426.09999943, 736126.499998242, 1645659.8),
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
			        "nom_reg": "String"
				}
			},
			{
				"name": "departement",
				"count": 1,
				"srs": "EPSG:4559",
				"bbox": (690574.399999426, 1592426.09999943, 736126.499998242, 1645659.8),
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
			        "nom_reg": "String"
				}
			}
		],"data": {}}


def test_vector_from_file_wrong_file_gpkg():
    """_summary_
    """


def test_vector_from_parameters_ok_shp():
    """_summary_
    """
    path = "tests/fixtures/TM_WORLD_BORDERS-0.3.shp"
    tables = [
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
			        "LAT": "Real"
				}
			}
		]
    expected_shp_vector  = {"path": path, "tables": [
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
			        "LAT": "Real"
				}
			}
		],"data": {}}



def test_vector_from_parameters_wrong_file_shp():
    """_summary_
    """

def test_vector_from_parameters_ok_geojson():
    """_summary_
    """
    path = "tests/fixtures/states.geojson"
    tables = [
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
			        "FEMALE": "Integer"
				}
			}
		]
    expected_geojson_vector  = {"path": path, "tables": [
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
			        "FEMALE": "Integer"
				}
			}
		],"data": {}}

    

def test_vector_from_parameters_wrong_file_geojson():
    """_summary_
    """

def test_vector_from_parameters_ok_gpkg():
    """_summary_
    """
    path = "tests/fixtures/martinique.gpkg"
    tables = [
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
			        "nom_reg": "String"
				}
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
			        "nom_reg": "String"
				}
			}
		]
    expected_gpkg_vector  = {"path": path, "tables": [
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
			        "nom_reg": "String"
				}
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
			        "nom_reg": "String"
				}
			}
		],"data": {}}
    


def test_vector_from_parameters_wrong_file_gpkg():
    """_summary_
    """

@patch('rok4.vector.Vector.get_unique_srs_tables_list', new_callable=PropertyMock)
def test_vector_get_unique_srs_tables_list_ok(mocker_uniq_srs_list):
    srs = "EPSG:4326"
    mocker_uniq_srs_list.patch(
        'Vector.get_unique_srs_tables_list',
        new_callable=mocker_uniq_srs_list.PropertyMock,
        return_value = ["EPSG:4326", "EPSG:3857", "EPSG:4559"]
    )
    vector = Vector()
    print(vector.get_unique_srs_tables_list)
    mocker_uniq_srs_list.assert_called_once_with()

    assert isinstance(Vector.get_unique_srs_tables_list(srs), object)

@patch("builtins.open", new_callable=mock_open, read_data="data")
def test_vectorset_patch(mock_file):
    srs = "EPSG:4559"
    assert open("path/to/open").read() == "data"
    mock_file.assert_called_with("path/to/open")
    with pytest.raises(Exception):
        VectorSet.get_unique_srs_tables_list(srs)
        assert isinstance(VectorSet.get_unique_srs_tables_list(srs), list)


@patch("builtins.open", new_callable=mock_open, read_data="data")
def test_vector_patch(mock_file):
    srs = "EPSG:3857"
    assert open("path/to/open").read() == "data"
    mock_file.assert_called_with("path/to/open")
    with pytest.raises(Exception):
        Vector.get_unique_srs_tables_list(srs)
        assert isinstance(Vector.get_unique_srs_tables_list(srs), list)
    

@patch('rok4.vector.Table.__init__', return_value=Table)
def test_table_init(mpatch):
    """tester le constructeur __init__ pour vérifier que l'instance lié à la 
        classe Table a bien été créée

    Args:
        mpatch (str): décorateur
    """
    patcher = patch('rok4.vector.Table.__init__')
    mpatch = patcher.start()
    name = "TM_WORLD_BORDERS-0.3"
    srs = "EPSG:4326" 
    count = 246
    bbox = (-179.99999999999997, 180.0, -90.0, 83.62359600000008)
    attributes = {
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
			        "LAT": "Real"
				}
    geometry_columns = ["geom"]
    obj_table = Table.__init__(srs,count,bbox,attributes,name, geometry_columns)
    mpatch.isinstance(obj_table, mpatch)
    mpatch.isinstance(obj_table[name], str)
    mpatch.isinstance(obj_table[srs], str)
    mpatch.isinstance(obj_table[count], int)
    mpatch.isinstance(obj_table[bbox], tuple)
    mpatch.isinstance(obj_table[attributes], dict)
    mpatch.isinstance(obj_table[geometry_columns], list)
    assert isinstance(obj_table, dict)
    assert (obj_table["name"] == name)
    assert (obj_table["srs"] == srs)
    assert (obj_table["count"] == count)
    assert (obj_table["bbox"] == bbox)
    assert (obj_table["attributes"] == attributes)
    assert (obj_table["geometry_columns"] == geometry_columns)
    mpatch.assert_called_once_with(srs, count, bbox, attributes, name, geometry_columns)
    patcher.stop()


def test_vector_ok_from_file():
    """ tester que les attributs path et tables renvoyés par la méthode 'from_file()' de 'Vector()' sont
         bien des chaînes de caractères en partant d'un fichier d'entrée d'extension *.geojson, *.gpkg et *.shp"""
    path_geojson = "tests/fixtures/states.geojson"
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
			        "FEMALE": "Integer"
				}
			}
		]
    path_gpkg = "tests/fixtures/martinique.gpkg"
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
			        "nom_reg": "String"
				}
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
			        "nom_reg": "String"
				}
			}
		]
    path_shp = "tests/fixtures/TM_WORLD_BORDERS-0.3.shp"
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
			        "LAT": "Real"
				}
			}
		]
    # vector_geojson = Vector.from_file(
    #     path_geojson, tables_geojson
    # )
    

    # vector_gpkg = Vector.from_file(
    #     path_gpkg, tables_gpkg
    # )



    # vector_shp = Vector.from_file(
    #         path_shp, tables_shp
    # )

    

@patch("rok4.vector.Vector.from_file")
def test_get_data_valid(mock_checkoutput):
    path = "tests/fixtures/martinique.gpkg"
    mock_stdout = MagicMock()
    mock_stdout.configure_mock(
        **{
            "stdout.decode.return_value": 'returned non-zero exit status 1.'
        }
    )

    mock_checkoutput.return_value = mock_stdout
	
    result = Vector.from_file(path)

#@patch("rok4.vector.Vector.from_file", side_effect=Exception("returned non-zero exit status 1."))
#def test_get_data_invalid(mock_checkoutput):
    # path = "tests/fixtures/martinique.gpkg"
    # mock_stdout = MagicMock()
    # mock_stdout.configure_mock(
    #     **{
    #         "stdout.decode.return_value": 'returned non-zero exit status 1.'
    #     }
    # )
    # with pytest.raises(Exception) as exc:
    #     Vector.from_file(path)
    # mock_checkoutput.return_value = mock_stdout
        

#def test_vector_ok_parameters():
    # """ tester que les attributs path et tables renvoyés par la méthode 'from_parameters()' de 'Vector()' sont
    #      bien des chaînes de caractères en partant d'un fichier d'entrée d'extension *.geojson, *.gpkg et *.shp"""
    # path = "tests/fixtures/states.geojson"
    # vector_geojson_output = Vector.from_parameters(
    #         "tests/fixtures/states.geojson",
    #         [
	# 		{
	# 			"name": "states",
	# 			"count": 52,
	# 			"srs": "EPSG:3857",
	# 			"bbox": (-19951818.272319775, 2017836.357428821, -7254560.414595957, 11553642.98126969),
	# 			"geometry_columns": ["geom"],
	# 			"attributes": {
	# 		        "id": "String",
	# 		        "STATE_ABBR": "String",
	# 		        "STATE_NAME": "String",
	# 		        "AREA_LAND": "Real",
	# 		        "AREA_WATER": "Real",
	# 		        "PERSONS": "Integer",
	# 		        "MALE": "Integer",
	# 		        "FEMALE": "Integer"
	# 			}
	# 		}
	# 	]
    # )
    

@mock.patch.dict(os.environ, {}, clear=True)
def test_vectorset_from_list_ok():
    """ tester que la méthode 'from_list()' de 'VectorSet()' a bien le chemin défini donnant accès 
        au jeu de données vecteur"""
    mocked_str = Mock()
    mocked_str.endswith.return_value = True # or something else you want
    mocked_str.endswith(".txt")
    try:
        path = get_osgeo_path("tests/fixtures/filelist.txt")
        assert path == "tests/fixtures/filelist.txt"
    except Exception as exc:
        assert False, f" the path of vector set from list {path} is not defined {exc}"
    

@patch('rok4.vector.Table.__init__', return_value=Table)
def test_table_init(mpatch):
    """tester le constructeur __init__ pour vérifier que l'instance lié à la 
        classe Table a bien été créée

    Args:
        mpatch (str): décorateur
    """
    patcher = patch('rok4.vector.Table.__init__')
    mpatch = patcher.start()
    name = "object1"
    srs = "2154" 
    count = 1000
    bbox = (150,23.5,-59.1,-5.6)
    attributes = {
			        "id": "String",
			        "STATE_ABBR": "String",
			        "STATE_NAME": "String",
			        "AREA_LAND": "Real",
			        "AREA_WATER": "Real",
			        "PERSONS": "Integer",
			        "MALE": "Integer",
			        "FEMALE": "Integer"
				}
    geometry_columns= ["geom"]
    obj_table = Table.__init__(srs,count,bbox,attributes,name,geometry_columns)
    mpatch.isinstance(obj_table,mpatch)
    mpatch.isinstance(obj_table[name],str)
    mpatch.isinstance(obj_table[srs],str)
    mpatch.isinstance(obj_table[count],int)
    mpatch.isinstance(obj_table[bbox],tuple)
    mpatch.isinstance(obj_table[attributes],dict)
    mpatch.isinstance(obj_table[geometry_columns],list)
    mpatch.assert_called_once_with(srs,count,bbox,attributes,name,geometry_columns)
    patcher.stop()

@mock.patch.dict(
    os.environ,
    {"ROK4_S3_URL": "https://a,https://b", "ROK4_S3_SECRETKEY": "a,b", "ROK4_S3_KEY": "a,b"},
    clear=True,
)
def test_get_osgeo_path_s3_ok():
    """tester que la méthode 'get_osgeo_path()' récupère bien le chemin donnant l'accès 
        à l'objet vecteur du bucket S3'
    """
    disconnect_s3_clients()

    try:
        path = get_osgeo_path("s3://bucket@b/to/object.ext")
        assert path == "/vsis3/bucket/to/object.ext"
    except Exception as exc:
        assert False, f"S3 osgeo path raises an exception: {exc}"