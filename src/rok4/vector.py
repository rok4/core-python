#!/usr/bin/env/ python3
"""Provide class to read informations on vector data set from paths list of vector files or from descriptor file or S3 vector objects paths.
The aim is to have one module who allows to load important informations of a set of vector data.
Data can be vector files or S3 vector objects.
The module contains the three classes as follows :

- `VectorSets` - Data Vector Sets
- `Vector` - Data Vector
- `Table` - Table (name (name of the table), attributes ({names of columns : their types}), count (number of objects),
   srs (coordinates reference system), bbox (boundary box surrounding), geometry_columns (names of geometry columns))

These classes would be necessary to make easily interactions between tools with these data.
cf : documentation de spécifications : module de chargement de données vecteur issue #97 datant du 5 juin 2025
"""

# -- IMPORTS --

# standard library
import os
import json
import subprocess
import geojson
import tempfile
from pathlib import Path
from typing import Union
from json.decoder import JSONDecodeError
from osgeo import ogr

# local : autres librairies de rok4
from rok4.storage import (
    copy,
    get_data_str,
    get_osgeo_path
)
from rok4.exceptions import FormatError, MissingAttributeError, StorageError

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

        # Liste des instances de la classe Vector représentant chaque fichier/objet vecteur du jeu de données
        self.__vectors: list["Vector"] = []
  
    @classmethod
    def from_list(
        cls,
        path_list_vector_files: str,

    ) -> "VectorSet":
        """Créer un VectorSet à partir de la liste des chemins des fichiers vecteurs.

        Args:
            path_list_vector_files (str): le chemin du fichier contenant la liste des chemins des fichiers vecteurs.

        Raises:
            Exception: si le fichier ne peut pas être copié depuis l'emplacement source de la liste vers le fichier temporaire.
            Exception: si le fichier filelist.txt existe.
            Exception: si le fichier filelist.txt est un fichier.
            Exception: si le fichier filelist.txt n'est pas lisible.
            Exception: si le fichier/objet vecteur existe.
            Exception: si le fichier n'est pas lisible.
            Exception: si le fichier n'est pas un fichier GeoJSON non valide.
            Exception: si le fichier n'est pas un fichier shapefile valide.
            Exception: si le fichier n'est pas un fichier geopackage valide.
            Exception: si le fichier contient des chemins de vecteurs non valides.
            Exception: si le fichier n'est pas dans le format attendu.
            Exception: si le chemin du fichier vecteur ou objet vecteur est vide.
            Exception: si le chemin de l'objet vecteur est bien un objet s3.
            Exception: si le chemin du fichier vecteur ou objet vecteur est un fichier.
            Exception: si l'instance de Vector est vide.
            Exception: si le jeu de données de fichiers/objets vecteur est vide.
            Exception: si le fichier ne contient aucun chemin de vecteur valide.
    
        Returns:
            VectorSet: une instance de VectorSet créée à partir de la liste des chemins du fichier vecteur.
        """

        # Création d'une nouvelle instance de VectorSet pour stocker les vecteurs du jeu de données
        self = cls()

        # initialisation des listes
        list_path_vector_files = []
        invalid_paths = []

        # Création du fichier temporaire
        tmp_list_obj = tempfile.NamedTemporaryFile(mode="r", delete=False)

        # Récupération du chemin vers le fichier temporaire
        tmp_list_file = tmp_list_obj.name

        # Copie depuis l'emplacement source de la liste vers le fichier temporaire
        try: 
            # pour être copié, l'emplacement source de la liste doit être un fichier ou un objet et être lisible
            if (Path(path_list_vector_files).is_file() or Path(path_list_vector_files).is_socket()) and os.access(path_list_vector_files, os.R_OK):
                copy(path_list_vector_files, tmp_list_file)
        except Exception as error_copy:
            raise StorageError("FILE", f"Cannot copy file {path_list_vector_files} to {tmp_list_file} : {error_copy}")

        tmp_list_obj.close()

        # on vérifie si le fichier 'filelist.txt' vecteur existe
        if not Path(tmp_list_file).exists():
            raise Exception(f"le fichier 'filelist.txt' n'existe pas {tmp_list_file}.")

        # on vérifie si le fichier 'filelist.txt' est un fichier
        if not Path(tmp_list_file).is_file():
            raise Exception(f"le chemin du fichier 'filelist.txt' n'est pas un fichier {tmp_list_file}.")
        
        # on vérifie si le fichier 'filelist.txt' est lisible
        if not os.access(tmp_list_file, os.R_OK):
            raise Exception(f"le fichier 'filelist.txt' n'est pas lisible {tmp_list_file}.")

        # récupération de chacun des chemins des fichiers vecteurs à partir de la "filelist.txt"
        with open(tmp_list_file) as list_files:
            list_path_vector_files = list_files.readlines()

        # on parcourt la liste des chemins des fichiers vecteurs
        for path_vector_file in list_path_vector_files:

            # on enlève les espaces et les retours à la ligne
            path_vector_file = path_vector_file.strip()

            # on remplace le chemin du fichier vecteur ou objet vecteur par le chemin du fichier de test "tests/fixtures"
            path_vector_file = path_vector_file.replace('file://./data','tests/fixtures')
            print(f"[VectorSet/from_list] path_vector_file == {path_vector_file}")

            # vérifier si les fichiers geojson, geopackage et shapefile dont les chemins 
            # donnant accès à ces fichiers existent bien, sont lisibles et sont valides

            if path_vector_file.endswith(".geojson"):
                try:
                    with open(path_vector_file) as geojson_file:
                        data = geojson.load(geojson_file)
                    if "type" not in data or data["type"] != "FeatureCollection":
                        raise Exception(f"{path_vector_file} is not a valid GeoJSON FeatureCollection.")
                    if "features" not in data or not isinstance(data["features"], list):
                        raise Exception(f"{path_vector_file} does not contain a valid 'features' list.")
                except Exception as e:
                    raise Exception(f"GeoJSON file {path_vector_file} is invalid: {e}")

            elif path_vector_file.endswith(".gpkg") or path_vector_file.endswith(".shp"):
                datasource = ogr.Open(path_vector_file)
                if not datasource or datasource.GetLayerCount() == 0:
                    raise Exception(f"{path_vector_file} is not a valid Geopackage or Shapefile.")
            else:
                raise Exception(f"Unsupported file type for {path_vector_file}")

            # Vérification du chemin du fichier ou objet vecteur
            if not path_vector_file or path_vector_file.startswith("s3://") or not os.path.isfile(path_vector_file) or not os.path.exists(path_vector_file) or not os.access(path_vector_file, os.R_OK):
                print(f"[VectorSet/from_list] chemin de vecteur non valide : {path_vector_file}")
                invalid_paths.append(path_vector_file)
                continue

            # on vérifie si le chemin du fichier vecteur ou objet vecteur est vide
            if not path_vector_file:
                print(f"[VectorSet/from_list] vector.__path_vector_file == {path_vector_file}")
                raise Exception(f"le fichier vecteur ou objet vecteur {path_vector_file} est vide.")
            
            # on vérifie si le chemin de l'objet vecteur est un objet S3
            if path_vector_file.startswith("s3://"):
                print(f"[VectorSet/from_list] vector.__path_vector_file == {path_vector_file}")
                raise Exception(f"l'objet vecteur {path_vector_file} est bien un objet S3.")
            
            # on vérifie si le chemin du fichier vecteur est un fichier
            if not Path(path_vector_file).is_file():
                print(f"[VectorSet/from_list] vector.__path_vector_file == {path_vector_file}")
                raise Exception(f"le fichier vecteur ou objet vecteur {path_vector_file} n'est pas un fichier.")
            
            # on vérifie si le fichier vecteur ou objet vecteur existe
            if not Path(path_vector_file).exists():
                print(f"[VectorSet/from_list] vector.__path_vector_file == {path_vector_file}")
                raise Exception(f"le fichier vecteur ou objet vecteur {path_vector_file} n'existe pas.")
            
            # on vérifie si le fichier vecteur ou objet vecteur est lisible
            if not os.access(path_vector_file, os.R_OK):
                print(f"[VectorSet/from_list] vector.__path_vector_file == {path_vector_file}")
                raise Exception(f"le fichier vecteur ou objet vecteur {path_vector_file} n'est pas lisible.")
            print(f"[VectorSet/from_list] le fichier vecteur ou objet vecteur, {path_vector_file}, est lisible")

            # on crée une instance de Vector à partir du chemin du fichier vecteur
            # On fait appel au constructeur `Vector.from_file` avec ce chemin fichier ou objet.
            # Le constructeur de Vector va alors convertir le chemin en chemin "osgeo" 
            # avec `get_osgeo_path` du module `storage`
            vector = Vector.from_file(get_osgeo_path(path_vector_file))

            print(f"[VectorSet/from_list] instance de Vector == {str(vector.__dict__)}")
            print("\n")

            if not vector:
                invalid_paths.append(path_vector_file)
                continue

            # on ajoute l'instance de Vector à la liste des vecteurs pour constituer la liste
            # de tous les vecteurs => jeu de données de fichiers/objets vecteur
            self.__vectors.append(vector)

        # on vérifie si le jeu de données de fichiers/objets vecteur obtenu est vide
        if not self.__vectors:
            raise Exception(f"le jeu de données de fichiers/objets vecteur obtenu est vide.")
        
        if invalid_paths:
            raise Exception(f"Le fichier 'filelist.txt' contient des chemins de vecteurs non valides : {invalid_paths}")

        # on vérifie que toutes les clefs et valeurs de chaque instance de Vector sont toutes présentes
        # et on lève une exception si un attribut est manquant ou vide

        REQUIRED_VECTOR_KEYS = ["path", "tables"]

        for index_vector, vector in enumerate(self.__vectors):
            if isinstance(vector, dict):
                for key_vector in REQUIRED_VECTOR_KEYS:
                    if key_vector not in vector or not vector[key_vector]:
                        raise MissingAttributeError(
                            f"Key '{key_vector}' is missing or empty in vector at index {index_vector}: {vector}", missing=self.__vectors
                        )
            elif isinstance(vector, list):
                if not vector:
                    raise MissingAttributeError(
                        f"Vector at index {index_vector} is an empty list: {vector}", missing=self.__vectors
                    )
                for index_subvector, subvector in enumerate(vector):
                    if not isinstance(subvector, dict):
                        raise MissingAttributeError(
                            f"Element at index {index_subvector} in vector list at index {index_vector} is not a dict: {subvector}", missing=self.__vectors
                        )
                    for key_vector in REQUIRED_VECTOR_KEYS:
                        if key_vector not in subvector or not subvector[key_vector]:
                            raise MissingAttributeError(
                                f"Key '{key_vector}' is missing or empty in subvector at index {index_subvector} of vector list at index {index_vector}: {subvector}", missing=self.__vectors
                            )
            elif hasattr(vector, "_Vector__path_vector_file") and hasattr(vector, "_Vector__tables"):
                if not getattr(vector, "_Vector__path_vector_file"):
                    raise MissingAttributeError(
                        f"Attribute '_Vector__path_vector_file' is missing or empty in vector at index {index_vector}: {vector}", missing=self.__vectors
                    )
                if not getattr(vector, "_Vector__tables") and not getattr(vector,"_Vector__tables") != "":
                    raise MissingAttributeError(
                        f"Attribute '_Vector__tables' is missing in vector at index {index_vector}: {vector}", missing=self.__vectors
                    )
            else:
                raise MissingAttributeError(
                    f"Vector at index {index_vector} is not a valid dict, list, or Vector instance: {vector}", missing=self.__vectors
                )
            
        # on supprime le fichier temporaire
        os.remove(tmp_list_file)

        print(
            "[VectorSet/from_list] self.__vectors == "
            + str(self.__vectors)
        )
        print("\n")

        return self
    
    @classmethod
    def from_descriptor(cls, path_descriptor_file: str) -> "VectorSet":
        """créer un VectorSet à partir du fichier du descriptor.

        Args:
            path_descriptor_file (str): chemin donnant accès au fichier descriptor

        Raises:
            Exception: si le fichier du descriptor n'existe pas.
            Exception: si le fichier du descriptor n'est pas un fichier.
            Exception: si le fichier du descriptor n'est pas lisible.
            RuntimeError: la commande avec le retour d'erreur.
            FormatError: si le fichier du descriptor n'est pas dans le format attendu.

        Returns:
            VectorSet: une instance de VectorSet est créée à partir du fichier du descriptor.
        """

        # Création d'une nouvelle instance de VectorSet pour stocker les vecteurs du jeu de données
        vectorset = cls()

        # on vérifie si le fichier du descriptor existe
        if not Path(path_descriptor_file).exists():
            raise Exception(f"le fichier du descriptor n'existe pas {path_descriptor_file}.")

        # on vérifie si le fichier du descriptor est un fichier
        if not Path(path_descriptor_file).is_file():
            raise Exception(f"le fichier du descriptor n'est pas un fichier {path_descriptor_file}.")
        
        # on vérifie si le fichier du descriptor est lisible
        if not os.access(path_descriptor_file, os.R_OK):
            raise Exception(f"le fichier du descriptor n'est pas lisible {path_descriptor_file}.")
        
        # on valide le fichier du descriptor contenant des données JSON pour
        # s'assurer que le contenu du fichier est bien un document JSON valide.
        try:
            subprocess.check_output("python3 -m json.tool "+path_descriptor_file, shell=True, stderr=subprocess.STDOUT
                )
        except subprocess.CalledProcessError as error:
            raise RuntimeError(
                f"command '{error.cmd}' return with error (code {error.returncode}): {error.output}"
            )
        
        print("[VectorSet/from_descriptor] le fichier du descriptor contient bien des données JSON valides.""\n")

        # on recourt à json.loads() pour lire le fichier JSON et le convertir en un objet Python correspondant sous forme d'une liste.
        try:
            vectorset.__descriptor_object = json.loads(get_data_str(path_descriptor_file))
        except JSONDecodeError as e:
            raise FormatError("JSON", vectorset.__descriptor_object, e)
        
        print("[VectorSet/from_descriptor] le fichier du descriptor a bien été converti en un objet Python correspondant sous forme d'une liste.""\n")

        print(
            "[VectorSet/from_descriptor] vectorset.__descriptor_object == "
            + str(vectorset.__descriptor_object)
        )
        print("\n")

        # On vérifie si toutes les clefs du vecteur et des tables du vecteur sont toutes présentes.
        
        REQUIRED_VECTOR_KEYS = ["path", "tables"]
        REQUIRED_TABLE_KEYS = ["name", "srs", "count", "bbox", "attributes", "geometry_columns"]

        for index_desc, vector_desc in enumerate(vectorset.__descriptor_object):

            # Vérifier les clefs et les valeurs au niveau du vecteur
            for key_vector in REQUIRED_VECTOR_KEYS:
                if key_vector not in vector_desc or not vector_desc[key_vector]:
                    raise MissingAttributeError(
                        f"Key '{key_vector}' is missing or empty in descriptor at index {index_desc}: {vector_desc}, missing={vector_desc}")
            
            # Vérifier les tables du vecteur
            tables = vector_desc["tables"]
            if not isinstance(tables, list) or not tables:
                raise MissingAttributeError(
                    f"'tables' is missing or empty in descriptor at index {index_desc}: {vector_desc}, missing={vector_desc}")
            for index_table, table in enumerate(tables):
                if not isinstance(table, dict):
                    raise MissingAttributeError(
                        f"Table at index {index_table} in descriptor at index {index_desc} is not a dict: {table}, missing={vector_desc}")
            
                for key_table in REQUIRED_TABLE_KEYS:
                    if key_table not in table or table[key_table] in [None, "", [], {}]:
                        raise MissingAttributeError(
                            f"Key '{key_table}' is missing or empty in table at index {index_table} of descriptor at index {index_desc}: {table}, missing={vector_desc}")

        # on obtient l'ensemble des jeux de données de fichier/objet vecteur à partir du fichier descriptor    
        for index_descriptor_object in range(len(vectorset.__descriptor_object)): 
            # on remplace le chemin du fichier vecteur ou objet vecteur par le chemin du fichier de test "tests/fixtures"
            vectorset.__descriptor_object[index_descriptor_object]["path"] = vectorset.__descriptor_object[index_descriptor_object]["path"].replace('file://./data','tests/fixtures')
            # Pour chaque dictionnaire dans la liste, on fait appel au constructeur `Vector.from_parameters` avec ce dictionnaire
            # 1°) récupération de tous les attributs de Vector dans le dictionnaire en entrée (`path`)
            # 2°) puis, pour chaque table dans le champ `tables`, faire appel au constructeur de Table avec tous les éléments suivants:
            vector = Vector.from_parameters(get_osgeo_path(vectorset.__descriptor_object[index_descriptor_object]["path"]), vectorset.__descriptor_object[index_descriptor_object]["tables"])
            # On ajoute l'objet vector créé dans l'attribut `__vectors` du VectorSet
            vectorset.__vectors.append(vector)

        print(
            "[VectorSet/from_descriptor] vectorset.__vectors == "
            + str(vectorset.__vectors)
        )
        print("\n")

        return vectorset

    @property
    def get_uniq_srs_tables_list(self) -> list[str]:
        """Retourne la liste unique des SRS de toutes les tables de tous les vecteurs du VectorSet.

        Returns:
            list[str]: la liste unique des SRS de toutes les tables de tous les vecteurs du VectorSet
        """

        # on initialise le set de srs de toutes les tables de tous les vecteurs du VectorSet
        uniq_srs_set_all_tables_of_all_vectors = set()

        for vector in self.__descriptor_object:
            # Cas où vector est un dict (tiré de from_descriptor)
            if isinstance(vector, dict) and "tables" in vector:
                tables = vector["tables"]
                for table_dict in tables:
                    if isinstance(table_dict, dict) and "srs" in table_dict:
                        uniq_srs_set_all_tables_of_all_vectors.add(table_dict["srs"])
            # Cas où vector est une instance de Vector
            elif hasattr(vector, "get_uniq_srs_tables_list"):
                uniq_srs_set_all_tables_of_all_vectors.add(vector.get_uniq_srs_tables_list)
            
        print("[Vectorset/get_uniq_srs_tables_list] uniq_srs_set_all_tables_of_all_vectors == "+str(list(uniq_srs_set_all_tables_of_all_vectors)))
        
        return list(uniq_srs_set_all_tables_of_all_vectors)


