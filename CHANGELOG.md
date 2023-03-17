## Summary



## Changelog

### [Added]

* Level
    * Fonction de test d'une tuile `is_in_limits` : ses indices sont ils dans les limites du niveau ?
* Pyramid
    * La lecture d'une tuile vérifie avant que les indices sont bien dans les limites du niveau
    * Les exceptions levées lors du décodage de la tuile raster emettent une exception `FormatError`
    * `get_tile_indices` accepte en entrée un système de coordonnées : c'est celui des coordonnées fournies et permet de faire une reprojection si celui ci n'est pas le même que celui des données dans la pyramide
* Utils
    * Meilleure gestion de reprojection par `reproject_bbox` : on détecte des systèmes identiques en entrée ou quand seul l'ordre des axes changent, pour éviter le calcul
    * Ajout de la fonction de reprojection d'un point `reproject_point` : on détecte des systèmes identiques en entrée ou quand seul l'ordre des axes changent, pour éviter le calcul
  
### [Changed]

* Utils :
    * `bbox_to_geometry` : on ne fournit plus de système de coordonnées, la fonction se content de créer la géométrie OGR à partir de la bbox, avec éventuellement une densification en points des bords
* Pyramid :
    * Renommage de fonction : `update_limits` -> `set_limits_from_bbox`. Le but est d'être plus explicite sur le fonctionnement de la fonction (on écrase les limites, on ne les met pas juste à jour par union avec la bbox fournie)
<!--
### [Added]

### [Changed]

### [Deprecated]

### [Removed]

### [Fixed]

### [Security]
-->
