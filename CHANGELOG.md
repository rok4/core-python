## Summary

Ajout du type de stockage HTTP.
Lecture par système de fichier virtuel avec GDAL

## Changelog

### [Added]

* Storage
    * Fonction `get_osgeo_path` permettant de configurer le bon sytème de fichier virtuel en fonction du chemin fourni, et retourne celui à utiliser dans le Open de gdal ou ogr

### [Changed]

* Storage
    * la récupération d'un client S3 (`__get_s3_client`) permet de récupérer le client, l'hôte, les clés d'accès et secrète, ainsi que le nom du bucket sans l'éventuel hôte du cluster
    * Ajout de la copie de HTTP vers FILE/S3/CEPH
    * Ajout de la fonction de lecture d'un fichier HTTP, de l'existence d'un fichier HTTP et du calcul de taille d'un fichier HTTP

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
