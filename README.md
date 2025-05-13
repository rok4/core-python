# Librairies ROK4 Python

![ROK4 Logo](https://rok4.github.io/assets/images/rok4.png)

Ces librairies facilitent la manipulation d'entités du projet ROK4 comme les Tile Matrix Sets, les pyramides ou encore les couches, ainsi que la manipulation des stockages associés.

## Installer la librairie

Installations système requises :

* debian : `apt install python3-rados python3-gdal`

Puis passer en mode superutilisateur pour taper cette ligne de commande et installer l'environnement virtuel de python :
```sh
sudo apt install python3.10-venv
```
puis revenir en mode normal et tapez cette ligne de commande :
```sh
source .venv/bin/activate
```

L'environnement d'exécution doit avoir accès aux librairies système. Dans le cas d'une utilisation au sein d'un environnement python, précisez bien à la création `python3 -m venv --system-site-packages .venv`.

Depuis [PyPI](https://pypi.org/project/rok4/) : `pip install rok4`

Depuis [GitHub](https://github.com/rok4/core-python/releases/) : `pip install https://github.com/rok4/core-python/releases/download/x.y.z/rok4-x.y.z-py3-none-any.whl`

## Utiliser la librairie

En dehors du dépôt `core-python`, tapez les ligne de commande suivantes dans un fichier shell `envvar.sh` contenant l'export de toutes les

variables d'environnement du projet `ROK4`:

```sh
export ROK4_TMS_DIRECTORY=s3://tilematrixsets
export ROK4_S3_KEY=rok4
export ROK4_S3_SECRETKEY=rok4S3storage
export ROK4_S3_URL=http://localhost:9000
```


### Comment définir le stockage de tous les buckets du projet rok4 sur le bucket s3 ?

![ROK4 STOCKAGE BUCKET](./HOWTO.md#comment-d%C3%A9finir-le-stockage-de-tous-les-buckets-du-projet-rok4-sur-le-bucket-s3-)


### Comment définir des données VECTEUR ?

*   A partir d'un fichier vecteur (shapefile, csv, GeoJSON ou Geopackage),
    *   le chemin d'accès au fichier/objet,
    *   csv : le dictionnaire des paramètres CSV :
        -srs : système de référence spatiale de la géométrie,
        -column_x : le champ de coordonnée X
        -column_y : le champ de coordonnée Y
        -column_wkt : le champ du WKT(Well Known Text) de la géométrie

*   A partir des paramètres :
    *   le chemin d'accès au fichier/objet,
    *   bbox : le rectangle de la boundary box dans la projection des données
    *   layers : le nom des couches vecteurs, leur nombre d'objets avec leurs attributs

![ROK4 DATA VECTEUR](./HOWTO.md#comment-exploiter-des-donn%C3%A9es-vecteur-)

### Comment définir des données RASTER et une structure décrivant un jeu de données RASTER ?

On part de la classe 'RasterSet()' qui décrit la structure d'un jeu de données raster :

*   à partir du descriptor ```"file:///data/images/descriptor.json"```
*   ou bien à partir d'une liste d'images et de code srs ```(
                        path="file:///data/SC1000.list",
                        srs="EPSG:3857"
                    )```


On part de la classe 'Raster()' qui définit des données raster :
*   à partir d'informations d'un fichier stocké en image TIFF ```file:///data/SC1000/0040_6150_L93.tif```
*   à partir d'un chargement d'informations à partir de paramètres liées à une image TIFF ```file:///data/SC1000/_0040_6150_L93.tif``` couplée à un masque d'image TIFF ```file:///data/SC1000/0040_6150_L93.msk```


Ces deux méthodologies permettent de retourner un sortie les éléments suivants décrivant le jeu de données raster :
*   chemin d'accès au fichier/objet (ex: file:///path/to/image.tif or s3://bucket/image.tif)
*   nombre de bandes colorées,
*   la boundary box (le rectangle),
*   les dimensions de l'image en pixel,
*   le format numérique des valeurs des couleurs,
*   le chemin d'accès au masque associé,
*   l'extension du masque et du fichier au format TIFF. (ex: ```file:///path/to/image.msk``` or ```s3://bucket/image.msk```)

![ROK4 RASTERSET](./HOWTO.md#comment-exploiter-des-donn%C3%A9es-raster-)

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
