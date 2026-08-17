#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rend les objets de la liste « matieres speciales » DANS leur matiere."""
import os, trimesh
from matieres import rendu_matiere
from objets_neufs import (vide_poche, dessous_de_verre, etiquette_jardin,
                          veilleuse_silhouette, boule_noel)
from plaques_race2 import plaque_niche
from complements import md01_medaillon
from rendus_catalogue import plaque_porte

OUT = 'sortie_mat'; os.makedirs(OUT, exist_ok=True)

def trio_etiquettes():
    ms = []
    for i, t in enumerate(['BASILIC', 'MENTHE', 'TOMATE']):
        m = etiquette_jardin(t); m.apply_translation([i*34, 0, 0]); ms.append(m)
    m = trimesh.util.concatenate(ms); m.fix_normals(); return m

def duo_sous_verre():
    a = dessous_de_verre(motif=0)
    b = dessous_de_verre(motif=2); b.apply_translation([26, 22, 6.2])
    m = trimesh.util.concatenate([a, b]); m.fix_normals(); return m

JOBS = [
  ('04_sous_verre_granit', duo_sous_verre,                                     'granit', (-55, 30)),
  ('07_etiquettes_bois',   trio_etiquettes,                                    'bois',   (-58, 26)),
  ('08_medaillon_phospho', lambda: md01_medaillon('VÉNUS', diam=36),           'phospho',(-55, 55)),
  ('09_veilleuse_phospho', lambda: veilleuse_silhouette(),                     'phospho',(-52, 18)),
  ('10_boule_paillettes',  lambda: boule_noel(),                               'paillettes', (-50, 20)),
]

for nom, f, mat, (az, el) in JOBS:
    m = f()
    rendu_matiere(m, f'{OUT}/{nom}.png', mat, azim=az, elev=el)
    print(nom, mat, m.extents.round(0))
