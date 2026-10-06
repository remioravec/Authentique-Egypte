#!/usr/bin/env python3
"""Lot 3 : les corrections de faits demandées page par page.

    WP_AUTH='compte:mdp' python3 outils/retours-06-faits.py --essai
    WP_AUTH='compte:mdp' python3 outils/retours-06-faits.py --appliquer

Chaque règle porte le numéro du commentaire de Mélanie dont elle vient. Rien
n'est décidé ici : on applique ce qu'elle a écrit, et on recalcule ce qui
peut l'être.

Le compteur « N séjours y passent » n'est plus saisi mais compté sur les
cartes réellement présentes. C'est ce qui lui donne raison deux fois : elle
demande 5 séjours sur Louxor, il y en a 5 ; et 3 sur le mont Sinaï, ce qui
est exactement le compte une fois retirés le doublon qu'elle signale et
l'oasis de Siwa, qui n'est pas dans le Sinaï.
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

ENCART_SINAI = (
    '<p class="note note--avert" data-securite>'
    '<b>Sécurité :</b> nous ne recommandons pas l’exploration de cette zone '
    'du fait du contexte géopolitique.</p>')


def carte_titres(h):
    """(début, fin, titre) de chaque carte de séjour."""
    out, i = [], 0
    while True:
        i = h.find('<article class="carte"', i)
        if i < 0:
            break
        p, k = 0, i
        while k < len(h):
            if h.startswith('<article', k):
                p += 1
            elif h.startswith('</article>', k):
                p -= 1
                if p == 0:
                    k += len('</article>')
                    break
            k += 1
        t = re.search(r'<a[^>]*>([^<]{5,90})</a>', h[i:k])
        out.append((i, k, (t.group(1).strip() if t else '')))
        i = k
    return out


def oter_carte(h, predicat, une_seule_si_double=False):
    """Retire les cartes que le prédicat désigne. Rend (html, nombre)."""
    n = 0
    while True:
        cartes = carte_titres(h)
        vise = None
        vus = {}
        for d, f, t in cartes:
            vus[t] = vus.get(t, 0) + 1
            if une_seule_si_double:
                if vus[t] > 1 and predicat(t):
                    vise = (d, f)
                    break
            elif predicat(t):
                vise = (d, f)
                break
        if not vise:
            break
        h = h[:vise[0]] + h[vise[1]:]
        n += 1
    return h, n


def oter_question(h, debut_du_titre):
    """Retire un <details> de FAQ par le début de sa question."""
    n = 0
    while True:
        i = h.find('<details class="faq__q')
        trouve = None
        j = 0
        while True:
            j = h.find('<details class="faq__q', j)
            if j < 0:
                break
            p, k = 0, j
            while k < len(h):
                if h.startswith('<details', k):
                    p += 1
                elif h.startswith('</details>', k):
                    p -= 1
                    if p == 0:
                        k += len('</details>')
                        break
                k += 1
            s = re.search(r'<summary[^>]*>(.*?)</summary>', h[j:k], re.S)
            txt = re.sub(r'<[^>]+>', '', s.group(1)).strip() if s else ''
            if txt.lower().startswith(debut_du_titre.lower()):
                trouve = (j, k)
                break
            j = k
        if not trouve:
            break
        h = h[:trouve[0]] + h[trouve[1]:]
        n += 1
    return h, n


def oter_bloc(h, ouvre, ferme, contient):
    """Retire un bloc borné à la main s'il contient le repère donné."""
    i = h.find(ouvre)
    while i >= 0:
        p, k = 0, i
        while k < len(h):
            if h.startswith(ouvre.split('>')[0], k):
                p += 1
            elif h.startswith(ferme, k):
                p -= 1
                if p == 0:
                    k += len(ferme)
                    break
            k += 1
        if contient in h[i:k]:
            return h[:i] + h[k:], 1
        i = h.find(ouvre, k)
    return h, 0


