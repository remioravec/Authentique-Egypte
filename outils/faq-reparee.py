#!/usr/bin/env python3
"""La FAQ : le bouton perdu, les rubriques vides, les questions mal rangées.

    WP_AUTH='compte:mdp' python3 outils/faq-reparee.py --essai
    WP_AUTH='compte:mdp' python3 outils/faq-reparee.py --appliquer

Mélanie, le 6 octobre : « beug sur la FAQ » (Le Caire), « j'ai l'impression
qu'il manque des questions comparé à la dernière fois » (accueil), « la FAQ
n'est pas rangée dans les bonnes catégories » (Croisières).

Elle a raison les trois fois, et c'est le même défaut.

  · Le 22 septembre, faq-pliee.py a plié les FAQ : cinq questions visibles,
    les autres derrière un bouton « Voir les N autres questions » posé après
    la dernière question — donc à l'intérieur du dernier bloc `faqu`.
  · Le 5 octobre, retours-06-faq.py a rangé les FAQ en rubriques en
    reconstruisant chaque bloc `faqu` à partir de ses seules questions. Le
    bouton n'était pas une question : il est parti. Sur 34 pages, 553
    questions sont restées masquées sans plus aucun moyen de les ouvrir.
  · Et les questions masquées l'étaient par leur rang d'avant le rangement :
    des rubriques entières se retrouvaient sans une seule question visible,
    leur titre seul à l'écran — « Organiser avec nous », puis rien.
  · Le classement, enfin, se faisait par mots-clés trop lâches : « Le
    paiement est-il fractionnable ? » tombait en « Formalités et santé »,
    « Quels papiers d'identité faut-il ? » en « Bon à savoir », et deux blocs
    par page répétaient chacun leurs propres rubriques.

Ce que fait cet outil, page par page :
  1. il reprend toutes les questions de la section, dans l'ordre, sans en
     perdre une — il refuse d'écrire si l'ensemble des questions change ;
  2. il les range dans une seule suite de rubriques, chaque rubrique
     enveloppée avec son titre ;
  3. il plie dans l'ordre de lecture : les cinq premières visibles ;
  4. il repose le bouton, hors des blocs `faqu` cette fois, pour qu'un
     rangement futur ne puisse plus l'emporter ;
  5. une rubrique sans question visible se cache tant que la FAQ est pliée.
"""

import argparse
import base64
import html
import os
import re
import sys
import time
import unicodedata

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cibles

SITE = 'https://authentiquegypte.com'
VISIBLES = 5

# Deux ordres distincts. On CLASSE du plus précis au plus vague — un visa
# reste un visa même quand la question parle de croisière, et « paiement »
# ne doit pas partir chez les formalités. On AFFICHE ensuite du lieu vers
# l'administratif : ce que la page a de propre d'abord, ce que toutes les
# pages partagent ensuite.
CLASSEMENT = [
    ('Formalités et santé',
     ('visa', 'passeport', 'papiers', 'identite', 'documents necessaires',
      'formalite', 'vaccin', 'sante', 'soins medicaux', 'medic', 'pharmacie',
      'eau du robinet', 'potable', 'securite', 'securis', 'dangereux',
      'prudent', 'destination sure', 'assurance', 'autorisation',
      'paludisme', 'malade', 'precaution')),
    ('Organiser et réserver',
     ('sur mesure', 'organiser', 'organise', 'reservez', 'reserver',
      'reservation', 'vols internationaux', 'vols internes', 'devis',
      'paiement', 'payer', 'regler', 'acompte', 'fractionn', 'rembours',
      'annul', 'changer mes dates', 'ne peux plus partir', 'offrir',
      'carte-cadeau', 'carte cadeau', 'tarif', 'prix', 'cout', 'budget',
      'personnaliser', 'combin', 'associer', 'autres destinations',
      'etape par etape', 'itineraire type', 'types de circuits',
      'avec authentique', 'guide est inclus', 'visites culturelles sont',
      'hebergements et quels transferts', 'itineraire fixe',
      'principales etapes')),
    ('Pour qui, à quel rythme',
     ('famille', 'enfant', 'adolescent', 'poussette', 'pmr',
      'mobilite reduite', 'personnes agees', 'physique', 'difficile',
      'rythme', 'trajets sont-ils longs', 'fait pour moi', 'quel age',
      'niveau', 'en solo', 'a deux', 'aux couples')),
    ('Avant de partir',
     ('quand partir', 'quand visiter', 'meilleure periode', 'periode',
      'meilleure saison', 'moment ideal', 'combien de jour',
      'combien de temps', 'duree', 'faisable en', 'meteo', 'temperature',
      'climat', 'chaleur', 'en ete', 'hiver', 'ramadan', 'affluence',
      'a l avance', 'emporter', 'valise', 'habiller', 'tenue', 'vetement',
      'equipement', 'prevoir', 'preparer', 'avant de partir', 'se situe',
      'se trouve', 's y rendre', 'rejoindre')),
    ('Découvrir',
     ('qu est-ce que', 'qu est-ce qui', 'pourquoi', 'unique', 'particulier',
      'special', 'celebre', 'vaut-il', 'photogenique', 'alternative',
      'difference entre la rive', 'vestiges', 'spirituel')),
    ('Sur place',
     ('que voir', 'que faire', 'incontournable', 'site', 'visiter', 'visite',
      'deplacer', 'transport', 'bateau', 'croisiere', 'naviguer', 'a bord',
      'dormir', 'hebergement', 'hotel', 'bivouac', 'lodge', 'base',
      'manger', 'restaurant', 'excursion', 'acces', 'distance', 'journee',
      'lever du soleil', 'randonnee', 'ascension', 'horaires', 'plongee',
      'snorkeling', 'recif', 'quartier', 'musee', 'temple', 'tombe', 'vue',
      'experience', 'activite', 'a pied', 'guide', 'faune', 'photo',
      'baigner', 'montgolfiere', 'marche', 'village', 'vallee',
      'bibliotheque')),
]
AFFICHAGE = ['Découvrir', 'Avant de partir', 'Sur place',
             'Pour qui, à quel rythme', 'Formalités et santé',
             'Organiser et réserver']
