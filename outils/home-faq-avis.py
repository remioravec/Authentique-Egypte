#!/usr/bin/env python3
"""Aligner la FAQ et les avis de l'accueil sur le design des 54 autres pages.

    python3 outils/home-faq-avis.py --essai        (hors ligne, sur la sauvegarde)
    WP_AUTH='compte:mdp' python3 outils/home-faq-avis.py --appliquer

La cause de l'écart, trouvée en comparant l'accueil à une page de référence :
les 54 autres pages ouvrent leur contenu par `<main class="pg">`, l'accueil
par `<main id="main">`. Toutes les règles du style portées par `.pg` — et il
y en a 68 dans la feuille de l'accueil elle-même — ne s'y appliquaient donc
jamais. D'où des avis et une FAQ au même balisage mais pas au même dessin.

On ne met pas `.pg` sur le <main> de l'accueil : cela ferait basculer d'un
coup le héros et toutes ses sections propres, bien au-delà de ce qui est
demandé. On enveloppe les deux seules sections concernées.

Cinq gestes, tous bornés à ces deux sections :

  1. une enveloppe `<div class="pg">` autour de la section avis et de la
     section FAQ — aucune règle ne vise `.pg` lui-même, l'enveloppe
     n'ajoute donc aucune mise en page ;
  2. la section avis passe de `section section--fond` à `pg-sec`, le
     conteneur qu'utilisent les autres pages ;
  3. les lignes d'étoiles `p.mur__et` sont retirées : les autres pages
     n'affichent pas de note par avis. ATTENTION, c'est une perte : un des
     huit avis est à 4/5, les sept autres à 5/5, et cette nuance disparaît.
     Le texte des avis, lui, n'est pas touché — jamais.
  4. le logo Google de chaque avis reçoit `class="gg"`, comme ailleurs ;
  5. le bloc `mur__liens` (vers les avis Google et TripAdvisor) est ajouté
     en pied de mur, à l'identique des autres pages.

Puis les règles `.pg`-portées qui manquent à la feuille de l'accueil sont
reprises telles quelles de la page de référence, media queries comprises.
"""

import argparse
import json
import os
import re
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAUVE = os.path.join(RACINE, 'sauvegarde', 'avant-mise-en-ligne')
HOME_BROUILLON, HOME_LIGNE = 8660, 38
REFERENCE = 8923          # Refonte · Destination · Voyage à Fayoum
FAMILLES = r'(\.pg \.?(mur|ini|faq|eyebrow)|\.pg-sec(--|\s*[,{]|$))'
# Ce qui n'a rien à faire dans ces deux sections, et qu'on ne reprend donc pas.
HORS_SUJET = r'(devis|hero|carte|bref|ariane|reperes|tabx|galerie|quand|etape|jour)'


def decoupe(c):
    """(media, selecteur, corps) pour chaque règle, @media aplaties."""
    out, i, n = [], 0, len(c)
    while i < n:
        j = c.find('{', i)
        if j < 0:
            break
        tete = c[i:j].strip()
        p, k = 1, j + 1
        while k < n and p:
            if c[k] == '{':
                p += 1
            elif c[k] == '}':
                p -= 1
            k += 1
        corps = c[j + 1:k - 1]
        if tete.startswith(('@media', '@supports')):
            for _, s, b in decoupe(corps):
                out.append((re.sub(r'\s+', ' ', tete), s, b))
        elif tete.startswith('@'):
            out.append(('', tete, corps.strip()))
        else:
            out.append(('', re.sub(r'\s+', ' ', tete), corps.strip()))
        i = k
    return out


def feuilles(s):
    """Les feuilles de style de la page, commentaires ôtés.

    Le commentaire compte : sans cela, le `/* ... */` que cet outil écrit
    en tête de son bloc se recollerait au premier sélecteur à la relecture,
    et l'outil croirait la règle absente à chaque passage.
    """
    c = ''.join(re.findall(r'<style[^>]*>(.*?)</style>', s, re.S))
    return re.sub(r'/\*.*?\*/', '', c, flags=re.S)


