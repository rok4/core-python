# Librairies ROK4 core Python

## Summary

Complétion des librairies Python utilisées par les outils python à venir du dépôt [pytools](https://github.com/rok4/pytools).

## Changelog

### [Added]

* Librairie d'abstraction du stockage (S3, CEPH ou FILE)
  * fonction de test de l'existence du fichier / objet

### [Changed]

* Librairie d'abstraction du stockage (S3, CEPH ou FILE)
  * la suppression d'un fichier ou objet n'existant pas ne lève pas d'erreur

### [Fixed]

* Sortie en erreur si le nom d'une pyramide FICHIER contient un slash
* Les indices d'une dalle calculés à partir de son chemin sont bien typés en entiers

<!-- 
### [Added]

### [Changed]

### [Deprecated]

### [Removed]

### [Fixed]

### [Security] 
-->