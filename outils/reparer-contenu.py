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
import html as H
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
VIDES = {'br', 'hr', 'img', 'input', 'meta', 'link', 'source', 'wbr',
         'col', 'area', 'base', 'embed', 'track', 'param'}


def equilibre(frag):
    """Vrai si le fragment ouvre et ferme exactement les mêmes balises.

    Un bloc qu'on retire doit se suffire : s'il emporte une fermeture sans
    son ouverture, la page se déforme à partir de là. On ne retire donc que
    des blocs équilibrés — c'est la seule garantie qui tienne sans analyser
    tout le document.
    """
    pile = []
    for m in re.finditer(r'<(/?)([A-Za-z][\w-]*)([^>]*)>', frag):
        fermant, nom = m.group(1), m.group(2).lower()
        if nom in VIDES or m.group(3).rstrip().endswith('/'):
            continue
        if not fermant:
            pile.append(nom)
        elif nom in pile:
            while pile and pile.pop() != nom:
                pass
        else:
            return False
    return not pile


def blocs_dupliques(h, minimum=700):
    """Un même bloc de contenu posé plusieurs fois dans la même page.

    La page agence en portait un de 3 514 octets, recopié quatre fois :
    l'histoire de Mélanie, l'équipe, les garanties, le bloc devis — tout
    revenait à l'identique d'une section à l'autre. Ce n'est pas de
    l'insistance, c'est un défaut de montage, et le lecteur le voit tout de
    suite.

    On ne compare pas des sens, on compare des octets : seules disparaissent
    les copies rigoureusement identiques à une occurrence précédente, et
    seulement si le bloc est équilibré. La première reste, et avec elle
    chaque mot du texte.
    """
    debut = h.find('<main')
    fin = h.find('<footer class="pied"')
    if debut < 0 or fin < 0:
        return h, 0
    corps, retires = h[debut:fin], 0

    def sous_boucle(position, texte):
        """Vrai si la position est dans un bloc dont la répétition est voulue.

        Le mur d'avis recopie ses cartes pour que le défilement boucle sans
        couture : les deux moitiés SONT identiques, et c'est le procédé, pas
        un défaut. Une première version retirait 6 786 octets d'avis sur
        chaque page et cassait l'animation. Même chose pour un carrousel.
        """
        for m in re.finditer(r'<div class="(?:mur|carrousel)[^"]*"', texte):
            profondeur, i = 0, m.start()
            for t in re.finditer(r'<(/?)div\b[^>]*>', texte[m.start():]):
                profondeur += 1 if not t.group(1) else -1
                if profondeur == 0:
                    i = m.start() + t.end()
                    break
            if m.start() <= position < i:
                return True
        return False

    for _ in range(12):        # quelques passes suffisent ; garde-fou
        vus, trouve = {}, None
        for m in re.finditer(r'<(?:section|div|article|aside|h[1-6])\b', corps):
            cle = corps[m.start():m.start() + minimum]
            if len(cle) < minimum:
                continue
            if sous_boucle(m.start(), corps):
                continue
            if cle in vus:
                trouve = (vus[cle], m.start())
                break
            vus[cle] = m.start()
        if not trouve:
            break
        a, b = trouve
        # La fenêtre identique s'étend des deux côtés. Ne l'étendre que vers
        # l'avant partait du milieu d'un conteneur : le bloc emportait un
        # </div> sans son ouverture, ne s'équilibrait jamais, et la page
        # agence gardait ses quatre copies malgré la détection.
        avant = 0
        while a - avant > 0 and b - avant > a and corps[a - avant - 1] == corps[b - avant - 1]:
            avant += 1
        apres = 0
        while b + apres < len(corps) and corps[a + apres] == corps[b + apres]:
            apres += 1
        fenetre = corps[b - avant:b + apres]
        decalage = b - avant

        # Dans cette fenêtre, on cherche le plus long fragment qui soit une
        # suite complète de frères — il commence sur une balise ouvrante et
        # se termine là où la pile des balises se vide.
        bloc, depart = '', 0
        for ouverture in [m.start() for m in
                          re.finditer(r'<[A-Za-z][\w-]*', fenetre)][:30]:
            pile, fin_eq = [], None
            for m in re.finditer(r'<(/?)([A-Za-z][\w-]*)([^>]*)>', fenetre[ouverture:]):
                fermant, nom = m.group(1), m.group(2).lower()
                if nom in VIDES or m.group(3).rstrip().endswith('/'):
                    continue
                if not fermant:
                    pile.append(nom)
                elif pile and nom in pile:
                    while pile and pile.pop() != nom:
                        pass
                    if not pile:
                        fin_eq = ouverture + m.end()
                else:
                    break
            if fin_eq and fin_eq - ouverture > len(bloc):
                bloc, depart = fenetre[ouverture:fin_eq], decalage + ouverture
        if len(bloc) < minimum:
            break
        b = depart

        corps = corps[:b] + corps[b + len(bloc):]
        retires += 1

    return (h[:debut] + corps + h[fin:], retires) if retires else (h, 0)


