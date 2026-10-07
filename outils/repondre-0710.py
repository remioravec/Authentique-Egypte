#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Les réponses aux vingt-cinq fils de Mélanie du 6 octobre.

    WP_AUTH='compte:mot de passe' ./outils/repondre-0710.py [--essai]

Vingt-quatre sont faits et se referment. Un reste ouvert : #12674, les
photos des avis — elles appartiennent aux voyageurs qui les ont postées
sur Google, je ne peux pas les reprendre sans elles.

Même mécanique que repondre-31.py : répondre rouvre un fil, on répond
d'abord, on classe ensuite, et rien n'est compté sans relecture.
"""

import argparse
import json
import os
import subprocess
import sys
import time

API = 'https://authentiquegypte.com/wp-json/ae-commentaires/v1'


def appel(methode, chemin, charge=None):
    """Un appel au plugin. Rend None sur refus, jamais un faux succès."""
    auth = os.environ.get('WP_AUTH', '')
    if ':' not in auth:
        sys.exit('WP_AUTH manquant.')
    cmd = ['curl', '-s', '--max-time', '90', '-u', auth, '-X', methode, API + chemin]
    if charge is not None:
        f = '/tmp/.ae-fil0710.json'
        json.dump(charge, open(f, 'w'), ensure_ascii=False)
        cmd += ['-H', 'Content-Type: application/json', '--data-binary', '@' + f]
    for essai in range(4):
        brut = subprocess.run(cmd, capture_output=True, text=True).stdout
        try:
            rep = json.loads(brut)
        except json.JSONDecodeError:
            time.sleep(2 ** essai)
            continue
        # Un corps d'erreur est du JSON valide : il faut le reconnaître.
        if isinstance(rep, dict) and rep.get('code') and rep.get('data', {}).get('status'):
            return None
        return rep
    return None

# (fil, message, on referme ?)
FAQ = ("Aucune question n'avait disparu, mais le bouton « Voir les N autres "
       "questions » avait sauté lors de ma dernière reprise de la FAQ : tout ce "
       "qui dépassait les cinq premières restait caché, sans moyen de l'ouvrir. "
       "Le bouton est revenu sur les trente-quatre pages concernées, et les "
       "questions sont de nouveau classées par rubrique (Découvrir, Avant de "
       "partir, Sur place, Pour qui, Formalités et santé, Organiser et réserver).")
DATE = ("La mention « Relevé sur la fiche le… » est retirée des trente-quatre "
        "pages qui la portaient.")
BOUTONS = ("Les boutons « Voir les avis sur Google » et « sur TripAdvisor » sont "
           "centrés sous les avis et passent en bleu plein, sur toutes les pages.")
VOILE = ("Le voile sombre posé sur la photo du haut est nettement allégé, sur "
         "ordinateur comme sur téléphone, et sur toutes les pages ; une légère "
         "ombre sous le texte le garde lisible sur les photos claires.")
REPONSES = [
    (12656, "Retirée : la phrase reste vide tant qu'aucun critère n'est coché.", True),
    (12657, "Le titre « Composez votre Égypte » est centré et le bloc a plus d'air "
            "au-dessus et en dessous.", True),
    (12658, "Les titres de l'accueil étaient noirs ; ils prennent le bleu des titres "
            "des autres pages, avec le petit surtitre « Nos itinéraires » au-dessus.", True),
    (12659, "« À partir de 1 895 € », le prix de la page du séjour.", True),
    (12660, "Chaque carte a maintenant son propre bouton : « Découvrir la dahabeya », "
            "« Partir vers Siwa », « Voir la nuit au monastère »… douze libellés "
            "différents au lieu de douze « Le jour par jour ».", True),
    (12661, "Carte d'Égypte ajoutée à la place du texte : les neuf destinations du "
            "site y sont épinglées, et chaque épingle mène à sa page.", True),
    (12662, "Retiré.", True),
    (12663, "« Comment ça se passe » remonte juste sous les itinéraires.", True),
    (12664, "Retiré.", True),
    (12665, "Retiré.", True),
    (12666, DATE, True),
    (12667, BOUTONS, True),
    (12668, FAQ, True),
    (12669, "Retiré de l'accueil, et l'outil qui pose ce bloc sur les pages ne l'y "
            "remettra plus.", True),
    (12670, VOILE, True),
    (12671, FAQ, True),
    (12672, DATE, True),
    (12673, BOUTONS, True),
    (12674, "Les avis du site sont recopiés de la fiche Google, texte seulement. Les "
            "photos jointes à un avis Google appartiennent au voyageur qui les a "
            "postées, et Google ne les fournit pas pour un affichage ailleurs : je "
            "ne peux pas les reprendre proprement.\n\n"
            "Ce qui marche : si des clients vous ont envoyé leurs photos et sont "
            "d'accord pour qu'elles paraissent, envoyez-les-moi avec le prénom de "
            "l'avis correspondant, je les place à côté. Je laisse ce fil ouvert "
            "pour votre réponse.", False),
    (12675, "Retiré : le filtre « Type de séjour » (Croisières / Mer Rouge) est "
            "remplacé par « Type de bateau », voir #12676.", True),
    (12676, "Le filtre « Type de bateau » propose « Bateau à moteur » (3 séjours) "
            "et « Bateau à voile (dahabeya) » (1 séjour).", True),
    (12677, VOILE, True),
    (12678, FAQ, True),
    (12679, "Le bouton « Demander mon devis » du texte de présentation passe en "
            "bleu nuit, sur toutes les pages ; le bouton doré reste réservé au "
            "bloc devis du bas.", True),
    (12680, BOUTONS, True),
]


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--essai', action='store_true')
    a = p.parse_args()

    tout = appel('GET', '/tout')
    if tout is None:
        sys.exit('Le plugin ne répond pas.')
    par_id = {x['id']: x for x in tout}

    envoyes = clos = 0
    for fil, message, refermer in REPONSES:
        x = par_id.get(fil)
        if not x:
            print('   #%-6d introuvable' % fil)
            continue
        deja = any(message[:40] in (r.get('message') or '')
                   for r in (x.get('reponses') or []))
        if deja and (not refermer or x.get('statut') == 'resolu'):
            continue
        print('   #%-6d %s%s' % (fil, message.replace('\n', ' ')[:70],
                                 '  [clos]' if refermer else '  [ouvert]'))
        if a.essai:
            continue

        if not deja:
            if appel('POST', '/fils/%d/reponses' % fil, {'message': message}) is None:
                print('      \u2717 réponse refusée')
                continue
            envoyes += 1
        if refermer:
            # Répondre rouvre le fil : on clôt après, jamais avant.
            appel('PATCH', '/fils/%d' % fil, {'statut': 'resolu'})

    # Rien n'est tenu pour fait avant d'être relu sur le serveur.
    relu = appel('GET', '/tout') or []
    etat = {x['id']: x for x in relu}
    manque = []
    for fil, message, refermer in REPONSES:
        x = etat.get(fil)
        if not x:
            manque.append('#%d disparu' % fil)
            continue
        if not any(message[:40] in (r.get('message') or '')
                   for r in (x.get('reponses') or [])):
            manque.append('#%d sans réponse' % fil)
        elif refermer and x.get('statut') != 'resolu':
            manque.append('#%d resté ouvert' % fil)
        elif refermer:
            clos += 1
    print('\n%d réponse(s) postée(s), %d fil(s) clos et vérifiés.' % (envoyes, clos))
    if manque:
        print('\u2717 à reprendre : %s' % ', '.join(manque))


if __name__ == '__main__':
    main()
