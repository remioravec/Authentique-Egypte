#!/usr/bin/env python3
"""Le plan de maillage, et sa pose là où le texte le permet.

    WP_AUTH='compte:mdp' python3 outils/maillage-plan.py --plan
    WP_AUTH='compte:mdp' python3 outils/maillage-plan.py --poser

La méthode (2.2) veut 11 liens entrants par cible, 11 ancres différentes,
en exact match contigu, et jamais un lien qui fasse reculer le lecteur
d'un stade. Deux de ses entrées manquent ici :

  — le `plan-<client>.json` n'existe pas : la phase 1 n'a pas eu lieu sur
    ce client. Le stade se déduit donc du gabarit, qui est la typologie
    même du site (guide → Problème, destination et profil → Solution,
    programme → Offre, /sur-mesure/ → Achat) ;
  — les ancres devraient venir des requêtes GSC de la cible. La propriété
    Search Console d'authentiquegypte.com n'est pas accessible depuis le
    compte connecté. Les ancres viennent donc du H1 et du titre de la
    cible, et de leurs variantes naturelles — deuxième meilleure source,
    et à remplacer par les requêtes réelles dès l'accès obtenu.

Ce que l'outil ne fait pas, et c'est délibéré : il n'invente pas de
phrase pour y loger un lien. Il ne pose un lien que là où l'expression
est DÉJÀ écrite dans le texte de la page source, hors titre, hors lien
existant, hors balise. Un lien que le texte ne porte pas reste au plan,
à poser à la rédaction. Mieux vaut 6 liens justes que 11 forcés.
"""

import argparse
import base64
import json
import os
import re
import sys
import time
import unicodedata

import requests

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = 'https://authentiquegypte.com'
STADE = {'guide': 'P', 'destination': 'S', 'profil': 'S', 'sejour': 'S',
         'programme': 'O', 'devis': 'A', 'accueil': '-', 'blog': '-',
         'agence': '-', 'autre': '-'}
RANG = {'P': 1, 'S': 2, 'O': 3, 'A': 4}
CIBLE = 11
# Une page source qui porterait trente liens ajoutés deviendrait un annuaire.
MAX_PAR_SOURCE = 6
MARQUE = 'data-ml'          # marque posée sur les liens de cet outil


def genre(u):
    c = u.replace(SITE, '').strip('/')
    if c == '':
        return 'accueil'
    if c == 'sur-mesure':
        return 'devis'
    if c == 'notre-blog':
        return 'blog'
    if c == 'qui-sommes-nous':
        return 'agence'
    if c.startswith('programs/'):
        return 'programme'
    if c.startswith('nos-sejours-egypte'):
        return 'sejour'
    if c.startswith('voyage-a-') or c in ('desert-blanc', 'lac-nasser',
                                          'mont-sinai', 'desert-noir'):
        return 'destination'
    if c.startswith('voyage-en-') or c.startswith('voyage-pmr'):
        return 'profil'
    if c in ('newsletter', 'mentions-legales-agence-voyage-egypte'):
        return 'autre'
    return 'guide'


def sans_accent(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s)
                   if unicodedata.category(c) != 'Mn').lower()


def segments(h):
    """Les tranches de texte visible du HTML, avec leur position.

    On saute le style, le script, les titres et l'intérieur des liens :
    un lien dans un h2 ou dans un autre lien n'est pas un lien de corps.
    """
    out = []
    i, n = 0, len(h)
    saut = {'style': 0, 'script': 0, 'a': 0, 'h1': 0, 'h2': 0, 'h3': 0,
            'h4': 0, 'h5': 0, 'h6': 0, 'summary': 0, 'nav': 0, 'header': 0,
            'footer': 0, 'button': 0, 'figcaption': 0}
    while i < n:
        j = h.find('<', i)
        if j < 0:
            j = n
        if j > i and not any(saut.values()):
            out.append((i, h[i:j]))
        if j >= n:
            break
        k = h.find('>', j)
        if k < 0:
            break
        balise = h[j + 1:k]
        m = re.match(r'(/?)([a-zA-Z0-9]+)', balise)
        if m:
            ferme, nom = m.group(1), m.group(2).lower()
            if nom in saut and not balise.endswith('/'):
                if ferme:
                    saut[nom] = max(0, saut[nom] - 1)
                else:
                    saut[nom] += 1
        i = k + 1
    return out


