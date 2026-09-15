#!/usr/bin/env python3
"""
Sort les brouillons de la refonte du back-office, pour les montrer sans compte.

    WP_AUTH='compte:mot de passe' ./outils/exposer-brouillons.py --sortie DIR

Une page en brouillon n'est visible que connecté : le client à qui l'on
envoie le lien tombe sur un 404. Ce script relève les pages sous « Refonte
2026 », rapatrie les images qu'elles citent, réécrit les adresses pour les
servir depuis le dossier, et pose un sommaire cliquable devant. Le tout
tient dans un dossier qu'on publie où l'on veut — aucune authentification.

Ce qui est montré est le contenu réellement stocké dans WordPress, à
l'instant du relevé, sans retouche : c'est le point de l'exercice.

Les images sont ramenées à 1400 px de large et réencodées, sinon le dossier
pèse cinquante mégaoctets. Celles qui manquent sur le site — le serveur
répond 404 — sont remplacées par un cadre qui le dit, plutôt que par
l'image cassée du navigateur : c'est un défaut du site, il doit se voir.
"""

import argparse
import datetime
import hashlib
import html as H
import json
import os
import re
import subprocess
import sys
from importlib.machinery import SourceFileLoader

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dep = SourceFileLoader('dep', os.path.join(RACINE, 'outils', 'deployer.py')).load_module()
som = SourceFileLoader('som', os.path.join(RACINE, 'outils', 'sommaire-cms.py')).load_module()

MERE = som.MERE
SITE = dep.SITE
LARGE = 1400
QUALITE = 80


def cle(url):
    return hashlib.md5(url.encode('utf-8')).hexdigest()[:12]


# ── relevé ────────────────────────────────────────────────────────────────

def relever():
    q = '/pages?parent=%d&per_page=100&status=any&context=edit&orderby=menu_order&order=asc'
    dossiers = []
    for d in dep.appel('GET', q % MERE):
        enfants = dep.appel('GET', q % d['id'])
        if enfants:
            dossiers.append((d, enfants))
    return dossiers


# ── images ────────────────────────────────────────────────────────────────

def images_citees(pages):
    urls = set()
    for p in pages:
        for u in re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', p['content']['raw'], re.I):
            if u.startswith('http'):
                urls.add(u)
    return sorted(urls)


def rapatrier(urls, brut):
    """Télécharge ce qui manque encore. Rend les URL que le site ne sert pas."""
    os.makedirs(brut, exist_ok=True)
    absentes = []
    for i, u in enumerate(urls, 1):
        chemin = os.path.join(brut, cle(u))
        if not os.path.exists(chemin) or os.path.getsize(chemin) == 0:
            code = subprocess.run(
                ['curl', '-s', '--max-time', '60', '-w', '%{http_code}',
                 '-o', chemin, u], capture_output=True, text=True).stdout.strip()
            if code != '200':
                absentes.append(u)
                if os.path.exists(chemin):
                    os.remove(chemin)
        sys.stdout.write('\r   %d/%d' % (i, len(urls)))
        sys.stdout.flush()
    print()
    return absentes


def reencoder(urls, brut, img):
    """Réduit et réencode. Rend, par URL, le nom du fichier à servir."""
    from PIL import Image
    os.makedirs(img, exist_ok=True)
    noms = {}
    for u in urls:
        source = os.path.join(brut, cle(u))
        if not os.path.exists(source):
            continue
        try:
            im = Image.open(source)
            im.load()
        except Exception:
            continue                       # une page d'erreur, pas une image
        base = cle(u)
        if getattr(im, 'n_frames', 1) > 1:  # un GIF animé reste tel quel
            noms[u] = base + '.gif'
            with open(os.path.join(img, noms[u]), 'wb') as f:
                f.write(open(source, 'rb').read())
            continue
        if im.width > LARGE:
            im = im.resize((LARGE, round(im.height * LARGE / im.width)), Image.LANCZOS)
        # Une transparence réelle, pas seulement un canal alpha tout opaque :
        # sans ce test les photos en PNG restent en PNG et pèsent trois fois trop.
        transparent = im.mode in ('RGBA', 'LA', 'P') and (
            im.convert('RGBA').getchannel('A').getextrema()[0] < 255)
        if transparent:
            noms[u] = base + '.png'
            im.convert('RGBA').save(os.path.join(img, noms[u]), optimize=True)
        else:
            noms[u] = base + '.jpg'
            im.convert('RGB').save(os.path.join(img, noms[u]), quality=QUALITE,
                                   optimize=True, progressive=True)
    return noms


# ── pages ─────────────────────────────────────────────────────────────────

