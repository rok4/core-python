## Summary

Lecture par système de fichier virtuel avec GDAL
Librairie de lecture d'une donnée raster.

## Changelog

### [Added]

* Storage
    * Fonction `get_osgeo_path` permettant de configurer le bon sytème de fichier virtuel en fonction du chemin fourni, et retourne celui à utiliser dans le Open de gdal ou ogr
* Raster :
  * Chargement des informations sur un fichier raster (chemin du fichier, chemin du fichier de masque si applicable, nombre de canaux, boundingbox de l'emprise géographique)
  * Tests unitaires

### [Changed]

* Storage
    * la récupération d'un client S3 (`__get_s3_client`) permet de récupérer le client, l'hôte, les clés d'accès et secrète, ainsi que le nom du bucket sans l'éventuel hôte du cluster
* README.md
    * Modification du bloc code de compilation pour utiliser explicitement python3, et installer certaines dépendances.

### [Fixed]

* Storage
    * Lecture binaire S3 : mauvaise configuration du nom du bucket et de l'objet et mauvaise lecture partielle

### [Removed]

* Exceptions
    * `NotImplementedError` est une exceptions native
<!--
### [Added]

### [Changed]

### [Deprecated]

### [Removed]

### [Fixed]

### [Security]
-->
