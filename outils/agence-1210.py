#!/usr/bin/env python3
"""« L'agence » (brouillon 9126), sur les seize commentaires du 12 octobre.

    WP_AUTH='compte:mdp' python3 outils/agence-1210.py --essai
    WP_AUTH='compte:mdp' python3 outils/agence-1210.py --appliquer

Le brouillon n'était pas dans la liste des pages refondues (cibles.py) : il
n'avait reçu aucune des retouches communes du 7 et du 12 octobre. D'où
plusieurs remarques qui étaient déjà réglées ailleurs. Il les reçoit ici.

  12952 photo du haut : la sienne (Abou Simbel depuis le bateau), et un
        voile plus léger — la feuille commune du 7 octobre.
  12953, 12954, 12955 « Notre histoire » : « en partenariat avec une agence
        égyptienne » ; « maisons d'hôtes, hôtels boutique de charme » ;
        « interlocuteur de ce côté-ci de la Méditerranée » retiré.
  12956 « le texte se chevauche » : la carte « Testés et approuvés » avait
        été posée À L'INTÉRIEUR de la carte « Loin de la foule » (mon outil
        du 6 octobre). Elle redevient une carte à part, et les quatre
        s'alignent.
  12957, 12967 l'équipe : la photo de Mélanie — celle envoyée le 5 octobre
        à 17 h 39, juste avant celle de Hend, qui n'avait jamais été posée —
        et les deux portraits mis en avant, en tête de la section.
  12958 « La presse et les plateformes » : de vraies cartes, cliquables.
  12959 la licence de notre partenaire, certifiée par l'ETAA, organisme du
        gouvernement égyptien.
  12961 les paiements : Paytravel, plateforme française réservée aux agences
        de voyages ; paiement en euros, versé à l'agence sur place.
  12962 sur place : un groupe WhatsApp avec l'agent local, les
        représentants et deux numéros d'urgence.
  12963 « guides francophones et égyptologues ».
  12965 les avis : le même mur que sur toutes les pages, avec les boutons.
  12966 le logo : c'est déjà le logo propre, à fond transparent ; il est
        posé sur le pied de page bleu nuit. Rien à changer — à lui dire.
  12968 les mentions juridiques dans une phrase, plus en liste.
"""

import argparse
import os
import re
import time

import requests

SITE = 'https://authentiquegypte.com'
URL = SITE + '/wp-json/wp/v2/pages/%d'
UP = SITE + '/wp-content/uploads/'
E = '.elementor-template-canvas .pg '
STYLES_COMMUNS = ('id="retours-07-10"', 'data-avis="statique"', 'data-retours-06', 'data-retours="12-10-global"')

STYLE = (
    '<style data-retours="12-10-agence">'
    + E + '.atouts.atouts--app{grid-template-columns:repeat(4,1fr)}'
    + E + '.atouts.atouts{align-items:stretch}'
    '@media (max-width:1000px){' + E + '.atouts.atouts--app{grid-template-columns:repeat(2,1fr)}}'
    '@media (max-width:560px){' + E + '.atouts.atouts--app{grid-template-columns:1fr}}'
    + E + '.equipe.equipe{grid-template-columns:repeat(2,1fr);gap:20px;margin:6px 0 30px}'
    + E + '.equipe .pers{grid-template-columns:auto 1fr;gap:4px 24px;padding:28px;align-items:center;'
    'box-shadow:0 10px 26px rgba(9,77,96,.08)}'
    + E + '.equipe .pers__m{width:112px;height:112px;font-size:2.4rem;border-radius:50%;object-fit:cover;'
    'object-position:50% 20%;grid-row:span 3}'
    + E + '.equipe .pers h3{font-size:1.4rem}'
    '@media (max-width:760px){' + E + '.equipe.equipe{grid-template-columns:1fr}' + E + '.equipe .pers__m{width:88px;height:88px}}'
    + E + '.presse.presse{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}'
    + E + '.presse .atout{padding:0;background:#fff;border:1px solid var(--ligne-pg,#E4E4EA);border-radius:18px;'
    'transition:box-shadow .2s,transform .2s}'
    + E + '.presse .atout:hover{box-shadow:0 12px 26px rgba(9,77,96,.12);transform:translateY(-2px)}'
    + E + '.presse .atout a{display:block;padding:22px 24px;text-decoration:none;height:100%}'
    + E + '.presse .atout h3{margin:0 0 6px;font:800 1.15rem "Manrope",sans-serif;letter-spacing:0;'
    'text-transform:none;color:var(--nuit-900,#094D60)}'
    + E + '.presse .atout p{margin:0;color:var(--texte,#5D5D5D);font-size:.95rem}'
    + E + '.presse .atout p::after{content:" →";color:var(--teal-txt,#10657C);font-weight:700}'
    '@media (max-width:900px){' + E + '.presse.presse{grid-template-columns:repeat(2,1fr)}}'
    '@media (max-width:520px){' + E + '.presse.presse{grid-template-columns:1fr}}'
    '</style>')

