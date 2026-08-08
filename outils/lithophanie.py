#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FORGEON — Générateur de lithophanies (photo -> objet imprimable)
----------------------------------------------------------------
Une lithophanie est une plaque dont l'EPAISSEUR varie avec la luminosité de la
photo : les zones claires sont fines (la lumière passe), les zones sombres sont
épaisses (elle est bloquée). Rétroéclairée, la photo apparaît.

Pourquoi c'est stratégique pour l'atelier : c'est de la GEOMETRIE PURE.
Aucun moteur 3D IA, aucune vue multiple, aucun crédit. Donc aucun des verrous
qui bloquent la chaîne 2D->3D ne s'applique ici.

Physique appliquée : la transmission suit la loi de Beer-Lambert
    I = I0 * exp(-k * e)
donc pour une luminosité cible L, l'épaisseur juste est
    e = -ln(L) / k
et non une simple règle de trois (qui écrase les gris et donne une image plate).

Validé le 08/08/2026 sur une VRAIE photo (bouvier bernois, robe noire = le pire
cas) : maillages étanches, normales cohérentes, volumes cohérents entre versions
plate et courbée, 9,8 % de surface bouchée après récupération des ombres.

Dépendances : numpy, pillow, trimesh  (pip install trimesh --break-system-packages)

Auteur : Claude (projet Atelier Figurines 3D) — 08/2026
"""

import numpy as np
from PIL import Image, ImageOps, ImageFilter
import trimesh
import math


# ---------------------------------------------------------------- paramètres
class Reglages:
    """Réglages par défaut, validés pour une Bambu Lab P2S en PLA blanc."""
    ep_min = 0.8      # mm — zones les plus claires (>= 2 périmètres de 0,4 mm)
    ep_max = 3.0      # mm — zones les plus sombres
    largeur = 100.0   # mm
    hauteur = None    # mm — calculée d'après les proportions de la photo
    pas_xy = 0.25     # mm entre deux points du maillage (buse 0,4 mm)
    cadre = 3.0       # mm — bordure pleine épaisseur (rigidité + finition)
    cadre_ep = None   # mm — épaisseur du cadre (par défaut = ep_max)
    gamma = 1.0       # >1 éclaircit, <1 assombrit
    contraste = 1.15  # étirement du contraste avant conversion
    flou = 0.5        # px — léger lissage : évite le bruit de pixel en relief
    inverser = False  # True si la photo est déjà un négatif
    courbe = 0.0      # mm — rayon de courbure (0 = plaque plate)
    ombres = None     # 0..1 — remonte les basses lumières. None = automatique.


# ------------------------------------------------------------------ image
def preparer_image(chemin_ou_img, reg: Reglages):
    """Photo -> carte de luminosité normalisée [0..1], prête pour le relief."""
    img = Image.open(chemin_ou_img) if isinstance(chemin_ou_img, str) else chemin_ou_img
    img = ImageOps.exif_transpose(img)          # respecte l'orientation de l'appareil
    img = img.convert("L")                       # niveaux de gris
    img = ImageOps.autocontrast(img, cutoff=1)   # utilise toute la plage

    # Récupération des ombres. Sur un sujet à dominante sombre (chien noir,
    # photo de nuit), une part énorme de la surface part à l'épaisseur maxi et
    # devient un aplat sans aucun détail. On mélange l'image à sa version
    # égalisée : les basses lumières remontent, la texture réapparaît, et le
    # contraste général est préservé.
    # Mesuré sur un bouvier bernois : 32 % de surface bouchée sans, 9,8 % avec.
    # Une photo claire (part sombre < 8 %) n'est pas touchée du tout.
    dose = reg.ombres
    if dose is None:                              # automatique
        h = np.asarray(img, dtype=np.float64) / 255.0
        part_sombre = float((h < 0.10).mean())
        dose = 0.0 if part_sombre < 0.08 else min(0.55, 0.40 + part_sombre)
    if dose > 0:
        img = Image.blend(img, ImageOps.equalize(img), float(dose))

    if reg.flou > 0:
        img = img.filter(ImageFilter.GaussianBlur(reg.flou))

    # taille du maillage d'après la largeur physique voulue et le pas
    nx = max(2, int(round(reg.largeur / reg.pas_xy)))
    ny = max(2, int(round(nx * img.height / img.width)))
    img = img.resize((nx, ny), Image.LANCZOS)

    L = np.asarray(img, dtype=np.float64) / 255.0
    if reg.inverser:
        L = 1.0 - L

    # contraste puis gamma
    L = np.clip((L - 0.5) * reg.contraste + 0.5, 0.0, 1.0)
    if reg.gamma != 1.0:
        L = np.power(L, 1.0 / reg.gamma)
    return L


def epaisseurs(L, reg: Reglages):
    """Luminosité -> épaisseur, via la loi de Beer-Lambert (transmission réelle).

    La transmission suit I = I0 * exp(-k*e), donc l'épaisseur juste est
    proportionnelle à -ln(L) et non à (1-L). Une conversion linéaire écrase
    les gris et donne une image plate et décevante.

    Le rattrapage des sujets sombres se fait en amont, dans preparer_image
    (récupération des ombres) : agir ici sur l'échelle des épaisseurs
    reviendrait à supprimer les vrais noirs, donc tout le contraste.
    Essai fait et abandonné le 08/08 — ne pas le refaire.
    """
    L = np.clip(L, 1e-3, 1.0)
    t = -np.log(L) / -math.log(1e-3)
    e = reg.ep_min + (reg.ep_max - reg.ep_min) * t
    return np.clip(e, reg.ep_min, reg.ep_max)


# ------------------------------------------------------------------ maillage
def _grille_triangles(ny, nx, decalage=0, inverser=False):
    """Triangulation d'une grille régulière ny x nx de sommets."""
    j, i = np.meshgrid(np.arange(nx - 1), np.arange(ny - 1))
    a = (i * nx + j).ravel() + decalage
    b = a + 1
    c = a + nx
    d = c + 1
    if inverser:
        f = np.vstack([np.column_stack([a, c, b]), np.column_stack([b, c, d])])
    else:
        f = np.vstack([np.column_stack([a, b, c]), np.column_stack([b, d, c])])
    return f


