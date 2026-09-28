#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Les réponses aux retours du 28 septembre.

    WP_AUTH='compte:mot de passe' ./outils/repondre-2809.py [--essai]

Faits et clos d'un côté ; de l'autre, ce qui attend d'elle — avec, à
chaque fois, exactement ce qu'il me manque.

Deux garde-fous repris de repondre-31.py : le plugin a sa propre racine
REST, et rien n'est compté comme fait sans être allé le revoir.
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
    # --- les quatre défauts d'affichage, corrigés ---
    (10796, "Corrigé. Ce n'était pas un bug d'affichage mais du code resté visible : "
            "« {#oasis-de-dakhla} » est la syntaxe d'ancre du Markdown, jamais "
            "convertie en HTML. Seize occurrences sur cette page, dans les titres et "
            "dans le sommaire. Les liens du sommaire fonctionnent toujours.", True),
    (10797, "Corrigé, même cause : voir #10796.", True),
    (10798, "Corrigé, même cause : voir #10796.", True),
    (10799, "Corrigé, même cause : voir #10796.", True),
    (10800, "Corrigé, même cause : voir #10796.", True),
    (10801, "Corrigé, même cause : voir #10796.", True),
    (10802, "Corrigé, même cause : voir #10796.", True),
    (10818, "Corrigé. L'apostrophe était encodée deux fois, d'où le « L&#x27;Égypte » "
            "qui s'affichait tel quel. Quinze occurrences en tout, sur cette page et "
            "sur trois autres — Le Caire, Fayoum et le Mont Sinaï.", True),
    (10819, "Corrigé, même cause : voir #10818.", True),
    (10765, "Corrigé : c'était le même double encodage de l'apostrophe que sur le "
            "blog. La description s'affiche maintenant normalement.", True),
    (10766, "Corrigé, même cause : voir #10765.", True),
    (10827, "Corrigé. Ce n'était pas un défaut de mise en page mais un tableau à deux "
            "colonnes aplati en une suite de paragraphes : les deux en-têtes d'abord, "
            "puis les lignes en alternance. Le tableau est reconstruit, avec ses trois "
            "lignes et ses deux colonnes, et il défile horizontalement sur téléphone.", True),
    (10828, "Corrigé, même cause : voir #10827.", True),
    (10803, "Fait : la FAQ est passée au gabarit du site, en questions dépliables. "
            "C'était une simple liste à puces où la question et la réponse se "
            "suivaient dans la même ligne.", True),
    (10804, "Fait : voir #10803.", True),
    (10805, "Fait : voir #10803.", True),
    (10806, "Fait : voir #10803.", True),
    (10807, "Fait : voir #10803.", True),

    # --- les descriptions de cartes ---
    (10767, "Fait. La ligne existait mais était vide, et réservait sa place sans rien "
            "dire — c'est ce blanc que vous voyiez. Elle porte maintenant "
            "l'itinéraire du séjour, repris de son déroulé : pour celui-ci, "
            "« Le Caire → Louxor → Edfou → Kom Ombo → Abou Simbel → Assouan → Louxor ». "
            "Trente-deux cartes étaient dans ce cas sur l'ensemble du site, toutes "
            "sont remplies.", True),
    (10768, "Fait : voir #10767. Ici « Le Caire → Assouan → Kom Ombo → Edfou → Louxor "
            "→ Hurghada ».", True),
    (10769, "Fait : voir #10767. Ici « Assouan → Abou Simbel → Assouan → Louxor → "
            "Le Caire ».", True),
    (10770, "Fait : voir #10767. Ici « Le Caire → Louxor → Hurghada ».", True),
    (10771, "Fait : voir #10767.", True),
    (10772, "Fait : voir #10767.", True),
    (10773, "Fait : voir #10767. Ici « Bahariya → Désert Blanc → Le Caire ».", True),

    # --- le voile, et ce que j'ai mesuré ---
    (10820, "Le voile sombre est repensé, et vous aviez raison de revenir dessus : "
            "l'alléger de 93 % à 80 %, comme je l'avais fait, ne suffisait pas — à "
            "80 % la photo est encore un aplat, et sur téléphone une seconde règle le "
            "remontait à 78 %.\n\n"
            "Le principe a changé. Le voile ne couvre plus toute l'image : il suit la "
            "colonne de texte, dense à gauche où il faut pouvoir lire, et nul sur le "
            "quart droit où la photo reprend ses couleurs. Mesuré : le tiers droit du "
            "bandeau est 35 à 38 % plus lumineux qu'avant, et le titre garde un "
            "contraste de 7 à 9 sur ordinateur (le minimum d'accessibilité est 3).\n\n"
            "Si c'est la photo elle-même que vous vouliez changer, envoyez-la ici." + ENVOI, False),

    # --- ses mots, reportés ---
    (10823, "Fait : « Paysages uniques » devient « Assistance H24 », sur les dix-huit "
            "pages qui portent ce bloc.", True),
    (10824, "Fait : « Découverte culturelle complète » devient « Conseils par experts "
            "locaux », sur les dix-huit pages.", True),
    (10741, "Fait : « voyage de vos rêves » devient « voyage sur mesure ».", True),
    (10745, "Fait : « Continuer » devient « Découvrir », sur les six pages où le "
            "bouton apparaît.", True),
    (10750, "Fait : voir #10745.", True),
    (10838, "Ajouté en italique sous la ligne : « Tous les sites desservis par la "
            "croisière ne sont pas accessibles. »", True),
    (10839, "Ajouté en italique : « Selon disponibilités dans les destinations. »", True),
    (10840, "Ajouté en italique : « Optionnel. »", True),

    # --- les retraits ---
    (10777, "Retirée.", True),
    (10778, "Retirée. Vous aviez deux questions sur les musées : celle-ci part, et "
            "l'autre est à reprendre — voir #10775.", True),
    (10786, "Retirée.", True),
    (10789, "Retirée.", True),
    (10790, "Retirée.", True),
    (10830, "Retiré.", True),
    (10831, "Retiré, avec son entrée de sommaire.", True),
    (10832, "Retiré.", True),
    (10833, "Retiré.", True),
    (10834, "Retiré.", True),
    (10835, "Retiré.", True),
    (10836, "Retiré.", True),
    (10841, "Retiré, avec son entrée de sommaire.", True),
    (10843, "Retiré.", True),
    (10784, "J'ai retiré la locution : la réponse commence maintenant par « Oui, "
            "notamment au lever du soleil. »\n\n"
            "Votre remarque pouvait se lire de deux façons — retirer la phrase, ou "
            "retirer la question entière. J'ai pris la moins destructrice. Si c'est "
            "toute la question qu'il faut enlever, dites-le et je la retire.", False),
    (10752, "La mention est réduite et atténuée. Je ne peux pas la supprimer "
            "complètement : c'est la seule condition de la licence OpenStreetMap, qui "
            "nous permet d'avoir une carte sans clé Google, sans cookie et sans "
            "bandeau de consentement.", True),

    # --- le bouton de devis ---
    (10742, "Bouton « Demander mon devis » ajouté, il renvoie vers votre page "
            "https://authentiquegypte.com/sur-mesure/", True),
    (10794, "Bouton ajouté vers la page de demande de devis.", True),
    (10822, "Bouton ajouté vers la page de demande de devis, aux couleurs du site.", True),

    # --- le défaut qu'elle n'avait pas vu ---
    (10779, "Vous aviez raison, et le problème était plus large que cette page.\n\n"
            "Le paragraphe « Sur mesure » a été écrit pour la mer Rouge — snorkeling, "
            "récifs coralliens, plongées profondes — et il a été recopié tel quel sur "
            "quinze pages. Quatorze n'ont rien à voir avec la plongée : le Désert "
            "blanc, le lac Nasser, Le Caire, Alexandrie, les quatre pages profil, le "
            "blog.\n\n"
            "Je ne l'ai pas réécrit : je l'ai coupé. Votre phrase devient « Nous "
            "créons votre itinéraire unique : choisissez votre rythme, vos escales et "
            "vos expériences. Chaque détail est pensé pour vous. » — la vôtre, moins "
            "l'énumération qui ne vaut que pour la mer Rouge. La seconde reprend la "
            "variante que vous aviez vous-même écrite pour le désert. La page mer "
            "Rouge garde son texte d'origine.\n\n"
            "Si vous voulez un paragraphe propre à chaque page, envoyez-les-moi et je "
            "les pose.", False),
    (10825, "Même correction que #10779 : le texte de plongée est parti de cette page. "
            "Le bouton de devis est ajouté.", True),
    (10780, "Bouton de devis ajouté, et le texte de plongée est parti — voir #10779.", True),
]

