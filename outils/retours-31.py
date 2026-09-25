#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Les trente-et-un retours que je peux traiter sans rien demander.

    WP_AUTH='compte:mot de passe' ./outils/retours-31.py [--essai]

Ce qui reste après les photos (qu'elle seule peut fournir) et les textes
(proposés, en attente de son choix). Tout ici est de la mise en forme,
du retrait désigné, ou ses propres mots.

LES PASTILLES DU HERO des pages profil (#10452-54, #10460-62). Six fils,
un mot chacun : « enlever ». Trois pastilles par page — le nombre de
séjours, la durée, le prix — qui répètent ce que les cartes disent juste
en dessous, et qui datent d'avant les filtres.

LES AVIS GOOGLE (#10423, #10431, #10466, #10483). Quatre fils qui disent
la même chose : moins gros, plus de couleur, et différents d'une page à
l'autre. Rémi tranche le nombre : huit. Les cartes se resserrent, le
guillemet passe en or, et la SÉLECTION TOURNE — chaque page tire ses huit
avis à partir d'un décalage calculé sur son identifiant, donc deux pages
voisines ne montrent pas les mêmes.

LES COULEURS (#10421, #10422, #10450, #10465, #9539). « Un peu plus de
couleurs, jaune pour que cela se démarque » : les tuiles « Pourquoi
nous » et « Sur mesure » prennent un filet or et un fond crème, et leurs
icônes passent en or.

L'ACCUEIL (#10472, #10475-77, #10479-81, #10484). Ses mots pour l'expert
local, deux profils et deux thèmes ajoutés, un paragraphe retiré, le
bloc nuit remonté avant les avis, les programmes avant les régions, le
bon bleu, et le bouton de FAQ qui ne chevauche plus le pied de page.

LE JOUR PAR JOUR (#10436, #10437). Texte resserré, et les sites cités
mis en gras — à partir d'une liste de lieux réels, jamais d'une
devinette sur les majuscules.

DIVERS (#10420, #10427, #10448, #10451, #10464). La sécurité en tête de
FAQ, le titre du hero sur une ligne, l'article PMR avant la FAQ, la
section « les familles adorent » avec ses mots, et un bouton vers tous
les programmes.
"""

import argparse
import html as H
import os
import re
import time
from importlib.machinery import SourceFileLoader

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MERE = 7642
Q = '/pages?parent=%d&per_page=100&status=any&context=edit&orderby=menu_order&order=asc'
E = '.elementor-template-canvas '

# Les lieux mis en gras dans le déroulé. Liste explicite : repérer les
# majuscules mettrait en gras « Accueil », « Transfert » et tous les
# débuts de phrase.
LIEUX = [
    'Grand Musée égyptien', 'Musée Égyptien', 'vallée des Rois', 'vallée des Reines',
    'Abou Simbel', 'Abu Simbel', 'Sainte-Catherine', 'mont Moïse', 'Kom Ombo',
    'Deir el-Bahari', 'Hatchepsout', 'Karnak', 'Louxor', 'Assouan', 'Philae',
    'Gizeh', 'Saqqara', 'Memphis', 'Edfou', 'Esna', 'Dendera', 'Abydos',
    'Le Caire', 'Alexandrie', 'Hurghada', 'Marsa Alam', 'Dahab',
    'Sharm el-Sheikh', 'lac Nasser', 'Siwa', 'Bahariya', 'Fayoum',
    'désert Blanc', 'désert blanc', 'Wadi El Rayan', 'Ramsès II', 'Néfertari',
    'Toutânkhamon', 'Khan el-Khalili', 'Nil', 'Aswan', 'Hatshepsout',
    'Sphinx', 'Mont Moïse', 'Sainte Catherine', 'Désert Noir', 'désert Noir',
]

FEUILLE = (
    '<style data-retours="31">'
    # Les avis : plus compacts, un guillemet en or, un filet de couleur.
    + E + '.pg .mur.mur.mur{gap:14px}'
    + E + '.pg .mur.mur.mur .mur__a{padding:16px 18px;border-top:3px solid var(--or,#FBB50E)}'
    + E + '.pg .mur.mur.mur .mur__a blockquote{font-size:.95rem;line-height:1.55;'
    '-webkit-line-clamp:6}'
    + E + '.pg .mur.mur.mur .mur__q{color:var(--or,#FBB50E);font-size:1.6rem;line-height:1}'
    + E + '.pg .mur.mur.mur .mur__a footer{padding-top:10px;font-size:.8rem}'
    # Les tuiles « pourquoi nous » et « sur mesure » : un peu d'or.
    + E + '.pg .rp-atout,' + E + '.pg .pourquoi li,' + E + '.pg .args li,'
    + E + '.pg .equipe__tuiles>div{background:var(--or-fond,#FEEDDC);'
    'border:1px solid #F3D9A8}'
    + E + '.pg .rp-atout h3,' + E + '.pg .pourquoi li b,' + E + '.pg .args li b'
    '{color:var(--nuit-900,#095360)}'
    + E + '.pg .rp-atout svg,' + E + '.pg .pourquoi svg,' + E + '.pg .args svg'
    '{color:var(--or,#FBB50E)}'
    # Le déroulé, resserré ; les lieux ressortent en gras.
    + E + '.pg .etape__pts li{font-size:.97rem;line-height:1.55}'
    + E + '.pg .etape__pts b{color:var(--nuit-900,#095360);font-weight:700}'
    + E + '.pg .jour__tete h3{font-size:1.12rem}'
    # Le bouton de FAQ ne colle plus au pied de page.
    + E + '.pg .faq__plus{margin-bottom:26px}'
    + E + 'section[data-plie]{padding-bottom:64px}'
    # Le titre du hero tient sur une ligne quand la place le permet. Ce
    # qui le coupait n'était pas la largeur de l'écran mais une mesure de
    # 18 caractères ; on la desserre au lieu d'interdire le retour, sans
    # quoi un titre long déborderait de son cadre.
    + E + '.pg .hero h1{text-wrap:balance}'
    '@media (min-width:1100px){' + E + '.pg .hero h1{max-width:30ch}}'
    '</style>')


def _fin(h, d, nom):
    p = 0
    for t in re.finditer(r'<(/?)%s\b[^>]*>' % nom, h[d:]):
        p += 1 if not t.group(1) else -1
        if p == 0:
            return d + t.end()
    return -1


def _retirer(h, balise, texte):
    """Le plus petit élément `balise` qui contient vraiment `texte`."""
    i = h.find(texte)
    if i < 0:
        return h, False
    cand = None
    for m in re.finditer(r'<%s\b[^>]*>' % balise, h[:i]):
        f = _fin(h, m.start(), balise)
        if f > i + len(texte):
            cand = (m.start(), f)
    if not cand or texte not in h[cand[0]:cand[1]]:
        return h, False
    return h[:cand[0]] + h[cand[1]:], True


# Le hero__pills ne porte pas la même chose selon le gabarit : sur un
# programme c'est le fil d'Ariane du séjour, sur une destination la durée
# conseillée. Seul le gabarit profil y répète ce que les cartes disent
# juste en dessous. Le retrait s'arrête donc à ces quatre pages.
PROFILS = (8926, 8927, 8928, 8929)


def sans_pastilles(h, pid):
    """Les trois pastilles du hero des pages profil : « enlever » ×6."""
    if pid not in PROFILS:
        return h, []
    d = h.find('<div class="hero__pills">')
    if d < 0:
        return h, []
    f = _fin(h, d, 'div')
    if f < 0:
        return h, []
    return h[:d] + h[f:], ['pastilles du hero retirées (#10452-54, #10460-62)']


def avis_varies(h, pid):
    """Huit avis, mais pas les mêmes d'une page à l'autre.

    Le mur porte huit cartes identiques partout : « qu'ils changent d'une
    page à une autre » revient trois fois. On fait tourner la sélection
    par un décalage tiré de l'identifiant de la page — même liste, autre
    fenêtre. Déterministe, donc stable d'un passage au suivant.
    """
    # Le mur déjà pivoté porte sa marque : sans elle, chaque passage
    # ferait tourner la sélection d'un cran de plus et l'outil ne serait
    # plus rejouable.
    if 'data-pivot' in h:
        return h, []
    d = h.find('<div class="mur">')
    if d < 0:
        return h, []
    f = _fin(h, d, 'div')
    if f < 0:
        return h, []
    cartes = re.findall(r'<article class="mur__a">.*?</article>', h[d:f], re.S)
    if len(cartes) < 2:
        return h, []
    dec = pid % len(cartes)
    tourne = cartes[dec:] + cartes[:dec]
    neuf = '<div class="mur" data-pivot="%d">%s</div>' % (dec, ''.join(tourne))
    if neuf == h[d:f]:
        return h, []
    return h[:d] + neuf + h[f:], ['avis pivotés de %d (#10423, #10431, #10466)' % dec]


def lieux_en_gras(h):
    """Les lieux cités dans le déroulé ressortent (#10436, #10437)."""
    d = h.find('<h2 id="t-jpj"')
    if d < 0:
        return h, []
    bloc = h[d:]
    fin = bloc.find('<h2 ', 10)
    bloc, reste = (bloc[:fin], bloc[fin:]) if fin > 0 else (bloc, '')
    avant = bloc
    for lieu in sorted(LIEUX, key=len, reverse=True):
        # Jamais deux fois : un lieu déjà en gras ne se réencadre pas.
        bloc = re.sub(r'(?<!<b>)\b%s\b(?!</b>)' % re.escape(lieu),
                      '<b>%s</b>' % lieu, bloc)
    # Un gras dans un gras : on aplatit.
    bloc = re.sub(r'<b>((?:(?!</b>).)*?)<b>(.*?)</b>', r'<b>\1\2', bloc, flags=re.S)
    if bloc == avant:
        return h, []
    return h[:d] + bloc + reste, ['lieux mis en gras (#10436, #10437)']


def securite_en_tete(h):
    """La question de sécurité passe en tête de FAQ (#10420)."""
    d = h.find('<div class="faqu"')
    if d < 0:
        return h, []
    f = _fin(h, d, 'div')
    if f < 0:
        return h, []
    bloc = h[d:f]
    qs = re.findall(r'<details class="faq__q[^"]*">.*?</details>', bloc, re.S)

    def _titre(q):
        # Le repérage se fait sur l'intitulé seul : « sécurité » revient
        # dans quantité de réponses, et hisser la mauvaise question crée
        # un doublon avec celle qui bascule dans le repli.
        m = re.search(r'<summary[^>]*>(.*?)</summary>', q, re.S)
        return re.sub(r'<[^>]+>', ' ', m.group(1)).lower() if m else ''

    cible = next((q for q in qs
                  if 'dangereux' in _titre(q) or 'sécurit' in _titre(q)
                  or 'sûr' in _titre(q)), None)
    if not cible or qs.index(cible) == 0:
        return h, []
    autres = [q for q in qs if q is not cible]
    # Elle passe en tête, donc visible : elle perd sa classe de repli.
    cible = cible.replace('faq__q faq__q--plus', 'faq__q')
    # Et la cinquième visible bascule dans le repli, pour en garder cinq.
    if len(autres) >= 5 and 'faq__q--plus' in bloc:
        autres[4] = autres[4].replace('<details class="faq__q">',
                                      '<details class="faq__q faq__q--plus">', 1)
    corps = bloc
    for q in qs:
        corps = corps.replace(q, '', 1)
    tete = corps[:corps.find('>') + 1]
    reste = corps[len(tete):]
    neuf = tete + cible + ''.join(autres) + reste
    if neuf == bloc:
        return h, []
    return h[:d] + neuf + h[f:], ['sécurité en tête de FAQ (#10420)']


# --- l'accueil, fil par fil ------------------------------------------

ACCUEIL_ID = 8660

# #10472 · « ce n'est pas les guides mais un expert local qui organise
# l'itinéraire, les étapes et qui fait les réservations ». Ses mots,
# posés dans la phrase existante.
EXPERT_AV = ("Nos égyptologues francophones écrivent l{0}itinéraire, réservent "
             "hébergements, transferts et vols internes, et restent joignables sur place.")
EXPERT_AP = ("Un expert local organise l{0}itinéraire et les étapes, fait les "
             "réservations \u2014 hébergements, transferts, vols internes \u2014 et reste "
             "joignable sur place.")

# #10475 · « ajouter : en groupe, entre amis ». Les huit séjours sont
# privatifs et modifiables : aucun ne se refuse à un groupe ou à une
# bande d'amis. Les deux critères les rendent donc tous, et je le lui
# dis dans le fil pour qu'elle restreigne si elle le souhaite.
QUI_PLUS = [('groupe', 'En groupe', 'en groupe'),
            ('amis', 'Entre amis', 'entre amis')]

# #10476 · « ajouter Le Caire, Croisière ». Le Caire est un critère
# neuf : il vise les séjours dont le déroulé y passe. « Croisière »
# existe déjà sous le nom « Le Nil » — c'est la même valeur, alors le
# bouton reprend son nom au lieu d'en ouvrir un second qui ferait
# doublon.
CAIRE_SEJOURS = 'Le Caire'
ENVIE_PLUS = [('caire', 'Le Caire', 'le Caire')]


def _opts(h, val):
    """Le groupe de boutons qui contient la valeur donnée."""
    i = h.find('data-val="%s"' % val)
    if i < 0:
        return -1, -1
    d = h.rfind('<div class="opts">', 0, i)
    if d < 0:
        return -1, -1
    return d, _fin(h, d, 'div')


def _boutons(h, ancre, ajouts):
    """Ajoute des boutons au groupe, sans jamais en doubler un."""
    d, f = _opts(h, ancre)
    if f < 0:
        return h, []
    bloc = h[d:f]
    neufs = ''
    poses = []
    for val, nom, _ in ajouts:
        if 'data-val="%s"' % val in bloc:
            continue
        neufs += ('<button class="opt" aria-pressed="false" data-val="%s">%s</button>'
                  % (val, nom))
        poses.append(nom)
    if not neufs:
        return h, []
    coupe = f - len('</div>')
    return h[:coupe] + neufs + h[coupe:], poses


def _lib(h, ajouts):
    """Les libellés du composeur : sans eux la phrase affiche « undefined »."""
    m = re.search(r'(const lib=\{)', h)
    if not m:
        return h
    for val, _, libelle in ajouts:
        if re.search(r'\b%s:' % val, h[m.end():m.end() + 400]):
            continue
        h = h[:m.end()] + "%s:'%s'," % (val, libelle) + h[m.end():]
    return h


def _marquer_cartes(h):
    """Les valeurs neuves posées sur les cartes qui les portent vraiment."""
    d = h.find('id="liste"')
    if d < 0:
        return h, 0
    f = _fin(h, h.rfind('<section', 0, d), 'section')
    if f < 0:
        return h, 0
    bloc, n = h[d:f], 0
    morceaux = re.split(r'(?=<article class="carte")', bloc)
    for i, c in enumerate(morceaux):
        m = re.match(r'<article class="carte"([^>]*)>', c)
        if not m:
            continue
        tete = m.group(0)
        # « en groupe » et « entre amis » : tous, les séjours sont privatifs.
        q = re.search(r'data-qui="([^"]*)"', tete)
        if q and 'groupe' not in q.group(1):
            vals = (q.group(1) + ' groupe amis').strip()
            tete = tete.replace(q.group(0), 'data-qui="%s"' % vals)
        # « Le Caire » : seulement si la ville est au déroulé de la carte.
        e = re.search(r'data-envie="([^"]*)"', tete)
        texte = re.sub(r'<[^>]+>', ' ', c)
        if e and 'caire' not in e.group(1).split() and CAIRE_SEJOURS in texte:
            tete = tete.replace(e.group(0), 'data-envie="%s caire"' % e.group(1))
        if tete != m.group(0):
            morceaux[i] = tete + c[m.end():]
            n += 1
    if not n:
        return h, 0
    return h[:d] + ''.join(morceaux) + h[f:], n


def accueil(h, pid):
    if pid != ACCUEIL_ID:
        return h, []
    faits = []

    # #10472 · un expert local, pas les guides. La page écrit
    # l'apostrophe tantôt droite, tantôt courbe : on essaie les deux.
    for apo in ('\u2019', "'"):
        if EXPERT_AV.format(apo) in h:
            h = h.replace(EXPERT_AV.format(apo), EXPERT_AP.format(apo))
            faits.append('un expert local, ses mots (#10472)')
            break

    # #10475 et #10476 · les critères qui manquaient
    h, poses = _boutons(h, 'solo', QUI_PLUS)
    if poses:
        h = _lib(h, QUI_PLUS)
        faits.append('« %s » ajoutés (#10475)' % ' » et « '.join(poses))
    h, poses = _boutons(h, 'sinai', ENVIE_PLUS)
    if poses:
        h = _lib(h, ENVIE_PLUS)
        faits.append('« %s » ajouté (#10476)' % ' » et « '.join(poses))
    if '>Le Nil<' in h:
        h = h.replace('>Le Nil<', '>Croisière sur le Nil<')
        h = h.replace("croisiere:'le Nil'", "croisiere:'la croisière sur le Nil'")
        faits.append('« Croisière sur le Nil » nommée (#10476)')
    h, n = _marquer_cartes(h)
    if n:
        faits.append('%d cartes reclassées (#10475, #10476)' % n)

    # #10477 · le paragraphe de trop
    h2, ok = _retirer(h, 'p', 'Chaque famille de séjours a sa page')
    if ok:
        h = h2
        faits.append('paragraphe retiré (#10477)')

    # #10480 · le bloc « avec les locaux » remonte avant les avis
    dn = h.find('<section class="section section--nuit">')
    da = h.find('aria-labelledby="t-avis"')
    da = h.rfind('<section', 0, da) if da > 0 else -1
    if dn > 0 and da > 0 and dn > da:
        fn = _fin(h, dn, 'section')
        if fn > 0:
            bloc = h[dn:fn]
            h = h[:dn] + h[fn:]
            da = h.rfind('<section', 0, h.find('aria-labelledby="t-avis"'))
            h = h[:da] + bloc + h[da:]
            faits.append('bloc remonté avant les avis (#10480)')

    # #10484 · « d'abord mettre les programmes » : le composeur passe
    # devant la présentation des familles de séjours.
    dr = h.find('<section class="section section--fond" id="resultats">')
    dp = h.find('<section class="section preuve">')
    if dr > 0 and dp > 0 and dr > dp:
        fr = _fin(h, dr, 'section')
        if fr > 0:
            bloc = h[dr:fr]
            h = h[:dr] + h[fr:]
            dp = h.find('<section class="section preuve">')
            h = h[:dp] + bloc + h[dp:]
            faits.append('les programmes en premier (#10484)')

    return h, faits




# La section « les familles adorent », avec ses mots à elle (#10451).
FAMILLES = (
    '<section class="pg-sec adorent"><div class="wrap">'
    '<p class="eyebrow">Pensé pour eux</p>'
    '<h2>Ce que les familles adorent</h2>'
    '<ul class="adorent__l">'
    '<li>Des chambres familiales ou communicantes, choisies une par une.</li>'
    '<li>Un guide égyptologue privatif qui cale le rythme sur celui des enfants, '
    'et leur parle comme on raconte une histoire.</li>'
    '<li>Un lit parapluie et un siège auto sur simple demande.</li>'
    '</ul></div></section>')

# Et celle des couples (#10463), sur le même modèle.
COUPLES = (
    '<section class="pg-sec adorent"><div class="wrap">'
    '<p class="eyebrow">Rien qu\'à deux</p>'
    '<h2>Ce que les couples préfèrent</h2>'
    '<ul class="adorent__l">'
    '<li>Un dîner dans un palace.</li>'
    '<li>Des hébergements de charme, choisis un par un.</li>'
    '<li>Un vol en montgolfière au lever du jour.</li>'
    '<li>Un repas à bord d\'une felouque privatisée.</li>'
    '<li>Un moment rien qu\'à vous sur la mer Rouge.</li>'
    '</ul></div></section>')

FEUILLE_ADORENT = (
    E + '.pg .adorent__l{display:grid;gap:12px;margin:18px 0 0;padding:0;list-style:none}'
    + E + '.pg .adorent__l li{background:var(--or-fond,#FEEDDC);border:1px solid #F3D9A8;'
    'border-radius:16px;padding:16px 20px;font-size:1rem;line-height:1.6;'
    'color:var(--texte,#5D5D5D)}'
    '@media (min-width:820px){' + E + '.pg .adorent__l{grid-template-columns:repeat(2,1fr)}}')

FEUILLE_PLUS = (E + '.pg .fac__plus-prog{margin:26px 0 0;text-align:center}')

VOIR_PLUS = ('<p class="fac__plus-prog"><a class="btn btn--fantome btn--sm" '
             'href="https://authentiquegypte.com/nos-sejours-egypte/">'
             'Voir tous les programmes</a></p>')

BLOG_PMR = ('<section class="pg-sec pg-sec--fond"><div class="wrap">'
            '<p class="eyebrow">À lire avant de partir</p>'
            '<h2>Voyager en Égypte en situation de mobilité réduite</h2>'
            '<p>Notre guide détaille site par site ce qui est accessible, ce qui '
            'demande de l\'aide, et ce qui ne l\'est pas.</p>'
            '<p><a class="btn btn--or btn--sm" '
            'href="https://authentiquegypte.com/voyage-pmr-en-egypte/">Lire le guide PMR</a></p>'
            '</div></section>')


def _sejours(h):
    """La section « Passer du profil au voyage », bornes comprises.

    Les pages profil n'ont pas de bloc .fac — les filtres à facettes sont
    allés sur les destinations. L'ancre de ses trois remarques est bien
    cette section-là.
    """
    d = h.find('<section class="pg-sec" id="sejours">')
    if d < 0:
        return -1, -1
    return d, _fin(h, d, 'section')


def sections_profil(h, pid):
    faits = []
    if pid not in PROFILS:
        return h, faits
    if pid == 8928 and 'Lire le guide PMR' not in h:
        g = h.find('<section class="pg-sec pg-sec--fond" data-plie')
        if g < 0:
            g = h.find('data-plie')
            g = h.rfind('<section', 0, g) if g > 0 else -1
        if g > 0:
            h = h[:g] + BLOG_PMR + h[g:]
            faits.append('guide PMR avant la FAQ (#10448)')

    d, f = _sejours(h)
    if f < 0:
        return h, faits

    # Le bouton vers tous les programmes se glisse à la fin de la liste,
    # dans la section, pas après elle (#10464).
    if 'fac__plus-prog' not in h:
        # Dans le .wrap, pas après : posé au-delà, le bouton perdrait la
        # gouttière et se collerait au bord de l'écran.
        ferme = h.rfind('</div></section>', d, f)
        pose = ferme if ferme > 0 else f - len('</section>')
        h = h[:pose] + VOIR_PLUS + h[pose:]
        faits.append('« Voir tous les programmes » (#10464)')
        d, f = _sejours(h)

    # Les encarts qu'elle a dictés viennent juste après la liste.
    if pid == 8927 and 'Ce que les familles adorent' not in h:
        h = h[:f] + FAMILLES + h[f:]
        faits.append('section « les familles adorent » (#10451)')
    if pid == 8926 and 'Ce que les couples préfèrent' not in h:
        h = h[:f] + COUPLES + h[f:]
        faits.append('section « les couples préfèrent » (#10463)')

    return h, faits


def corriger(h, pid):
    faits = []
    for etape in (lieux_en_gras, securite_en_tete):
        h, f = etape(h)
        faits += f
    h, f = sans_pastilles(h, pid); faits += f
    h, f = avis_varies(h, pid); faits += f
    h, f = accueil(h, pid); faits += f
    h, f = sections_profil(h, pid); faits += f

    feuille = FEUILLE.replace('</style>', FEUILLE_ADORENT + FEUILLE_PLUS + '</style>')
    ancienne = re.search(r'<style data-retours="31">.*?</style>', h, re.S)
    if ancienne and ancienne.group(0) != feuille:
        faits.append('feuille mise à jour')
    elif not ancienne:
        faits.append('avis resserrés, couleurs, FAQ décollée du pied')
    if not faits:
        return h, faits
    h = re.sub(r'<style data-retours="31">.*?</style>', '', h, flags=re.S)
    return h + feuille, faits


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--essai', action='store_true')
    a = p.parse_args()
    dep = SourceFileLoader('dep', os.path.join(RACINE, 'outils', 'deployer.py')).load_module()

    pages = []
    for d in dep.appel('GET', Q % MERE):
        if d['status'] == 'trash':
            continue
        pages += [k for k in dep.appel('GET', Q % d['id']) if k['status'] != 'trash']

    n = 0
    for k in pages:
        p_ = dep.appel('GET', '/pages/%d?context=edit' % k['id'])
        brut = re.sub(r'<!-- /?wp:html -->\n?', '', p_['content']['raw'])
        neuf, faits = corriger(brut, k['id'])
        if not faits:
            continue
        print('   #%-6d %-34s %s' % (k['id'], (p_.get('title') or {}).get('raw', '')[:34],
                                     ' · '.join(faits)[:96]))
        if a.essai:
            continue
        n += 1
        corps = '<!-- wp:html -->\n' + neuf + '\n<!-- /wp:html -->'
        for essai in range(4):
            try:
                dep.appel('POST', '/pages/%d' % k['id'], {'content': corps})
                relu = dep.appel('GET', '/pages/%d?context=edit' % k['id'])
                if 'data-retours="31"' in relu['content']['raw']:
                    break
            except SystemExit as motif:
                print('      reprise %d/3 — %s' % (essai + 1, str(motif).splitlines()[0][:60]))
            time.sleep(2 ** essai)
        else:
            print('      ✗ ABANDON #%d' % k['id'])
    print('\n%d page(s) corrigée(s).' % n)


if __name__ == '__main__':
    main()
