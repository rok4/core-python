"""Provide class to read informations on vector data set from paths list of vector files or from descriptor file or S3 vector objects paths.

The aim is to have one module who allows to load important informations of a set of vector data.
Data can be vector files or S3 vector objects.

The module contains the three classes as follows:
    - VectorSet: Vector Data (Files/Objects) Set
    - Vector: Vector Data (File/Object)
    - Table: Table Data (name, attributes, count, srs, bbox, geometry_columns)

These classes would be necessary to make easily interactions between tools with these data.

Example:
    ```python
    from rok4.vector import VectorSet
    # from list of paths to vector data:
    vectorset = VectorSet.from_list("file://./filelist.txt")
    # or from descriptor:
    vectorset = VectorSet.from_descriptor("file://./vectorset.json")
    ```
"""

# -- IMPORTS --

# standard library
import json
import os
import tempfile
from typing import Dict, List, Tuple, Union

# 3rd party
from osgeo import ogr

# package
from rok4.exceptions import FormatError, StorageError
from rok4.storage import copy, get_data_str, get_osgeo_path, put_data_str

# -- GLOBALS --

# Enable GDAL/OGR exceptions
ogr.UseExceptions()


class VectorSet:
    """A set of vector files/objects.

    Attributes:
        vectors (List[Vector]): List of Vector instances
    """

    def __init__(self) -> None:
        """Initialize a VectorSet instance."""
        self.vectors: List["Vector"] = []

    @classmethod
    def from_list(cls, path: str) -> "VectorSet":
        """Create a VectorSet from a list file containing paths to vector data.

        Args:
            path (str): Path to a file or object containing a list of paths to vector data.
                Each line should contain one path. Lines starting with # are ignored.

        Returns:
            VectorSet: A new VectorSet instance with loaded vector data

        Raises:
            StorageError: If the list file cannot be read or copied
        """
        self = cls()
        self.vectors = []

        working_path = get_osgeo_path(path)

        tmp_list_obj = tempfile.NamedTemporaryFile(mode="r", delete=False)
        tmp_list_file = tmp_list_obj.name

        copy(working_path, tmp_list_file)

        with open(tmp_list_file) as file:
            for line in file:
                line = line.strip()
                if line and not line.startswith("#"):
                    vector = Vector.from_file(line)
                    self.vectors.append(vector)

        tmp_list_obj.close()
        os.remove(tmp_list_file)

        return self

    @classmethod
    def from_descriptor(cls, path: str) -> "VectorSet":
        """Create a VectorSet from a descriptor file containing all information about vector data.

        Args:
            path (str): Path to descriptor file (JSON format)

        Returns:
            VectorSet: A new VectorSet instance with loaded vector data

        Raises:
            FormatError: If the descriptor file is not valid JSON
            StorageError: If the descriptor file cannot be read
        """
        vectorset = cls()
        descriptor_file = path
        descriptor_object = []

        working_path = get_osgeo_path(descriptor_file)
        descriptor_file = working_path

        try:
            descriptor_object = json.loads(get_data_str(descriptor_file))
        except json.JSONDecodeError as e:
            raise FormatError("JSON", descriptor_object, e)

        for descriptor_item in descriptor_object:
            vector = Vector.from_parameters(
                descriptor_item["path"],
                descriptor_item["tables"],
            )
            vectorset.vectors.append(vector)

        return vectorset

    @property
    def srs(self) -> List[str]:
        """Get the list of unique SRS of the tables in the set.

        Returns:
            List[str]: List of unique SRS identifiers
        """
        srs_list = []

        # for each vector in the set, we get its SRS
        for vector in self.vectors:
            for srs in vector.srs:
                if srs not in srs_list:
                    srs_list.append(srs)
        return srs_list

    @property
    def serializable(self) -> Dict[str, Union[str, List[str]]]:
        """Get the serializable version of the vector set.

        Returns:
            Dict[str, Union[str, List[str]]]: Dictionary version compliant to the descriptor format
        """
        serialization = {"vectors": []}

        for vector in self.vectors:
            serialization["vectors"].append(vector.serializable)

        return serialization

    def write_descriptor(self, path: str = None) -> None:
        """Write descriptor as JSON format to the provided path or return as string.

        Args:
            path (str, optional): Complete path (file or object) where to write the JSON.
                Defaults to None, in which case the JSON is returned to the caller.

        Raises:
            StorageError: If the descriptor cannot be written to the specified path
        """
        content = json.dumps(self.serializable, sort_keys=True)

        if path is not None:
            put_data_str(content, path)


