#!/usr/bin/env python3
"""
L'inventaire daté d'une page catégorie — « type de séjour ».

Même règle que pour les fiches : ce module ne rend rien et ne réécrit
rien, il RELÈVE. Le générateur ne travaillera que sur ce fichier.

Ce que la page catégorie porte, et que l'œil ne voit pas dans le HTML
d'Elementor :

1. **Les séjours de la famille**, dans l'ordre où la page les range —
   titre, lien, photo. Le prix et la durée, eux, ne sont PAS sur cette
   page : ils viennent des inventaires de fiches, déjà relevés.
2. **Les quatre arguments** de « Pourquoi voyager avec nous ? », qui
   sont des titres d'icônes sans texte : quatre mots, pas une phrase.
3. **Le bloc éditorial** et **l'appel final**, avec leurs paragraphes.
4. **La FAQ**, dans un accordéon `jkit_accordion` : la question est un
   `.card-header .title`, la réponse un `.card-body`. Les cinq réponses
   sont dans le HTML, contrairement à celles des fiches.
5. **Les avis Google** du widget Trustindex — et, sur cette page, le
   widget porte les ÉTOILES de chaque avis, en images `star/f.svg`
   (pleine) et `star/e.svg` (vide). C'est une note réelle, relevée.

    outils/inventaire-categorie.py desert-egypte
    outils/inventaire-categorie.py --tous

Écrit `docs/categories/<slug>.json`. Lecture seule côté site.
"""

import argparse
import html as H
import json
import os
import re
import sys
from importlib.machinery import SourceFileLoader

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SORTIE = os.path.join(RACINE, 'docs', 'categories')
PROGRAMMES = os.path.join(RACINE, 'docs', 'programmes')

_p = SourceFileLoader('invp', os.path.join(RACINE, 'outils',
                                           'inventaire-programme.py')).load_module()
SITE, API = _p.SITE, _p.API

# Les six familles, dans l'ordre du menu du site. Le libellé est celui
# que la page porte en H1 ; il n'est pas réécrit.
FAMILLES = ['nos-sejours-egypte', 'desert-egypte', 'croisieres-en-egypte',
            'mer-rouge', 'sinai-moise-et-saint-catherine', 'voyage-culturel-en-egypte']


def texte_nu(h):
    return _p.texte_nu(h)


def cartes(contenu):
    """Les séjours que la page range, dans son ordre."""
    lot = []
    for m in re.finditer(r'<article class="jkit-post[^"]*"[^>]*>(.*?)</article>', contenu, re.S):
        bloc = m.group(1)
        lien = re.search(r'href="([^"]*/programs/([^/"]+)/)"', bloc)
        titre = re.search(r'<h2 class="jkit-post-title">\s*<a[^>]*>(.*?)</a>', bloc, re.S)
        img = re.search(r'<img[^>]*\ssrc="([^"]+)"[^>]*>', bloc)
        alt = re.search(r'<img[^>]*\salt="([^"]*)"', bloc)
        if not lien or not titre:
            continue
        lot.append({'slug': lien.group(2), 'url': lien.group(1),
                    'titre': H.unescape(texte_nu(titre.group(1))),
                    'src_page': img.group(1) if img else '',
                    'alt_page': H.unescape(alt.group(1)) if alt else ''})
    return lot


def arguments(contenu):
    """« Pourquoi voyager avec nous ? » : un titre, quatre mots."""
    titre = ''
    m = re.search(r'<h2[^>]*>((?:(?!</h2>).)*?Pourquoi(?:(?!</h2>).)*?)</h2>', contenu, re.S)
    if m:
        titre = H.unescape(texte_nu(m.group(1)))
    lot = []
    for x in re.finditer(r'<h3 class="elementor-icon-box-title">\s*<span[^>]*>(.*?)</span>',
                         contenu, re.S):
        t = H.unescape(texte_nu(x.group(1)))
        if t and t not in lot:
            lot.append(t)
    return {'titre': titre, 'points': lot}


def bloc_texte(contenu, amorce):
    """Le titre et les paragraphes d'un bloc éditorial, à partir d'un H2.

    Le titre est cherché sur son TEXTE et non dans le HTML : l'éditeur
    découpe « Votre voyage, vos envies, notre expertise. » en trois
    `<span>` pour son animation, et « Votre voyage » ne s'y trouve donc
    jamais d'un seul tenant."""
    titres = [(m.start(), m.end(), H.unescape(texte_nu(m.group(1))))
              for m in re.finditer(r'<h2[^>]*>(.*?)</h2>', contenu, re.S)]
    for rang, (debut, fin, texte) in enumerate(titres):
        if amorce.lower() not in texte.lower():
            continue
        borne = titres[rang + 1][0] if rang + 1 < len(titres) else len(contenu)
        zone = contenu[fin:borne]
        paras = []
        for p in re.finditer(r'<p[^>]*>(.*?)</p>', zone, re.S):
            t = H.unescape(texte_nu(p.group(1)))
            if len(t) > 30 and t not in paras:
                paras.append(t)
        return {'titre': texte, 'paragraphes': paras}
    return None


