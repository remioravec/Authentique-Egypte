#!/usr/bin/env python3
"""
Transplante un corps de page avec son propre habillage, sans collision.

Couler une page dans le gabarit d'une autre, c'est faire cohabiter deux
feuilles de style écrites séparément. Elles emploient les mêmes mots pour
des choses différentes : sur une page profil, « edito » est un article
encadré ; dans le gabarit circuit, c'est une grille de deux colonnes. Le
corps repris héritait de la seconde, et les questions se retrouvaient dans
la colonne de gauche, leurs réponses dans celle de droite — illisible.

La parade tient en une idée : le corps repris n'emprunte plus aucun nom de
classe au gabarit. Chaque classe qu'il porte est renommée « rp-… », et les
règles de SA feuille d'origine le suivent, renommées de la même façon. Il
garde donc exactement l'allure qu'il avait sur sa page, quoi que le
gabarit décide par ailleurs, et le gabarit garde la sienne.

Rien du texte n'est touché : seuls les noms de classes changent.
"""

import re

PREFIXE = 'rp-'

# Ce qui ne doit surtout PAS être renommé : les classes que le gabarit pose
# lui-même autour du corps repris, et celles de la mise en forme.
INTOUCHABLES = {'pg-sec', 'pg-sec--fond', 'pg-sec--creme', 'pg-sec--serre',
                'pg-sec--nuit', 'mef', 'mef-q', 'mef-def', 'mef-tab',
                'repris', 'vu'}


# ── lecture d'une feuille ────────────────────────────────────────────────

def sans_commentaires(css):
    """Ôte les commentaires avant toute analyse.

    Un commentaire laissé en place colle sa fin au sélecteur qui suit —
    « … cartes d'atouts. */ .edito{…} » — et le navigateur jette la règle
    entière sans rien dire. C'est ce qui privait le contenu repris de son
    cadre : la règle était bien recopiée, simplement illisible.
    """
    return re.sub(r'/\*.*?\*/', '', css, flags=re.S)


def blocs(css):
    """Découpe une feuille en (prélude, corps) de premier niveau.

    Un analyseur complet serait hors sujet ; il suffit de suivre les
    accolades pour distinguer une règle d'une at-règle qui en contient.
    """
    css = sans_commentaires(css)
    out, depart, profondeur, debut_corps = [], 0, 0, None
    for i, c in enumerate(css):
        if c == '{':
            profondeur += 1
            if profondeur == 1:
                debut_corps = i
        elif c == '}':
            profondeur -= 1
            if profondeur == 0:
                out.append((css[depart:debut_corps].strip(), css[debut_corps + 1:i]))
                depart = i + 1
    return out


def classes_de(html):
    """Toutes les classes portées par un fragment de HTML."""
    vues = set()
    for attribut in re.findall(r'class="([^"]*)"', html):
        vues |= set(attribut.split())
    return vues - INTOUCHABLES


def _renomme_selecteur(selecteur, classes):
    def un(m):
        return '.' + PREFIXE + m.group(1) if m.group(1) in classes else m.group(0)
    return re.sub(r'\.([A-Za-z_][\w-]*)', un, selecteur)


def _touche(selecteur, classes):
    return any(c in classes for c in re.findall(r'\.([A-Za-z_][\w-]*)', selecteur))


def regles_utiles(css, classes, dans_media=False):
    """Les règles de cette feuille qui parlent des classes du corps repris.

    Les at-règles sont suivies : une largeur d'écran qui change la grille
    compte autant que la grille elle-même — sans elles, le corps repris
    serait juste sur un grand écran et cassé sur un téléphone.
    """
    gardees = []
    for selecteur, corps in blocs(css):
        if selecteur.startswith('@'):
            if selecteur.startswith(('@media', '@supports', '@container')):
                dedans = regles_utiles(corps, classes, True)
                if dedans:
                    gardees.append('%s{%s}' % (selecteur, ''.join(dedans)))
            continue
        parts = [p.strip() for p in selecteur.split(',') if p.strip()]
        retenus = [_renomme_selecteur(p, classes) for p in parts if _touche(p, classes)]
        if retenus:
            gardees.append('%s{%s}' % (','.join(retenus), corps.strip()))
    return gardees


def renommer(html, classes):
    """Renomme, dans le HTML, les classes retenues — et elles seules."""
    def un(m):
        jetons = [PREFIXE + x if x in classes else x for x in m.group(1).split()]
        return 'class="%s"' % ' '.join(jetons)
    return re.sub(r'class="([^"]*)"', un, html)


def greffer(corps, css_source):
    """Rend (corps renommé, feuille à poser). Le corps garde son allure."""
    classes = classes_de(corps)
    if not classes:
        return corps, ''
    regles = regles_utiles(css_source, classes)
    if not regles:
        return corps, ''
    return renommer(corps, classes), (
        '<style data-greffe="rp">\n/* Habillage d’origine du contenu repris — '
        'voir outils/greffe-css.py */\n%s\n</style>' % '\n'.join(regles))


def variables_manquantes(feuille, css_hote):
    """Les variables que la greffe emploie et que l'hôte ne définit pas.

    Une règle reprise qui appelle « var(--lat-fond) » alors que le gabarit
    ne connaît pas ce nom ne casse rien de visible : la propriété est
    simplement ignorée, et le bloc perd son fond sans que personne le
    remarque. Autant le dire tout haut.
    """
    voulues = set(re.findall(r'var\(\s*(--[\w-]+)', feuille))
    connues = set(re.findall(r'(--[\w-]+)\s*:', css_hote))
    return sorted(voulues - connues)
