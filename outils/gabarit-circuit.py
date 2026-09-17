#!/usr/bin/env python3
"""
Coule les destinations, les profils et le hub blog dans le gabarit circuit.

    ./outils/gabarit-circuit.py --moule FICHIER --site DIR --sortie DIR
                                [--seulement prefixe] [--essai]

Les pages catégorie — les « circuits » — portent le gabarit le plus abouti du
site : un héros, des repères, la liste des séjours, pourquoi nous, sur mesure,
deux FAQ, le mur d'avis, un appel au devis, les familles sœurs. Les
destinations, les profils de voyageur et le hub blog n'avaient qu'un tronçon
de cela. Ils reçoivent ici la même structure.

Le moule donne la forme, la page donne le contenu. Rien n'est écrit qui ne
soit déjà sur la page traitée ou sur le site : une section sans matière est
OMISE, jamais remplie au jugé.

Et le corps de la page passe ENTIER. Une première version ne reprenait que
les cartes et la FAQ, en comptant sur les sections du moule pour le reste :
mesuré mot distinct par mot distinct, elle perdait 2 627 mots sur les
quatorze pages — prix, durées, tout l'éditorial. Ici le corps éditorial est
transplanté tel quel entre la liste des séjours et la FAQ ; le moule
n'apporte que ce que la page n'a pas.
"""

import argparse
import html as H
import json
import os
import re
import sys
from importlib.machinery import SourceFileLoader

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_bleu = SourceFileLoader('bleu_unique',
                         os.path.join(RACINE, 'outils', 'bleu-unique.py')).load_module()
_greffe = SourceFileLoader('greffe_css',
                           os.path.join(RACINE, 'outils', 'greffe-css.py')).load_module()

# L'image de partage que chaque guide déclare en ligne. Le hub montrait le
# logo sur ses vingt-deux cartes, faute de mieux : le héros du guide ne
# porte pas d'image, et la première image de la page EST le logo de
# l'entête. Ce relevé vient des pages en ligne, une par une.
OG = os.path.join(RACINE, 'docs', 'og-guides.json')

FAMILLES = {
    'destination-': ('Destination', 'Les autres destinations',
                     'Les distances comptent : voici ce qui s’ajoute sans casser le rythme.'),
    'qui-part-':    ('Profil', 'Les autres façons de partir',
                     'Famille, couple, solo ou mobilité réduite : chaque profil a sa page.'),
    'hub-':         ('Blog', 'Les autres familles de séjours',
                     'Ce que l’équipe écrit depuis Le Caire, par sujet.'),
}


_CHARTE = []


def _charte():
    """La feuille commune du site, celle que les pages appellent par lien."""
    if not _CHARTE:
        chemin = os.path.join(RACINE, 'maquettes', 'assets', 'charte.css')
        with open(chemin, encoding='utf-8') as f:
            _CHARTE.append(f.read())
    return _CHARTE[0]


def _interieur(html, ouvrant):
    """Les bornes du contenu d'un conteneur, comptées en profondeur.

    « <div class="acc">.*?</div> » paraît juste et ne l'est pas : le point
    d'interrogation arrête la recherche au PREMIER </div>, qui est celui du
    premier accordéon, pas celui du conteneur. La FAQ de la page remplaçait
    donc un morceau de la première question, et les quatre questions
    suivantes du moule restaient là — sans conteneur pour les habiller, et
    surtout parlant de plongée en Mer Rouge au bas d'une page Désert noir.

    Rend (début du contenu, fin du contenu), ou None.
    """
    m = re.search(re.escape(ouvrant), html)
    if not m:
        return None
    profondeur, i = 1, m.end()
    for t in re.finditer(r'<(/?)div\b', html[m.end():]):
        profondeur += 1 if not t.group(1) else -1
        if profondeur == 0:
            return m.end(), m.end() + t.start()
    return None


def _prem(motif, h, defaut=''):
    m = re.search(motif, h, re.S)
    return m.group(1).strip() if m else defaut


def _texte(x):
    return re.sub(r'\s+', ' ', H.unescape(re.sub(r'<[^>]+>', ' ', x))).strip()


# ── lecture du moule ─────────────────────────────────────────────────────

