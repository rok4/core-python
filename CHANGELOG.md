## Summary

Fonction de lecture d'une tuile vecteur décodée.

## Changelog

### [Added]

* Pyramid
    * Décodage d'une tuile vecteur avec `get_tile_data_vector` (le pendant vecteur de `get_tile_data_raster`) : le résultat est un "dictionnaire GeoJSON", et les coordonnées sont en relatif à la tuile (souvent entre 0 et 4096)
* Utils
    * Ajout d'un cache pour la création de spatial reference (via la fonction `srs_to_spatialreference`)

### [Changed]

* Storage
    * La lecture d'un fichier ou objet qui n'existe pas émet toujours une exception `FileNotFoundError`
* Pyramid
    * Si la tuile que l'on veut lire est dans une dalle qui n'existe pas, on retourne `None`

<!--
### [Added]

### [Changed]

### [Deprecated]

### [Removed]

### [Fixed]

### [Security]
-->
