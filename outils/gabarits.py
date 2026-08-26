#!/usr/bin/env python3
"""
Verse le contenu extrait dans le gabarit qui lui correspond.

Un principe : **on ne réécrit pas le contenu du client**. Les phrases
sont celles du site, dans leur ordre. Ce module choisit une mise en
page, place les images, et ajoute les repères de la charte — chapô,
sommaire, encadrés, appel au devis. Rien de plus.

Ce qui manque reste marqué `.aremplir` plutôt que comblé au jugé : une
maquette qui invente un prix est pire qu'une maquette incomplète.

    ./outils/gabarits.py            écrit maquettes/site/*.html
    ./outils/gabarits.py <slug>     n'écrit que celle-là
"""

import html
import json
import os
import re
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAQUETTES = os.path.join(RACINE, 'maquettes')
SORTIE = os.path.join(MAQUETTES, 'site')
BLOCS = os.path.join(MAQUETTES, 'assets', 'blocs')

DEVIS = 'https://authentiquegypte.com/sur-mesure/'


def e(t):
    return html.escape(t or '', quote=True)


def bloc(nom):
    with open(os.path.join(BLOCS, nom), encoding='utf-8') as f:
        return f.read().rstrip('\n')


def coupe(texte, n):
    mots = (texte or '').split()
    return ' '.join(mots[:n]) + ('…' if len(mots) > n else '')


# ---------------------------------------------------------------- #
# L'enveloppe commune                                               #
# ---------------------------------------------------------------- #

def enveloppe(x, corps, description=''):
    return """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%(titre)s — Authentique Égypte</title>
<meta name="description" content="%(description)s">
<meta name="robots" content="noindex, nofollow">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Archivo:wght@600;700;800&family=Manrope:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="../assets/charte.css">
<style>
/* Repères propres aux pages reprises du site. */
.chapeau + .section{padding-top:38px}
.src{margin:0 0 26px;padding:11px 15px;background:var(--or-fond);border-radius:var(--r-s);
  font-size:.86rem;color:#7A5605;line-height:1.5}
.src a{color:inherit}
.corps{max-width:74ch}
.corps h2{font-size:clamp(1.4rem,2.4vw,1.85rem);margin:44px 0 14px}
.corps h3{font-size:1.16rem;margin:30px 0 10px}
.corps p{margin:0 0 16px;line-height:1.75}
.corps ul{margin:0 0 18px;padding-left:1.1rem}
.corps li{margin:0 0 8px;line-height:1.65}
.corps figure{margin:26px 0}
.corps figure img{width:100%%;border-radius:var(--r-m);display:block}
.corps figcaption{margin-top:9px;font-size:.86rem;color:var(--gris)}
.sommaire{background:var(--fond-2);border:1px solid var(--ligne);border-radius:var(--r-m);
  padding:20px 24px;margin:0 0 34px}
.sommaire b{display:block;font-size:.78rem;text-transform:uppercase;letter-spacing:.08em;
  color:var(--gris);margin-bottom:10px}
.sommaire ol{margin:0;padding-left:1.1rem}
.sommaire li{margin:0 0 6px}
.deux{display:grid;grid-template-columns:1fr 340px;gap:44px;align-items:start}
.flanc{position:sticky;top:88px;display:grid;gap:18px}
.encart{background:#fff;border:1px solid var(--ligne);border-radius:var(--r-m);padding:22px 24px;
  box-shadow:var(--ombre)}
.encart h3{margin:0 0 12px;font-size:1.02rem}
.encart ul{margin:0;padding-left:1.05rem;font-size:.94rem;color:var(--texte)}
.encart li{margin:0 0 7px}
.galerie{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:14px;margin:26px 0}
.galerie img{width:100%%;aspect-ratio:4/3;object-fit:cover;border-radius:var(--r-m);display:block}
.chiffres{display:flex;flex-wrap:wrap;gap:10px;margin:0 0 26px}
.chiffres span{background:var(--teal-fond);color:var(--teal-txt);border-radius:var(--r-pill);
  padding:7px 15px;font-size:.9rem;font-weight:600}
@media (max-width:900px){
  .deux{grid-template-columns:1fr;gap:30px}
  .flanc{position:static}
  .corps p,.corps li{font-size:1rem}
}
header .nav>a.btn--or,header .nav>a.btn--or[aria-current]{background:#E08A00;border-color:#E08A00;color:#fff}
header .nav>a.btn--or:hover{background:#C87700;border-color:#C87700}
</style>
</head>
<body>

%(entete)s

<main>
%(corps)s
</main>

%(pied)s
</body>
</html>
""" % {
        'titre': e(x['titre']),
        'description': e(description or coupe(x['chapo'], 26)),
        'entete': bloc('entete.html'),
        'pied': bloc('pied.html'),
        'corps': corps,
    }


