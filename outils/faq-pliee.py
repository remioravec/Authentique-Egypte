#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quatre retouches demandées de vive voix par Rémi le 22/09, au soir.

    WP_AUTH='compte:mot de passe' ./outils/faq-pliee.py [--essai]

1. LE PRIX EN DOUBLE dans la colonne collante. Depuis que les repères ont
   pris la tête de la colonne, le vieux bloc « À partir de … / Personne »
   répète le même chiffre trois lignes plus bas. Il part ; le repère
   reste. Dix fiches.

2. LES ANCRES DE SECTION sous la colonne collante — « Vue d'ensemble,
   Jour par jour, Questions » — partent aussi. Avec le sommaire retiré ce
   matin, c'était le dernier doublon d'une navigation que la page rend
   déjà en la faisant défiler. Quatorze fiches.

3. LA FAQ COUPÉE EN DEUX. Sur vingt-sept pages, les questions propres au
   séjour et le tronc commun vivaient dans deux blocs séparés par un
   titre intermédiaire — « Organiser, payer, modifier son voyage ». On
   lisait la FAQ, elle s'arrêtait, elle reprenait : Rémi l'a vu sur
   Fayoum. Les deux blocs n'en font plus qu'un, sans titre au milieu.

4. LA FAQ SE PLIE. Trente-six questions d'affilée sur certaines pages,
   c'est un mur. Cinq restent ouvertes à la lecture, les autres attendent
   derrière un bouton qui dit combien il en reste. Rien n'est supprimé :
   le bouton les déplie toutes, et les replie.

