#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Les séjours listés sur une page destination sont ceux qui y passent.

    WP_AUTH='compte:mot de passe' ./outils/sejours-reels.py [--essai]

Mélanie le dit cinq fois : « ce programme n'a pas Alexandrie » (quatre
fois) et « il manque beaucoup de séjours, ajouter tous les séjours où il
y a Le Caire ». Elle a raison sur les deux, et l'écart est mesurable.

CE QUI ÉTAIT AFFICHÉ, ET CE QUI EST VRAI. Les listes étaient construites
à partir des liens des pages actuellement en ligne. On les reconstruit à
partir du DÉROULÉ JOUR PAR JOUR des quatorze fiches — la seule source qui
dise vraiment où l'on passe.

    Le Caire        1 affiché → 9 réels
    Mont Sinaï      1 → 5
    Louxor          4 → 6
    Assouan         5 → 3
    Alexandrie      6 → 0
    Désert noir     6 → 0
    Désert blanc    2 → 1
    Fayoum, Lac Nasser : 1 → 1, déjà juste

Gizeh compte pour Le Caire : les pyramides sont dans l'agglomération, et
une fiche qui s'appelle « Le Caire et croisière » ne dit « Le Caire »
nulle part dans son déroulé — elle dit Gizeh.

DEUX PAGES SE RETROUVENT SANS AUCUN SÉJOUR, et c'est la vérité :
Alexandrie et le désert Noir n'apparaissent dans aucun itinéraire. On ne
les remplit pas avec des séjours qui n'y passent pas — c'était le
défaut. La section dit ce qui est, et propose le sur-mesure. À Mélanie
de nous dire si des séjours doivent exister pour ces deux lieux.
"""

import argparse
import html as H
import json
import os
import re
import time
from importlib.machinery import SourceFileLoader

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MERE = 7642
Q = '/pages?parent=%d&per_page=100&status=any&context=edit&orderby=menu_order&order=asc'
DEVIS = 'https://authentiquegypte.com/sur-mesure/'

# Les lieux cherchés dans le déroulé, et ce qu'ils valent pour chaque page.
VILLES = ['Le Caire', 'Gizeh', 'Alexandrie', 'Louxor', 'Assouan', 'Abou Simbel',
          'Abu Simbel', 'Hurghada', 'Siwa', 'Fayoum', 'Dahab', 'Sharm',
          'Sainte-Catherine', 'lac Nasser', 'Nubie', 'Kom Ombo', 'Edfou',
          'désert blanc', 'Bahariya', 'mont Moïse', 'Marsa Alam']

CIBLES = {
    'refonte-destination-voyage-au-caire': ['Le Caire'],
    'refonte-destination-voyage-a-louxor': ['Louxor'],
    'refonte-destination-voyage-a-assouan': ['Assouan'],
    'refonte-destination-voyage-a-alexandrie': ['Alexandrie'],
    'refonte-destination-voyage-a-fayoum': ['Fayoum'],
    'refonte-destination-desert-blanc': ['désert blanc', 'Bahariya'],
    'refonte-destination-desert-noir': ['désert noir'],
    'refonte-destination-lac-nasser': ['lac Nasser'],
    'refonte-destination-mont-sinai': ['mont Moïse', 'Sainte-Catherine'],
}

FLECHE = ('<svg width="15" height="11" viewBox="0 0 15 11" fill="none" aria-hidden="true">'
          '<path d="M1 5.5h12M9 1.5l4 4-4 4" stroke="currentColor" stroke-width="1.7" '
          'stroke-linecap="round" stroke-linejoin="round"/></svg>')


def _fin(h, debut, nom):
    p = 0
    for t in re.finditer(r'<(/?)%s\b[^>]*>' % nom, h[debut:]):
        p += 1 if not t.group(1) else -1
        if p == 0:
            return debut + t.end()
    return -1


def villes_du_deroule(h):
    """Les lieux cités dans le jour par jour, et nulle part ailleurs.

    Chercher dans la page entière ramènerait le méga-menu et les cartes
    « ces séjours se combinent bien » : toutes les fiches passeraient alors
    par toutes les villes. Seuls les volets d'étape et les titres de
    journée comptent.
    """
    corps = ' '.join(
        re.sub(r'<[^>]+>', ' ', x) for x in
        re.findall(r'<article class="etape".*?</article>|<div class="jour__tete">.*?</div>',
                   h, re.S))
    corps = re.sub(r'\s+', ' ', corps).lower()
    v = {x for x in VILLES if x.lower() in corps}
    if 'Gizeh' in v:
        v.add('Le Caire')
    return v


def fiche_de(h):
    """Ce qu'il faut pour bâtir une carte : titre, adresse, photo, prix, durée."""
    def un(motif, defaut=''):
        m = re.search(motif, h, re.S)
        return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', m.group(1))).strip() if m else defaut
    cles = re.findall(r'<div class="pan__cle"><small>[^<]*</small><b>([^<]+)</b>', h)
    img = re.search(r'<div class="hero__fond"><img[^>]*src="([^"]+)"[^>]*alt="([^"]*)"', h, re.S)
    return {
        'url': un(r'"url": "(https://authentiquegypte\.com/programs/[^"]+)"'),
        'titre': un(r'<h1[^>]*>(.*?)</h1>'),
        'chapo': un(r'<p class="hero__chapo">(.*?)</p>'),
        'prix': cles[0].strip() if cles else '',
        'duree': cles[1].strip() if len(cles) > 1 else '',
        'img': img.group(1) if img else '',
        'alt': img.group(2) if img else '',
    }


