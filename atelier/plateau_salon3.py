#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PLATEAU « SALON » v3 — LE premier jet (décision Franck 13/08).

  1. Plaque de niche Golden « ULYSSE »
  2. Plaque de porte os « OLYMPE »
  3. Porte-cartes « DÉTENTE CANINE »
  4. Porte-clés os « STELLA »
  5. Porte-clés chien assis « VÉNUS »
  6. Porte-clés médaillon rond golden « YUZU »
  7. Porte-clés patte de chien

Les noms = les chiens d'Angélique (4 goldens + 1 hovawart).
Le « prénom en relief » a été retiré : joli mais sans usage clair."""
import numpy as np
import trimesh
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union
from shapely.affinity import scale as sh_scale, translate as sh_translate, rotate as sh_rotate
from objets import controle
from plaques_race2 import plaque_niche, texte_poly, extrude_multi
from porte_cartes_salon import porte_cartes_salon
from rendus_catalogue import plaque_porte
from plateau_salon2 import (porte_cles_os, porte_cles_chien, poser_groupe,
                            ecrire_3mf_multi, image_couleurs,
                            PLATEAU, BOIS, BRUN, NOIR, BLANC)
from races2 import RACES


def medaillon_golden(texte='YUZU', diam=42.0, en_pieces=False):
    """Disque + silhouette golden en relief + nom en dessous + anneau."""
    r = diam / 2
    disque = Point(r, r).buffer(r)
    anneau_c = (r, diam + 3.4)
    anneau = Point(anneau_c).buffer(5.2).difference(Point(anneau_c).buffer(2.6))
    pont = Polygon([(r - 3, diam - 2), (r + 3, diam - 2), (r + 3, diam + 4), (r - 3, diam + 4)])
    base2d = unary_union([disque, anneau, pont]).buffer(0)
    if base2d.geom_type == 'MultiPolygon':
        base2d = max(base2d.geoms, key=lambda p: p.area)
    base = trimesh.creation.extrude_polygon(base2d, 3.2)

    sil = RACES['golden'][1]().buffer(0)
    x0, y0, x1, y1 = sil.bounds
    k = (diam * 0.62) / (x1 - x0)
    sil = sh_scale(sil, xfact=k, yfact=k, origin=(x0, y0))
    sil = sil.buffer(0.5).buffer(-0.25)
    x0, y0, x1, y1 = sil.bounds
    sil = sh_translate(sil, xoff=r - (x1 - x0) / 2 - x0, yoff=r * 0.86 - y0)

    t = texte_poly(texte, taille=20)
    tx0, ty0, tx1, ty1 = t.bounds
    kt = min((diam * 0.52) / (tx1 - tx0), 8.0 / (ty1 - ty0))
    t = sh_scale(t, xfact=kt, yfact=kt, origin=(tx0, ty0))
    tx0, ty0, tx1, ty1 = t.bounds
    t = sh_translate(t, xoff=r - (tx1 - tx0) / 2 - tx0, yoff=r * 0.34 - ty0)

    rel = extrude_multi(unary_union([sil, t]).buffer(0), 1.6)
    rel.apply_translation([0, 0, 2.2])
    if en_pieces:
        base.fix_normals(); rel.fix_normals()
        return base, rel
    m = trimesh.util.concatenate([base, rel])
    m.fix_normals()
    return m


def porte_cles_patte(larg=40.0, en_pieces=False):
    """Patte de chien : gros coussinet + 4 doigts, pleine, avec anneau."""
    cous = sh_scale(Point(0, 0).buffer(1.0), xfact=larg * 0.30, yfact=larg * 0.24)
    cous = sh_translate(cous, larg / 2, larg * 0.30)
    doigts = []
    for i, ang in enumerate([-38, -13, 13, 38]):
        d = sh_scale(Point(0, 0).buffer(1.0), xfact=larg * 0.105, yfact=larg * 0.135)
        a = np.radians(90 + ang)
        ray = larg * 0.40
        d = sh_translate(d, larg / 2 + np.cos(a) * ray, larg * 0.34 + np.sin(a) * ray)
        doigts.append(d)
    patte = unary_union([cous] + doigts).buffer(1.5).buffer(-1.5)
    x0, y0, x1, y1 = patte.bounds
    haut = y1 - y0
    anneau_c = ((x0 + x1) / 2, y1 + 3.0)
    anneau = Point(anneau_c).buffer(5.2).difference(Point(anneau_c).buffer(2.6))
    pont = Polygon([(anneau_c[0] - 3, y1 - 2), (anneau_c[0] + 3, y1 - 2),
                    (anneau_c[0] + 3, y1 + 3.5), (anneau_c[0] - 3, y1 + 3.5)])
    forme = unary_union([patte, anneau, pont]).buffer(0)
    if forme.geom_type == 'MultiPolygon':
        forme = max(forme.geoms, key=lambda p: p.area)
    base = trimesh.creation.extrude_polygon(forme, 3.2)
    # les coussinets en relief par-dessus (2e couleur) : version reduite
    rel2d = unary_union([sh_scale(g, xfact=0.72, yfact=0.72, origin='center')
                         for g in [cous] + doigts])
    rel = extrude_multi(rel2d, 1.6)
    rel.apply_translation([0, 0, 2.2])
    base.fix_normals(); rel.fix_normals()
    if en_pieces:
        return base, rel
    m = trimesh.util.concatenate([base, rel])
    m.fix_normals()
    return m


def plateau():
    objs = []
    (c1, r1), _ = plaque_niche('golden', prenom='ULYSSE', en_pieces=True)
    objs.append(('Plaque niche Golden ULYSSE', poser_groupe([(c1, BOIS), (r1, BRUN)], 4, 4)))
    c2, r2 = plaque_porte('OLYMPE', en_pieces=True)
    objs.append(('Plaque porte os OLYMPE', poser_groupe([(c2, BOIS), (r2, BRUN)], 4, 112)))
    c4, r4 = porte_cartes_salon(en_pieces=True)
    objs.append(('Porte-cartes Détente Canine', poser_groupe([(c4, NOIR), (r4, BLANC)], 186, 4)))
    c5, r5 = porte_cles_os('STELLA', en_pieces=True)
    objs.append(('Porte-clés os STELLA', poser_groupe([(c5, BOIS), (r5, BRUN)], 176, 108)))
    c6, r6 = porte_cles_chien('VÉNUS', en_pieces=True)
    objs.append(('Porte-clés chien VÉNUS', poser_groupe([(c6, BRUN), (r6, BOIS)], 192, 150)))
    c7, r7 = medaillon_golden('YUZU', en_pieces=True)
    objs.append(('Médaillon golden YUZU', poser_groupe([(c7, BOIS), (r7, BRUN)], 4, 192)))
    c8, r8 = porte_cles_patte(en_pieces=True)
    objs.append(('Porte-clés patte', poser_groupe([(c8, NOIR), (r8, BLANC)], 58, 192)))
    return objs


if __name__ == '__main__':
    objs = plateau()
    for nom, parts in objs:
        b = trimesh.util.concatenate([m for m, _ in parts]).bounds
        assert b[0][0] >= 0 and b[0][1] >= 0 and b[1][0] <= PLATEAU and b[1][1] <= PLATEAU, (nom, b)
    boites = [(nom, trimesh.util.concatenate([m for m, _ in parts]).bounds) for nom, parts in objs]
    for i in range(len(boites)):
        for j in range(i + 1, len(boites)):
            a, b = boites[i][1], boites[j][1]
            chev = not (a[1][0] + 2 < b[0][0] or b[1][0] + 2 < a[0][0] or
                        a[1][1] + 2 < b[0][1] or b[1][1] + 2 < a[0][1])
            assert not chev, (boites[i][0], boites[j][0])
    tout = trimesh.util.concatenate([m for _, parts in objs for m, _ in parts])
    tout.fix_normals()
    m2, infos = controle(tout, 'Plateau salon v3', appuis=(2.2, 3.0, 4.0, 10.0))
    print(infos['dim_mm'], infos['verdict'], infos['poids_g'], 'g', infos['cout_eur'], 'EUR',
          'pf', infos['porte_a_faux_pct'], '%')
    for nom, b in boites:
        print(f'  {nom:32s} {b[1][0]-b[0][0]:5.0f} x {b[1][1]-b[0][1]:5.0f} x {b[1][2]-b[0][2]:4.0f} mm')
    ecrire_3mf_multi(objs, 'sortie4/plateau_salon_v3.3mf', 'Plateau salon Forgeon v3 - 7 objets - 4 couleurs')
    image_couleurs(objs, 'sortie4/plateau_salon_v3_dessus.png', azim=-90, elev=78)
    image_couleurs(objs, 'sortie4/plateau_salon_v3.png')
