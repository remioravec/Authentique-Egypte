#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Les réponses aux commentaires de Mélanie du 12 octobre (197 fils), et aux
trois fils de septembre où elle a répondu le même jour.

    WP_AUTH='compte:mot de passe' ./outils/repondre-1210.py [--essai]

Même mécanique que repondre-0710.py : on répond, puis on clôt, puis on relit
sur le serveur. Restent ouverts les seuls fils où il faut une précision
d'elle.
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
        f = '/tmp/.ae-fil1210.json'
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

CONF = "Retiré, sur les quatorze pages de séjour : la ligne « Devis gratuit… » et ses deux pictogrammes."
GRAS = ("Le premier paragraphe n'est plus en gras ; seuls les lieux importants qu'il cite le sont. "
        "Même chose sur toutes les pages de séjour.")
EQUIP = "La partie « Avant de boucler le sac » (les équipements) est retirée, sur toutes les pages de séjour."
FORMAT = "La partie « Le bon format / combien de temps prévoir » est retirée, sur toutes les pages de séjour."
VOL = "« Le vol interne » est ajouté dans « Ce que le prix comprend »."
CONTACT = ("Deux boutons sous « Qui vous accompagne » : « Personnaliser ce séjour » et « Nous écrire sur "
           "WhatsApp ». Même chose sur toutes les pages de séjour.")
BEDOUIN = "« Guide privé bédouin », dans « Qui vous accompagne », dans les inclus et en haut de page."
FAQ_CLIC = ("Le bouton fonctionne pour les visiteurs. C'est l'outil de relecture qui l'empêchait : en mode commentaire, "
            "il capte tous les clics de la page (un clic pose une bulle). Désormais, quand le mode commentaire est "
            "actif, toutes les questions s'affichent dépliées : vous pouvez les relire et les commenter.")
VOILE = ("Le voile de la photo du haut est allégé sur toutes les pages en ligne depuis le 7 octobre. Votre "
         "commentaire est posé sur un brouillon (adresse en ?page_id=…), resté dans l'ancien état : sur la page "
         "en ligne, c'est bon.")
BOUTONS_AVIS = ("Sur la page en ligne, les boutons sont centrés, en bleu, et séparés des avis (corrigé le 7 octobre). "
                "Ce commentaire est posé sur un brouillon (adresse en ?page_id=…), resté dans l'ancien état.")
PRIX = "À partir de %s € par personne, sur la page et sur toutes les cartes du site."
AGENCE = "Fait sur la nouvelle page « L'agence » : "

