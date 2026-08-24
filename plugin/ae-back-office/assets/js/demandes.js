/* ============================================================
   Tableau des demandes — colonnes, glisser-déposer, fiche.

   Toutes les fiches sont déjà dans la page (bloc JSON) : ouvrir
   une fiche ne demande aucun aller-retour. Seuls le déplacement
   et l'ajout d'une note appellent le serveur.

   Le glisser-déposer natif HTML5 suffit ici — pas de bibliothèque.
   Un sélecteur de colonne reste présent dans la fiche : c'est le
   chemin au clavier, et le repli si le glisser échoue.
   ============================================================ */
(function () {
  'use strict';

  var noeud = document.getElementById('abo-fiches');
  if (!noeud || typeof ABO_DEMANDES === 'undefined') { return; }

  var FICHES = {};
  try {
    JSON.parse(noeud.textContent).forEach(function (f) { FICHES[f.id] = f; });
  } catch (e) { return; }

  var kanban = document.getElementById('abo-kanban');
  var tiroir = document.getElementById('abo-tiroir');
  var panneau = tiroir.querySelector('.abo-panneau');

  /* ---------------------------------------------------------- */
  /* Serveur                                                     */
  /* ---------------------------------------------------------- */

  function poster(action, donnees) {
    var corps = new URLSearchParams();
    corps.set('action', action);
    corps.set('nonce', ABO_DEMANDES.nonce);
    Object.keys(donnees).forEach(function (c) { corps.set(c, donnees[c]); });

    return fetch(ABO_DEMANDES.ajax, {
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
    kanban.querySelectorAll('.abo-col').forEach(function (col) {
      var n = col.querySelectorAll('.abo-fiche').length;
      col.querySelector('.abo-n').textContent = n;
      col.classList.toggle('abo-col--vide', n === 0);
    });
  }

  /* ---------------------------------------------------------- */
  /* Glisser-déposer                                             */
  /* ---------------------------------------------------------- */

  var enCours = null;

  kanban.addEventListener('dragstart', function (ev) {
    var fiche = ev.target.closest('.abo-fiche');
    if (!fiche) { return; }
    enCours = fiche;
    fiche.classList.add('abo-vol');
    ev.dataTransfer.effectAllowed = 'move';
    // Firefox n'amorce le glissement que si des données sont posées.
    ev.dataTransfer.setData('text/plain', fiche.dataset.id);
  });

  kanban.addEventListener('dragend', function () {
    if (enCours) { enCours.classList.remove('abo-vol'); }
    kanban.querySelectorAll('.abo-pile').forEach(function (p) { p.classList.remove('abo-survol'); });
    enCours = null;
  });

  kanban.addEventListener('dragover', function (ev) {
    var pile = ev.target.closest('.abo-pile');
    if (!pile || !enCours) { return; }
    ev.preventDefault();
    ev.dataTransfer.dropEffect = 'move';
    kanban.querySelectorAll('.abo-pile').forEach(function (p) {
      p.classList.toggle('abo-survol', p === pile);
    });
  });

  kanban.addEventListener('drop', function (ev) {
    var pile = ev.target.closest('.abo-pile');
    if (!pile || !enCours) { return; }
    ev.preventDefault();

    var fiche = enCours;
    var depart = fiche.parentElement;
    var statut = pile.dataset.statut;
    if (depart === pile) { return; }

    // On déplace tout de suite, on annule si le serveur refuse :
    // l'attente d'un aller-retour casserait le geste.
    pile.insertBefore(fiche, pile.querySelector('.abo-col-vide'));
    recompter();

    poster('abo_deplacer', { demande: fiche.dataset.id, statut: statut })
      .then(function () {
        if (FICHES[fiche.dataset.id]) { FICHES[fiche.dataset.id].statut = statut; }
      })
      .catch(function (e) {
        depart.insertBefore(fiche, depart.querySelector('.abo-col-vide'));
        recompter();
        window.alert(e.message);
      });
  });

  /* ---------------------------------------------------------- */
  /* Fiche                                                       */
  /* ---------------------------------------------------------- */

  function ouvrir(id) {
    var fiche = FICHES[id];
    if (!fiche) { return; }

    panneau.innerHTML = '';

    var tete = el('header', 'abo-fiche-tete');
    tete.appendChild(el('h2', '', fiche.titre));
    var fermer = el('button', 'abo-fermer', '✕');
    fermer.type = 'button';
    fermer.setAttribute('aria-label', 'Fermer la fiche');
    fermer.addEventListener('click', fermerTiroir);
    tete.appendChild(fermer);
    panneau.appendChild(tete);

    var meta = el('p', 'abo-fiche-meta');
    meta.textContent = fiche.formulaire + ' · ' + fiche.date;
    panneau.appendChild(meta);

    // Statut : le chemin clavier, en plus du glisser-déposer.
    var ligne = el('div', 'abo-fiche-statut');
    ligne.appendChild(el('label', '', 'Colonne'));
    var choix = document.createElement('select');
    Object.keys(ABO_DEMANDES.statuts).forEach(function (cle) {
      var o = document.createElement('option');
      o.value = cle;
      o.textContent = ABO_DEMANDES.statuts[cle];
      if (cle === fiche.statut) { o.selected = true; }
      choix.appendChild(o);
    });
    choix.addEventListener('change', function () {
      poster('abo_deplacer', { demande: id, statut: choix.value })
        .then(function () {
          fiche.statut = choix.value;
          var carte = kanban.querySelector('.abo-fiche[data-id="' + id + '"]');
          var pile = kanban.querySelector('.abo-pile[data-statut="' + choix.value + '"]');
          if (carte && pile) {
            pile.insertBefore(carte, pile.querySelector('.abo-col-vide'));
            recompter();
          }
        })
        .catch(function (e) { window.alert(e.message); });
    });
    ligne.appendChild(choix);
    panneau.appendChild(ligne);

    // Les champs remplis.
    var liste = el('dl', 'abo-fiche-champs');
    fiche.champs.forEach(function (champ) {
      var bloc = el('div');
      bloc.appendChild(el('dt', '', champ.nom));
      var dd = el('dd', '', champ.valeur);
      if (champ.type === 'email') {
        dd.innerHTML = '';
        var a = document.createElement('a');
        a.href = 'mailto:' + champ.valeur;
        a.textContent = champ.valeur;
        dd.appendChild(a);
      }
      bloc.appendChild(dd);
      liste.appendChild(bloc);
    });
    panneau.appendChild(liste);

    if (fiche.page) {
      var origine = el('p', 'abo-fiche-origine');
      var lien = document.createElement('a');
      lien.href = fiche.page;
      lien.target = '_blank';
      lien.rel = 'noreferrer';
      lien.textContent = 'Voir la page d’origine';
      origine.appendChild(lien);
      panneau.appendChild(origine);
    }

    // Actions.
    var actions = el('div', 'abo-fiche-actions');
    if (fiche.courriel) {
      var repondre = document.createElement('a');
      repondre.className = 'button button-primary';
      repondre.href = 'mailto:' + fiche.courriel +
        '?subject=' + encodeURIComponent('Votre voyage en Égypte');
      repondre.textContent = 'Répondre';
      actions.appendChild(repondre);
    }
    var supprimer = document.createElement('a');
    supprimer.className = 'button abo-suppr';
    supprimer.href = fiche.suppr;
    supprimer.textContent = 'Supprimer';
    supprimer.addEventListener('click', function (ev) {
      if (!window.confirm('Supprimer définitivement cette demande ?')) { ev.preventDefault(); }
    });
    actions.appendChild(supprimer);
    panneau.appendChild(actions);

    // Journal interne.
    panneau.appendChild(el('h3', 'abo-fiche-titre', 'Suivi'));
    var journal = el('div', 'abo-journal');
    function dessinerJournal() {
      journal.innerHTML = '';
      if (!fiche.journal.length) {
        journal.appendChild(el('p', 'abo-journal-vide', 'Rien pour l’instant.'));
        return;
      }
      fiche.journal.slice().reverse().forEach(function (ligne) {
        var l = el('p', 'abo-journal-ligne');
        l.appendChild(el('strong', '', ligne.auteur));
        l.appendChild(document.createTextNode(' — ' + ligne.message));
        l.appendChild(el('span', 'abo-journal-date', ligne.date));
        journal.appendChild(l);
      });
    }
    dessinerJournal();
    panneau.appendChild(journal);

    var saisie = el('div', 'abo-note');
    var zone = document.createElement('textarea');
    zone.rows = 2;
    zone.placeholder = 'Ajouter une note de suivi…';
    var ajouter = el('button', 'button', 'Ajouter');
    ajouter.type = 'button';
    ajouter.addEventListener('click', function () {
      var message = zone.value.trim();
      if (!message) { return; }
      ajouter.disabled = true;
      poster('abo_note', { demande: id, message: message })
        .then(function (ligne) {
          fiche.journal.push(ligne);
          zone.value = '';
          dessinerJournal();
          var carte = kanban.querySelector('.abo-fiche[data-id="' + id + '"]');
          if (carte) {
            var pied = carte.querySelector('footer');
            var n = fiche.journal.length;
            var puce = pied.querySelectorAll('.abo-puces')[1];
            if (!puce) { puce = el('span', 'abo-puces'); pied.appendChild(puce); }
            puce.textContent = n + (n > 1 ? ' notes' : ' note');
          }
        })
        .catch(function (e) { window.alert(e.message); })
        .then(function () { ajouter.disabled = false; });
    });
    saisie.appendChild(zone);
    saisie.appendChild(ajouter);
    panneau.appendChild(saisie);

    tiroir.hidden = false;
    document.body.classList.add('abo-tiroir-ouvert');
    fermer.focus();
  }

  function fermerTiroir() {
    tiroir.hidden = true;
    document.body.classList.remove('abo-tiroir-ouvert');
  }

  kanban.addEventListener('click', function (ev) {
    var fiche = ev.target.closest('.abo-fiche');
    if (fiche) { ouvrir(fiche.dataset.id); }
  });

  tiroir.addEventListener('click', function (ev) {
    if (ev.target.hasAttribute('data-fermer')) { fermerTiroir(); }
  });

  document.addEventListener('keydown', function (ev) {
    if (ev.key === 'Escape' && !tiroir.hidden) { fermerTiroir(); }
  });

  recompter();
})();
