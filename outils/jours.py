#!/usr/bin/env python3
"""Éditer le « jour par jour » d'une page de séjour sans casser le balisage.

Une journée vit à trois endroits : le sommaire (nav.jpjs), le bloc
div.jour#jour-N et son article.etape#etape-N. Ces fonctions les tiennent
ensemble : changer le titre d'un jour change aussi sa ligne du sommaire ;
ajouter un jour ajoute aussi sa ligne.

Les pastilles (repas, hébergement) reprennent les icônes déjà présentes
sur le site, relevées dans outils/jico.json. Une pastille dont le libellé
commence par « option: » est rendue comme option (bordure pointillée).

Tout passe par des chaînes : on lit la page brute, on rend la page brute.
Chaque fonction lève une erreur si ce qu'elle cherche n'est pas là, pour
qu'un script s'arrête plutôt que d'écrire une page à moitié modifiée.
"""

import json
import os
import re

ICI = os.path.dirname(os.path.abspath(__file__))
ICONES = json.load(open(os.path.join(ICI, 'jico.json'), encoding='utf-8'))
# Les libellés nouveaux prennent l'icône d'un libellé voisin.
PARENTE = {
    'Pension complète': 'Dîner',
    'Tout inclus à bord, sauf boissons': 'Bateau de croisière 5*',
    'Hôtel 5* ou hôtel boutique': 'Hôtel',
    'Hôtel 5* ou hôtel boutique à Hurghada': 'Hôtel 5* à Hurghada',
}


class Absent(Exception):
    pass


def bornes(h, debut_balise, nom):
    """(début, fin) de l'élément qui commence à debut_balise, profondeur comptée."""
    i = h.find(debut_balise)
    if i < 0:
        raise Absent(debut_balise)
    p, k = 0, i
    ouvre, ferme = '<' + nom, '</' + nom + '>'
    while k < len(h):
        if h.startswith(ouvre, k) and h[k + len(ouvre)] in ' >':
            p += 1
        elif h.startswith(ferme, k):
            p -= 1
            if p == 0:
                return i, k + len(ferme)
        k += 1
    raise Absent('fin de ' + debut_balise)


def jour(h, n):
    return bornes(h, '<div class="jour" id="jour-%d">' % n, 'div')


def nb_jours(h):
    return len(re.findall(r'<div class="jour" id="jour-\d+">', h))


def _dans_jour(h, n, fonction):
    a, b = jour(h, n)
    bloc = fonction(h[a:b])
    return h[:a] + bloc + h[b:]


def texte(html):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', html)).strip()


# --------------------------------------------------------------- titres
def titre(h, n, html):
    """Titre du jour (h3) et sa ligne du sommaire."""
    def f(bloc):
        nouveau, k = re.subn(r'<h3>.*?</h3>', '<h3>%s</h3>' % html, bloc, count=1, flags=re.S)
        if not k:
            raise Absent('h3 du jour %d' % n)
        return nouveau
    h = _dans_jour(h, n, f)
    h, k = re.subn(r'(<a href="#jour-%d">).*?(</a>)' % n,
                   lambda m: m.group(1) + texte(html) + m.group(2), h, count=1)
    return h


def sous_titre(h, n, html):
    """h4.etape__t ; None le retire, et on le crée s'il manque."""
    def f(bloc):
        if re.search(r'<h4 class="etape__t">', bloc):
            if html is None:
                return re.sub(r'<h4 class="etape__t">.*?</h4>', '', bloc, count=1, flags=re.S)
            return re.sub(r'<h4 class="etape__t">.*?</h4>', '<h4 class="etape__t">%s</h4>' % html,
                          bloc, count=1, flags=re.S)
        if html is None:
            return bloc
        return bloc.replace('<ul class="etape__pts">', '<h4 class="etape__t">%s</h4><ul class="etape__pts">' % html, 1)
    return _dans_jour(h, n, f)


# --------------------------------------------------------------- étapes
def li(t):
    """« option: … » devient une ligne d'option, le reste une ligne simple."""
    if t.startswith('option:'):
        return '<li class="etape__opt"><span class="etape__eti">En option</span>%s</li>' % t[7:].strip()
    return '<li>%s</li>' % t


