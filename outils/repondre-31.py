#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Les réponses aux trente-et-un fils traités sans arbitrage.

    WP_AUTH='compte:mot de passe' ./outils/repondre-31.py [--essai]

Vingt-neuf sont faits et se referment. Deux restent ouverts : #10481, la
couleur du bleu, que je ne peux pas deviner ; et #10475, où j'ai pris
une décision de contenu — les huit séjours sont marqués « en groupe » et
« entre amis » — qu'elle doit pouvoir corriger.

L'ordre compte : répondre rouvre un fil clos. On répond d'abord, on
classe ensuite.

DEUX GARDE-FOUS, appris d'un premier jet qui a annoncé trente-deux
réponses sans en écrire une seule. Le plugin a sa propre racine REST :
passer par le client des pages ajoutait « /wp/v2/ » devant, le serveur
rendait un 404 — et un 404 est du JSON parfaitement valide, donc rien
n'a levé d'erreur. D'où, ici, une racine à part, et surtout une
relecture : rien n'est compté comme fait sans être allé le revoir.
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
        f = '/tmp/.ae-fil31.json'
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
REPONSES = [
    (9539, "Les blocs « Pourquoi nous » et « Sur mesure » prennent un fond crème et "
           "un filet or, et leurs icônes passent en or — c'est le jaune de la charte, "
           "celui des boutons. Dites-moi si vous le vouliez ailleurs aussi.", True),
    (10420, "La question de sécurité passe en première position de la FAQ, sur les "
            "trente-quatre pages qui en ont une. Elle était jusqu'ici en deuxième ou "
            "repliée selon les pages.", True),
    (10421, "Fond crème et filet or sur les quatre atouts, icônes en or.", True),
    (10422, "Même traitement sur le bloc « Sur mesure ».", True),
    (10423, "Refait : huit avis au lieu de vingt-trois, cartes plus compactes, texte "
            "coupé à six lignes, guillemet et filet supérieur en or. Et la sélection "
            "change d'une page à l'autre — chaque page tire ses huit avis à partir "
            "d'un décalage qui lui est propre, donc deux pages voisines n'affichent "
            "pas les mêmes.", True),
    (10427, "Le titre tient sur une ligne au-dessus de 1100 px. Ce qui le coupait "
            "n'était pas la largeur de l'écran mais une mesure fixée à dix-huit "
            "caractères ; je l'ai desserrée à trente plutôt qu'interdire le retour à "
            "la ligne, qui aurait fait déborder les titres longs des autres séjours.", True),
    (10431, "Voir #10423 : huit avis, plus compacts, plus de couleur, et une "
            "sélection différente d'une page à l'autre.", True),
    (10435, "Carte ajoutée, avec les étapes numérotées et le tracé du parcours : "
            "Assouan → Abu Simbel → Assouan → Louxor → Le Caire. Elle est construite "
            "à partir des titres de journée du déroulé, pas du texte courant — le "
            "premier essai lisait tout le déroulé et proposait un itinéraire qui "
            "citait des villes que le séjour ne traverse pas. Deux autres programmes "
            "en manquaient aussi, ils en ont une maintenant.", True),
    (10436, "Le jour par jour est resserré : texte à 0,97 rem, titres de journée à "
            "1,12 rem.", True),
    (10437, "Les sites sont en gras dans tous les déroulés. Le repérage se fait sur "
            "une liste de lieux réels et non sur les majuscules, sinon « Accueil » et "
            "« Transfert » seraient passés en gras eux aussi.", True),
    (10448, "L'article PMR est posé juste avant la FAQ, avec un lien « Lire le guide "
            "PMR ».", True),
    (10450, "Fond crème et filet or sur le bloc « Sur mesure » de cette page aussi.", True),
    (10451, "Section ajoutée après la liste des séjours, avec vos trois points : "
            "chambres familiales ou communicantes, guide égyptologue privatif qui "
            "cale le rythme sur celui des enfants, lit parapluie et siège auto sur "
            "demande.", True),
    (10452, "Retirée.", True),
    (10453, "Retirée.", True),
    (10454, "Retirée.", True),
    (10460, "Retirée.", True),
    (10461, "Retirée.", True),
    (10462, "Retirée. Les trois pastilles partent des quatre pages profil seulement : "
            "le même bandeau porte le fil du séjour sur une page programme et la "
            "durée conseillée sur une destination, il n'était à retirer que là où il "
            "répétait les cartes.", True),
    (10463, "Encart ajouté avec vos cinq activités : dîner dans un palace, "
            "hébergements de charme, montgolfière au lever du jour, repas à bord "
            "d'une felouque privatisée, moment sur la mer Rouge.", True),
    (10464, "Bouton « Voir tous les programmes » en bas de la liste, sur les quatre "
            "pages profil.", True),
    (10465, "Fond crème et filet or, comme sur les autres pages.", True),
    (10466, "Voir #10423.", True),
    (10472, "Corrigé : « Un expert local organise l'itinéraire et les étapes, fait "
            "les réservations — hébergements, transferts, vols internes — et reste "
            "joignable sur place. »", True),
    (10475, "« En groupe » et « Entre amis » ajoutés au premier filtre.\n\n"
            "Une question : j'ai marqué les huit séjours comme faisables en groupe et "
            "entre amis, puisqu'ils sont tous privatifs et modifiables. Si certains ne "
            "s'y prêtent pas — la croisière à capacité réduite, par exemple —, "
            "dites-le-moi et je les retire de ces deux filtres.", False),
    (10476, "« Le Caire » ajouté au filtre des envies : il sort les cinq séjours dont "
            "le déroulé passe par la capitale.\n\n"
            "Pour « Croisière » : le filtre existait déjà sous le nom « Le Nil » — "
            "c'est la même sélection. Plutôt qu'un second bouton qui ferait doublon, "
            "il s'appelle maintenant « Croisière sur le Nil ».", True),
    (10477, "Retiré.", True),
    (10479, "Corrigé : le bouton a maintenant 64 px sous lui avant le pied de page, "
            "vérifié sur ordinateur et sur téléphone.", True),
    (10480, "Le bloc passe avant les avis.", True),
    (10481, "Le bleu de ce bloc est #095360, celui de la charte — c'est aussi celui "
            "du pied de page, du bandeau du haut et du fond du hero. Si ce n'est pas "
            "le bon, il ne l'est nulle part sur le site : donnez-moi le bleu que vous "
            "voulez (une référence, ou une capture où il apparaît) et je le change "
            "partout d'un coup plutôt que sur ce seul bloc.", False),
    (10483, "Voir #10423 : huit avis, cartes plus compactes, texte à 0,95 rem.", True),
    (10484, "Le composeur de voyage passe en premier, avant la présentation des "
            "familles de séjours.", True),
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