class Moule:
    """Le gabarit circuit, découpé en blocs qu'on peut remplacer un à un."""

    def __init__(self, chemin):
        with open(chemin, encoding='utf-8') as f:
            h = f.read()
        bornes = [m.start() for m in re.finditer(r'<section class="pg-sec', h)]
        pied = h.find('<footer class="pied"')
        if not bornes or pied < 0:
            raise SystemExit('%s n’a pas la forme d’une page catégorie' % chemin)
        self.tete = h[:bornes[0]]
        self.sections = [h[bornes[k]:(bornes[k + 1] if k + 1 < len(bornes) else pied)]
                         for k in range(len(bornes))]
        self.pied = h[pied:]

    def section(self, surtitre):
        """La section portant ce surtitre, ou None."""
        for s in self.sections:
            m = re.search(r'<p class="eyebrow">(.*?)</p>', s, re.S)
            if m and _texte(m.group(1)) == surtitre:
                return s
        return None

    def section_par_h2(self, debut):
        for s in self.sections:
            m = re.search(r'<h2[^>]*>(.*?)</h2>', s, re.S)
            if m and _texte(m.group(1)).startswith(debut):
                return s
        return None


# ── lecture de la page à couler ──────────────────────────────────────────

def lire_page(h):
    """Ce que la page porte : son titre, son image, ses cartes, sa FAQ."""
    def prem(motif, defaut=''):
        m = re.search(motif, h, re.S)
        return m.group(1).strip() if m else defaut

    return {
        'titre_html': prem(r'<h1[^>]*>(.*?)</h1>'),
        'titre': _texte(prem(r'<h1[^>]*>(.*?)</h1>')),
        'balise_titre': prem(r'<title>(.*?)</title>'),
        'meta': prem(r'<meta name="description" content="([^"]*)"'),
        # Deux familles de pages, deux habillages : les catégories posent un
        # « hero », les destinations, profils et guides un « chapeau ». Sans
        # le second repli, la fiche Louxor sortait avec l'image de la mer
        # Rouge derrière son titre, et sans chapô du tout.
        'chapo': (prem(r'<p class="hero__chapo">(.*?)</p>')
                  or prem(r'<section class="chapeau">.*?<p class="sous">(.*?)</p>')),
        'hero_img': (prem(r'<div class="hero__fond"><img src="([^"]+)"')
                     or prem(r'<div class="chapeau__bg"><img src="([^"]+)"')),
        'stats': prem(r'(<div class="chapeau__st">.*?</div>)'),
        'cartes': re.findall(r'<article class="carte".*?</article>', h, re.S),
        # Le chapeau que la page met au-dessus de ses cartes : surtitre,
        # titre, phrase d'accroche. Le moule en a un aussi, mais il parle de
        # la mer Rouge — et laisser tomber celui de la page, c'était perdre
        # « Passer du profil au voyage » et « Tous personnalisables… » sur
        # les treize pages qui les portent.
        'cartes_eyebrow': prem(r'<section[^>]*>(?:(?!</section>).)*?'
                               r'<p class="eyebrow">(.*?)</p>(?:(?!</section>).)*?'
                               r'<article class="carte"'),
        'cartes_titre': prem(r'<section[^>]*>(?:(?!</section>).)*?'
                             r'<h2[^>]*>(.*?)</h2>(?:(?!</section>).)*?<article class="carte"'),
        'cartes_lede': prem(r'<section[^>]*>(?:(?!</section>).)*?'
                            r'<p class="lede"[^>]*>(.*?)</p>(?:(?!</section>).)*?'
                            r'<article class="carte"'),
        'faq': re.findall(r'<details[^>]*>.*?</details>', h, re.S),
        'ariane': prem(r'(<nav class="ariane[^"]*"[^>]*>.*?</nav>)'),
        'pills': prem(r'(<div class="hero__pills">.*?</div>\s*(?=<h1))'),
        'reperes': prem(r'(<section class="[^"]*reperes[^"]*">.*?</section>)'),
        # Le bandeau de contact au-dessus de l'entête. Le moule n'en a pas :
        # sans ce report, « Agence locale basée au Caire · Une personne de
        # l'équipe vous répond » disparaissait des treize pages qui le
        # portaient — la seule phrase que la refonte perdait vraiment.
        'bandeau': prem(r'(<div class="bandeau">.*?</div>\s*</div>)'),
        'ld': ''.join(re.findall(
            r'<script type="application/ld\+json">.*?</script>', h, re.S)),
        'corps': corps_propre(h),
        # La feuille de la page d'origine : le corps repris emporte son
        # habillage avec lui plutôt que d'hériter de celui du moule. La
        # charte partagée vient d'abord, le style propre à la page ensuite,
        # dans l'ordre où le navigateur les lisait — sans la charte, un
        # « wrap » renommé perdait sa gouttière et le texte touchait le bord.
        'css': _charte() + ''.join(m.group(1) for m in
                                   re.finditer(r'<style[^>]*>(.*?)</style>', h, re.S)),
    }


