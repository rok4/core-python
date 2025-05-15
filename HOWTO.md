## Exemples de cas d'utilisations des librairies du projet ROK4

tapez les ligne de commande suivantes afin d'exporter toutes les variables d'environnement du projet `ROK4`:

```sh
export ROK4_TMS_DIRECTORY=s3://tilematrixsets
export ROK4_S3_KEY=rok4
export ROK4_S3_SECRETKEY=rok4S3storage
export ROK4_S3_URL=http://localhost:9000
```

### Comment lire une tuile de pyramide de données raster ?

*   On doit passer le bucket s3 de stockage exemple : ```"s3://pyramids/ALTI.json"``` en paramètre d'entrée de la méthode de classe ```from_descriptor()``` appliquée à la classe ```Pyramid()``` tel que :

```py
    # descriptor de la pyramide ALTI
    pyr_alti_descriptor = Pyramid.from_descriptor("s3://pyramids/ALTI.json")
```

*   Si l'on veut obtenir les indices d'une tuile de pyramide raster, on utilise la fonction ```get_tiles_indices(x_point, y_point, pyramid_level,srs_coords)```

```py
level, col, row, pcol, prow = pyr_alti_descriptor.get_tile_indices(16, 16, "0", srs = "IGNF:LAMB93")
```

où :
*   pcol : indice de colonne de pixels à partir des coordonnées du point,
*   prow : indice de rangée de pixels à partir des coordonnées du point,
*   level : niveau de la tuile,
*   col : colonne de la tuile,
*   row : rangée de la tuile.


