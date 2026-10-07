#!/usr/bin/env python3
"""Les réponses de Mélanie restées sans suite dans les fils de septembre.

    WP_AUTH='compte:mdp' python3 outils/retours-anciens.py --essai
    WP_AUTH='compte:mdp' python3 outils/retours-anciens.py --appliquer

Elle avait répondu, dans le plugin, à des questions qu'on lui posait. Ses
réponses n'avaient pas été appliquées :

  10774 Le Caire · « combien de jours rester au Caire », avec sa réponse.
        La question existait déjà avec une réponse générique (3 à 5 jours) :
        elle reçoit la sienne, et « Où trouver les meilleures vues sur le
        Nil ? », qu'elle voulait voir remplacée, est retirée.
  10775 Le Caire · les musées dans son ordre : le GEM, le Musée égyptien,
        le Musée de la civilisation, et « il y a plein de musées
        intéressants ».
  10785 Louxor · « peut-on visiter sans guide ? », reformulé dans son sens :
        un guide qui s'adapte à votre rythme, des explications riches.
  10430 Lac Nasser · un troisième séjour, « croisière et mer Rouge ». Et la
        dahabeya y reçoit son prix, 1 895 €, comme partout ailleurs.
  10476 Accueil · « oui, faites la distinction entre le Nil et croisière ».
        « Croisière » garde les quatre séjours qui embarquent ; « Le Nil »
        sort les six qui passent par Louxor ou Assouan, bateau ou pas.

Le texte de ses réponses est repris tel quel, orthographe des lieux
alignée sur le site (Gizeh, Saqqara, Dahchour).
"""

import argparse
import os
import re
import time

import requests

SITE = 'https://authentiquegypte.com'

# ------------------------------------------------------------------ Le Caire
JOURS_AVANT = re.compile(
    r'(<summary>Combien de jours prévoir pour visiter Le Caire \?</summary>'
    r'<div class="faq__r">)<p class="">.*?</p>(</div>)', re.S)
JOURS_APRES = (
    '<p class=""><b>Une journée</b> peut suffire pour voir les pyramides de '
    'Gizeh et le Grand Musée égyptien. <b>Deux jours</b> permettent de '
    'découvrir aussi le vieux Caire : Le Caire copte et Le Caire islamique. '
    'Une <b>troisième journée</b> peut s’ajouter pour les pyramides de '
    'Saqqara et de Dahchour, ou pour une activité comme un cours de '
    'cuisine.</p>')

VUES_NIL = re.compile(
    r'<details class="faq__q faq__q--plus"><summary>Où trouver les meilleures '
    r'vues sur le Nil \?</summary>.*?</details>', re.S)

MUSEES_AVANT = re.compile(
    r'(<summary>Quels musées visiter absolument \?</summary>'
    r'<div class="faq__r">)<p class="">.*?</p>(</div>)', re.S)
MUSEES_APRES = (
    '<p class="">D’abord le <b>Grand Musée égyptien</b> (GEM), au pied des '
    'pyramides de Gizeh ; puis le Musée égyptien de la place Tahrir, pour ses '
    'collections pharaoniques ; puis le Musée national de la civilisation '
    'égyptienne, qui expose les momies royales. Et Le Caire compte bien '
    'd’autres musées intéressants, comme le musée copte ou le musée d’art '
    'islamique.</p>')

# ------------------------------------------------------------------- Louxor
GUIDE_AVANT = re.compile(
    r'(<summary>Peut-on visiter Louxor sans guide \?</summary>'
    r'<div class="faq__r">)<p class="">.*?</p>(</div>)', re.S)
GUIDE_APRES = (
    '<p class="">Oui, les sites se visitent sans guide. Mais avec un guide qui '
    's’adapte à vos envies et à votre rythme, la visite change : il explique '
    'ce que les panneaux ne disent pas, la symbolique d’un relief, l’histoire '
    'd’un temple, le détail qu’on ne remarquerait pas seul. Vous repartez avec '
    'des explications riches, pas seulement des photos.</p>')

# --------------------------------------------------------------- Lac Nasser
VOILE_CARTE = ('<h3>Le Caire et croisière sur un bateau à voile</h3></a>')
VOILE_PRIX = ('<h3>Le Caire et croisière sur un bateau à voile</h3>'
              '<p>À partir de <b>1895 €</b></p></a>')
TROISIEME = (
    '<a href="https://authentiquegypte.com/programs/mer-rouge/"><div '
    'class="proches__img"><img src="https://authentiquegypte.com/wp-content/'
    'uploads/2023/11/WhatsApp-Image-2025-08-14-at-13.23.16.jpeg" alt="Pyramides, '
    'croisière et mer rouge en famille" decoding="async" sizes="(max-width:860px) '
    '100vw, 380px" width="1280" height="720" loading="lazy"></div><h3>Pyramides, '
    'croisière et mer rouge en famille</h3><p>À partir de <b>1485 €</b></p></a>')
FIN_PROCHES = '</div><div class="proches__tous">'

# ------------------------------------------------------------------ Accueil
BOUTON_AVANT = ('<button class="opt" aria-pressed="false" data-val="croisiere">'
                'Croisière sur le Nil</button>')