# Les têtes de groupe qui font une ancre utile : elles disent ce qu'on va
# trouver au bout du lien. « à Louxor » seul ne dit rien ; « visiter Louxor »,
# « étape à Louxor », « croisière vers Assouan » disent la page d'arrivée.
TETES = ('visiter', 'découvrir', 'explorer', 'séjour', 'voyage', 'circuit',
         'étape', 'nuit', 'nuits', 'journée', 'journées', 'escale', 'croisière',
         'excursion', 'partir', 'temples', 'temple', 'site', 'sites', 'passer',
         'rejoindre', 'remonter', 'descendre', 'traverser', 'dormir', 'arriver')

LIEUX = {'voyage-au-caire': 'Le Caire', 'voyage-a-louxor': 'Louxor',
         'voyage-a-assouan': 'Assouan', 'voyage-a-fayoum': 'Fayoum',
         'voyage-a-alexandrie': 'Alexandrie', 'desert-blanc': 'désert Blanc',
         'desert-noir': 'désert Noir', 'lac-nasser': 'lac Nasser',
         'mont-sinai': 'mont Sinaï'}


def ancres_du_texte(lieu, texte):
    """Les ancres que le texte porte déjà autour du lieu.

    On ne fabrique pas de phrase : on prend ce qui est écrit. L'ancre part
    d'une tête de groupe (TETES) et va jusqu'au lieu — « une étape à Louxor »
    donne « étape à Louxor ». Sans tête reconnue, pas d'ancre : mieux vaut
    laisser le lien au rédacteur que poser « à Louxor » sur une préposition.
    """
    out = []
    for m in re.finditer(re.escape(sans_accent(lieu)), sans_accent(texte)):
        d = m.start()
        avant = texte[max(0, d - 60):d]
        mots = re.findall(r"\s+|[^\s]+", avant)
        # on remonte au plus 4 mots en arrière à la recherche d'une tête
        k, pris = len(mots) - 1, []
        compte = 0
        while k >= 0 and compte < 5:
            t = mots[k]
            pris.insert(0, t)
            if t.strip():
                compte += 1
                if sans_accent(t.strip()) in [sans_accent(x) for x in TETES]:
                    debut = d - len(''.join(pris))
                    a = texte[debut:m.start() + len(lieu)]
                    # une ancre ne traverse pas une ponctuation forte : elle
                    # resterait collée à la phrase d'avant (« … sa capitale.
                    # Le Caire ») ou avalerait une parenthèse (« (Louxor »).
                    if (8 <= len(a) <= 60 and '\n' not in a
                            and not re.search(r'[.;:!?()«»"]', a)):
                        out.append((debut, a.strip()))
                    break
            k -= 1
    return out


def paragraphes(h):
    """Les <p> et <li> du corps, avec leurs tranches de texte.

    Chercher entre deux balises ne marche pas : un <strong> au milieu d'une
    phrase la découpe en morceaux de trente caractères, et toute mesure de
    longueur devient fausse. On prend donc le paragraphe entier comme unité,
    et on ne retient que ses tranches de texte pour y poser le lien.
    """
    out = []
    for m in re.finditer(r'<(p|li)\b[^>]*>', h):
        nom = m.group(1)
        p, k = 0, m.start()
        while k < len(h):
            if h.startswith('<' + nom, k) and (k == m.start() or h[k + 1 + len(nom)] in ' >'):
                p += 1
            elif h.startswith('</' + nom + '>', k):
                p -= 1
                if p == 0:
                    break
            k += 1
        bloc = h[m.end():k]
        if '<' + nom in bloc:          # paragraphe imbriqué : le père suffit
            continue
        tranches = [(m.end() + d, t) for d, t in segments(bloc)]
        visible = ''.join(t for _, t in tranches)
        if len(visible) >= 120:
            out.append((tranches, visible))
    return out


