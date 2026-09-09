#!/usr/bin/env python3
"""
Contrôle de fidélité du contenu — l'outil de l'agent CONTRÔLE CONTENU.

Compare une page produite à sa source (une URL en ligne ou un fichier
HTML) et dit, chiffres à l'appui, ce qui est repris, ce qui manque, ce
qui a été modifié et ce qui a été inventé :

- les phrases de la source retrouvées / manquantes / altérées ;
- les phrases de la page produite absentes de la source (inventées) ;
- les nombres (prix, durées, dates, quantités) présents des deux côtés ;
- les images : mêmes fichiers ou non, réduites ou en pleine taille ;
- les listes et les questions (FAQ).

usage : outils/verif/controle-contenu.py <source (URL ou fichier)> <page produite> [--json]
        [--coupe TEXTE]   ignore la source à partir de ce texte (widgets, pied de page…)
        [--zone SÉLECTEUR-TEXTE]   ne garde de la page produite que ce qui suit ce texte

Aucune réécriture n'est jugée acceptable par défaut : une phrase
altérée est signalée, l'agent décide si c'est une coquille ou un écart.
"""

import argparse
import difflib
import html as H
import json
import re
import sys
import urllib.request

_p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
_p.add_argument('source')
_p.add_argument('produit')
_p.add_argument('--json', action='store_true')
_p.add_argument('--coupe', default='')
_p.add_argument('--zone', default='')
_a = _p.parse_args()
ARGS = [_a.source, _a.produit]
OPTS = {'coupe': _a.coupe, 'zone': _a.zone}
EN_JSON = _a.json


def charger(ref):
    if re.match(r'^https?://', ref):
        req = urllib.request.Request(ref, headers={'User-Agent': 'Mozilla/5.0 (controle-contenu)'})
        return urllib.request.urlopen(req, timeout=60).read().decode('utf-8', 'replace')
    with open(ref, encoding='utf-8', errors='replace') as f:
        return f.read()


def texte_brut(h):
    h = re.sub(r'<(script|style|noscript|svg|template)[^>]*>.*?</\1>', ' ', h, flags=re.S | re.I)
    h = re.sub(r'<!--.*?-->', ' ', h, flags=re.S)
    # les fins de bloc deviennent des fins de phrase, pour ne pas coller deux paragraphes
    h = re.sub(r'</(p|li|h[1-6]|div|section|article|td|th|tr|summary|figcaption|blockquote)\s*>', '. ', h, flags=re.I)
    h = re.sub(r'<br\s*/?>', '. ', h, flags=re.I)
    h = re.sub(r'<[^>]+>', ' ', h)
    h = H.unescape(h)
    h = h.replace('\xa0', ' ')
    return re.sub(r'\s+', ' ', h).strip()


def phrases(t):
    out = []
    for p in re.split(r'(?<=[.!?…:])\s+', t):
        p = p.strip(' .:;-–—')
        if len(p.split()) >= 5:          # une phrase, pas une étiquette de bouton
            out.append(p)
    # dédoublonne en gardant l'ordre
    vues, uniques = set(), []
    for p in out:
        k = normaliser(p)
        if k not in vues:
            vues.add(k)
            uniques.append(p)
    return uniques


def normaliser(p):
    p = p.lower()
    p = re.sub(r'[’\'"«»“”()\[\]]', ' ', p)
    p = re.sub(r'[^\w\s€%/-]', ' ', p)
    return re.sub(r'\s+', ' ', p).strip()


def images(h):
    trouvees = []
    for m in re.finditer(r'<img[^>]+>', h, flags=re.I):
        src = re.search(r'\ssrc=["\']([^"\']+)', m.group(0))
        if not src:
            continue
        u = src.group(1)
        if u.startswith('data:') or 'wp-content/plugins' in u or 'gravatar' in u:
            continue
        trouvees.append(u)
    return trouvees


def base_image(u):
    b = u.split('?')[0].rsplit('/', 1)[-1]
    b = re.sub(r'-\d{2,4}x\d{2,4}(?=\.\w+$)', '', b)
    b = re.sub(r'-scaled(?=\.\w+$)', '', b)
    b = re.sub(r'-[a-z0-9]{24,}(?=\.\w+$)', '', b)   # condensé Elementor
    return b.lower()


def reduite(u):
    return bool(re.search(r'-\d{2,4}x\d{2,4}\.(jpe?g|png|webp)|elementor/thumbs/', u, re.I))


def nombres(t):
    return sorted(set(re.findall(r'\b\d[\d\s]{0,6}(?:[.,]\d+)?\s?(?:€|\$|%|jours?|nuits?|h\b|km|m\b|°c)', t, flags=re.I)))


def questions(t):
    return [p for p in phrases(t) if p.rstrip().endswith('?')]


src_html = charger(ARGS[0])
prod_html = charger(ARGS[1])

src_txt = texte_brut(src_html)
if OPTS.get('coupe') and isinstance(OPTS['coupe'], str):
    i = src_txt.find(OPTS['coupe'])
    if i > 0:
        src_txt = src_txt[:i]
prod_txt = texte_brut(prod_html)
if OPTS.get('zone') and isinstance(OPTS['zone'], str):
    i = prod_txt.find(OPTS['zone'])
    if i > 0:
        prod_txt = prod_txt[i:]

ps, pp = phrases(src_txt), phrases(prod_txt)
norm_p = {normaliser(p): p for p in pp}
norm_s = {normaliser(p): p for p in ps}

