#!/usr/bin/env python3
"""
Une seule FAQ par page, toujours la même dans le fond et dans la forme.

    ./outils/faq-unique.py --site DIR [--essai]
    WP_AUTH='compte:mot de passe' ./outils/faq-unique.py --cms [--essai]

Relevé sur les 57 pages déployées le 23/09/2026 : 310 questions distinctes,
40 pages avec une FAQ, et surtout DEUX blocs de FAQ sur les sept pages
destination — celui que la page d'origine portait, et celui que le moule
ajoute. Mélanie l'a écrit trois fois : « il y a trop de FAQ », « 2 FAQ côte
à côte, c'est trop, réorganiser », « la FAQ n'est pas la même sur chaque
page ».

Trois formes cohabitaient : des <details> numérotés « 1) … », des paires
<h3 class="mef-q"> + <p>, et des accordéons sans classe commune. Trois
formes, c'est trois fois le risque qu'une seule soit corrigée.

Ce que fait cet outil :

  — il ramasse toutes les questions d'une page, quelle que soit leur forme ;
  — il les dédoublonne sur la question normalisée ;
  — il sépare ce qui est propre à la page de ce qui vaut pour tous les
    voyages (le tronc commun : visa, vaccins, paiement, annulation), et
    remet le tronc en second, sous son propre intertitre ;
  — il retire les emoji des questions et des réponses, et la numérotation
    « 1) », qui ne survit pas à une fusion ;
  — il repose UNE section, à la place de la première, et supprime les autres.

Il ne réécrit aucune phrase : il déplace, il dédoublonne, il range.
"""

import argparse
import html as H
import os
import re
import sys
import time
from importlib.machinery import SourceFileLoader

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Les emoji, et rien d'autre. L'étoile des notes (★), les flèches (→) et
# le chevron du menu ne sont pas des emoji : ce sont des signes
# typographiques, ils restent.
EMOJI = re.compile(
    '[\U0001F000-\U0001FAFF☀-⛿✀-➿⬀-⯿'
    '️‍♀♂]')

# Le tronc commun, relevé le 23/09/2026 : ces treize questions sont posées
# mot pour mot sur trente-quatre pages. Elles ne parlent pas du lieu mais
# du voyage — elles passent donc en second, après ce qui est propre à la
# page.
TRONC = (
    'comment organiser un voyage sur mesure en égypte',
    'est-ce dangereux de venir en égypte',
    'quels papiers d’identité faut-il pour partir',
    'ai-je besoin d’un visa pour voyager en égypte',
    'dois-je faire des vaccins',
    'réservez-vous les vols internationaux',
    'réservez-vous les vols internes',
    'puis-je changer mes dates ou l’itinéraire après réservation',
    'que se passe-t-il si je ne peux plus partir',
    'comment puis-je régler mon voyage',
    'le paiement est-il fractionnable',
    'l’acompte est-il remboursable',
    'puis-je offrir un voyage ou un crédit à un proche',
)

EYEBROW = 'Questions fréquentes'
TITRE = 'Les questions qui reviennent avant de partir'
SOUS_TITRE = 'Organiser, payer, modifier son voyage'

FEUILLE = (
    '<style data-faq="unique">'
    '.pg-sec .faqu{margin:26px 0 0;max-width:820px;'
    'border:1px solid var(--ligne);border-radius:var(--r-l);background:#fff;overflow:hidden}'
    '.pg-sec .faq__q{border-bottom:1px solid var(--ligne)}'
    '.pg-sec .faq__q:last-child{border-bottom:0}'
    '.pg-sec .faq__q>summary{display:flex;justify-content:space-between;align-items:baseline;'
    'gap:16px;padding:16px 20px;cursor:pointer;list-style:none;'
    'font-size:1rem;font-weight:600;line-height:1.45;color:var(--nuit-900)}'
    '.pg-sec .faq__q>summary::-webkit-details-marker{display:none}'
    '.pg-sec .faq__q>summary::after{content:"+";flex:0 0 auto;'
    'font-family:"Manrope",sans-serif;font-size:1.3rem;font-weight:700;'
    'line-height:1;color:var(--teal-txt)}'
    '.pg-sec .faq__q[open]>summary::after{content:"\\2212"}'
    '.pg-sec .faq__q>summary:hover{background:var(--teal-fond)}'
    '.pg-sec .faq__q>summary:focus-visible{outline:3px solid var(--or);outline-offset:-3px}'
    '.pg-sec .faq__r{padding:0 20px 18px}'
    '.pg-sec .faq__r p{margin:0 0 10px;max-width:68ch;color:var(--texte);line-height:1.65}'
    '.pg-sec .faq__r p:last-child{margin-bottom:0}'
    '.pg-sec .faq__r ul,.pg-sec .faq__r ol{margin:0 0 10px;padding-left:22px;color:var(--texte)}'
    '.pg-sec .faq__t{margin:26px 0 0;font-family:"Manrope",sans-serif;font-size:.78rem;'
    'font-weight:800;letter-spacing:.1em;text-transform:uppercase;color:var(--teal-txt)}'
    '.pg-sec .faq__t+.faqu{margin-top:10px}'
    '</style>')


