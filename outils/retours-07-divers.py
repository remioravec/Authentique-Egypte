#!/usr/bin/env python3
"""Trois demandes de Mélanie qu'on pouvait trancher seul.

    WP_AUTH='compte:mdp' python3 outils/retours-07-divers.py --essai
    WP_AUTH='compte:mdp' python3 outils/retours-07-divers.py --appliquer

12257 « mettre un autre format pour quand partir ». La frise de douze mois
    avec ses températures demande un effort de lecture pour une réponse qui
    tient en trois lignes. On met donc les trois périodes devant — à
    privilégier, encore possible, à éviter — chacune avec sa plage de
    températures, et la frise mois par mois reste disponible juste en
    dessous, repliée. Les périodes ne sont pas saisies : elles sont groupées
    depuis les couleurs de la frise de chaque page.

12261 « ajouter les autorisations nécessaires pour le désert avec les
    autorités locales ». Les excursions à Siwa et au Fayoum disaient déjà
    « et autorisations » ; le désert blanc, non. Les trois le disent
    maintenant en entier, et de la même manière.

12285 et 12314 « est-ce possible d'enlever la mention ? » à propos du fond de
    carte OpenStreetMap. Non : c'est la condition de la licence sous laquelle
    le fond de carte est utilisé, la retirer mettrait le site en défaut. Mais
    la phrase complète n'est pas obligatoire. Elle devient le crédit court et
    discret qu'on voit au coin de toutes les cartes du web : « © OpenStreetMap »,
    en petit, aligné à droite, le lien menant à la page qui nomme les
    contributeurs.
"""

import argparse
import base64
import os
import re
import time

import requests

SITE = 'https://authentiquegypte.com'

MOIS = {'janv.': 'janvier', 'févr.': 'février', 'mars': 'mars',
        'avril': 'avril', 'mai': 'mai', 'juin': 'juin', 'juil.': 'juillet',
        'août': 'août', 'sept.': 'septembre', 'oct.': 'octobre',
        'nov.': 'novembre', 'déc.': 'décembre'}
ORDRE = ['janv.', 'févr.', 'mars', 'avril', 'mai', 'juin', 'juil.', 'août',
         'sept.', 'oct.', 'nov.', 'déc.']

PERIODES = [
    ('q-1', 'À privilégier',
     'Journées douces&nbsp;: on visite confortablement du matin au soir.'),
    ('q-2', 'Encore possible',
     'Il fait chaud l’après-midi&nbsp;: on sort tôt le matin et en fin de '
     'journée.'),
    ('q-3', 'À éviter',
     'Fortes chaleurs&nbsp;: les visites de plein air deviennent éprouvantes.'),
]

STYLE = (
    '<style id="quandp-css-3">'
    '.quandp{display:grid;gap:10px;margin:0 0 16px}'
    '.quandp__b{display:grid;grid-template-columns:1fr auto;gap:4px 18px;'
    'align-items:baseline;padding:14px 18px;'
    'border:1px solid var(--ligne,#E4E4EA);border-radius:var(--r-m,14px)}'
    '.quandp__b--1{background:#BEE6F1;border-color:#9ED3E2}'
    '.quandp__b--2{background:#FEF3DC;border-color:#EBD6A8}'
    '.quandp__b--3{background:#FBE9E3;border-color:#F0C9BE}'
    '.quandp__p{margin:0;font-weight:700;font-size:1.04rem;'
    'color:var(--nuit-900,#094D60)}'
    '.quandp__t{margin:0;font-weight:700;font-size:.95rem;white-space:nowrap;'
    'color:var(--nuit-900,#094D60);font-variant-numeric:tabular-nums}'
    '.quandp__q{margin:0;grid-column:1/-1;font-size:.95rem;'
    'color:var(--texte,#5D5D5D)}'
    '.quandp__d{margin:0 0 4px}'
    '.quandp__d>summary{cursor:pointer;padding:6px 0;font-size:.92rem;'
    'color:var(--nuit,#147894)}'
    '.quandp__d>summary:focus-visible{outline:2px solid var(--or,#ECAA24);'
    'outline-offset:2px}'
    '.quandp__d[open]>summary{margin-bottom:10px}'
    '.quandp__s{font-weight:400;color:#4a5a62}'
    '@media (max-width:560px){.quandp__b{grid-template-columns:1fr}'
    '.quandp__t{grid-column:1;margin-top:2px}}'
    '</style>')

