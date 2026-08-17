#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deux objets canins qui manquaient au dessin (15/08/2026) :
le porte-laisse mural et le cadre empreinte. Meme style que le reste."""
import numpy as np, trimesh
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union
from shapely.affinity import scale as sh_scale, translate as sh_translate
from objets import arrondi_rect
from plaques_race2 import texte_poly, extrude_multi
from races2 import RACES


def patte_2d(larg=40.0, cx=0.0, cy=0.0):
    """Empreinte de patte : coussinet + 4 doigts. Sert au cadre empreinte."""
    cous = sh_scale(Point(0,0).buffer(1.0, resolution=32), xfact=larg*0.30, yfact=larg*0.24)
    formes = [sh_translate(cous, cx, cy + larg*0.02)]
    for ang in (-38, -13, 13, 38):
        d = sh_scale(Point(0,0).buffer(1.0, resolution=24), xfact=larg*0.105, yfact=larg*0.135)
        a = np.radians(90 + ang); r = larg*0.40
        formes.append(sh_translate(d, cx + np.cos(a)*r, cy + larg*0.06 + np.sin(a)*r))
    return unary_union(formes)


def porte_laisse(prenom='REX', race='golden', larg=230.0, haut=92.0, n_crochets=3):
    """Barre murale : plaque + silhouette + prenom + 3 pitons a lèvre.
    Les pitons montent DROIT depuis la plaque posee a plat : rien ne surplombe."""
    plaque = trimesh.creation.extrude_polygon(arrondi_rect(larg, haut, 12), 6.0)
    plaque.apply_translation([larg/2, haut/2, 0])
    # trous de vis
    trous = []
    for cx in (13.0, larg-13.0):
        c = trimesh.creation.cylinder(radius=2.3, height=24, sections=28)
        c.apply_translation([cx, haut-13.0, 3]); trous.append(c)
    corps = trimesh.boolean.difference([plaque] + trous)

    # silhouette de race, en relief, a gauche
    sil = RACES[race][1]().buffer(0)
    x0,y0,x1,y1 = sil.bounds
    k = (haut*0.46)/(y1-y0)
    sil = sh_scale(sil, xfact=k, yfact=k, origin=(x0,y0)); x0,y0,x1,y1 = sil.bounds
    sil = sh_translate(sil, xoff=16-x0, yoff=haut*0.50-y0)
    rel_sil = extrude_multi(sil, 2.2); rel_sil.apply_translation([0,0,5.0])

    # prenom en relief, a droite de la silhouette
    t = texte_poly(prenom, taille=26)
    tx0,ty0,tx1,ty1 = t.bounds
    kt = min((larg*0.46)/(tx1-tx0), 24/(ty1-ty0))
    t = sh_scale(t, xfact=kt, yfact=kt, origin=(tx0,ty0)); tx0,ty0,tx1,ty1 = t.bounds
    t = sh_translate(t, xoff=larg*0.50-tx0, yoff=haut*0.56-ty0)
    rel_txt = extrude_multi(t, 2.2); rel_txt.apply_translation([0,0,5.0])

    # pitons : tige + levre qui retient la laisse (imprimes debout, sans bequille)
    pit = []
    for i in range(n_crochets):
        cx = larg*(0.20 + 0.30*i); cy = haut*0.24
        tige = trimesh.creation.cylinder(radius=6.5, height=26, sections=32)
        tige.apply_translation([cx, cy, 6.0+13])
        levre = trimesh.creation.cone(radius=10.5, height=9.0, sections=32)
        levre.apply_translation([cx, cy, 6.0+26])       # cone pointe en haut : imprimable
        pit += [tige, levre]
    m = trimesh.util.concatenate([corps, rel_sil, rel_txt] + pit)
    m.fix_normals(); return m


def cadre_empreinte(prenom='LOU', larg=124.0, haut=148.0):
    """Plaque souvenir : cadre en relief, empreinte de patte, prenom, trou d'accroche."""
    plaque = trimesh.creation.extrude_polygon(arrondi_rect(larg, haut, 10), 5.0)
    plaque.apply_translation([larg/2, haut/2, 0])
    accr = trimesh.creation.cylinder(radius=3.4, height=20, sections=28)
    accr.apply_translation([larg/2, haut-11.0, 2.5])
    corps = trimesh.boolean.difference([plaque, accr])

    ext = sh_translate(arrondi_rect(larg-14, haut-14, 8), larg/2, haut/2)
    intr = sh_translate(arrondi_rect(larg-26, haut-26, 6), larg/2, haut/2)
    cadre = ext.difference(intr).difference(Point(larg/2, haut-11.0).buffer(8.0))
    rel_cadre = extrude_multi(cadre.buffer(0), 2.0); rel_cadre.apply_translation([0,0,4.0])

    pat = patte_2d(larg=66.0, cx=larg/2, cy=haut*0.56)
    rel_pat = extrude_multi(pat, 3.0); rel_pat.apply_translation([0,0,4.0])

    t = texte_poly(prenom, taille=26)
    tx0,ty0,tx1,ty1 = t.bounds
    kt = min((larg*0.56)/(tx1-tx0), 19/(ty1-ty0))
    t = sh_scale(t, xfact=kt, yfact=kt, origin=(tx0,ty0)); tx0,ty0,tx1,ty1 = t.bounds
    t = sh_translate(t, xoff=larg/2-(tx1-tx0)/2-tx0, yoff=haut*0.155-ty0)
    rel_txt = extrude_multi(t, 2.4); rel_txt.apply_translation([0,0,4.0])

    m = trimesh.util.concatenate([corps, rel_cadre, rel_pat, rel_txt])
    m.fix_normals(); return m
