#!/usr/bin/env python3
"""Le blog : des filtres, des libellés qui disent quoi, et « Au choix » en moins.

    WP_AUTH='compte:mdp' python3 outils/retours-07-blog.py --essai
    WP_AUTH='compte:mdp' python3 outils/retours-07-blog.py --appliquer

Trois demandes de Mélanie sur /notre-blog/ :

12330 « est-ce possible de varier pour chaque article le texte du bouton ca
    fait bcp de répétition ». Les vingt-deux cartes disaient « Lire le guide ».
    Chaque libellé dit maintenant ce qu'on va trouver derrière, et aucun ne se
    répète.

12331 « est-ce possible de mettre des filtres par catégories d'articles ? ».
    Les vingt-deux articles sont tous dans la seule catégorie WordPress
    « Blog » : il n'y avait rien à exploiter. Les thèmes sont donc déclarés
    ici, sur les cartes, et le filtre est autonome — sa feuille de style et
    son script voyagent avec lui, sans dépendre du gabarit.

12332 « a supprimer » sur le surtitre « Au choix ».

Au passage, les vingt-deux images de cartes n'avaient pas d'alternative
textuelle : elles prennent le titre de l'article.

Le script est écrit sans esperluette et sans chevron ouvrant : WordPress
encode « && » en « &#038;&#038; » au rendu, ce qui casserait le filtre.
"""

import argparse
import base64
import html
import os
import re
import time

import requests

SITE = 'https://authentiquegypte.com'

RUBRIQUES = [
    ('tout', 'Tous les guides'),
    ('itineraires', 'Itinéraires et expériences'),
    ('famille', 'En famille et accessibilité'),
    ('reflexes', 'Éviter les faux pas'),
    ('securite', 'Sécurité'),
    ('saison', 'Quand partir'),
    ('formalites', 'Formalités et santé'),
    ('preparer', 'Préparer son voyage'),
]

# slug de l'article → (thème, libellé du bouton)
GUIDES = {
    '10-choses-a-ne-pas-faire-en-egypte':
        ('reflexes', 'Voir les 10 pièges'),
    'erreurs-voyage-egypte':
        ('reflexes', 'Voir les 10 erreurs'),
    'les-arnaques-et-erreurs-a-eviter-en-egypte':
        ('reflexes', 'Reconnaître les arnaques'),
    'comment-shabiller-en-egypte':
        ('preparer', 'Voir quoi emporter'),
    'guide-complet':
        ('preparer', 'Lire le guide complet'),
    'croisiere-egypte-dahabieh-bateau-felouque':
        ('itineraires', 'Comparer les trois bateaux'),
    'egypte-circuits-pour-passionnes-histoire':
        ('itineraires', 'Voir les 5 circuits'),
    'egypte-hors-des-sentiers-battus':
        ('itineraires', 'Découvrir les 8 lieux'),
    'experiences-egypte-au-dela-des-pyramides':
        ('itineraires', 'Voir les expériences'),
    'incontournables-voyage-egypte':
        ('itineraires', 'Parcourir les incontournables'),
    'preparer-son-voyage-au-caire':
        ('itineraires', 'Voir ce qu’il faut voir au Caire'),
    'egypte-en-hiver':
        ('saison', 'Lire pour l’hiver'),
    'quand-partir-en-egypte':
        ('saison', 'Voir mois par mois'),
    'passeport-egypte':
        ('formalites', 'Vérifier mon passeport'),
    'vaccins-egypte':
        ('formalites', 'Voir les vaccins conseillés'),
    'securite-egypte-2025':
        ('securite', 'Lire le point sécurité'),
    'securite-en-egypte-en-2026':
        ('securite', 'Lire le guide 2026'),
    'securite-en-egypte-pour-un-voyage-en-famille':
        ('securite', 'Lire le point famille'),
    'egypte-enfants-activites':
        ('famille', 'Voir les idées par âge'),
    'voyager-en-egypte-en-famille':
        ('famille', 'Lire la réponse complète'),
    'guide-complet-des-formalites-pour-un-voyage-en-egypte-pour-un-francophone':
        ('famille', 'Lire le guide famille'),
    'voyager-en-egypte-fauteuil-roulant':
        ('famille', 'Lire le guide accessibilité'),
}

