#!/usr/bin/env python3
"""
Audit d'un gabarit : structure, UX/UI, cohérence interne — sur le rendu.

    ./outils/audit-gabarit.py --site DIR --gabarit destination-
    ./outils/audit-gabarit.py --site DIR --gabarit '*' --vignettes

Trois familles de défauts, mesurées en bureau (1280) et au doigt (Pixel 5) :

  STRUCTURE   ce qui casse la page — débordement horizontal, titre h1 en
              double, section tombée hors du <main> du gabarit, image sans
              source, mur d'avis déplié, bloc resté invisible.
  UX/UI       ce qui la rend pénible — contraste sous le seuil WCAG, cible
              tactile sous 44 px, texte sous le plancher typographique.
  COHÉRENCE   ce qui la rend fausse — un fil d'Ariane qui nomme une autre
              page, deux fois le même titre, un saut de niveau, un lien
              qui ne mène nulle part.

La troisième famille est la plus coûteuse : elle ne se voit pas. Une page
au fil d'Ariane emprunté est belle, complète, et fausse.

Les seuils sont ceux des règles, pas des avis :
  contraste 4,5:1 (3:1 au-delà de 24 px ou 18,66 px en gras) · cible 44 px
  au doigt · plancher typographique 14 px · aucune section hors du <main>.
"""

import argparse
import collections
import json
import os
import shutil
import subprocess
import sys
from importlib.machinery import SourceFileLoader

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SONDE = os.path.join(RACINE, 'outils', 'audit', 'sonde.js')

# Un faux positif connu, gardé nommé plutôt que filtré en silence : le
# bouton clair pose du blanc sur un voile blanc à 8 %, et la composition
# retombe sur le bleu nuit de la carte — 7,04:1 pour de vrai. La case qui
# met le mur d'avis en pause, elle, fait 1×1 px : elle se commande par son
# étiquette, ce n'est pas une cible.
TOLERES = {'input.mur__stop'}

# Les liens relatifs des maquettes sont réécrits au DÉPLOIEMENT, vers le
# brouillon de la refonte quand il existe. Les signaler ici reviendrait à
# mesurer un fichier que personne ne consulte : on lit la table du
# déployeur plutôt que de la recopier, pour qu'elles ne divergent jamais.
def liens_reecrits():
    chemin = os.path.join(RACINE, 'outils', 'deployer-refonte.py')
    if not os.path.exists(chemin):
        return set()
    dep = SourceFileLoader('dep_refonte', chemin).load_module()
    return set(dep.LIENS) | {'../' + x for x in dep.LIENS}


def node_path():
    """Le dossier où Playwright est installé — il n'est pas dans le projet."""
    for racine in ('/opt/node22/lib/node_modules', '/usr/lib/node_modules',
                   '/usr/local/lib/node_modules'):
        if os.path.isdir(os.path.join(racine, 'playwright')):
            return racine
    trouve = subprocess.run(
        ['find', '/', '-type', 'd', '-name', 'playwright', '-path', '*node_modules*'],
        capture_output=True, text=True).stdout.splitlines()
    if not trouve:
        raise SystemExit('Playwright introuvable')
    return os.path.dirname(trouve[0])


def sonder(site, gabarit, sortie):
    env = dict(os.environ, NODE_PATH=node_path())
    r = subprocess.run(['node', SONDE, site, gabarit, sortie], env=env,
                       capture_output=True, text=True)
    if r.returncode:
        raise SystemExit('la sonde a échoué :\n' + r.stderr[-2000:])
    with open(sortie, encoding='utf-8') as f:
        return json.load(f)


