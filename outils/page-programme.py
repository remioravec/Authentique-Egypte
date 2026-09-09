#!/usr/bin/env python3
"""
Page programme : reprend le contenu d'une page de circuit (source
concurrente ou page live) et le coule dans le moule voyage d'Authentique
Égypte (maquettes/produit-siwa.html), sans réécrire une phrase.

Deux temps, séparés pour que chacun se contrôle :

  1. extraire(html)  → l'inventaire du contenu (dict, aussi écrit en JSON) :
     titre, chapô, repères, esprit du voyage, étapes, points forts,
     itinéraire jour par jour (textes, trajets, photos, hôtel, repas),
     tarifs, inclus / non inclus, infos pratiques, FAQ.
  2. rendre(inventaire, moule) → la page HTML dans notre DA : même entête,
     même pied, mêmes classes que le moule ; seul <main> change.

Ce qui est volontairement laissé de côté (habillage de la marque source) :
navigation, conseiller, avis, garanties, partenaire assurance, circuits
similaires. La liste est écrite dans l'inventaire (« ecartes ») pour que
l'agent CONTRÔLE CONTENU la retrouve.

usage : outils/page-programme.py <source.html> <sortie.html> [--json inventaire.json]
        [--moule maquettes/produit-siwa.html] [--titre-court "…"]
"""

import argparse
import html as H
import json
import re
import sys
from urllib.parse import parse_qs, urlparse

from bs4 import BeautifulSoup, NavigableString, Tag

DEVIS = 'https://authentiquegypte.com/sur-mesure/'
LIENS_LIVE = {                       # les liens entre maquettes, une fois la page seule
    'index.html': 'https://authentiquegypte.com/',
    'qui-sommes-nous.html': 'https://authentiquegypte.com/qui-sommes-nous/',
    'devis.html': 'https://authentiquegypte.com/sur-mesure/',
    'blog.html': 'https://authentiquegypte.com/notre-blog/',
    'categorie.html': 'https://authentiquegypte.com/nos-sejours-egypte/croisieres-en-egypte/',
    'categorie-desert.html': 'https://authentiquegypte.com/nos-sejours-egypte/desert-egypte/',
    'destination.html': 'https://authentiquegypte.com/voyage-au-caire/',
}
WHATSAPP = 'https://wa.me/201066619098'
COCHE = ('<svg aria-hidden="true" fill="none" height="16" viewBox="0 0 17 17" width="16">'
         '<path d="M3 8.8l3.6 3.6L14 5" stroke="#0F6E73" stroke-linecap="round" '
         'stroke-linejoin="round" stroke-width="2"></path></svg>')


# ------------------------------------------------------------------ utilitaires

def texte(el):
    return re.sub(r'\s+', ' ', el.get_text(' ', strip=True)) if el else ''


def image_pleine(src):
    """Une URL Next.js /_next/image?url=… redonne l'image d'origine."""
    if not src:
        return ''
    if src.startswith('/_next/image'):
        q = parse_qs(urlparse(src).query)
        return q.get('url', [''])[0]
    return src


def html_propre(el, garder_liens=False):
    """L'HTML intérieur d'un bloc, débarrassé des classes, des liens de
    navigation interne et des attributs de suivi ; strong / em / listes
    et sauts de ligne sont conservés tels quels."""
    el = BeautifulSoup(str(el), 'lxml').find(el.name) if isinstance(el, Tag) else el
    for t in el.find_all(True):
        for a in list(t.attrs):
            if a not in ('href', 'target', 'rel'):
                del t.attrs[a]
        if t.name == 'a':
            href = t.get('href', '')
            interne = href.startswith('/') or 'from_circuit=' in href
            if interne or not garder_liens:
                t.unwrap()
        elif t.name == 'span':
            t.unwrap()
    out = ''.join(str(c) for c in el.contents)
    out = re.sub(r'<p>\s*</p>', '', out)
    return re.sub(r'\s+', ' ', out).strip()


