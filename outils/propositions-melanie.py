#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Demander les photos, et proposer les textes plutôt que de les attendre.

    WP_AUTH='compte:mot de passe' ./outils/propositions-melanie.py [--essai]

Deux familles de fils restaient ouvertes faute d'un contenu qui n'existe
pas encore. Pour les photos, il n'y a pas d'échappatoire : la médiathèque
n'en contient pas, et poser l'image d'un autre lieu serait pire que pas
d'image. Le commentaire dit donc exactement quoi envoyer et comment —
le plugin accepte une image collée, glissée ou choisie dans la bulle.

Pour les textes, en revanche, attendre était une paresse. La règle du
projet est de ne pas réécrire le client sans son accord : elle n'interdit
pas de PROPOSER. Chaque fil reçoit donc deux ou trois formulations
prêtes à coller, et il suffit de répondre « la 2 » pour que je la pose.

Les fils restent ouverts dans les deux cas : c'est elle qui tranche.
"""

import argparse
import json
import os
import subprocess
import sys
import time

API = 'https://authentiquegypte.com/wp-json/ae-commentaires/v1'

COMMENT_ENVOYER = (
    "\n\nPour l'envoyer : rouvrez cette bulle sur la page et glissez la photo "
    "dedans, ou collez-la directement (Ctrl+V) — le champ accepte les images."
)

PHOTOS = {
 '10438': "Il me faut vos photos pour le faire : la médiathèque n'a aucune image par "
          "étape. Envoyez-en une par journée, nommée « jour 1 », « jour 2 »… et je les "
          "pose sur les quatorze fiches d'un coup." + COMMENT_ENVOYER,
 '9504':  "Je n'ai qu'une seule image d'Alexandrie dans la médiathèque, et elle ne montre "
          "aucun des sites cités. Il m'en faut une par site : phare, catacombes, "
          "bibliothèque, colonne de Pompée." + COMMENT_ENVOYER,
 '9506':  "Aucune photo de la colonne de Pompée dans la médiathèque. Envoyez-la-moi et je "
          "la pose ici." + COMMENT_ENVOYER,
 '9526':  "Laquelle souhaitez-vous ? Si vous en avez une en tête qui n'est pas encore dans "
          "la médiathèque, envoyez-la ici." + COMMENT_ENVOYER,
 '9527':  "Dites-moi laquelle ne va pas et envoyez celle qui doit la remplacer : je n'ai pas "
          "d'autre image de ce lieu en médiathèque." + COMMENT_ENVOYER,
 '9543':  "Quelle photo doit la remplacer ? Envoyez-la ici et je la mets en place."
          + COMMENT_ENVOYER,
 '10428': "Je veux bien corriger, mais il me faut le détail : quelles photos, et sur quel "
          "écran ? Si vous pouvez joindre une capture, c'est le plus simple."
          + COMMENT_ENVOYER,
}

# Deux fils sur le fond sombre, posés avant l'allègement du voile.
VOILE = {
 '9496': "Le voile posé sur la photo est allégé — de 93 % à 80 %, en s'éclaircissant vers "
         "la droite. C'est fait sur les 57 pages. Si la photo elle-même ne vous convient "
         "pas, envoyez-en une autre ici et je la remplace.",
 '9538': "Le voile est allégé sur toutes les pages, la photo ressort beaucoup mieux. Si "
         "c'est le fond que vous voulez changer, envoyez-moi l'image ici.",
}

TEXTES = {
 '10471':
   "Voici trois formulations, dites-moi laquelle et je la pose :\n\n"
   "1. « L'Égypte que vous choisissez, pas celle d'un catalogue »\n"
   "2. « Un itinéraire écrit avec vous, jamais recopié »\n"
   "3. « Votre Égypte, construite avec vous »\n\n"
   "La 3 est la plus sobre ; la 1 garde l'opposition qui vous plaisait, sans le mot "
   "« vendue ».",
 '10478':
   "Le titre annonce cinq façons alors que vous demandez d'ajouter Le Caire et Croisière "
   "— il en faudra sept. Trois propositions :\n\n"
   "1. « Où aller en Égypte »\n"
   "2. « Les régions que nous faisons découvrir »\n"
   "3. « Sept façons de voyager en Égypte »\n\n"
   "La 1 et la 2 ne se démoderont pas si vous ajoutez une région plus tard.",
 '10482':
   "Trois propositions :\n\n"
   "1. « Ce que disent nos voyageurs »\n"
   "2. « Leurs mots, pas les nôtres »\n"
   "3. « 23 avis, tous publiés sur Google »\n\n"
   "La 3 dit d'où viennent les avis sans avoir à le répéter en dessous.",
 '9544':
   "Trois propositions pour « Les autres façons de partir » :\n\n"
   "1. « Partir autrement »\n"
   "2. « Et vous, comment partez-vous ? »\n"
   "3. « Famille, couple, solo, mobilité réduite »\n\n"
   "La 3 dit directement ce que contient le bloc.",
 '10457':
   "Voici une version du paragraphe, à valider ou à corriger :\n\n"
   "« En Égypte, chaque journée devient une histoire que les enfants raconteront "
   "longtemps. Voir un hiéroglyphe de tout près, monter à bord d'une felouque, écouter "
   "un guide parler d'Hatchepsout comme d'une héroïne — ce ne sont pas des visites, ce "
   "sont des souvenirs. Nous calons le rythme sur le leur : des matinées courtes, des "
   "pauses vraies, et des soirées où les questions fusent encore autour du dîner. »\n\n"
   "J'ai gardé vos images et raccourci les phrases ; dites-moi ce qui ne va pas.",
 '10447':
   "Voici le paragraphe repris de ce que vous décrivez, à valider :\n\n"
   "« Organiser un voyage en Égypte en situation de mobilité réduite demande du travail : "
   "les sites sont anciens, les aménagements inégaux, et tout n'est pas accessible. Nous "
   "le disons franchement, site par site. Notre rôle est de vous dire ce qui est possible "
   "et ce qui ne l'est pas, puis de construire autour : véhicule adapté, rythme allégé, "
   "hébergements vérifiés, et un accompagnement qui ne vous lâche pas. Nous proposons ces "
   "séjours parce qu'ils en valent la peine, pas parce qu'ils sont simples. »\n\n"
   "Corrigez ce qui ne correspond pas à votre façon de le dire.",
 '10463':
   "Je peux écrire l'encart avec vos mots. Proposition :\n\n"
   "« Ce que les couples préfèrent — un dîner dans un palace, des hébergements de charme "
   "choisis un par un, un vol en montgolfière au lever du jour, un repas à bord d'une "
   "felouque privatisée, et un moment rien qu'à vous sur la mer Rouge. »\n\n"
   "Dites-moi ce que vous voulez ajouter ou retirer et je le pose.",
 '9528':
   "Vous avez raison, ces textes sont identiques d'une catégorie à l'autre : ils viennent "
   "du gabarit, pas de vous. Je peux en écrire un par destination à partir du contenu de "
   "chaque page — par exemple pour Assouan : « Philae, Abou Simbel et les villages nubiens, "
   "au rythme du Nil. » Dites-moi si je continue sur ce ton et je fais les neuf.",
 '9529':
   "Même remarque : je propose d'écrire un texte par destination à partir de ce que dit "
   "déjà chaque page. Pour Le Caire : « Gizeh, Saqqara et le Grand Musée égyptien, en une "
   "journée ou en trois. » Validez le ton et je fais les neuf.",
 '9530':
   "Même chose ici. Je m'appuie sur le contenu de chaque page pour que les textes diffèrent "
   "vraiment, plutôt que de changer trois mots.",
 '9531':
   "« Découvrir » est mon libellé de gabarit, pas votre texte : je peux le remplacer par le "
   "nom de la destination — « Voir Assouan », « Voir Le Caire » — comme je l'ai fait pour "
   "« Lire le guide » sur le blog, qui se répétait vingt-deux fois. Je le fais ?",
}


def appel(methode, chemin, charge=None):
    auth = os.environ.get('WP_AUTH', '')
    if ':' not in auth:
        sys.exit('WP_AUTH manquant.')
    cmd = ['curl', '-s', '--max-time', '90', '-u', auth, '-X', methode, API + chemin]
    if charge is not None:
        f = '/tmp/.ae-prop.json'
        json.dump(charge, open(f, 'w'), ensure_ascii=False)
        cmd += ['-H', 'Content-Type: application/json', '--data-binary', '@' + f]
    for essai in range(4):
        brut = subprocess.run(cmd, capture_output=True, text=True).stdout
        try:
            return json.loads(brut)
        except json.JSONDecodeError:
            time.sleep(2 ** essai)
    return None


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--essai', action='store_true')
    a = p.parse_args()

    tout = appel('GET', '/tout') or []
    par_id = {str(x['id']): x for x in tout}
    n = 0
    for nom, lot in (('photo', PHOTOS), ('voile', VOILE), ('texte', TEXTES)):
        for fil, texte in sorted(lot.items()):
            x = par_id.get(fil)
            if not x:
                print('   #%s introuvable' % fil)
                continue
            if any(texte[:45] in (r.get('message') or '') for r in (x.get('reponses') or [])):
                continue
            print('   #%-7s %-6s %s' % (fil, nom, texte.splitlines()[0][:66]))
            if a.essai:
                continue
            if appel('POST', '/fils/%s/reponses' % fil, {'message': texte}) is None:
                print('      ✗ refusé')
                continue
            n += 1
    print('\n%d commentaire(s) posté(s). Les fils restent ouverts : c\'est elle qui tranche.' % n)


if __name__ == '__main__':
    main()
