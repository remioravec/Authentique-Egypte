#!/usr/bin/env python3
"""Le bloc « Pour aller plus loin » : les liens que le texte ne portait pas.

    WP_AUTH='compte:mdp' python3 outils/maillage-bloc.py --essai
    WP_AUTH='compte:mdp' python3 outils/maillage-bloc.py --appliquer
    WP_AUTH='compte:mdp' python3 outils/maillage-bloc.py --retirer

L'audit l'a montré : sur 272 liens qu'il manquait pour tenir les onze
entrants du modèle, 22 seulement existaient déjà dans le texte. Les pages
citent les lieux en énumérations — « Le Caire, Louxor, Assouan » — jamais
en renvois rédigés. Rémi a tranché : un bloc contextuel en fin de page,
plutôt qu'une passe de rédaction qui déborderait de la journée.

Un bloc pèse moins qu'un lien en pleine phrase, et c'est assumé. Ce qu'il
apporte : les onze entrants, onze ancres différentes, et aucun lien qui
fasse reculer le lecteur dans le funnel.

Les ancres viennent des requêtes réelles de Search Console quand la page
en a (docs/gsc-requetes.json, relevé du 1er juillet au 30 septembre), et
seulement sinon d'une banque de variantes construites sur son titre. On
écrit l'ancre au stade d'arrivée, jamais au stade de la page qui la porte.

Le bloc est marqué `data-maillage` : --retirer le reprend en entier.
"""

import argparse
import base64
import json
import os
import re
import time
import unicodedata
from collections import defaultdict

import requests

SITE = 'https://authentiquegypte.com'
RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CIBLE = 11
MAX_PAR_BLOC = 6
# Un encart « Pour aller plus loin » qui ne porte qu'un lien n'a pas lieu
# d'être. Sous ce seuil, ses liens partent sur une autre page éligible.
MIN_PAR_BLOC = 3
# /qui-sommes-nous/ est revenue à son ancienne version Elementor à la demande
# de Rémi : elle rend ses propres données et ignore post_content. Y écrire un
# bloc ne produit rien de visible — on ne l'utilise ni comme source ni comme
# cible tant qu'elle est dans cet état.
HORS_JEU = {SITE + '/qui-sommes-nous/'}
MARQUE = 'data-maillage'

STADE = {'guide': 'P', 'destination': 'S', 'profil': 'S', 'sejour': 'S',
         'programme': 'O', 'devis': 'A', 'accueil': '-', 'blog': '-',
         'agence': '-', 'autre': '-'}
RANG = {'P': 1, 'S': 2, 'O': 3, 'A': 4}

STYLE = ('<style>'
         '.elementor-template-canvas .pg .ml{display:grid;'
         'grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:10px 26px;'
         'list-style:none;margin:18px 0 0;padding:0}'
         '.elementor-template-canvas .pg .ml li{margin:0}'
         '.elementor-template-canvas .pg .ml a{display:flex;align-items:center;gap:10px;'
         'min-height:44px;font-family:"Manrope",sans-serif;font-size:1rem;'
         'color:var(--teal-txt);text-decoration:none;border-bottom:1px solid var(--ligne-2);'
         'padding:6px 0}'
         '.elementor-template-canvas .pg .ml a:hover{color:var(--nuit-900)}'
         '.elementor-template-canvas .pg .ml a::before{content:"";flex:0 0 auto;width:6px;'
         'height:6px;border-radius:50%;background:var(--or)}'
         '</style>')


def sans_accent(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s)
                   if unicodedata.category(c) != 'Mn').lower()


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


LIEU = {'voyage-au-caire': ('Le Caire', 'au'), 'voyage-a-louxor': ('Louxor', 'à'),
        'voyage-a-assouan': ('Assouan', 'à'), 'voyage-a-fayoum': ('Fayoum', 'à'),
        'voyage-a-alexandrie': ('Alexandrie', 'à'),
        'desert-blanc': ('désert Blanc', 'dans le'),
        'desert-noir': ('désert Noir', 'dans le'),
        'lac-nasser': ('lac Nasser', 'sur le'), 'mont-sinai': ('mont Sinaï', 'au')}

