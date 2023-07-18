"""Provide class to read informations on vector data from file path or object path

The module contains the following class :

    - 'Vector' - Data Vector

"""

import os
import tempfile

from osgeo import ogr

from rok4.Exceptions import *
from rok4.Storage import copy, get_osgeo_path

# Enable GDAL/OGR exceptions
ogr.UseExceptions()


class Vector:
    """A data vector

    Attributes:
        path (str): path to the file/object
        bbox (Tuple[float, float, float, float]): bounding rectange in the data projection
        layers (List[Tuple[str, int, List[Tuple[str, str]]]]) : Vector layers with their name, their number of objects and their attributes
    """

    @classmethod
    def from_file(cls, path: str, **kwargs) -> "Vector":
        """Constructor method of a Vector from a file (Shapefile, Geopackage, CSV and GeoJSON)

        Args:
            path (str): path to the file/object
            **csv (Dict[str : str]) : dictionnary of CSV parameters :
                -srs (str) ("EPSG:2154" if not provided) : spatial reference system of the geometry
                -column_x (str) ("x" if not provided) : field of the x coordinate
                -column_y (str) ("y" if not provided) : field of the y coordinate
                -column_wkt (str) (None if not provided) : field of the WKT of the geometry if WKT use to define coordinate

        Examples:

            from rok4.Vector import Vector

            try:
                vector = Vector.from_file("file://tests/fixtures/ARRONDISSEMENT.shp")
                vector_csv1 = Vector.from_file("file://tests/fixtures/vector.csv" , csv={"delimiter":";", "column_x":"x", "column_y":"y"})
                vector_csv2 = Vector.from_file("file://tests/fixtures/vector2.csv" , csv={"delimiter":";", "column_wkt":"WKT"})

            except Exception as e:
                print(f"Vector creation raises an exception: {exc}")

        Raises:
            MissingEnvironmentError: Missing object storage informations
            StorageError: Storage read issue
            Exception: Wrong column
            Exception: Wrong data in column
            Exception: Wrong format of file
            Exception: Wrong data in the file

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
                        if column_wkt == None:
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
                if geom != None:
                    multipolygon.AddGeometry(geom)
            layers += [(name, count, attributes)]

        self.layers = layers
        self.bbox = multipolygon.GetEnvelope()

        return self

    @classmethod
    def from_parameters(cls, path: str, bbox: tuple, layers: list) -> "Vector":
        """Constructor method of a Vector from a parameters

        Args:
            path (str): path to the file/object
            bbox (Tuple[float, float, float, float]): bounding rectange in the data projection
            layers (List[Tuple[str, int, List[Tuple[str, str]]]]) : Vector layers with their name, their number of objects and their attributes

        Examples:

            try :
                vector = Vector.from_parameters("file://tests/fixtures/ARRONDISSEMENT.shp", (1,2,3,4), [('ARRONDISSEMENT', 14, [('ID', 'String'), ('NOM', 'String'), ('INSEE_ARR', 'String'), ('INSEE_DEP', 'String'), ('INSEE_REG', 'String'), ('ID_AUT_ADM', 'String'), ('DATE_CREAT', 'String'), ('DATE_MAJ', 'String'), ('DATE_APP', 'Date'), ('DATE_CONF', 'Date')])])

            except Exception as e:
                print(f"Vector creation raises an exception: {exc}")

        """

        self = cls()

        self.path = path
        self.bbox = bbox
        self.layers = layers

        return self