reprises, alterees, manquantes = [], [], []
for p in ps:
    k = normaliser(p)
    if k in norm_p:
        reprises.append(p)
        continue
    proche = difflib.get_close_matches(k, norm_p.keys(), n=1, cutoff=0.8)
    if proche:
        alterees.append((p, norm_p[proche[0]]))
    else:
        manquantes.append(p)

inventees = []
for p in pp:
    k = normaliser(p)
    if k in norm_s:
        continue
    if difflib.get_close_matches(k, norm_s.keys(), n=1, cutoff=0.8):
        continue
    inventees.append(p)

img_s = images(src_html)
img_p = images(prod_html)
bases_s = {base_image(u) for u in img_s}
bases_p = {base_image(u) for u in img_p}
img_hors_source = sorted(bases_p - bases_s)
img_non_reprises = sorted(bases_s - bases_p)
img_reduites = [u.split('/')[-1] for u in img_p if reduite(u)]

nb_s, nb_p = set(nombres(src_txt)), set(nombres(prod_txt))
nombres_perdus = sorted(nb_s - nb_p)
nombres_ajoutes = sorted(nb_p - nb_s)

q_s, q_p = questions(src_txt), questions(prod_txt)
q_manquantes = [q for q in q_s if normaliser(q) not in {normaliser(x) for x in q_p}]

couverture = 100.0 * (len(reprises) + len(alterees)) / max(1, len(ps))
exactitude = 100.0 * len(reprises) / max(1, len(ps))

releve = {
    'source': ARGS[0], 'produit': ARGS[1],
    'phrases': {'source': len(ps), 'produit': len(pp), 'reprises': len(reprises),
                'alterees': len(alterees), 'manquantes': len(manquantes), 'inventees': len(inventees)},
    'couverture_pct': round(couverture, 1), 'exactitude_pct': round(exactitude, 1),
    'alterees': [{'source': a, 'produit': b} for a, b in alterees],
    'manquantes': manquantes, 'inventees': inventees,
    'images': {'source': len(img_s), 'produit': len(img_p), 'reprises': len(bases_s & bases_p),
               'hors_source': img_hors_source, 'non_reprises': img_non_reprises, 'reduites': img_reduites},
    'nombres': {'perdus': nombres_perdus, 'ajoutes': nombres_ajoutes},
    'questions': {'source': len(q_s), 'produit': len(q_p), 'manquantes': q_manquantes},
}
bloquants = []
if inventees:
    bloquants.append('%d phrase(s) inventée(s) — absente(s) de la source' % len(inventees))
if manquantes:
    bloquants.append('%d phrase(s) de la source manquante(s)' % len(manquantes))
if nombres_perdus:
    bloquants.append('nombres perdus : ' + ', '.join(nombres_perdus[:8]))
if img_hors_source:
    bloquants.append('images étrangères à la source : ' + ', '.join(img_hors_source[:6]))
majeurs = []
if alterees:
    majeurs.append('%d phrase(s) altérée(s)' % len(alterees))
if img_reduites:
    majeurs.append('images réduites (floues) : ' + ', '.join(img_reduites[:6]))
if q_manquantes:
    majeurs.append('%d question(s) FAQ manquante(s)' % len(q_manquantes))
if nombres_ajoutes:
    majeurs.append('nombres ajoutés : ' + ', '.join(nombres_ajoutes[:8]))
releve['defauts'] = {'bloquants': bloquants, 'majeurs': majeurs}
releve['verdict'] = 'REFUSÉ' if bloquants else ('À CORRIGER' if majeurs else 'FIDÈLE')

if EN_JSON:
    print(json.dumps(releve, ensure_ascii=False, indent=1))
    sys.exit(0)

print('CONTRÔLE CONTENU —', ARGS[1])
print('  source  :', ARGS[0])
print('  verdict :', releve['verdict'])
print('  phrases : %d dans la source · %d reprises telles quelles · %d altérées · %d manquantes · %d inventées'
      % (len(ps), len(reprises), len(alterees), len(manquantes), len(inventees)))
print('  couverture %.1f %% · exactitude %.1f %%' % (couverture, exactitude))
print('  images  : %d/%d reprises · %d hors source · %d réduites'
      % (len(bases_s & bases_p), len(bases_s), len(img_hors_source), len(img_reduites)))
if nombres_perdus:
    print('  nombres perdus :', ', '.join(nombres_perdus))
if nombres_ajoutes:
    print('  nombres ajoutés :', ', '.join(nombres_ajoutes))
for titre, lot in (('MANQUANTES', manquantes), ('INVENTÉES', inventees)):
    if lot:
        print('  ' + titre + ' (' + str(len(lot)) + ')')
        for p in lot[:25]:
            print('    - ' + p[:140])
if alterees:
    print('  ALTÉRÉES (' + str(len(alterees)) + ')')
    for a, b in alterees[:15]:
        print('    - source  : ' + a[:120])
        print('      produit : ' + b[:120])
if img_hors_source:
    print('  IMAGES HORS SOURCE :', ', '.join(img_hors_source))
if img_non_reprises:
    print('  images de la source non reprises :', ', '.join(img_non_reprises[:12]))
if q_manquantes:
    print('  QUESTIONS FAQ MANQUANTES :')
    for q in q_manquantes:
        print('    - ' + q[:120])
