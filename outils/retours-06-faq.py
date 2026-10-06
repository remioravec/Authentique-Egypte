#!/usr/bin/env python3
"""Lot 2 : ranger les FAQ en catégories, et faire ressortir la réponse.

    WP_AUTH='compte:mdp' python3 outils/retours-06-faq.py --essai
    WP_AUTH='compte:mdp' python3 outils/retours-06-faq.py --appliquer

Mélanie, cinq fois : « globalement la FAQ est longue, est-ce possible de la
ranger en catégories ? » (12291, 12310, 12315, 12294), et en réponse à un
fil plus ancien : « est-ce possible de mettre des catégories pour la FAQ ? »
(10446). Elle a raison sur les chiffres : trente-deux pages portent dix
questions ou plus, et le mont Sinaï en compte trente-six.

Le gabarit prévoit déjà le titre de rubrique, `faq__t`, avec son filet : on
s'en sert plutôt que d'inventer une forme.

Quatre rubriques, dans l'ordre où l'on se pose les questions :

    Avant de partir   quand partir, combien de jours, météo, saison
    Sur place         que voir, se déplacer, dormir, manger
    Formalités et santé  visa, passeport, vaccins, argent, sécurité, tenue
    Organiser avec nous  devis, prix, sur mesure, groupe, guide, annulation

Une question qui ne tombe dans aucune garde sa place sous « Bon à savoir ».
L'ordre des questions change, leur texte jamais.

Et « est-ce possible de mettre en gras le texte important des FAQ ? »
(12309) : on ne met en gras que ce qui est vérifiable — la première donnée
chiffrée ou datée de la réponse, celle qu'on cherche du regard. Une période,
une durée, un prix, une température. Jamais une phrase choisie au jugé.
"""

import argparse
import base64
import json
import os
import re
import time
import unicodedata

import requests

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cibles

SITE = 'https://authentiquegypte.com'
RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEUIL = 10          # en deçà, une FAQ n'a pas besoin de rubriques

RUBRIQUES = [
    ('Avant de partir',
     ('quand partir', 'meilleure periode', 'periode', 'combien de jour',
      'combien de temps', 'duree', 'meteo', 'temperature', 'saison', 'climat',
      'chaleur', 'ramadan', 'affluence', 'reserver', 'a l avance')),
    ('Sur place',
     ('que voir', 'que faire', 'incontournable', 'site', 'visiter', 'visite',
      'deplacer', 'transport', 'bateau', 'croisiere', 'dormir', 'hebergement',
      'hotel', 'manger', 'restaurant', 'excursion', 'acces', 'distance',
      'journee type', 'lever du soleil', 'randonnee', 'plongee', 'snorkeling')),
    ('Formalités et santé',
     ('visa', 'passeport', 'formalite', 'vaccin', 'sante', 'medic', 'eau',
      'securite', 'dangereux', 'assurance', 'argent', 'monnaie', 'paiement',
      'carte bancaire', 'pourboire', 'tenue', 'habiller', 'vetement',
      'pharmacie', 'autorisation')),
    ('Organiser avec nous',
     ('devis', 'prix', 'tarif', 'budget', 'inclus', 'sur mesure',
      'personnalis', 'groupe', 'guide', 'chauffeur', 'annul', 'acompte',
      'modifier', 'combiner', 'adapte', 'enfant', 'famille', 'couple',
      'solo', 'mobilite', 'handicap', 'pmr')),
]
DEFAUT = 'Bon à savoir'

# une donnée qu'on cherche du regard : une période, une durée, un montant
# Les bornes de mot ne sont pas un détail : sans elles, « mai » se trouve
# dans « mais » et dans « jamais », et la mise en gras produit « mais ».
CHIFFRE = re.compile(
    r'(?<![^\W\d_])'
    r'((?:de\s+)?(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|'
    r'octobre|novembre|décembre)(?:\s+à\s+(?:janvier|février|mars|avril|mai|juin|'
    r'juillet|août|septembre|octobre|novembre|décembre))?'
    r'|\d+\s*(?:à\s*\d+\s*)?(?:jours?|nuits?|heures?|km|°C|€|minutes?))'
    r'(?![^\W\d_])',
    re.I)


def sa(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s)
                   if unicodedata.category(c) != 'Mn').lower()


def rubrique(question):
    q = sa(question)
    for nom, mots in RUBRIQUES:
        if any(mot in q for mot in mots):
            return nom
    return DEFAUT


def details(bloc):
    """Découpe une FAQ en <details>, bornés à la main."""
    out, i = [], 0
    while True:
        i = bloc.find('<details class="faq__q', i)
        if i < 0:
            break
        p, k = 0, i
        while k < len(bloc):
            if bloc.startswith('<details', k):
                p += 1
            elif bloc.startswith('</details>', k):
                p -= 1
                if p == 0:
                    k += len('</details>')
                    break
            k += 1
        out.append(bloc[i:k])
        i = k
    return out