class Vector:
    """un fichier/un objet vecteur

    Attributes:
        __path_vector_file (str) : chemin du fichier/objet vecteur
        __tables (list[dict[str, list[dict[str,Union[str,int,tuple[float,float,float,float],dict[str,str],list[str]]]]]]) : liste de dictionnaires associant paires clefs-valeurs : la clef est le nom de la table et la valeur de l'instance de Table
    """

    def __init__(self) -> None:
        """Constructeur d'initialisation de la classe Vector"""

        self.__tables: list[dict[str, list[dict[str,Union[str,int,tuple[float,float,float,float],dict[str,str],list[str]]]]]] = []
     
    @staticmethod
    def scrub_data_content_list(data_list: list[str])-> list[str]:
        """remplacer les éléments vides dans l'ancienne liste par une nouvelle liste sans élément vide

        Args:
            data_list (list[str]): liste à remplacer les éléments vides dans l'ancienne

        Returns:
            list[str]: nouvelle liste avec les valeurs vides supprimées de la liste
        """
        
        #print("[Vector/scrub_data_content_list] data_list == "+str(data_list))
        
        scrubbed_data_content_list = []

        for data_content in data_list:
            if isinstance(data_content, dict):
                data_content = Vector.scrub_data_content_dict(data_content)
            scrubbed_data_content_list.append(data_content)
        
        #print("[Vector/scrub_data_content_list] scrubbed_data_content_list == "+str(scrubbed_data_content_list))
        
        return scrubbed_data_content_list

    @staticmethod
    def scrub_data_content_dict(data_dict: dict[str,str]) -> dict[str,str]:
        """remplacer les éléments vides dans l'ancien dictionnaire par un nouveau dictionnaire sans élément vide

        Args:
            data_dict (dict[str,str]): dictionnaire à remplacer les éléments vides dans l'ancien

        Returns:
            dict[str,str]: nouveau dictionnaire avec les valeurs vides supprimées du dictionnaire
        """
        
        #print("[Vector/scrub_data_content_dict] input data_dict == "+str(data_dict))
        
        data_without_empty_elements = {}

        for key_data, data_content in data_dict.items():
            if isinstance(data_content, dict):
                data_content = Vector.scrub_data_content_dict(data_content)
            if isinstance(data_content, list):
                data_content = Vector.scrub_data_content_list(data_content)
            if not data_content in (u'', None, {}, []):
                data_without_empty_elements[key_data] = data_content

        data_dict.clear()
        data_dict.update(data_without_empty_elements)

        #print("[Vector/scrub_data_content_dict] ouput data_dict == "+str(data_dict))
        
        return data_dict

    @staticmethod
    def get_type_vector_data(path: str) -> str:
        """Obtenir le type du fichier vecteur ou objet vecteur

        Args:
            path (str): chemin du fichier vecteur ou objet vecteur

        Returns:
            str: type du fichier vecteur ou objet vecteur
        """
        
        if path.endswith(".geojson"):
            return "geojson"
        elif path.endswith(".gpkg"):
            return "gpkg"
        elif path.endswith(".shp"):
            return "shapefile"
        elif path.startswith("s3://"):
            return "s3_object"
        else:
            return "unknown"
        
    @classmethod
    def read_vector_data_content(cls, path: str) -> str:
        """lire le contenu des données vecteur à partir du chemin du fichier/objet vecteur

        Args:
            path (str): chemin du fichier/objet vecteur

        Raises:
            RuntimeError: commande avec le retour d'erreur
            RuntimeError: commande avec le retour d'erreur

        Returns:
            str: contenu des données vecteur
        """
        
        self = cls()

        if path.endswith(".geojson") or path.endswith(".gpkg") or path.endswith(".shp"):
            try:
                self._vector_data_content = subprocess.check_output(
                    'ogrinfo -json ' + path, shell=True, stderr=subprocess.STDOUT
                )
            except subprocess.CalledProcessError as error:
                raise RuntimeError(
                    f"command '{error.cmd}' return with error (code {error.returncode}): {error.output}"
                )
        elif path.startswith("s3://"):
            try:
                self._object_s3_data_content = json.loads(get_data_str(path))
            except Exception as e:
                raise RuntimeError(f"Failed to read S3 object: {e}")
        else:
            pass

        return self

    @classmethod
    def add_instance_table_to_list_tables(cls, path: str) -> list[dict[str,"Table"]]:
        """Ajouter une instance de Table à la liste des tables du vecteur.

        Args:
            path (str): Chemin du fichier vecteur ou objet vecteur.

        Raises:
            Exception: Si le fichier vecteur ou objet vecteur n'existe pas.

        Returns:
            list[dict[str,"Table"]]: liste des tables du vecteur associant le nom de la table aux instances de Table.
        """

        vector = cls()

        # on vérifie si le chemin du fichier vecteur ou objet vecteur est valide
        if not Path(path).exists():
            raise Exception(f"le chemin du fichier vecteur ou objet vecteur est invalide {path}.")
        # on vérifie si le fichier vecteur ou objet vecteur existe
        data_source = ogr.Open(path, update=0)
        if not data_source:
            raise Exception(f"le fichier vecteur ou objet vecteur n'existe pas {path}.")
        for i in range(data_source.GetLayerCount()):
            # on parcourt les couches de la source de données
            layer = data_source.GetLayerByIndex(i)
            name = layer.GetName()
            srs = layer.GetSpatialRef().ExportToWkt() if layer.GetSpatialRef() else None
            count = layer.GetFeatureCount()
            extent = layer.GetExtent()  # (minX, maxX, minY, maxY)
            bbox = (extent[0], extent[2], extent[1], extent[3])  # (minX, minY, maxX, maxY)
            attributes = {}
            layer_defn = layer.GetLayerDefn()
            for j in range(layer_defn.GetFieldCount()):
                field_defn = layer_defn.GetFieldDefn(j)
                attributes[field_defn.GetName()] = field_defn.GetFieldTypeName(field_defn.GetType())
            geometry_columns = [layer_defn.GetGeomFieldDefn(0).GetName()] if layer_defn.GetGeomFieldCount() > 0 else []

            # on créé l'instance Table
            table_instance = Table(
                name=name,
                srs=srs,
                count=count,
                bbox=bbox,
                attributes=attributes,
                geometry_columns=geometry_columns
            )
            # on ajoute l'instance Table à la liste des tables
            vector.__tables.append([{name : table_instance}])

        return vector.__tables

    @classmethod
    def from_file(cls, path: str) -> "Vector":
        """Créer une instance de Vector à partir d'un fichier ou objet vecteur.

        Args:
            path (str): Chemin du fichier vecteur ou objet vecteur.

        Raises:
            Exception: Si le fichier vecteur ou objet vecteur n'existe pas.
            Exception: Si le fichier vecteur ou objet vecteur n'est pas lisible.
            Exception: Si le fichier vecteur ou objet vecteur n'est pas un fichier.
            Exception: Si le fichier vecteur ou objet vecteur n'est pas un fichier valide.
            MissingAttributeError: Si un attribut requis est manquant dans le vecteur de données.
            MissingAttributeError: Si un attribut requis est manquant dans le vecteur de données.
            MissingAttributeError: Si un attribut requis est manquant dans le vecteur de données.
            MissingAttributeError: Si un attribut requis est manquant dans le vecteur de données.

        Returns:
            Vector: Instance du vecteur à partir du fichier.
        """

        # Création d'une nouvelle instance de Vector pour représenter le fichier/objet vecteur
        self = cls()

        # récupération de chacun des chemins des fichiers vecteurs à partir de la "filelist.txt"
        self.__path_vector_file = path

        # on récupère le type du fichier vecteur ou objet vecteur
        self.type_vector = Vector.get_type_vector_data(self.__path_vector_file)
        print(f"[Vector/from_file] le type de données vecteur est : {self.type_vector}")
        
        # on vérifie le type de données vecteur
        if Vector.get_type_vector_data(self.__path_vector_file) == "shapefile" or Vector.get_type_vector_data(self.__path_vector_file) == "gpkg" or Vector.get_type_vector_data(self.__path_vector_file) == "geojson":
            print("[Vector/from_file] c'est un fichier vecteur")
        
        elif Vector.get_type_vector_data(get_osgeo_path(self.__path_vector_file)) == "s3_object":
            print("[Vector/from_file] c'est un objet S3")
        
        else:
            print("[Vector/from_file] c'est un fichier inconnu : ce n'est ni un fichier vecteur ni un objet vecteur !")

        # on vérifie si le chemin de l'objet vecteur est un objet S3
        if self.__path_vector_file.startswith("s3://"):
            self.__is_s3 = True
        else:
            self.__is_s3 = False
            self.__path_local_file = self.__path_vector_file

        # on vérifie si le chemin du fichier vecteur ou objet vecteur est valide
        if not Path(path).exists():
            raise Exception(f"le chemin du fichier vecteur ou objet vecteur n'est pas valide {path}.")

        # on vérifie si le chemin du fichier vecteur ou objet vecteur est un fichier
        if not Path(path).is_file():
            raise Exception(f"le chemin du fichier vecteur ou objet vecteur n'est pas un fichier {path}.")
        
        # on vérifie si le fichier vecteur ou objet vecteur est lisible
        if not os.access(path, os.R_OK):
            raise Exception(f"le fichier vecteur ou objet vecteur n'est pas lisible {path}.")
        
        print(f"[Vector/from_file] le fichier vecteur ou objet vecteur, {path}, est lisible")
       
        # on ajoute une instance de Table à la liste des tables du vecteur pour chaque fichier/objet vecteur.
        # si on charge un fichier vecteur de type geojson => fichier d'extension *.geojson (ex : states.geojson)
        if self.__path_vector_file.endswith(".geojson"):

            try:
                self.vector_geojson = {
                    "path": self.__path_vector_file,
                    "tables": self.add_instance_table_to_list_tables(path=self.__path_vector_file),
                    "data" : Vector.read_vector_data_content(self.__path_vector_file).__dict__,
                }
                # remplacer les éléments vides dans l'ancienne liste par une nouvelle liste sans élément vide
                Vector.scrub_data_content_list(self.vector_geojson["tables"])
                # remplacer les éléments vides dans l'ancien dictionnaire par un nouveau dictionnaire sans élément vide
                Vector.scrub_data_content_dict(self.vector_geojson["data"])
                print("[Vector/from_file] self.vector_geojson == " + str(self.vector_geojson))
                print("\n")

            except KeyError as error_key:
                raise MissingAttributeError(
                    f"l'attribut {error_key.args} est manquant dans le vecteur de données."
                )

        # si on charge un fichier vecteur de type geopackage => fichier d'extension *.gpkg (ex : martinique.gpkg)
        elif self.__path_vector_file.endswith(".gpkg"):

            try:
                self.vector_gpkg = {
                    "path": self.__path_vector_file,
                    "tables": self.add_instance_table_to_list_tables(path=self.__path_vector_file),
                    "data": Vector.read_vector_data_content(self.__path_vector_file).__dict__, 
                }
                # remplacer les éléments vides dans l'ancienne liste par une nouvelle liste sans élément vide
                Vector.scrub_data_content_list(self.vector_gpkg["tables"])
                # remplacer les éléments vides dans l'ancien dictionnaire par un nouveau dictionnaire sans élément vide
                Vector.scrub_data_content_dict(self.vector_gpkg["data"])
                print("[Vector/from_file] self.vector_gpkg == " + str(self.vector_gpkg))
                print("\n")

            except KeyError as error_key:
                raise MissingAttributeError(
                    f"l'attribut {error_key.args} est manquant dans le vecteur de données."
                )

        # si on charge un fichier vecteur de type shapefile => fichier d'extension *.shp (ex : TM_WORLD_BORDERS-0.3.shp)
        elif self.__path_vector_file.endswith(".shp"):

            try:
                self.vector_shp = {
                    "path": self.__path_vector_file,
                    "tables": self.add_instance_table_to_list_tables(path=self.__path_vector_file),
                    "data" : Vector.read_vector_data_content(self.__path_vector_file).__dict__,
                }
                # remplacer les éléments vides dans l'ancienne liste par une nouvelle liste sans élément vide
                Vector.scrub_data_content_list(self.vector_shp["tables"])
                # remplacer les éléments vides dans l'ancien dictionnaire par un nouveau dictionnaire sans élément vide
                Vector.scrub_data_content_dict(self.vector_shp["data"])
                print("[Vector/from_file] self.vector_shp == " + str(self.vector_shp))
                print("\n")

            except KeyError as error_key:
                raise MissingAttributeError(
                    f"l'attribut {error_key.args} est manquant dans le vecteur de données."
                )

        # si on charge un objet vecteur de type objet S3
        elif self.__path_vector_file.startswith("s3://"):
                
            try:
                self.vector_object = {
                    "path": self.path_to_object_file,
                    "tables": self.add_instance_table_to_list_tables(path=self.path_to_object_file),
                    "data" : Vector.read_vector_data_content(self.__path_vector_file).__dict__,
                }
                # remplacer les éléments vides dans l'ancienne liste par une nouvelle liste sans élément vide
                Vector.scrub_data_content_list(self.vector_object["tables"])
                # remplacer les éléments vides dans l'ancien dictionnaire par un nouveau dictionnaire sans élément vide
                Vector.scrub_data_content_dict(self.vector_object["data"])
                print("[Vector/from_file] self.vector_object == " + str(self.vector_object))
                print("\n")

            except KeyError as error_key:
                raise MissingAttributeError(
                    f"l'attribut {error_key.args} est manquant dans le vecteur de données."
                )
        else:
            pass

        return self

    @classmethod
    def from_parameters(cls, path: str, table: dict[str, "Table"]) -> "Vector":
        """créer une instance de Vector à partir des paramètres fournis.

        Args:
            path (str): chemin au fichier ou objet vecteur
            table (dict[str, "Table"]): un dictionnaire de tables associé au vecteur.

        Raises:
            MissingAttributeError: un attribut requis est manquant dans le vecteur de données.
            MissingAttributeError: un attribut requis est manquant dans le vecteur de données.
            MissingAttributeError: un attribut requis est manquant dans le vecteur de données.
            MissingAttributeError: un attribut requis est manquant dans le vecteur de données.
            MissingAttributeError: un attribut requis est manquant dans le vecteur de données.
            MissingAttributeError: un attribut requis est manquant dans le vecteur de données.

        Returns:
            Vector: une instance de Vector est créée à partir des paramètres fournis.
        """

        # Création d'une nouvelle instance de Vector pour représenter le fichier/objet vecteur
        self = cls()

        # remplissage de la liste des tables du vecteur : self.__tables
        for index_table in range(len(table)):
            if path.endswith(".gpkg"):
                try:
                    self.__tables.append(
                        [
                            {
                                table[index_table]["name"]: Table(
                                    table[index_table]["name"],
                                    table[index_table]["srs"],
                                    table[index_table]["count"],
                                    table[index_table]["bbox"],
                                    table[index_table]["attributes"],
                                    table[index_table]["geometry_columns"],
                                ).__dict__
                            }
                        ]
                    )
                except KeyError as error_key:
                    raise MissingAttributeError(
                        f"l'attribut {error_key.args} est manquant dans le vecteur de données."
                    )
            else:
                try:
                    self.__tables.append(
                        [
                            {
                                table[index_table - 1]["name"]: Table(
                                    table[index_table - 1]["name"],
                                    table[index_table - 1]["srs"],
                                    table[index_table - 1]["count"],
                                    table[index_table - 1]["bbox"],
                                    table[index_table - 1]["attributes"],
                                    table[index_table - 1]["geometry_columns"],
                                ).__dict__
                            }
                        ]
                    ),
                except KeyError as error_key:
                    raise MissingAttributeError(
                        f"l'attribut {error_key} est manquant dans le vecteur de données."
                    )

        # récupérer les informations directement fournies dans les tables de données vecteurs
        if path.endswith(".geojson"):
            try:
                self.vector_geojson = {
                    "path": path,
                    "tables": self.__tables,
                    "data": Vector.read_vector_data_content(path).__dict__
                }
                # remplacer les éléments vides dans l'ancienne liste par une nouvelle liste sans élément vide
                Vector.scrub_data_content_list(self.vector_geojson["tables"])
                # remplacer les éléments vides dans l'ancien dictionnaire par un nouveau dictionnaire sans élément vide
                Vector.scrub_data_content_dict(self.vector_geojson["data"])
                print(
                    "[Vector/from_parameters] self.vector_geojson == "
                    + str(self.vector_geojson)
                )
                print("\n")
            except KeyError as error_key:
                raise MissingAttributeError(
                    f"l'attribut {error_key.args} est manquant dans le vecteur de données."
                )

        elif path.endswith(".gpkg"):
            try:
                self.vector_gpkg = {
                    "path": path,
                    "tables": self.__tables,
                    "data": Vector.read_vector_data_content(path).__dict__
                }
                # remplacer les éléments vides dans l'ancienne liste par une nouvelle liste sans élément vide
                Vector.scrub_data_content_list(self.vector_gpkg["tables"])
                # remplacer les éléments vides dans l'ancien dictionnaire par un nouveau dictionnaire sans élément vide
                Vector.scrub_data_content_dict(self.vector_gpkg["data"])
                print(
                    "[Vector/from_parameters] self.vector_gpkg == " + str(self.vector_gpkg)
                )
                print("\n")
            except KeyError as error_key:
                raise MissingAttributeError(
                    f"l'attribut {error_key.args} est manquant dans le vecteur de données."
                )

        elif path.endswith(".shp"):
            try:
                self.vector_shp = {
                    "path": path,
                    "tables": self.__tables,
                    "data": Vector.read_vector_data_content(path).__dict__
                }
                # remplacer les éléments vides dans l'ancienne liste par une nouvelle liste sans élément vide
                Vector.scrub_data_content_list(self.vector_shp["tables"])
                # remplacer les éléments vides dans l'ancien dictionnaire par un nouveau dictionnaire sans élément vide
                Vector.scrub_data_content_dict(self.vector_shp["data"])
                print("[Vector/from_parameters] self.vector_shp == " + str(self.vector_shp))
                print("\n")
            except KeyError as error_key:
                raise MissingAttributeError(
                    f"l'attribut {error_key.args} est manquant dans le vecteur de données."
                )

        elif path.startswith("s3://"):
            try:
                self.vector_object = {
                    "path": path,
                    "tables": self.__tables,
                    "data": Vector.read_vector_data_content(path).__dict__
                }
                # remplacer les éléments vides dans l'ancienne liste par une nouvelle liste sans élément vide
                Vector.scrub_data_content_list(self.vector_object["tables"])
                # remplacer les éléments vides dans l'ancien dictionnaire par un nouveau dictionnaire sans élément vide
                Vector.scrub_data_content_dict(self.vector_object["data"])
                print(
                    "[Vector/from_parameters] self.vector_object == "
                    + str(self.vector_object)
                )
                print("\n")
            except KeyError as error_key:
                raise MissingAttributeError(
                    f"l'attribut {error_key.args} est manquant dans le vecteur de données."
                )
        else:
            pass

        return self

    
    @property
    def get_uniq_srs_tables_list(self) -> list[str]:
        """Obtenir la liste des SRS uniques des tables du vecteur.  

        Returns:
            list[str]: la liste des SRS uniques des tables du vecteur.
        """

        # on initialise le set de srs des tables du vecteur
        uniq_srs_set_all_tables_of_one_vector = set()
        
        for table_list in self.__tables:
            for table_dict in table_list:
                for table in table_dict.values():
                    # Si table est une instance de Table, alors on ajoute table['_Table__attributes'] au set de srs
                    if isinstance(table, Table):
                        uniq_srs_set_all_tables_of_one_vector.add(table['_Table__attributes'])
                    # Si table est un dictionnaire (comme dans from_parameters()), 
                    # alors on ajoute l'élément "_Table__attributes" du dictionnaire de table dans le set de srs
                    elif isinstance(table, dict) and "_Table__attributes" in table:
                        uniq_srs_set_all_tables_of_one_vector.add(table["_Table__attributes"])

        print("[Vector/get_uniq_srs_tables_list] list(uniq_srs_set_all_tables_of_one_vector) == "+str(list(uniq_srs_set_all_tables_of_one_vector)))
        print("\n")

        return list(uniq_srs_set_all_tables_of_one_vector)