BLOC_REPETE = re.compile(
    r'<h2[^>]*>(?:(?!</h2>).)*</h2>(?:\s*<p class="">(?:(?!</p>).)*</p>)+', re.S)


# La feuille du composant « colonne latérale ». Elle vit dans le style des
# pages guide et n'a jamais été mise en commun : la page agence porte le
# balisage sans une seule règle pour le tenir. Relevée telle quelle sur
# guide-quand-partir-en-egypte.html, dont elle vient.
FEUILLE_LAT = '.lat{display:grid;gap:16px}.lat__b{background:#fff;border:1px solid var(--ligne);border-radius:var(--r-l);padding:22px;position:relative;overflow:hidden}.lat__b h4{font-family:"Archivo",sans-serif;font-size:1.04rem;font-weight:600;margin:0 0 12px;letter-spacing:-.4px}.lat__b ul{list-style:none;margin:0;padding:0;display:grid;font-family:"Manrope",sans-serif;font-size:.89rem}.lat__b li a{display:flex;align-items:center;justify-content:space-between;gap:10px;padding:10px 0;border-bottom:1px solid var(--ligne-2);color:var(--nuit-900);font-weight:600}.lat__b li:last-child a{border-bottom:0}.lat__b li a:hover{color:var(--teal-txt)}.lat__b li a svg{flex:0 0 auto;transition:transform .2s}.lat__b li a:hover svg{transform:translateX(3px)}.lat--devis{background:var(--nuit-900);border-color:var(--nuit-900);color:#C1D6D9}.lat--devis::before{content:"";position:absolute;top:0;left:0;right:0;height:4px;background:linear-gradient(90deg,var(--or),var(--or-clair))}.lat--devis h4{color:#fff}.lat--devis p{font-size:.9rem;margin-bottom:16px}@media (max-width:900px){.lat__b,.lat__b ul,.lat__b li a,.lat__b p,.lat__b h4{font-size:.95rem}.lat__b li a{min-height:44px;display:flex;align-items:center;}.lat__b li a{padding-top:9px;padding-bottom:9px}}.lat__b h3{font-family:"Archivo",sans-serif;font-size:1.05rem;font-weight:600;margin:0 0 13px;letter-spacing:-.4px}.lat--devis h3{color:#fff}'


# Le bleu de titre du site rendait 4,34:1 sur blanc — seize centièmes sous
# le seuil. Même teinte, même saturation, deux crans de clarté en moins.
# Un premier choix à #137C8F passait sur blanc (4,88:1) mais pas sur les
# fonds teintés du site — 4,42:1 sur le bleu pâle des aperçus. On descend
# donc au cran qui tient partout : 5,98:1 au pire, sur le fond le plus
# clair du site. Teinte et saturation inchangées.
BLEU_AVANT, BLEU_APRES = '#148194', '#116676'


def bleu_des_titres(h):
    """Corrige la VALEUR, pas les sélecteurs qui l'emploient.

    Une première approche listait les règles à reprendre une à une : à
    chaque passage la mesure en trouvait de nouvelles — « Le programme
    inclus », « TripAdvisor », les entêtes de tableau… La couleur est la
    même partout ; c'est elle qu'on remplace, une fois, dans la feuille.
    """
    n = 0
    for avant in (BLEU_AVANT, BLEU_AVANT.lower(), '#137C8F', '#137c8f',
                  'rgb(20, 129, 148)', 'rgb(20,129,148)'):
        n += h.count(avant)
        h = h.replace(avant, BLEU_APRES)
    return h, n