def carte(f):
    jours = re.search(r'(\d+)', f['duree'] or '')
    pastille = ('<span class="carte__duree">%s jour%s</span>'
                % (jours.group(1), 's' if jours and int(jours.group(1)) > 1 else '')) if jours else ''
    chapo = f['chapo']
    if len(chapo) > 120:
        chapo = chapo[:119].rstrip(' ,;:') + '…'
    return (
        '<article class="carte" data-duree="%s" data-prix="%s">'
        '<div class="carte__img">%s<img src="%s" alt="%s" loading="lazy" decoding="async"></div>'
        '<div class="carte__corps"><h3><a href="%s">%s</a></h3>'
        '<p class="carte__route">%s</p>'
        '<div class="carte__pied"><span class="prix"><small>À partir de</small>'
        '<b>%s</b> <i>/ pers.</i></span>'
        '<a href="%s" class="lien-fl" aria-label="Voir le détail : %s">Voir le détail %s</a>'
        '</div></div></article>'
        % (_tranche_duree(jours), _tranche_prix(f['prix']), pastille,
           H.escape(f['img']), H.escape(f['alt']), H.escape(f['url']), H.escape(f['titre']),
           H.escape(chapo), H.escape(f['prix']), H.escape(f['url']),
           H.escape(f['titre']), FLECHE))


def _tranche_duree(m):
    if not m:
        return ''
    j = int(m.group(1))
    return '1-2' if j <= 2 else ('3-5' if j <= 5 else '6+')


def _tranche_prix(p):
    n = re.sub(r'[^\d]', '', p or '')
    if not n:
        return ''
    n = int(n)
    return '0-500' if n < 500 else ('500-1000' if n < 1000 else '1000+')


VIDE = (
    '<p class="fac__rien" style="display:block">Aucun de nos séjours ne passe '
    'aujourd\'hui par %s. Dites-nous vos dates et ce que vous voulez y voir&nbsp;: '
    'nous construisons l\'itinéraire. <a href="' + DEVIS + '">Demander un devis</a>.</p>')


def corriger(h, slug, fiches, lieu):
    cles = CIBLES.get(slug)
    if not cles:
        return h, []
    gardes = [i for i, f in fiches.items()
              if any(c.lower() in ' '.join(f['villes']).lower() for c in cles)]
    gardes.sort(key=lambda i: int(re.sub(r'[^\d]', '', fiches[i]['prix']) or 0))

    d = h.find('<div class="cartes')
    if d < 0:
        return h, []
    f = _fin(h, d, 'div')
    if f < 0:
        return h, []
    avant = len(re.findall(r'<article class="carte"', h[d:f]))

    if gardes:
        neuf = ('<div class="cartes cartes--2">%s</div>'
                % ''.join(carte(fiches[i]) for i in gardes))
    else:
        neuf = '<div class="cartes cartes--2">%s</div>' % (VIDE % H.escape(lieu))
    if neuf == h[d:f]:
        return h, []
    h = h[:d] + neuf + h[f:]

    # Le compteur de la zone de filtres doit suivre.
    h = re.sub(r'(<p class="fac__cpt"[^>]*>)\d+ séjours?',
               lambda m: '%s%d séjour%s' % (m.group(1), len(gardes), 's' if len(gardes) > 1 else ''),
               h)
    return h, ['séjours recalculés : %d → %d' % (avant, len(gardes))]


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

    # Les quatorze fiches d'abord : elles disent où l'on passe.
    fiches = {}
    for k in pages:
        if not k['slug'].startswith('refonte-programme-'):
            continue
        h = k['content']['raw']
        f = fiche_de(h)
        f['villes'] = villes_du_deroule(h)
        if f['url'] and f['titre']:
            fiches[str(k['id'])] = f
    print('%d fiche(s) lue(s).\n' % len(fiches))

    n = 0
    for k in pages:
        if k['slug'] not in CIBLES:
            continue
        p_ = dep.appel('GET', '/pages/%d?context=edit' % k['id'])
        titre = (p_.get('title') or {}).get('raw', '')
        lieu = re.sub(r'^Refonte · Destination · Voyage (?:au |à l.|à la |à |dans le |)', '',
                      titre).strip() or titre
        brut = re.sub(r'<!-- /?wp:html -->\n?', '', p_['content']['raw'])
        neuf, faits = corriger(brut, k['slug'], fiches, lieu)
        if not faits:
            continue
        print('   #%-6d %-32s %s' % (k['id'], titre[24:56], ' · '.join(faits)))
        if a.essai:
            continue
        n += 1
        corps = '<!-- wp:html -->\n' + neuf + '\n<!-- /wp:html -->'
        for essai in range(4):
            try:
                dep.appel('POST', '/pages/%d' % k['id'], {'content': corps})
                relu = dep.appel('GET', '/pages/%d?context=edit' % k['id'])
                if 'class="cartes' in relu['content']['raw']:
                    break
            except SystemExit as motif:
                print('      reprise %d/3 — %s' % (essai + 1, str(motif).splitlines()[0][:60]))
            time.sleep(2 ** essai)
        else:
            print('      ✗ ABANDON #%d' % k['id'])
    print('\n%d page(s) destination remise(s) à jour.' % n)


if __name__ == '__main__':
    main()
