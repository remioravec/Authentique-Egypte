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
import os
import re
import sys
from importlib.machinery import SourceFileLoader

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_bleu = SourceFileLoader('bleu_unique',
                         os.path.join(RACINE, 'outils', 'bleu-unique.py')).load_module()

FAMILLES = {
    'destination-': ('Destination', 'Les autres destinations',
                     'Les distances comptent : voici ce qui s’ajoute sans casser le rythme.'),
    'qui-part-':    ('Profil', 'Les autres façons de partir',
                     'Famille, couple, solo ou mobilité réduite : chaque profil a sa page.'),
    'hub-':         ('Blog', 'Les autres familles de séjours',
                     'Ce que l’équipe écrit depuis Le Caire, par sujet.'),
}


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
        'chapo': prem(r'<p class="hero__chapo">(.*?)</p>'),
        'hero_img': prem(r'<div class="hero__fond"><img src="([^"]+)"'),
        'cartes': re.findall(r'<article class="carte".*?</article>', h, re.S),
        'faq': re.findall(r'<details[^>]*>.*?</details>', h, re.S),
        'ariane': prem(r'(<nav class="ariane[^"]*"[^>]*>.*?</nav>)'),
        'pills': prem(r'(<div class="hero__pills">.*?</div>\s*(?=<h1))'),
        'reperes': prem(r'(<section class="[^"]*reperes[^"]*">.*?</section>)'),
        'ld': ''.join(re.findall(
            r'<script type="application/ld\+json">.*?</script>', h, re.S)),
        'corps': corps_propre(h),
    }


def corps_propre(h):
    """Le corps éditorial de la page, sans son habillage ni ses doublons.

    Tout ce qui vit entre le fil d'Ariane et le pied de page, moins les blocs
    que le gabarit circuit repose lui-même : la liste des séjours, la FAQ,
    le mur d'avis et l'appel au devis. Ce qui reste est propre à la page et
    n'existe nulle part ailleurs — c'est ce que la première version jetait.
    """
    m = re.search(r'</nav>\s*(.*?)\s*<footer class="pied"', h, re.S)
    if not m:
        return ''
    corps = m.group(1)
    for motif in (r'<section[^>]*>(?:(?!</section>).)*?<article class="carte".*?</section>',
                  r'<section[^>]*>(?:(?!</section>).)*?<details.*?</section>',
                  r'<div class="mur".*?</div>\s*</div>\s*</section>',
                  # L'appel au devis de la page : le moule en pose un, et
                  # deux « Votre projet » sur la même page se lisent comme
                  # un bug plutôt que comme une insistance.
                  r'<section[^>]*>(?:(?!</section>).)*?<div class="devis">.*?</section>',
                  r'<section[^>]*>(?:(?!</section>).)*?class="bande.*?</section>'):
        corps = re.sub(motif, '', corps, flags=re.S)
    return corps.strip()


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
    tete = _remplacer_ou_retirer(tete, r'<nav class="ariane[^"]*"[^>]*>.*?</nav>', p['ariane'])
    tete = _remplacer_ou_retirer(tete, r'<p class="hero__chapo">.*?</p>', p['chapo'] and
                                 '<p class="hero__chapo">%s</p>' % p['chapo'])
    tete = _remplacer_ou_retirer(tete, r'<div class="hero__pills">.*?</div>\s*(?=<h1)', p['pills'])
    moule_rep = re.search(r'<section class="[^"]*reperes[^"]*">.*?</section>', tete, re.S)
    reperes = p['reperes'] or reperes_des_cartes(
        p['cartes'], moule_rep.group(0) if moule_rep else '')
    tete = _remplacer_ou_retirer(tete, r'<section class="[^"]*reperes[^"]*">.*?</section>',
                                 reperes)
    # Les données structurées du moule annoncent son propre nom : laissées en
    # place, elles déclarent à Google qu'une page Louxor s'appelle
    # « Découverte de la Mer rouge ». Invisible à l'œil, fausse pour les
    # moteurs — le pire des deux mondes.
    tete = re.sub(r'<script type="application/ld\+json">.*?</script>', '', tete, flags=re.S)
    if p['ld']:
        tete = tete.replace('</head>', p['ld'] + '</head>', 1)
    return tete


