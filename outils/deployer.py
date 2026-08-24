#!/usr/bin/env python3
"""
Déploie les maquettes en pages BROUILLON sur authentiquegypte.com.

Ce que le script fait :
  – crée (ou retrouve) une page mère « Refonte 2026 », en brouillon ;
  – crée (ou retrouve) une page brouillon par maquette, sous cette mère ;
  – applique le gabarit Elementor Canvas, qui sert un <body> nu, sans
    en-tête ni pied de thème ;
  – transforme la maquette avec outils/vers-page-wp.py ;
  – réécrit les liens entre maquettes vers les URL WordPress réelles ;
  – ne publie rien, ne touche à aucune page existante, ne modifie ni les
    menus, ni les redirections, ni le contenu en ligne.

Il est idempotent : relancé, il met à jour les mêmes pages au lieu d'en
créer de nouvelles. La reconnaissance se fait sur le slug.

Identifiants attendus dans la variable d'environnement WP_AUTH, au format
`identifiant:mot de passe d'application`.

    WP_AUTH='moncompte:xxxx xxxx xxxx' ./outils/deployer.py
"""

import json
import os
import re
import subprocess
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = 'https://authentiquegypte.com'
API = SITE + '/wp-json/wp/v2'

sys.path.insert(0, os.path.join(RACINE, 'outils'))
from importlib.machinery import SourceFileLoader
_vers = SourceFileLoader('vers_page_wp', os.path.join(RACINE, 'outils', 'vers-page-wp.py')).load_module()

# Le parcours de relecture, dans l'ordre. Le libellé « cible » indique la
# page du site en ligne que la maquette remplacera à terme ; il ne sert
# ici qu'à documenter, aucune redirection n'est posée.
PARCOURS = [
    {
        'fichier': 'index.html',
        'slug': 'accueil',
        'titre': 'Refonte · Accueil',
        'cible': SITE + '/',
    },
    {
        'fichier': 'categorie-desert.html',
        'slug': 'categorie-voyage-desert',
        'titre': 'Refonte · Catégorie — Voyage dans le désert',
        'cible': SITE + '/nos-sejours-egypte/desert-egypte/',
    },
    {
        'fichier': 'produit-siwa.html',
        'slug': 'voyage-oasis-de-siwa',
        'titre': 'Refonte · Voyage — Oasis de Siwa',
        'cible': SITE + '/programs/excursion-a-loasis-de-siwa/',
    },
    {
        'fichier': 'article-quand-partir.html',
        'slug': 'guide-quand-partir-en-egypte',
        'titre': 'Refonte · Guide — Quand partir en Égypte',
        'cible': SITE + '/quand-partir-en-egypte/',
    },
    {
        'fichier': 'blog.html',
        'slug': 'hub-guides-pratiques',
        'titre': 'Refonte · Hub — Guides pratiques',
        'cible': SITE + '/notre-blog/',
    },
    {
        'fichier': 'destination.html',
        'slug': 'destination-le-caire',
        'titre': 'Refonte · Destination — Voyage au Caire',
        'cible': SITE + '/voyage-au-caire/',
    },
    {
        'fichier': 'qui-sommes-nous.html',
        'slug': 'agence-qui-sommes-nous',
        'titre': 'Refonte · Agence — Qui sommes-nous',
        'cible': SITE + '/qui-sommes-nous/',
    },
    {
        'fichier': 'devis.html',
        'slug': 'demande-de-devis',
        'titre': 'Refonte · Devis — Demande de devis',
        'cible': SITE + '/sur-mesure/',
    },
]

PARENT_SLUG = 'refonte-2026'
PARENT_TITRE = 'Refonte 2026'


def auth():
    valeur = os.environ.get('WP_AUTH', '').strip()
    if not valeur or ':' not in valeur:
        sys.exit("WP_AUTH manquant. Format attendu : 'identifiant:mot de passe d application'")
    return valeur