VIDES = {'br', 'hr', 'img', 'input', 'meta', 'link', 'source', 'wbr',
         'col', 'area', 'base', 'embed', 'track', 'param'}


def equilibrer(frag):
    """Referme ce que le fragment ouvre, et jette ce qu'il ferme en trop.

    Un corps découpé au milieu d'une page n'est pas un fragment valide : il
    emporte le « </main> » de sa page, et les « </div> » des conteneurs dont
    on a retiré l'ouverture en supprimant une section. Recollé dans le
    gabarit, ce « </main> » ferme le <main class="pg"> du moule bien avant
    la fin : tout ce qui suit — les avis, la FAQ, l'appel au devis, les
    familles sœurs — se retrouve HORS de la portée « .pg » et perd d'un coup
    toutes ses règles. Le mur d'avis, réglé pour tenir en 700 px, en
    occupait 4 959. C'est ce que montrait la capture : une page qui
    s'effondre à partir du milieu.

    On ne devine rien : une fermeture sans ouverture dans le fragment est
    retirée, une ouverture sans fermeture est refermée à la fin.
    """
    sortie, pile, position = [], [], 0
    for m in re.finditer(r'<(/?)([A-Za-z][\w-]*)([^>]*)>', frag):
        fermant, nom = m.group(1), m.group(2).lower()
        if nom in VIDES or m.group(3).rstrip().endswith('/'):
            continue
        if not fermant:
            pile.append(nom)
            continue
        if nom in pile:
            while pile and pile.pop() != nom:
                pass
            continue
        # Fermeture orpheline : on la saute, elle fermerait une balise du
        # gabarit.
        sortie.append(frag[position:m.start()])
        position = m.end()
    sortie.append(frag[position:])
    return ''.join(sortie) + ''.join('</%s>' % x for x in reversed(pile))


def corps_propre(h):
    """Le corps éditorial de la page, sans son habillage ni ses doublons.

    Tout ce qui vit entre le fil d'Ariane et le pied de page, moins les blocs
    que le gabarit circuit repose lui-même : la liste des séjours, la FAQ,
    le mur d'avis et l'appel au devis. Ce qui reste est propre à la page et
    n'existe nulle part ailleurs — c'est ce que la première version jetait.
    """
    # Le corps commence après le DERNIER bloc d'en-tête de la page — héros,
    # repères, fil d'Ariane, dans l'ordre où elle les pose. Deux bornes plus
    # naïves ont échoué : après le premier </nav> on emportait le méga-menu,
    # et après le fil d'Ariane on emportait encore le héros, parce que sur ces
    # pages le fil est DANS le héros. Résultat visible : un second titre, un
    # second fil et de seconds chiffres au milieu du gabarit.
    fin_pied = h.find('<footer class="pied"')
    if fin_pied < 0:
        return ''
    depart = 0
    for motif in (r'<section class="hero[^"]*".*?</section>',
                  r'<section class="chapeau[^"]*">.*?</section>',
                  r'<section class="[^"]*reperes[^"]*">.*?</section>',
                  r'<nav class="ariane[^"]*"[^>]*>.*?</nav>'):
        for m in re.finditer(motif, h[:fin_pied], re.S):
            depart = max(depart, m.end())
    if not depart:
        m = re.search(r'</nav>', h[:fin_pied])
        depart = m.end() if m else 0
    corps = h[depart:fin_pied]
    for motif in (r'<section[^>]*>(?:(?!</section>).)*?<article class="carte".*?</section>',
                  r'<section[^>]*>(?:(?!</section>).)*?<details.*?</section>',
                  r'<div class="mur".*?</div>\s*</div>\s*</section>',
                  # L'appel au devis de la page : le moule en pose un, et
                  # deux « Votre projet » sur la même page se lisent comme
                  # un bug plutôt que comme une insistance.
                  r'<section[^>]*>(?:(?!</section>).)*?<div class="devis">.*?</section>',
                  r'<section[^>]*>(?:(?!</section>).)*?class="bande.*?</section>'):
        corps = re.sub(motif, '', corps, flags=re.S)
    corps = equilibrer(corps).strip()
    if not corps:
        return ''
    # Enveloppé dans une section du gabarit : sans elle le contenu repris
    # s'affiche pleine largeur, sans rythme ni gouttière, collé au bloc
    # précédent — c'est ce qui rendait les destinations illisibles.
    nu = corps.lstrip()
    if nu.startswith('<section'):
        pass
    elif nu.startswith('<div class="wrap">'):
        # La page apporte déjà sa gouttière : en ajouter une seconde
        # rétrécissait le texte de deux fois la marge, à chaque page.
        corps = '<section class="pg-sec">%s</section>' % corps
    else:
        corps = '<section class="pg-sec"><div class="wrap">%s</div></section>' % corps
    return corps


