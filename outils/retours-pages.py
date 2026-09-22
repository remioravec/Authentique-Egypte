#!/usr/bin/env python3
"""
Les corrections de contenu demandées page par page dans la relecture.

    WP_AUTH='compte:mot de passe' ./outils/retours-pages.py [--essai]

Chaque ligne du tableau porte le numéro du fil de relecture auquel elle
répond. Rien n'est corrigé qui ne soit demandé, et rien n'est demandé qui
ne soit corrigé sans le dire : une édition qui ne trouve pas son ancre est
SIGNALÉE, jamais passée sous silence. C'est le seul moyen de savoir qu'une
correction a été perdue au lieu de croire qu'elle a été faite.

Les textes ajoutés sont ceux de Mélanie, remis en phrase quand sa note
était télégraphique. Rien n'est inventé.
"""

import argparse
import os
import re
import sys
import time
from importlib.machinery import SourceFileLoader

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# (fil, action, cible, remplacement)
#   remplacer     : la cible doit exister, elle devient le remplacement
#   retirer       : la cible disparaît
#   ajouter_apres : le remplacement est inséré juste après la cible
EDITS = {
    8922: [   # Destination · Assouan
        ('9514', 'remplacer',
         '<small>Durée annoncée</small><b>4 à 9 jours</b>',
         '<small>Durée conseillée</small><b>1 à 3 jours</b>'),
        ('9517', 'remplacer',
         '<p class="">Depuis Louxor :</p>',
         '<p class=""><strong>Depuis Louxor :</strong></p>'),
        ('9518', 'remplacer',
         'Croisière sur le Nil (2 à 4 jours selon l’itinéraire)',
         'Croisière sur le Nil (3 nuits minimum)'),
        ('9519', 'ajouter_apres',
         '<p class="">Croisière sur le Nil (3 nuits minimum)</p>',
         '<p class="">Route (4 heures, avec la possibilité de visiter les temples '
         'de Kom Ombo et d’Edfou)</p>'),
        ('9520', 'retirer',
         '<p class="">Le choix dépend du temps disponible et de la manière dont le '
         'voyage est structuré.</p>', ''),
        ('9521', 'ajouter_apres',
         'pour un retour en début d’après-midi.</p>',
         '<p class="">Le mieux reste de dormir sur place : cela coupe la route, permet '
         'd’assister au spectacle son et lumière des temples d’Abou Simbel, et de '
         'découvrir les temples sans trop de monde.</p>'),
        ('9522', 'remplacer',
         'Il a été déplacé pierre par pierre dans les années 70',
         'Il a été déplacé pierre par pierre par l’UNESCO dans les années 70'),
        ('9523', 'ajouter_apres',
         'notamment en felouque.</p>',
         '<p class="">Les croisières se font en dahabeya, en bateau à moteur ou en '
         'felouque.</p>'),
        ('9525', 'ajouter_apres',
         'des maisons aux façades peintes des villages traditionnels.</p>',
         '<p class="">Le monastère Saint-Siméon, rejoint à dos de dromadaire à travers '
         'le désert, reste peu fréquenté ; un tour en felouque complète bien la '
         'journée.</p>'),
    ],

    8598: [   # Circuits · Nos séjours (page mère)
        # Le hero n'avait aucune image. Celle-ci est jointe par Mélanie au
        # fil #9553. On reprend la structure exacte des autres heros :
        # un fond net, et le même visuel flouté derrière pour habiller les
        # bords quand la photo ne couvre pas toute la largeur.
        ('9553', 'remplacer',
         '<section class="hero"><div class="hero__in">',
         '<section class="hero" style="--une-l:1280px;--une-h:360px">'
         '<div class="hero__flou" data-flou="oui" aria-hidden="true">'
         '<img src="https://authentiquegypte.com/wp-content/uploads/2026/09/flo-p-zpmvpEXM_Qc-unsplash-1-scaled.jpg" alt="" '
         'decoding="async" loading="lazy"></div>'
         '<div class="hero__fond">'
         '<img src="https://authentiquegypte.com/wp-content/uploads/2026/09/flo-p-zpmvpEXM_Qc-unsplash-1-scaled.jpg" alt="" '
         'decoding="async" loading="lazy"></div>'
         '<div class="hero__in">'),
    ],
    8598: [   # Circuit · Nos séjours (page mère)
        # Le compteur annonçait « 0 séjour » alors que la page en porte
        # quatorze. Un zéro affiché en tête de page dit au visiteur qu'il
        # n'y a rien à voir.
        ('9547', 'remplacer', '>0 séjour</span>', '>14 séjours</span>'),
        # La phrase de Mélanie, fil #9551 : les séjours sont une base, pas
        # un catalogue figé. Elle manquait, et c'est ce qui distingue une
        # agence sur mesure d'un tour-opérateur.
        ('9551', 'ajouter_apres', '<h1>Nos séjours</h1>',
         '<p class="hero__chapo">Tous nos séjours sont entièrement modifiables selon '
         'vos envies : ce n’est qu’une première base pour construire le vôtre.</p>'),
    ],
    8596: [   # Circuit · Déserts et Oasis
        # La question que Mélanie demande d'ajouter, fil #9563, avec sa
        # réponse telle qu'elle l'a écrite.
        ('9563', 'ajouter_apres', '<div class="faqu">',
         '<details class="faq__q"><summary>Organisez-vous les autorisations '
         'nécessaires pour les déserts&nbsp;?</summary><div class="faq__r">'
         '<p>Oui, nous organisons bien les autorisations nécessaires auprès du '
         'ministère du tourisme égyptien.</p></div></details>'),
    ],
    8923: [   # Destination · Fayoum
        # « Il n'y a qu'un seul séjour sur Fayoum, faire attention à
        # l'affichage et à la conjugaison » : la pastille accordait
        # « conseillés » au masculin pluriel derrière « 1 nuit ».
        ('9533', 'remplacer', '<b>1 nuit</b>conseillés', '<b>1 nuit</b>conseillée'),
    ],
    8595: [   # Circuit · Croisières
        ('9560', 'remplacer',
         'plus grand, avec tout le confort moderne, souvent en groupe',
         'plus grand, tout le confort moderne, mais très touristique'),
    ],
    8921: [   # Destination · Alexandrie
        # L'image que Mélanie a jointe elle-même au fil #9498. Le visuel en
        # place était une photo du Sinaï — elle n'a jamais montré
        # Alexandrie.
        ('9498', 'remplacer',
         'https://authentiquegypte.com/wp-content/uploads/2025/06/DSC00581-1-scaled.jpg',
         'https://authentiquegypte.com/wp-content/uploads/2026/09/flo-p-zpmvpEXM_Qc-unsplash-scaled.jpg'),
        ('9498b', 'remplacer',
         'https://authentiquegypte.com/wp-content/uploads/2025/06/DSC00581-1-scaled.jpg',
         'https://authentiquegypte.com/wp-content/uploads/2026/09/flo-p-zpmvpEXM_Qc-unsplash-scaled.jpg'),
        ('9505', 'remplacer',
         'Voiture : 2h30 en moyenne selon le traficCela permet',
         'Voiture : 2h30 en moyenne selon le trafic. Cela permet'),
        ('9513', 'remplacer', '<b>2 jours</b>conseillés', '<b>1 à 2 jours</b>conseillés'),
        # « Il n'y a pas vraiment de snorkeling que nous organisons à
        # Alexandrie » : la phrase promettait des plongées et des sites
        # sous-marins. On retire ce qui n'est pas proposé, on garde la
        # promesse qui reste vraie.
        ('9509', 'remplacer',
         'choisissez votre rythme, vos escales et vos expériences sous-marines. '
         'Du snorkeling parmi les récifs coralliens aux plongées profondes , '
         'des villages côtiers aux sites sous-marins spectaculaires ,',
         'choisissez votre rythme, vos escales et vos visites. Des sites antiques '
         'aux quartiers du bord de mer, des musées aux marchés,'),
    ],
}

