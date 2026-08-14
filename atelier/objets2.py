# -*- coding: utf-8 -*-
"""Deux objets repris le 13/08 : le porte-cartes allege et le range-telecommande."""
import numpy as np, trimesh
from shapely.geometry import Polygon
from shapely.ops import unary_union
from objets import controle

def meilleure_pose(m):
    """Essaie les six facons de poser l'objet et garde celle qui ne demande
    aucune bequille (et, a egalite, la moins haute)."""
    R = trimesh.transformations.rotation_matrix
    poses = [np.eye(4), R(np.pi,[1,0,0]), R(np.pi/2,[1,0,0]), R(-np.pi/2,[1,0,0]),
             R(np.pi/2,[0,1,0]), R(-np.pi/2,[0,1,0])]
    best, note = None, None
    for T in poses:
        c = m.copy(); c.apply_transform(T)
        _, i = controle(c, 'essai')
        cle = (round(i['porte_a_faux_pct'],1), i['surface_plateau_cm2'])
        if note is None or cle < note:
            note, best = cle, c
    return best


def extr(poly, L):
    m = trimesh.creation.extrude_polygon(poly, L)
    m.apply_transform(trimesh.transformations.rotation_matrix(-np.pi/2, [1,0,0]))
    return m

# ---------------- porte-cartes, version creuse (tache 1228)
def porte_cartes_creux():
    L = 96.0
    ext = [(0,0),(52,0),(52,10),(42,40),(33,40),(29,9),(24,9),(20,40),(11,40),(0,10)]
    plein = Polygon(ext)
    # on evide l'interieur, en laissant le dessous OUVERT : rien a soutenir dedans
    creux = plein.buffer(-2.4)
    if creux.is_empty: raise SystemExit("evidement impossible")
    parts = list(creux.geoms) if creux.geom_type=='MultiPolygon' else [creux]
    # on prolonge le creux vers le bas pour deboucher sous l'objet
    bas = []
    for p in parts:
        x0,y0,x1,y1 = p.bounds
        bas.append(Polygon([(x0,-5),(x1,-5),(x1,y0+0.5),(x0,y0+0.5)]))
    creux = unary_union(parts + bas)
    reste = plein.difference(creux)
    parts2 = list(reste.geoms) if reste.geom_type=='MultiPolygon' else [reste]
    m = trimesh.util.concatenate([extr(p, L) for p in parts2 if p.area > 1])
    m.apply_transform(trimesh.transformations.rotation_matrix(np.pi, [0,0,1]))
    return m

# ---------------- range-telecommande, poche ouverte inclinee (tache 970)
def range_telecommande():
    L = 150.0                     # largeur : 3 telecommandes cote a cote
    # profil de cote : dos vertical a visser au mur, poche penchee en avant,
    # ouverte en haut ET sur le devant -> on voit les telecommandes, rien ne surplombe.
    ext = [
        (0,0), (70,0),          # semelle, du mur vers l'avant
        (66,80), (62,80),       # montant avant : il penche VERS le mur en montant
        (60,8), (6,8),          # fond de la poche
        (6,140), (0,140),       # dos a visser au mur
    ]
    return meilleure_pose(extr(Polygon(ext), L))

if __name__ == '__main__':
    from rendu import image, ecrire_3mf
    import json, os
    os.makedirs('sortie2', exist_ok=True)
    res = []
    for ref, nom, f in [('PCV-02','Le Porte-cartes (version allegee)', porte_cartes_creux),
                        ('RT-01','Le Range-telecommande', range_telecommande)]:
        m, i = controle(f(), nom)
        i.update(ref=ref)
        m.export(f'sortie2/{ref}.stl'); ecrire_3mf(m, f'sortie2/{ref}.3mf', nom)
        image(m, f'sortie2/{ref}.png')
        res.append(i); print(ref, i['dim_mm'], i['verdict'], i['poids_g'],'g', i['cout_eur'],'EUR', 'porte-a-faux', i['porte_a_faux_pct'],'%')
    json.dump(res, open('sortie2/rapport.json','w'), ensure_ascii=False, indent=1)
