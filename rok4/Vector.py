"""Provide class to read informations on vector data from file path or object path

The module contains the following class :
    
    - 'Vector' - Data Vector

"""

from osgeo import ogr
from rok4.Storage import get_data_str, copy
from rok4.Exceptions import *
import os

# Enable GDAL/OGR exceptions
ogr.UseExceptions()

class Vector :
    """A data vector
    
    Attributes:
        path (str): path to the file/object
        bbox (Tuple[float, float, float, float]): bounding rectange in the data projection
        layers (List[Tuple[str, int, List[Tuple[str, str]]]]) : Vector layers with their name, their number of objects and their attributes
    """
    
    def __init__(self, path: str, delimiter: str = ";", column_x : str = "x" , column_y : str = "y", column_WKT : str = None) -> None :
        """Constructor method for Shapefile, Geopackage, CSV and GeoJSON

        Args:
            path: path to the file/object
            delimiter (only for CSV) : delimiter between fields
            column_x (only for CSV) : field of the x coordinate
            column_y (only for CSV) : field of the y coordinate
            column_WKT (only for CSV if geometry in WKT) : field of the WKT of the geometry

        """
        
        self.path = path
        
        path_split = path.split("/")
        
        if path.endswith(".csv") :
            
            data = get_data_str(path)
            data = data.split("\n")
            for i in range (len(data)) :
                data[i] = data[i].split(delimiter)
                
            attributes = []
            for i in range (len(data[0])) :
                attributes += [(data[0][i] , "String")]
            layers = [(path_split[-1][:-4], len(data)-1, attributes)]
            self.layers = layers
            
            geomcol = ogr.Geometry(ogr.wkbGeometryCollection)
            if column_WKT == None :
                data_x = data[0].index(column_x)
                data_y = data[0].index(column_y)
                for i in range (1, len(data) - 1) :
                    point = ogr.Geometry(ogr.wkbPoint)
                    point.AddPoint(float(data[i][data_x]), float(data[i][data_y]))
                    geomcol.AddGeometry(point)
            
            else :
                data_WKT = data[0].index(column_WKT)
                for i in range (1, len(data) - 1) :
                    geom = ogr.CreateGeometryFromWKT(data[i][data_WKT])
                    geomcol.AddGeometry(geom)
                    
            self.bbox = geomcol.GetEnvelope()
            
        else :
        
            if path.endswith(".shp") :
                
                tmp_path = "/tmp/" + path_split[-1][:-4]
                
                copy(path, "file://" + tmp_path + ".shp")
                copy(path[:-4] + ".shx", "file://" + tmp_path + ".shx")
                copy(path[:-4] + ".cpg", "file://" + tmp_path + ".cpg")
                copy(path[:-4] + ".dbf", "file://" + tmp_path + ".dbf")
                copy(path[:-4] + ".prj", "file://" + tmp_path + ".prj")
                
                dataSource = ogr.Open(tmp_path + ".shp", 0)
                
                os.remove(tmp_path + ".shp")
                os.remove(tmp_path + ".shx")
                os.remove(tmp_path + ".cpg")
                os.remove(tmp_path + ".dbf")
                os.remove(tmp_path + ".prj")
                
            elif path.endswith(".gpkg") :
                tmp_path = "/tmp/" + path_split[-1][:-5]
                
                copy(path, "file://" + tmp_path + ".gpkg")
                
                dataSource = ogr.Open(tmp_path + ".gpkg", 0)
                
                os.remove(tmp_path + ".gpkg")
                
            elif path.endswith(".geojson") :
                tmp_path = "/tmp/" + path_split[-1][:-8]
                
                copy(path, "file://" + tmp_path + ".geojson")
                
                dataSource = ogr.Open(tmp_path + ".geojson", 0)
                
                os.remove(tmp_path + ".geojson")
        
            multipolygon = ogr.Geometry(ogr.wkbGeometryCollection)
            layer = dataSource.GetLayer()
            
            layers = []
            for i in range (dataSource.GetLayerCount()) :
                layer = dataSource.GetLayer(i)
                name = layer.GetName()
                count = layer.GetFeatureCount()
                layerDefinition = layer.GetLayerDefn()
                attributes = []
                for i in range(layerDefinition.GetFieldCount()):
                    fieldName =  layerDefinition.GetFieldDefn(i).GetName()
                    fieldTypeCode = layerDefinition.GetFieldDefn(i).GetType()
                    fieldType = layerDefinition.GetFieldDefn(i).GetFieldTypeName(fieldTypeCode)
                    attributes += [(fieldName, fieldType)]
                for feature in layer :
                    geom = feature.GetGeometryRef()
                    if geom != None :
                        multipolygon.AddGeometry(geom)
                layers += [(name, count, attributes)]
                
            self.layers = layers
            self.bbox = multipolygon.GetEnvelope()
            
        print(self.bbox)
        print(self.layers)