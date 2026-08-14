#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Images d'apercu + fichiers .3mf prets a imprimer."""
import io, json, os, zipfile, base64
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import trimesh
from objets import OBJETS, controle

os.makedirs('sortie', exist_ok=True)

ENTETE = """<?xml version="1.0" encoding="UTF-8"?>
<model unit="millimeter" xml:lang="fr-FR" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">
 <metadata name="Application">Atelier Figurines 3D</metadata>
 <metadata name="Title">{titre}</metadata>
 <resources>
  <object id="1" type="model">
   <mesh>
    <vertices>
{sommets}
    </vertices>
    <triangles>
{triangles}
    </triangles>
   </mesh>
  </object>
 </resources>
 <build><item objectid="1"/></build>
</model>"""

CT = """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>
</Types>"""

RELS = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>
</Relationships>"""


def ecrire_3mf(m, chemin, titre):
    v = '\n'.join(f'     <vertex x="{x:.4f}" y="{y:.4f}" z="{z:.4f}"/>' for x, y, z in m.vertices)
    t = '\n'.join(f'     <triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in m.faces)
    xml = ENTETE.format(titre=titre, sommets=v, triangles=t)
    with zipfile.ZipFile(chemin, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml', CT)
        z.writestr('_rels/.rels', RELS)
        z.writestr('3D/3dmodel.model', xml)


def image(m, chemin, couleur='#8fb8e8', azim=None):
    mm = m.copy()
    # on decoupe les grandes faces : sinon le dessin les empile dans le mauvais ordre
    if len(mm.faces) < 30000:
        v, f = trimesh.remesh.subdivide_to_size(mm.vertices, mm.faces, max_edge=5.0)
        mm = trimesh.Trimesh(vertices=v, faces=f, process=False)
    fig = plt.figure(figsize=(4.6, 4.6), dpi=115)
    ax = fig.add_subplot(111, projection='3d')
    plat = mm.extents[2] < 0.35 * max(mm.extents[0], mm.extents[1])
    elev, az = (52.0, -62.0) if plat else (22.0, -58.0)
    azim = az if azim is None else azim
    e, a = np.radians(elev), np.radians(azim)
    oeil = np.array([np.cos(e) * np.cos(a), np.cos(e) * np.sin(a), np.sin(e)])
    ordre = np.argsort(mm.triangles_center @ oeil)      # du plus loin au plus proche
    tri = mm.vertices[mm.faces][ordre]
    col = Poly3DCollection(tri, alpha=1.0)
    n = mm.face_normals[ordre]
    lum = np.clip(0.35 + 0.65 * (n @ np.array([0.35, -0.55, 0.75])), 0.12, 1.0)
    base = np.array(matplotlib.colors.to_rgb(couleur))
    col.set_facecolor(np.clip(base[None, :] * lum[:, None], 0, 1))
    col.set_edgecolor('none')
    ax.add_collection3d(col)
    d = mm.extents.max() / 2 * 1.15
    c = mm.bounds.mean(axis=0)
    ax.set_xlim(c[0] - d, c[0] + d); ax.set_ylim(c[1] - d, c[1] + d); ax.set_zlim(c[2] - d, c[2] + d)
    ax.set_box_aspect((1, 1, 1))
    ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off()
    ax.patch.set_alpha(0.0)
    fig.patch.set_facecolor('#141413')
    fig.tight_layout(pad=0)
    fig.savefig(chemin, facecolor='#141413', bbox_inches='tight', pad_inches=0.02)
    plt.close(fig)


if __name__ == '__main__':
    rapport = []
    for ref, nom, famille, f, mode in OBJETS:
        appuis = (4.0,) if ref == 'PR-01' else ()
        m, infos = controle(f(), nom, mode=mode, appuis=appuis)
        infos.update(ref=ref, famille=famille, mode=mode)
        m.export(f'sortie/{ref}.stl')
        ecrire_3mf(m, f'sortie/{ref}.3mf', nom)
        image(m, f'sortie/{ref}.png')
        infos['png'] = f'sortie/{ref}.png'
        rapport.append(infos)
        print(ref, infos['dim_mm'], infos['verdict'], infos['poids_g'], 'g')
    json.dump(rapport, open('sortie/rapport.json', 'w'), ensure_ascii=False, indent=1)
    print('fichiers :', sorted(os.listdir('sortie')))
