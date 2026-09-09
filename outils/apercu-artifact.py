#!/usr/bin/env python3
"""Une copie AUTOPORTANTE d'une page, pour la montrer en ligne.

La page produite pointe la charte du site par un chemin relatif :
`assets/charte.css`. C'est juste sur le disque et dans le site, et c'est
introuvable partout ailleurs — un aperçu publié perd alors toute sa mise
en forme et n'affiche qu'une colonne de liens nus.

Ce script fabrique la copie à montrer : la charte entre dans la page, et
rien d'autre ne change. Les photos restent servies par le site de la
cliente, en lecture seule.

    outils/apercu-artifact.py maquettes/site/programme-<slug>.html
"""

import os
import re
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHARTE = os.path.join(RACINE, 'maquettes', 'assets', 'charte.css')
SORTIE = os.environ.get('APERCU_SORTIE') or '/tmp'


def main():
    if len(sys.argv) < 2:
        sys.exit('usage : apercu-artifact.py <page.html> [autre.html …]')
    with open(CHARTE, encoding='utf-8') as f:
        charte = f.read()
    for chemin in sys.argv[1:]:
        with open(chemin, encoding='utf-8') as f:
            page = f.read()
        neuf, n = re.subn(r'<link rel="stylesheet" href="[^"]*charte\.css">',
                          '<style>\n/* charte du site, intégrée pour l\'aperçu */\n'
                          + charte + '\n</style>', page)
        if not n:
            sys.exit('%s : aucun appel à la charte' % chemin)
        cible = os.path.join(SORTIE, os.path.basename(chemin))
        with open(cible, 'w', encoding='utf-8') as f:
            f.write(neuf)
        print('%-58s %d Ko' % (cible, os.path.getsize(cible) // 1024))


if __name__ == '__main__':
    main()
