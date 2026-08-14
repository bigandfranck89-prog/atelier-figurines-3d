#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Les 4 compléments de présentoir qui manquaient (catalogue du 09/08).

PK-01  Porte-clés photo : cadre + anneau, la plaque photo est produite par la
       fonction lithophanie du serveur (ici : motif patte de démonstration).
MD-01  Médaillon au nom pour collier : recto prénom relief, verso téléphone
       GRAVÉ en miroir (s'imprime posé à plat). PETG ou TPU, JAMAIS de PLA.
DC-01  Doseur à croquettes : gobelet + poignée-lame verticale, sans support.
ST-01  Support de téléphone : le chien assis tient le téléphone (fente 13 mm
       inclinée), base large, marqué du nom du commerce.
"""
import numpy as np
import trimesh
from shapely.geometry import Point, Polygon, LineString
from shapely.ops import unary_union
from shapely.affinity import scale as sh_scale, translate as sh_translate
from objets import controle, arrondi_rect
from plaques_race2 import texte_poly, extrude_multi
from plateau_salon3 import porte_cles_patte
from races2 import RACES


def pk01_porte_cles_photo(larg=52.0, haut=40.0, en_pieces=False):
    """Cadre 52x40, anneau, fond 1 mm + motif patte de démonstration.
    En production : le fond est remplacé par la lithophanie de la photo client."""
    ext = sh_translate(arrondi_rect(larg, haut, 5), larg / 2, haut / 2)
    intr = sh_translate(arrondi_rect(larg - 8, haut - 8, 4), larg / 2, haut / 2)
    anneau_c = (larg / 2, haut + 3.6)
    anneau = Point(anneau_c).buffer(5.2).difference(Point(anneau_c).buffer(2.6))
    pont = Polygon([(larg/2 - 3.5, haut - 2), (larg/2 + 3.5, haut - 2),
                    (larg/2 + 3.5, haut + 4), (larg/2 - 3.5, haut + 4)])
    cadre2d = unary_union([ext.difference(intr), anneau, pont]).buffer(0)
    if cadre2d.geom_type == 'MultiPolygon':
        cadre2d = max(cadre2d.geoms, key=lambda p: p.area)
    cadre = trimesh.creation.extrude_polygon(cadre2d, 4.0)
    fond = trimesh.creation.extrude_polygon(intr.buffer(0.6), 1.2)
    # motif patte de demonstration (2 mm de relief sur le fond)
    cous = sh_scale(Point(0, 0).buffer(1.0), xfact=8.5, yfact=6.8)
    cous = sh_translate(cous, larg / 2, haut * 0.40)
    doigts = []
    for ang in [-36, -12, 12, 36]:
        d = sh_scale(Point(0, 0).buffer(1.0), xfact=3.2, yfact=4.0)
        a = np.radians(90 + ang)
        doigts.append(sh_translate(d, larg / 2 + np.cos(a) * 12.5, haut * 0.44 + np.sin(a) * 12.5))
    motif = unary_union([cous] + doigts).intersection(intr)
    rel = extrude_multi(motif, 2.0)
    rel.apply_translation([0, 0, 1.0])
    base = trimesh.util.concatenate([cadre, fond])
    base.fix_normals(); rel.fix_normals()
    if en_pieces:
        return base, rel
    m = trimesh.util.concatenate([base, rel])
    m.fix_normals()
    return m


def md01_medaillon(texte='LOU', diam=32.0, en_pieces=False, tel=None):
    """Médaillon de collier : disque, petit os, prénom, trou renforcé.
    Si tel est donné : gravé en creux au VERSO (miroir, lisible en retournant),
    profondeur 0,8 mm — s'imprime posé à plat, sans rien changer."""
    r = diam / 2
    disque = Point(r, r).buffer(r)
    oeil_c = (r, diam - 3.4)
    renfort = Point(oeil_c).buffer(4.6)
    forme = unary_union([disque, renfort]).buffer(0).difference(Point(oeil_c).buffer(2.0))
    base = trimesh.creation.extrude_polygon(forme, 3.0)
    if tel:
        from shapely.affinity import scale as sh_miroir
        lignes = tel.split('/') if '/' in tel else ([tel[:len(tel)//2+1].strip(), tel[len(tel)//2+1:].strip()]
                                                    if len(tel) > 9 else [tel])
        grav2d = []
        for li, lig in enumerate(lignes):
            g = texte_poly(lig, taille=20)
            gx0, gy0, gx1, gy1 = g.bounds
            kg = min((diam * 0.72) / (gx1 - gx0), 6.0 / (gy1 - gy0))
            g = sh_scale(g, xfact=kg, yfact=kg, origin=(gx0, gy0))
            gx0, gy0, gx1, gy1 = g.bounds
            y_lig = r + 4.0 - li * 9.0 - (gy1 - gy0)
            g = sh_translate(g, xoff=r - (gx1 - gx0) / 2 - gx0, yoff=y_lig - gy0)
            grav2d.append(g)
        grav = unary_union(grav2d).buffer(0)
        grav = sh_miroir(grav, xfact=-1, yfact=1, origin=(r, r))   # miroir : lisible retourne
        poincon = extrude_multi(grav.buffer(0.05), 1.2)
        poincon.apply_translation([0, 0, -0.2])                     # grave 0,8 mm sous z=0..0.8
        base = trimesh.boolean.difference([base, poincon])
    # petit os au-dessus du prenom
    c = Point(0, 0).buffer(2.1)
    osx = unary_union([sh_translate(c, -5.5, 1.4), sh_translate(c, -5.5, -1.4),
                       sh_translate(c, 5.5, 1.4), sh_translate(c, 5.5, -1.4),
                       Polygon([(-5.5, -2.1), (5.5, -2.1), (5.5, 2.1), (-5.5, 2.1)])]).buffer(0.5).buffer(-0.5)
    osx = sh_translate(osx, r, r * 1.30)
    t = texte_poly(texte, taille=20)
    tx0, ty0, tx1, ty1 = t.bounds
    kt = min((diam * 0.58) / (tx1 - tx0), 7.0 / (ty1 - ty0))
    t = sh_scale(t, xfact=kt, yfact=kt, origin=(tx0, ty0))
    tx0, ty0, tx1, ty1 = t.bounds
    t = sh_translate(t, xoff=r - (tx1 - tx0) / 2 - tx0, yoff=r * 0.48 - ty0)
    rel = extrude_multi(unary_union([osx, t]).buffer(0), 1.4)
    rel.apply_translation([0, 0, 2.0])
    base.fix_normals(); rel.fix_normals()
    if en_pieces:
        return base, rel
    m = trimesh.util.concatenate([base, rel])
    m.fix_normals()
    return m


def dc01_doseur(en_pieces=False):
    """Gobelet conique (Ø78 haut, Ø58 bas, h 80) + poignée-lame verticale."""
    n = 48
    def anneau_pts(r, z):
        return [(r * np.cos(a), r * np.sin(a), z) for a in np.linspace(0, 2 * np.pi, n, endpoint=False)]
    ext_bas, ext_haut = anneau_pts(29.0, 0), anneau_pts(39.0, 80)
    int_bas, int_haut = anneau_pts(26.6, 3.0), anneau_pts(36.6, 80)
    verts = ext_bas + ext_haut + int_bas + int_haut + [(0, 0, 0), (0, 0, 3.0)]
    F = []
    for i in range(n):
        j = (i + 1) % n
        F += [[i, j, n + i], [j, n + j, n + i]]                       # paroi ext
        F += [[2*n + i, 3*n + i, 2*n + j], [2*n + j, 3*n + i, 3*n + j]]  # paroi int
        F += [[n + i, n + j, 3*n + i], [n + j, 3*n + j, 3*n + i]]     # levre haute
        F += [[i, 4*n, j]]                                            # fond ext
        F += [[2*n + i, 2*n + j, 4*n + 1]]                            # fond int
    coque = trimesh.Trimesh(vertices=np.array(verts, dtype=float), faces=np.array(F))
    coque.fix_normals()
    # poignee : lame verticale du bas vers le haut, collee au flanc
    lame2d = Polygon([(28, 4), (52, 22), (56, 34), (56, 66), (52, 74), (44, 78), (37.5, 78),
                      (37.5, 70), (46, 66), (48, 58), (48, 36), (44, 28), (27.5, 14)]).buffer(1.0).buffer(-1.0)
    lame = trimesh.creation.extrude_polygon(lame2d, 8.0)
    T = np.eye(4); T[:3, :3] = np.array([[1, 0, 0], [0, 0, 1], [0, 1, 0]], dtype=float)
    lame.apply_transform(T)
    lame.apply_translation([0, 4.0, 0])
    if lame.volume < 0:
        lame.invert()
    lame.fix_normals()
    m = trimesh.util.concatenate([coque, lame])
    m.fix_normals()
    if en_pieces:
        return coque, lame
    return m


def st01_support_telephone(en_pieces=False, marque='DÉTENTE CANINE'):
    """Le chien assis tient le téléphone : base 100x70, fente 13 mm inclinée,
    dossier = silhouette chien assis épaisse 14 mm, nom du commerce en relief."""
    base2d = sh_translate(arrondi_rect(100, 70, 8), 50, 35)
    base = trimesh.creation.extrude_polygon(base2d, 8.0)
    fente = trimesh.creation.box(extents=[84, 13, 40])
    fente.apply_transform(trimesh.transformations.rotation_matrix(np.radians(-18), [1, 0, 0]))
    fente.apply_translation([50, 30, 14])
    base = trimesh.boolean.difference([base, fente])
    sil = RACES['neutre'][1]().buffer(0)
    x0, y0, x1, y1 = sil.bounds
    k = 75.0 / (y1 - y0)
    sil = sh_scale(sil, xfact=k, yfact=k, origin=(x0, y0))
    sil = sil.buffer(1.2).buffer(-0.6)
    x0, y0, x1, y1 = sil.bounds
    sil = sh_translate(sil, xoff=-x0, yoff=-y0)
    chien = trimesh.creation.extrude_polygon(
        sil if sil.geom_type == 'Polygon' else max(sil.geoms, key=lambda p: p.area), 14.0)
    T = np.eye(4); T[:3, :3] = np.array([[1, 0, 0], [0, 0, 1], [0, 1, 0]], dtype=float)
    chien.apply_transform(T)
    lchien = chien.extents[0]
    chien.apply_translation([50 - lchien / 2 - chien.bounds[0][0], 40.0, 6.0])
    if chien.volume < 0:
        chien.invert()
    chien.fix_normals()
    marq = None
    if marque:
        t = texte_poly(marque, taille=20)
        tx0, ty0, tx1, ty1 = t.bounds
        kt = min(80.0 / (tx1 - tx0), 9.0 / (ty1 - ty0))
        t = sh_scale(t, xfact=kt, yfact=kt, origin=(tx0, ty0))
        tx0, ty0, tx1, ty1 = t.bounds
        t = sh_translate(t, xoff=50 - (tx1 - tx0) / 2 - tx0, yoff=8.0 - ty0)
        marq = extrude_multi(t, 1.4)
        marq.apply_translation([0, 0, 7.0])   # mord 1 mm dans la base
        marq.fix_normals()
    m = trimesh.util.concatenate([base, chien] + ([marq] if marq else []))
    m.fix_normals()
    if en_pieces:
        return (base, chien, marq) if marq else (base, chien)
    return m
