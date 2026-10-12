#!/usr/bin/env python3
"""Les pages couple et famille : les blocs que Mélanie refusait depuis septembre.

    WP_AUTH='compte:mdp' python3 outils/profils-1210.py --essai
    WP_AUTH='compte:mdp' python3 outils/profils-1210.py --appliquer

  10788 couple, réponse du 12 : « C'est un tout — la couleur jaune orange ne
        va pas, il faut que tout soit aligné et donne envie. »
  10844 famille : « La couleur ne convient pas, ce n'est pas aligné, plutôt
        dans des bulles. »
  10845 famille : « Un paragraphe sur nos activités coup de cœur pour les
        familles, que tout soit aligné, une ou deux photos à côté, un peu
        de couleur, et une incitation. »

  Les blocs « Ce que les couples préfèrent » et « Ce que les familles
  adorent » (avec, côté famille, « Nos activités coup de cœur ») deviennent
  un seul bloc : un paragraphe, les activités en pastilles alignées, deux
  photos, et deux boutons (composer le séjour, nous écrire sur WhatsApp).
  Plus de crème ni d'or : le bleu clair du site.

  12993 famille, « Nos guides pour voyager en famille » : des cartes avec
        photo et description, au lieu de trois liens.
  12985 couple, « l'image ne convient pas, mettez n'importe quel paysage » :
        la tuile « Voyage PMR » de « Partir autrement » montrait un
        personnage détouré sans décor. Elle prend une felouque sur le Nil,
        sur les trois pages qui la montrent.
"""

import argparse
import os
import re
import time

import requests

SITE = 'https://authentiquegypte.com'
UP = SITE + '/wp-content/uploads/'
WA = 'https://wa.me/201066619098'
E = '.elementor-template-canvas .pg '

STYLE = (
    '<style data-retours="12-10-profils">'
    + E + '.envies__g{display:grid;grid-template-columns:1.1fr .9fr;gap:48px;align-items:center}'
    + E + '.envies__lede{font-size:1.08rem;line-height:1.75;color:var(--texte,#5D5D5D);margin:14px 0 0;max-width:60ch}'
    + E + '.envies__l{display:flex;flex-wrap:wrap;gap:10px;list-style:none;padding:0;margin:20px 0 0}'
    + E + '.envies__l li{background:#E3F4F9;color:var(--nuit-900,#094D60);border-radius:999px;padding:9px 16px;'
    'font:600 .95rem/1.3 "Manrope",sans-serif}'
    + E + '.envies__h{margin:26px 0 0;font:700 1rem "Manrope",sans-serif;color:var(--nuit-900,#094D60)}'
    + E + '.envies__plus{list-style:none;padding:0;margin:10px 0 0;display:grid;gap:8px}'
    + E + '.envies__plus li{position:relative;padding-left:28px;line-height:1.6;color:var(--texte,#5D5D5D)}'
    + E + '.envies__plus li::before{content:"";position:absolute;left:0;top:.35em;width:16px;height:16px;'
    'border-radius:50%;background:#147894 url("data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 '
    'viewBox=%270 0 24 24%27%3E%3Cpath d=%27M6 12.5l4 4 8-9%27 fill=%27none%27 stroke=%27white%27 '
    'stroke-width=%273%27 stroke-linecap=%27round%27 stroke-linejoin=%27round%27/%3E%3C/svg%3E") center/11px no-repeat}'
    + E + '.envies__act{display:flex;flex-wrap:wrap;gap:12px;margin:28px 0 0}'
    + E + '.envies__ph{display:grid;grid-template-columns:1fr 1fr;gap:14px}'
    + E + '.envies__ph img{display:block;width:100%;aspect-ratio:3/4;object-fit:cover;border-radius:20px}'
    + E + '.envies__ph img:nth-child(2){margin-top:36px}'
    + E + '.envies__g>*{min-width:0}'
    '@media (max-width:900px){' + E + '.envies__g{grid-template-columns:minmax(0,1fr);gap:28px}'
    + E + '.envies__ph img{aspect-ratio:4/3}' + E + '.envies__ph img:nth-child(2){margin-top:0}}'
    + E + '.guif__c{list-style:none;padding:0;margin:20px 0 0;display:grid;grid-template-columns:repeat(3,1fr);gap:18px}'
    + E + '.guif__c a{display:flex;flex-direction:column;height:100%;background:#fff;border:1px solid var(--ligne-pg,#E4E4EA);'
    'border-radius:20px;overflow:hidden;text-decoration:none;transition:box-shadow .2s,transform .2s}'
    + E + '.guif__c a:hover{box-shadow:0 12px 28px rgba(9,77,96,.12);transform:translateY(-2px)}'
    + E + '.guif__c img{display:block;width:100%;aspect-ratio:16/10;object-fit:cover}'
    + E + '.guif__c h3{margin:16px 18px 6px;font-size:1.06rem;line-height:1.35;color:var(--nuit-900,#094D60)}'
    + E + '.guif__c p{margin:0 18px;font-size:.95rem;line-height:1.6;color:var(--texte,#5D5D5D);flex:1}'
    + E + '.guif__c span{margin:14px 18px 18px;font:700 .92rem "Manrope",sans-serif;color:var(--teal-txt,#10657C)}'
    '@media (max-width:900px){' + E + '.guif__c{grid-template-columns:1fr}}'
    + E + '.args.args b{font-weight:700}'
    '</style>')


