## Summary

Lecture facilitée de la liste d'une pyramide. Lecture d'informations sur une donnée raster unique depuis un fichier ou une liste de paramètres.

## Changelog

### [Added]

* Raster
    * Chargement des informations sur un fichier raster (chemin du fichier, chemin du fichier de masque si applicable, nombre de canaux, boundingbox de l'emprise géographique)
        * depuis le fichier raster
        * depuis une liste de paramètres provenant d'une utilisation précédente
    * Tests unitaires
    * Documentation interne des fonctions et classes

* Pyramid
    * Fonctions de gestion de la liste : chargement et lecture (via un generator)
    * Taille du header d'une dalle stockée dans la variable `ROK4_IMAGE_HEADER_SIZE`
    * La proriété `tile_extension` : retourne l'extension d'une tuile de la pyramide en fonction du format
    * Des exemples d'utilisation des fonctions principales

### [Changed]

* README.md
    * Modification du bloc code de compilation pour utiliser explicitement python3, et installer certaines dépendances.
* Utils
    * Fonction de calcul de la boundix box d'une donnée
    * Fonction de détermination du format de variable des couleurs dans une donéne raster


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
