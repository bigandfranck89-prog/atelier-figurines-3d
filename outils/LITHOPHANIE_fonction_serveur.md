# Lithophanie — fonction serveur

La logique de `lithophanie.py` (référence algorithmique, dans ce même dossier) a été
portée en fonction serveur Supabase le 09/08/2026. Elle tourne 24 h/24 : ni PC allumé,
ni crédit d'IA, ni moteur 3D.

## Appel

```
POST https://bmvytqfddrfgcgokoxfn.supabase.co/functions/v1/lithophanie
Content-Type: application/json

{
  "image_url": "https://…/photo.jpg",   // ou "image_base64": "…"
  "largeur_mm": 100,                     // 30 à 220
  "session": "app_xxx"                   // sert à nommer le fichier
}
```

Réglages optionnels : `ep_min` (0,6 à 2,0 — défaut 0,8), `ep_max` (défaut 3,0),
`cadre_mm` (défaut 3,0), `points_larg` (60 à 320 — défaut 250), `contraste`
(défaut 1,15), `ombres` (0 à 1, `null` = dose automatique).

## Réponse

```json
{
  "ok": true,
  "url": "https://…/storage/v1/object/public/atelier/lithophanies/xxx.stl",
  "controle": {
    "triangles": 249996, "dimensions_mm": [100, 3, 100],
    "volume_cm3": 11.47, "poids_g": 14.2, "cout_matiere_eur": 0.28,
    "pct_bouche": 13.7, "pct_crame": 62.6, "ombres_appliquees": 0,
    "tient_sur_P2S": true, "fichier_Mo": 12.5, "millisecondes": 72
  },
  "impression": { "matiere": "PLA BLANC obligatoire", "couche_mm": 0.08, "remplissage_pct": 100, "supports": "aucun" }
}
```

En cas d'échec, la fonction répond **200** avec `{ ok: false, erreur, etapes }` —
voir « pièges » ci-dessous.

## Mesures réelles (tests du 09/08)

| Test | Dimensions | Matière | Fichier | Temps |
|---|---|---|---|---|
| Plaque 100 mm | 100 × 100 mm | 14,2 g — 0,28 € | 12,5 Mo | 72 ms |
| Plaque 150 mm | 150 × 150 mm | 29,5 g — 0,59 € | 12,5 Mo | 72 ms |

Vérification indépendante : la taille réelle du fichier déposé (12 499 884 octets)
correspond exactement à `84 + 249 996 × 50`, la formule du STL binaire.

## Trois pièges, pour toute future fonction serveur de ce projet

**1. Les clés Supabase ne sont plus des JWT.**
`SUPABASE_SERVICE_ROLE_KEY` vaut `sb_secret_…` et `SUPABASE_ANON_KEY` vaut
`sb_publishable_…`. L'API storage refuse alors un simple en-tête `Authorization`
(403 « Invalid Compact JWS ») : il faut envoyer **aussi** l'en-tête `apikey` avec
la même valeur.

**2. Le relais n8n n'expose pas le corps des réponses en erreur.**
Il ne renvoie que « Request failed with status code 400 ». Une fonction appelée par
le relais doit donc répondre **200 avec `{ok:false, erreur, etapes}`**, sinon le
diagnostic à distance est impossible. Le tableau `etapes` (image décodée, grille,
pixels lus, épaisseurs, triangles) permet de localiser une panne en un seul essai.

**3. Depuis le cloud, on ne peut pas appeler la fonction directement.**
Le bac à sable de Claude n'atteint ni `supabase.co` ni `fal.media` (403 du proxy).
Le seul chemin est le relais :

```sql
INSERT INTO public.file_travaux (projet, type, payload, statut) VALUES
('Atelier Figurines 3D', 'http',
 '{"method":"POST","url":"…/functions/v1/lithophanie",
   "headers":{"Content-Type":"application/json"},
   "body":{"image_url":"…","largeur_mm":100}}'::jsonb, 'a_faire');
-- puis relire la colonne resultat environ 80 secondes plus tard
```

## Reste à faire

Brancher l'appel dans l'app (`index.html`) : choisir une photo, choisir la taille,
appeler la fonction, afficher l'aperçu et le lien. Ne jamais faire transiter le
fichier (12 Mo) par la base — seulement son lien.
