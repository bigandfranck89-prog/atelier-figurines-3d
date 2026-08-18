#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Les vues de l'URNE COMPAGNON : assemblee, de face, en pieces sur le plateau,
et les trois tailles cote a cote."""
import os, numpy as np, trimesh
from matieres import rendu_matiere
from rendu_multi import rendu_objet
from urne import urne_compagnon, MARBRE, PAIL
from objets import controle

OUT = os.environ.get('OUT_URNE', 'sortie_urne')
os.makedirs(OUT, exist_ok=True)


def poser(m, x=0.0, y=0.0):
    m = m.copy(); m.apply_translation(-m.bounds[0]); m.apply_translation([x, y, 0]); return m


def vues():
    a = urne_compagnon('LOU', 20.0)
    rendu_objet(a, f'{OUT}/urne_3quarts.png', azim=66, elev=22, zoom=1.06)
    rendu_objet(a, f'{OUT}/urne_face.png',    azim=100, elev=12, zoom=1.06)

    p = urne_compagnon('LOU', 20.0, en_pieces=True)
    corps = poser(p['corps'], 0, 0)
    cvl = poser(p['couvercle'], corps.extents[0] + 14, 8)
    med = poser(p['medaillon'], corps.extents[0] + 14, cvl.extents[1] + 26)
    rendu_objet([(corps, MARBRE), (cvl, MARBRE), (med, PAIL)],
                f'{OUT}/urne_pieces_plateau.png', azim=-62, elev=34, zoom=1.02)

    lot, x = [], 0.0
    for kg in (6, 20, 40):
        parts = urne_compagnon('LOU', kg)
        larg = max(q.extents[0] for q, _ in parts)
        for q, mat in parts:
            q = q.copy(); q.apply_translation([x, 0, 0]); lot.append((q, mat))
        x += larg + 16
    rendu_objet(lot, f'{OUT}/urne_trois_tailles.png', azim=88, elev=10, zoom=1.15)


def chiffres():
    lignes = []
    for kg in (6, 20, 40):
        p = urne_compagnon('LOU', kg, en_pieces=True)
        d = {}
        for nom, m in (('corps', p['corps']), ('couvercle', p['couvercle']),
                       ('medaillon', p['medaillon'])):
            _, r = controle(m, nom, appuis=(4.4,) if nom == 'medaillon' else ())
            d[nom] = r
        lignes.append((kg, p, d))
    return lignes


if __name__ == '__main__':
    vues()
    for kg, p, d in chiffres():
        tot = sum(d[k]['poids_g'] for k in d)
        print(f"{kg:>3} kg | urne {p['h']:.0f} mm | contenance {p['contenance_cm3']:.0f} cm3 | "
              f"{tot:.0f} g | {tot/30:.1f} h | {tot/1000*20:.2f} EUR de matiere | "
              + ' '.join(f"{k}:{d[k]['verdict']}/{d[k]['porte_a_faux_pct']}%" for k in d))
