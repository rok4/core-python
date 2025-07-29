#!/usr/bin/env/ python3
"""Provide class to read informations on vector data set from paths list of vector files or descriptor file.
The aim is to have one module who allows to load important informations of a set of vector data.
Data can be files or S3 objects.
The module contains the three classes as follows :

- `VectorSets` - Data Vector Sets
- `Vector` - Data Vector
- `Table` - Table (name (name of the table), attributes ({names of columns : their types}), count (number of objects),
   srs (coordinates reference system), bbox (boundary box surrounding), geometry_columns (names of geometry columns))

These classes would be necessary to make easily interactions between tools with these data.
"""

# -- IMPORTS --

import json

# standard library
import os
import subprocess
from json.decoder import JSONDecodeError
from pathlib import Path
from typing import Union

import geojson

# 3rd party
from osgeo import ogr

from rok4.exceptions import FormatError, MissingAttributeError

# package
from rok4.storage import get_data_str, get_osgeo_path

# -- GLOBALS --

# Enable GDAL/OGR exceptions
ogr.UseExceptions()


class VectorSet:
    """correspond à un ensemble de fichiers/objets vecteur

    Attributes:
        __vectors (list["Vector"]): instances de Vector
    """

    def __init__(self) -> None:
        """Constructeur d'initialisation de la classe VectorSet"""

        self.__vectors: list["Vector"] = []
        self.__tables: dict[str, Table] = {}

    @classmethod
    def from_list(
        cls,
        path: str,
        tables: dict[
            str, list[dict[str, Union[str, int, tuple[float, float, float, float], list[str]]]]
        ],
    ) -> "VectorSet":
        """Constructor method of a VectorSet from lists
        un fichier ou un objet contient une liste de chemins vers les fichiers vecteurs ou objects vecteur

        Args:
            path (str): chemin du fichier vecteur ou objet vecteur (ex: "file://tests/fixtures/filelist.txt")
            tables (dict[str, list[dict[str,Union[str,int,tuple[float,float,float,float],list[str]]]]]): liste de paires clefs : nom de la table - valeurs associées à la table

        Raises:
            Exception: le chemin du fichier vecteur ou objet vecteur n'est pas valide

        Returns:
            VectorSet: jeu de fichiers/objets vecteur
        """

        vectorset = cls()

        vectorset.__tables = tables

        # récupération de chacun des chemins des fichiers vecteurs à partir de la "filelist.txt"
        with open(path) as list_files:
            list_path_vector_files = list_files.readlines()

        # on constitue la liste de tous les vecteurs  => jeu de données de fichiers/objets vecteur
        try:
            for index_path_vector_file in range(len(list_path_vector_files)):
                # récupération des jeux de données vecteurs à partir de la filelist.txt (liste des chemins des fichiers/objets vecteurs)
                vectorset.__vectors.append(
                    [
                        {"path": list_path_vector_files[index_path_vector_file]},
                        {"tables": vectorset.__tables[index_path_vector_file]},
                    ]
                )
        except OSError as error_not_valid_path:
            message_pattern: str = (
                f"le chemin du fichier vecteur ou objet vecteur n'est pas valide {path},{error_not_valid_path}.\n"
            )
            message = message_pattern.format(path=path, error=error_not_valid_path)
            raise Exception(message) from error_not_valid_path

        print("[VectorSet/from_list] vectorset.__vectors == " + str(vectorset.__vectors))
        print("\n")

        return vectorset

    @classmethod
    def from_descriptor(cls, path: str) -> "VectorSet":
        """Constructor method of a VectorSet from the descriptor
           un fichier ou un objet contient toutes les informations sur les fichiers vecteur ou objets vecteur

        Args:
            path (str): chemin du fichier vecteur ou objet vecteur (ex: "file://tests/fixtures/vectorset.json")

        Raises :
            FormatError : levée si les données ne sont pas parsables

        Returns:
            VectorSet: jeu de fichiers/objets vecteur
        """

        vectorset = cls()

        # on constitue la liste de tous les vecteurs => jeu de données de fichiers/objets vecteur
        try:
            vectorset.descriptor_file = json.loads(get_data_str(path))
        except JSONDecodeError as error_descriptor:
            # Parse du fichier descriptor JSON avec un message indiquant d'où vient l'erreur si jamais cela échoue
            message_pattern: str = f"Impossible de parser le JSON, {path}, {error_descriptor}\n"
            message = message_pattern.format(
                path=path,
                error=error_descriptor,
            )
            raise FormatError(message) from error_descriptor

        print(
            "[VectorSet/from_descriptor] vectorset.descriptor_file == "
            + str(vectorset.descriptor_file)
        )
        print("\n")

        # on obtient l'ensemble des jeux de données de fichier/objet vecteur à partir du fichier descriptor
        vectorset.__vectors = {
            "path": vectorset.descriptor_file[0]["path"],
            "tables": vectorset.descriptor_file[0]["tables"],
        }

        print("[VectorSet/from_descriptor] vectorset.__vectors == " + str(vectorset.__vectors))
        print("\n")

        return vectorset

    @property
    def get_unique_srs_tables_list(srs: str) -> list[str]:
        """obtenir la liste des srs uniques des tables
        Args :
            srs (str): système de référence spatiale des coordonnées
        Returns:
            list (str): liste des srs uniques des tables
        """

        return Vector.get_unique_srs_tables_list(srs)


