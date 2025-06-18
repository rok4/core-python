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
from typing import Tuple

# package
from rok4.storage import copy, get_osgeo_path, get_data_str

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
        self = cls()

        self.path = path

        path_split = path.split("/")


        if path_split[0] == "ceph:" or path.endswith(".csv"):
            if path.endswith(".shp"):
                with tempfile.TemporaryDirectory() as tmp:
                    tmp_path = tmp + "/" + path_split[-1][:-4]

                    copy(path, "file://" + tmp_path + ".shp")
                    copy(path[:-4] + ".shx", "file://" + tmp_path + ".shx")
                    copy(path[:-4] + ".cpg", "file://" + tmp_path + ".cpg")
                    copy(path[:-4] + ".dbf", "file://" + tmp_path + ".dbf")
                    copy(path[:-4] + ".prj", "file://" + tmp_path + ".prj")

                    dataSource = ogr.Open(tmp_path + ".shp", 0)

            elif path.endswith(".gpkg"):
                with tempfile.TemporaryDirectory() as tmp:
                    tmp_path = tmp + "/" + path_split[-1][:-5]

                    copy(path, "file://" + tmp_path + ".gpkg")

                    dataSource = ogr.Open(tmp_path + ".gpkg", 0)

            elif path.endswith(".geojson"):
                with tempfile.TemporaryDirectory() as tmp:
                    tmp_path = tmp + "/" + path_split[-1][:-8]

                    copy(path, "file://" + tmp_path + ".geojson")

                    dataSource = ogr.Open(tmp_path + ".geojson", 0)
                    gdal_ogr_compliant_path = get_osgeo_path(path)
                    load_full_data_into_string=get_data_str(gdal_ogr_compliant_path)

            elif path.endswith(".csv"):
                # Récupération des informations optionnelles
                if "csv" in kwargs:
                    csv = kwargs["csv"]
                else:
                    csv = {}

                if "srs" in csv and csv["srs"] is not None:
                    srs = csv["srs"]
                else:
                    srs = "EPSG:2154"

                if "column_x" in csv and csv["column_x"] is not None:
                    column_x = csv["column_x"]
                else:
                    column_x = "x"

                if "column_y" in csv and csv["column_y"] is not None:
                    column_y = csv["column_y"]
                else:
                    column_y = "y"

                if "column_wkt" in csv:
                    column_wkt = csv["column_wkt"]
                else:
                    column_wkt = None

                with tempfile.TemporaryDirectory() as tmp:
                    tmp_path = tmp + "/" + path_split[-1][:-4]
                    name_fich = path_split[-1][:-4]

                    copy(path, "file://" + tmp_path + ".csv")

                    with tempfile.NamedTemporaryFile(
                        mode="w", suffix=".vrt", dir=tmp, delete=False
                    ) as tmp2:
                        vrt_file = "<OGRVRTDataSource>\n"
                        vrt_file += '<OGRVRTLayer name="' + name_fich + '">\n'
                        vrt_file += "<SrcDataSource>" + tmp_path + ".csv</SrcDataSource>\n"
                        vrt_file += "<SrcLayer>" + name_fich + "</SrcLayer>\n"
                        vrt_file += "<LayerSRS>" + srs + "</LayerSRS>\n"
                        if column_wkt is None:
                            vrt_file += (
                                '<GeometryField encoding="PointFromColumns" x="'
                                + column_x
                                + '" y="'
                                + column_y
                                + '"/>\n'
                            )
                        else:
                            vrt_file += (
                                '<GeometryField encoding="WKT" field="' + column_wkt + '"/>\n'
                            )
                        vrt_file += "</OGRVRTLayer>\n"
                        vrt_file += "</OGRVRTDataSource>"
                        tmp2.write(vrt_file)
                    dataSourceVRT = ogr.Open(tmp2.name, 0)
                    os.remove(tmp2.name)
                    dataSource = ogr.GetDriverByName("ESRI Shapefile").CopyDataSource(
                        dataSourceVRT, tmp_path + "shp"
                    )

            else:
                raise Exception("This format of file cannot be loaded")

        else:
            dataSource = ogr.Open(get_osgeo_path(path), 0)

        multipolygon = ogr.Geometry(ogr.wkbGeometryCollection)
        try:
            layer = dataSource.GetLayer()
        except AttributeError:
            raise Exception(f"The content of {self.path} cannot be read")

        layers = []
        for i in range(dataSource.GetLayerCount()):
            layer = dataSource.GetLayer(i)
            name = layer.GetName()
            count = layer.GetFeatureCount()
            layerDefinition = layer.GetLayerDefn()
            attributes = []
            for j in range(layerDefinition.GetFieldCount()):
                fieldName = layerDefinition.GetFieldDefn(j).GetName()
                fieldTypeCode = layerDefinition.GetFieldDefn(j).GetType()
                fieldType = layerDefinition.GetFieldDefn(j).GetFieldTypeName(fieldTypeCode)
                attributes += [(fieldName, fieldType)]
            for feature in layer:
                geom = feature.GetGeometryRef()
                if geom is not None:
                    multipolygon.AddGeometry(geom)
            layers += [(name, count, attributes)]

        self.layers = layers
        self.bbox = multipolygon.GetEnvelope()

        return self

    
    @classmethod
    def from_descriptor(cls, path: str) -> "VectorSet":
        """Constructor method of a VectorSet from the descriptor
           un fichier ou un objet contient toutes les informations sur les fichiers vecteur ou objets vecteur

        Args:
            path (str): chemin du fichier vecteur ou objet vecteur

        Returns:
            VectorSet: jeu de fichiers/objets vecteur
        """
        self = cls()

        self.path = path

        return self

    @property
    def get_unique_srs_tables_list(srs: str)-> list[str]:
        """obtenir la liste des srs uniques des tables
        Args :
            srs (str) : système de référence spatiale des coordonnées
        Returns:
            list(str): liste des srs uniques des tables
        """
        return ["2154", "4326", "3857", "4210"," 4258"]