# Ce qui attend d'elle : on répond, on laisse ouvert.
ATTENTE = [
    (10738, "Ce n'est pas un défaut d'affichage : ces séjours n'ont de prix nulle "
            "part, ni sur la carte ni sur leur propre page. Quatre sont concernés — "
            "Découverte de la Nubie, Le Caire et croisière sur un bateau à voile, "
            "Coucher de soleil sur le mont Moïse, Roadtrip sur mesure. Donnez-moi "
            "leurs tarifs et je les pose ; sinon je laisse « Prix sur devis », "
            "dites-moi simplement lequel des deux."),
    (10739, "Voir #10738 : quatre séjours n'ont de prix nulle part. Il me faut les "
            "vôtres."),
    (10740, "Voir #10738."),
    (10743, "Il me faut l'adresse exacte de votre fiche Google — celle qui ouvre "
            "directement la liste des avis. Envoyez-la ici et je la pose sur les "
            "trente-quatre pages d'un coup."),
    (10749, "Il me faut les deux adresses : celle de votre fiche Google et celle de "
            "votre page TripAdvisor. Une fois que je les ai, les deux liens partent "
            "sur toutes les pages en même temps."),
    (10759, "Voir #10749 : il me faut l'adresse de votre page TripAdvisor."),
    (10764, "Voir #10749."),
    (10781, "Voir #10749."),
    (10795, "Voir #10749."),
    (10826, "Voir #10749."),
    (10848, "Voir #10749."),
    (10775, "J'ai bien noté l'ordre : d'abord le GEM, puis le Musée égyptien, puis le "
            "Musée de la civilisation égyptienne. Pouvez-vous me donner la phrase "
            "complète telle que vous la voulez, avec les autres musées que vous "
            "aimeriez citer ? Je ne réécris pas votre texte sans votre accord."),
    (10776, "Noté : foodtour, cours de cuisine avec une association locale, tyrolienne "
            "près de l'église troglodyte, dîner-croisière sur le Nil le soir. "
            "Confirmez-moi la formulation et je remplace le paragraphe."),
    (10785, "Pouvez-vous m'écrire la phrase telle que vous la voulez ? J'ai compris le "
            "sens — un guide qui s'adapte à votre rythme et qui explique ce qu'on ne "
            "lit pas sur place — mais ce sont vos mots qui doivent y être."),
    (10817, "Il me faut le logo au format PNG avec fond transparent. Celui de la "
            "médiathèque a un fond blanc." + ENVOI),
    (10837, "Voir #10817 : il me faut le logo en PNG à fond transparent."),
    (10757, "Le format de la frise météo est à refaire, je suis d'accord. C'est une "
            "refonte de bloc et non une retouche : je préfère vous montrer deux "
            "propositions avant de la déployer sur les trente-quatre pages qui la "
            "portent. Je les prépare."),
    (10758, "Noté : « ce que le prix comprend » doit venir juste après le prix, et non "
            "après la météo. Je le fais en même temps que la refonte de la météo, pour "
            "ne pas déplacer deux fois les mêmes blocs."),
    (10761, "C'est la demande la plus lourde de la série : une photo par journée, un "
            "lien vers la carte, des icônes hébergement et repas, et un sommaire des "
            "étapes. Les icônes et le sommaire, je peux les faire seul. Les photos "
            "par journée, il me les faut — c'est le même besoin que #10438. Je vous "
            "prépare une maquette du jour par jour avant de la déployer sur les "
            "quatorze fiches."),
    (10791, "Je n'ai pas réussi à reproduire le défaut d'alignement : la FAQ de cette "
            "page s'affiche correctement chez moi sur ordinateur et sur téléphone. "
            "Pouvez-vous m'envoyer une capture, en me disant sur quel appareil et "
            "quel navigateur ?" + ENVOI),
    (10792, "Bonne idée, et la FAQ est effectivement longue. Avant de la découper, "
            "dites-moi vos catégories : je pense à « Avant de partir », « Sur place », "
            "« Le séjour », « Santé et sécurité » — mais c'est vous qui savez ce que "
            "vos voyageurs demandent le plus."),
    (10737, "Le filtre existe déjà : je l'ai construit pour les pages destination "
            "(durée, budget, sans rechargement de page). Le porter ici est faisable. "
            "Dites-moi sur quels critères vous voulez trier les programmes — durée, "
            "prix, région, type de séjour ?"),
    (10747, "Même réponse que #10737 : le filtre existe, il faut choisir ses critères. "
            "Vous proposez région, type de bateau et budget — je peux le faire, mais "
            "il me manque le type de bateau : il n'est indiqué sur aucune fiche. "
            "Donnez-le-moi séjour par séjour et je pose le filtre."),
    (10782, "Voir #10737."),
    (10787, "Voir #10737."),
    (10842, "Voir #10737."),
    (10829, "Il me faut votre liste : quels médicaments sont interdits à l'entrée, et "
            "lesquels demandent une ordonnance. C'est une information médicale et "
            "réglementaire, je ne la rédige pas de mémoire."),
]