DEFAUT = 'Bon à savoir'

STYLE = (
    '<style id="faq-rub-css">'
    '.faq__rub{display:grid;gap:10px}'
    '.faqu .faq__rub + .faq__rub{margin-top:6px}'
    'section[data-plie]:not(.faq--ouverte) '
    '.faq__rub:not(:has(.faq__q:not(.faq__q--plus))){display:none}'
    'section[data-plie] .faq__q--plus{display:none}'
    'section[data-plie].faq--ouverte .faq__q--plus{display:block}'
    # l'accueil n'a pas de .pg : le bouton y garde quand même sa forme
    '.faq__plus{display:block;width:100%;margin:16px 0 0;'
    'padding:14px 20px;background:#fff;color:var(--teal-txt,#10657C);'
    'border:1px solid var(--ligne,#E4E4EA);border-radius:14px;'
    'font-weight:700;font-size:1rem;min-height:48px;cursor:pointer}'
    '.faq__plus:hover{background:var(--teal-fond,#BEE6F1)}'
    '.faq__plus:focus-visible{outline:3px solid var(--or,#ECAA24);'
    'outline-offset:2px}'
    '</style>')

SCRIPT = (
    '<script data-faq="pliee">(function(){'
    'document.querySelectorAll("section[data-plie]").forEach(function(f){'
    'var b=f.querySelector(".faq__plus");if(!b){return;}'
    'if(b.dataset.pose){return;}b.dataset.pose="1";'
    'var reste=b.getAttribute("data-reste")||"";'
    'b.addEventListener("click",function(){'
    'var ouvert=f.classList.toggle("faq--ouverte");'
    'b.setAttribute("aria-expanded",ouvert?"true":"false");'
    'b.textContent=ouvert?"Afficher moins de questions":reste;'
    'if(!ouvert){f.querySelectorAll(".faq__q--plus[open]").forEach('
    'function(d){d.open=false;});'
    'f.scrollIntoView({block:"start",behavior:"smooth"});}'
    '});});})();</script>')


def sa(s):
    s = unicodedata.normalize('NFD', html.unescape(s))
    return ''.join(c for c in s if unicodedata.category(c) != 'Mn').lower() \
        .replace('’', "'").replace("'", ' ')


def rubrique(q):
    t = ' ' + sa(q) + ' '
    for nom, mots in CLASSEMENT:
        if any(m in t for m in mots):
            return nom
    return DEFAUT


def fin_div(h, d):
    p, k = 0, d
    while k < len(h):
        if h.startswith('<div', k):
            p += 1
        elif h.startswith('</div>', k):
            p -= 1
            if p == 0:
                return k + len('</div>')
        k += 1
    return -1


def paires(zone):
    """Chaque question refaite à neuf : son <summary> et sa réponse.

    On ne découpe pas les <details> par expression régulière : sur quatre
    pages, un <details> mal refermé en contient un autre, et le premier
    « </details> » rencontré n'est pas le sien. On reprend donc chaque
    question par ses deux morceaux sûrs — l'intitulé, et le <div class=
    "faq__r"> qui le suit, compté à la profondeur — et on rebâtit le
    <details> autour.
    """
    out, i = [], 0
    while True:
        i = zone.find('<summary', i)
        if i < 0:
            return out
        j = zone.find('</summary>', i)
        r = zone.find('<div class="faq__r"', j)
        if j < 0 or r < 0:
            return out
        f = fin_div(zone, r)
        if f < 0:
            return out
        suivant = zone.find('<summary', j)
        if 0 <= suivant < r:
            i = j       # un intitulé sans réponse : on le laisse
            continue
        out.append('<details class="faq__q">' + zone[i:j + len('</summary>')]
                   + zone[r:f] + '</details>')
        i = f


