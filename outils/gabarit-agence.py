#!/usr/bin/env python3
"""
Monte la page agence sur l'ordre des sections relevé chez les concurrents.

    ./outils/gabarit-agence.py --moule FICHIER --site DIR --sortie DIR [--essai]

L'ordre ne vient pas d'une intuition : il est relevé sur sept agences qui se
positionnent en France sur « agence de voyage égypte francophone », « agence
locale egypte » et « voyage sur mesure egypte agence » — Voyageurs du Monde,
Terres Égyptiennes, Cheops Travel, Altaï Egypt, Égypte Éthique, Égypte
Voyages, Étendues Sauvages. Vingt-six pages ouvertes.

Ce que le marché impose (au moins quatre agences sur sept) : accroche,
approche en piliers, engagements, garanties, bureaux, équipe nommée,
assistance, appel au devis. Ce qui distingue : la presse — AUCUN des sept
concurrents n'en a, et Authentique Égypte a Le Figaro deux fois, Marie
Claire, Evaneos, Partir.com, TripAdvisor. Elle remonte donc de la septième
place à la troisième.

Deux règles tiennent ce fichier.

Rien n'est écrit qui ne soit déjà publié par l'agence. Chaque bloc dit d'où
il vient. Ce qui manque est marqué « à remplir » et reste visible comme tel :
un trou signalé se comble, un trou masqué se découvre en production.

Et AUCUNE garantie n'est affichée sans preuve. Immatriculation Atout France,
garantie financière APST, responsabilité civile professionnelle, numéro de
licence égyptienne : tant que l'agence n'a pas confirmé qu'elles existent,
la page n'en dit pas un mot. Afficher une garantie qu'on n'a pas est une
mention trompeuse, et c'est le genre de ligne qu'un gabarit ajoute sans que
personne ne la relise.
"""

import argparse
import html as H
import os
import re
import sys
from importlib.machinery import SourceFileLoader

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_circ = SourceFileLoader('gabarit_circuit',
                         os.path.join(RACINE, 'outils', 'gabarit-circuit.py')).load_module()
_bleu = SourceFileLoader('bleu_unique',
                         os.path.join(RACINE, 'outils', 'bleu-unique.py')).load_module()

SIRET = '928 008 226 00013'
SIEGE = '17 Avenue Gambetta, 82000 Montauban, France'
MENTIONS = 'https://authentiquegypte.com/mentions-legales-agence-voyage-egypte/'

# Ce que l'agence seule peut fournir. Marqué sur la page, pas deviné.
A_REMPLIR = {
    'fondation': 'année de création de l’agence',
    'voyageurs': 'nombre de voyageurs accompagnés',
    'equipe': 'photos et biographies de l’équipe',
    'licence': 'numéro de licence touristique égyptienne et nom du partenaire qui la détient',
    'garanties': 'immatriculation Atout France, garantie financière, responsabilité civile '
                 '— à vérifier avant toute publication',
    'delai': 'délai réel d’envoi du premier devis',
    'tarif': 'formulation de l’engagement tarifaire',
    'bureau': 'adresse du bureau du Caire, si elle est communicable',
}


def texte(x):
    return re.sub(r'\s+', ' ', H.unescape(re.sub(r'<[^>]+>', ' ', x))).strip()


def a_remplir(cle):
    return ('<p class="atelier"><span class="aremplir">à remplir</span> %s</p>'
            % H.escape(A_REMPLIR[cle]))


def source(url, quoi):
    return ('<p class="prov">Repris de <a href="%s" target="_blank" rel="noopener">%s</a>.</p>'
            % (url, H.escape(quoi)))


