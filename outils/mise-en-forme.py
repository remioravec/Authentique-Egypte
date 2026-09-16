#!/usr/bin/env python3
"""
Rend lisible le contenu repris du site : titres, listes, tableaux, rythme.

    ./outils/mise-en-forme.py FICHIER... [--essai]

Les pages du site en ligne arrivent aplaties. Tout y est un paragraphe : les
questions comme les réponses, les énumérations comme les explications. Sur
les guides et les destinations, cela donne quatre cents paragraphes
identiques à la suite — un mur de texte gris où l'œil ne trouve aucune prise.

Rien n'est réécrit ici, et rien n'est ajouté. Chaque transformation déplace
du texte déjà présent d'une balise vers une autre, mot pour mot :

  · un paragraphe qui se termine par « ? » et qu'un autre suit est une
    question — il devient un intertitre ;
  · trois paragraphes de suite bâtis sur « Étiquette : texte » sont une
    énumération — ils deviennent une liste à puces ;
  · le reste ne bouge pas.

La feuille de style, elle, ne touche à aucun texte : elle donne au corps
repris la mesure, le rythme et les puces du gabarit.
"""

import argparse
import html as H
import os
import re
import sys

MARQUE = 'mef-1'

# ── la feuille ───────────────────────────────────────────────────────────

# Une seule règle par rôle, et toutes accrochées à « .mef » : la feuille du
# gabarit reste maîtresse partout ailleurs. Les couleurs viennent des
# variables de la charte — aucune valeur en dur, sinon un changement de
# charte laisserait ces blocs derrière lui.
STYLE = """<style data-mef="{marque}">
/* Mise en forme du contenu repris — voir outils/mise-en-forme.py */
.mef{--mef-mes:68ch}
.mef p,.mef ul,.mef ol,.mef dl,.mef figure{max-width:var(--mef-mes)}
/* Le tableau est une donnée, pas une lecture suivie : la mesure de confort
   du texte l'étranglerait en colonnes de trois mots. */
.mef .mef-tab{max-width:none}
.mef table{max-width:none}
.mef p{margin:0 0 1.1em;line-height:1.75;color:var(--texte)}
.mef p:last-child{margin-bottom:0}
.mef>h2,.mef .mef-h2{font-size:clamp(1.35rem,2.4vw,1.75rem);line-height:1.25;
  margin:2.4em 0 .7em;color:var(--nuit);text-wrap:balance}
.mef>h2:first-child{margin-top:0}
.mef h3,.mef .mef-q{font-size:clamp(1.05rem,1.6vw,1.22rem);line-height:1.35;
  margin:2em 0 .5em;color:var(--nuit);text-wrap:balance}
.mef h4{font-size:1rem;margin:1.6em 0 .4em;color:var(--nuit)}
/* Une question posée dans le corps : reconnaissable sans crier. */
.mef .mef-q{position:relative;padding-left:18px;font-family:"Manrope",sans-serif;font-weight:700}
.mef .mef-q::before{content:"";position:absolute;left:0;top:.34em;bottom:.34em;width:4px;
  border-radius:2px;background:var(--teal)}
.mef .mef-q+p{margin-top:0}
/* La reprise du site laisse certaines questions en minuscule. La capitale
   est posée à l'affichage : le texte, lui, n'est pas retouché. */
.mef .mef-q::first-letter{text-transform:uppercase}
/* Listes : la puce prend la couleur de marque, le texte garde son rythme. */
.mef ul,.mef ol{margin:0 0 1.3em;padding-left:0;list-style:none}
.mef ul>li,.mef ol>li{position:relative;padding-left:26px;margin:0 0 .55em;
  line-height:1.7;color:var(--texte)}
.mef ul>li::before{content:"";position:absolute;left:6px;top:.62em;width:7px;height:7px;
  border-radius:50%;background:var(--teal)}
.mef ol{counter-reset:mef}
.mef ol>li{counter-increment:mef}
.mef ol>li::before{content:counter(mef);position:absolute;left:0;top:.05em;width:20px;
  text-align:center;font-family:"Manrope",sans-serif;font-size:.78rem;font-weight:700;
  line-height:20px;border-radius:50%;background:var(--teal-fond);color:var(--teal-txt)}
.mef li>b:first-child,.mef li>strong:first-child{color:var(--nuit)}
/* Une énumération « Étiquette : texte » se lit mieux en deux temps. */
.mef .mef-def>li{padding-left:0}
.mef .mef-def>li::before{display:none}
.mef .mef-def>li{border-left:3px solid var(--ligne-2);padding:2px 0 2px 16px}
.mef .mef-def>li b:first-child{display:block;color:var(--nuit);
  font-family:"Manrope",sans-serif;font-size:.92rem}
.mef dl{display:grid;gap:.2em .9em;grid-template-columns:auto 1fr}
.mef dt{font-weight:700;color:var(--nuit)}
.mef dd{margin:0;color:var(--texte)}
/* Tableaux : jamais de débordement horizontal de la page. */
.mef .mef-tab{overflow-x:auto;overflow-y:hidden;margin:0 0 1.4em;
  border:1px solid var(--ligne-2);border-radius:var(--r-m);
  /* Une ombre portée n'apparaît qu'au bord vers lequel il reste à défiler :
     le lecteur voit qu'il y a une colonne de plus, sans indication écrite. */
  background:linear-gradient(90deg,var(--papier) 30%,transparent),
             linear-gradient(90deg,transparent,var(--papier) 70%) 100% 0,
             radial-gradient(farthest-side at 0 50%,rgba(0,0,0,.13),transparent),
             radial-gradient(farthest-side at 100% 50%,rgba(0,0,0,.13),transparent) 100% 0;
  background-repeat:no-repeat;background-size:40px 100%,40px 100%,14px 100%,14px 100%;
  background-attachment:local,local,scroll,scroll}
.mef table{border-collapse:collapse;width:100%;font-size:.94rem}
.mef th,.mef td{padding:11px 16px;text-align:left;border-bottom:1px solid var(--ligne-2);
  vertical-align:top;line-height:1.5}
.mef tbody tr:nth-child(even){background:color-mix(in srgb,var(--fond) 55%,transparent)}
.mef th{font-family:"Manrope",sans-serif;font-size:.76rem;letter-spacing:.05em;line-height:1.3;
  text-transform:uppercase;color:var(--nuit);background:var(--fond)}
/* L'entête ne force pas la largeur : mise sur une seule ligne, elle poussait
   à elle seule le tableau au-delà de la colonne de lecture, et la dernière
   colonne sortait de l'écran. */
.mef thead th:first-child,.mef tbody th{white-space:normal}
.mef tbody tr:last-child td{border-bottom:0}
.mef td+td{font-variant-numeric:tabular-nums}
.mef blockquote{margin:0 0 1.4em;padding:2px 0 2px 20px;border-left:3px solid var(--or);
  color:var(--nuit);font-size:1.05rem}
.mef img{max-width:100%;height:auto;border-radius:var(--r-m)}
/* Les deux colonnes de la page reprise n'avaient aucune règle : la colonne
   latérale tombait sous le texte, pleine largeur. */
.colonnes{display:grid;grid-template-columns:minmax(0,1fr) 320px;gap:48px;
  align-items:start}
.colonnes>aside{position:sticky;top:96px}
@media (max-width:960px){
  .colonnes{grid-template-columns:minmax(0,1fr);gap:36px}
  .colonnes>aside{position:static}
}
</style>""".replace('{marque}', MARQUE)


