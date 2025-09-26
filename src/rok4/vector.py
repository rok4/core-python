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
from rok4.exceptions import FormatError, StorageError
from rok4.storage import copy, get_data_str, get_osgeo_path, put_data_str

# -- GLOBALS --

# Enable GDAL/OGR exceptions
ogr.UseExceptions()


class VectorSet:
    """
    correspond to a set of vector files/objects
     : List of vector data
     
    """
    __vectors: List["Vector"] = []  # type: ignore # instances of Vector class

    def __init__(self)-> None:
        """
        A file or an object containg all the informations to access the vector data (files/objects)
        """

        self.vectors: List["Vector"] = VectorSet.__vectors  # instances of Vector class

    @classmethod
    def from_list(cls, path:str)-> "VectorSet":
        """
        A file or an object containg a list of path to vector data (files/objects)

        :param path: List of path to vector data
        """

        self  = cls()
        # Récupération du chemin vers le fichier ou l'objet
        working_path = get_osgeo_path(path)

        # Création du fichier temporaire
        tmp_list_obj = tempfile.NamedTemporaryFile(mode="r", delete=False)

        # Récupération du chemin vers le fichier temporaire
        tmp_list_file = tmp_list_obj.name

        # Copie depuis l'emplacement source de la liste vers le fichier temporaire
        try:
            copy(working_path, tmp_list_file)
        except Exception as error_copy:
            raise StorageError(
                "FILE",
                f"Cannot copy file {working_path} to {tmp_list_file} : {error_copy}",
            )
        print(f"Temporary file created : {tmp_list_file}")
        print(f"[VectorSet/from_list] Temporary file used : {tmp_list_file}")
        print(f"[VectorSet/from_list] List file used : {working_path}")
        # lecture du fichier temporaire
        try:
            with open(tmp_list_file, "r") as file:
                for line in file:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        vector = Vector.from_file(line)
                        self.vectors.append(vector)
        except Exception as e:
            raise StorageError("FILE", f"Cannot read file {tmp_list_file} : {e}")
        print(f"[VectorSet/from_list] Number of vector data in the set : {len(self.vectors)}")
        print(f"[VectorSet/from_list] List of vector data in the set : {self.vectors}")
        print("\n")

        # une fois les informations récupérées
        # on peut fermer le fichier temporaire
        tmp_list_obj.close()

        # on supprime le fichier temporaire
        os.remove(tmp_list_file)
        return self

    @classmethod
    def from_descriptor(cls, path:str)-> "VectorSet":
        """
        A file or an object containg all the informations to access the vector data (files/objects)

        :param path: Path to descriptor file
        """
     
        vectorset  = cls()
        descriptor_file = path
        # Récupération du chemin vers le fichier ou l'objet
        working_path = get_osgeo_path(descriptor_file)
        descriptor_file = working_path
        # lecture du descripteur
        try:
            vectorset.descriptor_object = json.loads(get_data_str(descriptor_file))
        except json.JSONDecodeError as e:
            raise FormatError("JSON", vectorset.descriptor_object, e)
        print(f"[VectorSet/from_descriptor] Descriptor object : {vectorset.descriptor_object}")
        # on obtient l'ensemble des jeux de données de fichier/objet vecteur à partir du fichier descriptor
        for index_descriptor_object in range(len(vectorset.descriptor_object)):
            print(f"[VectorSet/from_descriptor] Descriptor object {index_descriptor_object} : {vectorset.descriptor_object[index_descriptor_object]}")
            # Pour chaque dictionnaire dans la liste, on fait appel au constructeur `Vector.from_parameters` avec ce dictionnaire
            # 1°) récupération de tous les attributs de Vector dans le dictionnaire en entrée (`path`)
            # 2°) puis, pour chaque table dans le champ `tables`, faire appel au constructeur de Table avec tous les éléments suivants:
            vector = Vector.from_parameters(
                vectorset.descriptor_object[index_descriptor_object]["path"],
                vectorset.descriptor_object[index_descriptor_object]["tables"],
            )
            # On ajoute l'objet vector créé dans l'attribut `__vectors` du VectorSet
            vectorset.__vectors.append(vector)

        print("[VectorSet/from_descriptor] vectorset.__vectors == " + str(vectorset.__vectors))
        print("\n")
        print(f"[VectorSet/from_descriptor] Number of vector data in the set : {len(vectorset.vectors)}")
        print(f"[VectorSet/from_descriptor] List of vector data in the set : {vectorset.vectors}")
        return vectorset
    

    @property
    def srs(self)-> List[str]:
        """
        Get the list of uniq SRS of the tables in the set

        :return: List of SRS
        :rtype: List[str]
        """
        srs_list = []
        for vector in self.vectors:
            for srs in vector.srs:
                if srs not in srs_list:
                    srs_list.append(srs)
        return srs_list
    
    @property
    def serializable(self)-> Dict[str, Union[str, List[str]]]:
        """Get the serializable version of the vector set

        Returns:
            Dict[str, Union[str, List[str]]]: Get the dictionary version compliant to the descriptor of the vector set
        """
        
        # OLD VERSION WITH RASTER DATA
        # serialization = {"bbox": list(self.bbox), "srs": self.srs, "colors": [], "raster_list": []}
        # for color in self.colors:
        #     color_serial = {"bands": color[0], "format": color[1].name}
        #     serialization["colors"].append(color_serial)
        # for raster in self.raster_list:
        #     raster_dict = {
        #         "path": raster.path,
        #         "dimensions": list(raster.dimensions),
        #         "bbox": list(raster.bbox),
        #         "bands": raster.bands,
        #         "format": raster.format.name,
        #     }
        #     if raster.mask is not None:
        #         raster_dict["mask"] = raster.mask
        #     serialization["raster_list"].append(raster_dict)

        # Get the dict version corresponding to the descriptor of the vector data
        serialization = {"vectors": []}
        for vector in self.vectors:
            serialization["vectors"].append(vector.serializable)

        return serialization

    def write_descriptor(self, path: str = None)-> None:
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
    __path: str = ""  # path of the vector file/object
    __tables: Dict[str, "Table"] = {}  # dictionnary of Table instances, key is the name of the table and the value the instance of Table class

    def __init__(self) -> None:
        """
        to retrieve information directly
        """
        self.path = Vector.__path
        self.tables = Vector.__tables

    @classmethod
    def from_file(cls, path:str)-> "Vector":
        """
        to retrieve information from a vector file or a vector object

        :param path: Path to vector file/object file
        """

        self = cls()
        self.path = path

        working_path = get_osgeo_path(path)
        datasource = ogr.Open(working_path)
        if datasource is None:
            raise StorageError("FILE", f"Cannot open vector file/object {working_path}")
        print(f"[Vector/from_file] Vector file/object used : {working_path}")
        # parcours des couches
        for i in range(datasource.GetLayerCount()):
            layer = datasource.GetLayerByIndex(i)
            name = layer.GetName()
            count = layer.GetFeatureCount()
            srs = layer.GetSpatialRef().GetAttrValue("AUTHORITY", 1)
            extent = layer.GetExtent()
            bbox = (extent[0], extent[2], extent[1], extent[3])  # minX, minY, maxX, maxY
            # parcours des champs
            attributes = {}
            layer_defn = layer.GetLayerDefn()
            for j in range(layer_defn.GetFieldCount()):
                field_defn = layer_defn.GetFieldDefn(j)
                field_name = field_defn.GetName()
                field_type = field_defn.GetTypeName()
                attributes[field_name] = field_type
            # parcours des colonnes de géométrie
            geometry_columns = {}
            geom_field_count = layer_defn.GetGeomFieldCount()
            for k in range(geom_field_count):
                geom_field_defn = layer_defn.GetGeomFieldDefn(k)
                geom_field_name = geom_field_defn.GetName()
                geom_field_type = ogr.GeometryTypeToName(geom_field_defn.GetType())
                geometry_columns[geom_field_name] = geom_field_type
            # création de l'instance de Table
            table_instance = Table(name, count, srs, bbox, attributes, geometry_columns)
            self.tables[name] = table_instance
    
        print(f"[Vector/from_file] Vector data loaded : {self.path} with {len(self.tables)} tables")
        
        # affichage des informations récupérées
        for i in range(datasource.GetLayerCount()):
            layer = datasource.GetLayer(i)
            print(f"Name: {layer.GetName()}")
            # Attention, GetExtent retourne dans l'ordre xmin xmax ymin ymax, et nous on veut les bbox dans l'ordre xmin ymin xmax ymax
            print(f"    Bbox: {layer.GetExtent()[0]},{layer.GetExtent()[2]} {layer.GetExtent()[1]},{layer.GetExtent()[3]}")
            print(f"    Count: {layer.GetFeatureCount()}")
            print(f"    Geometry column: {layer.GetGeometryColumn()}")
            print(f"    SRS: {layer.GetSpatialRef().GetAuthorityName(None)}:{layer.GetSpatialRef().GetAuthorityCode(None)}")

            # Le champ détecté comme FID n'est pas dans les champs récupérés avec GetFieldDefn
            if layer.GetFIDColumn() != "":
                print(f"        \"{layer.GetFIDColumn()}\": \"Integer\"")

        for j in range(layer.GetLayerDefn().GetFieldCount()):
            field = layer.GetLayerDefn().GetFieldDefn(j)
            print(f"        \"{field.GetName()}\": \"{field.GetTypeName()}\"")

        print("\n")

        print(f"[Vector/from_file] List of tables in the vector data : {self.tables}")
        print(f"[Vector/from_file] List of SRS in the vector data : {self.srs}")
        print(f"[Vector/from_file] List of geometries in the vector data : {geometry_columns}")
        print(f"[Vector/from_file] List of attributes in the vector data : {attributes}")
        print(f"[Vector/from_file] List of vector data in the set : {self}")
        # fermeture de la datasource
        datasource = None

        return self

    @classmethod
    def from_parameters(cls, path: str, tables: Dict[str, "Table"]) -> "Vector":
        """
        to retrieve information directly

        :param path: Path to vector file/object
        :param tables: List of table names to consider in the vector data (default: all tables)
        """

        self = cls()
        self.path = path
        self.tables = tables
        print(f"[Vector/from_parameters] Vector data loaded : {self.path} with {len(self.tables)} tables")
        print(f"[Vector/from_parameters] List of tables in the vector data : {self.tables}")
        print(f"[Vector/from_parameters] List of vector data in the set : {self}")

        return self
        
    @property
    def srs(self)-> List[str]:
        """
        Get the list of uniq SRS of the tables in the vector data

        :return: List of SRS
        :rtype: List[str]
        """
        srs_list = []
        for table in self.tables.values():
            if table.srs not in srs_list:
                srs_list.append(table.srs)
        return srs_list
    
    @property
    def serializable(self)-> Dict[str, Union[str, List[str]]]:
        """
        Get the dictiionary version corresponding to the descriptor of the vector data
        """
        serialization = {"path": self.path, "tables": []}
        for table in self.tables.values():
            serialization["tables"].append(table.serializable)
        return serialization