STYLE = (
    '<style id="guides-css">'
    '#guides .gf{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 10px;'
    'padding:0;list-style:none}'
    '#guides .gf__b{font:inherit;font-size:.9rem;line-height:1.25;'
    'padding:9px 15px;border:1px solid var(--ligne,#E4E4EA);'
    'border-radius:999px;background:#fff;color:#1b1b1f;cursor:pointer;'
    'transition:background .15s,border-color .15s,color .15s}'
    '#guides .gf__b b{font-weight:500}'
    '#guides .gf__b small{opacity:.5;margin-left:7px;font-size:.85em;'
    'font-variant-numeric:tabular-nums}'
    '#guides .gf__b:hover{border-color:var(--nuit,#147894)}'
    '#guides .gf__b[aria-pressed="true"]{background:var(--nuit,#147894);'
    'border-color:var(--nuit,#147894);color:#fff}'
    '#guides .gf__b[aria-pressed="true"] small{opacity:.75}'
    '#guides .gf__b:focus-visible{outline:2px solid var(--or,#ECAA24);'
    'outline-offset:2px}'
    '#guides .gf__cpt{margin:0 0 26px;font-size:.9rem;color:#5e5e66}'
    '@media (max-width:640px){#guides .gf{gap:6px}'
    '#guides .gf__b{font-size:.84rem;padding:8px 12px}}'
    '</style>')

SCRIPT = (
    '<script id="guides-js">(function(){'
    'var z=document.getElementById("guides");'
    'if(!z){return;}'
    'var bs=z.querySelectorAll("[data-gf]");'
    'var cs=z.querySelectorAll("article[data-theme-guide]");'
    'var cpt=z.querySelector(".gf__cpt");'
    'function montre(c){'
    'var n=0;'
    'Array.prototype.forEach.call(cs,function(el){'
    'var ok=c==="tout";'
    'if(!ok){if(el.getAttribute("data-theme-guide")===c){ok=true;}}'
    'el.hidden=!ok;'
    'if(ok){n=n+1;}'
    '});'
    'if(cpt){cpt.textContent=n===1?"1 guide affiché":n+" guides affichés";}'
    '}'
    'Array.prototype.forEach.call(bs,function(b){'
    'b.addEventListener("click",function(){'
    'Array.prototype.forEach.call(bs,function(o){'
    'o.setAttribute("aria-pressed",o===b?"true":"false");'
    '});'
    'montre(b.getAttribute("data-gf"));'
    '});'
    '});'
    '})();</script>')


def cartes(h):
    out, i = [], 0
    while True:
        i = h.find('<article class="carte"', i)
        if i < 0:
            return out
        p, k = 0, i
        while k < len(h):
            if h.startswith('<article', k):
                p += 1
            elif h.startswith('</article>', k):
                p -= 1
                if p == 0:
                    k += len('</article>')
                    break
            k += 1
        out.append((i, k))
        i = k


def filtre(compte):
    lis = []
    for cle, nom in RUBRIQUES:
        n = compte['tout'] if cle == 'tout' else compte.get(cle, 0)
        if not n:
            continue
        lis.append(
            '<li><button type="button" class="gf__b" data-gf="%s" '
            'aria-pressed="%s"><b>%s</b><small>%d</small></button></li>'
            % (cle, 'true' if cle == 'tout' else 'false', nom, n))
    return (STYLE + '<ul class="gf">' + ''.join(lis) + '</ul>'
            + '<p class="gf__cpt" role="status" aria-live="polite">'
            '%d guides affichés</p>' % compte['tout'])