def defauts(page, vue):
    """Les écarts d'une page dans une vue, en clair."""
    d, c = page[vue]['structure'], page[vue]['coherence']
    out = []
    if d['debord']:
        out.append(('STRUCTURE', 'déborde de %d px' % (d['debord'] - (390 if vue == 'mobile' else 1280)),
                    ' '.join(d['larges'][:3])))
    if d['h1'] != 1:
        out.append(('STRUCTURE', '%d titre h1' % d['h1'], ''))
    if d['horsMain']:
        out.append(('STRUCTURE', '%d section hors du <main>' % len(d['horsMain']),
                    ' '.join(d['horsMain'][:3])))
    if d['sectionsMain'] < 2:
        out.append(('STRUCTURE', '%d section dans le <main>' % d['sectionsMain'], ''))
    if d['imgSansSrc']:
        out.append(('STRUCTURE', '%d image sans source' % d['imgSansSrc'], ''))
    if d['murHaut'] > 2500:
        out.append(('STRUCTURE', 'mur d’avis déplié : %d px' % d['murHaut'], ''))
    if d['pales']:
        out.append(('STRUCTURE', '%d bloc resté invisible' % d['pales'], ''))

    for x in page[vue]['contraste']:
        if x['sel'] in TOLERES:
            continue
        out.append(('UX/UI', 'contraste %.2f:1 (seuil %s)' % (x['ct'], x['seuil']),
                    '%s — « %s »' % (x['sel'], x['txt'])))
    if vue == 'mobile':
        for x in page[vue]['cibles']:
            # Un lien DANS une phrase est excepté par la règle : l'étirer à
            # 44 px déchirerait le paragraphe qui le porte. La sonde le
            # signale à part plutôt que de le compter comme un défaut.
            if x['sel'] in TOLERES or x.get('enLigne'):
                continue
            out.append(('UX/UI', 'cible %d×%d px (seuil 44)' % (x['w'], x['h']),
                        '%s — « %s »' % (x['sel'], x['txt'])))
    for x in page[vue]['petits']:
        out.append(('UX/UI', 'texte à %s px (plancher 14)' % x['px'],
                    '%s — « %s »' % (x['sel'], x['txt'])))

    if c['filFaux']:
        out.append(('COHÉRENCE', 'le fil d’Ariane nomme une autre page',
                    '« %s » sous « %s »' % (c['fil'], c['h1'])))
    for t in c['h2Doubles']:
        out.append(('COHÉRENCE', 'titre en double', t))
    if c['sautsTitres']:
        out.append(('COHÉRENCE', 'saut de niveau de titre', ' '.join(c['sautsTitres'])))
    morts = [x for x in c['liensMorts'] if x not in REECRITS]
    if morts:
        out.append(('COHÉRENCE', '%d lien sans destination' % len(morts),
                    ' '.join(morts[:4])))
    if c['imgSansAlt']:
        out.append(('COHÉRENCE', '%d image sans attribut alt' % c['imgSansAlt'], ''))
    return out


REECRITS = liens_reecrits()


def gabarits_deployes():
    """Les préfixes que le déploiement pose réellement sous « Refonte 2026 »."""
    chemin = os.path.join(RACINE, 'outils', 'deployer-refonte.py')
    if not os.path.exists(chemin):
        return []
    dep = SourceFileLoader('dep_refonte2', chemin).load_module()
    return dep.TYPES


DEPLOYES = gabarits_deployes()


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--site', required=True)
    p.add_argument('--gabarit', default='*',
                   help='préfixe de fichier, « * » pour tout le dossier, '
                        '« deploye » pour les seules pages de la refonte')
    p.add_argument('--sortie', help='où écrire le relevé brut (JSON)')
    p.add_argument('--detail', action='store_true', help='une ligne par écart, page par page')
    a = p.parse_args()

    site = os.path.abspath(a.site)
    # « * » lit le dossier entier, y compris les gabarits remplacés — les
    # fiches « voyage- » et les catégories « categorie- », que le
    # déploiement ne pose plus. Les compter fausse le bilan : une page que
    # personne ne verra n'a pas de défaut.
    if a.gabarit == 'deploye':
        a.gabarit = '*'
        deployes = True
    else:
        deployes = False
    sortie = a.sortie or os.path.join(RACINE, 'audit-%s.json'
                                      % (a.gabarit.strip('-*') or 'tout'))
    pages = sonder(site, a.gabarit, sortie)
    if deployes:
        garde = tuple(t[0] for t in DEPLOYES) + ('agence-',)
        pages = [x for x in pages if x['f'].startswith(garde)]
    if not pages:
        raise SystemExit('aucune page pour le préfixe « %s »' % a.gabarit)

    print('═══ %d page(s) · gabarit « %s »\n' % (len(pages), a.gabarit))

    # Un défaut présent sur toutes les pages est un défaut du GABARIT ; un
    # défaut sur une seule est un accident de cette page. Les deux se
    # corrigent, mais pas au même endroit.
    par_ecart = collections.defaultdict(set)
    for page in pages:
        for vue in ('bureau', 'mobile'):
            for famille, ecart, ou in defauts(page, vue):
                par_ecart[(famille, ecart, ou, vue)].add(page['f'])

    if not par_ecart:
        print('Aucun écart. %d page(s) mesurée(s) en bureau et au doigt.' % len(pages))
        return

    n = len(pages)
    for famille in ('STRUCTURE', 'COHÉRENCE', 'UX/UI'):
        lignes = [(e, ou, vue, f) for (fa, e, ou, vue), f in par_ecart.items() if fa == famille]
        if not lignes:
            continue
        print('── %s' % famille)
        for ecart, ou, vue, fichiers in sorted(lignes, key=lambda x: (-len(x[3]), x[0])):
            portee = ('le gabarit' if len(fichiers) == n
                      else '%d/%d pages' % (len(fichiers), n))
            print('   %-7s %-44s %-12s %s' % (vue, ecart[:44], portee, ou[:60]))
            if a.detail and len(fichiers) < n:
                for x in sorted(fichiers):
                    print('             · %s' % x)
        print()

    total = sum(len(f) for f in par_ecart.values())
    print('%d écart(s) distinct(s), %d occurrence(s) sur %d page(s).'
          % (len(par_ecart), total, n))
    print('Relevé brut : %s' % sortie)


if __name__ == '__main__':
    main()