# ── repérage ─────────────────────────────────────────────────────────────

def _texte(x):
    return re.sub(r'\s+', ' ', H.unescape(re.sub(r'<[^>]+>', ' ', x))).strip()


# Un paragraphe « nu » : celui que la reprise a produit, sans rôle déclaré.
# Les paragraphes de la charte — lede, src, eyebrow, carte__route — portent
# tous une classe : ils ne sont jamais touchés.
NU = re.compile(r'<p class="">(.*?)</p>', re.S)
ETIQUETTE = re.compile(r'^([^.!?:]{3,60})\s*:\s+(\S.*)$', re.S)


COLLAGE = re.compile(r'^(.{10,130}\?)([a-zà-öø-ÿ].*)$', re.S)


def _scinder(h):
    """Une question et sa réponse collées dans le même paragraphe.

    « quand éviter la foule ?janvier, février et novembre sont les mois les
    plus calmes » : la reprise du site a perdu la séparation, et la question
    se lit comme le début d'une phrase. Le point d'interrogation suivi sans
    espace d'une minuscule ne laisse guère de doute — c'est le seul cas où
    l'on coupe, et rien n'est réécrit : les deux morceaux sont le texte
    d'origine, à la lettre près.
    """
    n = [0]

    def un(m):
        inter = m.group(1)
        if re.search(r'<\w', inter):
            return m.group(0)
        c = COLLAGE.match(_texte(inter))
        if not c:
            return m.group(0)
        n[0] += 1
        return '<p class="">%s</p>\n<p class="">%s</p>' % (H.escape(c.group(1).strip()),
                                                           H.escape(c.group(2).strip()))

    return NU.sub(un, h), n[0]


