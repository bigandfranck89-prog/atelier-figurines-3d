/* =====================================================================
   Onglet « Validation » de l'application Atelier Figurines 3D.

   Ce fichier est charge a la demande par index.html (au premier clic sur
   l'onglet) et dessine tout le contenu dans #valid-zone.

   Il vit ici, et pas dans index.html, pour une raison pratique : index.html
   fait plus de 100 000 caracteres et ne peut etre republie qu'en entier.
   Toute correction de la validation se fait donc dans ce petit fichier,
   sans jamais risquer d'abimer l'application cliente.

   Il attend de index.html :
     - window.SUPA_URL   adresse Supabase
     - window.authH()    en-tetes d'authentification
     - window.verdictEp(mm)      (facultatif) phrase de verdict d'epaisseur
     - window.mesurerSolidite()  (facultatif) mesure sur le vrai fichier 3D
   ===================================================================== */
(function () {
  "use strict";

  var PAR_PAGE = 12;          // on n'affiche pas 90 cartes d'un coup
  var IMG_PARALLELE = 2;      // les apercus sont fabriques a la demande :
  var IMG_TIMEOUT = 30000;    // au-dela de 2 a la fois, le service abandonne.

  var toutes = [], affichees = 0, file = [], enCours = 0, dejaRetente = {};

  function $(id) { return document.getElementById(id); }

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }

  function base() { return window.SUPA_URL || ""; }
  function entetes() {
    return (typeof window.authH === "function")
      ? window.authH()
      : { "Content-Type": "application/json" };
  }

  function verdict(mm) {
    if (typeof window.verdictEp === "function") return window.verdictEp(mm);
    mm = Number(mm);
    if (mm >= 3) return '<span style="color:#5be3a5">✅ Mesuré : ' + mm.toFixed(1) + ' mm (≥ 3 mm partout).</span>';
    if (mm >= 1.5) return '<span style="color:#ffcf7a">🟠 Mesuré : ' + mm.toFixed(1) + ' mm — fragile.</span>';
    return '<span style="color:#ff9aa4">🔴 Mesuré : ' + mm.toFixed(1) + ' mm — casserait.</span>';
  }

  function phraseCompteur() {
    var n = toutes.length;
    var t = '<b style="color:#e6edf3">' + n + '</b> proposition' + (n > 1 ? 's' : '') + ' en attente de ton choix.';
    if (n > affichees) t += ' <span style="color:#7ea6ff">' + affichees + ' affichée' + (affichees > 1 ? 's' : '') + '.</span>';
    return t;
  }

  /* ---------- file d'attente des apercus ----------
     Chaque image est fabriquee a la demande et prend plusieurs secondes.
     En reclamer 90 d'un coup revenait a n'en obtenir que deux ou trois. */

  function allegerUrl(u) {
    // 768 px est inutile sur un telephone, et deux fois plus long a fabriquer
    return String(u).replace(/([?&])width=\d+/, "$1width=512")
                    .replace(/([?&])height=\d+/, "$1height=512");
  }

  function nouveauGrain(u) {
    return String(u).replace(/([?&])seed=\d+/, "$1seed=" + Math.floor(Math.random() * 999999));
  }

  function enfiler(id, url) { file.push({ id: id, url: url }); pomper(); }

  function pomper() {
    while (enCours < IMG_PARALLELE && file.length) {
      var t = file.shift();
      if (!$("vv" + t.id)) continue;      // carte plus affichee
      enCours++;
      charger1(t.id, t.url, false);
    }
  }

  // horsFile : relance demandee par Franck, elle ne doit pas attendre son tour
  function charger1(id, url, horsFile) {
    var zone = $("vv" + id);
    if (!zone) { if (!horsFile) { enCours--; pomper(); } return; }
    var fini = false;
    var img = new Image();
    function libere() { if (!horsFile) { enCours--; pomper(); } }

    var minuteur = setTimeout(function () {
      if (fini) return;
      fini = true; img.src = "";
      echec(id, url, "L'aperçu met trop de temps à se fabriquer.");
      libere();
    }, IMG_TIMEOUT);

    img.onload = function () {
      if (fini) return;
      fini = true; clearTimeout(minuteur);
      var z = $("vv" + id);
      if (z) {
        img.style.cssText = "width:100%;display:block;max-height:280px;object-fit:contain";
        z.innerHTML = ""; z.appendChild(img);
      }
      libere();
    };
    img.onerror = function () {
      if (fini) return;
      fini = true; clearTimeout(minuteur);
      // la plupart des echecs sont des fabrications abandonnees en route :
      // on retente une fois tout seul avant d'embeter Franck. La relance
      // repasse par la file : sinon plusieurs echecs simultanes relanceraient
      // tous en meme temps et on retomberait dans l'engorgement d'origine.
      if (!horsFile && !dejaRetente[id]) {
        dejaRetente[id] = 1;
        var u2 = nouveauGrain(url);
        libere();
        setTimeout(function () { file.unshift({ id: id, url: u2 }); pomper(); }, 600);
        return;
      }
      echec(id, url, "L'aperçu n'a pas pu être fabriqué.");
      libere();
    };
    img.alt = "";
    img.src = url;
  }

  function attente() {
    return '<div style="padding:24px 12px;text-align:center;color:#9aa0a6;font-size:13px">' +
           'Aperçu en préparation…</div>';
  }

  function echec(id, url, msg) {
    var z = $("vv" + id);
    if (!z) return;
    z.setAttribute("data-url", url);
    z.innerHTML = '<div style="padding:22px 12px;text-align:center;color:#9aa0a6;font-size:13px;line-height:1.5">' +
      '🖼️ ' + esc(msg) + '<br>Tu peux décider avec le texte.' +
      '<br><button class="abtn sec" style="margin-top:8px" onclick="validationRelancerImg(' + id + ')">' +
      '🔄 Réessayer l\'aperçu</button></div>';
  }

  window.validationRelancerImg = function (id) {
    var z = $("vv" + id); if (!z) return;
    var url = z.getAttribute("data-url"); if (!url) return;
    z.innerHTML = attente();
    charger1(id, nouveauGrain(url), true);   // immediat, sans passer par la file
  };

  /* ---------- rendu ---------- */

  function carte(p) {
    var vign = p.image_url
      ? '<div id="vv' + p.id + '" style="background:#0f1115;min-height:150px;display:flex;' +
        'align-items:center;justify-content:center">' + attente() + '</div>'
      : '';
    var mesure = p.model_url
      ? '<button class="abtn sec" style="flex:1;min-width:130px" onclick="mesurerSolidite(' + p.id +
        ',\'' + esc(p.model_url) + '\')">📏 Vérifier la solidité</button>'
      : '<span class="abtn dis" style="flex:1;min-width:130px">📏 Pas encore de 3D</span>';
    return '<div class="card" style="flex-direction:column;align-items:stretch" id="prop-' + p.id + '">' +
      '<div id="ev' + p.id + '"></div>' + vign +
      '<div style="padding:4px 2px">' +
        '<div class="t">' + esc(p.nom || "Sans nom") +
          (p.categorie ? ' · <span style="color:#9aa0a6">' + esc(p.categorie) + '</span>' : '') + '</div>' +
        '<div class="s">' + esc(p.description || "") + '</div>' +
        (p.regles_solidite ? '<div class="al info" style="margin-top:6px">🛡️ Règles solidité : ' +
          esc(p.regles_solidite) + '</div>' : '') +
        '<div id="ep-' + p.id + '" style="font-size:13px;margin-top:6px;color:#9aa0a6">' +
          (p.epaisseur_min_mm != null ? verdict(p.epaisseur_min_mm)
            : '📏 Épaisseur pas encore mesurée (pas de fichier 3D).') + '</div>' +
      '</div>' +
      '<div style="display:flex;gap:8px;margin-top:8px;flex-wrap:wrap">' + mesure +
        '<button class="abtn vert" style="flex:1;min-width:110px" onclick="deciderProp(' + p.id + ',\'garde\')">✅ Garder</button>' +
        '<button class="abtn sec" style="flex:1;min-width:110px" onclick="deciderProp(' + p.id + ',\'rejete\')">✖️ Rejeter</button>' +
      '</div></div>';
  }

  function ajouterPage() {
    var lot = toutes.slice(affichees, affichees + PAR_PAGE);
    $("valid-liste").insertAdjacentHTML("beforeend", lot.map(carte).join(""));
    lot.forEach(function (p) { if (p.image_url) enfiler(p.id, allegerUrl(p.image_url)); });
    affichees += lot.length;
    majEntete();
  }
  window.validationPageSuivante = ajouterPage;

  function majEntete() {
    var c = $("valid-cpt"); if (c) c.innerHTML = phraseCompteur();
    var s = $("valid-suite"); if (!s) return;
    var reste = toutes.length - affichees;
    s.innerHTML = reste > 0
      ? '<button class="abtn sec" style="width:100%" onclick="validationPageSuivante()">' +
        'Voir les ' + Math.min(PAR_PAGE, reste) + ' suivantes (' + reste + ' restantes)</button>'
      : '';
  }

  window.chargerValidation = function () {
    var zone = $("valid-zone"); if (!zone) return;
    toutes = []; affichees = 0; file = []; enCours = 0; dejaRetente = {};
    zone.innerHTML = '<p style="color:#9aa0a6;padding:14px">Chargement des propositions…</p>';

    fetch(base() + "/rest/v1/catalogue_propositions?statut=eq.propose&order=cree_le.desc&limit=500",
          { headers: entetes() })
      .then(function (r) { if (!r.ok) throw new Error("HTTP " + r.status); return r.json(); })
      .then(function (rows) {
        toutes = Array.isArray(rows) ? rows : [];
        if (!toutes.length) {
          zone.innerHTML = '<p style="color:#9aa0a6;padding:14px">Aucune proposition en attente. ' +
            'Le générateur du catalogue en dépose de nouvelles chaque jour.</p>';
          return;
        }
        zone.innerHTML = '<div id="valid-cpt" style="padding:2px 12px 10px;color:#9aa0a6;font-size:13px"></div>' +
                         '<div id="valid-liste"></div>' +
                         '<div id="valid-suite" style="margin:6px 2px 22px"></div>';
        ajouterPage();
      })
      .catch(function () {
        zone.innerHTML = '<p style="color:#ff9aa4;padding:14px">Impossible de charger les propositions ' +
          '(connexion ?).<br><button class="abtn sec" style="margin-top:10px" ' +
          'onclick="chargerValidation()">Réessayer</button></p>';
      });
  };

  window.deciderProp = function (id, decision) {
    var etat = $("ev" + id), carteEl = $("prop-" + id);
    if (etat) etat.innerHTML = '<div style="padding:6px 2px;font-size:13px;color:#9aa0a6">Enregistrement…</div>';
    fetch(base() + "/rest/v1/catalogue_propositions?id=eq." + id, {
      method: "PATCH",
      headers: Object.assign({}, entetes(), { Prefer: "return=minimal" }),
      body: JSON.stringify({ statut: decision, decide_le: new Date().toISOString() })
    })
    .then(function (r) {
      if (!r.ok) throw new Error("HTTP " + r.status);
      if (carteEl) { carteEl.style.opacity = ".45"; carteEl.style.pointerEvents = "none"; }
      if (etat) etat.innerHTML = '<div style="padding:6px 2px;font-size:13px;color:' +
        (decision === "garde" ? "#5be3a5" : "#9aa0a6") + '">' +
        (decision === "garde" ? "✅ Gardée — elle part au catalogue." : "✖️ Rejetée.") + '</div>';
      for (var i = 0; i < toutes.length; i++) {
        if (toutes[i].id === id) { toutes.splice(i, 1); affichees--; break; }
      }
      majEntete();
    })
    .catch(function () {
      // ne jamais laisser croire que c'est enregistre
      if (etat) etat.innerHTML = '<div style="padding:6px 2px;font-size:13px;color:#ff9aa4">' +
        '⚠️ Pas enregistré (connexion ?). Réessaie.</div>';
    });
  };

  // si l'onglet a ete ouvert avant que ce fichier soit arrive, on dessine
  if (document.getElementById("valid-zone") && window.__validationAttendue) {
    window.__validationAttendue = false;
    window.chargerValidation();
  }
})();