# Un plancher posé sur des sélecteurs se contourne tout seul : il suffit
# qu'une règle non listée descende plus bas. Posé sur les VALEURS, il tient.
PLANCHER_PX = 14.0
RACINE_PX = 16.0


def plancher_typo(h):
    """Remonte à 14 px toute taille de police déclarée en dessous.

    Les unités relatives sont converties sur la racine de 16 px du site —
    « .72rem » vaut 11,5 px et remonte à « .875rem ». On ne touche ni aux
    tailles déjà au-dessus du plancher, ni aux valeurs en pourcentage ou en
    mots-clés, qui dépendent d'un contexte qu'on ne peut pas lire ici.
    """
    n = [0]

    def une(m):
        valeur, unite = float(m.group(1)), m.group(2)
        px = valeur * (RACINE_PX if unite in ('rem', 'em') else 1)
        if unite not in ('px', 'rem', 'em') or px >= PLANCHER_PX:
            return m.group(0)
        n[0] += 1
        if unite == 'px':
            return 'font-size:%dpx' % PLANCHER_PX
        return 'font-size:%grem' % (PLANCHER_PX / RACINE_PX)

    return re.sub(r'font-size:\s*(\d*\.?\d+)(px|rem|em|%)', une, h), n[0]


# Les quatre fiches dont la refonte avait perdu le prix. Relevé sur les
# pages en ligne le 17 septembre 2026, avec leur mention « / Personne » :
#   /programs/campement-au-coeur-du-mont-moise/            290 €
#   /programs/decouverte-de-la-nubie/                      895 €
#   /programs/le-caire-et-croisiere-sur-un-bateau-a-voile/ 1895 €
#   /programs/roadtrip-en-egypte/                          1635 €
# Rien n'est calculé ni déduit : ce sont les montants que le site affiche.
PRIX_MANQUANTS = {
    'Coucher de soleil et nuit sur le mont Moïse': '290 €',
    'Découverte de la Nubie': '895 €',
    'Le Caire et croisière sur un bateau à voile': '1895 €',
    'Roadtrip en Égypte sur mesure': '1635 €',
}


def _texte(x):
    return re.sub(r'\s+', ' ', H.unescape(re.sub(r'<[^>]+>', ' ', x))).strip()


def prix_par_personne(h):
    """Le prix, par personne, visible sur chaque fiche séjour.

    Quatre fiches sur quatorze sortaient sans prix — sur les pages qui
    vendent. Et là où il apparaissait, le repère disait « À partir de »
    sans dire de quoi : le site en ligne précise « / Personne », la refonte
    l'avait laissé tomber.

    Le repère manquant est posé AVANT la durée, comme sur les dix autres
    fiches, pour que les quatorze se lisent de la même façon.
    """
    m = re.search(r'<section class="[^"]*reperes[^"]*">.*?</section>', h, re.S)
    if not m:
        return h, 0
    bloc, n = m.group(0), 0

    # Le libellé, sur toutes les fiches qui portent déjà un prix.
    bloc, k = re.subn(r'<small>À partir de</small>',
                      '<small>Par personne, à partir de</small>', bloc)
    n += k

    if '<small>Par personne' not in bloc:
        titre = re.search(r'<h1[^>]*>(.*?)</h1>', h, re.S)
        nom = _texte(titre.group(1)) if titre else ''
        prix = PRIX_MANQUANTS.get(nom)
        if prix:
            picto = re.search(r'<svg[^>]*>.*?</svg>', bloc, re.S)
            li = ('<li>%s<small>Par personne, à partir de</small><b>%s</b></li>'
                  % (picto.group(0) if picto else '', prix))
            bloc = bloc.replace('<ul>', '<ul>' + li, 1)
            n += 1
    return (h[:m.start()] + bloc + h[m.end():], n) if n else (h, 0)


def hero_sans_photo(h):
    """Les articles de blog n'ont plus de photo dans leur bandeau de titre.

    Demande de Rémi du 17/09 : pas d'image en avant sur les guides, et des
    images dans le corps seulement là où elles apportent quelque chose. Le
    bandeau ne perd rien à l'œil — il porte déjà un fond bleu nuit, et la
    photo vivait sous un dégradé à 94 % d'opacité qui la rendait presque
    invisible.

    On reconnaît un guide à son fil d'Ariane : « Guides pratiques ». C'est
    plus sûr que le nom du fichier, que cette fonction ne voit pas.
    """
    if 'Guides pratiques' not in h:
        return h, 0
    return re.subn(r'<div class="chapeau__bg">.*?</div>\s*', '', h, flags=re.S)


