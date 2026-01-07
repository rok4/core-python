#!/usr/bin/env python3
# PROGRAM NAME : test_vector.py
# CONTEXT : These core-python libraries facilitate the manipulation of entities in the ROK4 project such as
# Tile Matrix Sets, pyramids, and layers, as well as the manipulation of associated storage.
# AIM : write unit tests and integration tests for the vector data loading module 'vector.py'
# INPUTS : the three classes 'VectorSet()', 'Vector()' and 'Table()' of the module 'vector.py'

import builtins
import json

# standard library
import os
from json.decoder import JSONDecodeError
from unittest.mock import MagicMock, mock_open, patch

# 3rd party
import pytest  # type: ignore

# local : other rok4 libraries
from rok4.exceptions import FormatError, StorageError
from rok4.storage import get_osgeo_path

# import of classes from the 'vector' library of rok4 for which we need to test their functions
from rok4.vector import Table, Vector, VectorSet


def test_from_list_calls_get_osgeo_path(tmp_path) -> None:
    """Test that from_list correctly calls get_osgeo_path."""
    # Create a dummy file to act as the list file
    filelist = tmp_path / "filelist.txt"
    filelist.write_text("/tmp/fake_vector.geojson\n")

    # Patch get_osgeo_path to check it is called and control its output
    with patch("rok4.vector.get_osgeo_path") as mock_get_osgeo_path, patch(
        "rok4.vector.copy"
    ), patch("rok4.vector.Vector.from_file"):
        mock_get_osgeo_path.return_value = str(filelist)
        VectorSet.from_list(str(filelist))
        mock_get_osgeo_path.assert_called_once_with(str(filelist))


def test_from_list_reads_and_appends_vectors(tmp_path) -> None:
    """Test that from_list correctly reads a file and appends Vector instances."""
    # Create a fake file with some lines (including a comment and empty line)
    filelist = tmp_path / "filelist.txt"
    filelist.write_text(
        """
# This is a comment
/path/to/vector1.geojson

/path/to/vector2.geojson
"""
    )

    # Patch dependencies: get_osgeo_path, copy, Vector.from_file, and tempfile.NamedTemporaryFile
    with patch("rok4.vector.get_osgeo_path", return_value=str(filelist)), patch(
        "rok4.vector.copy"
    ), patch("rok4.vector.Vector.from_file") as mock_from_file, patch(
        "rok4.vector.tempfile.NamedTemporaryFile"
    ) as mock_tempfile:

        # Simulate NamedTemporaryFile returning our file path
        mock_tmp = MagicMock()
        mock_tmp.name = str(filelist)
        mock_tempfile.return_value = mock_tmp

        # Mock Vector.from_file to return a dummy object
        dummy_vector = MagicMock()
        mock_from_file.return_value = dummy_vector

        vectorset = VectorSet.from_list("dummy_path")

        # Should call Vector.from_file twice (for the two non-comment, non-empty lines)
        assert mock_from_file.call_count == 2
        # Should append the dummy_vector twice
        assert vectorset.vectors == [dummy_vector, dummy_vector]


def test_from_descriptor_calls_vector_from_parameters() -> None:
    """Test that from_descriptor correctly calls Vector.from_parameters for each entry in the descriptor."""
    # Prepare a fake descriptor object as JSON string
    descriptor = [
        {"path": "file1.geojson", "tables": {"t1": "table1"}},
        {"path": "file2.geojson", "tables": {"t2": "table2"}},
    ]
    descriptor_json = json.dumps(descriptor)

    # Patch dependencies
    with patch("rok4.vector.get_osgeo_path", return_value="dummy.json"), patch(
        "rok4.vector.get_data_str", return_value=descriptor_json
    ), patch("rok4.vector.Vector.from_parameters") as mock_from_parameters:

        # Set up the mock to return a unique object for each call
        dummy_vectors = [MagicMock(name="Vector1"), MagicMock(name="Vector2")]
        mock_from_parameters.side_effect = dummy_vectors

        vectorset = VectorSet.from_descriptor("dummy.json")

        # Check that Vector.from_parameters was called with correct arguments
        assert mock_from_parameters.call_count == 2
        mock_from_parameters.assert_any_call("file1.geojson", {"t1": "table1"})
        mock_from_parameters.assert_any_call("file2.geojson", {"t2": "table2"})

        # Check that vectors contains the dummy vectors
        assert dummy_vectors[0] in vectorset.vectors
        assert dummy_vectors[1] in vectorset.vectors

    assert isinstance(VectorSet.from_descriptor("file://tests/fixtures/vectorset.json"), VectorSet)


