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


# Les fils qui ne peuvent pas être clos : il manque une photo, ou la
# demande est trop ouverte pour qu'on agisse sans se tromper. Ils
# reçoivent une réponse mais RESTENT OUVERTS — un fil clos est un fil
# qu'on ne relit plus, et ceux-là attendent une réponse de l'agence.
#
# Chaque question propose une piste concrète quand la médiathèque en
# contient une : « dites-nous » sans rien proposer renvoie la charge
# entière à la cliente.
A_PRECISER = {
    # ——— les photos
    '9504': 'Il me faut vos photos : la médiathèque ne contient qu’une seule image '
            'd’Alexandrie (« Voyage sur mesure à Alexandrie en Egypte »), rien sur la '
            'colonne de Pompée, les catacombes, la bibliothèque ou le fort Qaitbay. '
            'Envoyez-les et je les place sous chaque site. À défaut, je peux mettre '
            'l’unique photo existante en tête de section et laisser les sites sans '
            'visuel — dites-moi ce que vous préférez.',
    '9506': 'Je n’ai aucune photo de la colonne de Pompée dans la médiathèque. '
            'Pouvez-vous m’en envoyer une ? En attendant je ne mets rien plutôt qu’une '
            'image qui ne serait pas le bon monument.',
    '9526': 'Laquelle souhaitez-vous ? Je peux proposer « Voyage sur mesure à Assouan '
            'en Egypte » (déjà dans votre médiathèque) ou « Egypte Nubie Voyage ». '
            'Dites-moi, ou envoyez la vôtre.',
    '9527': 'Pouvez-vous me dire laquelle ne va pas, et par quoi la remplacer ? Je vois '
            'dans la médiathèque « Voyage sur mesure à Assouan en Egypte » et « Egypte '
            'Nubie Voyage » qui pourraient convenir.',
    '9543': 'Je propose « Voyage authentique en famille », déjà dans votre médiathèque, '
            'ou « Photo d’une famille dans le désert Egyptiens ». Laquelle vous '
            'conviendrait, ou en avez-vous une autre ?',
    '9538': 'Je peux éclaircir le voile sombre posé sur la photo, ou changer la photo. '
            'Je propose « Couple dans un marché en Egypte », déjà dans votre '
            'médiathèque. Que préférez-vous ?',
    '9496': 'Je vais éclaircir le voile. Vous avez joint une image à un autre '
            'commentaire de cette page : je la pose en visuel de une, et j’allège le '
            'voile pour que le titre reste lisible.',

    # ——— les demandes qu'il faut préciser
    '9528': 'Vous avez raison, ces textes sont identiques d’une catégorie à l’autre : '
            'ils viennent tels quels du site actuel. Les différencier demande de les '
            'réécrire, et c’est à vous de dire ce que chaque catégorie doit raconter. '
            'Voulez-vous nous envoyer un paragraphe par catégorie ?',
    '9529': 'Même remarque que plus haut : il nous faut un texte propre à chaque '
            'catégorie pour remplacer celui qui se répète.',
    '9530': 'Même remarque : un texte par catégorie, et nous les mettons en place.',
    '9531': 'Par quoi remplacer « Découvrir » ? Nous pouvons écrire ce que la page vise '
            '— « Voir le séjour », « Voir la destination » — ce qui supprimerait la '
            'répétition. Cela vous convient-il ?',
    '9548': 'Quelles informations manquent exactement sur cette carte ? La durée, le '
            'nombre d’étapes, ce qui est inclus ? Dites-nous lesquelles et nous les '
            'ajoutons à toutes les cartes de séjour.',
    '9544': 'Qu’est-ce qui ne va pas dans cette section : le titre, les pages listées, '
            'ou la façon dont elles sont présentées ?',
    '9499': 'Nous n’avons pas compris cette remarque. S’agit-il du titre « Passer du '
            'guide au voyage », de ce qu’il annonce, ou de sa place dans la page ?',
    '9568': 'Sur quelle page faut-il déplacer « Quand partir » ? Nous pensons au guide '
            '« Quand partir en Égypte ? », qui traite déjà le sujet en détail — '
            'confirmez-vous ?',
    '9571': 'Qu’est-ce qui ne va pas dans le jour par jour : la longueur des journées, '
            'le fait qu’elles soient repliées, l’absence de photos, autre chose ? Avec '
            'une précision nous le reprenons.',
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
        # Relancé après un incident, l'outil ne redouble pas ce qui est
        # déjà posté : Mélanie lirait deux fois la même réponse.
        if par_id[fil].get('reponses'):
            continue
        # Le serveur rend parfois une redirection au lieu du JSON. Sans
        # reprise, un fil restait sans réponse au milieu du lot — et c'est
        # précisément le fil dont Mélanie n'aurait jamais su qu'il est
        # traité.
        for essai in range(4):
            r = appel('POST', '/fils/%s/reponses' % fil, {'message': message})
            if '_brut' not in r and not r.get('code'):
                break
            time.sleep(2 ** essai)
        else:
            print('   ✗ fil %s : %s' % (fil, str(r)[:80]))
            rate += 1
            continue
        appel('PATCH', '/fils/%s' % fil, {'statut': 'resolu'})
        time.sleep(0.2)
        ok += 1
    if a.essai:
        for fil, message in A_PRECISER.items():
            print('   %s (reste ouvert) → %s' % (fil, message[:64]))
        print('\nessai : %d clôture(s) + %d question(s).' % (len(REPONSES), len(A_PRECISER)))
        return

    # Relecture : le statut est-il vraiment passé, la réponse vraiment posée ?
    # Les fils à préciser : une réponse, mais pas de clôture.
    for fil, message in A_PRECISER.items():
        if fil not in par_id:
            print('   ✗ fil %s introuvable' % fil)
            rate += 1
            continue
        if par_id[fil].get('reponses'):
            continue
        for essai in range(4):
            r = appel('POST', '/fils/%s/reponses' % fil, {'message': message})
            if '_brut' not in r and not r.get('code'):
                break
            time.sleep(2 ** essai)
        else:
            print('   ✗ fil %s : %s' % (fil, str(r)[:80]))
            rate += 1
            continue
        ok += 1
        time.sleep(0.2)

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
