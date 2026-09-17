#!/usr/bin/env python3
"""
Répare les défauts de contenu relevés par le contrôle du 15/09, sans arbitrage.

    ./outils/reparer-contenu.py --site DIR [--essai]

Ne touche qu'à ce qui est objectivement faux, c'est-à-dire vérifiable contre
la page en ligne ou contre le code lui-même. Tout ce qui demande une décision
éditoriale — les FAQ écrites hors source, les titres de section supprimés, les
promesses commerciales du bloc de conversion — est laissé en place et listé
en fin de passage, à trancher par l'agence.

Chaque réparation dit combien de fois elle s'est appliquée. Une réparation qui
ne s'applique nulle part est signalée : c'est qu'elle ne correspond plus à ce
que portent les pages, et qu'il faut la relire plutôt que la garder au chaud.
"""

import argparse
import os
import re

# ── ce qui est objectivement faux ────────────────────────────────────────

def visa(h):
    """Le prix du visa à l'arrivée : la page d'accueil du site dit 25 €.

    Relevé le 15/09 dans le HTML de https://authentiquegypte.com/ :
    « Oui, il peut être obtenu à l'arrivée (25 € en espèces ou CB) ou en
    ligne. » Vingt pages affichaient 30 €. C'est un chiffre du client, pas
    une formulation : il n'y a rien à arbitrer.
    """
    return re.subn(r'\(30 € en espèces ou CB\)', '(25 € en espèces ou CB)', h)


def inspecteur_maillage(h):
    """L'inspecteur de maillage, laissé allumé.

    C'est un outil de relecture interne : un bouton flottant et un encart qui
    commente les choix de maillage (« Questions sœurs placées après le bloc de
    conversion… »). Une règle `.mm-legende{display:block}` posée APRÈS la règle
    de base le laissait visible sur 27 pages. Le client lit donc les notes de
    travail au milieu de la page. On remet l'encart à l'état masqué ; le code
    reste, l'outil se rallume en changeant une règle.
    """
    return re.subn(r'\.mm-legende\{display:block\}', '.mm-legende{display:none}', h)


def shortcode(h):
    """« [trustindex no-registration=google] » affiché en clair.

    Un shortcode WordPress non interprété, recopié tel quel depuis la page en
    ligne où il est, lui, remplacé par le widget d'avis. Il n'existe sur
    aucune des pages sources : c'est du texte qui fuit dans le rendu.
    """
    return re.subn(r'\s*\[trustindex[^\]]*\]', '', h)


def image_vide(h):
    """Une balise <img src=""> : le navigateur affiche une icône cassée."""
    return re.subn(r'<img src=""[^>]*>', '', h)


def fleche_tronquee(h):
    """Le <path> de la flèche « Autres destinations », coupé en plein attribut.

    La génération a tranché le fichier au milieu de `stroke-linejoin="round"`,
    emportant avec elle la fermeture du <svg>, du lien, de la liste et des
    trois conteneurs qui suivent. Le navigateur avale tout ce qui suit comme
    un attribut du <path> — le titre « Les séjours qui passent par … » et la
    première carte séjour disparaissent à la lecture.

    On rétablit la fin de la flèche telle qu'elle est écrite partout ailleurs
    sur la même page, puis les fermetures manquantes.
    """
    # La coupure tombe n'importe où dans « stroke-width="2" stroke-linecap… » :
    # énumérer les préfixes possibles en couvrait six sur neuf. On prend tout
    # ce qui suit jusqu'au `</ul>` sans jamais traverser une balise.
    motif = re.compile(
        r'(<path d="M1 5\.5h12M9 1\.5l4 4-4 4" stroke="currentColor" )[^<>]*</ul>')
    fin = ('stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'
           '</svg></a></li></ul></div></div></aside></div></div>')
    return motif.subn(lambda m: m.group(1) + fin, h)


AVIS = re.compile(
    r'<article\b[^>]*>(?:(?!</?article\b).)*?<b>([^<]*)</b>Publié sur Google'
    r'(?:(?!</?article\b).)*?</article>', re.S)