def test_from_descriptor_raises_formaterror_on_jsondecodeerror() -> None:
    """Test that from_descriptor raises FormatError on JSONDecodeError."""
    # Patch get_osgeo_path to avoid file system dependency
    with patch("rok4.vector.get_osgeo_path", return_value="dummy.json"), patch(
        "rok4.vector.get_data_str", return_value="{invalid json}"
    ):
        with pytest.raises(FormatError) as excinfo:
            VectorSet.from_descriptor("dummy.json")
        assert "JSON" in str(excinfo.value)


class FakeVector:
    """Fake Vector class for testing purposes."""

    def __init__(self, srs_list):
        self._srs = srs_list

    @property
    def srs(self):
        return self._srs


def test_vectorset_srs_property() -> None:
    """Test the srs property of VectorSet to ensure it aggregates unique SRS from its vectors."""
    v1 = FakeVector(["EPSG:4326", "EPSG:3857"])
    v2 = FakeVector(["EPSG:4326", "EPSG:32631"])
    v3 = FakeVector(["EPSG:3857"])
    vectorset = VectorSet()
    vectorset.vectors = [v1, v2, v3]

    result = vectorset.srs
    assert result == ["EPSG:4326", "EPSG:3857", "EPSG:32631"]
    assert isinstance(vectorset.srs, list)


class FakeVectorSerializable:
    """A fake serializable vector class for testing purposes."""

    def __init__(self, serializable):
        self._serializable = serializable

    @property
    def serializable(self):
        return self._serializable


def test_vectorset_serializable() -> None:
    """Test that the VectorSet class is serializable."""
    v1 = FakeVectorSerializable({"path": "a.geojson", "tables": []})
    v2 = FakeVectorSerializable({"path": "b.geojson", "tables": []})
    vectorset = VectorSet()
    vectorset.vectors = [v1, v2]

    expected = {
        "vectors": [{"path": "a.geojson", "tables": []}, {"path": "b.geojson", "tables": []}]
    }
    assert vectorset.serializable == expected


def test_vector_from_file_raises_storageerror_on_none_datasource() -> None:
    """Test that Vector.from_file raises StorageError when ogr.Open returns None."""
    with patch("rok4.vector.ogr.Open", return_value=None):
        with pytest.raises(StorageError) as excinfo:
            Vector.from_file("dummy_path.geojson")
        assert "Cannot open vector file/object" in str(excinfo.value)


@patch.dict(os.environ, {}, clear=True)
def test_filelistpath_is_ok_by_equals_assertion() -> None:
    """test that the 'get_osgeo_path()' method of 'Storage()' correctly retrieves the path giving access
    to the vector dataset"""
    try:
        path = get_osgeo_path("data/filelist.txt")
        assert path == "data/filelist.txt"
    except Exception as exc:
        assert False, f" the path of vector set from list {path} is not defined {exc}"


@patch.dict(os.environ, {}, clear=True)
def test_geojson_file_path_is_ok_by_equals_assertion() -> None:
    """test that the 'get_osgeo_path()' method of 'Storage()' correctly retrieves the path giving access
    to the vector dataset"""
    try:
        geojson_file_path = get_osgeo_path("data/states.geojson")
        assert geojson_file_path == "data/states.geojson"
    except Exception as exc:
        assert (
            False
        ), f" the path of vector geojson file from file {geojson_file_path} is not defined {exc}"


@patch.dict(os.environ, {}, clear=True)
def test_gpkg_file_path_is_ok_by_equals_assertion() -> None:
    """test that the 'get_osgeo_path()' method of 'Storage()' correctly retrieves the path giving access
    to the vector dataset"""
    try:
        gpkg_file_path = get_osgeo_path("data/martinique.gpkg")
        assert gpkg_file_path == "data/martinique.gpkg"
    except Exception as exc:
        assert (
            False
        ), f" the path of vector geopackage file from file {gpkg_file_path} is not defined {exc}"


