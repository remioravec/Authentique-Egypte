#!/usr/bin/env python3
"""
Transforme une maquette autonome en contenu de page WordPress.

Le gabarit Elementor Canvas donne un <body> nu — ni en-tête ni pied de
thème — mais Astra, Elementor et Jeg Kit chargent quand même leur CSS.
Certaines de leurs règles portent une classe (`.elementor-kit-4658 h1`,
specificite 0-1-1) et écraseraient nos règles d'élément (`h1`, 0-0-1),
quel que soit l'ordre de chargement : une classe l'emporte toujours sur
un nombre quelconque d'éléments.

On préfixe donc les sélecteurs d'élément de la maquette par
`.elementor-template-canvas` — la classe que le gabarit pose sur <body>.
Nos règles passent à 0-1-1 ou mieux, à égalité ou au-dessus du thème, et
comme notre <style> est injecté dans le corps, il vient en dernier : il
gagne. Les sélecteurs qui portent déjà une classe ou un identifiant ne
sont pas touchés : le thème ne connaît pas nos noms de classe.

Usage :
    ./outils/vers-page-wp.py maquettes/index.html > contenu.html
"""

import re
import sys

CLASSE_HOTE = '.elementor-template-canvas'

# Règles at- qui ne contiennent pas de sélecteurs à préfixer.
AT_OPAQUES = ('@keyframes', '@font-face', '@page', '@counter-style', '@property')

# Sélecteurs qu'on laisse tels quels : ils ne visent pas le contenu.
INTOUCHABLES = (':root', 'html', 'from', 'to', '*')


def prefixer_selecteur(selecteur: str) -> str:
    """Préfixe un sélecteur simple s'il commence par un élément nu."""
    selecteur = selecteur.strip()
    if not selecteur:
        return selecteur

    # :root porte les variables : le préfixer les rendrait inaccessibles
    # aux éléments hors du corps. On le laisse.
    if selecteur.startswith(':root') or selecteur.startswith('html'):
        return selecteur

    # Étapes en pourcentage d'une animation.
    if re.fullmatch(r'\d+%', selecteur) or selecteur in ('from', 'to'):
        return selecteur

    # `body` est justement l'élément qui porte la classe hôte.
    if selecteur == 'body':
        return 'body' + CLASSE_HOTE
    if selecteur.startswith('body '):
        return 'body' + CLASSE_HOTE + selecteur[4:]
    if selecteur.startswith('body.') or selecteur.startswith('body['):
        return 'body' + CLASSE_HOTE + selecteur[4:]

    # On préfixe aussi les sélecteurs qui portent déjà une classe. Le thème
    # ne connaît pas nos noms de classe, mais il stylise les éléments avec
    # une classe à lui : `.elementor-kit-4658 button` vaut 0-1-1 et bat
    # `.opt` (0-1-0). Un préfixe de plus met toutes nos règles au-dessus.
    return CLASSE_HOTE + ' ' + selecteur


def prefixer_bloc_selecteurs(liste: str) -> str:
    return ', '.join(prefixer_selecteur(s) for s in liste.split(','))


def prefixer_css(css: str) -> str:
    """Parcourt la feuille et préfixe les sélecteurs des règles de style."""
    sortie = []
    i = 0
    n = len(css)

    while i < n:
        # Commentaire
        if css.startswith('/*', i):
            fin = css.find('*/', i + 2)
            fin = n if fin == -1 else fin + 2
            sortie.append(css[i:fin])
            i = fin
            continue

        # Blanc
        if css[i].isspace():
            sortie.append(css[i])
            i += 1
            continue

        # Fin du préambule : on lit jusqu'à { ou ; (règle at- sans corps)
        j = i
        profondeur_paren = 0
        while j < n:
            if css[j] == '(':
                profondeur_paren += 1
            elif css[j] == ')':
                profondeur_paren -= 1
            elif css[j] in '{;' and profondeur_paren == 0:
                break
            j += 1

        preambule = css[i:j]

        if j >= n:
            sortie.append(preambule)
            break

        if css[j] == ';':  # @import, @charset…
            sortie.append(preambule + ';')
            i = j + 1
            continue

        # Corps entre accolades, en comptant l'imbrication.
        k = j + 1
        profondeur = 1
        while k < n and profondeur:
            if css.startswith('/*', k):
                fin = css.find('*/', k + 2)
                k = n if fin == -1 else fin + 2
                continue
            if css[k] == '{':
                profondeur += 1
            elif css[k] == '}':
                profondeur -= 1
            k += 1

        corps = css[j + 1:k - 1]
        tete = preambule.strip()

        if tete.startswith('@'):
            nom = tete.split()[0].lower()
            if nom.startswith(AT_OPAQUES):
                sortie.append(preambule + '{' + corps + '}')
            else:
                # @media, @supports, @layer : on descend dans le corps.
                sortie.append(preambule + '{' + prefixer_css(corps) + '}')
        else:
            sortie.append(prefixer_bloc_selecteurs(tete) + '{' + corps + '}')

        i = k

    return ''.join(sortie)


