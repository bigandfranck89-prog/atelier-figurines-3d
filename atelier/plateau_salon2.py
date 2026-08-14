#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PLATEAU « SALON » v2 — briques communes : porte-clés os/chien, pose,
écriture 3MF multi-objets, rendu couleurs. (Le plateau courant est la v3.)

4 bobines AMS lite : bois clair, brun chocolat, noir mat, blanc crème.
Le .3mf contient des OBJETS SÉPARÉS : 1 clic par pièce pour la couleur."""
import io
import zipfile
import numpy as np
import trimesh
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union
from shapely.affinity import scale as sh_scale, translate as sh_translate
from objets import controle, prenom
from plaques_race2 import plaque_niche, texte_poly, extrude_multi
from porte_cartes_salon import porte_cartes_salon
from rendus_catalogue import plaque_porte

PLATEAU = 250.0
BOIS, BRUN, NOIR, BLANC = '#d8c49a', '#4a3826', '#24242a', '#f2ede2'


def porte_cles_os(texte='STELLA', larg=72.0, haut=34.0, en_pieces=False):
    r = haut * 0.30
    c = Polygon([(r * np.cos(a), r * np.sin(a)) for a in np.linspace(0, 2 * np.pi, 40)])
    os_ = unary_union([
        sh_translate(c, 13, haut * 0.34), sh_translate(c, 13, haut * 0.66),
        sh_translate(c, larg - 13, haut * 0.34), sh_translate(c, larg - 13, haut * 0.66),
        Polygon([(13, haut * 0.22), (larg - 13, haut * 0.22), (larg - 13, haut * 0.78), (13, haut * 0.78)]),
    ]).buffer(1.2).buffer(-1.2)
    anneau = Point(2.0, haut / 2).buffer(5.6).difference(Point(2.0, haut / 2).buffer(2.6))
    forme = unary_union([os_, anneau]).buffer(0)
    base = trimesh.creation.extrude_polygon(forme, 3.2)
    t = texte_poly(texte, taille=20)
    tx0, ty0, tx1, ty1 = t.bounds
    kt = min((larg * 0.52) / (tx1 - tx0), 12.0 / (ty1 - ty0))
    t = sh_scale(t, xfact=kt, yfact=kt, origin=(tx0, ty0))
    tx0, ty0, tx1, ty1 = t.bounds
    # centre du corps de l'os (sans l'anneau) : entre x=4 et x=larg
    t = sh_translate(t, xoff=(4 + larg) / 2 - (tx1 - tx0) / 2 - tx0,
                     yoff=(haut - (ty1 - ty0)) / 2 - ty0)
    rel = extrude_multi(t, 1.6)
    rel.apply_translation([0, 0, 2.2])
    if en_pieces:
        base.fix_normals(); rel.fix_normals()
        return base, rel
    m = trimesh.util.concatenate([base, rel])
    m.fix_normals()
    return m


def porte_cles_chien(texte='VÉNUS', haut=40.0, en_pieces=False):
    """Chien assis sur un petit socle qui porte le nom, + anneau."""
    from races2 import RACES
    sil = RACES['neutre'][1]().buffer(0)
    x0, y0, x1, y1 = sil.bounds
    k = haut / (y1 - y0)
    sil = sh_scale(sil, xfact=k, yfact=k, origin=(x0, y0))
    sil = sil.buffer(0.9).buffer(-0.4)
    x0, y0, x1, y1 = sil.bounds
    sil = sh_translate(sil, xoff=-x0, yoff=-y0)
    lchien = sil.bounds[2] - sil.bounds[0]
    lsocle = max(lchien + 10, 46.0)
    socle = Polygon([(0, 0), (lsocle, 0), (lsocle, 11), (0, 11)]).buffer(1.0).buffer(-1.0)
    sil = sh_translate(sil, xoff=(lsocle - lchien) / 2, yoff=10.0)
    anneau_c = (lsocle / 2, haut + 10.0 + 3.0)
    anneau = Point(anneau_c).buffer(5.2).difference(Point(anneau_c).buffer(2.6))
    corps2d = unary_union([socle, sil, anneau,
                           Polygon([(lsocle/2-3, haut+6), (lsocle/2+3, haut+6),
                                    (lsocle/2+3, haut+12), (lsocle/2-3, haut+12)])]).buffer(0)
    if corps2d.geom_type == 'MultiPolygon':
        corps2d = max(corps2d.geoms, key=lambda p: p.area)
    base = trimesh.creation.extrude_polygon(corps2d, 3.2)
    t = texte_poly(texte, taille=20)
    tx0, ty0, tx1, ty1 = t.bounds
    kt = min((lsocle * 0.7) / (tx1 - tx0), 7.5 / (ty1 - ty0))
    t = sh_scale(t, xfact=kt, yfact=kt, origin=(tx0, ty0))
    tx0, ty0, tx1, ty1 = t.bounds
    t = sh_translate(t, xoff=(lsocle - (tx1 - tx0)) / 2 - tx0, yoff=2.0 - ty0)
    rel = extrude_multi(t, 1.6)
    rel.apply_translation([0, 0, 2.2])
    if en_pieces:
        base.fix_normals(); rel.fix_normals()
        return base, rel
    m = trimesh.util.concatenate([base, rel])
    m.fix_normals()
    return m


def poser_groupe(parts, x, y):
    tout = trimesh.util.concatenate([p for p, _ in parts])
    dec = -tout.bounds[0] + np.array([x, y, 0])
    out = []
    for p, c in parts:
        q = p.copy()
        q.apply_translation(dec)
        out.append((q, c))
    return out


def ecrire_3mf_multi(objs, chemin, titre):
    """Un .3mf avec un objet nommé par pièce colorable (2 par produit)."""
    corps_xml = []
    items = []
    oid = 1
    for nom, parts in objs:
        for k, (m, coul) in enumerate(parts):
            v = '\n'.join(f'      <vertex x="{x:.3f}" y="{y:.3f}" z="{z:.3f}"/>'
                          for x, y, z in m.vertices)
            f = '\n'.join(f'      <triangle v1="{a}" v2="{b}" v3="{c}"/>'
                          for a, b, c in m.faces)
            etiquette = f'{nom} — {"relief" if k else "corps"}'
            corps_xml.append(
                f'  <object id="{oid}" type="model" name="{etiquette}">\n'
                f'   <mesh>\n    <vertices>\n{v}\n    </vertices>\n'
                f'    <triangles>\n{f}\n    </triangles>\n   </mesh>\n  </object>')
            items.append(f'  <item objectid="{oid}"/>')
            oid += 1
    modele = ('<?xml version="1.0" encoding="UTF-8"?>\n'
              '<model unit="millimeter" xml:lang="fr-FR" '
              'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">\n'
              f' <metadata name="Title">{titre}</metadata>\n'
              ' <resources>\n' + '\n'.join(corps_xml) + '\n </resources>\n'
              ' <build>\n' + '\n'.join(items) + '\n </build>\n</model>')
    ct = ('<?xml version="1.0" encoding="UTF-8"?>\n'
          '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">\n'
          '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>\n'
          '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>\n'
          '</Types>')
    rels = ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
            '<Relationship Target="/3D/3dmodel.model" Id="rel-1" '
            'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>\n'
            '</Relationships>')
    with zipfile.ZipFile(chemin, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml', ct)
        z.writestr('_rels/.rels', rels)
        z.writestr('3D/3dmodel.model', modele)


def image_couleurs(objs, chemin, azim=-120, elev=28):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.colors as mcolors
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    maillages, couleurs = [], []
    for _, parts in objs:
        for m, c in parts:
            mm = m.copy()
            if len(mm.faces) < 30000:
                v, f = trimesh.remesh.subdivide_to_size(mm.vertices, mm.faces, max_edge=6.0)
                mm = trimesh.Trimesh(vertices=v, faces=f, process=False)
            maillages.append(mm)
            couleurs.append(np.array(mcolors.to_rgb(c)))
    fig = plt.figure(figsize=(6.4, 6.4), dpi=115)
    ax = fig.add_subplot(111, projection='3d')
    tout = trimesh.util.concatenate(maillages)
    e, a = np.radians(elev), np.radians(azim)
    oeil = np.array([np.cos(e) * np.cos(a), np.cos(e) * np.sin(a), np.sin(e)])
    tris, facecols, prof = [], [], []
    for mm, base in zip(maillages, couleurs):
        n = mm.face_normals
        lum = np.clip(0.42 + 0.58 * (n @ np.array([0.35, -0.55, 0.75])), 0.15, 1.0)
        for i, tri in enumerate(mm.vertices[mm.faces]):
            tris.append(tri)
            facecols.append(np.clip(base * lum[i], 0, 1))
            prof.append(tri.mean(axis=0) @ oeil)
    ordre = np.argsort(prof)
    col = Poly3DCollection([tris[i] for i in ordre], alpha=1.0)
    col.set_facecolor([facecols[i] for i in ordre])
    col.set_edgecolor('none')
    ax.add_collection3d(col)
    d = tout.extents.max() / 2 * 1.12
    c = tout.bounds.mean(axis=0)
    ax.set_xlim(c[0]-d, c[0]+d); ax.set_ylim(c[1]-d, c[1]+d); ax.set_zlim(c[2]-d, c[2]+d)
    ax.set_box_aspect((1, 1, 1))
    ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off(); ax.patch.set_alpha(0)
    fig.patch.set_facecolor('#ffffff')
    fig.tight_layout(pad=0)
    fig.savefig(chemin, facecolor='#ffffff', bbox_inches='tight')
    plt.close(fig)
