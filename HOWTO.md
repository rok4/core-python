
# Cas d'usage simple : exemple avec des données ALTI
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

    print(f"type de pyramide {pyr_alti_descriptor.type}")
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