def bloc_apres(h, ancre, fin='</section>'):
    """Le morceau de page qui suit un titre, jusqu'à la fin de sa section.

    Deux bornes, apprises d'un premier montage où « Votre projet » revenait
    huit fois : on s'arrête au prochain titre de même niveau, et on retire les
    appels au devis emportés au passage — le gabarit en pose un seul, à la fin.
    """
    i = h.find('>' + ancre)
    if i < 0:
        return ''
    debut = h.rfind('<', 0, i)
    j = h.find(fin, debut)
    bloc = h[debut:j + len(fin)] if j > 0 else h[debut:debut + 1600]

    # Pas de borne sur les titres : la section « équipe » enchaîne quatre H3
    # de même niveau — un titre de bloc puis ses trois sous-blocs — et s'y
    # arrêter perdait « Des experts passionnés par leur pays », « Connaissant
    # parfaitement le terrain » et « À taille humaine et authentiques ».
    # C'est le retrait des appels au devis, plus bas, qui réglait le doublon.
    for motif in (r'<section[^>]*>(?:(?!</section>).)*?<div class="devis">.*?</section>',
                  r'<div class="devis">.*?</div>\s*</div>\s*</div>'):
        bloc = re.sub(motif, '', bloc, flags=re.S)
    return bloc


def section(surtitre, titre, corps, fond=False):
    return ('<section class="pg-sec%s"><div class="wrap">'
            '<p class="eyebrow">%s</p><h2>%s</h2>%s</div></section>'
            % (' pg-sec--fond' if fond else '', H.escape(surtitre), H.escape(titre), corps))


def accroche(agence):
    """La phrase de positionnement, qui suit le H1 sur la page actuelle.

    « Notre structure franco-égyptienne s'appuie sur des années de terrain… »
    Sept agences sur sept en ont une : c'est la section la plus universelle du
    marché, et la seule chose que la page dit d'elle-même avant d'entrer dans
    le détail. Une première version la perdait — elle ne vit ni dans un chapô
    ni dans une section, seulement collée sous le titre.
    """
    m = re.search(r'Agence francophone en Égypte\s*</[^>]+>\s*<([a-z]+)[^>]*>(.*?)</\1>',
                  agence, re.S)
    if m and 'franco-égyptienne' in m.group(2):
        return texte(m.group(2))
    m = re.search(r'(Notre structure franco-égyptienne[^<]{40,400})', agence)
    return H.unescape(m.group(1)).strip() if m else ''