# Les pastilles du hero à retirer, repérées par le texte qu'elles portent.
# Mélanie : « 8 séjours y passent » → « enlever » (fil #9512). Le chiffre
# vient des liens de la page en ligne, et aucun des séjours listés ne
# passe réellement par Alexandrie : afficher le compte, c'est afficher une
# promesse fausse.
PASTILLES = {8921: [('9512', 'séjours y passent')]}


# Les sections entières à retirer, repérées par leur titre exact.
SECTIONS = {
    8921: [('9508', 'Pourquoi voyager en Égypte avec nous ?')],
}

# Les questions de FAQ à retirer, repérées par leur intitulé exact.
QUESTIONS = {
    8922: [('9524', 'Quels sont les avantages de visiter Assouan par rapport à '
                    'Louxor ou au Caire ?')],
}


# Le voile du hero. La charte le pose à 93 % d'opacité : le titre est
# parfaitement lisible, mais la photo disparaît dessous — « le fond est
# trop sombre » (#9496), « photo trop sombre » (#9538). On l'allège, sans
# descendre au point que le titre blanc cesse de passer : le contraste
# est mesuré sur la couleur composée après coup, pas supposé.
VOILE = ('<style data-hero="voile">'
         '.pg .hero::after{background:linear-gradient(96deg,'
         'rgba(6,61,71,.80) 0%,rgba(6,61,71,.62) 52%,rgba(6,61,71,.46) 100%)}'
         '@media (max-width:860px){.pg .hero::after{background:linear-gradient(180deg,'
         'rgba(8,70,80,.58) 0%,rgba(6,61,71,.78) 100%)}}'
         '</style>')
ALLEGER_VOILE = {8921: '9496', 8926: '9538'}


def _fin(h, debut, nom):
    p = 0
    for t in re.finditer(r'<(/?)%s\b[^>]*>' % nom, h[debut:]):
        p += 1 if not t.group(1) else -1
        if p == 0:
            return debut + t.end()
    return -1


