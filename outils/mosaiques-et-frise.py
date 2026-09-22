#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quatre retouches demandées de vive voix par Rémi le 22/09.

    WP_AUTH='compte:mot de passe' ./outils/mosaiques-et-frise.py [--essai]

1. LE SOMMAIRE sous la colonne collante disparaît. « Le fil du séjour »
   répétait, en miniature, l'itinéraire jour par jour qui se trouve deux
   écrans plus bas ; il allongeait la colonne sans rien apprendre. Les
   ancres de section, elles, restent : ce sont elles qui servent.

2. LA MOSAÏQUE DE PHOTOS devient un damier. Une grande vignette suivie de
   petites, sur un nombre de photos qui ne tombait jamais juste, laissait
   des trous en bas de grille. Désormais : des carrés tous identiques,
   trois ou quatre par rangée selon ce qui tombe juste — donc des rangées
   toujours pleines, sur écran large comme sur téléphone. Les photos
   laissées de côté ne sont
   pas perdues : la dernière vignette porte un « +N photos » et la
   visionneuse, qui n'ouvrait qu'une image à la fois, sait maintenant
   passer de l'une à l'autre. Aucune photo ne quitte la page.

3. LE MUR D'AVIS devient lui aussi un damier de cartes carrées, huit par
   page — deux rangées pleines de quatre. Les colonnes qui coulaient
   librement donnaient des cartes de hauteurs inégales et des fins de
   colonne dans le vide. Le lien « voir les avis sur Google » reste : il
   mène au compte complet.

   Au passage, un défaut découvert en mesurant : trois fiches du Sinaï
   (#8581, #8589, #8594) rangeaient 22 blocs de texte de Mélanie — la
   liste du sac, les repas, les températures, le type de tente — dans le
   mur d'avis, présentés au visiteur comme des avis Google alors que ce
   sont ses propres pages. Ces blocs ne sont nulle part ailleurs : ils
   sont déplacés, mot pour mot, dans une section « Bon à savoir » posée
   juste avant les avis. Rien n'est supprimé, rien n'est réécrit ; leur
   mise en forme d'origine (titres, listes) avait déjà été perdue avant
   cet outil, et je ne l'invente pas. À arbitrer par Rémi.

4. LA FRISE « QUAND PARTIR » ne garde que le mois et les degrés. Les
   commentaires (« excellent, doux ») et l'affluence faisaient trois
   lignes de texte par mois, soit trente-six lignes sur une frise qu'on
   lit d'un coup d'œil. La couleur dit déjà conseillé, chaud ou à éviter,
   et la légende sous la frise l'explique.

Le mur d'avis vit sur 35 pages, les trois autres blocs sur les 14 fiches
programme : l'outil touche chaque page où le bloc existe, pas seulement
celles où le défaut a été remarqué.
"""

import argparse
import os
import re
import sys
import time
from importlib.machinery import SourceFileLoader

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Les blocs repêchés quittent le mur d'avis : ils perdent du même coup la
# dispense d'emoji accordée aux témoignages Google.
_EMO = SourceFileLoader('_emo', os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 'logo-emoji.py')).load_module()
MERE = 7642
Q = '/pages?parent=%d&per_page=100&status=any&context=edit&orderby=menu_order&order=asc'

# Le nombre d'avis affichés. Multiple de quatre ET de deux : les rangées
# restent pleines en 4 colonnes comme en 2.
AVIS_MAX = 8

# Les règles du moule portent le préfixe de l'hôte et trois classes. Une
# règle à deux classes perd, même écrite plus loin dans la cascade. Toutes
# les règles ci-dessous sont donc préfixées, et les classes doublées là où
# une règle du moule vise déjà le même élément.
H = '.elementor-template-canvas '

FEUILLE = (
    '<style data-mosaique="carre">'

    # --- La mosaïque de photos : des carrés, tous pareils, dans un cadre.
    + H + '.pg .galerie.galerie{display:grid;grid-template-columns:repeat(4,1fr);'
    'gap:10px;margin:0 0 14px;padding:10px;background:var(--fond,#F7F7F9);'
    'border:1px solid var(--ligne-pg,#E4E4EA);border-radius:var(--r-l,20px)}'
    + H + '.pg .galerie.galerie[data-col="1"]{grid-template-columns:1fr}'
    + H + '.pg .galerie.galerie[data-col="2"]{grid-template-columns:repeat(2,1fr)}'
    + H + '.pg .galerie.galerie[data-col="3"]{grid-template-columns:repeat(3,1fr)}'
    + H + '.pg .galerie.galerie a{position:relative;display:block;aspect-ratio:1/1;'
    'grid-column:auto;grid-row:auto;border-radius:12px;overflow:hidden;'
    'background:#fff;border:1px solid var(--ligne-pg,#E4E4EA);min-height:0}'
    + H + '.pg .galerie.galerie a:first-child{grid-column:auto;grid-row:auto;aspect-ratio:1/1}'
    + H + '.pg .galerie.galerie img{width:100%;height:100%;object-fit:cover;display:block}'
    + H + '.pg .galerie.galerie .gal__hors{display:none}'
    + H + '.pg .galerie.galerie .gal__plus{position:absolute;inset:0;display:grid;'
    'place-items:center;background:rgba(9,83,96,.62);color:#fff;'
    'font-family:"Manrope",sans-serif;font-weight:800;font-size:1rem;'
    'letter-spacing:.01em;text-align:center;padding:8px}'
    # Deux colonnes seulement sur petit écran : 4, 8, 12… restent des
    # multiples de 2, donc les rangées restent pleines.
    # Sous 900px la grille retombe à deux colonnes — sauf les galeries de
    # moins de quatre photos, qui n'auraient plus de rangée pleine.
    '@media (max-width:900px){' + H + '.pg .galerie.galerie:not([data-petit]),'
    + H + '.pg .galerie.galerie[data-col="3"]:not([data-petit])'
    '{grid-template-columns:repeat(2,1fr)}}'

    # --- Les flèches de la visionneuse.
    + H + '.pg-lb .lb__nav{position:absolute;top:50%;transform:translateY(-50%);'
    'left:auto;right:auto;background:rgba(255,255,255,.16);color:#fff;'
    'border:1px solid rgba(255,255,255,.4);border-radius:50%;width:48px;height:48px;'
    'min-height:48px;padding:0;font-size:1.4rem;line-height:1;display:grid;place-items:center}'
    + H + '.pg-lb .lb__nav--prec{left:18px}'
    + H + '.pg-lb .lb__nav--suiv{right:18px}'
    + H + '.pg-lb .lb__cpt{position:absolute;left:0;right:0;bottom:18px;top:auto;'
    'text-align:center;color:#fff;font-family:"Manrope",sans-serif;font-size:.9rem;'
    'font-variant-numeric:tabular-nums;background:none;border:0;padding:0}'

    # --- Le mur d'avis : un damier de cartes carrées.
    + H + '.pg .mur.mur.mur{display:grid;columns:auto;grid-template-columns:repeat(4,1fr);'
    'gap:16px;align-items:stretch}'
    + H + '.pg .mur.mur.mur .mur__a{display:flex;flex-direction:column;aspect-ratio:1/1;'
    'margin:0;padding:20px;background:#fff;border:1px solid var(--ligne-pg,#E4E4EA);'
    'border-radius:16px;box-shadow:0 1px 3px rgba(12,34,37,.06);overflow:hidden}'
    + H + '.pg .mur.mur.mur .mur__a blockquote{flex:1 1 auto;min-height:0;margin:2px 0 10px;'
    'font-size:.94rem;line-height:1.6;-webkit-line-clamp:7}'
    + H + '.pg .mur.mur.mur .mur__a footer{margin-top:auto;padding-top:12px;'
    'border-top:1px solid var(--ligne-2,#EFEFF3)}'
    '@media (max-width:900px){' + H + '.pg .mur.mur.mur{grid-template-columns:repeat(2,1fr)}}'
    '@media (max-width:620px){' + H + '.pg .mur.mur.mur{grid-template-columns:1fr}'
    + H + '.pg .mur.mur.mur .mur__a blockquote{-webkit-line-clamp:9}}'

    # --- Les blocs repêchés du mur d'avis.
    + H + '.pg .asavoir__l{display:grid;grid-template-columns:repeat(2,1fr);gap:18px;'
    'margin:18px 0 0}'
    + H + '.pg .asavoir__b{background:#fff;border:1px solid var(--ligne-pg,#E4E4EA);'
    'border-radius:16px;padding:18px 20px}'
    + H + '.pg .asavoir__b h3{margin:0 0 8px;font-size:1.02rem}'
    + H + '.pg .asavoir__b p{margin:0;font-size:.95rem;line-height:1.65;color:var(--texte,#5D5D5D)}'
    '@media (max-width:820px){' + H + '.pg .asavoir__l{grid-template-columns:1fr}}'

    # --- La frise : mois et degrés, rien d'autre.
    + H + '.pg .quand__frise li{gap:2px;padding:12px 6px}'
    + H + '.pg .quand__frise .q-t{font-size:.95rem}'
    '</style>'
)

# La visionneuse n'ouvrait qu'une image : sans passage d'une photo à
# l'autre, les photos rangées derrière le « +N » seraient inatteignables.
SCRIPT = """<script data-mosaique="nav">
(function(){
  var lb=document.getElementById('pg-lb'); if(!lb||lb.dataset.nav) return;
  var img=lb.querySelector('img');
  var liste=Array.prototype.slice.call(document.querySelectorAll('.galerie [data-lb]'));
  if(!img||liste.length<2) return;
  lb.dataset.nav='1';
  var i=0;
  function poser(k){
    i=(k+liste.length)%liste.length;
    var a=liste[i];
    img.src=a.getAttribute('href');
    img.alt=a.getAttribute('data-alt')||'';
    cpt.textContent=(i+1)+' / '+liste.length;
  }
  function bouton(classe, libelle, texte, pas){
    var b=document.createElement('button');
    b.type='button'; b.className='lb__nav '+classe;
    b.setAttribute('aria-label', libelle); b.textContent=texte;
    b.addEventListener('click',function(ev){ ev.stopPropagation(); poser(i+pas); });
    lb.appendChild(b); return b;
  }
  var cpt=document.createElement('p');
  cpt.className='lb__cpt'; cpt.setAttribute('aria-live','polite');
  lb.appendChild(cpt);
  bouton('lb__nav--prec','Photo précédente','\\u2039',-1);
  bouton('lb__nav--suiv','Photo suivante','\\u203A',1);
  liste.forEach(function(a,k){
    a.addEventListener('click',function(){ poser(k); });
  });
  document.addEventListener('keydown',function(ev){
    if(!lb.classList.contains('on')) return;
    if(ev.key==='ArrowLeft') poser(i-1);
    if(ev.key==='ArrowRight') poser(i+1);
  });
})();
</script>"""


def _fin(h, debut, nom):
    """L'indice juste après la balise fermante qui va avec celle ouverte en `debut`."""
    p = 0
    for t in re.finditer(r'<(/?)%s\b[^>]*>' % nom, h[debut:]):
        p += 1 if not t.group(1) else -1
        if p == 0:
            return debut + t.end()
    return -1


# ---------------------------------------------------------------- sommaire

def retirer_sommaire(h):
    faits = []
    while True:
        d = h.find('<nav class="somm"')
        if d < 0:
            break
        f = _fin(h, d, 'nav')
        if f < 0:
            break
        h = h[:d] + h[f:]
        faits.append('sommaire retiré')
    return h, faits[:1]


# ---------------------------------------------------------------- galerie

def _photos(bloc):
    """Les ancres de la galerie, débarrassées de nos propres ajouts."""
    out = []
    for m in re.finditer(r'<a\b[^>]*\bdata-lb\b[^>]*>.*?</a>', bloc, re.S):
        a = m.group(0)
        a = re.sub(r'<span class="gal__plus">.*?</span>', '', a, flags=re.S)
        a = a.replace(' class="gal__hors"', '').replace(' hidden', '')
        out.append(a)
    return out


def carrer_galerie(h):
    d = h.find('<section class="galerie')
    if d < 0:
        return h, []
    f = _fin(h, d, 'section')
    if f < 0:
        return h, []
    bloc = h[d:f]
    photos = _photos(bloc)
    n = len(photos)
    if not n:
        return h, []

    # On cherche le découpage qui laisse le moins de photos de côté tout en
    # remplissant chaque rangée — à l'écran large comme sur téléphone, où
    # la grille retombe à deux colonnes. D'où le pas de 4 (4 → 2 → plein)
    # et le pas de 6 pour les grilles de trois (6 → 2 → plein).
    if n < 4:
        montrees, colonnes = n, n
    else:
        par4, par3 = (n // 4) * 4, (n // 6) * 6
        montrees, colonnes = (par3, 3) if par3 > par4 else (par4, 4)

    reste = n - montrees
    visibles = photos[:montrees]
    if reste:
        # La dernière vignette visible porte le compte des photos rangées
        # derrière elle ; la visionneuse va les chercher.
        libelle = '+%d photo%s' % (reste, 's' if reste > 1 else '')
        visibles[-1] = visibles[-1][:-len('</a>')] + \
            '<span class="gal__plus">%s</span></a>' % libelle
    caches = [a.replace('<a ', '<a class="gal__hors" hidden ', 1) for a in photos[montrees:]]

    neuf = ('<section class="galerie" data-col="%d"%s>%s</section>'
            % (colonnes, ' data-petit="1"' if n < 4 else '',
               ''.join(visibles + caches)))
    if neuf == bloc:
        return h, []
    quoi = 'galerie carrée (%d/%d)' % (montrees, n)
    return h[:d] + neuf + h[f:], [quoi]


# ---------------------------------------------------------------- mur d'avis

def _texte(x):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', x)).strip()


def hors_mur(h):
    """Le texte d'une page, mur d'avis retiré."""
    d = h.find('<div class="mur">')
    if d < 0:
        return _texte(h)
    f = _fin(h, d, 'div')
    return _texte(h[:d] + (h[f:] if f > 0 else ''))


def _repecher(intrus):
    """Les blocs de Mélanie égarés dans le mur, remis en prose, mot pour mot.

    Le texte est repris tel quel ; seul le libellé de pied sert de titre
    quand il en est un. « liste » n'en est pas un : c'est la trace d'une
    liste perdue avant cet outil, et un titre inventé serait pire que pas
    de titre.
    """
    blocs = []
    for a in intrus:
        q = re.search(r'<blockquote>(.*?)</blockquote>', a, re.S)
        if not q or not q.group(1).strip():
            continue
        lab = re.search(r'<footer>.*?<b>(.*?)</b>', a, re.S)
        titre = (lab.group(1).strip() if lab else '')
        if titre.lower() in ('', 'liste', 'texte', 'paragraphe'):
            titre = ''
        bloc = ('<div class="asavoir__b">%s<p>%s</p></div>'
                % ('<h3>%s</h3>' % titre if titre else '', q.group(1).strip()))
        blocs.append(_EMO._nettoyer(bloc))
    if not blocs:
        return ''
    return ('<section class="pg-sec asavoir" aria-labelledby="t-asavoir"><div class="wrap">'
            '<p class="eyebrow">Avant de partir</p>'
            '<h2 id="t-asavoir">Bon à savoir</h2>'
            '<div class="asavoir__l">%s</div></div></section>' % ''.join(blocs))


def carrer_mur(h, corpus=''):
    d = h.find('<div class="mur">')
    if d < 0:
        return h, []
    f = _fin(h, d, 'div')
    if f < 0:
        return h, []
    bloc = h[d:f]
    cartes = re.findall(r'<article class="mur__a">.*?</article>', bloc, re.S)
    if not cartes:
        return h, []

    # Un avis Google porte la mention de sa source. Ce qui ne la porte pas
    # n'est pas un avis : c'est du texte de Mélanie rangé là par erreur.
    avis = [c for c in cartes if 'Publié sur Google' in c]
    intrus = [c for c in cartes if 'Publié sur Google' not in c]

    # Deux passages de l'outil d'avis ont pu laisser des doublons.
    vus, uniques = set(), []
    for c in avis:
        q = re.search(r'<blockquote>(.*?)</blockquote>', c, re.S)
        cle = (q.group(1) if q else c).strip()
        if cle in vus:
            continue
        vus.add(cle)
        uniques.append(c)

    gardes = uniques[:AVIS_MAX]
    neuf = '<div class="mur">%s</div>' % ''.join(gardes)
    faits = []
    if neuf != bloc:
        faits.append("mur d'avis carré (%d/%d)" % (len(gardes), len(avis)))
    h = h[:d] + neuf + h[f:]

    # Un bloc dont le texte se lit déjà ailleurs dans la refonte, hors
    # mur d'avis, est un résidu de greffe : sa vraie place existe, celui-ci
    # est une copie sans contexte (le paragraphe sur la dahabeya traînait
    # ainsi sur quatorze pages, PMR et blog compris, alors qu'il est à sa
    # place sur « Mer rouge et plages »). On le retire sans le repêcher.
    residus = 0
    if intrus and corpus:
        vivants = []
        for a in intrus:
            q = re.search(r'<blockquote>(.*?)</blockquote>', a, re.S)
            cle = _texte(q.group(1))[:70] if q else ''
            if cle and cle in corpus:
                residus += 1
            else:
                vivants.append(a)
        intrus = vivants
    if residus:
        faits.append('%d résidu(s) de greffe retiré(s)' % residus)

    if intrus:
        # Si l'outil d'avis a rechargé le mur, un bloc peut déjà avoir été
        # repêché lors d'un passage précédent : on ne le pose pas deux fois.
        deja = h[h.find('class="asavoir"'):] if 'class="asavoir"' in h else ''
        def _neuf(a):
            q = re.search(r'<blockquote>(.*?)</blockquote>', a, re.S)
            return not q or q.group(1).strip()[:60] not in deja
        intrus = [a for a in intrus if _neuf(a)]
    if intrus:
        sauve = _repecher(intrus)
        if sauve:
            # Juste avant la section qui porte le mur.
            pose = h.rfind('<section', 0, h.find('<div class="mur">'))
            if pose < 0:
                pose = h.find('<div class="mur">')
            h = h[:pose] + sauve + h[pose:]
            faits.append('%d bloc(s) repêché(s) du mur' % len(intrus))
    return h, faits


# ---------------------------------------------------------------- frise météo

def alleger_frise(h):
    d = h.find('<ol class="quand__frise">')
    if d < 0:
        return h, []
    f = _fin(h, d, 'ol')
    if f < 0:
        return h, []
    bloc = h[d:f]
    neuf = re.sub(r'<span class="q-c">.*?</span>', '', bloc, flags=re.S)
    neuf = re.sub(r'<small>.*?</small>', '', neuf, flags=re.S)
    if neuf == bloc:
        return h, []
    h = h[:d] + neuf + h[f:]
    # La note de provenance annonçait « températures et affluence » ; sans
    # l'affluence sur la frise, elle annoncerait ce qui n'y est plus.
    h = h.replace('Températures et affluence relevées', 'Températures relevées')
    return h, ['frise réduite aux degrés']


# ----------------------------------------------------------------

def corriger(h, corpus=''):
    faits = []
    for etape in (retirer_sommaire, carrer_galerie, alleger_frise):
        h, f = etape(h)
        faits += f
    h, f = carrer_mur(h, corpus)
    faits += f
    # Une feuille posée par un passage précédent peut être périmée : le
    # damier corrigé sur téléphone, par exemple, ne change pas le balisage.
    # Sans ce test, la correction n'atteindrait jamais les pages qui n'ont
    # que le mur d'avis.
    ancienne = re.search(r'<style data-mosaique="carre">.*?</style>', h, re.S)
    if ancienne and ancienne.group(0) != FEUILLE:
        faits.append('feuille mise à jour')
    if not faits:
        return h, faits
    h = re.sub(r'<style data-mosaique="carre">.*?</style>', '', h, flags=re.S)
    h = re.sub(r'<script data-mosaique="nav">.*?</script>', '', h, flags=re.S)
    h += FEUILLE
    if 'class="galerie' in h:
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

    # Premier temps : ce que la refonte dit déjà hors des murs d'avis.
    brutes = {}
    corpus = []
    for k in pages:
        p_ = dep.appel('GET', '/pages/%d?context=edit' % k['id'])
        brutes[k['id']] = p_
        corpus.append(hors_mur(re.sub(r'<!-- /?wp:html -->\n?', '',
                                      p_['content']['raw'])))
    corpus = ' \u00a7 '.join(corpus)

    n = 0
    for k in pages:
        p_ = brutes[k['id']]
        brut = re.sub(r'<!-- /?wp:html -->\n?', '', p_['content']['raw'])
        neuf, faits = corriger(brut, corpus)
        if not faits:
            continue
        titre = (p_.get('title') or {}).get('raw', '')
        print('   #%-6d %-40s %s' % (k['id'], titre[:40], ' · '.join(faits)))
        if a.essai:
            continue
        n += 1
        corps = '<!-- wp:html -->\n' + neuf + '\n<!-- /wp:html -->'
        for essai in range(4):
            try:
                dep.appel('POST', '/pages/%d' % k['id'], {'content': corps})
                relu = dep.appel('GET', '/pages/%d?context=edit' % k['id'])
                if 'data-mosaique="carre"' in relu['content']['raw']:
                    break
            except SystemExit as motif:
                print('      reprise %d/3 — %s' % (essai + 1, str(motif).splitlines()[0][:60]))
            time.sleep(2 ** essai)
        else:
            print('      ✗ ABANDON #%d' % k['id'])
    print('\n%d page(s) retouchée(s).' % n)


if __name__ == '__main__':
    main()
