"""Provide class to read informations on vector data set from paths list of vector files or from descriptor file or S3 vector objects paths.
The aim is to have one module who allows to load important informations of a set of vector data.
Data can be vector files or S3 vector objects.
The module contains the three classes as follows :

- `VectorSet` - Vector Data (Files/Objects) Set
- `Vector` - Vector Data (File/Object)
- `Table` - Table Data (name (name of the table), attributes ({names of columns : their types}), count (number of objects),
   srs (coordinates reference system), bbox (boundary box surrounding), geometry_columns (names of geometry columns))

These classes would be necessary to make easily interactions between tools with these data.
cf : specifications : "module de chargement de données vecteur" issue #97 dated 2025-06-05
=> three classes : 'VectorSet', 'Vector' et 'Table' with the main idea is to call only VectorSet class.
We must call only the two following constructors and have the same state at the end such as:
```python
from rok4.vector import VectorSet

vectorset = VectorSet.from_list("file://./filelist.txt")
# ou
vectorset = VectorSet.from_descriptor("file://./vectorset.json")
```
"""

# -- IMPORTS --

# standard library
import json
import os
import tempfile
from typing import List, Dict, Tuple, Union

# 3rd party
from osgeo import ogr

# package
from rok4.storage import copy, get_osgeo_path, put_data_str

# -- GLOBALS --

# Enable GDAL/OGR exceptions
ogr.UseExceptions()


class VectorSet:
    """
    correspond to a set of vector files/objects
     : List of vector data
     
    """
    __vectors: List["Vector"] = []  # type: ignore # instances of Vector class

    def __init__(self):
        """
        A file or an object containg all the informations to access the vector data (files/objects)

        :param path: Path to descriptor file
        """

        self.vectors: List["Vector"] = VectorSet.__vectors  # instances of Vector class

    @classmethod
    def from_list(cls, path:str):
        """
        A file or an object containg a list of path to vector data (files/objects)

        :param path: List of path to vector data
        """


    @classmethod
    def from_descriptor(cls, path:str):
        """
        A file or an object containg all the informations to access the vector data (files/objects)

        :param path: Path to descriptor file
        """
    
    @property
    def srs(self)->List[str]:
        """
        Get the list of uniq SRS of the tables in the set

        :return: List of SRS
        :rtype: List[str]
        """
    
    @property
    def serializable(self)->Dict[str, Union[str, List[str]]]:
        """
        dictiionary corresponding to the descriptor of the vector set
        """
        serialization = {"bbox": list(self.bbox), "srs": self.srs, "colors": [], "raster_list": []}
        for color in self.colors:
            color_serial = {"bands": color[0], "format": color[1].name}
            serialization["colors"].append(color_serial)
        for raster in self.raster_list:
            raster_dict = {
                "path": raster.path,
                "dimensions": list(raster.dimensions),
                "bbox": list(raster.bbox),
                "bands": raster.bands,
                "format": raster.format.name,
            }
            if raster.mask is not None:
                raster_dict["mask"] = raster.mask
            serialization["raster_list"].append(raster_dict)

        return serialization

    def write_descriptor(self, path: str = None) -> None:
        """Print descriptor as JSON format to the provided path, in the standard output if not provided

        Args:
            path (str, optional): Complete path (file or object) where to print the JSON. Defaults to None, JSON is printed to standard output.
        """
        content = json.dumps(self.serializable, sort_keys=True)
        if path is None:
            print(content)
        else:
            put_data_str(content, path)

class Vector:
    """A vector file/Object 
    """
    __path = ""  # path of the vector file/object
    __tables = {}  # dictionnary of Table instances, key is the name of the table and the value the instance of Table class

    def __init__(self):
        """
        to retrieve information directly

        :param path: Path to vector file/object
        :param tables: List of table names to consider in the vector data (default: all tables)
        """
        self.path = Vector.__path
        self.tables = Vector.__tables

    @classmethod
    def from_file(cls, path:str):
        """
        to retrieve information from a vector file or a vector object

        :param path: Path to vector file
        """


    @classmethod
    def from_parameters(cls, path:str, tables:Dict[str, "Table"]):
        """
        to retrieve information directly

        :param path: Path to vector file/object
        :param tables: List of table names to consider in the vector data (default: all tables)
        """

    @property
    def srs(self)->List[str]:
        """
        Get the list of uniq SRS of the tables in the vector data

        :return: List of SRS
        :rtype: List[str]
        """
    
    @property
    def serializable(self)->Dict[str, Union[str, List[str]]]:
        """
        dictiionary corresponding to the descriptor of the vector data
        """
        serialization = {"path": self.path, "tables": []}
        for table in self.tables.values():
            serialization["tables"].append(table.serializable)
        return serialization

class Table:
    """A table file/Object """

    def __init__(self, name:str, count: int, srs:str, bbox:Tuple[float, float, float, float], attributes:Dict[str, str], geometry_colums:Dict[str, str]):
        """
        to retrieve information directly

        :param name: Name of the table
        :param count: Number of features in the table
        :param srs: SRS of the table
        :param bbox: Bounding box of the table (minX, minY, maxX, maxY)
        :param attributes: Name of the columns and their type (key is the name of the attribute and value is the type of the attribute)
        :param geometry_colums: Name of the geometry columns (key is the name of the geometry column and value is the type of the geometry column)
        """
        self.name = name
        self.count = count
        self.srs = srs
        self.bbox = bbox
        self.attributes = attributes
        self.geometry_colums = geometry_colums

    @property
    def serializable(self)->Dict[str, Union[str, int, Tuple[float, float, float, float], Dict[str, str]]]:
        """
        dictiionary corresponding to the descriptor of the table
        """
        serialization = {
            "name": self.name,
            "count": self.count,
            "srs": self.srs,
            "bbox": list(self.bbox),
            "attributes": self.attributes,
            "geometry_colums": self.geometry_colums,
        }
        return serialization
    
if __name__ == "__main__":

    pathtoparentdir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

    # Ci-dessous deux usages pour le chargement de données vecteur à partir de 'vectorset':
    ############################################################################################################
    # EXEMPLE 1 : FICHIER D'ENTREE => FICHIER CONTENANT LES CHEMINS DES DONNEES VECTEUR : 'filelist.txt'       #
    ############################################################################################################
    # entrées
    pathtofilelisttxt = os.path.abspath(
        os.path.join(pathtoparentdir, "tests/fixtures/filelist.txt")
    )
    vectorset = VectorSet()
    # VectorSet.from_list -> Vector.from_file (usage de ogr pour récupérer les informations nécessaires) -> Table
    # On veut récupérer les informations à partir d'une liste : VectorSet.from_list -> Vector.from_file (usage de ogr pour récupérer les informations nécessaires) -> Table
    vectorset.from_list(pathtofilelisttxt)

    ###################################################################################
    # EXEMPLE 2 : FICHIER D'ENTREE => FICHIER DU DESCRIPTEUR : 'vectorset.json'       #
    ###################################################################################
    # entrées
    pathtodescriptor = os.path.join(pathtoparentdir, "tests/fixtures/vectorset.json")
    vectorset = VectorSet()
    # On veut récupérer les informations à partir d'un fichier geojson : Vector.from_file(pathtogeojsonfilename) -> Table
    # VectorSet.from_descriptor (lecture de toutes les informations dans le descripteur) -> Vector.from_parameters -> Table
    # On veut récupérer les informations à partir d'un descripteur : VectorSet.from_descriptor (lecture de toutes les informations dans le descripteur) -> Vector.from_parameters -> Table
    vectorset.from_descriptor(pathtodescriptor)