def flux_google(fichiers, source):
    """Les auteurs du vrai flux d'avis, reconnus à leur présence partout.

    Le mur reprend la même fiche Google sur toutes les pages qui en portent
    un : ses dix auteurs reviennent donc sur chacune. Un « auteur » qui
    n'apparaît que sur une page n'est pas un avis, c'est du contenu de cette
    page tombé dans le mur — un chapeau éditorial, une question de FAQ, une
    ligne de matériel de trek (« ⛺ Couchage », « 🍳 Petit-déjeuner »).

    Ce critère se lit sur le corpus, pas sur un fichier : il fallait donc
    compter d'abord, réparer ensuite. Une première version jugeait l'auteur
    sur la forme de son nom, et proposait de retirer dix-sept entrées dont
    quatorze étaient de vrais avis mal découpés.
    """
    vus, murs = {}, 0
    for f in fichiers:
        with open(os.path.join(source, f), encoding='utf-8') as fh:
            h = fh.read()
        auteurs = {m.group(1).strip() for m in AVIS.finditer(h)}
        if not auteurs:
            continue
        murs += 1
        for a in auteurs:
            vus[a] = vus.get(a, 0) + 1
    return {a for a, n in vus.items() if murs and n >= .8 * murs}, murs


def faux_avis(h, flux):
    """La fausse attribution sort ; le texte reste.

    Attribuer à Google un texte que l'agence a écrit — son chapeau éditorial
    signé « Nos séjours en Égypte », son appel au devis signé « Demandez un
    Devis Personnalisé », une ligne de matériel de trek signée « ⛺ Couchage »
    — c'est un faux témoignage. Mais ces cartes portent du contenu réel : sur
    les quarante-huit blocs concernés, quarante-quatre contiennent un texte
    qui n'existe NULLE PART AILLEURS sur leur page. Les supprimer, comme une
    première version le faisait, effaçait le chapeau de « Nos séjours », la
    moitié de la FAQ du mont Moïse et les consignes de matériel du trek.

    On retire donc du pied de carte ce qui ment — le logo Google et la mention
    « Publié sur Google » — et le guillemet décoratif. L'étiquette, elle, reste :
    sur les cartes saisonnières du mont Moïse, c'est elle qui porte « ☀️ Été
    (juin – août) », et la retirer laissait des températures sans saison.

    Reste un défaut de structure : ces cartes sont du contenu de page avalé
    par le mur d'avis. Les remettre à leur place demande de reprendre le
    générateur, pas de retoucher les pages.
    """
    faux = 0

    def _bloc(m):
        nonlocal faux
        if m.group(1).strip() in flux:
            return m.group(0)
        faux += 1
        carte = re.sub(r'<span class="ini ini--g">.*?</span>\s*(?=<span><b>)', '',
                       m.group(0), flags=re.S)
        carte = carte.replace('</b>Publié sur Google</span>', '</b></span>')
        return re.sub(r'<span class="mur__q"[^>]*>.*?</span>', '', carte, flags=re.S)

    return AVIS.sub(_bloc, h), faux


def titre_accueil(h):
    """Le H1 de l'accueil et celui de l'agence, remplacés par un libellé.

    « HOME » et « Qui sommes nous » sont des entrées de menu, pas des titres
    de page. Le site en ligne écrit « Voyage sur mesure en Egypte » et
    « Agence francophone en Égypte ».
    """
    n = 0
    for faux, vrai in (('HOME', 'Voyage sur mesure en Egypte'),
                       ('Qui sommes nous', 'Agence francophone en Égypte')):
        h, k = re.subn(r'(<h1[^>]*>)%s(</h1>)' % re.escape(faux),
                       r'\g<1>%s\g<2>' % vrai, h)
        n += k
    return h, n


def duree_detournee(h):
    """« 45 jours conseillés » sur l'accueil.

    Le chiffre vient de la FAQ : « le solde 45 jours avant le départ ». Un
    délai de paiement présenté comme une durée de séjour recommandée. La
    pastille sort ; aucune durée conseillée n'est écrite pour l'accueil.
    """
    return re.subn(r'\s*<[^>]*>\s*45 jours\s*(?:conseillés?)?\s*</[^>]*>', '', h)