@patch.dict(os.environ, {}, clear=True)
def test_shp_file_path_is_ok_by_equals_assertion() -> None:
    """test that the 'get_osgeo_path()' method of 'Storage()' correctly retrieves the path giving access
    to the vector dataset"""
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
    """test that the 'get_osgeo_path()' method correctly retrieves the path giving access
    to the vector object in the S3 bucket
    """
    try:
        path = get_osgeo_path("s3://bucket@b/to/object.ext")
        assert path == "/vsis3/bucket/to/object.ext"
    except Exception as exc:
        assert False, f"S3 osgeo path raises an exception: {exc}"


@patch("builtins.open", new_callable=mock_open, read_data="fake.geojson")
def test_by_mocking_open_function_with_a_not_valid_geojson(mocked_file_geojson_not_valid) -> None:
    """Test that Vector.from_file raises StorageError when ogr.Open returns None.

    Args:
        mocked_file_geojson_not_valid (str): a mocked file path to a non valid geojson file
    """
    vectorset = VectorSet()
    assert open("path/to/open").read() == "fake.geojson"
    with pytest.raises(Exception):
        vectorset.from_list(mocked_file_geojson_not_valid)
    mocked_file_geojson_not_valid.assert_called()


@patch("builtins.open", new_callable=mock_open, read_data="fake.gpkg")
def test_by_mocking_open_function_with_a_not_valid_gpkg(mocked_file_gpkg_not_valid) -> None:
    """Test that Vector.from_file raises StorageError when ogr.Open returns None.
    Args:
        mocked_file_gpkg_not_valid (str): a mocked file path to a non valid geopackage file
    """
    vectorset = VectorSet()
    assert open("path/to/open").read() == "fake.gpkg"
    with pytest.raises(Exception):
        vectorset.from_list(mocked_file_gpkg_not_valid)
    mocked_file_gpkg_not_valid.assert_called()


@patch("builtins.open", new_callable=mock_open, read_data="fake.shp")
def test_by_mocking_open_function_with_a_not_valid_shp(mocked_file_shp_not_valid) -> None:
    """Test that Vector.from_file raises StorageError when ogr.Open returns None."""
    vectorset = VectorSet()
    assert open("path/to/open").read() == "fake.shp"
    with pytest.raises(Exception):
        vectorset.from_list(mocked_file_shp_not_valid)
    mocked_file_shp_not_valid.assert_called()


@patch("builtins.open", new_callable=mock_open, read_data="fake.s3_vector_object")
def test_by_mocking_open_function_with_a_not_valid_vector_object(
    mocked_file_s3_vector_object_not_valid,
) -> None:
    """Test that Vector.from_file raises StorageError when ogr.Open returns None."""
    vectorset = VectorSet()
    assert open("path/to/open").read() == "fake.s3_vector_object"
    with pytest.raises(Exception):
        vectorset.from_list(mocked_file_s3_vector_object_not_valid)
    mocked_file_s3_vector_object_not_valid.assert_called()


@patch.object(builtins, "open", new_callable=mock_open, read_data="data/states.geojson")
@patch.object(builtins, "open", new_callable=mock_open, read_data="data/TM_WORLD_BORDERS-0.3.shp")
@patch.object(builtins, "open", new_callable=mock_open, read_data="data/martinique.gpkg")
def test_reading_vector_files_by_mocking_open_function_all_parameters_ok(
    mocked_file_open_geojson, mocked_file_open_shp, mocked_file_open_gpkg
) -> None:
    """test that the path and tables attributes returned by the 'from_file()' method of 'Vector()' are"""
    """indeed strings starting from an input file with extensions *.geojson, *.gpkg, and *.shp"""
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


@patch("builtins.open", new_callable=mock_open, read_data="data/filelist.txt")
def test_if_filelist_txt_is_ok_by_mocking_open_function_with_a_valid_filelist(mocked_file) -> None:
    """test that the path and tables attributes returned by the 'from_list()' method of 'VectorSet()' are
    indeed strings starting from an input file with extension *.txt
    """
    assert open("path/to/open").read() == "data/filelist.txt"
    mocked_file.assert_called_with("path/to/open")


