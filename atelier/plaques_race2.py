#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Plaque de niche v3 : silhouette de race PROFESSIONNELLE en relief,
cadre en relief, prénom en relief, deux trous de vis.

Remplace plaques_race.py (silhouettes v2 jugées moches — tâche 1104/1160).
"""
import trimesh
from shapely.geometry import Point
from shapely.affinity import scale as sh_scale, translate as sh_translate
from races2 import RACES
from objets import arrondi_rect, controle


def texte_poly(texte, taille=26):
    from matplotlib.textpath import TextPath
    from matplotlib.font_manager import FontProperties
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    from shapely.geometry.polygon import orient
    fp = FontProperties(family='DejaVu Sans', weight='bold')
    contours = TextPath((0, 0), texte, size=taille, prop=fp).to_polygons()
    polys = sorted([Polygon(c) for c in contours if len(c) > 2], key=lambda p: -p.area)
    pleins, creux = [], []
    for p in polys:
        (creux if any(g.contains(p) for g in pleins) else pleins).append(p)
    return unary_union([
        orient(Polygon(p.exterior.coords, [c.exterior.coords for c in creux if p.contains(c)]), 1.0)
        for p in pleins])


def extrude_multi(geom, h):
    geoms = geom.geoms if geom.geom_type == 'MultiPolygon' else [geom]
    parts = [trimesh.creation.extrude_polygon(g, h) for g in geoms if g.area > 0.5]
    m = trimesh.util.concatenate(parts)
    m.fix_normals()
    return m


def plaque_niche(race_cle, prenom='LOU', larg=150.0, haut=100.0, en_pieces=False):
    nom, f = RACES[race_cle]

    # corps de la plaque, 4 mm
    plaque = trimesh.creation.extrude_polygon(arrondi_rect(larg, haut, 8), 4.0)
    plaque.apply_translation([larg / 2, haut / 2, 0])

    # trous de vis dans les coins hauts
    centres_vis = [(10.0, haut - 10.0), (larg - 10.0, haut - 10.0)]
    trous = []
    for cx, cy in centres_vis:
        c = trimesh.creation.cylinder(radius=2.2, height=20, sections=32)
        c.apply_translation([cx, cy, 2])
        trous.append(c)

    # cadre en relief (bande de 3.5 mm) — interrompu autour des vis
    ext = sh_translate(arrondi_rect(larg, haut, 8), larg / 2, haut / 2)
    intr = sh_translate(arrondi_rect(larg - 7, haut - 7, 6), larg / 2, haut / 2)
    cadre = ext.difference(intr)
    for cx, cy in centres_vis:
        cadre = cadre.difference(Point(cx, cy).buffer(6.0))
    cadre = cadre.buffer(0)
    rel_cadre = extrude_multi(cadre, 2.2)
    rel_cadre.apply_translation([0, 0, 3.0])  # mord 1 mm, culmine a 5.2

    # silhouette : zone haute, jamais sur les vis ni le cadre
    sil = f().buffer(0)
    zx, zy, zw, zh = 20.0, 34.0, larg - 40.0, 56.0   # zone utile
    x0, y0, x1, y1 = sil.bounds
    k = min(zw / (x1 - x0), zh / (y1 - y0))
    interdits = [Point(cx, cy).buffer(7.5) for cx, cy in centres_vis]
    for _ in range(8):
        s = sh_scale(sil, xfact=k, yfact=k, origin=(0, 0))
        x0, y0, x1, y1 = s.bounds
        s = sh_translate(s, xoff=(larg - (x1 - x0)) / 2 - x0,
                         yoff=zy + (zh - (y1 - y0)) / 2 - y0)
        if not any(s.intersects(z) for z in interdits) and s.within(
                sh_translate(arrondi_rect(larg - 9, haut - 9, 6), larg / 2, haut / 2)):
            break
        k *= 0.93
    sil = s
    rel_sil = extrude_multi(sil, 3.0)
    rel_sil.apply_translation([0, 0, 3.0])   # mord 1 mm, culmine a 6

    # prénom sous la silhouette
    t = texte_poly(prenom, taille=26)
    tx0, ty0, tx1, ty1 = t.bounds
    kt = min((larg * 0.66) / (tx1 - tx0), 20 / (ty1 - ty0))
    t = sh_scale(t, xfact=kt, yfact=kt, origin=(tx0, ty0))
    tx0, ty0, tx1, ty1 = t.bounds
    t = sh_translate(t, xoff=(larg - (tx1 - tx0)) / 2 - tx0, yoff=10 - ty0)
    rel_txt = extrude_multi(t, 3.0)
    rel_txt.apply_translation([0, 0, 3.0])

    corps = trimesh.boolean.difference([plaque] + trous)
    if en_pieces:
        reliefs = trimesh.util.concatenate([rel_cadre, rel_sil, rel_txt])
        reliefs.fix_normals()
        return (corps, reliefs), nom
    m = trimesh.util.concatenate([corps, rel_cadre, rel_sil, rel_txt])
    m.fix_normals()
    return m, nom


if __name__ == '__main__':
    import os, json
    from rendu import ecrire_3mf, image
    os.makedirs('sortie4', exist_ok=True)
    rap = []
    for cle in RACES:
        m, nom = plaque_niche(cle)
        m2, infos = controle(m, f'Plaque de niche — {nom}', appuis=(3.0,))
        infos['race'] = cle
        m.export(f'sortie4/plaque_{cle}.stl')
        ecrire_3mf(m, f'sortie4/plaque_{cle}.3mf', f'Plaque de niche {nom}')
        image(m2, f'sortie4/plaque_{cle}.png')
        rap.append(infos)
        print(cle, infos['dim_mm'], infos['verdict'], infos['poids_g'], 'g', infos['cout_eur'], 'EUR')
    json.dump(rap, open('sortie4/rapport.json', 'w'), ensure_ascii=False, indent=1)
