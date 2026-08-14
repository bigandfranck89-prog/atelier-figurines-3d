#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Les 5 premiers objets non canins — dessin, controle, fichiers.

Regles de dessin appliquees a tous :
  - poses a plat sur le plateau, aucune bequille (support) necessaire
  - toute matiere qui surplombe le vide reste sous 45 degres
  - parois de 1,6 mm minimum (4 passages de buse de 0,4)
  - dimensions du monde reel (carte de visite 90x55, casque, bougie chauffe-plat)
"""
import numpy as np
import trimesh
from shapely.geometry import Polygon, Point
from shapely.affinity import translate as sh_translate

MM = 1.0


# ----------------------------------------------------------------- outils

def extruder(profil_xy, hauteur, trous=None):
    """Extrude un contour 2D (liste de points) sur une hauteur en Z."""
    poly = Polygon(profil_xy, holes or []) if (holes := trous) else Polygon(profil_xy)
    return trimesh.creation.extrude_polygon(poly, hauteur)


def arrondi_rect(l, h, r, n=12):
    """Rectangle a coins arrondis, centre en 0."""
    p = Polygon([(-l / 2, -h / 2), (l / 2, -h / 2), (l / 2, h / 2), (-l / 2, h / 2)])
    return p.buffer(-r, join_style=1).buffer(r * 2, join_style=1).buffer(-r, join_style=1)


def losange(cx, cy, larg, haut):
    """Trou en losange : ses deux faces hautes sont a moins de 45 degres."""
    return Polygon([(cx, cy - haut / 2), (cx + larg / 2, cy),
                    (cx, cy + haut / 2), (cx - larg / 2, cy)])


def controle(m, nom, plateau=250.0, mode='normal', appuis=()):
    """Mesure et verdict d'imprimabilite."""
    m = m.copy()
    m.fix_normals()
    m.apply_translation(-m.bounds[0])                     # pose sur le plateau
    n = m.face_normals
    a = m.area_faces
    # une face qui regarde vers le bas a plus de 45 degres = porte-a-faux...
    masque = n[:, 2] < -np.cos(np.radians(45))
    # ... sauf le dessous qui repose sur le plateau : il ne surplombe rien.
    z_faces = m.vertices[m.faces][:, :, 2].max(axis=1)
    sur_plateau = z_faces < 0.6
    for z_appui in appuis:                                # faces posees sur un autre corps
        sur_plateau |= np.abs(z_faces - z_appui) < 0.05
    masque = masque & ~sur_plateau
    # ... ni une face qui s'appuie sur de la matiere juste en dessous
    idx = np.where(masque)[0]
    if len(idx):
        centres = m.triangles_center[idx] + np.array([0, 0, -0.15])
        dirs = np.tile([0, 0, -1.0], (len(idx), 1))
        pts, ray_id, _ = m.ray.intersects_location(ray_origins=centres, ray_directions=dirs)
        if len(pts):
            dist = centres[ray_id][:, 2] - pts[:, 2]
            # soutenu seulement si la matiere est a moins d'un millimetre en dessous
            proches = np.unique(ray_id[dist < 1.0])
            masque[idx[proches]] = False
    pct = 100.0 * a[masque].sum() / a.sum()
    dim = m.extents
    vol = m.volume / 1000.0                               # cm3
    aire = m.area / 100.0                                 # cm2
    if mode == 'spirale':
        # imprime en une seule paroi qui monte en tournant
        matiere = (aire / 2) * 0.08                       # 0,8 mm d'epaisseur
    else:
        coque = min(aire * 0.12, vol)                     # 1,2 mm de paroi pleine
        matiere = coque + (vol - coque) * 0.15            # 15 % de remplissage
    poids = matiere * 1.24
    surface = (dim[0] * dim[1]) / 100.0                   # cm2 au sol
    verdict = 'vert' if pct < 3 else ('orange' if pct < 8 else 'rouge')
    return m, {
        'nom': nom,
        'matiere_cm3': round(matiere, 1),
        'dim_mm': f"{dim[0]:.0f} x {dim[1]:.0f} x {dim[2]:.0f}",
        'volume_cm3': round(vol, 1),
        'poids_g': round(poids, 1),
        'cout_eur': round(poids / 1000 * 20, 2),
        'porte_a_faux_pct': round(pct, 1),
        'surface_plateau_cm2': round(surface, 1),
        'etanche': bool(m.is_watertight),
        'faces': int(len(m.faces)),
        'tient_plateau': bool(max(dim[0], dim[1]) <= plateau and dim[2] <= plateau),
        'verdict': verdict,
    }


