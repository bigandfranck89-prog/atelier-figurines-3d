/* Réglages du 13/08/2026 — petit fichier de correctifs, chargé après js/app.js.
   Il ne réécrit rien : il ajuste trois choses et s'efface s'il plante. */
(function () {
  try {
    // 1) Remplissage des objets de déco : 12 % -> 10 % (l'étude dit 5 à 10 %).
    if (typeof USAGES !== "undefined" && USAGES.deco) USAGES.deco.dens = 10;

    // 2) L'imprimante par défaut n'est plus la P2S de l'ami : on achète une A1.
    if (!localStorage.getItem("atelier_imprimante")) {
      localStorage.setItem("atelier_imprimante", "a1");
    }

    // 3) Sur grand écran, la 3D à gauche et le chat à droite, en pleine hauteur.
    //    Sur téléphone, rien ne change : la 3D en haut, le chat dessous.
    var css = document.createElement("style");
    css.textContent =
      "@media (min-width:900px){" +
      ".v3wrap{display:grid;grid-template-columns:1fr 340px;grid-template-rows:auto 1fr;column-gap:10px}" +
      ".v3wrap .v3top{grid-column:1/-1}" +
      ".v3wrap iframe{grid-column:1;grid-row:2}" +
      ".v3wrap .v3chat{grid-column:2;grid-row:2;border-top:0;border-left:1px solid #23262e;height:100%}" +
      ".v3wrap .v3chat .msgs{flex:1 1 auto;max-height:none;overflow-y:auto}" +
      "}";
    document.head.appendChild(css);
  } catch (e) {
    console.warn("reglages-2026-08-13 :", e);
  }
})();