def bandeau_source(x):
    return ('<p class="src">Contenu repris de <a href="%s">%s</a>, sans réécriture. '
            'Seule la mise en page change.</p>' % (e(x['url']), e(x['url'])))


def chapeau(x, surtitre, chiffres=()):
    img = x['images'][0]['src'] if x['images'] else ''
    fond = ('<div class="chapeau__bg"><img src="%s" alt=""></div>' % e(img)) if img else ''
    puces = ''
    if chiffres:
        puces = '<div class="chiffres">%s</div>' % ''.join(
            '<span>%s</span>' % e(c) for c in chiffres if c)
    return """<section class="chapeau">
  %s
  <div class="wrap">
    <nav class="ariane" aria-label="Fil d'Ariane"><ol>
      <li><a href="../index.html">Accueil</a></li>
      <li><span aria-current="page">%s</span></li>
    </ol></nav>
    <p class="eyebrow eyebrow--clair">%s</p>
    <h1>%s</h1>
    <p class="sous">%s</p>
    %s
  </div>
</section>""" % (fond, e(coupe(x['titre'], 6)), e(surtitre), e(x['titre']), e(x['chapo']), puces)


def utiles(sections):
    """Écarte les titres sans contenu — un intertitre seul au milieu de
    la page fait croire à un bloc perdu."""
    return [s for s in sections if s['blocs']]


def rendre_sections(sections, images, depuis=0):
    """Le contenu, dans son ordre, avec les images réparties entre les
    sections plutôt qu'entassées en fin de page."""
    sections = utiles(sections)
    sortie = []
    restantes = list(images)
    for n, s in enumerate(sections):
        if s['titre']:
            sortie.append('<h%d id="s%d">%s</h%d>' % (s['niveau'], n, e(s['titre']), s['niveau']))
        for b in s['blocs']:
            if b['type'] == 'p':
                sortie.append('<p>%s</p>' % e(b['texte']))
            elif b['type'] == 'liste':
                sortie.append('<ul>%s</ul>' % ''.join('<li>%s</li>' % e(t) for t in b['items']))
            elif b['type'] == 'blockquote':
                sortie.append('<blockquote><p>%s</p></blockquote>' % e(b['texte']))
            elif b['type'] == 'figcaption':
                sortie.append('<p class="note">%s</p>' % e(b['texte']))
        # une image toutes les deux sections, tant qu'il en reste
        if restantes and n % 2 == 1:
            im = restantes.pop(0)
            sortie.append('<figure><img src="%s" alt="%s" loading="lazy" decoding="async">%s</figure>'
                          % (e(im['src']), e(im['alt']),
                             ('<figcaption>%s</figcaption>' % e(im['alt'])) if im['alt'] else ''))
    if restantes:
        sortie.append('<div class="galerie">%s</div>' % ''.join(
            '<img src="%s" alt="%s" loading="lazy" decoding="async">' % (e(i['src']), e(i['alt']))
            for i in restantes))
    return '\n'.join(sortie)