PROFIL = {
    'voyage-en-famille-en-egypte': ['Voyage en famille en Égypte',
                                    'Partir en Égypte avec des enfants',
                                    'Séjour en famille en Égypte',
                                    'Égypte en famille', 'Voyager en famille en Égypte',
                                    'Circuit familial en Égypte',
                                    'Vacances en famille en Égypte',
                                    'Égypte avec les enfants',
                                    'Voyage familial sur mesure en Égypte',
                                    'Séjour familial en Égypte',
                                    'Découvrir l’Égypte en famille'],
    'voyage-en-couple-en-egypte': ['Voyage en couple en Égypte',
                                   'Séjour en amoureux en Égypte', 'Égypte en couple',
                                   'Voyage romantique en Égypte',
                                   'Partir à deux en Égypte',
                                   'Circuit en couple en Égypte',
                                   'Escapade en couple en Égypte',
                                   'Lune de miel en Égypte',
                                   'Séjour en couple sur mesure',
                                   'Voyage à deux en Égypte',
                                   'Découvrir l’Égypte en couple'],
    'voyage-solo-en-egypte': ['Voyage solo en Égypte', 'Partir seul en Égypte',
                              'Égypte en solo', 'Voyager seul en Égypte',
                              'Séjour solo en Égypte', 'Circuit en solo en Égypte',
                              'Voyage individuel en Égypte',
                              'Partir en Égypte sans groupe',
                              'Égypte pour voyageur solo', 'Séjour individuel en Égypte',
                              'Découvrir l’Égypte en solo'],
    'voyage-pmr-en-egypte': ['Voyage PMR en Égypte',
                             'Égypte en fauteuil roulant',
                             'Voyage accessible en Égypte',
                             'Séjour adapté en Égypte',
                             'Égypte à mobilité réduite',
                             'Circuit accessible en Égypte',
                             'Voyager en Égypte en fauteuil',
                             'Égypte pour personne à mobilité réduite',
                             'Séjour PMR sur mesure en Égypte',
                             'Voyage adapté en Égypte',
                             'Accessibilité en Égypte'],
}


def banque(url, titre, gsc, genre_cible='autre'):
    """Les onze ancres possibles d'une cible, les requêtes réelles d'abord."""
    # Les requêtes de ce site sont courtes et souvent informationnelles
    # (« el fayoum », « hurgada », « meteo louxor egypte ») : telles quelles
    # elles font de mauvaises ancres. On ne garde que celles qui portent une
    # intention de voyage, et on laisse les variantes rédigées faire le reste.
    INTENTION = ('voyage', 'sejour', 'séjour', 'circuit', 'agence', 'partir',
                 'visiter', 'visite', 'faire', 'croisiere', 'croisière',
                 'excursion', 'decouvrir', 'découvrir', 'famille', 'couple',
                 'solo', 'hors des sentiers')
    out = []
    for q, imp, clics, pos in gsc.get(url.replace(SITE, ''), []):
        k = sans_accent(q)
        if (len(q.split()) >= 3 and 'authentique' not in k
                and any(sans_accent(w) in k for w in INTENTION)):
            out.append(q[0].upper() + q[1:])
    c = url.replace(SITE, '').strip('/')
    if c in LIEU:
        lieu, prep = LIEU[c]
        out += ['Voyage %s %s' % (prep, lieu), 'Séjour %s %s' % (prep, lieu),
                'Que faire %s %s' % (prep, lieu), 'Visiter %s' % lieu,
                'Circuit %s %s' % (prep, lieu), 'Découvrir %s' % lieu,
                'Partir %s %s' % (prep, lieu), 'Étape %s %s' % (prep, lieu),
                '%s en Égypte' % lieu[0].upper() + lieu[1:],
                '%s sur mesure' % lieu[0].upper() + lieu[1:],
                'Nos séjours %s %s' % (prep, lieu)]
    if c in PROFIL:
        out += PROFIL[c]
    t = re.sub(r'\s*[|–—-]\s*(Authentique|Agence|Voyage en Égypte).*$', '', titre).strip()
    t = t.rstrip(' :;,.!?')          # « … à éviter en Égypte : » → sans le deux-points
    if t:
        out.append(t)
        # « Le programme : … » ne veut rien dire sur un guide, et « Voir le
        # séjour … » non plus. Ces tournures sont réservées aux programmes.
        if genre_cible == 'programme':
            out += ['Le programme : %s' % t, 'Voir le séjour %s' % t,
                    'Découvrir « %s »' % t]
        elif genre_cible == 'guide':
            out += ['Notre guide : %s' % t, 'Lire « %s »' % t]
        else:
            out += ['En savoir plus sur %s' % t, 'Découvrir « %s »' % t]
    vus, net = set(), []
    for x in out:
        k = sans_accent(x)
        if k not in vus and 3 <= len(x.split()) + 1 and len(x) <= 70:
            vus.add(k)
            net.append(x)
    return net