# ── montage ──────────────────────────────────────────────────────────────

def poser_tete(tete, p, famille):
    """Le héros du moule reçoit le titre, l'image et le fil de la page.

    Et surtout : ce que la page ne remplace pas est RETIRÉ, jamais laissé. Le
    moule est une vraie page — sa mer Rouge, son prix de 1485 €, ses 9 jours,
    son fil d'Ariane. Une première version ne remplaçait que ce que la page
    portait : la fiche Louxor sortait avec le chapô de la mer Rouge, ses
    repères et son fil. Une page fausse, pas une page incomplète.
    """
    if p['balise_titre']:
        tete = re.sub(r'<title>.*?</title>', lambda _: '<title>%s</title>' % p['balise_titre'],
                      tete, count=1, flags=re.S)
    if p['meta']:
        tete = re.sub(r'(<meta name="description" content=")[^"]*(")',
                      lambda m: m.group(1) + p['meta'].replace('"', '&quot;') + m.group(2),
                      tete, count=1)
    if p['titre_html']:
        tete = re.sub(r'(<h1[^>]*>).*?(</h1>)',
                      lambda m: m.group(1) + p['titre_html'] + m.group(2),
                      tete, count=1, flags=re.S)
    if p['hero_img']:
        # Le héros du moule sert deux fois la même image, en fond net et en
        # fond flou : les deux suivent, srcset compris, sinon le flou montre
        # encore la mer Rouge derrière un titre de Louxor.
        tete = re.sub(r'(<div class="hero__(?:flou|fond)"[^>]*>)<img [^>]*>',
                      lambda m: '%s<img src="%s" alt="" decoding="async" '
                                'loading="lazy">' % (m.group(1), p['hero_img']), tete)
    # Le fil du moule porte sa propre gouttière — une <div class="wrap">
    # posée ENTRE le <nav> et le <ol>. Échanger les balises collait le fil
    # au bord gauche ; ne remplacer que ce qui suit immédiatement le <nav>
    # ne remplaçait rien du tout, à cause de ce wrap : les neuf
    # destinations sortaient avec le fil du moule, « Découverte de la Mer
    # rouge » au bas d'une page « Voyage Désert blanc ». On remplace donc
    # le <ol> là où il se trouve, à l'intérieur du fil.
    tete = _poser_ariane(tete, p['ariane'])
    tete = _remplacer_ou_retirer(tete, r'<p class="hero__chapo">.*?</p>', p['chapo'] and
                                 '<p class="hero__chapo">%s</p>' % p['chapo'])
    moule_pills = re.search(r'<div class="hero__pills">.*?</div>\s*(?=<h1)', tete, re.S)
    pills = p['pills'] or pills_des_stats(
        p['stats'], moule_pills.group(0) if moule_pills else '')
    tete = _remplacer_ou_retirer(tete, r'<div class="hero__pills">.*?</div>\s*(?=<h1)', pills)
    moule_rep = re.search(r'<section class="[^"]*reperes[^"]*">.*?</section>', tete, re.S)
    reperes = p['reperes'] or reperes_des_cartes(
        p['cartes'], moule_rep.group(0) if moule_rep else '', sans_compte=bool(pills))
    tete = _remplacer_ou_retirer(tete, r'<section class="[^"]*reperes[^"]*">.*?</section>',
                                 reperes)
    # Les données structurées du moule annoncent son propre nom : laissées en
    # place, elles déclarent à Google qu'une page Louxor s'appelle
    # « Découverte de la Mer rouge ». Invisible à l'œil, fausse pour les
    # moteurs — le pire des deux mondes.
    if p['bandeau'] and '<div class="bandeau">' not in tete:
        tete = tete.replace('<body>', '<body>\n' + p['bandeau'], 1)
    tete = re.sub(r'<script type="application/ld\+json">.*?</script>', '', tete, flags=re.S)
    if p['ld']:
        tete = tete.replace('</head>', p['ld'] + '</head>', 1)
    return tete


# Les rubriques du méga-menu — « Destinations », « Qui part » — n'ont pas
# de page à elles : sur la maquette, leur maillon pointait vers
# « ../index.html », qui ne mène nulle part une fois la page dans le CMS.
ACCUEIL = 'https://authentiquegypte.com/'


