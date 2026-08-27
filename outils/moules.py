#!/usr/bin/env python3
"""
Les maquettes servent de moule.

La première version de la génération fabriquait sa propre mise en page,
plus simple que les maquettes. C'était une erreur : les maquettes sont
le travail validé — panneau de réservation collant, itinéraire jour par
jour, inclusions, FAQ dépliante, séjours sœurs — et c'est sur elles que
Mélanie a laissé ses retours.

Ce module ne redessine rien. Il ouvre le fichier de maquette, remplace
les blocs de contenu par ceux de la page traitée, et laisse tout le
reste intact : structure, styles, entête, pied, blocs de réassurance.
"""

import html as _html
import os
import re

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAQUETTES = os.path.join(RACINE, 'maquettes')


def e(t):
    return _html.escape(t or '', quote=True)


def coupe(texte, n):
    mots = (texte or '').split()
    return ' '.join(mots[:n]) + ('…' if len(mots) > n else '')


def bornes(html, ancre, depuis=0):
    """Début et fin de l'élément dont la balise ouvrante contient `ancre`.

    On compte les balises de même nom pour retrouver la fermeture : une
    recherche naïve du premier `</div>` s'arrêterait au premier enfant.
    """
    i = html.find(ancre, depuis)
    if i < 0:
        return None
    # Une ancre qui commence par « < » EST déjà le début de la balise :
    # reculer jusqu'au « < » précédent viserait l'élément parent.
    debut = i if ancre.startswith('<') else html.rfind('<', 0, i)
    balise = re.match(r'<([a-z0-9]+)', html[debut:]).group(1)
    if html[debut:].startswith('<%s' % balise) and re.match(r'<%s[^>]*/>' % balise, html[debut:]):
        return debut, debut + html[debut:].index('/>') + 2

    profondeur = 0
    for t in re.finditer(r'<(/?)%s\b[^>]*?(/?)>' % balise, html[debut:]):
        if t.group(2) == '/':
            continue
        profondeur += -1 if t.group(1) else 1
        if profondeur == 0:
            return debut, debut + t.end()

    return None


def remplacer(html, ancre, neuf, depuis=0):
    """Remplace l'élément repéré par `ancre`. Lève si l'ancre a disparu."""
    b = bornes(html, ancre, depuis)
    if not b:
        raise SystemExit('Ancre introuvable dans le moule : %s' % ancre)

    return html[:b[0]] + neuf + html[b[1]:]


def vider(html, ancre, depuis=0):
    """Retire complètement un bloc du moule."""
    return remplacer(html, ancre, '', depuis)


def moule(fichier):
    with open(os.path.join(MAQUETTES, fichier), encoding='utf-8') as f:
        return f.read()


def entete_html(page, titre, description):
    """Titre, description et robots — le reste de <head> vient du moule."""
    page = re.sub(r'<title>.*?</title>',
                  '<title>%s — Authentique Égypte</title>' % e(titre), page, count=1, flags=re.S)
    page = re.sub(r'<meta name="description" content="[^"]*">',
                  '<meta name="description" content="%s">' % e(description), page, count=1)
    if 'name="robots"' not in page:
        page = page.replace('</title>', '</title>\n<meta name="robots" content="noindex, nofollow">', 1)

    return page


def bandeau_source(url):
    return ('<p class="src">Contenu repris de <a href="%s">%s</a>, sans réécriture&nbsp;: '
            'seule la mise en page change.</p>' % (e(url), e(url)))


def style_source():
    """Le seul style ajouté au moule : le bandeau qui dit d'où vient le texte."""
    return ('\n.src{margin:0 0 24px;padding:11px 15px;background:var(--or-fond);'
            'border-radius:var(--r-s);font-size:.86rem;color:#7A5605;line-height:1.5}'
            '\n.src a{color:inherit}\n')


def poser_style(page):
    return page.replace('</style>', style_source() + '</style>', 1)


_TAILLES = {}
_MINIATURE = re.compile(r'(https://authentiquegypte\.com/wp-content/uploads/[^\s"\']*?)'
                        r'-\d{2,4}x\d{2,4}(\.(?:jpe?g|png|webp|gif))', re.I)


def _repond(url):
    if url not in _TAILLES:
        import urllib.request
        try:
            r = urllib.request.Request(url, method='HEAD')
            with urllib.request.urlopen(r, timeout=20) as rep:
                _TAILLES[url] = rep.status == 200
        except Exception:
            _TAILLES[url] = False
    return _TAILLES[url]


def defloute(page):
    """Remplace les vignettes « …-300x200.jpg » par l'image d'origine.

    WordPress référence souvent une taille intermédiaire : affichée en
    grand dans la maquette, elle rend flou. On ne touche qu'aux images
    du site, et seulement quand le plein format répond vraiment — les
    originaux volumineux s'appellent parfois « …-scaled.jpg ».
    """
    def rem(m):
        for cand in (m.group(1) + m.group(2), m.group(1) + '-scaled' + m.group(2)):
            if _repond(cand):
                return cand
        return m.group(0)
    return _MINIATURE.sub(rem, page)


def paragraphes(blocs, classe='lede'):
    """Les blocs de contenu, dans le balisage de la maquette."""
    out = []
    for b in blocs:
        if b['type'] == 'p':
            out.append('<p class="%s">%s</p>' % (classe, e(b['texte'])))
        elif b['type'] == 'titre_etape':
            out.append('<h4>%s</h4>' % e(b['texte']))
        elif b['type'] == 'liste':
            out.append('<ul>%s</ul>' % ''.join('<li>%s</li>' % e(i) for i in b['items']))
        elif b['type'] == 'tableau':
            out.append(tableau(b))
        elif b['type'] == 'blockquote':
            out.append('<blockquote><p>%s</p></blockquote>' % e(b['texte']))
        elif b['type'] == 'figcaption':
            out.append('<p class="note">%s</p>' % e(b['texte']))

    return '\n'.join(out)


def tableau(b):
    tete = ''
    if b.get('entetes'):
        tete = '<thead><tr>%s</tr></thead>' % ''.join(
            '<th scope="col">%s</th>' % e(c) for c in b['entetes'])
    corps = ''.join(
        '<tr>%s</tr>' % ''.join(
            ('<th scope="row">%s</th>' if i == 0 else '<td>%s</td>') % e(c)
            for i, c in enumerate(l))
        for l in b.get('lignes', []))

    return '<div class="tab-cadre"><table class="choix">%s<tbody>%s</tbody></table></div>' % (tete, corps)