Et, tant qu'on y est : le texte des cartes d'avis Google passe de .94 à
1.02 rem, comme demandé. La carte restant carrée, le témoignage est borné
à six lignes au lieu de sept — sinon il déborderait de son cadre.
"""

import argparse
import os
import re
import time
from importlib.machinery import SourceFileLoader

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MERE = 7642
Q = '/pages?parent=%d&per_page=100&status=any&context=edit&orderby=menu_order&order=asc'

# Le nombre de questions ouvertes d'emblée.
VISIBLES = 5

H = '.elementor-template-canvas '

FEUILLE = (
    '<style data-faq="pliee">'
    # Les questions au-delà des cinq premières attendent leur tour.
    + H + 'section[data-plie] .faq__q--plus{display:none}'
    + H + 'section[data-plie].faq--ouverte .faq__q--plus{display:block}'
    + H + '.pg-sec .faqu + .faqu{margin-top:0}'
    + H + '.pg .faq__plus{display:block;width:100%;margin:14px 0 0;padding:14px 20px;'
    'background:#fff;color:var(--teal-txt,#106D7C);border:1px solid var(--ligne-pg,#E4E4EA);'
    'border-radius:14px;font-family:"Manrope",sans-serif;font-weight:700;font-size:1rem;'
    'min-height:48px;cursor:pointer;transition:background .2s,border-color .2s}'
    + H + '.pg .faq__plus:hover{background:var(--teal-fond,#EAF6F9);'
    'border-color:var(--teal-txt,#106D7C)}'
    # Le texte des avis, un cran plus gros ; la carte reste carrée, donc
    # le témoignage tient sur une ligne de moins.
    + H + '.pg .mur.mur.mur .mur__a blockquote{font-size:1.02rem;-webkit-line-clamp:6}'
    '@media (max-width:620px){'
    + H + '.pg .mur.mur.mur .mur__a blockquote{-webkit-line-clamp:9}}'
    '</style>'
)

SCRIPT = """<script data-faq="pliee">
(function(){
  document.querySelectorAll('section[data-plie]').forEach(function(f){
    var b=f.querySelector('.faq__plus'); if(!b) return;
    var reste=b.getAttribute('data-reste')||'';
    b.addEventListener('click',function(){
      var ouvert=f.classList.toggle('faq--ouverte');
      b.setAttribute('aria-expanded', ouvert?'true':'false');
      b.textContent = ouvert ? 'Afficher moins de questions' : reste;
      if(!ouvert){
        f.querySelectorAll('.faq__q--plus[open]').forEach(function(d){ d.open=false; });
        f.scrollIntoView({block:'start', behavior:'smooth'});
      }
    });
  });
})();
</script>"""


def _fin(h, debut, nom):
    p = 0
    for t in re.finditer(r'<(/?)%s\b[^>]*>' % nom, h[debut:]):
        p += 1 if not t.group(1) else -1
        if p == 0:
            return debut + t.end()
    return -1


# ------------------------------------------------- le prix en double

def prix_unique(h):
    d = h.find('<aside class="pan">')
    if d < 0:
        return h, []
    f = _fin(h, d, 'aside')
    if f < 0:
        return h, []
    aside = h[d:f]
    # On ne retire le vieux bloc que si le repère porte bien le prix :
    # sinon on effacerait la seule mention du tarif.
    tete = aside[:aside.find('</div></div>') + 12] if '<div class="pan__cles">' in aside else ''
    if '€' not in tete:
        return h, []
    neuf = re.sub(r'<p class="pan__prix"[^>]*>.*?</p>', '', aside, flags=re.S)
    if neuf == aside:
        return h, []
    return h[:d] + neuf + h[f:], ['prix en double retiré']


# ------------------------------------------------- les ancres de section

def sans_ancres(h):
    faits = []
    while True:
        d = h.find('<nav class="pg-anc"')
        if d < 0:
            break
        f = _fin(h, d, 'nav')
        if f < 0:
            break
        h = h[:d] + h[f:]
        faits = ['ancres de section retirées']
    return h, faits


# ------------------------------------------------- la FAQ

def plier_faq(h):
    """Cinq questions ouvertes, le reste derrière un bouton.

    On ne reconstruit pas le conteneur : sur les quatre pages de profil,
    la dernière question est fermée APRÈS le div qui la contient
    (« …</div></div></div></details></div> »), un balisage que le
    navigateur répare en silence mais qu'un compteur de profondeur ne
    peut pas suivre — s'y fier faisait disparaître une question. On se
    contente donc de marquer la section et de classer les questions au
    fil du texte, sans rien déplacer.
    """
    d = h.find('<div class="faqu"')
    if d < 0:
        return h, []
    s_ = h.rfind('<section', 0, d)
    if s_ < 0:
        return h, []
    f_ = _fin(h, s_, 'section')
    if f_ < 0:
        return h, []
    bloc = h[s_:f_]

    # On repart des questions nues : le pliage d'un passage précédent ne
    # doit pas se superposer à lui-même.
    bloc = bloc.replace('<details class="faq__q faq__q--plus">',
                        '<details class="faq__q">')
    bloc = re.sub(r'<button type="button" class="faq__plus".*?</button>', '',
                  bloc, flags=re.S)

    # Le titre de la FAQ a perdu son ancre quand la FAQ a été refondue, et
    # le lien « Le détail, question par question » de la section tarif
    # pointe toujours dessus : dix fiches avec un lien qui ne mène nulle
    # part. On la repose.
    if 'id="t-faq"' not in bloc:
        bloc = re.sub(r'<h2(?![^>]*\bid=)>', '<h2 id="t-faq">', bloc, count=1)

    ouvertures = [m.start() for m in re.finditer(r'<details class="faq__q">', bloc)]
    total = len(ouvertures)
    if not total:
        return h, []

    # De la fin vers le début : chaque remplacement décale ce qui suit.
    for pos in reversed(ouvertures[VISIBLES:]):
        bloc = (bloc[:pos] + '<details class="faq__q faq__q--plus">'
                + bloc[pos + len('<details class="faq__q">'):])

    reste = total - VISIBLES
    if reste > 0:
        libelle = ('Voir les %d autres questions' % reste) if reste > 1 \
            else 'Voir la dernière question'
        bouton = ('<button type="button" class="faq__plus" aria-expanded="false" '
                  'data-reste="%s">%s</button>' % (libelle, libelle))
        dernier = bloc.rfind('</details>')
        coupe = dernier + len('</details>')
        bloc = bloc[:coupe] + bouton + bloc[coupe:]
        tete = re.match(r'<section\b[^>]*>', bloc).group(0)
        if 'data-plie' not in tete:
            bloc = tete[:-1] + ' data-plie>' + bloc[len(tete):]

    if bloc == h[s_:f_]:
        return h, []
    quoi = ['FAQ pliée (%d/%d)' % (min(VISIBLES, total), total)]
    if 'id="t-faq"' not in h[s_:f_] and 'id="t-faq"' in bloc:
        quoi.append('ancre #t-faq reposée')
    return h[:s_] + bloc + h[f_:], quoi


def sans_titre_milieu(h):
    if '<p class="faq__t">' not in h:
        return h, []
    return re.sub(r'<p class="faq__t">.*?</p>', '', h, flags=re.S), ['titre du milieu retiré']


# -------------------------------------------------

def corriger(h):
    faits = []
    for etape in (prix_unique, sans_ancres, sans_titre_milieu, plier_faq):
        h, f = etape(h)
        faits += f
    # Le grossissement des avis ne change pas le balisage : sans ce test,
    # il n'atteindrait jamais les pages qui n'ont rien d'autre à corriger.
    ancienne = re.search(r'<style data-faq="pliee">.*?</style>', h, re.S)
    if ancienne and ancienne.group(0) != FEUILLE:
        faits.append('feuille mise à jour')
    elif not ancienne and '<div class="mur">' in h:
        faits.append('feuille posée')
    if not faits:
        return h, faits
    h = re.sub(r'<style data-faq="pliee">.*?</style>', '', h, flags=re.S)
    h = re.sub(r'<script data-faq="pliee">.*?</script>', '', h, flags=re.S)
    h += FEUILLE
    if 'data-plie>' in h:
        h += SCRIPT
    return h, faits


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
        neuf, faits = corriger(brut)
        if not faits:
            continue
        print('   #%-6d %-40s %s' % (k['id'], (p_.get('title') or {}).get('raw', '')[:40],
                                     ' · '.join(faits)))
        if a.essai:
            continue
        n += 1
        corps = '<!-- wp:html -->\n' + neuf + '\n<!-- /wp:html -->'
        for essai in range(4):
            try:
                dep.appel('POST', '/pages/%d' % k['id'], {'content': corps})
                relu = dep.appel('GET', '/pages/%d?context=edit' % k['id'])
                if 'data-faq="pliee"' in relu['content']['raw']:
                    break
            except SystemExit as motif:
                print('      reprise %d/3 — %s' % (essai + 1, str(motif).splitlines()[0][:60]))
            time.sleep(2 ** essai)
        else:
            print('      ✗ ABANDON #%d' % k['id'])
    print('\n%d page(s) retouchée(s).' % n)


if __name__ == '__main__':
    main()
