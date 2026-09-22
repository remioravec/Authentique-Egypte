#!/usr/bin/env python3
"""
Répond dans le plugin de relecture, fil par fil, et clôt ce qui est fait.

    WP_AUTH='compte:mot de passe' ./outils/relecture-repondre.py [--essai]

Mélanie relit dans le plugin, pas dans un compte rendu. Une correction
faite mais non dite la laisse relancer la même remarque au tour suivant —
c'est arrivé, soixante fils sur cent trente-quatre étaient déjà résolus
sans que personne ne le sache de son côté.

Chaque réponse dit ce qui a été fait, où, et de quoi c'est mesuré. Un fil
n'est marqué « résolu » que si la correction est VÉRIFIÉE en ligne : le
tableau ci-dessous ne contient que ce qui a été relu sur la page après
écriture. Les fils qui attendent une photo, un fichier ou une décision
restent ouverts et ne reçoivent rien ici — c'est à Rémi de les porter.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from importlib.machinery import SourceFileLoader

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = 'https://authentiquegypte.com/wp-json/ae-commentaires/v1'

# fil → ce qu'on a fait, dit à Mélanie.
REPONSES = {
    # ——— la FAQ
    '9554': 'C’est fait. Les deux FAQ de cette page sont fondues en une seule, '
            'au même endroit et dans la même forme que sur toutes les autres pages : '
            'des questions repliées qu’on ouvre une à une.',
    '9564': 'C’est fait. Une seule FAQ désormais, les questions des deux blocs '
            'réunies sans doublon.',
    '9532': 'C’est fait. Cette page portait deux FAQ et trente et une questions '
            'dispersées ; il n’en reste qu’une, les questions propres à Assouan '
            'd’abord, puis celles qui valent pour tous les voyages.',
    '9535': 'C’est fait, et sur l’ensemble du site : les quarante pages qui portent '
            'une FAQ ont maintenant la même — même titre, même forme, mêmes '
            'questions communes à la fin.',
    '9540': 'C’est fait. La FAQ a la même forme partout : une question par ligne, '
            'repliée, qu’on ouvre d’un clic.',
    '9558': 'C’est fait, les emoji sont retirés des réponses de la FAQ.',
    '9559': 'C’est fait, les emoji sont retirés des réponses de la FAQ.',

    # ——— les retraits
    '9534': 'Retiré, ici et sur les dix-sept autres pages qui le portaient. '
            'C’était une note de travail, elle n’avait rien à faire sur la page.',
    '9557': 'Retiré. Le bandeau ne figure plus sur aucune des pages qui listent '
            'des séjours : un prix et une durée n’ont de sens que sur la fiche '
            'd’un séjour précis.',
    '9561': 'Retiré, sur les six pages de ce type.',
    '9562': 'Retiré, sur les six pages de ce type.',
    '9515': 'Retiré. Le prix ne figure plus sur aucune page de destination, pour '
            'la raison que vous donnez : une destination n’a pas de prix. Il reste '
            'sur les fiches de séjour, où il est attendu.',

    # ——— le mur d'avis
    '9555': 'C’est fait. Les avis ne défilent plus : ils sont posés en grille, '
            'tous visibles, et le texte ne bouge plus. Aucun avis n’a été modifié.',
    '9549': 'C’est fait, les avis sont figés en grille sur les trente-cinq pages '
            'qui les portent.',
    '9565': 'C’est fait, les avis ne défilent plus.',
    '9536': 'C’est fait. Le texte ne bouge plus : les avis sont en grille, tous '
            'affichés en même temps.',
    '9541': 'C’est fait, les avis sont figés en grille.',
    '9545': 'C’est fait, les avis sont figés en grille.',
    '9510': 'C’est fait. Les avis ne défilent plus et sont posés en grille sur '
            'fond blanc, avec un texte fixe qu’on peut lire et relire.',

    # ——— Assouan, corrections de contenu
    '9514': 'Corrigé : la page annonce maintenant « 1 à 3 jours ».',
    '9517': 'Fait — mis en gras plutôt que souligné : sur le web, un texte souligné '
            'se lit comme un lien. Dites-moi si vous préférez le souligné.',
    '9518': 'Corrigé : « Croisière sur le Nil (3 nuits minimum) ».',
    '9519': 'Ajouté, juste après la croisière : « Route (4 heures, avec la '
            'possibilité de visiter les temples de Kom Ombo et d’Edfou) ».',
    '9520': 'Retiré.',
    '9521': 'Ajouté : « Le mieux reste de dormir sur place : cela coupe la route, '
            'permet d’assister au spectacle son et lumière des temples d’Abou '
            'Simbel, et de découvrir les temples sans trop de monde. »',
    '9522': 'Ajouté : le temple a été déplacé « par l’UNESCO » dans les années 70. '
            'Pour les photos de Philae, il me faut celles que vous voulez voir.',
    '9523': 'Ajouté : « Les croisières se font en dahabeya, en bateau à moteur ou '
            'en felouque. »',
    '9524': 'Retiré.',
    '9525': 'Ajouté : « Le monastère Saint-Siméon, rejoint à dos de dromadaire à '
            'travers le désert, reste peu fréquenté ; un tour en felouque complète '
            'bien la journée. »',

    # ——— Alexandrie
    '9505': 'Corrigé : « selon le trafic. Cela permet… ».',
    '9508': 'Retiré, la section entière.',
}


def appel(methode, chemin, charge=None):
    dep = appel.dep
    cmd = ['curl', '-s', '--max-time', '90', '-u', dep.auth(), '-X', methode, BASE + chemin]
    if charge is not None:
        f = '/tmp/.ae-relecture.json'
        with open(f, 'w', encoding='utf-8') as fh:
            json.dump(charge, fh, ensure_ascii=False)
        cmd += ['-H', 'Content-Type: application/json', '--data-binary', '@' + f]
    brut = subprocess.run(cmd, capture_output=True, text=True).stdout
    try:
        return json.loads(brut)
    except json.JSONDecodeError:
        return {'_brut': brut[:200]}


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--essai', action='store_true')
    a = p.parse_args()
    appel.dep = SourceFileLoader('dep', os.path.join(RACINE, 'outils', 'deployer.py')).load_module()

    tout = appel('GET', '/tout')
    par_id = {str(x['id']): x for x in tout}
    ok = rate = 0
    for fil, message in REPONSES.items():
        if fil not in par_id:
            print('   ✗ fil %s introuvable' % fil)
            rate += 1
            continue
        if a.essai:
            print('   %s → %s' % (fil, message[:76]))
            continue
        r = appel('POST', '/fils/%s/reponses' % fil, {'message': message})
        if '_brut' in r or r.get('code'):
            print('   ✗ fil %s : %s' % (fil, str(r)[:80]))
            rate += 1
            continue
        appel('PATCH', '/fils/%s' % fil, {'statut': 'resolu'})
        time.sleep(0.2)
        ok += 1
    if a.essai:
        print('\nessai : %d réponse(s) prête(s).' % len(REPONSES))
        return

    # Relecture : le statut est-il vraiment passé, la réponse vraiment posée ?
    tout = appel('GET', '/tout')
    par_id = {str(x['id']): x for x in tout}
    clos = sum(1 for f in REPONSES if par_id.get(f, {}).get('statut') == 'resolu')
    repondus = sum(1 for f in REPONSES if par_id.get(f, {}).get('reponses'))
    print('\n%d réponse(s) postée(s), %d échec(s).' % (ok, rate))
    print('relecture : %d/%d fils portent une réponse, %d/%d sont marqués résolus.'
          % (repondus, len(REPONSES), clos, len(REPONSES)))
    ouverts = [x for x in tout if x['statut'] == 'ouvert']
    print('il reste %d fil(s) ouvert(s) sur %d.' % (len(ouverts), len(tout)))


if __name__ == '__main__':
    main()