def sommaire(sections):
    sections = utiles(sections)
    titres = [(n, s['titre']) for n, s in enumerate(sections) if s['titre']]
    if len(titres) < 3:
        return ''
    return ('<nav class="sommaire" aria-label="Sommaire"><b>Sur cette page</b><ol>%s</ol></nav>'
            % ''.join('<li><a href="#s%d">%s</a></li>' % (n, e(t)) for n, t in titres))


def appel_devis(titre, phrase):
    return """<section class="section section--nuit">
  <div class="wrap" style="text-align:center">
    <h2 style="color:#fff;margin-bottom:14px">%s</h2>
    <p class="lede" style="color:#C3D5DA;max-width:58ch;margin:0 auto 26px">%s</p>
    <a href="%s" class="btn btn--or">Demander mon devis</a>
  </div>
</section>""" % (e(titre), e(phrase), DEVIS)


# ---------------------------------------------------------------- #
# Un rendu par gabarit                                              #
# ---------------------------------------------------------------- #

def rendre_voyage(x):
    """Fiche séjour : ce qu'on paie, combien de temps, ce qui est inclus."""
    chiffres = [c for c in (x['duree'], ('À partir de ' + x['prix']) if x['prix'] else '') if c]
    inclus = ('<div class="encart"><h3>Le programme inclut</h3><ul>%s</ul></div>'
              % ''.join('<li>%s</li>' % e(i) for i in x['inclus'])) if x['inclus'] else ''
    exclus = ('<div class="encart"><h3>Non inclus</h3><ul>%s</ul></div>'
              % ''.join('<li>%s</li>' % e(i) for i in x['exclus'])) if x['exclus'] else ''
    prix = ('<div class="encart"><h3>Le prix</h3><p class="prix" style="font-size:1.5rem">'
            '<small>À partir de</small><b>%s</b> <i>/ pers.</i></p>'
            '<p style="font-size:.9rem;color:var(--gris);margin:10px 0 16px">%s</p>'
            '<a href="%s" class="btn btn--or btn--bloc btn--sm">Demander mon devis</a></div>'
            % (e(x['prix']), e(x['duree'] or 'Durée à confirmer'), DEVIS)) if x['prix'] else ''

    # Les sections d'inclusion sont déjà dans le flanc : on ne les répète pas.
    corps_sections = [s for s in x['sections']
                      if not re.match(r"(le programme inclu|n'inclus pas|non inclus)", s['titre'], re.I)]

    return enveloppe(x, """
%s
<section class="section">
  <div class="wrap">
    %s
    <div class="deux">
      <div class="corps">
        %s
        %s
      </div>
      <aside class="flanc">%s%s%s</aside>
    </div>
  </div>
</section>
%s
""" % (chapeau(x, 'Séjour', chiffres), bandeau_source(x), sommaire(corps_sections),
       rendre_sections(corps_sections, x['images'][1:]), prix, inclus, exclus,
       appel_devis('Ce séjour vous intéresse ?',
                   'Dites-nous vos dates et le nombre de voyageurs : nous vous répondons '
                   'avec un itinéraire chiffré, jour par jour.')))


def rendre_guide(x):
    """Article de guide : du texte, un sommaire, et une sortie vers le devis."""
    return enveloppe(x, """
%s
<section class="section">
  <div class="wrap">
    %s
    <div class="deux">
      <div class="corps">
        %s
        %s
      </div>
      <aside class="flanc">
        <div class="encart">
          <h3>Un projet de voyage&nbsp;?</h3>
          <p style="font-size:.94rem;color:var(--texte);margin:0 0 16px">Nous construisons
            l'itinéraire avec vous, selon vos dates et votre rythme.</p>
          <a href="%s" class="btn btn--or btn--bloc btn--sm">Demander mon devis</a>
        </div>
        <div class="encart">
          <h3>À lire aussi</h3>
          <ul><li><a href="../blog.html" class="lien-txt">Tous nos guides pratiques</a></li></ul>
        </div>
      </aside>
    </div>
  </div>
</section>
%s
""" % (chapeau(x, 'Guide pratique'), bandeau_source(x), sommaire(x['sections']),
       rendre_sections(x['sections'], x['images'][1:]), DEVIS,
       appel_devis('Prêt à partir ?',
                   'Un conseiller vous répond sous 48 h, hors vendredi et samedi.')))


