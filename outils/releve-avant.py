#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
L'état du site avant la bascule, daté, pour pouvoir prouver après coup.

    WP_AUTH='compte:mot de passe' ./outils/releve-avant.py

Aucune URL ne change à la bascule : on remplace le contenu des pages en
ligne, elles gardent leur adresse. Donc rien ne devrait bouger côté
référencement. Mais « ne devrait pas » n'est pas une preuve, et le jour
où une position baisse, il faut pouvoir dire ce qui était vrai avant.

Ce que le relevé prend, pour les 58 cibles :

  – le titre et la description que Yoast sert aujourd'hui, et leur
    longueur ;
  – le code de réponse, la taille de la page et le temps de rendu ;
  – l'empreinte du contenu, pour repérer toute dérive ;
  – les ancres internes réellement visées par un lien de la page.

Sur ce dernier point, le relevé a corrigé ce que je supposais. Je
craignais que la refonte fasse disparaître des ancres visées de
l'extérieur. Vérification faite sur les pages en ligne : les seules
ancres utilisées sont #content, posée par le thème, et des
expand-xxxxxxx, engendrées par les accordéons d'Elementor. Aucune
n'est une ancre de contenu que quelqu'un aurait pu mettre dans un
lien, et celles d'Elementor disparaissent avec le contenu qui les
portait, en même temps que les liens qui les visaient. Rien à
préserver de ce côté.

Et pour le site : le sitemap, le robots.txt, et le décompte des URL
qu'ils annoncent.

Le fichier sort dans docs/releve-<date>.json. Le relancer après la
bascule donne les deux colonnes à comparer.
"""

import base64
import hashlib
import json
import os
import re
import sys
import time
from importlib.machinery import SourceFileLoader

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = 'https://authentiquegypte.com'
CARTE = os.path.join(RACINE, 'docs', 'carte-mise-en-ligne.json')


def main():
    import datetime
    import requests
    S = requests.Session()
    S.verify = '/root/.ccr/ca-bundle.crt'
    u, m = os.environ['WP_AUTH'].split(':', 1)
    S.headers['Authorization'] = 'Basic ' + base64.b64encode(('%s:%s' % (u, m)).encode()).decode()
    B = SITE + '/wp-json/wp/v2/'

    carte = json.load(open(CARTE))
    jour = datetime.date.today().isoformat()
    out = {'date': datetime.datetime.now().isoformat(timespec='seconds'),
           'site': SITE, 'cibles': {}, 'site_global': {}}

    # Le sitemap et le robots : ce que le site déclare de lui-même.
    for nom, chemin in (('robots', '/robots.txt'), ('sitemap', '/sitemap_index.xml')):
        try:
            r = S.get(SITE + chemin, timeout=40)
            out['site_global'][nom] = {'code': r.status_code, 'octets': len(r.content),
                                       'texte': r.text[:1800]}
            if nom == 'sitemap':
                out['site_global']['sitemaps'] = re.findall(r'<loc>([^<]+)</loc>', r.text)
        except Exception as e:
            out['site_global'][nom] = {'erreur': str(e)[:90]}

    n_url = 0
    for sm in out['site_global'].get('sitemaps', [])[:12]:
        try:
            r = S.get(sm, timeout=40)
            n_url += len(re.findall(r'<loc>', r.text))
        except Exception:
            pass
    out['site_global']['urls_au_sitemap'] = n_url

    for i, c in enumerate(carte):
        typ, cid, url = c['cible_type'], c['cible_id'], c['cible_url']
        e = {}
        try:
            r = S.get(B + '%s/%d' % (typ, cid), params={'context': 'edit'}, timeout=50).json()
            y = r.get('yoast_head_json') or {}
            brut = (r.get('content') or {}).get('raw', '')
            e['yoast_titre'] = y.get('title', '')
            e['yoast_desc'] = y.get('description', '')
            e['titre_car'] = len(e['yoast_titre'])
            e['desc_car'] = len(e['yoast_desc'])
            e['canonique'] = y.get('canonical', '')
            e['modele'] = r.get('template') or ''
            e['slug'] = r.get('slug')
            e['modifie'] = r.get('modified')
            e['octets'] = len(brut)
            e['empreinte'] = hashlib.sha1(brut.encode()).hexdigest()
        except Exception as ex:
            e['erreur_api'] = str(ex)[:90]
        try:
            t0 = time.time()
            r = S.get(url, timeout=50)
            e['code'] = r.status_code
            e['ms'] = int((time.time() - t0) * 1000)
            e['octets_servis'] = len(r.content)
            e['ancres'] = sorted(set(re.findall(r'\sid="(t-[a-z0-9-]+|s\d+|jour-\d+)"', r.text)))
            m2 = re.search(r'<title>(.*?)</title>', r.text, re.S)
            e['titre_servi'] = m2.group(1).strip() if m2 else ''
        except Exception as ex:
            e['erreur_page'] = str(ex)[:90]
        out['cibles']['%s-%d' % (typ, cid)] = e
        if (i + 1) % 10 == 0:
            print('   %d / %d' % (i + 1, len(carte)))
        time.sleep(0.25)

    chemin = os.path.join(RACINE, 'docs', 'releve-%s.json' % jour)
    json.dump(out, open(chemin, 'w'), ensure_ascii=False, indent=1)

    codes = {}
    for e in out['cibles'].values():
        codes[e.get('code', 'erreur')] = codes.get(e.get('code', 'erreur'), 0) + 1
    vides = [k for k, e in out['cibles'].items() if not e.get('yoast_desc')]
    longs = [k for k, e in out['cibles'].items() if e.get('titre_car', 0) > 60]
    courts = [k for k, e in out['cibles'].items() if 0 < e.get('desc_car', 0) < 70]
    anc = sum(len(e.get('ancres') or []) for e in out['cibles'].values())
    print('\n%s' % chemin)
    print('   %d cible(s) · codes %s' % (len(out['cibles']), codes))
    print('   %d URL au sitemap · robots %s'
          % (out['site_global'].get('urls_au_sitemap', 0),
             out['site_global'].get('robots', {}).get('code')))
    print('   %d ancre(s) interne(s) relevée(s)' % anc)
    print('   descriptions Yoast vides : %d' % len(vides))
    print('   titres au-delà de 60 caractères : %d' % len(longs))
    print('   descriptions en deçà de 70 caractères : %d' % len(courts))


if __name__ == '__main__':
    main()