# Le crédit de licence est porté en style sur la balise : la feuille du
# gabarit répète son sélecteur six fois pour gagner en spécificité, et aucune
# règle posée ici ne passerait devant.
CREDIT = ('<figcaption class="%s" style="text-align:right;font-size:11px;'
          'line-height:1.4;opacity:.5;margin:8px 0 0">&copy; <a '
          'href="https://www.openstreetmap.org/copyright" target="_blank" '
          'rel="noopener" style="font-size:11px">OpenStreetMap</a>'
          '</figcaption>')

AUTORISATIONS = ('Les entrées aux %s et les autorisations auprès des '
                 'autorités locales')


def periode(mois):
    """« Octobre à mars », « Avril, mai et septembre », « Septembre »."""
    idx = sorted(ORDRE.index(m) for m in mois)
    noms = [MOIS[ORDRE[i]] for i in idx]
    if len(idx) <= 3:
        t = ', '.join(noms[:-1]) + ' et ' + noms[-1] if len(noms) > 1 else noms[0]
        return t[0].upper() + t[1:]
    # suites consécutives, en tenant compte du passage de décembre à janvier
    suites, courante = [], [idx[0]]
    for i in idx[1:]:
        if i == courante[-1] + 1:
            courante.append(i)
        else:
            suites.append(courante)
            courante = [i]
    suites.append(courante)
    if len(suites) > 1 and suites[0][0] == 0 and suites[-1][-1] == 11:
        suites[-1] = suites[-1] + suites.pop(0)
    bouts = []
    for s in suites:
        a, b = MOIS[ORDRE[s[0]]], MOIS[ORDRE[s[-1]]]
        bouts.append(a if a == b else '%s à %s' % (a, b))
    t = ', '.join(bouts[:-1]) + ' et ' + bouts[-1] if len(bouts) > 1 else bouts[0]
    return t[0].upper() + t[1:]


def bandes(frise):
    """Les trois périodes, lues sur les couleurs de la frise."""
    mois = re.findall(
        r'<li class="(q-[123])[^"]*"><b>([^<]+)</b>'
        r'<span class="q-t">(-?\d+)-(-?\d+)\s*°C</span></li>', frise)
    if len(mois) != 12:
        return None
    par = {}
    for cl, m, bas, haut in mois:
        if m not in MOIS:
            return None
        par.setdefault(cl, []).append((m, int(bas), int(haut)))
    out = []
    for cl, titre, phrase in PERIODES:
        if cl not in par:
            continue
        g = par[cl]
        out.append(
            '<div class="quandp__b quandp__b--%s"><p class="quandp__p">%s<span '
            'class="quandp__s"> · %s</span></p><p class="quandp__t">%d à '
            '%d&nbsp;°C</p><p class="quandp__q">%s</p></div>'
            % (cl[-1], periode([m for m, _, _ in g]), titre,
               min(b for _, b, _ in g), max(h for _, _, h in g), phrase))
    return '<div class="quandp">' + ''.join(out) + '</div>'


def bloc_quand(h):
    """Pose les trois périodes devant la frise, et replie la frise."""
    if 'class="quandp"' in h:
        # déjà posé : on remet seulement les classes de couleur à jour
        return re.subn(r'class="quandp__b q-([123])"',
                       r'class="quandp__b quandp__b--\1"', h)
    i = h.find('<ol class="quand__frise">')
    if i < 0:
        return h, 0
    f = h.find('</ol>', i) + len('</ol>')
    g = h.find('</p>', h.find('<p class="quand__leg">', f))
    if g < 0:
        return h, 0
    g += len('</p>')
    frise, leg = h[i:f], h[f:g]
    b = bandes(frise)
    if not b:
        return h, 0
    neuf = (b + '<details class="quandp__d"><summary>Le détail mois par '
            'mois</summary>' + frise + leg + '</details>')
    return h[:i] + neuf + h[g:], 1