def _poser_ariane(tete, ariane):
    """Le fil de la page prend la place de celui du moule, liens compris."""
    nav = re.search(r'<nav class="ariane[^"]*"[^>]*>.*?</nav>', tete, re.S)
    maillons = re.search(r'<ol.*?</ol>', ariane or '', re.S)
    if not nav:
        return tete
    if not maillons:
        # Pas de fil sur la page : celui du moule nomme une AUTRE page, le
        # garder serait mentir. On le retire.
        return tete[:nav.start()] + tete[nav.end():]

    def maillon(m):
        lien, texte = m.group(1), m.group(2)
        if lien.startswith(('http://', 'https://')):
            return m.group(0)
        if _texte(texte).lower().startswith('accueil'):
            return '<a href="%s">%s</a>' % (ACCUEIL, texte)
        # Un lien mort se lit plus mal qu'un maillon sans lien.
        return texte

    corrige = re.sub(r'<a href="([^"]*)">(.*?)</a>', maillon, maillons.group(0), flags=re.S)
    ancien = re.search(r'<ol.*?</ol>', nav.group(0), re.S)
    if not ancien:
        return tete
    neuf = nav.group(0)[:ancien.start()] + corrige + nav.group(0)[ancien.end():]
    return tete[:nav.start()] + neuf + tete[nav.end():]


def _remplacer_ou_retirer(tete, motif, contenu):
    """Le bloc du moule prend la valeur de la page, ou disparaît.

    Le laisser tel quel reviendrait à prêter à une page les faits d'une autre :
    c'est la faute la plus coûteuse de tout l'exercice, parce qu'elle ne se
    voit pas — la page est belle, complète, et fausse.
    """
    return re.sub(motif, lambda _: contenu or '', tete, count=1, flags=re.S)


def pills_des_stats(stats, moule_pills):
    """Les pastilles du héros, reprises des chiffres que la page affiche.

    « 3 jours conseillés · 4 séjours y passent » : ces chiffres étaient au
    milieu du bandeau de la page, un bandeau que le gabarit remplace. Ils
    remontent dans le héros plutôt que de disparaître — même texte, place
    du moule. Sans eux le héros sortait nu, le titre seul sur la photo.
    """
    if not stats:
        return ''
    morceaux = re.findall(r'<span[^>]*>(.*?)</span>', stats, re.S)
    if not morceaux:
        return ''
    picto = re.search(r'<svg[^>]*>.*?</svg>', moule_pills or '', re.S)
    return '<div class="hero__pills">%s</div>' % ''.join(
        '<span class="pill">%s%s</span>' % (picto.group(0) if picto else '', x.strip())
        for x in morceaux)


def cartes_des_guides(source, moule_section):
    """Les cartes du hub blog, bâties sur les pages guide du même dossier.

    Le hub ne listait aucun de ses articles — relevé par le contrôle de
    contenu, qui comptait zéro des sept liens de la page en ligne. On ne
    fabrique rien : le titre, l'adresse et l'image de chaque carte sont ceux
    que la page guide porte elle-même, et l'extrait est son propre chapô.
    Vingt-deux cartes, soit tout le blog, là où la page en ligne n'en montre
    que sept.
    """
    modele = re.search(r'<article class="carte".*?</article>', moule_section or '', re.S)
    vignettes = {}
    if os.path.exists(OG):
        with open(OG, encoding='utf-8') as f:
            vignettes = json.load(f)
    cartes = []
    for nom in sorted(os.listdir(source)):
        if not nom.startswith('guide-') or not nom.endswith('.html'):
            continue
        with open(os.path.join(source, nom), encoding='utf-8') as f:
            g = f.read()
        titre = re.search(r'<h1[^>]*>(.*?)</h1>', g, re.S)
        lien = re.search(r'Contenu repris de\s*<a[^>]*href="([^"]+)"', g)
        # Dans cet ordre : l'image de partage relevée en ligne, puis celle du
        # bandeau du guide, puis la première image de son corps. Jamais celle
        # de l'entête — c'est le logo, et c'est ce qui donnait vingt-deux
        # cartes identiques.
        corps = g[g.find('<article class="corps">'):g.find('<footer class="pied"')]
        img = (vignettes.get(nom)
               or _prem(r'<div class="hero__fond"><img src="([^"]+)"', g)
               or _prem(r'<div class="chapeau__bg"><img src="([^"]+)"', g)
               or _prem(r'<img src="(https://authentiquegypte[^"]+)"', corps))
        # Le chapô du guide, là où sa page le met : « hero__chapo » sur les
        # pages à héros, « p.sous » dans le bandeau des guides, à défaut le
        # premier paragraphe. Sans le deuxième repli, vingt cartes sur
        # vingt-deux sortaient sans une ligne de résumé.
        chapo = (re.search(r'<p class="hero__chapo">(.*?)</p>', g, re.S)
                 or re.search(r'<section class="chapeau">.*?<p class="sous">(.*?)</p>', g, re.S)
                 or re.search(r'<div class="prose[^"]*">\s*<p>(.*?)</p>', g, re.S)
                 or re.search(r'<article class="corps">.*?<p[^>]*>(.*?)</p>', g, re.S))
        if not (titre and lien):
            continue
        extrait = _texte(chapo.group(1))[:150] if chapo else ''
        cartes.append(
            '<article class="carte">'
            '%s'
            '<div class="carte__c"><h3><a href="%s">%s</a></h3>'
            '%s'
            '<div class="carte__b"><a class="lien-fl" href="%s">Lire le guide</a></div>'
            '</div></article>'
            % ('<a class="carte__img" href="%s" tabindex="-1" aria-hidden="true">'
               '<img src="%s" alt="" loading="lazy" decoding="async"></a>'
               % (lien.group(1), img) if img else '',
               lien.group(1), titre.group(1).strip(),
               '<p class="carte__route">%s…</p>' % H.escape(extrait) if extrait else '',
               lien.group(1)))
    return cartes


