#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Les défauts réels trouvés en validant la fiche Fayoum, corrigés partout.

    WP_AUTH='compte:mot de passe' ./outils/defauts-relecture.py [--essai]

Fayoum devait servir de référence aux treize autres fiches : tout ce
qu'on y laisse passer se recopie quatorze fois. Deux contrôles l'ont
passée au crible ; j'ai vérifié chaque alerte une par une. Plusieurs
étaient fausses — attributs HTML en double (zéro), phrase recollée dans
le hero (les deux mentions sont séparées par un gap flex de 18px),
sélecteur de carte absent (il est là). Restent ces cinq-là, toutes
mesurées, toutes de mon fait :

1. « N'inclus pas » est du français fautif. Le titre devient « Non
   inclus ». Quatorze pages.

2. UN LIEN QUI PASSE PAR GOOGLE. Dans la réponse « Est-ce dangereux de
   venir en Égypte ? », le lien vers l'article sécurité pointe sur
   google.com/url?sa=t&…&url=https://authentiquegypte.com/… — un
   copier-coller depuis une page de résultats. Le visiteur part chez
   Google pour revenir sur le site, le jus de lien se perd en route et
   l'URL expirera. On pointe directement. Trente-quatre pages.

3. UNE VIRGULE AVANT SON MOT : « puis le solde ,45 jours avant le
   départ ». Dans mon texte du tronc commun, pas dans celui de Mélanie.

4. CHAQUE PAGE ANNONÇAIT QU'ELLE EST UNE MAQUETTE. Le pied affichait
   « © 2026 Authentique Égypte — Maquette de refonte, charte relevée le
   21/08/2026 ». Vrai pendant la fabrication, intenable le jour de la
   mise en ligne : la mention part maintenant, pas la veille. Les 57
   pages.

5. LE BOUTON OR EST ILLISIBLE. Blanc sur or, le contraste mesure 1,79:1
   là où la norme demande 4,5:1. Ce n'est pas un choix de direction
   artistique : la charte déclare deux fois .btn--or{color:nuit-900}
   (6,5:1, lisible), et une règle tardive l'écrase en blanc. On retire
   l'écrasement, la charte reprend la main. C'est le bouton « Recevoir
   mon devis » : celui sur lequel on compte.
"""

import argparse
import os
import re
import time
from importlib.machinery import SourceFileLoader

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MERE = 7642
Q = '/pages?parent=%d&per_page=100&status=any&context=edit&orderby=menu_order&order=asc'

PIED_NEUF = '© 2026 Authentique Égypte'

# La règle tardive qui rend le bouton or illisible, et son pendant sur
# les icônes. On la remplace plutôt que de la supprimer : une feuille du
# moule peut être réécrite ailleurs, une couleur explicite ne l'est pas.
BLANC = ('.elementor-template-canvas .pg .btn--or, '
         '.elementor-template-canvas .pg .btn--or:hover, '
         '.elementor-template-canvas .pg .btn--or:focus-visible, '
         '.elementor-template-canvas .pg .pg-mob .btn--or{color:#fff}')
NOIR = BLANC.replace('color:#fff', 'color:var(--nuit-900,#095360)')
BLANC_SVG = '.elementor-template-canvas .pg .btn--or svg{color:#fff}'
NOIR_SVG = BLANC_SVG.replace('color:#fff', 'color:var(--nuit-900,#095360)')


def corriger(h):
    faits = []

    n = h.count('N&#x27;inclus pas') + h.count("N'inclus pas")
    if n:
        h = h.replace('N&#x27;inclus pas', 'Non inclus').replace("N'inclus pas", 'Non inclus')
        faits.append('« Non inclus »')

    # Le lien rendu par Google porte la vraie adresse dans son paramètre
    # url= : on la ressort plutôt que de la deviner.
    def direct(m):
        # Dans le HTML l'esperluette est encodée : le paramètre s'écrit
        # « &amp;url= », pas « &url= ». Chercher l'un sans l'autre ne
        # trouvait rien et laissait le redirecteur en place.
        vraie = re.search(r'(?:[?&]|&amp;)url=(https[^&"]+)', m.group(0))
        return vraie.group(1) if vraie else m.group(0)

    avant = h
    h = re.sub(r'https://www\.google\.com/url\?[^"\']+', direct, h)
    if h != avant:
        faits.append('lien direct au lieu du redirecteur Google')

    if 'solde ,' in h:
        h = h.replace('solde ,', 'solde, ')
        faits.append('virgule remise à sa place')

    if 'Maquette de refonte, charte relevée' in h:
        h = re.sub(r'© 2026 Authentique Égypte[^<]*', PIED_NEUF, h)
        faits.append('mention de maquette retirée du pied')

    if BLANC in h or BLANC_SVG in h:
        h = h.replace(BLANC, NOIR).replace(BLANC_SVG, NOIR_SVG)
        faits.append('bouton or lisible (1,79:1 → 6,5:1)')

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
        neuf, faits = corriger(brut)
        if not faits:
            continue
        print('   #%-6d %-38s %s' % (k['id'], (p_.get('title') or {}).get('raw', '')[:38],
                                     ' · '.join(faits)))
        if a.essai:
            continue
        n += 1
        corps = '<!-- wp:html -->\n' + neuf + '\n<!-- /wp:html -->'
        for essai in range(4):
            try:
                dep.appel('POST', '/pages/%d' % k['id'], {'content': corps})
                relu = dep.appel('GET', '/pages/%d?context=edit' % k['id'])
                if 'Maquette de refonte, charte relevée' not in relu['content']['raw']:
                    break
            except SystemExit as motif:
                print('      reprise %d/3 — %s' % (essai + 1, str(motif).splitlines()[0][:60]))
            time.sleep(2 ** essai)
        else:
            print('      ✗ ABANDON #%d' % k['id'])
    print('\n%d page(s) corrigée(s).' % n)


if __name__ == '__main__':
    main()
