#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CORRECTIONS DU 15/08/2026 apres relecture de Franck, objet par objet."""
import numpy as np, trimesh
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union
from shapely.affinity import scale as sh_scale, translate as sh_translate
from objets import arrondi_rect
from plaques_race2 import texte_poly, extrude_multi
from races2 import RACES
from objets_canins import patte_2d

BOIS,MARBRE,PAIL,PHOS='bois','marbre','paillettes','phospho'
CREME,NOIR,TERRA='#e8dbb7','#24242a','#b15533'

def _cale(poly, larg, cible_l, cy, haut_max):
    x0,y0,x1,y1 = poly.bounds
    k = min(cible_l/(x1-x0), haut_max/(y1-y0))
    p = sh_scale(poly, xfact=k, yfact=k, origin=(x0,y0))
    x0,y0,x1,y1 = p.bounds
    return sh_translate(p, xoff=larg/2-(x1-x0)/2-x0, yoff=cy-(y1-y0)/2-y0)


def enseigne_v2(nom='DÉTENTE CANINE', tel='06 12 34 56 78',
                mail='contact@detente-canine.fr', larg=240.0, haut=150.0):
    """FRANCK : « il faudrait le numero de telephone et l'adresse mail ».
    fond BOIS · cadre MARBRE · nom + coordonnees PHOSPHO · silhouette PAILLETTES."""
    corps = trimesh.creation.extrude_polygon(arrondi_rect(larg, haut, 14), 5.0)
    corps.apply_translation([larg/2, haut/2, 0])
    trous=[]
    for cx in (15.0, larg-15.0):
        c = trimesh.creation.cylinder(radius=2.6, height=24, sections=28)
        c.apply_translation([cx, haut-13.0, 2.5]); trous.append(c)
    corps = trimesh.boolean.difference([corps]+trous)
    ext  = sh_translate(arrondi_rect(larg-12, haut-12, 10), larg/2, haut/2)
    intr = sh_translate(arrondi_rect(larg-28, haut-28, 7),  larg/2, haut/2)
    cadre = ext.difference(intr)
    for cx in (15.0, larg-15.0):
        cadre = cadre.difference(Point(cx, haut-13.0).buffer(7.5))
    cadre = extrude_multi(cadre.buffer(0), 2.6); cadre.apply_translation([0,0,4.0])
    sil = RACES['golden'][1]().buffer(0)
    sil = _cale(sil, larg, larg*0.26, haut*0.70, haut*0.30)
    sil = sh_translate(sil, xoff=-larg*0.31, yoff=0)
    sil = extrude_multi(sil, 2.4); sil.apply_translation([0,0,4.0])
    tx=[]
    for txt, cy, cl, hm in ((nom, haut*0.70, 0.44, 24),
                            (tel, haut*0.40, 0.46, 15),
                            (mail, haut*0.22, 0.60, 11)):
        t = _cale(texte_poly(txt, taille=24), larg, larg*cl, cy, hm)
        if txt == nom: t = sh_translate(t, xoff=larg*0.13, yoff=0)
        tx.append(extrude_multi(t, 2.6))
    t = trimesh.util.concatenate(tx); t.apply_translation([0,0,4.0])
    return [(corps,BOIS),(cadre,MARBRE),(sil,PAIL),(t,PHOS)]


def plaque_porte_v2(prenom='STELLA', larg=150.0, haut=77.0):
    """FRANCK : « on dirait qu'il n'y a que du phosphore ».
    C'etait vrai : ma coupe en bandes donnait TOUTE la face du dessus au phospho.
    Corrige : l'os reste en BOIS, seul le prenom luit, et un lisere MARBRE le souligne."""
    r = haut*0.30
    c1 = Polygon([(r*np.cos(a), r*np.sin(a)) for a in np.linspace(0,2*np.pi,48)])
    os_ = unary_union([
        sh_translate(c1,14,haut*0.32), sh_translate(c1,14,haut*0.68),
        sh_translate(c1,larg-14,haut*0.32), sh_translate(c1,larg-14,haut*0.68),
        Polygon([(14,haut*0.20),(larg-14,haut*0.20),(larg-14,haut*0.80),(14,haut*0.80)]),
    ]).buffer(2).buffer(-2)
    base = trimesh.creation.extrude_polygon(os_, 4.0)
    liseré = os_.difference(os_.buffer(-4.0))
    lis = extrude_multi(liseré.buffer(0), 1.6); lis.apply_translation([0,0,3.2])
    t = _cale(texte_poly(prenom, taille=26), larg, larg*0.50, haut/2, 26)
    rel = extrude_multi(t, 3.0); rel.apply_translation([0,0,3.2])
    return [(base,BOIS),(lis,MARBRE),(rel,PHOS)]