def faq(contenu):
    """L'accordéon de la page : question, réponse, dans l'ordre."""
    lot = []
    for m in re.finditer(r'<a[^>]*class="card-header-button"[^>]*>\s*<span class="title">(.*?)</span>'
                         r'.*?<div class="card-expand"[^>]*>\s*<div class="card-body">(.*?)</div>\s*</div>',
                         contenu, re.S):
        q = H.unescape(texte_nu(m.group(1)))
        rep = re.sub(r'\s+', ' ', m.group(2)).strip()
        # Les attributs de rédaction de l'éditeur ne sont pas du contenu.
        rep = re.sub(r'\s+data-(start|end)="\d+"', '', rep)
        if q:
            lot.append({'q': q, 'reponse_html': rep})
    return lot


def notes_des_avis(contenu):
    """La note de chaque avis, comptée sur les étoiles du widget.

    Le widget Trustindex dessine cinq images par avis : `star/f.svg`
    pour une étoile pleine, `star/e.svg` pour une vide. La note est donc
    RELEVÉE, pas supposée — et elle n'est pas toujours de cinq : sur
    cette page, un avis en porte quatre."""
    lot = []
    for bloc in re.split(r'class="ti-review-item', contenu)[1:]:
        etoiles = re.findall(r'star/([fe])\.svg', bloc[:bloc.find('ti-review-text-container')
                                                       if 'ti-review-text-container' in bloc
                                                       else 4000])
        if len(etoiles) >= 5:
            lot.append(etoiles[:5].count('f'))
        else:
            lot.append(None)
    return lot


def inventorier(slug, medias, releve):
    lot = _p.lire('%s/pages?slug=%s&_fields=id,slug,link,title,content,modified_gmt,yoast_head_json'
                  % (API, slug))
    if not lot:
        raise SystemExit('page catégorie introuvable : ' + slug)
    p = lot[0]
    contenu = p['content']['rendered']
    y = p.get('yoast_head_json') or {}

    lots = cartes(contenu)
    # La photo de chaque carte est résolue jusqu'à son original, comme
    # sur les fiches : sans cette mesure, on ne sait pas ce qui sera flou.
    for i, c in enumerate(lots):
        if c['src_page']:
            img = _p.image_inventaire(medias, c['src_page'], c['alt_page'], 'carte', i)
            img['srcset'] = _p.srcset(img)
            c['image'] = img
        c.pop('src_page', None)
        c.pop('alt_page', None)

    blocs = _p.blocs_du_contenu(contenu)
    _, ecartes = _p.retirer_avis(blocs)
    temoins = _p.temoignages(ecartes)
    notes = notes_des_avis(contenu)
    for i, t in enumerate(temoins):
        if i < len(notes) and notes[i]:
            t['note'] = notes[i]

    inv = {
        'slug': slug,
        'id': p['id'],
        'url': p['link'],
        'releve': releve,
        'modified_gmt': p.get('modified_gmt'),
        'title_seo': (y.get('title') or '').strip(),
        'meta_description': (y.get('description') or '').strip(),
        'h1': H.unescape(texte_nu(re.search(r'<h1[^>]*>(.*?)</h1>', contenu, re.S).group(1)))
              if re.search(r'<h1[^>]*>(.*?)</h1>', contenu, re.S)
              else H.unescape(p['title']['rendered']),
        'sejours': lots,
        'arguments': arguments(contenu),
        'editorial': bloc_texte(contenu, 'Votre voyage'),
        'appel': bloc_texte(contenu, 'Créez un voyage'),
        'faq': faq(contenu),
        'avis_google': {'nombre': _p.avis_google(contenu),
                        'source': 'widget Google de la page catégorie',
                        'releve': releve, 'temoignages': temoins},
    }
    inv['anomalies'] = anomalies(inv)
    return inv


def anomalies(inv):
    a = []
    if not inv['sejours']:
        a.append('aucun séjour listé sur la page')
    if not inv['faq']:
        a.append("la page n'a pas de FAQ")
    sans = [c['slug'] for c in inv['sejours']
            if not os.path.exists(os.path.join(PROGRAMMES, c['slug'] + '.json'))]
    if sans:
        a.append('séjours sans inventaire de fiche : ' + ', '.join(sans))
    petites = [c['slug'] for c in inv['sejours']
               if c.get('image') and (c['image'].get('largeur') or 0) < 760]
    if petites:
        a.append('photos de carte sous 760 px : ' + ', '.join(petites))
    if inv['arguments']['points'] and len(inv['arguments']['points']) != 4:
        a.append('%d argument(s) au lieu de 4' % len(inv['arguments']['points']))
    return a


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('slug', nargs='?', default='')
    p.add_argument('--tous', action='store_true')
    a = p.parse_args()
    slugs = FAMILLES if a.tous else ([a.slug] if a.slug else [])
    if not slugs:
        sys.exit('usage : inventaire-categorie.py <slug> | --tous')

    os.makedirs(SORTIE, exist_ok=True)
    medias = _p.Medias()
    releve = __import__('datetime').date.today().isoformat()
    for slug in slugs:
        inv = inventorier(slug, medias, releve)
        with open(os.path.join(SORTIE, slug + '.json'), 'w', encoding='utf-8') as f:
            json.dump(inv, f, ensure_ascii=False, indent=1)
        print('%-34s %d séjour(s) · %d question(s) · %d avis · %d argument(s)'
              % (slug, len(inv['sejours']), len(inv['faq']),
                 len(inv['avis_google']['temoignages']), len(inv['arguments']['points'])))
        for x in inv['anomalies']:
            print('    ⚠ ' + x)
    medias.enregistrer()


if __name__ == '__main__':
    main()
