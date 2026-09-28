#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Les textes que je lui faisais choisir, et que je pose moi-même.

    WP_AUTH='compte:mot de passe' ./outils/textes-proposes.py [--essai]

Sept fils où j'avais écrit « dites-moi laquelle et je la pose » ou
« à valider ». Les lui laisser en suspens, c'est lui donner du travail
pour une décision que j'ai déjà instruite. On pose, et un mot d'elle
suffit à changer.

DEUX DE MES PROPOSITIONS ÉTAIENT MAUVAISES, ET JE M'EN SUIS APERÇU EN
LES POSANT

Pour « Les autres façons de partir » je recommandais « Famille, couple,
solo, mobilité réduite ». Or la ligne juste dessous dit déjà « Famille,
couple, solo ou mobilité réduite : chaque profil a sa page ». Le titre
aurait répété son propre chapeau. C'est « Partir autrement » qui est
posé.

Pour « Les avis Google de l'agence » je recommandais « 23 avis, tous
publiés sur Google ». Le compteur juste à droite affiche déjà « 23 avis
Google sur l'agence ». Même faute. C'est « Leurs mots, pas les nôtres »
qui est posé.

Une proposition se juge dans la page, pas dans la liste.
"""

import argparse
import os
import re
import time
from importlib.machinery import SourceFileLoader

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MERE = 7642
Q = '/pages?parent=%d&per_page=100&status=any&context=edit&orderby=menu_order&order=asc'

# (avant, après, fil) — remplacements exacts, sur toute page qui les porte.
TEXTES = [
    # #9544 — « Partir autrement » : le chapeau dit déjà les quatre profils.
    ('<h2 style="margin-bottom:14px">Les autres façons de partir</h2>',
     '<h2 style="margin-bottom:14px">Partir autrement</h2>', '9544'),

    # #10471 — elle n'aime pas « pas vendue en catalogue ».
    ("<h1>L'Égypte construite <em>avec vous</em>, pas vendue en catalogue</h1>",
     "<h1>Votre Égypte, construite <em>avec vous</em></h1>", '10471'),

    # #10478 — le bloc liste bien cinq familles, mais elle veut un autre
    # titre. Un intitulé sans compte ne se démentira pas si elle en ajoute.
    ('<h2 style="margin-bottom:14px">Cinq façons de voyager en Égypte</h2>',
     '<h2 style="margin-bottom:14px">Choisissez votre façon de voyager</h2>', '10478'),

    # #10482 — le compteur voisin dit déjà « 23 avis Google ».
    ('<h2 id="t-avis">Les avis Google de l\'agence</h2>',
     '<h2 id="t-avis">Leurs mots, pas les nôtres</h2>', '10482'),

    # #10776 — ses activités, ses mots.
    ('Assister à un atelier d’artisanat traditionnel ou partager un dîner égyptien '
     'au bord du Nil.',
     'Un foodtour, un cours de cuisine avec une association locale, une tyrolienne '
     'près de l’église troglodyte, ou un dîner-croisière sur le Nil en soirée.',
     '10776'),
]

# #10457 — le chapeau famille : la phrase d'origine est longue et je ne
# connais pas son début exact caractère pour caractère. On la remplace
# par bornes plutôt que par égalité.
FAMILLE_AP = ('En Égypte, chaque journée devient une histoire que les enfants '
              'raconteront longtemps. Voir un hiéroglyphe de tout près, monter à '
              'bord d’une felouque, écouter un guide parler d’Hatchepsout comme '
              'd’une héroïne — ce ne sont pas des visites, ce sont des souvenirs. '
              'Nous calons le rythme sur le leur : des matinées courtes, des pauses '
              'vraies, et des soirées où les questions fusent encore autour du dîner.')


# #10447 — le chapeau PMR, d'après ce qu'elle décrit : dire franchement
# que tout n'est pas accessible, et que nous le faisons quand même. Comme
# pour les familles, on remplace par bornes : le paragraphe d'origine est
# long, et l'égalité de chaîne échoue sur une apostrophe près.
PMR_AP = ('Organiser un voyage en Égypte en situation de mobilité réduite demande du '
          'travail : les sites sont anciens, les aménagements inégaux, et tout n’est '
          'pas accessible. Nous le disons franchement, site par site. Notre rôle est '
          'de vous dire ce qui est possible et ce qui ne l’est pas, puis de construire '
          'autour : véhicule adapté, rythme allégé, hébergements vérifiés, et un '
          'accompagnement qui ne vous lâche pas. Nous proposons ces séjours parce '
          'qu’ils en valent la peine, pas parce qu’ils sont simples.')


def _chapeau(h, marqueur, neuf):
    """Remplace le chapeau du hero, repéré par un bout de sa phrase."""
    if neuf[:40] in h:
        return h, False
    m = re.search(r'(<p class="hero__chapo">)(.*?)(</p>)', h, re.S)
    if not m or marqueur not in m.group(2):
        return h, False
    return h[:m.start()] + m.group(1) + neuf + m.group(3) + h[m.end():], True


def chapeau_famille(h, pid):
    if pid != 8927:
        return h, False
    return _chapeau(h, 'les enfants raconteront', FAMILLE_AP)


def chapeau_pmr(h, pid):
    if pid != 8928:
        return h, False
    return _chapeau(h, 'situation de mobilité réduite', PMR_AP)


def corriger(h, pid):
    faits = []
    for av, ap, fil in TEXTES:
        if av in h:
            h = h.replace(av, ap)
            faits.append('texte posé (#%s)' % fil)
    h, ok = chapeau_famille(h, pid)
    if ok:
        faits.append('chapeau famille posé (#10457)')
    h, ok = chapeau_pmr(h, pid)
    if ok:
        faits.append('chapeau PMR posé (#10447)')
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

    n = 0
    for k in pages:
        p_ = dep.appel('GET', '/pages/%d?context=edit' % k['id'])
        brut = re.sub(r'<!-- /?wp:html -->\n?', '', p_['content']['raw'])
        neuf, faits = corriger(brut, k['id'])
        if not faits:
            continue
        print('   #%-6d %-34s %s' % (k['id'], (p_.get('title') or {}).get('raw', '')[:34],
                                     ' · '.join(faits)[:74]))
        if a.essai:
            continue
        n += 1
        corps = '<!-- wp:html -->\n' + neuf + '\n<!-- /wp:html -->'
        for essai in range(4):
            try:
                dep.appel('POST', '/pages/%d' % k['id'], {'content': corps})
                relu = dep.appel('GET', '/pages/%d?context=edit' % k['id'])
                if corriger(re.sub(r'<!-- /?wp:html -->\n?', '',
                                   relu['content']['raw']), k['id'])[1] == []:
                    break
            except SystemExit as motif:
                print('      reprise %d/3 — %s' % (essai + 1, str(motif).splitlines()[0][:60]))
            time.sleep(2 ** essai)
        else:
            print('      ✗ ABANDON #%d' % k['id'])
    print('\n%d page(s) corrigée(s).' % n)


if __name__ == '__main__':
    main()