# ------------------------------------------------------ 1. porte-cartes

def porte_cartes():
    """Carte de visite standard 90 x 55 mm. Bloc en coin, fente inclinee.
    Imprime sur sa face arriere : la fente devient verticale, zero bequille."""
    L = 100.0                       # carte de 90 mm + marge
    # profil vu de cote (X = profondeur, Y = hauteur) : large en bas, etroit en haut,
    # et la fente s'ouvre vers le CIEL -> aucune matiere ne surplombe le vide.
    # le contour fait le tour ET plonge dans la fente : celle-ci debouche en haut
    exterieur = [
        (0, 0), (58, 0), (58, 10), (46, 42),
        (35, 42), (30, 9), (25, 9), (21, 42),
        (12, 42), (0, 10),
    ]
    poly = Polygon(exterieur)
    m = trimesh.creation.extrude_polygon(poly, L)
    m.apply_transform(trimesh.transformations.rotation_matrix(-np.pi / 2, [1, 0, 0]))
    m.apply_transform(trimesh.transformations.rotation_matrix(np.pi, [0, 0, 1]))
    return m


# ------------------------------------------------- 2. support de casque

def support_casque():
    """Profil decoupe de cote puis epaissi : la forme entiere est verticale,
    donc rien ne surplombe le vide. Arche de 150 mm pour un casque adulte."""
    e = 70.0                       # epaisseur (largeur de l'arche)
    profil = [
        (0, 0), (95, 0), (95, 8), (58, 14),          # pied lourd
        (52, 40), (50, 120),                          # colonne qui monte
        (58, 175), (78, 205), (96, 218),              # col qui part en avant
        (96, 232), (72, 224), (44, 196),              # crochet (dessous a 45 deg)
        (32, 150), (30, 60), (16, 16), (0, 12),
    ]
    m = extruder(profil, e)
    # on couche le profil : X = profondeur, Y = largeur, Z = hauteur
    m.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))
    return m


# --------------------------------------------------------- 3. photophore

def photophore():
    """Bougie chauffe-plat LED de 40 mm. Paroi ajouree de losanges :
    aucun sommet de trou n'est plat, donc aucun pont a imprimer."""
    d_ext, h = 78.0, 92.0
    paroi = 2.0
    exterieur = Point(0, 0).buffer(d_ext / 2, resolution=64)
    interieur = Point(0, 0).buffer(d_ext / 2 - paroi, resolution=64)
    tube = trimesh.creation.extrude_polygon(Polygon(exterieur.exterior.coords,
                                                    [interieur.exterior.coords]), h)
    fond = trimesh.creation.extrude_polygon(exterieur, 2.5)

    # rangees de losanges decalees
    trous = []
    for rang, z in enumerate(np.arange(14, h - 12, 17.0)):
        for k in range(10):
            ang = np.radians(k * 36 + (18 if rang % 2 else 0))
            lo = trimesh.creation.box(extents=[24, 13, 13])
            lo.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 4, [1, 0, 0]))
            lo.apply_transform(trimesh.transformations.rotation_matrix(ang, [0, 0, 1]))
            lo.apply_translation([np.cos(ang) * d_ext / 2, np.sin(ang) * d_ext / 2, z])
            trous.append(lo)

    m = trimesh.boolean.difference([trimesh.util.concatenate([tube, fond])] + trous)
    return m


# ------------------------------------------------------ 4. prenom relief