def grasser(d):
    """Met en gras la première donnée chiffrée ou datée de la réponse."""
    i = d.find('<div class="faq__r">')
    if i < 0 or '<b>' in d or '<strong>' in d:
        return d, 0
    j = d.find('<p', i)
    if j < 0:
        return d, 0
    f = d.find('</p>', j)
    para = d[j:f]
    # On ne touche pas à l'intérieur d'une balise. Le motif ne doit pas
    # exiger un « < » final : le dernier morceau de texte d'un paragraphe
    # n'en a pas, et c'est justement là que se trouve le plus souvent la
    # donnée cherchée.
    textes = [(m.start(1), m.group(1)) for m in re.finditer(r'>([^<]+)', para)]
    for pos, t in textes:
        mm = CHIFFRE.search(t)
        if not mm:
            continue
        a, b = pos + mm.start(), pos + mm.end()
        neuf = para[:a] + '<b>' + para[a:b] + '</b>' + para[b:]
        return d[:j] + neuf + d[f:], 1
    return d, 0


def corriger(h):
    j = {'faq': 0, 'rubriques': 0, 'gras': 0}
    i = 0
    while True:
        i = h.find('<div class="faqu">', i)
        if i < 0:
            break
        p, k = 0, i
        while k < len(h):
            if h.startswith('<div', k):
                p += 1
            elif h.startswith('</div>', k):
                p -= 1
                if p == 0:
                    k += 6
                    break
            k += 1
        bloc = h[i:k]
        ds = details(bloc)
        if 'faq__t' in bloc or len(ds) < SEUIL:
            # on grasse quand même, sans ranger
            neuf = bloc
            for d in ds:
                g, n = grasser(d)
                if n:
                    neuf = neuf.replace(d, g, 1)
                    j['gras'] += n
            h = h[:i] + neuf + h[k:]
            i = i + len(neuf)
            continue

        groupes = {}
        for d in ds:
            q = re.search(r'<summary[^>]*>(.*?)</summary>', d, re.S)
            q = re.sub(r'<[^>]+>', '', q.group(1)) if q else ''
            g, n = grasser(d)
            j['gras'] += n
            groupes.setdefault(rubrique(q), []).append(g)

        morceaux = []
        for nom, _ in RUBRIQUES:
            if groupes.get(nom):
                morceaux.append('<p class="faq__t">%s</p>' % nom
                                + ''.join(groupes[nom]))
                j['rubriques'] += 1
        if groupes.get(DEFAUT):
            morceaux.append('<p class="faq__t">%s</p>' % DEFAUT
                            + ''.join(groupes[DEFAUT]))
            j['rubriques'] += 1
        neuf = '<div class="faqu">' + ''.join(morceaux) + '</div>'
        h = h[:i] + neuf + h[k:]
        j['faq'] += 1
        i = i + len(neuf)
    return h, j


def main():
    p = argparse.ArgumentParser()
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument('--essai', action='store_true')
    g.add_argument('--appliquer', action='store_true')
    a = p.parse_args()

    S = requests.Session(); S.verify = '/root/.ccr/ca-bundle.crt'
    u, m = os.environ['WP_AUTH'].split(':', 1)
    S.headers['Authorization'] = 'Basic ' + base64.b64encode(
        ('%s:%s' % (u, m)).encode()).decode()
    B = SITE + '/wp-json/wp/v2/'
    couples = cibles.toutes()

    total = {'faq': 0, 'rubriques': 0, 'gras': 0}
    a_ecrire = []
    for c in couples:
        d = S.get(B + '%s/%d' % (c['type'], c['cible']),
                  params={'context': 'edit'}, timeout=120).json()
        h = (d.get('content') or {}).get('raw', '')
        neuf, j = corriger(h)
        if neuf == h:
            continue
        # aucune question ne doit disparaître
        if neuf.count('<details class="faq__q') != h.count('<details class="faq__q'):
            raise SystemExit('question perdue sur %s' % c['url'])
        for k in total:
            total[k] += j[k]
        a_ecrire.append((c, neuf, j))

    print('FAQ rangées en rubriques : %d' % total['faq'])
    print('rubriques posées         : %d' % total['rubriques'])
    print('réponses mises en gras   : %d' % total['gras'])
    print('%d page(s) à écrire' % len(a_ecrire))
    if a.essai and a_ecrire:
        c, n1, _ = a_ecrire[0]
        i = n1.find('<div class="faqu">')
        ex = re.findall(r'<p class="faq__t">([^<]+)</p>', n1[i:i + 60000])
        print('\nexemple, %s : %s' % (c['url'].replace(SITE, ''), ' · '.join(ex)))
        m2 = re.search(r'<b>([^<]{3,40})</b>', n1[i:i + 60000])
        print('   première mise en gras : « %s »' % (m2.group(1) if m2 else '—'))
    if a.essai:
        return

    for c, neuf, j in a_ecrire:
        for essai in range(4):
            r = S.post(B + '%s/%d' % (c['type'], c['cible']),
                       json={'content': '<!-- wp:html -->\n' + neuf + '\n<!-- /wp:html -->'},
                       timeout=300)
            if r.status_code < 300:
                break
            time.sleep(2 ** essai)
        else:
            raise SystemExit('écriture refusée sur %s' % c['url'])
    print('\n%d page(s) écrites.' % len(a_ecrire))


if __name__ == '__main__':
    main()
