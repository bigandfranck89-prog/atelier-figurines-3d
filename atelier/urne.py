#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L'URNE COMPAGNON — le plus gros gain de la liste « matieres speciales »
(note FORGEON du 15/08/2026 : 44,90 -> 59-69 EUR en marbre).

POURQUOI CE DESSIN-LA, ET PAS UN VASE AVEC UN COUVERCLE :
  1. LA CONTENANCE EST CALCULEE, PAS DECOREE. Regle des pompes funebres animalieres :
     1 pouce cube de cendres par livre de poids vif, soit 36 cm3 par kilo. L'urne se
     dimensionne donc sur le POIDS DU CHIEN, avec 12 % de marge. Une urne trop petite
     est un drame le jour de la remise : c'est le seul chiffre a ne pas rater.
  2. LA PERSONNALISATION EST UNE PIECE SEPAREE. Le corps est generique, le MEDAILLON
     porte le prenom et la patte. On imprime les corps a l'avance (10 h de machine) et
     le medaillon a la commande (25 min). C'est le seul moyen de tenir « livre en 48 h »
     sans stocker un corps par prenom.
  3. RIEN NE SURPLOMBE LE VIDE, AUCUNE BEQUILLE :
     - corps : solide de revolution, aucune pente au-dela de 45 degres ;
     - logement du medaillon : LOSANGE (pointe en haut), la seule forme de creux
       vertical qui s'imprime sans plafond — meme regle que les trous de objets.py ;
     - couvercle : imprime A L'ENVERS, petit diametre sur le plateau, il s'evase a
       39 degres. Il est rendu ici DANS SA POSITION D'IMPRESSION.
  4. ON NE PERCE JAMAIS UNE URNE. Le creux du medaillon n'est PAS rabote dans le
     ventre — la paroi ne fait que 2,8 mm, on l'aurait traversee. Il est taille dans
     un CARTOUCHE rapporte de 4 mm de saillie : il reste 3,8 mm de paroi derriere.
     (Premier jet corrige : le rabotage ouvrait un trou dans l'urne.)
"""
import numpy as np
import trimesh
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union
from shapely.affinity import scale as sh_scale, translate as sh_translate

from objets import losange, controle
from plaques_race2 import texte_poly, extrude_multi
from objets_canins import patte_2d

MARBRE, BOIS, PAIL, PHOS = 'marbre', 'bois', 'paillettes', 'phospho'

# redresse une piece dessinee a plat (relief vers +Z) pour la coller sur la
# facade avant (relief vers +Y), sans miroir : le prenom reste lisible.
_DEBOUT = np.eye(4)
_DEBOUT[:3, :3] = np.array([[-1, 0, 0], [0, 0, 1], [0, 1, 0]], dtype=float)

CM3_PAR_KG = 36.1        # 1 pouce cube par livre de poids vif
MARGE = 1.12             # on ne remplit jamais une urne a ras bord
EP = 2.8                 # paroi
EP_FOND = 4.0            # fond


# --------------------------------------------------------------- le corps

def _profil(h, r_bas, r_ventre, r_col):
    """Silhouette de l'urne, du bas vers le haut. Aucune pente > 45 degres."""
    zs = np.array([0.00, 0.06, 0.22, 0.45, 0.68, 0.86, 1.00]) * h
    rs = np.array([r_bas, r_bas * 1.05, r_ventre, r_ventre,
                   r_ventre * 0.90, r_col * 1.12, r_col])
    return zs, rs


def _corps(h, r_bas, r_ventre, r_col):
    """Solide de revolution creux, fond plein. Aucune pente au-dela de 45 degres."""
    zs, rs = _profil(h, r_bas, r_ventre, r_col)
    z_fin = np.linspace(0, h, 90)
    r_ext = np.interp(z_fin, zs, rs)
    r_int = np.clip(r_ext - EP, 0.5, None)

    contour = [(0.0, 0.0)]
    contour += [(r_ext[i], z_fin[i]) for i in range(len(z_fin))]
    contour += [(r_int[i], z_fin[i]) for i in range(len(z_fin) - 1, -1, -1)
                if z_fin[i] >= EP_FOND]
    contour += [(0.0, EP_FOND)]
    corps = trimesh.creation.revolve(np.array(contour, dtype=float), sections=128)
    corps.fix_normals()
    return corps, (z_fin, r_ext)


def _cartouche(corps, prof_ext, z_c, larg, haut, saillie=4.0):
    """LE CARTOUCHE : un bossage en losange colle sur le ventre, dont la face
    avant est PLATE et VERTICALE. On ne RABOTE pas le ventre pour l'aplatir —
    ca percerait une paroi de 2,8 mm — on AJOUTE de la matiere : c'est elle qui
    donne les 3 mm de creux du medaillon en gardant 3,8 mm de paroi derriere.
    Un prisme en losange n'a aucune face horizontale : il s'imprime sans bequille."""
    z_fin, r_ext = prof_ext
    los = losange(0.0, z_c, larg, haut)
    xs, zz = np.array(los.exterior.coords).T
    r_here = np.interp(zz, z_fin, r_ext)
    y_surf = np.sqrt(np.clip(r_here ** 2 - xs ** 2, 0.0, None))
    y_avant = float(np.interp(z_c, z_fin, r_ext)) + saillie
    y_arriere = float(y_surf.min()) - 1.5          # mord juste assez pour souder

    boss = trimesh.creation.extrude_polygon(los, y_avant - y_arriere)
    boss.apply_transform(_DEBOUT)
    boss.apply_translation([0, y_arriere, 0])
    m = trimesh.boolean.union([corps, boss])
    m.fix_normals()
    return m, y_avant


def _creux_medaillon(y_avant, z_c, larg, haut, prof=3.0):
    """Logement en losange : pointe en haut, ses faces hautes restent sous 45 degres."""
    los = losange(0.0, z_c, larg, haut)
    m = trimesh.creation.extrude_polygon(los, prof + 8.0)
    m.apply_transform(_DEBOUT)                 # le losange se redresse, il creuse vers l'avant
    m.apply_translation([0, y_avant - prof, 0])
    return m


def _cale_losange(geom, larg, haut, cy, part=0.80):
    """Cale un dessin DANS le losange : a la hauteur cy, le losange ne fait plus
    que larg*(1-2|cy|/haut) de large. C'est ce calcul qui evite que le prenom
    deborde en pointe basse — le defaut du premier jet."""
    dispo = larg * (1.0 - 2.0 * abs(cy) / haut) * part
    x0, y0, x1, y1 = geom.bounds
    k = min(dispo / (x1 - x0), (haut * 0.30) / (y1 - y0))
    g = sh_scale(geom, xfact=k, yfact=k, origin=(x0, y0))
    x0, y0, x1, y1 = g.bounds
    return sh_translate(g, xoff=-(x1 - x0) / 2 - x0, yoff=cy - (y1 - y0) / 2 - y0)


def medaillon(prenom='LOU', larg=44.0, haut=58.0, prof=3.2, ep=4.4, jeu=0.35):
    """La piece personnalisee : losange, patte + prenom en relief.
    S'imprime A PLAT, en 25 minutes, dans la matiere que l'on veut —
    c'est elle, et elle seule, que l'on relance pour chaque commande."""
    los = losange(0.0, 0.0, larg - 2 * jeu, haut - 2 * jeu)
    base = trimesh.creation.extrude_polygon(los, ep)

    pat = _cale_losange(patte_2d(larg=40.0), larg, haut, haut * 0.15, part=0.62)
    txt = _cale_losange(texte_poly(prenom, taille=22), larg, haut, -haut * 0.17, part=0.80)

    rel = extrude_multi(unary_union([pat, txt]).buffer(0), 1.6)
    rel.apply_translation([0, 0, ep])
    m = trimesh.util.concatenate([base, rel])
    m.fix_normals()
    return m


def couvercle(r_col, h=None, jeu=0.35, ep=3.2):
    """Couvercle tronconique + jupe qui entre dans le col.
    RENDU DANS SA POSITION D'IMPRESSION : petit diametre sur le plateau,
    il s'evase a moins de 45 degres, la jupe monte ensuite. Zero bequille."""
    r_bas = r_col + 2.2          # la lèvre deborde du col : on l'attrape avec deux doigts
    r_haut = r_col * 0.42
    # la hauteur SUIT le diametre : c'est elle qui garde la pente sous 45 degres.
    # (un couvercle de hauteur fixe s'aplatit quand l'urne grandit, et devient
    #  impossible a imprimer sans bequille — verifie sur l'urne de 40 kg.)
    if h is None:
        h = max(24.0, (r_bas - r_haut) / 0.78)
    zs = [0.0, h * 0.86, h]
    rs = [r_haut, r_bas * 0.98, r_bas]
    r_j = r_col - EP - jeu
    # le creux d'allegement s'arrete AVANT l'aplomb de la jupe : sinon la jupe
    # demarre au-dessus du vide et il lui faut une bequille (vu sur l'urne de 6 kg).
    r_creux = min(r_bas - ep, r_j - 3.0)
    contour = [(0.0, 0.0)]
    contour += list(zip(rs, zs))
    contour += [(r_creux, h), (r_haut * 0.55, ep * 1.6), (0.0, ep * 1.6)]
    chapeau = trimesh.creation.revolve(np.array(contour, dtype=float), sections=128)

    jupe = trimesh.creation.revolve(np.array(
        [(r_j - 2.4, h), (r_j, h), (r_j, h + 9.0), (r_j - 1.2, h + 11.0),
         (r_j - 2.4, h + 11.0), (r_j - 2.4, h)], dtype=float), sections=128)
    m = trimesh.boolean.union([chapeau, jupe])
    m.fix_normals()
    return m


# ------------------------------------------------------------ l'assemblage

def dimensions(poids_chien_kg=20.0):
    """Contenance necessaire, puis taille de l'urne qui la donne."""
    v_cible = poids_chien_kg * CM3_PAR_KG * MARGE          # cm3
    h, r_ventre = 118.0, 52.0                              # gabarit de reference
    for _ in range(6):
        cap = contenance(h, r_ventre)
        k = (v_cible / cap) ** (1 / 3.0)
        h, r_ventre = h * k, r_ventre * k
    return round(h, 1), round(r_ventre, 1), round(v_cible, 0)


def contenance(h, r_ventre):
    """Volume interieur reel, en cm3 (integration du profil)."""
    zs, rs = _profil(h, r_ventre * 0.90, r_ventre, r_ventre * 0.58)
    z = np.linspace(EP_FOND, h - 1.0, 400)
    r = np.clip(np.interp(z, zs, rs) - EP, 0, None)
    return float(np.trapezoid(np.pi * r ** 2, z) / 1000.0)


def urne_compagnon(prenom='LOU', poids_chien_kg=20.0, en_pieces=False):
    h, r_ventre, v_cible = dimensions(poids_chien_kg)
    r_bas, r_col = r_ventre * 0.90, r_ventre * 0.58
    corps, prof_ext = _corps(h, r_bas, r_ventre, r_col)

    larg = min(46.0, r_ventre * 0.80)
    haut = max(larg * 1.30, min(62.0, h * 0.46))       # plus HAUT que large : c'est
    z_c = h * 0.50                                     # ce qui rend le creux imprimable
    corps, y_avant = _cartouche(corps, prof_ext, z_c, larg + 9.0, haut + 12.0)
    corps = trimesh.boolean.difference(
        [corps, _creux_medaillon(y_avant, z_c, larg, haut, prof=3.2)])
    corps.fix_normals()

    med = medaillon(prenom, larg=larg, haut=haut)
    cvl = couvercle(r_col)

    if en_pieces:
        return {'corps': corps, 'medaillon': med, 'couvercle': cvl, 'h': h,
                'r_ventre': r_ventre, 'contenance_cm3': contenance(h, r_ventre)}

    m2 = med.copy()                                   # vue d'assemblage
    m2.apply_transform(_DEBOUT)
    m2.apply_translation([0, y_avant - 3.2, z_c])
    c2 = cvl.copy()
    c2.apply_transform(trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0]))
    c2.apply_translation([0, 0, -c2.bounds[0][2] + h - 11.0])
    return [(corps, MARBRE), (c2, MARBRE), (m2, PAIL)]


if __name__ == '__main__':
    for kg in (6, 20, 40):
        p = urne_compagnon('LOU', kg, en_pieces=True)
        print(f"--- chien de {kg} kg : urne {p['h']:.0f} mm, contenance "
              f"{p['contenance_cm3']:.0f} cm3 (besoin {kg*CM3_PAR_KG*MARGE:.0f})")
        for nom, m in (('corps', p['corps']), ('couvercle', p['couvercle']),
                       ('medaillon', p['medaillon'])):
            _, r = controle(m, nom, appuis=(4.4,) if nom == 'medaillon' else ())
            print('   ', {k: r[k] for k in ('nom', 'dim_mm', 'poids_g', 'cout_eur',
                                            'porte_a_faux_pct', 'etanche', 'verdict')})