class Vector:
    """un fichier/un objet vecteur

    Attributes:
        __path_vector_file (Path) : chemin du fichier/objet vecteur
        __tables (dict[str, Table]) : la clef est le nom de la table et la valeur de l'instance de Table
    """

    def __init__(self) -> None:
        """Constructeur d'initialisation de la classe Vector"""

        self.__path_vector_file: Path = ""
        self.__tables: dict[str, Table] = {}

        # initialisation des dictionnaires des vecteurs de données
        self.__vector_geojson = {}
        self.__vector_gpkg = {}
        self.__vector_shp = {}
        self.__vector_object = {}

    @classmethod
    def from_file(cls, path: str) -> "Vector":
        """Constructor method of a Vector from file

        Args:
            path (str): chemin du fichier/objet vecteur

        Raises:
            MissingAttributeError: l'attribut {error_key.args} est manquant dans le vecteur de données quand le programme traite les fichiers geopackage
            MissingAttributeError: l'attribut {error_key.args} est manquant dans le vecteur de données quand le programme traite les fichiers geojson
            MissingAttributeError: l'attribut {error_key.args} est manquant dans le vecteur de données quand le programme traite les fichiers shapefile
            Exception: levée d'exception quand le programme retourne une erreur dans l'exécution de la lecture du contenu du geojson quand le programme traite les fichiers geojson
            MissingAttributeError: l'attribut {error_key.args} est manquant dans le vecteur de données quand le programme traite les fichiers geojson
            RuntimeError: levée d'exception quand le programme retourne une erreur dans l'exécution de subprocess.checkoutput quand le programme traite les fichiers geopackage
            MissingAttributeError: l'attribut {error_key.args} est manquant dans le vecteur de données quand le programme traite les fichiers geopackage
            RuntimeError: levée d'exception quand le programme retourne une erreur dans l'exécution de subprocess.checkoutput quand le programme traite les fichiers shapefile
            MissingAttributeError: l'attribut {error_key.args} est manquant dans le vecteur de données quand le programme traite les fichiers shapefile
            MissingAttributeError: l'attribut {error_key.args} est manquant dans le vecteur de données quand le programme traite les objets vecteurs

        Returns:
            "Vector": fichier/objet S3 vecteur à partir du fichier
        """

        # instanciation
        vector = cls()

        # affectation
        vector.__path_vector_file = path

        # remplissage du dictionnaire : vector.__tables
        if vector.__path_vector_file.endswith("gpkg"):
            try:
                vector.__tables = {
                    tables[1][0]["name"]: Table(
                        tables[1][0]["name"],
                        tables[1][0]["srs"],
                        tables[1][0]["count"],
                        tables[1][0]["bbox"],
                        tables[1][0]["attributes"],
                        tables[1][0]["geometry_columns"],
                    ).__dict__,
                    tables[1][1]["name"]: Table(
                        tables[1][1]["name"],
                        tables[1][1]["srs"],
                        tables[1][1]["count"],
                        tables[1][1]["bbox"],
                        tables[1][1]["attributes"],
                        tables[1][1]["geometry_columns"],
                    ).__dict__,
                }
            except KeyError as error_key:
                raise MissingAttributeError(
                    f"l'attribut {error_key.args} est manquant dans le vecteur de données."
                )
        elif vector.__path_vector_file.endswith("geojson"):
            try:
                vector.__tables = {
                    tables[0][0]["name"]: Table(
                        tables[0][0]["name"],
                        tables[0][0]["srs"],
                        tables[0][0]["count"],
                        tables[0][0]["bbox"],
                        tables[0][0]["attributes"],
                        tables[0][0]["geometry_columns"],
                    ).__dict__,
                }
            except KeyError as error_key:
                raise MissingAttributeError(
                    f"l'attribut {error_key.args} est manquant dans le vecteur de données."
                )
        elif vector.__path_vector_file.endswith("shp"):
            try:
                vector.__tables = {
                    tables[2][0]["name"]: Table(
                        tables[2][0]["name"],
                        tables[2][0]["srs"],
                        tables[2][0]["count"],
                        tables[2][0]["bbox"],
                        tables[2][0]["attributes"],
                        tables[2][0]["geometry_columns"],
                    ).__dict__,
                }
            except KeyError as error_key:
                raise MissingAttributeError(
                    f"l'attribut {error_key.args} est manquant dans le vecteur de données."
                )
        else:
            pass

        print("[Vector/from_file] vector.__tables == " + str(vector.__tables))
        print("\n")

        # si on charge un fichier vecteur de type geojson => fichier d'extension *.geojson (ex : states.geojson)
        if vector.__path_vector_file.endswith("geojson"):

            try:
                with open(vector.__path_vector_file) as f:
                    vector.geojson_data_content = geojson.load(f)
            except Exception as error_reading_geojson:
                raise Exception(
                    f"Erreur à la lecture du contenu du geojson {error_reading_geojson.args}"
                )

            try:
                vector.__vector_geojson = {
                    "path": vector.__path_vector_file,
                    "tables": vector.__tables,
                    "data": vector.geojson_data_content,
                }
                print(
                    "[Vector/from_file] vector.__vector_geojson == " + str(vector.__vector_geojson)
                )
                print("\n")

            except KeyError as error_key:
                raise MissingAttributeError(
                    f"l'attribut {error_key.args} est manquant dans le vecteur de données."
                )

        # si on charge un fichier vecteur de type geopackage => fichier d'extension *.gpkg (ex : martinique.gpkg)
        elif vector.__path_vector_file.endswith("gpkg"):

            try:
                vector.gpkg_data_content = subprocess.check_output(
                    "ogrinfo -json " + vector.__path_vector_file,
                    shell=True,
                    stderr=subprocess.STDOUT,
                )

            except subprocess.CalledProcessError as error:
                raise RuntimeError(
                    "command '{}' return with error (code {}): {}".format(
                        error.cmd, error.returncode, error.output
                    )
                )

            try:
                vector.__vector_gpkg = {
                    "path": vector.__path_vector_file,
                    "tables": vector.__tables,
                    "data": vector.gpkg_data_content,
                }

                print("[Vector/from_file] vector.__vector_gpkg == " + str(vector.__vector_gpkg))
                print("\n")

            except KeyError as error_key:
                raise MissingAttributeError(
                    f"l'attribut {error_key.args} est manquant dans le vecteur de données."
                )

        # si on charge un fichier vecteur de type shapefile => fichier d'extension *.shp (ex : TM_WORLD_BORDERS-0.3.shp)
        elif vector.__path_vector_file.endswith("shp"):

            try:
                vector.shp_data_content = subprocess.check_output(
                    "ogrinfo -json " + vector.__path_vector_file,
                    shell=True,
                    stderr=subprocess.STDOUT,
                )

            except subprocess.CalledProcessError as error:
                raise RuntimeError(
                    "command '{}' return with error (code {}): {}".format(
                        error.cmd, error.returncode, error.output
                    )
                )

            try:
                vector.__vector_shp = {
                    "path": vector.__path_vector_file,
                    "tables": vector.__tables,
                    "data": vector.shp_data_content,
                }
                print("[Vector/from_file] vector.__vector_shp == " + str(vector.__vector_shp))
                print("\n")

            except KeyError as error_key:
                raise MissingAttributeError(
                    f"l'attribut {error_key.args} est manquant dans le vecteur de données."
                )

        elif vector.__path_vector_file.startswith("s3://"):

            vector.path_to_object_file = get_osgeo_path(vector.__path_vector_file)

            with open(vector.path_to_object_file) as geojson_file:
                vector.object_s3_data_content = get_data_str(geojson.load(geojson_file))

            try:
                vector.__vector_object = {
                    "path": vector.path_to_object_file,
                    "tables": vector.__tables,
                    "data": vector.object_s3_data_content,
                }
                print("[Vector/from_file] vector.__vector_object == " + str(vector.__vector_object))
                print("\n")

            except KeyError as error_key:
                raise MissingAttributeError(
                    f"l'attribut {error_key.args} est manquant dans le vecteur de données."
                )

        else:
            pass

        return vector

    @classmethod
    def from_parameters(cls, path: str, table: dict[str, "Table"]) -> "Vector":
        """Constructor method of a Vector from the descriptor

        Args:
            path (str): chemin du fichier objet/vecteur
            table (dict[str, "Table"]): la clef est le nom de la table et la valeur de l'instance de Table
        Raises:
            MissingAttributeError: l'attribut {error_key.args} est manquant dans le vecteur de données quand le programme traite les fichiers geopackage
            MissingAttributeError: l'attribut {error_key.args} est manquant dans le vecteur de données quand le programme traite les fichiers shapefile et geojson
            MissingAttributeError: l'attribut {error_key.args} est manquant dans le vecteur de données quand le programme traite les fichiers geojson
            MissingAttributeError: l'attribut {error_key.args} est manquant dans le vecteur de données quand le programme traite les fichiers geopackage
            MissingAttributeError: l'attribut {error_key.args} est manquant dans le vecteur de données quand le programme traite les fichiers shapefile
            MissingAttributeError: l'attribut {error_key.args} est manquant dans le vecteur de données quand le programme traite les objets vecteurs

        Returns:
            "Vector": fichier/objet s3 Vecteur à partir du descripteur ("file://tests/fixtures/vectorset.json")
        """

        # instanciation
        vector = cls()

        # affectation
        vector.__path_vector_file = path

        # remplissage du dictionnaire : vector.__tables
        if vector.__path_vector_file.endswith("gpkg"):
            try:
                vector.__tables = {
                    table[0]["name"]: Table(
                        table[0]["name"],
                        table[0]["srs"],
                        table[0]["count"],
                        table[0]["bbox"],
                        table[0]["attributes"],
                        table[0]["geometry_columns"],
                    ).__dict__,
                    table[1]["name"]: Table(
                        table[1]["name"],
                        table[1]["srs"],
                        table[1]["count"],
                        table[1]["bbox"],
                        table[1]["attributes"],
                        table[1]["geometry_columns"],
                    ).__dict__,
                }
            except KeyError as error_key:
                raise MissingAttributeError(
                    f"l'attribut {error_key.args} est manquant dans le vecteur de données."
                )
        else:
            try:
                vector.__tables = {
                    table[0]["name"]: Table(
                        table[0]["name"],
                        table[0]["srs"],
                        table[0]["count"],
                        table[0]["bbox"],
                        table[0]["attributes"],
                        table[0]["geometry_columns"],
                    ).__dict__,
                }
            except KeyError as error_key:
                raise MissingAttributeError(
                    f"l'attribut {error_key.args} est manquant dans le vecteur de données."
                )

        print("[Vector/from_parameters] vector.__tables == " + json.dumps(vector.__tables))
        print("\n")

        # récupérer les informations directement fournies dans les tables de données vecteurs
        if vector.__path_vector_file.endswith("geojson"):
            try:
                vector.__vector_geojson = {
                    "path": vector.__path_vector_file,
                    "tables": vector.__tables,
                    "data": str(vector.from_file(vector.__path_vector_file).geojson_data_content),
                }

                print(
                    "[Vector/from_parameters] vector.__vector_geojson == "
                    + str(vector.__vector_geojson)
                )
                print("\n")
            except KeyError as error_key:
                raise MissingAttributeError(
                    f"l'attribut {error_key.args} est manquant dans le vecteur de données."
                )

        elif vector.__path_vector_file.endswith("gpkg"):
            try:
                vector.__vector_gpkg = {
                    "path": vector.__path_vector_file,
                    "tables": vector.__tables,
                    "data": str(vector.from_file(vector.__path_vector_file).gpkg_data_content),
                }

                print(
                    "[Vector/from_parameters] vector.__vector_gpkg == " + str(vector.__vector_gpkg)
                )
                print("\n")
            except KeyError as error_key:
                raise MissingAttributeError(
                    f"l'attribut {error_key.args} est manquant dans le vecteur de données."
                )

        elif vector.__path_vector_file.endswith("shp"):
            try:
                vector.__vector_shp = {
                    "path": vector.__path_vector_file,
                    "tables": vector.__tables,
                    "data": str(vector.from_file(vector.__path_vector_file).shp_data_content),
                }

                print("[Vector/from_parameters] vector.__vector_shp == " + str(vector.__vector_shp))
                print("\n")
            except KeyError as error_key:
                raise MissingAttributeError(
                    f"l'attribut {error_key.args} est manquant dans le vecteur de données."
                )

        elif vector.__path_vector_file.startswith("s3://"):
            try:
                vector.__vector_object = {
                    "path": get_osgeo_path(vector.__path_vector_file),
                    "tables": vector.__tables,
                    "data": str(
                        vector.from_file(
                            get_osgeo_path(vector.__path_vector_file)
                        ).object_s3_data_content
                    ),
                }

                print(
                    "[Vector/from_parameters] vector.__vector_object == "
                    + str(vector.__vector_object)
                )
                print("\n")
            except KeyError as error_key:
                raise MissingAttributeError(
                    f"l'attribut {error_key.args} est manquant dans le vecteur de données."
                )

        else:
            pass

        return vector

    @property
    def get_unique_srs_tables_list(srs: str) -> list[str]:
        """obtenir la liste des srs uniques des tables
        Args :
            srs (str) : système de référence spatiale des coordonnées
        Returns:
            list[str]: la liste des srs uniques des tables
        """

        # initialisation
        list_uniq_srs_tables = []

        if Vector._path_vector_file.endswith("geojson"):
            print(
                "[Vector/get_unique_srs_tables_list] Vector._vector_geojson['tables']['crs']['properties']['name'] == "
                + json.dumps(Vector._vector_geojson["tables"]["crs"]["properties"]["name"])
            )
            list_uniq_srs_tables.append(
                Vector._vector_geojson["tables"]["crs"]["properties"]["name"]
            )
        elif Vector._path_vector_file.endswith("gpkg"):
            for index_layers in range(len(Vector._vector_gpkg["layers"])):
                for index_parameters in range(
                    len(
                        Vector._vector_gpkg["layers"][index_layers]["geometryFields"]["projjson"][
                            "parameters"
                        ]
                    )
                ):
                    list_uniq_srs_tables.append(
                        Vector._vector_gpkg["layers"][index_layers]["geometryFields"]["projjson"][
                            "parameters"
                        ][index_parameters]["id"]["code"]
                    )
                    print(
                        "[Vector/get_unique_srs_tables_list] Vector.Vector._vector_gpkg['layers'][index_layers]['geometryFields']['projjson']['parameters'][index_parameters]['id']['code'] == "
                        + json.dumps(
                            Vector._vector_gpkg["layers"][index_layers]["geometryFields"][
                                "projjson"
                            ]["parameters"][index_parameters]["id"]["code"]
                        )
                    )
        elif Vector._path_vector_file.endswith("shp"):
            for index_layers in range(len(Vector._vector_shp["layers"])):
                list_uniq_srs_tables.append(
                    Vector._vector_shp["layers"][index_layers]["geometryFields"]["id"]["code"]
                )
                print(
                    "[Vector/get_unique_srs_tables_list] Vector._vector_shp['layers'][index_layers]['geometryFields']['id']['code'] == "
                    + json.dumps(
                        Vector._vector_shp["layers"][index_layers]["geometryFields"]["id"]["code"]
                    )
                )
        elif Vector._path_vector_file.startswith("s3://"):
            print("[Vector/get_unique_srs_tables_list] Vector._vector_object")
        else:
            pass

        print(
            "[Vector/get_unique_srs_tables_list] list_uniq_srs_tables == "
            + str(list_uniq_srs_tables)
        )
        print("\n")

        return list_uniq_srs_tables