def reperes_des_cartes(cartes, moule_section, sans_compte=False):
    """Les repères du héros, calculés sur les cartes de la page.

    Le moule en porte — « à partir de 1485 €, 9 jours, 1 séjour au choix » —
    mais ce sont ceux de la mer Rouge : ils sont retirés. Plutôt que de laisser
    le héros nu, on les recalcule sur les séjours que la page liste elle-même.
    Rien n'est ajouté : ces prix et ces durées sont ceux des cartes, qui
    viennent des fiches du site.
    """
    if not cartes or not moule_section:
        return ''
    prix, jours = [], []
    for c in cartes:
        m = re.search(r'À partir de\s*<b>\s*([\d\s]+)\s*€|([\d\s]{3,6})\s*€', _texte(c))
        if m:
            brut = (m.group(1) or m.group(2)).replace(' ', '')
            if brut.isdigit():
                prix.append(int(brut))
        m = re.search(r'(\d+)\s*jours?', _texte(c))
        if m:
            jours.append(int(m.group(1)))
    lignes = []
    n = len(cartes)
    # Le nombre de séjours figure déjà dans les pastilles du héros quand la
    # page en porte : le répéter deux blocs plus bas se lit comme un bug.
    if not sans_compte:
        lignes.append(('Séjours', '%d au choix' % n))
    if prix:
        lignes.append(('À partir de', '%d €' % min(prix)))
    if jours:
        lignes.append(('Durée', ('%d jour%s' % (min(jours), 's' if min(jours) > 1 else ''))
                       if min(jours) == max(jours)
                       else '%d à %d jours' % (min(jours), max(jours))))
    if len(lignes) < 2:
        return ''
    # Le picto du moule suit le RÔLE de la ligne, pas son rang : une première
    # version prenait les pictos dans l'ordre, si bien qu'un prix s'affichait
    # sous une coche et une durée sous un symbole euro.
    modeles = {}
    for li in re.findall(r'<li>.*?</li>', moule_section, re.S):
        etiquette = _texte(re.search(r'<small>(.*?)</small>', li, re.S).group(1)) \
            if re.search(r'<small>', li) else ''
        picto = re.search(r'<svg[^>]*>.*?</svg>', li, re.S)
        if etiquette and picto:
            modeles[etiquette.lower()] = (etiquette, picto.group(0))
    def modele(role):
        for cle, valeur in modeles.items():
            if cle.startswith(role.lower()):
                return valeur
        return (role, '')
    corps = ''
    for role, valeur in lignes:
        etiquette, picto = modele(role)
        corps += ('<li>%s<small>%s</small><b>%s</b></li>'
                  % (picto, H.escape(etiquette), H.escape(valeur)))
    return '<section class="reperes"><div class="wrap"><ul>%s</ul></div></section>' % corps


# Le nom d'un lieu porte son article, et le français ne le devine pas : on
# ne peut pas fabriquer « le Désert blanc » à partir de « Voyage Désert
# blanc » sans savoir qu'il est masculin. Les cas que le titre ne donne pas
# sont donc écrits ici, une fois, plutôt que tirés au jugé à chaque appel.
LIEUX = {
    'Voyage Désert blanc': 'le Désert blanc',
    'Voyage dans le Désert noir': 'le Désert noir',
    'Voyage au Lac Nasser': 'le lac Nasser',
    'Voyage au Mont Sinaï sur mesure': 'le mont Sinaï',
    'Voyage au Caire': 'Le Caire',
}