def texte(x):
    return re.sub(r'\s+', ' ', H.unescape(re.sub(r'<[^>]+>', ' ', x))).strip()


def _cle(q):
    """La question réduite à ce qui permet de reconnaître un doublon."""
    q = texte(q).casefold()
    q = re.sub(r'^\d+[).]\s*', '', q)
    q = q.replace("'", '’')
    return re.sub(r'[\s?!.:]+$', '', q).strip()


def sans_emoji(x):
    return re.sub(r'  +', ' ', EMOJI.sub('', x))


def _fin_balise(h, debut, nom):
    """La fin de l'élément ouvert en `debut`, comptée en profondeur."""
    p = 0
    for t in re.finditer(r'<(/?)%s\b[^>]*>' % nom, h[debut:]):
        p += 1 if not t.group(1) else -1
        if p == 0:
            return debut + t.end()
    return -1


def questions_de(bloc):
    """Les couples (question, réponse) d'un bloc, quelle que soit sa forme."""
    out = []

    # Forme 1 : <details><summary>Q</summary>…R…</details>
    i = 0
    while True:
        d = bloc.find('<details', i)
        if d < 0:
            break
        f = _fin_balise(bloc, d, 'details')
        if f < 0:
            break
        corps = bloc[d:f]
        s = re.search(r'<summary[^>]*>(.*?)</summary>', corps, re.S)
        if s:
            reste = corps[s.end():]
            reste = re.sub(r'</details>\s*$', '', reste)
            # La coquille intérieure du moule n'apporte rien à la réponse.
            reste = re.sub(r'^\s*<div[^>]*>(.*)</div>\s*$', r'\1', reste, flags=re.S)
            out.append((s.group(1), reste))
        i = f

    # Forme 2 : <h3 class="mef-q">Q</h3> puis les <p>/<ul> jusqu'au titre suivant
    for m in re.finditer(r'<h3[^>]*class="[^"]*mef-q[^"]*"[^>]*>(.*?)</h3>', bloc, re.S):
        suite = bloc[m.end():]
        # La borne doit aussi reconnaître une balise FERMANTE : « </section »
        # ne correspond pas à « <section\b ». Sans elle, la réponse de la
        # dernière question d'une section avalait le </section> qui la
        # suivait — et la section unifiée le reposait ailleurs, laissant la
        # page avec une fermeture de plus que d'ouvertures.
        fin = re.search(r'<(?:h[1-4]|details|section)\b|</(?:section|main|article)\b', suite)
        out.append((m.group(1), suite[:fin.start()] if fin else suite[:2500]))
    return out


def est_faq(section):
    """Une section qui pose des questions, quel que soit son titre."""
    h2 = re.search(r'<h2[^>]*>(.*?)</h2>', section, re.S)
    titre = texte(h2.group(1)) if h2 else ''
    if re.search(r'FAQ|questions?', titre, re.I):
        return True
    return section.count('<details') >= 2 or section.count('mef-q') >= 2


def rendre(propres, communes):
    """La section unique, dans la forme que toutes les pages partagent."""
    def accordeon(couples):
        return '<div class="faqu">%s</div>' % ''.join(
            '<details class="faq__q"><summary>%s</summary>'
            '<div class="faq__r">%s</div></details>'
            % (q, r) for q, r in couples)

    corps = accordeon(propres) if propres else ''
    if communes:
        if propres:
            corps += '<p class="faq__t">%s</p>' % SOUS_TITRE
        corps += accordeon(communes)
    return ('<section class="pg-sec pg-sec--fond"><div class="wrap">'
            '<p class="eyebrow">%s</p><h2>%s</h2>%s</div></section>'
            % (EYEBROW, TITRE, corps))


