"""Provide class to read informations on vector data set from list or descriptor
The aim is to have one module who allows to load important informations of a set of vector data
Data can be files or S3 objects.
The module contains the following class :

- `VectorSets` - Data Vector Sets
- `Vector` - Data Vector
- `Table` - Table(name, attributes(columns, types of attributes), count, srs, bbox)
These classes would be necessary to make easily interactions between tools with these data.
"""

# -- IMPORTS --

# standard library
import os
import tempfile

# 3rd party
from osgeo import ogr

# type de structures de données
from typing import List, Dict, Tuple

# package
from rok4.storage import copy, get_osgeo_path

# -- GLOBALS --

# Enable GDAL/OGR exceptions
ogr.UseExceptions()

# On veut récupérer les informations à partir d'une liste : VectorSet.from_list -> Vector.from_file (usage de ogr pour récupérer les informations nécessaire) -> Table

shp_info = "ogrinfo -json -so -al ".shapefile
VectorSet.from_list(cls, path: str) -> Vector.from_file (shp_info) -> Table    
    
# On veut récupérer les informations à partir d'un descripteur : VectorSet.from_descriptor (lecture de toutes les informations dans le descripteur) -> Vector.from_parameters -> Table

VectorSet.from_descriptor (cls, path: str) -> Vector.from_parameters (cls, path: str, tables:List[str])-> Table

class VectorSet:
    """ correspond à un ensemble de fichiers/objets vecteur
    """

    @classmethod
    def from_list(cls, path: str) -> "VectorSet":
        """Constructor method of a VectorSet from lists
        un fichier ou un objet contient une liste de chemins vers 
        les fichiers vecteurs ou objects vecteur"""
    
    @classmethod
    def from_descriptor(cls, path: str) -> "VectorSet":
        """Constructor method of a VectorSet from the descriptor
           un fichier ou un objet contient toutes les informations sur les fichiers vecteur ou objets vecteur"""

    @property
    def get_unique_srs_tables_list(srs: str)-> List[str]
        """obtenir la liste des srs uniques des tables
        """
        return ["2154", "4326"]

class Vector:
    """un fichier/un objet vecteur
    """
    # attributs de classe
    # chemin du fichier objet/vecteur
    _path: str = ""
    # la clé est le nom de la table et la valeur de l'instance de Table
    _tables: Dict[Table]  = {[]}

    @classmethod
    def from_file(cls, path: str) -> "Vector":
        """Constructor method of a Vector from file"""

    @classmethod
    def from_parameters(cls, path: str, tables:List[str]) -> "Vector":
        """Constructor method of a Vector from the descriptor"""

    @property
    def get_unique_srs_tables_list(srs: str)->List[str]
        """obtenir la liste des srs uniques des tables
        """
        return ["2154", "4326"]

class Table:
    """Une table vecteur
    """

    def __init__(self, name:str, attributes:Dict, count:int, srs:str, bbox:Tuple[float, float, float, float]) -> "Table":
        """constructeur de Table contenant les informations directement fournies

        Args:
            name (str): _description_
            attributes (Dict): _description_
            count (int): _description_
            srs (str): _description_
            bbox (Tuple[float, float, float, float]): _description_

        Returns:
            Table: _description_
        """
        self.__name = name
        self.__attributes = attributes
        self.__count = count
        self.__srs = srs
        self.__bbox = bbox