def _remplacer_ou_retirer(tete, motif, contenu):
    """Le bloc du moule prend la valeur de la page, ou disparaît.

    Le laisser tel quel reviendrait à prêter à une page les faits d'une autre :
    c'est la faute la plus coûteuse de tout l'exercice, parce qu'elle ne se
    voit pas — la page est belle, complète, et fausse.
    """
    return re.sub(motif, lambda _: contenu or '', tete, count=1, flags=re.S)


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
    cartes = []
    for nom in sorted(os.listdir(source)):
        if not nom.startswith('guide-') or not nom.endswith('.html'):
            continue
        with open(os.path.join(source, nom), encoding='utf-8') as f:
            g = f.read()
        titre = re.search(r'<h1[^>]*>(.*?)</h1>', g, re.S)
        lien = re.search(r'Contenu repris de\s*<a[^>]*href="([^"]+)"', g)
        img = (re.search(r'<div class="hero__fond"><img src="([^"]+)"', g)
               or re.search(r'<img src="(https://authentiquegypte[^"]+)"', g))
        chapo = (re.search(r'<p class="hero__chapo">(.*?)</p>', g, re.S)
                 or re.search(r'<div class="prose[^"]*">\s*<p>(.*?)</p>', g, re.S))
        if not (titre and lien):
            continue
        extrait = _texte(chapo.group(1))[:150] if chapo else ''
        cartes.append(
            '<article class="carte">'
            '<a class="carte__img" href="%s" tabindex="-1" aria-hidden="true">'
            '<img src="%s" alt="" loading="lazy" decoding="async"></a>'
            '<div class="carte__c"><h3><a href="%s">%s</a></h3>'
            '%s'
            '<div class="carte__b"><a class="lien-fl" href="%s">Lire le guide</a></div>'
            '</div></article>'
            % (lien.group(1), img.group(1) if img else '', lien.group(1),
               titre.group(1).strip(),
               '<p class="carte__route">%s…</p>' % H.escape(extrait) if extrait else '',
               lien.group(1)))
    return cartes


def reperes_des_cartes(cartes, moule_section):
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
    lignes.append(('Séjours', '%d au choix' % n))
    if prix:
        lignes.append(('À partir de', '%d €' % min(prix)))
    if jours:
        lignes.append(('Durée', ('%d jour%s' % (min(jours), 's' if min(jours) > 1 else ''))
                       if min(jours) == max(jours)
                       else '%d à %d jours' % (min(jours), max(jours))))
    if len(lignes) < 2:
        return ''
    # On reprend le picto du moule pour chaque ligne, dans l'ordre où il les
    # pose : la forme reste celle du gabarit, seules les valeurs changent.
    pictos = re.findall(r'<svg[^>]*>.*?</svg>', moule_section, re.S)
    corps = ''.join(
        '<li>%s<small>%s</small><b>%s</b></li>'
        % (pictos[i % len(pictos)] if pictos else '', H.escape(a), H.escape(b))
        for i, (a, b) in enumerate(lignes))
    return '<section class="reperes"><div class="wrap"><ul>%s</ul></div></section>' % corps


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
    lieu = re.sub(r'^(?:Voyage|Séjour|Excursion)\s+(?:à|au|aux|en|dans le|dans la|sur le)\s+',
                  '', p['titre'])
    titre = {'Destination': 'Les séjours qui passent par %s' % lieu,
             'Profil': 'Les séjours pour %s' % p['titre'].lower(),
             'Blog': 'Les guides à lire avant de partir'}[famille]
    return re.sub(r'(<h2[^>]*>).*?(</h2>)', lambda m: m.group(1) + H.escape(titre) + m.group(2),
                  s, count=1, flags=re.S)


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
    tete = re.sub(r'(<div class="acc">).*?(</div>)',
                  lambda m: m.group(1) + ''.join(p['faq']) + m.group(2),
                  tete, count=1, flags=re.S)
    return tete + reste


# Pas de section « sœurs » montée ici : le moule n'en porte pas d'exploitable,
# et chaque destination comme chaque profil arrive avec la sienne — « Louxor
# se combine bien », « Les autres façons de partir ». Reprendre celle du moule
# afficherait des circuits au bas d'une page destination.


def monter(moule, p, famille, source=None):
    corps = [section_cartes(moule, p, famille, source), p['corps']]
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
    return poser_tete(moule.tete, p, famille) + ''.join(x for x in corps if x) + moule.pied


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
