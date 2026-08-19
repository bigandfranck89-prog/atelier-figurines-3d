#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""FIN DE LA LIGNE « DESSINER LA COULEUR DANS LE CATALOGUE » (tache 1349).

Ce qui restait au 18/08 : le photophore silhouette de race, les plaques en
trois couleurs, et la gamme « couleurs du salon ». C'est ici.

REGLE ANTI-GASPILLAGE DU 13/08 APPLIQUEE PARTOUT : la couleur se decoupe en
BANDES DE HAUTEUR. Chaque objet de ce fichier annonce lui-meme ses hauteurs de
coupe, et aucun ne demande plus de DEUX changements de fil.

VERITE MATIERE (note « LES MATIERES SPECIALES ») : le marbre ne laisse pas
passer la lumiere. Un photophore garde donc une partie HAUTE EN BLANC — la
couleur va dans la bande basse, qui ne sert pas a eclairer.
"""
import numpy as np
import trimesh
from shapely.geometry import Point
from shapely.affinity import scale as sh_scale, translate as sh_translate

from objets import arrondi_rect, controle
from plaques_race2 import texte_poly, extrude_multi
from races2 import RACES


# =====================================================================
# 1. PHOTOPHORE SILHOUETTE DE RACE
#    Deux bandes, UN SEUL changement. Paroi mince partout dans la bande
#    haute : la bougie la traverse. La silhouette, elle, garde toute son
#    epaisseur — donc elle reste NOIRE en ombre chinoise sur la lumiere.
# =====================================================================

PHOTO_DIAM = 78.0     # diametre exterieur
PHOTO_HAUT = 95.0     # hauteur totale
PHOTO_FOND = 2.4      # epaisseur du fond
PHOTO_BAS = 28.0      # hauteur de la bande basse (couleur) -> LA COUPE
PHOTO_MINCE = 1.0     # paroi qui laisse passer la lumiere
PHOTO_EPAIS = 2.4     # paroi de la bande basse et epaisseur de la silhouette


def _anneau(r_ext, r_int, z0, z1, seg=180):
    """Anneau plein entre deux rayons, de z0 a z1."""
    couronne = Point(0, 0).buffer(r_ext, resolution=seg // 4).difference(
        Point(0, 0).buffer(r_int, resolution=seg // 4))
    m = trimesh.creation.extrude_polygon(couronne, z1 - z0)
    m.apply_translation([0, 0, z0])
    return m


def _plaque_cintree(poly, r_peau, ep, z_bas, angle0=0.0, pas=0.9):
    """Prend un contour 2D et l'enroule sur l'interieur du cylindre.

    poly est dans un repere ou x est la LONGUEUR D'ARC en mm et y la hauteur.
    Le resultat mord de 0,3 mm dans la paroi pour que la soudure soit franche.
    """
    plate = extrude_multi(poly, ep + 0.3)
    v, f = trimesh.remesh.subdivide_to_size(plate.vertices, plate.faces, max_edge=pas)
    x, y, z = v[:, 0], v[:, 1], v[:, 2]
    theta = angle0 + x / r_peau               # longueur d'arc -> angle
    r = (r_peau + 0.3) - z                    # z=0 dans la paroi, z=max vers l'interieur
    w = np.column_stack([r * np.cos(theta), r * np.sin(theta), z_bas + y])
    m = trimesh.Trimesh(vertices=w, faces=f, process=True)
    m.fix_normals()
    return m


def photophore_race(race='neutre', prenom=None, diam=PHOTO_DIAM, haut=PHOTO_HAUT):
    """Photophore a bougie LED. Silhouette de race en ombre chinoise.

    Rend (mesh, coupes, couleurs) : coupes = hauteurs de changement de fil.
    """
    nom = RACES[race][0]
    ro = diam / 2.0
    ri_mince = ro - PHOTO_MINCE
    ri_epais = ro - PHOTO_EPAIS

    fond = trimesh.creation.cylinder(radius=ro, height=PHOTO_FOND, sections=180)
    fond.apply_translation([0, 0, PHOTO_FOND / 2])
    paroi = _anneau(ro, ri_mince, PHOTO_FOND, haut)
    doublage = _anneau(ri_mince + 0.01, ri_epais, PHOTO_FOND, PHOTO_BAS)

    corps = trimesh.boolean.union([fond, paroi, doublage])

    pieces = [corps]

    # --- la silhouette, enroulee sur la paroi mince ---
    zone_h = haut - PHOTO_BAS - 16.0                     # marge haute
    sil = RACES[race][1]().buffer(0)
    x0, y0, x1, y1 = sil.bounds
    k = min((np.pi * ri_mince * 0.62) / (x1 - x0), zone_h / (y1 - y0))
    sil = sh_scale(sil, xfact=k, yfact=k, origin=(x0, y0))
    x0, y0, x1, y1 = sil.bounds
    sil = sh_translate(sil, xoff=-x0, yoff=-y0)
    arc = x1 - x0
    pieces.append(_plaque_cintree(
        sil, ri_mince, PHOTO_EPAIS - PHOTO_MINCE + 0.6,
        z_bas=PHOTO_BAS + 6.0, angle0=-arc / (2 * ri_mince)))

    # --- le prenom, enroule a l'oppose ---
    if prenom:
        t = texte_poly(prenom, taille=22)
        tx0, ty0, tx1, ty1 = t.bounds
        kt = min((np.pi * ri_mince * 0.40) / (tx1 - tx0), 16.0 / (ty1 - ty0))
        t = sh_scale(t, xfact=kt, yfact=kt, origin=(tx0, ty0))
        tx0, ty0, tx1, ty1 = t.bounds
        t = sh_translate(t, xoff=-tx0, yoff=-ty0)
        arct = tx1 - tx0
        pieces.append(_plaque_cintree(
            t, ri_mince, PHOTO_EPAIS - PHOTO_MINCE + 0.6,
            z_bas=PHOTO_BAS + 14.0,
            angle0=np.pi - arct / (2 * ri_mince)))

    m = trimesh.boolean.union(pieces)
    m.fix_normals()
    return m, [PHOTO_BAS], ['couleur du salon', 'blanc mat (la lumiere passe)'], nom


# =====================================================================
# 2. PLAQUE EN TROIS COULEURS
#    Le tour de force : trois couleurs avec DEUX changements seulement,
#    parce que les trois sont des TRANCHES DE HAUTEUR et rien d'autre.
#      0    -> 4,0 mm : le fond
#      4,0  -> 5,2 mm : le cadre + le pied de la silhouette et du prenom
#      5,2  -> 6,8 mm : le haut de la silhouette et du prenom, seuls
# =====================================================================

PLAQUE_FOND = 4.0
PLAQUE_CADRE = 1.2          # le cadre s'arrete la
PLAQUE_RELIEF = 2.8         # la silhouette et le texte montent plus haut


def plaque_trois_couleurs(race_cle, prenom='LOU', larg=150.0, haut=100.0):
    """Plaque de niche declinee en trois couleurs par tranches de hauteur."""
    nom, f = RACES[race_cle]

    plaque = trimesh.creation.extrude_polygon(arrondi_rect(larg, haut, 8), PLAQUE_FOND)
    plaque.apply_translation([larg / 2, haut / 2, 0])

    centres_vis = [(10.0, haut - 10.0), (larg - 10.0, haut - 10.0)]
    trous = []
    for cx, cy in centres_vis:
        c = trimesh.creation.cylinder(radius=2.2, height=20, sections=32)
        c.apply_translation([cx, cy, 2])
        trous.append(c)

    ext = sh_translate(arrondi_rect(larg, haut, 8), larg / 2, haut / 2)
    intr = sh_translate(arrondi_rect(larg - 7, haut - 7, 6), larg / 2, haut / 2)
    cadre = ext.difference(intr)
    for cx, cy in centres_vis:
        cadre = cadre.difference(Point(cx, cy).buffer(6.0))
    rel_cadre = extrude_multi(cadre.buffer(0), PLAQUE_CADRE + 1.0)
    rel_cadre.apply_translation([0, 0, PLAQUE_FOND - 1.0])

    sil = f().buffer(0)
    zx, zy, zw, zh = 20.0, 34.0, larg - 40.0, 56.0
    x0, y0, x1, y1 = sil.bounds
    k = min(zw / (x1 - x0), zh / (y1 - y0))
    interdits = [Point(cx, cy).buffer(7.5) for cx, cy in centres_vis]
    dedans = sh_translate(arrondi_rect(larg - 9, haut - 9, 6), larg / 2, haut / 2)
    for _ in range(8):
        s = sh_scale(sil, xfact=k, yfact=k, origin=(0, 0))
        x0, y0, x1, y1 = s.bounds
        s = sh_translate(s, xoff=(larg - (x1 - x0)) / 2 - x0,
                         yoff=zy + (zh - (y1 - y0)) / 2 - y0)
        if not any(s.intersects(z) for z in interdits) and s.within(dedans):
            break
        k *= 0.93
    rel_sil = extrude_multi(s, PLAQUE_RELIEF + 1.0)
    rel_sil.apply_translation([0, 0, PLAQUE_FOND - 1.0])

    t = texte_poly(prenom, taille=26)
    tx0, ty0, tx1, ty1 = t.bounds
    kt = min((larg * 0.66) / (tx1 - tx0), 20 / (ty1 - ty0))
    t = sh_scale(t, xfact=kt, yfact=kt, origin=(tx0, ty0))
    tx0, ty0, tx1, ty1 = t.bounds
    t = sh_translate(t, xoff=(larg - (tx1 - tx0)) / 2 - tx0, yoff=10 - ty0)
    rel_txt = extrude_multi(t, PLAQUE_RELIEF + 1.0)
    rel_txt.apply_translation([0, 0, PLAQUE_FOND - 1.0])

    corps = trimesh.boolean.difference([plaque] + trous)
    m = trimesh.boolean.union([corps, rel_cadre, rel_sil, rel_txt])
    m.fix_normals()
    coupes = [PLAQUE_FOND, PLAQUE_FOND + PLAQUE_CADRE]
    return m, coupes, ['fond', 'cadre', 'silhouette et prenom'], nom


# =====================================================================
# 3. LA GAMME « COULEURS DU SALON »
#    Le nuancier d'Angelique n'est PAS connu (note du 15/08 : « lui
#    demander »). On ne devine donc pas : on livre la MECANIQUE, cinq
#    propositions a lui montrer, et un fichier a remplir d'un mot.
# =====================================================================

PALETTES_SALON = {
    'lin_et_ardoise': ('Lin et ardoise',
                       ['#e7e0d3', '#4a4f55', '#b08d5a'],
                       "Neutre chaud. Va avec n'importe quel mur, ne vieillit pas."),
    'vert_sauge': ('Vert sauge',
                   ['#cfd8c4', '#5c6b52', '#f2ede2'],
                   "Le vert des salons de toilettage recents : calme, propre, vivant."),
    'terracotta': ('Terracotta',
                   ['#e3c4ac', '#a8563a', '#3a3128'],
                   "Chaleureux, tres photogenique. Le meme registre que l'identite APC."),
    'bleu_nuit': ('Bleu nuit et or',
                  ['#eef1f4', '#22304a', '#c9a227'],
                  "Le seul qui monte le prix percu : fond clair, or en touche finale."),
    'rose_poudre': ('Rose poudre',
                    ['#f4e2e2', '#8a5a63', '#f2ede2'],
                    "Pour les petits chiens et la clientele qui offre. Tres Instagram."),
}

#: rempli quand Angelique aura repondu — une seule ligne a changer.
PALETTE_RETENUE = None


def couleurs(palette=None):
    """Les trois teintes a charger dans l'AMS, dans l'ordre des tranches."""
    cle = palette or PALETTE_RETENUE
    if cle is None:
        raise ValueError(
            "Aucune palette retenue : Angelique n'a pas encore choisi. "
            "Passer une cle de PALETTES_SALON, ou renseigner PALETTE_RETENUE.")
    return PALETTES_SALON[cle][1]


def plan_de_chargement(objets, palette=None):
    """Regle n°4 de l'anti-gaspillage : on groupe par couleur, pas par objet.

    Rend l'ordre d'impression qui minimise le nombre de changements de fil
    pour une fournee entiere.
    """
    teintes = couleurs(palette)
    lignes, total = [], 0
    for rang, teinte in enumerate(teintes):
        lot = [(nom, coupes) for nom, coupes in objets if len(coupes) >= rang]
        if not lot:
            continue
        lignes.append({'rang': rang + 1, 'teinte': teinte,
                       'objets': [n for n, _ in lot]})
        total += 1
    return {'changements': max(0, total - 1), 'passes': lignes}


CATALOGUE_COULEUR = [
    # nom                              coupes (hauteurs de changement de fil)
    ('Photophore silhouette de race',  [PHOTO_BAS]),
    ('Plaque de niche 3 couleurs',     [PLAQUE_FOND, PLAQUE_FOND + PLAQUE_CADRE]),
    ('Vase / photophore Silk degrade', []),
    ('Boule de Noel bicolore',         [36.0]),
    ('Urne compagnon (medaillon a part)', []),
    ('Cadre empreinte',                []),
    ('Vide-poche d entree',            [5.0]),
    ('Dessous-de-verre lot de 4',      [3.3]),
    ('Etiquette de jardin lot de 6',   []),
    ('Veilleuse silhouette',           [9.0]),
]


if __name__ == '__main__':
    import json
    import os
    from rendu import ecrire_3mf, image
    from bandes_hauteur import bandes

    os.makedirs('sortie_couleur', exist_ok=True)
    rapport = []

    for cle in RACES:
        m, coupes, roles, nom = photophore_race(cle, prenom=None)
        m2, infos = controle(m, f'Photophore silhouette — {nom}', mode='normal')
        infos.update(race=cle, objet='photophore', coupes=coupes, couleurs=roles,
                     changements=len(coupes), etanche=bool(m.is_watertight))
        m.export(f'sortie_couleur/photophore_{cle}.stl')
        ecrire_3mf(m, f'sortie_couleur/photophore_{cle}.3mf', f'Photophore {nom}')
        image(m2, f'sortie_couleur/photophore_{cle}.png')
        rapport.append(infos)
        print('photophore', cle, infos['dim_mm'], infos['verdict'],
              infos['poids_g'], 'g', 'etanche' if m.is_watertight else 'FUITE')

    for cle in RACES:
        m, coupes, roles, nom = plaque_trois_couleurs(cle)
        m2, infos = controle(m, f'Plaque 3 couleurs — {nom}', appuis=(PLAQUE_FOND,))
        infos.update(race=cle, objet='plaque3c', coupes=coupes, couleurs=roles,
                     changements=len(coupes), etanche=bool(m.is_watertight))
        parts = bandes(m, coupes, roles)
        for (piece, role), suffixe in zip(parts, ('fond', 'cadre', 'relief')):
            piece.export(f'sortie_couleur/plaque3c_{cle}_{suffixe}.stl')
        m.export(f'sortie_couleur/plaque3c_{cle}.stl')
        image(m2, f'sortie_couleur/plaque3c_{cle}.png')
        rapport.append(infos)
        print('plaque3c', cle, infos['dim_mm'], infos['verdict'],
              infos['poids_g'], 'g', 'etanche' if m.is_watertight else 'FUITE')

    json.dump(rapport, open('sortie_couleur/rapport.json', 'w'),
              ensure_ascii=False, indent=1)
