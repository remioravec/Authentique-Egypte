#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Les 24 fils restés ouverts le 12 octobre au soir : ce qu'on a pu faire sans
attendre Mélanie (photos-1210.py, bateaux-1210.py, pmr-1210.py,
medicaments-1210.py, complements-1210.py).

    WP_AUTH='compte:mot de passe' ./outils/repondre-1210b.py [--essai]

Même mécanique que repondre-1210.py, dont on reprend l'appel au plugin : on
répond, puis on clôt, puis on relit sur le serveur. Puis les trois commentaires de 14 h sur l'accueil (accueil-1210b.py).
Restent ouverts les fils
qui demandent une photo qu'on n'a pas (Bahariya, atelier, colonne de Pompée,
sites d'Alexandrie) et les deux bulles posées sur la page entière.
"""

import argparse
import importlib.util
import os
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('rep1210', os.path.join(ICI, 'repondre-1210.py'))
R = importlib.util.module_from_spec(spec)
spec.loader.exec_module(R)
appel = R.appel

ENVOI = ("\n\nSi vous préférez une autre photo : rouvrez cette bulle et glissez-la dedans, ou collez-la "
         "(Ctrl+V).")

REPONSES = [
    # Photos
    (10820, "Remplacée : la carte « Les arnaques et erreurs à éviter » montre maintenant un couple dans un souk "
            "(photo de votre médiathèque), à la place du visuel publicitaire au bandeau « Egypt »." + ENVOI, True),
    (10744, "Fait. La tuile « Voyage culturel » a maintenant sa photo partout où elle apparaît (les colonnes d'un "
            "temple) ; elle ne reprend plus la felouque de la tuile « Croisières ». La tuile « Désert » montre le "
            "désert blanc au lieu du sommet du Sinaï." + ENVOI, True),
    (10746, "C'est la tuile « Sinaï » : elle porte maintenant la photo du Sinaï que vous avez "
            "envoyée (#11271)." + ENVOI, True),
    (10751, "Même tuile « Sinaï » que sur « Nos séjours » : elle porte maintenant la photo du Sinaï que vous avez "
            "envoyée (#11271)." + ENVOI, True),
    (9526, "La carte « Pyramides et croisière sur le Nil » a sa photo (une felouque sur le Nil), comme toutes les "
           "cartes de la page." + ENVOI, True),
    (9527, "La carte « Roadtrip » montrait Karnak, à Louxor, sur la page d'Assouan. Sur cette page, elle montre "
           "désormais les villages nubiens d'Assouan (votre photo) ; ailleurs, elle garde celle du séjour." + ENVOI,
     True),
    (9543, "C'est la tuile « Voyage PMR » : le dessin au trait est remplacé par une photo (une felouque sur le Nil) "
           "depuis le 12 octobre." + ENVOI, True),
    (10846, "Même tuile « Voyage PMR » : le dessin au trait est remplacé par une photo (une felouque sur le Nil) "
            "depuis le 12 octobre." + ENVOI, True),
    (10816, "Fait : le guide a sa photo de fond, le coucher de soleil sur l'oasis de Siwa (l'un des huit lieux du "
            "guide)." + ENVOI, True),
    (10854, "Fait : le guide a sa photo de fond, les pyramides de Gizeh." + ENVOI, True),
    (10856, "Fait : « Plongée en mer Rouge » a sa photo, les eaux de la mer Rouge. Le crédit « Photo de Tom » "
            "était déjà retiré." + ENVOI, True),
    (10438, "Fait avec la médiathèque : chaque journée des programmes a maintenant une photo de son lieu, jamais "
            "deux fois la même dans un séjour (19 journées illustrées aujourd'hui). Une seule reste sans photo : "
            "le jour 1 du désert blanc, à Bahariya — la médiathèque n'a aucune image de l'oasis, et je ne mets "
            "pas une autre oasis à sa place. C'est le fil #10809 qui la demande." + ENVOI, True),
    (10761, "Tout est en place : les icônes hébergement et repas, le sommaire des étapes, le lien vers la carte, et "
            "maintenant une photo par journée (sauf Bahariya, dont la médiathèque n'a aucune image — voir #10809)."
     + ENVOI, True),
    # Contenu
    (10748, "Fait. « Pourquoi nous » est remplacé, sur la page Croisières, par « Felouque, dahabeya ou bateau à "
            "moteur ? » : trois cartes avec photo, durée, description et « Pour qui ». Felouque : 2 nuits minimum ; "
            "dahabeya : 4 à 5 jours de navigation ; bateau à moteur 5* : 3 à 4 nuits. Les textes reprennent votre "
            "guide « Croisière en Égypte : dahabieh, bateau, felouque », vers lequel un bouton renvoie.\n\n"
            "La médiathèque n'a pas de photo de bateau à moteur : sa carte montre le Nil à Assouan. Envoyez-en "
            "une si vous en avez.", True),
    (10446, "Fait. Quatre questions ajoutées à la FAQ de la page PMR :\n"
            "— Je ne peux pas me lever, ou très peu : le voyage est-il possible ?\n"
            "— Fauteuil roulant manuel ou électrique : qu'est-ce que cela change ?\n"
            "— Je voyage avec un appareil respiratoire : comment l'organiser ?\n"
            "— Un accompagnant peut-il m'aider au quotidien ?\n\n"
            "Les réponses reprennent uniquement ce que dit votre guide « Voyager en Égypte en fauteuil roulant ». "
            "Relisez-les : si une réponse ne correspond pas à ce que vous proposez, dites-le ici.", True),
    (10829, "Fait, dans une nouvelle partie du guide : « Voyager avec ses médicaments : ordonnance et produits "
            "interdits ». Il n'existe pas de liste officielle publiée par l'Égypte. La partie donne donc la règle : "
            "certains médicaments y sont classés comme stupéfiants et demandent une autorisation préalable du "
            "ministère égyptien de la Santé (le tramadol, par exemple). Elle conseille aussi de voyager avec "
            "l'ordonnance, une attestation du médecin et les boîtes d'origine, et de se renseigner auprès de "
            "l'ambassade pour un traitement particulier.\n\n"
            "Source citée : les conseils du ministère belge des Affaires étrangères (repris par mesvaccins.net, "
            "mise à jour du 26 novembre 2025). Si vous avez une information plus précise, je l'ajoute.", True),
    (10738, "Les quatorze cartes de « Nos séjours » affichent maintenant leur prix, Nubie comprise (1 190 €).", True),
    (12674, "Je clos ce fil : les photos des avis Google ne peuvent pas être reprises. Si des clients vous envoient "
            "leurs photos et acceptent qu'elles paraissent, rouvrez-le avec la photo et le prénom de l'avis : je "
            "la placerai à côté.", True),
    # L'accueil, commentaires de 14 h (outils/accueil-1210b.py)
    (13514, "La carte est réduite de moitié : sur ordinateur, elle est maintenant à gauche et les six vignettes de "
            "destination à droite, au lieu de prendre toute la largeur (près de 1 000 px de haut). Les noms des "
            "lieux restent lisibles. Sur téléphone, rien ne change.", True),
    (13515, "Le titre devient « Nos destinations en Égypte ». Si vous avez une autre formulation en tête, écrivez-la "
            "ici et je la pose telle quelle.", True),
    (13516, "Le fond du composeur est nettement plus transparent (55 % au lieu de 78 %) : on voit la photo à travers. "
            "Les intitulés gris sont un peu plus foncés pour rester lisibles.", True),
    # Reste ouvert : il manque des photos
    (9504, "Deux sites ont maintenant leur photo, sous « Que voir à Alexandrie ? » : le fort Qaitbay et les jardins "
           "de Montaza (vos photos du 5 octobre). Il manque encore la bibliothèque, les catacombes de Kom "
           "el-Shoqafa et la colonne de Pompée.\n\nPour les envoyer : rouvrez cette bulle et glissez les photos "
           "dedans, ou collez-les (Ctrl+V).", False),
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
                print('      ✗ réponse refusée')
                continue
            envoyes += 1
        if refermer:
            # Répondre rouvre le fil : on clôt après, jamais avant.
            appel('PATCH', '/fils/%d' % fil, {'statut': 'resolu'})

    if a.essai:
        return
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
    ouverts = [x['id'] for x in relu if x.get('statut') != 'resolu']
    print('\n%d réponse(s) postée(s), %d fil(s) clos et vérifiés.' % (envoyes, clos))
    print('%d fils, %d ouverts : %s' % (len(relu), len(ouverts), ', '.join(map(str, sorted(ouverts)))))
    if manque:
        print('✗ à reprendre : %s' % ', '.join(manque))


if __name__ == '__main__':
    main()
