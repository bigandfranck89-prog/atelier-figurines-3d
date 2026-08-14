#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Les deux planches de présentation SALON, version soignée :
chaque objet rendu seul sous son meilleur angle, nom du chien visible,
carte avec ombre, en-tête et pastilles des 4 bobines."""
from plateau_salon3 import plateau as plateau1
from plateau_salon2 import poser_groupe, BOIS, BRUN, NOIR, BLANC
from objets import photophore
from objets2 import range_telecommande
from complements import pk01_porte_cles_photo, md01_medaillon, dc01_doseur, st01_support_telephone
from rendu2 import belle_image, carte, planche

PASTILLES = [(BOIS, 'bois clair'), (BRUN, 'brun chocolat'), (NOIR, 'noir mat'), (BLANC, 'blanc crème')]

# ---------------------------------------------------------------- plateau 1
VUES1 = {
    'Plaque niche Golden ULYSSE':    dict(azim=-90, elev=64, zoom=1.06),
    'Plaque porte os OLYMPE':        dict(azim=-90, elev=64, zoom=1.06),
    'Porte-cartes Détente Canine':   dict(azim=115, elev=16, zoom=1.0),
    'Porte-clés os STELLA':          dict(azim=-90, elev=68, zoom=1.04),
    'Porte-clés chien VÉNUS':        dict(azim=-90, elev=66, zoom=1.04),
    'Médaillon golden YUZU':         dict(azim=-90, elev=68, zoom=1.04),
    'Porte-clés patte':              dict(azim=-90, elev=68, zoom=1.04),
}
SOUS1 = {
    'Plaque niche Golden ULYSSE':  'Plaque de niche · 150 × 100 mm',
    'Plaque porte os OLYMPE':      'Plaque de porte · 168 × 74 mm',
    'Porte-cartes Détente Canine': 'Porte-cartes du salon · 52 × 96 mm',
    'Porte-clés os STELLA':        'Porte-clés os · 73 mm',
    'Porte-clés chien VÉNUS':      'Porte-clés · chien assis · 51 mm',
    'Médaillon golden YUZU':       'Porte-clés médaillon golden · Ø 42 mm',
    'Porte-clés patte':            'Porte-clés patte · 40 mm',
}

# ---------------------------------------------------------------- plateau 2
def objets2():
    objs = []
    from plateau_deco import rt_couleurs, ph_couleurs
    objs.append(('Range-télécommande', rt_couleurs(),
                 'Maison · 70 × 140 mm', dict(azim=100, elev=42, zoom=1.0)))
    cq, lm = dc01_doseur(en_pieces=True)
    objs.append(('Doseur à croquettes', [(cq, BLANC), (lm, BRUN)],
                 'Repas · Ø 78 · 80 mm', dict(azim=25, elev=22, zoom=1.0)))
    st = st01_support_telephone(en_pieces=True)
    objs.append(('Support téléphone',
                 [(st[0], NOIR), (st[1], BOIS)] + ([(st[2], BLANC)] if len(st) > 2 else []),
                 'Le chien tient le téléphone · 100 × 70 mm', dict(azim=-38, elev=24, zoom=1.0)))
    objs.append(('Photophore ajouré', ph_couleurs(),
                 'Déco · Ø 78 · 92 mm · bougie LED', dict(azim=-55, elev=20, zoom=1.0)))
    ca, mo = pk01_porte_cles_photo(en_pieces=True)
    objs.append(('Porte-clés photo', [(ca, BRUN), (mo, BLANC)],
                 'La photo du client en mini-lampe · 52 mm', dict(azim=-90, elev=66, zoom=1.04)))
    b6, r6 = md01_medaillon('VÉNUS', diam=36, en_pieces=True, tel='06 12 34 / 56 78 90')
    objs.append(('Médaillon VÉNUS', [(b6, BOIS), (r6, BRUN)],
                 'Recto prénom · verso téléphone gravé · Ø 36 mm', dict(azim=-90, elev=68, zoom=1.04)))
    return objs


if __name__ == '__main__':
    # plateau 1
    cartes1 = []
    for nom, parts in plateau1():
        vue = VUES1[nom]
        png = f'sortie4/pres1_{len(cartes1)}.png'
        belle_image(parts, png, **vue)
        cartes1.append(carte(png, nom.replace('Plaque niche Golden ', 'Plaque niche « ')
                             .replace('Plaque porte os ', 'Plaque os « ')
                             .replace('Porte-clés os ', 'Porte-clés os « ')
                             .replace('Porte-clés chien ', 'Porte-clés « ')
                             .replace('Médaillon golden ', 'Médaillon « ')
                             + (' »' if nom != 'Porte-cartes Détente Canine' and nom != 'Porte-clés patte' else ''),
                             SOUS1[nom]))
    p1 = planche(cartes1, 'FORGEON · Plateau 1 — le salon',
                 'Les chiens d’Angélique : Ulysse, Olympe, Stella, Vénus, Yuzu · 7 objets · 180 g · une journée d’impression',
                 PASTILLES, 'x', colonnes=4)
    p1.save('sortie4/PLANCHE_plateau1_salon.png')
    print('planche 1 ok')

    # plateau 2
    cartes2 = []
    for i, (nom, parts, sous, vue) in enumerate(objets2()):
        png = f'sortie4/pres2_{i}.png'
        belle_image(poser_groupe(parts, 0, 0), png, **vue)
        cartes2.append(carte(png, nom, sous))
    p2 = planche(cartes2, 'FORGEON · Plateau 2 — utile & déco',
                 'À lancer le lendemain · 6 objets · 348 g · mêmes 4 bobines',
                 PASTILLES, 'x', colonnes=3)
    p2.save('sortie4/PLANCHE_plateau2_deco.png')
    print('planche 2 ok')