def monter(moule, agence, accueil):
    """Les treize sections, dans l'ordre du marché."""
    s = []
    phrase = accroche(agence)

    # 2. Les chiffres. Seul celui qui est publié sur le site est affiché.
    avis = re.search(r'(\d+)\s+avis Google', agence) or re.search(r'(\d+)\s+avis Google', accueil)
    chiffres = ''
    if avis:
        chiffres += ('<p class="chiffres"><b>%s <span>avis Google</span></b></p>'
                     % H.escape(avis.group(1)))
    tete_bref = '<p class="lede">%s</p>' % H.escape(phrase) if phrase else ''
    s.append(section('En bref', 'L’agence en quelques repères',
                     tete_bref + chiffres + a_remplir('fondation') + a_remplir('voyageurs')))

    # 3. L'histoire, telle qu'elle est écrite. La date manque.
    hist = bloc_apres(agence, 'Notre histoire')
    if hist:
        s.append(section('Notre histoire', 'Une aventure née d’un regard curieux',
                         hist + a_remplir('fondation'), fond=True))

    # 4. Les trois piliers, rapatriés de l'accueil où ils sont déjà rédigés.
    piliers = bloc_apres(accueil, 'Privées')
    if piliers:
        s.append(section('Notre approche', 'Ce qui fait un voyage avec nous',
                         piliers + source('https://authentiquegypte.com/',
                                          'la page d’accueil du site')))

    # 5. L'équipe. Le manque le plus net face au marché : quatre agences et
    #    demie sur sept montrent des visages et des noms, la page n'en a aucun.
    eq = bloc_apres(agence, 'Une équipe locale engagée')
    s.append(section('Qui vous répond', 'Notre équipe', eq + a_remplir('equipe'), fond=True))

    # 6. La méthode. Rare sur le marché — une agence et demie sur sept.
    meth = bloc_apres(agence, 'Contact initial')
    if meth:
        s.append(section('Comment ça se passe', 'De votre premier message au départ',
                         meth + a_remplir('delai')))

    # 7. Les engagements.
    eng = bloc_apres(agence, 'Des voyages flexibles')
    if eng:
        s.append(section('Nos engagements', 'Un voyage local, souple et respectueux',
                         eng + a_remplir('tarif'), fond=True))

    # 8. Les garanties. Uniquement ce qui est publié aux mentions légales.
    juridique = ('<ul class="garanties">'
                 '<li><b>Authentique Égypte (OREYA)</b></li>'
                 '<li>SIRET&nbsp;: %s</li>'
                 '<li>Siège social&nbsp;: %s</li></ul>%s'
                 % (H.escape(SIRET), H.escape(SIEGE),
                    source(MENTIONS, 'les mentions légales du site')))
    s.append(section('Garanties', 'Qui nous sommes, juridiquement',
                     juridique + a_remplir('licence') + a_remplir('garanties')))

    # 9. Les bureaux.
    s.append(section('Où nous trouver', 'Nos bureaux',
                     a_remplir('bureau'), fond=True))

    # 10. La presse : l'atout que personne n'a. Elle remonte.
    presse = bloc_apres(agence, 'Le Figaro', fin='</section>')
    if presse:
        s.append(section('Ils parlent de nous', 'La presse et les plateformes', presse))

    # 11. Les avis, 12. la FAQ, 13. l'appel au devis : pris au moule, qui les
    #     porte déjà dans la forme validée.
    for debut in ('Ce que disent', 'Ce séjour vous tente'):
        bloc = moule.section_par_h2(debut)
        if not bloc:
            continue
        # Le moule conclut sur « Ce séjour vous tente ? » : il n'y a pas de
        # séjour sur une page agence.
        bloc = re.sub(r'(<h2[^>]*>)Ce séjour vous tente[^<]*(</h2>)',
                      lambda m: '%sParlons de votre projet.%s' % (m.group(1), m.group(2)),
                      bloc)
        s.append(bloc)
    faq = bloc_apres(agence, 'FAQ - Questions')
    if faq:
        s.insert(-1, section('Avant de nous écrire', 'Les questions qu’on nous pose',
                             faq, fond=True))
    return s


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--moule', required=True)
    p.add_argument('--site', required=True)
    p.add_argument('--sortie', required=True)
    p.add_argument('--essai', action='store_true')
    a = p.parse_args()

    src = os.path.abspath(a.site)
    moule = _circ.Moule(os.path.abspath(a.moule))
    with open(os.path.join(src, 'agence-qui-sommes-nous.html'), encoding='utf-8') as f:
        agence = f.read()
    accueil = ''
    for nom in os.listdir(src):
        if nom.startswith('accueil-'):
            with open(os.path.join(src, nom), encoding='utf-8') as f:
                accueil = f.read()

    page = _circ.lire_page(agence)
    tete = _circ.poser_tete(moule.tete, page, 'Agence')
    corps = monter(moule, agence, accueil)
    h = _bleu.unifier(tete + ''.join(corps) + moule.pied)

    manquants = len(re.findall(r'class="aremplir"', h))
    print('→ %d section(s) montées, %d emplacement(s) « à remplir »' % (len(corps), manquants))
    for cle, quoi in A_REMPLIR.items():
        print('   %-11s %s' % (cle, quoi))
    print('\nAucune garantie affichée sans preuve : ni Atout France, ni APST, ni RCP,')
    print('ni numéro de licence — tant que l’agence ne les a pas confirmés.')
    if not a.essai:
        os.makedirs(a.sortie, exist_ok=True)
        with open(os.path.join(a.sortie, 'agence-qui-sommes-nous.html'), 'w',
                  encoding='utf-8') as f:
            f.write(h)
        print('\nécrit %s (%d octets)' % (a.sortie, len(h)))


if __name__ == '__main__':
    main()
