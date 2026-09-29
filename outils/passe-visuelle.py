#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Passe visuelle sur les 57 pages de la refonte.

    WP_AUTH='compte:mot de passe' ./outils/passe-visuelle.py [--essai]

Rémi : « à la première lecture visuelle, il y a beaucoup de bug ». Il avait
raison. J'ai miroité les 57 pages en local, je les ai passées à la sonde à
1280 px et à 390 px, puis je les ai regardées une par une. Ce que je corrige
ici, dans l'ordre de ce qui saute aux yeux.

1. Le bouton « Obtenir mon devis » de l'en-tête. Sur 34 pages il n'a aucun
   fond : c'est du texte, pas un bouton. Sur 23 autres il est en #E08A00,
   un orange d'avant la charte, avec du blanc dessus — contraste 2,7, sous
   le plancher de 4,5. La règle fautive, a.btn--or[aria-current], avait
   échappé au passage de charte. Un seul or désormais, #ECAA24 sur #094D60,
   partout.

2. Le plancher typographique de 14 px. 2 567 morceaux de texte passaient
   dessous, jusqu'à 11,52 px : les légendes de carte, les pieds d'avis, les
   prix, les puces des cartes. Le <small> du navigateur vaut 0,8 em et
   personne ne l'avait repris.

3. 209 espaces manquantes après un </strong>, un </b> ou un </a>, sur 47
   pages. « les 8 itinérairesde cette page », « le désert Noiret le mont
   Sinaï », « Réponse sous 48 h(hors vendredi et samedi) ». C'est ma mise
   en gras qui avalait l'espace suivante.

4. Des entités doublement échappées restées visibles dans le résumé des
   étapes : « d&#x27;une oasis », « Désert Noir &amp; Désert Blanc ».

5. Les avis rognés. Sur 34 pages, le mur coupe chaque témoignage à six
   lignes dans une carte carrée : 287 px cachés en médiane, aucun moyen de
   lire la suite. Les avis sont la parole des voyageurs, ils ne peuvent pas
   s'arrêter au milieu d'une phrase. La carte reprend sa hauteur, et un
   « Lire la suite » ouvre celles qui dépassent encore.

6. Le tableau qui sort de l'écran sur mobile (3 pages) : 586 px de large
   dans 390. Le cadre défile maintenant.

7. Les minuscules de « Quand partir » et du blog : titres et phrases sans
   capitale, « l'égypte », « le caire », et la question collée à sa réponse
   dans le chapô.

8. « Mélanie » nommée comme interlocutrice sur les 14 pages programme, alors
   qu'elle a demandé le 28/09 d'y mettre un expert local.

9. Les écarts de vocabulaire d'une page à l'autre : « Dès » contre « À
   partir de », « Aswan » contre « Assouan », « Edfu » contre « Edfou »,
   « Hatchesput » pour Hatchepsout.

10. Le lien des cartes du blog qui répétait le titre tronqué (« 10 choses à
    ne pas faire en Égypt… ») au lieu d'annoncer ce qu'il ouvre.

