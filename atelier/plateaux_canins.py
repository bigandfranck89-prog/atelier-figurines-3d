#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Les deux plateaux canins « matieres », composes le 15/08/2026.

REGLE QUI COMMANDE LA COMPOSITION : le bois, le marbre, les paillettes et le
phosphorescent sont ABRASIFS et demandent la buse acier trempe 0,6. On ne les
melange donc pas avec du PLA ordinaire sur la meme impression : chaque plateau
est monte AUTOUR D'UNE FAMILLE DE MATIERE, pas au hasard.
"""
import numpy as np, trimesh
from matieres import couleurs_matiere
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from PIL import Image, ImageFilter

PLATEAU = 256.0
MARGE = 4.0
ECART = 4.0

def poser(m):
    m = m.copy(); m.apply_translation(-m.bounds[0]); return m

def _tourner(m):
    m = m.copy()
    m.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2, [0,0,1]))
    return poser(m)

def caler(objets):
    """Rangement en etageres, version soignee : chaque objet est essaye DANS LES DEUX
    SENS et dans toutes les etageres deja ouvertes. La derniere etagere peut grandir.
    Rend (places, recales)."""
    util = PLATEAU - 2*MARGE
    etageres = []          # [{'y':.., 'h':.., 'x':..}]
    places, refuses = [], []
    for nom, m0, mat in objets:
        m0 = poser(m0)
        variantes = [m0, _tourner(m0)]
        pose = None
        for i, et in enumerate(etageres):
            derniere = (i == len(etageres)-1)
            for v in variantes:
                dx, dy = v.extents[0], v.extents[1]
                if et['x'] + dx > MARGE + util:            # pas la place en largeur
                    continue
                if dy <= et['h']:                          # rentre sous la hauteur
                    pose = (v, et, dx, dy); break
                if derniere and et['y'] + dy <= MARGE + util:   # on fait grandir
                    pose = (v, et, dx, dy); break
            if pose: break
        if not pose:                                       # nouvelle etagere
            y = MARGE if not etageres else etageres[-1]['y'] + etageres[-1]['h'] + ECART
            # on prend l'orientation la plus ETROITE : elle laisse de la place
            # a droite pour la piece suivante. Poser large bloque l'etagere.
            for v in sorted(variantes, key=lambda q: q.extents[0]):
                dx, dy = v.extents[0], v.extents[1]
                if dx <= util and y + dy <= MARGE + util:
                    et = {'y': y, 'h': dy, 'x': MARGE}
                    etageres.append(et); pose = (v, et, dx, dy); break
        if not pose:
            refuses.append(nom); continue
        v, et, dx, dy = pose
        v = v.copy(); v.apply_translation([et['x'], et['y'], 0])
        places.append((nom, v, mat))
        et['x'] += dx + ECART; et['h'] = max(et['h'], dy)
    return places, refuses

def rendu_plateau(places, chemin, azim=-60, elev=42, montrer_plateau=True):
    tris, cols, prof = [], [], []
    e,a = np.radians(elev), np.radians(azim)
    oeil = np.array([np.cos(e)*np.cos(a), np.cos(e)*np.sin(a), np.sin(e)])
    L1 = np.array([0.38,-0.5,0.78]); L1/=np.linalg.norm(L1)
    L2 = np.array([-0.6,0.55,0.3]);  L2/=np.linalg.norm(L2)
    if montrer_plateau:
        pl = trimesh.creation.box(extents=[PLATEAU, PLATEAU, 3.0])
        pl.apply_translation([PLATEAU/2, PLATEAU/2, -1.5])
        tris.append(pl.vertices[pl.faces])
        cols.append(np.tile(np.array([0.20,0.21,0.23]), (len(pl.faces),1)))
        prof.append(pl.triangles_center @ oeil)
    for nom, m, mat in places:
        mm = m
        if len(mm.faces) < 2500:
            v,f = trimesh.remesh.subdivide_to_size(mm.vertices, mm.faces, max_edge=5.0)
            mm = trimesh.Trimesh(vertices=v, faces=f, process=False)
        base = couleurs_matiere(mm.triangles_center, mat)
        nrm = mm.face_normals
        if mat == 'phospho':
            lum = np.clip(0.80+0.20*np.clip(nrm@L1,0,1)+0.10*np.clip(nrm@L2,0,1), 0.7, 1.15)
        else:
            lum = np.clip(0.34+0.52*np.clip(nrm@L1,0,1)+0.22*np.clip(nrm@L2,0,1), 0.16, 1.05)
        tris.append(mm.vertices[mm.faces]); cols.append(np.clip(base*lum[:,None],0,1))
        prof.append(mm.triangles_center @ oeil)
    tris=np.concatenate(tris); cols=np.concatenate(cols); prof=np.concatenate(prof)
    o=np.argsort(prof)
    fig=plt.figure(figsize=(8.4,8.4), dpi=150); ax=fig.add_subplot(111, projection='3d')
    c=Poly3DCollection(tris[o], alpha=1.0)
    c.set_facecolor(cols[o]); c.set_edgecolor(cols[o]); c.set_linewidth(0.25)
    ax.add_collection3d(c)
    d=PLATEAU/2*1.02
    ax.set_xlim(PLATEAU/2-d,PLATEAU/2+d); ax.set_ylim(PLATEAU/2-d,PLATEAU/2+d)
    ax.set_zlim(-d, d)
    ax.set_box_aspect((1,1,1)); ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off(); ax.patch.set_alpha(0); fig.patch.set_alpha(0)
    fig.tight_layout(pad=0); fig.savefig(chemin, transparent=True, bbox_inches='tight')
    plt.close(fig); return chemin
