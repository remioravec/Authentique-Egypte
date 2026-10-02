#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bascule la refonte sur les URL en ligne, sans rien perdre.

    WP_AUTH='compte:mot de passe' ./outils/mise-en-ligne.py --essai
    WP_AUTH='compte:mot de passe' ./outils/mise-en-ligne.py --sauvegarder
    WP_AUTH='compte:mot de passe' ./outils/mise-en-ligne.py --appliquer
    WP_AUTH='compte:mot de passe' ./outils/mise-en-ligne.py --revenir

Le principe : on ne publie pas les brouillons, on remplace le CONTENU des
contenus déjà en ligne. Chaque page garde son URL, son identifiant, ses
liens entrants et son historique Yoast. Rien ne change d'adresse, donc
rien ne casse et aucune redirection n'est à poser.

Quatre temps, dans cet ordre, et jamais autrement :

  --essai         dit ce qui changerait, page par page, sans rien écrire.
  --sauvegarder   écrit l'état actuel des 57 cibles dans sauvegarde/,
                  contenu, gabarit, titre et slug. C'est le filet.
  --appliquer     bascule. Refuse de démarrer sans sauvegarde du jour.
  --revenir       remet la sauvegarde en place, dans l'autre sens.

Ce que la bascule fait à chaque cible :

  1. remplace le contenu par celui du brouillon apparié ;
  2. passe le gabarit à elementor_canvas — sans quoi le thème Astra
     ajouterait son en-tête et son pied à ceux que la page embarque
     déjà, et le visiteur verrait deux menus et deux pieds de page ;
  3. réécrit les liens de brouillon : ?page_id=8660 devient l'URL
     définitive de la cible correspondante. Il y en a 286 sur 22 pages,
     et l'un d'eux, ?page_id=9126, pointe vers une page à la corbeille.

