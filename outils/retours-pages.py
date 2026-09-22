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
    8921: [   # Destination · Alexandrie
        ('9505', 'remplacer',
         'Voiture : 2h30 en moyenne selon le traficCela permet',
         'Voiture : 2h30 en moyenne selon le trafic. Cela permet'),
    ],
}

# Les sections entières à retirer, repérées par leur titre exact.
SECTIONS = {
    8921: [('9508', 'Pourquoi voyager en Égypte avec nous ?')],
}

# Les questions de FAQ à retirer, repérées par leur intitulé exact.
QUESTIONS = {
    8922: [('9524', 'Quels sont les avantages de visiter Assouan par rapport à '
                    'Louxor ou au Caire ?')],
}


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
    faits, rates = [], []
    for fil, action, cible, remp in EDITS.get(pid, []):
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
        (faits if ok else rates).append(fil if ok else (fil, 'section', titre[:58]))
    for fil, intitule in QUESTIONS.get(pid, []):
        h, ok = retirer_question(h, intitule)
        (faits if ok else rates).append(fil if ok else (fil, 'question', intitule[:58]))
    return h, faits, rates


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
        neuf, faits, rates = corriger(pid, brut)
        titre = (p_.get('title') or {}).get('raw', '')
        print('\n#%d %s' % (pid, titre[:52]))
        print('   appliqués (%d) : %s' % (len(faits), ', '.join(str(f) for f in faits) or '—'))
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
