#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Les objets canins muraux :
le porte-laisse, le cadre empreinte (15/08/2026) et le porte-sachets
(nuit du 19-20/08/2026). Meme style que le reste du catalogue."""
import numpy as np, trimesh
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union
from shapely.affinity import scale as sh_scale, translate as sh_translate
from objets import arrondi_rect
from plaques_race2 import texte_poly, extrude_multi
from races2 import RACES


def patte_2d(larg=40.0, cx=0.0, cy=0.0):
    """Empreinte de patte : coussinet + 4 doigts. Sert au cadre empreinte."""
    cous = sh_scale(Point(0,0).buffer(1.0, resolution=32), xfact=larg*0.30, yfact=larg*0.24)
    formes = [sh_translate(cous, cx, cy + larg*0.02)]
    for ang in (-38, -13, 13, 38):
        d = sh_scale(Point(0,0).buffer(1.0, resolution=24), xfact=larg*0.105, yfact=larg*0.135)
        a = np.radians(90 + ang); r = larg*0.40
        formes.append(sh_translate(d, cx + np.cos(a)*r, cy + larg*0.06 + np.sin(a)*r))
    return unary_union(formes)


def porte_laisse(prenom='REX', race='golden', larg=230.0, haut=92.0, n_crochets=3):
    """Barre murale : plaque + silhouette + prenom + 3 pitons a lèvre.
    Les pitons montent DROIT depuis la plaque posee a plat : rien ne surplombe."""
    plaque = trimesh.creation.extrude_polygon(arrondi_rect(larg, haut, 12), 6.0)
    plaque.apply_translation([larg/2, haut/2, 0])
    # trous de vis
    trous = []
    for cx in (13.0, larg-13.0):
        c = trimesh.creation.cylinder(radius=2.3, height=24, sections=28)
        c.apply_translation([cx, haut-13.0, 3]); trous.append(c)
    corps = trimesh.boolean.difference([plaque] + trous)

    # silhouette de race, en relief, a gauche
    sil = RACES[race][1]().buffer(0)
    x0,y0,x1,y1 = sil.bounds
    k = (haut*0.46)/(y1-y0)
    sil = sh_scale(sil, xfact=k, yfact=k, origin=(x0,y0)); x0,y0,x1,y1 = sil.bounds
    sil = sh_translate(sil, xoff=16-x0, yoff=haut*0.50-y0)
    rel_sil = extrude_multi(sil, 2.2); rel_sil.apply_translation([0,0,5.0])

    # prenom en relief, a droite de la silhouette
    t = texte_poly(prenom, taille=26)
    tx0,ty0,tx1,ty1 = t.bounds
    kt = min((larg*0.46)/(tx1-tx0), 24/(ty1-ty0))
    t = sh_scale(t, xfact=kt, yfact=kt, origin=(tx0,ty0)); tx0,ty0,tx1,ty1 = t.bounds
    t = sh_translate(t, xoff=larg*0.50-tx0, yoff=haut*0.56-ty0)
    rel_txt = extrude_multi(t, 2.2); rel_txt.apply_translation([0,0,5.0])

    # pitons : tige + levre qui retient la laisse.
    # CORRIGE DANS LA NUIT DU 19-20/08/2026. L'ancienne levre etait un cone de
    # rayon 10,5 pose sur une tige de rayon 6,5 : ca laissait une corniche de
    # 4 mm dans le vide tout autour, et l'objet sortait ORANGE a 6,2 pct de
    # porte-a-faux. La levre est maintenant un TRONC DE CONE qui s'evase vers le
    # haut sur 5 mm (38,7 deg par rapport a la verticale, donc sous les 45 deg
    # que l'imprimante sait tenir). Elle retient toujours la laisse, et plus rien
    # ne surplombe.
    pit = []
    for i in range(n_crochets):
        cx = larg*(0.20 + 0.30*i); cy = haut*0.24
        profil = np.array([[0.0, 0.0], [6.5, 0.0], [6.5, 22.0],
                           [10.5, 27.0], [10.5, 29.0], [0.0, 29.0]])
        piton = trimesh.creation.revolve(profil, sections=48)
        piton.fix_normals()
        piton.apply_translation([cx, cy, 6.0])
        pit.append(piton)
    # UN SEUL CORPS. L'ancienne version empilait 11 solides distincts avec
    # concatenate : le trancheur voyait onze objets poses au meme endroit au lieu
    # d'une piece. union() les soude vraiment.
    m = trimesh.boolean.union([corps, rel_sil, rel_txt] + pit)
    m.fix_normals(); return m


def cadre_empreinte(prenom='LOU', larg=124.0, haut=148.0):
    """Plaque souvenir : cadre en relief, empreinte de patte, prenom, trou d'accroche."""
    plaque = trimesh.creation.extrude_polygon(arrondi_rect(larg, haut, 10), 5.0)
    plaque.apply_translation([larg/2, haut/2, 0])
    accr = trimesh.creation.cylinder(radius=3.4, height=20, sections=28)
    accr.apply_translation([larg/2, haut-11.0, 2.5])
    corps = trimesh.boolean.difference([plaque, accr])

    ext = sh_translate(arrondi_rect(larg-14, haut-14, 8), larg/2, haut/2)
    intr = sh_translate(arrondi_rect(larg-26, haut-26, 6), larg/2, haut/2)
    cadre = ext.difference(intr).difference(Point(larg/2, haut-11.0).buffer(8.0))
    rel_cadre = extrude_multi(cadre.buffer(0), 2.0); rel_cadre.apply_translation([0,0,4.0])

    pat = patte_2d(larg=66.0, cx=larg/2, cy=haut*0.56)
    rel_pat = extrude_multi(pat, 3.0); rel_pat.apply_translation([0,0,4.0])

    t = texte_poly(prenom, taille=26)
    tx0,ty0,tx1,ty1 = t.bounds
    kt = min((larg*0.56)/(tx1-tx0), 19/(ty1-ty0))
    t = sh_scale(t, xfact=kt, yfact=kt, origin=(tx0,ty0)); tx0,ty0,tx1,ty1 = t.bounds
    t = sh_translate(t, xoff=larg/2-(tx1-tx0)/2-tx0, yoff=haut*0.155-ty0)
    rel_txt = extrude_multi(t, 2.4); rel_txt.apply_translation([0,0,4.0])

    # meme correction que pour le porte-laisse : union() et pas concatenate(),
    # sinon le cadre, la patte et le prenom restent quatre solides separes.
    m = trimesh.boolean.union([corps, rel_cadre, rel_pat, rel_txt])
    m.fix_normals(); return m