def paragraphes(el):
    """Les <p> d'un bloc, en HTML propre ; un bloc sans <p> devient un <p>."""
    ps = el.find_all('p', recursive=False) if el else []
    if not ps:
        return ['<p>' + html_propre(el) + '</p>'] if el and texte(el) else []
    return ['<p>' + html_propre(p) + '</p>' for p in ps if texte(p)]


# ------------------------------------------------------------------ extraction

def extraire(html):
    s = BeautifulSoup(html, 'lxml')
    inv = {'source': '', 'ecartes': []}
    can = s.find('link', rel='canonical')
    inv['source'] = can['href'] if can else ''
    inv['title'] = texte(s.title)
    md = s.find('meta', attrs={'name': 'description'})
    inv['description'] = md['content'] if md else ''

    art = s.find('article')
    hero = art.find('section')
    inv['etiquettes'] = [texte(x) for x in hero.select('.flex.flex-wrap.gap-2 > span')]
    inv['h1'] = texte(hero.find('h1'))
    inv['chapo'] = texte(hero.find('h1').find_next('p'))
    inv['hero_image'] = {'src': image_pleine(hero.find('img').get('src')),
                         'alt': hero.find('img').get('alt', '')}
    prix = hero.find(string=re.compile('À partir de'))
    inv['prix_depuis'] = texte(prix.find_parent('div').find_all('span')[1]) if prix else ''
    inv['ecartes'] += [texte(x) for x in hero.select('.flex-col.gap-1 span')]     # ancienneté, avis
    inv['ecartes'] += [texte(b) for b in hero.find_all('button')]                 # boutons de la source

    # Repères (durée, prix, saisons, style, confort, voyageurs)
    reperes = []
    for bloc in hero.find_next_sibling('section').select('.flex-col.items-center'):
        ps = bloc.find_all('p')
        if len(ps) == 2:
            reperes.append({'label': texte(ps[0]), 'valeur': texte(ps[1])})
    inv['reperes'] = reperes

    # L'esprit du voyage
    h2 = art.find('h2', string=re.compile("esprit du voyage"))
    inv['esprit'] = {'titre': texte(h2), 'paragraphes': paragraphes(h2.find_next_sibling('div'))}
    inv['ecartes'] += [texte(a) for a in h2.parent.select('a.rounded-full')]      # liens de thème

    # Les étapes de votre voyage
    h2 = art.find('h2', string=re.compile("étapes de votre voyage"))
    etapes = []
    for ligne in h2.find_next_sibling('div').find_all('div', recursive=False):
        badge = texte(ligne.find('span'))
        spans = ligne.select('span.truncate')
        etapes.append({'jours': badge, 'lieu': texte(spans[0]) if spans else '',
                       'hebergement': texte(spans[1]) if len(spans) > 1 else ''})
    inv['etapes'] = {'titre': texte(h2), 'lignes': etapes}

    # Points forts
    h2 = art.find('h2', string=re.compile("Points forts"))
    inv['points_forts'] = {'titre': texte(h2),
                           'items': [texte(x) for x in h2.find_next_sibling('div').select('span')]}

    # Conseiller (écarté : marque de la source)
    aside = art.find('aside')
    if aside:
        for p in aside.find_all('p'):
            if texte(p) and 'Tarif indicatif' not in texte(p):
                inv['ecartes'].append(texte(p))

    # Itinéraire jour par jour
    h2 = art.find('h2', string=re.compile("Itinéraire jour par jour"))
    jours = []
    for a in art.select('article[data-day-index]'):
        j = {'n': int(a['data-day-index']) + 1}
        img = a.find('img')
        j['image'] = {'src': image_pleine(img.get('src')), 'alt': img.get('alt', '')} if img else None
        j['titre'] = texte(a.find('h3'))
        lieu = a.find('h3').find_next_sibling('div')
        j['lieu'] = texte(lieu.find('a')) if lieu and lieu.find('a') else texte(lieu)
        j['blocs'] = []
        corps = a.select_one('.space-y-4')
        for bloc in corps.find_all('div', recursive=False):
            tete = bloc.select_one('p.text-sm.font-medium')
            if tete and '→' in texte(tete):            # un trajet
                meta = [texte(x) for x in tete.find_next_sibling('div').find_all('span', recursive=False)] \
                    if tete.find_next_sibling('div') else []
                txt = bloc.find_all('div', recursive=False)[-1]
                j['blocs'].append({'type': 'trajet', 'titre': texte(tete),
                                   'meta': ' · '.join(m for m in meta if m),
                                   'paragraphes': paragraphes(txt) if txt is not bloc.find('div') else []})
            else:                                       # un récit
                j['blocs'].append({'type': 'recit', 'paragraphes': paragraphes(bloc)})
        pieds = a.select('.flex-wrap.gap-2\\.5 > span')
        j['hebergement'] = ''
        j['repas'] = []
        for sp in pieds:
            t = texte(sp)
            if sp is pieds[0] and not re.match(r'^(Petit-déjeuner|Déjeuner|Dîner)$', t):
                j['hebergement'] = t
            else:
                j['repas'].append(t)
        jours.append(j)
    inv['itineraire'] = {'titre': texte(h2), 'jours': jours}

    # Tarifs
    h2 = art.find('h2', string=re.compile("Tarif par personne"))
    sec = h2.parent
    tarifs = []
    for ligne in sec.select('.rounded-xl.overflow-hidden > div'):
        sp = ligne.find_all('span', recursive=False)
        if len(sp) == 2:
            tarifs.append({'base': texte(sp[0]), 'prix': texte(sp[1]).replace(' /pers.', '').replace('/pers.', '').strip()})
    inv['tarifs'] = {'titre': texte(h2), 'lignes': tarifs,
                     'note': texte(sec.find('p', class_=re.compile('text-\\[11px\\]')))}
    adapt = sec.find('h3', string=re.compile('adapté'))
    inv['adapter'] = {'titre': texte(adapt), 'texte': texte(adapt.find_next_sibling('p'))}
    inv['ecartes'].append(texte(adapt.find_next_sibling('button')))
    for h3 in sec.find_all('h3'):
        t = texte(h3)
        if t in ('Non inclus', 'Inclus'):
            inv['non_inclus' if t == 'Non inclus' else 'inclus'] = \
                [texte(li) for li in h3.find_next_sibling('ul').find_all('li')]

    # Informations pratiques
    h2 = art.find('h2', string=re.compile("Informations pratiques"))
    infos = []
    for bouton in h2.find_next_sibling('div').find_all('button'):
        titre = texte(bouton.find('span', class_=re.compile('font-semibold')))
        corps = bouton.find_next_sibling('div').select_one('.prose')
        infos.append({'titre': titre, 'html': html_propre(corps, garder_liens=True)})
    inv['infos'] = {'titre': texte(h2), 'items': infos}
    chapka = art.find('h3', string=re.compile('Chapka'))
    if chapka:
        inv['ecartes'] += [texte(chapka), texte(chapka.find_parent('div', class_='p-6').find('p')),
                           texte(chapka.find_parent('div', class_='p-6').find('a'))]

    # FAQ
    h2 = art.find('h2', string=re.compile("Questions fréquentes"))
    faq = []
    for bouton in h2.find_next_sibling('div').find_all('button'):
        faq.append({'q': texte(bouton.find('span')),
                    'r': texte(bouton.find_next_sibling('div'))})
    inv['faq'] = {'titre': texte(h2), 'items': faq}

    # Conseiller, circuits similaires : écartés
    h2 = art.find('h2', string=re.compile("Parlons de votre aventure"))
    if h2:
        inv['ecartes'] += [texte(h2)] + [texte(p) for p in h2.parent.find_all('p')]
    for h2 in s.find_all('h2', string=re.compile('Circuits similaires')):
        inv['ecartes'].append(texte(h2))
    inv['ecartes'] = [e for e in inv['ecartes'] if e]
    return inv


