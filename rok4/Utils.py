"""Provide functions to manipulate OGR / OSR entities
"""

import os

from typing import Dict, List, Tuple, Union
from osgeo import ogr, osr
ogr.UseExceptions()
osr.UseExceptions()

def srs_to_spatialreference(srs: str) -> 'osgeo.osr.SpatialReference':
    """Convert coordinates system as string to OSR spatial reference

    Args:
        srs (str): coordinates system PROJ4 compliant, with authority and code, like EPSG:3857 or IGNF:LAMB93

    Raises:
        RuntimeError: Provided SRS is invalid for OSR

    Returns:
        osgeo.osr.SpatialReference: Corresponding OSR spatial reference
    """

    authority, code = srs.split(':', 1)

    sr = osr.SpatialReference()
    if authority.upper() == "EPSG":
        sr.ImportFromEPSG(int(code))
    else:
        sr.ImportFromProj4(f"+init={srs.upper()} +wktext")

    return sr

def bbox_to_geometry(bbox: Tuple[float, float, float, float], srs: str = None, densification: int = 0) -> 'osgeo.ogr.Geometry':  
    """Convert bbox coordinates to OGR geometry

    Args:
        bbox (Tuple[float, float, float, float]): bounding box (xmin, ymin, xmax, ymax)
        srs (str, optional): coordinates system. Defaults to None.
        densification (int, optional): Number of point to add for each side of bounding box. Defaults to 0.

    Raises:
        RuntimeError: Provided SRS is invalid for OSR
        
    Returns:
        osgeo.ogr.Geometry: Corresponding OGR geometry, with spatial reference if provided
    """    

    ring = ogr.Geometry(ogr.wkbLinearRing)

    if densification > 0:
        step_x = (bbox[2] - bbox[0]) / (densification + 1)
        step_y = (bbox[3] - bbox[1]) / (densification + 1)

        for i in range(densification + 1):
            ring.AddPoint(bbox[0] + step_x * i, bbox[1])
        for i in range(densification + 1):
            ring.AddPoint(bbox[2], bbox[1] + step_y * i)
        for i in range(densification + 1):
            ring.AddPoint(bbox[2] - step_x * i, bbox[3])
        for i in range(densification + 1):
            ring.AddPoint(bbox[0], bbox[3] - step_y * i)
        ring.AddPoint(bbox[0], bbox[1])

    else:
        ring.AddPoint(bbox[0], bbox[1])
        ring.AddPoint(bbox[2], bbox[1])
        ring.AddPoint(bbox[2], bbox[3])
        ring.AddPoint(bbox[0], bbox[3])
        ring.AddPoint(bbox[0], bbox[1])
    

    geom = ogr.Geometry(ogr.wkbPolygon)
    geom.AddGeometry(ring)
    geom.SetCoordinateDimension(2)

    if srs is not None:
        geom.AssignSpatialReference(srs_to_spatialreference(srs))
    
    return geom



def reproject_bbox(bbox: Tuple[float, float, float, float], srs_src: str, srs_dst: str, densification: int = 5) -> Tuple[float, float, float, float]:
    """Return bounding box in other coordinates system 

    Points are added to be sure output bounding box contains input bounding box

    Args:
        bbox (Tuple[float, float, float, float]): bounding box (xmin, ymin, xmax, ymax) with source coordinates system
        srs_src (str): source coordinates system
        srs_dst (str): destination coordinates system
        densification (int, optional): Number of point to add for each side of bounding box. Defaults to 5.

    Returns:
        Tuple[float, float, float, float]: bounding box (xmin, ymin, xmax, ymax) with destination coordinates system
    """

    bbox_src = bbox_to_geometry(bbox, srs_src, densification)
    sr_geo = srs_to_spatialreference(srs_dst)

    bbox_dst = bbox_src.Clone()
    os.environ["OGR_ENABLE_PARTIAL_REPROJECTION"] = "YES"
    bbox_dst.TransformTo(sr_geo)

    env = bbox_dst.GetEnvelope()
    return (env[0], env[2], env[1], env[3])