def lieu_de(titre):
    """Le lieu, tel qu'on l'écrit après « qui passent par »."""
    if titre in LIEUX:
        return LIEUX[titre]
    m = re.match(r'(?:Voyage|Séjour|Excursion)\s+'
                 r'(?:à l\'|à la |au |aux |à |en |dans (?:le |la |les )?|sur (?:le |la )?)(.+)$',
                 titre)
    return m.group(1).strip() if m else titre


def _compte(n):
    return '%d séjour%s' % (n, 's' if n > 1 else '') if n else 'sur mesure'


def section_cartes(moule, p, famille, source=None):
    """« Au choix » : les cartes de la page, ou pas de section du tout.

    Le hub blog n'arrive avec aucune carte — la page en ligne ne liste pas
    ses articles. Les siennes sont bâties sur les pages guide du dossier.
    """
    s = moule.section('Au choix')
    if s is None:
        return ''
    liste = p['cartes']
    if not liste and famille == 'Blog' and source:
        liste = cartes_des_guides(source, s)
    if not liste:
        return ''
    # Découpage explicite plutôt qu'expression régulière : la section se
    # termine par « </div><p class="cartes__src">…</p></div></section> », et
    # aucun motif raisonnable ne tenait à la fois le dernier </article> et
    # cette note de provenance — qu'il faut garder, elle date les prix.
    ouvre = re.search(r'<div class="cartes[^"]*">', s)
    dernier = s.rfind('</article>')
    if not ouvre or dernier < 0:
        return ''
    s = s[:ouvre.end()] + ''.join(liste) + s[dernier + len('</article>'):]
    # Le moule vient d'une famille d'un seul séjour : sa grille est réglée
    # pour une carte large. Vingt-deux guides dans cette grille sortaient
    # en colonnes de travers ; le modificateur suit le nombre réel.
    s = re.sub(r'(<div class="cartes)[^"]*(">)',
               lambda m: '%s cartes--%s%s' % (m.group(1), 1 if len(liste) == 1 else 2,
                                              m.group(2)), s, count=1)
    titre = p['cartes_titre'] or H.escape(
        {'Destination': 'Les séjours qui passent par %s' % lieu_de(p['titre']),
         'Profil': 'Les séjours pour %s' % p['titre'].lower(),
         'Blog': 'Les guides à lire avant de partir'}[famille])
    # Le titre que la page porte est lui-même issu d'une passe précédente, et
    # trois destinations sur neuf en sortaient bancales : « par Voyage Désert
    # blanc », « par Caire », « par Mont Sinaï sur mesure ». Quand il suit ce
    # moule-là, on le refait proprement — c'est un titre calculé, pas une
    # phrase du client.
    if famille == 'Destination' and re.match(
            r'Les séjours qui passent par\b', _texte(titre)):
        titre = H.escape('Les séjours qui passent par %s' % lieu_de(p['titre']))
    s = re.sub(r'(<h2[^>]*>).*?(</h2>)', lambda m: m.group(1) + titre + m.group(2),
               s, count=1, flags=re.S)
    # Le surtitre de la page prend la place de celui du moule quand elle en
    # a un. Celui du moule — « Au choix » — ne nomme aucune famille : il
    # peut rester sans rien affirmer de faux.
    if p['cartes_eyebrow']:
        s = re.sub(r'<p class="eyebrow">.*?</p>',
                   lambda _: '<p class="eyebrow">%s</p>' % p['cartes_eyebrow'],
                   s, count=1, flags=re.S)
    if p['cartes_lede']:
        s = re.sub(r'(<h2[^>]*>.*?</h2>)',
                   lambda m: '%s<p class="lede" style="margin:14px 0 30px">%s</p>'
                             % (m.group(1), p['cartes_lede']),
                   s, count=1, flags=re.S)
    return s


def section_faq(moule, p):
    """Les deux FAQ du moule : la première reçoit celle de la page."""
    s = moule.section('Avant de choisir')
    if s is None:
        return ''
    if not p['faq']:
        # Pas de question propre à la page : on retire le premier accordéon
        # et son titre, on garde « Avant de réserver », commun au site.
        coupe = s.find('<p class="eyebrow">Avant de réserver</p>')
        return '<section class="pg-sec pg-sec--fond"><div class="wrap">' + s[coupe:] if coupe > 0 else ''
    fin = s.find('<p class="eyebrow">Avant de réserver</p>')
    tete, reste = (s[:fin], s[fin:]) if fin > 0 else (s, '')
    bornes = _interieur(tete, '<div class="acc">')
    if not bornes:
        return s
    debut, fin_acc = bornes
    tete = tete[:debut] + ''.join(p['faq']) + tete[fin_acc:]
    return tete + reste


