#!/usr/bin/env python3
"""
Gabarit « programme » : l'UX de la page circuit de voyageegypte.fr
(Nomadays) — hero plein écran, bandeau de repères, colonne + panneau
collant, jour par jour illustré, tarifs, inclus / non inclus, infos
pratiques et FAQ côte à côte, appel final, circuits similaires — avec les
couleurs, les polices et les boutons d'Authentique Égypte, et le contenu
des pages existantes du site, sans réécrire une phrase.

Entrées :
- docs/extraits.json : la fiche séjour en ligne (sections, prix, inclus…) ;
- maquettes/produit-siwa.html : entête, pied, photos pleine taille,
  questions de la FAQ, séjours sœurs (le moule de la DA) ;
- la page d'accueil en ligne : infos pratiques (les trois FAQ), réassurance,
  texte d'accompagnement.

usage : outils/gabarit-programme.py <id-fiche> <sortie.html> [--accueil home.html]
        ex.  outils/gabarit-programme.py 2393 maquettes/programme-siwa.html
"""

import argparse
import html as H
import html as html_
import json
import os
import re
import sys
import urllib.request

from bs4 import BeautifulSoup

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEVIS = 'https://authentiquegypte.com/sur-mesure/'
WHATSAPP = 'https://wa.me/201066619098'
ACCUEIL = 'https://authentiquegypte.com/'

e = H.escape


def texte(el):
    return re.sub(r'\s+', ' ', el.get_text(' ', strip=True)) if el else ''


# ------------------------------------------------------------------ contenu

def fiche(id_):
    for x in json.load(open(os.path.join(RACINE, 'docs', 'extraits.json'), encoding='utf-8')):
        if x.get('id') == id_:
            return x
    sys.exit(f'fiche {id_} absente de docs/extraits.json')


def para(t):
    """Un paragraphe du déroulé ; l'extraction a perdu les sauts de ligne de la
    page live (« pèlerins.Le monastère »), on les rend sans toucher au texte."""
    return re.sub(r'([.!?»])([A-ZÀ-Ý])', r'\1<br>\2', e(t))


def jours(x):
    """Le déroulé : un jour = un titre « Jour N » suivi de ses étapes."""
    sec = next(s for s in x['sections'] if re.search(r'étapes|programme|itinéraire', s['titre'] or '', re.I))
    js, jour, etape = [], None, None
    for b in sec['blocs']:
        if b['type'] == 'titre_etape':
            if re.match(r'^Jour\s*\d', b['texte']) or jour is None:
                jour = {'titre': b['texte'], 'etapes': [], 'mentions': []}
                js.append(jour)
                etape = None
                if not re.match(r'^Jour\s*\d', b['texte']):
                    etape = {'titre': b['texte'], 'p': [], 'mentions': []}
                    jour['etapes'].append(etape)
            else:
                etape = {'titre': b['texte'], 'p': [], 'mentions': []}
                jour['etapes'].append(etape)
        elif b['type'] == 'p' and jour is not None:
            if re.match(r'^FAQ\b', b['texte']):
                continue                                   # intertitre de la FAQ, pas du déroulé
            if etape is None:
                etape = {'titre': '', 'p': [], 'mentions': []}
                jour['etapes'].append(etape)
            etape['p'].append(b['texte'])
        elif b['type'] == 'liste' and jour is not None:
            items = b.get('items') or []
            if any(re.match(r"^(Le programme|N'inclus)", i) for i in items) or set(items) & set(x['inclus'] + x['exclus']):
                continue                                   # les inclusions sont lues ailleurs
            (etape['mentions'] if etape is not None else jour['mentions']).extend(items)
    return js


def intro(x):
    """Le titre éditorial et les paragraphes de présentation."""
    titre = next((s['titre'] for s in x['sections'] if s['niveau'] == 2 and s['titre'] and not s['blocs']), '')
    paras, sous = [], ''
    for s in x['sections']:
        if s['niveau'] == 2 and s['titre'] and re.search(r"vue d'ensemble|présentation", s['titre'], re.I):
            sous, paras = s['titre'], [b['texte'] for b in s['blocs'] if b['type'] == 'p']
    return titre, sous, paras


def faq(x, moule):
    """Les questions posées sur la page (le moule les liste toutes) ; seule la
    réponse rédigée en ligne est reprise, les autres sont remontées à part."""
    reponses = {}
    for s in x['sections']:
        if s['niveau'] == 3 and '?' in (s['titre'] or ''):
            html = ''
            for b in s['blocs']:
                # la fin de la section live est le panneau de réservation (prix,
                # bouton, repères) : il n'appartient pas à la réponse
                if b['type'] == 'p' and re.match(r'^([AÀ]\s*partir|Personaliser|Personnaliser)', b['texte']):
                    break
                if b['type'] == 'p':
                    html += f'<p>{e(b["texte"])}</p>'
                elif b['type'] == 'liste':
                    html += '<ul>' + ''.join(f'<li>{e(i)}</li>' for i in b['items']) + '</ul>'
            reponses[s['titre'].strip()] = html
    questions = [texte(d.summary) for d in moule.select('.faq details')]
    avec = [{'q': q, 'html': reponses[q]} for q in questions if q in reponses]
    sans = [q for q in questions if q not in reponses]
    return avec, sans


def reperes(x):
    """La liste courte du panneau de réservation (durée, rythme, guide…)."""
    for s in x['sections']:
        for b in s['blocs']:
            if b['type'] == 'liste' and any(re.search(r'jours? minimum', i) for i in b.get('items', [])):
                return b['items']
    return []


def photos_etapes(live_html):
    """Dans la page live, chaque volet du déroulé porte une photo (servie en
    300 px) : titre du volet → fichier plein format."""
    s = BeautifulSoup(live_html, 'lxml')
    out = {}
    for img in s.select('img[src*="/wp-content/uploads/"]'):
        titre = img.find_previous(class_=re.compile('toggle-title|title', re.I))
        if titre is None:
            continue
        t = titre.get_text(' ', strip=True)
        src = re.sub(r'-\d+x\d+(\.\w+)$', r'\1', img['src'])
        if t and t not in out and not re.search(r'logo|screenshot', src, re.I):
            out[t] = src
    return out


def photos(moule):
    return [{'src': a.img['src'], 'alt': a.img.get('alt', '')} for a in moule.select('.galerie a') if a.img]


def soeurs(moule):
    out = []
    for a in moule.select('.grille a.carte'):
        img = a.find('img')
        prix = a.select_one('.prix b')
        out.append({'href': a['href'], 'src': img['src'] if img else '', 'alt': img.get('alt', '') if img else '',
                    'titre': texte(a.select_one('h3')), 'route': texte(a.select_one('.carte__route')),
                    'tag': texte(a.select_one('.carte__tag')), 'prix': texte(prix) if prix else ''})
    return out