def section(h, ancre):
    """Les bornes du <section> qui contient l'ancre, comptées à la main.

    Pas de regex : ces pages font jusqu'à 3,7 Mo, et une expression
    gourmande sur un balisage imbriqué ne revient jamais.
    """
    i = h.find(ancre)
    if i < 0:
        raise SystemExit('ancre %s absente' % ancre)
    d = h.rfind('<section', 0, i)
    p, k = 0, d
    while k < len(h):
        if h.startswith('<section', k):
            p += 1
        elif h.startswith('</section>', k):
            p -= 1
            if p == 0:
                return d, k + len('</section>')
        k += 1
    raise SystemExit('section non fermée autour de %s' % ancre)


def corriger(home, ref):
    """Rend le nouveau contenu de l'accueil, et le compte rendu des gestes."""
    journal = {}

    # --- la section avis -----------------------------------------------
    da, fa = section(home, 'id="t-avis"')
    avis = home[da:fa]

    av = avis.replace('<section class="section section--fond"',
                      '<section class="pg-sec"', 1)
    journal['conteneur avis'] = int(av != avis)

    # les étoiles : on borne chaque <p class="mur__et"> à la main
    n_et = 0
    while True:
        i = av.find('<p class="mur__et">')
        if i < 0:
            break
        j = av.find('</p>', i)
        av = av[:i] + av[j + 4:]
        n_et += 1
    journal['lignes d étoiles retirées'] = n_et

    # le logo Google prend la classe qu'il a ailleurs
    av, n_gg = re.subn(r'<svg width="21" height="21" viewBox="0 0 48 48" aria-hidden="true">',
                       '<svg class="gg" aria-hidden="true" width="21" height="21" '
                       'viewBox="0 0 48 48">', av)
    journal['logos Google classés'] = n_gg

    # le bloc de liens vers Google et TripAdvisor : l'accueil l'a déjà.
    # On ne le reprend de la référence que s'il manque.
    i = ref.find('<div class="mur__liens">')
    if i < 0:
        raise SystemExit('mur__liens absent de la référence')
    j = ref.find('</div>', ref.find('</a>', ref.rfind('<a', i, ref.find('</div>', i) + 6)))
    # bornage sûr : on compte les <div> ouverts
    p, k = 0, i
    while k < len(ref):
        if ref.startswith('<div', k):
            p += 1
        elif ref.startswith('</div>', k):
            p -= 1
            if p == 0:
                liens = ref[i:k + 6]
                break
        k += 1
    else:
        raise SystemExit('mur__liens non fermé dans la référence')
    if 'mur__liens' not in av:
        # juste après la fermeture du mur, comme sur les autres pages
        m = av.find('<div class="mur"')
        p, k = 0, m
        while k < len(av):
            if av.startswith('<div', k):
                p += 1
            elif av.startswith('</div>', k):
                p -= 1
                if p == 0:
                    k += 6
                    break
            k += 1
        av = av[:k] + liens + av[k:]
        journal['bloc de liens ajouté'] = 1
    else:
        journal['bloc de liens ajouté'] = 0

    if home[:da].rstrip().endswith('<div class="pg">'):
        journal['enveloppe pg sur les avis'] = 0      # déjà posée
    else:
        av = '<div class="pg">' + av + '</div>'
        journal['enveloppe pg sur les avis'] = 1
    home = home[:da] + av + home[fa:]

    # --- la section FAQ ------------------------------------------------
    df, ff = section(home, 'id="t-faq"')
    if home[:df].rstrip().endswith('<div class="pg">'):
        journal['enveloppe pg sur la FAQ'] = 0        # déjà posée
    else:
        home = (home[:df] + '<div class="pg">' + home[df:ff] + '</div>' + home[ff:])
        journal['enveloppe pg sur la FAQ'] = 1

    # --- les règles manquantes ----------------------------------------
    rh, rr = decoupe(feuilles(home)), decoupe(feuilles(ref))
    deja = {(c, s) for c, s, _ in rh}
    def confiner(sel):
        """Garder la règle dans les deux sections enveloppées, pas ailleurs.

        Les règles de base `.pg-sec` de la référence ne sont pas portées par
        `.pg` : telles quelles, elles toucheraient toutes les sections de
        l'accueil. On insère donc `.pg` devant.
        """
        return ', '.join(
            (x if '.pg ' in x else
             x.replace('.elementor-template-canvas ', '.elementor-template-canvas .pg ', 1)
             if '.elementor-template-canvas ' in x else '.pg ' + x)
            for x in (y.strip() for y in sel.split(',')))

    aporter = []
    for c, s, b in rr:
        if not re.search(FAMILLES, s) or re.search(HORS_SUJET, s):
            continue
        s2 = confiner(s)
        if (c, s2) in deja or (c, s) in deja:
            continue
        aporter.append((c, s2, b))
    par_media = {}
    for c, s, b in aporter:
        par_media.setdefault(c, []).append('%s{%s}' % (s, b))
    bloc = []
    for c in sorted(par_media, key=lambda x: (x != '', x)):
        regles = ''.join(par_media[c])
        bloc.append(regles if not c else '%s{%s}' % (c, regles))
    if bloc:
        home += ('<style>/* FAQ et avis de l\'accueil, alignés sur les autres '
                 'pages : les règles portées par .pg que cette feuille '
                 'n\'avait pas. */\n' + '\n'.join(bloc) + '</style>')
    journal['règles reportées'] = len(aporter)
    return home, journal