def aplatir(texte: str) -> str:
    """Supprime les lignes vides.

    `wpautop` découpe le contenu sur les lignes vides et y insère
    `</p><p>` — y compris à l'intérieur d'un <style> ou d'un <script>,
    car sa protection de ces balises n'intervient qu'à l'étape suivante,
    celle des <br>. Une feuille de style qui contient une ligne vide voit
    donc toutes les règles suivantes sortir du bloc et cesser de
    s'appliquer. Sans ligne vide, wpautop n'a plus rien à découper, et
    les retours simples restent protégés.
    """
    return re.sub(r'\n[ \t]*\n+', '\n', texte)


def dépouiller_css(css: str) -> str:
    """Retire les commentaires : ils sont dans le dépôt, pas besoin en ligne."""
    return re.sub(r'/\*.*?\*/', '', css, flags=re.S)


def convertir(html: str) -> str:
    """Extrait de la maquette ce qui doit vivre dans le contenu de la page."""
    # La feuille de style de la maquette, préfixée.
    styles = re.findall(r'<style[^>]*>(.*?)</style>', html, re.S | re.I)
    css = '\n'.join(prefixer_css(dépouiller_css(bloc)) for bloc in styles)

    # Les polices Google, à recharger dans le corps (les navigateurs
    # acceptent un <link rel=stylesheet> hors du head).
    polices = re.findall(
        r'<link[^>]+fonts\.googleapis\.com[^>]*>', html, re.I
    )

    # Les données structurées de la maquette.
    ld = re.findall(
        r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>.*?</script>',
        html, re.S | re.I
    )

    # Le corps, scripts de comportement compris.
    corps = re.search(r'<body[^>]*>(.*)</body>', html, re.S | re.I)
    corps = corps.group(1) if corps else html

    # Les blocs ld+json vivent déjà dans le head : on ne les duplique pas.
    for bloc in ld:
        corps = corps.replace(bloc, '')

    morceaux = []
    morceaux.append(
        '<!-- Maquette de refonte servie en brouillon. '
        'Gabarit Elementor Canvas, sélecteurs préfixés par '
        'outils/vers-page-wp.py. Ne pas modifier ici : la source est '
        'dans le dépôt, sous maquettes/. -->'
    )
    morceaux.extend(polices)
    morceaux.extend(ld)
    morceaux.append('<style>\n' + css + '\n</style>')
    morceaux.append(corps.strip())

    # Enveloppé dans un bloc Gutenberg « HTML personnalisé ».
    #
    # Ce n'est pas cosmétique : dès que le contenu porte des délimiteurs de
    # bloc, `do_blocks()` retire `wpautop` du filtre `the_content`. Sans
    # cela wpautop insère `</p><p>` à chaque ligne vide — jusque dans les
    # <style> — et coupe les <a> qui contiennent des <div>, que le parseur
    # rouvre ensuite en double. Le bloc wp:html restitue son contenu tel
    # quel ; wptexturize, lui, épargne déjà <style> et <script>.
    return '<!-- wp:html -->\n' + aplatir('\n'.join(morceaux)) + '\n<!-- /wp:html -->'


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit('usage : vers-page-wp.py <maquette.html>')
    with open(sys.argv[1], encoding='utf-8') as f:
        sys.stdout.write(convertir(f.read()))
