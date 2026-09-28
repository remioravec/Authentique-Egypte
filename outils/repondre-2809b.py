#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Les trente fils qui restaient sans un mot.

    WP_AUTH='compte:mot de passe' ./outils/repondre-2809b.py [--essai]

Quatre étaient actionnables et sont faits. Vingt-trois attendent une
photo — pour chacun je dis exactement laquelle, et comment l'envoyer.
Les trois derniers sont des refontes de bloc à maquetter.

Un fil sans réponse est un fil dont elle ne sait pas s'il a été lu.
"""

import argparse
import json
import os
import subprocess
import sys
import time

API = 'https://authentiquegypte.com/wp-json/ae-commentaires/v1'

ENVOI = ("\n\nPour l'envoyer : rouvrez cette bulle sur la page et glissez la photo "
         "dedans, ou collez-la directement (Ctrl+V).")

# (fil, message, on referme ?)
REPONSES = [
    # --- les quatre faits ---
    (10856, "Fait. Ce n'était pas une photo mais un crédit resté en légende : "
            "« Photo de Tom », sous le titre « Plongée en Mer Rouge ». Retiré — "
            "c'était le seul du site.\n\n"
            "Pour la photo à ajouter, envoyez-la-moi ici." + ENVOI, False),
    (10783, "Retirée de la page Louxor.\n\n"
            "Pour information : le déroulé de cette croisière passe bien par Louxor, "
            "c'est pour cela qu'elle apparaissait — la liste n'avait pas tort "
            "techniquement. Mais c'est vous qui vendez, et je comprends qu'on ne "
            "propose pas une croisière sur le lac Nasser à quelqu'un qui cherche "
            "Louxor.", True),
    (10793, "Retiré.", True),
    (10847, "Fait : un bloc « Nos guides pour voyager en famille » est posé sous "
            "« Les autres façons de partir », avec vos trois guides existants — "
            "« Que faire en Égypte avec des enfants », « Peut-on voyager en Égypte "
            "en famille ? » et « Sécurité en Égypte pour un voyage en famille ».\n\n"
            "Vous avez un quatrième guide, « Le voyage en Égypte en famille : tout "
            "savoir ! », que je n'ai pas mis : son lien source pointe vers la page "
            "des formalités, pas vers lui. Donnez-moi sa bonne adresse et je "
            "l'ajoute.", False),

    # --- les photos du guide « hors des sentiers battus » ---
    (10808, "Il me faut vos photos : je n'ai aucune image de l'oasis de Dakhla dans "
            "la médiathèque, et je ne poserai pas la photo d'un autre lieu." + ENVOI, False),
    (10809, "Même chose pour Bahariya : aucune image en médiathèque." + ENVOI, False),
    (10810, "Pour le Désert Blanc j'ai des images en médiathèque, mais je préfère que "
            "vous choisissiez celle qui va ici plutôt que de décider seul. Dites-moi "
            "laquelle, ou envoyez la vôtre." + ENVOI, False),
    (10811, "Aucune image du Désert Noir en médiathèque." + ENVOI, False),
    (10812, "J'ai des images du Fayoum en médiathèque. Laquelle voulez-vous ici ?" + ENVOI, False),
    (10813, "J'ai une image de Siwa en médiathèque. Je la pose, ou vous préférez "
            "envoyer la vôtre ?" + ENVOI, False),
    (10814, "J'ai des images du lac Nasser en médiathèque. Laquelle ici ?" + ENVOI, False),
    (10815, "Aucune image du Sud Sinaï hors de celles du mont Moïse. Envoyez-moi "
            "celle que vous voulez." + ENVOI, False),
    (10816, "C'est la photo de une du guide : il m'en faut une qui vaille pour les "
            "huit lieux, ou dites-moi laquelle des huit mettre en avant." + ENVOI, False),

    # --- les autres photos ---
    (10744, "Il me faut la photo de la famille de séjours « Voyage culturel en "
            "Égypte ». Pour la structure de la carte, dites-moi ce qui ne va pas — "
            "l'ordre des informations, la place de la photo, la taille ?" + ENVOI, False),
    (10746, "La photo n'est pas arrivée avec le commentaire. Renvoyez-la ici et je la "
            "pose." + ENVOI, False),
    (10751, "Quelle image voulez-vous à la place ? Envoyez-la ici." + ENVOI, False),
    (10846, "Quelle photo doit remplacer celle-ci ? Envoyez-la et je la mets." + ENVOI, False),
    (10853, "Noté : une pyramide en photo de une pour la page Le Caire. J'ai plusieurs "
            "images de Gizeh en médiathèque — je peux poser « Pyramides de Gizeh au "
            "lever du jour », ou vous m'envoyez la vôtre." + ENVOI, False),
    (10854, "Il me faut une photo de fond pour cette page. Envoyez-la ici." + ENVOI, False),
    (10855, "Il me faut une photo d'atelier — poterie ou hiéroglyphes. Je n'en ai "
            "aucune en médiathèque." + ENVOI, False),

    # --- les « enlever l'image » sans repère ---
    (10753, "Je ne sais pas laquelle vous visez : le commentaire n'a pas accroché "
            "d'élément, et cette page porte une douzaine d'images. Reposez la bulle "
            "en cliquant directement sur l'image à retirer, ou envoyez-moi une "
            "capture.", False),
    (10754, "Même chose que #10753 : il me faut savoir quelle image.", False),
    (10755, "Le commentaire a accroché du code au lieu de l'élément — l'image de "
            "Louxor. Confirmez-moi que c'est bien celle-là, avec son texte, et je "
            "retire les deux.", False),
    (10756, "Même chose que #10753 : il me faut savoir quelle image.", False),
    (10852, "Même chose que #10753 : il me faut savoir quelle photo.", False),

    # --- les refontes à maquetter ---
    (10748, "Je retire volontiers ce bloc, mais ce que vous voulez à la place — une "
            "explication par type de bateau, avec image et durée — est du contenu que "
            "je n'ai pas : felouque, dahabieh, croisière 5*, il me faut pour chacun "
            "une description, une durée et une photo. Envoyez-les-moi et je construis "
            "le bloc. En attendant je laisse l'existant plutôt qu'un trou.", False),
    (10788, "Quel est le problème avec ce bloc : la mise en forme des lignes, la "
            "couleur, le fait que ce soit une liste ? Je vous prépare deux "
            "propositions dès que je sais ce qui vous gêne — je préfère ne pas "
            "refaire au hasard un encart que vous venez de dicter.", False),
    (10844, "Même question que #10788 : dites-moi ce qui ne va pas dans la "
            "présentation et je vous fais deux propositions.", False),
    (10845, "Même question. Ces deux blocs — « ce que les familles adorent » et « nos "
            "activités coup de cœur » — partagent la même mise en forme : si je la "
            "change, je la change pour les deux, et pour l'équivalent couple.", False),

    # --- le reste ---
    (10774, "J'ai bien la nouvelle question — « combien de jours rester au Caire ? » — "
            "mais il me faut votre réponse. Je ne l'invente pas : c'est vous qui "
            "savez ce que vous recommandez.", False),
]


def appel(methode, chemin, charge=None):
    auth = os.environ.get('WP_AUTH', '')
    if ':' not in auth:
        sys.exit('WP_AUTH manquant.')
    cmd = ['curl', '-s', '--max-time', '90', '-u', auth, '-X', methode, API + chemin]
    if charge is not None:
        f = '/tmp/.ae-fil2809b.json'
        json.dump(charge, open(f, 'w'), ensure_ascii=False)
        cmd += ['-H', 'Content-Type: application/json', '--data-binary', '@' + f]
    for essai in range(4):
        brut = subprocess.run(cmd, capture_output=True, text=True).stdout
        try:
            rep = json.loads(brut)
        except json.JSONDecodeError:
            time.sleep(2 ** essai)
            continue
        if isinstance(rep, dict) and rep.get('code') and rep.get('data', {}).get('status'):
            return None
        return rep
    return None


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--essai', action='store_true')
    a = p.parse_args()

    tout = appel('GET', '/tout')
    if tout is None:
        sys.exit('Le plugin ne répond pas.')
    par_id = {x['id']: x for x in tout}

    envoyes = 0
    for fil, message, refermer in REPONSES:
        x = par_id.get(fil)
        if not x:
            print('   #%-6d introuvable' % fil)
            continue
        deja = any(message[:40] in (r.get('message') or '')
                   for r in (x.get('reponses') or []))
        if deja and (not refermer or x.get('statut') == 'resolu'):
            continue
        print('   #%-6d %s%s' % (fil, message.replace('\n', ' ')[:64],
                                 '  [clos]' if refermer else '  [ouvert]'))
        if a.essai:
            continue
        if not deja:
            if appel('POST', '/fils/%d/reponses' % fil, {'message': message}) is None:
                print('      ✗ réponse refusée')
                continue
            envoyes += 1
        if refermer:
            appel('PATCH', '/fils/%d' % fil, {'statut': 'resolu'})

    if a.essai:
        print('\n%d fil(s) visés.' % len(REPONSES))
        return

    etat = {x['id']: x for x in (appel('GET', '/tout') or [])}
    manque = []
    for fil, message, refermer in REPONSES:
        x = etat.get(fil)
        if not x:
            manque.append('#%d disparu' % fil)
        elif not any(message[:40] in (r.get('message') or '')
                     for r in (x.get('reponses') or [])):
            manque.append('#%d sans réponse' % fil)
        elif refermer and x.get('statut') != 'resolu':
            manque.append('#%d resté ouvert' % fil)
    muets = [x for x in etat.values()
             if x.get('statut') != 'resolu' and not x.get('reponses')]
    print('\n%d réponse(s) postée(s). Fils encore sans aucune réponse : %d'
          % (envoyes, len(muets)))
    if manque:
        print('✗ à reprendre : %s' % ', '.join(manque))


if __name__ == '__main__':
    main()
