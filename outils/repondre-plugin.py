#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Le plugin remis à jour : les fils du 5 octobre et ceux de septembre.

    WP_AUTH='compte:mot de passe' ./outils/repondre-plugin.py [--essai]

Le 7 octobre, 150 fils étaient encore ouverts. Les 82 du 5 octobre avaient
été traités sur le site les 6 et 7, mais aucun n'avait reçu de réponse dans
le plugin : Mélanie ne pouvait pas savoir ce qui était fait. Parmi ceux de
septembre, beaucoup ont été réglés depuis par d'autres passes, et huit
portaient une réponse d'elle restée sans suite — appliquées par
retours-anciens.py, caire-une.py, prix-alignes.py et sinai-etapes.py.

Restent ouverts, et seulement eux, les fils qui attendent quelque chose
qu'elle seule peut fournir : des photos, le tarif de la Nubie, la liste des
médicaments, ses questions sur le handicap, le contenu sur les bateaux, et
deux « modifier le design » dont on ne sait pas ce qui gêne.
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
        f = '/tmp/.ae-filplugin.json'
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
AGENCE = "Fait sur la nouvelle page « L'agence », qui remplacera « Qui sommes-nous » à sa mise en ligne : "
DEVIS = ("Bouton « Demander mon devis » ajouté dans le bloc « Sur mesure », sur toutes "
         "les pages, avec le premier paragraphe en gras.")
ESPACE = "Espace ajouté entre les avis et les boutons, sur toutes les pages."
FAQ_RUB = ("La FAQ est rangée en rubriques (Découvrir, Avant de partir, Sur place, Pour qui, "
           "Formalités et santé, Organiser et réserver) : cinq questions visibles, un bouton "
           "pour les autres. Même chose sur toutes les pages.")
AGENCE_LOCALE = "« Agence locale basée au Caire » est retirée de tout le site (une cinquantaine de mentions)."
PRIX_520 = "« À partir de 520 € par personne », sur la page et sur les cartes."
OSM = ("Elle ne peut pas disparaître complètement : c'est la condition de la licence du fond "
       "de carte (OpenStreetMap). Elle est réduite au crédit discret qu'on voit sur toutes les "
       "cartes du web : « © OpenStreetMap », en petit, dans le coin.")
VOILE = ("Le voile sombre sur la photo du haut est de nouveau allégé, nettement, sur toutes les "
         "pages, ordinateur et téléphone.")
PRIX = ("Les cartes affichent maintenant le prix de trois des quatre séjours, comme leurs "
        "pages : dahabeya 1 895 €, mont Moïse 290 €, roadtrip 1 635 €. Reste la Nubie, qui "
        "n'a de prix nulle part : voir #10738.")
IMAGES = ("Cette page a été refaite depuis et les images cassées sont parties. S'il en reste "
          "une à retirer, reposez une bulle dessus sur la page en ligne.")
TEXTE_VILLE = "Le texte générique est remplacé par une courte présentation de %s."