MANQUE = ('data:image/svg+xml;charset=utf-8,'
          "%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 600 400'%3E"
          "%3Crect width='600' height='400' fill='%23FBEBE6'/%3E"
          "%3Crect x='6' y='6' width='588' height='388' fill='none' "
          "stroke='%23B4402A' stroke-width='3' stroke-dasharray='12 8'/%3E"
          "%3Ctext x='300' y='190' text-anchor='middle' font-family='sans-serif' "
          "font-size='30' font-weight='700' fill='%23B4402A'%3EImage absente%3C/text%3E"
          "%3Ctext x='300' y='232' text-anchor='middle' font-family='sans-serif' "
          "font-size='21' fill='%23B4402A'%3Ele site r&#233;pond 404%3C/text%3E%3C/svg%3E")


def rendre(page, noms, absentes, retour):
    """Le contenu WordPress, servi comme une page autonome."""
    c = page['content']['raw']

    # `srcset` et `sizes` renvoient vers le site : le navigateur y piocherait
    # une adresse distante, que la publication n'autorise pas à charger.
    c = re.sub(r'\s(?:srcset|data-srcset|sizes)=(["\'])[^"\']*\1', '', c, flags=re.I)

    def _img(m):
        u = m.group(1)
        if u in noms:
            return m.group(0).replace(u, '../img/' + noms[u])
        if u in absentes:
            return m.group(0).replace(u, MANQUE)
        return m.group(0)

    c = re.sub(r'<img[^>]+src=["\']([^"\']+)["\']', lambda m: _img(m), c)
    c = re.sub(r'<!--\s*/?wp:html\s*-->', '', c)

    titre = page['title']['raw']
    barre = (
        '<div class="expo-barre">'
        '<a class="expo-retour" href="%s">&larr; Sommaire</a>'
        '<span class="expo-titre">%s</span>'
        '<span class="expo-id">#%d &middot; brouillon</span>'
        '</div>' % (retour, H.escape(som.nom_court(titre)), page['id'])
    )
    style = (
        '<style>'
        '.expo-barre{position:sticky;top:0;z-index:2147483647;display:flex;align-items:center;'
        'gap:16px;padding:10px 18px;background:#0E1519;color:#EAF1F4;'
        'font:600 14px/1.4 "Manrope",system-ui,sans-serif}'
        '.expo-retour{color:#7FD8E6;text-decoration:none;font-weight:800;white-space:nowrap}'
        '.expo-retour:hover{text-decoration:underline}'
        '.expo-titre{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}'
        '.expo-id{color:#8FA0A8;font-weight:700;white-space:nowrap}'
        '@media(max-width:600px){.expo-titre{display:none}}'
        '</style>'
    )
    return ('<!doctype html><html lang="fr"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>%s</title>%s</head><body class="elementor-template-canvas">%s\n%s\n'
            '</body></html>' % (H.escape(titre), style, barre, c))


# ── sommaire ──────────────────────────────────────────────────────────────

