#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
La carte du voyage, sur les programmes qui n'en avaient pas.

    WP_AUTH='compte:mot de passe' ./outils/carte-programme.py [--essai]

« Ajouter une carte du voyage » (#10435). Quatre programmes n'en
portaient aucune : ceux dont la v1 n'avait pas de dessin à convertir, là
où outils/carte-leaflet.py n'avait rien à reprendre. Celle-ci se
construit à partir du séjour lui-même.

D'OÙ VIENNENT LES ÉTAPES. Des titres de journée, pas du texte courant.
Le premier essai lisait le déroulé en entier et rendait « Abu Simbel →
Louxor → Le Caire → lac Nasser » pour un séjour qui commence à Assouan :
une prose de voyage cite quantité de lieux qu'on ne traverse pas. Le
titre d'une journée, lui, dit où l'on est ce jour-là.

LES ALIAS SONT DES FAITS. Karnak et la vallée des Rois sont à Louxor,
Gizeh et le musée Égyptien au Caire, Philae à Assouan. Une journée
intitulée « Visite des Pyramides de Gizeh » est une journée au Caire, et
c'est la ville qu'il faut placer — pas un point de plus sur la carte.

CE QUE L'OUTIL REFUSE DE FAIRE. Moins de deux étapes reconnues : pas de
carte. Une carte à un seul point ne dit rien d'un itinéraire, et une
carte fausse vaut moins que pas de carte.
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

CARTE = SourceFileLoader('carte_leaflet',
                         os.path.join(RACINE, 'outils', 'carte-leaflet.py')).load_module()
LIEUX = CARTE.LIEUX

# Ce qu'un titre de journée peut nommer, et la ville que cela désigne.
# Rien ici n'est une interprétation : ce sont des positions connues.
ALIAS = [
    ('Abu Simbel', 'Abu Simbel'), ('Abou Simbel', 'Abu Simbel'),
    ('Aswan', 'Assouan'), ('Assouan', 'Assouan'), ('Philae', 'Assouan'),
    ('Kom Ombo', 'Kom Ombo'), ('Edfu', 'Edfou'), ('Edfou', 'Edfou'),
    ('Louxor', 'Louxor'), ('Karnak', 'Louxor'), ('Vallée des Rois', 'Louxor'),
    ('vallée des Rois', 'Louxor'), ('Deir el-Bahari', 'Louxor'),
    ('Hatchepsout', 'Louxor'), ('Hatshepsout', 'Louxor'), ('Memnon', 'Louxor'),
    ('Le Caire', 'Le Caire'), ('Caire', 'Le Caire'), ('Gizeh', 'Le Caire'),
    ('Guizeh', 'Le Caire'), ('Sphinx', 'Le Caire'), ('Saqqara', 'Le Caire'),
    ('Musée Égyptien', 'Le Caire'), ('musée Egyptien', 'Le Caire'),
    ('Hurghada', 'Hurghada'), ('Gouna', 'Hurghada'), ('mer rouge', 'Hurghada'),
    ('mer Rouge', 'Hurghada'),
    ('Sainte-Catherine', 'Sainte-Catherine'), ('Sainte Catherine', 'Sainte-Catherine'),
    ('Gebel Moussa', 'Gebel Moussa'), ('mont Moïse', 'Gebel Moussa'),
    ('Sharm el-Sheikh', 'Sharm el-Sheikh'), ('Dahab', 'Dahab'),
    ('Siwa', 'Siwa'), ('Fayoum', 'Fayoum'), ('Bahariya', 'Bahariya'),
    ('Désert Blanc', 'Désert Blanc'), ('désert blanc', 'Désert Blanc'),
    ('Alexandrie', 'Alexandrie'),
    ('lac Nasser', 'Lac Nasser'), ('Lac Nasser', 'Lac Nasser'),
]

# Le cadre ne s'appelle pas « carte » : cette classe-là porte déjà, dans
# le moule, les vignettes de séjour — un padding, un figcaption écrasé et
# un soulèvement au survol. La carte du voyage hériterait de tout cela.
TETE = (
    '<figure class="cartep"><figcaption class="cartep__tete">'
    '<p class="eyebrow">Sur la carte</p><h2>L’itinéraire de votre séjour</h2>'
    '</figcaption>')

PIED = ('<figcaption class="cartep__note">Fond de carte OpenStreetMap France '
        '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" '
        'rel="noopener">les contributeurs d’OpenStreetMap</a>.</figcaption></figure>')

FEUILLE = (
    '<style data-carte-prog="1">'
    '.elementor-template-canvas .pg .cartep{margin:0;padding:0}'
    '.elementor-template-canvas .pg .cartep__tete{margin:0 0 18px;text-align:center;padding:0}'
    '.elementor-template-canvas .pg .cartep__note{margin:12px 0 0;'
    'text-align:center;font-size:.8rem;color:var(--gris,#6E7680)}'
    '.elementor-template-canvas .pg .cartep__tete h2{margin:0}'
    '</style>')


def _fin(h, d, nom):
    p = 0
    for t in re.finditer(r'<(/?)%s\b[^>]*>' % nom, h[d:]):
        p += 1 if not t.group(1) else -1
        if p == 0:
            return d + t.end()
    return -1


def etapes_de(h):
    """Les villes traversées, dans l'ordre des journées."""
    titres = [re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', m.group(1)))
              for m in re.finditer(r'<div class="jour__tete">(.*?)</div>', h, re.S)]
    ordre = []
    for titre in titres:
        # Un titre peut nommer deux villes (« Le Caire - Oasis de Siwa ») :
        # on les prend dans l'ordre où elles y figurent.
        trouves = []
        for mot, ville in ALIAS:
            i = titre.find(mot)
            if i >= 0:
                trouves.append((i, ville))
        for _, ville in sorted(trouves):
            # Deux journées au même endroit ne font qu'un point.
            if not ordre or ordre[-1] != ville:
                ordre.append(ville)
    # Un aller-retour repasse par la même ville : c'est voulu, la
    # polyligne doit le montrer. Seules les répétitions consécutives
    # tombent, déjà écartées plus haut.
    return [v for v in ordre if v in LIEUX]


def corriger(h):
    if 'carte__map' in h or 'data-carte-prog' in h:
        return h, []
    etapes = etapes_de(h)
    if len(set(etapes)) < 2:
        return h, []
    d = h.find('<h2 id="t-jpj"')
    if d < 0:
        return h, []
    pose = h.rfind('<section', 0, d)
    if pose < 0:
        return h, []

    donnees = [{'n': e, 'lat': LIEUX[e][0], 'lon': LIEUX[e][1]} for e in etapes]
    liste = ''.join('<li><b>%d</b>%s</li>' % (i + 1, H.escape(e))
                    for i, e in enumerate(etapes))
    bloc = (TETE
            + '<div class="carte__map" data-carte=\'%s\' role="img" '
              'aria-label="Carte de l’itinéraire : %s"></div>'
              '<ul class="carte__etapes">%s</ul>'
              % (json.dumps(donnees, ensure_ascii=False).replace("'", '&#39;'),
                 H.escape(' puis '.join(etapes)), liste)
            + PIED)
    h = h[:pose] + '<section class="pg-sec">' + bloc + '</section>' + h[pose:]
    # Le fond français, comme sur les cartes de destination : les
    # étiquettes y sont en français. Le script vient de carte-leaflet.py,
    # dont il ne diffère que par cette ligne — la créditer à OpenStreetMap
    # France tout en tirant les tuiles du serveur international serait un
    # crédit faux.
    script = CARTE.SCRIPT.replace('https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                                  'https://a.tile.openstreetmap.fr/osmfr/{z}/{x}/{y}.png')
    return CARTE.TETE + FEUILLE + h + script, etapes


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
        neuf, etapes = corriger(brut)
        if not etapes:
            continue
        print('   #%-6d %-38s %s' % (k['id'], (p_.get('title') or {}).get('raw', '')[:38],
                                     ' → '.join(etapes)))
        if a.essai:
            continue
        n += 1
        corps = '<!-- wp:html -->\n' + neuf + '\n<!-- /wp:html -->'
        for essai in range(4):
            try:
                dep.appel('POST', '/pages/%d' % k['id'], {'content': corps})
                relu = dep.appel('GET', '/pages/%d?context=edit' % k['id'])
                if 'data-carte-prog' in relu['content']['raw']:
                    break
            except SystemExit as motif:
                print('      reprise %d/3 — %s' % (essai + 1, str(motif).splitlines()[0][:60]))
            time.sleep(2 ** essai)
        else:
            print('      ✗ ABANDON #%d' % k['id'])
    print('\n%d carte(s) ajoutée(s).' % n)


if __name__ == '__main__':
    main()