def points(h, n, lignes):
    def f(bloc):
        nouveau, k = re.subn(r'<ul class="etape__pts">.*?</ul>',
                             '<ul class="etape__pts">%s</ul>' % ''.join(li(t) for t in lignes),
                             bloc, count=1, flags=re.S)
        if not k:
            raise Absent('liste du jour %d' % n)
        return nouveau
    return _dans_jour(h, n, f)


def lire_points(h, n):
    a, b = jour(h, n)
    m = re.search(r'<ul class="etape__pts">(.*?)</ul>', h[a:b], re.S)
    return re.findall(r'<li[^>]*>(.*?)</li>', m.group(1), re.S) if m else []


# --------------------------------------------------------------- pastilles
def pastille(lib):
    opt = lib.startswith('option:')
    lib = lib[7:].strip() if opt else lib
    cle = lib if lib in ICONES else PARENTE.get(lib, 'Hôtel')
    svg = ICONES.get(cle) or ICONES['Hôtel']
    if opt:
        return '<span class="jico__e" data-opt>%s<em>En option :</em> %s</span>' % (svg, lib)
    return '<span class="jico__e">%s%s</span>' % (svg, lib)


def pastilles(h, n, libelles, hebergement=None):
    """Remplace les pastilles du jour. hebergement : texte de la ligne
    « Hébergement » (etape__meta) ; '' la retire, None n'y touche pas."""
    def f(bloc):
        neuf = '<p class="jico">%s</p>' % ''.join(pastille(x) for x in libelles) if libelles else ''
        if '<p class="jico">' in bloc:
            bloc = re.sub(r'<p class="jico">.*?</p>', neuf, bloc, count=1, flags=re.S)
        else:
            i = bloc.rfind('</article>')
            bloc = bloc[:i] + neuf + bloc[i:]
        if hebergement is not None:
            m = re.search(r'<p class="etape__meta">.*?</p>', bloc, re.S)
            if m and hebergement == '':
                bloc = bloc[:m.start()] + bloc[m.end():]
            elif m:
                bloc = bloc[:m.start()] + re.sub(r'<i>.*?</i>', '<i>%s</i>' % hebergement, m.group(0), count=1, flags=re.S) + bloc[m.end():]
        return bloc
    return _dans_jour(h, n, f)


# --------------------------------------------------------------- photo
def sans_photo(h, n):
    def f(bloc):
        return re.sub(r'<a class="etape__photo".*?</a>', '', bloc, count=1, flags=re.S)
    return _dans_jour(h, n, f)


# --------------------------------------------------------------- jours
def ajouter_jour(h, titre_html, lignes, libelles, lieu, sous=None):
    """Ajoute un jour après le dernier, sans photo, et sa ligne au sommaire."""
    n = nb_jours(h) + 1
    a, b = jour(h, n - 1)
    bloc = ('<div class="jour" id="jour-%d"><div class="jour__tete"><h3>%s</h3>'
            '<span class="jour__no">Jour %d</span></div><article class="etape" id="etape-%d" '
            'data-lieu="%s">%s<ul class="etape__pts">%s</ul>%s</article></div>'
            % (n, titre_html, n, n, lieu,
               '<h4 class="etape__t">%s</h4>' % sous if sous else '',
               ''.join(li(t) for t in lignes),
               '<p class="jico">%s</p>' % ''.join(pastille(x) for x in libelles) if libelles else ''))
    h = h[:b] + bloc + h[b:]
    i = h.find('<ol class="jpjs__l">')
    if i >= 0:
        j = h.find('</ol>', i)
        h = h[:j] + '<li><span class="jpjs__n">J%d</span><a href="#jour-%d">%s</a></li>' % (n, n, texte(titre_html)) + h[j:]
    return h


def retirer_section(h, eyebrow):
    """Retire la <section> dont le surtitre est eyebrow. Rend (h, retirée ?)."""
    i = h.find('<p class="eyebrow">%s</p>' % eyebrow)
    if i < 0:
        return h, False
    s = h.rfind('<section', 0, i)
    a, b = bornes(h[s:], h[s:s + 9], 'section')
    return h[:s] + h[s + b:], True
