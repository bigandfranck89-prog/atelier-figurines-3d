#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Silhouettes de chiens PROFESSIONNELLES (v3) — tache 1104 refaite.

Source : planche « Dog breeds silhouettes » de FreeSVG (domaine public / CC0,
https://freesvg.org/dog-breeds-silhouettes, fichier 190785, auteur OpenClipart)
et « Sitting Dog Silhouette » (CC0, https://freesvg.org/sitting-dog-silhouette,
fichier 177950). Contours extraits des SVG puis convertis en polygones.

Remplace les silhouettes dessinees a la main de races.py (jugees moches par
Franck le 13/08/2026 — il avait raison).
"""
import json
import os
from shapely.geometry import Polygon
from shapely.geometry.polygon import orient
from shapely.ops import unary_union

DOSSIER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'svg_races')


def charge(nom):
    """Lit les sous-contours JSON (repere SVG, y vers le bas), rend un
    polygone shapely y vers le haut, trous geres par inclusion."""
    brut = json.load(open(os.path.join(DOSSIER, nom + '.json')))
    polys = []
    for sp in brut:
        if len(sp) < 3:
            continue
        p = Polygon([(x, -y) for x, y in sp]).buffer(0)
        if not p.is_empty and p.area > 1.0:
            polys.append(p)
    polys.sort(key=lambda p: -p.area)
    pleins, creux = [], []
    for p in polys:
        (creux if any(g.contains(p) for g in pleins) else pleins).append(p)
    assembles = []
    for p in pleins:
        trous = [c.exterior.coords for c in creux if p.contains(c)]
        assembles.append(orient(Polygon(p.exterior.coords, trous), 1.0))
    return unary_union(assembles).buffer(0)


RACES = {
    'golden':    ('Golden retriever',            lambda: charge('retriever')),
    'berger':    ('Berger allemand',             lambda: charge('berger')),
    'husky':     ('Husky sibérien',              lambda: charge('husky')),
    'caniche':   ('Caniche',                     lambda: charge('caniche')),
    'teckel':    ('Teckel',                      lambda: charge('teckel')),
    'beagle':    ('Beagle',                      lambda: charge('beagle')),
    'chihuahua': ('Chihuahua',                   lambda: charge('chihuahua')),
    'neutre':    ('Toutes races (chien assis)',  lambda: charge('assis')),
}
