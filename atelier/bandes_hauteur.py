#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Coupe un objet en BANDES DE HAUTEUR pour lui donner plusieurs matieres.
C'est la facon la moins chere de faire du multi-matiere : un seul changement
de fil par bande, donc presque pas de purge."""
import numpy as np, trimesh

def bandes(mesh, coupes, matieres):
    """coupes : hauteurs en mm, ex [30] pour deux bandes. len(matieres)=len(coupes)+1."""
    b = mesh.bounds; zmin, zmax = b[0][2], b[1][2]
    bornes = [zmin-1] + list(coupes) + [zmax+1]
    dx = (b[1][0]-b[0][0])*2 + 20; dy = (b[1][1]-b[0][1])*2 + 20
    cx = (b[0][0]+b[1][0])/2; cy = (b[0][1]+b[1][1])/2
    out = []
    for i, mat in enumerate(matieres):
        z0, z1 = bornes[i], bornes[i+1]
        boite = trimesh.creation.box(extents=[dx, dy, z1-z0])
        boite.apply_translation([cx, cy, (z0+z1)/2])
        m = trimesh.boolean.intersection([mesh, boite])
        if m is None or m.is_empty or len(m.faces) == 0:
            continue
        m.fix_normals(); out.append((m, mat))
    return out