def test_missing_vector_keys() -> None:
    """Test that from_descriptor raises an exception when required keys are missing."""
    vectorset = VectorSet()
    descriptor_file_with_missing_keys = [
        {
            "path": "file://./tests/fixtures/martinique.gpkg",
        }
    ]
    REQUIRED_VECTOR_KEYS = ["path", "tables"]
    with patch(
        "rok4.vector.VectorSet.from_descriptor",
        return_value="[{'path': 'file://./tests/fixtures/martinique.gpkg',}]",
    ) as mocked_missing_vector_keys:
        vectorset.from_descriptor(descriptor_file_with_missing_keys)
        assert "tables" not in descriptor_file_with_missing_keys
    mocked_missing_vector_keys.call_count == 2
    mocked_missing_vector_keys.call_args(REQUIRED_VECTOR_KEYS[0], REQUIRED_VECTOR_KEYS[1])


@patch("json.loads", return_value=dict({"the_data": "This is fake data"}))
def test_descriptor_is_not_valid_with_a_fake_file_path(mocked_json_loads) -> None:
    """Test that from_descriptor raises an exception on invalid file path."""
    vectorset = VectorSet()
    path_to_fake_descriptor = "/non_exists/fake_descriptor.json"
    mocked_json_loads.side_effect = json.loads(JSONDecodeError("JSON", path_to_fake_descriptor, 1))
    with pytest.raises(Exception):
        vectorset.from_descriptor(path_to_fake_descriptor)
    mocked_json_loads.assert_called_once()


@patch.object(Vector, "srs", return_value=["EPSG:4326"])
def test_vector_get_uniq_srs_tables_list_mocked(mocked_get_srs) -> None:
    """test that the 'srs' property of the 'Vector()' class correctly retrieves the list of unique SRS"""
    vector = Vector()
    result = vector.srs()
    assert isinstance(vector.srs(), list)
    assert result == ["EPSG:4326"]
    mocked_get_srs.assert_called()


def test_vector_srs_property_with_multiple_tables() -> None:
    """Test that Vector.srs returns unique SRS from all tables, testing lines 289-294."""
    vector = Vector()
    vector.path = "/tmp/test.gpkg"
    
    # Create tables with different SRS
    table1 = Table("table1", 10, "EPSG:4326", (0, 0, 1, 1), {"id": "Integer"}, ["geom"])
    table2 = Table("table2", 20, "EPSG:3857", (0, 0, 2, 2), {"name": "String"}, ["geom"])
    table3 = Table("table3", 30, "EPSG:4326", (0, 0, 3, 3), {"value": "Real"}, ["geom"])  # Duplicate SRS
    
    vector.tables = {"table1": table1, "table2": table2, "table3": table3}
    
    # Test the srs property (lines 289-294)
    result = vector.srs
    
    # Should return unique SRS only
    assert isinstance(result, list)
    assert len(result) == 2
    assert "EPSG:4326" in result
    assert "EPSG:3857" in result


def test_vector_srs_property_empty_tables() -> None:
    """Test that Vector.srs returns empty list when no tables exist."""
    vector = Vector()
    vector.path = "/tmp/test.geojson"
    vector.tables = {}
    
    result = vector.srs
    
    assert isinstance(result, list)
    assert len(result) == 0


def test_vector_srs_property_single_table() -> None:
    """Test that Vector.srs returns single SRS for one table."""
    vector = Vector()
    vector.path = "/tmp/test.shp"
    
    table = Table("single", 100, "EPSG:2154", (1, 2, 3, 4), {"attr": "String"}, ["geom"])
    vector.tables = {"single": table}
    
    result = vector.srs
    
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0] == "EPSG:2154"


