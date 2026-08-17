#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Les 4 objets NEUFS de la liste « matieres speciales » du 15/08/2026,
plus deux repris du catalogue. Meme style que le reste de l'atelier."""
import numpy as np, trimesh
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union
from shapely.affinity import scale as sh_scale, translate as sh_translate
from objets import arrondi_rect
from plaques_race2 import texte_poly, extrude_multi
from races2 import RACES


def vide_poche(larg=140.0, prof=100.0, haut=34.0, prenom='LOU'):
    """Coupelle d'entree a bords releves, avec le prenom en relief au fond."""
    ext = sh_translate(arrondi_rect(larg, prof, 22), larg/2, prof/2)
    corps = trimesh.creation.extrude_polygon(ext, haut)
    creux = sh_translate(arrondi_rect(larg-16, prof-16, 18), larg/2, prof/2)
    n, cs = 26, []
    for i in range(n+1):                       # paroi qui s'evase : rien ne surplombe
        t = i/n; z = 5.0 + t*(haut-5.0)
        k = 1.0 + 0.26*t
        pol = sh_scale(creux, xfact=k, yfact=k, origin=(larg/2, prof/2))
        cs.append((pol, z))
    tr = []
    for (p1,z1),(p2,z2) in zip(cs[:-1], cs[1:]):
        s = trimesh.creation.extrude_polygon(p2, z2-z1+0.01)
        s.apply_translation([0,0,z1]); tr.append(s)
    m = trimesh.boolean.difference([corps]+tr)
    t = texte_poly(prenom, taille=26)
    x0,y0,x1,y1 = t.bounds
    k = min((larg*0.42)/(x1-x0), 18/(y1-y0))
    t = sh_scale(t, xfact=k, yfact=k, origin=(x0,y0)); x0,y0,x1,y1 = t.bounds
    t = sh_translate(t, xoff=larg/2-(x1-x0)/2-x0, yoff=prof/2-(y1-y0)/2-y0)
    rel = extrude_multi(t, 1.6); rel.apply_translation([0,0,4.2])
    out = trimesh.util.concatenate([m, rel]); out.fix_normals(); return out


def dessous_de_verre(diam=95.0, ep=6.0, motif=0):
    """Sous-verre rond, bord releve, rainures concentriques anti-glisse."""
    d = diam/2
    base = trimesh.creation.extrude_polygon(Point(d,d).buffer(d, resolution=72), ep*0.55)
    bord2d = Point(d,d).buffer(d, resolution=72).difference(Point(d,d).buffer(d-4.5, resolution=72))
    bord = trimesh.creation.extrude_polygon(bord2d, ep)
    an = []
    for i in range(3+motif):
        r = d-11-i*7.5
        if r < 8: break
        a2d = Point(d,d).buffer(r, resolution=64).difference(Point(d,d).buffer(r-2.2, resolution=64))
        a = trimesh.creation.extrude_polygon(a2d, 1.2); a.apply_translation([0,0,ep*0.55])
        an.append(a)
    m = trimesh.util.concatenate([base,bord]+an); m.fix_normals(); return m


def etiquette_jardin(texte='BASILIC', larg=26.0, haut=112.0):
    """Marqueur de plantes : pique + plaque, texte en relief."""
    corps2d = unary_union([
        sh_translate(arrondi_rect(larg, 44, 5), larg/2, haut-22),
        Polygon([(larg/2-4, 14),(larg/2+4, 14),(larg/2+4, haut-20),(larg/2-4, haut-20)]),
        Polygon([(larg/2-4, 14),(larg/2+4, 14),(larg/2, 0)]),
    ]).buffer(0)
    m = trimesh.creation.extrude_polygon(corps2d, 4.0)
    t = texte_poly(texte, taille=20)
    x0,y0,x1,y1 = t.bounds
    k = min((larg*0.80)/(x1-x0), 11/(y1-y0))
    t = sh_scale(t, xfact=k, yfact=k, origin=(x0,y0)); x0,y0,x1,y1 = t.bounds
    t = sh_translate(t, xoff=larg/2-(x1-x0)/2-x0, yoff=haut-22-(y1-y0)/2-y0)
    rel = extrude_multi(t, 1.4); rel.apply_translation([0,0,3.0])
    out = trimesh.util.concatenate([m, rel]); out.fix_normals(); return out


def veilleuse_silhouette(race='neutre', haut=105.0, ep=10.0):
    """Silhouette decoupee debout sur un socle : se charge le jour, luit la nuit."""
    sil = RACES[race][1]().buffer(0)
    x0,y0,x1,y1 = sil.bounds
    k = haut/(y1-y0)
    sil = sh_scale(sil, xfact=k, yfact=k, origin=(x0,y0))
    sil = sil.buffer(1.4).buffer(-0.7)
    if sil.geom_type == 'MultiPolygon': sil = max(sil.geoms, key=lambda p:p.area)
    x0,y0,x1,y1 = sil.bounds
    sil = sh_translate(sil, xoff=-x0, yoff=-y0)
    fig = trimesh.creation.extrude_polygon(sil, ep)
    T = np.eye(4); T[:3,:3] = np.array([[1,0,0],[0,0,1],[0,1,0]], dtype=float)
    fig.apply_transform(T)
    if fig.volume < 0: fig.invert()
    L = fig.extents[0]
    socle2d = sh_translate(arrondi_rect(L*0.86, 44, 10), 0, 0)
    socle = trimesh.creation.extrude_polygon(socle2d, 9.0)
    socle.apply_translation([L/2 - socle.bounds[0][0] - socle.extents[0]/2, ep/2, 0])
    fig.apply_translation([-fig.bounds[0][0], -fig.bounds[0][1], 7.0])
    out = trimesh.util.concatenate([socle, fig]); out.fix_normals(); return out


def boule_noel(diam=72.0):
    """Boule de Noel : sphere aplatie + fenetre plate pour la photo + anneau."""
    s = trimesh.creation.icosphere(subdivisions=4, radius=diam/2)
    s.apply_scale([1.0, 0.62, 1.0])
    coupe = trimesh.creation.box(extents=[diam, diam, diam])
    coupe.apply_translation([0, -diam*0.31 - diam/2 + 1.6, 0])
    s = trimesh.boolean.difference([s, coupe])
    an = trimesh.creation.annulus(r_min=2.6, r_max=5.4, height=3.4)
    an.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2, [1,0,0]))
    an.apply_translation([0, 0, diam/2 + 3.6])
    pont = trimesh.creation.box(extents=[7,3.4,6]); pont.apply_translation([0,0,diam/2+1.0])
    out = trimesh.util.concatenate([s, an, pont]); out.fix_normals(); return out