def soeurs_live(x, cat_html, fiches):
    """Les autres séjours de la catégorie live (cartes « Découvrir »), avec le
    prix et la durée de leur propre fiche ; photo = première image de la fiche
    en plein format (les vignettes Elementor sont ramenées au fichier d'origine)."""
    s = BeautifulSoup(cat_html, 'lxml')
    urls = []
    for a in s.find_all('a', href=True):
        if 'Découvrir' in a.get_text() and a['href'] not in urls and a['href'].rstrip('/') != x['url'].rstrip('/'):
            urls.append(a['href'])
    par_url = {f['url'].rstrip('/'): f for f in fiches if f.get('url')}
    out = []
    for u in urls:
        f = par_url.get(u.rstrip('/'))
        if not f or not f.get('prix'):
            continue
        src, alt = '', ''
        for im in f.get('images') or []:
            m = re.search(r'/elementor/thumbs/(.+?)-[a-z0-9]{40,}\.(\w+)$', im['src'])
            cand = f"https://authentiquegypte.com/wp-content/uploads/2025/06/{m.group(1)}.{m.group(2)}" if m \
                else re.sub(r'-\d+x\d+(\.\w+)$', r'\1', im['src'])
            if re.search(r'logo|screenshot', cand, re.I):
                continue
            src, alt = cand, im.get('alt') or f['titre']
            break
        tag = next((i for sec in f['sections'] for b in sec['blocs'] if b['type'] == 'liste'
                    for i in b.get('items', []) if re.search(r'jours? minimum', i)), '')
        out.append({'href': f['url'], 'src': src, 'alt': alt, 'titre': f['titre'], 'tag': tag, 'prix': f['prix'], 'route': ''})
    return out


def accueil(html):
    """Les blocs réutilisés de la page d'accueil : les trois FAQ pratiques,
    la réassurance en trois points, le texte d'accompagnement."""
    s = BeautifulSoup(html, 'lxml')
    groupes = []
    for acc in s.select('.jkit-accordion'):
        h2 = acc.find_previous('h2')
        items = []
        for c in acc.select('.card-wrapper'):
            corps = c.select_one('.card-body')
            for t in corps.find_all(True):
                for at in list(t.attrs):
                    if at not in ('href',):
                        del t.attrs[at]
            items.append({'q': texte(c.select_one('.title')),
                          'html': re.sub(r'\s+', ' ', ''.join(str(y) for y in corps.contents)).strip()})
        groupes.append({'titre': texte(h2), 'items': items})
    points = [{'titre': texte(b.select_one('.title')), 'texte': texte(b.select_one('.icon-box-description'))}
              for b in s.select('.jkit-icon-box')]
    h2 = s.find('h2', string=re.compile('Voyagez autrement'))
    texte_agence = texte(h2.find_next('p')) if h2 else ''
    accomp = texte(s.find('h2', string=re.compile('Pouvons-nous vous accompagner')))
    return {'groupes': groupes, 'points': points, 'agence': texte(h2), 'texte_agence': texte_agence, 'accompagner': accomp}


# ------------------------------------------------------------------ rendu

ICONES = {
    'horloge': '<path d="M12 7v5l3 2"/><circle cx="12" cy="12" r="9"/>',
    'euro': '<path d="M17 6.5A6 6 0 0 0 7 12a6 6 0 0 0 10 5.5M5 10h8M5 14h8"/>',
    'pas': '<path d="M4 20c4-1 5-6 5-6l3-9 3 9s1 5 5 6"/><path d="M9 14h6"/>',
    'voiture': '<path d="M5 11l1.5-4.5A2 2 0 0 1 8.4 5h7.2a2 2 0 0 1 1.9 1.5L19 11M4 11h16v6h-2a2 2 0 1 1-4 0H10a2 2 0 1 1-4 0H4z"/>',
    'guide': '<circle cx="12" cy="8" r="3.5"/><path d="M5 20a7 7 0 0 1 14 0"/>',
    'maison': '<path d="M4 11l8-7 8 7v9H4z"/><path d="M10 20v-6h4v6"/>',
    'pin': '<path d="M12 21s6-5.5 6-11a6 6 0 1 0-12 0c0 5.5 6 11 6 11z"/><circle cx="12" cy="10" r="2.2"/>',
    'lit': '<path d="M3 18V8M3 12h18v6M7 12V9h6v3"/>',
    'repas': '<path d="M7 3v7a2 2 0 0 0 4 0V3M9 3v18M17 3c-2 2-3 5-3 8h3v10"/>',
    'chevron': '<path d="M6 9l6 6 6-6"/>',
    'coche': '<path d="M5 12l4.5 4.5L19 7"/>',
    'croix': '<path d="M6 6l12 12M18 6L6 18"/>',
    'etoile': '<path d="M12 3l2.7 5.8 6.3.7-4.7 4.3 1.3 6.2L12 17l-5.6 3 1.3-6.2L3 9.5l6.3-.7z"/>',
    'bulle': '<path d="M4 6a3 3 0 0 1 3-3h10a3 3 0 0 1 3 3v8a3 3 0 0 1-3 3H9l-5 4z"/>',
    'doc': '<path d="M7 3h7l5 5v13H7z"/><path d="M14 3v5h5M10 13h6M10 17h6"/>',
    'bouclier': '<path d="M12 3l7 3v6c0 4.5-3 7.5-7 9-4-1.5-7-4.5-7-9V6z"/>',
    'carte': '<path d="M3 7h18v11H3z"/><path d="M3 11h18"/>',
}


CHEV = None


def ico(nom, taille=18):
    return (f'<svg aria-hidden="true" width="{taille}" height="{taille}" viewBox="0 0 24 24" fill="none" '
            f'stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{ICONES[nom]}</svg>')


def chev():
    return ico('chevron', 18).replace('<svg ', '<svg class="chev" ', 1)


def icone_repere(libelle):
    l = libelle.lower()
    if 'jour' in l: return 'horloge'
    if 'rythme' in l: return 'pas'
    if 'chauffeur' in l or 'véhicule' in l: return 'voiture'
    if 'guide' in l: return 'guide'
    if 'héberg' in l: return 'maison'
    return 'coche'


def icone_mention(m):
    return 'lit' if re.search(r'nuit|héberg', m, re.I) else 'repas'


