#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AMENAGEMENT — première version simple de la pièce (les murs seulement).
Reprend les outils de rendu de l'atelier (atelier/rendu_multi.py) sans les
modifier. Code propre à ce projet, séparé du dossier atelier/.

Cotes approximatives, à confirmer/affiner avec Franck (voir le fil de
discussion "aménagement bureau"). Unité : centimètres.

Repère : origine = coin haut-gauche (angle mur du Velux / mur du bureau).
x = le long du mur du Velux (vers la droite du croquis papier de Franck).
y = en s'éloignant du mur du Velux, vers le fond de la pièce.
z = hauteur.
"""
import os
import sys
import numpy as np
import trimesh
from shapely.geometry import Polygon

sys.path.insert(0, os.path.dirname(__file__))
from rendu_piece import rendu_piece as rendu_objet  # noqa: E402

OUT = os.environ.get('OUT_AMENAGEMENT', 'sortie_amenagement')
os.makedirs(OUT, exist_ok=True)

# ---- cotes de la piece (cm), d'apres le releve vocal + le croquis papier ----
MUR_VELUX = 330          # mur du haut, avec le Velux
MUR_BUREAU = 330         # mur perpendiculaire, gauche (angle bureau/Velux)
RETOUR_NOTCH = 110       # profondeur du renfoncement escalier (vers y+)
LARGEUR_NOTCH = 90       # largeur du mur qui porte la porte, dans le renfoncement

HAUT_MUR = 250           # hauteur sous plafond plat estimee (cm)
HAUT_PENTE_AU_MUR = 130  # la pente commence a cette hauteur pres du mur Velux
EP_MUR = 8               # epaisseur murs (cm), juste pour la lecture visuelle

COULEUR_MUR = '#ece4d3'
COULEUR_SOL = '#cdb98f'
COULEUR_PENTE = '#b9c3cc'
COULEUR_RADIATEUR = '#e5e7ea'
COULEUR_VELUX = '#8fb7c9'
COULEUR_PORTE = '#a97c50'


def contour_piece():
    """Rectangle MUR_VELUX x MUR_BUREAU, coin bas-droit coupe (renfoncement
    escalier), sens horaire depuis le coin haut-gauche."""
    # Renfoncement place cote x petit (gauche des donnees) : avec la camera
    # utilisee pour les vues (azim=90), cela l'affiche a DROITE a l'ecran,
    # comme sur le croquis papier de Franck (Velux en haut, porte en bas a
    # droite).
    x0, y0 = 0.0, 0.0
    x1, y1 = MUR_VELUX, MUR_BUREAU
    xn = LARGEUR_NOTCH        # fin (en x) du mur interieur du renfoncement
    yn = y1 - RETOUR_NOTCH    # debut (en y) du mur interieur du renfoncement
    return [
        (x0, y0), (x1, y0),      # mur du Velux (haut)
        (x1, y1),                # mur de droite, plein
        (xn, y1),                # mur du bas, jusqu'au renfoncement
        (xn, yn),                # retour du renfoncement (vers l'escalier)
        (x0, yn),                # mur interieur du renfoncement (la porte est ici)
    ], (x0, yn, xn, yn)  # + segment de porte (x_debut, y, x_fin, y)


def boite(x0, y0, z0, x1, y1, z1):
    m = trimesh.creation.box(extents=[x1 - x0, y1 - y0, z1 - z0])
    m.apply_translation([(x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2])
    return m


def murs_et_sol():
    pts, porte_seg = contour_piece()
    poly = Polygon(pts)
    parts = []

    # sol
    sol = trimesh.creation.extrude_polygon(poly, height=2)
    parts.append((sol, COULEUR_SOL))

    # murs : un prisme fin le long de chaque arete, sauf la largeur de la porte
    n = len(pts)
    px0, py, px1, _ = porte_seg
    for i in range(n):
        ax, ay = pts[i]
        bx, by = pts[(i + 1) % n]
        est_mur_porte = (abs(ay - by) < 1e-6 and abs(ay - py) < 1e-6
                          and {round(ax), round(bx)} == {round(px0), round(px1)})
        if est_mur_porte:
            # on laisse l'ouverture de la porte (1 m de haut de vide, linteau au-dessus)
            hp = 205  # cm, hauteur de porte standard
            seg = Polygon([(ax, ay), (bx, by), (bx, by + EP_MUR), (ax, ay + EP_MUR)])
            lint = trimesh.creation.extrude_polygon(seg, height=HAUT_MUR - hp)
            lint.apply_translation([0, 0, hp])
            parts.append((lint, COULEUR_PORTE))
            continue
        dx, dy = bx - ax, by - ay
        length = float(np.hypot(dx, dy))
        if length < 1:
            continue
        nx, ny = -dy / length, dx / length  # normale (epaisseur vers l'exterieur)
        seg = Polygon([
            (ax, ay), (bx, by),
            (bx + nx * EP_MUR, by + ny * EP_MUR),
            (ax + nx * EP_MUR, ay + ny * EP_MUR),
        ])
        mur = trimesh.creation.extrude_polygon(seg, height=HAUT_MUR)
        parts.append((mur, COULEUR_MUR))

    # pente : plan incline pres du mur du Velux (y=0), simple indicateur visuel
    # (surface fine a une seule epaisseur, pas une extrusion : juste un repere
    # visuel de la zone ou le plafond descend, pas une piece imprimable)
    largeur_pente_y = 150
    z0, z1 = HAUT_PENTE_AU_MUR, HAUT_MUR
    verts = np.array([
        [0, 0, z0], [MUR_VELUX, 0, z0],
        [MUR_VELUX, largeur_pente_y, z1], [0, largeur_pente_y, z1],
    ])
    faces = np.array([[0, 1, 2], [0, 2, 3]])
    pente = trimesh.Trimesh(vertices=verts, faces=faces, process=False)
    parts.append((pente, COULEUR_PENTE))

    # radiateur : petit repere sur le mur du Velux, centre, partie basse
    rad_larg = 90
    rad_x0 = MUR_VELUX / 2 - rad_larg / 2
    parts.append((boite(rad_x0, 0, 20, rad_x0 + rad_larg, EP_MUR + 6, 75), COULEUR_RADIATEUR))

    # Velux : repere sur la pente, au-dessus du radiateur
    vx0 = MUR_VELUX / 2 - 30
    parts.append((boite(vx0, 40, HAUT_MUR + 2, vx0 + 60, 100, HAUT_MUR + 6), COULEUR_VELUX))

    return parts


def vues():
    parts = murs_et_sol()
    rendu_objet(parts, f'{OUT}/piece_dessus.png', azim=90, elev=88, zoom=0.98)
    rendu_objet(parts, f'{OUT}/piece_face_velux.png', azim=90, elev=8, zoom=0.92)
    rendu_objet(parts, f'{OUT}/piece_angle.png', azim=-40, elev=28, zoom=1.0)


if __name__ == '__main__':
    vues()
    print('Vues generees dans', OUT)
