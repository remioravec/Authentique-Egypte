#!/usr/bin/env python3
"""Les textes de présentation des destinations.

    WP_AUTH='compte:mdp' python3 outils/retours-07-villes.py --essai
    WP_AUTH='compte:mdp' python3 outils/retours-07-villes.py --appliquer

Mélanie demande quatre fois la même chose : « est-ce possible à la place de
mettre un court texte sur la ville et présenter la ville » (12313 Louxor,
12320 Assouan, 12322 Le Caire, 12323 Lac Nasser). Le chapô qu'elle vise est
le même sur sept pages de destination : « Confiez l'organisation de votre
voyage en Égypte à nos agents locaux. » Elle l'a aussi fait retirer du blog
(12329). On le remplace donc partout, pas seulement sur les quatre pages où
elle a laissé un commentaire.

Chaque texte est tiré de ce que la page dit déjà d'elle-même — ses sites, ses
durées, ses périodes, son climat. Rien n'est inventé : la FAQ d'Assouan donne
les 280 km jusqu'à Abou Simbel, celle de Fayoum le 4x4 pour Wadi Al-Hitan,
celle du mont Sinaï le départ entre une et deux heures du matin.

Alexandrie (12321) n'a pas de page : Mélanie écrit elle-même « je vais en
ajouter » (12298). Rien à faire ici.
"""

import argparse
import base64
import os
import re
import time

import requests

SITE = 'https://authentiquegypte.com'

CHAPOS = {
    5191: (  # Le Caire · 12322
        'Le Caire tient dans un même horizon les pyramides de Gizeh et le '
        'Sphinx, les momies royales du Musée égyptien, le quartier islamique '
        'classé à l’UNESCO, les églises du Vieux Caire et les ruelles de Khan '
        'el-Khalili. Comptez trois à cinq jours pour en voir l’essentiel sans '
        'courir, et un chauffeur&nbsp;: ici, c’est la circulation qui décide '
        'du reste.'),
    5201: (  # Louxor · 12313
        'Louxor est le plus grand musée à ciel ouvert du monde. Sur la rive '
        'est, le temple de Karnak et le temple de Louxor au bord du '
        'fleuve&nbsp;; sur la rive ouest, la vallée des Rois, le temple '
        'd’Hatchepsout adossé à la montagne thébaine et les colosses de '
        'Memnon. Deux à trois jours suffisent pour les deux rives, et une '
        'montgolfière à l’aube si le cœur vous en dit.'),
    5210: (  # Assouan · 12320
        'Assouan est la ville la plus paisible du Nil égyptien, celle où le '
        'fleuve s’élargit entre les îles et les villages nubiens. On y visite '
        'le temple de Philae sauvé des eaux, qu’on rejoint en bateau, l’île '
        'Éléphantine, l’obélisque inachevé resté dans sa carrière de granit et '
        'le mausolée de l’Aga Khan. Un à deux jours suffisent, trois si vous '
        'poussez jusqu’à Abou Simbel, à 280&nbsp;km au sud.'),
    5556: (  # Lac Nasser · 12323
        'Le lac Nasser est né du haut barrage d’Assouan, et sa mise en eau a '
        'obligé l’Égypte à déplacer ses temples pierre par pierre&nbsp;: Abou '
        'Simbel d’abord, puis Amada, Derr et Wadi es-Seboua, posés aujourd’hui '
        'sur ses rives. On y navigue trois à quatre nuits, entre des criques '
        'désertiques et des îles que presque personne ne visite, d’octobre à '
        'avril.'),
    5229: (  # Fayoum · même chapô, même défaut
        'À une heure et demie de route au sud-ouest du Caire, Fayoum occupe '
        'une dépression cernée de désert&nbsp;: le lac salé de Qarun et sa '
        'réserve naturelle, les deux cascades de Wadi El Rayan, les squelettes '
        'de baleines fossiles de Wadi Al-Hitan classés à l’UNESCO, et les '
        'ateliers de poterie de Tunis Village. Une journée donne un aperçu, '
        'deux permettent d’atteindre les sites qui demandent un 4x4.'),
    5547: (  # mont Sinaï
        'Le mont Sinaï, le Gebel Moussa des Égyptiens, domine le village de '
        'Sainte-Catherine et son monastère. On en fait l’ascension de nuit, '
        'départ entre une et deux heures du matin, pour être au sommet au '
        'lever du soleil&nbsp;; on visite le monastère en redescendant. '
        'D’octobre à avril&nbsp;: en été il fait chaud même la nuit, et '
        'l’hiver le sommet approche parfois zéro degré.'),
    5532: (  # Désert blanc
        'À quelques heures de piste de l’oasis de Bahariya, le Désert blanc '
        'est une plaine de craie que le vent a sculptée en champignons et en '
        'tours. On y marche au lever et au coucher du soleil, quand la roche '
        'prend la lumière, et le ciel nocturne y est l’un des plus purs '
        'd’Égypte. Deux à trois jours au minimum, de novembre à '
        'mars&nbsp;; l’été est déconseillé.'),
}

GENERIQUE = re.compile(
    r'<p class="hero__chapo">Confiez l(?:&#x27;|&#039;|\'|’)organisation'
    r'(?:(?!</p>).)*?</p>', re.S)


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
    B = SITE + '/wp-json/wp/v2/pages/'

    a_ecrire = []
    for i, texte in CHAPOS.items():
        d = S.get(B + str(i), params={'context': 'edit'}, timeout=120).json()
        h = (d.get('content') or {}).get('raw', '')
        titre = (d.get('title') or {}).get('raw', '')
        trouve = GENERIQUE.findall(h)
        if len(trouve) != 1:
            print('%-34s %d chapô générique trouvé(s) — laissée en place'
                  % (titre[:34], len(trouve)))
            continue
        neuf = GENERIQUE.sub(
            '<p class="hero__chapo">' + texte + '</p>', h, count=1)
        a_ecrire.append((i, titre, neuf))
        print('%-34s %d caractères de présentation' % (titre[:34], len(texte)))

    print('\n%d page(s) à écrire' % len(a_ecrire))
    if a.essai:
        return
    for i, titre, neuf in a_ecrire:
        for essai in range(4):
            r = S.post(B + str(i), json={
                'content': '<!-- wp:html -->\n' + neuf + '\n<!-- /wp:html -->'},
                timeout=300)
            if r.status_code < 300:
                break
            time.sleep(2 ** essai)
        else:
            raise SystemExit('écriture refusée sur %s' % titre)
        d = S.get(B + str(i), params={'context': 'edit'}, timeout=120).json()
        vu = (d.get('content') or {}).get('raw', '')
        if GENERIQUE.search(vu):
            raise SystemExit('le chapô générique est encore là sur %s' % titre)
    print('%d page(s) écrites et relues.' % len(a_ecrire))


if __name__ == '__main__':
    main()
