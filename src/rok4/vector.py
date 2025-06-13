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
from osgeo import gdal, ogr

# type de structures de données
from typing import List, Dict, Tuple

# package
from rok4.storage import copy, get_osgeo_path

# -- GLOBALS --

# Enable GDAL/OGR exceptions
ogr.UseExceptions()


class VectorSet:
    """ correspond à un ensemble de fichiers/objets vecteur
    """

    @classmethod
    def from_list(cls, path: str) -> "VectorSet":
        """Constructor method of a VectorSet from lists
        un fichier ou un objet contient une liste de chemins vers 
        les fichiers vecteurs ou objects vecteur

        Args:
            path (str): chemin du fichier vecteur ou objet vecteur

        Returns:
            VectorSet: jeu de fichiers/objets vecteur
        """
    
    @classmethod
    def from_descriptor(cls, path: str) -> "VectorSet":
        """Constructor method of a VectorSet from the descriptor
           un fichier ou un objet contient toutes les informations sur les fichiers vecteur ou objets vecteur

        Args:
            path (str): chemin du fichier vecteur ou objet vecteur

        Returns:
            VectorSet: jeu de fichiers/objets vecteur
        """

    @property
    def get_unique_srs_tables_list(srs: str)-> List[str]:
        """obtenir la liste des srs uniques des tables
        Args :
            srs (str) : système de référence spatiale des coordonnées
        Returns:
            List(str): liste des srs uniques des tables
        """
        return ["2154", "4326", "3857", "4210"," 4258"]

class Vector():
    """un fichier/un objet vecteur
    """
    # attributs de classe
    # chemin du fichier objet/vecteur
    _path: str = ""
    # la clé est le nom de la table et la valeur de l'instance de Table
    _tables: Dict[str, List[str]]  = {[]}

    @classmethod
    def from_file(cls, path: str) -> "Vector":
        """Constructor method of a Vector from file

        Args:
            path (str): chemin du fichier/objet vecteur

        Returns:
            Vector: fichier/objet S3 vecteur à partir du fichier
        """

    @classmethod
    def from_parameters(cls, path: str, tables:List[str]) -> "Vector":
        """Constructor method of a Vector from the descriptor

        Args:
            path (str): chemin du fichier objet/vecteur
            tables (List[str]): le nom de la table et la valeur de l'instance de Table

        Returns:
            Vector: fichier/objet s3 Vecteur à partir du descripteur
        """

    @property
    def get_unique_srs_tables_list(srs: str)-> List[str]:
        """obtenir la liste des srs uniques des tables
        Args :
            srs (str) : système de référence spatiale des coordonnées
        Returns:
            List[str]: la liste des srs uniques des tables
        """
        return ["2154", "4326", "3857", "4210"," 4258"]

class Table:
    """Une table vecteur
    """

    def __init__(self, name:str, attributes:Dict, count:int, srs:str, bbox:Tuple[float, float, float, float]) -> "Table":
        """constructeur de Table contenant les informations directement fournies

        Args:
            name (str): nom des objets
            attributes (Dict): nom des attributs (colonnes + types des colonnes)
            count (int): nombre d'objets
            srs (str): code correspondant au système de référence spatiale des coordonnées
            bbox (Tuple[float, float, float, float]): rectangle englobant

        Returns:
            Table: une instance de Table
        """
        self.__name = name
        self.__attributes = attributes
        self.__count = count
        self.__srs = srs
        self.__bbox = bbox

if __name__ == '__main__' :

    # Ci-dessous deux usages pour le chargement de données vecteur
    dirname = os.path.dirname(__file__)
    shpfilename = os.path.join(dirname, 'core-python/tests/fixtures/ARRONDISSEMENT.shp')
    shp_info = "ogrinfo -json ".shpfilename
    # On veut récupérer les informations à partir d'une liste : VectorSet.from_list -> Vector.from_file (usage de ogr pour récupérer les informations nécessaire) -> Table
    VectorSet.from_list(cls, path)
    Vector.from_file (shp_info)
    name = my_object1
    attributes = {"colonne1": str}
    count = 100
    srs = "2154"
    bbox = (100.0, 23.6, -6.93, 3.369)
    table1 = Table(name, attributes, count, srs, bbox)   
    # On veut récupérer les informations à partir d'un descripteur : VectorSet.from_descriptor (lecture de toutes les informations dans le descripteur) -> Vector.from_parameters -> Table
    VectorSet.from_descriptor (cls, path)
    Vector.from_parameters (cls, path, tables)
    name = my_object2
    attributes = {"colonne1": str}
    count = 3000
    srs = "2154"
    bbox = (100.0, 23.6, -6.93, 3.369)
    table2 = Table(name, attributes, count, srs, bbox)