def rendre_page(x, surtitre, titre_appel, phrase_appel):
    """Destination, catégorie, « qui part », agence : même ossature."""
    return enveloppe(x, """
%s
<section class="section">
  <div class="wrap">
    %s
    <div class="corps">
      %s
      %s
    </div>
  </div>
</section>
%s
""" % (chapeau(x, surtitre, [x['duree']] if x['duree'] else []), bandeau_source(x),
       sommaire(x['sections']), rendre_sections(x['sections'], x['images'][1:]),
       appel_devis(titre_appel, phrase_appel)))


RENDUS = {
    'voyage':      rendre_voyage,
    'guide':       rendre_guide,
    'destination': lambda x: rendre_page(x, 'Destination', 'Envie de découvrir cette région ?',
                                         'Nous l’intégrons à votre itinéraire, au bon moment de l’année.'),
    'categorie':   lambda x: rendre_page(x, 'Nos séjours', 'Un séjour à construire ?',
                                         'Dites-nous ce que vous avez en tête : nous vous répondons avec un programme chiffré.'),
    'qui-part':    lambda x: rendre_page(x, 'Qui part', 'Parlons de votre voyage',
                                         'Chaque itinéraire se construit avec vous, selon votre rythme et vos contraintes.'),
    'hub-guides':  lambda x: rendre_page(x, 'Guides pratiques', 'Une question sans réponse ?',
                                         'Écrivez-nous : une personne de l’équipe vous répond.'),
    'agence':      lambda x: rendre_page(x, 'L’agence', 'Parlons de votre voyage',
                                         'Un conseiller en France, une équipe au Caire.'),
    'accueil':     lambda x: rendre_page(x, 'Accueil', 'Par où commencer ?',
                                         'Dites-nous vos envies et vos dates : nous construisons l’itinéraire.'),
    'legal':       lambda x: rendre_page(x, 'Informations légales', 'Une question ?',
                                         'Écrivez-nous, nous répondons.'),
}


def main():
    with open(os.path.join(RACINE, 'docs', 'extraits.json'), encoding='utf-8') as f:
        extraits = {x['id']: x for x in json.load(f)}
    with open(os.path.join(RACINE, 'docs', 'inventaire.json'), encoding='utf-8') as f:
        inventaire = json.load(f)

    vise = sys.argv[1] if len(sys.argv) > 1 else None
    os.makedirs(SORTIE, exist_ok=True)

    faits, ignores = 0, []
    for item in inventaire:
        if vise and item['slug'] != vise:
            continue
        rendu = RENDUS.get(item['gabarit'])
        if not rendu:
            ignores.append((item['slug'], item['gabarit']))
            continue
        x = extraits.get(item['id'])
        if not x or not x['sections']:
            ignores.append((item['slug'], 'contenu vide'))
            continue
        chemin = os.path.join(SORTIE, '%s-%s.html' % (item['gabarit'], item['slug'][:60]))
        with open(chemin, 'w', encoding='utf-8') as f:
            f.write(rendu(x))
        faits += 1
        if vise:
            print('écrit :', os.path.relpath(chemin, RACINE))

    if not vise:
        print('%d pages générées dans maquettes/site/.' % faits)
        for slug, raison in ignores:
            print('  ignoré : %-46s %s' % (slug[:46], raison))


if __name__ == '__main__':
    main()
