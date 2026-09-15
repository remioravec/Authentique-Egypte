#!/usr/bin/env python3
"""
Rend à « Nos séjours » la liste de séjours qu'elle avait perdue.

    ./outils/sejours-manquants.py --site DIR [--essai]

La page « Nos séjours » est la porte d'entrée du catalogue : en ligne, elle
affiche treize séjours. Dans la refonte, elle n'en affichait aucun — hero,
repères, puis directement la FAQ. C'est la page la plus visitée de la
famille, et c'était un trou.

Rien n'est fabriqué. Chaque carte posée ici est reprise TELLE QUELLE d'une
page catégorie sœur, qui la porte déjà : même image, même titre, même
durée, même prix, même adresse. La page « Nos séjours » réunit ce que ses
cinq sœurs montrent séparément, et deux cartes qui mènent au même séjour
n'y figurent qu'une fois.

L'outil ne fait rien si la page porte déjà des cartes : il répare un
manque, il ne remplace pas un choix.
"""

import argparse
import html as H
import os
import re
import sys

CIBLE = 'famille-nos-sejours-egypte.html'
SOEURS = 'famille-'


def _texte(x):
    return re.sub(r'\s+', ' ', H.unescape(re.sub(r'<[^>]+>', ' ', x))).strip()


def cartes_des_soeurs(source):
    """Les cartes séjour que portent les autres pages catégorie.

    Dédoublonnées sur l'adresse du séjour : « Pyramides et croisière sur le
    Nil » apparaît sous les croisières et sous le voyage culturel, mais ne
    doit apparaître qu'une fois dans la liste complète. La première
    rencontrée l'emporte, dans l'ordre alphabétique des pages, pour que le
    résultat ne dépende pas de l'ordre de lecture du système de fichiers.
    """
    vues, cartes = {}, []
    for nom in sorted(os.listdir(source)):
        if not nom.startswith(SOEURS) or nom == CIBLE or not nom.endswith('.html'):
            continue
        with open(os.path.join(source, nom), encoding='utf-8') as f:
            h = f.read()
        for m in re.finditer(r'<article class="carte".*?</article>', h, re.S):
            lien = re.search(r'href="(https://authentiquegypte\.com/programs/[^"]+)"',
                             m.group(0))
            if not lien or lien.group(1) in vues:
                continue
            vues[lien.group(1)] = nom
            cartes.append((lien.group(1), m.group(0), nom))
    return cartes


def carte_de_fiche(chemin, modele):
    """Une carte pour un séjour qu'aucune page sœur ne montre.

    Quatre fiches n'apparaissent sur aucune page catégorie : la Nubie, le
    roadtrip, « Pyramides, Louxor et mer rouge » et le lever du soleil à
    Sainte-Catherine. Les omettre de la liste complète serait rendre une
    page qui reste fausse — moins fausse, mais fausse.

    La carte est donc bâtie sur le modèle des autres, et chacune de ses
    valeurs — titre, image, durée, prix, adresse — est lue sur la fiche
    elle-même. Ce que la fiche ne dit pas n'est pas écrit : sans prix, la
    carte porte « Prix sur devis », la mention que les dix autres cartes
    emploient déjà dans ce cas.
    """
    with open(chemin, encoding='utf-8') as f:
        g = f.read()
    slug = os.path.basename(chemin)[len('programme-'):-len('.html')]
    url = 'https://authentiquegypte.com/programs/%s/' % slug
    titre = re.search(r'<h1[^>]*>(.*?)</h1>', g, re.S)
    if not titre:
        return ''
    img = (re.search(r'<div class="hero__fond"><img ([^>]*)>', g)
           or re.search(r'<div class="chapeau__bg"><img ([^>]*)>', g))
    reperes = dict((_texte(a), _texte(b)) for a, b in re.findall(
        r'<li>(?:<svg.*?</svg>)?<small>(.*?)</small><b>(.*?)</b></li>', g, re.S))
    duree = next((v for k, v in reperes.items() if k.lower().startswith('dur')), '')
    prix = next((v for k, v in reperes.items() if k.lower().startswith('à partir')), '')

    # Le picto vient du modèle : la carte garde la forme des autres.
    picto = re.search(r'<svg[^>]*>.*?</svg>', modele, re.S)
    puces = ('<p class="carte__ch">Les étapes de votre séjour&nbsp;:</p>'
             '<ul class="carte__p"><li>%s<span>%s</span></li></ul>'
             % (picto.group(0) if picto else '', H.escape(duree))) if duree else ''
    return (
        '<article class="carte">'
        '%s'
        '<div class="carte__c">'
        '<h3><a href="%s">%s</a></h3>'
        '%s'
        '<div class="carte__b">%s'
        '<a class="btn btn--fantome btn--sm" href="%s">Voir le séjour</a>'
        '</div></div></article>'
        % ('<a class="carte__img" href="%s" tabindex="-1" aria-hidden="true">'
           '<img %s></a>' % (url, img.group(1)) if img else '',
           url, titre.group(1).strip(), puces,
           ('<span class="carte__prix"><small>À partir de</small><b>%s</b></span>'
            % H.escape(prix)) if prix else
           '<span class="carte__prix carte__prix--vide">Prix sur devis</span>',
           url))


