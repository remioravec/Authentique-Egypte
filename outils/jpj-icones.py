#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Les icônes hébergement et repas du jour par jour.

    WP_AUTH='compte:mot de passe' ./outils/jpj-icones.py [--essai]

« Différencier par des petites icônes les hébergements et les repas
inclus ou pas inclus selon la journée, car parfois c'est marqué parfois
non » (#10761).

JE LUI AVAIS RÉPONDU QUE C'ÉTAIT IMPOSSIBLE. J'AVAIS TORT.

J'avais compté treize journées sur soixante-cinq portant un hébergement
et aucune portant un repas — mais je n'avais regardé que le bloc
« etape__meta », qui n'est renseigné presque nulle part. Le déroulé
lui-même, lui, parle : cinquante-deux journées nomment un hébergement,
trente-cinq nomment un repas.

ET SURTOUT : « INCLUS » NE SE DEVINE PAS, IL EST ÉCRIT

La section « Ce que le prix comprend » liste, sur les quatorze
programmes, « Les repas mentionnés » dans la colonne des inclusions. Le
site affirme donc lui-même qu'un repas cité au déroulé est compris. Et
le balisage distingue déjà les lignes « En option », qui ne le sont pas.

Croiser ces deux affirmations n'invente rien. On pose donc trois états,
et trois seulement :

    cité dans une ligne normale   → compris
    cité dans une ligne En option → en option
    non cité                      → rien du tout

Le troisième état compte autant que les deux autres. Afficher « déjeuner
non inclus » là où le texte se tait serait une invention — le silence de
la fiche n'est pas un refus.
"""

import argparse
import html as H
import os
import re
import time
from importlib.machinery import SourceFileLoader

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MERE = 7642
Q = '/pages?parent=%d&per_page=100&status=any&context=edit&orderby=menu_order&order=asc'
E = '.elementor-template-canvas '

# L'ordre de la journée, pas l'ordre alphabétique.
REPAS = [('pdj', 'Petit-déjeuner', r'petits?.?d[ée]jeuners?'),
         ('dej', 'Déjeuner', r'(?<!petit.)(?<!petit-)d[ée]jeuners?'),
         ('din', 'Dîner', r'd[îi]ners?')]

# Les formes d'hébergement telles qu'elle les écrit. On classe ses mots,
# on n'extrait pas un nom libre : « nuit en maison d'hôtes » donne
# « Maison d'hôtes », pas un fragment coupé à l'apostrophe.
LOGIS = [('Bivouac', r'bivouac|campement|camp\b|sous les étoiles'),
         ('Bateau', r'\bbateau|felouque|dahab[ei]ya|dahabieh|à bord'),
         ('Lodge', r'[ée]co.?lodge|lodge'),
         ("Maison d'hôtes", r"maison d.h[ôo]tes|guest.?house"),
         ('Monastère', r'monast[èe]re|refuge'),
         ('Hôtel', r'h[ôo]tel')]

ICONES = {
    'lit': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" '
           'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
           '<path d="M3 18v-7a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v7M3 14h18M7 9V7a1 1 0 0 1 1-1h3'
           'a1 1 0 0 1 1 1v2"/></svg>',
    'repas': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" '
             'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
             '<path d="M6 3v8a2 2 0 0 0 4 0V3M8 11v10M17 3c-1.5 1.5-2 3.5-2 5.5 0 1.5.5 2.5 2 '
             '2.5v10"/></svg>',
}

FEUILLE = (
    '<style data-jpj-ico="1">'
    + E + '.pg .jico{display:flex;flex-wrap:wrap;gap:8px;align-items:center;'
    'margin:14px 0 0;padding:12px 0 0;border-top:1px solid var(--ligne-pg,#E4E4EA)}'
    + E + '.pg .jico__e{display:inline-flex;align-items:center;gap:7px;'
    'padding:6px 12px;border-radius:999px;font-family:"Manrope",sans-serif;'
    'font-size:.82rem;font-weight:600;line-height:1.3;'
    'background:var(--or-fond,#FEEDDC);color:var(--nuit-900,#095360);'
    'border:1px solid #F3D9A8}'
    + E + '.pg .jico__e svg{width:15px;height:15px;flex:0 0 auto}'
    # « En option » se distingue d'un coup d'œil : contour seul, pas de fond.
    + E + '.pg .jico__e[data-opt]{background:transparent;'
    'border:1px dashed var(--ligne-pg,#E4E4EA);color:var(--gris,#6E7680);font-weight:500}'
    + E + '.pg .jico__e[data-opt] em{font-style:normal;opacity:.85}'
    '</style>')


def _fin(h, d, nom):
    p = 0
    for t in re.finditer(r'<(/?)%s\b[^>]*>' % nom, h[d:]):
        p += 1 if not t.group(1) else -1
        if p == 0:
            return d + t.end()
    return -1


def _texte(x):
    return H.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', x)))


def _depart(t):
    """La journée du vol retour : l'hôtel y est cité, mais on n'y dort pas.

    « Petit-déjeuner à l'hôtel, transfert à l'aéroport » nomme un hôtel
    sans qu'il y ait de nuit. Exiger le mot « nuit » partout coûtait bien
    plus cher : les journées d'arrivée disent « transfert à votre hôtel »
    sans jamais l'écrire, et dix-neuf journées perdaient leur hébergement.
    On ne retire donc que le cas du départ.
    """
    if re.search(r'\bnuit\b|nuit[ée]e|dormir|coucher', t, re.I):
        return False
    return bool(re.search(r'vol (?:international|de retour|retour)|transfert (?:à|vers) '
                          r"l.a[ée]roport|d[ée]part.{0,20}a[ée]roport|fin (?:du|de) s[ée]jour",
                          t, re.I))


def lire_journee(j):
    """Ce que la journée affirme : son logis, ses repas, ses options."""
    options = re.findall(r'<li class="etape__opt">.*?</li>', j, re.S)
    normal = _texte(re.sub(r'<li class="etape__opt">.*?</li>', '', j, flags=re.S))
    opt = _texte(' '.join(options))

    compris, en_option = [], []
    for cle, nom, rx in REPAS:
        if re.search(rx, normal, re.I):
            compris.append((cle, nom))
        elif re.search(rx, opt, re.I):
            en_option.append((cle, nom))

    # Le bloc méta, quand il existe, donne le nom exact : on le préfère.
    m = re.search(r'<span class="etape__sv">.*?<b>Hébergement</b><i>(.*?)</i>', j, re.S)
    logis = _texte(m.group(1)).strip() if m else ''
    if not logis and not _depart(normal):
        for nom, rx in LOGIS:
            if re.search(rx, normal, re.I):
                logis = nom
                break
    return logis, compris, en_option


def bandeau(logis, compris, en_option):
    if not logis and not compris and not en_option:
        return ''
    bouts = []
    if logis:
        bouts.append('<span class="jico__e">%s%s</span>'
                     % (ICONES['lit'], H.escape(logis)))
    for _, nom in compris:
        bouts.append('<span class="jico__e">%s%s</span>' % (ICONES['repas'], nom))
    for _, nom in en_option:
        bouts.append('<span class="jico__e" data-opt>%s%s <em>· en option</em></span>'
                     % (ICONES['repas'], nom))
    return '<p class="jico">%s</p>' % ''.join(bouts)


def corriger(h):
    d = h.find('<h2 id="t-jpj"')
    if d < 0:
        return h, []
    f = _fin(h, h.rfind('<section', 0, d), 'section')
    if f < 0:
        return h, []
    zone = h[d:f]

    morceaux = re.split(r'(?=<div class="jour")', zone)
    n = 0
    for i, j in enumerate(morceaux):
        if not j.startswith('<div class="jour'):
            continue
        # On repart de zéro : sans ce retrait, un second passage empile
        # les bandeaux au lieu de les remplacer.
        j = re.sub(r'<p class="jico">.*?</p>', '', j, flags=re.S)
        band = bandeau(*lire_journee(j))
        if not band:
            morceaux[i] = j
            continue
        # À la fin de l'article de l'étape, pas après la journée : le
        # bandeau appartient au détail, pas au titre suivant.
        k = j.rfind('</article>')
        morceaux[i] = (j[:k] + band + j[k:]) if k > 0 else (j + band)
        n += 1
    neuf = ''.join(morceaux)
    if neuf == zone:
        return h, []
    h = h[:d] + neuf + h[f:]
    if 'data-jpj-ico="1"' not in h:
        h += FEUILLE
    return h, ['%d journée(s) étiquetée(s) (#10761)' % n]


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--essai', action='store_true')
    a = p.parse_args()
    dep = SourceFileLoader('dep', os.path.join(RACINE, 'outils', 'deployer.py')).load_module()

    pages = []
    for d in dep.appel('GET', Q % MERE):
        if d['status'] == 'trash':
            continue
        pages += [k for k in dep.appel('GET', Q % d['id']) if k['status'] != 'trash']

    n = 0
    for k in pages:
        p_ = dep.appel('GET', '/pages/%d?context=edit' % k['id'])
        brut = re.sub(r'<!-- /?wp:html -->\n?', '', p_['content']['raw'])
        neuf, faits = corriger(brut)
        if not faits:
            continue
        print('   #%-6d %-34s %s' % (k['id'], (p_.get('title') or {}).get('raw', '')[:34],
                                     ' · '.join(faits)))
        if a.essai:
            continue
        n += 1
        corps = '<!-- wp:html -->\n' + neuf + '\n<!-- /wp:html -->'
        for essai in range(4):
            try:
                dep.appel('POST', '/pages/%d' % k['id'], {'content': corps})
                relu = dep.appel('GET', '/pages/%d?context=edit' % k['id'])
                if 'data-jpj-ico="1"' in relu['content']['raw']:
                    break
            except SystemExit as motif:
                print('      reprise %d/3 — %s' % (essai + 1, str(motif).splitlines()[0][:60]))
            time.sleep(2 ** essai)
        else:
            print('      ✗ ABANDON #%d' % k['id'])
    print('\n%d page(s) corrigée(s).' % n)


if __name__ == '__main__':
    main()