class Table:
    """Une table vecteur"""

    def __init__(
        self,
        name: str,
        attributes: dict[str, dict[str, str]],
        count: int,
        srs: str,
        bbox: tuple[float, float, float, float],
        geometry_columns: list[str],
    ) -> "Table":
        """constructeur de Table contenant les informations directement fournies

        Args:
            name (str): nom de la table
            attributes (dict[str,dict[str,str]]): {nom des colonnes : types des colonnes}
            count (int): nombre d'objets
            srs (str): système de référence spatiale des coordonnées
            bbox (tuple[float, float, float, float]): rectangle englobant
            geometry_columns (list[str]) : noms des colonnes géométriques

        Example:
            "tables": [
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

        Returns:
            Table: une instance de Table
        """

        # initialisation des attributs quand un nouvel objet est créé
        self.__name = name
        self.__attributes = attributes
        self.__count = count
        self.__srs = srs
        self.__bbox = bbox
        self.__geometry_columns = geometry_columns


if __name__ == "__main__":

    pathtoparentdir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

    # Ci-dessous deux usages pour le chargement de données vecteur
    ###############################################################################################
    # EXEMPLE 1 : FICHIER D'ENTREE => FICHIER GEOJSON DE DONNEES VECTEUR : 'states.geojson'       #
    ###############################################################################################
    # entrées
    table_geojson = [
        {
            "name": "states",
            "count": 52,
            "srs": "EPSG:3857",
            "bbox": (-19951818.272319775, 2017836.357428821, -7254560.414595957, 11553642.98126969),
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

    table_gpkg = [
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
                "nom_reg": "String",
            },
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
                "nom_reg": "String",
            },
        },
    ]

    table_shp = [
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
    tables = [table_geojson, table_gpkg, table_shp]
    pathtogeojsonfilename = os.path.join(pathtoparentdir, "tests/fixtures/states.geojson")
    pathtodescriptor = os.path.join(pathtoparentdir, "tests/fixtures/vectorset.json")
    pathtofilelisttxt = os.path.abspath(
        os.path.join(pathtoparentdir, "tests/fixtures/filelist.txt")
    )
    vectorset = VectorSet()

    # VectorSet.from_list -> Vector.from_file (usage de ogr pour récupérer les informations nécessaires) -> Table
    # On veut récupérer les informations à partir d'une liste : VectorSet.from_list -> Vector.from_file (usage de ogr pour récupérer les informations nécessaires) -> Table
    vectorset.from_list(pathtofilelisttxt, tables)
    Vector.from_file(pathtogeojsonfilename)

    # VectorSet.from_descriptor (lecture de toutes les informations dans le descripteur) -> Vector.from_parameters -> Table
    # On veut récupérer les informations à partir d'un descripteur : VectorSet.from_descriptor (lecture de toutes les informations dans le descripteur) -> Vector.from_parameters -> Table
    vectorset.from_descriptor(pathtodescriptor)
    Vector.from_parameters(pathtogeojsonfilename, table_geojson)

    # print (f'"{tables1[0]["srs"]}"'"\n")
    print("\n")

    # Ci-dessous deux usages pour le chargement de données vecteur
    ####################################################################################################
    # EXEMPLE 2 : FICHIER D'ENTREE => FICHIER GEOPACKAGE DE DONNEES VECTEUR : 'martinique.gpkg'        #
    ####################################################################################################
    # entrées
    pathtogpkgfilename = os.path.join(pathtoparentdir, "tests/fixtures/martinique.gpkg")
    vectorset = VectorSet()

    # VectorSet.from_list -> Vector.from_file (usage de ogr pour récupérer les informations nécessaires) -> Table
    # On veut récupérer les informations à partir d'une liste : VectorSet.from_list -> Vector.from_file (usage de ogr pour récupérer les informations nécessaires) -> Table
    vectorset.from_list(pathtofilelisttxt, tables)
    Vector.from_file(pathtogpkgfilename)

    # VectorSet.from_descriptor (lecture de toutes les informations dans le descripteur) -> Vector.from_parameters -> Table
    # On veut récupérer les informations à partir d'un descripteur : VectorSet.from_descriptor (lecture de toutes les informations dans le descripteur) -> Vector.from_parameters -> Table
    vectorset.from_descriptor(pathtodescriptor)
    Vector.from_parameters(pathtogpkgfilename, table_gpkg)

    # Ci-dessous deux usages pour le chargement de données vecteur
    ###########################################################################################################
    # EXEMPLE 3 : FICHIER D'ENTREE => FICHIER SHAPEFILE DE DONNEES VECTEUR : 'TM_WORLD_BORDERS-0.3.shp'       #
    ###########################################################################################################
    # entrées
    pathtoshpfilename = os.path.join(pathtoparentdir, "tests/fixtures/TM_WORLD_BORDERS-0.3.shp")
    vectorset = VectorSet()

    # VectorSet.from_list -> Vector.from_file (usage de ogr pour récupérer les informations nécessaires) -> Table
    # On veut récupérer les informations à partir d'une liste : VectorSet.from_list -> Vector.from_file (usage de ogr pour récupérer les informations nécessaires) -> Table
    vectorset.from_list(pathtofilelisttxt, tables)
    Vector.from_file(pathtoshpfilename)

    # VectorSet.from_descriptor (lecture de toutes les informations dans le descripteur) -> Vector.from_parameters -> Table
    # On veut récupérer les informations à partir d'un descripteur : VectorSet.from_descriptor (lecture de toutes les informations dans le descripteur) -> Vector.from_parameters -> Table
    vectorset.from_descriptor(pathtodescriptor)
    Vector.from_parameters(pathtoshpfilename, table_shp)
