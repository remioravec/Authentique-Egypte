#!/usr/bin/env python3
"""La fiche de l'agence en JSON-LD, et la note qu'elle affiche.

    python3 outils/agence-et-note.py --essai
    WP_AUTH='compte:mdp' python3 outils/agence-et-note.py --appliquer

Deux gestes qui vont ensemble, et dans cet ordre : on affiche, puis on
déclare. La règle tenue depuis le début sur ce site — ne jamais déclarer
en JSON-LD ce que la page ne montre pas — vaut ici plus qu'ailleurs :
Google demande explicitement que la note soit visible pour la prendre.

La donnée vient de la fiche Google Business de l'agence, relevée le
25 septembre 2026 : 4,9 sur 5, 24 avis, dont 22 à cinq étoiles et 2 à
quatre. Le `place_id` de la fiche relevée — ChIJOZOsXzk5WBQRMujsdlYsBy8
— est exactement celui du lien « Voir les avis sur Google » que le site
porte déjà : c'est la même fiche, la preuve est datée et vérifiable.

Le compteur affiché disait « 23 avis · relevé le 10 septembre 2026 ». On
le met à jour avec la note et la date du nouveau relevé.

Une chose à savoir, et qu'il faut dire : Google ne fabrique pas d'étoiles
dans ses résultats à partir d'un avis qu'une entreprise porte sur
elle-même. Ce balisage ne fera donc pas apparaître d'étoiles dans la
SERP. Il sert ailleurs : les moteurs de réponse lisent cette donnée, et
c'est là qu'elle compte.
"""

import argparse
import base64
import json
import os
import re
import time

import requests

SITE = 'https://authentiquegypte.com'
RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ID = SITE + '/#agence'
RELEVE = '25 septembre 2026'

FICHE = {
    '@context': 'https://schema.org',
    '@type': 'TravelAgency',
    '@id': ID,
    'name': 'Authentique Égypte',
    'url': SITE + '/',
    'description': ("Agence de voyage francophone basée au Caire, spécialisée "
                    "dans les séjours sur mesure en Égypte."),
    'telephone': '+201066619098',
    'email': 'contact@authentiquegypte.com',
    'address': {'@type': 'PostalAddress', 'streetAddress': '16 Al Goalf, Maadi',
                'addressLocality': 'Le Caire', 'postalCode': '11728',
                'addressRegion': 'Gouvernorat du Caire', 'addressCountry': 'EG'},
    'geo': {'@type': 'GeoCoordinates', 'latitude': 29.968, 'longitude': 31.268},
    'openingHoursSpecification': [{
        '@type': 'OpeningHoursSpecification',
        'dayOfWeek': ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday'],
        'opens': '09:00', 'closes': '17:00'}],
    'sameAs': [
        'https://search.google.com/local/reviews?placeid=ChIJOZOsXzk5WBQRMujsdlYsBy8',
        ('https://www.tripadvisor.fr/Attraction_Review-g294201-d15316887-Reviews-'
         'Authentique_Egypte-Cairo_Cairo_Governorate.html')],
    'aggregateRating': {'@type': 'AggregateRating', 'ratingValue': '4.9',
                        'reviewCount': 24, 'bestRating': '5', 'worstRating': '1'},
}

ANCIEN_CPT = re.compile(
    r'(<p class="mur__cpt">)(.*?)(</p>)', re.S)
NEUF_CPT = ('<b>4,9 sur 5 · 24 avis Google sur l&#x27;agence</b>'
            '<small>Relevé sur la fiche le ' + RELEVE + '</small>')
BLOC = ('<script type="application/ld+json" data-agence>'
        + json.dumps(FICHE, ensure_ascii=False) + '</script>')


def corriger(h):
    """Rend le contenu corrigé et le compte des gestes."""
    j = {'compteur': 0, 'fiche': 0}
    if 'class="mur"' not in h:
        return h, j
    neuf, n = ANCIEN_CPT.subn(lambda m: m.group(1) + NEUF_CPT + m.group(3), h)
    j['compteur'] = n
    if 'data-agence' not in neuf:
        neuf += BLOC
        j['fiche'] = 1
    return neuf, j


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
    man = json.load(open(os.path.join(
        RACINE, 'sauvegarde/avant-mise-en-ligne/2026-10-02/MANIFESTE.json')))

    total = {'compteur': 0, 'fiche': 0}
    touchees = []
    for c in man['couples']:
        r = S.get(B + '%s/%d' % (c['type'], c['cible']),
                  params={'context': 'edit'}, timeout=120)
        h = (r.json().get('content') or {}).get('raw', '')
        neuf, j = corriger(h)
        if neuf == h:
            continue
        for k in total:
            total[k] += j[k]
        touchees.append((c, neuf, j))

    print('%d page(s) à toucher · compteur %d · fiche %d'
          % (len(touchees), total['compteur'], total['fiche']))
    if touchees:
        _, n1, _ = touchees[0]
        i = n1.find('<p class="mur__cpt">')
        print('   compteur après : %s'
              % re.sub(r'<[^>]+>', ' | ', n1[i:i + 220]).strip()[:150])
    # contrôle : le JSON écrit doit se relire
    json.loads(json.dumps(FICHE))
    print('   fiche JSON-LD : %d octets, relecture OK' % len(json.dumps(FICHE)))

    if a.essai:
        return

    for c, neuf, j in touchees:
        charge = {'content': '<!-- wp:html -->\n' + neuf + '\n<!-- /wp:html -->'}
        for essai in range(4):
            r = S.post(B + '%s/%d' % (c['type'], c['cible']), json=charge, timeout=300)
            if r.status_code < 300:
                break
            time.sleep(2 ** essai)
        else:
            raise SystemExit('écriture refusée sur %s' % c['url'])
        print('   %-9s #%-6d %s' % (c['type'], c['cible'], c['url'].replace(SITE, '')))
    print('\n%d page(s) écrites.' % len(touchees))


if __name__ == '__main__':
    main()
