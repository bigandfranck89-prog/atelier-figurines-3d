#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PLATEAU n° 2 « utile & déco » — à enchaîner le lendemain du plateau salon.

  1. RT-01  Range-télécommande         (bandes : socle brun 0-22, liseré crème 22-26, corps bois)
  2. DC-01  Doseur à croquettes        (crème, poignée brune)
  3. ST-01  Support téléphone chien    (base noire, chien bois, marqué DÉTENTE CANINE en blanc)
  4. PH-01  Photophore ajouré          (anneaux bruns 0-8 et 84-92, crème au milieu)
  5. PK-01  Porte-clés photo           (cadre brun, motif crème)
  6. MD-01  Médaillon VÉNUS Ø36       (recto prénom, verso téléphone gravé)

Écartés de ce plateau : le vase VS-01 (mode spirale : il s'imprime seul) et
le support casque SC-01 (23 cm de haut : mieux vaut l'imprimer seul).
Mêmes 4 bobines que le plateau salon."""
import trimesh
from objets import controle, photophore
from objets2 import range_telecommande
from complements import pk01_porte_cles_photo, md01_medaillon, dc01_doseur, st01_support_telephone
from plateau_salon2 import poser_groupe, ecrire_3mf_multi, image_couleurs, PLATEAU, BOIS, BRUN, NOIR, BLANC
from bandes import tranches


def rt_couleurs():
    """Range-télécommande en 3 bandes : socle brun, liseré crème, corps bois."""
    b1, b2, b3 = tranches(range_telecommande(), [22.0, 26.0])
    return [(b1, BRUN), (b2, BLANC), (b3, BOIS)]


def ph_couleurs():
    """Photophore : anneaux bruns en bas et en haut, crème au milieu."""
    b1, b2, b3 = tranches(photophore(), [8.0, 84.0])
    return [(b1, BRUN), (b2, BLANC), (b3, BRUN)]


def plateau():
    objs = []
    objs.append(('Range-télécommande', poser_groupe(rt_couleurs(), 4, 4)))
    cq, lm = dc01_doseur(en_pieces=True)
    objs.append(('Doseur à croquettes', poser_groupe([(cq, BLANC), (lm, BRUN)], 4, 150)))
    st = st01_support_telephone(en_pieces=True)
    parts_st = [(st[0], NOIR), (st[1], BOIS)] + ([(st[2], BLANC)] if len(st) > 2 else [])
    objs.append(('Support téléphone chien', poser_groupe(parts_st, 110, 4)))
    objs.append(('Photophore ajouré', poser_groupe(ph_couleurs(), 110, 80)))
    ca, mo = pk01_porte_cles_photo(en_pieces=True)
    objs.append(('Porte-clés photo', poser_groupe([(ca, BRUN), (mo, BLANC)], 110, 164)))
    b6, r6 = md01_medaillon('VÉNUS', diam=36, en_pieces=True, tel='06 12 34 / 56 78 90')
    objs.append(('Médaillon VÉNUS', poser_groupe([(b6, BOIS), (r6, BRUN)], 170, 164)))
    return objs


if __name__ == '__main__':
    objs = plateau()
    for nom, parts in objs:
        b = trimesh.util.concatenate([m for m, _ in parts]).bounds
        assert b[0][0] >= 0 and b[0][1] >= 0 and b[1][0] <= PLATEAU and b[1][1] <= PLATEAU, (nom, b)
    boites = [(nom, trimesh.util.concatenate([m for m, _ in parts]).bounds) for nom, parts in objs]
    for i in range(len(boites)):
        for j in range(i + 1, len(boites)):
            a, b = boites[i][1], boites[j][1]
            chev = not (a[1][0] + 2 < b[0][0] or b[1][0] + 2 < a[0][0] or
                        a[1][1] + 2 < b[0][1] or b[1][1] + 2 < a[0][1])
            assert not chev, (boites[i][0], boites[j][0])
    tout = trimesh.util.concatenate([m for _, parts in objs for m, _ in parts])
    tout.fix_normals()
    m2, infos = controle(tout, 'Plateau 2 utile & deco', appuis=(1.0, 1.2, 2.0, 2.2, 6.0, 8.0, 22.0, 26.0, 84.0))
    print(infos['dim_mm'], infos['verdict'], infos['poids_g'], 'g', infos['cout_eur'], 'EUR',
          'pf', infos['porte_a_faux_pct'], '%')
    for nom, b in boites:
        print(f'  {nom:28s} {b[1][0]-b[0][0]:5.0f} x {b[1][1]-b[0][1]:5.0f} x {b[1][2]-b[0][2]:4.0f} mm')
    ecrire_3mf_multi(objs, 'sortie4/plateau2_deco.3mf', 'Plateau 2 Forgeon - utile et deco - 4 couleurs')
    image_couleurs(objs, 'sortie4/plateau2_deco_dessus.png', azim=-90, elev=78)
    image_couleurs(objs, 'sortie4/plateau2_deco.png', azim=-55, elev=30)