# ------------------------------------------------------------------ rendu

CSS_SUPPLEMENT = """
/* ---------- page programme : compléments au moule ---------- */
.atouts{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:1fr 1fr;gap:10px}
.atouts li{display:flex;gap:10px;align-items:center;background:var(--teal-fond);border:1px solid #CFEBEC;
  border-radius:var(--r-m);padding:12px 14px;font-family:"Manrope",sans-serif;font-weight:600;font-size:.95rem;color:var(--nuit-900)}
.atouts li::before{content:"✓";color:var(--teal-txt);font-weight:700}
.etapes{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:1fr 1fr;gap:8px}
.etapes li{display:flex;gap:12px;align-items:center;background:var(--fond);border-radius:var(--r-m);padding:10px 14px}
.etapes .j{flex:0 0 auto;background:var(--nuit-900);color:#fff;font-family:"Manrope",sans-serif;font-weight:700;
  font-size:.74rem;letter-spacing:.04em;padding:4px 10px;border-radius:var(--r-pill)}
.etapes b{display:block;font-family:"Manrope",sans-serif;font-size:.95rem;color:var(--noir)}
.etapes small{display:block;color:var(--gris);font-size:.82rem}
.jour .no::before{content:attr(data-n)}
.jour>summary h3{margin:0;font:inherit;color:inherit;letter-spacing:inherit;line-height:inherit}
.jour__img{margin:14px 0 18px;border-radius:var(--r-m);overflow:hidden;aspect-ratio:16/9;background:var(--fond)}
.jour__img img{width:100%;height:100%;object-fit:cover;display:block}
.jour__lieu{font-family:"Manrope",sans-serif;font-size:.86rem;color:var(--teal-txt);font-weight:700;margin:0 0 4px}
.etape__meta{font-family:"Manrope",sans-serif;font-size:.82rem;color:var(--gris);margin:-4px 0 10px}
.resa .prix .depuis{display:block;font-size:.74rem;color:var(--gris);letter-spacing:.04em}
.jour__meta{display:flex;flex-wrap:wrap;gap:8px;margin:14px 0 0}
.chip{font-family:"Manrope",sans-serif;font-size:.8rem;font-weight:600;color:var(--nuit-900);background:var(--fond-2);
  border:1px solid #D6E8F5;border-radius:var(--r-pill);padding:5px 12px}
.chip--nuit{background:var(--or-fond);border-color:#F6D9A8;color:#7A5605}
.tarifs{width:100%;border-collapse:collapse;font-family:"Manrope",sans-serif;font-size:.95rem;margin:0 0 12px}
.tarifs td{padding:12px 14px;border-top:1px solid var(--ligne-2)}
.tarifs tr:first-child td{border-top:0}
.tarifs td:last-child{text-align:right;font-weight:700;color:var(--noir)}
.tarifs tr.tarifs--min td{background:var(--teal-fond);color:var(--teal-txt)}
.tarifs tr.tarifs--min td:last-child{color:var(--teal-txt)}
.resa .tarifs{font-size:.88rem;margin:0}
.resa .tarifs td{padding:9px 6px}
.resa .repere{display:flex;justify-content:space-between;gap:12px}
.resa .repere small{color:var(--gris);font-weight:400}
.resa .repere b{text-align:right;font-weight:600;color:var(--noir)}
.prat summary{font-size:1.02rem}
.prat .faq__c h3{font-size:1rem;margin:16px 0 6px;color:var(--nuit-900)}
.prat .faq__c p{margin:0 0 .8em}
#mm-btn{display:none}   /* le bouton d'annotations du moule : rien à montrer ici */
@media (max-width:760px){.atouts,.etapes{grid-template-columns:1fr}}
"""