HERO = UP + '2026/10/WhatsApp-Image-2026-06-10-at-12.44.27.jpeg'
MELANIE = UP + '2026/10/1443160_w-768_h-1024_q-70_m-crop.jpg'
HEND = UP + '2026/10/1674642_w-768_h-1024_q-70_m-crop-2.jpg'


def r(h, avant, apres, quoi, j, regex=False):
    if regex:
        h2, n = re.subn(avant, apres, h, count=1, flags=re.S)
    else:
        n = h.count(avant)
        h2 = h.replace(avant, apres, 1)
    j.append(('' if n else '✗ ') + quoi)
    return h2


def corriger(h, ref, j):
    # photo du haut
    h = r(h, r'(<div class="hero__flou"[^>]*><img src=")[^"]*(")', r'\g<1>%s\2' % HERO, '12952 photo du haut', j, True)
    h = r(h, r'(<div class="hero__fond"><img src=")[^"]*(")', r'\g<1>%s\2' % HERO, '12952 photo du haut (fond)', j, True)
    # les feuilles communes qui lui manquaient
    i = h.find('<main')
    i = h.find('>', i) + 1
    ajout = ''
    for marque in STYLES_COMMUNS:
        if marque in h:
            continue
        m = re.search(r'<style[^>]*%s[^>]*>.*?</style>' % re.escape(marque), ref, re.S)
        if m:
            ajout += m.group(0)
    h = h[:i] + ajout + STYLE + h[i:]
    j.append('feuilles communes : voile allégé, avis, bandeau, atouts')
    # Notre histoire
    h = r(h, 'elle commence à organiser des séjours avec une agence égyptienne du Caire. Les guides, les chauffeurs et '
             'les maisons d’hôtes étaient déjà là',
          'elle commence à organiser des séjours en partenariat avec une agence égyptienne du Caire. Les guides, les '
          'chauffeurs, les maisons d’hôtes et les hôtels boutique de charme étaient déjà là',
          '12953, 12954 partenariat, hôtels boutique', j)
    h = r(h, 'La société française est enregistrée en 2024, pour que les voyageurs aient un interlocuteur de ce côté-ci '
             'de la Méditerranée et un contrat de droit français.',
          'La société française est enregistrée en 2024 : chaque voyage est couvert par un contrat de droit français.',
          '12955 reformulé', j)
    # Testés et approuvés : sortie de la carte qui la contenait
    m = re.search(r'(</p>)(<div class="atout"><h3>Testés et approuvés</h3>.*?</div>)(</div>)', h, re.S)
    if m:
        h = h[:m.start()] + m.group(1) + m.group(3) + m.group(2) + h[m.end():]
        j.append('12956 « Testés et approuvés » remis à côté des autres')
    else:
        j.append('✗ 12956 introuvable')
    k = h.rfind('<div class="atouts', 0, h.find('Testés et approuvés'))
    h = h[:k] + h[k:].replace('<div class="atouts', '<div class="atouts atouts--app', 1)
    # l'équipe : photos, et en tête de section
    h = r(h, '<span class="pers__m" aria-hidden="true">M</span><h3>Mélanie</h3>',
          '<img class="pers__m" src="%s" alt="Mélanie" width="112" height="112" loading="lazy" decoding="async">'
          '<h3>Mélanie</h3>' % MELANIE, '12957 photo de Mélanie', j)
    h = re.sub(r'<img class="pers__m" src="[^"]*1674642[^"]*"[^>]*>',
               '<img class="pers__m" src="%s" alt="Hend" width="112" height="112" loading="lazy" decoding="async">'
               % HEND, h, count=1)
    a = h.find('<div class="equipe')
    b = h.find('</article></div>', a) + len('</article></div>')
    equipe = h[a:b]
    h = h[:a] + h[b:]
    t = h.find('<h2>Notre équipe</h2>') + len('<h2>Notre équipe</h2>')
    h = h[:t] + equipe + h[t:]
    j.append('12967 Mélanie et Hend en tête, portraits agrandis')
    # garanties
    h = r(h, 'travaille en partenariat avec une agence titulaire d&#x27;une licence touristique officielle en Égypte.',
          'travaille en partenariat avec une agence égyptienne titulaire d’une licence certifiée par l’ETAA, '
          'l’organisme du gouvernement égyptien qui agrée les agences de voyages.', '12959 ETAA', j)
    h = r(h, r'<ul class="garanties rev"><li><b>Authentique Égypte \(OREYA\)</b></li><li>SIRET&nbsp;: 928 008 226 '
             r'00013</li><li>Siège social&nbsp;: 17 Avenue Gambetta, 82000 Montauban, France</li></ul>',
          '<p>Authentique Égypte est une marque de la société <b>OREYA</b>, immatriculée sous le SIRET 928 008 226 '
          '00013, dont le siège social est au 17 avenue Gambetta, 82000 Montauban.</p>', '12968 mentions dans le texte',
          j, True)
    # FAQ
    h = r(h, '<p>Les paiements sont effectués directement à notre partenaire en Égypte, une agence reconnue et certifiée. '
             'Vous bénéficiez d&#x27;un suivi personnalisé et d&#x27;un interlocuteur en France pour toute question.</p>',
          '<p>Les paiements passent par <b>Paytravel</b>, une plateforme de paiement sécurisée basée en France et '
          'réservée aux agences de voyages. Vous payez en euros, et le paiement est versé directement à notre agence '
          'partenaire sur place.</p>', '12961 Paytravel', j)
    h = r(h, '<p>Notre équipe locale est disponible 24h/24 et 7j/7. Nous avons des représentants dans chaque destination '
             'ainsi que des contacts avec des médecins et pharmacies locales pour votre sécurité.</p>',
          '<p>Sur place, un <b>groupe WhatsApp</b> réunit votre agent local, nos représentants et <b>deux numéros '
          'd’urgence</b>, joignables 24h/24 et 7j/7. Nous avons des représentants dans chaque destination, et des '
          'contacts avec des médecins et des pharmacies locales.</p>', '12962 groupe WhatsApp', j)
    h = r(h, '<p>Oui, tous nos guides sont officiellement certifiés et régulièrement évalués pour garantir des visites '
             'enrichissantes et sécurisées.</p>',
          '<p>Oui. Ce sont des <b>guides francophones et égyptologues</b>, officiellement certifiés et régulièrement '
          'évalués.</p>', '12963 guides francophones et égyptologues', j)
    # les avis : le mur des autres pages
    m = re.search(r'<section class="pg-sec" aria-labelledby="t-avis">.*?</section>', ref, re.S)
    a = h.find('<section class="pg-sec" aria-labelledby="t-avis">')
    if m and a >= 0:
        # le mur contient des <section>? non : on borne par le bouton TripAdvisor
        b = h.find('</section>', h.find('Voir les avis sur TripAdvisor', a))
        if b < 0:
            b = h.find('</section>', a)
        h = h[:a] + m.group(0) + h[b + len('</section>'):]
        j.append('12965 mur d’avis des autres pages')
    return h


def main():
    a = argparse.ArgumentParser()
    a.add_argument('--essai', action='store_true')
    a.add_argument('--appliquer', action='store_true')
    a.add_argument('--vers')
    a = a.parse_args()
    s = requests.Session()
    s.verify = '/root/.ccr/ca-bundle.crt'
    s.auth = tuple(os.environ['WP_AUTH'].split(':', 1))
    h = s.get(URL % 9126, params={'context': 'edit'}, timeout=300).json()['content']['raw']
    if 'data-retours="12-10-agence"' in h:
        print('Déjà fait.')
        return
    ref = s.get(URL % 5201, params={'context': 'edit'}, timeout=300).json()['content']['raw']
    j = []
    h = corriger(h, ref, j)
    for x in j:
        print('  ' + x)
    if a.vers:
        open(a.vers, 'w', encoding='utf-8').write(h)
    if a.appliquer:
        if any(x.startswith('✗') for x in j):
            raise SystemExit('Une étape a échoué : rien n’est écrit.')
        for essai in range(4):
            try:
                print('écrit :', s.post(URL % 9126, json={'content': h}, timeout=600).status_code)
                break
            except requests.RequestException:
                time.sleep(2 ** essai)


if __name__ == '__main__':
    main()