REPONSES = [
    # ---------------------------------------------------------- 5 octobre
    (12249, AGENCE_LOCALE, True),
    (12252, AGENCE_LOCALE, True),
    (12256, AGENCE_LOCALE, True),
    (12254, PRIX_520, True),
    (12255, PRIX_520, True),
    (12259, PRIX_520, True),
    (12257, "« Quand partir » passe en trois périodes (à privilégier, encore possible, à "
            "éviter), chacune avec ses températures ; la frise mois par mois reste "
            "disponible, repliée. Même format sur toutes les pages.", True),
    (12258, "Retiré : il n'y a plus d'onglet « une journée ».", True),
    (12260, "Retirée.", True),
    (12261, "Ajoutées aux inclus des trois excursions dans le désert.", True),
    (12262, "Retirée.", True),
    (12263, "Retiré, sur toutes les pages : c'était le même élément partout.", True),
    (12264, "Retiré.", True),
    (12265, "Retiré.", True),
    (12270, "Photo de une remplacée.", True),
    (12279, "Photo de une remplacée.", True),
    (12272, "Le doublon est retiré.", True),
    (12273, "Retiré : Siwa n'est plus parmi les séjours du Sinaï.", True),
    (12274, "La photo n'est pas arrivée avec le commentaire : le plugin n'a rien reçu. "
            "Envoyez-la-moi par mail en me disant pour quelle carte, et je la pose.", False),
    (12276, "Fait : la carte montre maintenant les étapes — Mont Sinaï et Sainte-Catherine "
            "(le monastère est au pied du mont, à 2 km : une seule épingle pour les deux), "
            "Dahab et Charm el-Cheikh. On peut zoomer, et chaque épingle ouvre une bulle.", True),
    (12277, DEVIS, True), (12292, DEVIS, True), (12295, DEVIS, True),
    (12304, DEVIS, True), (12311, DEVIS, True), (12316, DEVIS, True),
    (12280, "Titre corrigé : « Voyage dans le Sinaï sur mesure ».", True),
    (12281, "La page montre 3 séjours, et le compteur les compte maintenant tout seul.", True),
    (12282, "Encart de sécurité ajouté, avec votre texte.", True),
    (12283, "Les deux séjours qui vont à Abou Simbel sont ajoutés : « Pyramides et croisière "
            "sur le Nil » et « Pyramides, croisière et mer rouge en famille ». 3 séjours.", True),
    (12284, "Retiré.", True), (12299, "Retiré.", True), (12303, "Retiré.", True),
    (12300, "Retirée.", True), (12302, "Retirée.", True),
    (12285, OSM, True), (12314, OSM, True),
    (12286, "Question retirée.", True), (12287, "Question retirée.", True),
    (12289, "Question retirée.", True), (12290, "Question retirée.", True),
    (12308, "Question retirée.", True),
    (12288, "Réponse reprise avec vos mots : 3 ou 4 nuits en général pour la croisière, "
            "une journée si l'on veut seulement Abou Simbel.", True),
    (12291, FAQ_RUB, True), (12294, FAQ_RUB, True), (12310, FAQ_RUB, True), (12315, FAQ_RUB, True),
    (12293, ESPACE, True), (12296, ESPACE, True), (12305, ESPACE, True),
    (12312, ESPACE, True), (12317, ESPACE, True), (12328, ESPACE, True),
    (12298, "Alexandrie est en ligne au nouveau format. Envoyez-moi vos photos quand vous "
            "voulez, je les ajoute.", True),
    (12306, "Deux séjours ajoutés, qui passent par Assouan : la croisière sur le lac Nasser "
            "et la croisière en bateau à voile. La page en montre 5.", True),
    (12307, "Retiré.", True),
    (12309, "Dans les réponses, la donnée qu'on cherche — période, durée, prix, "
            "température — est en gras.", True),
    (12313, TEXTE_VILLE % "Louxor", True),
    (12320, TEXTE_VILLE % "Assouan", True),
    (12321, TEXTE_VILLE % "Alexandrie", True),
    (12322, TEXTE_VILLE % "la ville", True),
    (12323, TEXTE_VILLE % "Lac Nasser et d'Abou Simbel", True),
    (12318, "5 séjours, comptés automatiquement sur les cartes.", True),
    (12319, "« 2 jours minimum ».", True),
    (12326, "Photo remplacée.", True),
    (12329, "Retiré.", True),
    (12330, "Chaque article a son propre libellé : vingt-deux, tous différents.", True),
    (12331, "Sept thèmes en filtres en haut du blog.", True),
    (12332, "« Au choix » est retiré.", True),
    (12349, "Quatre itinéraires ajoutés (Fayoum, Roadtrip, Pyramides-Louxor-mer Rouge, "
            "mont Moïse) : l'accueil en montre 12.", True),
    (12347, "Le logo est remplacé partout par une version propre à fond transparent : "
            "l'ancien fichier gardait un liseré autour du dessin.", True),
    (12348, "Voir #12347 : logo remplacé partout.", True),
    (12333, "Merci. La note est à jour : 4,9 sur 5, 24 avis.", True),
    (12336, AGENCE + "les deux mentions « Source : … » sont retirées.", True),
    (12337, AGENCE + "la carte « Testés et approuvés » est ajoutée, avec vos mots.", True),
    (12338, AGENCE + "la galerie « En images » est retirée.", True),
    (12340, "Il n'y a aucune photo de l'équipe dans la médiathèque. En attendant, la carte "
            "de Hend porte un monogramme. Envoyez-moi sa photo (et la vôtre) et je les "
            "pose.", False),
    (12342, AGENCE + "« Notre histoire » est réécrite.", True),
    (12343, AGENCE + "les cinq étapes y sont, dans l'ordre : prise de contact, envoi du "
            "devis, modifications, validation, préparation avant le voyage.", True),
    (12344, AGENCE + "la FAQ a la même forme que sur les autres pages.", True),
    (12345, AGENCE + "un vrai bouton « Demander mon devis » vers la page de demande.", True),
    (12346, AGENCE + "le même mur d'avis que les autres pages, avec les liens Google et "
            "TripAdvisor.", True),
    # ---------------------------------------------------------- septembre
    (7696, "La page « Sur mesure » est revenue à votre formulaire le 3 octobre : la question "
           "du bateau n'y est plus. Le type de bateau se choisit maintenant sur la page "
           "Croisières (filtre « Type de bateau »). Pour expliquer chaque bateau, voir #10748.", True),
    (9496, VOILE, True),
    (9538, VOILE, True),
    (9528, "Chaque destination a maintenant sa propre présentation : le texte générique "
           "« Confiez l'organisation… » a disparu des pages de destination.", True),
    (9529, "Voir #9528 : chaque destination a son propre texte.", True),
    (9530, "Voir #9528 : chaque destination a son propre texte.", True),
    (9531, "« Découvrir » ne se répète plus : chaque bouton dit où il mène.", True),
    (9548, "Chaque carte affiche maintenant le parcours, la durée, les principaux inclus "
           "et le prix.", True),
    (9567, "Les voyageurs choisissent leurs dates dans le formulaire de devis (date "
           "d'arrivée, date de départ). Le bloc « Quand partir » est passé en trois "
           "périodes.", True),
    (9568, "Votre remarque du 5 octobre (#12257) demandait un autre format pour ce bloc "
           "plutôt que son retrait : il est passé en trois périodes, frise repliée. Je le "
           "laisse donc sur les pages de séjour ; dites-le si vous préférez le retirer.", True),
    (9569, "Sans retour de votre part, je considère la carte validée. Rouvrez si besoin.", True),
    (9571, "Le jour par jour est repris : icônes hébergement et repas sur chaque journée, "
           "sites en gras, texte resserré. Les photos par journée attendent vos images "
           "(#10438).", True),
    (10430, "Ajouté : « Pyramides, croisière et mer rouge en famille », 1 485 €. Et la "
            "dahabeya affiche son prix, 1 895 €.", True),
    (10456, "Sans retour de votre part, je considère les deux retouches validées.", True),
    (10475, "Merci : tous les séjours restent dans « En groupe » et « Entre amis ».", True),
    (10476, "Fait : « Croisière » et « Le Nil » sont deux boutons distincts sur l'accueil. "
            "« Croisière » sort les 4 séjours qui embarquent ; « Le Nil » les 6 qui passent "
            "par Louxor ou Assouan, bateau ou pas.", True),
    (10446, "Les rubriques sont faites. J'attends vos questions sur le handicap, avec vos "
            "réponses, pour les ajouter.", False),
    (10481, "Corrigé : le bleu du site est votre #094D60, partout.", True),
    (10738, "Les cartes affichent maintenant le prix des séjours qui en ont un sur leur "
            "page (dahabeya, mont Moïse, roadtrip). Reste la Nubie, qui n'a de prix "
            "nulle part : donnez-moi son tarif et je le pose.", False),
    (10739, PRIX, True), (10740, PRIX, True), (11268, PRIX, True), (11278, PRIX, True),
    (10747, "Le filtre « Type de bateau » est en place sur la page Croisières : bateau à "
            "moteur (3 séjours) ou à voile (la dahabeya).", True),
    (10749, "Les deux liens, Google et TripAdvisor, sont sur toutes les pages qui portent "
            "des avis.", True),
    (10753, IMAGES, True), (10754, IMAGES, True), (10756, IMAGES, True), (10852, IMAGES, True),
    (10755, "L'image de Louxor est réparée. Reposez une bulle dessus sur la page en ligne si "
            "vous voulez toujours la retirer.", True),
    (10757, "« Quand partir » est passé en trois périodes, frise mois par mois repliée.", True),
    (10758, "« Ce que le prix comprend » vient maintenant juste après le prix, avant "
            "« Quand partir ».", True),
    (10762, "Fait : « Assistance H24 » remplace « Paysages uniques ».", True),
    (10774, "Fait : votre réponse est en place, et « Où trouver les meilleures vues sur le "
            "Nil ? » est retirée. Le haut de la page dit aussi « deux à trois jours ».", True),
    (10775, "Fait, dans votre ordre : le Grand Musée égyptien (GEM), le Musée égyptien, le "
            "Musée de la civilisation, et une ligne sur les autres musées du Caire.", True),
    (10779, DEVIS, True),
    (10784, "Fait.", True),
    (10785, "Reformulé : « Oui, les sites se visitent sans guide. Mais avec un guide qui "
            "s'adapte à vos envies et à votre rythme, la visite change : il explique ce que "
            "les panneaux ne disent pas… Vous repartez avec des explications riches, pas "
            "seulement des photos. »", True),
    (10792, FAQ_RUB, True),
    (10817, "Le logo est remplacé partout par une version propre à fond transparent.", True),
    (10837, "Voir #10817 : logo remplacé partout.", True),
    (10847, "Sans retour de votre part, je considère le bloc validé.", True),
    (10853, "La une du Caire montre maintenant le Sphinx devant la pyramide de Khéphren. "
            "Votre image n'est pas arrivée (le plugin n'a rien reçu) : si vous préférez la "
            "vôtre, envoyez-la par mail et je la remplace.", True),
    (11272, "Fait : les séjours qui embarquent sont tous dans les croisières.", True),
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