def corriger(h):
    j = {}

    def note(cle, n):
        if n:
            j[cle] = j.get(cle, 0) + n

    a = h.find('<main')
    b = h.find('</main>', a)
    if a < 0 or b < 0:
        raise SystemExit('pas de main refermé')
    tete, corps, pied = h[:a], h[a:b], h[b:]

    # 12332 · « a supprimer » sur le surtitre
    corps, n = re.subn(r'<p class="eyebrow">Au choix</p>', '', corps)
    note('12332 surtitre retiré', n)

    compte = {'tout': 0}
    inconnus = []
    for deb, fin in reversed(cartes(corps)):
        c = corps[deb:fin]
        m = re.search(r'authentiquegypte\.com/([a-z0-9-]+)/', c)
        slug = m.group(1) if m else ''
        if slug not in GUIDES:
            inconnus.append(slug)
            continue
        theme, libelle = GUIDES[slug]
        neuf = c
        if 'data-theme-guide' not in neuf:
            neuf = neuf.replace('<article class="carte"',
                                '<article class="carte" data-theme-guide="%s"'
                                % theme, 1)
        # 12330 · varier le libellé du bouton
        neuf, n = re.subn(r'(class="lien-fl"[^>]*>)[^<]*(</a>)',
                          lambda mm: mm.group(1) + libelle + mm.group(2), neuf)
        note('12330 libellé', n)
        # une alternative textuelle pour l'image de la carte
        t = re.search(r'<h3><a[^>]*>(.*?)</a>', neuf, re.S)
        if t:
            titre = html.escape(html.unescape(
                re.sub(r'<[^>]+>', '', t.group(1))).strip(), quote=True)
            neuf, n = re.subn(r'(<img [^>]*?)alt=""', r'\1alt="%s"' % titre,
                              neuf)
            note('alt rempli', n)
        compte['tout'] += 1
        compte[theme] = compte.get(theme, 0) + 1
        if neuf != c:
            corps = corps[:deb] + neuf + corps[fin:]

    if inconnus:
        raise SystemExit('article(s) hors tableau : %s' % ', '.join(inconnus))

    # 12331 · le filtre, posé devant la grille, et le script derrière
    if 'class="gf"' not in corps:
        k = corps.find('<div class="cartes cartes--2">')
        if k < 0:
            raise SystemExit('grille des guides introuvable')
        corps = (corps[:k] + '<div id="guides">' + filtre(compte)
                 + corps[k:])
        # on referme juste après la dernière carte de la grille
        g = corps.find('</article></div>') + len('</article></div>')
        corps = corps[:g] + SCRIPT + '</div>' + corps[g:]
        note('12331 filtre posé', 1)

    return tete + corps + pied, j, compte


def main():
    p = argparse.ArgumentParser()
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument('--essai', action='store_true')
    g.add_argument('--appliquer', action='store_true')
    a = p.parse_args()

    S = requests.Session(); S.verify = '/root/.ccr/ca-bundle.crt'
    u, m = os.environ['WP_AUTH'].split(':', 1)
    S.headers['Authorization'] = 'Basic ' + base64.b64encode(
        ('%s:%s' % (u, m)).encode()).decode()
    B = SITE + '/wp-json/wp/v2/pages/2368'

    for essai in range(5):
        r = S.get(B, params={'context': 'edit'}, timeout=240)
        if r.status_code < 300:
            break
        time.sleep(2 ** essai)
    else:
        raise SystemExit('lecture refusée : %d' % r.status_code)
    h = (r.json().get('content') or {}).get('raw', '')
    neuf, j, compte = corriger(h)
    print(' · '.join('%s ×%d' % (k, v) for k, v in sorted(j.items())))
    print('thèmes : ' + ', '.join('%s %d' % (k, compte[k])
                                  for k, _ in RUBRIQUES if compte.get(k)))
    libelles = re.findall(r'class="lien-fl"[^>]*>([^<]*)</a>', neuf)
    print('%d libellés, %d distincts' % (len(libelles), len(set(libelles))))
    if neuf == h:
        print('rien à écrire')
        return
    if a.essai:
        open('/tmp/claude-0/blog-essai.html', 'w').write(neuf)
        return
    for essai in range(4):
        r = S.post(B, json={
            'content': '<!-- wp:html -->\n' + neuf + '\n<!-- /wp:html -->'},
            timeout=300)
        if r.status_code < 300:
            break
        time.sleep(2 ** essai)
    else:
        raise SystemExit('écriture refusée')
    print('page écrite.')


if __name__ == '__main__':
    main()