def test_vector_from_parameters() -> None:
    """test that the path and tables attributes returned by the 'from_parameters()' method of 'Vector()' are
    indeed strings starting from input parameters 'path' and 'tables'
    """

    # Prepare test data
    path = "/tmp/test.geojson"
    tables = {
        "table1": {
            "name": "table1",
            "count": 10,
            "srs": "EPSG:4326",
            "bbox": [0.0, 0.0, 1.0, 1.0],
            "attributes": {"id": "Integer"},
            "geometry_columns": ["geom"]
        },
        "table2": {
            "name": "table2",
            "count": 20,
            "srs": "EPSG:3857",
            "bbox": [0.0, 0.0, 2.0, 2.0],
            "attributes": {"name": "String"},
            "geometry_columns": ["geometry"]
        }
    }

    # Call the method
    vector = Vector.from_parameters(path, tables)

    # Check attributes
    assert vector.path == path
    assert len(vector.tables) == 2
    assert "table1" in vector.tables
    assert "table2" in vector.tables
    assert isinstance(vector.tables["table1"], Table)
    assert isinstance(vector.tables["table2"], Table)


def test_vector_ok_from_file() -> None:
    """Test that the from_file method returns Vector instances with proper tables."""
    # Create a mock datasource and layer
    mock_datasource = MagicMock()
    mock_layer = MagicMock()
    
    # Configure the mock layer
    mock_layer.GetName.return_value = "test_layer"
    mock_layer.GetFeatureCount.return_value = 100
    mock_layer.GetGeometryColumn.return_value = "geom"
    
    # Mock spatial reference
    mock_srs = MagicMock()
    mock_srs.GetAuthorityName.return_value = "EPSG"
    mock_srs.GetAuthorityCode.return_value = "4326"
    mock_layer.GetSpatialRef.return_value = mock_srs
    
    # Mock extent (xmin, xmax, ymin, ymax)
    mock_layer.GetExtent.return_value = (0.0, 10.0, 0.0, 10.0)
    
    # Mock FID column
    mock_layer.GetFIDColumn.return_value = ""
    
    # Mock layer definition with fields
    mock_layer_def = MagicMock()
    mock_layer_def.GetFieldCount.return_value = 1
    
    mock_field = MagicMock()
    mock_field.GetName.return_value = "id"
    mock_field.GetTypeName.return_value = "Integer"
    mock_layer_def.GetFieldDefn.return_value = mock_field
    
    mock_layer.GetLayerDefn.return_value = mock_layer_def
    
    # Configure the datasource
    mock_datasource.GetLayerCount.return_value = 1
    mock_datasource.GetLayer.return_value = mock_layer
    
    # Patch ogr.Open to return our mock datasource
    with patch("rok4.vector.ogr.Open", return_value=mock_datasource):
        vector_geojson = Vector.from_file("test.geojson")
        vector_gpkg = Vector.from_file("test.gpkg")
        vector_shp = Vector.from_file("test.shp")
        
        # Test if the returned objects are indeed instances of Vector
        assert isinstance(vector_geojson, Vector)
        assert isinstance(vector_gpkg, Vector)
        assert isinstance(vector_shp, Vector)
        
        # Verify that tables were created
        assert len(vector_geojson.tables) == 1
        assert "test_layer" in vector_geojson.tables
        assert isinstance(vector_geojson.tables["test_layer"], Table)