11. Le chapô d'une carte de profil qui reprenait le texte du premier jour
    (« Arrivée au CaireAccueil à l'aéroport… ») au lieu du séjour.

12. Cinq pages portaient un </div> de trop, et la FAQ s'arrêtait 280 px
    avant le bord que son titre atteignait.
"""

import argparse
import os
import re
import time
from importlib.machinery import SourceFileLoader

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MERE = 7642
Q = '/pages?parent=%d&per_page=100&status=any&context=edit&orderby=menu_order&order=asc'
E = '.elementor-template-canvas '
# Le moule pose ses règles avec trois classes ou plus (.pg .mur.mur.mur …).
# Pour qu'une correction passe devant sans toucher au moule, on répète la
# classe hôte : même élément, même cible, spécificité plus haute.
H = '.elementor-template-canvas' * 6 + ' '
MARQUE = 'data-vis1="1"'

# --- 1 et 2 : la feuille ---------------------------------------------------

# Les classes qui passaient sous 14 px, relevées à la sonde. Les couches
# Leaflet en sont exclues : ce sont les commandes de la carte, pas du texte
# de la page.
PLANCHER = ('.menu__pan small,.mur__a footer,.mur__a footer span,.mur__a footer b,'
            '.jico__e,.jpjs__n,.jpjs__t p,.fac__o small,.fac__tete p,.carte__pin,'
            '.carte__etapes b,.carte__duree,.carte__meta .puce,.prix small,.prix i,'
            '.pan__cle small,.situe__note,.situe__note a,.cartep__note,'
            '.art__ill figcaption,.eyebrow,small,.carte__tag,.vign span,'
            '.fille__nb,.fille__txt span,.etape .vers,.etape .quand,.gens span,'
            '.champ span,.pied__g h3,.devis__act small,.jico__e em')

FEUILLE = (
    '<style ' + MARQUE + '>'
    # 1. un seul or, y compris dans l'en-tête où la règle .pg ne portait pas
    + H + '.btn--or{background:#ECAA24;border-color:#ECAA24;color:#094D60}'
    + H + '.btn--or:hover,' + H + '.btn--or:focus-visible'
    '{background:#FFC758;border-color:#FFC758;color:#094D60}'
    # 2. plancher typographique
    + ','.join(H + c for c in PLANCHER.split(',')) + '{font-size:.875rem}'
    # 5. le mur d'avis reprend sa hauteur
    + H + '.mur__a{aspect-ratio:auto;height:auto}'
    + H + '.mur__a blockquote{-webkit-line-clamp:10;flex:0 1 auto}'
    + H + '.mur__a[data-ouvert] blockquote{-webkit-line-clamp:unset;'
    'display:block;overflow:visible}'
    + H + '.mur__plus{display:none;align-self:flex-start;margin:-6px 0 10px;padding:0;'
    'border:0;background:none;font:inherit;font-size:.875rem;font-weight:700;'
    'color:#10657C;text-decoration:underline;text-underline-offset:2px;cursor:pointer}'
    + H + '.mur__a[data-deborde] .mur__plus{display:inline-block}'
    # 6. le tableau défile au lieu de sortir de l'écran
    + H + '.tab-cadre,' + H + '.mef-tab{overflow-x:auto;'
    '-webkit-overflow-scrolling:touch;max-width:100%}'
    # 15. le panneau « Composez votre Égypte » déborde du hero, qui le
    # rogne : le hero lui fait la place qu'il déborde.
    + H + '.hero:has(.compo){padding-bottom:36px}'
    # 16. le chapô du hero, posé sur une photo claire, gagne l'ombre que
    # le titre portait déjà.
    + H + '.hero .lede,' + H + '.hero__in p,' + H + '.hero p.sous'
    '{text-shadow:0 1px 10px rgba(3,38,45,.85),0 1px 3px rgba(3,38,45,.7)}'
    # 12. la FAQ rejoint le bord que son titre atteint
    + H + '.faqu{max-width:none}'
    + H + '.faqu .faq__r p,' + H + '.faqu .faq__r li{max-width:78ch}'
    '</style>')

SCRIPT = (
    '<script ' + MARQUE + '>(function(){'
    'var cartes=document.querySelectorAll(".mur__a");'
    'if(!cartes.length)return;'
    'function jauger(){Array.prototype.forEach.call(cartes,function(c){'
    'var q=c.querySelector("blockquote");if(!q)return;'
    'if(c.hasAttribute("data-ouvert"))return;'
    'if(q.scrollHeight>q.clientHeight+3)c.setAttribute("data-deborde","1");'
    'else c.removeAttribute("data-deborde");});}'
    'Array.prototype.forEach.call(cartes,function(c){'
    'if(c.querySelector(".mur__plus"))return;'
    'var q=c.querySelector("blockquote");if(!q)return;'
    'var b=document.createElement("button");b.type="button";'
    'b.className="mur__plus";b.textContent="Lire la suite";'
    'b.addEventListener("click",function(){'
    'if(c.hasAttribute("data-ouvert")){c.removeAttribute("data-ouvert");'
    'b.textContent="Lire la suite";jauger();}'
    'else{c.setAttribute("data-ouvert","1");b.textContent="Réduire";}});'
    'q.parentNode.insertBefore(b,q.nextSibling);});'
    'jauger();window.addEventListener("resize",jauger);'
    'if(document.fonts&&document.fonts.ready)document.fonts.ready.then(jauger);'
    '})();</script>')

# --- 3 : les espaces avalées ----------------------------------------------

# Une lettre ou une parenthèse ouvrante collée à la fermeture d'une balise
# en ligne. On laisse la ponctuation, les unités et les apostrophes : là,
# l'absence d'espace est correcte.
ESPACE = re.compile(r'</(?:b|strong|a|em|i)>'
                    r'(?=[A-Za-zÀ-ÖØ-öø-ÿ(]'
                    r'|<(?:small|b|strong|em|i)\b[^>]*>[a-zàâçéèêëîïôûùüÿ(])')

# --- 4 : les entités restées visibles -------------------------------------

DOUBLE = re.compile(r'&amp;(#x27;|#x2019;|#8217;|#039;|nbsp;|amp;|quot;|lt;|gt;)')
# --- 9 : le vocabulaire ----------------------------------------------------

MOTS = [(r'>Dès<', '>À partir de<'),
        (r'>Votre programme de voyage<', '>Les étapes de votre séjour\u00a0:<'),
        (r'\bHatchesput\b', 'Hatchepsout'),
        (r'\bAswan\b', 'Assouan'),
        (r'\bEdfu\b', 'Edfou')]

# --- 7 : les minuscules ----------------------------------------------------

PROPRES = ['Égypte', 'Égyptien', 'Égyptiens', 'Caire', 'Nil', 'Louxor', 'Assouan',
           'Alexandrie', 'Siwa', 'Fayoum', 'Abou Simbel', 'Sinaï', 'Hurghada',
           'Dahab', 'Mer Rouge', 'Nubie', 'Karnak', 'Gizeh', 'Sainte-Catherine',
           'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin', 'Juillet',
           'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']
# Ces mois-là ne prennent la majuscule qu'en début de phrase : on les traite
# à part, la liste ci-dessus ne sert qu'au démarrage d'un bloc.
MOIS = set(m.lower() for m in PROPRES[-12:])
LIEUX = [p for p in PROPRES[:-12]]


def _fin(h, d, nom):
    """Fin de la balise ouverte en d, en comptant la profondeur."""
    p = 0
    for t in re.finditer(r'<(/?)%s\b[^>]*>' % nom, h[d:]):
        p += 1 if not t.group(1) else -1
        if p == 0:
            return d + t.end()
    return -1


def _zones_texte(h):
    """Les bornes des <style> et <script>, où rien ne doit être touché."""
    hors = []
    for m in re.finditer(r'<(style|script)\b', h):
        f = _fin(h, m.start(), m.group(1))
        hors.append((m.start(), f if f > 0 else len(h)))
    return hors


def _dehors(hors, i):
    return not any(a <= i < b for a, b in hors)


def espaces_avalees(h):
    hors = _zones_texte(h)
    bouts, dern, n = [], 0, 0
    for m in ESPACE.finditer(h):
        if not _dehors(hors, m.start()):
            continue
        bouts.append(h[dern:m.end()])
        bouts.append(' ')
        dern = m.end()
        n += 1
    if not n:
        return h, 0
    bouts.append(h[dern:])
    return ''.join(bouts), n


def entites(h):
    """Seules les entités doublement échappées sont fautives : &amp;#x27;
    s'affiche tel quel, &#x27; s'affiche comme une apostrophe et n'a rien à
    se reprocher."""
    neuf = DOUBLE.sub(r'&\1', h)
    return neuf, 0 if neuf == h else len(DOUBLE.findall(h))


# --- 13 : le gras tombé dans les attributs ---------------------------------

# Une passe de mise en gras a couru sur des blocs entiers, attributs compris.
# Résultat : src="…/Voyage-sur-mesure-a-<b>Louxor</b>-en-Egypte.png". L'URL
# ne mène nulle part et la photo ne s'affiche pas.
ATTR = re.compile(r'(\s(?:alt|data-alt|aria-label|href|src|srcset|title|'
                  r'data-reste|data-titre|value|content)=")([^"]*<[a-z/][^"]*)(")',
                  re.I)


def attributs_pollues(h):
    n = 0
    bouts, dern = [], 0
    for m in ATTR.finditer(h):
        propre = re.sub(r'</?[a-z][^>]*>', '', m.group(2))
        if propre == m.group(2):
            continue
        bouts.append(h[dern:m.start(2)])
        bouts.append(propre)
        dern = m.end(2)
        n += 1
    if not n:
        return h, 0
    bouts.append(h[dern:])
    return ''.join(bouts), n


# --- 14 : ce qui n'a rien à faire sur une page vue par la cliente ----------

# Le calque « Maillage ON/OFF » servait à montrer les liens internes pendant
# une présentation. Il flotte au-dessus du contenu et Mélanie le voit.
MAILLAGE = re.compile(r'<button class="mm-btn"[^>]*>.*?</button>', re.S)
MAILLAGE_JS = re.compile(r"<script>\s*/\* calque d'annotation maillage.*?</script>", re.S)
# Deux pages portaient </body></html> au milieu du contenu, suivi d'autres
# feuilles : le navigateur s'en remet, pas l'éditeur.
FERMETURE = re.compile(r'</body>\s*</html>\s*')
# Un <a> sans texte ni image : rien à cliquer, rien à lire.
LIEN_VIDE = re.compile(r'<a\b(?![^>]*\bclass=)[^>]*>\s*</a>')


def menage(h):
    n = 0
    for rx in (MAILLAGE, MAILLAGE_JS, FERMETURE, LIEN_VIDE):
        neuf, k = rx.subn('', h)
        h, n = neuf, n + k
    return h, n


def vocabulaire(h):
    n = 0
    hors = _zones_texte(h)
    for motif, mis in MOTS:
        bouts, dern, k = [], 0, 0
        for m in re.finditer(motif, h):
            if not _dehors(hors, m.start()):
                continue
            bouts.append(h[dern:m.start()])
            bouts.append(mis)
            dern = m.end()
            k += 1
        if k:
            bouts.append(h[dern:])
            h = ''.join(bouts)
            n += k
    return h, n


def _capitaliser(t):
    """Première lettre en capitale, et les noms propres rendus à eux-mêmes."""
    for lieu in sorted(LIEUX, key=len, reverse=True):
        t = re.sub(r'(?<![\w’\'])%s(?![\w])' % re.escape(lieu.lower()), lieu, t)
    t = re.sub(r"(?<![\w’'])l['’]égypte\b", 'l’Égypte', t)
    t = re.sub(r"(?<![\w’'])d['’]égypte\b", 'd’Égypte', t)
    if t and t[0].isalpha() and t[0].islower():
        t = t[0].upper() + t[1:]
    return t


BLOC = re.compile(r'(<(p|h2|h3|h4|summary|li|caption)(?:\s[^>]*)?>)([^<]{6,}?)(?=<)')


def minuscules(h, pid):
    """Rend leurs capitales aux pages qui les avaient perdues (7)."""
    if pid not in (8945, 8952):
        return h, 0
    hors = _zones_texte(h)
    bouts, dern, n = [], 0, 0
    for m in BLOC.finditer(h):
        if not _dehors(hors, m.start()):
            continue
        t = m.group(3)
        if not t.strip() or not t.strip()[0].isalpha() or not t.strip()[0].islower():
            # le texte commence déjà bien, mais des noms propres peuvent
            # traîner en minuscules
            pass
        neuf = _capitaliser(t)
        if neuf == t:
            continue
        bouts.append(h[dern:m.start(3)])
        bouts.append(neuf)
        dern = m.end(3)
        n += 1
    if not n:
        return h, 0
    bouts.append(h[dern:])
    return ''.join(bouts), n


def chapo_colle(h, pid):
    """La question collée à sa réponse dans le chapô (7)."""
    m = re.search(r'(<p class="sous">)([^<]+)(</p>)', h)
    if not m:
        return h, False
    t = m.group(2)
    neuf = re.sub(r'\s*\?([A-Za-zÀ-ÖØ-öø-ÿ])', r' ? \1', t)
    neuf = re.sub(r'\s+\?', ' ?', neuf)
    if neuf == t:
        return h, False
    return h[:m.start(2)] + neuf + h[m.end(2):], True


def expert_local(h):
    """Mélanie n'est plus nommée comme interlocutrice (8)."""
    if '<b>Mélanie</b>' not in h:
        return h, 0
    n = h.count('<b>Mélanie</b>')
    return h.replace('<b>Mélanie</b>', '<b>Votre expert local</b>'), n


def lien_blog(h):
    """Le lien des cartes annonce ce qu'il ouvre (10)."""
    n = 0
    bouts, dern = [], 0
    for m in re.finditer(r'(<a class="lien-fl"[^>]*aria-label="Lire\s*:[^"]*"[^>]*>)'
                         r'([^<]*)(</a>)', h):
        if m.group(2).strip() in ('Lire le guide', ''):
            continue
        bouts.append(h[dern:m.start(2)])
        bouts.append('Lire le guide')
        dern = m.end(2)
        n += 1
    if not n:
        return h, 0
    bouts.append(h[dern:])
    return ''.join(bouts), n


def divs_en_trop(h):
    """Les </div> orphelins que cinq pages portaient (12)."""
    prof, coupes = 0, []
    for m in re.finditer(r'<(/?)div\b[^>]*>', h):
        if m.group(1):
            prof -= 1
            if prof < 0:
                coupes.append((m.start(), m.end()))
                prof = 0
        else:
            prof += 1
    if not coupes:
        return h, 0
    bouts, dern = [], 0
    for a, b in coupes:
        bouts.append(h[dern:a])
        dern = b
    bouts.append(h[dern:])
    return ''.join(bouts), len(coupes)


# --- 17 : les photos qui n'existent plus ----------------------------------

# Huit vignettes de la croisière sur le lac Nasser pointent vers des
# fichiers supprimés de la médiathèque : la galerie n'affiche que des
# icônes cassées. On ne devine pas une photo de remplacement, on retire
# l'entrée et on le dit à Mélanie.
_VU = {}
IMG_SITE = re.compile(r'https://authentiquegypte\.com/wp-content/uploads/[^"\s]+')


def _vivante(url, tete):
    if url not in _VU:
        _VU[url] = tete(url)
    return _VU[url]


VIGNETTE = re.compile(r'<a\b[^>]*\bdata-lb\b[^>]*>\s*<img\b[^>]*>\s*</a>')


def photos_mortes(h, tete):
    if tete is None:
        return h, 0
    n = 0
    bouts, dern = [], 0
    for m in VIGNETTE.finditer(h):
        liens = set(IMG_SITE.findall(m.group(0)))
        if not liens or any(_vivante(u, tete) for u in liens):
            continue
        bouts.append(h[dern:m.start()])
        dern = m.end()
        n += 1
    if not n:
        return h, 0
    bouts.append(h[dern:])
    return ''.join(bouts), n


def corriger(h, pid, ledes, tete=None):
    faits = []
    h, n = espaces_avalees(h)
    if n:
        faits.append('%d espace(s) rendue(s)' % n)
    h, n = entites(h)
    if n:
        faits.append('%d entité(s) décodée(s)' % n)
    h, n = attributs_pollues(h)
    if n:
        faits.append('%d attribut(s) dépollué(s)' % n)
    h, n = vocabulaire(h)
    if n:
        faits.append('%d mot(s) harmonisé(s)' % n)
    h, n = minuscules(h, pid)
    if n:
        faits.append('%d bloc(s) recapitalisé(s)' % n)
    h, ok = chapo_colle(h, pid)
    if ok:
        faits.append('chapô décollé')
    h, n = expert_local(h)
    if n:
        faits.append('expert local (×%d)' % n)
    h, n = lien_blog(h)
    if n:
        faits.append('%d lien(s) de carte' % n)
    h, n = photos_mortes(h, tete)
    if n:
        faits.append('%d photo(s) morte(s) retirée(s)' % n)
    h, n = chapo_carte(h, ledes)
    if n:
        faits.append('%d chapô(s) de carte' % n)
    h, n = menage(h)
    if n:
        faits.append('%d résidu(s) retiré(s)' % n)
    h, n = divs_en_trop(h)
    if n:
        faits.append('%d </div> en trop' % n)
    if MARQUE not in h:
        h += FEUILLE + SCRIPT
        faits.append('feuille visuelle')
    return h, faits


DEBUT_JOUR = re.compile(r'^(Arrivée|Accueil|Transfert|Vol |Départ|Installation)\b')


def chapo_carte(h, ledes):
    """Un chapô de carte qui reprenait le premier jour (11)."""
    n = 0
    bouts, dern = [], 0
    for m in re.finditer(r'<h3><a href="[^"]+"[^>]*>([^<]*)</a></h3>'
                         r'(<p class="carte__route">([^<]*)</p>)', h):
        titre, t = m.group(1), m.group(3)
        if not DEBUT_JOUR.match(t.strip()):
            continue
        lede = ledes.get(_cle(titre))
        bouts.append(h[dern:m.start(3)] if lede else h[dern:m.start(2)])
        if lede:
            bouts.append(lede)
            dern = m.end(3)
        else:
            # Deux séjours n'ont pas de « Vue d'ensemble » : plutôt que de
            # laisser le texte du premier jour tenir lieu de résumé, on
            # retire la ligne. La description manque, elle est à écrire.
            dern = m.end(2)
        n += 1
    if not n:
        return h, 0
    bouts.append(h[dern:])
    return ''.join(bouts), n


def recolter_ledes(pages, brut):
    """L'accroche de chaque page programme, pour réparer les chapôs (11)."""
    out = {}
    for k in pages:
        h = brut.get(k['id'], '')
        m = re.search(r'<p class="prose__tete">([^<]{40,})</p>', h) \
            or re.search(r'<div class="vue__t"><p>([^<]{40,})</p>', h)
        if not m:
            continue
        t = re.sub(r'\s+', ' ', m.group(1)).strip()
        if len(t) > 190:
            t = t[:186].rsplit(' ', 1)[0] + '…'
        out[_cle(k.get('titre', ''))] = t
    return out


def _cle(t):
    """Le titre d'un séjour, réduit à ce qui l'identifie."""
    t = re.sub(r'<[^>]+>', '', t or '')
    t = t.replace('&#x27;', '’').replace('&rsquo;', '’').replace("'", '’')
    t = re.sub(r'^Refonte\s*·\s*[^·]+·\s*', '', t)
    return re.sub(r'\s+', ' ', t).strip().lower()


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
        brut[k['id']] = re.sub(r'<!-- /?wp:html -->\n?', '', p_['content']['raw'])
        k['titre'] = (p_.get('title') or {}).get('raw', '')
    import requests
    S = requests.Session()
    S.verify = '/root/.ccr/ca-bundle.crt'

    def tete(url):
        """La photo répond-elle encore ? Une seule requête par URL."""
        try:
            return S.head(url, timeout=25, allow_redirects=True).status_code < 400
        except Exception:
            return True          # dans le doute, on ne retire rien

    ledes = recolter_ledes(pages, brut)
    print('%d accroche(s) de séjour récoltée(s).\n' % len(ledes))

    n = 0
    for k in pages:
        neuf, faits = corriger(brut[k['id']], k['id'], ledes, tete)
        if not faits:
            continue
        print('   #%-6d %-30s %s' % (k['id'], k['titre'][:30], ' · '.join(faits)[:96]))
        if a.essai:
            continue
        n += 1
        corps = '<!-- wp:html -->\n' + neuf + '\n<!-- /wp:html -->'
        for essai in range(4):
            try:
                dep.appel('POST', '/pages/%d' % k['id'], {'content': corps})
                relu = dep.appel('GET', '/pages/%d?context=edit' % k['id'])
                reste = corriger(re.sub(r'<!-- /?wp:html -->\n?', '',
                                        relu['content']['raw']), k['id'], ledes, tete)[1]
                if not reste:
                    break
                print('      reste : %s' % ' · '.join(reste)[:70])
            except SystemExit as motif:
                print('      reprise %d/3 — %s' % (essai + 1, str(motif).splitlines()[0][:60]))
            time.sleep(2 ** essai)
        else:
            print('      ✗ ABANDON #%d' % k['id'])
    print('\n%d page(s) corrigée(s).' % n)


if __name__ == '__main__':
    main()