def prenom(texte='LOU', en_pieces=False):
    """Plaque + prenom en relief. Les lettres montent droit : rien ne surplombe."""
    from matplotlib.textpath import TextPath
    from matplotlib.font_manager import FontProperties
    from shapely.ops import unary_union
    from shapely.geometry.polygon import orient

    fp = FontProperties(family='DejaVu Sans', weight='bold')
    contours = TextPath((0, 0), texte, size=48, prop=fp).to_polygons()
    polys = sorted([Polygon(c) for c in contours if len(c) > 2], key=lambda p: -p.area)
    pleins, creux = [], []
    for p in polys:
        (creux if any(g.contains(p) for g in pleins) else pleins).append(p)
    parts = [orient(Polygon(p.exterior.coords,
                            [c.exterior.coords for c in creux if p.contains(c)]), 1.0)
             for p in pleins]
    mot = unary_union(parts)
    morceaux = list(mot.geoms) if mot.geom_type == 'MultiPolygon' else [mot]

    lettres = trimesh.util.concatenate(
        [trimesh.creation.extrude_polygon(g, 7.0) for g in morceaux])
    lettres.fix_normals()
    lettres.apply_translation(-lettres.bounds[0])

    lx, ly = lettres.extents[0], lettres.extents[1]
    plaque = trimesh.creation.extrude_polygon(arrondi_rect(lx + 26, ly + 22, 6), 4.0)
    plaque.apply_translation(-plaque.bounds[0])
    lettres.apply_translation([13, 11, 1.0])          # les lettres mordent dans la plaque

    # deux corps qui se touchent : le trancheur les fusionne, et on evite
    # les surprises d'un calcul booleen sur des lettres fines.
    lettres.apply_translation([0, 0, 3.0])             # les lettres posent sur la plaque
    if en_pieces:
        return plaque, lettres
    return trimesh.util.concatenate([plaque, lettres])


# ------------------------------------------------------------- 5. vase

def vase():
    """Vase torsade : la paroi monte en tournant, chaque couche deborde
    de moins d'un demi-millimetre sur la precedente."""
    h, n_z, n_a = 175.0, 90, 96
    zs = np.linspace(0, h, n_z)
    sommets, faces = [], []
    for i, z in enumerate(zs):
        t = z / h
        rayon = 34 + 22 * np.sin(np.pi * t * 0.92)        # ventru au milieu
        torsion = np.radians(85) * t
        for k in range(n_a):
            a = 2 * np.pi * k / n_a
            ondulation = 1 + 0.13 * np.sin(6 * (a + torsion))
            r = rayon * ondulation
            sommets.append([r * np.cos(a), r * np.sin(a), z])
    for i in range(n_z - 1):
        for k in range(n_a):
            a0 = i * n_a + k
            a1 = i * n_a + (k + 1) % n_a
            b0, b1 = a0 + n_a, a1 + n_a
            faces += [[a0, b0, b1], [a0, b1, a1]]
    # fond
    c_bas = len(sommets); sommets.append([0, 0, 0])
    for k in range(n_a):
        faces.append([c_bas, (k + 1) % n_a, k])
    # bord haut ferme (vase plein, creuse par le trancheur en mode spirale)
    c_haut = len(sommets); sommets.append([0, 0, h])
    for k in range(n_a):
        faces.append([c_haut, (n_z - 1) * n_a + k, (n_z - 1) * n_a + (k + 1) % n_a])
    m = trimesh.Trimesh(vertices=np.array(sommets), faces=np.array(faces))
    m.fix_normals()
    return m


# ------------------------------------------------------------------ main

OBJETS = [
    ('PCV-01', 'Le Porte-cartes de visite', 'Bureau', porte_cartes,   'normal'),
    ('SC-01',  'Le Support de casque',      'Bureau', support_casque, 'normal'),
    ('PH-01',  'Le Photophore ajoure',      'Deco',   photophore,     'normal'),
    ('PR-01',  'Le Prenom en relief',       'Deco',   prenom,         'normal'),
    ('VS-01',  'Le Vase torsade',           'Deco',   vase,           'spirale'),
]

if __name__ == '__main__':
    import json, os
    os.makedirs('sortie', exist_ok=True)
    rapport = []
    for ref, nom, famille, f, mode in OBJETS:
        m = f()
        m, infos = controle(m, nom, mode=mode)
        infos['mode'] = mode
        infos['ref'] = ref
        infos['famille'] = famille
        m.export(f'sortie/{ref}.stl')
        rapport.append(infos)
        print(ref, json.dumps(infos, ensure_ascii=False))
    json.dump(rapport, open('sortie/rapport.json', 'w'), ensure_ascii=False, indent=1)
