#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Les réponses que mon propre travail a rendues fausses.

    WP_AUTH='compte:mot de passe' ./outils/reponses-caduques.py [--essai]

Les soixante-douze fils ouverts portent tous une réponse de ma part, et
toutes datent d'avant le 29 septembre — donc d'avant les deux grandes
passes de correction. Neuf d'entre elles ne tiennent plus.

Trois parce que j'avais demandé des précisions sur un défaut que j'ai
trouvé et corrigé depuis. Mélanie avait raison, et c'est moi qui ne
savais pas où regarder. Une parce que je lui ai donné une couleur qui
n'existe plus dans le site. Cinq parce que je lui ai dit « je ne sais
pas de quelle image vous parlez » alors que huit images de cette page
étaient cassées.

Chaque réponse a été vérifiée contre le contenu déployé avant d'être
écrite : les attributs réparés, les vignettes mortes retirées, la
largeur de la FAQ, la couleur de la charte. Rien d'annoncé qui ne soit
mesuré.

Les trois fils dont il ne reste rien à attendre d'elle sont clos. Les
six autres restent ouverts : ils appellent encore sa réponse.

L'ordre compte : répondre rouvre un fil résolu, donc on répond d'abord
et on clôt ensuite.
"""

import argparse
import json
import os
import re
import sys
import time

SITE = 'https://authentiquegypte.com'
API = SITE + '/wp-json/ae-commentaires/v1'

# (fil, réponse, clore)
MESSAGES = [

    (10428, """Vous aviez raison, et j'avais tort de vous demander des précisions : le défaut était dans le code, pas dans votre description.

Deux causes, l'une et l'autre corrigées. La première : une de mes passes de mise en gras avait couru à l'intérieur des attributs d'image. Le fichier s'appelait « …/Voyage-sur-mesure-a-&lt;b&gt;Louxor&lt;/b&gt;-en-Egypte.png », une adresse qui ne mène nulle part. Quinze attributs de cette page étaient dans ce cas, sur douze pages au total. La seconde : huit vignettes de la galerie pointaient vers des fichiers supprimés de la médiathèque. Vérifiées une par une, elles répondaient toutes « page introuvable ».

Les adresses sont réparées et répondent, les huit vignettes mortes sont retirées. Il reste onze photos sur cette page, toutes vérifiées.""", True),

    (10791, """Vous aviez raison et je n'avais pas su le reproduire. Le défaut n'était pas dans le pliage des questions, mais dans leur largeur : la liste s'arrêtait 280 pixels avant le bord que son propre titre atteignait — le bloc était plafonné à 840 pixels dans un conteneur qui en fait 1120. D'où cette impression de décalage au milieu de la page.