# =====================================================================
# PORTE-SACHETS MURAL  (ecrit dans la nuit du 19-20/08/2026)
#
# La tache 1274 demandait d'appliquer les silhouettes de race au porte-laisse
# ET au porte-sachets. Le porte-laisse les avait deja ; le porte-sachets, lui,
# N'EXISTAIT PAS DU TOUT. Il est ecrit ici.
#
# LE CHOIX QUI COMPTE, C'EST LE SENS D'IMPRESSION. Un distributeur a sachets
# est une boite : pose a plat, son ventre est un enorme surplomb. Debout, c'est
# un simple tube — zero porte-a-faux. Donc il s'imprime DEBOUT, et :
#   - on laisse tomber le rouleau par le HAUT, qui reste ouvert ;
#   - les sachets sortent par le BAS, par un entonnoir qui s'evase vers le haut
#     a 45 deg : chaque couche deborde a peine de celle d'en dessous, donc il
#     tient tout seul ;
#   - la silhouette de race est un RELIEF EXTERIEUR enroule sur le tube, la
#     meme technique que le photophore.
# =====================================================================

SAC_DIAM = 62.0        # diametre exterieur
SAC_HAUT = 105.0       # hauteur du tube
SAC_PAROI = 2.4
SAC_TROU = 26.0        # diametre de sortie des sachets
SAC_ENTONNOIR = 14.0   # hauteur de l'entonnoir (= (54-26)/2, donc pile 45 deg)


