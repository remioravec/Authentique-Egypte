#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Répondre à Mélanie dans le plugin, fil par fil, et clore ce qui est fait.

    WP_AUTH='compte:mot de passe' ./outils/repondre-2409.py [--essai]

Une réponse est postée sous chaque fil traité, puis le fil est marqué
résolu — dans cet ordre, parce que répondre rouvre un fil clos. Les fils
qui attendent encore quelque chose d'elle reçoivent la question et
restent ouverts : c'est tout l'intérêt de les laisser ouverts.
"""

import argparse
import json
import os
import subprocess
import sys
import time

API = 'https://authentiquegypte.com/wp-json/ae-commentaires/v1'

# Traités : une réponse, puis on clôt.
FAITS = {
 '10416': "C'est fait : les cartes utilisent maintenant le fond d'OpenStreetMap France, "
          "qui affiche les noms en français là où ils existent. Toujours aucun cookie.",
 '10417': "Ajouté, avec vos mots : « À 5 h du Caire en voiture. »",
 '10418': "La question s'intitule maintenant « Que voir ? ».",
 '10419': "Réponse reprise : le camping avec les autorisations nécessaires et selon les "
          "disponibilités, sinon guest house ou eco-lodge.",
 '10424': "Le voile posé sur la photo est allégé — de 93 % à 80 %. C'est fait sur toutes "
          "les pages, pas seulement celle-ci.",
 '10426': "Vous aviez raison de dire « toutes les pages » : le voile est allégé sur les 57, "
          "de 93 % à 80 %, en s'éclaircissant vers la droite. Le titre reste lisible, "
          "c'est ce qui limite l'allègement.",
 '10429': "La frise est agrandie : les degrés passent de 0,95 à 1,05 rem.",
 '10432': "Retiré. Vous aviez raison : ce bloc répétait mot pour mot une réponse de la FAQ "
          "qui se trouve deux sections plus bas.",
 '10433': "Retiré, comme le bloc Paiement, pour la même raison.",
 '10434': "Retiré également. Le lien « Le détail, question par question » reste et mène à la FAQ.",
 '10439': "Ligne retirée.",
 '10440': "Journée retirée.",
 '10442': "Retiré.",
 '10443': "Visite retirée.",
 '10444': "Remplacé : le Grand Musée égyptien (GEM) à la place du survol en hélicoptère.",
 '10445': "Le voile de la photo est allégé sur toutes les pages. Si c'est la photo elle-même "
          "que vous voulez changer, envoyez-la-moi et je la pose.",
 '10449': "Bandeau supprimé.",
 '10455': "Le filtre est allégé, ici et sur les 57 pages.",
 '10459': "Bandeau supprimé.",
 '10467': "Chaque lien reprend maintenant le titre du guide qu'il ouvre.",
 '10468': "Corrigé, comme les trois autres.",
 '10469': "Corrigé.",
 '10470': "Corrigé — les 22 occurrences.",
 '10473': "Retiré. Au passage, ce bloc affichait « N voyageurs accompagnés », le N en toutes "
          "lettres : un repère de fabrication jamais rempli. Il part avec.",
 '10474': "Retiré du haut de page. Le compte reste sous les avis, plus bas.",
 '10485': "Les cartes sont passées au fond d'OpenStreetMap France, qui rend les noms français.",
 # les séjours recalculés
 '9500': "Vous avez raison. J'ai relu les quatorze itinéraires un par un : aucun ne passe par "
         "Alexandrie. La liste était construite à partir des liens de la page en ligne, et "
         "c'est elle qui se trompait. La page ne propose donc plus de séjour pour Alexandrie "
         "et invite au sur-mesure. Dites-moi si des séjours doivent y passer.",
 '9501': "Même réponse qu'au-dessus : vérifié sur les quatorze itinéraires, aucun ne passe par "
         "Alexandrie. La liste est corrigée.",
 '9502': "Même réponse : la liste est reconstruite à partir des déroulés jour par jour.",
 '9503': "Même réponse : corrigé.",
 '10425': "Vous aviez raison, et l'écart était important : la page affichait 1 séjour alors que "
          "9 passent par Le Caire. Les listes sont maintenant construites à partir du déroulé "
          "jour par jour des fiches, et Gizeh compte pour Le Caire. Le Mont Sinaï passe de 1 à 5, "
          "Louxor de 4 à 6, Assouan de 5 à 3.",
}

# Ouverts : on pose la question, on ne clôt pas.
QUESTIONS = {
 '10428': "Quelles photos ne s'affichent pas bien — celles du déroulé, de la galerie, ou les "
          "deux ? Et sur quel appareil l'avez-vous vu ?",
 '10430': "Quel troisième séjour voulez-vous voir ici ? Je peux prendre le suivant de la même "
          "catégorie, mais je préfère que vous choisissiez.",
 '10438': "Il me faut vos photos : la médiathèque n'en contient pas par étape. Envoyez-les-moi "
          "nommées par étape et je les pose sur les quatorze fiches.",
 '10446': "Pouvez-vous me donner les questions ET vos réponses ? Je peux poser « le voyageur "
          "peut-il se lever ? », « fauteuil roulant manuel ou électrique ? », « machine "
          "respiratoire ? » — mais les réponses doivent être les vôtres.",
 '10447': "J'ai bien compris le sens. Pouvez-vous m'écrire le paragraphe tel que vous le voulez ? "
          "Je ne réécris pas votre texte sans votre accord.",
 '10457': "Quel passage ne vous convient pas, et par quoi le remplacer ? Je peux vous proposer "
          "une version si vous préférez.",
 '9567': "Un sélecteur de dates est un vrai développement : il faut décider ce qu'il fait — "
         "filtrer les séjours disponibles, ou pré-remplir le formulaire de devis ? Dites-moi "
         "lequel et Rémi vous dira ce que ça représente.",
}


def appel(methode, chemin, charge=None):
    auth = os.environ.get('WP_AUTH', '')
    if ':' not in auth:
        sys.exit("WP_AUTH manquant.")
    cmd = ['curl', '-s', '--max-time', '90', '-u', auth, '-X', methode, API + chemin]
    if charge is not None:
        f = '/tmp/.ae-fil.json'
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
    n_rep = n_clos = 0

    for fil, texte in sorted(FAITS.items()) + sorted(QUESTIONS.items()):
        x = par_id.get(fil)
        if not x:
            print('   #%s introuvable' % fil)
            continue
        clore = fil in FAITS
        deja = any(texte[:40] in (r.get('message') or '') for r in (x.get('reponses') or []))
        if deja and (x['statut'] == 'resolu' or not clore):
            continue
        print('   #%-7s %-9s %s' % (fil, 'clôture' if clore else 'question',
                                    texte[:64].replace('\n', ' ')))
        if a.essai:
            continue
        if not deja:
            r = appel('POST', '/fils/%s/reponses' % fil, {'message': texte})
            if r is None:
                print('      ✗ réponse refusée')
                continue
            n_rep += 1
        if clore:
            # Répondre rouvre le fil : on clôt après, jamais avant.
            appel('PATCH', '/fils/%s' % fil, {'statut': 'resolu'})
            n_clos += 1

    print('\n%d réponse(s) postée(s), %d fil(s) clos.' % (n_rep, n_clos))


if __name__ == '__main__':
    main()
