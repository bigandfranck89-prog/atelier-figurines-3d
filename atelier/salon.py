#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LE PLATEAU VITRINE D'ANGELIQUE — objets MULTI-MATIERES (15/08/2026).

Principe pose par Franck : la machine tient 4 bobines, il faut s'en servir.
Chaque objet melange plusieurs matieres, mais TOUJOURS PAR COUCHES DE HAUTEUR :
le corps monte d'abord, puis les reliefs. Un seul changement de fil par etage,
donc presque pas de purge — c'est la regle anti-gaspillage du 13/08.

Chaque fonction rend une LISTE de (morceau, matiere) : le rendu et le trancheur
savent alors quelle bobine utiliser pour quoi.
"""
import numpy as np, trimesh
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union
from shapely.affinity import scale as sh_scale, translate as sh_translate
from objets import arrondi_rect
from plaques_race2 import texte_poly, extrude_multi
from races2 import RACES


def _cale(poly, larg, cible_l, cy, haut_max):
    x0,y0,x1,y1 = poly.bounds
    k = min(cible_l/(x1-x0), haut_max/(y1-y0))
    p = sh_scale(poly, xfact=k, yfact=k, origin=(x0,y0))
    x0,y0,x1,y1 = p.bounds
    return sh_translate(p, xoff=larg/2-(x1-x0)/2-x0, yoff=cy-(y1-y0)/2-y0)


def enseigne_salon(nom='DÉTENTE CANINE', sous='TOILETTAGE CANIN',
                   larg=224.0, haut=132.0):
    """L'ENSEIGNE DU SALON — la piece de demonstration.
    fond BOIS · cadre MARBRE · nom PHOSPHORESCENT (lisible le soir) ·
    silhouette PAILLETTES. Quatre matieres, trois changements de fil."""
    corps = trimesh.creation.extrude_polygon(arrondi_rect(larg, haut, 14), 5.0)
    corps.apply_translation([larg/2, haut/2, 0])
    trous = []
    for cx in (15.0, larg-15.0):
        c = trimesh.creation.cylinder(radius=2.6, height=24, sections=28)
        c.apply_translation([cx, haut-13.0, 2.5]); trous.append(c)
    corps = trimesh.boolean.difference([corps] + trous)

    ext  = sh_translate(arrondi_rect(larg-12, haut-12, 10), larg/2, haut/2)
    intr = sh_translate(arrondi_rect(larg-28, haut-28, 7),  larg/2, haut/2)
    cadre = ext.difference(intr)
    for cx in (15.0, larg-15.0):
        cadre = cadre.difference(Point(cx, haut-13.0).buffer(7.5))
    cadre = extrude_multi(cadre.buffer(0), 2.6); cadre.apply_translation([0,0,4.0])

    sil = RACES['golden'][1]().buffer(0)
    sil = _cale(sil, larg, larg*0.30, haut*0.66, haut*0.34)
    sil = sh_translate(sil, xoff=-larg*0.30, yoff=0)
    sil = extrude_multi(sil, 2.4); sil.apply_translation([0,0,4.0])

    t1 = _cale(texte_poly(nom, taille=26), larg, larg*0.44, haut*0.66, 22)
    t1 = sh_translate(t1, xoff=larg*0.14, yoff=0)
    t1 = extrude_multi(t1, 2.8); t1.apply_translation([0,0,4.0])
    t2 = _cale(texte_poly(sous, taille=20), larg, larg*0.40, haut*0.28, 12)
    t2 = extrude_multi(t2, 2.2); t2.apply_translation([0,0,4.0])

    return [(corps,'bois'), (cadre,'marbre'), (sil,'paillettes'),
            (trimesh.util.concatenate([t1,t2]),'phospho')]


def porte_cartes_salon(nom='DÉTENTE CANINE', larg=104.0, prof=62.0):
    """Sur le comptoir, vu par TOUTES ses clientes.
    socle MARBRE · dossier BOIS · nom PHOSPHORESCENT."""
    socle = trimesh.creation.extrude_polygon(
        sh_translate(arrondi_rect(larg, prof, 9), larg/2, prof/2), 10.0)
    fente = trimesh.creation.box(extents=[larg*0.86, 12.0, 22.0])
    fente.apply_transform(trimesh.transformations.rotation_matrix(np.radians(-14),[1,0,0]))
    fente.apply_translation([larg/2, prof*0.42, 12.0])
    socle = trimesh.boolean.difference([socle, fente])

    dos = trimesh.creation.extrude_polygon(
        sh_translate(arrondi_rect(larg, 46, 8), larg/2, 23), 5.0)
    T = np.eye(4); T[:3,:3] = np.array([[1,0,0],[0,0,1],[0,1,0]], dtype=float)
    dos.apply_transform(T)
    dos.apply_translation([0, prof-7.0, 9.0])

    t = _cale(texte_poly(nom, taille=22), larg, larg*0.74, 23, 13)
    t = extrude_multi(t, 2.0)
    t.apply_transform(T); t.apply_translation([0, prof-8.6, 9.0])
    return [(socle,'marbre'), (dos,'bois'), (t,'phospho')]


def veilleuse_deux_matieres(race='neutre', haut=104.0, ep=11.0):
    """Le chien LUIT, le socle est en marbre. Un seul changement de fil."""
    sil = RACES[race][1]().buffer(0)
    x0,y0,x1,y1 = sil.bounds
    k = haut/(y1-y0)
    sil = sh_scale(sil, xfact=k, yfact=k, origin=(x0,y0)).buffer(1.4).buffer(-0.7)
    if sil.geom_type=='MultiPolygon': sil = max(sil.geoms, key=lambda p:p.area)
    x0,y0,x1,y1 = sil.bounds
    sil = sh_translate(sil, xoff=-x0, yoff=-y0)
    fig = trimesh.creation.extrude_polygon(sil, ep)
    T = np.eye(4); T[:3,:3] = np.array([[1,0,0],[0,0,1],[0,1,0]], dtype=float)
    fig.apply_transform(T)
    if fig.volume < 0: fig.invert()
    L = fig.extents[0]
    socle = trimesh.creation.extrude_polygon(
        sh_translate(arrondi_rect(L*0.88, 46, 11), 0, 0), 11.0)
    socle.apply_translation([L/2 - socle.bounds[0][0] - socle.extents[0]/2, ep/2, 0])
    fig.apply_translation([-fig.bounds[0][0], -fig.bounds[0][1], 9.0])
    return [(socle,'marbre'), (fig,'phospho')]


def plaque_niche_multi(race='golden', prenom='ULYSSE', larg=150.0, haut=100.0):
    """La plaque de niche en QUATRE matieres : fond bois, cadre marbre,
    silhouette paillettes, prenom phosphorescent (lisible la nuit)."""
    plaque = trimesh.creation.extrude_polygon(arrondi_rect(larg, haut, 8), 4.0)
    plaque.apply_translation([larg/2, haut/2, 0])
    vis = [(10.0, haut-10.0), (larg-10.0, haut-10.0)]
    trous = []
    for cx,cy in vis:
        c = trimesh.creation.cylinder(radius=2.2, height=20, sections=28)
        c.apply_translation([cx,cy,2]); trous.append(c)
    corps = trimesh.boolean.difference([plaque]+trous)

    ext  = sh_translate(arrondi_rect(larg, haut, 8), larg/2, haut/2)
    intr = sh_translate(arrondi_rect(larg-7, haut-7, 6), larg/2, haut/2)
    cadre = ext.difference(intr)
    for cx,cy in vis: cadre = cadre.difference(Point(cx,cy).buffer(6.0))
    cadre = extrude_multi(cadre.buffer(0), 2.2); cadre.apply_translation([0,0,3.0])

    sil = RACES[race][1]().buffer(0)
    sil = _cale(sil, larg, larg*0.62, haut*0.62, haut*0.44)
    sil = extrude_multi(sil, 3.0); sil.apply_translation([0,0,3.0])

    t = _cale(texte_poly(prenom, taille=26), larg, larg*0.62, 15, 19)
    t = extrude_multi(t, 3.0); t.apply_translation([0,0,3.0])
    return [(corps,'bois'), (cadre,'marbre'), (sil,'paillettes'), (t,'phospho')]
