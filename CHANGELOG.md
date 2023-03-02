# Librairies ROK4 core Python

## Summary

Ajout des librairies de lecture respectives de données vecteur et de données raster, de tests unitaires et ajout de fonctionnalité pour le stockage. Amélioration de la gestion du projet et de l'intégration continue.

## Changelog

### [Added]

* Librairie de lecture de données vecteur :
  * Chargement de données vecteur pour des fichiers shapefile, Geopackage, CSV et GeoJSON
  * Ecriture des tests unitaires
* Librairie Pyramid : complétion des tests unitaires
* Librairie Storage : prise en charge de la copie CEPH -> S3
* Gestion du projet (compilations, dépendances...) via poetry
* Injection de la version dans le fichier `pyproject.toml` et `__init__.py` (définition de la variable `__version__`)
* Évolution de la CI github
    * Vérification des installations et tests unitaires sous python 3.8, 3.9 et 3.10, sous ubuntu 20.04 et ubuntu 22.04
    * Publication de l'artefact avec les résultats des tests unitaires
    * Nettoyage de la release en cas d'erreur
    * Compilation de la documentation et publication sur la branche gh-pages
* Librairie "Raster" de lecture de données raster :
  * Chargement des informations sur un fichier raster (chemin du fichier, chemin du fichier de masque si applicable, nombre de canaux, boundingbox de l'emprise géographique)
  * Tests unitaires

<!--
### [Added]

### [Changed]

### [Deprecated]

### [Removed]

### [Fixed]

### [Security]
-->
