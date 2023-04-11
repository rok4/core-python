## Summary

Lecture facilitée de la liste d'une pyramide.
Modification de la gestion des vecteurs

## Changelog

### [Added]

* Pyramid
    * Fonctions de gestion de la liste : chargement et lecture (via un generator)
    * Taille du header d'une dalle stockée dans la variable `ROK4_IMAGE_HEADER_SIZE`
    * La proriété `tile_extension` : retourne l'extension d'une tuile de la pyramide en fonction du format
    * Des exemples d'utilisation des fonctions principales

### [Changed]

* Vector
    * Utilisation de kwargs pour les paramètres du csv
    * Gestion des CSV par OGR
    * Passage par get_osgeo_path pour la lecture virtuelle
    * 2 constructeurs pour les vecteurs : from_file et from_parameters

### [Fixed]

* Storage
    * Lecture de la taille d'un objet S3 : pas besoin d'enlever des quotes dans le header `Content-Length`
<!--
### [Added]

### [Changed]

### [Deprecated]

### [Removed]

### [Fixed]

### [Security]
-->
