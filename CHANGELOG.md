# Librairies ROK4 core Python

## Summary

Initialisation des librairies Python utilisées par les outils python à venir du dépôt [pytools](https://github.com/rok4/pytools).

## Changelog

### [Added]

* Librairie d'abstraction du stockage (S3, CEPH ou FILE)
  * récupération du contenu sous forme de string
  * écriture d'un contenu string
  * création d'un lien symbolique
  * copie fichier/objet <-> fichier/objet
* Librairie de chargement d'un Tile Matrix Set
* Librairie de gestion d'un descripteur de pyramide
  * chargement depuis un descripteur ou par clone (avec changement de stockage)
  * écriture du descripteur
* Tests unitaires couvrant ces librairies

<!-- 
### [Added]

### [Changed]

### [Deprecated]

### [Removed]

### [Fixed]

### [Security] 
-->