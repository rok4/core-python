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


    # Exploitation de la classe Pyramid
    print ("\nExploitation de la classe Pyramid\n")
    # POUR l'ALTI :
    print ("\npour des données ALTI\n")
    # chemin de la dalle ou du bloc de tuiles
    slab_alti_path = "~/Documents/Pyramide/RASTER/ALTI/01/DATA_10_21_29"
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
    print (f"données du slab: \n")
    print (f" type de slab {slab_indexes[0]}")
    print (f" identifiant du niveau {slab_indexes[1]}")
    print (f" nombre de tuiles en largeur par slab {slab_indexes[2]}")
    print (f" nombre de tuiles en hauteur par slab : {slab_indexes[3]}")
    level, col, row, pcol, prow = pyr_alti_descriptor.get_tile_indices(16, 16, "0", srs = "IGNF:LAMB93")

    data_binary = pyr_alti_descriptor.get_tile_data_binary(level, col, row)
    data_raster = pyr_alti_descriptor.get_tile_data_raster(level, col, row)

    #print(data_binary)
    print(data_raster)
    for (slab_type, level, column, row), infos in pyr_alti_descriptor.list_generator():
        print(infos)

    # pour la BDORTHO
    print ("\npour des données raster BDORTHO\n")
    pyramid_ortho_descriptor = Pyramid.from_descriptor("s3://pyramids/BDORTHO.json")
    slab_ortho_path = "~/Documents/Pyramide/RASTER/ALTI/01/DATA_13_168_234"

    print (f"créer une pyramide à partir du path de son descriptor {pyramid_ortho_descriptor}")
    print(f"type de pyramide {pyramid_ortho_descriptor.type}")
    print(f"format des tuiles de données vecteur : {pyramid_ortho_descriptor.format}")
    print(f"niveau le plus bas de la pyramide : {pyramid_ortho_descriptor.bottom_level}")
    print(f"niveau le plus haut de la pyramide : {pyramid_ortho_descriptor.top_level}")
    print ()
    slab_type, level, column, row = pyr_alti_descriptor.get_infos_from_slab_path(slab_ortho_path)
    slab_indexes = pyr_alti_descriptor.get_infos_from_slab_path(slab_ortho_path)
    print ("données du slab: \n")
    print (f" type de slab {slab_indexes[0]}")
    print (f" identifiant du niveau {slab_indexes[1]}")
    print (f" nombre de tuiles en largeur par slab {slab_indexes[2]}")
    print (f" nombre de tuiles en hauteur par slab : {slab_indexes[3]}")
    level, col, row, pcol, prow = pyramid_ortho_descriptor.get_tile_indices(16, 16, "0", srs = "IGNF:LAMB93")

    data_binary = pyramid_ortho_descriptor.get_tile_data_binary(level, col, row)
    data_raster = pyramid_ortho_descriptor.get_tile_data_raster(level, col, row)

    #print(data_binary)
    print(data_raster)

    # for (slab_type, level, column, row), infos in pyramid_ortho_descriptor.list_generator():
    #     print(infos)

    print("\n\n")

    # pour les limites ADMINISTRATIVES
    print ("\npour des données VECTEUR LES LIMITES ADMINISTRATIVES\n")
    pyramid_limits_administratives_descriptor = Pyramid.from_descriptor("s3://pyramids/LIMADM.json")
    slab_limits_administratives_path = "~/Documents/Pyramide/VECTEUR/LIMITES_ADMINISTRATIVES/DATA_15_678_940"

    slab_indexes = pyramid_limits_administratives_descriptor.get_infos_from_slab_path(slab_limits_administratives_path)
    print(f"type de pyramide {pyramid_limits_administratives_descriptor.type}")
    print(f"format des tuiles de données vecteur : {pyramid_limits_administratives_descriptor.format}")
    print(f"niveau le plus bas de la pyramide : {pyramid_limits_administratives_descriptor.bottom_level}")
    print(f"niveau le plus haut de la pyramide : {pyramid_limits_administratives_descriptor.top_level}")
    print (f"créer une pyramide à partir du path de son descriptor : {pyramid_limits_administratives_descriptor}")
    print ("données du slab: \n")
    print (f" type de slab {slab_indexes[0]}")
    print (f" identifiant du niveau {slab_indexes[1]}")
    print (f" nombre de tuiles en largeur par slab {slab_indexes[2]}")
    print (f" nombre de tuiles en hauteur par slab : {slab_indexes[3]}")
    print("\n")
    """ for (slab_type, level, column, row), infos in pyramid_limits_administratives_descriptor.list_generator():
        print(infos) """
