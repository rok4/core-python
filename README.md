# Librairies ROK4 Python

![ROK4 Logo](https://rok4.github.io/assets/images/rok4.png)

Ces librairies facilitent la manipulation d'entités du projet ROK4 comme les Tile Matrix Sets, les pyramides ou encore les couches, ainsi que la manipulation des stockages associés.

## Installer la librairie

Installations système requises :

* debian : `apt install python3-rados python3-gdal`

Depuis [PyPI](https://pypi.org/project/rok4/) : `pip install rok4`

Depuis [GitHub](https://github.com/rok4/core-python/releases/) : `pip install https://github.com/rok4/core-python/releases/download/x.y.z/rok4-x.y.z-py3-none-any.whl`

Puis passer en mode superutilisateur pour taper cette ligne de commande et installer l'environnement virtuel de python :
```sh
sudo apt install python3.10-venv
```
puis revenir en mode normal et tapez cette ligne de commande :
```sh
source .venv/bin/activate
```

L'environnement d'exécution doit avoir accès aux librairies système. Dans le cas d'une utilisation au sein d'un environnement python, précisez bien à la création `python3 -m venv --system-site-packages .venv`.

## Utiliser la librairie

Voici un exemple d'arborescence d'organisation des scripts et des fichiers json pour l'exploitation des informations sur les pyramides de tuiles de données raster ou vecteur :
```sh
tree ../../Pyramide/
../../Pyramide/
├── JSON
│   ├── layers
│   │   └── pente.json
│   ├── pyramides
│   │   └── ALTI.json
│   ├── styles
│   │   └── pente.json
│   └── tilematrixsets
│       └── PM.json
├── RASTER
│   ├── ALTI
│   │   ├── DATA_0_0_0
│   │   └── DATA_11_42_58
│   └── BDORTHO
│       ├── DATA_11_42_58
│       └── DATA_14_338_470
├── scripts
│   ├── data_tilesmatrix_launcher.py
│   └── envvar.sh
└── VECTEUR
    └── BDPARCELLAIRE
        ├── DATA_11_21_29
        └── DATA_14_169_235

11 directories, 12 files
```

En dehors du dépôt `core-python`, tapez les ligne de commande suivantes dans un fichier shell `envvar.sh` contenant l'export de toutes les variables d'environnement du projet `ROK4`:
```sh
export ROK4_TMS_DIRECTORY=s3://tilematrixsets
export ROK4_S3_KEY=rok4
export ROK4_S3_SECRETKEY=rok4S3storage
export ROK4_S3_URL=http://localhost:9000
```


Dans un script nommé par exemple `data_tilesmatrix_launcher.py`
Le script `data_tilesmatrix_launcher.py` contient les lignes suivantes :
```python
#!/usr/bin/env python3
# Nom : data_tilesmatrix_launcher.py
# But : récupérer des informations sur les pyramides de tuiles que l'on analyse
# Dossier cible : pyramide tuiles de données raster ALTI et BDORTHO par exemple, et de données vecteur BDPARCELLAIRE

from enum import Enum
import json

# import des packages de rok4
from rok4.enums import PyramidType, SlabType, StorageType, ColorFormat
from rok4.pyramid import Level, Pyramid
from rok4.layer import Layer
from rok4.vector import Vector
from rok4.raster import Raster, RasterSet
from rok4.style import Colour, Palette, Slope, Exposition, Estompage, Legend, Style
from rok4.storage import *
from rok4.utils import *
from rok4.tile_matrix_set import TileMatrix, TileMatrixSet


try :

    tms = TileMatrixSet("PM")
    print(f"le nom du tms est le suivant : {tms.name}")
    print(f"le nom du tms est le suivant : {tms.path}")
    print(f"le code srs associé au système de projection planimétrique est le suivant : {tms.srs}")

    typePyramid = PyramidType("RASTER")
    slabType = SlabType("MASK")
    storageType = StorageType("s3://")

    print (f"type de pyramide : {typePyramid}")
    print (f"type de slab : {slabType}")
    print (f"type de stockage : {storageType}")

    couleur = Colour({
                    "value": 600,
                    "red": 220,
                    "green": 179,
                    "blue": 99,
                    "alpha": 255
                }, "Style")
    print(f"les canaux rouge, vert, bleu et alpha : {couleur.rgba}")
    print(f"les canaux rouge, vert, bleu : {couleur.rgb}")

    # Ouverture d'un fichier JSON d'une couche
    print(f"\nOuverture d'un fichier JSON d'une couche\n")
    with open("~/Documents/Pyramide/JSON/layers/pente.json") as json_file:
        data = json.load(json_file)
        print(f"type de structure de données de data : {type(data)}")
        print(f'mots-clefs : {data["keywords"]}')
        print(f'niveau le plus bas de la pyramide : {data["pyramids"][0]["bottom_level"]}')
        print(f'niveau le plus haut de la pyramide : {data["pyramids"][0]["top_level"]}')
        print(f'le chemin d accès à la pyramide : {data["pyramids"][0]["path"]}')
        print(f'le style choisi : {data["styles"][0]}')
        print(f'code srs de la projection planimétrique : {data["extra_crs"][0]}')

    # Ouverture d'un fichier JSON d'une pyramide
    print ("\nOuverture d'un fichier JSON d'une pyramide\n")
    with open("~/Documents/Pyramide/JSON/pyramides/ALTI.json") as json_file:
        data = json.load(json_file)
        print(f"type de structure de données de data : {type(data)}")
        #print(data)
        print(f'nombre de niveaux de la pyramide : {len(data["levels"])}')
        #print(data["levels"])
        #print(data["levels"]["tile_limits"])
        print(data["levels"][0]["tile_limits"])
        print(f'niveau zéro de stockage de la pyramide : {data["levels"][0]["storage"]}')
        print(f'nom de la tuile de la pyramide : {data["tile_matrix_set"]}')
        #print(f'niveaux de la tuile de la pyramide : {data["levels"]}')
        print(f'niveau zéro de la tuile de la pyramide : {data["levels"][0]}')
        print(f'max de la colonne en limite de tuile niveau zéro de la tuile de la pyramide : {data["levels"][0]["tile_limits"]["max_col"]}')
        print(f'données de stockage du niveau zéro de la tuile de la pyramide : {data["levels"][0]["storage"]}')
        print(f'type de stockage : {data["levels"][0]["storage"]["type"]}')
        print(f'préfixe de l image : {data["levels"][0]["storage"]["image_prefix"]}')
        print(f'nom du bucket de stockage : {data["levels"][0]["storage"]["bucket_name"]}')
        print(f'nombre de tuiles par hauteur : {data["levels"][0]["tiles_per_height"]}')

    # Ouverture d'un fichier JSON d'un style
    print ("\nOuverture d'un fichier JSON d'un style\n")
    with open("~/Documents/Pyramide/JSON/styles/pente.json") as json_file:
        data = json.load(json_file)
        print(f"type de structure de données de data : {type(data)}")
        print(f'le titre : {data["title"]}')
        print(f'pente : {data["keywords"][0]}')
        print(f'ce dont il s"agit : {data["keywords"][1]}')
        print(f'niveau le plus bas : {data["pyramids"][0]["bottom_level"]}')
        print(f'niveau le plus haut : {data["pyramids"][0]["top_level"]}')
        print(f'type de palette : {data["styles"][0]}')
        print(f'code srs associé à la projection planimétrique : {data["extra_crs"][0]}')

    # Ouverture d'un fichier JSON d'un tilematrixset
    print ("\nOuverture d'un fichier JSON d'un tilematrixset\n")
    with open("~/Documents/Pyramide/JSON/tilematrixsets/PM.json") as json_file:
        data = json.load(json_file)
        print(f"type de structure de données de data : {type(data)}")
        print(f'nom de la pyramide : {data["id"]}')
        print(f'code srs projection planimétrique : {data["crs"]}')
        print(f'nombre de tuiles de la pyramide : {len(data["tileMatrices"])}')
        print(f'coordonnées du point origine : {data["tileMatrices"][0]["pointOfOrigin"]}')
        print(f'taille de la cellule : {data["tileMatrices"][0]["cellSize"]}')
        print(f'nombre d"éléments de la matrices de tuiles cad le nombre de tuiles : {len(data["tileMatrices"])}')


    # Exploitation de la classe Vector
    print ("\nExploitation de la classe Vector\n")

    bbox = (10.6, 6.6, 3.3, 3.7)
    layers = [("vector1", 10, [("attribute1", "attribute2")])]
    pathtorasterpyramide = "~/Documents/Pyramide/RASTER/BDORTHO/DATA_14_338_470"
    pathtovecteurrpyramide = "~/Documents/Pyramide/VECTEUR/BDPARCELLAIRE/DATA_14_169_235"

    vector = Vector()
    print(f"le path donnant accès aux données de la pyramide de tuile vecteur est : {vector.from_parameters(pathtovecteurrpyramide, bbox, layers).__dict__['path']}")
    print(f"la boundary box de la pyramide de tuile vecteur est : {vector.from_parameters(pathtovecteurrpyramide, bbox, layers).__dict__['bbox']}")
    print(f"les couches vectorielles avec leur nom, le nombre d'objets et leurs attributs {vector.from_parameters(pathtovecteurrpyramide, bbox, layers).__dict__['layers']}")

except Exception as exc :

    print (exc)
```

Puis exécuter le programme :
```sh
python3 data_tilesmatrix_launcher.py
```
Le résultat donne :
```sh
myusername@pcname:~$ python3 data_tilesmatrix_launcher.py
le nom du tms est le suivant : PM
le nom du tms est le suivant : s3://tilematrixsets/PM.json
le code srs associé au système de projection planimétrique est le suivant : EPSG:3857
type de pyramide : PyramidType.RASTER
type de slab : SlabType.MASK
type de stockage : StorageType.S3
les canaux rouge, vert, bleu et alpha : (220, 179, 99, 255)
les canaux rouge, vert, bleu : (220, 179, 99)

Ouverture d'un fichier JSON d'une couche

type de structure de données de data : <class 'dict'>
mots-clefs : ['Pente', 'Dérivé de la BD Alti']
niveau le plus bas de la pyramide : 13
niveau le plus haut de la pyramide : 0
le chemin d accès à la pyramide : s3://pyramids/PENTE.json
le style choisi : montagne_palette
code srs de la projection planimétrique : EPSG:4559

Ouverture d'un fichier JSON d'une pyramide

type de structure de données de data : <class 'dict'>
nombre de niveaux de la pyramide : 14
{'max_col': 0, 'max_row': 0, 'min_col': 0, 'min_row': 0}
niveau zéro de stockage de la pyramide : {'type': 'S3', 'image_prefix': 'ALTI/DATA_0', 'bucket_name': 'pyramids'}
nom de la tuile de la pyramide : PM
niveau zéro de la tuile de la pyramide : {'tile_limits': {'max_col': 0, 'max_row': 0, 'min_col': 0, 'min_row': 0}, 'storage': {'type': 'S3', 'image_prefix': 'ALTI/DATA_0', 'bucket_name': 'pyramids'}, 'tiles_per_width': 16, 'id': '0', 'tiles_per_height': 16}
max de la colonne en limite de tuile niveau zéro de la tuile de la pyramide : 0
données de stockage du niveau zéro de la tuile de la pyramide : {'type': 'S3', 'image_prefix': 'ALTI/DATA_0', 'bucket_name': 'pyramids'}
type de stockage : S3
préfixe de l image : ALTI/DATA_0
nom du bucket de stockage : pyramids
nombre de tuiles par hauteur : 16

Ouverture d'un fichier JSON d'un style

type de structure de données de data : <class 'dict'>
le titre : Pente
pente : Pente
ce dont il s"agit : Dérivé de la BD Alti
niveau le plus bas : 13
niveau le plus haut : 0
type de palette : montagne_palette
code srs associé à la projection planimétrique : EPSG:4559

Ouverture d'un fichier JSON d'un tilematrixset

type de structure de données de data : <class 'dict'>
nom de la pyramide : PM
code srs projection planimétrique : EPSG:3857
nombre de tuiles de la pyramide : 22
coordonnées du point origine : [-20037508.3427892, 20037508.3427892]
taille de la cellule : 156543.033928041
nombre d"éléments de la matrices de tuiles cad le nombre de tuiles : 22

Exploitation de la classe Vector

le path donnant accès aux données de la pyramide de tuile vecteur est : ~/Documents/Pyramide/VECTEUR/BDPARCELLAIRE/DATA_14_169_235
la boundary box de la pyramide de tuile vecteur est : (10.6, 6.6, 3.3, 3.7)
les couches vectorielles avec leur nom, le nombre d'objets et leurs attributs [('vector1', 10, [('attribute1', 'attribute2')])]
```

Les variables d'environnement suivantes peuvent être nécessaires, par module :

* `storage` : plus de détails dans la documentation technique du module
    * `ROK4_READING_LRU_CACHE_SIZE` : Nombre d'élément dans le cache de lecture (0 pour ne pas avoir de limite)
    * `ROK4_READING_LRU_CACHE_TTL` : Durée de validité d'un élément du cache, en seconde (0 pour ne pas avoir de limite)
    * `ROK4_CEPH_CONFFILE` : Fichier de configuration du cluster Ceph
    * `ROK4_CEPH_USERNAME` : Compte d'accès au cluster Ceph
    * `ROK4_CEPH_CLUSTERNAME` : Nom du cluster Ceph
    * `ROK4_S3_KEY` : Clé(s) de(s) serveur(s) S3
    * `ROK4_S3_SECRETKEY` : Clé(s) secrète(s) de(s) serveur(s) S3
    * `ROK4_S3_URL` : URL de(s) serveur(s) S3
    * `ROK4_SSL_NO_VERIFY` : Désactivation de la vérification SSL pour les accès S3 (n'importe quelle valeur non vide)
* `tile_matrix_set` :
    * `ROK4_TMS_DIRECTORY` : Dossier racine (fichier ou objet) des tile matrix sets
* `style` :
    * `ROK4_STYLES_DIRECTORY` : Dossier racine (fichier ou objet) des styles

Readings uses a LRU cache system with a TTL. It's possible to configure it with environment variables :
- ROK4_READING_LRU_CACHE_SIZE : Number of cached element. Default 64. Set 0 or a negative integer to configure a cache without bound. A power of two make cache more efficient.
- ROK4_READING_LRU_CACHE_TTL : Validity duration of cached element, in seconds. Default 300. 0 or negative integer to get cache without expiration date.

To disable cache (always read data on storage), set ROK4_READING_LRU_CACHE_SIZE to 1 and ROK4_READING_LRU_CACHE_TTL to 1.

Using CEPH storage requires environment variables :

Using S3 storage requires environment variables :

Plus d'exemple dans la documentation développeur.


## Contribuer

* Installer les dépendances de développement :

    ```sh
    python3 -m pip install -e .[dev]
    pre-commit install
    ```

* Consulter les [directives de contribution](./CONTRIBUTING.md)

## Compiler la librairie

```sh
apt install python3-venv python3-rados python3-gdal
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade build bump2version
bump2version --current-version 0.0.0 --new-version x.y.z patch

# Run unit tests
python3 -m pip install -e .[test]
# To use system installed modules rados and osgeo
echo "/usr/lib/python3/dist-packages/" >.venv/lib/python3.10/site-packages/system.pth
python3 -c 'import sys; print (sys.path)'
# Run tests
coverage run -m pytest
# Get tests report and generate site
coverage report -m
coverage html -d dist/tests/

# Build documentation
python3 -m pip install -e .[doc]
pdoc3 --html --output-dir dist/ rok4

# Build artefacts
python3 -m build
```

Remarque :

Lors de l'installation du paquet apt `python3-gdal`, une dépendance, peut demander des interactions de configuration. Pour installer dans un environnement non-interactif, définir la variable shell `DEBIAN_FRONTEND=noninteractive` permet d'adopter une configuration par défaut.

## Publier la librairie sur Pypi

Configurer le fichier `$HOME/.pypirc` avec les accès à votre compte PyPI.

```sh
python3 -m pip install --upgrade twine
python3 -m twine upload --repository pypi dist/rok4-x.y.z-py3-none-any.whl dist/rok4-x.y.z.tar.gz
```