def _questions(h):
    """Un paragraphe qui pose une question, et que d'autres suivent.

    Sur les guides, la page en ligne écrit ses questions comme des
    paragraphes : « Pourquoi visiter Louxor ? » a exactement la même taille,
    la même graisse et la même couleur que la réponse en dessous. Rien ne
    dit au lecteur où commence chaque sujet. Le texte ne change pas — sa
    balise, si.
    """
    n = [0]

    def un(m):
        t = _texte(m.group(1))
        # Un « ? » seul ne suffit pas : une phrase longue qui se termine par
        # une question est une phrase, pas un intertitre.
        if not (t.endswith('?') and 8 <= len(t) <= 130 and t.count('?') == 1):
            return m.group(0)
        n[0] += 1
        return '<h3 class="mef-q">%s</h3>' % m.group(1).strip()

    return NU.sub(un, h), n[0]


def _listes(h):
    """Trois « Étiquette : texte » de suite forment une énumération.

    « Jour 1 : rive est », « Jour 2 : rive ouest »… : la page en ligne les
    aligne en paragraphes. Trois suffisent pour que le motif soit voulu et
    non fortuit — en dessous, on ne touche à rien. Et deux paragraphes ne
    se suivent que si rien d'autre ne les sépare : un intertitre entre les
    deux coupe l'énumération, sinon on ramasserait deux séries en une.
    """
    nus = list(NU.finditer(h))
    series, courante = [], []
    for k, m in enumerate(nus):
        t = _texte(m.group(1))
        bon = bool(ETIQUETTE.match(t)) and len(t) <= 260
        colle = (bool(courante)
                 and not _texte(h[courante[-1].end():m.start()])
                 and '<' not in h[courante[-1].end():m.start()])
        if bon and (not courante or colle):
            courante.append(m)
            continue
        if len(courante) >= 3:
            series.append(courante)
        courante = [m] if bon else []
    if len(courante) >= 3:
        series.append(courante)

    sortie, pos, n = [], 0, 0
    for serie in series:
        sortie.append(h[pos:serie[0].start()])
        items = []
        for x in serie:
            inter = x.group(1).strip()
            e = ETIQUETTE.match(_texte(inter))
            if re.search(r'<\w', inter):
                # Le paragraphe porte du balisage — un lien, une mise en
                # gras : il passe tel quel plutôt que d'être découpé, pour
                # qu'aucun mot ni aucun lien ne se perde en chemin.
                items.append('<li>%s</li>' % inter)
            else:
                items.append('<li><b>%s</b> %s</li>'
                             % (H.escape(e.group(1).strip()),
                                H.escape(e.group(2).strip())))
        sortie.append('<ul class="mef-def">%s</ul>' % ''.join(items))
        n += 1
        pos = serie[-1].end()
    sortie.append(h[pos:])
    return ''.join(sortie), n


def _tableaux(h):
    """Chaque tableau dans son propre défilement.

    Un tableau plus large que l'écran pousse la page entière de côté sur
    mobile : le lecteur fait défiler le site pour lire une colonne.
    """
    n = [0]

    def un(m):
        n[0] += 1
        return '<div class="mef-tab">%s</div>' % m.group(0)

    return re.sub(r'(?<!<div class="mef-tab">)<table\b.*?</table>', un, h, flags=re.S), n[0]


def _reveal(h):
    """Le filet de sécurité de l'animation d'entrée tombe à 900 ms.

    Les blocs entrent en fondu quand ils croisent le bord de l'écran ; un
    minuteur les rend tous visibles, quoi qu'il arrive. Il était à 2,5 s :
    un lecteur qui fait défiler vite, un appareil lent, une capture d'écran
    ou une impression voyaient du texte à dix pour cent d'opacité. Le fondu
    reste, son garde-fou arrive simplement plus tôt.
    """
    return re.subn(r"(setTimeout\(\(\)=>\{cibles\.forEach\(el=>el\.classList\.add\('vu'\)\)\},)2500",
                   r'\g<1>900', h)


