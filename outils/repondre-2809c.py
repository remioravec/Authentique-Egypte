#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Les fils que j'avais renvoyés à la cliente à tort.

    WP_AUTH='compte:mot de passe' ./outils/repondre-2809c.py [--essai]

Rémi : « si un commentaire est facilement modifiable de notre côté, sois
proactif. On essaie de donner le moins de travail à la cliente. »

En reprenant les quatre-vingt-douze fils ouverts avec ce regard, une
bonne partie de ce que j'avais renvoyé vers elle était à ma portée. Pire :
trois de mes réponses étaient factuellement fausses.

CE QUE J'AI AFFIRMÉ À TORT

« Je n'ai aucune image de l'oasis de Dakhla » — la médiathèque en
contient six. « Aucune image du Désert Noir » — elle en contient deux.
« Il me faut le logo en PNG à fond transparent » — deux logos
transparents y sont déjà, et c'est celui-là qui est en ligne.

Je n'avais pas cherché. Ces trois réponses sont corrigées et le travail
est fait.

LE LIEN GOOGLE QUE JE RÉCLAMAIS

Il était dans le site depuis le début, sur quatorze pages, sous le
bouton « Voir les avis sur Google ». Vingt-et-une pages portaient un mur
d'avis sans ce bouton : il y est.
"""

import argparse
import json
import os
import subprocess
import sys
import time

API = 'https://authentiquegypte.com/wp-json/ae-commentaires/v1'

VOIR = ("\n\nToutes mes excuses : je vous avais demandé quelque chose que j'avais "
        "déjà sous la main. Je n'avais pas cherché avant de vous écrire.")

# (fil, message, on referme ?)
REPONSES = [
    # --- les liens d'avis : faits, plus rien à fournir ---
    (10743, "Fait, et je n'avais pas besoin de vous le demander : le lien vers votre "
            "fiche Google était déjà dans le site, sur quatorze pages. Les "
            "vingt-et-une pages qui ne l'avaient pas l'ont maintenant." + VOIR, True),
    (10749, "Fait pour les deux. Le lien Google était déjà dans le site — je vous "
            "l'avais demandé pour rien. Pour TripAdvisor, j'ai trouvé votre fiche "
            "(« AUTHENTIQUE ÉGYPTE », Le Caire) et posé le lien sur les trente-cinq "
            "pages qui portent un mur d'avis.\n\n"
            "Une seule chose à vérifier, d'un coup d'œil : TripAdvisor refuse les "
            "requêtes automatiques, je n'ai donc pas pu ouvrir la page moi-même pour "
            "confirmer que c'est bien la vôtre. Cliquez le bouton une fois et "
            "dites-moi si ça tombe juste.", False),
    (10759, "Fait : le lien TripAdvisor est posé ici et sur toutes les pages qui ont "
            "un mur d'avis. Voir #10749 pour la petite vérification.", True),
    (10764, "Fait : les deux liens sont posés.", True),
    (10781, "Fait : les deux liens sont posés.", True),
    (10795, "Fait : les deux liens sont posés.", True),
    (10826, "Fait : les deux liens sont posés.", True),
    (10848, "Fait : les deux liens sont posés.", True),

    # --- les photos du guide : sept sur huit trouvées ---
    (10808, "Fait, et je vous dois une correction : je vous avais écrit « je n'ai "
            "aucune image de l'oasis de Dakhla ». C'était faux, la médiathèque en "
            "contient six. J'ai posé « DAKHLA-OASIS-DAY-3 ». Si vous en préférez une "
            "autre, dites-le." + VOIR, True),
    (10810, "Fait : « Voyage au désert blanc en Égypte », prise dans votre "
            "médiathèque.", True),
    (10811, "Fait, avec la même correction qu'en #10808 : je vous avais dit qu'il n'y "
            "avait aucune image du Désert Noir, il y en a deux. J'ai posé « Voyage "
            "dans le Désert noir en Égypte »." + VOIR, True),
    (10812, "Fait : « FAYOUM-J2 », prise dans votre médiathèque.", True),
    (10813, "Fait : « SIWA-J2 », prise dans votre médiathèque.", True),
    (10814, "Fait : « lake nasser », prise dans votre médiathèque.", True),
    (10815, "Fait : « Voyage au Mont Sinaï », prise dans votre médiathèque.", True),
    (10809, "Celui-ci reste : Bahariya est le seul des huit lieux dont la médiathèque "
            "n'a aucune image, et je ne mettrai pas la photo d'une autre oasis à sa "
            "place. Les sept autres sont posées.\n\n"
            "Pour l'envoyer : rouvrez cette bulle sur la page et glissez la photo "
            "dedans, ou collez-la directement (Ctrl+V).", False),

    # --- le logo : ma réponse était fausse, et le vrai défaut est ailleurs ---
    (10817, "Je me suis trompé, et le vrai problème n'est pas celui que vous pensez.\n\n"
            "Le logo en ligne EST à fond transparent — mesuré, 94 % de ses pixels le "
            "sont. Je vous ai demandé un PNG transparent alors que vous en avez déjà "
            "deux en médiathèque.\n\n"
            "Ce qui ne va pas est plus ennuyeux : le logo du site est entièrement "
            "doré. Le bateau sombre et l'eau bleu clair de votre charte ont disparu — "
            "l'outil de détourage les a emportés avec le fond. Il ne reste que le "
            "lettrage, ce qui explique qu'il paraisse délavé sur l'en-tête blanc "
            "(contraste mesuré à 2,1).\n\n"
            "Pouvez-vous m'envoyer le fichier d'origine du logo, celui de la charte, "
            "avec le bateau et l'eau ? Je le remets partout d'un coup.", False),
    (10837, "Voir #10817 : le logo est bien transparent, mais il a perdu le bateau et "
            "l'eau de votre charte. Il me faut le fichier d'origine.", False),
]


def appel(methode, chemin, charge=None):
    auth = os.environ.get('WP_AUTH', '')
    if ':' not in auth:
        sys.exit('WP_AUTH manquant.')
    cmd = ['curl', '-s', '--max-time', '90', '-u', auth, '-X', methode, API + chemin]
    if charge is not None:
        f = '/tmp/.ae-fil2809c.json'
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
        print('   #%-6d %s%s' % (fil, message.replace('\n', ' ')[:62],
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
    o = [x for x in etat.values() if x.get('statut') != 'resolu']
    print('\n%d réponse(s) postée(s). Fils ouverts : %d' % (envoyes, len(o)))
    if manque:
        print('✗ à reprendre : %s' % ', '.join(manque))


if __name__ == '__main__':
    main()
