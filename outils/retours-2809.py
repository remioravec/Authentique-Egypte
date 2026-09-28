#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Les retours du 28 septembre que je peux traiter seul.

    WP_AUTH='compte:mot de passe' ./outils/retours-2809.py [--essai]

Cent treize fils déposés en trois jours, plus un mail. Voici ceux qui ne
demandent ni photo, ni prix, ni arbitrage : des défauts avérés, des
retraits désignés, et ses propres mots à reporter.

QUATRE DÉFAUTS QU'ELLE A VUS SANS POUVOIR LES NOMMER

« Attention il y a un bug » revient quatorze fois. Ce ne sont pas
quatorze bugs mais quatre, dont chacun se répète :

1. Un double échappement. « L&amp;#x27;Égypte » s'affiche tel quel au
   lieu de « L'Égypte » : l'apostrophe a été encodée deux fois. Quinze
   occurrences sur quatre pages.

2. Du Markdown resté brut. Les titres du guide « hors des sentiers
   battus » portent « {#oasis-de-dakhla} » en fin de ligne — la syntaxe
   d'ancre du Markdown, jamais convertie. Seize occurrences, dans les
   titres ET dans le sommaire.

3. Un tableau aplati. Sur la page vaccins, les colonnes « À faire » et
   « À éviter » sont devenues une suite de paragraphes : les deux
   en-têtes d'abord, puis les lignes en alternance. Illisible. On
   reconstruit le tableau.

4. Une FAQ qui n'en est pas une. Celle du guide est une simple liste à
   puces où question et réponse se suivent dans le même <li>. On la
   repasse au gabarit du site, en coupant au point d'interrogation.

UN CINQUIÈME DÉFAUT QU'ELLE N'A PAS VU, ET QUI EST LE PLUS GRAVE

Le paragraphe « Sur mesure » écrit pour la mer Rouge — snorkeling,
récifs coralliens, plongées profondes — est recopié sur QUINZE pages.
Quatorze n'ont rien à voir avec la plongée : le Désert blanc, le lac
Nasser, Le Caire, Alexandrie, les quatre pages profil, le blog. Ses
deux « reformuler » pointaient ce texte sans qu'elle en mesure
l'étendue.

Je ne le réécris pas : je le coupe. Sa phrase devient « Nous créons
votre itinéraire unique : choisissez votre rythme, vos escales et vos
expériences. » — la sienne, moins l'énumération qui ne vaut que pour la
mer Rouge. Même principe pour la seconde, calquée sur la variante qu'elle
a elle-même écrite pour le désert.

LES DESCRIPTIONS DE CARTES

« Il n'y a pas de description du programme », sept fois sur la page Le
Caire. Trente-deux cartes sur cent sont dans ce cas. La ligne existe
ailleurs et porte l'itinéraire — « Le Caire → Assouan → Louxor ». On la
remplit de la même façon, à partir des titres de journée du séjour :
c'est factuel, et c'est différent d'une carte à l'autre.
"""

import argparse
import html as H
import json
import os
import re
import time
from importlib.machinery import SourceFileLoader

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MERE = 7642
Q = '/pages?parent=%d&per_page=100&status=any&context=edit&orderby=menu_order&order=asc'
E = '.elementor-template-canvas '
DEVIS = 'https://authentiquegypte.com/sur-mesure/'

CARTE = SourceFileLoader('carte_programme',
                         os.path.join(RACINE, 'outils', 'carte-programme.py')).load_module()


def _fin(h, d, nom):
    p = 0
    for t in re.finditer(r'<(/?)%s\b[^>]*>' % nom, h[d:]):
        p += 1 if not t.group(1) else -1
        if p == 0:
            return d + t.end()
    return -1


def _porteur(h, balise, texte, depuis=0):
    """Le plus petit élément `balise` qui contient vraiment `texte`."""
    i = h.find(texte, depuis)
    if i < 0:
        return None
    cand = None
    for m in re.finditer(r'<%s\b[^>]*>' % balise, h[:i]):
        f = _fin(h, m.start(), balise)
        if f > i + len(texte):
            cand = (m.start(), f)
    if not cand or texte not in h[cand[0]:cand[1]]:
        return None
    return cand


def _retirer(h, balise, texte):
    # Un titre est cité deux fois : dans le sommaire d'abord, dans le
    # corps ensuite. Chercher le texte tout court tombe sur le lien du
    # sommaire, qu'aucun <h2> n'entoure — et le retrait échoue en
    # silence. Pour un titre, on vise la balise elle-même.
    if re.fullmatch(r'h[1-6]', balise):
        m = re.search(r'<%s\b[^>]*>(?:(?!</%s>).)*?%s(?:(?!</%s>).)*?</%s>'
                      % (balise, balise, re.escape(texte), balise, balise), h, re.S)
        return (h[:m.start()] + h[m.end():], True) if m else (h, False)
    c = _porteur(h, balise, texte)
    if not c:
        return h, False
    return h[:c[0]] + h[c[1]:], True


# --- 1. le double échappement ----------------------------------------

def desechapper(h):
    """« L&amp;#x27;Égypte » s'affiche tel quel : l'apostrophe a été
    encodée deux fois. On retire la couche de trop, pas les deux."""
    neuf = re.sub(r'&amp;(#x27;|#8217;|#039;|nbsp;|amp;)', r'&\1', h)
    return neuf, neuf != h


# --- 2. le markdown resté brut ---------------------------------------

def sans_markdown(h):
    """« {#oasis-de-dakhla} » en fin de titre : syntaxe d'ancre Markdown.

    Les titres portent déjà un id="sN" et le sommaire y renvoie : la
    mention ne sert à rien, elle s'affiche seulement.
    """
    neuf = re.sub(r'\s*\{#[^}<>]{1,60}\}', '', h)
    return neuf, neuf != h


# --- 3. le tableau « À faire / À éviter » ----------------------------

def tableau_faire_eviter(h):
    """Deux colonnes aplaties en une suite de paragraphes.

    L'ordre du document dit tout : les deux en-têtes, puis les lignes en
    alternance. On ne devine rien, on relit la suite telle qu'elle est.
    """
    d = h.find('<p class="">À faire</p><p class="">À éviter</p>')
    if d < 0:
        return h, False
    # Le tableau s'arrête au titre suivant. On borne d'abord, on lit
    # ensuite : chercher les paragraphes d'abord et s'arrêter « au
    # premier titre rencontré » revenait à repérer un texte par sa
    # première occurrence dans toute la page, et le tableau avalait la
    # section d'après.
    titre = re.search(r'<h[1-6]\b', h[d:])
    fin = d + (titre.start() if titre else len(h) - d)
    zone = h[d:fin]
    paras = re.findall(r'<p class="">(.*?)</p>', zone, re.S)
    if len(paras) < 4:
        return h, False
    lignes = [(paras[i], paras[i + 1]) for i in range(2, len(paras) - 1, 2)]
    if not lignes:
        return h, False
    fin = fin - d
    corps = ''.join('<tr><td>%s</td><td>%s</td></tr>' % (a, b) for a, b in lignes)
    table = ('<div class="tabx"><table class="tabx__t">'
             '<thead><tr><th scope="col">À faire</th>'
             '<th scope="col">À éviter</th></tr></thead>'
             '<tbody>%s</tbody></table></div>' % corps)
    return h[:d] + table + h[d + fin:], True


FEUILLE_TAB = (
    E + '.pg .tabx{overflow-x:auto;margin:20px 0}'
    + E + '.pg .tabx__t{width:100%;border-collapse:collapse;font-size:.97rem;'
    'line-height:1.55;min-width:460px}'
    + E + '.pg .tabx__t th{background:var(--or-fond,#FEEDDC);'
    'color:var(--nuit-900,#095360);font-family:"Manrope",sans-serif;'
    'font-weight:700;text-align:left;padding:12px 16px;'
    'border:1px solid #F3D9A8}'
    + E + '.pg .tabx__t td{padding:12px 16px;border:1px solid var(--ligne-pg,#E4E4EA);'
    'vertical-align:top;color:var(--texte,#5D5D5D)}')


# --- 4. la FAQ du guide ----------------------------------------------

def faq_du_guide(h):
    """Une liste à puces où question et réponse se suivent dans le <li>.

    On coupe au premier point d'interrogation : ce qui précède est la
    question, ce qui suit la réponse. Sans point d'interrogation, on ne
    touche à rien plutôt que de couper au hasard.
    """
    m = re.search(r'(<h2 id="s\d+">FAQ[^<]*</h2>)(<ul>.*?</ul>)', h, re.S)
    if not m:
        return h, False
    items = re.findall(r'<li>(.*?)</li>', m.group(2), re.S)
    qs = []
    for it in items:
        c = re.match(r'(.*?\?)\s*(.*)', it, re.S)
        if not c:
            return h, False
        qs.append((c.group(1).strip(), c.group(2).strip()))
    if not qs:
        return h, False
    bloc = ''.join(
        '<details class="faq__q"%s><summary>%s</summary>'
        '<div class="faq__r"><p>%s</p></div></details>'
        % (' open' if i == 0 else '', q, r) for i, (q, r) in enumerate(qs))
    return h.replace(m.group(0), m.group(1) + '<div class="faqu">%s</div>' % bloc), True


# --- 5. le paragraphe de plongée, là où il n'a rien à faire -----------

PLONGEE_AV = ("Nous créons votre itinéraire unique : choisissez votre rythme, vos "
              "escales et vos expériences sous-marines. Du snorkeling parmi les "
              "récifs coralliens aux plongées profondes , des villages côtiers aux "
              "sites sous-marins spectaculaires , chaque détail est pensé pour vous.")
PLONGEE_AP = ("Nous créons votre itinéraire unique : choisissez votre rythme, vos "
              "escales et vos expériences. Chaque détail est pensé pour vous.")
EQUIPAGE_AV = ("Avec nos équipages locaux passionnés , vivez une expérience de "
               "plongée authentique , celle qui vous ressemble.")
EQUIPAGE_AP = ("Guidés par nos équipes locales passionnées, vivez l’Égypte dans "
               "toute son authenticité.")

# La mer Rouge garde son texte : c'est le sien, et il y est juste.
MER_ROUGE = (8597, 8590)


def hors_sujet_plongee(h, pid):
    if pid in MER_ROUGE:
        return h, False
    fait = False
    for av, ap in ((PLONGEE_AV, PLONGEE_AP), (EQUIPAGE_AV, EQUIPAGE_AP)):
        if av in h:
            h = h.replace(av, ap)
            fait = True
    return h, fait


# --- 6. la ligne d'itinéraire des cartes -----------------------------

def _route_de(pages, titre):
    """L'itinéraire d'un séjour, lu sur sa propre page."""
    g = pages.get(titre)
    if not g:
        return ''
    etapes = CARTE.etapes_de(g)
    return ' → '.join(etapes) if len(etapes) > 1 else ''


VIDE = re.compile(r'<p class="carte__route"[^>]*>\s*</p>')


def routes_des_cartes(h, pages):
    """« Il n'y a pas de description du programme » : on pose l'itinéraire.

    Le défaut n'est pas toujours une ligne absente. Le plus souvent la
    ligne est là mais vide — « <p class="carte__route"></p> » — et elle
    réserve sa place dans la carte sans rien dire. C'est ce blanc qu'elle
    voit. On traite les deux cas.
    """
    morceaux = re.split(r'(?=<article class="carte)', h)
    n = 0
    for i, c in enumerate(morceaux):
        if not c.startswith('<article class="carte'):
            continue
        vide = VIDE.search(c)
        if 'carte__route' in c and not vide:
            continue
        m = re.search(r'<h3[^>]*>(?:<a[^>]*>)?(.*?)(?:</a>)?</h3>', c, re.S)
        if not m:
            continue
        titre = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', m.group(1))).strip()
        route = _route_de(pages, H.unescape(titre))
        if not route:
            continue
        ligne = '<p class="carte__route">%s</p>' % H.escape(route)
        morceaux[i] = (VIDE.sub(ligne, c, count=1) if vide
                       else c[:m.end()] + ligne + c[m.end():])
        n += 1
    return (''.join(morceaux), n) if n else (h, 0)


# --- 7. les renommages qu'elle a dictés ------------------------------

RENOMME = [
    ('>Continuer<', '>Découvrir<', '#10745, #10750'),
    ('>Paysages uniques<', '>Assistance H24<', '#10823'),
    ('>Découverte culturelle complète<', '>Conseils par experts locaux<', '#10824'),
    ('voyage de vos rêves', 'voyage sur mesure', '#10741'),
    ('Voyage de vos rêves', 'Voyage sur mesure', '#10741'),
]


# --- 8. les retraits désignés ----------------------------------------

RETRAITS = {
    8924: [('details', 'Quels conseils pour une visite optimale', '#10786')],
    8925: [('details', 'Que prévoir pour un séjour équilibré', '#10777'),
           ('details', 'Quels musées visiter au Caire', '#10778')],
    8926: [('details', 'Y a-t-il un âge idéal pour voyager en Égypte à deux', '#10789'),
           ('p', 'Les couples adorent', '#10790')],
    8927: [('p', 'Pensé pour eux', '#10843')],
    8949: [('p', 'Validé par Authentique Égypte', '#10830'),
           ('h4', 'Votre feuille de route santé personnalisée', '#10831'),
           ('p', 'Côté Vaccins (À vérifier avant le départ)', '#10832'),
           ('p', 'Le conseil de notre équipe locale', '#10833'),
           ('p', 'Dans votre trousse à pharmacie', '#10834'),
           ('p', 'aurez compris, la question du vaccin', '#10835'),
           ('p', 'En choisissant de partir avec notre agence', '#10836')],
    8951: [('h3', 'En résumé', '#10841')],
}

# « enleve c'est une activité tres populaire » : elle vise la locution,
# pas la question — sinon la réponse entière disparaîtrait. Je retire la
# locution et je le lui dis dans le fil.
CLAUSES = {8924: [('Oui, c’est une activité très populaire, notamment',
                   'Oui, notamment', '#10784')]}


def _sommaire(h, texte):
    """Retirer un titre casse son entrée de sommaire : on l'emporte."""
    m = re.search(r'<li><a href="#s\d+">[^<]*%s[^<]*</a></li>' % re.escape(texte[:34]), h)
    return (h.replace(m.group(0), ''), True) if m else (h, False)


# --- 9. ses ajouts, mot pour mot -------------------------------------

AJOUTS = {
    8951: [("Croisières sur le Nil avec cabines aménagées PMR",
            "<em>Tous les sites desservis par la croisière ne sont pas accessibles.</em>",
            '#10838'),
           ("Véhicules équipés de rampes disponibles sur demande",
            "<em>Selon disponibilités dans les destinations.</em>", '#10839'),
           ("L’accompagnant aidant : pour l’aide pratique (déplacements, transferts, "
            "assistance quotidienne)", "<em>Optionnel.</em>", '#10840')],
}


def ajouts_dictes(h, pid):
    faits = []
    for ancre, ajout, fil in AJOUTS.get(pid, []):
        if ajout in h or ancre not in h:
            continue
        i = h.find(ancre) + len(ancre)
        # On se pose juste après la fin de l'élément qui porte l'ancre.
        j = h.find('<', i)
        h = h[:j] + ' ' + ajout + h[j:] if j > 0 else h
        faits.append('mention ajoutée (%s)' % fil)
    return h, faits


# --- 10. le bouton de devis ------------------------------------------

BOUTON = ('<p class="cta-devis"><a class="btn btn--or" href="%s">'
          'Demander mon devis</a></p>' % DEVIS)

DEVIS_SUR = {
    8598: 'Demandez un Devis Personnalisé',      # #10742
    8926: 'Votre voyage, vos envies, notre expertise.',   # #10794
    8952: 'Votre voyage, vos envies, notre expertise.',   # #10825
    8925: 'Votre voyage, vos envies, notre expertise.',   # #10780
}


def bouton_devis(h, pid):
    ancre = DEVIS_SUR.get(pid)
    if not ancre or 'cta-devis' in h:
        return h, []
    c = _porteur(h, 'section', ancre)
    if not c:
        return h, []
    # Dans le .wrap de la section, à la fin — pas après elle.
    ferme = h.rfind('</div></section>', c[0], c[1])
    pose = ferme if ferme > 0 else c[1] - len('</section>')
    return h[:pose] + BOUTON + h[pose:], ['bouton vers la demande de devis']


# --- 11. la mention OpenStreetMap, plus discrète ----------------------

FEUILLE_OSM = (E + '.pg .cartep__note,' + E + '.pg .situe__note'
               '{font-size:.72rem;opacity:.72}')


# --- 12. le voile du hero --------------------------------------------

# « La photo principale est trop sombre, j'ai l'impression qu'il y a un
# filtre. » Elle a raison : à 80 % à gauche c'est un aplat, et sur
# mobile une seconde règle remontait à 78 %. Alléger encore ne suffit
# pas — il faut changer de principe. Le voile ne couvre plus toute
# l'image : il devient un dégradé qui part du bas, là où le texte se
# trouve, et laisse le haut de la photo intact.
# « La photo principale est trop sombre, j'ai l'impression qu'il y a un
# filtre. » Elle a raison, et le premier correctif que j'ai essayé était
# pire : un dégradé parti du bas ramenait le contraste du titre blanc à
# 2,1 — sous le plancher de 3,0, donc illisible.
#
# Le texte du hero occupe toute la hauteur (le titre à 15-39 %, le bloc
# prix jusqu'à 90 %) mais seulement les deux tiers gauche. Le voile suit
# donc cette forme : dense à gauche, où il faut lire, et NUL à droite,
# où la photo reprend ses couleurs. L'ancien laissait encore 46 % de
# voile sur ce bord ; c'est ce reste-là qui donnait le « filtre ».
FEUILLE_VOILE = (
    E + '.pg .hero::after{background:'
    # Le titre court jusqu'à 63 % de la largeur : le dégradé tient sa
    # densité jusque-là et ne s'ouvre qu'après. Le faire descendre plus
    # tôt laissait la fin du titre sur une photo claire — c'est ce qui
    # ramenait le contraste à 2,9 sur la page blog.
    'linear-gradient(94deg,rgba(6,61,71,.90) 0%,rgba(6,61,71,.86) 40%,'
    'rgba(6,61,71,.78) 64%,rgba(6,61,71,.28) 78%,rgba(6,61,71,.04) 90%,'
    'rgba(6,61,71,0) 100%)}'
    # L'ombre portée assombrit le pourtour immédiat des lettres sans
    # toucher au reste de l'image : c'est elle qui permet de garder le
    # voile aussi clair.
    + E + '.pg .hero h1{text-shadow:0 2px 16px rgba(3,38,45,.92),'
    '0 1px 3px rgba(3,38,45,.75)}'
    # Sur téléphone la colonne de texte prend toute la largeur : le
    # dégradé redevient vertical, mais s'ouvre en haut.
    '@media (max-width:860px){' + E + '.pg .hero::after{background:'
    'linear-gradient(182deg,rgba(6,61,71,.28) 0%,rgba(6,61,71,.66) 26%,'
    'rgba(6,61,71,.74) 100%)}}')

FEUILLE = ('<style data-retours="28-09">' + FEUILLE_TAB + FEUILLE_OSM
           + FEUILLE_VOILE + E + '.pg .cta-devis{margin:22px 0 0}'
           + E + '.pg .faqu .faq__r p{margin:0}</style>')


def corriger(h, pid, pages):
    faits = []

    h, ok = desechapper(h)
    if ok:
        faits.append('double échappement corrigé (#10765, #10818)')
    h, ok = sans_markdown(h)
    if ok:
        faits.append('markdown brut retiré (#10796-10802)')
    h, ok = tableau_faire_eviter(h)
    if ok:
        faits.append('tableau à faire / à éviter reconstruit (#10827)')
    h, ok = faq_du_guide(h)
    if ok:
        faits.append('FAQ au gabarit du site (#10803-10807)')
    h, ok = hors_sujet_plongee(h, pid)
    if ok:
        faits.append('texte de plongée hors sujet coupé (#10779, #10825)')

    h, n = routes_des_cartes(h, pages)
    if n:
        faits.append('%d itinéraire(s) de carte posé(s) (#10767-10773)' % n)

    for av, ap, fil in RENOMME:
        if av in h:
            h = h.replace(av, ap)
            faits.append('« %s » → « %s » (%s)' % (av.strip('<>'), ap.strip('<>'), fil))

    for balise, texte, fil in RETRAITS.get(pid, []):
        h2, ok = _retirer(h, balise, texte)
        if ok:
            h = h2
            if balise in ('h2', 'h3', 'h4'):
                h, _ = _sommaire(h, texte)
            faits.append('retiré (%s)' % fil)

    for av, ap, fil in CLAUSES.get(pid, []):
        if av in h:
            h = h.replace(av, ap)
            faits.append('locution retirée (%s)' % fil)

    h, f = ajouts_dictes(h, pid); faits += f
    h, f = bouton_devis(h, pid); faits += f

    ancienne = re.search(r'<style data-retours="28-09">.*?</style>', h, re.S)
    if ancienne and ancienne.group(0) != FEUILLE:
        faits.append('feuille mise à jour')
    elif not ancienne:
        faits.append('voile du hero repensé, tableau, mention OSM')
    if not faits:
        return h, faits
    h = re.sub(r'<style data-retours="28-09">.*?</style>', '', h, flags=re.S)
    return h + FEUILLE, faits


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

    brut = {}
    for k in pages:
        p_ = dep.appel('GET', '/pages/%d?context=edit' % k['id'])
        brut[k['id']] = (re.sub(r'<!-- /?wp:html -->\n?', '', p_['content']['raw']),
                         (p_.get('title') or {}).get('raw', ''))

    # Les séjours, retrouvés par leur h1 : c'est là que vit l'itinéraire.
    par_titre = {}
    for h, _ in brut.values():
        m = re.search(r'<h1[^>]*>(.*?)</h1>', h, re.S)
        if m:
            par_titre[H.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', m.group(1))).strip())] = h

    n = 0
    for pid, (h, titre) in brut.items():
        neuf, faits = corriger(h, pid, par_titre)
        if not faits:
            continue
        print('   #%-6d %-32s %s' % (pid, titre[:32], ' · '.join(faits)[:100]))
        if a.essai:
            continue
        n += 1
        corps = '<!-- wp:html -->\n' + neuf + '\n<!-- /wp:html -->'
        for essai in range(4):
            try:
                dep.appel('POST', '/pages/%d' % pid, {'content': corps})
                relu = dep.appel('GET', '/pages/%d?context=edit' % pid)
                if 'data-retours="28-09"' in relu['content']['raw']:
                    break
            except SystemExit as motif:
                print('      reprise %d/3 — %s' % (essai + 1, str(motif).splitlines()[0][:60]))
            time.sleep(2 ** essai)
        else:
            print('      ✗ ABANDON #%d' % pid)
    print('\n%d page(s) corrigée(s).' % n)


if __name__ == '__main__':
    main()