def bouton_annotations(h):
    """Le bouton d'annotation des maquettes n'a rien à faire sur une page montrée.

    « Annotations OFF » / « Maillage OFF », posé en bas à droite de
    quarante-quatre pages : c'est l'inspecteur qui sert à relire une
    maquette, pas un élément du site. Une passe précédente avait remasqué
    la légende qu'il révèle, mais laissé le bouton lui-même, qui reste
    donc visible et cliquable pour un visiteur.

    Le script qui l'écoute part avec lui : laissé seul, il cherche un
    élément absent et lève une erreur au chargement de chaque page.
    """
    n = 0
    h, k = re.subn(r'\s*<button class="mm-btn"[^>]*>.*?</button>', '', h, flags=re.S)
    n += k
    h, k = re.subn(r"\s*<script>\s*\(function\(\)\{\s*"
                   r"const b=document\.getElementById\('mm-btn'\);.*?</script>",
                   '', h, flags=re.S)
    n += k
    return h, n


def colonne_sans_style(h):
    """La colonne latérale rendue visible là où rien ne la stylait.

    Sur la page agence, le bloc « Un projet de voyage ? » sortait en texte
    blanc sur fond blanc — 1,00:1 — et sur toute la largeur de la page :
    le balisage avait été transplanté, pas la feuille qui va avec. Mesuré,
    c'était le défaut le plus grave de la page.

    On ne pose la feuille que si la page porte le balisage ET ne porte
    aucune règle pour lui : ailleurs, c'est celle de la page qui commande.
    """
    if 'class="lat__b' not in h or re.search(r'\.lat__b\s*\{', h):
        return h, 0
    feuille = '<style data-reparation="lat-1">%s</style>' % FEUILLE_LAT
    if '</head>' not in h:
        return h, 0
    return h.replace('</head>', feuille + '</head>', 1), 1


# Chaque entrée : où chercher, de quelle balise vers quelle balise. Un
# niveau de titre sauté annonce, pour un lecteur d'écran, une section qui
# n'existe pas — c'est le seul motif de ces échanges. Le texte ne bouge
# pas ; la feuille posée plus bas rend à la nouvelle balise l'apparence
# exacte de l'ancienne, faute de quoi le titre changerait de taille.
NIVEAUX = [
    (r'<nav class="som"[^>]*>', 'h4', 'h2'),          # « Sur cette page », juste après le h1
    (r'<footer class="pied"', 'h4', 'h3'),            # colonnes du pied, après un h2
    (r'<figcaption class="carte__tete"', 'h3', 'h2'),  # légende de la carte d'itinéraire
    (r'<div class="atouts"', 'h3', 'h2'),             # les trois atouts de l'accueil
]


