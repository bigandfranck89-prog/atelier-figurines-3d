# -*- coding: utf-8 -*-
"""PLATEAU 1 — BOIS : les trois grandes pieces, calees a la main."""
import numpy as np, trimesh
from plateaux_canins import rendu_plateau, poser
from objets_canins import porte_laisse, cadre_empreinte
from plaques_race2 import plaque_niche

def tourner(m):
    m=m.copy(); m.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2,[0,0,1])); return poser(m)

pl=[]
a = poser(porte_laisse('REX','golden'));      a.apply_translation([13,4,0])
b = poser(cadre_empreinte('LOU'));            b.apply_translation([4,102,0])
c = tourner(poser(plaque_niche('golden','ULYSSE')[0])); c.apply_translation([134,102,0])
for nom,m in [('Porte-laisse mural REX',a),('Cadre empreinte LOU',b),('Plaque de niche ULYSSE',c)]:
    pl.append((nom,m,'bois'))

g=0
for n,m,_ in pl:
    gr=(m.volume/1000.0*(0.35+0.65*0.15))*1.24; g+=gr
    x0,y0=m.bounds[0][:2]; x1,y1=m.bounds[1][:2]
    print(f'{n:24s} x {x0:5.0f}-{x1:5.0f}  y {y0:5.0f}-{y1:5.0f}  {gr:5.1f} g', flush=True)
print(f'-> {g:.0f} g, ~{g/30:.1f} h de machine', flush=True)
# controle de non-chevauchement
for i in range(len(pl)):
    for j in range(i+1,len(pl)):
        A,B=pl[i][1].bounds,pl[j][1].bounds
        if A[0][0]<B[1][0] and B[0][0]<A[1][0] and A[0][1]<B[1][1] and B[0][1]<A[1][1]:
            print('!! CHEVAUCHEMENT', pl[i][0], pl[j][0], flush=True)
print('controle fait', flush=True)
rendu_plateau(pl,'sortie_mat/plateau1.png',azim=-60,elev=44); print('3/4 ok', flush=True)
rendu_plateau(pl,'sortie_mat/plateau1_dessus.png',azim=-90,elev=88); print('dessus ok', flush=True)