CSS = r"""
/* ===== gabarit programme : l'UX du circuit Nomadays, la DA Authentique Égypte ===== */
.pg{--pg-max:1180px}
.pg .wrap{width:min(100% - 40px,var(--pg-max));margin-inline:auto}
.pg h2{font-family:"Archivo",sans-serif;font-weight:600;letter-spacing:-.6px;font-size:clamp(1.6rem,2.6vw,2.1rem);line-height:1.2;margin:0 0 20px;color:var(--noir)}
.pg h3{font-family:"Archivo",sans-serif;font-weight:600;letter-spacing:-.3px;margin:0}
.pg p{margin:0 0 .9em}
/* --- hero --- */
.pg .ariane{padding:12px 0}
.hero{position:relative;height:min(82vh,760px);min-height:560px;overflow:hidden;background:var(--nuit-900)}
.hero img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;background:transparent}
.hero::before{content:"";position:absolute;inset:0;background:linear-gradient(180deg,rgba(11,81,112,.35) 0%,rgba(11,81,112,.12) 40%,rgba(5,35,50,.78) 100%)}
.hero__in{position:absolute;left:0;right:0;bottom:0;padding:32px 0 40px}
.hero__pills{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 16px}
.pill{display:inline-flex;align-items:center;gap:6px;font-family:"Manrope",sans-serif;font-size:.78rem;font-weight:600;color:#fff;
  background:rgba(255,255,255,.18);border:1px solid rgba(255,255,255,.28);backdrop-filter:blur(8px);border-radius:var(--r-pill);padding:6px 12px}
.hero h1{color:#fff;font-size:clamp(2.1rem,4.6vw,3.4rem);line-height:1.08;margin:0 0 12px;max-width:16ch;text-shadow:0 2px 18px rgba(0,0,0,.35);text-wrap:balance}
.hero__chapo{color:rgba(255,255,255,.86);font-size:1.12rem;max-width:56ch;margin:0 0 20px;font-weight:300}
.hero__bas{display:flex;flex-wrap:wrap;align-items:center;gap:18px;margin:0 0 22px}
.hero__prix{background:rgba(255,255,255,.12);backdrop-filter:blur(10px);border:1px solid rgba(255,255,255,.2);border-radius:var(--r-m);padding:10px 18px;color:#fff;font-family:"Manrope",sans-serif}
.hero__prix small{display:block;font-size:.72rem;opacity:.75}
.hero__prix b{display:block;font-size:1.7rem;font-weight:700;letter-spacing:-.8px;line-height:1.15}
.hero__prix i{font-style:normal;font-size:.76rem;opacity:.75}
.hero__conf{display:grid;gap:4px;color:rgba(255,255,255,.82);font-family:"Manrope",sans-serif;font-size:.9rem}
.hero__act{display:flex;flex-wrap:wrap;gap:12px}
.btn--verre{background:rgba(255,255,255,.14);color:#fff;border-color:rgba(255,255,255,.35);backdrop-filter:blur(8px)}
.btn--verre:hover{background:rgba(255,255,255,.26);border-color:rgba(255,255,255,.5)}
/* --- repères --- */
.reps{background:var(--fond-2);border-bottom:1px solid var(--ligne)}
.reps ul{list-style:none;margin:0;padding:26px 0;display:grid;grid-template-columns:repeat(6,1fr);gap:18px}
.reps li{display:flex;flex-direction:column;align-items:center;text-align:center;gap:6px;font-family:"Manrope",sans-serif}
.reps li svg{color:var(--teal-txt)}
.reps small{font-size:.7rem;letter-spacing:.08em;text-transform:uppercase;color:var(--gris)}
.reps b{font-size:.92rem;color:var(--nuit-900);font-weight:700}
/* --- deux colonnes --- */
.deux{display:grid;grid-template-columns:minmax(0,2fr) minmax(300px,1fr);gap:44px;padding:52px 0 60px;align-items:start}
.deux>div{min-width:0;display:grid;gap:48px}
.prose{font-size:1.05rem;color:var(--texte)}
.prose strong{color:var(--nuit-900)}
.themes{display:flex;flex-wrap:wrap;gap:10px;margin-top:22px;padding-top:22px;border-top:1px solid var(--ligne-2)}
.themes a{font-family:"Manrope",sans-serif;font-size:.86rem;font-weight:600;color:var(--teal-txt);border:1px solid var(--teal);border-radius:var(--r-pill);padding:8px 14px;text-decoration:none}
.themes a:hover{background:var(--teal-fond)}
.etapes-carte{background:var(--fond-2);border-radius:var(--r-l);padding:22px 24px}
.etapes-carte h2{font-size:1.35rem;margin-bottom:12px}
.etapes-carte ol{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:1fr 1fr;gap:6px}
.etapes-carte li{display:flex;gap:10px;align-items:center;background:rgba(255,255,255,.7);border-radius:var(--r-s);padding:8px 12px;min-width:0}
.etapes-carte .j{flex:0 0 auto;background:var(--teal-txt);color:#fff;font-family:"Manrope",sans-serif;font-weight:800;font-size:.66rem;padding:3px 8px;border-radius:var(--r-pill);letter-spacing:.04em}
.etapes-carte span{font-family:"Manrope",sans-serif;font-size:.92rem;font-weight:600;color:var(--nuit-900);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.forts{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:14px 0!important;padding:0}
.forts li{list-style:none;display:flex;gap:10px;align-items:flex-start;background:var(--teal-fond);border-radius:var(--r-m);padding:12px 14px;font-family:"Manrope",sans-serif;font-size:.93rem;font-weight:600;color:var(--nuit-900)}
.forts li svg{flex:0 0 auto;color:var(--teal-txt);margin-top:2px}
.forts{margin:0;padding:0}
/* --- panneau collant --- */
.pan{position:sticky;top:84px;display:grid;gap:16px}
.pan__carte{background:#fff;border:1px solid var(--ligne);border-radius:var(--r-l);box-shadow:var(--ombre);padding:22px 22px 20px}
.pan__prix small{display:block;font-family:"Manrope",sans-serif;font-size:.74rem;color:var(--gris)}
.pan__prix b{font-family:"Manrope",sans-serif;font-size:2.1rem;font-weight:800;color:var(--noir);letter-spacing:-1.2px;line-height:1.1}
.pan__prix i{font-style:normal;font-family:"Manrope",sans-serif;font-size:.78rem;color:var(--gris)}
.pan__liste{list-style:none;margin:14px 0 0;padding:14px 0;border-top:1px solid var(--ligne-2);border-bottom:1px solid var(--ligne-2);display:grid;gap:9px;font-family:"Manrope",sans-serif;font-size:.92rem;color:var(--nuit-900)}
.pan__liste li{display:flex;gap:10px;align-items:center}
.pan__liste svg{color:var(--teal-txt);flex:0 0 auto}
.pan__note{font-family:"Manrope",sans-serif;font-size:.76rem;color:var(--gris);margin:12px 0 0;display:flex;gap:6px;align-items:flex-start}
.pan__equipe{margin-top:14px;padding-top:12px;border-top:1px solid var(--ligne-2)}
.pan__equipe img{width:100%;aspect-ratio:4/3;object-fit:cover;border-radius:var(--r-m);display:block}
.pan__equipe small{display:block;font-family:"Manrope",sans-serif;font-size:.7rem;letter-spacing:.1em;text-transform:uppercase;color:var(--gris);margin:12px 0 2px}
.pan__equipe b{display:block;font-family:"Manrope",sans-serif;font-size:1rem;color:var(--noir)}
.pan__equipe span{display:block;font-family:"Manrope",sans-serif;font-size:.86rem;color:var(--gris)}
.pan__act{display:grid;gap:9px;margin-top:14px}
.pan__conf{background:#fff;border:1px solid var(--ligne);border-radius:var(--r-l);padding:16px;text-align:center;font-family:"Manrope",sans-serif;font-size:.8rem;color:var(--gris);display:grid;gap:4px}
.pan__conf b{color:var(--nuit-900)}
/* --- jour par jour --- */
.jpj{background:linear-gradient(180deg,var(--fond) 0,#fff 100%);padding:60px 0 70px}
.jpj__grille{display:grid;grid-template-columns:44px minmax(0,720px) minmax(280px,1fr);gap:0 32px;align-items:start}
.jpj__grille--seul{grid-template-columns:minmax(0,720px) minmax(280px,1fr)}
.rail{position:sticky;top:100px;display:grid;gap:14px;justify-items:center;padding-top:22px}
.rail a{display:block;width:10px;height:10px;border-radius:50%;background:var(--ligne);transition:transform .2s var(--ease),background .2s}
.rail a:hover,.rail a.on{background:var(--teal);transform:scale(1.4);box-shadow:0 0 0 4px var(--teal-fond)}
.jr{scroll-margin-top:96px}
.jr+.jr{margin-top:56px}
.jour__photo{position:relative;height:clamp(240px,34vw,420px);border-radius:var(--r-l);overflow:hidden;margin:0 0 22px;background:var(--fond)}
.jour__photo img{width:100%;height:100%;object-fit:cover;display:block}
.jour__photo::after{content:"";position:absolute;inset:0;background:linear-gradient(0deg,rgba(11,81,112,.32),transparent 45%)}
.jour__badge{position:absolute;left:16px;top:16px;z-index:2;background:rgba(11,81,112,.9);color:#fff;font-family:"Manrope",sans-serif;font-weight:800;font-size:.84rem;letter-spacing:.06em;padding:6px 12px;border-radius:var(--r-s);backdrop-filter:blur(6px)}
.jr__intro p{color:var(--texte);font-size:1.05rem;margin:0 0 .8em}
.jr h3{font-size:clamp(1.4rem,2.4vw,1.85rem);margin:0 0 6px;color:var(--noir)}
.jour__lieu{display:flex;align-items:center;gap:6px;font-family:"Manrope",sans-serif;font-size:.9rem;color:var(--gris);margin:0 0 18px}
.jour__lieu svg{color:var(--teal-txt)}
.jet{display:grid;grid-template-columns:36px minmax(0,1fr);gap:12px;align-items:start}
.jet+.jet{margin-top:18px}
.jet__ico{width:36px;height:36px;border-radius:var(--r-s);background:var(--teal-fond);color:var(--teal-txt);display:grid;place-items:center}
.jet h4{font-family:"Manrope",sans-serif;font-size:1rem;font-weight:700;color:var(--nuit-900);margin:8px 0 6px}
.jet p{color:var(--texte);font-size:1rem;margin:0 0 .7em}
.jet__photo{margin:4px 0 14px;border-radius:var(--r-m);overflow:hidden;aspect-ratio:3/2;background:var(--fond)}
.jet__photo img{width:100%;height:100%;object-fit:cover;display:block}
.mentions{display:flex;flex-wrap:wrap;gap:8px;margin:22px 0 0}
.mention{display:inline-flex;align-items:center;gap:6px;font-family:"Manrope",sans-serif;font-size:.8rem;font-weight:600;color:var(--teal-txt);background:var(--teal-fond);border-radius:var(--r-pill);padding:5px 12px}
.cote{position:sticky;top:96px;display:grid;gap:12px}
.cote__photos{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.cote__photos a{display:block;aspect-ratio:4/3;border-radius:var(--r-m);overflow:hidden;background:var(--fond)}
.cote__photos img{width:100%;height:100%;object-fit:cover;display:block;transition:transform .6s var(--ease)}
.cote__photos a:hover img{transform:scale(1.05)}
.cote__carte{background:#fff;border:1px solid var(--ligne);border-radius:var(--r-l);box-shadow:var(--ombre);padding:22px;text-align:center;font-family:"Manrope",sans-serif;font-size:.9rem;color:var(--gris)}
.cote__carte b{display:block;color:var(--nuit-900);font-size:1rem;margin-bottom:6px}
/* --- tarifs --- */
.tarifs-sec{padding:60px 0}
.tarifs-grille{display:grid;grid-template-columns:1fr 1fr;gap:40px}
.tarifs-grille>div{display:grid;gap:22px;align-content:start}
.tarifs-grille__prix{order:-1}
.tarif{border:1px solid var(--ligne);border-radius:var(--r-m);overflow:hidden;font-family:"Manrope",sans-serif}
.tarif div{display:flex;justify-content:space-between;align-items:center;padding:14px 16px;background:var(--teal-fond);color:var(--teal-txt);font-size:.95rem}
.tarif b{font-size:1.15rem;font-weight:800}
.tarif b small{font-size:.75rem;font-weight:500;color:var(--gris)}
.adapter{background:var(--teal-fond);border:1px solid var(--teal);border-radius:var(--r-m);padding:22px}
.adapter h3{color:var(--teal-txt);font-size:1.05rem;margin-bottom:8px}
.adapter ul{list-style:none;margin:0 0 16px;padding:0;display:grid;gap:8px;font-family:"Manrope",sans-serif;font-size:.92rem;color:var(--nuit-900)}
.adapter li{display:flex;gap:9px;align-items:flex-start}
.adapter li svg{flex:0 0 auto;color:var(--teal-txt);margin-top:3px}
.inc h3{display:flex;align-items:center;gap:8px;font-size:1.08rem;margin-bottom:12px}
.inc ul{list-style:none;margin:0;padding:0;display:grid;gap:10px;font-size:.95rem;color:var(--texte)}
.inc li{display:flex;gap:10px;align-items:flex-start}
.inc li svg{flex:0 0 auto;margin-top:3px}
.inc--oui h3 svg,.inc--oui li svg{color:#1E9E5A}
.inc--non h3 svg,.inc--non li svg{color:#E0523C}
/* --- pratique + FAQ --- */
.prat{background:var(--fond-2);padding:70px 0}
.prat__grille{display:grid;grid-template-columns:1fr 1fr;gap:40px;align-items:start}
.acc{background:#fff;border:1px solid var(--ligne);border-radius:var(--r-l);overflow:hidden}
.acc+.acc{margin-top:14px}
.acc__t{font-family:"Manrope",sans-serif;font-size:.72rem;letter-spacing:.12em;text-transform:uppercase;color:var(--gris);padding:14px 20px 4px;margin:0}
.acc details{border-top:1px solid var(--ligne-2)}
.acc details:first-of-type{border-top:0}
.acc summary{list-style:none;cursor:pointer;display:flex;align-items:center;gap:12px;padding:16px 20px;font-family:"Manrope",sans-serif;font-weight:700;font-size:.98rem;color:var(--noir)}
.acc summary::-webkit-details-marker{display:none}
.acc summary>svg:first-child{color:var(--teal-txt);flex:0 0 auto}
.acc summary .chev{margin-left:auto;color:var(--gris);transition:transform .25s var(--ease);flex:0 0 auto}
.acc details[open] summary .chev{transform:rotate(180deg)}
.acc summary:hover{color:var(--teal-txt)}
.acc__c{padding:0 20px 18px 52px;color:var(--texte);font-size:.95rem}
.acc__c :last-child{margin-bottom:0}
.acc__c ul{padding-left:18px;margin:0 0 .8em}
.acc__c h3{font-size:1rem;color:var(--nuit-900);margin:14px 0 6px}
.acc--faq .acc__c{padding-left:20px}
.prat__cote{position:sticky;top:96px}
.prat__cote .pourquoi{margin-top:0}
.pourquoi{margin-top:18px;background:#fff;border:1px solid var(--ligne);border-radius:var(--r-l);padding:22px}
.pourquoi h3{font-size:1.1rem;margin-bottom:14px;color:var(--nuit-900)}
.pourquoi ul{list-style:none;margin:0;padding:0;display:grid;gap:14px}
.pourquoi li{display:grid;grid-template-columns:40px 1fr;gap:12px;align-items:start}
.pourquoi li span{width:40px;height:40px;border-radius:var(--r-s);background:var(--or-fond);color:#7A5605;display:grid;place-items:center}
.pourquoi b{display:block;font-family:"Manrope",sans-serif;color:var(--noir);margin-bottom:2px}
.pourquoi p{font-size:.92rem;color:var(--texte);margin:0}
/* --- appel final --- */
.final{background:var(--or-fond);padding:70px 0}
.final__grille{display:grid;grid-template-columns:1fr 1.15fr;gap:48px;align-items:center}
.final__photo{position:relative;justify-self:center}
.final__photo img{width:min(100%,340px);aspect-ratio:4/5;object-fit:cover;border-radius:var(--r-l);box-shadow:var(--ombre-f);display:block}
.final__badge{position:absolute;right:-14px;bottom:-14px;background:var(--nuit-900);color:#fff;border-radius:var(--r-m);padding:10px 14px;box-shadow:var(--ombre);font-family:"Manrope",sans-serif}
.final__badge b{display:block;font-size:1.3rem;line-height:1}
.final__badge small{font-size:.72rem;opacity:.85}
.final__sous{font-family:"Manrope",sans-serif;font-weight:700;color:var(--teal-txt);font-size:.9rem;margin:0 0 14px}
.final__act{display:flex;flex-wrap:wrap;gap:12px;margin-top:22px}
.final__conf{display:flex;flex-wrap:wrap;gap:16px;margin-top:20px;font-family:"Manrope",sans-serif;font-size:.8rem;color:var(--gris)}
.final__conf span{display:inline-flex;align-items:center;gap:5px}
.final__conf svg{color:var(--teal-txt)}
/* --- circuits similaires --- */
.simil{padding:60px 0;border-top:1px solid var(--ligne)}
.simil h2{text-align:center}
.simil__grille{display:grid;grid-template-columns:repeat(3,1fr);gap:22px}
.simil a{display:block;text-decoration:none;color:inherit}
.simil__img{position:relative;aspect-ratio:4/3;border-radius:var(--r-m);overflow:hidden;background:var(--fond);margin-bottom:12px}
.simil__img img{width:100%;height:100%;object-fit:cover;display:block;transition:transform .6s var(--ease)}
.simil a:hover img{transform:scale(1.05)}
.simil__tag{position:absolute;left:12px;top:12px;background:rgba(255,255,255,.92);color:var(--nuit-900);font-family:"Manrope",sans-serif;font-size:.74rem;font-weight:700;padding:5px 10px;border-radius:var(--r-pill)}
.simil h3{font-size:1.02rem;margin-bottom:4px}
.simil a:hover h3{color:var(--teal-txt)}
.simil p{font-family:"Manrope",sans-serif;font-size:.86rem;color:var(--gris);margin:0}
.simil p b{color:var(--noir)}
.simil__tous{text-align:center;margin-top:28px}
/* --- mobile --- */
@media (max-width:1000px){
  .deux{grid-template-columns:1fr;gap:34px}
  .pan{position:static}
  .jpj__grille{grid-template-columns:1fr}
  .rail{display:none}
  .cote{position:static;margin-top:36px}
  .prat__cote{position:static}
  .tarifs-grille,.prat__grille,.final__grille{grid-template-columns:1fr}
  .tarifs-grille__prix{order:0}
  .simil__grille{grid-template-columns:1fr 1fr}
  .reps ul{grid-template-columns:repeat(3,1fr)}
}
@media (max-width:900px){
  .pg small,.pg .pill,.pg .hero__prix i,.pg .hero__conf,.pg .reps b,.pg .themes a,.pg .pan__prix i,.pg .pan__note,.pg .pan__equipe span,
  .pg .tarif b small,.pg .pan__liste,.pg .adapter ul,.pg .jour__badge,.pg .mention,.pg .acc__t,.pg .final__conf,.pg .final__sous,.pg .simil__tag,.pg .simil p,.pg .pourquoi p,.pg .forts span{font-size:.95rem}
}
@media (max-width:640px){
  .hero{height:auto;min-height:0}
  .hero img{position:relative;height:260px}
  .hero::before{background:var(--nuit-900)}
  .hero__in{position:relative;padding:22px 0 26px}
  .hero h1{font-size:1.9rem}
  .reps ul{grid-template-columns:1fr 1fr}
  .etapes-carte ol,.forts,.simil__grille{grid-template-columns:1fr}
  .etapes-carte span{white-space:normal}
}
@media (prefers-reduced-motion:reduce){.pg *{transition:none!important}}
"""