# Pas de section « sœurs » montée ici : le moule n'en porte pas d'exploitable,
# et chaque destination comme chaque profil arrive avec la sienne — « Louxor
# se combine bien », « Les autres façons de partir ». Reprendre celle du moule
# afficherait des circuits au bas d'une page destination.


def monter(moule, p, famille, source=None):
    # Le corps repris part avec son propre habillage, renommé pour qu'aucun
    # nom de classe ne soit lu deux fois. Sans cela, « edito » — un article
    # encadré sur une page profil, une grille de deux colonnes dans le
    # gabarit circuit — coupait chaque question de sa réponse.
    repris, feuille = _greffe.greffer(p['corps'], p['css'])
    # La grille des guides tient trois colonnes : le rail du sommaire, la
    # colonne de lecture, la colonne latérale. Une page qui n'a pas de
    # sommaire n'a que deux enfants : son texte tombait alors dans le rail
    # — 222 px de large — et sa colonne latérale prenait la place de la
    # lecture. C'est ce qui rendait le hub blog illisible sous ses cartes.
    if 'rp-art' in repris and 'rp-som' not in repris:
        feuille = feuille.replace(
            '</style>',
            '.rp-art{grid-template-columns:minmax(0,1fr) 300px}'
            '@media (max-width:900px){.rp-art{grid-template-columns:minmax(0,1fr)}}'
            '</style>')
    corps = [section_cartes(moule, p, famille, source), repris]
    for surtitre in ('Pourquoi nous', 'Sur mesure'):
        bloc = moule.section(surtitre)
        if bloc:
            # Le moule parle de la mer Rouge : son titre suit la page, sinon
            # un Louxor demanderait « pourquoi voyager à la Mer Rouge ».
            bloc = re.sub(r'(<h2[^>]*>)Pourquoi voyager en Égypte[^<]*(</h2>)',
                          lambda m: '%sPourquoi voyager en Égypte avec nous ?%s'
                                    % (m.group(1), m.group(2)), bloc)
            corps.append(bloc)
    corps.append(section_faq(moule, p))
    for debut in ('Ce que disent', 'Ce séjour vous tente'):
        bloc = moule.section_par_h2(debut)
        if bloc:
            corps.append(bloc)
    tete = poser_tete(moule.tete, p, famille)
    if feuille:
        tete = tete.replace('</head>', feuille + '\n</head>', 1)
    return tete + ''.join(x for x in corps if x) + moule.pied


def main():
    a_p = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    a_p.add_argument('--moule', required=True)
    a_p.add_argument('--site', required=True)
    a_p.add_argument('--sortie', required=True)
    a_p.add_argument('--seulement')
    a_p.add_argument('--essai', action='store_true')
    a = a_p.parse_args()

    moule = Moule(os.path.abspath(a.moule))
    source = os.path.abspath(a.site)
    os.makedirs(a.sortie, exist_ok=True)

    cibles = [f for f in sorted(os.listdir(source))
              if f.endswith('.html') and any(f.startswith(x) for x in FAMILLES)
              and (not a.seulement or f.startswith(a.seulement))]
    pages = {}
    for f in cibles:
        with open(os.path.join(source, f), encoding='utf-8') as fh:
            pages[f] = lire_page(fh.read())

    print('→ Moule : %s — %d section(s)\n' % (os.path.basename(a.moule), len(moule.sections)))
    for f in cibles:
        famille = FAMILLES[next(x for x in FAMILLES if f.startswith(x))][0]
        h = _bleu.unifier(monter(moule, pages[f], famille, source))
        etat = '%d carte(s), %d question(s), corps %d o' % (
            len(pages[f]['cartes']), len(pages[f]['faq']), len(pages[f]['corps']))
        print('   %-46s %-34s %6d → %6d octets'
              % (f[:46], etat, os.path.getsize(os.path.join(source, f)), len(h)))
        if not a.essai:
            with open(os.path.join(a.sortie, f), 'w', encoding='utf-8') as fh:
                fh.write(h)
    print('\n%d page(s) %s.' % (len(cibles), 'à couler' if a.essai else 'coulée(s)'))


if __name__ == '__main__':
    main()