def main():
    p = argparse.ArgumentParser()
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument('--essai', action='store_true')
    g.add_argument('--appliquer', action='store_true')
    a = p.parse_args()

    jours = sorted(j for j in os.listdir(SAUVE) if len(j) == 10 and j[4] == '-')
    D = os.path.join(SAUVE, jours[-1], 'brouillons')
    home = json.load(open(os.path.join(D, '%d.json' % HOME_BROUILLON)))['contenu']
    ref = json.load(open(os.path.join(D, '%d.json' % REFERENCE)))['contenu']

    neuf, journal = corriger(home, ref)
    for k, v in journal.items():
        print('   %-28s %s' % (k, v))
    print('   %-28s %d → %d octets' % ('taille', len(home), len(neuf)))

    # contrôles hors ligne, avant toute écriture
    def balises(s):
        o = len(re.findall(r'<(section|div|article|details)[\s>]', s))
        f = len(re.findall(r'</(section|div|article|details)>', s))
        return o, f
    print('   %-28s avant %s · après %s' % ('balises ouvertes/fermées',
                                            balises(home), balises(neuf)))
    def mots(s):
        return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ',
                      re.sub(r'<style.*?</style>|<script.*?</script>', ' ', s, flags=re.S)))
    ma, mn = mots(home), mots(neuf)
    perdus = [x for x in ('Quel bonheur', 'avis Google sur', 'Questions fréquentes')
              if x in ma and x not in mn]
    print('   %-28s %s' % ('repères de texte perdus', perdus or 'aucun'))
    print('   %-28s %d → %d caractères' % ('texte visible', len(ma), len(mn)))
    neuf2, _ = corriger(neuf, ref)
    print('   %-28s %s' % ('idempotent', 'oui' if neuf2 == neuf else 'NON'))

    chemin = os.path.join(os.environ.get('SP', '/tmp'), 'home-corrigee.html')
    open(chemin, 'w').write(neuf)
    print('   écrit dans %s' % chemin)

    if a.essai:
        return

    import base64, time, requests
    S = requests.Session(); S.verify = '/root/.ccr/ca-bundle.crt'
    u, m = os.environ['WP_AUTH'].split(':', 1)
    S.headers['Authorization'] = 'Basic ' + base64.b64encode(
        ('%s:%s' % (u, m)).encode()).decode()
    B = 'https://authentiquegypte.com/wp-json/wp/v2/'

    # le brouillon garde le contenu tel quel ; la page en ligne reçoit la
    # même correction appliquée à SON contenu, liens déjà réécrits comprises
    r = S.get(B + 'pages/%d' % HOME_LIGNE, params={'context': 'edit'}, timeout=120)
    enligne = (r.json().get('content') or {}).get('raw', '')
    neuf_ligne, j2 = corriger(enligne, ref)
    print('\nen ligne : %d → %d octets · %s' % (len(enligne), len(neuf_ligne), j2))

    for base, pid, corps in (('pages', HOME_BROUILLON, neuf),
                             ('pages', HOME_LIGNE, neuf_ligne)):
        charge = {'content': '<!-- wp:html -->\n' + corps + '\n<!-- /wp:html -->'}
        for essai in range(4):
            r = S.post(B + '%s/%d' % (base, pid), json=charge, timeout=300)
            if r.status_code < 300:
                print('   écrit %s #%d' % (base, pid))
                break
            print('      reprise %d/3 — HTTP %d' % (essai + 1, r.status_code))
            time.sleep(2 ** essai)
        else:
            sys.exit('écriture refusée sur %s #%d' % (base, pid))


if __name__ == '__main__':
    main()
