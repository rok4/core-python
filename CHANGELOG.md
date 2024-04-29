## 2.1.5

### [Changed]

* Pyramid : la fonction de chargement de la liste en mémoire retourne le nombre de dalle

## 2.1.4

### [Fixed]

* Storage : la réponse à un HEAD (test existence en S3) donne un code 404 et non NoSuchKey (confusion avec la lecture d'objet)
* RasterSet: le chargement d'un raster set à partir d'un fichier ou d'un descripteur utilise la librairie Storage et non la librairie GDAL

## 2.1.3

### [Fixed]

* Storage : dans le cas d'une lecture ou d'un test existence sur un objet S3 absent, le code dans la réponse n'est pas 404 mais NoSuchKey

## 2.1.0

### [Added]

* Pyramid
    * Ajout de fonctions pour récupérer la tile_limits et le nombre de canaux de cette pyramide
    * Ajout de fonctions pour ajouter ou supprimer des niveaux dans une pyramide
* TileMatrixSet
    * Ajout de fonctions pour récupérer la hauteur et la largeur de tuiles d'un TileMatrixSet

### [Changed]

* Pyramid
    * Ajout d'un paramètre optionnel "mask" pour le constructeur from other afin de pouvoir conserver ou non les masques de la pyramide servant de base à la nouvellle
* Gestion des documentations des différentes versions avec l'outil [mike](https://github.com/jimporter/mike)

## 2.0.1

### [Added]

* `storage` : le cache de lecture est configurable en taille (avec ROK4_READING_LRU_CACHE_SIZE) et en temps de rétention (avec ROK4_READING_LRU_CACHE_TTL)

### [Security]

* Montée de version de pillow (faille de sécurité liée à libwebp)

## 2.0.0

### [Fixed]

* Pyramid
    * quand on lit une tuile dans une pyramide PNG 1 canal, on retourne bien aussi un numpy.array à 3 dimensions (la dernière dimension sera bien un array à un élément)

### [Changed]

* Storage
    * Le client S3 garde ouverte des connexions
    * La fonction get_data_binary a un système de cache de type LRU, avec un temps de validité de 5 minutes

## 1.7.1

### [Added]

* Raster
    * Classe RasterSet, réprésentant une collection d'objets de la classe Raster, avec des informations supplémentaires
    * Méthodes d'import et export des informations extraites par une instance RasterSet, au travers d'un descripteur (fichier ou objet json, voire sortie standard)
    * Documentation interne
    * Tests unitaires pour la classe RasterSet
    * Classe Raster : constructeur à partir des paramètres

* Pyramid
    * Fonction de calcul de la taille d'une pyramide
    * Générateur de lecture de la liste du contenu

* Storage
    * Fonction de calcul de la taille des fichiers d'un chemin selon le stockage
    * Ajout de la copie de HTTP vers FILE/S3/CEPH
    * Ajout de la fonction de lecture d'un fichier HTTP, de l'existence d'un fichier HTTP et du calcul de taille d'un fichier HTTP

### [Changed]

* Raster
    * Homogénéisation du code
    * Mise en conformité PEP-8
* test_Raster
    * Homogénéisation du code
    * Mise en conformité PEP-8
* Utils
    * Mise en conformité PEP-8 des fonctions `compute_bbox` et `compute_format`


### [Fixed]

* Utils
    * Correction d'un nom de variable dans la fonction `compute_format`, qui écrasait une fonction du noyau python.



## 1.6.0

Lecture par système de fichier virtuel avec GDAL

### [Added]

* Storage
    * Fonction `get_osgeo_path` permettant de configurer le bon sytème de fichier virtuel en fonction du chemin fourni, et retourne celui à utiliser dans le Open de gdal ou ogr

### [Changed]

* Storage
    * la récupération d'un client S3 (`__get_s3_client`) permet de récupérer le client, l'hôte, les clés d'accès et secrète, ainsi que le nom du bucket sans l'éventuel hôte du cluster

### [Fixed]

* Storage
    * Lecture binaire S3 : mauvaise configuration du nom du bucket et de l'objet et mauvaise lecture partielle

### [Removed]

* Exceptions
    * `NotImplementedError` est une exceptions native


## 1.5.0

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


## 1.4.4

Ajout de fonctionnalités de lecture de donnée d'une pyramide et suivi des recommandations PyPA pour la gestion du projet.

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


## 1.3.0

Ajout de la librairie de lecture de données vecteur, de tests unitaires et ajout de fonctionnalité pour le stockage. Amélioration de la gestion du projet et de l'intégration continue.

### [Added]

* Librairie de lecture de données vecteur :
  * Chargement de données vecteur pour des fichiers shapefile, Geopackage, CSV et GeoJSON
  * Ecriture des tests unitaires
* Librairie Pyramid : complétion des tests unitaires
* Librairie Storage : prise en charge de la copie CEPH -> S3
* Gestion du projet (compilations, dépendances...) via poetry
* Injection de la version dans le fichier `pyproject.toml` et `__init__.py` (définition de la variable `__version__`)
* Évolution de la CI github
    * Vérification des installations et tests unitaires sous ubuntu 20.04 python 3.8 et ubuntu 22.04 python 3.10
    * Publication de l'artefact avec les résultats des tests unitaires
    * Nettoyage de la release en cas d'erreur
    * Compilation de la documentation et publication sur la branche gh-pages


## 1.2.0

Ajout des librairies pour l'utilitaire make-layer.py

### [Added]

* Librairie Storage : complétion des tests unitaires

* Librairie Pyramid :
  * Ajout de getter sur les niveaux du haut et du bas

* Ajout de la librairie de gestion d'une couche Layer :
  * Chargement d'une couche depuis des paramètres
  * Chargement d'une couche depuis un descripteur
  * Écriture du descripteur au format attendu par le serveur
  * Écriture des tests unitaires

* Ajout d'une librairie d'utilitaires Utils
  * Conversion d'un SRS en objet OSR SpatialReference
  * Conversion d'une bbox en objet OGR Geometry
  * Reprojection d'une bbox avec densification des côtés et reprojection partielle
  * Écriture des tests unitaires

* Configuration de l'outil coverage pour voir la couverture des tests unitaires


## 1.1.0

Prise en charge de plusieurs clusters S3 de stockage.

### [Added]

* Librairie d'abstraction du stockage :
  * Prise en charge de plusieurs clusters S3. Les variables d'environnement pour le stockage S3 précisent plusieurs valeurs séparées par des virgules, et les noms des buckets peuvent être suffixés par "@{S3 cluster host}". Par défaut, le premier cluster défini est utilisé. L'hôte du cluster n'est jamais écrit dans le descripteur de pyramide ou le fichier liste (puisque stockés sur le cluster, on sait sur lequel sont les objets). Les objets symboliques ne le précisent pas non plus et ne peuvent être qu'au sein d'un cluster S3


## 1.0.0

Initialisation des librairies Python utilisées par les outils python à venir du dépôt [pytools](https://github.com/rok4/pytools).

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