def oter_pilule(h, repere):
    """Retire une pastille <span class="pill"> qui contient le repère."""
    n, i = 0, 0
    while True:
        i = h.find('<span class="pill"', i)
        if i < 0:
            break
        p, k = 0, i
        while k < len(h):
            if h.startswith('<span', k):
                p += 1
            elif h.startswith('</span>', k):
                p -= 1
                if p == 0:
                    k += len('</span>')
                    break
            k += 1
        if repere in h[i:k]:
            h = h[:i] + h[k:]
            n += 1
            continue
        i = k
    return h, n


def oter_onglet_duree(h, repere):
    """Retire un onglet de durée : son libellé, son volet et son bouton."""
    n = 0
    m = re.search(r'<label class="duree__o"[^>]*for="(duree-\d+)"[^>]*>'
                  r'(?:(?!</label>).)*?' + re.escape(repere)
                  + r'(?:(?!</label>).)*?</label>', h, re.S)
    if not m:
        return h, 0
    ident = m.group(1)
    h = h[:m.start()] + h[m.end():]
    n += 1
    # le volet correspondant
    i = h.find('<div class="duree__c">')
    while i >= 0:
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
        if repere in h[i:k]:
            h = h[:i] + h[k:]
            break
        i = h.find('<div class="duree__c">', k)
    # et le bouton radio qui le commandait
    h = re.sub(r'<input[^>]*id="' + re.escape(ident) + r'"[^>]*>', '', h)
    return h, n


def recompter(h):
    """Le compteur de séjours suit les cartes, il ne se saisit plus."""
    n = len(carte_titres(h))
    if not n:
        return h, 0
    neuf, k = re.subn(r'<b>\d+</b>\s*séjours?\s*y\s*passe(?:nt)?',
                      '<b>%d</b> séjour%s y passe%s' % (n, 's' if n > 1 else '',
                                                        'nt' if n > 1 else ''), h)
    return neuf, k