def cadre_empreinte_v2(prenom='LOU', larg=124.0, haut=148.0):
    """FRANCK : « on ne dirait pas que c'est du bois marbre ».
    Meme cause. Corrige en QUATRE matieres bien separees, comme la plaque de niche."""
    plaque = trimesh.creation.extrude_polygon(arrondi_rect(larg, haut, 10), 5.0)
    plaque.apply_translation([larg/2, haut/2, 0])
    accr = trimesh.creation.cylinder(radius=3.4, height=20, sections=28)
    accr.apply_translation([larg/2, haut-11.0, 2.5])
    corps = trimesh.boolean.difference([plaque, accr])
    ext  = sh_translate(arrondi_rect(larg-14, haut-14, 8), larg/2, haut/2)
    intr = sh_translate(arrondi_rect(larg-26, haut-26, 6), larg/2, haut/2)
    cadre = ext.difference(intr).difference(Point(larg/2, haut-11.0).buffer(8.0))
    cadre = extrude_multi(cadre.buffer(0), 2.4); cadre.apply_translation([0,0,4.0])
    pat = patte_2d(larg=66.0, cx=larg/2, cy=haut*0.56)
    pat = extrude_multi(pat, 3.2); pat.apply_translation([0,0,4.0])
    t = _cale(texte_poly(prenom, taille=26), larg, larg*0.56, haut*0.155, 19)
    t = extrude_multi(t, 2.8); t.apply_translation([0,0,4.0])
    return [(corps,BOIS),(cadre,MARBRE),(pat,PAIL),(t,PHOS)]


def medaillon_v2(prenom='REX', diam=38.0):
    """FRANCK : « on ne voit rien du tout, on dirait juste un medaillon rond ».
    Corrige : disque PHOSPHO + os et prenom en PAILLETTES, qui accrochent la lumiere."""
    r = diam/2
    oeil=(r, diam-3.4)
    forme = unary_union([Point(r,r).buffer(r, resolution=48),
                         Point(oeil).buffer(4.6)]).buffer(0).difference(Point(oeil).buffer(2.0))
    base = trimesh.creation.extrude_polygon(forme, 3.0)
    c = Point(0,0).buffer(2.1, resolution=20)
    osx = unary_union([sh_translate(c,-5.5,1.4), sh_translate(c,-5.5,-1.4),
                       sh_translate(c,5.5,1.4), sh_translate(c,5.5,-1.4),
                       Polygon([(-5.5,-2.1),(5.5,-2.1),(5.5,2.1),(-5.5,2.1)])]).buffer(0.5).buffer(-0.5)
    osx = sh_translate(osx, r, r*1.32)
    t = _cale(texte_poly(prenom, taille=20), diam, diam*0.62, r*0.52, 7.5)
    rel = extrude_multi(unary_union([osx, t]).buffer(0), 1.6); rel.apply_translation([0,0,2.2])
    return [(base,PHOS),(rel,PAIL)]


def boule_photo_v2(diam=78.0):
    """FRANCK : « en quoi c'est une boule photo ? Ou est-ce que tu mets la photo ? »
    Il avait raison : mon ancienne boule etait un simple oeuf, sans photo nulle part.
    Refaite en VRAI produit photo : un cadre ajoure qui tient une PLAQUE PHOTO
    (lithophanie) — on la met devant une lumiere et l'image apparait.
    cadre PAILLETTES · plaque photo BLANC (c'est la lumiere qui traverse qui fait l'image)."""
    r = diam/2
    ext = Point(r,r).buffer(r, resolution=64)
    fen = Point(r,r).buffer(r-9.0, resolution=64)         # fenetre de la photo
    cadre2d = ext.difference(fen)
    oeil_c = (r, diam+4.0)
    anneau = Point(oeil_c).buffer(6.2, resolution=32).difference(Point(oeil_c).buffer(3.0, resolution=24))
    pont = Polygon([(r-4, diam-3),(r+4, diam-3),(r+4, diam+5),(r-4, diam+5)])
    cadre2d = unary_union([cadre2d, anneau, pont]).buffer(0)
    if cadre2d.geom_type=='MultiPolygon': cadre2d = max(cadre2d.geoms, key=lambda p:p.area)
    cadre = trimesh.creation.extrude_polygon(cadre2d, 9.0)
    # feuillure : la plaque photo se glisse dedans
    feuil = trimesh.creation.extrude_polygon(fen.buffer(2.4), 3.0)
    feuil.apply_translation([0,0,6.0])
    cadre = trimesh.boolean.difference([cadre, feuil])
    photo = trimesh.creation.extrude_polygon(fen.buffer(2.0), 2.6)
    photo.apply_translation([0,0,6.0])
    # petit relief de demonstration sur la plaque (a la place de la vraie photo)
    sil = RACES['golden'][1]().buffer(0)
    sil = _cale(sil, diam, diam*0.52, r, diam*0.34)
    rel = extrude_multi(sil, 0.9); rel.apply_translation([0,0,8.6])
    photo = trimesh.util.concatenate([photo, rel]); photo.fix_normals()
    return [(cadre,PAIL),(photo,CREME)]