def rendre(x, moule_html, home, etapes_img=None, soeurs_=None):
    etapes_img = etapes_img or {}
    moule = BeautifulSoup(moule_html, 'lxml')
    ph = photos(moule)
    js = jours(x)
    titre_etapes = next(s['titre'] for s in x['sections'] if re.search(r'étapes|programme|itinéraire', s['titre'] or '', re.I)).rstrip(' :')
    titre_faq = next((b['texte'] for s_ in x['sections'] for b in s_['blocs'] if b['type'] == 'p' and re.match(r'^FAQ\b', b['texte'])), 'FAQ')
    titre_inclus = texte(moule.find(['h2', 'h3'], string=re.compile('inclus'))) or "Le programme inclus, et ce qu'il n'inclut pas"
    titre_intro, sous_intro, paras = intro(x)
    faq_avec, faq_sans = faq(x, moule)
    rep = reperes(x)
    sr = soeurs_ if soeurs_ else soeurs(moule)
    titre = x['titre']
    prix = x['prix']
    categorie = CATEGORIE

    o = []
    o.append('<nav class="ariane" aria-label="Fil d\'Ariane"><div class="wrap"><ol>'
             f'<li><a href="{ACCUEIL}">Accueil</a></li>'
             '<li><a href="https://authentiquegypte.com/nos-sejours-egypte/">Nos séjours en Égypte</a></li>'
             f'<li><a href="{categorie[1]}">{e(categorie[0])}</a></li>'
             f'<li><span aria-current="page">{e(titre)}</span></li></ol></div></nav>')
    # ---------------- hero
    o.append(f'<section class="hero"><img src="{e(ph[0]["src"])}" alt="{e(ph[0]["alt"])}" fetchpriority="high" decoding="async">')
    o.append('<div class="hero__in"><div class="wrap"><div class="hero__pills">'
             f'<span class="pill">{e(categorie[0])}</span>'
             + ''.join(f'<span class="pill">{ico("horloge",14) if "jour" in r.lower() else ico("guide",14)} {e(r)}</span>'
                       for r in rep if re.search(r'jour|guide', r, re.I)) + '</div>')
    o.append(f'<h1>{e(titre)}</h1><p class="hero__chapo">{e(titre_intro)}</p>')
    o.append('<div class="hero__bas">'
             f'<div class="hero__prix"><small>À partir de</small><b>{e(prix)}</b><i>/ Personne</i></div>'
             '<div class="hero__conf"><span>23 avis Google sur l\'agence</span></div></div>')
    o.append(f'<div class="hero__act"><a class="btn btn--or" href="{DEVIS}">Personaliser ce séjour</a>'
             f'<a class="btn btn--verre" href="{WHATSAPP}">{ico("bulle",18)} Poser une question sur WhatsApp</a></div>')
    o.append('</div></div></section>')

    # ---------------- repères
    o.append('<section class="reps"><div class="wrap"><ul>')
    o.append(f'<li>{ico("euro",22)}<small>À partir de</small><b>{e(prix)}/pers.</b></li>')
    for r in rep:
        lab, val = ('Durée', r) if 'jour' in r.lower() else (r.split(' ')[0] if False else r, r)
        if 'jour' in r.lower():
            o.append(f'<li>{ico("horloge",22)}<small>Durée</small><b>{e(r)}</b></li>')
        else:
            o.append(f'<li>{ico(icone_repere(r),22)}<b>{e(r)}</b></li>')
    o.append('</ul></div></section>')

    # ---------------- deux colonnes
    o.append('<div class="wrap"><div class="deux"><div>')
    o.append(f'<section><h2>{e(sous_intro or titre_intro)}</h2><div class="prose">' + ''.join(f'<p>{e(p)}</p>' for p in paras) + '</div>'
             '<div class="themes">'
             f'<a href="{categorie[1]}">Tous nos séjours {e(categorie[0].lower())}</a>'
             '<a href="https://authentiquegypte.com/nos-sejours-egypte/">Tous nos séjours en Égypte</a>'
             '<a href="https://authentiquegypte.com/voyage-en-couple-en-egypte/">Voyage en couple</a>'
             '<a href="https://authentiquegypte.com/voyage-en-famille-en-egypte/">Voyage en famille</a>'
             '</div></section>')
    # étapes : les titres d'étapes du déroulé
    if len(js) > 1:
        o.append('<section class="etapes-carte"><h2>Les étapes de votre séjour</h2><ol>')
    for j in js if len(js) > 1 else []:
        n = re.match(r'^Jour\s*(\d+)', j['titre'])
        num = f'J{n.group(1)}' if n else 'J1'
        for k, et in enumerate(j['etapes']):
            if et['titre']:
                o.append(f'<li><span class="j">{num}</span><span>{e(et["titre"])}</span></li>')
    if len(js) > 1:
        o.append('</ol></section>')
    # points forts : la réponse « ce qui rend Siwa unique »
    forts = next((f for f in faq_avec if '<ul>' in f['html']), None)
    faq_reste = [f for f in faq_avec if f is not forts]
    if forts:
        corps_f = re.sub(r'<ul>(.*?)</ul>',
                         lambda m: '<ul class="forts">' + re.sub(r'<li>', '<li>' + ico("coche", 18) + '<span>', m.group(1)).replace('</li>', '</span></li>') + '</ul>',
                         forts['html'], count=1, flags=re.S)
        o.append(f'<section><h2>{e(forts["q"])}</h2><div class="prose">{corps_f}</div></section>')
    o.append('</div>')
    # panneau collant
    o.append('<aside class="pan"><div class="pan__carte">'
             f'<p class="pan__prix"><small>À partir de</small><b>{e(prix)}</b> <i>/ Personne</i></p>'
             '<ul class="pan__liste">' + ''.join(f'<li>{ico("coche",16)}{e(r)}</li>' for r in rep) + '</ul>'
             '<p class="pan__note">Devis gratuit · réponse sous 48 h (hors vendredi et samedi)</p>'
             f'<div class="pan__act"><a class="btn btn--or btn--bloc" href="{DEVIS}">Personaliser ce séjour</a>'
             f'<a class="btn btn--wa btn--bloc" href="{WHATSAPP}">Poser une question sur WhatsApp</a></div>'
             '<div class="pan__equipe"><b>Authentique Égypte</b><span>Agence locale basée au Caire</span></div>'
             '</div></aside></div></div>')

    # ---------------- jour par jour
    o.append(f'<section class="jpj"><div class="wrap"><h2>{e(titre_etapes)}</h2><div class="jpj__grille{"" if len(js) > 1 else " jpj__grille--seul"}">')
    if len(js) > 1:
        o.append('<nav class="rail" aria-label="Jours">' + ''.join(f'<a href="#jour-{i+1}" aria-label="Aller au jour {i+1}"></a>' for i in range(len(js))) + '</nav>')
    o.append('<div>')
    alerte = moule.select_one('.alerte')
    if alerte is not None:
        del alerte['data-dec']
        o.append(str(alerte))
    for i, j in enumerate(js):
        n = re.match(r'^Jour\s*(\d+)\s*:?\s*(.*)$', j['titre'])
        num, tit = (n.group(1), n.group(2) or j['titre']) if n else (str(i + 1), j['titre'])
        photo = {'src': etapes_img[j['titre']], 'alt': tit} if j['titre'] in etapes_img else ph[(i + 1) % len(ph)]
        o.append(f'<article class="jr" id="jour-{i+1}"><div class="jour__photo"><img src="{e(photo["src"])}" alt="{e(photo["alt"])}" loading="lazy" decoding="async"><span class="jour__badge">J{num}</span></div>')
        o.append(f'<h3>{e(tit)}</h3>')
        for et in j['etapes']:
            if not et['titre']:
                o.append('<div class="jr__intro">' + ''.join(f'<p>{para(p)}</p>' for p in et['p']) + '</div>')
                continue
            o.append(f'<div class="jet"><span class="jet__ico">{ico("pin",17)}</span><div>'
                     + (f'<h4>{e(et["titre"])}</h4>' if et['titre'] else '')
                     + (f'<figure class="jet__photo"><img src="{e(etapes_img[et["titre"]])}" alt="{e(et["titre"])}" loading="lazy" decoding="async"></figure>'
                        if et['titre'] in etapes_img else '')
                     + ''.join(f'<p>{para(p)}</p>' for p in et['p'])
                     + (('<div class="mentions">' + ''.join(f'<span class="mention">{ico(icone_mention(m),13)}{e(m)}</span>' for m in et['mentions']) + '</div>') if et['mentions'] else '')
                     + '</div></div>')
        if j['mentions']:
            o.append('<div class="mentions">' + ''.join(f'<span class="mention">{ico(icone_mention(m),13)}{e(m)}</span>' for m in j['mentions']) + '</div>')
        o.append('</article>')
    o.append('</div>')
    o.append('<aside class="cote"><div class="cote__photos">' +
             ''.join(f'<a href="{e(p["src"])}"><img src="{e(p["src"])}" alt="{e(p["alt"])}" loading="lazy" decoding="async"></a>' for p in ph[1:5]) +
             '</div></aside>')
    o.append('</div></div></section>')

    # ---------------- tarifs, inclus
    o.append(f'<section class="tarifs-sec"><div class="wrap"><h2>{e(titre_inclus)}</h2><div class="tarifs-grille"><div class="tarifs-grille__inc">')
    o.append(f'<div class="inc inc--oui"><h3>{ico("coche",18)}Le programme inclus</h3><ul>' + ''.join(f'<li>{ico("coche",14)}{e(i)}</li>' for i in x['inclus']) + '</ul></div>')
    o.append(f'<div class="inc inc--non"><h3>{ico("croix",18)}N\'inclus pas</h3><ul>' + ''.join(f'<li>{ico("croix",14)}{e(i)}</li>' for i in x['exclus']) + '</ul></div>')
    o.append('</div><div class="tarifs-grille__prix">')
    o.append(f'<div class="tarif"><div><span>À partir de</span><b>{e(prix)} <small>/ Personne</small></b></div></div>')
    o.append('<div class="adapter"><h3>Ce séjour vous tente ? Ajustons-le à vos dates.</h3><ul>'
             f'<li>{ico("coche",15)}Devis gratuit, détaillé jour par jour, sans engagement</li>'
             f'<li>{ico("coche",15)}Guide égyptologue francophone et chauffeur privatif</li>'
             f'<li>{ico("coche",15)}Acompte seulement une fois l\'itinéraire validé</li></ul>'
             f'<a class="btn btn--or btn--bloc" href="{DEVIS}">Personaliser ce séjour</a></div>')
    o.append('</div></div></div></section>')

    # ---------------- infos pratiques + FAQ
    ic_groupe = {'Organisation': 'doc', 'Réservation': 'carte', 'Paiement': 'euro'}
    o.append('<section class="prat"><div class="wrap"><div class="prat__grille"><div><h2>Informations pratiques</h2>')
    for g in home['groupes']:
        icn = next((v for k, v in ic_groupe.items() if k.lower() in g['titre'].lower()), 'doc')
        o.append(f'<div class="acc"><p class="acc__t">{e(g["titre"])}</p>')
        for it in g['items']:
            o.append(f'<details><summary>{ico(icn,18)}{e(it["q"])}{chev()}</summary><div class="acc__c">{it["html"]}</div></details>')
        o.append('</div>')
    pourquoi = (f'<div class="pourquoi"><h3>{e(home["agence"])}</h3><ul>' +
                ''.join(f'<li><span>{ico("etoile",18)}</span><div><b>{e(p["titre"])}</b><p>{e(p["texte"])}</p></div></li>' for p in home['points']) +
                '</ul></div>')
    if faq_reste:
        o.append(pourquoi + '</div>')
        o.append(f'<div><h2>{e(titre_faq)}</h2><div class="acc acc--faq">')
        for f in faq_reste:
            o.append(f'<details><summary>{e(f["q"])}{chev()}</summary><div class="acc__c">{f["html"]}</div></details>')
        o.append('</div></div>')
    else:
        o.append('</div><div class="prat__cote">' + pourquoi + '</div>')
    o.append('</div></div></section>')

    # ---------------- appel final
    o.append('<section class="final"><div class="wrap"><div class="final__grille">'
             f'<div class="final__photo"><img src="{e(ph[1 % len(ph)]["src"])}" alt="{e(ph[1 % len(ph)]["alt"])}" loading="lazy" decoding="async">'
             '<div class="final__badge"><b>23</b><small>avis Google</small></div></div>'
             f'<div><h2>{e(home["accompagner"])}</h2><p class="final__sous">Agence locale basée au Caire</p>'
             f'<p class="prose">{e(home["texte_agence"])}</p>'
             f'<div class="final__act"><a class="btn btn--or" href="{DEVIS}">Demande de devis</a><a class="btn btn--fantome" href="{WHATSAPP}">{ico("bulle",17)} Poser une question sur WhatsApp</a></div>'
             f'<div class="final__conf"><span>{ico("coche",13)}Réponse sous 48 h</span><span>{ico("coche",13)}Guide privatif</span><span>{ico("coche",13)}Chauffeur et véhicule sécurisé</span><span>{ico("coche",13)}Aucune carte bancaire demandée à cette étape</span></div>'
             '</div></div></div></section>')

    # ---------------- circuits similaires
    o.append('<section class="simil"><div class="wrap"><h2>Siwa se combine, ou se remplace</h2><div class="simil__grille">')
    for s_ in sr:
        tag = f'<span class="simil__tag">{e(s_["tag"])}</span>' if s_['tag'] else ''
        prix_ = f'<p>À partir de <b>{e(s_["prix"])}</b> <small>/pers.</small></p>' if s_['prix'] else f'<p>{e(s_["route"])}</p>'
        o.append(f'<a href="{e(s_["href"])}"><div class="simil__img"><img src="{e(s_["src"])}" alt="{e(s_["alt"])}" loading="lazy" decoding="async">{tag}</div><h3>{e(s_["titre"])}</h3>{prix_}</a>')
    o.append('</div><div class="simil__tous"><a class="btn btn--fantome" href="https://authentiquegypte.com/nos-sejours-egypte/">Voir tous nos séjours</a></div></div></section>')

    corps = '\n'.join(o)
    corps = re.sub(r'(?<=[^\s>]) ([?!])', r'&nbsp;\1', corps)
    corps = re.sub(r'href="https://www\.google\.com/url\?[^"]*?url=([^&"]+)[^"]*"',
                   lambda m: 'href="' + urllib.parse.unquote(m.group(1)) + '"', corps)

    # ---------------- assemblage sur le moule : entête, pied, styles, scripts
    h = moule_html
    h = re.sub(r'<title>.*?</title>', f'<title>{e(titre)} — Authentique Égypte</title>', h, count=1, flags=re.S)
    h = re.sub(r'<main>.*?</main>', '<main class="pg">\n' + corps + '\n</main>', h, count=1, flags=re.S)
    h = re.sub(r'<div class="resa-mob">.*?</a>\s*</div>',
               f'<div class="resa-mob"><span class="p"><small>{e(titre)}</small><b>{e(prix)}</b> <i>/ pers.</i></span>'
               f'<a class="btn btn--or btn--sm" href="{DEVIS}">Personaliser ce séjour</a></div>', h, count=1, flags=re.S)
    qr = [{'q': it['q'], 'html': it['html']} for g in home['groupes'] for it in g['items']]
    h = re.sub(r'<script type="application/ld\+json">.*?</script>', json_ld(x, js, faq_avec + qr, ph), h, count=1, flags=re.S)
    h = re.sub(r'(<div id="lb"[^>]*aria-label=")[^"]*"', r'\1Photos du séjour"', h, count=1)
    h = h.replace('</style>', CSS + '#mm-btn{display:none}\n</style>', 1)
    h = h.replace("querySelectorAll('.galerie a')", "querySelectorAll('.galerie a, .cote__photos a')", 1)
    h = h.replace('</title>', f'</title>\n<link rel="canonical" href="{x["url"]}">', 1)
    for rel, live in LIENS_LIVE.items():
        h = h.replace(f'href="{rel}"', f'href="{live}"')
    return h, {'jours': len(js), 'etapes': sum(len(j['etapes']) for j in js), 'faq_avec': len(faq_avec),
               'faq_sans': faq_sans, 'photos': len(ph), 'infos': sum(len(g['items']) for g in home['groupes'])}