BOUTON_APRES = ('<button class="opt" aria-pressed="false" data-val="croisiere">'
                'Croisière</button><button class="opt" aria-pressed="false" '
                'data-val="nil">Le Nil</button>')
LIB_AVANT = "croisiere:'la croisière sur le Nil',"
LIB_APRES = "croisiere:'la croisière',nil:'le Nil',"
# Les séjours qui passent par Louxor ou Assouan, d'après leur parcours.
PAR_LE_NIL = ['pyramides-et-croisiere-sur-le-nil',
              'le-caire-et-croisiere-sur-un-bateau-a-voile',
              'croisiere-sur-le-lac-nasser', 'mer-rouge', 'roadtrip-en-egypte',
              'pyramides-louxor-et-mer-rouge-en-famille']


def session():
    s = requests.Session()
    s.verify = '/root/.ccr/ca-bundle.crt'
    s.auth = tuple(os.environ['WP_AUTH'].split(':', 1))
    return s


def requete(s, methode, url, **k):
    for essai in range(4):
        try:
            r = s.request(methode, url, timeout=300, **k)
            if r.status_code < 500:
                return r
        except requests.RequestException:
            pass
        time.sleep(2 ** essai)
    raise SystemExit('Le site ne répond pas : ' + url)


def un(motif, rempl, h, nom, journal):
    """Une substitution qui doit avoir lieu exactement une fois."""
    if isinstance(motif, str):
        n = h.count(motif)
        h = h.replace(motif, rempl, 1)
    else:
        h, n = motif.subn(rempl, h, count=1)
    if n != 1:
        raise SystemExit('%s : %d occurrence(s), j’arrête.' % (nom, n))
    journal.append(nom)
    return h


def caire(h, j):
    h = un(JOURS_AVANT, lambda m: m.group(1) + JOURS_APRES + m.group(2), h,
           '10774 réponse « combien de jours »', j)
    h = un(VUES_NIL, '', h, '10774 « meilleures vues sur le Nil » retirée', j)
    h = un(MUSEES_AVANT, lambda m: m.group(1) + MUSEES_APRES + m.group(2), h,
           '10775 musées dans son ordre', j)
    # Une question repliée de moins : le bouton suit.
    m = re.search(r'Voir les (\d+) autres questions', h)
    n = int(m.group(1))
    h = h.replace('Voir les %d autres questions' % n,
                  'Voir les %d autres questions' % (n - 1))
    j.append('bouton FAQ %d → %d' % (n, n - 1))
    return h


def louxor(h, j):
    return un(GUIDE_AVANT, lambda m: m.group(1) + GUIDE_APRES + m.group(2), h,
              '10785 guide reformulé', j)


def nasser(h, j):
    h = un(VOILE_CARTE, VOILE_PRIX, h, '10430 prix de la dahabeya', j)
    debut = h.find('<div class="proches">')
    fin = h.find(FIN_PROCHES, debut)
    if debut < 0 or fin < 0:
        raise SystemExit('Bloc « proches » introuvable.')
    h = h[:fin] + TROISIEME + h[fin:]
    j.append('10430 troisième séjour')
    return h


def accueil(h, j):
    h = un(BOUTON_AVANT, BOUTON_APRES, h, '10476 bouton « Le Nil »', j)
    h = un(LIB_AVANT, LIB_APRES, h, '10476 libellé du composeur', j)
    debut = h.find('id="liste"')
    fin = h.find('</section>', debut)
    grille = h[debut:fin]
    for slug in PAR_LE_NIL:
        lien = 'programs/%s/' % slug
        i = grille.find(lien)
        a = grille.rfind('<article class="carte"', 0, i)
        b = grille.find('>', a)
        tete = grille[a:b]
        m = re.search(r'data-envie="([^"]*)"', tete)
        if i < 0 or not m:
            raise SystemExit('Carte introuvable : ' + slug)
        nouvelle = tete.replace(m.group(0), 'data-envie="%s nil"' % m.group(1))
        grille = grille[:a] + nouvelle + grille[b:]
    j.append('10476 « nil » sur %d cartes' % len(PAR_LE_NIL))
    return h[:debut] + grille + h[fin:]


PAGES = [('pages', 5191, caire), ('pages', 5201, louxor),
         ('programs', 1198, nasser), ('pages', 38, accueil)]


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--essai', action='store_true')
    p.add_argument('--appliquer', action='store_true')
    a = p.parse_args()
    s = session()
    for typ, pid, fonction in PAGES:
        url = '%s/wp-json/wp/v2/%s/%d' % (SITE, typ, pid)
        h = requete(s, 'GET', url, params={'context': 'edit'}).json()['content']['raw']
        if 'data-val="nil"' in h or 'Une journée</b> peut suffire' in h \
                or 'des explications riches, pas seulement' in h \
                or 'programs/mer-rouge/"><div class="proches__img"' in h:
            print('%-5d déjà fait' % pid)
            continue
        j = []
        h = fonction(h, j)
        print('%-5d %s' % (pid, ' · '.join(j)))
        if a.appliquer:
            r = requete(s, 'POST', url, json={'content': h})
            print('      écrit :', r.status_code)


if __name__ == '__main__':
    main()