def bloc(liens):
    li = ''.join('<li><a href="%s">%s</a></li>' % (u, a) for a, u in liens)
    return ('<section class="pg-sec pg-sec--serre" ' + MARQUE + '><div class="wrap">'
            '<p class="eyebrow">Pour aller plus loin</p>'
            '<ul class="ml">' + li + '</ul></div></section>')


def retirer(h):
    """Ôte le bloc et son style, bornés à la main."""
    for ouvre, ferme in (('<section class="pg-sec pg-sec--serre" ' + MARQUE + '>',
                          '</section>'),):
        while True:
            i = h.find(ouvre)
            if i < 0:
                break
            p, k = 0, i
            while k < len(h):
                if h.startswith('<section', k):
                    p += 1
                elif h.startswith('</section>', k):
                    p -= 1
                    if p == 0:
                        k += len('</section>')
                        break
                k += 1
            h = h[:i] + h[k:]
    h = h.replace(STYLE, '')
    return h


def poser(h, liens):
    """Insère le bloc juste avant la fin du <main>, après le dernier contenu."""
    h = retirer(h)
    i = h.rfind('</main>')
    if i < 0:
        return h + bloc(liens) + STYLE
    return h[:i] + bloc(liens) + h[i:] + STYLE


def main():
    p = argparse.ArgumentParser()
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument('--essai', action='store_true')
    g.add_argument('--appliquer', action='store_true')
    g.add_argument('--retirer', action='store_true')
    args = p.parse_args()

    S = requests.Session(); S.verify = '/root/.ccr/ca-bundle.crt'
    u, m = os.environ['WP_AUTH'].split(':', 1)
    S.headers['Authorization'] = 'Basic ' + base64.b64encode(
        ('%s:%s' % (u, m)).encode()).decode()
    B = SITE + '/wp-json/wp/v2/'

    man = json.load(open(os.path.join(
        RACINE, 'sauvegarde/avant-mise-en-ligne/2026-10-02/MANIFESTE.json')))
    etat = json.load(open(os.path.join(RACINE, 'docs/maillage-etat.json')))
    gsc = json.load(open(os.path.join(RACINE, 'docs/gsc-requetes.json')))

    pages = {}
    for c in man['couples']:
        if (c['url'].rstrip('/') + '/') in HORS_JEU:
            continue
        d = S.get(B + '%s/%d' % (c['type'], c['cible']),
                  params={'context': 'edit'}, timeout=120).json()
        url = c['url'].rstrip('/') + '/'
        pages[url] = {'type': c['type'], 'id': c['cible'],
                      'corps': (d.get('content') or {}).get('raw', ''),
                      'titre': (d.get('title') or {}).get('raw', ''),
                      'genre': genre(url), 'stade': STADE[genre(url)]}
    print('%d page(s) chargées' % len(pages))

    if args.retirer:
        n = 0
        for u2, p2 in pages.items():
            neuf = retirer(p2['corps'])
            if neuf == p2['corps']:
                continue
            S.post(B + '%s/%d' % (p2['type'], p2['id']),
                   json={'content': '<!-- wp:html -->\n' + neuf + '\n<!-- /wp:html -->'},
                   timeout=300).raise_for_status()
            n += 1
            print('   retiré de %s' % u2.replace(SITE, ''))
        print('%d bloc(s) retirés.' % n)
        return

    entrants = {u2: len(v) for u2, v in etat['entrants'].items()}
    deja = {u2: {s for s, _ in etat['entrants'].get(u2, [])} for u2 in pages}

    sortants = defaultdict(list)     # source → [(ancre, cible)]
    recu = defaultdict(int)
    ordre = sorted(pages, key=lambda x: ({'O': 0, 'S': 1, 'P': 2}.get(pages[x]['stade'], 9),
                                         entrants.get(x, 0)))
    for cible in ordre:
        pc = pages[cible]
        if pc['genre'] not in ('programme', 'destination', 'profil', 'sejour', 'guide'):
            continue
        besoin = CIBLE - entrants.get(cible, 0)
        if besoin <= 0:
            continue
        anc = banque(cible, pc['titre'], gsc, pc['genre'])
        if not anc:
            continue
        i = 0
        def priorite(x):
            n = len(sortants[x])
            # 0 : entamée et pas pleine — on la remplit d'abord
            # 1 : vierge — on n'en ouvre une que si nécessaire
            # 2 : pleine
            if n >= MAX_PAR_BLOC:
                return (2, 0, x)
            return (0 if n else 1, -n, x)

        for src in sorted(pages, key=priorite):
            if i >= besoin or i >= len(anc):
                break
            if src == cible or src in deja[cible]:
                continue
            if len(sortants[src]) >= MAX_PAR_BLOC:
                continue
            ps = pages[src]
            if ps['stade'] in RANG and pc['stade'] in RANG and \
               RANG[ps['stade']] > RANG[pc['stade']]:
                continue
            if any(c2 == cible for _, c2 in sortants[src]):
                continue
            sortants[src].append((anc[i], cible))
            recu[cible] += 1
            i += 1

    print('\n%-46s %-11s %5s %6s %6s' % ('cible', 'genre', 'avant', 'ajout', 'total'))
    for c2 in sorted(recu, key=lambda x: (pages[x]['genre'], x)):
        print('%-46s %-11s %5d %6d %6d'
              % (c2.replace(SITE, '')[:46], pages[c2]['genre'], entrants.get(c2, 0),
                 recu[c2], entrants.get(c2, 0) + recu[c2]))
    tenues = sum(1 for c2 in recu if entrants.get(c2, 0) + recu[c2] >= CIBLE)
    print('\n%d lien(s) à poser sur %d page(s) · %d cible(s) atteignent les 11'
          % (sum(len(v) for v in sortants.values()),
             sum(1 for v in sortants.values() if v), tenues))
    doublons = [s for s, v in sortants.items()
                if len({sans_accent(a) for a, _ in v}) != len(v)]
    print('ancres répétées dans un même bloc : %s' % (doublons or 'aucune'))

    if args.essai:
        s0 = next(s for s, v in sortants.items() if v)
        print('\nexemple, %s :' % s0.replace(SITE, ''))
        for a, c2 in sortants[s0]:
            print('   « %s » → %s' % (a, c2.replace(SITE, '')))
        return

    # un bloc d'un ou deux liens n'a pas lieu d'être : on ne le pose pas
    maigres = [s2 for s2, v in sortants.items() if 0 < len(v) < MIN_PAR_BLOC]
    perdus = sum(len(sortants[s2]) for s2 in maigres)
    for s2 in maigres:
        sortants[s2] = []
    if maigres:
        print('%d bloc(s) sous %d liens non posés (%d lien(s) laissés au plan)'
              % (len(maigres), MIN_PAR_BLOC, perdus))

    n, nettoyees = 0, 0
    for src in pages:
        liens = sortants.get(src) or []
        if not liens:
            # la page n'en porte plus : on ôte le bloc s'il y en avait un
            neuf = retirer(pages[src]['corps'])
            if neuf != pages[src]['corps']:
                S.post(B + '%s/%d' % (pages[src]['type'], pages[src]['id']),
                       json={'content': '<!-- wp:html -->\n' + neuf + '\n<!-- /wp:html -->'},
                       timeout=300).raise_for_status()
                nettoyees += 1
            continue
        neuf = poser(pages[src]['corps'], liens)
        for essai in range(4):
            r = S.post(B + '%s/%d' % (pages[src]['type'], pages[src]['id']),
                       json={'content': '<!-- wp:html -->\n' + neuf + '\n<!-- /wp:html -->'},
                       timeout=300)
            if r.status_code < 300:
                break
            time.sleep(2 ** essai)
        else:
            raise SystemExit('écriture refusée sur %s' % src)
        n += 1
        print('   %-46s %d lien(s)' % (src.replace(SITE, ''), len(liens)))
    print('\n%d bloc(s) posés · %d page(s) nettoyées.' % (n, nettoyees))


if __name__ == '__main__':
    main()