*   Si l'on veut récupérer les données raster d'une tuile de Pyramide :
```py
data_raster = pyr_alti_descriptor.get_tile_data_raster(level, col, row)
```
![ROK4 pyramide ALTI](./HOWTO.md#cas-dusage-simple--exemple-avec-des-donn%C3%A9es-alti)

### Comment lire une tuile de pyramide de données vecteur ?

*   Même principe qu'avec le cas RASTER, si l'on veut récupérer les données vecteur d'une tuile de Pyramide :

*   Cas d'usage : données VECTEUR : pyramide LIMITES ADMINISTRATIVES
```py
pyramid_vector = Pyramid.from_descriptor("s3://pyramids/LIMADM.json")
level, col, row, pcol, prow = pyramid.get_tile_indices(tile_level, tile_column, tile_row)
data_vector = pyramid.get_tile_data_vector(level, col, row)
```

![ROK4 pyramide VECTEUR](./HOWTO.md#comment-exploiter-des-donn%C3%A9es-vecteur-)


### Comment exploiter des données vecteur ?

*   A partir du chargement d'un fichier vecteur (shapefile, csv, GeoJSON ou Geopackage) comme suit :
    *  le chemin d'accès au fichier/objet,
    *  csv : le dictionnaire des paramètres CSV.

```py
from rok4.vector import Vector

vector = Vector.from_file("https://github.com/rok4/core-python/blob/develop/tests/fixtures/ARRONDISSEMENT.shp")
vector_csv1 = Vector.from_file(
    "https://github.com/rok4/core-python/blob/develop/tests/fixtures/vector.csv",
    csv={"delimiter":";", "column_x":"x", "column_y":"y"}
)
vector_csv2 = Vector.from_file(
    "https://github.com/rok4/core-python/blob/develop/tests/fixtures/vector2.csv",
    csv={"delimiter":";", "column_wkt":"WKT"}
)
```

*   A partir des paramètres comme suit :
    *  le chemin d'accès au fichier/objet,
    *  bbox : le rectangle de la boundary box dans la projection des données,
    *  layers : le nom des couches vecteurs, leur nombre d'objets avec leurs attributs.

```py
from rok4.vector import Vector

vector = Vector.from_parameters(
    "https://github.com/rok4/core-python/blob/develop/tests/fixtures/ARRONDISSEMENT.shp", 
    (1,2,3,4), 
    [('ARRONDISSEMENT', 14, [('ID', 'String'), ('NOM', 'String'), ('INSEE_ARR', 'String'), ('INSEE_DEP', 'String'), ('INSEE_REG', 'String'), ('ID_AUT_ADM', 'String'), ('DATE_CREAT', 'String'), ('DATE_MAJ', 'String'), ('DATE_APP', 'Date'), ('DATE_CONF', 'Date')]
    )]
)
```

### Comment exploiter des données raster ?

On part de la classe 'RasterSet()' qui décrit la structure d'un jeu de données raster :

*  à partir du descriptor tel que :

```py
from rok4.raster import RasterSet

raster_set = RasterSet.from_descriptor(
                        "file:///data/images/descriptor.json"
)
```

*  ou bien à partir d'une liste d'images et de code srs tel que :

```py
from rok4.raster import RasterSet

raster_set = RasterSet.from_list(
                        path="file:///data/SC1000.list",
                        srs="EPSG:3857"
)
```

On part de la classe 'Raster()' qui définit des données raster :

*  à partir d'informations d'un fichier stocké en image TIFF tel que :

```py
from rok4.raster import Raster

raster = Raster.from_file("file:///data/SC1000/0040_6150_L93.tif")
```

*  à partir d'un chargement d'informations à partir de paramètres liées à une image TIFF couplée à un masque d'image TIFF tel que :

```py
from rok4.raster import Raster

raster = Raster.from_parameters(
    path="file:///data/SC1000/_0040_6150_L93.tif",
    mask="file:///data/SC1000/0040_6150_L93.msk",
    bands=3,
    format=ColorFormat.UINT8,
    dimensions=(2000, 2000),
    bbox=(40000.000, 5950000.000, 240000.000, 6150000.000)
)
```


### Comment définir le stockage de tous les buckets du projet rok4 sur le bucket s3 ?

=> exemple pour la BDORTHO : ```s3://layers/bdortho.json```

*  Pour obtenir le niveau le plus bas et le niveau le plus haut des pyramides de tuile à partir du descriptor:
```py
from rok4.pyramid import Pyramid
from rok4.storage import get_data_str, get_infos_from_path, put_data_str
from rok4.utils import reproject_bbox

storage_type, path, root, base_name = get_infos_from_path(descriptor)
pyramids = [{
    "bottom_level": "13", 
    "top_level": "0", 
    "path": "s3://pyramids/BDORTHO.json"
    }]
for p in pyramids :
    pyramid = Pyramid.from_descriptor(p["path"])
    bottom_level = p.get("bottom_level", None)
    top_level = p.get("top_level", None)
levels = pyramid.get_levels(bottom_level, top_level)
```

### Cas d'usage simple : exemple avec des données ALTI

```sh
myusername@pcname:~$ python3 data_tilesmatrix_launcher.py
créer une pyramide à partir du path de son descriptor RASTER pyramid 'ALTI' (S3 storage)
format des tuiles de données vecteur : TIFF_ZIP_FLOAT32
niveau le plus bas de la pyramide : RASTER pyramid's level '13' (S3 storage)
niveau le plus haut de la pyramide : RASTER pyramid's level '0' (S3 storage)
données du slab:
type de slab SlabType.DATA
identifiant du niveau 10
nombre de tuiles en largeur par slab 21
nombre de tuiles en hauteur par slab : 29
 ```

### Comment obtenir ces résultats ?

```py
#!/usr/bin/env python3

# import des packages de rok4
from rok4.enums import PyramidType, SlabType, StorageType, ColorFormat
from rok4.pyramid import Pyramid, Level

# chemin du descriptor de la pyramide alti
path_to_pyramid_alti_descriptor = "s3://pyramids/ALTI.json"

# descriptor de la pyramide ALTI
pyr_alti_descriptor = Pyramid.from_descriptor(path_to_pyramid_alti_descriptor)
print (f"créer une pyramide à partir du path de son descriptor {pyr_alti_descriptor}")

print(f"format des tuiles de données vecteur : {pyr_alti_descriptor.format}")
print(f"niveau le plus bas de la pyramide : {pyr_alti_descriptor.bottom_level}")
print(f"niveau le plus haut de la pyramide : {pyr_alti_descriptor.top_level}")

slab_type, level, column, row = pyr_alti_descriptor.get_infos_from_slab_path(slab_alti_path)
slab_indexes = pyr_alti_descriptor.get_infos_from_slab_path(slab_alti_path)

print ("données du slab: \n")
print (f" type de slab {slab_indexes[0]}")
print (f" identifiant du niveau {slab_indexes[1]}")
print (f" nombre de tuiles en largeur par slab {slab_indexes[2]}")
print (f" nombre de tuiles en hauteur par slab : {slab_indexes[3]}")
level, col, row, pcol, prow = pyr_alti_descriptor.get_tile_indices(16, 16, "0", srs = "IGNF:LAMB93")
data_raster = pyr_alti_descriptor.get_tile_data_raster(level, col, row)

print(data_raster)
 ```

### Cas d'usage simple avec le TileMatrixSet "PM":

emplacement du bucket de stockage : ```s3://tilematrixsets/PM.json```

voici une partie de sa structure en objet json pour le tms ```PM```:

```json
{
   "tileMatrices" : [
      {
         "id" : "0",
         "tileWidth" : 256,
         "scaleDenominator" : 559082264.028718,
         "matrixWidth" : 1,
         "cellSize" : 156543.033928041,
         "matrixHeight" : 1,
         "tileHeight" : 256,
         "pointOfOrigin" : [
            -20037508.3427892,
            20037508.3427892
         ]
      },
      {
         "matrixHeight" : 2,
         "pointOfOrigin" : [
            -20037508.3427892,
            20037508.3427892
         ],
         "tileHeight" : 256,
         "cellSize" : 78271.5169640205,
         "scaleDenominator" : 279541132.014359,
         "matrixWidth" : 2,
         "tileWidth" : 256,
         "id" : "1"
      },
      {
         "cellSize" : 39135.7584820102,
         "pointOfOrigin" : [
            -20037508.3427892,
            20037508.3427892
         ],
         "tileHeight" : 256,
         "matrixHeight" : 4,
         "tileWidth" : 256,
         "matrixWidth" : 4,
         "scaleDenominator" : 139770566.007179,
         "id" : "2"
      },{},{},...
}
```

### Exploitation des données d'un fichier JSON d'un tilematrixset exemple : PM.json

```py
#!/usr/bin/env python3
import json
# import des packages de rok4
from rok4.enums import PyramidType, SlabType, StorageType, ColorFormat
from rok4.tile_matrix_set import TileMatrix, TileMatrixSet

try:
    tms = TileMatrixSet("PM")
    print(f"le nom du tms : {tms.name}")
    print(f"le chemin du tms : {tms.path}")
    print(f"le code srs : {tms.srs}")

    typePyramid = PyramidType("RASTER")
    slabType = SlabType("MASK")
    storageType = StorageType("s3://")

    print (f"type de pyramide : {typePyramid}")
    print (f"type de slab : {slabType}")
    print (f"type de stockage : {storageType}")

    # Ouverture d'un fichier JSON d'un tilematrixset
    print ("\nOuverture d'un fichier JSON d'un tilematrixset\n")

    with open("s3://tilematrixsets/PM.json") as json_file:
        data = json.load(json_file)
        print(f"type de structure de données de data : {type(data)}")
        print(f'nom de la pyramide : {data["id"]}')
        print(f'code srs projection planimétrique : {data["crs"]}')
        print(f'nombre de tuiles de la pyramide : {len(data["tileMatrices"])}')
        print(f'coordonnées du point origine : {data["tileMatrices"][0]["pointOfOrigin"]}')
        print(f'taille de la cellule : {data["tileMatrices"][0]["cellSize"]}')
        print(f'nombre d"éléments de la matrices de tuiles cad le nombre de tuiles : {len(data["tileMatrices"])}')

except Exception as exc :
    print (exc)
```

### Exemple de style du projet rok4 :

* Exemple du style : la **montagne palette** parmi les **onze styles** stockés sur le bucket de stockage s3 :

* Ci-jointe la structure en objet json dont l'emplacement est le suivant ```s3://styles/montagne_palette.json```:

```json
{
	"identifier": "montagne_palette",
    "title": "Pente par paliers standards",
	"abstract": "Pente affichée par parlier standard de 30 a 90 degres",
	"keywords": ["MNT"],
    "legend": {
        "format": "image/png",
        "url": "http://ign.fr",
        "height": 100,
        "width": 100,
        "min_scale_denominator": 0,
        "max_scale_denominator": 30
    },
    "palette": {
        "max_value": 91,
        "rgb_continuous": true,
        "alpha_continuous": true,
        "colours": [
            { "value": 0, "red": 255, "green": 255, "blue": 255, "alpha": 0 },
            { "value": 29, "red": 255, "green": 255, "blue": 255, "alpha": 0 },
            { "value": 30, "red": 242, "green": 229, "blue": 0, "alpha": 255 },
            { "value": 34, "red": 242, "green": 229, "blue": 0, "alpha": 255 },
            { "value": 35, "red": 243, "green": 148, "blue": 25, "alpha": 255 },
            { "value": 39, "red": 243, "green": 148, "blue": 25, "alpha": 255 },
            { "value": 40, "red": 225, "green": 0, "blue": 0, "alpha": 255 },
            { "value": 44, "red": 225, "green": 0, "blue": 0, "alpha": 255 },
            { "value": 45, "red": 200, "green": 137, "blue": 187, "alpha": 255 },
            { "value": 90, "red": 200, "green": 137, "blue": 187, "alpha": 255 },
            { "value": 91, "red": 255, "green": 255, "blue": 255, "alpha": 0 }
        ]
    }
}
```
