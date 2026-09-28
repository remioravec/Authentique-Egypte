#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Les filtres sur les pages circuits et profil, et une facette de plus.

    WP_AUTH='compte:mot de passe' ./outils/facettes-circuits.py [--essai]

« Enlever "au choix" et mettre un filtre » (#10737), « un filtre pour
trier les croisières selon les régions, le type de bateau et le budget »
(#10747), « ajouter un filtre croisière » (#10782), « enlever la phrase
et mettre un filtre » (#10787, #10842).

Le composant existe depuis les pages destination : durée et budget, en
cases à cocher, sans rechargement. On le porte ici, avec une troisième
facette — le type de séjour — qui répond au « filtre croisière ».

D'OÙ VIENT LE TYPE DE SÉJOUR

Des cinq pages de famille, lues à l'exécution : un séjour appartient aux
familles qui le listent. Six des dix y figurent dans plusieurs — une
croisière sur le Nil est à la fois « croisière » et « culturel ». Ce
n'est pas une ambiguïté à trancher, c'est le catalogue tel qu'il est.

D'où une correction au script : il comparait la valeur d'une carte à
celle d'une case, une contre une. Il compare maintenant des listes, et
une carte ressort dès qu'une de ses familles est cochée.

CE QUE JE NE FAIS PAS

Le tri par type de bateau qu'elle demande : felouque, dahabieh,
croisière 5★ n'apparaissent sur aucune fiche. La donnée n'existe pas, et
je ne vais pas la deviner d'après un titre.
"""

import argparse
import html as H_
import os
import re
import time
from importlib.machinery import SourceFileLoader

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MERE = 7642
Q = '/pages?parent=%d&per_page=100&status=any&context=edit&orderby=menu_order&order=asc'

FAC = SourceFileLoader('facettes_destination',
                       os.path.join(RACINE, 'outils', 'facettes-destination.py')).load_module()
H = FAC.H
DUREES, BUDGETS, MINIMUM = FAC.DUREES, FAC.BUDGETS, FAC.MINIMUM

# Les cinq familles, avec le nom qu'en donne le fil d'Ariane des pages
# programme. C'est lui qui fait foi : lire les cartes des pages de famille
# ramassait aussi leurs renvois croisés, et laissait quatre séjours sur
# quatorze sans classement.
FAMILLES = [('croisiere', 'Croisières', 'Croisières en Égypte'),
            ('desert', 'Désert et oasis', 'Déserts et Oasis égyptiens'),
            ('mer', 'Mer Rouge', 'Mer rouge et plongée'),
            ('sinai', 'Sinaï', 'Découverte du Sinaï'),
            ('culturel', 'Culturel', 'Voyage culturel en Égypte')]

# Les pages qui reçoivent les filtres : les six circuits et les quatre profils.
CIBLES = (8595, 8596, 8597, 8598, 8599, 8600, 8926, 8927, 8928, 8929)

# Le script d'origine comparait une valeur à une valeur. Avec une facette
# où une carte porte plusieurs familles, il faut comparer des listes.
SCRIPT = FAC.SCRIPT.replace(
    "        if(g[nom].indexOf(carte.dataset[nom]) < 0) return false;",
    "        var mien = (carte.dataset[nom] || '').split(' ').filter(Boolean);\n"
    "        if(!g[nom].some(function(v){ return mien.indexOf(v) >= 0; })) return false;"
).replace(
    "          return k.dataset[c.dataset.g] === c.value && garde(k, g, c.dataset.g);",
    "          return (k.dataset[c.dataset.g] || '').split(' ').indexOf(c.value) >= 0\n"
    "                 && garde(k, g, c.dataset.g);"
).replace('data-facettes="v1"', 'data-facettes="v2"')

FEUILLE = FAC.FEUILLE.replace('data-facettes="v1"', 'data-facettes="v2"')


def _fin(h, d, nom):
    p = 0
    for t in re.finditer(r'<(/?)%s\b[^>]*>' % nom, h[d:]):
        p += 1 if not t.group(1) else -1
        if p == 0:
            return d + t.end()
    return -1


def duree_de(c):
    """La durée, où qu'elle soit écrite sur la carte.

    Les pages circuits ne la mettent ni dans une puce ni sur la photo,
    mais dans la liste des points forts — « 4 jours minimum ». Sans ce
    troisième endroit, quatorze cartes sur la page mère n'avaient aucune
    durée, donc aucune tranche, donc aucun filtre.
    """
    j, _ = FAC.lire_carte(c)
    if j is not None:
        return j
    m = re.search(r'<span>\s*(\d+)\s*jours?\b', c)
    return int(m.group(1)) if m else None


def prix_de(c):
    return FAC.lire_carte(c)[1]


def _cle(t):
    """Un titre réduit à ce qui l'identifie.

    La carte écrit « l&#x27;Oasis », le titre de la page « l’Oasis » :
    une fois déséchappées, l'une a l'apostrophe droite et l'autre la
    courbe. Deux séjours sur quatorze échappaient au classement pour
    ce seul caractère.
    """
    t = H_.unescape(re.sub(r'<[^>]+>', '', t or ''))
    t = t.replace('\u2019', "'").replace('\u2018', "'")
    return re.sub(r'\s+', ' ', t).strip().lower()


def _titre(h):
    m = re.search(r'<h1[^>]*>(.*?)</h1>', h, re.S)
    return _cle(m.group(1)) if m else ''


def table_familles(pages):
    """Titre du séjour → sa famille, lue dans son propre fil d'Ariane.

    Chaque page programme annonce sa famille : « Accueil / Nos séjours en
    Égypte / Croisières en Égypte / Croisière sur le lac Nasser ». C'est
    la seule source qui les couvre toutes les quatorze.
    """
    table = {}
    for h in pages.values():
        if '<h1' not in h:
            continue
        fil = re.search(r'<nav class="ariane[^"]*"[^>]*>.*?</nav>', h, re.S)
        if not fil:
            continue
        texte = re.sub(r'<[^>]+>', ' ', fil.group(0))
        t = _titre(h)
        if not t:
            continue
        for cle, _, libelle in FAMILLES:
            if libelle in texte:
                table.setdefault(t, set()).add(cle)
    return table


def _groupe_familles(cartes, table):
    lignes = []
    for cle, nom, _ in FAMILLES:
        n = sum(1 for c in cartes if cle in c['familles'])
        if not n:
            continue
        lignes.append(
            '<label class="fac__o"><input type="checkbox" data-g="famille" value="%s">'
            '<b>%s</b><small>%d</small></label>' % (cle, nom, n))
    if len(lignes) < 2:
        return ''
    return ('<fieldset class="fac__g"><legend>Type de séjour</legend>%s</fieldset>'
            % ''.join(lignes))


def refaire(bloc, table):
    cartes = re.findall(r'<article class="carte"[^>]*>.*?</article>', bloc, re.S)
    if len(cartes) < 2:
        return bloc, None

    lues = []
    for c in cartes:
        t = re.search(r'<h3[^>]*>(?:<a[^>]*>)?(.*?)(?:</a>)?</h3>', c, re.S)
        nom = _cle(t.group(1)) if t else ''
        lues.append({'html': c, 'duree': duree_de(c), 'prix': prix_de(c),
                     'familles': table.get(nom, set())})

    neuves = []
    for x in lues:
        c = re.sub(r'<article class="carte"[^>]*>',
                   '<article class="carte" data-duree="%s" data-prix="%s" data-famille="%s">'
                   % (FAC._tranche(DUREES, x['duree']),
                      FAC._tranche(BUDGETS, x['prix']),
                      ' '.join(sorted(x['familles']))), x['html'], count=1)
        neuves.append(c)
    grille = '<div class="cartes cartes--2">%s</div>' % ''.join(neuves)

    groupes = ''
    if len(cartes) >= MINIMUM:
        groupes = (_groupe_familles(lues, table)
                   + FAC._groupe('duree', 'Durée', DUREES, lues, 'duree')
                   + FAC._groupe('prix', 'Budget', BUDGETS, lues, 'prix'))
    if not groupes:
        return ('<div class="fac" data-fac style="grid-template-columns:1fr">%s</div>'
                % grille), len(cartes)

    colonne = ('<details class="fac__pli" open><summary>Affiner la recherche</summary>'
               '<div class="fac__col"><div class="fac__tete"><p>Affiner</p>'
               '<button type="button" class="fac__raz" data-fac-raz hidden>Tout effacer'
               '</button></div>%s</div></details>' % groupes)
    return ('<div class="fac" data-fac>%s<div>'
            '<p class="fac__cpt" data-fac-cpt aria-live="polite">%d séjours</p>%s'
            '<p class="fac__rien" data-fac-rien hidden>Aucun séjour ne répond à ces '
            'critères. Retirez un filtre, ou <a href="https://authentiquegypte.com/'
            'sur-mesure/">demandez-nous un sur-mesure</a>.</p></div></div>'
            % (colonne, len(cartes), grille)), len(cartes)


def sans_vieux_filtre(h):
    """L'ancien filtre à boutons radio cède la place aux facettes."""
    d = h.find('<div class="filtre">')
    if d < 0:
        return h, False
    f = _fin(h, d, 'div')
    return (h[:d] + h[f:], True) if f > 0 else (h, False)


def corriger(h, pid, table):
    if pid not in CIBLES:
        return h, []
    faits = []

    h, ok = sans_vieux_filtre(h)
    if ok:
        faits.append('ancien filtre retiré')

    # « Au choix » ne dit rien ; le bloc porte maintenant des filtres.
    if '<p class="eyebrow">Au choix</p>' in h:
        h = h.replace('<p class="eyebrow">Au choix</p>',
                      '<p class="eyebrow">Trouvez le vôtre</p>')
        faits.append('« Au choix » remplacé (#10737)')

    # La phrase que les pages profil remplacent par un filtre.
    # L'espace insécable et l'apostrophe droite : chercher la phrase
    # telle qu'on l'écrit ne la trouve pas telle qu'elle est écrite.
    neuf = re.sub(r'<p class="lede"[^>]*>Tous personnalisables.{0,90}?</p>', '', h, flags=re.S)
    if neuf != h:
        h = neuf
        faits.append('phrase remplacée par les filtres (#10787, #10842)')

    d = h.find('<div class="fac"')
    if d < 0:
        d = h.find('<div class="cartes')
    if d < 0:
        return h, faits
    f = _fin(h, d, 'div')
    if f < 0:
        return h, faits
    neuf, n = refaire(h[d:f], table)
    if n is not None and neuf != h[d:f]:
        h = h[:d] + neuf + h[f:]
        faits.append('%d cartes%s' % (n, ' + facettes' if 'fac__g' in neuf else ''))

    if not faits:
        return h, faits
    ancienne = re.search(r'<style data-facettes="v2">.*?</style>', h, re.S)
    if not ancienne or ancienne.group(0) != FEUILLE:
        h = re.sub(r'<style data-facettes="v[12]">.*?</style>', '', h, flags=re.S)
        h = re.sub(r'<script data-facettes="v[12]">.*?</script>', '', h, flags=re.S)
        h += FEUILLE + SCRIPT
    return h, faits


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--essai', action='store_true')
    a = p.parse_args()
    dep = SourceFileLoader('dep', os.path.join(RACINE, 'outils', 'deployer.py')).load_module()

    pages = []
    for d in dep.appel('GET', Q % MERE):
        if d['status'] == 'trash':
            continue
        pages += [k for k in dep.appel('GET', Q % d['id']) if k['status'] != 'trash']

    brut = {}
    for k in pages:
        p_ = dep.appel('GET', '/pages/%d?context=edit' % k['id'])
        brut[k['id']] = (re.sub(r'<!-- /?wp:html -->\n?', '', p_['content']['raw']),
                         (p_.get('title') or {}).get('raw', ''))

    table = table_familles({i: h for i, (h, _) in brut.items()})
    print('   %d séjours classés par famille\n' % len(table))

    n = 0
    for pid, (h, titre) in brut.items():
        neuf, faits = corriger(h, pid, table)
        if not faits:
            continue
        print('   #%-6d %-34s %s' % (pid, titre[:34], ' · '.join(faits)[:74]))
        if a.essai:
            continue
        n += 1
        corps = '<!-- wp:html -->\n' + neuf + '\n<!-- /wp:html -->'
        for essai in range(4):
            try:
                dep.appel('POST', '/pages/%d' % pid, {'content': corps})
                relu = dep.appel('GET', '/pages/%d?context=edit' % pid)
                if 'data-facettes="v2"' in relu['content']['raw']:
                    break
            except SystemExit as motif:
                print('      reprise %d/3 — %s' % (essai + 1, str(motif).splitlines()[0][:60]))
            time.sleep(2 ** essai)
        else:
            print('      ✗ ABANDON #%d' % pid)
    print('\n%d page(s) corrigée(s).' % n)


if __name__ == '__main__':
    main()
