#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LES QUATRE STYLES DE FORGEON — 15/08/2026.
Chaque style = une ambiance, une famille de matieres, une planche d'impression.
Tout objet melange au moins deux matieres (regle du 15/08)."""
import numpy as np, trimesh
from bandes_hauteur import bandes
import salon, objets, objets_neufs, objets_canins
from complements import md01_medaillon, pk01_porte_cles_photo, dc01_doseur, st01_support_telephone
from plateau_salon3 import porte_cles_patte
from plaques_race2 import plaque_niche
from rendus_catalogue import plaque_porte

BOIS,MARBRE,PAIL,PHOS = 'bois','marbre','paillettes','phospho'
OR,ARG = 'silk_or','silk_argent'
NOIR,CREME,TERRA,VERT = '#24242a','#e8dbb7','#b15533','#68724d'

# ---------- STYLE 1 : L'ATELIER (chaud, artisan)
def s1_porte_laisse():
    m = objets_canins.porte_laisse('REX','golden')
    return bandes(m, [6.0], [BOIS, MARBRE])       # plaque bois, pitons marbre
def s1_cadre():
    m = objets_canins.cadre_empreinte('LOU')
    return bandes(m, [5.0], [BOIS, MARBRE])
def s1_plaque_porte():
    m = plaque_porte('STELLA')
    return bandes(m, [4.0], [BOIS, PHOS])         # os bois, prenom qui luit

# ---------- STYLE 2 : LA NUIT (lumiere, blanc, phospho)
def s2_photophore():
    m = objets.photophore()
    return bandes(m, [26.0], [MARBRE, CREME])     # pied pierre, corps blanc translucide
def s2_boule():
    m = objets_neufs.boule_noel()
    m.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2,[1,0,0]))
    m.apply_translation(-m.bounds[0])
    return bandes(m, [22.0], [PHOS, CREME])
def s2_veilleuse():  return salon.veilleuse_deux_matieres()
def s2_medaillon():
    return [(md01_medaillon('REX', diam=36, tel='0612345678'), PHOS)]

# ---------- STYLE 3 : LE BIJOU (or, argent, pierre)
def s3_medaillon_or():
    b, r = md01_medaillon('VÉNUS', diam=36, en_pieces=True)
    return [(b, MARBRE), (r, OR)]
def s3_patte_or():
    b, r = porte_cles_patte(44, en_pieces=True)
    return [(b, NOIR), (r, OR)]
def s3_cles_photo():
    b, r = pk01_porte_cles_photo(en_pieces=True)
    return [(b, MARBRE), (r, ARG)]
def s3_vide_poche():
    m = objets_neufs.vide_poche(prenom='LOU')
    return bandes(m, [7.0], [MARBRE, OR])

# ---------- STYLE 4 : MODERNE (graphique, deco maison)
def s4_vase():
    return bandes(objets.vase(), [58, 116], [NOIR, TERRA, CREME])
def s4_support_tel():
    parts = st01_support_telephone(en_pieces=True)
    out = [(parts[0], NOIR), (parts[1], TERRA)]
    if len(parts) > 2 and parts[2] is not None: out.append((parts[2], CREME))
    return out
def s4_sous_verre():
    return bandes(objets_neufs.dessous_de_verre(motif=1), [3.3], [NOIR, TERRA])
def s4_doseur():
    return bandes(dc01_doseur(), [40.0], [VERT, CREME])
def s4_etiquettes():
    ms=[]
    for i,t in enumerate(['BASILIC','MENTHE','TOMATE']):
        m = objets_neufs.etiquette_jardin(t); m.apply_translation([i*34,0,0]); ms.append(m)
    m = trimesh.util.concatenate(ms); m.fix_normals()
    return bandes(m, [4.0], [BOIS, CREME])

def masse(parts, mode='normal'):
    """Le vase s'imprime EN SPIRALE : une seule paroi de 0,8 mm, pas de remplissage.
    Sa matiere se calcule sur la SURFACE, pas sur le volume interieur — sinon on
    trouve 750 g pour un objet qui en pese 35."""
    if mode == 'spirale':
        aire = sum(p.area for p,_ in parts)/100.0        # cm2
        return (aire/2)*0.08*1.24
    v = sum(p.volume for p,_ in parts)/1000.0
    return (v*(0.35+0.65*0.15))*1.24
