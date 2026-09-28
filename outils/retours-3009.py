#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Les dix retours arrivés pendant la nuit, et les sept que je peux traiter.

    WP_AUTH='compte:mot de passe' ./outils/retours-3009.py [--essai]

Presque tous sur la page mère des séjours.

#11272, « il me semble qu'il y a plus de programmes avec des croisières ».
Elle a raison, et j'ai vérifié un par un. Le filtre s'appuyait sur le fil
d'Ariane, qui donne la famille du catalogue : trois séjours y sont rangés
sous Croisières. Mais deux autres embarquent pour de vrai — « Embarquement
sur bateau à voile traditionnel (dahabieh) pour 4-5 jours de navigation »
pour le roadtrip, « embarquement sur votre bateau de croisière » pour les
Pyramides en famille. Ils rejoignent le filtre.

Un troisième, Découverte de la Nubie, ne le rejoint pas : son déroulé ne
porte qu'une balade en felouque, et une balade n'est pas une croisière.
C'est la différence entre lire un mot et lire ce qu'il dit.

#11273, sur « Trouvez le vôtre », que j'avais posé hier à la place de « au
choix » : elle demande de l'enlever ou de dire que les programmes sont
personnalisables, avec un bouton de contact. La seconde branche vaut mieux
que la première — on ne retire pas une amorce, on lui donne un sens.

#11275, « enlever les majuscules à chaque mot ». Deux titres du site les
portent : « Demandez un Devis Personnalisé » et « Mon Conseiller Santé
Égypte ».