class Table:
    """A table file/Object """

    def __init__(self, name: str, count: int, srs: str, bbox: Tuple[float, float, float, float], attributes: Dict[str, str], geometry_columns: List[str]) -> None:
        """
        to retrieve information directly

        :param name: Name of the table
        :param count: Number of features in the table
        :param srs: SRS of the table
        :param bbox: Bounding box of the table (minX, minY, maxX, maxY)
        :param attributes: Name of the columns and their type (key is the name of the attribute and value is the type of the attribute)
        :param geometry_columns: Name of the geometry columns
        """
        self.name = name
        self.count = count
        self.srs = srs
        self.bbox = bbox
        self.attributes = attributes
        self.geometry_columns = geometry_columns

    @property
    def serializable(self) -> Dict[str, Union[str, int, Tuple[float, float, float, float], List[str]]]:
        """Get the dict version of the table, descriptor compliant
        Returns:
            Dict[str, Union[str, int, Tuple[float, float, float, float], List[str]]]: dictionary corresponding to the descriptor of the table
        """
        serialization = {
            "name": self.name,
            "count": self.count,
            "srs": self.srs,
            "bbox": Tuple(self.bbox),
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
        os.path.join(pathtoparentdir, "data/filelist.txt")
    )
    vectorset = VectorSet()
    # VectorSet.from_list -> Vector.from_file (usage de ogr pour récupérer les informations nécessaires) -> Table
    # On veut récupérer les informations à partir d'une liste : VectorSet.from_list -> Vector.from_file (usage de ogr pour récupérer les informations nécessaires) -> Table
    vectorset.from_list(pathtofilelisttxt)

    ###################################################################################
    # EXEMPLE 2 : FICHIER D'ENTREE => FICHIER DU DESCRIPTEUR : 'vectorset.json'       #
    ###################################################################################
    # entrées
    pathtodescriptor = os.path.join(pathtoparentdir, "data/vectorset.json")
    vectorset = VectorSet()
    # On veut récupérer les informations à partir d'un fichier geojson : Vector.from_file(pathtogeojsonfilename) -> Table
    # VectorSet.from_descriptor (lecture de toutes les informations dans le descripteur) -> Vector.from_parameters -> Table
    # On veut récupérer les informations à partir d'un descripteur : VectorSet.from_descriptor (lecture de toutes les informations dans le descripteur) -> Vector.from_parameters -> Table
    vectorset.from_descriptor(pathtodescriptor)