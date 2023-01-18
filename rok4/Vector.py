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
        layers (List[Tuple[str, int, List[Tuple[str, str]]]]) : Vector layers
    """
    
    def __init__(self, path: str) -> None :
        """Constructor method

        Args:
            path: path to the file/object

        """
        
        self.path = path
        
        path_split = path.split("/")
        
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
        
        multipolygon = ogr.Geometry(ogr.wkbGeometryCollection)
        layer = dataSource.GetLayer()
        for feature in layer :
            geom = feature.GetGeometryRef()
            multipolygon.AddGeometry(geom)
        
        self.bbox = multipolygon.GetEnvelope()
        
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
            layers += [(name, count, attributes)]
        self.layers = layers