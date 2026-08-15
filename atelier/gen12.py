#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fabrique les visuels des 12 produits sans image du catalogue (15/08/2026).

Contexte : au 15/08/2026, 12 des 26 lignes de fichiers_produits avaient
image_conception vide. Ce programme les fabrique toutes, en reutilisant le
code de dessin deja sauvegarde ici (objets.py, objets2.py, complements.py,
plaques_race2.py) et le rendu soigne de rendu2.py.

Usage :
    pip install trimesh shapely numpy matplotlib pillow manifold3d rtree scipy networkx
    python3 gen12.py            # les 12
    python3 gen12.py PN-02       # une seule reference

Sortie, dans sortie/ : <REF>_brut.png (objet detoure, fond transparent),
<REF>.jpg (carte catalogue 430x470 avec titre et ombre portee) et <REF>.svg
(la meme carte, JPEG embarque en base64, autonome).

Les 12 references produites :
  PCV-01 SC-01 PH-01 PR-01 VS-01 PCV-02 RT-01 PN-02 MD-01 PK-01 DC-01 ST-01

Couleurs AMS du projet : bois clair, brun chocolat, noir mat, blanc creme.
"""
import os, sys, json, base64
from rendu2 import belle_image, carte

BOIS, BRUN, NOIR, BLANC = '#d8c49a', '#4a3826', '#24242a', '#f2ede2'
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sortie')
os.makedirs(OUT, exist_ok=True)


def pieces(ref):
    """Retourne (liste (mesh, couleur), titre, sous-titre, (azimut, elevation))."""
    if ref == 'PCV-01':
        from objets import porte_cartes
        return [(porte_cartes(), NOIR)], 'Le Porte-cartes de visite', 'Bureau - PCV-01', (-55, 22)
    if ref == 'SC-01':
        from objets import support_casque
        return [(support_casque(), NOIR)], 'Le Support de casque', 'Bureau - SC-01', (-60, 14)
    if ref == 'PH-01':
        from objets import photophore
        return [(photophore(), BLANC)], 'Le Photophore ajoure', 'Deco - PH-01', (-55, 12)
    if ref == 'PR-01':
        from objets import prenom
        p, l = prenom('LOU', en_pieces=True)
        return [(p, BOIS), (l, BRUN)], 'Le Prenom en relief', 'Deco - PR-01', (-55, 48)
    if ref == 'VS-01':
        from objets import vase
        return [(vase(), BOIS)], 'Le Vase torsade', 'Deco - VS-01', (-55, 12)
    if ref == 'PCV-02':
        from objets2 import porte_cartes_creux
        return [(porte_cartes_creux(), NOIR)], 'Le Porte-cartes allege', 'Bureau - PCV-02', (-55, 22)
    if ref == 'RT-01':
        from objets2 import range_telecommande
        return [(range_telecommande(), BOIS)], 'Le Range-telecommande', 'Maison - RT-01', (-55, 20)
    if ref == 'PN-02':
        from plaques_race2 import plaque_niche
        (c, r), _ = plaque_niche('golden', prenom='ULYSSE', en_pieces=True)
        return [(c, BOIS), (r, BRUN)], 'La Plaque de niche par race', 'Univers canin - PN-02', (-55, 52)
    if ref == 'MD-01':
        from complements import md01_medaillon
        b, r = md01_medaillon('VENUS', en_pieces=True)
        return [(b, BRUN), (r, BOIS)], 'Le Medaillon recto-verso', 'Promenade - MD-01', (-55, 55)
    if ref == 'PK-01':
        from complements import pk01_porte_cles_photo
        b, r = pk01_porte_cles_photo(en_pieces=True)
        return [(b, NOIR), (r, BLANC)], 'Le Porte-cles photo', 'Photo souvenir - PK-01', (-55, 55)
    if ref == 'DC-01':
        from complements import dc01_doseur
        return [(dc01_doseur(), BOIS)], 'Le Doseur a croquettes', 'Repas - DC-01', (-55, 18)
    if ref == 'ST-01':
        from complements import st01_support_telephone
        parts = st01_support_telephone(en_pieces=True)
        out = [(parts[0], NOIR), (parts[1], BOIS)]
        if len(parts) > 2 and parts[2] is not None:
            out.append((parts[2], BLANC))
        return out, 'Le Support telephone chien', 'Bureau - ST-01', (-55, 22)
    raise SystemExit('reference inconnue : ' + ref)


REFS = ['PCV-01', 'SC-01', 'PH-01', 'PR-01', 'VS-01', 'PCV-02',
        'RT-01', 'PN-02', 'MD-01', 'PK-01', 'DC-01', 'ST-01']

if __name__ == '__main__':
    voulu = sys.argv[1:] or REFS
    for ref in voulu:
        parts, titre, sous, (azim, elev) = pieces(ref)
        brut = os.path.join(OUT, ref + '_brut.png')
        belle_image(parts, brut, azim=azim, elev=elev)
        c = carte(brut, titre, sous)
        jpg = os.path.join(OUT, ref + '.jpg')
        c.convert('RGB').save(jpg, 'JPEG', quality=86)
        b64 = base64.b64encode(open(jpg, 'rb').read()).decode()
        svg = ('<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
               'width="430" height="470" viewBox="0 0 430 470">'
               '<image width="430" height="470" xlink:href="data:image/jpeg;base64,' + b64 + '"/></svg>')
        open(os.path.join(OUT, ref + '.svg'), 'w').write(svg)
        print(ref, 'OK', len(b64) // 1024, 'Ko base64')
