# Librairies ROK4 core Python

## Summary

Prise en charge de plusieurs clusters S3 de stockage.
Lecture de données vecteur

## Changelog

### [Added]

* Librairie d'abstraction du stockage :
  * Prise en charge de plusieurs clusters S3. Les variables d'environnement pour le stockage S3 précisent plusieurs valeurs séparées par des virgules, et les noms des buckets peuvent être suffixés par "@{S3 cluster host}". Par défaut, le premier cluster défini est utilisé. L'hôte du cluster n'est jamais écrit dans le descripteur de pyramide ou le fichier liste (puisque stockés sur le cluster, on sait sur lequel sont les objets). Les objets symboliques ne le précisent pas non plus et ne peuvent être qu'au sein d'un cluster S3
* Librairie de lecture de données vecteur :
  * Récupération de données vecteur pour des fichiers shapefile, Geopackage, CSV et GeoJSON

<!--
### [Added]

### [Changed]

### [Deprecated]

### [Removed]

### [Fixed]

### [Security]
-->
