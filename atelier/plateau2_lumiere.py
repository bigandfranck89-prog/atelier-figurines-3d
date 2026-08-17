# -*- coding: utf-8 -*-
import numpy as np, trimesh
from plateaux_canins import caler, rendu_plateau, poser
from complements import md01_medaillon, pk01_porte_cles_photo
from plateau_salon3 import porte_cles_patte
from objets_neufs import veilleuse_silhouette, boule_noel

def boule_posee():
    """La boule est coupee plat sur un cote : cette face doit toucher le plateau,
    sinon il faudrait des bequilles."""
    m = boule_noel()
    m.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2, [1,0,0]))
    return poser(m)

P2=[]
for n in ['VÉNUS','STELLA','YUZU','OLYMPE']:
    P2.append((f'Médaillon {n}', md01_medaillon(n, diam=36, tel='0612345678'), 'phospho'))
P2.append(('Veilleuse silhouette', veilleuse_silhouette(), 'phospho'))
for i in range(3):
    P2.append((f'Porte-clés patte {i+1}', porte_cles_patte(42), 'paillettes'))
for i in range(2):
    P2.append((f'Porte-clés photo {i+1}', pk01_porte_cles_photo(), 'marbre'))
P2.append(('Boule de Noël', boule_posee(), 'paillettes'))
pl, ref = caler(P2)
print('places', len(pl), '| recales', ref, flush=True)
g=0
for n,m,mat in pl:
    gr=(m.volume/1000.0*(0.35+0.65*0.15))*1.24; g+=gr
    print(f'   {n:24s} {mat:11s} {m.extents[0]:4.0f} x {m.extents[1]:4.0f} x {m.extents[2]:4.0f} mm  {gr:5.1f} g', flush=True)
print(f'-> {g:.0f} g, ~{g/30:.1f} h', flush=True)
rendu_plateau(pl,'sortie_mat/plateau2_dessus.png',azim=-90,elev=88); print('dessus ok', flush=True)