REPONSES = [
    # ------------------------------------------------------------- accueil
    (12936, "Le bloc « Composez votre Égypte » devient translucide, on voit la photo à travers, et il est plus "
            "compact.", True),
    (12937, "Nouvelle carte : elle est dessinée, et non plus faite de tuiles d'images. Les noms sont nets sur tous "
            "les écrans, téléphone compris, et chaque destination reste cliquable.", True),
    (12938, "« Neuf destinations, d'Alexandrie au lac Nasser » : la carte en montre neuf.", True),
    (12939, "« 51 jours avant le départ », dans toutes les FAQ du site.", True),
    (12940, FAQ_CLIC, True),
    (12941, "Tirets retirés : « …fait les réservations (hébergements, transferts, vols internes) et reste "
            "joignable sur place. »", True),
    (12997, "Retiré : la section s'appelle simplement « Comment ça se passe ».", True),
    (12998, "Retiré.", True),
    (12999, "Les boutons d'avis sont centrés, colorés et espacés sur toutes les pages en ligne. Ceux que vous avez vus "
            "collés étaient sur des brouillons (adresses en ?page_id=…). Pour les photos des avis Google : elles "
            "appartiennent aux voyageurs et Google ne permet pas de les reprendre ; voir #12674.", True),
    # ---------------------------------------------------------- croisières
    (12942, "Nouveau filtre « Croisière » : « Sur le Nil » (3 séjours) et « Sur le lac Nasser » (1).", True),
    (12943, "Nouveau design pour « Pourquoi nous », sur toutes les pages : quatre cartes blanches alignées, chaque "
            "pictogramme dans une pastille bleue. Plus de crème ni d'or.", True),
    (12944, "Réécrit avec vos mots : « En général 3 à 4 nuits : cela dépend du sens de la croisière, d'Assouan vers "
            "Louxor ou l'inverse, et du type de bateau. Des croisières plus longues sont possibles : plus lentes, "
            "avec davantage de temps libre. »", True),
    (12946, "Votre photo des montagnes du Sinaï remplace la plage sur la tuile « Sinaï », sur toutes les pages qui "
            "la montrent.", True),
    # ------------------------------------------------------- destinations
    (12947, "« Découverte de la Nubie » est ajoutée aux séjours d'Assouan.", True),
    (12948, "Le bloc « Sur mesure » devient un bandeau bleu, avec deux boutons : « Demander mon devis » et « Nous "
            "écrire sur WhatsApp ». Sur toutes les pages.", True),
    (12949, "Retiré, sur toutes les pages.", True),
    (12950, "La page montre neuf séjours qui passent par Le Caire : Fayoum, désert blanc, Siwa, Pyramides et croisière "
            "sur le Nil, Pyramides-croisière-mer Rouge en famille, Pyramides-Louxor-mer Rouge en famille, croisière "
            "sur le lac Nasser, roadtrip, dahabeya. Votre commentaire montrait encore l'ancien prix du Fayoum "
            "(185 €), c'était sans doute une version en cache. S'il en manque un, dites-moi lequel.", True),
    # -------------------------------------------------------------- agence
    (12952, AGENCE + "votre photo d'Abou Simbel en haut de page, et le voile allégé.", True),
    (12953, AGENCE + "« elle commence à organiser des séjours en partenariat avec une agence égyptienne du Caire ».", True),
    (12954, AGENCE + "« les maisons d'hôtes et les hôtels boutique de charme ».", True),
    (12955, AGENCE + "« La société française est enregistrée en 2024 : chaque voyage est couvert par un contrat de "
            "droit français. »", True),
    (12956, AGENCE + "la carte « Testés et approuvés » était posée à l'intérieur d'une autre carte, d'où le "
            "chevauchement. Elle est remise à côté des trois autres, et les quatre sont alignées.", True),
    (12957, AGENCE + "votre photo, celle envoyée le 5 octobre avec celle de Hend, est posée. Dites-moi si ce n'est pas "
            "celle-là.", True),
    (12958, AGENCE + "la presse et les plateformes deviennent des cartes cliquables, alignées.", True),
    (12959, AGENCE + "« en partenariat avec une agence égyptienne titulaire d'une licence certifiée par l'ETAA, "
            "l'organisme du gouvernement égyptien qui agrée les agences de voyages ».", True),
    (12961, AGENCE + "« Les paiements passent par Paytravel, une plateforme de paiement sécurisée basée en France et "
            "réservée aux agences de voyages. Vous payez en euros, et le paiement est versé directement à notre "
            "agence partenaire sur place. »", True),
    (12962, AGENCE + "« Sur place, un groupe WhatsApp réunit votre agent local, nos représentants et deux numéros "
            "d'urgence. »", True),
    (12963, AGENCE + "« des guides francophones et égyptologues ».", True),
    (12964, "Ce commentaire ne s'est accroché à aucun bloc (il pointe la page entière). Quelle partie faut-il "
            "reformater ? Reposez la bulle directement dessus.", False),
    (12965, AGENCE + "le même mur d'avis que sur toutes les pages, avec les boutons Google et TripAdvisor.", True),
    (12966, "Le logo du pied de page est bien le logo propre, à fond transparent : c'est le fond bleu nuit du pied de "
            "page que vous voyez autour. Si vous préférez une autre version (par exemple en blanc sur le bleu), "
            "envoyez-la-moi.", True),
    (12967, AGENCE + "Mélanie et Hend sont en tête de la section « Notre équipe », avec leurs portraits agrandis.", True),
    (12968, AGENCE + "les mentions juridiques sont dans une phrase, plus en liste.", True),
    # ---------------------------------------------------------------- Nubie
    (12969, "La page dit 1 190 € : c'est le prix de votre commentaire suivant, sur la page en ligne (#13123), posé "
            "après celui-ci. Si c'est 1 290 €, dites-le-moi.", True),
    (12970, "La page est passée au nouveau format, avec le voile allégé des autres pages.", True),
    (12971, "Description ajoutée en haut de page : « Au sud d'Assouan, la Nubie déroule ses villages aux maisons "
            "peintes de couleurs vives, le long du Nil et du lac Nasser… »", True),
    (12972, "Retiré.", True), (12973, "Retiré.", True), (12974, "Retiré.", True),
    (12975, "Le texte de présentation a maintenant le même format que sur les autres pages de séjour.", True),
    (12976, "Le jour par jour est en place. Attention : c'est celui qui était sur l'ancienne page, et il décrit un "
            "voyage Le Caire, Louxor, Edfou, Kom Ombo, sans la Nubie. Je l'ai remis au format pour que vous puissiez "
            "le corriger journée par journée.", True),
    (12977, "Retirée.", True), (12978, "Retirées : la galerie garde six photos.", True), (12979, "Retirée.", True),
    (12980, "Retirée.", True), (12981, "Retirée.", True), (12982, "Retirée.", True),
    (12983, "Les avis ont le même format que sur les autres programmes.", True),
    (13122, "La page « Découverte de la Nubie » est passée au nouveau format. Le jour par jour est celui qui était en "
            "ligne (Le Caire, Louxor, Edfou, Kom Ombo) : vous pouvez maintenant le commenter journée par journée.", True),
    (13123, PRIX % "1 190", True),
    # --------------------------------------------------------- couple, famille
    (12985, "La tuile « Voyage PMR » montrait un personnage détouré, sans décor : elle a maintenant une photo de "
            "felouque sur le Nil, sur les trois pages qui la montrent.", True),
    (12986, BOUTONS_AVIS, True), (12987, BOUTONS_AVIS, True),
    (12988, VOILE, True),
    (12989, "Retiré, sur les pages couple, famille et solo.", True),
    (12990, "Les deux séjours « en famille » ouvrent la liste : « Pyramides, Louxor et mer Rouge en famille » (qui "
            "manquait) puis « Pyramides, croisière et mer Rouge en famille ».", True),
    (12993, "Les guides sont maintenant des cartes avec photo, titre et description.", True),
    (12994, "Le bloc « Sur mesure » est un bandeau bleu, avec « Demander mon devis » et « Nous écrire sur "
            "WhatsApp ».", True),
    (12995, BOUTONS_AVIS, True), (12996, BOUTONS_AVIS, True),
    (10788, "Refait : plus de jaune ni d'orange. « Ce que les couples préfèrent » est maintenant un paragraphe, les "
            "envies en pastilles bleues alignées, deux photos et un bouton « Composer notre voyage à deux ».", True),
    (10844, "Refait : les activités en bulles bleues alignées, plus de crème ni d'or.", True),
    (10845, "Refait comme vous le décriviez : un paragraphe, les activités coup de cœur en bulles, ce qui est pensé pour "
            "les familles, deux photos à côté, et deux boutons pour passer à l'action.", True),
    # ------------------------------------------------------------- séjours
    (13000, PRIX % "295", True), (13001, PRIX % "295", True), (13003, PRIX % "295", True), (13002, GRAS, True),
    (13004, "« Le nouveau Musée égyptien (GEM) » au jour 2.", True),
    (13005, "« Temple de Karnak et Edfou (chaque lundi et mercredi) ».", True),
    (13006, "« Ce séjour est privatif au Caire, à Assouan et à Louxor : vous ne partagez ni le guide, ni le véhicule. "
            "Pendant la croisière, vous naviguez avec un petit groupe francophone. »", True),
    (13007, CONF, True), (13008, CONF, True), (13009, CONF, True),
    (13010, CONF, True), (13011, CONF, True), (13012, CONF, True), (13013, GRAS, True),
    (13014, "Remplacée par une photo des pyramides de Gizeh.", True),
    (13015, "Jour 1 : dîner retiré.", True), (13016, "Jour 1 : « Nuit à l'hôtel. »", True),
    (13017, "Jour 2 : petit-déjeuner et déjeuner, et le nouveau Musée égyptien en gras.", True),
    (13018, "Jour 3 : temple de Philae, puis 3h30 de route vers Abou Simbel ; son et lumière en option ; "
            "petit-déjeuner.", True),
    (13019, "Jour 4 : temples d'Abou Simbel, retour sur Assouan (3h30), embarquement, navigation et temple de Kom Ombo, "
            "nuit à bord. Le jour 5 garde son titre « Kom Ombo et navigation vers Edfou » : dites-moi ce qu'il devient, "
            "puisque Kom Ombo est maintenant au jour 4.", True),
    (13020, "« Tout inclus à bord, sauf boissons », sur les journées en bateau.", True),
    (13021, PRIX % "1 495", True), (13022, PRIX % "1 495", True), (13023, PRIX % "1 495", True),
    (13024, VOL, True), (13025, CONTACT, True),
    (13026, "« …une piscine à bord, des repas sous forme de buffet pour un large choix, et des animations le soir : "
            "spectacle de danse, tour de magie. »", True),
    (13027, "Ajouté : « À bord, la pension est complète, avec une piscine et des animations le soir. »", True),
    (13028, FAQ_CLIC, True),
    (13029, PRIX % "680", True), (13030, PRIX % "680", True), (13031, PRIX % "680", True),
    (13032, EQUIP, True), (13033, BEDOUIN, True), (13034, BEDOUIN, True),
    (13035, "« Chauffeur privatif en 4x4 ».", True),
    (13036, "La nuit en campement est remplacée par une nuit à l'hôtel, et « Les hébergements » sont dans les inclus.", True),
    (13037, "Les autorisations auprès des autorités locales sont dans les inclus.", True),
    (13038, FORMAT, True), (13039, CONF, True), (13040, CONF, True), (13041, CONF, True),
    (13042, CONF, True), (13043, CONF, True), (13044, CONF, True),
    (13045, "Texte de présentation ajouté : « Aux portes de la Grande Mer de Sable, près de la frontière libyenne, "
            "Siwa est une oasis de palmiers et de sources… »", True),
    (13046, PRIX % "695", True), (13047, PRIX % "695", True), (13053, PRIX % "695", True), (13048, GRAS, True),
    (13049, "Retiré.", True), (13050, FORMAT, True),
    (13051, "Retiré : le déroulé de Sainte-Catherine, et l'aperçu de ses étapes, ont quitté la page (voir #13052).", True),
    (13052, "Votre itinéraire est en place, jour par jour, avec les photos de Siwa : arrivée, Gabal Al Mawta, Shali "
            "et le coucher de soleil à Fatnas ; lacs salés, source de Cléopâtre, temples d'Amon et d'Alexandre ; "
            "Gabal Dakrur, Grande Mer de Sable, Bir Wahed et sandboarding ; retour au Caire.", True),
    (13054, BEDOUIN, True), (13055, EQUIP, True),
    (13056, "Retiré.", True), (13057, "Retiré.", True), (13058, "Retiré.", True),
    (13059, FORMAT, True),
    (13060, "Jour 2 : dîner et nuit à l'hôtel, plus de campement.", True),
    (13061, "Titre : « Excursion dans le désert blanc et noir ».", True),
    (13062, GRAS, True), (13063, BEDOUIN, True),
    (13064, CONF, True), (13065, CONF, True), (13066, CONF, True),
    (13067, PRIX % "445", True), (13068, PRIX % "445", True), (13069, PRIX % "445", True),
    (13070, "Retiré.", True),
    (13071, "Ce commentaire ne s'est accroché à aucun élément (il pointe la page entière). Que faut-il enlever ? "
            "Reposez la bulle directement dessus.", False),
    (13072, "Retirée.", True), (13073, "Retirée.", True),
    (13074, PRIX % "1 690", True), (13075, PRIX % "1 690", True), (13076, PRIX % "1 690", True),
    (13077, EQUIP, True),
    (13078, "Jour 1 : dîner retiré.", True), (13079, "Jour 1 : « Nuit à l'hôtel. »", True),
    (13080, "Jour 2 : petit-déjeuner et déjeuner.", True),
    (13081, "Jour 3 : temple de Philae, déjeuner, monastère de Saint-Siméon à dos de dromadaire, embarquement et nuit "
            "à bord ; petit-déjeuner, déjeuner et dîner.", True),
    (13082, "« Découverte d'Assouan ».", True),
    (13083, "Jour 4 : matinée libre à Assouan.", True),
    (13084, "Jour 4 : petit-déjeuner, déjeuner et dîner.", True),
    (13085, "Jour 5 : petit-déjeuner, déjeuner et dîner.", True),
    (13086, "Jour 5 : « En fin de journée, navigation jusqu'au temple d'Edfou. »", True),
    (13087, "Jour 6 : temple d'Edfou et navigation jusqu'à Louxor ; montgolfière retirée.", True),
    (13088, "Jour 7 : montgolfière en option, vallée des Rois, temple d'Hatchepsout, transfert vers la mer Rouge.", True),
    (13089, "Jour 9 ajouté : petit-déjeuner, puis transfert à l'aéroport de Hurghada.", True),
    (13090, VOL, True),
    (13091, "Retirée.", True), (13092, "Retirée.", True),
    (13093, "La FAQ reprend vos questions : départs le lundi, le mercredi et le vendredi ; itinéraire adapté à tous "
            "les âges ; guide privé pendant toute la croisière ; sièges auto et lits bébé ; chambre familiale, suite "
            "familiale ou deux cabines communicantes à bord ; aucun vaccin ; visa de 30 € à l'arrivée, adultes comme "
            "enfants ; sécurité.", True),
    (13094, CONF, True), (13095, CONF, True), (13096, CONF, True),
    (13097, "Le séjour est rangé en « Voyage en famille » (fil d'Ariane) et apparaît en croisière, en mer Rouge, sur "
            "Le Caire, Assouan et Louxor.", True),
    (13098, "Retiré.", True),
    (13099, "Le roadtrip est rangé en « Culturel » et « En famille » ; une case « En famille » s'ajoute au filtre.", True),
    (13100, "Rangé en « Culturel », « En famille » et « Mer Rouge » ; il apparaît aussi sur les pages Voyage "
            "culturel et Séjour en mer Rouge. Sa carte, incomplète, est refaite.", True),
    (13101, GRAS, True), (13102, "« 6 jours minimum », sur la page et sur les cartes.", True),
    (13103, "Retiré.", True),
    (13104, "« le nouveau Musée égyptien (GEM) ».", True),
    (13105, "Ajouté au jour 3 : « En option : felouque sur le Nil pour découvrir les villages nubiens. »", True),
    (13106, "Jour 4 : petit-déjeuner.", True), (13107, "Jour 3 : petit-déjeuner et déjeuner.", True),
    (13108, "Jour 3 : déjeuner.", True), (13109, "Jour 5 : petit-déjeuner.", True),
    (13110, "Retirée.", True), (13111, "Jour 6 : petit-déjeuner.", True),
    (13112, "Jour 7 : petit-déjeuner et dîner, et « Route pour Hurghada (4h30 de route) ».", True),
    (13113, "Jour 8 : pension complète et nuit à l'hôtel.", True),
    (13114, "Retiré.", True), (13115, "Retiré.", True),
    (13116, "Retirée.", True), (13117, "Retirée.", True), (13118, "Retirée.", True), (13119, "Retirée.", True),
    (13120, "« Quand partir » est déplacé à la fin.", True), (13121, VOL, True),
    (13124, "Jour 1 : dîner retiré.", True),
    (13125, "Jour 2 : petit-déjeuner, déjeuner et nuit à l'hôtel.", True),
    (13126, "Jour 3 : vélo, atelier de hiéroglyphes, poterie ou felouque l'après-midi ; montgolfière en option le "
            "matin.", True),
    (13127, "« Hôtel 5* ou hôtel boutique ».", True),
    (13128, "« à Hurghada (ou El Gouna, El Quseir, Marsa Alam) ».", True),
    (13129, "Deux journées ajoutées : jour 7, journée libre à Hurghada en pension complète ; jour 8, petit-déjeuner "
            "puis transfert à l'aéroport. Le séjour fait 8 jours.", True),
    (13130, EQUIP, True), (13131, CONTACT, True),
    (13132, "Retirée.", True), (13133, "Retirée.", True), (13134, "Retirée.", True), (13135, "Retirée.", True),
    (13136, CONF, True), (13137, CONF, True), (13138, CONF, True),
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
