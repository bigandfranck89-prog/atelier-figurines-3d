// Service worker de la page Validation UNIQUEMENT.
//
// Il vit dans /validation/, donc sa portee s'arrete a ce dossier : il ne voit
// jamais les pages de l'application cliente et ne peut pas les perturber.
// Il n'efface aucun cache autre que le sien, contrairement au sw.js de l'app.
//
// Role : (1) permettre au navigateur de proposer l'installation,
//        (2) garder les apercus deja fabriques, pour ne pas les refaire.

const CACHE_IMAGES = "validation-apercus-v1";

self.addEventListener("install", () => self.skipWaiting());

self.addEventListener("activate", (e) => {
  // on ne supprime QUE nos anciennes versions, jamais les caches des autres
  e.waitUntil(
    caches.keys()
      .then((ks) => Promise.all(
        ks.filter((k) => k.startsWith("validation-apercus-") && k !== CACHE_IMAGES)
          .map((k) => caches.delete(k))
      ))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (e) => {
  // Les apercus sont fabriques a la demande et coutent plusieurs secondes :
  // une fois obtenus, on les garde definitivement. On se fie au type de la
  // requete (image) plutot qu'au nom du serveur, pour rester valable si on
  // change un jour de fabricant d'images.
  if (e.request.method === "GET" && e.request.destination === "image") {
    e.respondWith(
      caches.open(CACHE_IMAGES).then((c) =>
        c.match(e.request).then((garde) =>
          garde || fetch(e.request).then((r) => {
            if (r && r.ok) c.put(e.request, r.clone());
            return r;
          })
        )
      )
    );
    return;
  }

  // Tout le reste passe par le reseau, sans mise en cache : aucune surprise.
  e.respondWith(fetch(e.request));
});