def appel(methode, chemin, charge=None):
    auth = os.environ.get('WP_AUTH', '')
    if ':' not in auth:
        sys.exit('WP_AUTH manquant.')
    cmd = ['curl', '-s', '--max-time', '90', '-u', auth, '-X', methode, API + chemin]
    if charge is not None:
        f = '/tmp/.ae-fil2809.json'
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


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--essai', action='store_true')
    a = p.parse_args()

    tout = appel('GET', '/tout')
    if tout is None:
        sys.exit('Le plugin ne répond pas.')
    par_id = {x['id']: x for x in tout}

    travaux = [(f, m, True) for f, m, *r in REPONSES for _ in (0,)][:0]  # lisibilité
    travaux = list(REPONSES) + [(f, m, False) for f, m in ATTENTE]

    envoyes = 0
    for fil, message, refermer in travaux:
        x = par_id.get(fil)
        if not x:
            print('   #%-6d introuvable' % fil)
            continue
        deja = any(message[:40] in (r.get('message') or '')
                   for r in (x.get('reponses') or []))
        if deja and (not refermer or x.get('statut') == 'resolu'):
            continue
        print('   #%-6d %s%s' % (fil, message.replace('\n', ' ')[:66],
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
        print('\n%d fil(s) visés.' % len(travaux))
        return

    # Rien n'est tenu pour fait avant d'être relu sur le serveur.
    etat = {x['id']: x for x in (appel('GET', '/tout') or [])}
    clos, manque = 0, []
    for fil, message, refermer in travaux:
        x = etat.get(fil)
        if not x:
            manque.append('#%d disparu' % fil)
        elif not any(message[:40] in (r.get('message') or '')
                     for r in (x.get('reponses') or [])):
            manque.append('#%d sans réponse' % fil)
        elif refermer and x.get('statut') != 'resolu':
            manque.append('#%d resté ouvert' % fil)
        elif refermer:
            clos += 1
    print('\n%d réponse(s) postée(s), %d fil(s) clos et vérifiés.' % (envoyes, clos))
    if manque:
        print('✗ à reprendre : %s' % ', '.join(manque))


if __name__ == '__main__':
    main()
