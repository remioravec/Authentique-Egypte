/* ============================================================
   Calque de commentaires — le geste de Google Docs et de Figma.

   1. On active l'outil (bouton en bas à droite, ou touche C).
   2. On survole : l'élément sous le curseur se souligne.
   3. On clique : une bulle s'ouvre au point cliqué, avec un simple
      champ de texte. Pas de type à choisir, pas de champ obligatoire.
   4. On écrit, éventuellement on colle ou dépose une image, on envoie
      (ou Ctrl+Entrée).
   5. Une épingle numérotée reste sur l'élément. Au clic, le fil
      s'ouvre : réponses, résolution, suppression.

   Le commentaire est ancré trois fois : sélecteur CSS, texte de
   l'élément en secours, et position relative dans sa boîte. Une
   page qui bouge un peu ne perd pas ses épingles.
   ============================================================ */
(function () {
  'use strict';

  if (typeof AEC === 'undefined') { return; }

  /* ---------------------------------------------------------- */
  /* API                                                         */
  /* ---------------------------------------------------------- */

  function api(chemin, options) {
    options = options || {};
    var entetes = { 'X-WP-Nonce': AEC.nonce };
    var corps = options.body;
    if (corps && !(corps instanceof FormData)) {
      entetes['Content-Type'] = 'application/json';
      corps = JSON.stringify(corps);
    }
    return fetch(AEC.racine + chemin, {
      method: options.method || 'GET',
      credentials: 'same-origin',
      headers: entetes,
      body: corps
    }).then(function (r) {
      return r.json().then(function (d) {
        if (!r.ok) { throw new Error((d && d.message) || ('Erreur ' + r.status)); }
        return d;
      });
    });
  }

  /* ---------------------------------------------------------- */
  /* Utilitaires                                                 */
  /* ---------------------------------------------------------- */

  function el(balise, classe, texte) {
    var n = document.createElement(balise);
    if (classe) { n.className = classe; }
    if (texte !== undefined) { n.textContent = texte; }
    return n;
  }

  function initiales(nom) {
    return (nom || '?').split(/[\s._-]+/).filter(Boolean).slice(0, 2)
      .map(function (m) { return m[0].toUpperCase(); }).join('') || '?';
  }

  function quand(iso) {
    var d = new Date(iso);
    if (isNaN(d)) { return ''; }
    var ecart = (Date.now() - d.getTime()) / 1000;
    if (ecart < 60) { return "à l'instant"; }
    if (ecart < 3600) { return 'il y a ' + Math.floor(ecart / 60) + ' min'; }
    if (ecart < 86400) { return 'il y a ' + Math.floor(ecart / 3600) + ' h'; }
    return d.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' });
  }

  function ralentir(fn, delai) {
    var t;
    return function () {
      var a = arguments, c = this;
      clearTimeout(t);
      t = setTimeout(function () { fn.apply(c, a); }, delai);
    };
  }

  /** Chemin CSS d'un élément, depuis <body>, avec raccourci par identifiant. */
  function selecteurDe(cible) {
    if (!cible || cible === document.body) { return 'body'; }
    var morceaux = [];
    var noeud = cible;
    while (noeud && noeud !== document.body && noeud.nodeType === 1) {
      if (noeud.id) {
        morceaux.unshift('#' + CSS.escape(noeud.id));
        return morceaux.join(' > ');
      }
      var rang = 1, frere = noeud;
      while ((frere = frere.previousElementSibling)) {
        if (frere.nodeName === noeud.nodeName) { rang++; }
      }
      morceaux.unshift(noeud.nodeName.toLowerCase() + ':nth-of-type(' + rang + ')');
      noeud = noeud.parentElement;
    }
    morceaux.unshift('body');
    return morceaux.join(' > ');
  }

  /** Retrouve l'élément d'un fil : sélecteur d'abord, texte en secours. */
  function resoudre(fil) {
    if (fil.selecteur) {
      try {
        var trouve = document.querySelector(fil.selecteur);
        if (trouve && !trouve.closest('.aec')) { return trouve; }
      } catch (e) { /* sélecteur devenu invalide */ }
    }
    if (fil.ancre) {
      var candidats = document.body.querySelectorAll(
        'h1,h2,h3,h4,h5,p,li,td,th,a,button,span,img,figcaption,blockquote,summary,label');
      for (var i = 0; i < candidats.length; i++) {
        if (candidats[i].closest('.aec')) { continue; }
        var t = (candidats[i].textContent || '').trim().slice(0, 120);
        if (t && t === fil.ancre) { return candidats[i]; }
      }
    }
    return null;
  }

  function decrire(cible) {
    if (cible.nodeName === 'IMG') {
      return 'Image · ' + (cible.getAttribute('alt') || (cible.currentSrc || '').split('/').pop() || '');
    }
    var t = (cible.textContent || '').trim().replace(/\s+/g, ' ');
    return t ? (t.length > 110 ? t.slice(0, 110) + '…' : t) : '<' + cible.nodeName.toLowerCase() + '>';
  }

  /* ---------------------------------------------------------- */
  /* État et racine                                              */
  /* ---------------------------------------------------------- */

  var etat = { fils: [], mode: false, actif: 0, filtre: 'ouvert', bulle: null, cible: null };

  var racine = el('div', 'aec');
  document.body.appendChild(racine);

  /* ---------------------------------------------------------- */
  /* Barre d'outil                                               */
  /* ---------------------------------------------------------- */

  var ICONE_BULLE = '<svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">' +
    '<path d="M14 9.5A2.5 2.5 0 0 1 11.5 12H5l-3 2.5V4a2 2 0 0 1 2-2h7.5A2.5 2.5 0 0 1 14 4.5v5Z" ' +
    'stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/></svg>';
  var ICONE_LISTE = '<svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">' +
    '<path d="M2.5 4h11M2.5 8h11M2.5 12h7" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>';
  var ICONE_IMAGE = '<svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">' +
    '<rect x="1.8" y="3" width="12.4" height="10" rx="2" stroke="currentColor" stroke-width="1.5"/>' +
    '<circle cx="5.6" cy="6.6" r="1.2" fill="currentColor"/>' +
    '<path d="M2.6 12.2 6 9.1l2.6 2.1 2.2-1.8 2.6 2.3" stroke="currentColor" stroke-width="1.5" ' +
    'stroke-linecap="round" stroke-linejoin="round"/></svg>';

  var outil = el('div', 'aec-outil');

  var btnMode = el('button');
  btnMode.type = 'button';
  btnMode.setAttribute('aria-pressed', 'false');
  btnMode.innerHTML = ICONE_BULLE + '<span class="aec-mot">Commenter</span>';
  btnMode.title = 'Commenter (touche C)';

  var sep = el('span', 'aec-sep');

  var btnListe = el('button');
  btnListe.type = 'button';
  var jeton = el('span', 'aec-jeton', '0');
  btnListe.innerHTML = ICONE_LISTE;
  btnListe.appendChild(jeton);
  btnListe.title = 'Voir tous les commentaires de la page';

  outil.appendChild(btnMode);
  outil.appendChild(sep);
  outil.appendChild(btnListe);
  racine.appendChild(outil);

  /* ---------------------------------------------------------- */
  /* Surlignage et épingles                                      */
  /* ---------------------------------------------------------- */

  var survol = el('div', 'aec-survol');
  survol.style.display = 'none';
  racine.appendChild(survol);

  var coucheEpingles = el('div', 'aec-epingles');
  racine.appendChild(coucheEpingles);

  function visibles() {
    return etat.fils.filter(function (f) {
      return etat.filtre === 'tous' ? true : f.statut === 'ouvert';
    });
  }

  function placerEpingles() {
    coucheEpingles.innerHTML = '';
    visibles().forEach(function (fil, rang) {
      var cible = resoudre(fil);
      if (!cible) { return; }
      var boite = cible.getBoundingClientRect();
      if (!boite.width && !boite.height) { return; }

      var b = el('button', 'aec-epingle');
      b.type = 'button';
      b.appendChild(el('span', 'aec-pastille-n', String(rang + 1)));
      b.setAttribute('data-statut', fil.statut);
      b.setAttribute('data-fil', fil.id);
      b.title = fil.message.slice(0, 140);
      b.style.left = (boite.left + window.scrollX + boite.width * (fil.x || 0.5)) + 'px';
      b.style.top = (boite.top + window.scrollY + boite.height * (fil.y || 0.5)) + 'px';
      if (fil.id === etat.actif) { b.classList.add('aec-actif'); }

      b.addEventListener('click', function (ev) {
        ev.preventDefault();
        ev.stopPropagation();
        ouvrirFil(fil.id, b);
      });

      coucheEpingles.appendChild(b);
    });
  }

  var replacer = ralentir(placerEpingles, 110);
  window.addEventListener('resize', replacer);
  window.addEventListener('load', replacer);
  document.addEventListener('toggle', replacer, true);
  document.addEventListener('load', replacer, true); // images qui arrivent

  /* ---------------------------------------------------------- */
  /* Zone de saisie réutilisable                                 */
  /* ---------------------------------------------------------- */

  /**
   * Construit un champ de saisie complet : texte, image collée ou
   * déposée, bouton d'envoi. `envoyer(message, imageId)` doit rendre
   * une promesse.
   */
  function saisie(options) {
    var bloc = el('div', 'aec-saisie');
    var zone = document.createElement('textarea');
    zone.placeholder = options.placeholder || 'Écrire un commentaire…';
    zone.rows = 2;
    bloc.appendChild(zone);

    var apercu = el('div', 'aec-apercu');
    apercu.style.display = 'none';
    bloc.appendChild(apercu);

    var actions = el('div', 'aec-actions');

    var champFichier = document.createElement('input');
    champFichier.type = 'file';
    champFichier.accept = 'image/*';
    champFichier.style.display = 'none';

    var btnImage = el('button', 'aec-btn aec-btn--vide aec-btn--image');
    btnImage.type = 'button';
    btnImage.innerHTML = ICONE_IMAGE + '<span>Joindre une image</span>';
    btnImage.title = 'Choisir un fichier — ou collez une capture d’écran (Ctrl + V)';
    btnImage.addEventListener('click', function () { champFichier.click(); });

    var droite = el('div', 'aec-droite');
    var btnAnnuler = el('button', 'aec-btn aec-btn--vide', options.annuler || 'Annuler');
    btnAnnuler.type = 'button';
    var btnEnvoyer = el('button', 'aec-btn aec-btn--plein', options.envoi || 'Commenter');
    btnEnvoyer.type = 'button';
    btnEnvoyer.disabled = true;

    if (options.onAnnuler) { droite.appendChild(btnAnnuler); }
    droite.appendChild(btnEnvoyer);

    actions.appendChild(btnImage);
    actions.appendChild(droite);
    bloc.appendChild(actions);
    bloc.appendChild(champFichier);

    var aide = el('p', 'aec-aide', 'Ctrl + Entrée pour envoyer · collez une capture d’écran pour la joindre');
    bloc.appendChild(aide);

    var erreur = el('p', 'aec-erreur');
    bloc.appendChild(erreur);

    var imageId = 0;

    function autoHauteur() {
      zone.style.height = 'auto';
      zone.style.height = Math.min(zone.scrollHeight, 200) + 'px';
    }

    function majBouton() {
      btnEnvoyer.disabled = !zone.value.trim() && !imageId;
    }

    zone.addEventListener('input', function () { autoHauteur(); majBouton(); });

    /**
     * Le fichier collé n'a pas toujours de type MIME.
     *
     * Une capture collée depuis l'outil de capture de Windows arrive
     * parfois avec `type` vide et sans nom. La version précédente la
     * rejetait en silence : la cliente croyait avoir joint une image,
     * et rien ne partait. On retombe sur l'extension, et si tout
     * manque on suppose une capture PNG — le serveur revérifie de
     * toute façon.
     */
    function nomDeFichier(fichier) {
      var nom = (fichier && fichier.name) || '';
      if (/\.(jpe?g|png|webp|gif|avif)$/i.test(nom)) { return nom; }
      var type = (fichier && fichier.type) || '';
      var ext = { 'image/jpeg': 'jpg', 'image/png': 'png', 'image/webp': 'webp',
                  'image/gif': 'gif', 'image/avif': 'avif' }[type] || 'png';
      return 'capture-' + Date.now() + '.' + ext;
    }

    function estUneImage(fichier) {
      if (!fichier) { return false; }
      if (fichier.type && fichier.type.indexOf('image/') === 0) { return true; }
      if (fichier.type) { return false; }
      return /\.(jpe?g|png|webp|gif|avif)$/i.test(fichier.name || '') || fichier.size > 0;
    }

    function televerser(fichier) {
      if (!fichier) { return; }
      if (!estUneImage(fichier)) {
        erreur.textContent = 'Ce fichier n’est pas une image. Formats acceptés : JPG, PNG, WEBP, GIF, AVIF.';
        return;
      }
      var donnees = new FormData();
      donnees.append('fichier', fichier, nomDeFichier(fichier));
      erreur.textContent = '';
      btnEnvoyer.disabled = true;
      btnEnvoyer.textContent = 'Envoi de l’image…';
      api('/image', { method: 'POST', body: donnees })
        .then(function (r) {
          imageId = r.id;
          apercu.innerHTML = '';
          var img = document.createElement('img');
          img.src = r.url;
          img.alt = '';
          var retirer = el('button', '', '✕');
          retirer.type = 'button';
          retirer.title = 'Retirer l’image';
          retirer.addEventListener('click', function () {
            imageId = 0;
            apercu.style.display = 'none';
            apercu.innerHTML = '';
            majBouton();
          });
          var cadre = el('div', 'aec-apercu__cadre');
          cadre.appendChild(img);
          cadre.appendChild(retirer);
          apercu.appendChild(cadre);
          apercu.appendChild(el('span', 'aec-apercu__ok', 'Image jointe — elle partira avec votre commentaire'));
          apercu.style.display = 'block';
        })
        .catch(function (e) {
          imageId = 0;
          erreur.textContent = 'L’image n’a pas pu être envoyée : ' + e.message;
        })
        .then(function () {
          btnEnvoyer.textContent = options.envoi || 'Commenter';
          majBouton();
        });
    }

    champFichier.addEventListener('change', function () {
      if (champFichier.files && champFichier.files[0]) { televerser(champFichier.files[0]); }
    });

    /**
     * Coller une capture d'écran, comme dans Figma.
     *
     * Trois corrections par rapport à la version précédente, chacune
     * correspondant à un cas où la cliente croyait avoir joint une
     * image alors que rien ne partait :
     *
     *  1. l'écoute était posée sur la zone de texte seule. Un Ctrl+V
     *     fait sans avoir cliqué DANS le champ ne déclenchait rien ;
     *  2. `items` ignore les fichiers que certains navigateurs ne
     *     présentent que dans `clipboardData.files` ;
     *  3. une image copiée depuis Word, un mail ou Google Docs n'arrive
     *     pas comme fichier mais comme HTML contenant une balise
     *     <img>. On va la chercher là aussi.
     */
    function imageDuPressePapier(dt) {
      if (!dt) { return null; }

      var fichiers = dt.files || [];
      for (var i = 0; i < fichiers.length; i++) {
        if (estUneImage(fichiers[i])) { return fichiers[i]; }
      }

      var items = dt.items || [];
      for (var j = 0; j < items.length; j++) {
        if (items[j].kind === 'file') {
          var f = items[j].getAsFile();
          if (estUneImage(f)) { return f; }
        }
      }
      return null;
    }

    /** Une image collée en HTML : <img src="data:image/png;base64,…">. */
    function imageDuHtml(dt) {
      if (!dt || !dt.getData) { return null; }
      var html = '';
      try { html = dt.getData('text/html') || ''; } catch (e) { return null; }
      var trouve = html.match(/<img[^>]+src=["'](data:image\/[a-z+]+;base64,[^"']+)["']/i);
      if (!trouve) { return null; }
      try {
        var partie = trouve[1].split(',');
        var type = partie[0].slice(5).split(';')[0];
        var binaire = atob(partie[1]);
        var octets = new Uint8Array(binaire.length);
        for (var k = 0; k < binaire.length; k++) { octets[k] = binaire.charCodeAt(k); }
        return new Blob([octets], { type: type });
      } catch (e) { return null; }
    }

    function surCollage(ev) {
      var dt = ev.clipboardData || window.clipboardData;
      var image = imageDuPressePapier(dt) || imageDuHtml(dt);
      if (!image) { return; }
      ev.preventDefault();
      televerser(image);
    }

    // Sur tout le bloc, pas seulement dans la zone de texte.
    bloc.addEventListener('paste', surCollage);

    // Et sur la page entière tant que ce champ est à l'écran : c'est le
    // geste naturel — on ouvre la bulle, on colle, sans cliquer d'abord.
    function collageGlobal(ev) {
      if (!bloc.isConnected) {
        document.removeEventListener('paste', collageGlobal, true);
        return;
      }
      if (bloc.contains(ev.target)) { return; } // déjà traité au-dessus
      surCollage(ev);
    }
    document.addEventListener('paste', collageGlobal, true);

    // Déposer un fichier.
    ['dragover', 'drop'].forEach(function (nom) {
      bloc.addEventListener(nom, function (ev) {
        ev.preventDefault();
        if (nom === 'drop' && ev.dataTransfer && ev.dataTransfer.files[0]) {
          televerser(ev.dataTransfer.files[0]);
        }
      });
    });

    function envoyer() {
      var message = zone.value.trim();
      if (!message && !imageId) { return; }
      btnEnvoyer.disabled = true;
      btnEnvoyer.textContent = 'Envoi…';
      erreur.textContent = '';
      options.envoyer(message, imageId)
        .catch(function (e) {
          erreur.textContent = e.message;
          btnEnvoyer.disabled = false;
          btnEnvoyer.textContent = options.envoi || 'Commenter';
        });
    }

    btnEnvoyer.addEventListener('click', envoyer);
    btnAnnuler.addEventListener('click', function () { options.onAnnuler && options.onAnnuler(); });
    zone.addEventListener('keydown', function (ev) {
      if ((ev.metaKey || ev.ctrlKey) && ev.key === 'Enter') { ev.preventDefault(); envoyer(); }
    });

    bloc.focus = function () { zone.focus(); };
    return bloc;
  }

  /* ---------------------------------------------------------- */
  /* Bulle : composeur et fil                                    */
  /* ---------------------------------------------------------- */

  function fermerBulle() {
    if (etat.bulle) { etat.bulle.remove(); etat.bulle = null; }
    etat.cible = null;
    etat.actif = 0;
    survol.style.display = 'none';
    placerEpingles();
    dessinerPanneau();
  }

  /** Place une bulle près d'un point, sans déborder de la fenêtre. */
  function poser(bulle, pageX, pageY) {
    racine.appendChild(bulle);
    var l = bulle.offsetWidth, h = bulle.offsetHeight;
    var x = pageX + 14, y = pageY + 14;
    if (x + l > window.scrollX + window.innerWidth - 12) { x = pageX - l - 14; }
    if (y + h > window.scrollY + window.innerHeight - 12) { y = Math.max(window.scrollY + 12, pageY - h - 14); }
    bulle.style.left = Math.max(window.scrollX + 12, x) + 'px';
    bulle.style.top = Math.max(window.scrollY + 12, y) + 'px';
  }

  function ouvrirComposeur(cible, point) {
    fermerBulle();
    etat.cible = cible;

    var bulle = el('div', 'aec-bulle');
    var entete = el('div', 'aec-msg');
    entete.style.paddingBottom = '0';
    entete.style.borderBottom = '0';
    entete.appendChild(el('p', 'aec-cible', decrire(cible)));
    bulle.appendChild(entete);

    var champ = saisie({
      placeholder: 'Qu’est-ce qui ne va pas ici ?',
      envoi: 'Commenter',
      onAnnuler: fermerBulle,
      envoyer: function (message, imageId) {
        var boite = cible.getBoundingClientRect();
        return api('/fils', {
          method: 'POST',
          body: {
            message: message,
            url: location.href,
            post: AEC.post,
            selecteur: selecteurDe(cible),
            ancre: (cible.textContent || '').trim().slice(0, 120),
            x: boite.width ? (point.clientX - boite.left) / boite.width : 0.5,
            y: boite.height ? (point.clientY - boite.top) / boite.height : 0.5,
            largeur: window.innerWidth,
            image_id: imageId
          }
        }).then(function (fil) {
          etat.fils.push(fil);
          fermerBulle();
          basculerMode(false);
          etat.actif = fil.id;
          placerEpingles();
          dessinerPanneau();
        });
      }
    });
    bulle.appendChild(champ);

    poser(bulle, point.pageX, point.pageY);
    etat.bulle = bulle;
    champ.focus();
  }

  function bloc(message, options) {
    var m = el('div', 'aec-msg' + (options.reponse ? ' aec-msg--reponse' : ''));
    var tete = el('div', 'aec-tete');
    tete.appendChild(el('span', 'aec-ini', initiales(message.auteur)));
    tete.appendChild(el('span', 'aec-nom', message.auteur));
    tete.appendChild(el('span', 'aec-quand', quand(message.date)));
    m.appendChild(tete);

    if (options.ancre) { m.appendChild(el('p', 'aec-cible', '« ' + options.ancre + ' »')); }
    m.appendChild(el('p', 'aec-texte', message.message));

    if (message.image) {
      var lien = document.createElement('a');
      lien.href = message.image;
      lien.target = '_blank';
      lien.rel = 'noreferrer';
      var img = document.createElement('img');
      img.className = 'aec-vignette';
      img.src = message.image;
      img.alt = 'Image jointe';
      img.loading = 'lazy';
      lien.appendChild(img);
      m.appendChild(lien);
    }
    return m;
  }

  function ouvrirFil(id, ancrage) {
    var fil = etat.fils.find(function (f) { return f.id === id; });
    if (!fil) { return; }

    fermerBulle();
    etat.actif = id;

    var bulle = el('div', 'aec-bulle');
    bulle.id = 'aec-' + id;

    var corps = el('div', 'aec-fil');
    corps.appendChild(bloc(fil, { ancre: fil.ancre }));
    fil.reponses.forEach(function (r) { corps.appendChild(bloc(r, { reponse: true })); });
    bulle.appendChild(corps);

    bulle.appendChild(saisie({
      placeholder: 'Répondre…',
      envoi: 'Répondre',
      envoyer: function (message, imageId) {
        return api('/fils/' + id + '/reponses', {
          method: 'POST',
          body: { message: message, image_id: imageId }
        }).then(function (maj) {
          remplacer(maj);
          ouvrirFil(id, ancrage);
        });
      }
    }));

    var liens = el('div', 'aec-liens');
    var btnResoudre = el('button', '', fil.statut === 'resolu' ? '↺ Rouvrir' : '✓ Résoudre');
    btnResoudre.type = 'button';
    btnResoudre.addEventListener('click', function () {
      api('/fils/' + id, {
        method: 'PATCH',
        body: { statut: fil.statut === 'resolu' ? 'ouvert' : 'resolu' }
      }).then(function (maj) {
        remplacer(maj);
        fermerBulle();
      }).catch(function (e) { window.alert(e.message); });
    });
    liens.appendChild(btnResoudre);

    if (AEC.peutModerer || fil.auteur_id === AEC.moi.id) {
      var btnSuppr = el('button', 'aec-danger', 'Supprimer');
      btnSuppr.type = 'button';
      btnSuppr.addEventListener('click', function () {
        if (!window.confirm('Supprimer ce commentaire et ses réponses ?')) { return; }
        api('/fils/' + id, { method: 'DELETE' }).then(function () {
          etat.fils = etat.fils.filter(function (f) { return f.id !== id; });
          fermerBulle();
        }).catch(function (e) { window.alert(e.message); });
      });
      liens.appendChild(btnSuppr);
    }
    bulle.appendChild(liens);

    var pageX, pageY;
    if (ancrage) {
      var b = ancrage.getBoundingClientRect();
      pageX = b.left + window.scrollX;
      pageY = b.bottom + window.scrollY;
    } else {
      pageX = window.scrollX + window.innerWidth / 2 - 170;
      pageY = window.scrollY + 100;
    }

    poser(bulle, pageX, pageY);
    etat.bulle = bulle;
    placerEpingles();
    dessinerPanneau();
  }

  function remplacer(maj) {
    var i = etat.fils.findIndex(function (f) { return f.id === maj.id; });
    if (i >= 0) { etat.fils[i] = maj; } else { etat.fils.push(maj); }
  }

  /* ---------------------------------------------------------- */
  /* Mode commentaire                                            */
  /* ---------------------------------------------------------- */

  function basculerMode(actif) {
    etat.mode = !!actif;
    document.body.classList.toggle('aec-mode', etat.mode);
    btnMode.setAttribute('aria-pressed', String(etat.mode));
    survol.style.display = 'none';
    if (!etat.mode && etat.bulle && !etat.actif) { fermerBulle(); }
  }

  btnMode.addEventListener('click', function () { basculerMode(!etat.mode); });

  document.addEventListener('mousemove', function (ev) {
    if (!etat.mode) { return; }
    var cible = ev.target;
    if (!cible || cible.closest('.aec')) { survol.style.display = 'none'; return; }
    var b = cible.getBoundingClientRect();
    survol.style.display = 'block';
    survol.style.left = (b.left + window.scrollX) + 'px';
    survol.style.top = (b.top + window.scrollY) + 'px';
    survol.style.width = b.width + 'px';
    survol.style.height = b.height + 'px';
  }, true);

  document.addEventListener('click', function (ev) {
    if (!etat.mode || ev.target.closest('.aec')) { return; }
    ev.preventDefault();
    ev.stopPropagation();
    ouvrirComposeur(ev.target, {
      clientX: ev.clientX, clientY: ev.clientY,
      pageX: ev.pageX, pageY: ev.pageY
    });
  }, true);

  document.addEventListener('keydown', function (ev) {
    var saisieEnCours = /^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement.nodeName)
      || document.activeElement.isContentEditable;
    if (ev.key === 'Escape') {
      if (etat.bulle) { fermerBulle(); } else if (etat.mode) { basculerMode(false); }
      return;
    }
    if (saisieEnCours || ev.metaKey || ev.ctrlKey || ev.altKey) { return; }
    if (ev.key === 'c' || ev.key === 'C') { basculerMode(!etat.mode); }
  });

  /* ---------------------------------------------------------- */
  /* Panneau latéral                                             */
  /* ---------------------------------------------------------- */

  var panneau = el('aside', 'aec-panneau');
  panneau.setAttribute('data-ouvert', '0');

  var tete = el('div', 'aec-panneau__tete');
  tete.appendChild(el('strong', '', 'Commentaires'));
  var btnFermer = el('button', 'aec-fermer', '✕');
  btnFermer.type = 'button';
  btnFermer.setAttribute('aria-label', 'Fermer');
  tete.appendChild(btnFermer);
  panneau.appendChild(tete);

  var filtres = el('div', 'aec-filtres');
  [['ouvert', 'À traiter'], ['tous', 'Tous']].forEach(function (paire) {
    var b = el('button', '', paire[1]);
    b.type = 'button';
    b.setAttribute('aria-pressed', String(paire[0] === etat.filtre));
    b.addEventListener('click', function () {
      etat.filtre = paire[0];
      filtres.querySelectorAll('button').forEach(function (x) { x.setAttribute('aria-pressed', 'false'); });
      b.setAttribute('aria-pressed', 'true');
      dessinerPanneau();
      placerEpingles();
    });
    filtres.appendChild(b);
  });
  panneau.appendChild(filtres);

  var corpsPanneau = el('div', 'aec-panneau__corps');
  panneau.appendChild(corpsPanneau);

  var zonePages = el('div', 'aec-pages');
  zonePages.appendChild(el('h4', '', 'Pages à relire'));
  panneau.appendChild(zonePages);

  racine.appendChild(panneau);

  function ouvrirPanneau(ouvert) {
    panneau.setAttribute('data-ouvert', ouvert ? '1' : '0');
    btnListe.setAttribute('aria-pressed', String(!!ouvert));
    document.body.classList.toggle('aec-panneau-ouvert', !!ouvert);
  }
  btnFermer.addEventListener('click', function () { ouvrirPanneau(false); });
  btnListe.addEventListener('click', function () {
    ouvrirPanneau(panneau.getAttribute('data-ouvert') !== '1');
  });

  function dessinerPanneau() {
    var liste = visibles();
    var ouverts = etat.fils.filter(function (f) { return f.statut === 'ouvert'; }).length;
    jeton.textContent = String(ouverts);
    jeton.setAttribute('data-zero', ouverts ? '0' : '1');

    corpsPanneau.innerHTML = '';
    if (!liste.length) {
      corpsPanneau.appendChild(el('p', 'aec-vide',
        etat.fils.length
          ? 'Rien à traiter sur cette page.'
          : 'Aucun commentaire ici. Cliquez sur « Commenter », puis sur l’élément à changer.'));
      return;
    }

    liste.forEach(function (fil, rang) {
      var carte = el('div', 'aec-carte');
      carte.setAttribute('data-statut', fil.statut);
      if (fil.id === etat.actif) { carte.classList.add('aec-actif'); }

      var tete = el('div', 'aec-tete');
      tete.appendChild(el('span', 'aec-carte-n', String(rang + 1)));
      tete.appendChild(el('span', 'aec-nom', fil.auteur));
      tete.appendChild(el('span', 'aec-quand', quand(fil.date)));
      carte.appendChild(tete);

      if (fil.ancre) { carte.appendChild(el('p', 'aec-cible', '« ' + fil.ancre.slice(0, 70) + ' »')); }
      carte.appendChild(el('p', 'aec-texte', fil.message));
      if (fil.reponses.length) {
        carte.appendChild(el('p', 'aec-aide',
          fil.reponses.length + (fil.reponses.length > 1 ? ' réponses' : ' réponse')));
      }

      carte.addEventListener('click', function () {
        var cible = resoudre(fil);
        if (cible) { cible.scrollIntoView({ block: 'center', behavior: 'smooth' }); }
        setTimeout(function () {
          var epingle = coucheEpingles.querySelector('[data-fil="' + fil.id + '"]');
          ouvrirFil(fil.id, epingle);
        }, cible ? 380 : 0);
      });

      corpsPanneau.appendChild(carte);
    });
  }

  function dessinerPages(pages) {
    pages.forEach(function (page) {
      var a = document.createElement('a');
      a.href = page.url;
      a.textContent = page.titre;
      if (page.post && page.post === AEC.post) { a.setAttribute('aria-current', 'page'); }
      var n = el('span', 'aec-jeton', String(page.ouverts));
      n.setAttribute('data-zero', page.ouverts ? '0' : '1');
      a.appendChild(n);
      zonePages.appendChild(a);
    });
  }

  /* ---------------------------------------------------------- */
  /* Démarrage                                                   */
  /* ---------------------------------------------------------- */

  api('/fils?post=' + AEC.post + '&url=' + encodeURIComponent(location.href))
    .then(function (fils) {
      etat.fils = fils;
      dessinerPanneau();
      placerEpingles();

      var ancre = /^#aec-(\d+)$/.exec(location.hash);
      if (ancre) {
        var id = parseInt(ancre[1], 10);
        var fil = etat.fils.find(function (f) { return f.id === id; });
        var cible = fil && resoudre(fil);
        if (cible) { cible.scrollIntoView({ block: 'center' }); }
        setTimeout(function () {
          ouvrirFil(id, coucheEpingles.querySelector('[data-fil="' + id + '"]'));
        }, 300);
      }
    })
    .catch(function (e) {
      corpsPanneau.appendChild(el('p', 'aec-erreur', e.message));
    });

  api('/pages').then(dessinerPages).catch(function () { zonePages.style.display = 'none'; });
})();
