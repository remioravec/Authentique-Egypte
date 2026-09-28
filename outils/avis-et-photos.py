#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ce que j'avais renvoyé à la cliente et que je pouvais faire moi-même.

    WP_AUTH='compte:mot de passe' ./outils/avis-et-photos.py [--essai]

Onze fils attendaient d'elle des liens d'avis, huit attendaient des
photos. En vérifiant au lieu de demander, la plupart se règlent ici.

LES LIENS D'AVIS (#10743, #10749, #10759, #10764, #10781, #10795,
#10826, #10848). J'ai réclamé l'adresse de la fiche Google : elle était
déjà dans le site, sur quatorze pages, sous le bouton « Voir les avis
sur Google ». Vingt-et-une pages portent un mur d'avis sans ce bouton.
On le pose partout.

Pour TripAdvisor, la fiche existe et je l'ai trouvée en cherchant —
« AUTHENTIQUE ÉGYPTE (Le Caire) ». TripAdvisor refuse les requêtes
automatiques, je n'ai donc pas pu ouvrir la page moi-même pour la
vérifier : le lien est posé et signalé comme à confirmer d'un coup
d'œil.

LES PHOTOS DU GUIDE (#10808 à #10815). J'ai écrit « je n'ai aucune
image de l'oasis de Dakhla » et « aucune image du Désert Noir ». C'était
faux : la médiathèque en contient six et deux. Je n'avais pas cherché.
Sept des huit lieux ont leur photo ici ; seul Bahariya n'en a aucune.
"""

import argparse
import os
import re
import time
from importlib.machinery import SourceFileLoader

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MERE = 7642
Q = '/pages?parent=%d&per_page=100&status=any&context=edit&orderby=menu_order&order=asc'
E = '.elementor-template-canvas '

GOOGLE = 'https://search.google.com/local/reviews?placeid=ChIJOZOsXzk5WBQRMujsdlYsBy8'
TRIPADVISOR = ('https://www.tripadvisor.fr/Attraction_Review-g294201-d15316887-'
               'Reviews-Authentique_Egypte-Cairo_Cairo_Governorate.html')

BTN_GOOGLE = ('<a class="mur__lien btn btn--fantome btn--sm" href="%s" '
              'target="_blank" rel="noopener">Voir les avis sur Google</a>' % GOOGLE)
BTN_TRIPA = ('<a class="mur__lien mur__lien--ta btn btn--fantome btn--sm" href="%s" '
             'target="_blank" rel="noopener">Voir les avis sur TripAdvisor</a>' % TRIPADVISOR)

# (identifiant de section, lieu, url) — la médiathèque, vérifiée fichier
# par fichier. Bahariya est absent : aucune image, et je ne mets pas la
# photo d'une autre oasis à la place.
PHOTOS_GUIDE = [
    ('s1', 'Oasis de Dakhla',
     'https://authentiquegypte.com/wp-content/uploads/2025/09/DAKHLA-OASIS-DAY-3.jpeg'),
    ('s5', 'Désert Blanc',
     'https://authentiquegypte.com/wp-content/uploads/2025/07/Voyage-au-desert-blanc-en-Egypte.png'),
    ('s7', 'Désert Noir',
     'https://authentiquegypte.com/wp-content/uploads/2025/07/Voyage-dans-le-Desert-noir-en-Egypte.png'),
    ('s9', 'Fayoum',
     'https://authentiquegypte.com/wp-content/uploads/2025/09/FAYOUM-J2.jpeg'),
    ('s11', 'Oasis de Siwa',
     'https://authentiquegypte.com/wp-content/uploads/2025/09/SIWA-J2-scaled.jpg'),
    ('s13', 'Lac Nasser',
     'https://authentiquegypte.com/wp-content/uploads/2023/10/lake-nasser-1024x683-1.jpg'),
    ('s15', 'Sud Sinaï',
     'https://authentiquegypte.com/wp-content/uploads/2025/07/Voyage-au-Mont-Sinai.png'),
]

FEUILLE = (
    '<style data-avis="1">'
    + E + '.pg .mur__liens{display:flex;flex-wrap:wrap;gap:10px;align-items:center}'
    + E + '.pg .art__ill{margin:16px 0 20px}'
    + E + '.pg .art__ill img{width:100%;height:auto;display:block;'
    'border-radius:var(--r-l,20px);aspect-ratio:16/9;object-fit:cover}'
    + E + '.pg .art__ill figcaption{margin:8px 0 0;font-size:.82rem;'
    'color:var(--gris,#6E7680)}'
    '</style>')


def _fin(h, d, nom):
    p = 0
    for t in re.finditer(r'<(/?)%s\b[^>]*>' % nom, h[d:]):
        p += 1 if not t.group(1) else -1
        if p == 0:
            return d + t.end()
    return -1


def liens_avis(h):
    """Le bouton Google là où il manque, TripAdvisor partout."""
    if 'class="mur"' not in h:
        return h, []
    faits = []
    m = re.search(r'<a class="mur__lien[^"]*"[^>]*>.*?</a>', h, re.S)

    if m:
        # Un groupe, pour que les deux boutons tiennent côte à côte.
        if 'mur__liens' not in h:
            h = (h[:m.start()] + '<div class="mur__liens">' + m.group(0) + '</div>'
                 + h[m.end():])
        if 'tripadvisor' not in h.lower():
            i = h.find('</div>', h.find('<div class="mur__liens">'))
            h = h[:i] + BTN_TRIPA + h[i:]
            faits.append('lien TripAdvisor ajouté')
        return h, faits

    # Pas de bouton du tout : on le pose à la fin du mur.
    d = h.find('<div class="mur">')
    if d < 0:
        d = h.find('<div class="mur"')
    if d < 0:
        return h, faits
    f = _fin(h, d, 'div')
    if f < 0:
        return h, faits
    h = (h[:f] + '<div class="mur__liens">' + BTN_GOOGLE + BTN_TRIPA + '</div>' + h[f:])
    faits.append('liens Google et TripAdvisor ajoutés')
    return h, faits


def photos_guide(h, pid):
    """Les sept photos que la médiathèque avait, et que j'avais niées."""
    if pid != 8936:
        return h, []
    n = 0
    for ancre, lieu, url in PHOTOS_GUIDE:
        if url in h:
            continue
        m = re.search(r'<h2 id="%s">.*?</h2>' % ancre, h, re.S)
        if not m:
            continue
        fig = ('<figure class="art__ill"><img src="%s" alt="%s" loading="lazy" '
               'decoding="async"></figure>' % (url, lieu))
        h = h[:m.end()] + fig + h[m.end():]
        n += 1
    return (h, ['%d photo(s) du guide posée(s)' % n]) if n else (h, [])


def corriger(h, pid):
    faits = []
    h, f = liens_avis(h); faits += f
    h, f = photos_guide(h, pid); faits += f
    if not faits:
        return h, faits
    if 'data-avis="1"' not in h:
        h += FEUILLE
    return h, faits


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
        neuf, faits = corriger(brut, k['id'])
        if not faits:
            continue
        print('   #%-6d %-34s %s' % (k['id'], (p_.get('title') or {}).get('raw', '')[:34],
                                     ' · '.join(faits)[:80]))
        if a.essai:
            continue
        n += 1
        corps = '<!-- wp:html -->\n' + neuf + '\n<!-- /wp:html -->'
        for essai in range(4):
            try:
                dep.appel('POST', '/pages/%d' % k['id'], {'content': corps})
                relu = dep.appel('GET', '/pages/%d?context=edit' % k['id'])
                if 'data-avis="1"' in relu['content']['raw']:
                    break
            except SystemExit as motif:
                print('      reprise %d/3 — %s' % (essai + 1, str(motif).splitlines()[0][:60]))
            time.sleep(2 ** essai)
        else:
            print('      ✗ ABANDON #%d' % k['id'])
    print('\n%d page(s) corrigée(s).' % n)


if __name__ == '__main__':
    main()
