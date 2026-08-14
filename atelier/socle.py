#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FORGEON — Socle de lampe pour lithophanie
------------------------------------------
Sans socle, on livre une plaque : le client a un « cadre », pas une lampe.
Avec socle, il glisse la plaque dans la rainure, pose une bougie LED du
commerce derrière, et il a une vraie lampe. C'est ce qui fait tenir la
promesse du produit.

MÉTHODE : le socle est un PROFIL 2D extrudé sur la largeur. C'est plus sûr
qu'un assemblage d'opérations booléennes (essayé le 09/08 : maillage non
étanche et bloc de 108 cm³, soit 2,70 € de matière pour rien) et ça donne
un objet étanche par construction, trois fois plus léger.

Vu de côté, de l'avant vers l'arrière :
    ┌──┐                     bloc avant (14 mm) : porte la rainure inclinée
    │▓▓│___________┌──┐      plateforme basse (4 mm) : on y pose la bougie
    └──┴───────────┴──┘      rebord arrière (10 mm) : la bougie ne recule pas

Contraintes d'impression (Bambu P2S, PLA, sans support) : base plate,
aucun porte-à-faux, parois >= 3 mm, rainure débouchante vers le haut.

Bougie LED chauffe-plat standard : 37 à 39 mm de diamètre, 15 à 20 mm de haut.
"""

import numpy as np
import trimesh
from shapely.geometry import Polygon


class Socle:
    """Réglages. Les valeurs par défaut conviennent aux deux formats vendus."""
    largeur_plaque = 100.0   # mm — largeur de la lithophanie à recevoir
    ep_plaque = 3.0          # mm — épaisseur de la plaque
    jeu = 0.6                # mm — jeu d'insertion (tolérance d'impression)
    marge = 12.0             # mm de socle de chaque côté de la plaque

    prof_bloc = 16.0         # mm — profondeur du bloc avant
    haut_bloc = 14.0         # mm
    prof_plateforme = 30.0   # mm — place pour la bougie LED
    haut_plateforme = 4.0    # mm
    prof_rebord = 4.0        # mm
    haut_rebord = 10.0       # mm

    prof_rainure = 9.0       # mm — profondeur de la rainure
    inclinaison = 10.0       # degrés — la plaque penche vers l'arrière


def profil(reg: Socle) -> Polygon:
    """Section du socle vue de côté (axe Y = profondeur, axe Z = hauteur)."""
    y1 = reg.prof_bloc
    y2 = y1 + reg.prof_plateforme
    y3 = y2 + reg.prof_rebord
    contour = [
        (0, 0), (y3, 0), (y3, reg.haut_rebord), (y2, reg.haut_rebord),
        (y2, reg.haut_plateforme), (y1, reg.haut_plateforme),
        (y1, reg.haut_bloc), (0, reg.haut_bloc),
    ]

    # rainure inclinée : le haut part vers l'arrière, donc la plaque penche
    # en arrière et ne bascule pas vers l'avant.
    larg = reg.ep_plaque + reg.jeu
    centre = reg.prof_bloc / 2
    z_haut = reg.haut_bloc
    z_bas = reg.haut_bloc - reg.prof_rainure
    decal = reg.prof_rainure * np.tan(np.radians(reg.inclinaison))
    fente = [
        (centre - larg / 2 + decal, z_haut + 2),   # dépasse : la rainure débouche
        (centre + larg / 2 + decal, z_haut + 2),
        (centre + larg / 2, z_bas),
        (centre - larg / 2, z_bas),
    ]
    return Polygon(contour).difference(Polygon(fente))


def construire(reg: Socle = None) -> trimesh.Trimesh:
    reg = reg or Socle()
    largeur = reg.largeur_plaque + 2 * reg.marge
    m = trimesh.creation.extrude_polygon(profil(reg), height=largeur)
    # extrude_polygon travaille dans le plan XY et extrude selon Z. Notre profil
    # est dessiné en (profondeur, hauteur) et l'extrusion donne la largeur.
    # Permutation circulaire (x,y,z) -> (z,x,y) : largeur en X, profondeur en Y,
    # hauteur en Z. Déterminant +1, donc pas d'effet miroir sur la pièce.
    permute = np.array([[0, 0, 1, 0],
                        [1, 0, 0, 0],
                        [0, 1, 0, 0],
                        [0, 0, 0, 1]], dtype=float)
    m.apply_transform(permute)
    # centré en X et Y, posé sur le plateau (Z=0)
    bas = m.bounds[0]
    m.apply_translation([0, 0, -bas[2]])
    centre = (m.bounds[0] + m.bounds[1]) / 2
    m.apply_translation([-centre[0], -centre[1], 0])
    m.merge_vertices()
    m.fix_normals()
    return m


def controler(m: trimesh.Trimesh, reg: Socle = None, densite=1.24,
              prix_kg=20.0, remplissage=0.15):
    """Contrôle du socle.

    remplissage : un socle s'imprime creux (15 % suffit). Le poids réel est
    donc bien inférieur au volume plein — on donne les deux pour ne pas
    surestimer le coût comme au premier essai.
    """
    reg = reg or Socle()
    ext = m.bounds[1] - m.bounds[0]
    vol = m.volume / 1000.0
    poids_plein = vol * densite
    # parois + dessus/dessous pleins, cœur au taux de remplissage
    poids_reel = poids_plein * (0.35 + 0.65 * remplissage)
    return {
        "etanche": bool(m.is_watertight),
        "normales_coherentes": bool(m.is_winding_consistent),
        "un_seul_morceau": int(m.body_count) == 1,
        "triangles": int(len(m.faces)),
        "dimensions_mm": [round(float(v), 1) for v in ext],
        "volume_cm3": round(vol, 1),
        "poids_g_estime": round(float(poids_reel), 1),
        "cout_matiere_eur": round(float(poids_reel) / 1000 * prix_kg, 2),
        "pose_a_plat": bool(abs(m.bounds[0][2]) < 0.01),
        "largeur_rainure_mm": reg.ep_plaque + reg.jeu,
    }


if __name__ == "__main__":
    import json
    for larg in (100.0, 150.0):
        r = Socle()
        r.largeur_plaque = larg
        if larg > 120:
            r.prof_bloc, r.haut_bloc = 18.0, 16.0     # plus stable en grand format
        m = construire(r)
        m.export(f"FORGEON_socle_{int(larg)}mm.stl")
        print(f"\n=== socle pour plaque {int(larg)} mm")
        print(json.dumps(controler(m, r), indent=2, ensure_ascii=False))
