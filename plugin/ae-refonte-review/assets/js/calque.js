/* ============================================================
   Calque de relecture — parcours + annotations.

   Chargé uniquement sur les URL /refonte/, et uniquement pour un
   compte qui a la capacité de lecture : ce fichier n'est jamais
   servi à un visiteur du site en ligne.
   ============================================================ */
(function () {
  'use strict';

  var noeudConfig = document.getElementById('ae-refonte-config');
  if (!noeudConfig) { return; }

  var CFG;
  try {
    CFG = JSON.parse(noeudConfig.textContent);
  } catch (e) {
    return;
  }

  /* ---------------------------------------------------------- */
  /* Accès à l'API                                              */
  /* ---------------------------------------------------------- */

  function api(chemin, options) {
    options = options || {};
    var entetes = { 'X-WP-Nonce': CFG.nonce };
    if (!(options.body instanceof FormData)) {
      entetes['Content-Type'] = 'application/json';
    }
    return fetch(CFG.racine + chemin, {
      method: options.method || 'GET',
      credentials: 'same-origin',
      headers: entetes,
      body: options.body instanceof FormData ? options.body
        : (options.body ? JSON.stringify(options.body) : undefined)
    }).then(function (r) {
      return r.json().then(function (donnees) {
        if (!r.ok) {
          throw new Error((donnees && donnees.message) || 'Erreur ' + r.status);
        }
        return donnees;
      });
    });
  }

  /* ---------------------------------------------------------- */
  /* Petits utilitaires                                         */
  /* ---------------------------------------------------------- */

  function el(balise, classe, texte) {
    var n = document.createElement(balise);
    if (classe) { n.className = classe; }
    if (texte !== undefined) { n.textContent = texte; }
    return n;
  }

  function echapper(chaine) {
    var n = document.createElement('div');
    n.textContent = chaine == null ? '' : String(chaine);
    return n.innerHTML;
  }

  function ralentir(fn, delai) {
    var t;
    return function () {
      var args = arguments, ctx = this;
      clearTimeout(t);
      t = setTimeout(function () { fn.apply(ctx, args); }, delai);
    };
  }

  /**
   * Chemin CSS d'un élément, depuis <body>, en nth-of-type.
   * Un identifiant, quand il existe, coupe court : il est stable
   * même si la maquette est réordonnée.
   */
  function selecteurDe(cible) {
    if (!cible || cible === document.body) { return 'body'; }
    if (cible.id) { return '#' + CSS.escape(cible.id); }

    var morceaux = [];
    var noeud = cible;

    while (noeud && noeud !== document.body && noeud.nodeType === 1) {
      if (noeud.id) {
        morceaux.unshift('#' + CSS.escape(noeud.id));
        return morceaux.join(' > ');
      }
      var balise = noeud.nodeName.toLowerCase();
      var rang = 1;
      var frere = noeud;
      while ((frere = frere.previousElementSibling)) {
        if (frere.nodeName === noeud.nodeName) { rang++; }
      }
      morceaux.unshift(balise + ':nth-of-type(' + rang + ')');
      noeud = noeud.parentElement;
    }

    morceaux.unshift('body');
    return morceaux.join(' > ');
  }

  /** Retrouve l'élément d'une demande : par sélecteur, sinon par son texte. */
  function resoudre(note) {
    if (note.selecteur) {
      try {
        var trouve = document.querySelector(note.selecteur);
        if (trouve && !trouve.closest('.aer-racine')) { return trouve; }
      } catch (e) { /* sélecteur devenu invalide : on tente l'ancre */ }
    }
    if (note.ancre) {
      var candidats = document.body.querySelectorAll('h1,h2,h3,h4,p,li,td,th,a,button,span,img,figcaption');
      for (var i = 0; i < candidats.length; i++) {
        if (candidats[i].closest('.aer-racine')) { continue; }
        var texte = (candidats[i].textContent || '').trim().slice(0, 80);
        if (texte && texte === note.ancre) { return candidats[i]; }
      }
    }
    return null;
  }

  /** Résumé lisible d'un élément, pour l'afficher dans le composeur. */
  function decrire(cible) {
    var balise = cible.nodeName.toLowerCase();
    if (balise === 'img') { return 'Image · ' + (cible.getAttribute('alt') || cible.getAttribute('src') || '').slice(0, 70); }
    var texte = (cible.textContent || '').trim().replace(/\s+/g, ' ');
    return texte ? texte.slice(0, 90) + (texte.length > 90 ? '…' : '') : '<' + balise + '>';
  }

  /* ---------------------------------------------------------- */
  /* État                                                        */
  /* ---------------------------------------------------------- */

  var etat = {
    notes: [],
    filtre: 'ouvertes',
    annote: false,
    cible: null,
    visee: 0
  };

  var racine = el('div', 'aer-racine');
  document.body.appendChild(racine);

  /* ---------------------------------------------------------- */
  /* Barre de parcours                                          */
  /* ---------------------------------------------------------- */

  var barre = el('div', 'aer-barre');
  var index = CFG.parcours.findIndex(function (p) { return p.id === CFG.maquette; });

  var btnPrec = el('button', 'aer-cachable', '‹ Précédente');
  var choix = document.createElement('select');
  CFG.parcours.forEach(function (p) {
    var opt = document.createElement('option');
    opt.value = p.url;
    opt.textContent = p.titre + (p.ouverte ? ' (' + p.ouverte + ')' : '');
    if (p.id === CFG.maquette) { opt.selected = true; }
    choix.appendChild(opt);
  });
  var btnSuiv = el('button', 'aer-cachable', 'Suivante ›');

  btnPrec.disabled = index <= 0;
  btnSuiv.disabled = index < 0 || index >= CFG.parcours.length - 1;
  btnPrec.addEventListener('click', function () { location.href = CFG.parcours[index - 1].url; });
  btnSuiv.addEventListener('click', function () { location.href = CFG.parcours[index + 1].url; });
  choix.addEventListener('change', function () { location.href = choix.value; });

  var etatBadge = el('span', 'aer-etat aer-cachable', CFG.etats[CFG.etat] || CFG.etat);
  etatBadge.setAttribute('data-etat', CFG.etat);

  var btnAnnoter = el('button', '', 'Annoter');
  var btnListe = el('button', '', 'Demandes');
  var pastille = el('span', 'aer-pastille', '0');
  btnListe.appendChild(pastille);

  barre.appendChild(btnPrec);
  barre.appendChild(choix);
  barre.appendChild(btnSuiv);
  barre.appendChild(el('span', 'aer-barre__sep'));
  barre.appendChild(etatBadge);
  if (CFG.peutAnnoter) { barre.appendChild(btnAnnoter); }
  barre.appendChild(btnListe);

  if (CFG.peutGerer) {
    var selEtat = document.createElement('select');
    Object.keys(CFG.etats).forEach(function (cle) {
      var o = document.createElement('option');
      o.value = cle;
      o.textContent = CFG.etats[cle];
      if (cle === CFG.etat) { o.selected = true; }
      selEtat.appendChild(o);
    });
    selEtat.className = 'aer-cachable';
    selEtat.addEventListener('change', function () {
      api('/maquettes/' + CFG.maquette, { method: 'PATCH', body: { etat: selEtat.value } })
        .then(function (r) {
          etatBadge.textContent = CFG.etats[r.etat] || r.etat;
          etatBadge.setAttribute('data-etat', r.etat);
        })
        .catch(function (e) { window.alert(e.message); });
    });
    barre.appendChild(selEtat);
  }

  racine.appendChild(barre);

  /* ---------------------------------------------------------- */
  /* Panneau latéral                                            */
  /* ---------------------------------------------------------- */

  var panneau = el('aside', 'aer-panneau');
  panneau.setAttribute('data-ouvert', '0');

  var tete = el('div', 'aer-panneau__tete');
  tete.appendChild(el('strong', '', 'Demandes sur cette page'));
  var btnFermer = el('button', 'aer-panneau__fermer', '✕');
  btnFermer.setAttribute('aria-label', 'Fermer le panneau');
  tete.appendChild(btnFermer);
  panneau.appendChild(tete);

  var filtres = el('div', 'aer-filtres');
  [['ouvertes', 'À traiter'], ['toutes', 'Toutes'], ['traitee', 'Traitées']].forEach(function (paire) {
    var b = el('button', '', paire[1]);
    b.setAttribute('aria-pressed', paire[0] === etat.filtre ? 'true' : 'false');
    b.addEventListener('click', function () {
      etat.filtre = paire[0];
      filtres.querySelectorAll('button').forEach(function (x) { x.setAttribute('aria-pressed', 'false'); });
      b.setAttribute('aria-pressed', 'true');
      dessinerListe();
    });
    filtres.appendChild(b);
  });
  panneau.appendChild(filtres);

  var corps = el('div', 'aer-panneau__corps');
  panneau.appendChild(corps);
  racine.appendChild(panneau);

  function ouvrirPanneau(ouvert) {
    panneau.setAttribute('data-ouvert', ouvert ? '1' : '0');
    btnListe.classList.toggle('aer-actif', !!ouvert);
  }
  btnFermer.addEventListener('click', function () { ouvrirPanneau(false); });
  btnListe.addEventListener('click', function () {
    ouvrirPanneau(panneau.getAttribute('data-ouvert') !== '1');
  });

  /* ---------------------------------------------------------- */
  /* Épingles                                                   */
  /* ---------------------------------------------------------- */

  var coucheEpingles = el('div', 'aer-epingles');
  racine.appendChild(coucheEpingles);

  function placerEpingles() {
    coucheEpingles.innerHTML = '';
    var visibles = notesVisibles();

    visibles.forEach(function (note, rang) {
      var cible = resoudre(note);
      if (!cible) { return; }

      var boite = cible.getBoundingClientRect();
      if (!boite.width && !boite.height) { return; }

      var bouton = el('button', 'aer-epingle', String(rang + 1));
      bouton.setAttribute('data-statut', note.statut);
      bouton.setAttribute('data-note', note.id);
      bouton.title = note.message.slice(0, 120);
      bouton.style.left = (boite.left + window.scrollX + boite.width * (note.x || 0.5)) + 'px';
      bouton.style.top = (boite.top + window.scrollY + boite.height * (note.y || 0.5)) + 'px';
      if (note.id === etat.visee) { bouton.classList.add('aer-vise'); }

      bouton.addEventListener('click', function (ev) {
        ev.preventDefault();
        ev.stopPropagation();
        viser(note.id, false);
      });

      coucheEpingles.appendChild(bouton);
    });
  }

  var replacer = ralentir(placerEpingles, 120);
  window.addEventListener('resize', replacer);
  window.addEventListener('load', replacer);
  document.addEventListener('toggle', replacer, true); // les <details> de la maquette

  /* ---------------------------------------------------------- */
  /* Liste des demandes                                         */
  /* ---------------------------------------------------------- */

  function notesVisibles() {
    return etat.notes.filter(function (n) {
      if (etat.filtre === 'toutes') { return true; }
      if (etat.filtre === 'traitee') { return n.statut === 'traitee' || n.statut === 'refusee'; }
      return n.statut === 'ouverte' || n.statut === 'en_cours';
    });
  }

  function dessinerListe() {
    corps.innerHTML = '';
    var visibles = notesVisibles();

    var ouvertes = etat.notes.filter(function (n) {
      return n.statut === 'ouverte' || n.statut === 'en_cours';
    }).length;
    pastille.textContent = String(ouvertes);
    pastille.setAttribute('data-zero', ouvertes ? '0' : '1');

    if (!visibles.length) {
      corps.appendChild(el('p', 'aer-vide',
        etat.notes.length ? 'Rien dans ce filtre.'
          : 'Aucune demande sur cette page. Cliquez sur « Annoter », puis sur l\'élément à changer.'));
      placerEpingles();
      return;
    }

    visibles.forEach(function (note, rang) {
      corps.appendChild(fiche(note, rang + 1));
    });
    placerEpingles();
  }

  function fiche(note, rang) {
    var carte = el('article', 'aer-note');
    carte.id = 'ae-note-' + note.id;
    if (note.id === etat.visee) { carte.classList.add('aer-vise'); }

    var enTete = el('div', 'aer-note__tete');
    enTete.appendChild(el('span', 'aer-note__num', String(rang)));
    enTete.appendChild(el('span', 'aer-note__type', CFG.types[note.type] || note.type));
    enTete.appendChild(el('span', 'aer-note__meta',
      note.auteur + ' · ' + (CFG.statuts[note.statut] || note.statut)));
    carte.appendChild(enTete);

    if (note.ancre) {
      carte.appendChild(el('p', 'aer-note__ancre', '« ' + note.ancre + ' »'));
    }

    carte.appendChild(el('p', 'aer-note__message', note.message));

    if (note.valeur) {
      var valeur = el('p', 'aer-note__valeur');
      if (note.type === 'couleur') {
        var puce = el('span', 'aer-puce-couleur');
        puce.style.background = note.valeur;
        valeur.appendChild(puce);
        valeur.appendChild(document.createTextNode('Couleur proposée : ' + note.valeur));
      } else {
        valeur.innerHTML = '<b>Proposition :</b> ' + echapper(note.valeur);
      }
      carte.appendChild(valeur);
    }

    if (note.media) {
      var img = document.createElement('img');
      img.className = 'aer-note__media';
      img.src = note.media;
      img.alt = 'Image proposée';
      img.loading = 'lazy';
      carte.appendChild(img);
    }

    note.reponses.forEach(function (rep) {
      var r = el('p', 'aer-reponse');
      r.innerHTML = '<b>' + echapper(rep.auteur) + ' :</b> ' + echapper(rep.message);
      carte.appendChild(r);
    });

    var pied = el('div', 'aer-note__pied');

    var btnAller = el('button', '', 'Voir sur la page');
    btnAller.addEventListener('click', function () { viser(note.id, true); });
    pied.appendChild(btnAller);

    var btnRep = el('button', '', 'Répondre');
    btnRep.addEventListener('click', function () {
      var message = window.prompt('Votre réponse :');
      if (!message) { return; }
      api('/notes/' + note.id + '/reponses', { method: 'POST', body: { message: message } })
        .then(charger)
        .catch(function (e) { window.alert(e.message); });
    });
    pied.appendChild(btnRep);

    if (CFG.peutGerer) {
      var sel = document.createElement('select');
      Object.keys(CFG.statuts).forEach(function (cle) {
        var o = document.createElement('option');
        o.value = cle;
        o.textContent = CFG.statuts[cle];
        if (cle === note.statut) { o.selected = true; }
        sel.appendChild(o);
      });
      sel.addEventListener('change', function () {
        api('/notes/' + note.id, { method: 'PATCH', body: { statut: sel.value } })
          .then(charger)
          .catch(function (e) { window.alert(e.message); });
      });
      pied.appendChild(sel);
    }

    if (CFG.peutGerer || note.auteur_id === CFG.moi.id) {
      var btnSuppr = el('button', 'aer-danger', 'Supprimer');
      btnSuppr.addEventListener('click', function () {
        if (!window.confirm('Supprimer cette demande ?')) { return; }
        api('/notes/' + note.id, { method: 'DELETE' })
          .then(charger)
          .catch(function (e) { window.alert(e.message); });
      });
      pied.appendChild(btnSuppr);
    }

    carte.appendChild(pied);
    return carte;
  }

  /** Met une demande en avant : sur la page et dans le panneau. */
  function viser(id, defiler) {
    etat.visee = id;
    ouvrirPanneau(true);
    dessinerListe();

    var carte = document.getElementById('ae-note-' + id);
    if (carte) { carte.scrollIntoView({ block: 'nearest', behavior: 'smooth' }); }

    if (defiler) {
      var note = etat.notes.find(function (n) { return n.id === id; });
      var cible = note && resoudre(note);
      if (cible) { cible.scrollIntoView({ block: 'center', behavior: 'smooth' }); }
    }
  }

  /* ---------------------------------------------------------- */
  /* Mode annotation                                            */
  /* ---------------------------------------------------------- */

  var survol = el('div', 'aer-survol');
  var survolNom = el('span', 'aer-survol__nom');
  survol.appendChild(survolNom);
  survol.style.display = 'none';
  racine.appendChild(survol);

  function basculerAnnotation(actif) {
    etat.annote = actif;
    document.body.classList.toggle('aer-annote', actif);
    btnAnnoter.classList.toggle('aer-actif', actif);
    btnAnnoter.textContent = actif ? 'Terminer' : 'Annoter';
    survol.style.display = 'none';
    if (!actif) { fermerComposeur(); }
  }

  btnAnnoter.addEventListener('click', function () { basculerAnnotation(!etat.annote); });

  document.addEventListener('mousemove', function (ev) {
    if (!etat.annote) { return; }
    var cible = ev.target;
    if (!cible || cible.closest('.aer-racine')) { survol.style.display = 'none'; return; }

    var boite = cible.getBoundingClientRect();
    survol.style.display = 'block';
    survol.style.left = (boite.left + window.scrollX) + 'px';
    survol.style.top = (boite.top + window.scrollY) + 'px';
    survol.style.width = boite.width + 'px';
    survol.style.height = boite.height + 'px';
    survolNom.textContent = cible.nodeName.toLowerCase();
  }, true);

  document.addEventListener('click', function (ev) {
    if (!etat.annote) { return; }
    if (ev.target.closest('.aer-racine')) { return; }

    ev.preventDefault();
    ev.stopPropagation();

    var cible = ev.target;
    var boite = cible.getBoundingClientRect();

    ouvrirComposeur(cible, {
      x: boite.width ? (ev.clientX - boite.left) / boite.width : 0.5,
      y: boite.height ? (ev.clientY - boite.top) / boite.height : 0.5,
      pageX: ev.clientX,
      pageY: ev.clientY
    });
  }, true);

  document.addEventListener('keydown', function (ev) {
    if (ev.key === 'Escape') {
      if (composeur) { fermerComposeur(); }
      else if (etat.annote) { basculerAnnotation(false); }
    }
  });

  /* ---------------------------------------------------------- */
  /* Composeur de demande                                       */
  /* ---------------------------------------------------------- */

  var composeur = null;

  function fermerComposeur() {
    if (composeur) { composeur.remove(); composeur = null; }
    etat.cible = null;
    survol.style.display = 'none';
  }

  function ouvrirComposeur(cible, position) {
    fermerComposeur();
    etat.cible = cible;

    var type = cible.nodeName.toLowerCase() === 'img' ? 'image' : 'texte';

    composeur = el('div', 'aer-composeur');
    composeur.appendChild(el('h3', '', 'Votre demande'));
    composeur.appendChild(el('p', 'aer-cible', decrire(cible)));

    // Choix du type de demande
    var types = el('div', 'aer-types');
    Object.keys(CFG.types).forEach(function (cle) {
      var b = el('button', '', CFG.types[cle]);
      b.setAttribute('aria-pressed', cle === type ? 'true' : 'false');
      b.addEventListener('click', function () {
        type = cle;
        types.querySelectorAll('button').forEach(function (x) { x.setAttribute('aria-pressed', 'false'); });
        b.setAttribute('aria-pressed', 'true');
        dessinerChampValeur();
      });
      types.appendChild(b);
    });
    composeur.appendChild(types);

    // Le message
    var champMessage = el('div', 'aer-champ');
    var etiquette = el('label', '', 'Ce que vous voulez changer');
    etiquette.setAttribute('for', 'aer-message');
    var zone = document.createElement('textarea');
    zone.id = 'aer-message';
    zone.placeholder = 'Exemple : cette police est trop petite sur mon téléphone.';
    champMessage.appendChild(etiquette);
    champMessage.appendChild(zone);
    composeur.appendChild(champMessage);

    // Le champ qui dépend du type
    var champValeur = el('div', 'aer-champ');
    composeur.appendChild(champValeur);

    var mediaId = 0;

    function dessinerChampValeur() {
      champValeur.innerHTML = '';
      mediaId = 0;

      if (type === 'texte') {
        var l = el('label', '', 'Texte de remplacement (facultatif)');
        var i = document.createElement('input');
        i.type = 'text';
        i.className = 'aer-valeur';
        i.placeholder = 'Le texte exact que vous voulez voir';
        i.value = (cible.textContent || '').trim().slice(0, 200);
        champValeur.appendChild(l);
        champValeur.appendChild(i);
      } else if (type === 'couleur') {
        var lc = el('label', '', 'Couleur souhaitée');
        var ic = document.createElement('input');
        ic.type = 'color';
        ic.className = 'aer-valeur';
        ic.value = '#167FA4';
        champValeur.appendChild(lc);
        champValeur.appendChild(ic);
      } else if (type === 'image') {
        var li = el('label', '', 'Image de remplacement (facultatif)');
        var ii = document.createElement('input');
        ii.type = 'file';
        ii.accept = 'image/*';
        ii.addEventListener('change', function () {
          if (!ii.files || !ii.files[0]) { return; }
          var donnees = new FormData();
          donnees.append('fichier', ii.files[0]);
          envoyer.disabled = true;
          envoyer.textContent = 'Envoi de l\'image…';
          api('/media', { method: 'POST', body: donnees })
            .then(function (r) { mediaId = r.id; })
            .catch(function (e) { erreur.textContent = e.message; })
            .then(function () {
              envoyer.disabled = false;
              envoyer.textContent = 'Envoyer la demande';
            });
        });
        champValeur.appendChild(li);
        champValeur.appendChild(ii);
      }
    }
    dessinerChampValeur();

    var actions = el('div', 'aer-composeur__act');
    var envoyer = el('button', 'aer-btn aer-btn--or', 'Envoyer la demande');
    var annuler = el('button', 'aer-btn aer-btn--plat', 'Annuler');
    actions.appendChild(envoyer);
    actions.appendChild(annuler);
    composeur.appendChild(actions);

    var erreur = el('p', 'aer-erreur');
    composeur.appendChild(erreur);

    annuler.addEventListener('click', fermerComposeur);

    envoyer.addEventListener('click', function () {
      var message = zone.value.trim();
      if (!message) {
        erreur.textContent = 'Dites-nous en un mot ce qui ne va pas.';
        zone.focus();
        return;
      }

      var saisie = champValeur.querySelector('.aer-valeur');

      envoyer.disabled = true;
      envoyer.textContent = 'Envoi…';
      erreur.textContent = '';

      api('/notes', {
        method: 'POST',
        body: {
          maquette: CFG.maquette,
          type: type,
          message: message,
          valeur: saisie ? saisie.value : '',
          media_id: mediaId,
          selecteur: selecteurDe(cible),
          ancre: (cible.textContent || '').trim().slice(0, 80),
          x: position.x,
          y: position.y,
          largeur: window.innerWidth
        }
      }).then(function (note) {
        fermerComposeur();
        basculerAnnotation(false);
        return charger().then(function () { viser(note.id, false); });
      }).catch(function (e) {
        erreur.textContent = e.message;
        envoyer.disabled = false;
        envoyer.textContent = 'Envoyer la demande';
      });
    });

    racine.appendChild(composeur);

    // Placement : à côté du clic, sans déborder de la fenêtre.
    var largeur = composeur.offsetWidth;
    var hauteur = composeur.offsetHeight;
    var gauche = Math.min(position.pageX + 14, window.innerWidth - largeur - 12);
    var haut = Math.min(position.pageY + 14, window.innerHeight - hauteur - 12);
    composeur.style.left = Math.max(12, gauche) + 'px';
    composeur.style.top = Math.max(12, haut) + 'px';

    zone.focus();
  }

  /* ---------------------------------------------------------- */
  /* Chargement                                                 */
  /* ---------------------------------------------------------- */

  function charger() {
    return api('/notes?maquette=' + CFG.maquette)
      .then(function (notes) {
        etat.notes = notes;
        dessinerListe();
      })
      .catch(function (e) {
        corps.innerHTML = '';
        corps.appendChild(el('p', 'aer-erreur', e.message));
      });
  }

  charger().then(function () {
    // Lien profond depuis le back-office ou depuis un courriel : #ae-note-42
    var ancre = /^#ae-note-(\d+)$/.exec(location.hash);
    if (ancre) { viser(parseInt(ancre[1], 10), true); }
  });
})();