# Un « .*? » suffisait à croire bien faire : faute de lui interdire de
# franchir un </h2>, il traversait trois sections pour atteindre le premier
# titre suivi d'un paragraphe nu, et comparait des blocs qui n'existaient pas.
BLOC_REPETE = re.compile(
    r'<h2[^>]*>(?:(?!</h2>).)*</h2>(?:\s*<p class="">(?:(?!</p>).)*</p>)+', re.S)


def titres_colonne(h):
    """Les titres de la colonne latérale passent de h4 à h3.

    La page pose des h2, puis la colonne latérale ouvre en h4 : le niveau
    h3 est sauté. Pour un lecteur d'écran, un niveau sauté veut dire qu'un
    titre manque — il annonce une section qui n'existe pas. Le rendu ne
    change pas d'un pixel : c'est la feuille qui décide de la taille, pas
    la balise.
    """
    # Le compteur porte sur les TITRES convertis, pas sur les blocs
    # parcourus : « re.subn » sur les <aside> comptait une substitution même
    # quand le remplacement était identique à l'original, et annonçait
    # soixante-huit corrections à chaque passage, y compris sur une page
    # déjà corrigée.
    n = [0]

    def dans_aside(m):
        bloc, k = re.subn(r'<h4([^>]*)>(.*?)</h4>', r'<h3\1>\2</h3>',
                          m.group(0), flags=re.S)
        n[0] += k
        return bloc

    return re.sub(r'<aside\b.*?</aside>', dans_aside, h, flags=re.S), n[0]


def contraste_pied(h):
    """Contraste, plancher typographique et cibles tactiles — le bloc commun.

    Aucune règle ne leur donnait de couleur : ils prenaient donc le noir par
    défaut du navigateur, sur le fond #095360 du pied. Mesuré sur le rendu :
    2,42:1, pour un seuil WCAG AA de 4,5:1 à cette taille. En blanc, 9,8:1.
    Le défaut est sur les cinquante-sept pages, la page de référence
    comprise — il ne vient pas de la refonte, il y était déjà.
    """
    if 'data-reparation="ae-1"' in h:
        return h, 0
    regle = (
        # Mesures faites sur le rendu, pas sur la règle : c'est la couleur
        # réellement composée à l'écran qui compte, pas celle qu'on déclare.
        '.pied h3{color:#fff}'                 # 2,42:1 → 8,69:1
        '.pied span{color:#B9DADF}'            # 4,33:1 → 5,86:1
        # Le gabarit pose « .pg .mur__q » : une règle de classe seule y perd,
        # et le guillemet restait or. Même portée, donc même poids.
        '.pg .mur__q,.mur__q{color:#7A5605}'   # 1,79:1 → 6,64:1 (seuil 3)
        # La pastille de durée des cartes manquait le seuil de seize
        # centièmes. Même teinte, même saturation : seule la clarté baisse,
        # pour que le bleu de marque reste le bleu de marque.
        '.puce{color:#137C8F}'                 # 4,34:1 → 4,64:1
        # ── Plancher typographique : 14 px, décision de Rémi du 17/09.
        # La charte descendait à 11,8 px sur « À partir de ». Ce sont des
        # étiquettes, jamais du texte courant, mais la règle d'accessibilité
        # ne fait pas cette distinction et le client a tranché.
        #
        # Deux précautions. La portée « .pg » est répétée parce que le
        # gabarit écrit « .pg .reperes small » : une règle de classe seule y
        # perd, et le premier jet n'a rien changé du tout. Et le préfixe
        # « rp- » — celui que la greffe pose sur le contenu repris — a sa
        # propre ligne, sans quoi le plancher s'arrêtait à la porte du corps
        # transplanté.
        '.pg small,.pg .reperes small,.pg .prix small,.pg .carte__prix small,'
        '.pg .tarif__ligne b small,.pg .devis__act small,.pied small,small'
        '{font-size:14px}'
        '.pg .eyebrow,.pg .eyebrow--clair,.eyebrow,.rp-eyebrow,'
        '.rp-eyebrow--clair{font-size:14px}'
        '.pg .puce,.pg .pill,.pg .pill b,.puce,.pill,.rp-puce,.rp-pill'
        '{font-size:14px}'
        '.pg .prix i,.pg .carte__prix i,.prix i,.rp-prix i{font-size:14px}'
        '.pg dl dt,.pg dl dd,.pg .somm b,.pg .som a,dl dt,dl dd,.rp-som a'
        '{font-size:14px}'
        '.pied span,.pied a,.pied li,.bandeau span,.bandeau strong,.bandeau a'
        '{font-size:14px}'
        # Le titre de la colonne latérale est passé de h4 à h3 pour ne plus
        # sauter de niveau. Sa mise en forme était accrochée à la balise :
        # sans ces deux lignes il reprenait la couleur des h3 du corps —
        # du bleu sur le bleu nuit de la carte, 2,42:1. On rend à la balise
        # ce que la précédente avait, à l'identique.
        '.lat__b h3,.rp-lat__b h3{font-family:"Archivo",sans-serif;'
        'font-size:1.05rem;font-weight:600;margin:0 0 13px;letter-spacing:-.4px}'
        '.lat--devis h3,.rp-lat--devis h3{color:#fff}'
        '.pg .ariane a,.pg .ariane li,.pg .ariane span,.ariane a,.ariane li,'
        '.ariane span{font-size:14px}'
        '.pg .carte__route,.carte__route,.rp-carte__route,.src,.rp-src,'
        '.cartes__src,.rp-cartes__src{font-size:14px}'
        # ── Cibles tactiles : au doigt, le seuil est 44 px. On n'agrandit
        # QUE sur pointeur grossier — la densité de la charte reste celle
        # prévue pour un écran. Les liens DANS une phrase sont laissés tels
        # quels : la règle les excepte, et les étirer casserait le texte.
        '@media (pointer:coarse){'
        '.lien-fl,.pied a,.ariane a,.bandeau a,.logo,.som a,.rp-som a,'
        '.carte__corps h3 a,.carte__c h3 a,.rp-carte__corps h3 a'
        '{min-height:44px;display:inline-flex;align-items:center}'
        '}')
    # Le bloc correctif se pose EN DERNIER, juste avant </head>, et pas dans
    # la première feuille venue : la greffe du contenu repris ajoute la
    # sienne après celle du gabarit, et à poids égal c'est la dernière qui
    # gagne. Posé trop tôt, le plancher s'arrêtait à la porte du corps
    # transplanté — « Poursuivre le voyage » restait à 12,5 px.
    feuille = '<style data-reparation="ae-1">%s</style>' % regle
    if '</head>' in h:
        return h.replace('</head>', feuille + '</head>', 1), 1
    return re.subn(r'(</style>)', lambda m: regle + m.group(1), h, count=1)


