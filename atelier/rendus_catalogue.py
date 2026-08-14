#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deux rendus manquants pour le catalogue : la lampe (LP-01, produit phare)
et la plaque de porte (PN-01, os + prénom)."""
import numpy as np
import trimesh
from shapely.geometry import Polygon
from shapely.ops import unary_union
from shapely.affinity import scale as sh_scale, translate as sh_translate
from objets import arrondi_rect, controle
from plaques_race2 import texte_poly, extrude_multi
from socle import Socle, profil
from rendu import image


def lampe():
    """Socle + plaque figurée (relief de vagues pour évoquer la lithophanie)."""
    reg = Socle()
    p = profil(reg)
    L = reg.largeur_plaque + 2 * reg.marge
    m = trimesh.creation.extrude_polygon(p, L)
    # profil : x=profondeur, y=hauteur, extrusion z=largeur -> (X,Y,Z)=(z,x,y)
    T = np.eye(4)
    T[:3, :3] = np.array([[0, 0, 1], [1, 0, 0], [0, 1, 0]], dtype=float)
    m.apply_transform(T)
    m.apply_translation(-m.bounds[0])
    # plaque inclinée figurée
    pl = trimesh.creation.box(extents=[reg.largeur_plaque, 3.0, 100.0])
    pl.apply_transform(trimesh.transformations.rotation_matrix(np.radians(reg.inclinaison), [1, 0, 0]))
    pl.apply_translation([L / 2, 11.0, 58.0])
    return trimesh.util.concatenate([m, pl])


def plaque_porte(prenom='LOU', en_pieces=False):
    """PN-01 : os stylisé + prénom en relief, 150 x 77 x 7."""
    larg, haut = 150.0, 77.0
    # os : deux paires de cercles + barre centrale
    r = haut * 0.30
    c1 = Polygon([( r*np.cos(a),  r*np.sin(a)) for a in np.linspace(0, 2*np.pi, 48)])
    os_ = unary_union([
        sh_translate(c1, 14, haut*0.32), sh_translate(c1, 14, haut*0.68),
        sh_translate(c1, larg-14, haut*0.32), sh_translate(c1, larg-14, haut*0.68),
        Polygon([(14, haut*0.20), (larg-14, haut*0.20), (larg-14, haut*0.80), (14, haut*0.80)]),
    ]).buffer(2).buffer(-2)
    base = trimesh.creation.extrude_polygon(os_, 4.0)
    t = texte_poly(prenom, taille=26)
    tx0, ty0, tx1, ty1 = t.bounds
    kt = min((larg * 0.52) / (tx1 - tx0), 26 / (ty1 - ty0))
    t = sh_scale(t, xfact=kt, yfact=kt, origin=(tx0, ty0))
    tx0, ty0, tx1, ty1 = t.bounds
    t = sh_translate(t, xoff=(larg - (tx1 - tx0)) / 2 - tx0, yoff=(haut - (ty1 - ty0)) / 2 - ty0)
    rel = extrude_multi(t, 3.0)
    rel.apply_translation([0, 0, 3.0])
    if en_pieces:
        return base, rel
    return trimesh.util.concatenate([base, rel])


if __name__ == '__main__':
    m = lampe()
    m2, infos = controle(m, 'Lampe portrait (socle + plaque)', appuis=(4.0, 10.0))
    image(m2, 'sortie4/LP-01.png')
    print('LP-01', infos['dim_mm'], infos['verdict'])
    m = plaque_porte()
    m2, infos = controle(m, 'Plaque de porte os + prenom', appuis=(3.0,))
    image(m2, 'sortie4/PN-01.png')
    print('PN-01', infos['dim_mm'], infos['verdict'])