C'est corrigé sur les 58 pages : la FAQ rejoint maintenant le bord de son titre.""", True),

    (11277, """Je confirme après coup : les deux liens, Google et TripAdvisor, sont toujours en place sous les avis. Je viens de les revérifier sur la page, après les cinq passes de correction qui ont suivi votre remarque.""", True),

    (10481, """Je me suis trompé en vous répondant, et il faut que je le dise clairement.

Je vous citais #095360 comme « le bleu de la charte ». Il n'est plus nulle part dans le site, et il n'aurait jamais dû y être : ce n'était pas le vôtre. En reprenant la charte graphique que vous nous avez envoyée, j'ai relevé votre bleu — #094D60 — et votre or — #ECAA24 — et j'ai réaligné les 58 pages dessus.

Le bloc que vous visiez porte donc maintenant votre bleu et non le mien. Dites-moi si c'est le bon.""", False),

    (10753, """Huit vignettes de cette page pointaient vers des fichiers supprimés de la médiathèque : elles s'affichaient en image cassée. Je les ai retirées, après avoir vérifié une par une qu'aucune ne répondait.

Est-ce que c'était l'une de celles-là que vous vouliez enlever ? S'il en reste une à retirer, reposez la bulle dessus : la page n'en porte plus que onze, ce sera plus facile à désigner.""", False),

    (10754, """Même réponse qu'au fil #10753 : huit images cassées ont été retirées de cette page. Dites-moi si celle que vous visiez en faisait partie.""", False),

    (10756, """Même réponse qu'au fil #10753 : huit images cassées ont été retirées de cette page. Dites-moi si celle que vous visiez en faisait partie.""", False),

    (10852, """Même réponse qu'au fil #10753 : huit images cassées ont été retirées de cette page. Dites-moi si celle que vous visiez en faisait partie.""", False),

    (10755, """Je comprends maintenant pourquoi votre bulle s'était accrochée à du code au lieu de l'image : l'adresse de cette image était corrompue. Une de mes passes de mise en gras avait écrit une balise à l'intérieur de l'attribut — « Voyage-sur-mesure-a-&lt;b&gt;Louxor&lt;/b&gt;-en-Egypte.png » — ce qui cassait le repère autant que l'affichage.

C'est réparé. L'image de Louxor s'affiche de nouveau. Reposez la bulle dessus si vous voulez toujours la retirer avec son texte : elle s'accrochera correctement cette fois.""", False),
]


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--essai', action='store_true')
    a = p.parse_args()

    import base64
    import requests
    S = requests.Session()
    S.verify = '/root/.ccr/ca-bundle.crt'
    u, m = os.environ['WP_AUTH'].split(':', 1)
    S.headers['Authorization'] = 'Basic ' + base64.b64encode(('%s:%s' % (u, m)).encode()).decode()

    def appel(methode, chemin, charge=None):
        r = S.request(methode, API + chemin, json=charge, timeout=60)
        try:
            d = r.json()
        except Exception:
            print('      réponse illisible (%s) : %s' % (r.status_code, r.text[:90]))
            return None
        # Un corps d'erreur est du JSON valide : il faut le reconnaître.
        if isinstance(d, dict) and d.get('code') and d.get('data', {}).get('status'):
            print('      refus %s : %s' % (d['data']['status'], str(d.get('message'))[:80]))
            return None
        return d

    avant = appel('GET', '/tout')
    fils = avant if isinstance(avant, list) else (avant or {}).get('fils', [])
    etat = {f['id']: f.get('statut') for f in fils}
    reps = {f['id']: len(f.get('reponses') or []) for f in fils}

    n = 0
    for fil, message, clore in MESSAGES:
        if fil not in etat:
            print('   ✗ #%s introuvable' % fil)
            continue
        print('   #%-6s %-9s %s' % (fil, etat[fil],
                                    ('réponse + clôture' if clore else 'réponse')))
        if a.essai:
            continue
        if appel('POST', '/fils/%s/reponses' % fil, {'message': message}) is None:
            print('      ✗ réponse non posée')
            continue
        if clore:
            time.sleep(1)
            # On clôt APRÈS : répondre rouvre un fil.
            if appel('PATCH', '/fils/%s' % fil, {'statut': 'resolu'}) is None:
                print('      ✗ clôture refusée')
        n += 1
        time.sleep(1)

    if a.essai:
        print('\n%d fil(s) à reprendre.' % len(MESSAGES))
        return

    # On relit pour vérifier, plutôt que de croire les codes de retour.
    apres = appel('GET', '/tout')
    fils = apres if isinstance(apres, list) else (apres or {}).get('fils', [])
    e2 = {f['id']: (f.get('statut'), len(f.get('reponses') or [])) for f in fils}
    souci = 0
    for fil, _, clore in MESSAGES:
        st, nr = e2.get(fil, ('?', 0))
        if nr <= reps.get(fil, 0):
            print('   ✗ #%s : la réponse n a pas été enregistrée' % fil); souci += 1
        if clore and st != 'resolu':
            print('   ✗ #%s : toujours %s' % (fil, st)); souci += 1
    print('\n%d fil(s) repris · %d anomalie(s) à la relecture.' % (n, souci))


if __name__ == '__main__':
    main()