#11277 était déjà fait avant qu'elle ne l'écrive : les liens Google et
TripAdvisor sont sur cette page depuis hier soir.
"""

import argparse
import os
import re
import time
from importlib.machinery import SourceFileLoader

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MERE = 7642
Q = '/pages?parent=%d&per_page=100&status=any&context=edit&orderby=menu_order&order=asc'
E = '.elementor-template-canvas '
DEVIS = 'https://authentiquegypte.com/sur-mesure/'

# Les lieux mis en gras dans le paragraphe d'accueil (#11276). Liste
# explicite : repérer les majuscules mettrait en gras « Que », « Grâce »
# et tous les débuts de phrase.
LIEUX = ['Pyramides de Gizeh', 'Nil', 'mer Rouge', 'Égypte']

# Les séjours dont le déroulé porte un embarquement, et que le fil
# d'Ariane range pourtant ailleurs (#11272).
CROISIERES = ['Roadtrip en Égypte sur mesure',
              'Pyramides, croisière et mer rouge en famille']

MAJUSCULES = [('Demandez un Devis Personnalisé', 'Demandez un devis personnalisé'),
              ('Mon Conseiller Santé Égypte', 'Mon conseiller santé Égypte')]

AMORCE = ('<p class="eyebrow">Tous personnalisables</p>')
SOUS_TITRE = ('<p class="sejours__note">Chaque programme est un point de départ&nbsp;: '
              'la durée, les étapes et les hébergements s’ajustent à ce que vous '
              'voulez. <a href="%s">Dites-nous ce que vous cherchez</a>.</p>' % DEVIS)

BOUTON_CONTACT = ('<p class="asavoir__cta"><a class="btn btn--or btn--sm" href="%s">'
                  'Nous contacter</a></p>' % DEVIS)

FEUILLE = (
    '<style data-r3009="1">'
    + E + '.pg .sejours__note{margin:0 0 20px;max-width:64ch;font-size:1rem;'
    'line-height:1.6;color:var(--texte,#5D5D5D)}'
    + E + '.pg .sejours__note a{color:var(--teal-txt,#10657C);text-decoration:underline;'
    'text-underline-offset:2px}'
    + E + '.pg .asavoir__cta{margin:14px 0 0}'
    + E + '.pg .asavoir__b b{color:var(--nuit-900,#094D60);font-weight:700}'
    '</style>')


def _fin(h, d, nom):
    p = 0
    for t in re.finditer(r'<(/?)%s\b[^>]*>' % nom, h[d:]):
        p += 1 if not t.group(1) else -1
        if p == 0:
            return d + t.end()
    return -1


def boutons_en_couleur(h):
    """« Voir le séjour » passe du contour au plein (#11269)."""
    neuf = re.sub(r'<a class="btn btn--fantome btn--sm"([^>]*)>Voir le séjour</a>',
                  r'<a class="btn btn--or btn--sm"\1>Voir le séjour</a>', h)
    return neuf, neuf != h


def croisiere_en_plus(h):
    """Les deux séjours qui embarquent rejoignent le filtre (#11272)."""
    n = 0
    morceaux = re.split(r'(?=<article class="carte)', h)
    for i, c in enumerate(morceaux):
        if not c.startswith('<article class="carte'):
            continue
        if not any(s in c for s in CROISIERES):
            continue
        m = re.search(r'data-famille="([^"]*)"', c)
        if not m or 'croisiere' in m.group(1).split():
            continue
        vals = ' '.join(sorted(set(m.group(1).split() + ['croisiere'])))
        morceaux[i] = c.replace(m.group(0), 'data-famille="%s"' % vals, 1)
        n += 1
    if not n:
        return h, 0
    h = ''.join(morceaux)
    # Le compteur de la case doit suivre, sinon il annonce trois séjours
    # et la liste en montre cinq.
    total = len(re.findall(r'data-famille="[^"]*\bcroisiere\b[^"]*"', h))
    h = re.sub(r'(<input type="checkbox" data-g="famille" value="croisiere">'
               r'<b>Croisières</b><small>)\d+(</small>)',
               r'\g<1>%d\g<2>' % total, h)
    return h, n


def amorce_et_note(h, pid):
    """« Trouvez le vôtre » prend un sens, et renvoie au sur-mesure (#11273)."""
    if pid != 8598 or 'sejours__note' in h:
        return h, False
    av = '<p class="eyebrow">Trouvez le vôtre</p><h2>Nos séjours</h2>'
    if av not in h:
        return h, False
    return h.replace(av, AMORCE + '<h2>Nos séjours</h2>' + SOUS_TITRE), True


def bouton_contact(h, pid):
    """Le bloc « demandez un devis » gagne son bouton (#11274)."""
    if pid != 8598 or 'asavoir__cta' in h:
        return h, False
    i = h.find('Demandez un devis personnalisé')
    if i < 0:
        i = h.find('Demandez un Devis Personnalisé')
    if i < 0:
        return h, False
    d = h.rfind('<div class="asavoir__b">', 0, i)
    if d < 0:
        return h, False
    f = _fin(h, d, 'div')
    if f < 0:
        return h, False
    pose = f - len('</div>')
    return h[:pose] + BOUTON_CONTACT + h[pose:], True


def gras_intro(h, pid):
    """Les lieux du paragraphe d'accueil ressortent (#11276)."""
    if pid != 8598:
        return h, False
    m = re.search(r'(<h3>Nos séjours en Égypte</h3><p>)(.*?)(</p>)', h, re.S)
    if not m or '<b>' in m.group(2):
        return h, False
    corps = m.group(2)
    for lieu in sorted(LIEUX, key=len, reverse=True):
        corps = re.sub(r'(?<!<b>)\b%s\b(?!</b>)' % re.escape(lieu),
                       '<b>%s</b>' % lieu, corps, count=1)
    if corps == m.group(2):
        return h, False
    return h[:m.start()] + m.group(1) + corps + m.group(3) + h[m.end():], True


def corriger(h, pid):
    faits = []
    h, ok = boutons_en_couleur(h)
    if ok:
        faits.append('boutons « Voir le séjour » en couleur (#11269)')
    h, n = croisiere_en_plus(h)
    if n:
        faits.append('%d séjour(s) ajouté(s) au filtre croisière (#11272)' % n)
    for av, ap in MAJUSCULES:
        if av in h:
            h = h.replace(av, ap)
            faits.append('majuscules retirées (#11275)')
    h, ok = amorce_et_note(h, pid)
    if ok:
        faits.append('amorce et renvoi au sur-mesure (#11273)')
    h, ok = bouton_contact(h, pid)
    if ok:
        faits.append('bouton de contact (#11274)')
    h, ok = gras_intro(h, pid)
    if ok:
        faits.append('lieux en gras (#11276)')
    if not faits:
        return h, faits
    if 'data-r3009="1"' not in h:
        h += FEUILLE
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
        print('   #%-6d %-32s %s' % (k['id'], (p_.get('title') or {}).get('raw', '')[:32],
                                     ' · '.join(faits)[:80]))
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