def bloc(eyebrow, titre, lede, puces, sous_titre, plus, bouton, photos):
    return ('<section class="pg-sec envies"><div class="wrap"><div class="envies__g"><div>'
            '<p class="eyebrow">%s</p><h2>%s</h2><p class="envies__lede">%s</p>'
            '<ul class="envies__l">%s</ul>%s'
            '<p class="envies__act"><a class="btn btn--or" href="%s/sur-mesure/">%s</a>'
            '<a class="btn btn--fantome" href="%s">Nous écrire sur WhatsApp</a></p></div>'
            '<div class="envies__ph">%s</div></div></div></section>'
            % (eyebrow, titre, lede, ''.join('<li>%s</li>' % x for x in puces),
               ('<p class="envies__h">%s</p><ul class="envies__plus">%s</ul>'
                % (sous_titre, ''.join('<li>%s</li>' % x for x in plus))) if plus else '',
               SITE, bouton, WA,
               ''.join('<img src="%s" alt="%s" loading="lazy" decoding="async">' % (UP + f, alt) for f, alt in photos)))


FAMILLE = bloc(
    'En famille', 'Ce que les familles adorent',
    'Nos activités coup de cœur se glissent dans le séjour, au rythme des enfants et selon leur âge : '
    'on les choisit ensemble, au moment de construire l’itinéraire.',
    ['Un moment de felouque privative', 'Un atelier de hiéroglyphes', 'Un cours de cuisine',
     'Une balade en kayak', 'Une sortie en quad', 'Un atelier de poterie',
     'Un spectacle son et lumière', 'Du sandsurf', 'Les plages de la mer Rouge'],
    'Pensé pour les familles',
    ['Des chambres familiales ou communicantes, choisies une par une.',
     'Un guide égyptologue privatif qui cale le rythme sur celui des enfants, et leur parle comme on raconte une histoire.',
     'Un lit parapluie et un siège auto sur simple demande.'],
    'Composer notre séjour en famille',
    [('2025/06/Photo-dune-famille-dans-le-desert-Egyptiens-768x512.png', 'Une famille dans le désert égyptien'),
     ('2023/11/flying-carpet-Si1MFhSLNWY-unsplash-768x512.jpg', 'Felouque sur le Nil')])

COUPLE = bloc(
    'Rien qu’à deux', 'Ce que les couples préfèrent',
    'Ce que les couples nous demandent le plus, et que nous glissons dans leur séjour, à leur rythme :',
    ['Un dîner dans un palace', 'Des hébergements de charme', 'Un vol en montgolfière au lever du jour',
     'Un repas à bord d’une felouque privatisée', 'Un moment rien qu’à vous sur la mer Rouge'],
    None, None,
    'Composer notre voyage à deux',
    [('2025/06/Couple-dans-un-marche-en-Egypte-768x512.png', 'Un couple dans un marché en Égypte'),
     ('2025/10/Voyage-en-couple-en-egypte-authentique-1.png', 'Voyage en couple en Égypte')])

