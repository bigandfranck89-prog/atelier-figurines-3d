#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PREMIER ESSAI D'IMPRESSION — porte-cartes au nom du salon d'Angélique.
Base : porte-cartes allégé (vert au contrôle) + « DÉTENTE CANINE » et chien
assis en relief sur la PAROI AVANT INCLINÉE (matière pleine derrière)."""
import numpy as np
import trimesh
from shapely.affinity import scale as sh_scale, translate as sh_translate
from objets import controle
from objets2 import porte_cartes_creux
from plaques_race2 import texte_poly, extrude_multi
from races2 import RACES

# paroi avant : du bord (x=52, z=-10) au sommet (x=42, z=-40)
V = np.array([-10.0, 0.0, -30.0]); V /= np.linalg.norm(V)      # vers le haut du mur
N = np.array([30.0, 0.0, -10.0]); N /= np.linalg.norm(N)       # normale sortante
U = np.array([0.0, -1.0, 0.0])                                  # le long de l'objet
BAS = np.array([52.0, 0.0, -10.0])                              # bord bas du mur


def pose_sur_paroi(geom, larg_cible, s_bas, epais=1.6, mord=1.0, y_centre=48.0):
    """Extrude un dessin 2D et le plaque sur la paroi inclinée."""
    x0, y0, x1, y1 = geom.bounds
    k = larg_cible / (x1 - x0)
    g = sh_scale(geom, xfact=k, yfact=k, origin=(x0, y0))
    x0, y0, x1, y1 = g.bounds
    g = sh_translate(g, xoff=-x0, yoff=-y0)
    long_txt = x1 - x0
    rel = extrude_multi(g, epais)
    T = np.eye(4)
    T[:3, 0] = U; T[:3, 1] = V; T[:3, 2] = N
    ancre_y = (96.0 + long_txt) / 2.0          # centre le dessin le long de l'objet
    T[:3, 3] = BAS + V * s_bas + np.array([0.0, ancre_y, 0.0]) - N * mord
    rel.apply_transform(T)
    return rel, y1 - y0


def porte_cartes_salon(en_pieces=False):
    m = porte_cartes_creux()
    m.apply_transform(trimesh.transformations.rotation_matrix(np.pi, [0, 0, 1]))

    t = texte_poly('DÉTENTE CANINE', taille=20)
    rel_t, h_t = pose_sur_paroi(t, 78.0, 6.0)

    sil = RACES['neutre'][1]().buffer(0)
    sx0, sy0, sx1, sy1 = sil.bounds
    sil = sh_scale(sil, xfact=13.0 / (sy1 - sy0), yfact=13.0 / (sy1 - sy0), origin=(sx0, sy0))
    sil = sil.buffer(0.35).buffer(-0.15)      # epaissit les pattes fines
    rel_s, _ = pose_sur_paroi(sil, sil.bounds[2] - sil.bounds[0], 6.0 + h_t + 3.0)

    R = trimesh.transformations.rotation_matrix(np.pi, [0, 1, 0])
    if en_pieces:
        corps = m.copy(); corps.apply_transform(R); corps.fix_normals()
        rel = trimesh.util.concatenate([rel_t, rel_s])
        rel.apply_transform(R); rel.fix_normals()
        return corps, rel
    tout = trimesh.util.concatenate([m, rel_t, rel_s])
    # remet debout pour l'impression (le haut en +z)
    tout.apply_transform(R)
    tout.fix_normals()
    return tout