def question(d):
    m = re.search(r'<summary[^>]*>(.*?)</summary>', d, re.S)
    return html.unescape(re.sub(r'<[^>]+>', '', m.group(1))).strip() if m else ''


def corriger(h):
    i = h.find('id="t-faq"')
    if i < 0:
        return h, None
    s = h.rfind('<section', 0, i)
    d = h.find('<div class="faqu"', i)
    if s < 0 or d < 0:
        return h, None
    # tous les blocs faqu qui se suivent, avec ce qui les sépare
    blocs, k = [], d
    while True:
        f = fin_div(h, k)
        if f < 0:
            return h, None
        blocs.append((k, f))
        suite = re.match(r'\s*(<button type="button" class="faq__plus"[^>]*>'
                         r'.*?</button>\s*)?<div class="faqu"', h[f:], re.S)
        if not suite:
            break
        k = f + suite.end() - len('<div class="faqu"')
    deb, fin = blocs[0][0], blocs[-1][1]
    # un bouton qui suivrait le dernier bloc part avec la zone réécrite
    apres = re.match(r'\s*<button type="button" class="faq__plus"[^>]*>.*?</button>',
                     h[fin:], re.S)
    if apres:
        fin += apres.end()
    zone = h[deb:fin]

    ds = paires(zone)
    if not ds:
        return h, None
    vus, uniques = set(), []
    for x in ds:
        q = question(x)
        if q in vus:
            continue
        vus.add(q)
        uniques.append(x)

    groupes = {}
    for x in uniques:
        groupes.setdefault(rubrique(question(x)), []).append(x)
    ordre = AFFICHAGE + [DEFAUT]
    rangees = [(n, groupes[n]) for n in ordre if groupes.get(n)]

    # plier dans l'ordre de lecture
    rang, sortie = 0, []
    for nom, qs in rangees:
        morceaux = []
        for x in qs:
            if rang >= VISIBLES:
                x = x.replace('<details class="faq__q">',
                              '<details class="faq__q faq__q--plus">', 1)
            morceaux.append(x)
            rang += 1
        sortie.append('<div class="faq__rub"><p class="faq__t">%s</p>%s</div>'
                      % (nom, ''.join(morceaux)))
    total = len(uniques)
    neuf = '<div class="faqu">' + ''.join(sortie) + '</div>'
    reste = total - VISIBLES
    if reste > 0:
        libelle = ('Voir les %d autres questions' % reste if reste > 1
                   else 'Voir la dernière question')
        neuf += ('<button type="button" class="faq__plus" aria-expanded="false" '
                 'data-reste="%s">%s</button>' % (libelle, libelle))

    # contrôle : les mêmes questions, ni plus ni moins
    avant = {html.unescape(re.sub(r'<[^>]+>', '', x)).strip()
             for x in re.findall(r'<summary[^>]*>(.*?)</summary>', zone, re.S)}
    apres = {question(x) for x in paires(neuf)}
    if avant != apres:
        raise SystemExit('l ensemble des questions changerait : %s'
                         % sorted(avant ^ apres)[:4])

    h = h[:deb] + neuf + h[fin:]
    # la section se plie
    tete = re.match(r'<section\b[^>]*>', h[s:]).group(0)
    if reste > 0 and 'data-plie' not in tete:
        h = h[:s] + tete[:-1] + ' data-plie>' + h[s + len(tete):]
    # feuille et script, une seule fois, version à jour
    h = re.sub(r'<style id="faq-rub-css">.*?</style>', '', h, flags=re.S)
    h = re.sub(r'<script data-faq="pliee">.*?</script>', '', h, flags=re.S)
    s = h.rfind('<section', 0, h.find('id="t-faq"'))
    h = h[:s] + STYLE + SCRIPT + h[s:]
    return h, {'questions': total, 'doublons': len(ds) - total,
               'visibles': min(total, VISIBLES),
               'rubriques': ' · '.join('%s %d' % (n, len(q)) for n, q in rangees)}


def mal_refermee(h):
    a = h.find('<main')
    b = h.find('</main>', a)
    if a < 0 or b < 0:
        a, b = 0, len(h)
    pile, seules = [], 0
    for m in re.finditer(r'<(section|div|details|article)(?:\s[^>]*)?>'
                         r'|</(section|div|details|article)>', h[a:b]):
        if m.group(0).startswith('</'):
            if pile and pile[-1] == m.group(2):
                pile.pop()
            else:
                seules += 1
        else:
            pile.append(m.group(1))
    return seules + len(pile)


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

    a_ecrire = []
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
        if not j or neuf == h:
            continue
        if mal_refermee(neuf) > mal_refermee(h):
            raise SystemExit('%s serait moins bien refermée' % c['url'])
        a_ecrire.append((c, neuf))
        print('%-46s %2d q. (%d doublon) · %s'
              % (c['url'].replace(SITE, '')[:46], j['questions'], j['doublons'],
                 j['rubriques']))

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
