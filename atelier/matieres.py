#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rendu des objets DANS LA MATIERE (marbre, bois, phosphorescent, paillettes).
Au lieu d'une couleur unique, chaque facette recoit sa propre teinte, calculee
d'apres sa position : c'est ce qui donne les veines du marbre et le fil du bois."""
import numpy as np, trimesh, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt, matplotlib.colors as mc
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from PIL import Image, ImageFilter

def _bruit(p, f, dec=0.0):
    """Petit bruit lisse, sans dependance externe."""
    return (np.sin(p[:,0]*f + dec) * np.sin(p[:,1]*f*1.31 + 1.7 + dec)
            * np.sin(p[:,2]*f*0.79 + 3.1 + dec))

def couleurs_matiere(centres, matiere, graine=0):
    n = len(centres); rng = np.random.default_rng(graine)
    p = centres
    if matiere == 'marbre':
        base = np.array(mc.to_rgb('#efece4'))
        v = _bruit(p,0.055) + 0.5*_bruit(p,0.13,1.2) + 0.25*_bruit(p,0.31,2.4)
        veine = np.clip(1.0 - np.abs(np.sin(p[:,0]*0.05 + p[:,2]*0.035 + 2.6*v))**0.32, 0, 1)
        gris = np.array(mc.to_rgb('#8d8b86'))
        c = base[None,:]*(1-veine[:,None]*0.85) + gris[None,:]*(veine[:,None]*0.85)
        c += rng.normal(0, 0.012, (n,3))
    elif matiere == 'granit':
        base = np.array(mc.to_rgb('#9c6b5e'))
        c = np.tile(base,(n,1)) + rng.normal(0,0.040,(n,3))
        gr = rng.random(n)
        c[gr>0.84] = np.array(mc.to_rgb('#e8ded2'))     # eclats clairs
        c[gr<0.12] = np.array(mc.to_rgb('#33272170'[:7]))  # eclats sombres
    elif matiere == 'bois':
        clair = np.array(mc.to_rgb('#c9a878')); fonce = np.array(mc.to_rgb('#6f4a2c'))
        g = _bruit(p,0.045)*0.5
        fil = 0.5 + 0.5*np.sin(p[:,2]*0.55 + p[:,0]*0.06 + 5.0*g)
        fil = fil**1.5
        c = fonce[None,:]*(1-fil[:,None]) + clair[None,:]*fil[:,None]
        c += rng.normal(0,0.015,(n,3))
    elif matiere == 'phospho':
        # couleur STRICTEMENT uniforme : sinon on voit le decoupage en triangles
        c = np.tile(np.array(mc.to_rgb('#bdf7c4')),(n,1))
    elif matiere == 'paillettes':
        # fond uniforme : les etincelles sont ajoutees a l'image, bien plus fines
        c = np.tile(np.array(mc.to_rgb('#8c2733')),(n,1))
    else:
        c = np.tile(np.array(mc.to_rgb(matiere)),(n,1))
    return np.clip(c,0,1)

def rendu_matiere(mesh, chemin, matiere, azim=-55, elev=25, zoom=1.0, taille=5.4):
    m = mesh.copy()
    # la couleur est calculee PAR FACETTE : les matieres a grain fin (granit,
    # paillettes) exigent des facettes petites, sinon on voit de gros triangles.
    fin = {'marbre': 2.0}.get(matiere, 2.8)
    if len(m.faces) < 40000:
        v,f = trimesh.remesh.subdivide_to_size(m.vertices, m.faces, max_edge=fin)
        m = trimesh.Trimesh(vertices=v, faces=f, process=False)
    centre = m.bounds.mean(axis=0)
    e,a = np.radians(elev), np.radians(azim)
    oeil = np.array([np.cos(e)*np.cos(a), np.cos(e)*np.sin(a), np.sin(e)])
    L1 = np.array([0.38,-0.5,0.78]); L1/=np.linalg.norm(L1)
    L2 = np.array([-0.6,0.55,0.3]);  L2/=np.linalg.norm(L2)
    base = couleurs_matiere(m.triangles_center, matiere)
    nrm = m.face_normals
    if matiere == 'phospho':          # matiere qui EMET : peu d'ombres, tout est clair
        lum = np.clip(0.80 + 0.20*np.clip(nrm@L1,0,1) + 0.10*np.clip(nrm@L2,0,1), 0.7, 1.15)
    else:
        lum = np.clip(0.34 + 0.52*np.clip(nrm@L1,0,1) + 0.22*np.clip(nrm@L2,0,1), 0.16, 1.05)
    cols = np.clip(base*lum[:,None], 0, 1)
    ordre = np.argsort(m.triangles_center@oeil)
    fig = plt.figure(figsize=(taille,taille), dpi=150)
    ax = fig.add_subplot(111, projection='3d')
    col = Poly3DCollection(m.vertices[m.faces][ordre], alpha=1.0)
    # on peint aussi le contour de chaque facette de SA propre couleur :
    # sinon des coutures blanches apparaissent entre triangles coplanaires.
    col.set_facecolor(cols[ordre]); col.set_edgecolor(cols[ordre]); col.set_linewidth(0.35)
    ax.add_collection3d(col)
    d = m.extents.max()/2*1.06/zoom
    ax.set_xlim(centre[0]-d,centre[0]+d); ax.set_ylim(centre[1]-d,centre[1]+d)
    ax.set_zlim(centre[2]-d,centre[2]+d)
    ax.set_box_aspect((1,1,1)); ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off(); ax.patch.set_alpha(0); fig.patch.set_alpha(0)
    fig.tight_layout(pad=0); fig.savefig(chemin, transparent=True, bbox_inches='tight')
    plt.close(fig)
    if matiere in ('granit','paillettes'):
        _grain_image(chemin, matiere)
    if matiere == 'phospho':          # halo vert autour de l'objet
        im = Image.open(chemin).convert('RGBA')
        al = im.split()[3]
        halo = Image.new('RGBA', im.size, (150,255,170,0))
        halo.putalpha(al.filter(ImageFilter.GaussianBlur(16)).point(lambda a:int(a*0.75)))
        Image.alpha_composite(halo, im).save(chemin)
    return chemin


def _grain_image(chemin, matiere):
    """Ajoute le grain fin APRES le rendu, dans la silhouette de l'objet.
    Beaucoup moins gourmand que de subdiviser le maillage, et bien plus fin."""
    im = Image.open(chemin).convert('RGBA')
    a = np.array(im).astype(np.float32)
    masque = a[:,:,3] > 8
    rng = np.random.default_rng(7)
    b = rng.random(a.shape[:2])
    if matiere == 'granit':
        clair = b > 0.88; sombre = b < 0.14
        for k, cible, force in ((clair, np.array([232,222,210.]), 0.55),
                                (sombre, np.array([51,39,33.]), 0.45)):
            sel = k & masque
            a[sel, :3] = a[sel, :3]*(1-force) + cible*force
    else:                                   # paillettes
        etin = (b > 0.9885) & masque
        a[etin, :3] = np.minimum(255, a[etin, :3]*0.25 + np.array([255,250,225.])*0.75)
        fin = (b > 0.93) & (b <= 0.9885) & masque
        a[fin, :3] = np.minimum(255, a[fin, :3]*1.16)
    out = Image.fromarray(a.astype(np.uint8))
    if matiere == 'paillettes':             # petit eclat autour des etincelles
        h = out.filter(ImageFilter.GaussianBlur(1.4))
        out = Image.blend(out, h, 0.28)
        out.putalpha(im.split()[3])
    out.save(chemin)
