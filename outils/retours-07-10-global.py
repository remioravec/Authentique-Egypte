#!/usr/bin/env python3
"""Les retours du 6 octobre qui valent pour tout le site.

    WP_AUTH='compte:mdp' python3 outils/retours-07-10-global.py --essai
    WP_AUTH='compte:mdp' python3 outils/retours-07-10-global.py --appliquer

12666, 12672 « enlever la date partout sur le site » : « Relevé sur la fiche
    le 25 septembre 2026 », sous la note des avis. La note et le nombre
    d'avis restent.

12667, 12673, 12680 « bouton au milieu et de couleur » : les deux liens
    « Voir les avis sur Google / sur TripAdvisor » étaient des boutons
    transparents alignés à gauche. Ils passent au centre, pleins, en bleu
    nuit — la couleur du site qui ne concurrence pas l'or du devis.

12670, 12677 « le filtre de la photo est toujours trop foncé sur toutes les
    pages » : le voile posé sur la photo du haut de page couvrait les deux
    tiers gauches à 86-90 % d'opacité — la photo ne se voyait plus. Il
    descend à 64-54 % là où se trouve le texte et s'efface plus tôt. Le
    titre et le chapô gardent leur ombre portée, qui suffit à leur lecture.

12679 « mettre d'une autre couleur » sur le « Demander mon devis » de la
    section « Votre voyage, vos envies, notre expertise ». Sur trois pages
    cette section avait deux boutons identiques : celui ajouté le 6 octobre
    dans le texte, et un plus ancien resté seul sous le titre. L'ancien part,
    et celui qui reste passe en bleu nuit, partout où la section existe.
"""

import argparse
import base64
import os
import re
import sys
import time

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cibles

SITE = 'https://authentiquegypte.com'
E = '.elementor-template-canvas'

STYLE = (
    '<style id="retours-07-10">'
    # 12670, 12677 — le voile du haut de page, plus léger
    + E + ' .pg .hero.hero::after{background:linear-gradient(94deg,'
    'rgba(6,61,71,.64) 0%,rgba(6,61,71,.54) 42%,rgba(6,61,71,.30) 66%,'
    'rgba(6,61,71,.08) 84%,rgba(6,61,71,0) 100%)}'
    '@media (max-width:860px){' + E + ' .pg .hero.hero::after{'
    'background:linear-gradient(182deg,rgba(6,61,71,.18) 0%,'
    'rgba(6,61,71,.46) 34%,rgba(6,61,71,.58) 100%)}}'
    + E + ' .pg .hero .hero__chapo,' + E + ' .pg .hero h1{'
    'text-shadow:0 2px 14px rgba(3,38,45,.85),0 1px 3px rgba(3,38,45,.7)}'
    # 12667, 12673, 12680 — les boutons d'avis, au centre et pleins
    '.mur__liens.mur__liens{justify-content:center;margin-top:28px}'
    '.mur__liens .mur__lien.mur__lien{background:var(--nuit,#147894);'
    'border-color:var(--nuit,#147894);color:#fff}'
    '.mur__liens .mur__lien.mur__lien:hover,'
    '.mur__liens .mur__lien.mur__lien:focus-visible{'
    'background:var(--nuit-900,#094D60);border-color:var(--nuit-900,#094D60);'
    'color:#fff}'
    # 12679 — le devis de la section « Votre voyage… », en bleu nuit
    '.edito__act .btn.btn--nuit{background:var(--nuit,#147894);'
    'border-color:var(--nuit,#147894);color:#fff}'
    '.edito__act .btn.btn--nuit:hover{background:var(--nuit-900,#094D60);'
    'border-color:var(--nuit-900,#094D60);color:#fff}'
    '</style>')


def corriger(h):
    j = {}

    def note(k, n):
        if n:
            j[k] = j.get(k, 0) + n

    a = h.find('<main')
    b = h.find('</main>', a)
    if a < 0 or b < 0:
        return h, j
    tete, corps, pied = h[:a], h[a:b], h[b:]

    # 12666, 12672 — la date du relevé
    corps, n = re.subn(r'<small>\s*Relevé sur la fiche le[^<]*</small>', '', corps)
    note('date du relevé retirée', n)

    # 12679 — le doublon du devis, et sa couleur
    i = corps.find('Votre voyage, vos envies, notre expertise')
    if i >= 0:
        s = corps.rfind('<section', 0, i)
        f = corps.find('</section>', i)
        seg = corps[s:f]
        neuf = seg
        if 'data-devis-bloc' in neuf:
            neuf, n = re.subn(
                r'<p class="cta-devis">\s*<a [^>]*>\s*Demander mon devis\s*</a>\s*</p>',
                '', neuf)
            note('12679 bouton en double retiré', n)
        neuf, n = re.subn(
            r'(<p class="edito__act"[^>]*>\s*<a class="btn) btn--or(")',
            r'\1 btn--nuit\2', neuf)
        note('12679 devis en bleu nuit', n)
        corps = corps[:s] + neuf + corps[f:]

    if j or 'mur__liens' in corps or 'class="hero"' in corps:
        corps = re.sub(r'<style id="retours-07-10">.*?</style>', '', corps,
                       flags=re.S)
        corps = STYLE + corps
        note('feuille posée', 1)
    return tete + corps + pied, j


def main():
    p = argparse.ArgumentParser()
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument('--essai', action='store_true')
    g.add_argument('--appliquer', action='store_true')
    p.add_argument('--seulement', type=int, default=0)
    a = p.parse_args()

    S = requests.Session(); S.verify = '/root/.ccr/ca-bundle.crt'
    u, m = os.environ['WP_AUTH'].split(':', 1)
    S.headers['Authorization'] = 'Basic ' + base64.b64encode(
        ('%s:%s' % (u, m)).encode()).decode()
    B = SITE + '/wp-json/wp/v2/'

    a_ecrire, tot = [], {}
    for c in cibles.toutes():
        if a.seulement and c['cible'] != a.seulement:
            continue
        for essai in range(5):
            r = S.get(B + '%s/%d' % (c['type'], c['cible']),
                      params={'context': 'edit'}, timeout=300)
            if r.status_code < 300:
                break
            time.sleep(2 ** essai)
        h = (r.json().get('content') or {}).get('raw', '')
        neuf, j = corriger(h)
        if neuf == h:
            continue
        a_ecrire.append((c, neuf))
        for k, v in j.items():
            tot[k] = tot.get(k, 0) + v
    for k, v in sorted(tot.items()):
        print('%-34s %d' % (k, v))
    print('\n%d page(s) à écrire' % len(a_ecrire))
    if a.essai:
        return
    for c, neuf in a_ecrire:
        for essai in range(4):
            r = S.post(B + '%s/%d' % (c['type'], c['cible']), json={
                'content': '<!-- wp:html -->\n' + neuf + '\n<!-- /wp:html -->'},
                timeout=600)
            if r.status_code < 300:
                break
            time.sleep(2 ** essai)
        else:
            raise SystemExit('écriture refusée sur %s' % c['url'])
    print('%d page(s) écrites.' % len(a_ecrire))


if __name__ == '__main__':
    main()