def bloc_repete(h):
    """Un même bloc titre + paragraphes, posé plusieurs fois sur la page.

    La page « qui sommes-nous » du site en ligne répète son appel au devis
    — « Voyagez autrement avec une agence qui vous met en lien… » — à la fin
    de chacune de ses parties. Reprise d'un bloc, la page de refonte le
    portait six fois de suite, le même titre et le même paragraphe, ce qui
    se lit comme un bug plutôt que comme une insistance.

    On ne compare pas des sens, on compare des octets : seules disparaissent
    les copies rigoureusement identiques à une occurrence précédente. Le
    premier exemplaire reste, et avec lui chaque mot du texte.
    """
    vus, coupes = set(), []
    for m in BLOC_REPETE.finditer(h):
        if m.group(0) in vus:
            coupes.append((m.start(), m.end()))
        else:
            vus.add(m.group(0))
    if not coupes:
        return h, 0
    sortie, pos = [], 0
    for debut, fin in coupes:
        sortie.append(h[pos:debut])
        pos = fin
    sortie.append(h[pos:])
    return ''.join(sortie), len(coupes)


def mur_avis_mobile(h):
    """Le mur d'avis n'est plus déplié en entier sur téléphone.

    La règle visait juste : sous 860 px, et pour qui demande moins
    d'animation, le défilement automatique du mur s'arrête. Mais en coupant
    l'animation elle a aussi retiré la hauteur de la fenêtre —
    « height:auto;overflow:visible » — et les soixante-dix-huit avis se
    sont empilés : 6 317 px d'avis à faire défiler au doigt, sur chacune
    des trente-cinq pages qui portent le mur, avant d'atteindre la suite.

    La fenêtre reprend une hauteur, et c'est elle qui défile, pas la page.
    L'animation reste arrêtée, le bouton reste caché : rien de l'intention
    d'origine n'est perdu.
    """
    return re.subn(
        r'\.pg \.mur__f\{height:auto;overflow:visible;'
        r'-webkit-mask-image:none;mask-image:none\}',
        '.pg .mur__f{height:min(70vh,560px);overflow-y:auto;'
        '-webkit-overflow-scrolling:touch;'
        '-webkit-mask-image:none;mask-image:none}', h)


