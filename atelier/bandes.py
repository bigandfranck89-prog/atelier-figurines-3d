#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Découpe un maillage en tranches horizontales étanches, pour donner une
couleur par bande dans le trancheur (l'AMS fait le reste)."""
import numpy as np
import trimesh


def tranches(m, hauteurs):
    """hauteurs = [z1, z2, ...] -> [morceau 0..z1, z1..z2, ..., dernier]."""
    reste = m.copy()
    reste.apply_translation([0, 0, -reste.bounds[0][2]])
    morceaux = []
    for z in hauteurs:
        bas = trimesh.intersections.slice_mesh_plane(
            reste, plane_normal=[0, 0, -1], plane_origin=[0, 0, z], cap=True)
        haut = trimesh.intersections.slice_mesh_plane(
            reste, plane_normal=[0, 0, 1], plane_origin=[0, 0, z], cap=True)
        morceaux.append(bas)
        reste = haut
    morceaux.append(reste)
    for mo in morceaux:
        mo.fix_normals()
    return morceaux
