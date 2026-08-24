#!/usr/bin/env python3
"""
Remplace les marqueurs <!--ENTETE--> et <!--PIED--> d'un gabarit par les
blocs communs, relevés une fois pour toutes dans maquettes/devis.html.

Les maquettes restent des fichiers HTML autonomes, ouvrables tels quels
dans un navigateur : ce script est un outil d'écriture, pas une étape de
construction. On l'exécute quand on crée un gabarit, puis le fichier vit
sa vie.

    ./outils/blocs.py maquettes/destination.html
"""

import re
import sys
import os

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELE = os.path.join(RACINE, 'maquettes', 'devis.html')


def extraire(source, debut, fin):
    i = source.index(debut)
    j = source.index(fin, i) + len(fin)
    return source[i:j]


def main():
    modele = open(MODELE, encoding='utf-8').read()

    bandeau = extraire(modele, '<div class="bandeau">', '</div>\n</div>')
    entete = extraire(modele, '<header class="entete">', '</header>')
    pied = extraire(modele, '<footer class="pied">', '</footer>')

    for chemin in sys.argv[1:]:
        page = open(chemin, encoding='utf-8').read()
        page = page.replace('<!--ENTETE-->', bandeau + '\n\n' + entete)
        page = page.replace('<!--PIED-->', pied)

        # La page courante se marque elle-même dans la navigation.
        nom = os.path.basename(chemin)
        page = page.replace(' aria-current="page">Obtenir mon devis<', '>Obtenir mon devis<')
        page = re.sub(r'(<a href="%s"[^>]*)>' % re.escape(nom),
                      lambda m: m.group(1) + ' aria-current="page">', page, count=1)

        open(chemin, 'w', encoding='utf-8').write(page)
        print('%-34s en-tête et pied injectés (%d octets)' % (nom, len(page)))


if __name__ == '__main__':
    main()
