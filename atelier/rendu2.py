#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rendus soignés pour les planches de présentation : maillage fin,
deux lumières + ambiance, fond transparent, puis cartes avec ombre portée."""
import numpy as np
import trimesh
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from PIL import Image, ImageDraw, ImageFilter, ImageFont

POLICE = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
POLICE_N = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'


def belle_image(parts, chemin, azim=-55, elev=26, zoom=1.0):
    """parts = [(mesh, '#couleur'), ...] — rendu PNG transparent."""
    maillages, bases = [], []
    for m, c in parts:
        mm = m.copy()
        if len(mm.faces) < 60000:
            v, f = trimesh.remesh.subdivide_to_size(mm.vertices, mm.faces, max_edge=2.6)
            mm = trimesh.Trimesh(vertices=v, faces=f, process=False)
        maillages.append(mm)
        bases.append(np.array(mcolors.to_rgb(c)))
    tout = trimesh.util.concatenate(maillages)
    centre = tout.bounds.mean(axis=0)
    e, a = np.radians(elev), np.radians(azim)
    oeil = np.array([np.cos(e) * np.cos(a), np.cos(e) * np.sin(a), np.sin(e)])
    L1 = np.array([0.38, -0.5, 0.78]); L1 /= np.linalg.norm(L1)
    L2 = np.array([-0.6, 0.55, 0.3]); L2 /= np.linalg.norm(L2)
    tris, cols, prof = [], [], []
    for mm, base in zip(maillages, bases):
        n = mm.face_normals
        lum = np.clip(0.34 + 0.52 * np.clip(n @ L1, 0, 1) + 0.22 * np.clip(n @ L2, 0, 1), 0.16, 1.05)
        cc = np.clip(base[None, :] * lum[:, None], 0, 1)
        tris.append(mm.vertices[mm.faces])
        cols.append(cc)
        prof.append(mm.triangles_center @ oeil)
    tris = np.concatenate(tris); cols = np.concatenate(cols); prof = np.concatenate(prof)
    ordre = np.argsort(prof)
    fig = plt.figure(figsize=(5.2, 5.2), dpi=150)
    ax = fig.add_subplot(111, projection='3d')
    col = Poly3DCollection(tris[ordre], alpha=1.0)
    col.set_facecolor(cols[ordre]); col.set_edgecolor('none')
    ax.add_collection3d(col)
    d = tout.extents.max() / 2 * 1.06 / zoom
    ax.set_xlim(centre[0]-d, centre[0]+d); ax.set_ylim(centre[1]-d, centre[1]+d)
    ax.set_zlim(centre[2]-d, centre[2]+d)
    ax.set_box_aspect((1, 1, 1)); ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off(); ax.patch.set_alpha(0)
    fig.patch.set_alpha(0)
    fig.tight_layout(pad=0)
    fig.savefig(chemin, transparent=True, bbox_inches='tight')
    plt.close(fig)


def rogner(im):
    b = im.getbbox()
    return im.crop(b) if b else im


def carte(png, titre, sous, taille=(430, 470), fond='#f7f3ea'):
    """Une carte produit : ombre douce + objet + étiquettes."""
    w, h = taille
    c = Image.new('RGBA', (w, h), fond)
    obj = rogner(Image.open(png).convert('RGBA'))
    zone = (w - 44, h - 132)
    k = min(zone[0] / obj.width, zone[1] / obj.height)
    obj = obj.resize((max(1, int(obj.width * k)), max(1, int(obj.height * k))), Image.LANCZOS)
    ox, oy = (w - obj.width) // 2, 26 + (zone[1] - obj.height) // 2
    # ombre portee : silhouette ecrasee, floutee
    alpha = obj.split()[3].point(lambda a: 110 if a > 30 else 0)
    om = Image.new('L', (w, h), 0)
    ombre_h = max(10, int(obj.height * 0.10))
    sil = alpha.resize((int(obj.width * 0.94), ombre_h))
    om.paste(sil, (ox + int(obj.width * 0.03), oy + obj.height - ombre_h // 2))
    om = om.filter(ImageFilter.GaussianBlur(9))
    c.paste(Image.new('RGBA', (w, h), (60, 48, 30, 255)), (0, 0), om)
    c.paste(obj, (ox, oy), obj)
    dr = ImageDraw.Draw(c)
    f1 = ImageFont.truetype(POLICE, 25)
    f2 = ImageFont.truetype(POLICE_N, 17)
    tw = dr.textlength(titre, font=f1)
    dr.text(((w - tw) / 2, h - 96), titre, font=f1, fill='#241c10')
    tw2 = dr.textlength(sous, font=f2)
    dr.text(((w - tw2) / 2, h - 60), sous, font=f2, fill='#8a7f6b')
    return c


def planche(cartes, titre, sous_titre, pastilles, chemin, colonnes=4, fond='#efe8da'):
    w, h = cartes[0].size
    lignes = (len(cartes) + colonnes - 1) // colonnes
    marge, entete = 26, 150
    W = colonnes * w + (colonnes + 1) * marge
    H = entete + lignes * (h + marge) + marge
    pl = Image.new('RGB', (W, H), fond)
    dr = ImageDraw.Draw(pl)
    fT = ImageFont.truetype(POLICE, 44)
    fS = ImageFont.truetype(POLICE_N, 22)
    dr.text((marge + 8, 30), titre, font=fT, fill='#241c10')
    dr.text((marge + 10, 92), sous_titre, font=fS, fill='#776d5a')
    x = W - marge - 8 - len(pastilles) * 56
    for coul, _ in pastilles:
        dr.ellipse([x, 44, x + 42, 86], fill=coul, outline='#00000030', width=2)
        x += 56
    for i, ca in enumerate(cartes):
        gx = marge + (i % colonnes) * (w + marge)
        gy = entete + (i // colonnes) * (h + marge)
        coin = Image.new('RGBA', ca.size, (0, 0, 0, 0))
        ImageDraw.Draw(coin).rounded_rectangle([0, 0, ca.size[0]-1, ca.size[1]-1], 18, fill=(255, 255, 255, 255))
        pl.paste(ca, (gx, gy), coin)
    return pl