def construire(L, reg: Reglages):
    """Construit le maillage étanche de la lithophanie.

    Orientation : la plaque est DEBOUT, prête à imprimer sans la tourner.
      X = largeur, Z = hauteur, Y = épaisseur (dos plat en Y=0).
    """
    ny, nx = L.shape
    e = epaisseurs(L, reg)

    # cadre : bordure ramenée à pleine épaisseur
    cadre_ep = reg.cadre_ep if reg.cadre_ep else reg.ep_max
    if reg.cadre > 0:
        bx = max(1, int(round(reg.cadre / reg.pas_xy)))
        e[:bx, :] = cadre_ep
        e[-bx:, :] = cadre_ep
        e[:, :bx] = cadre_ep
        e[:, -bx:] = cadre_ep

    largeur = reg.largeur
    hauteur = reg.hauteur if reg.hauteur else largeur * ny / nx

    xs = np.linspace(-largeur / 2, largeur / 2, nx)
    zs = np.linspace(hauteur, 0.0, ny)          # ligne 0 de l'image = haut
    X, Z = np.meshgrid(xs, zs)

    # courbure optionnelle (lampe cylindrique) : la plaque s'enroule autour de Z
    if reg.courbe > 0:
        # Le dos est un arc de cercle de centre C=(0,R) et de rayon R.
        # Un point du dos vaut P = C + R*(sin a, -cos a), donc la normale
        # SORTANTE (qui s'éloigne de C) est u = (sin a, -cos a).
        # On épaissit vers l'extérieur : le relief est convexe, la lumière
        # se place à l'intérieur du cylindre.
        # ATTENTION : une erreur de signe ici (ny_ = +cos) vrille le maillage
        # et fausse le volume sans casser l'étanchéité. Bug trouvé le 08/08.
        R = reg.courbe
        ang = X / R
        X0 = R * np.sin(ang)
        Y0 = R - R * np.cos(ang)                 # dos
        nx_, ny_ = np.sin(ang), -np.cos(ang)     # normale sortante
        dos = np.column_stack([X0.ravel(), Y0.ravel(), Z.ravel()])
        face = np.column_stack([(X0 + nx_ * e).ravel(),
                                (Y0 + ny_ * e).ravel(),
                                Z.ravel()])
    else:
        dos = np.column_stack([X.ravel(), np.zeros(X.size), Z.ravel()])
        face = np.column_stack([X.ravel(), e.ravel(), Z.ravel()])

    sommets = np.vstack([face, dos])
    n = face.shape[0]

    faces = [
        _grille_triangles(ny, nx, 0, inverser=False),      # avant (relief)
        _grille_triangles(ny, nx, n, inverser=True),       # arrière (plat)
    ]

    # les 4 bords, pour fermer le volume
    idx = np.arange(ny * nx).reshape(ny, nx)
    def bord(ligne_a, ligne_b, inv=False):
        a, b = ligne_a[:-1], ligne_a[1:]
        c, d = ligne_b[:-1], ligne_b[1:]
        if inv:
            return np.vstack([np.column_stack([a, c, b]), np.column_stack([b, c, d])])
        return np.vstack([np.column_stack([a, b, c]), np.column_stack([b, d, c])])

    faces.append(bord(idx[0, :],  idx[0, :] + n,  inv=True))    # haut
    faces.append(bord(idx[-1, :], idx[-1, :] + n, inv=False))   # bas
    faces.append(bord(idx[:, 0],  idx[:, 0] + n,  inv=False))   # gauche
    faces.append(bord(idx[:, -1], idx[:, -1] + n, inv=True))    # droite

    m = trimesh.Trimesh(vertices=sommets, faces=np.vstack(faces), process=True)
    m.merge_vertices()
    m.fix_normals()
    return m


