#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rendu d'un objet compose de PLUSIEURS matieres."""
import numpy as np, trimesh
from matieres import couleurs_matiere, _grain_image
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from PIL import Image, ImageFilter

def rendu_objet(parts, chemin, azim=-55, elev=40, zoom=1.0):
    tris, cols, prof, mask_ph = [], [], [], []
    e,a = np.radians(elev), np.radians(azim)
    oeil = np.array([np.cos(e)*np.cos(a), np.cos(e)*np.sin(a), np.sin(e)])
    L1 = np.array([0.38,-0.5,0.78]); L1/=np.linalg.norm(L1)
    L2 = np.array([-0.6,0.55,0.3]);  L2/=np.linalg.norm(L2)
    tout = trimesh.util.concatenate([p for p,_ in parts])
    for m, mat in parts:
        mm = m
        if len(mm.faces) < 6000:
            v,f = trimesh.remesh.subdivide_to_size(mm.vertices, mm.faces, max_edge=2.6)
            mm = trimesh.Trimesh(vertices=v, faces=f, process=False)
        base = couleurs_matiere(mm.triangles_center, mat)
        nrm = mm.face_normals
        if mat == 'phospho':
            lum = np.clip(0.82+0.18*np.clip(nrm@L1,0,1)+0.10*np.clip(nrm@L2,0,1), 0.72, 1.15)
        else:
            lum = np.clip(0.34+0.52*np.clip(nrm@L1,0,1)+0.22*np.clip(nrm@L2,0,1), 0.16, 1.05)
        tris.append(mm.vertices[mm.faces]); cols.append(np.clip(base*lum[:,None],0,1))
        prof.append(mm.triangles_center@oeil)
    tris=np.concatenate(tris); cols=np.concatenate(cols); prof=np.concatenate(prof)
    o=np.argsort(prof)
    fig=plt.figure(figsize=(6.0,6.0), dpi=150); ax=fig.add_subplot(111, projection='3d')
    c=Poly3DCollection(tris[o], alpha=1.0)
    c.set_facecolor(cols[o]); c.set_edgecolor(cols[o]); c.set_linewidth(0.3)
    ax.add_collection3d(c)
    ctr=tout.bounds.mean(axis=0); d=tout.extents.max()/2*1.06/zoom
    ax.set_xlim(ctr[0]-d,ctr[0]+d); ax.set_ylim(ctr[1]-d,ctr[1]+d); ax.set_zlim(ctr[2]-d,ctr[2]+d)
    ax.set_box_aspect((1,1,1)); ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off(); ax.patch.set_alpha(0); fig.patch.set_alpha(0)
    fig.tight_layout(pad=0); fig.savefig(chemin, transparent=True, bbox_inches='tight')
    plt.close(fig)
    if any(mt=='paillettes' for _,mt in parts): _grain_image(chemin,'paillettes')
    return chemin