Ce que la bascule ne touche pas, et ne doit jamais toucher : le titre,
le slug, la page mère, les méta Yoast, les images à la une. Tout cela
porte le référencement acquis.
"""

import argparse
import datetime
import html as H
import json
import os
import re
import sys
import time
from importlib.machinery import SourceFileLoader

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MERE = 7642
SITE = 'https://authentiquegypte.com'
Q = '/pages?parent=%d&per_page=100&status=any&context=edit&orderby=menu_order&order=asc'
SAUVE = os.path.join(RACINE, 'sauvegarde', 'avant-mise-en-ligne')

# Le type de contenu visé par chaque gabarit. Une page de guide ne peut
# pas devenir un article : on écrit dans l'article qui existe déjà.
GABARIT_TYPE = {'1 · Gabarit circuit': 'pages', '2 · Gabarit programme': 'programs',
                '3 · Gabarit destination': 'pages', '4 · Gabarit qui part': 'pages',
                '5 · Gabarit guide': 'posts', '6 · Gabarit blog': 'pages',
                '7 · Gabarit accueil': 'pages', '8 · Gabarit qui sommes-nous': 'pages'}
PREFIXES = ('refonte-famille-', 'refonte-programme-', 'refonte-destination-',
            'refonte-qui-part-', 'refonte-guide-', 'refonte-hub-guides-',
            'refonte-accueil-')

# Ce que ni le slug ni le titre ne tranchent seuls : l'accueil, dont la
# cible s'appelle « HOME » ; les deux Sainte-Catherine, que le site
# publie en double ; et mer-rouge, qui est à la fois une famille et un
# séjour.
FORCE = {8660: ('pages', 38), 8589: ('programs', 5864), 8594: ('programs', 5109),
         8597: ('pages', 470), 8590: ('programs', 540), 9126: ('pages', 105)}

CANVAS = 'elementor_canvas'

# Trois pages n'ont pas leur contenu, et ce n'est pas un défaut de forme :
# « Découverte de la Nubie » n'a ni carte, ni jour-par-jour, ni tarif
# alors que les treize autres fiches les ont ; « Désert noir » et
# « Alexandrie » n'exposent aucun séjour, seulement le message qui dit
# qu'il n'y en a pas. Leurs pages en ligne, elles, ont du contenu.
# Rémi a tranché : on bascule à 55 et on les laisse en l'état jusqu'à ce
# que Mélanie fournisse l'itinéraire et tranche les deux destinations.
ECARTEES = {8583: 'Découverte de la Nubie — ni carte, ni jour-par-jour, ni tarif',
            8918: 'Désert noir — aucun séjour exposé',
            8921: 'Alexandrie — aucun séjour exposé'}


def _cle(t):
    t = H.unescape(re.sub(r'<[^>]+>', '', t or ''))
    t = t.replace('’', "'").replace('&#x27;', "'")
    t = re.sub(r'^Refonte\s*·\s*', '', t)
    t = re.sub(r'^[^·]{1,22}·\s*', '', t)
    t = re.sub(r'^\d+\s*·\s*', '', t)
    t = re.sub(r'\s*\((?:page mère|\d+\s*séjours?)\)\s*$', '', t)
    t = re.sub(r'\s*—\s*doublon\s+\S+$', '', t)
    return re.sub(r'\s+', ' ', t).strip().lower()


def _nu(h):
    return re.sub(r'<!-- /?wp:html -->\n?', '', h)


def recenser(dep, api):
    """Les 57 brouillons, et le contenu en ligne de chaque type."""
    brouillons = []
    for d in dep.appel('GET', Q % MERE):
        if d['status'] == 'trash':
            continue
        for k in dep.appel('GET', Q % d['id']):
            if k['status'] == 'trash':
                continue
            p = dep.appel('GET', '/pages/%d?context=edit' % k['id'])
            brouillons.append({'id': p['id'], 'slug': p['slug'], 'titre': p['title']['raw'],
                               'gabarit': d['title']['raw'], 'contenu': _nu(p['content']['raw'])})
    vivants = []
    for base in ('pages', 'posts', 'programs'):
        for page in (1, 2, 3):
            lot = api(base, page)
            if not lot:
                break
            for k in lot:
                vivants.append({'type': base, 'id': k['id'], 'slug': k['slug'],
                                'titre': k['title']['raw'], 'url': k.get('link'),
                                'modele': k.get('template') or '',
                                'contenu': k['content']['raw'],
                                'cle': _cle(k['title']['raw'])})
            if len(lot) < 100:
                break
    return brouillons, vivants


def apparier(brouillons, vivants):
    par_slug = {(v['type'], v['slug']): v for v in vivants}
    par_cle = {}
    for v in vivants:
        par_cle.setdefault((v['type'], v['cle']), []).append(v)
    par_id = {(v['type'], v['id']): v for v in vivants}

    couples, perdus = [], []
    for b in brouillons:
        typ = next((t for g, t in GABARIT_TYPE.items()
                    if b['gabarit'].startswith('Refonte · ' + g)), None)
        if not typ:
            perdus.append((b, 'gabarit inconnu')); continue
        if b['id'] in FORCE:
            cible = par_id.get(FORCE[b['id']]); comment = 'forcé'
        else:
            base = next((b['slug'][len(p):] for p in PREFIXES
                         if b['slug'].startswith(p)), None)
            cible = par_slug.get((typ, base)) if base else None
            comment = 'slug'
            if not cible:
                l = par_cle.get((typ, _cle(b['titre'])))
                cible, comment = (l[0], 'titre') if l and len(l) == 1 else (None, comment)
            if not cible and base:
                # WordPress tronque les slugs longs : on retombe sur le préfixe
                c = [v for v in vivants if v['type'] == typ and v['slug'].startswith(base[:40])]
                cible, comment = (c[0], 'slug tronqué') if len(c) == 1 else (None, comment)
        if not cible:
            perdus.append((b, 'sans cible')); continue
        if b['id'] in ECARTEES:
            continue
        couples.append({'b': b, 'c': cible, 'comment': comment})
    vus = [x['c']['id'] for x in couples]
    doubles = sorted({i for i in vus if vus.count(i) > 1})
    return couples, perdus, doubles


def liens_de_brouillon(contenu, vers):
    """?page_id=8660 devient l'URL définitive. 9126 n'en a pas : on le dit."""
    manquants = set()

    def _un(m):
        pid = int(m.group(1))
        url = vers.get(pid)
        if not url:
            manquants.add(pid)
            return m.group(0)
        return url

    neuf = re.sub(r'https://authentiquegypte\.com/\?page_id=(\d+)/?', _un, contenu)
    neuf = re.sub(r'\?page_id=(\d+)', lambda m: _un(m) or m.group(0), neuf)
    return neuf, manquants


# L'extension de relecture pose ses épingles dans la page. Elles n'ont
# rien à faire en ligne.
RELECTURE = [re.compile(r'<div[^>]*\bclass="[^"]*\baec[-_][^"]*"[^>]*>.*?</div>', re.S),
             re.compile(r'<script[^>]*\baec[-_][^>]*>.*?</script>', re.S)]


def nettoyer(contenu):
    n = 0
    for rx in RELECTURE:
        contenu, k = rx.subn('', contenu)
        n += k
    return contenu, n


def preparer(couples):
    """Le contenu tel qu'il partira, et ce qui aura changé."""
    vers = {x['b']['id']: x['c']['url'] for x in couples}
    plan = []
    for x in couples:
        c, m = liens_de_brouillon(x['b']['contenu'], vers)
        c, nrel = nettoyer(c)
        plan.append({'brouillon': x['b']['id'], 'titre': x['b']['titre'],
                     'type': x['c']['type'], 'cible': x['c']['id'], 'url': x['c']['url'],
                     'comment': x['comment'],
                     'modele_avant': x['c']['modele'] or '(défaut)',
                     'modele_apres': CANVAS,
                     'liens_reecrits': len(re.findall(r'\?page_id=\d+', x['b']['contenu']))
                                       - len(re.findall(r'\?page_id=\d+', c)),
                     'liens_orphelins': sorted(m),
                     'relecture_retiree': nrel,
                     'octets_avant': len(x['c']['contenu']), 'octets_apres': len(c),
                     'contenu': c})
    return plan


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument('--essai', action='store_true', help='dit, n écrit rien')
    g.add_argument('--sauvegarder', action='store_true')
    g.add_argument('--appliquer', action='store_true')
    g.add_argument('--revenir', action='store_true')
    a = p.parse_args()

    dep = SourceFileLoader('dep', os.path.join(RACINE, 'outils', 'deployer.py')).load_module()
    import base64
    import requests
    S = requests.Session()
    S.verify = '/root/.ccr/ca-bundle.crt'
    u, m = os.environ['WP_AUTH'].split(':', 1)
    S.headers['Authorization'] = 'Basic ' + base64.b64encode(('%s:%s' % (u, m)).encode()).decode()
    B = SITE + '/wp-json/wp/v2/'

    def api(base, page):
        r = S.get(B + base, params={'per_page': 100, 'status': 'publish',
                                    'page': page, 'context': 'edit'}, timeout=60)
        return r.json() if r.status_code == 200 else []

    def ecrire(base, pid, charge):
        r = S.post(B + '%s/%d' % (base, pid), json=charge, timeout=90)
        if r.status_code >= 300:
            raise RuntimeError('%s %s/%d : %s' % (r.status_code, base, pid, r.text[:160]))
        return r.json()

    if a.revenir:
        # Le manifeste commande, pas le contenu du dossier : lui seul dit
        # quels couples la bascule a touchés. Un fichier de travail égaré
        # dans la sauvegarde ne doit pas partir en écriture, et surtout pas
        # un fichier au contenu vide, qui viderait la page.
        jours = sorted(j for j in (os.listdir(SAUVE) if os.path.isdir(SAUVE) else [])
                       if re.fullmatch(r'\d{4}-\d{2}-\d{2}', j))
        if not jours:
            sys.exit('Aucune sauvegarde datée. Rien à remettre.')
        d = os.path.join(SAUVE, jours[-1])
        man = json.load(open(os.path.join(d, 'MANIFESTE.json')))
        print('Je remets la sauvegarde du %s (%d couples au manifeste).'
              % (jours[-1], len(man['couples'])))
        n = 0
        for c in man['couples']:
            f = os.path.join(d, '%s-%d.json' % (c['type'], c['cible']))
            if not os.path.isfile(f):
                print('   ✗ sauvegarde manquante : %s' % f)
                continue
            s = json.load(open(f))
            if not s.get('contenu'):
                print('   ✗ sauvegarde vide, je ne touche pas à %s #%d'
                      % (s['type'], s['id']))
                continue
            for essai in range(4):
                try:
                    ecrire(s['type'], s['id'],
                           {'content': s['contenu'], 'template': s['modele']})
                    n += 1
                    print('   %-9s #%-6d %-24s %s' % (s['type'], s['id'],
                          s['modele'] or '(défaut)', (s['url'] or '').replace(SITE, '')))
                    break
                except Exception as motif:
                    print('      reprise %d/3 — %s' % (essai + 1, str(motif)[:70]))
                    time.sleep(2 ** essai)
            else:
                print('      ✗ ABANDON %s #%d' % (s['type'], s['id']))
        print('\n%d / %d contenu(s) remis dans leur état du %s.'
              % (n, len(man['couples']), jours[-1]))
        return

    brouillons, vivants = recenser(dep, api)
    couples, perdus, doubles = apparier(brouillons, vivants)
    print('%d brouillon(s) · %d contenu(s) en ligne · %d apparié(s)'
          % (len(brouillons), len(vivants), len(couples)))
    if ECARTEES:
        print('\n%d page(s) écartée(s) de la bascule, leur version en ligne reste :'
              % len(ECARTEES))
        for i, motif in sorted(ECARTEES.items()):
            print('   #%-6d %s' % (i, motif))
        print()
    if perdus or doubles:
        for b, motif in perdus:
            print('   ✗ #%-6d %-50s %s' % (b['id'], b['titre'][:50], motif))
        if doubles:
            print('   ✗ cibles visées deux fois : %s' % doubles)
        sys.exit('\nAppariement incomplet : je ne bascule rien.')

    plan = preparer(couples)
    orphelins = sorted({i for x in plan for i in x['liens_orphelins']})

    if a.essai:
        print('\n%-9s %-7s %-44s %-16s %6s %6s %s'
              % ('type', 'cible', 'url', 'gabarit', 'avant', 'après', 'liens'))
        for x in sorted(plan, key=lambda y: (y['type'], y['url'] or '')):
            print('%-9s #%-6d %-44s %-16s %6d %6d %4d'
                  % (x['type'], x['cible'], (x['url'] or '').replace(SITE, '')[:44],
                     x['modele_avant'][:16], x['octets_avant'], x['octets_apres'],
                     x['liens_reecrits']))
        print('\n%d liens de brouillon réécrits · %d balises de relecture retirées'
              % (sum(x['liens_reecrits'] for x in plan),
                 sum(x['relecture_retiree'] for x in plan)))
        pas_canvas = [x for x in plan if x['modele_avant'] != CANVAS]
        print('%d cible(s) à passer en %s (sinon : deux en-têtes et deux pieds)'
              % (len(pas_canvas), CANVAS))
        if orphelins:
            print('\n⚠ liens de brouillon sans cible, à régler AVANT la bascule : %s'
                  % orphelins)
        return

    if a.sauvegarder:
        jour = datetime.date.today().isoformat()
        d = os.path.join(SAUVE, jour)
        os.makedirs(d, exist_ok=True)

        def fiche(base, pid):
            """L'enregistrement entier, tel que l'API le rend en édition."""
            r = S.get(B + '%s/%d' % (base, pid), params={'context': 'edit'}, timeout=60)
            return r.json() if r.status_code == 200 else {'erreur': r.status_code}

        # 1. les 57 cibles, enregistrement complet et méta Yoast comprises
        for x in plan:
            e = fiche(x['type'], x['cible'])
            json.dump({'type': x['type'], 'id': x['cible'], 'url': x['url'],
                       'modele': e.get('template') or '', 'titre': (e.get('title') or {}).get('raw', ''),
                       'slug': e.get('slug'), 'parent': e.get('parent'),
                       'statut': e.get('status'), 'image_une': e.get('featured_media'),
                       'ordre': e.get('menu_order'), 'modifie': e.get('modified'),
                       'yoast': e.get('yoast_head_json') or {},
                       'meta': e.get('meta') or {},
                       'contenu': (e.get('content') or {}).get('raw', ''),
                       'extrait': (e.get('excerpt') or {}).get('raw', ''),
                       'entier': e},
                      open(os.path.join(d, '%s-%d.json' % (x['type'], x['cible'])), 'w'),
                      ensure_ascii=False)

        # 2. les quatre pages en ligne qui n'ont pas de refonte : elles ne
        #    bougeront pas, mais une sauvegarde sans elles serait partielle
        hors = os.path.join(d, 'hors-refonte')
        os.makedirs(hors, exist_ok=True)
        for pid in (105, 786, 3784, 3785):
            e = fiche('pages', pid)
            json.dump(e, open(os.path.join(hors, 'pages-%d.json' % pid), 'w'), ensure_ascii=False)

        # 3. les 57 brouillons eux-mêmes, dans l'état exact qui part en ligne
        bro = os.path.join(d, 'brouillons')
        os.makedirs(bro, exist_ok=True)
        for b in brouillons:
            json.dump(b, open(os.path.join(bro, '%d.json' % b['id']), 'w'), ensure_ascii=False)

        # 4. le manifeste : ce qu'on a pris, et de quoi vérifier au retour
        import hashlib
        manifeste = {'date': datetime.datetime.now().isoformat(timespec='seconds'),
                     'site': SITE, 'cibles': len(plan), 'brouillons': len(brouillons),
                     'hors_refonte': [105, 786, 3784, 3785],
                     'empreintes': {}}
        for nom in sorted(os.listdir(d)):
            f = os.path.join(d, nom)
            if os.path.isfile(f):
                manifeste['empreintes'][nom] = hashlib.sha1(open(f, 'rb').read()).hexdigest()
        manifeste['couples'] = [{'brouillon': x['brouillon'], 'type': x['type'],
                                 'cible': x['cible'], 'url': x['url'],
                                 'modele_avant': x['modele_avant']} for x in plan]
        json.dump(manifeste, open(os.path.join(d, 'MANIFESTE.json'), 'w'),
                  ensure_ascii=False, indent=1)
        octets = sum(os.path.getsize(os.path.join(r, f))
                     for r, _, fs in os.walk(d) for f in fs)
        print('Sauvegarde du %s dans %s' % (jour, d))
        print('   %d cible(s) · %d brouillon(s) · 4 page(s) hors refonte · %.1f Mo'
              % (len(plan), len(brouillons), octets / 1e6))
        print('   Retour en arrière : ./outils/mise-en-ligne.py --revenir')
        return

    if a.appliquer:
        jour = datetime.date.today().isoformat()
        d = os.path.join(SAUVE, jour)
        if not os.path.isdir(d) or len(os.listdir(d)) < len(plan):
            sys.exit('Sauvegarde du jour absente ou incomplète. '
                     'Lance --sauvegarder d abord.')
        if orphelins:
            sys.exit('Liens de brouillon sans cible : %s. Je ne bascule pas.' % orphelins)
        n = 0
        for x in plan:
            corps = '<!-- wp:html -->\n' + x['contenu'] + '\n<!-- /wp:html -->'
            for essai in range(4):
                try:
                    ecrire(x['type'], x['cible'],
                           {'content': corps, 'template': CANVAS})
                    n += 1
                    print('   %-9s #%-6d %s' % (x['type'], x['cible'],
                                                (x['url'] or '').replace(SITE, '')))
                    break
                except Exception as motif:
                    print('      reprise %d/3 — %s' % (essai + 1, str(motif)[:70]))
                    time.sleep(2 ** essai)
            else:
                print('      ✗ ABANDON %s #%d' % (x['type'], x['cible']))
        print('\n%d / %d contenu(s) basculé(s).' % (n, len(plan)))


if __name__ == '__main__':
    main()