def appel(methode, chemin, charge=None, params=''):
    """Un appel REST, via curl pour rester dans le proxy sortant de la session."""
    commande = ['curl', '-s', '--max-time', '120', '-u', auth(), '-X', methode,
                API + chemin + params]
    fichier = None
    if charge is not None:
        fichier = '/tmp/.ae-charge.json'
        with open(fichier, 'w', encoding='utf-8') as f:
            json.dump(charge, f, ensure_ascii=False)
        commande += ['-H', 'Content-Type: application/json', '--data-binary', '@' + fichier]

    brut = subprocess.run(commande, capture_output=True, text=True).stdout
    try:
        return json.loads(brut)
    except json.JSONDecodeError:
        sys.exit('Réponse illisible de %s :\n%s' % (chemin, brut[:400]))


def trouver_page(slug):
    resultat = appel('GET', '/pages', params='?slug=%s&status=any&per_page=1&context=edit' % slug)
    if isinstance(resultat, list) and resultat:
        return resultat[0]
    return None


def poser_page(slug, champs):
    """Crée la page si elle manque, la met à jour sinon. Toujours en brouillon."""
    existante = trouver_page(slug)
    if existante:
        reponse = appel('POST', '/pages/%d' % existante['id'], champs)
        action = 'mise à jour'
    else:
        champs = dict(champs, slug=slug, status='draft')
        reponse = appel('POST', '/pages', champs)
        action = 'créée'

    if 'id' not in reponse:
        sys.exit('Échec sur %s : %s' % (slug, reponse.get('message', reponse)))

    return reponse, action


def main():
    print('→ Page mère')
    mere, action = poser_page(PARENT_SLUG, {
        'title': PARENT_TITRE,
        'status': 'draft',
        'content': (
            '<!-- wp:paragraph --><p>Espace de refonte. Les pages filles sont '
            'des maquettes en brouillon : elles ne sont visibles que depuis un '
            'compte connecté disposant des droits d\'édition, et ne remplacent '
            'aucune page en ligne.</p><!-- /wp:paragraph -->'
        ),
    })
    print('   %s — id %d (%s)' % (PARENT_TITRE, mere['id'], action))

    # Premier passage : garantir l'existence de chaque page, pour connaître
    # les URL avant d'écrire les liens.
    print('→ Pages de maquette')
    pages = {}
    for rang, etape in enumerate(PARCOURS, start=1):
        page, action = poser_page(etape['slug'], {
            'title': etape['titre'],
            'status': 'draft',
            'parent': mere['id'],
            'menu_order': rang,
            'template': 'elementor_canvas',
        })
        pages[etape['fichier']] = page
        print('   %-28s id %-6d %s' % (etape['slug'], page['id'], action))

    # Un brouillon n'a pas d'URL propre : on passe par ?page_id=.
    liens = {f: '%s/?page_id=%d' % (SITE, p['id']) for f, p in pages.items()}
    # Les maquettes que nous n'avons pas encore produites gardent leur lien
    # local : elles doivent rester visiblement absentes, pas discrètement
    # redirigées ailleurs.

    print('→ Contenus')
    for etape in PARCOURS:
        chemin = os.path.join(RACINE, 'maquettes', etape['fichier'])
        with open(chemin, encoding='utf-8') as f:
            contenu = _vers.convertir(f.read(), os.path.join(RACINE, 'maquettes'))

        for fichier, url in liens.items():
            contenu = contenu.replace('href="%s"' % fichier, 'href="%s"' % url)

        page = pages[etape['fichier']]
        reponse = appel('POST', '/pages/%d' % page['id'], {'content': contenu})
        if 'id' not in reponse:
            sys.exit('Échec du contenu sur %s : %s' % (etape['slug'], reponse.get('message')))
        print('   %-28s %6d octets → %s' % (etape['slug'], len(contenu), liens[etape['fichier']]))

    print()
    print('Terminé. Toutes les pages sont en BROUILLON.')
    print('Aucune page existante n\'a été modifiée.')


if __name__ == '__main__':
    main()