def niveaux_de_titres(h):
    """Rétablit l'échelle des titres là où un niveau était sauté."""
    n = 0
    for ancre, avant, apres in NIVEAUX:
        m = re.search(ancre, h)
        if not m:
            continue
        # La portée s'arrête à la fin du bloc ouvert par l'ancre : on ne
        # renomme pas des titres qui n'ont rien à voir, plus bas dans la page.
        fin = h.find('</footer>', m.start()) if 'footer' in ancre else None
        if fin is None:
            fin = h.find('</nav>', m.start()) if '<nav' in ancre else None
        if fin is None:
            fin = h.find('</figcaption>', m.start()) if 'figcaption' in ancre else None
        if fin is None:
            fin = h.find('</div>', h.find('</div>', m.start()) + 6)
        bloc, k = re.subn(r'<%s([^>]*)>(.*?)</%s>' % (avant, avant),
                          r'<%s\1>\2</%s>' % (apres, apres),
                          h[m.start():fin], flags=re.S)
        if k:
            h = h[:m.start()] + bloc + h[fin:]
            n += k
    return h, n


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
        '.puce{color:#116676}'                 # 4,34:1 → 6,27:1
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
        # Le marqueur « à remplir » et les titres du pied de colonne
        # restaient sous le plancher, et le doré du pied ne tenait pas le
        # seuil sur le fond clair du bloc « guide de voyage ».
        '.aremplir,.rp-aremplir{font-size:14px}'
        '.guide h4,.rp-guide h4,.guide__t,.rp-guide__t{color:#116676}'
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
        # Les h4 des sommaires et des colonnes descendaient à 11,5 px : ce
        # sont des titres, pas des mentions, et ils passaient sous le
        # plancher sans que la règle sur « small » les voie.
        '.som h4,.pied h4,.lat__b h4,.rp-som h4,.rp-lat__b h4,'
        '.lat__b ul,.rp-lat__b ul{font-size:14px}'
        # Les titres qui ont changé de balise pour ne plus sauter de niveau
        # gardent l'apparence exacte qu'ils avaient : la mise en forme était
        # accrochée à « h4 » ou « h3 », elle se serait perdue au change.
        '.som h2,.rp-som h2{font-size:14px;letter-spacing:.15em;'
        'text-transform:uppercase;color:var(--gris);font-weight:700;'
        'margin:0 0 14px;font-family:"Manrope",sans-serif}'
        '.pied h3{font-family:"Manrope",sans-serif;font-size:14px;'
        'letter-spacing:.15em;text-transform:uppercase;color:var(--or);'
        'font-weight:700;margin:0 0 14px}'
        '.atouts h2,.rp-atouts h2{font-size:.98rem;margin:0 0 8px;'
        'display:flex;gap:10px;align-items:center}'
        # Le bleu de titre #148194 rendait 4,34:1 sur blanc — seize
        # centièmes sous le seuil. Même teinte, même saturation, deux crans
        # de clarté en moins : le bleu de marque reste le bleu de marque.
        '.mef th,th,.mef h2,.mef h3,.mef .mef-q,.pg h2,.pg h3,'
        'h2,h3,.rp-corps h2,.rp-corps h3{color:#116676}'
        # Un titre posé sur un bloc sombre doit rester clair : la règle
        # précédente le repeignait en bleu sur le bleu nuit du bloc devis
        # — 1,78:1. C'est moi qui l'avais cassé en corrigeant le reste.
        '.devis h2,.devis h3,.rp-devis h2,.rp-devis h3,'
        '.pg .devis h2,.pg .devis h3,.mur h2,.pg .mur h2,'
        '.pg-sec--nuit h2,.pg-sec--nuit h3,.bande h2,.bande h3{color:#fff}'
        '.pg .pied h3,.pied h3{color:var(--or)}'
        '.pg .hero h1,.hero h1,.pg .hero h2,.lat--devis h3,.rp-lat--devis h3,'
        '.pg-sec--nuit h2,.pg-sec--nuit h3{color:#fff}'
        '.mef th,.mef td,th,td,figcaption,.fig__leg,.pan__note,.pan__avis,'
        '.pan__avis b,.pg-anc a,.quand__frise small,.devis__act small,'
        '.guide span,.rp-guide span{font-size:14px}'
        # La frise « quand partir » code l'affluence en gris clair : 2,71:1
        # sur son fond. C'est une donnée, pas une mention discrète.
        '.quand__frise small,.pg .quand__frise small{color:#5A6069}'
        # Deux cibles de l'aside des fiches séjour restaient sous le doigt.
        '@media (pointer:coarse){'
        '.pan__avis a,.pg-anc a,.pan a,.pan button,.pg .pan a,.pg .pan button,'
        '.pg .pg-anc a,.galerie a,.pg .galerie a'
        '{min-height:44px;min-width:44px;display:inline-flex;'
        'align-items:center;justify-content:center}'
        '}'
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
    ('bloc de contenu dupliqué retiré', blocs_dupliques),
    ('bleu des titres au seuil de contraste', bleu_des_titres),
    ('plancher typographique à 14 px', plancher_typo),
    ('prix par personne sur les fiches séjour', prix_par_personne),
    ('photo du bandeau retirée sur les guides', hero_sans_photo),
    ('bouton d’annotation des maquettes retiré', bouton_annotations),
    ('colonne latérale sans feuille de style', colonne_sans_style),
    ('titres de colonne latérale en h3', titres_colonne),
    ('échelle des titres rétablie', niveaux_de_titres),
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