class Vector():
    """un fichier/un objet vecteur
    """
    # attributs de classe
    # chemin du fichier objet/vecteur
    _path: str = ""
    # la clé est le nom de la table et la valeur de l'instance de Table
    _tables: dict[str, list[str]]  = {}

    @classmethod
    def from_file(cls, path: str) -> "Vector":
        """Constructor method of a Vector from file

        Args:
            path (str): chemin du fichier/objet vecteur

        Returns:
            Vector: fichier/objet S3 vecteur à partir du fichier
        """
        self = cls()

        self.path = path

        path_split = path.split("/")

        if path_split[0] == "ceph:" or path.endswith(".csv"):
            if path.endswith(".shp"):
                with tempfile.TemporaryDirectory() as tmp:
                    tmp_path = tmp + "/" + path_split[-1][:-4]

                    copy(path, "file://" + tmp_path + ".shp")
                    copy(path[:-4] + ".shx", "file://" + tmp_path + ".shx")
                    copy(path[:-4] + ".cpg", "file://" + tmp_path + ".cpg")
                    copy(path[:-4] + ".dbf", "file://" + tmp_path + ".dbf")
                    copy(path[:-4] + ".prj", "file://" + tmp_path + ".prj")

                    dataSource = ogr.Open(tmp_path + ".shp", 0)

            elif path.endswith(".gpkg"):
                with tempfile.TemporaryDirectory() as tmp:
                    tmp_path = tmp + "/" + path_split[-1][:-5]

                    copy(path, "file://" + tmp_path + ".gpkg")

                    dataSource = ogr.Open(tmp_path + ".gpkg", 0)

            elif path.endswith(".geojson"):
                with tempfile.TemporaryDirectory() as tmp:
                    tmp_path = tmp + "/" + path_split[-1][:-8]

                    copy(path, "file://" + tmp_path + ".geojson")

                    dataSource = ogr.Open(tmp_path + ".geojson", 0)

            elif path.endswith(".csv"):
                # Récupération des informations optionnelles
                if "csv" in kwargs:
                    csv = kwargs["csv"]
                else:
                    csv = {}

                if "srs" in csv and csv["srs"] is not None:
                    srs = csv["srs"]
                else:
                    srs = "EPSG:2154"

                if "column_x" in csv and csv["column_x"] is not None:
                    column_x = csv["column_x"]
                else:
                    column_x = "x"

                if "column_y" in csv and csv["column_y"] is not None:
                    column_y = csv["column_y"]
                else:
                    column_y = "y"

                if "column_wkt" in csv:
                    column_wkt = csv["column_wkt"]
                else:
                    column_wkt = None

                with tempfile.TemporaryDirectory() as tmp:
                    tmp_path = tmp + "/" + path_split[-1][:-4]
                    name_fich = path_split[-1][:-4]

                    copy(path, "file://" + tmp_path + ".csv")

                    with tempfile.NamedTemporaryFile(
                        mode="w", suffix=".vrt", dir=tmp, delete=False
                    ) as tmp2:
                        vrt_file = "<OGRVRTDataSource>\n"
                        vrt_file += '<OGRVRTLayer name="' + name_fich + '">\n'
                        vrt_file += "<SrcDataSource>" + tmp_path + ".csv</SrcDataSource>\n"
                        vrt_file += "<SrcLayer>" + name_fich + "</SrcLayer>\n"
                        vrt_file += "<LayerSRS>" + srs + "</LayerSRS>\n"
                        if column_wkt is None:
                            vrt_file += (
                                '<GeometryField encoding="PointFromColumns" x="'
                                + column_x
                                + '" y="'
                                + column_y
                                + '"/>\n'
                            )
                        else:
                            vrt_file += (
                                '<GeometryField encoding="WKT" field="' + column_wkt + '"/>\n'
                            )
                        vrt_file += "</OGRVRTLayer>\n"
                        vrt_file += "</OGRVRTDataSource>"
                        tmp2.write(vrt_file)
                    dataSourceVRT = ogr.Open(tmp2.name, 0)
                    os.remove(tmp2.name)
                    dataSource = ogr.GetDriverByName("ESRI Shapefile").CopyDataSource(
                        dataSourceVRT, tmp_path + "shp"
                    )

            else:
                raise Exception("This format of file cannot be loaded")

        else:
            dataSource = ogr.Open(get_osgeo_path(path), 0)

        multipolygon = ogr.Geometry(ogr.wkbGeometryCollection)
        try:
            layer = dataSource.GetLayer()
        except AttributeError:
            raise Exception(f"The content of {self.path} cannot be read")

        layers = []
        for i in range(dataSource.GetLayerCount()):
            layer = dataSource.GetLayer(i)
            name = layer.GetName()
            count = layer.GetFeatureCount()
            layerDefinition = layer.GetLayerDefn()
            attributes = []
            for j in range(layerDefinition.GetFieldCount()):
                fieldName = layerDefinition.GetFieldDefn(j).GetName()
                fieldTypeCode = layerDefinition.GetFieldDefn(j).GetType()
                fieldType = layerDefinition.GetFieldDefn(j).GetFieldTypeName(fieldTypeCode)
                attributes += [(fieldName, fieldType)]
            for feature in layer:
                geom = feature.GetGeometryRef()
                if geom is not None:
                    multipolygon.AddGeometry(geom)
            layers += [(name, count, attributes)]

        self.layers = layers
        self.bbox = multipolygon.GetEnvelope()

        return self


    @classmethod
    def from_parameters(cls, path: str, tables: list[str]) -> "Vector":
        """Constructor method of a Vector from the descriptor

        Args:
            path (str): chemin du fichier objet/vecteur
            tables (list[str]): le nom de la table et la valeur de l'instance de Table

        Returns:
            Vector: fichier/objet s3 Vecteur à partir du descripteur
        """
        self = cls()

        self.path = path
        self.tables = tables

        return self

    @property
    def get_unique_srs_tables_list(srs: str)-> list[str]:
        """obtenir la liste des srs uniques des tables
        Args :
            srs (str) : système de référence spatiale des coordonnées
        Returns:
            list[str]: la liste des srs uniques des tables
        """
        return ["2154", "3857", "4210"," 4258", "4326"]

class Table:
    """Une table vecteur
    """

    def __init__(self, name: str, attributes:dict, count:int, srs:str, bbox:Tuple[float, float, float, float]) -> "Table":
        """constructeur de Table contenant les informations directement fournies

        Args:
            name (str): nom des objets
            attributes (dict): nom des attributs (colonnes + types des colonnes)
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
    VectorSet.from_list(path)
    Vector.from_file(shp_info)
    name = my_object1
    attributes = {"colonne1": str}
    count = 100
    srs = "2154"
    bbox = (100.0, 23.6, -6.93, 3.369)
    table1 = Table(name, attributes, count, srs, bbox)  

    # On veut récupérer les informations à partir d'un descripteur : VectorSet.from_descriptor (lecture de toutes les informations dans le descripteur) -> Vector.from_parameters -> Table
    VectorSet.from_descriptor(path)
    Vector.from_parameters(path, tables)
    name = my_object2
    attributes = {"colonne1": str}
    count = 3000
    srs = "2154"
    bbox = (100.0, 23.6, -6.93, 3.369)
    table2 = Table(name, attributes, count, srs, bbox)