class Table:
    """Une table vecteur"""

    def __init__(
        self,
        name: str,
        attributes: dict[str, str],
        count: int,
        srs: str,
        bbox: tuple[float, float, float, float],
        geometry_columns: list[str],
    ) -> "Table":
        """constructeur de Table contenant les informations directement fournies

        Args:
            name (str): nom de la table
            attributes (dict[str,str]): {nom des colonnes : types des colonnes}
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


    def __repr__(self) -> str:
        """représentation de la classe Table

        Returns:
            str: représentation de la classe Table
        """
        return f"Table(name={self.__name}, srs={self.__srs}, count={self.__count}, bbox={self.__bbox}, geometry_columns={self.__geometry_columns}, attributes={self.__attributes})"

    @property
    def name(self) -> str:
        """nom de la table"""
        return self.__name

    @property
    def attributes(self) -> dict[str, str]:
        """attributs de la table"""
        return self.__attributes

    @property
    def count(self) -> int:
        """nombre d'objets dans la table"""
        return self.__count

    @property
    def srs(self) -> str:
        """système de référence spatiale des coordonnées"""
        return self.__srs

    @property
    def bbox(self) -> tuple[float, float, float, float]:
        """rectangle englobant"""
        return self.__bbox

    @property
    def geometry_columns(self) -> list[str]:
        """noms des colonnes géométriques"""
        return self.__geometry_columns
