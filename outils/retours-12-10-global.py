#!/usr/bin/env python3
"""Ce qui vaut pour tout le site, dans les commentaires de Mélanie du 12 octobre.

    WP_AUTH='compte:mdp' python3 outils/retours-12-10-global.py --essai
    WP_AUTH='compte:mdp' python3 outils/retours-12-10-global.py --appliquer

  12939 « 51 jours avant le départ » : le solde se règle 51 jours avant, pas
        45 — dans toutes les FAQ, et dans leurs données structurées.
  12940, 13028 « je n'arrive pas à cliquer » sur « Voir les autres
        questions » : en mode commentaire, l'extension de relecture capte
        tous les clics de la page (commentaires.js, l. 699). Pendant la
        relecture, la FAQ s'affiche donc dépliée ; pour les visiteurs, rien
        ne change.
  12948, 12949, 12994 le bloc « Sur mesure » : « mettre des couleurs »,
        « enlever ce texte » (« Guidés par nos équipes locales… »),
        « un bouton pour nous contacter via WhatsApp ou le formulaire ». Il
        devient un bandeau bleu du site, avec deux boutons.
  12943 « Pourquoi nous » : « changer le design ». Les quatre atouts
        quittent le crème et l'or — la couleur que Mélanie refuse depuis
        septembre (10788, 10844) — pour des cartes blanches alignées, chaque
        pictogramme dans une pastille bleue.
  12989 « Passer du profil au voyage » : surtitre retiré.
"""

import argparse
import importlib.util
import os
import re
import time

import requests

ICI = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('cibles', os.path.join(ICI, 'cibles.py'))
CIBLES = importlib.util.module_from_spec(spec)
spec.loader.exec_module(CIBLES)
SITE = CIBLES.SITE
WA = 'https://wa.me/201066619098'

E = '.elementor-template-canvas .pg '
STYLE = (
    '<style data-retours="12-10-global">'
    # relecture : tout déplier
    'body.aec-mode section[data-plie] .faq__rub{display:grid!important}'
    'body.aec-mode section[data-plie] .faq__q--plus{display:block!important}'
    'body.aec-mode .faq__plus{display:none!important}'
    # le bandeau « Sur mesure »
    + E + '.pg-sec--surmesure .edito.edito{background:linear-gradient(135deg,#0F6E86 0%,#094D60 100%);'
    'border-radius:24px;padding:44px 48px;align-items:center;box-shadow:0 18px 40px rgba(9,77,96,.18)}'
    + E + '.pg-sec--surmesure .edito h2{color:#fff}'
    + E + '.pg-sec--surmesure .edito .eyebrow{color:var(--or-clair,#FFC758)}'
    + E + '.pg-sec--surmesure .edito .prose p,' + E + '.pg-sec--surmesure .edito .prose p:first-child'
    '{color:#E3F2F6;font-weight:400}'
    + E + '.pg-sec--surmesure .edito .prose p:first-child{font-size:1.12rem;color:#fff}'
    + E + '.pg-sec--surmesure .edito__act{display:flex;flex-wrap:wrap;gap:12px;margin:22px 0 0}'
    '@media (max-width:760px){' + E + '.pg-sec--surmesure .edito.edito{padding:30px 22px}}'
    # « Pourquoi nous »
    + E + '.args.args{grid-template-columns:repeat(4,1fr);gap:18px}'
    + E + '.args.args li{flex-direction:column;justify-content:flex-start;text-align:center;gap:14px;'
    'background:#fff;border:1px solid var(--ligne-pg,#E4E4EA);border-radius:20px;padding:28px 18px;'
    'box-shadow:0 6px 18px rgba(9,77,96,.06)}'
    + E + '.args.args svg{width:24px;height:24px;padding:15px;box-sizing:content-box;border-radius:50%;'
    'background:#E3F4F9;color:var(--nuit-900,#094D60)}'
    + E + '.args.args b{font-size:1.02rem}'
    '@media (max-width:900px){' + E + '.args.args{grid-template-columns:repeat(2,1fr)}}'
    '@media (max-width:420px){' + E + '.args.args{grid-template-columns:1fr}}'
    '</style>')


def corriger(h):
    j = []
    k = h.count('45 jours avant le départ')
    if k:
        h = h.replace('45 jours avant le départ', '51 jours avant le départ')
        j.append('51 jours (%d)' % k)
    # le bloc « Sur mesure »
    n = 0
    for m in reversed(list(re.finditer(r'<section class="pg-sec"><div class="wrap"><div class="edito">'
                                       r'<div><p class="eyebrow">Sur mesure</p>', h))):
        fin = h.find('</section>', m.end())
        bloc = h[m.start():fin]
        bloc = bloc.replace('<section class="pg-sec">', '<section class="pg-sec pg-sec--surmesure">', 1)
        bloc = re.sub(r'<p>Guidés par nos équipes locales passionnées, vivez l’Égypte dans toute son '
                      r'authenticité\.</p>', '', bloc)
        bloc = re.sub(r'<p class="edito__act" data-devis-bloc>.*?</p>',
                      '<p class="edito__act" data-devis-bloc><a class="btn btn--or" href="%s/sur-mesure/">'
                      'Demander mon devis</a><a class="btn btn--verre" href="%s">Nous écrire sur WhatsApp</a></p>'
                      % (SITE, WA), bloc, count=1, flags=re.S)
        h = h[:m.start()] + bloc + h[fin:]
        n += 1
    if n:
        j.append('bandeau Sur mesure (%d)' % n)
    k = h.count('<p class="eyebrow">Passer du profil au voyage</p>')
    if k:
        h = h.replace('<p class="eyebrow">Passer du profil au voyage</p>', '')
        j.append('surtitre « Passer du profil au voyage »')
    if 'data-retours="12-10-global"' not in h:
        i = h.find('<main')
        i = h.find('>', i) + 1 if i >= 0 else 0
        h = h[:i] + STYLE + h[i:]
    return h, j


def main():
    a = argparse.ArgumentParser()
    a.add_argument('--essai', action='store_true')
    a.add_argument('--appliquer', action='store_true')
    a = a.parse_args()
    s = requests.Session()
    s.verify = '/root/.ccr/ca-bundle.crt'
    s.auth = tuple(os.environ['WP_AUTH'].split(':', 1))
    for c in CIBLES.toutes():
        url = '%s/wp-json/wp/v2/%s/%d' % (SITE, c['type'], c['cible'])
        h = None
        for essai in range(4):
            try:
                h = s.get(url, params={'context': 'edit'}, timeout=300).json()['content']['raw']
                break
            except Exception:
                time.sleep(2 ** essai)
        if h is None or 'data-retours="12-10-global"' in h:
            continue
        h2, j = corriger(h)
        print('%-6d %-50s %s' % (c['cible'], c['url'].replace(SITE, ''), ' · '.join(j)))
        if a.appliquer:
            for essai in range(4):
                try:
                    print('       écrit :', s.post(url, json={'content': h2}, timeout=600).status_code)
                    break
                except requests.RequestException:
                    time.sleep(2 ** essai)


if __name__ == '__main__':
    main()
