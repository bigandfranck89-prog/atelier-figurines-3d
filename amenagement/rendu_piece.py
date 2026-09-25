#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AMENAGEMENT — rendu pour des objets a l'echelle d'une PIECE (metres), pas
d'une figurine (mm). Meme principe que atelier/rendu_multi.py (trimesh +
matplotlib, ombrage par facette), mais SANS la subdivision fine de maillage :
a l'echelle d'une piece, subdivide_to_size(max_edge=2.6) explose en centaines
de milliers de triangles et bloque le rendu. Les murs et le sol sont des
surfaces plates : elles n'ont pas besoin de ce grain.
Fichier propre a amenagement/, n'importe rien qui modifie atelier/.
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import matplotlib.colors as mc


def rendu_piece(parts, chemin, azim=-55, elev=40, zoom=1.0, taille=6.5):
    """parts: liste de (trimesh.Trimesh, couleur_hex)."""
    import trimesh
    tris, cols, prof = [], [], []
    e, a = np.radians(elev), np.radians(azim)
    oeil = np.array([np.cos(e) * np.cos(a), np.cos(e) * np.sin(a), np.sin(e)])
    L1 = np.array([0.38, -0.5, 0.78]); L1 /= np.linalg.norm(L1)
    L2 = np.array([-0.5, 0.55, 0.35]); L2 /= np.linalg.norm(L2)
    tout = trimesh.util.concatenate([p for p, _ in parts])
    for m, coul in parts:
        base = np.array(mc.to_rgb(coul))
        nrm = m.face_normals
        lum = np.clip(0.42 + 0.42 * np.clip(nrm @ L1, 0, 1) + 0.22 * np.clip(nrm @ L2, 0, 1), 0.25, 1.05)
        cols_m = np.clip(base[None, :] * lum[:, None], 0, 1)
        tris.append(m.vertices[m.faces])
        cols.append(cols_m)
        prof.append(m.triangles_center @ oeil)
    tris = np.concatenate(tris); cols = np.concatenate(cols); prof = np.concatenate(prof)
    o = np.argsort(prof)
    fig = plt.figure(figsize=(taille, taille), dpi=150)
    ax = fig.add_subplot(111, projection='3d')
    c = Poly3DCollection(tris[o], alpha=1.0)
    c.set_facecolor(cols[o]); c.set_edgecolor((0, 0, 0, 0.15)); c.set_linewidth(0.25)
    ax.add_collection3d(c)
    ctr = tout.bounds.mean(axis=0); d = tout.extents.max() / 2 * 1.08 / zoom
    ax.set_xlim(ctr[0] - d, ctr[0] + d); ax.set_ylim(ctr[1] - d, ctr[1] + d); ax.set_zlim(ctr[2] - d, ctr[2] + d)
    ax.set_box_aspect((1, 1, 1)); ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off(); ax.patch.set_alpha(0); fig.patch.set_alpha(0)
    fig.tight_layout(pad=0); fig.savefig(chemin, transparent=False, facecolor='#f7f4ee', bbox_inches='tight')
    plt.close(fig)
    return chemin