"""   

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
    vectorset.from_list(pathtofilelisttxt)
    Vector.from_file(pathtogeojsonfilename)
    
    # On veut récupérer les informations à partir d'un fichier geojson : Vector.from_file(pathtogeojsonfilename) -> Table
    # VectorSet.from_descriptor (lecture de toutes les informations dans le descripteur) -> Vector.from_parameters -> Table
    # On veut récupérer les informations à partir d'un descripteur : VectorSet.from_descriptor (lecture de toutes les informations dans le descripteur) -> Vector.from_parameters -> Table
    vectorset.from_descriptor(pathtodescriptor)
    Vector.from_parameters(pathtogeojsonfilename, table_geojson)

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
    vectorset.from_list(pathtofilelisttxt)
    Vector.from_file(pathtogpkgfilename)

    # VectorSet.from_descriptor (lecture de toutes les informations dans le descripteur) -> Vector.from_parameters -> Table
    # On veut récupérer les informations à partir d'un descripteur : VectorSet.from_descriptor (lecture de toutes les informations dans le descripteur) -> Vector.from_parameters -> Table
    vectorset.from_descriptor(pathtodescriptor)
    Vector.from_parameters(pathtogpkgfilename, table_gpkg)

    print("\n")

    # Ci-dessous deux usages pour le chargement de données vecteur
    ###########################################################################################################
    # EXEMPLE 3 : FICHIER D'ENTREE => FICHIER SHAPEFILE DE DONNEES VECTEUR : 'TM_WORLD_BORDERS-0.3.shp'       #
    ###########################################################################################################
    # entrées
    pathtoshpfilename = os.path.join(pathtoparentdir, "tests/fixtures/TM_WORLD_BORDERS-0.3.shp")
    vectorset = VectorSet()

    # VectorSet.from_list -> Vector.from_file (usage de ogr pour récupérer les informations nécessaires) -> Table
    # On veut récupérer les informations à partir d'une liste : VectorSet.from_list -> Vector.from_file (usage de ogr pour récupérer les informations nécessaires) -> Table
    vectorset.from_list(pathtofilelisttxt)
    Vector.from_file(pathtoshpfilename)

    # VectorSet.from_descriptor (lecture de toutes les informations dans le descripteur) -> Vector.from_parameters -> Table
    # On veut récupérer les informations à partir d'un descripteur : VectorSet.from_descriptor (lecture de toutes les informations dans le descripteur) -> Vector.from_parameters -> Table
    vectorset.from_descriptor(pathtodescriptor)
    Vector.from_parameters(pathtoshpfilename, table_shp)

    ######################################################################
    # EXEMPLE 4 : OBTENIR DES SRS UNIQUES DES TABLES DES DONNEES VECTEUR #
    ######################################################################

    vectorset = VectorSet.from_descriptor(pathtodescriptor)
    srs_uniques = vectorset.get_uniq_srs_tables_list
    print("\n")
    print("srs uniques de vectorset.get_uniq_srs_tables_list == "+str(srs_uniques))
    print("\n")

    vector_geojson = Vector.from_parameters(pathtogeojsonfilename, table_geojson)
    srs_uniques = vector_geojson.get_uniq_srs_tables_list
    print("srs uniques de vector_geojson.get_uniq_srs_tables_list == "+str(srs_uniques))
    print("\n")
    
    vector_gpkg = Vector.from_parameters(pathtogpkgfilename, table_gpkg)
    srs_uniques = vector_gpkg.get_uniq_srs_tables_list
    print("srs uniques de vector_gpkg.get_uniq_srs_tables_list == "+str(srs_uniques))
    print("\n")

    vector_shp = Vector.from_parameters(pathtoshpfilename, table_shp)
    srs_uniques = vector_shp.get_uniq_srs_tables_list
    print("srs uniques de vector_shp.get_uniq_srs_tables_list == "+str(srs_uniques))
    print("\n") """