def rendre(inv, moule, titre_court=None):
    h = moule
    esc = H.escape
    titre_court = titre_court or inv['h1']

    # --- titre, description
    h = re.sub(r'<title>.*?</title>', '<title>' + esc(re.sub(r'\s*\|.*$', '', inv['title'])) +
               ' — Authentique Égypte</title>', h, count=1, flags=re.S)
    h = re.sub(r'<meta name="description" content="[^"]*">',
               '<meta name="description" content="' + esc(inv['description'], quote=True) + '">', h, count=1)

    # --- main
    o = []
    o.append('<main>\n<div class="wrap">')
    o.append('<nav aria-label="Fil d\'Ariane" class="ariane"><ol>'
             '<li><a href="https://authentiquegypte.com/">Accueil</a></li>'
             '<li><a href="https://authentiquegypte.com/nos-sejours-egypte/">Nos séjours en Égypte</a></li>'
             '<li><a href="https://authentiquegypte.com/nos-sejours-egypte/voyage-culturel-en-egypte/">Voyage culturel</a></li>'
             f'<li><span aria-current="page">{esc(titre_court)}</span></li></ol></nav>')
    o.append('<div class="tete"><p class="eyebrow">' + esc(' · '.join(inv['etiquettes'])) + '</p>'
             f'<h1>{esc(inv["h1"])}</h1><p>{esc(inv["chapo"])}</p></div>')

    # galerie : la photo de tête + les premières photos de l'itinéraire
    photos = [inv['hero_image']] + [j['image'] for j in inv['itineraire']['jours'] if j.get('image')]
    o.append('<div class="galerie">')
    for i, ph in enumerate(photos[:5]):
        leg = f'<span class="galerie__leg">{esc(ph["alt"])}</span>' if i == 0 else ''
        pri = 'fetchpriority="high"' if i == 0 else 'loading="lazy"'
        o.append(f'<a href="{esc(ph["src"])}"><img alt="{esc(ph["alt"])}" decoding="async" {pri} src="{esc(ph["src"])}">{leg}</a>')
    o.append('</div>')

    o.append('<div class="colonnes"><div>')
    # esprit du voyage
    o.append(f'<p class="eyebrow">Le circuit</p><h2>{esc(inv["esprit"]["titre"])}</h2>')
    o.append(''.join(p.replace('<p>', '<p class="lede">') for p in inv['esprit']['paragraphes']))

    # points forts
    o.append(f'<div class="bloc-t"><p class="eyebrow">Ce que vous verrez</p><h2>{esc(inv["points_forts"]["titre"])}</h2><ul class="atouts">')
    o.append(''.join(f'<li>{esc(x)}</li>' for x in inv['points_forts']['items']))
    o.append('</ul></div>')

    # étapes
    o.append(f'<div class="bloc-t"><p class="eyebrow">Le fil du voyage</p><h2>{esc(inv["etapes"]["titre"])}</h2><ul class="etapes">')
    for e in inv['etapes']['lignes']:
        o.append(f'<li><span class="j">{esc(e["jours"])}</span><span><b>{esc(e["lieu"])}</b><small>{esc(e["hebergement"])}</small></span></li>')
    o.append('</ul></div>')

    # itinéraire
    o.append(f'<div class="bloc-t"><p class="eyebrow">Jour par jour</p><h2>{esc(inv["itineraire"]["titre"])}</h2>')
    for j in inv['itineraire']['jours']:
        o.append(f'<details class="jour"><summary><b class="no" data-n="{j["n"]:02d}"></b><h3>{esc(j["titre"])}</h3></summary><div class="jour__c">')
        if j.get('image'):
            o.append(f'<div class="jour__img"><img alt="{esc(j["image"]["alt"])}" loading="lazy" decoding="async" src="{esc(j["image"]["src"])}"></div>')
        if j.get('lieu'):
            o.append(f'<p class="jour__lieu">{esc(j["lieu"])}</p>')
        for b in j['blocs']:
            if b['type'] == 'trajet':
                meta = f'<p class="etape__meta">{esc(b["meta"])}</p>' if b['meta'] else ''
                o.append(f'<div class="etape"><h4>{esc(b["titre"])}</h4>{meta}' + ''.join(b['paragraphes']) + '</div>')
            else:
                o.append('<div class="jour__intro">' + ''.join(b['paragraphes']) + '</div>')
        chips = ([f'<span class="chip chip--nuit">{esc(j["hebergement"])}</span>'] if j['hebergement'] else []) + \
                [f'<span class="chip">{esc(r)}</span>' for r in j['repas']]
        if chips:
            o.append('<p class="jour__meta">' + ''.join(chips) + '</p>')
        o.append('</div></details>')
    o.append('</div>')

    # tarifs
    mini = min(inv['tarifs']['lignes'], key=lambda l: int(re.sub(r'\D', '', l['prix']) or 0)) if inv['tarifs']['lignes'] else None
    o.append(f'<div class="bloc-t"><p class="eyebrow">Budget</p><h2>{esc(inv["tarifs"]["titre"])}</h2><table class="tarifs">')
    for l in inv['tarifs']['lignes']:
        cl = ' class="tarifs--min"' if l is mini else ''
        o.append(f'<tr{cl}><td>{esc(l["base"])}</td><td>{esc(l["prix"])} <small>/pers.</small></td></tr>')
    o.append('</table>' + f'<p class="note">{esc(inv["tarifs"]["note"])}</p></div>')

    # inclus / non inclus
    o.append('<div class="bloc-t"><p class="eyebrow">Le détail</p><h2>Inclus et non inclus</h2><div class="incl">')
    o.append('<div class="incl__col incl__col--oui"><h3><span class="ic">✓</span>Inclus</h3><ul class="oui">' +
             ''.join(f'<li>{esc(x)}</li>' for x in inv.get('inclus', [])) + '</ul></div>')
    o.append('<div class="incl__col incl__col--non"><h3><span class="ic">✕</span>Non inclus</h3><ul class="non">' +
             ''.join(f'<li>{esc(x)}</li>' for x in inv.get('non_inclus', [])) + '</ul></div>')
    o.append('</div></div>')

    # infos pratiques
    o.append(f'<div class="bloc-t prat"><p class="eyebrow">Avant de partir</p><h2>{esc(inv["infos"]["titre"])}</h2><div class="faq">')
    for it in inv['infos']['items']:
        o.append(f'<details><summary>{esc(it["titre"])}</summary><div class="faq__c">{it["html"]}</div></details>')
    o.append('</div></div>')

    # FAQ
    o.append(f'<div class="bloc-t"><p class="eyebrow">On nous demande</p><h2>{esc(inv["faq"]["titre"])}</h2><div class="faq">')
    for it in inv['faq']['items']:
        o.append(f'<details><summary>{esc(it["q"])}</summary><div class="faq__c"><p>{esc(it["r"])}</p></div></details>')
    o.append('</div></div>')
    o.append('</div>')  # fin colonne

    # aside
    o.append('<aside><div class="resa">')
    o.append(f'<p class="prix" style="margin:0 0 2px"><span class="depuis">À partir de</span><b>{esc(inv["prix_depuis"])}</b> <i>par personne</i></p>')
    o.append('<ul>' + ''.join(f'<li class="repere"><small>{esc(r["label"])}</small><b>{esc(r["valeur"])}</b></li>'
                              for r in inv['reperes'] if r['label'] != 'À partir de') + '</ul>')
    o.append('<table class="tarifs">' + ''.join(
        '<tr' + (' class="tarifs--min"' if l is mini else '') + f'><td>{esc(l["base"])}</td><td>{esc(l["prix"])} <small>/pers.</small></td></tr>'
        for l in inv['tarifs']['lignes']) + '</table>')
    o.append(f'<p class="note" style="margin:8px 0 14px;font-family:Manrope,sans-serif;color:var(--gris);font-size:.8rem">{esc(inv["tarifs"]["note"])}</p>')
    o.append(f'<div class="act"><a class="btn btn--or btn--bloc" href="{DEVIS}">Personnaliser ce circuit</a>'
             f'<a class="btn btn--wa btn--bloc" href="{WHATSAPP}">Poser une question sur WhatsApp</a></div>')
    o.append('<p class="note" style="margin:12px 0 0;font-family:Manrope,sans-serif;color:var(--gris);text-align:center">Devis gratuit · réponse sous 48 h (hors vendredi et samedi)</p>')
    o.append('</div></aside></div>')  # fin colonnes
    o.append('</div>')  # fin wrap

    # bande devis : le texte de la source, nos boutons
    o.append('<section class="section"><div class="wrap"><div class="devis"><div>'
             f'<p class="eyebrow eyebrow--clair">Votre projet</p><h2>{esc(inv["adapter"]["titre"])}</h2>'
             f'<p style="margin:16px 0 0;color:#C3D5DA">{esc(inv["adapter"]["texte"])}</p></div>'
             f'<div class="devis__act"><a class="btn btn--or btn--bloc" href="{DEVIS}">Personnaliser ce circuit</a>'
             f'<a class="btn btn--wa btn--bloc" href="{WHATSAPP}">Poser une question sur WhatsApp</a>'
             '<small>Aucune carte bancaire demandée à cette étape.</small></div></div></div></section>')
    o.append('</main>')

    h = re.sub(r'<main>.*?</main>', lambda m: '\n'.join(o), h, count=1, flags=re.S)

    # barre mobile
    h = re.sub(r'<div class="resa-mob">.*?</div>\s*</div>',
               f'<div class="resa-mob"><span class="p"><small>{esc(titre_court)}</small><b>{esc(inv["prix_depuis"])}</b> <i>/ pers.</i></span>'
               f'<a class="btn btn--or btn--sm" href="{DEVIS}">Personnaliser ce circuit</a></div>', h, count=1, flags=re.S)

    # les liens de maquette de l'entête et du pied pointent sur le site live
    for rel, live in LIENS_LIVE.items():
        h = h.replace(f'href="{rel}"', f'href="{live}"')

    # CSS complémentaire
    h = h.replace('</style>', CSS_SUPPLEMENT + '</style>', 1)
    return h


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('source')
    p.add_argument('sortie')
    p.add_argument('--json', default='')
    p.add_argument('--moule', default='maquettes/produit-siwa.html')
    p.add_argument('--titre-court', default='')
    a = p.parse_args()
    inv = extraire(open(a.source, encoding='utf-8', errors='replace').read())
    if a.json:
        with open(a.json, 'w', encoding='utf-8') as f:
            json.dump(inv, f, ensure_ascii=False, indent=1)
    page = rendre(inv, open(a.moule, encoding='utf-8').read(), a.titre_court or None)
    with open(a.sortie, 'w', encoding='utf-8') as f:
        f.write(page)
    j = inv['itineraire']['jours']
    print(f'{a.sortie} : {len(j)} jours, {len(inv["faq"]["items"])} FAQ, {len(inv["infos"]["items"])} infos pratiques, '
          f'{len(inv.get("inclus", []))} inclus / {len(inv.get("non_inclus", []))} non inclus, '
          f'{len(photos_de(inv))} photos, {len(inv["ecartes"])} éléments écartés (marque source)')


def photos_de(inv):
    return [inv['hero_image']] + [j['image'] for j in inv['itineraire']['jours'] if j.get('image')]


if __name__ == '__main__':
    sys.exit(main())