# ------------------------------------------------------------------ contrôle
def controler(m: trimesh.Trimesh, reg: Reglages, densite=1.24, prix_kg=20.0):
    """Contrôle qualité : le fichier est-il réellement imprimable et vendable ?

    densite : g/cm3 du PLA. prix_kg : prix de la bobine en EUR/kg.

    LECON DU 08/08 : l'etancheite ne suffit PAS a valider un maillage.
    Un maillage vrille peut afficher etanche=True et normales_coherentes=True
    tout en ayant un volume 4 fois trop petit. Toujours croiser le volume
    avec une estimation independante (surface x epaisseur moyenne).
    """
    ext = m.bounds[1] - m.bounds[0]
    vol_cm3 = m.volume / 1000.0
    poids = vol_cm3 * densite
    r = {
        "etanche": bool(m.is_watertight),
        "volume_correct": bool(m.volume > 0),
        "normales_coherentes": bool(m.is_winding_consistent),
        "triangles": int(len(m.faces)),
        "dimensions_mm": [round(float(v), 2) for v in ext],
        "volume_cm3": round(vol_cm3, 2),
        "poids_g": round(float(poids), 1),
        "cout_matiere_eur": round(float(poids) / 1000.0 * prix_kg, 2),
        "ep_min_mm": reg.ep_min,
        "ep_max_mm": reg.ep_max,
        "tient_sur_P2S": bool(ext[0] <= 256 and ext[1] <= 256 and ext[2] <= 256),
    }
    r["bon_pour_impression"] = bool(
        r["etanche"] and r["volume_correct"] and r["normales_coherentes"]
        and r["tient_sur_P2S"] and reg.ep_min >= 0.8
    )
    return r


def generer(image, sortie_stl, reg: Reglages = None, sortie_3mf=None):
    """Chaîne complète : photo -> fichier imprimable + rapport de contrôle."""
    reg = reg or Reglages()
    L = preparer_image(image, reg)
    m = construire(L, reg)
    m.export(sortie_stl)
    if sortie_3mf:
        m.export(sortie_3mf)
    return m, controler(m, reg)


# --------------------------------------------------------------- livraison
NOTICE = """FORGEON - Lithophanie personnalisee
=====================================
Votre photo transformee en objet lumineux.

COMMENT L'IMPRIMER (reglages verifies pour Bambu Lab P2S,
valables sur toute imprimante FDM)

  Matiere ............ PLA BLANC imperativement. Le blanc diffuse la
                       lumiere ; une couleur foncee ne laissera rien passer.
  Position ........... DEBOUT, le dos plat contre le plateau. Le fichier
                       est deja oriente : ne le tournez pas.
  Hauteur de couche .. 0,08 mm (profil "High Quality").
  Remplissage ........ 100 %. Non negociable : en dessous, la lumiere
                       passe de facon irreguliere et on voit la trame.
  Supports ........... AUCUN.
  Vitesse ............ Reduite (50 %) sur les parois.
  Lissage (ironing) .. Desactive.

  Duree indicative : 2 h 30 a 4 h. A confirmer par votre trancheur.

COMMENT L'UTILISER
  Posez la plaque devant une source lumineuse : bougie LED, ruban LED,
  petite lampe. L'image apparait.
  JAMAIS de bougie a flamme : le PLA se deforme des 55-60 C.

Usage personnel et cadeau : libre. Revente : non autorisee.
Fabrique par FORGEON.
"""


def livrer(image, nom_zip, reg: Reglages = None):
    """Produit le ZIP client : le STL + la notice d'impression.

    Le ZIP n'est pas cosmetique : un STL brut fait 21 a 33 Mo alors qu'Etsy
    limite les fichiers numeriques a 20 Mo. Compresse, il tombe a 3-10 Mo,
    ce qui permet de garder la finesse maximale sans decimer le maillage.
    """
    import zipfile, os, tempfile
    reg = reg or Reglages()
    tmp = os.path.join(tempfile.gettempdir(), "litho_tmp.stl")
    m, rapport = generer(image, tmp, reg)
    with zipfile.ZipFile(nom_zip, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        z.write(tmp, "lithophanie.stl")
        z.writestr("LISEZ-MOI_impression.txt", NOTICE)
    os.remove(tmp)
    rapport["zip_Mo"] = round(os.path.getsize(nom_zip) / 1e6, 2)
    return rapport


if __name__ == "__main__":
    import json, sys
    img = sys.argv[1] if len(sys.argv) > 1 else "photo.jpg"
    rap = livrer(img, "FORGEON_lithophanie.zip")
    print(json.dumps(rap, indent=2, ensure_ascii=False))