def corriger(url, h):
    j = {}

    def note(cle, n):
        if n:
            j[cle] = j.get(cle, 0) + n

    c = url.replace(SITE, '')

    if c == '/mont-sinai/':
        # 12272 · « il y a deux fois le même itinéraire »
        h, n = oter_carte(h, lambda t: 'Lever du soleil' in t,
                          une_seule_si_double=True)
        note('12272 doublon retiré', n)
        # 12273 · « cet itinéraire ne fait pas parti du sinai »
        h, n = oter_carte(h, lambda t: 'Siwa' in t)
        note('12273 Siwa retirée', n)
        # 12280 · « écrire voyage dans le sinai sur mesure »
        h, n = re.subn(r'Voyage au Mont Sinaï sur mesure',
                       'Voyage dans le Sinaï sur mesure', h)
        note('12280 titre', n)
        # 12282 · encart de sécurité, texte de Mélanie
        if 'data-securite' not in h:
            i = h.find('<h2 id="t-carte"')
            if i < 0:
                i = h.find('Où se trouve')
            if i >= 0:
                f = h.find('</section>', i)
                if f > 0:
                    h = h[:f] + ENCART_SINAI + h[f:]
                    note('12282 encart sécurité', 1)

    if c == '/voyage-a-louxor/':
        # 12319 · « 2 jours minimum »
        h, n = re.subn(r'<b>3 jours</b>\s*conseillés', '<b>2 jours</b> minimum', h)
        note('12319 durée', n)

    if c == '/voyage-au-caire/':
        # 12264 et 12265 · « supprimer ce texte »
        h, n = oter_pilule(h, 'séjour')
        note('12264 compteur retiré', n)
        h, n = oter_pilule(h, 'conseillés')
        note('12265 durée retirée', n)

    if c == '/voyage-a-assouan/':
        # 12307 · « enlever accessible en bateau ou a pied »
        h, n = re.subn(r',?\s*accessibles? en bateau ou à pied(?: selon la saison)?', '', h)
        note('12307 mention retirée', n)
        # 12308 · « a enlever »
        h, n = oter_question(h, 'Quelle est la meilleure période pour aller à Assouan')
        note('12308 question retirée', n)

    if c == '/lac-nasser/':
        for num, debut in (('12286', 'Quelle faune observer'),
                           ('12287', 'Est-ce adapté aux amateurs de photographie'),
                           ('12289', 'Qu’est-ce qui rend le Lac Nasser unique'),
                           ('12290', 'Peut-on combiner le Lac Nasser')):
            h, n = oter_question(h, debut)
            note('%s question retirée' % num, n)
        # 12288 · la durée, dans les mots de Mélanie
        h, n = re.subn(
            r'Quatre à cinq jours permettent de découvrir les sites majeurs',
            'Une croisière dure généralement trois à quatre nuits. Pour Abou '
            'Simbel seul, une journée suffit, même si nous recommandons d’y '
            'dormir sur place', h)
        note('12288 durée reformulée', n)

    if c in ('/voyage-a-fayoum/', '/lac-nasser/'):
        # 12302, 12303, 12284, 12299, 12300
        h, n = re.subn(
            r'<p[^>]*>Tous personnalisables(?:&nbsp;|\s)*:(?:(?!</p>).)*?</p>',
            '', h, flags=re.S)
        note('12302 phrase retirée', n)
        # 12303, 12284 · « a enlever » sur « Passer du guide au voyage »
        h, n = re.subn(r'<p class="eyebrow">Passer du guide au voyage</p>', '', h)
        note('12303 surtitre retiré', n)

    if c == '/notre-blog/':
        # 12329 · « a supprimer »
        h, n = re.subn(
            r'<p[^>]*>Confiez l(?:&#x27;|&#039;|\'|’)organisation de votre voyage'
            r'(?:(?!</p>).)*?</p>', '', h, flags=re.S)
        note('12329 texte générique retiré', n)

    if c == '/programs/excursion-dans-le-desert-blanc/':
        # 12254, 12255, 12259 · « a partir de 520 euros par personne »
        h, n = re.subn(r'415\s*€', '520 €', h)
        note('12254 prix', n)
        # 12258 · « non il n'y a pas d'excursion d'une journée »
        h, n = oter_onglet_duree(h, 'une journée')
        note('12258 onglet d une journée retiré', n)
        # 12260 · « enlever la nuit en camping dans le désert »
        h, n = re.subn(r'<li[^>]*>(?:(?!</li>).)*?Une nuit en camping dans le désert(?:(?!</li>).)*?</li>',
                       '', h, flags=re.S)
        note('12260 ligne retirée', n)
        # 12262 · « enlever toute cette partie » (la valise)
        h, n = oter_bloc(h, '<section', '</section>', 'Quels équipements prévoir')
        note('12262 section équipement retirée', n)

    # le compteur suit toujours les cartes
    h, n = recompter(h)
    note('compteur recalculé', n)
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
    man = json.load(open(os.path.join(
        RACINE, 'sauvegarde/avant-mise-en-ligne/2026-10-02/MANIFESTE.json')))

    a_ecrire = []
    for c in man['couples']:
        d = S.get(B + '%s/%d' % (c['type'], c['cible']),
                  params={'context': 'edit'}, timeout=120).json()
        h = (d.get('content') or {}).get('raw', '')
        neuf, j = corriger(c['url'].rstrip('/') + '/', h)
        if neuf == h:
            continue
        o = len(re.findall(r'<(section|div|article|details|p|li)[\s>]', neuf))
        f = len(re.findall(r'</(section|div|article|details|p|li)>', neuf))
        if o != f:
            raise SystemExit('balises déséquilibrées sur %s : %d/%d'
                             % (c['url'], o, f))
        a_ecrire.append((c, neuf, j))
        print('%-46s %s' % (c['url'].replace(SITE, '')[:46],
                            ' · '.join('%s ×%d' % (k, v) for k, v in j.items())))

    print('\n%d page(s) à écrire' % len(a_ecrire))
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
    print('%d page(s) écrites.' % len(a_ecrire))


if __name__ == '__main__':
    main()
