#!/usr/bin/env python3
"""
Relève tout le contenu du site et le range par gabarit.

C'est l'étape 1 et 2 du chantier : savoir ce qu'il y a, et de quel type
est chaque page. Rien n'est modifié sur le site — lecture seule.

    WP_AUTH="identifiant:mot de passe" ./outils/inventaire.py

Écrit docs/inventaire.json (la donnée) et docs/inventaire.md (le tableau
à relire). Le classement suit le même vocabulaire que l'extension
AE Back-office, pour que les deux disent la même chose.
"""

import base64
import json
import os
import re
import sys
import urllib.request

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = 'https://authentiquegypte.com'
API = SITE + '/wp-json/wp/v2'

# Les pages déjà refaites en maquette : on ne les reprend pas.
DEJA = {7642, 7643, 7644, 7645, 7646, 7655, 7656, 7657, 7658}

# La page mère des catégories de séjours.
MERE_SEJOURS = 116

GABARITS = {
    'accueil':    'Accueil',
    'categorie':  'Catégorie de séjours',
    'voyage':     'Fiche voyage',
    'destination': 'Destination',
    'qui-part':   'Qui part',
    'hub-guides': 'Hub des guides',
    'guide':      'Guide',
    'devis':      'Demande de devis',
    'agence':     'Agence',
    'legal':      'Mentions légales',
    'technique':  'Technique',
}

# Ce qui ne se déduit pas d'une règle : on le nomme.
FORCES = {
    'nos-sejours-egypte': 'categorie',
    'qui-sommes-nous': 'agence',
    'sur-mesure': 'devis',
    'notre-blog': 'hub-guides',
    'mentions-legales-agence-voyage-egypte': 'legal',
    'newsletter': 'technique',
    'voyage-sur-mesure-en-egyptepart': 'accueil',
    'voyage-en-couple-en-egypte': 'qui-part',
    'voyage-en-famille-en-egypte': 'qui-part',
    'voyage-solo-en-egypte': 'qui-part',
    'voyage-pmr-en-egypte': 'qui-part',
}

DESTINATIONS = re.compile(
    r'^(voyage-a-|voyage-au-|desert-|mont-|lac-)', re.I)


def deduire(item, type_wp):
    """Le gabarit d'un contenu. L'ordre des tests fait la règle."""
    slug = item.get('slug', '')

    if slug in FORCES:
        return FORCES[slug]
    if type_wp == 'programs':
        return 'voyage'
    if type_wp == 'posts':
        return 'guide'
    if item.get('parent') == MERE_SEJOURS:
        return 'categorie'
    if DESTINATIONS.match(slug):
        return 'destination'
    return 'autre'


def lire(auth, chemin):
    r = urllib.request.Request(API + chemin, headers={'Authorization': 'Basic ' + auth})
    with urllib.request.urlopen(r, timeout=120) as rep:
        return json.loads(rep.read().decode())


def tout(auth, base):
    sortie, page = [], 1
    while True:
        lot = lire(auth, '/%s?per_page=100&page=%d&status=publish&context=edit' % (base, page))
        sortie += lot
        if len(lot) < 100:
            return sortie
        page += 1


def sans_balises(html):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', html or '')).strip()


def main():
    auth_brut = os.environ.get('WP_AUTH')
    if not auth_brut:
        sys.exit('WP_AUTH manquant : WP_AUTH="identifiant:mot de passe" ./outils/inventaire.py')
    auth = base64.b64encode(auth_brut.encode()).decode()

    releve = []
    for base in ('pages', 'posts', 'programs'):
        for item in tout(auth, base):
            if item['id'] in DEJA:
                continue
            html = item.get('content', {}).get('raw', '') or ''
            images = []
            for src in re.findall(r'<img[^>]+src="([^"]+)"', html):
                if src not in images:
                    images.append(src)
            releve.append({
                'id': item['id'],
                'type': base,
                'slug': item.get('slug', ''),
                'titre': sans_balises(item.get('title', {}).get('raw', '')),
                'url': item.get('link', ''),
                'gabarit': deduire(item, base),
                'parent': item.get('parent', 0),
                'mots': len(sans_balises(html).split()),
                'images': images,
                'modifie': item.get('modified', ''),
            })

    releve.sort(key=lambda x: (list(GABARITS).index(x['gabarit']) if x['gabarit'] in GABARITS else 99,
                               -x['mots']))

    dossier = os.path.join(RACINE, 'docs')
    os.makedirs(dossier, exist_ok=True)
    with open(os.path.join(dossier, 'inventaire.json'), 'w', encoding='utf-8') as f:
        json.dump(releve, f, ensure_ascii=False, indent=1)

    lignes = ['# Inventaire du site, rangé par gabarit', '',
              'Relevé automatique, lecture seule. Les huit pages déjà refaites en '
              'maquette sont exclues.', '',
              '**%d contenus à reprendre.**' % len(releve), '']
    for cle, nom in GABARITS.items():
        lot = [x for x in releve if x['gabarit'] == cle]
        if not lot:
            continue
        lignes += ['## %s — %d' % (nom, len(lot)), '',
                   '| Titre | Type | Mots | Images | URL |', '|---|---|---:|---:|---|']
        for x in lot:
            lignes.append('| %s | %s | %d | %d | %s |' % (
                x['titre'].replace('|', '/'), x['type'], x['mots'], len(x['images']), x['url']))
        lignes.append('')
    orphelins = [x for x in releve if x['gabarit'] not in GABARITS]
    if orphelins:
        lignes += ['## Non classés — %d' % len(orphelins), '']
        for x in orphelins:
            lignes.append('- %s (%s) — %s' % (x['titre'], x['type'], x['url']))
        lignes.append('')

    with open(os.path.join(dossier, 'inventaire.md'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(lignes))

    print('%d contenus relevés.' % len(releve))
    for cle, nom in GABARITS.items():
        n = len([x for x in releve if x['gabarit'] == cle])
        if n:
            print('  %-22s %2d' % (nom, n))
    if orphelins:
        print('  %-22s %2d  ← à nommer' % ('NON CLASSÉS', len(orphelins)))
        for x in orphelins:
            print('        %s (%s)' % (x['slug'], x['type']))


if __name__ == '__main__':
    main()