GUIDES = (
    '<ul class="guif__c">'
    + ''.join('<li><a href="%s/%s/"><img src="%s" alt="" loading="lazy" decoding="async"><h3>%s</h3><p>%s</p>'
              '<span>Lire le guide →</span></a></li>' % (SITE, slug, UP + img, titre, desc)
              for slug, img, titre, desc in (
                  ('egypte-enfants-activites', '2023/11/calin-stan-Mv15X2n8JVE-unsplash-scaled.jpg',
                   'Que faire en Égypte avec des enfants',
                   'Nos idées d’activités et de visites adaptées aux enfants, même aux tout-petits.'),
                  ('voyager-en-egypte-en-famille', '2023/11/yuriy-kostin-cc6kWqOr790-unsplash-scaled.jpg',
                   'Peut-on voyager en Égypte en famille ?',
                   'Nos conseils, des itinéraires adaptés et des activités ludiques pour partir sereinement.'),
                  ('securite-en-egypte-pour-un-voyage-en-famille',
                   '2023/11/axp-photography-VFd1Ui3BuQU-unsplash-1-scaled.jpg',
                   'Sécurité en Égypte pour un voyage en famille',
                   'Ce qu’il faut savoir pour voyager l’esprit tranquille avec vos enfants.')))
    + '</ul>')

PMR_AVANT = re.compile(r'<img src="[^"]*Voyage_pmr_en_egypte_authentique_-_1-removebg-preview\.png"[^>]*>')
PMR_APRES = ('<img src="%s2023/11/flying-carpet-Si1MFhSLNWY-unsplash-scaled.jpg" alt="Felouque sur le Nil" '
             'loading="lazy" decoding="async">' % UP)


def section(h, debut):
    i = h.find(debut)
    if i < 0:
        return None
    return i, h.find('</section>', i) + len('</section>')


def corriger(pid, h, j):
    if pid == 5035:
        a = section(h, '<section class="pg-sec adorent">')
        if a:
            h = h[:a[0]] + FAMILLE + h[a[1]:]
            j.append('bloc famille refait (10844, 10845)')
        a = section(h, '<section class="pg-sec coups">')
        if a:
            h = h[:a[0]] + h[a[1]:]
        m = re.search(r'<ul class="guif__l">.*?</ul>', h, re.S)
        if m:
            h = h[:m.start()] + GUIDES + h[m.end():]
            j.append('guides famille en cartes (12993)')
    if pid == 5044:
        a = section(h, '<section class="pg-sec adorent">')
        if a:
            h = h[:a[0]] + COUPLE + h[a[1]:]
            j.append('bloc couple refait (10788)')
    h, k = PMR_AVANT.subn(PMR_APRES, h)
    if k:
        j.append('tuile PMR : felouque sur le Nil (12985)')
    if j and 'data-retours="12-10-profils"' not in h:
        i = h.find('<main')
        i = h.find('>', i) + 1
        h = h[:i] + STYLE + h[i:]
    return h


def main():
    a = argparse.ArgumentParser()
    a.add_argument('--essai', action='store_true')
    a.add_argument('--appliquer', action='store_true')
    a = a.parse_args()
    s = requests.Session()
    s.verify = '/root/.ccr/ca-bundle.crt'
    s.auth = tuple(os.environ['WP_AUTH'].split(':', 1))
    for pid in (5035, 5044, 5052, 5095):
        url = '%s/wp-json/wp/v2/pages/%d' % (SITE, pid)
        h = s.get(url, params={'context': 'edit'}, timeout=300).json()['content']['raw']
        if 'data-retours="12-10-profils"' in h:
            print(pid, 'déjà fait')
            continue
        j = []
        h = corriger(pid, h, j)
        print(pid, ' · '.join(j))
        if a.appliquer and j:
            for essai in range(4):
                try:
                    print('   écrit :', s.post(url, json={'content': h}, timeout=600).status_code)
                    break
                except requests.RequestException:
                    time.sleep(2 ** essai)


if __name__ == '__main__':
    main()