def fiches_sans_carte(source, deja):
    """Les fiches séjour du dossier qu'aucune carte ne mène."""
    manquantes = []
    for nom in sorted(os.listdir(source)):
        if not nom.startswith('programme-') or not nom.endswith('.html'):
            continue
        slug = nom[len('programme-'):-len('.html')]
        if any(('/programs/%s/' % slug) in u or u.rstrip('/').endswith('/' + slug)
               for u in deja):
            continue
        manquantes.append(nom)
    return manquantes


def section(modele_source, cartes, titre):
    """La section « Au choix », bâtie sur celle d'une page sœur.

    On reprend son ouverture et sa fermeture — le surtitre, le titre, la
    note qui date les prix — pour que la page n'invente aucune forme : elle
    porte exactement la même section que ses sœurs, avec plus de cartes.
    """
    debut = modele_source.find('<article class="carte"')
    ouvre = modele_source.rfind('<section', 0, debut)
    if ouvre < 0:
        return ''
    dernier = modele_source.rfind('</article>')
    ferme = modele_source.find('</section>', dernier)
    if dernier < 0 or ferme < 0:
        return ''
    tete = modele_source[ouvre:debut]
    pied = modele_source[dernier + len('</article>'):ferme + len('</section>')]
    tete = re.sub(r'(<h2[^>]*>).*?(</h2>)',
                  lambda m: m.group(1) + H.escape(titre) + m.group(2), tete, count=1, flags=re.S)
    tete = re.sub(r'(<div class="cartes)[^"]*(">)',
                  lambda m: '%s cartes--4%s' % (m.group(1), m.group(2)), tete, count=1)
    return tete + ''.join(c for _, c, _ in cartes) + pied


def poser(h, bloc):
    """La liste va juste après les repères, là où elle est sur les sœurs."""
    m = re.search(r'<section class="[^"]*reperes[^"]*">.*?</section>', h, re.S)
    if not m:
        m = re.search(r'<nav class="ariane[^"]*"[^>]*>.*?</nav>', h, re.S)
    if not m:
        return h, False
    return h[:m.end()] + '\n' + bloc + h[m.end():], True


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--site', required=True)
    p.add_argument('--essai', action='store_true')
    a = p.parse_args()

    source = os.path.abspath(a.site)
    chemin = os.path.join(source, CIBLE)
    if not os.path.exists(chemin):
        raise SystemExit('%s est introuvable dans %s' % (CIBLE, source))
    with open(chemin, encoding='utf-8') as f:
        h = f.read()

    if '<article class="carte"' in h:
        print('→ %s porte déjà %d carte(s) : rien à faire.'
              % (CIBLE, len(re.findall(r'<article class="carte"', h))))
        return

    cartes = cartes_des_soeurs(source)
    if not cartes:
        raise SystemExit('aucune carte séjour trouvée sur les pages sœurs')

    modele = os.path.join(source, cartes[0][2])
    with open(modele, encoding='utf-8') as f:
        source_modele = f.read()
    manquantes = fiches_sans_carte(source, [u for u, _, _ in cartes])
    for nom in manquantes:
        neuve = carte_de_fiche(os.path.join(source, nom), cartes[0][1])
        if neuve:
            cartes.append(('https://authentiquegypte.com/programs/%s/'
                           % nom[len('programme-'):-len('.html')], neuve, nom))
    bloc = section(source_modele, cartes, 'Nos séjours')
    if not bloc:
        raise SystemExit('la page modèle %s n’a pas la forme attendue' % cartes[0][2])

    neuf, pose = poser(h, bloc)
    if not pose:
        raise SystemExit('pas de point d’insertion dans %s' % CIBLE)

    print('→ %d séjour(s) distincts, repris de %d page(s) sœur(s)'
          % (len(cartes), len({n for _, _, n in cartes})))
    for url, carte, nom in cartes:
        titre = re.search(r'<h3[^>]*>(.*?)</h3>', carte, re.S)
        print('   %-52s ← %s' % (_texte(titre.group(1))[:52] if titre else url[-40:],
                                 nom.replace('famille-', '').replace('.html', '')))
    if a.essai:
        print('\nEssai : rien n’a été écrit.')
        return
    with open(chemin, 'w', encoding='utf-8') as f:
        f.write(neuf)
    print('\n%s : %d octets → %d.' % (CIBLE, len(h), len(neuf)))


if __name__ == '__main__':
    main()