def credit_carte(h):
    fait = 0
    for classe in ('situe__note', 'cartep__note'):
        voulu = CREDIT % classe
        h, n = re.subn(
            r'<figcaption class="%s"[^>]*>(?:(?!</figcaption>).)*?'
            r'OpenStreetMap(?:(?!</figcaption>).)*?</figcaption>' % classe,
            lambda m, v=voulu: v if m.group(0) != v else m.group(0),
            h, flags=re.S)
        if n and voulu in h:
            fait += n
    return h, fait


def style(h):
    """Pose la feuille du bloc, en remplaçant celle d'une version passée."""
    h = re.sub(r'<style id="quandp-css(?:-\d+)?">.*?</style>', '', h,
               flags=re.S)
    i = h.find('<section class="pg-sec quand-dest"')
    if i < 0:
        i = h.find('<ol class="quand__frise">')
        if i < 0:
            return h, 0
        i = h.rfind('<section', 0, i)
    return h[:i] + STYLE + h[i:], 1


def corriger(h):
    j = {}

    def note(cle, n):
        if n:
            j[cle] = j.get(cle, 0) + n

    a = h.find('<main')
    b = h.find('</main>', a)
    if a < 0 or b < 0:
        raise SystemExit('pas de main refermé')
    tete, corps, pied = h[:a], h[a:b], h[b:]

    corps, n = bloc_quand(corps)
    note('12257 périodes posées', n)
    corps, n = credit_carte(corps)
    note('12285 crédit raccourci', n)
    if n or 'class="quandp"' in corps:
        corps, k = style(corps)
        note('feuille de style', k)

    # 12261 · les autorisations auprès des autorités locales
    for mot in ('monuments', 'sites'):
        corps, n = re.subn(
            r'<span>Les entrées aux %s(?: et autorisations)?</span>' % mot,
            '<span>' + (AUTORISATIONS % mot) + '</span>', corps)
        note('12261 autorisations', n)

    return tete + corps + pied, j


def main():
    p = argparse.ArgumentParser()
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument('--essai', action='store_true')
    g.add_argument('--appliquer', action='store_true')
    p.add_argument('--seulement', type=int, default=0,
                   help='ne traiter qu une page, pour voir le rendu avant')
    a = p.parse_args()

    S = requests.Session(); S.verify = '/root/.ccr/ca-bundle.crt'
    u, m = os.environ['WP_AUTH'].split(':', 1)
    S.headers['Authorization'] = 'Basic ' + base64.b64encode(
        ('%s:%s' % (u, m)).encode()).decode()
    B = SITE + '/wp-json/wp/v2/'

    cibles = [('pages', i) for i in (5191, 5201, 5210, 5219, 5229, 5532, 5541,
                                     5547, 5556)]
    cibles += [('programs', i) for i in
               (1168, 1198, 1369, 1408, 2054, 2193, 2393, 540, 5109, 5412,
                5515, 5864, 7336)]

    if a.seulement:
        cibles = [c for c in cibles if c[1] == a.seulement]
    a_ecrire = []
    for t, i in cibles:
        for essai in range(5):
            r = S.get(B + '%s/%d' % (t, i), params={'context': 'edit'},
                      timeout=240)
            if r.status_code < 300:
                break
            time.sleep(2 ** essai)
        else:
            raise SystemExit('lecture refusée sur %s/%d : %d'
                             % (t, i, r.status_code))
        h = (r.json().get('content') or {}).get('raw', '')
        neuf, j = corriger(h)
        if neuf == h:
            print('%-9s %-5d rien' % (t, i))
            continue
        a_ecrire.append((t, i, neuf))
        print('%-9s %-5d %s' % (t, i, ' · '.join('%s ×%d' % (k, v)
                                                 for k, v in sorted(j.items()))))

    print('\n%d page(s) à écrire' % len(a_ecrire))
    if a.essai:
        if a_ecrire:
            open('/tmp/claude-0/quand-essai.html', 'w').write(a_ecrire[0][2])
        return
    for t, i, neuf in a_ecrire:
        for essai in range(4):
            r = S.post(B + '%s/%d' % (t, i), json={
                'content': '<!-- wp:html -->\n' + neuf + '\n<!-- /wp:html -->'},
                timeout=600)
            if r.status_code < 300:
                break
            time.sleep(2 ** essai)
        else:
            raise SystemExit('écriture refusée sur %s/%d' % (t, i))
    print('%d page(s) écrites.' % len(a_ecrire))


if __name__ == '__main__':
    main()
