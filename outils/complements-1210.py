#!/usr/bin/env python3
"""Deux photos encore posables sans Mélanie (fils ouverts du 12 octobre).

    WP_AUTH='compte:mdp' python3 outils/complements-1210.py --essai
    WP_AUTH='compte:mdp' python3 outils/complements-1210.py --appliquer

  10820 « photo a changer » sur la carte « Les arnaques et erreurs à éviter »
        du blog : c'était un visuel publicitaire (tour-014, bandeau noir
        « Egypt »). Elle prend la photo d'un couple dans un souk, déjà dans
        la médiathèque.
  9504  « des photos pour chaque site » d'Alexandrie : la médiathèque a
        maintenant le fort Qaitbay et les jardins de Montaza (photos qu'elle
        a déposées le 5 octobre). Elles vont sous la réponse « Que voir à
        Alexandrie ? ». La bibliothèque, les catacombes et la colonne de
        Pompée attendent toujours les siennes.
  9527  « la photo ne correspond pas » sur « Voyage à Assouan » : la carte du
        roadtrip y montrait Karnak, à Louxor. Sur cette page, elle prend les
        villages nubiens d'Assouan (photo déposée par Mélanie) ; ailleurs, la
        carte garde la photo du séjour.
  10438 les journées restées sans photo après photos-1210.py, parce que les
        photos de leur lieu étaient déjà prises ailleurs dans la page : on
        regarde le titre du jour plutôt que son lieu (Abou Simbel, le désert
        noir, la navigation vers Kom Ombo, la mer Rouge). Bahariya reste
        sans photo : la médiathèque n'en a aucune.
"""

import argparse
import os
import re

import requests

SITE = 'https://authentiquegypte.com'
UP = SITE + '/wp-content/uploads/'
E = '.elementor-template-canvas .pg '

BLOG = 2368
MARCHE = UP + '2025/06/Couple-dans-un-marche-en-Egypte-768x512.png'

ALEX = 5219
ALEX_PHOTOS = [('2026/10/abdullah-ali-cD4Ix4i1HZ8-unsplash-768x576.jpg', 'Le fort Qaitbay'),
               ('2026/10/ahmed-assem-RvB3p8sJyCo-unsplash-768x512.jpg', 'Les jardins de Montaza')]
APRES = '<p class="">Jardins de Montaza</p>'
STYLE = ('<style data-retours="12-10-alexandrie">'
         + E + '.alex-photos{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px;margin:16px 0 0}'
         + E + '.alex-photos figure{margin:0}'
         + E + '.alex-photos img{display:block;width:100%;aspect-ratio:3/2;object-fit:cover;border-radius:14px}'
         + E + '.alex-photos figcaption{margin-top:6px;font-size:.85rem;color:var(--texte,#5D5D5D)}'
         '@media (max-width:560px){' + E + '.alex-photos{grid-template-columns:1fr}}'
         '</style>')


def blog(h, j):
    if '2025/05/tour-014.png' in h:
        h = h.replace(UP + '2025/05/tour-014.png', MARCHE)
        j.append('carte « arnaques » : photo du souk')
    return h


def alexandrie(h, j):
    if 'class="alex-photos"' in h or APRES not in h:
        return h
    figs = ''.join('<figure><img src="%s" alt="%s" loading="lazy" decoding="async"><figcaption>%s</figcaption></figure>'
                   % (UP + f, alt, alt) for f, alt in ALEX_PHOTOS)
    h = h.replace(APRES, APRES + '<div class="alex-photos">%s</div>' % figs, 1)
    m = h.find('<main')
    m = h.find('>', m) + 1
    h = h[:m] + STYLE + h[m:]
    j.append('« Que voir à Alexandrie ? » : fort Qaitbay et jardins de Montaza')
    return h


ASSOUAN = 5210
KARNAK = UP + '2023/11/kristina-tamasauskaite-bVRArO7LwB0-unsplash-scaled.jpg'
NUBIENS = UP + '2026/09/Aswan-villages-nubiens-scaled.jpg'


def assouan(h, j):
    for m in re.finditer(r'<article class="carte.*?</article>', h, re.S):
        if KARNAK in m.group(0) and 'Roadtrip' in m.group(0):
            c = m.group(0).replace(KARNAK, NUBIENS)
            c = re.sub(r'(<img [^>]*src="%s"[^>]*alt=")[^"]*"' % re.escape(NUBIENS), r'\1Villages nubiens à Assouan"', c)
            j.append('carte du roadtrip : villages nubiens d’Assouan')
            return h[:m.start()] + c + h[m.end():]
    return h


JOURS = {
    'pyramides-et-croisiere-sur-le-nil': (4, '2026/10/WhatsApp-Image-2026-06-10-at-12.44.27.jpeg',
                                          'Les temples d’Abou Simbel'),
    'excursion-dans-le-desert-blanc': (2, '2025/07/Voyage-dans-le-Desert-noir-en-Egypte.png', 'Le désert noir'),
    'mer-rouge': (4, '2023/11/nile-4069222_1280.jpg', 'Navigation sur le Nil'),
    'itineraire-sinai-sainte-catherine-mont-moise-et-mer-rouge': (7, '2023/11/yuriy-kostin-cc6kWqOr790-unsplash-scaled.jpg',
                                                                   'Plage de la mer Rouge'),
    'pyramides-louxor-et-mer-rouge-en-famille': (7, '2025/07/peggy-anke-YxpoB3bvlZQ-unsplash-scaled.jpg',
                                                 'Lagon de la mer Rouge'),
}


def journee(n, f, alt):
    def faire(h, j):
        if f in h:
            return h
        m = re.search(r'(<div class="jour" id="jour-%d">.*?<article class="etape" id="etape-\d+" data-lieu="[^"]*">)'
                      % n, h, re.S)
        if not m or h[m.end():m.end() + 40].startswith('<a class="etape__photo"'):
            return h
        ph = ('<a class="etape__photo" data-lb href="%s" data-alt="%s" aria-label="Agrandir la photo : %s">'
              '<img src="%s" alt="%s" decoding="async" sizes="(max-width:1040px) 100vw, 780px" loading="lazy"></a>'
              % (UP + f, alt, alt, UP + f, alt))
        j.append('jour %d : %s' % (n, alt))
        return h[:m.end()] + ph + h[m.end():]
    return faire


def main():
    a = argparse.ArgumentParser()
    a.add_argument('--essai', action='store_true')
    a.add_argument('--appliquer', action='store_true')
    a = a.parse_args()
    s = requests.Session()
    s.verify = '/root/.ccr/ca-bundle.crt'
    s.auth = tuple(os.environ['WP_AUTH'].split(':', 1))
    taches = [('pages', BLOG, blog), ('pages', ALEX, alexandrie), ('pages', ASSOUAN, assouan)]
    for slug, (n, f, alt) in JOURS.items():
        pid = s.get(SITE + '/wp-json/wp/v2/programs', params={'slug': slug, '_fields': 'id'}, timeout=120).json()[0]['id']
        taches.append(('programs', pid, journee(n, f, alt)))
    for typ, pid, f in taches:
        url = '%s/wp-json/wp/v2/%s/%d' % (SITE, typ, pid)
        h = s.get(url, params={'context': 'edit'}, timeout=300).json()['content']['raw']
        j = []
        h2 = f(h, j)
        print(pid, ' · '.join(j) or 'rien à faire')
        if j and a.appliquer:
            print('  écrit :', s.post(url, json={'content': h2}, timeout=600).status_code)


if __name__ == '__main__':
    main()