def _marquer(h):
    """Pose la classe « mef » là où — et seulement là où — il y a du texte repris.

    Marquer large serait pire que ne rien marquer : la mesure de 68 caractères
    et le rythme de lecture conviennent à un article, pas à une grille de
    cartes. On ne marque donc qu'un conteneur qui porte des paragraphes nus,
    c'est-à-dire du contenu venu du site et non dessiné par le gabarit.
    """
    # Le préfixe « rp- » est celui que la greffe pose sur le contenu repris
    # pour qu'il n'emprunte aucun nom de classe au gabarit : les conteneurs
    # à marquer s'appellent donc « wrap » ou « rp-wrap » selon la page.
    h = re.sub(r'<article class="(rp-)?corps">',
               lambda m: '<article class="%scorps mef">' % (m.group(1) or ''), h)

    def bloc(m):
        if '<p class=""' not in m.group(0) and 'class="mef-q"' not in m.group(0):
            return m.group(0)
        # Si la section porte déjà sa colonne de lecture, c'est ELLE qu'on
        # marque, pas la section entière : la colonne latérale contient une
        # carte sur fond sombre, et les couleurs de la feuille — un gris de
        # texte, un bleu de titre, pensés pour du papier blanc — y tombaient
        # sur du bleu nuit. Mesuré : le titre du bloc devis à 1,90:1 et son
        # paragraphe à 1,32:1, pour un seuil de 4,5:1. Illisible.
        if re.search(r'<article class="(rp-)?corps', m.group(0)):
            return m.group(0)
        return re.sub(r'<div class="(rp-)?wrap">',
                      lambda w: '<div class="%swrap mef">' % (w.group(1) or ''),
                      m.group(0), count=1)

    for motif in (r'<section class="(?:rp-)?section[^"]*">.*?</section>',
                  r'<section class="pg-sec[^"]*">.*?</section>'):
        h = re.sub(motif, bloc, h, flags=re.S)
    return h


def embellir(h):
    """Applique la mise en forme à une page entière. Idempotent."""
    if MARQUE in h:
        return h, {}
    h, c = _scinder(h)
    h, q = _questions(h)
    h, l = _listes(h)
    h, t = _tableaux(h)
    h, r = _reveal(h)
    h = _marquer(h)
    if '</head>' in h:
        h = h.replace('</head>', STYLE + '</head>', 1)
    return h, {'questions': q, 'collages': c, 'listes': l, 'tableaux': t, 'reveal': r}


# ── contrôle ─────────────────────────────────────────────────────────────

def mots(h):
    """Le sac de mots d'une page — pour prouver qu'on n'a rien perdu."""
    corps = re.sub(r'<(script|style)\b.*?</\1>', ' ', h, flags=re.S)
    return sorted(re.findall(r"[\w’'-]+", _texte(corps).lower()))


def main():
    a_p = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    a_p.add_argument('fichiers', nargs='+')
    a_p.add_argument('--essai', action='store_true')
    a = a_p.parse_args()

    total, perdus = {'questions': 0, 'collages': 0, 'listes': 0,
                     'tableaux': 0, 'reveal': 0}, 0
    for f in a.fichiers:
        with open(f, encoding='utf-8') as fh:
            avant = fh.read()
        apres, bilan = embellir(avant)
        if not bilan:
            print('   %-58s déjà mis en forme' % os.path.basename(f)[:58])
            continue
        # Le contrôle qui compte : mot pour mot, rien n'a bougé.
        m_av, m_ap = mots(avant), mots(apres)
        ecart = sorted(set(m_av) ^ set(m_ap))
        for k in total:
            total[k] += bilan[k]
        print('   %-58s %2d question(s), %d collage(s), %d liste(s), %d tableau(x)%s'
              % (os.path.basename(f)[:58], bilan['questions'], bilan['collages'],
                 bilan['listes'], bilan['tableaux'],
                 '' if not ecart else '   ⚠ ÉCART %s' % ecart[:6]))
        if ecart:
            perdus += 1
            continue
        if not a.essai:
            with open(f, 'w', encoding='utf-8') as fh:
                fh.write(apres)

    print('\n%d question(s) promues, %d collage(s) défaits, %d liste(s), '
          '%d tableau(x) protégé(s), %d garde-fou(s) avancé(s).'
          % (total['questions'], total['collages'], total['listes'],
             total['tableaux'], total['reveal']))
    if perdus:
        print('%d page(s) NON écrites : le texte ne correspondait plus.' % perdus)
        sys.exit(1)


if __name__ == '__main__':
    main()