def test_vector_from_file_with_fid_column() -> None:
    """Test Vector.from_file when layer has a FID column (line 224-225)."""
    # Create a mock datasource and layer
    mock_datasource = MagicMock()
    mock_layer = MagicMock()
    
    # Configure the mock layer
    mock_layer.GetName.return_value = "layer_with_fid"
    mock_layer.GetFeatureCount.return_value = 50
    mock_layer.GetGeometryColumn.return_value = "geom"
    
    # Mock spatial reference
    mock_srs = MagicMock()
    mock_srs.GetAuthorityName.return_value = "EPSG"
    mock_srs.GetAuthorityCode.return_value = "3857"
    mock_layer.GetSpatialRef.return_value = mock_srs
    
    # Mock extent
    mock_layer.GetExtent.return_value = (1.0, 5.0, 2.0, 6.0)
    
    # Mock FID column - THIS TESTS LINE 224-225
    mock_layer.GetFIDColumn.return_value = "fid"
    
    # Mock layer definition with fields
    mock_layer_def = MagicMock()
    mock_layer_def.GetFieldCount.return_value = 2
    
    # Mock two fields
    mock_field1 = MagicMock()
    mock_field1.GetName.return_value = "name"
    mock_field1.GetTypeName.return_value = "String"
    
    mock_field2 = MagicMock()
    mock_field2.GetName.return_value = "value"
    mock_field2.GetTypeName.return_value = "Real"
    
    mock_layer_def.GetFieldDefn.side_effect = [mock_field1, mock_field2]
    mock_layer.GetLayerDefn.return_value = mock_layer_def
    
    # Configure the datasource
    mock_datasource.GetLayerCount.return_value = 1
    mock_datasource.GetLayer.return_value = mock_layer
    
    # Patch ogr.Open to return our mock datasource
    with patch("rok4.vector.ogr.Open", return_value=mock_datasource):
        vector = Vector.from_file("test_with_fid.gpkg")
        
        # Verify vector was created
        assert isinstance(vector, Vector)
        assert len(vector.tables) == 1
        assert "layer_with_fid" in vector.tables
        
        # Verify the FID column was added to attributes (line 225)
        table = vector.tables["layer_with_fid"]
        assert "fid" in table.attributes
        assert table.attributes["fid"] == "Integer"
        
        # Verify other fields were also added
        assert "name" in table.attributes
        assert table.attributes["name"] == "String"
        assert "value" in table.attributes
        assert table.attributes["value"] == "Real"


def test_vector_from_file_without_fid_column() -> None:
    """Test Vector.from_file when layer has no FID column (line 224 false branch)."""
    # Create a mock datasource and layer
    mock_datasource = MagicMock()
    mock_layer = MagicMock()
    
    # Configure the mock layer
    mock_layer.GetName.return_value = "layer_no_fid"
    mock_layer.GetFeatureCount.return_value = 25
    mock_layer.GetGeometryColumn.return_value = "geometry"
    
    # Mock spatial reference
    mock_srs = MagicMock()
    mock_srs.GetAuthorityName.return_value = "EPSG"
    mock_srs.GetAuthorityCode.return_value = "4326"
    mock_layer.GetSpatialRef.return_value = mock_srs
    
    # Mock extent
    mock_layer.GetExtent.return_value = (0.0, 10.0, 0.0, 10.0)
    
    # Mock FID column - empty string (no FID column)
    mock_layer.GetFIDColumn.return_value = ""
    
    # Mock layer definition with one field
    mock_layer_def = MagicMock()
    mock_layer_def.GetFieldCount.return_value = 1
    
    mock_field = MagicMock()
    mock_field.GetName.return_value = "id"
    mock_field.GetTypeName.return_value = "Integer"
    
    mock_layer_def.GetFieldDefn.return_value = mock_field
    mock_layer.GetLayerDefn.return_value = mock_layer_def
    
    # Configure the datasource
    mock_datasource.GetLayerCount.return_value = 1
    mock_datasource.GetLayer.return_value = mock_layer
    
    # Patch ogr.Open to return our mock datasource
    with patch("rok4.vector.ogr.Open", return_value=mock_datasource):
        vector = Vector.from_file("test_no_fid.geojson")
        
        # Verify vector was created
        assert isinstance(vector, Vector)
        assert len(vector.tables) == 1
        
        # Verify NO FID column was added to attributes
        table = vector.tables["layer_no_fid"]
        assert "fid" not in table.attributes
        
        # Verify only the regular field was added
        assert "id" in table.attributes
        assert table.attributes["id"] == "Integer"
        assert len(table.attributes) == 1