def sommaire(dossiers, absentes_par_page):
    total = sum(len(k) for _, k in dossiers)
    compte = {som.numero(som.titre_de(d)): len(k) for d, k in dossiers}
    j = datetime.date.today()
    o = []
    o.append('<header class="tete">')
    o.append('<p class="eyebrow">Authentique Égypte · refonte 2026</p>')
    o.append('<h1>Les pages à regarder</h1>')
    o.append('<p class="chapo">Les %d pages de la refonte, telles qu’elles sont '
             'enregistrées dans WordPress. Elles y sont en brouillon, donc invisibles '
             'sans compte : elles sont recopiées ici pour être ouvertes sans rien '
             'demander. <b>Voir la page</b> l’affiche, <b>Modifier</b> ouvre l’éditeur '
             'WordPress et demande, lui, d’être connecté.</p>' % total)
    o.append('<p class="chiffres">%s<b>0 <span>publiée</span></b></p>' % ''.join(
        '<b>%d <span>%s</span></b>' % (compte.get(n, 0), mot)
        for n, mot in ((1, 'circuits'), (2, 'séjours'), (3, 'références'))))
    if absentes_par_page:
        o.append('<p class="avis avis--rouge">%s</p>' % ' '.join(
            '<b>%s</b> cite %d image%s que le site ne sert pas (404) : '
            'elles apparaissent en cadre rouge. Le défaut est sur le site, '
            'pas dans la refonte.' % (H.escape(t), n, 's' if n > 1 else '')
            for t, n in absentes_par_page))
    o.append('</header>')

    for d, enfants in dossiers:
        n = som.numero(som.titre_de(d))
        o.append('<section class="dossier"><div class="dossier__tete">'
                 '<span class="num">%d</span><h2>%s</h2>'
                 '<span class="cpt">%d page%s</span></div>'
                 % (n, H.escape(som.nom_court(som.titre_de(d))), len(enfants),
                    's' if len(enfants) > 1 else ''))
        if n in som.LEGENDES:
            o.append('<p class="legende">%s</p>' % H.escape(som.LEGENDES[n]))
        o.append('<ol class="pages">')

        vus = {}
        for p in enfants:
            vus.setdefault(som.groupe_de(som.titre_de(p))[1], []).append(p['id'])
        doubles = {i for ids in vus.values() if len(ids) > 1 for i in ids}

        groupe = None
        for p in enfants:
            g, nom = som.groupe_de(som.titre_de(p))
            if g and g != groupe:
                o.append('<li class="groupe"><span>%s</span></li>' % H.escape(g))
                groupe = g
            if p['id'] in doubles:
                nom += ' · /%s' % re.sub(r'^refonte-(?:programme|famille)-', '', p['slug'])
            o.append(
                '<li class="page">'
                '<span class="page__nom">%s%s</span>'
                '<span class="page__meta"><code>#%d</code></span>'
                '<span class="page__act">'
                '<a class="b b--v" href="p/%d.html">Voir la page</a>'
                '<a class="b" href="%s/wp-admin/post.php?post=%d&amp;action=edit" '
                'target="_blank" rel="noopener">Modifier</a>'
                '</span></li>'
                % (H.escape(nom), '<em>doublon</em>' if p['id'] in doubles else '',
                   p['id'], p['id'], SITE, p['id']))
        o.append('</ol></section>')

    o.append('<footer class="pied">')
    o.append('<p><b>Ce qui reste à trancher avec Mélanie :</b> les durées annoncées qui '
             'ne collent pas au nombre de jours écrits, les trois fiches dont '
             'l’itinéraire n’existe pas dans le contenu d’origine, et le choix de la '
             'page à garder entre les deux Sainte-Catherine, marquées « doublon ».</p>')
    o.append('<p>Copie du CMS au %d %s %d. Les images sont réduites à %d px de large '
             'pour tenir dans la publication ; sur le site elles gardent leur taille '
             'd’origine.</p>' % (j.day, som.MOIS[j.month - 1], j.year, LARGE))
    o.append('</footer>')

    # Le sommaire du CMS et celui-ci partagent leur habillage mais pas leur
    # nom : l'un vit dans le back-office, l'autre se donne sans compte.
    tete = som.TETE.replace('<title>Refonte 2026 · Back-office</title>',
                            '<title>Refonte 2026 — les pages</title>')
    return (tete + '<style>' + som.STYLE + EXTRA + '</style>\n'
            '<body>\n<div class="wrap">\n' + '\n'.join(o) + '\n</div>\n</body>')


EXTRA = """
.avis--rouge{border-left-color:var(--rouge);background:var(--rouge-fond);color:var(--rouge)}
.avis--rouge b{color:var(--rouge)}
"""


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--sortie', required=True, help='dossier à produire')
    p.add_argument('--cache', help='dossier des images déjà téléchargées')
    a = p.parse_args()

    sortie = os.path.abspath(a.sortie)
    brut = os.path.abspath(a.cache) if a.cache else os.path.join(sortie, '.brut')
    os.makedirs(os.path.join(sortie, 'p'), exist_ok=True)

    print('→ Relevé du CMS')
    dossiers = relever()
    pages = [p for _, enfants in dossiers for p in enfants]
    print('   %d dossier(s), %d page(s)' % (len(dossiers), len(pages)))

    hors = [p['id'] for p in pages if p['status'] != 'draft']
    if hors:
        raise SystemExit('des pages ne sont pas en brouillon : %s' % hors)

    print('→ Images')
    urls = images_citees(pages)
    absentes = set(rapatrier(urls, brut))
    noms = reencoder(urls, brut, os.path.join(sortie, 'img'))
    print('   %d image(s) servie(s), %d absente(s) du site' % (len(noms), len(absentes)))

    print('→ Pages')
    par_page = []
    for page in pages:
        cassees = len({u for u in re.findall(
            r'<img[^>]+src=["\']([^"\']+)["\']', page['content']['raw'], re.I)
            if u in absentes})
        if cassees:
            par_page.append((som.groupe_de(som.titre_de(page))[1], cassees))
        html = rendre(page, noms, absentes, '../index.html')
        with open(os.path.join(sortie, 'p', '%d.html' % page['id']), 'w',
                  encoding='utf-8') as f:
            f.write(html)

    with open(os.path.join(sortie, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(sommaire(dossiers, par_page))

    total = sum(os.path.getsize(os.path.join(r, f))
                for r, _, fs in os.walk(sortie) for f in fs
                if not r.startswith(brut))
    nb = sum(len(fs) for r, _, fs in os.walk(sortie) if not r.startswith(brut))
    print('\n→ %s : %d fichier(s), %.1f Mo' % (sortie, nb, total / 1e6))


if __name__ == '__main__':
    main()
