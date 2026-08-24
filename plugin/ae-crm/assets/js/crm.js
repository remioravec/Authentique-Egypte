/* ============================================================
   AE CRM — colonnes, glisser-déposer, fiche client.

   Toutes les fiches sont déjà dans la page (bloc JSON) : ouvrir
   une fiche ne demande aucun aller-retour. Seuls le déplacement
   et l'ajout d'une note appellent le serveur.

   Le glisser-déposer natif HTML5 suffit ici — pas de bibliothèque.
   Un sélecteur de colonne reste présent dans la fiche : c'est le
   chemin au clavier, et le seul praticable sur téléphone, où le
   glisser-déposer natif n'existe pas.
   ============================================================ */
(function () {
  'use strict';

  var noeud = document.getElementById('crm-fiches');
  if (!noeud || typeof AE_CRM === 'undefined') { return; }

  var FICHES = {};
  try {
    JSON.parse(noeud.textContent).forEach(function (f) { FICHES[f.id] = f; });
  } catch (e) { return; }

  var tableau = document.getElementById('crm-tableau');
  var tiroir = document.getElementById('crm-tiroir');
  if (!tableau || !tiroir) { return; }
  var panneau = tiroir.querySelector('.crm-panneau');

  /* ---------------------------------------------------------- */
  /* Serveur                                                     */
  /* ---------------------------------------------------------- */

  function poster(action, donnees) {
    var corps = new URLSearchParams();
    corps.set('action', action);
    corps.set('nonce', AE_CRM.nonce);
    Object.keys(donnees).forEach(function (c) { corps.set(c, donnees[c]); });

    return fetch(AE_CRM.ajax, {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: corps.toString()
    }).then(function (r) { return r.json(); }).then(function (r) {
      if (!r.success) { throw new Error((r.data && r.data.message) || 'Échec'); }
      return r.data;
    });
  }

  function el(balise, classe, texte) {
    var n = document.createElement(balise);
    if (classe) { n.className = classe; }
    if (texte !== undefined) { n.textContent = texte; }
    return n;
  }

  function recompter() {
    tableau.querySelectorAll('.crm-col').forEach(function (col) {
      var n = col.querySelectorAll('.crm-carte').length;
      col.querySelector('.crm-n').textContent = n;
      col.classList.toggle('crm-col--vide', n === 0);
    });
  }

  /**
   * Met à jour le compteur de notes d'une carte.
   *
   * Le compteur est toujours présent dans le balisage, simplement
   * masqué quand il n'y a rien : chercher à le créer au vol, c'était
   * dépendre d'une structure de carte qui a changé une fois déjà.
   */
  function majCompteur(id, n) {
    var carte = tableau.querySelector('.crm-carte[data-id="' + id + '"]');
    if (!carte) { return; }
    var cpt = carte.querySelector('.crm-cpt');
    var valeur = cpt && cpt.querySelector('.crm-cpt-n');
    if (!cpt || !valeur) { return; }
    valeur.textContent = n;
    cpt.hidden = (n === 0);
  }

  /* ---------------------------------------------------------- */
  /* Glisser-déposer                                             */
  /* ---------------------------------------------------------- */

  var enCours = null;

  tableau.addEventListener('dragstart', function (ev) {
    var carte = ev.target.closest('.crm-carte');
    if (!carte) { return; }
    enCours = carte;
    carte.classList.add('crm-vol');
    ev.dataTransfer.effectAllowed = 'move';
    // Firefox n'amorce le glissement que si des données sont posées.
    ev.dataTransfer.setData('text/plain', carte.dataset.id);
  });

  tableau.addEventListener('dragend', function () {
    if (enCours) { enCours.classList.remove('crm-vol'); }
    tableau.querySelectorAll('.crm-pile').forEach(function (p) { p.classList.remove('crm-survol'); });
    enCours = null;
  });

  tableau.addEventListener('dragover', function (ev) {
    var pile = ev.target.closest('.crm-pile');
    if (!pile || !enCours) { return; }
    ev.preventDefault();
    ev.dataTransfer.dropEffect = 'move';
    tableau.querySelectorAll('.crm-pile').forEach(function (p) {
      p.classList.toggle('crm-survol', p === pile);
    });
  });

  tableau.addEventListener('drop', function (ev) {
    var pile = ev.target.closest('.crm-pile');
    if (!pile || !enCours) { return; }
    ev.preventDefault();

    var carte = enCours;
    var depart = carte.parentElement;
    var statut = pile.dataset.statut;
    if (depart === pile) { return; }

    // On déplace tout de suite, on annule si le serveur refuse :
    // l'attente d'un aller-retour casserait le geste.
    pile.insertBefore(carte, pile.querySelector('.crm-col-vide'));
    recompter();

    poster('aecrm_deplacer', { demande: carte.dataset.id, statut: statut })
      .then(function () {
        if (FICHES[carte.dataset.id]) { FICHES[carte.dataset.id].statut = statut; }
      })
      .catch(function (e) {
        depart.insertBefore(carte, depart.querySelector('.crm-col-vide'));
        recompter();
        window.alert(e.message);
      });
  });

  /* ---------------------------------------------------------- */
  /* Fiche client                                                */
  /* ---------------------------------------------------------- */

  function ouvrir(id) {
    var fiche = FICHES[id];
    if (!fiche) { return; }

    panneau.innerHTML = '';

    var tete = el('header', 'crm-tete');

    // La même pastille que sur la carte : on reconnaît la personne
    // sans avoir à relire son nom.
    var source = tableau.querySelector('.crm-carte[data-id="' + id + '"] .crm-ava');
    var ava = el('span', 'crm-ava', source ? source.textContent.trim() : '?');
    if (source) {
      ava.style.background = source.style.background;
      ava.style.color = source.style.color;
    }
    tete.appendChild(ava);
    tete.appendChild(el('h2', '', fiche.titre.replace(/\s*—.*$/, '')));

    var fermer = el('button', 'crm-fermer', '✕');
    fermer.type = 'button';
    fermer.setAttribute('aria-label', 'Fermer la fiche');
    fermer.addEventListener('click', fermerTiroir);
    tete.appendChild(fermer);
    panneau.appendChild(tete);

    var meta = el('p', 'crm-meta');
    var etiquette = el('span', 'crm-tag', fiche.formulaire || 'Formulaire');
    var tagSource = tableau.querySelector('.crm-carte[data-id="' + id + '"] .crm-tag');
    if (tagSource) {
      etiquette.style.background = tagSource.style.background;
      etiquette.style.color = tagSource.style.color;
    }
    meta.appendChild(etiquette);
    meta.appendChild(document.createTextNode(fiche.date));
    panneau.appendChild(meta);

    // Statut : le chemin clavier, en plus du glisser-déposer.
    var ligne = el('div', 'crm-statut');
    var etiq = el('label', '', 'Colonne');
    etiq.setAttribute('for', 'crm-choix-statut');
    ligne.appendChild(etiq);
    var choix = document.createElement('select');
    choix.id = 'crm-choix-statut';
    Object.keys(AE_CRM.statuts).forEach(function (cle) {
      var o = document.createElement('option');
      o.value = cle;
      o.textContent = AE_CRM.statuts[cle];
      if (cle === fiche.statut) { o.selected = true; }
      choix.appendChild(o);
    });
    choix.addEventListener('change', function () {
      var vise = choix.value;
      poster('aecrm_deplacer', { demande: id, statut: vise })
        .then(function () {
          fiche.statut = vise;
          var carte = tableau.querySelector('.crm-carte[data-id="' + id + '"]');
          var pile = tableau.querySelector('.crm-pile[data-statut="' + vise + '"]');
          if (carte && pile) {
            pile.insertBefore(carte, pile.querySelector('.crm-col-vide'));
            recompter();
          }
        })
        .catch(function (e) { window.alert(e.message); });
    });
    ligne.appendChild(choix);
    panneau.appendChild(ligne);

    // Les champs remplis.
    panneau.appendChild(el('h3', 'crm-titre', 'La demande'));
    var liste = el('dl', 'crm-champs');
    fiche.champs.forEach(function (champ) {
      var bloc = el('div');
      bloc.appendChild(el('dt', '', champ.nom));
      var dd = el('dd');
      if (champ.type === 'email') {
        var a = document.createElement('a');
        a.href = 'mailto:' + champ.valeur;
        a.textContent = champ.valeur;
        dd.appendChild(a);
      } else {
        dd.textContent = champ.valeur;
      }
      bloc.appendChild(dd);
      liste.appendChild(bloc);
    });
    panneau.appendChild(liste);

    if (fiche.page) {
      var origine = el('p', 'crm-origine');
      var lien = document.createElement('a');
      lien.href = fiche.page;
      lien.target = '_blank';
      lien.rel = 'noreferrer';
      lien.textContent = 'Voir la page d’origine';
      origine.appendChild(lien);
      panneau.appendChild(origine);
    }

    // Actions.
    var actions = el('div', 'crm-actions');
    if (fiche.courriel) {
      var repondre = document.createElement('a');
      repondre.className = 'button button-primary';
      repondre.href = 'mailto:' + fiche.courriel +
        '?subject=' + encodeURIComponent('Votre voyage en Égypte');
      repondre.textContent = 'Répondre';
      actions.appendChild(repondre);
    }
    var supprimer = document.createElement('a');
    supprimer.className = 'button crm-suppr';
    supprimer.href = fiche.suppr;
    supprimer.textContent = 'Supprimer';
    supprimer.addEventListener('click', function (ev) {
      if (!window.confirm('Supprimer définitivement cette demande ?')) { ev.preventDefault(); }
    });
    actions.appendChild(supprimer);
    panneau.appendChild(actions);

    // Journal interne.
    panneau.appendChild(el('h3', 'crm-titre', 'Suivi'));
    var journal = el('div', 'crm-journal');
    function dessinerJournal() {
      journal.innerHTML = '';
      if (!fiche.journal.length) {
        journal.appendChild(el('p', 'crm-journal-vide', 'Rien pour l’instant.'));
        return;
      }
      fiche.journal.slice().reverse().forEach(function (l) {
        var p = el('p', 'crm-journal-ligne');
        p.appendChild(el('strong', '', l.auteur));
        p.appendChild(document.createTextNode(' — ' + l.message));
        p.appendChild(el('span', 'crm-journal-date', l.date));
        journal.appendChild(p);
      });
    }
    dessinerJournal();
    panneau.appendChild(journal);

    var saisie = el('div', 'crm-note');
    var zone = document.createElement('textarea');
    zone.rows = 2;
    zone.placeholder = 'Ajouter une note de suivi…';
    zone.setAttribute('aria-label', 'Note de suivi');
    var ajouter = el('button', 'button', 'Ajouter');
    ajouter.type = 'button';
    ajouter.addEventListener('click', function () {
      var message = zone.value.trim();
      if (!message) { return; }
      ajouter.disabled = true;
      poster('aecrm_note', { demande: id, message: message })
        .then(function (l) {
          fiche.journal.push(l);
          zone.value = '';
          dessinerJournal();
          majCompteur(id, fiche.journal.length);
        })
        .catch(function (e) { window.alert(e.message); })
        .then(function () { ajouter.disabled = false; });
    });
    saisie.appendChild(zone);
    saisie.appendChild(ajouter);
    panneau.appendChild(saisie);

    tiroir.hidden = false;
    document.body.classList.add('crm-tiroir-ouvert');
    fermer.focus();
  }

  function fermerTiroir() {
    tiroir.hidden = true;
    document.body.classList.remove('crm-tiroir-ouvert');
  }

  tableau.addEventListener('click', function (ev) {
    var carte = ev.target.closest('.crm-carte');
    if (carte) { ouvrir(carte.dataset.id); }
  });

  // Les cartes sont focalisables : Entrée et Espace les ouvrent aussi.
  tableau.addEventListener('keydown', function (ev) {
    if (ev.key !== 'Enter' && ev.key !== ' ') { return; }
    var carte = ev.target.closest('.crm-carte');
    if (!carte) { return; }
    ev.preventDefault();
    ouvrir(carte.dataset.id);
  });

  tiroir.addEventListener('click', function (ev) {
    if (ev.target.hasAttribute('data-fermer')) { fermerTiroir(); }
  });

  document.addEventListener('keydown', function (ev) {
    if (ev.key === 'Escape' && !tiroir.hidden) { fermerTiroir(); }
  });

  recompter();
})();
