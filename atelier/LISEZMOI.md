# Atelier Forgeon — code de génération des objets (sauvegarde du 14/08/2026)

Tout objet et tout plateau d'impression se REGÉNÈRE depuis ce dossier :

    pip install trimesh shapely numpy matplotlib pillow manifold3d
    python3 plateau_salon3.py    # plateau 1 « salon » (7 objets personnalisés) -> .3mf + rendus
    python3 plateau_deco.py      # plateau 2 « utile & déco » (6 objets) -> .3mf + rendus
    python3 planches_pres.py     # les 2 planches de présentation soignées
    python3 plaques_race2.py     # les 8 plaques de niche individuelles
    python3 complements.py       # PK-01, MD-01, DC-01, ST-01 individuels

Les contours de silhouettes (svg_races/*.json) viennent de dessins DOMAINE PUBLIC :
freesvg.org fichier 190785 (planche 20 races, OpenClipart) et 177950 (chien assis).
Vente autorisée, pas d'attribution exigée.

Noms des chiens d'Angélique utilisés : Ulysse, Olympe, Stella, Vénus, Yuzu
(4 golden retrievers + 1 hovawart).

Couleurs AMS (4 bobines) : bois clair #d8c49a · brun chocolat #4a3826 ·
noir mat #24242a · blanc crème #f2ede2.

Non sauvegardés ici (régénérables ou obsolètes) : races.py/plaques_race.py (v1
moche, abandonnée), catalogue_builder.py, page_angelique.py (la page est en ligne
dans /catalogue/plaques.html), deco_couleurs.py (remplacé par bandes.py),
rendus_catalogue.py::lampe (la vraie lampe = fonction serveur lithophanie+socle).
"""