def _relief_cintre(poly, r_peau, ep, z_bas, angle0=0.0, pas=0.9):
    """Enroule un contour 2D sur la peau exterieure du tube."""
    plate = extrude_multi(poly, ep + 0.3)
    v, f = trimesh.remesh.subdivide_to_size(plate.vertices, plate.faces, max_edge=pas)
    x, y, z = v[:, 0], v[:, 1], v[:, 2]
    theta = angle0 + x / r_peau
    r = (r_peau - 0.3) + z
    w = np.column_stack([r*np.cos(theta), r*np.sin(theta), z_bas + y])
    m = trimesh.Trimesh(vertices=w, faces=f, process=True)
    m.fix_normals()
    return m


def porte_sachets(prenom='REX', race='golden', diam=SAC_DIAM, haut=SAC_HAUT):
    """Distributeur mural de sachets, silhouette de race en relief.

    Rend (mesh, nom_de_race). S'imprime debout, sans aucune bequille.
    """
    nom = RACES[race][0]
    ro = diam/2.0
    ri = ro - SAC_PAROI

    # tube + entonnoir de sortie, d'un seul tenant, par revolution
    profil = np.array([
        [SAC_TROU/2.0,          0.0],                 # bord du trou de sortie
        [ri,                    SAC_ENTONNOIR],       # l'entonnoir monte a 45 deg
        [ri,                    haut],                # paroi interieure
        [ro,                    haut],                # rebord du haut
        [ro,                    0.0],                 # paroi exterieure
        [SAC_TROU/2.0 + SAC_PAROI, 0.0],              # dessous de l'entonnoir
        [SAC_TROU/2.0,          0.0],                 # on referme le profil
    ])
    corps = trimesh.creation.revolve(profil, sections=120)
    # revolve rend la piece a l'envers (volume negatif) : on remet les faces
    # dans le bon sens, sinon le trancheur imprimerait le vide et pas la matiere.
    corps.fix_normals()

    pieces = [corps]

    # silhouette de race, en relief sur le devant
    sil = RACES[race][1]().buffer(0)
    x0, y0, x1, y1 = sil.bounds
    k = min((np.pi*ro*0.58)/(x1-x0), (haut*0.42)/(y1-y0))
    sil = sh_scale(sil, xfact=k, yfact=k, origin=(x0, y0))
    x0, y0, x1, y1 = sil.bounds
    sil = sh_translate(sil, xoff=-x0, yoff=-y0)
    arc = x1 - x0
    pieces.append(_relief_cintre(sil, ro, 2.0, z_bas=haut*0.42,
                                 angle0=-arc/(2*ro)))

    # prenom en relief, sous la silhouette
    t = texte_poly(prenom, taille=22)
    tx0, ty0, tx1, ty1 = t.bounds
    kt = min((np.pi*ro*0.42)/(tx1-tx0), 15.0/(ty1-ty0))
    t = sh_scale(t, xfact=kt, yfact=kt, origin=(tx0, ty0))
    tx0, ty0, tx1, ty1 = t.bounds
    t = sh_translate(t, xoff=-tx0, yoff=-ty0)
    arct = tx1 - tx0
    pieces.append(_relief_cintre(t, ro, 2.0, z_bas=haut*0.13,
                                 angle0=-arct/(2*ro)))

    # deux oreilles de fixation a l'arriere, dans le plan vertical :
    # imprimees debout elles ne surplombent rien.
    for zc in (haut*0.78, haut*0.28):
        oreille = trimesh.creation.box(extents=[5.0, 26.0, 18.0])
        oreille.apply_translation([-(ro + 1.0), 0.0, zc])
        vis = trimesh.creation.cylinder(radius=2.3, height=40, sections=28)
        vis.apply_transform(trimesh.transformations.rotation_matrix(
            np.pi/2, [0, 1, 0]))
        vis.apply_translation([-(ro + 1.0), 0.0, zc])
        pieces.append(trimesh.boolean.difference([oreille, vis]))

    m = trimesh.boolean.union(pieces)
    m.fix_normals()
    return m, nom