def retirer_section(h, titre):
    """La section dont le <h2> porte ce titre, en entier."""
    for m in re.finditer(r'<section\b[^>]*>', h):
        f = _fin(h, m.start(), 'section')
        if f < 0:
            continue
        bloc = h[m.start():f]
        h2 = re.search(r'<h2[^>]*>(.*?)</h2>', bloc, re.S)
        if h2 and re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', h2.group(1))).strip() == titre:
            return h[:m.start()] + h[f:], True
    return h, False


def retirer_question(h, intitule):
    """L'accordéon dont le <summary> porte cet intitulé."""
    for m in re.finditer(r'<details\b[^>]*>', h):
        f = _fin(h, m.start(), 'details')
        if f < 0:
            continue
        bloc = h[m.start():f]
        s = re.search(r'<summary[^>]*>(.*?)</summary>', bloc, re.S)
        if s and re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', s.group(1))).strip() == intitule:
            return h[:m.start()] + h[f:], True
    return h, False


def corriger(pid, h):
    """Rend (page, [fils appliqués], [fils NON appliqués])."""
    faits, rates, deja = [], [], []
    for fil, action, cible, remp in EDITS.get(pid, []):
        # Relancé, l'outil ne doit RIEN refaire : un « ajouter_apres » dont
        # l'ancre est toujours là parce qu'elle survit à l'ajout poserait
        # le texte une seconde fois. On reconnaît donc d'abord ce qui est
        # déjà en place, et on ne confond plus « déjà fait » avec
        # « ancre introuvable » — les deux se lisaient pareil dans le
        # rapport, et c'est justement la différence qui compte.
        if action == 'ajouter_apres' and remp in h:
            deja.append(fil)
            continue
        if action == 'remplacer' and cible not in h and remp in h:
            deja.append(fil)
            continue
        if action == 'retirer' and cible not in h:
            deja.append(fil)
            continue
        if cible not in h:
            rates.append((fil, action, cible[:58]))
            continue
        if action == 'remplacer':
            h = h.replace(cible, remp, 1)
        elif action == 'retirer':
            h = h.replace(cible, '', 1)
        elif action == 'ajouter_apres':
            h = h.replace(cible, cible + remp, 1)
        faits.append(fil)
    for fil, titre in SECTIONS.get(pid, []):
        h, ok = retirer_section(h, titre)
        (faits if ok else deja).append(fil)
    for fil, mot in PASTILLES.get(pid, []):
        n = len(h)
        h = re.sub(r'<span class="pill">(?:(?!</span>).)*?%s(?:(?!</span>).)*?</span>' % re.escape(mot),
                   '', h, flags=re.S)
        (faits if len(h) < n else deja).append(fil)
    if pid in ALLEGER_VOILE and 'data-hero="voile"' not in h:
        h += VOILE
        faits.append(ALLEGER_VOILE[pid])
    for fil, intitule in QUESTIONS.get(pid, []):
        h, ok = retirer_question(h, intitule)
        (faits if ok else deja).append(fil)
    return h, faits, rates, deja


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--essai', action='store_true')
    a = p.parse_args()
    dep = SourceFileLoader('dep', os.path.join(RACINE, 'outils', 'deployer.py')).load_module()

    cibles = sorted(set(list(EDITS) + list(SECTIONS) + list(QUESTIONS)))
    total_f = total_r = 0
    for pid in cibles:
        p_ = dep.appel('GET', '/pages/%d?context=edit' % pid)
        brut = re.sub(r'<!-- /?wp:html -->\n?', '', p_['content']['raw'])
        neuf, faits, rates, deja = corriger(pid, brut)
        titre = (p_.get('title') or {}).get('raw', '')
        print('\n#%d %s' % (pid, titre[:52]))
        print('   appliqués (%d) : %s' % (len(faits), ', '.join(str(f) for f in faits) or '—'))
        if deja:
            print('   déjà en place (%d) : %s' % (len(deja), ', '.join(str(f) for f in deja)))
        total_f += len(faits)
        for r in rates:
            total_r += 1
            print('   ✗ NON APPLIQUÉ — fil %s (%s) : ancre « %s » introuvable' % r)
        if a.essai or not faits:
            continue
        corps = '<!-- wp:html -->\n' + neuf + '\n<!-- /wp:html -->'
        for essai in range(4):
            try:
                dep.appel('POST', '/pages/%d' % pid, {'content': corps})
                relu = dep.appel('GET', '/pages/%d?context=edit' % pid)
                if len(relu['content']['raw']) > 1000:
                    break
            except SystemExit as motif:
                print('      reprise %d/3 — %s' % (essai + 1, str(motif).splitlines()[0][:60]))
            time.sleep(2 ** essai)
        else:
            print('      ✗ ABANDON, la page reste telle quelle')
    print('\n%d correction(s) appliquée(s), %d non appliquée(s).' % (total_f, total_r))


if __name__ == '__main__':
    main()