CATEGORIE = ('Déserts et Oasis égyptiens', 'https://authentiquegypte.com/nos-sejours-egypte/desert-egypte/')

LIENS_LIVE = {
    'index.html': ACCUEIL, 'qui-sommes-nous.html': 'https://authentiquegypte.com/qui-sommes-nous/',
    'devis.html': DEVIS, 'blog.html': 'https://authentiquegypte.com/notre-blog/',
    'categorie.html': 'https://authentiquegypte.com/nos-sejours-egypte/croisieres-en-egypte/',
    'categorie-desert.html': 'https://authentiquegypte.com/nos-sejours-egypte/desert-egypte/',
    'destination.html': 'https://authentiquegypte.com/voyage-au-caire/',
}


def json_ld(x, js, faq_avec, ph):
    trip = {'@context': 'https://schema.org', '@type': 'TouristTrip', 'name': x['titre'], 'url': x['url'],
            'image': [p['src'] for p in ph],
            'provider': {'@type': 'TravelAgency', 'name': 'Authentique Égypte', 'url': ACCUEIL},
            'itinerary': {'@type': 'ItemList', 'numberOfItems': len(js),
                          'itemListElement': [{'@type': 'ListItem', 'position': i + 1, 'name': j['titre']} for i, j in enumerate(js)]},
            'offers': {'@type': 'Offer', 'price': re.sub(r'\D', '', x['prix']), 'priceCurrency': 'EUR',
                       'seller': {'@type': 'TravelAgency', 'name': 'Authentique Égypte'}}}
    def propre(t):
        return re.sub(r'\s+([.,;:!?])', r'\1', t)
    faq = {'@context': 'https://schema.org', '@type': 'FAQPage',
           'mainEntity': [{'@type': 'Question', 'name': f['q'],
                           'acceptedAnswer': {'@type': 'Answer', 'text': propre(html_.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', re.sub(r'</(li|p)>', '. ', f['html'])))).replace('. .', '.').replace('..', '.').replace('?.', '?').strip())}} for f in faq_avec]}
    fil = {'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': 1, 'name': 'Accueil', 'item': ACCUEIL},
        {'@type': 'ListItem', 'position': 2, 'name': 'Nos séjours en Égypte', 'item': 'https://authentiquegypte.com/nos-sejours-egypte/'},
        {'@type': 'ListItem', 'position': 3, 'name': CATEGORIE[0], 'item': CATEGORIE[1]},
        {'@type': 'ListItem', 'position': 4, 'name': x['titre'], 'item': x['url']}]}
    return '<script type="application/ld+json">' + json.dumps([trip, faq, fil], ensure_ascii=False) + '</script>'


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('fiche', type=int)
    p.add_argument('sortie')
    p.add_argument('--accueil', default='', help="copie locale de la page d'accueil (sinon téléchargée)")
    p.add_argument('--live', default='', help="copie locale de la page live (sinon téléchargée) : photos du déroulé")
    p.add_argument('--categorie', default='', help="copie locale de la page catégorie live (sinon téléchargée) : séjours voisins")
    p.add_argument('--moule', default=os.path.join(RACINE, 'maquettes', 'produit-siwa.html'))
    a = p.parse_args()
    x = fiche(a.fiche)
    if a.accueil:
        home_html = open(a.accueil, encoding='utf-8', errors='replace').read()
    else:
        req = urllib.request.Request(ACCUEIL, headers={'User-Agent': 'Mozilla/5.0 (gabarit-programme)'})
        home_html = urllib.request.urlopen(req, timeout=60).read().decode('utf-8', 'replace')
    if a.live:
        live_html = open(a.live, encoding='utf-8', errors='replace').read()
    else:
        req = urllib.request.Request(x['url'], headers={'User-Agent': 'Mozilla/5.0 (gabarit-programme)'})
        live_html = urllib.request.urlopen(req, timeout=60).read().decode('utf-8', 'replace')
    if a.categorie:
        cat_html = open(a.categorie, encoding='utf-8', errors='replace').read()
    else:
        req = urllib.request.Request(CATEGORIE[1], headers={'User-Agent': 'Mozilla/5.0 (gabarit-programme)'})
        cat_html = urllib.request.urlopen(req, timeout=60).read().decode('utf-8', 'replace')
    toutes = json.load(open(os.path.join(RACINE, 'docs', 'extraits.json'), encoding='utf-8'))
    page, bilan = rendre(x, open(a.moule, encoding='utf-8').read(), accueil(home_html), photos_etapes(live_html),
                         soeurs_live(x, cat_html, toutes))
    with open(a.sortie, 'w', encoding='utf-8') as f:
        f.write(page)
    print(f"{a.sortie} : {bilan['jours']} jour(s), {bilan['etapes']} étapes, {bilan['photos']} photos, "
          f"{bilan['faq_avec']} FAQ avec réponse, {bilan['infos']} infos pratiques")
    if bilan['faq_sans']:
        print('  questions posées en ligne sans réponse rédigée (non affichées) :')
        for q in bilan['faq_sans']:
            print('   -', q)


if __name__ == '__main__':
    sys.exit(main())
