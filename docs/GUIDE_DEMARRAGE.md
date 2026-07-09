# Atelier Figurines 3D — Guide de démarrage (09/07/2026)

Tout est monté en **100 % gratuit** (décision de Franck). Les comptes payants (Meshy Pro, Midjourney…)
se branchent tout à la fin, chacun en changeant UNE valeur de config.

## La chaîne, en clair

```
L'ami (Telegram) ──► n8n « Bot ami » ──► Pollinations.ai (image gratuite, sans compte)
      ▲                    │  boucle de critique/validation de l'IMAGE (boutons Telegram)
      │                    ▼
      │              Meshy (image → 3D)  ◄── clé API à brancher
      │                    │  boucle de critique/validation de la 3D (visionneuse web)
      │                    ▼
      └──── notification « 3D validée » à Franck ──► Bambu Studio ──► fichier .3mf ──► l'ami imprime (P2S)
```

- **Suivi & galerie** : app PWA https://bigandfranck89-prog.github.io/atelier-figurines-3d
- **Mémoire** : tables Supabase `atelier_figurines` + `atelier_iterations` (projet JARVIS)
- **Workflows n8n** : dossier `n8n/` de ce dépôt (2 fichiers JSON à importer)

## Ce que Franck doit faire (une seule fois, ~15 min)

1. **Se reconnecter à n8n** (http://localhost:5678 — la session avait expiré).
2. **Créer le bot Telegram de l'ami** : parler à `@BotFather` → `/newbot` → nom du bot
   (ex. « Atelier Figurines 3D ») → identifiant (ex. `AtelierFigurines3DBot`) → **copier le token**.
3. **Importer les 2 workflows** dans n8n : menu ⋯ → *Import from file* →
   `Atelier_Figurines_3D__Bot_ami.json` puis `Atelier_Figurines_3D__Suivi_Meshy.json`.
4. **Remplir la CONFIG** (en haut du nœud « Relever Telegram » du workflow Bot ami,
   et en haut du nœud du workflow Suivi Meshy) :
   - `TELEGRAM_TOKEN` : le token BotFather
   - `SUPABASE_SERVICE_KEY` : clé *service_role* du projet JARVIS
     (Supabase → Settings → API → `service_role`)
   - `FRANCK_CHAT_ID` : ton chat_id Telegram (le même que pour Alfred)
   - `MESHY_KEY` : à laisser « A_REMPLIR » tant que le compte Meshy n'existe pas —
     le bot fonctionne quand même (il s'arrête proprement après l'image validée et te prévient)
5. **Activer** les 2 workflows (interrupteur en haut à droite).
6. **Créer le compte Meshy gratuit** (meshy.ai → Sign up) quand tu veux brancher la 3D :
   récupérer la clé API (Settings → API Keys) → la coller dans `MESHY_KEY` des 2 workflows.
7. Donner le lien du bot à l'ami + lui installer l'app (elle est déjà en ligne).

## Choix du générateur d'images

- **V1 (branchée)** : Pollinations.ai, modèle **Flux** — gratuit, sans compte, sans clé.
- **Banc d'essai qualité** : ouvrir `comparatif.html` dans l'app — le même prompt part sur
  plusieurs moteurs, tu juges sur pièces avec l'ami.
- **Si qualité insuffisante** : Google AI Studio (Imagen, gratuit avec clé à créer par Franck) —
  se branche en changeant la fonction `urlImage` du workflow. Payant (Midjourney/DALL·E) : à la fin.

## Le fichier d'impression (.3mf) — étape manuelle pour l'instant

Quand l'ami valide une 3D, tu reçois le lien du modèle (.glb) sur Telegram :
1. Télécharger le .glb (⚠️ les liens Meshy **expirent** — télécharger dans la journée).
2. Ouvrir dans **Bambu Studio**, profil **P2S** : plateau 256×256×256, buse 0,4,
   couche 0,16 mm, supports « arbre » si surplombs, remplissage 15 %.
3. Redimensionner (~12-15 cm de haut en général), trancher, **exporter en .3mf**
   (les réglages sont embarqués) et l'envoyer à l'ami.
4. Après impression : noter poids/temps réels → onglet **Calculs** de l'app pour le coût,
   et reporter dans la fiche Supabase (colonnes `poids_g`, `temps_impression_min`, `cout_total_eur`).

## Règles à ne pas oublier

- **PERSO** : tout est permis (licences incluses) — le bot rappelle automatiquement
  « interdit à la vente » quand il détecte un personnage sous licence.
- **VENTE** : créations originales uniquement, jamais à perte (prix ≥ coût × 3),
  rien de publié sans le OUI de Franck, pas de produits pour enfants.
- On n'attend **jamais** 6 figurines pour lancer une impression.

## Où sont les affaires

| Quoi | Où |
|---|---|
| App (PWA) | https://bigandfranck89-prog.github.io/atelier-figurines-3d |
| Code + workflows | https://github.com/bigandfranck89-prog/atelier-figurines-3d |
| Pipeline (données) | Supabase JARVIS → `atelier_figurines`, `atelier_iterations` |
| Tâches du projet | Supabase → `taches_claude` (projet = 'Atelier Figurines 3D') |
| Docs de juin (13 fichiers) | PC fixe (le ZIP Gmail est bloqué par Google) |