def ancres(url, h1, titre):
    """Les expressions candidates pour pointer vers cette cible.

    De la plus spécifique à la plus courte, jamais un seul mot : une ancre
    d'un mot ne dit pas ce qu'on va trouver, et la méthode demande l'exact
    match contigu de la requête, pas le nom propre seul.
    """
    out = []
    for t in (h1, titre):
        if not t:
            continue
        t = re.sub(r'\s*[|–—-]\s*(Authentique|Agence|Voyage en Égypte).*$', '', t).strip()
        if len(t.split()) >= 2:
            out.append(t)
    c = url.replace(SITE, '').strip('/')
    lieu = None
    for p, l in (('voyage-au-caire', 'Le Caire'), ('voyage-a-louxor', 'Louxor'),
                 ('voyage-a-assouan', 'Assouan'), ('voyage-a-fayoum', 'Fayoum'),
                 ('voyage-a-alexandrie', 'Alexandrie'), ('desert-blanc', 'désert Blanc'),
                 ('desert-noir', 'désert Noir'), ('lac-nasser', 'lac Nasser'),
                 ('mont-sinai', 'mont Sinaï')):
        if c == p:
            lieu = l
    if lieu:
        out += ['voyage à %s' % lieu, 'séjour à %s' % lieu, 'circuit à %s' % lieu,
                'voyage au %s' % lieu, 'séjour au %s' % lieu]
    for p, e in (('voyage-en-famille-en-egypte', ['voyage en famille en Égypte',
                                                  'voyage en famille', 'séjour en famille']),
                 ('voyage-en-couple-en-egypte', ['voyage en couple en Égypte',
                                                 'voyage en couple']),
                 ('voyage-solo-en-egypte', ['voyage solo en Égypte', 'voyage en solo',
                                            'voyager seul']),
                 ('voyage-pmr-en-egypte', ['voyage PMR', 'voyage en fauteuil roulant',
                                           'mobilité réduite'])):
        if c == p:
            out += e
    # dédoublonnage en gardant l'ordre, le plus long d'abord
    vus, net = set(), []
    for a in sorted(out, key=len, reverse=True):
        k = sans_accent(a)
        if k not in vus and len(a) >= 8:
            vus.add(k)
            net.append(a)
    return net