@patch("rok4.vector.Table.__init__", return_value=Table)
def test_table_init_returns_an_instance_of_table(mocked_patch) -> None:
    """test __init__ constructor to check that an object of the
        class Table has been created

    Args:
        mocked_patch (str): decorator
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
    """test that the properties of the 'Table()' class are all ok"""
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
    }
    assert isinstance(table.attributes, dict)

    # Test property 'count'
    assert table.count == 256
    assert isinstance(table.count, int)


class FakeTable:
    """A fake table class for testing purposes."""

    def __init__(self, serializable):
        self._serializable = serializable

    @property
    def serializable(self):
        return self._serializable


def test_vector_serializable() -> None:
    """Test that the Vector class is serializable."""

    vector = Vector()

    # Create mock Table objects with known serializable output
    t1 = Table("table1", 1, "EPSG:4326", (0, 0, 1, 1), {"id": "int"}, ["geom"])
    t2 = Table("table2", 2, "EPSG:3857", (1, 1, 2, 2), {"name": "str"}, ["geom2"])

    vector.path = "/tmp/data.geojson"
    vector.tables = {"table1": t1, "table2": t2}

    expected = {"path": "/tmp/data.geojson", "tables": [t1.serializable, t2.serializable]}
    assert vector.serializable == expected


def test_table_serializable() -> None:
    """Test that the Table class is serializable."""
    name = "mytable"
    count = 42
    srs = "EPSG:4326"
    bbox = (1.0, 2.0, 3.0, 4.0)
    attributes = {"id": "Integer", "name": "String"}
    geometry_columns = ["geom"]

    table = Table(name, count, srs, bbox, attributes, geometry_columns)
    expected = {
        "name": name,
        "count": count,
        "srs": srs,
        "bbox": tuple(bbox),  # Tuple is redundant, but matches your code
        "attributes": attributes,
        "geometry_columns": geometry_columns,  # Note: typo in key, should be "geometry_columns"
    }
    assert table.serializable == expected


def test_vectorset_write_descriptor_with_path() -> None:
    """Test that write_descriptor correctly writes JSON to the provided path."""
    vectorset = VectorSet()
    
    # Create a simple vector with mock serializable data
    mock_vector = MagicMock()
    mock_vector.serializable = {"path": "test.geojson", "tables": []}
    vectorset.vectors = [mock_vector]
    
    with patch("rok4.vector.put_data_str") as mock_put_data_str:
        vectorset.write_descriptor("s3://bucket/descriptor.json")
        
        # Verify put_data_str was called with correct arguments
        mock_put_data_str.assert_called_once()
        args = mock_put_data_str.call_args[0]
        
        # Check the JSON content
        json_content = args[0]
        assert json.loads(json_content) == {"vectors": [{"path": "test.geojson", "tables": []}]}
        
        # Check the path
        assert args[1] == "s3://bucket/descriptor.json"


def test_vectorset_write_descriptor_without_path() -> None:
    """Test that write_descriptor does nothing when path is None."""
    vectorset = VectorSet()
    
    # Create a simple vector with mock serializable data
    mock_vector = MagicMock()
    mock_vector.serializable = {"path": "test.geojson", "tables": []}
    vectorset.vectors = [mock_vector]
    
    with patch("rok4.vector.put_data_str") as mock_put_data_str:
        vectorset.write_descriptor(None)
        
        # Verify put_data_str was NOT called
        mock_put_data_str.assert_not_called()


def test_vectorset_write_descriptor_json_format() -> None:
    """Test that write_descriptor produces correctly formatted JSON."""
    vectorset = VectorSet()
    
    # Create vectors with realistic data
    v1 = Vector()
    v1.path = "file1.geojson"
    v1.tables = {}
    
    v2 = Vector()
    v2.path = "file2.geojson"
    v2.tables = {}
    
    vectorset.vectors = [v1, v2]
    
    with patch("rok4.vector.put_data_str") as mock_put_data_str:
        vectorset.write_descriptor("/tmp/output.json")
        
        # Get the JSON content that was written
        json_content = mock_put_data_str.call_args[0][0]
        parsed = json.loads(json_content)
        
        # Verify structure
        assert "vectors" in parsed
        assert len(parsed["vectors"]) == 2
        assert parsed["vectors"][0]["path"] == "file1.geojson"
        assert parsed["vectors"][1]["path"] == "file2.geojson"
        assert parsed["vectors"][0]["tables"] == []
        assert parsed["vectors"][1]["tables"] == []


def test_vectorset_write_descriptor_storage_error() -> None:
    """Test that write_descriptor propagates StorageError when put_data_str fails."""
    vectorset = VectorSet()
    vectorset.vectors = []
    
    with patch("rok4.vector.put_data_str") as mock_put_data_str:
        mock_put_data_str.side_effect = StorageError("S3", "Failed to write")
        
        with pytest.raises(StorageError):
            vectorset.write_descriptor("/tmp/output.json")
