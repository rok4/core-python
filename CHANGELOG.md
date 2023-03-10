## Summary

Ajout de fonctionnalités de lecture de donnée d'une pyramide et suivi des recommandations PyPA pour la gestion du projet.

## Changelog

### [Added]

* TileMatrix :
    * Fonction de calcul des indices de tuile et de pixel dans la tuile à partir d'un point dans le système de coordonnées du TMS
* Pyramid :
    * Fonction de calcul des indices de tuile et de pixel dans la tuile à partir d'un point dans le système de coordonnées du TMS et éventuellement un niveau
    * Fonctions de lecture d'une tuile : au format binaire source ou au format tableau à 3 dimensions pour les tuiles raster
* Storage :
    * Fonction de lecture binaire, complète ou partielle, d'un fichier ou objet S3 ou CEPH
* Exceptions : NotImplementedError permet de préciser qu'une fonctionnalité n'a pas été implémentée pour tous les cas. Ici, on ne gère pas la décompression des données raster pour les compressions packbit et LZW
* Ajout de la publication PyPI dans la CI GitHub 

### [Changed]

* Storage :
    * La lecture sous forme de chaîne s'appuie sur la lecture complète binaire. Aucun changement à l'usage.

* TileMatrixSet : quelque soit le système de coordonnées, on ne gère que un ordre des axes X,Y ou Lon,Lat. Cependant, les fonctions de calcul de ou à partir de bbox respectent l'ordre du système dans ces dernières.

* Passage de la configuration du projet dans le fichier `pyproject.toml`

<!--
### [Added]

### [Changed]

### [Deprecated]

### [Removed]

### [Fixed]

### [Security]
-->