def main():
    p = argparse.ArgumentParser()
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument('--plan', action='store_true')
    g.add_argument('--poser', action='store_true')
    a = p.parse_args()

    S = requests.Session(); S.verify = '/root/.ccr/ca-bundle.crt'
    u, m = os.environ['WP_AUTH'].split(':', 1)
    S.headers['Authorization'] = 'Basic ' + base64.b64encode(
        ('%s:%s' % (u, m)).encode()).decode()
    B = SITE + '/wp-json/wp/v2/'

    man = json.load(open(os.path.join(
        RACINE, 'sauvegarde/avant-mise-en-ligne/2026-10-02/MANIFESTE.json')))
    etat = json.load(open(os.path.join(RACINE, 'docs/maillage-etat.json')))

    # on charge le contenu réel, celui qu'on écrira
    pages = {}
    for c in man['couples']:
        r = S.get(B + '%s/%d' % (c['type'], c['cible']),
                  params={'context': 'edit'}, timeout=120)
        d = r.json()
        corps = (d.get('content') or {}).get('raw', '')
        url = c['url'].rstrip('/') + '/'
        h1 = re.sub(r'<[^>]+>', '', (re.search(r'<h1[^>]*>(.*?)</h1>', corps, re.S)
                                     or [None, ''])[1]).strip()
        pages[url] = {'type': c['type'], 'id': c['cible'], 'corps': corps,
                      'genre': genre(url), 'stade': STADE[genre(url)],
                      'h1': h1, 'titre': (d.get('title') or {}).get('raw', '')}
    print('%d page(s) chargées depuis le CMS' % len(pages))

    entrants = {u: len(v) for u, v in etat['entrants'].items()}
    deja = {u: {s for s, _ in etat['entrants'].get(u, [])} for u in pages}

    plan, poses, sans_place = [], 0, 0
    poses_par_source = {}
    # on câble les cibles qui vendent d'abord : Offre, puis Solution
    ordre = sorted(pages, key=lambda x: ({'O': 0, 'S': 1, 'P': 2}.get(pages[x]['stade'], 9),
                                         entrants.get(x, 0)))
    for cible in ordre:
        pc = pages[cible]
        if pc['genre'] not in ('programme', 'destination', 'profil', 'sejour', 'guide'):
            continue
        besoin = CIBLE - entrants.get(cible, 0)
        if besoin <= 0:
            continue
        exprs = ancres(cible, pc['h1'], pc['titre'])
        if not exprs:
            continue
        lieu = LIEUX.get(cible.replace(SITE, '').strip('/'))
        trouves = []
        for src in pages:
            if src == cible or src in deja[cible] or len(trouves) >= besoin:
                continue
            if poses_par_source.get(src, 0) >= MAX_PAR_SOURCE:
                continue
            ps = pages[src]
            # jamais un lien qui fait reculer le lecteur d'un stade
            if ps['stade'] in RANG and pc['stade'] in RANG and \
               RANG[ps['stade']] > RANG[pc['stade']]:
                continue
            cand = []
            for tranches, _ in paragraphes(ps['corps']):
                for pos, txt in tranches:
                    for e in exprs:
                        k = sans_accent(txt).find(sans_accent(e))
                        if k >= 0:
                            cand.append((pos + k, txt[k:k + len(e)]))
                    if lieu:
                        for d, anc in ancres_du_texte(lieu, txt):
                            cand.append((pos + d, anc))
                        k = sans_accent(txt).find(sans_accent(lieu))
                        if k >= 0:
                            cand.append((pos + k, txt[k:k + len(lieu)]))
            # l'ancre la plus informative d'abord, et jamais deux fois la même
            for pos, anc in sorted(cand, key=lambda x: -len(x[1])):
                if any(sans_accent(anc) == sans_accent(t['ancre']) for t in trouves):
                    continue
                trouves.append({'source': src, 'ancre': anc, 'position': pos})
                poses_par_source[src] = poses_par_source.get(src, 0) + 1
                break
        plan.append({'cible': cible, 'genre': pc['genre'], 'stade': pc['stade'],
                     'avant': entrants.get(cible, 0), 'besoin': besoin,
                     'trouves': trouves})
        poses += len(trouves)
        sans_place += besoin - len(trouves)

    print('\n%-46s %-11s %5s %6s %6s %6s'
          % ('cible', 'genre', 'avant', 'manque', 'posés', 'ancres'))
    for x in sorted(plan, key=lambda y: (y['genre'], y['cible'])):
        d = len({sans_accent(t['ancre']) for t in x['trouves']})
        x['ancres_distinctes'] = d
        print('%-46s %-11s %5d %6d %6d %6d'
              % (x['cible'].replace(SITE, '')[:46], x['genre'], x['avant'],
                 x['besoin'], len(x['trouves']), d))
    print('\n%d lien(s) trouvables dans le texte · %d sans emplacement'
          % (poses, sans_place))
    json.dump(plan, open(os.path.join(RACINE, 'docs/maillage-plan.json'), 'w'),
              ensure_ascii=False, indent=1)
    print('plan écrit dans docs/maillage-plan.json')

    if a.plan:
        return

    # pose : on écrit source par source, en partant de la fin du document
    # pour que les positions déjà calculées restent valables
    par_source = {}
    for x in plan:
        for t in x['trouves']:
            par_source.setdefault(t['source'], []).append((t['position'], t['ancre'],
                                                           x['cible']))
    n = 0
    for src, items in par_source.items():
        corps = pages[src]['corps']
        for pos, ancre, cible in sorted(items, reverse=True):
            if corps[pos:pos + len(ancre)] != ancre:
                print('   ✗ %s : le texte a bougé sous « %s »'
                      % (src.replace(SITE, ''), ancre))
                continue
            lien = '<a href="%s" %s>%s</a>' % (cible, MARQUE, ancre)
            corps = corps[:pos] + lien + corps[pos + len(ancre):]
        charge = {'content': '<!-- wp:html -->\n' + corps + '\n<!-- /wp:html -->'}
        for essai in range(4):
            r = S.post(B + '%s/%d' % (pages[src]['type'], pages[src]['id']),
                       json=charge, timeout=300)
            if r.status_code < 300:
                break
            time.sleep(2 ** essai)
        else:
            sys.exit('écriture refusée sur %s' % src)
        n += len(items)
        print('   %-46s %d lien(s)' % (src.replace(SITE, ''), len(items)))
    print('\n%d lien(s) posés sur %d page(s).' % (n, len(par_source)))


if __name__ == '__main__':
    main()