def support_telephone_v2(marque='DÉTENTE CANINE'):
    """FRANCK : « il faut bien prevoir le chien assez haut pour tenir les telephones,
    peut-etre une petite encoche en bas pour bien le faire tenir ».
    Corrige : dossier porte a 128 mm (un grand smartphone fait 160 mm, il faut le tenir
    au-dessus de sa moitie), et une BUTEE de 6 mm devant, qui empeche l'appareil de glisser."""
    L, P = 112.0, 86.0
    base = trimesh.creation.extrude_polygon(sh_translate(arrondi_rect(L,P,9), L/2, P/2), 9.0)
    # gorge inclinee ou se pose le telephone
    gorge = trimesh.creation.box(extents=[L*0.80, 15.0, 34.0])
    gorge.apply_transform(trimesh.transformations.rotation_matrix(np.radians(-16),[1,0,0]))
    gorge.apply_translation([L/2, P*0.42, 15.0])
    base = trimesh.boolean.difference([base, gorge])
    # LA BUTEE demandee : petit rebord devant, l'appareil ne peut plus glisser
    butee = trimesh.creation.extrude_polygon(
        sh_translate(arrondi_rect(L*0.80, 7.0, 2.5), L/2, P*0.20), 15.0)
    # dossier : la silhouette du chien, montee a 128 mm
    sil = RACES['neutre'][1]().buffer(0)
    x0,y0,x1,y1 = sil.bounds
    k = 128.0/(y1-y0)
    sil = sh_scale(sil, xfact=k, yfact=k, origin=(x0,y0)).buffer(1.2).buffer(-0.6)
    if sil.geom_type=='MultiPolygon': sil = max(sil.geoms, key=lambda p:p.area)
    x0,y0,x1,y1 = sil.bounds
    sil = sh_translate(sil, xoff=-x0, yoff=-y0)
    chien = trimesh.creation.extrude_polygon(sil, 15.0)
    T=np.eye(4); T[:3,:3]=np.array([[1,0,0],[0,0,1],[0,1,0]],dtype=float)
    chien.apply_transform(T)
    if chien.volume<0: chien.invert()
    chien.apply_translation([L/2-chien.extents[0]/2-chien.bounds[0][0], P*0.72, 7.0])
    t = _cale(texte_poly(marque, taille=20), L, L*0.72, 0, 9)
    t = sh_translate(t, xoff=0, yoff=4.0)
    marq = extrude_multi(t, 1.6); marq.apply_translation([0,0,8.0])
    return [(base,NOIR),(butee,TERRA),(chien,TERRA),(marq,CREME)]


def _vase_plein(h_profil, dr, z0=0.0, sur_hauteur=0.0, n_z=70, n_a=96):
    """Solide FERME en forme de vase. « dr » decale le rayon (negatif = plus petit).
    IMPORTANT : le profil est toujours calcule sur h_profil, meme quand on prolonge
    au-dessus — sinon la paroi interieure ne suit plus la paroi exterieure et les
    deux se croisent (c'est ce qui donnait un vase en lambeaux au premier essai)."""
    def ray(z, a):
        t = min(max(z, 0.0), h_profil)/h_profil
        tors = np.radians(85)*t
        return (34 + 22*np.sin(np.pi*t*0.92))*(1 + 0.13*np.sin(6*(a+tors))) + dr
    zs = list(np.linspace(z0, h_profil, n_z))
    if sur_hauteur > 0: zs.append(h_profil + sur_hauteur)
    S=[]; F=[]
    for z in zs:
        for k in range(n_a):
            a = 2*np.pi*k/n_a
            r = ray(z, a)
            S.append([r*np.cos(a), r*np.sin(a), z])
    nz = len(zs)
    for i in range(nz-1):
        for k in range(n_a):
            a0=i*n_a+k; a1=i*n_a+(k+1)%n_a
            F += [[a0,a0+n_a,a1+n_a],[a0,a1+n_a,a1]]
    cb=len(S); S.append([0,0,zs[0]])
    for k in range(n_a): F.append([cb,(k+1)%n_a,k])
    ch=len(S); S.append([0,0,zs[-1]])
    for k in range(n_a):
        F.append([ch,(nz-1)*n_a+k,(nz-1)*n_a+(k+1)%n_a])
    m=trimesh.Trimesh(vertices=np.array(S), faces=np.array(F)); m.fix_normals(); return m


def vase_creux(h=176.0, paroi=1.2, fond=2.2):
    """FRANCK : « on ne dirait pas qu'il est creux, j'espere qu'il sera creux
    et etanche surtout ». Mon premier essai etait un bloc PLEIN (l'ecran le montrait
    massif), le deuxieme n'etait pas etanche, le troisieme avait les parois qui se
    croisaient. Celui-ci : un vase plein MOINS le meme vase reduit de la paroi et
    prolonge vers le haut. Creux pour de vrai, ferme en bas, ouvert en haut, etanche."""
    ext  = _vase_plein(h, 0.0)
    intr = _vase_plein(h, -paroi, z0=fond, sur_hauteur=12.0)
    m = trimesh.boolean.difference([ext, intr])
    m.fix_normals(); return m
