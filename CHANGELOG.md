## Summary

Fonction de lecture d'une tuile vecteur décodée.
Librairie de lecture d'une donnée raster.

## Changelog

### [Added]

* Pyramid
    * Décodage d'une tuile vecteur avec `get_tile_data_vector` (le pendant vecteur de `get_tile_data_raster`) : le résultat est un "dictionnaire GeoJSON", et les coordonnées sont en relatif à la tuile (souvent entre 0 et 4096)
* Utils
    * Ajout d'un cache pour la création de spatial reference (via la fonction `srs_to_spatialreference`)
* Raster :
  * Chargement des informations sur un fichier raster (chemin du fichier, chemin du fichier de masque si applicable, nombre de canaux, boundingbox de l'emprise géographique)
  * Tests unitaires

### [Changed]

* Storage
    * La lecture d'un fichier ou objet qui n'existe pas émet toujours une exception `FileNotFoundError`
    * Ajout d'un prototype vide de fonction 'get_osgeo_path', qui a terme, à partir d'un chemin complet vers une image, retournera le chemin système d'un fichier local de travail, créé si besoin.
* Pyramid
    * Si la tuile que l'on veut lire est dans une dalle qui n'existe pas, on retourne `None`
* README.md
    * Modification du bloc code de compilation pour utiliser explicitement python3, et installer certaines dépendances.

<!--
### [Added]

### [Changed]

### [Deprecated]

### [Removed]

### [Fixed]

### [Security]
-->