def unifier(h):
    """Une page, une FAQ. Rend (page, nombre de blocs fondus, questions)."""
    # Les <section> sont IMBRIQUÉES sur plusieurs pages. Un
    # « <section…>.*?</section> » non gourmand s'arrête à la première
    # fermeture venue — celle de la section INTÉRIEURE. La section
    # extérieure était alors coupée en deux : la moitié qui portait treize
    # questions n'était vue par personne, et surtout, en retirant la
    # « section » ainsi délimitée on emportait une ouverture sans sa
    # fermeture. Le balisage des pages profil est passé de 10 ouvertures
    # et 10 fermetures à 9 et 10. Le navigateur rattrape, pas les outils.
    #
    # On relève donc TOUTES les sections, à tous les niveaux, en comptant
    # la profondeur ; on garde celles qui posent des questions ; puis on
    # écarte celles qui en contiennent une autre déjà gardée. Reste la
    # section la plus intérieure qui porte vraiment la FAQ.
    toutes = []
    i = 0
    while True:
        d = h.find('<section', i)
        if d < 0:
            break
        f_ = _fin_balise(h, d, 'section')
        if f_ > 0:
            toutes.append((d, f_, h[d:f_]))
        i = d + 8
    gardees = [t for t in toutes if est_faq(t[2])]
    bornes = [t for t in gardees
              if not any(u is not t and t[0] < u[0] and u[1] <= t[1] for u in gardees)]
    bornes.sort()
    if not bornes:
        return h, 0, 0

    vues, propres, communes = set(), [], []
    for _, _, bloc in bornes:
        for q, r in questions_de(bloc):
            q = sans_emoji(re.sub(r'^\s*\d+[).]\s*', '', q.strip()))
            r = sans_emoji(r).strip()
            k = _cle(q)
            if not k or k in vues:
                continue
            vues.add(k)
            (communes if k in TRONC else propres).append((q, r))

    neuve = rendre(propres, communes)
    # De la dernière à la première, pour que les positions restent justes.
    for n, (deb, fin, _) in enumerate(reversed(bornes)):
        h = h[:deb] + (neuve if n == len(bornes) - 1 else '') + h[fin:]
    h = re.sub(r'<style data-faq="unique">.*?</style>', '', h, flags=re.S)
    # En DERNIER : à égalité de spécificité, c'est l'ordre qui tranche, et
    # le moule pose ses propres règles d'accordéon plus bas dans la page.
    h = h + FEUILLE
    return h, len(bornes), len(vues)


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--site', help='dossier de pages à traiter sur place')
    p.add_argument('--cms', action='store_true', help='traiter les brouillons du CMS')
    p.add_argument('--essai', action='store_true', help='mesurer sans rien écrire')
    a = p.parse_args()
    if not a.site and not a.cms:
        raise SystemExit('il faut --site DIR ou --cms')

    if a.site:
        for nom in sorted(os.listdir(a.site)):
            if not nom.endswith('.html'):
                continue
            chemin = os.path.join(a.site, nom)
            with open(chemin, encoding='utf-8') as f:
                h = f.read()
            neuf, blocs, q = unifier(h)
            if blocs:
                print('   %-56s %d bloc(s) → 1, %d questions' % (nom[:56], blocs, q))
                if not a.essai:
                    with open(chemin, 'w', encoding='utf-8') as f:
                        f.write(neuf)
        return

    dep = SourceFileLoader('dep', os.path.join(RACINE, 'outils', 'deployer.py')).load_module()
    MERE = 7642
    Q = '/pages?parent=%d&per_page=100&status=any&context=edit&orderby=menu_order&order=asc'
    pages = []
    for d in dep.appel('GET', Q % MERE):
        if d['status'] == 'trash':
            continue
        pages += [k for k in dep.appel('GET', Q % d['id']) if k['status'] != 'trash']

    total_blocs = total_pages = 0
    for k in pages:
        p_ = dep.appel('GET', '/pages/%d?context=edit' % k['id'])
        brut = p_['content']['raw']
        h = re.sub(r'<!-- /?wp:html -->\n?', '', brut)
        neuf, blocs, q = unifier(h)
        if not blocs:
            continue
        titre = (p_.get('title') or {}).get('raw', '')
        print('   #%-6d %-46s %d bloc(s) → 1, %2d questions'
              % (k['id'], titre[:46], blocs, q))
        total_blocs += blocs
        total_pages += 1
        if a.essai:
            continue
        # Le contenu repart dans la coquille de blocs qu'il avait.
        corps = '<!-- wp:html -->\n' + neuf + '\n<!-- /wp:html -->'
        # Le serveur rend parfois une redirection au lieu du JSON, et le
        # script s'arrêtait au milieu du lot. La transformation est
        # idempotente — une page déjà unifiée se reconstruit à l'identique
        # — donc une reprise ne peut pas abîmer ce qui est déjà écrit.
        for essai in range(4):
            try:
                dep.appel('POST', '/pages/%d' % k['id'], {'content': corps})
                relu = dep.appel('GET', '/pages/%d?context=edit' % k['id'])
                if relu['content']['raw'].count('data-faq="unique"') == 1:
                    break
                print('      reprise %d/3 — la feuille n’est pas sur la page' % (essai + 1))
            except SystemExit as motif:
                print('      reprise %d/3 — %s' % (essai + 1, str(motif).splitlines()[0][:70]))
            time.sleep(2 ** essai)
        else:
            print('      ✗ ABANDON sur cette page, elle reste telle quelle')
    print('\n%d page(s), %d bloc(s) de FAQ fondus en %d.'
          % (total_pages, total_blocs, total_pages))


if __name__ == '__main__':
    main()