REPARATIONS = [
    ('prix du visa 30 € → 25 €', visa),
    ('inspecteur de maillage remasqué', inspecteur_maillage),
    ('shortcode trustindex retiré', shortcode),
    ('balise <img src=""> retirée', image_vide),
    ('flèche et fermetures rétablies', fleche_tronquee),
    ('fausse attribution Google retirée', faux_avis),
    ('H1 de page rétabli', titre_accueil),
    ('durée détournée retirée', duree_detournee),
    ('mur d’avis replié sur mobile', mur_avis_mobile),
    ('bloc d’appel au devis en double retiré', bloc_repete),
    ('titres de colonne latérale en h3', titres_colonne),
    ('contraste, plancher 14 px, cibles tactiles', contraste_pied),
]

# ── ce qui demande un arbitrage, et qu'on ne touche donc pas ─────────────

A_TRANCHER = [
    ('FAQ écrites hors source', r'Institut Pasteur le conseille|assistance téléphonique '
     r'disponible|politiques de flexibilité|permis de circulation'),
    ('promesses du bloc de conversion', r'Acompte seulement une fois l.itinéraire validé'),
    ('libellé « Voir le détail »', r'Voir le détail'),
]


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--site', required=True)
    p.add_argument('--essai', action='store_true', help='montrer sans rien écrire')
    a = p.parse_args()

    source = os.path.abspath(a.site)
    # Les feuilles de style aussi : la règle qui rallumait l'inspecteur de
    # maillage vivait dans charte.css, intégrée ensuite dans chaque page. En ne
    # lisant que les .html, une première passe a corrigé les 27 copies et
    # laissé l'original, qui les a toutes réécrites au déploiement suivant.
    fichiers = sorted(f for f in os.listdir(source) if f.endswith(('.html', '.css')))
    compte = {nom: [0, 0] for nom, _ in REPARATIONS}      # [occurrences, pages]

    flux, murs = flux_google(fichiers, source)
    print('→ Mur d’avis : %d page(s) en portent un, %d auteur(s) présents sur '
          'toutes — c’est le flux Google.\n   %s\n'
          % (murs, len(flux), ', '.join(sorted(flux))))

    for f in fichiers:
        chemin = os.path.join(source, f)
        with open(chemin, encoding='utf-8') as fh:
            h = depart = fh.read()
        for nom, fonction in REPARATIONS:
            h, n = fonction(h, flux) if fonction is faux_avis else fonction(h)
            if n:
                compte[nom][0] += n
                compte[nom][1] += 1
        if h != depart and not a.essai:
            with open(chemin, 'w', encoding='utf-8') as fh:
                fh.write(h)

    print('→ Réparations%s' % (' (essai)' if a.essai else ''))
    for nom, _ in REPARATIONS:
        n, pages = compte[nom]
        etat = '%5d fois, %2d page(s)' % (n, pages) if n else '      — ne s’applique nulle part'
        print('   %-38s %s' % (nom, etat))
    muettes = [nom for nom, _ in REPARATIONS if not compte[nom][0]]
    if muettes:
        print('\nÀ relire : %s ne trouve(nt) plus rien. Soit c’est déjà corrigé,\n'
              'soit le motif ne correspond plus à ce que portent les pages.'
              % ', '.join('« %s »' % m for m in muettes))

    print('\n→ Laissé en place, à trancher par l’agence')
    for nom, motif in A_TRANCHER:
        touchees = [f for f in fichiers
                    if re.search(motif, open(os.path.join(source, f), encoding='utf-8').read())]
        print('   %-38s %2d page(s)' % (nom, len(touchees)))


if __name__ == '__main__':
    main()