class Vector:
    """A vector file/object.

    Attributes:
        path (str): Path to the vector file/object
        tables (Dict[str, Table]): Dictionary of Table instances, keyed by table name
    """

    def __init__(self) -> None:
        """Initialize a Vector instance."""
        self.path: str = ""
        self.tables: Dict[str, "Table"] = {}

    @classmethod
    def from_file(cls, path: str) -> "Vector":
        """Create a Vector instance from a vector file or object.

        Args:
            path (str): Path to vector file/object

        Returns:
            Vector: A new Vector instance with loaded data

        Raises:
            StorageError: If the vector file/object cannot be opened
        """
        self = cls()
        self.path = path

        working_path = get_osgeo_path(path)
        datasource = ogr.Open(working_path)

        if datasource is None:
            raise StorageError("FILE", f"Cannot open vector file/object {working_path}")

        self.tables = {}

        for i in range(datasource.GetLayerCount()):
            layer = datasource.GetLayer(i)
            name = layer.GetName()
            count = layer.GetFeatureCount(0)
            srs = f"{layer.GetSpatialRef().GetAuthorityName(None)}:{layer.GetSpatialRef().GetAuthorityCode(None)}"
            bbox = (
                layer.GetExtent()[0],
                layer.GetExtent()[2],
                layer.GetExtent()[1],
                layer.GetExtent()[3],
            )
            geometry_columns = [layer.GetGeometryColumn()]

            attributes = {}
            if layer.GetFIDColumn() != "":
                attributes[layer.GetFIDColumn()] = "Integer"

            for j in range(layer.GetLayerDefn().GetFieldCount()):
                field = layer.GetLayerDefn().GetFieldDefn(j)
                attributes[field.GetName()] = field.GetTypeName()

            table_instance = Table(name, count, srs, bbox, attributes, geometry_columns)
            self.tables[name] = table_instance

        datasource = None

        return self

    @classmethod
    def from_parameters(cls, path: str, tables: Dict[str, "Table"]) -> "Vector":
        """Create a Vector instance from parameters.

        Args:
            path (str): Path to vector file/object
            tables (Dict[str, "Table"]): dictionary of table data with key-value pairs whose keys are table names and values are Table instances.

        Returns:
            Vector: A new Vector instance
        """
        self = cls()
        self.path = path
        self.tables = {}

        # Handle both list and dict formats
        if isinstance(tables, list):
            # List format from descriptor
            for table_data in tables:
                table_instance = Table(
                    name=table_data["name"],
                    count=table_data["count"],
                    srs=table_data["srs"],
                    bbox=tuple(table_data["bbox"]),
                    attributes=table_data["attributes"],
                    geometry_columns=table_data["geometry_columns"],
                )
                self.tables[table_data["name"]] = table_instance
        else:
            # Dict format
            for table_name, table_data in tables.items():
                table_instance = Table(
                    name=table_data["name"],
                    count=table_data["count"],
                    srs=table_data["srs"],
                    bbox=tuple(table_data["bbox"]),
                    attributes=table_data["attributes"],
                    geometry_columns=table_data["geometry_columns"],
                )
                self.tables[table_name] = table_instance

        return self

    @property
    def srs(self) -> List[str]:
        """Get the list of unique SRS of the tables in the vector data.

        Returns:
            List[str]: List of unique SRS identifiers
        """
        srs_list = []
        # for each table in the vector data, we get its SRS
        for table in self.tables.values():
            if table.srs not in srs_list:
                srs_list.append(table.srs)
        return srs_list

    @property
    def serializable(self) -> Dict[str, Union[str, List[str]]]:
        """Get the dictionary version corresponding to the descriptor of the vector data.

        Returns:
            Dict[str, Union[str, List[str]]]: Dictionary version compliant to the descriptor format
        """
        serialization = {"path": self.path, "tables": []}

        for table in self.tables.values():
            serialization["tables"].append(table.serializable)

        return serialization


class Table:
    """A table in a vector file/object.

    Attributes:
        name (str): Name of the table
        count (int): Number of features in the table
        srs (str): Spatial reference system of the table
        bbox (Tuple[float, float, float, float]): Bounding box (minX, minY, maxX, maxY)
        attributes (Dict[str, str]): Column names and their types
        geometry_columns (List[str]): Names of geometry columns
    """

    def __init__(
        self,
        name: str,
        count: int,
        srs: str,
        bbox: Tuple[float, float, float, float],
        attributes: Dict[str, str],
        geometry_columns: List[str],
    ) -> None:
        """Initialize a Table instance.

        Args:
            name (str): Name of the table
            count (int): Number of features in the table
            srs (str): SRS of the table
            bbox (Tuple[float, float, float, float]): Bounding box (minX, minY, maxX, maxY)
            attributes (Dict[str, str]): Column names and their types
            geometry_columns (List[str]): Names of geometry columns
        """
        self.name = name
        self.count = count
        self.srs = srs
        self.bbox = bbox
        self.attributes = attributes
        self.geometry_columns = geometry_columns

    @property
    def serializable(
        self,
    ) -> Dict[str, Union[str, int, Tuple[float, float, float, float], List[str]]]:
        """Get the dict version of the table, descriptor compliant.

        Returns:
            Dict[str, Union[str, int, Tuple[float, float, float, float], List[str]]]: Dictionary corresponding to the descriptor format
        """

        serialization = {
            "name": self.name,
            "count": self.count,
            "srs": self.srs,
            "bbox": tuple(self.bbox),
            "attributes": self.attributes,
            "geometry_columns": self.geometry_columns,
        }
        return serialization
