#!/usr/bin/env python3
"""
Monte la page agence sur l'ordre des sections relevé chez les concurrents.

    ./outils/gabarit-agence.py --moule FICHIER --site DIR --sortie DIR [--essai]

L'ordre ne vient pas d'une intuition : il est relevé sur sept agences qui se
positionnent en France sur « agence de voyage égypte francophone », « agence
locale egypte » et « voyage sur mesure egypte agence » — Voyageurs du Monde,
Terres Égyptiennes, Cheops Travel, Altaï Egypt, Égypte Éthique, Égypte
Voyages, Étendues Sauvages. Vingt-six pages ouvertes.

Ce que le marché impose (au moins quatre agences sur sept) : accroche,
approche en piliers, engagements, garanties, bureaux, équipe nommée,
assistance, appel au devis. Ce qui distingue : la presse — AUCUN des sept
concurrents n'en a, et Authentique Égypte a Le Figaro deux fois, Marie
Claire, Evaneos, Partir.com, TripAdvisor. Elle remonte donc de la septième
place à la troisième.

Deux règles tiennent ce fichier.

Rien n'est écrit qui ne soit déjà publié par l'agence. Chaque bloc dit d'où
il vient. Ce qui manque est marqué « à remplir » et reste visible comme tel :
un trou signalé se comble, un trou masqué se découvre en production.

Et AUCUNE garantie n'est affichée sans preuve. Immatriculation Atout France,
garantie financière APST, responsabilité civile professionnelle, numéro de
licence égyptienne : tant que l'agence n'a pas confirmé qu'elles existent,
la page n'en dit pas un mot. Afficher une garantie qu'on n'a pas est une
mention trompeuse, et c'est le genre de ligne qu'un gabarit ajoute sans que
personne ne la relise.
"""

import argparse
import html as H
import json
import os
import re
import sys
from importlib.machinery import SourceFileLoader

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_circ = SourceFileLoader('gabarit_circuit',
                         os.path.join(RACINE, 'outils', 'gabarit-circuit.py')).load_module()
_bleu = SourceFileLoader('bleu_unique',
                         os.path.join(RACINE, 'outils', 'bleu-unique.py')).load_module()

SIRET = '928 008 226 00013'
SIEGE = '17 Avenue Gambetta, 82000 Montauban, France'
MENTIONS = 'https://authentiquegypte.com/mentions-legales-agence-voyage-egypte/'

# Les réponses de Mélanie, relevées dans le plugin de relecture le
# 30 août 2026 (fils #8495 à #8511 sur la maquette #7657). Elles répondent
# aux emplacements que la page marquait « à remplir ». Rien n'est déduit :
# c'est ce qu'elle a écrit, remis en phrase quand la note était télégraphique.
MELANIE = {
    'fondation': '2019 en Égypte, en collaboration avec notre agence sur place. '
                 'La société française a été enregistrée en 2024.',
    'voyageurs': '3493',
    'equipe': [
        ('Mélanie', 'Fondatrice',
         'Organise des séjours sur mesure depuis bientôt dix ans. Vit entre '
         'Le Caire et l’Égypte, et adore donner ses meilleurs conseils.'),
        ('Hend', 'Agente locale — Égyptienne francophone',
         'Égyptienne francophone, elle adore parler de son pays et le faire '
         'découvrir. Basée au Caire.'),
    ],
    'equipe_note': 'Au-delà des conseillères locales présentes sur place, toute une '
                   'équipe s’occupe des réservations, gère le séjour sur place et '
                   'assure la représentation.',
}

# Ce qui manque encore. Marqué sur la page, jamais deviné.
A_REMPLIR = {
    'licence': 'numéro de licence touristique égyptienne et nom du partenaire qui la détient',
    'garanties': 'immatriculation Atout France, garantie financière, responsabilité civile '
                 '— à vérifier avant toute publication',
    'delai': 'délai réel d’envoi du premier devis',
    'tarif': 'formulation de l’engagement tarifaire',
    'bureau': 'adresse du bureau du Caire, si elle est communicable',
    'note': 'note Google exacte — Mélanie indique 4,7 « il me semble », '
            'à confirmer avant affichage',
}


def texte(x):
    return re.sub(r'\s+', ' ', H.unescape(re.sub(r'<[^>]+>', ' ', x))).strip()


def a_remplir(cle):
    return ('<p class="atelier"><span class="aremplir">à remplir</span> %s</p>'
            % H.escape(A_REMPLIR[cle]))


def source(url, quoi):
    """D'où vient le bloc, en légende.

    « Repris de » imposait un complément féminin singulier : le renvoi aux
    mentions légales s'affichait « Repris de les mentions légales du site ».
    Deux points ne se trompent jamais de genre.
    """
    return ('<p class="prov">Source&nbsp;: <a href="%s" target="_blank" '
            'rel="noopener">%s</a></p>' % (url, H.escape(quoi)))


# Les morceaux déjà pris. Sans ce registre, deux ancres proches rendaient
# le MÊME grand bloc — la page agence portait ainsi l'histoire de Mélanie,
# l'équipe et les garanties quatre fois de suite, et sept colonnes latérales
# pour une seule utile.
_PRIS = []


def bloc_apres(h, ancre, fin='</section>', bornes=()):
    """Le morceau de page qui suit un titre, jusqu'à la fin de sa section.

    Deux bornes, apprises d'un premier montage où « Votre projet » revenait
    huit fois : on s'arrête au prochain titre de même niveau, et on retire les
    appels au devis emportés au passage — le gabarit en pose un seul, à la fin.
    """
    i = h.find('>' + ancre)
    if i < 0:
        return ''
    debut = h.rfind('<', 0, i)
    # La plupart des ancres sont des <h3> posés dans un « <div class="atout"> »,
    # et ces div sont des frères d'une même grille. Partir du <h3> coupait donc
    # au milieu d'un frère : on remonte au conteneur et on prend le bloc entier.
    # Le motif de balise englobe le « > » final : sans lui, t.end() tombait
    # AVANT le chevron et le bloc sortait coupé en plein « </div », ce qui
    # déformait tout ce qui suivait — et empêchait de reconnaître la boîte
    # voisine, donc de prendre les trois piliers ou les quatre médias.
    boite = h.rfind('<div class="atout"', 0, debut)
    if boite >= 0:
        profondeur, fin_boite = 0, -1
        for t in re.finditer(r'<(/?)div\b[^>]*>', h[boite:]):
            profondeur += 1 if not t.group(1) else -1
            if profondeur == 0:
                fin_boite = boite + t.end()
                break
        if fin_boite > i:
            # Les boîtes voisines qui n'ouvrent pas une autre section font
            # partie du même groupe : « Notre approche » en compte trois,
            # « Ils parlent de nous » quatre. S'arrêter à la première n'en
            # gardait qu'une, et le registre des morceaux déjà pris effaçait
            # les autres pour de bon.
            while True:
                reste = h[fin_boite:fin_boite + 40]
                suivant = h.find('<div class="atout"', fin_boite)
                if suivant < 0 or texte(reste.split('<')[0]):
                    break
                p2, f2 = 0, -1
                for t in re.finditer(r'<(/?)div\b[^>]*>', h[suivant:]):
                    p2 += 1 if not t.group(1) else -1
                    if p2 == 0:
                        f2 = suivant + t.end()
                        break
                # La borne se teste sur le TITRE entier, pas sur un morceau :
                # « Le Figaro Madame » contient « Le Figaro », et la boîte
                # s'arrêtait donc avant lui — la page ne citait que deux des
                # quatre médias.
                if f2 < 0 or any(('<h3>%s</h3>' % b2) in h[suivant:f2] for b2 in bornes):
                    break
                fin_boite = f2
            bloc = h[boite:fin_boite]
            bloc = re.sub(r'<p class="(?:atelier|prov)">.*?</p>', '', bloc, flags=re.S)
            for vu in _PRIS:
                if vu and vu in bloc:
                    bloc = bloc.replace(vu, '')
            if texte(bloc):
                _PRIS.append(bloc)
            return _circ.equilibrer(bloc)
    # La borne de fin est la PLUS PROCHE entre la fin de section et l'ancre
    # suivante : s'arrêter à « </section> » ramassait tout ce qui séparait
    # deux titres, y compris les blocs destinés aux sections d'après.
    j = h.find(fin, debut)
    # L'ancre du bloc courant ne peut pas être sa propre borne de fin : la
    # première version la retrouvait à sa place et concluait qu'il n'y avait
    # rien après, si bien qu'aucune borne ne s'appliquait jamais.
    apres = i + len(ancre)
    fins = [x for x in (h.find('>' + b2, apres) for b2 in bornes if b2 != ancre) if x > 0]
    if fins:
        prochaine = h.rfind('<', 0, min(fins))
        if prochaine > debut and (j < 0 or prochaine < j):
            j, fin = prochaine, ''
    bloc = h[debut:j + len(fin)] if j > 0 else h[debut:debut + 1600]
    # La page reprise a déjà servi de source à une génération précédente :
    # elle en a gardé nos marqueurs d'atelier (« à remplir ») et nos
    # légendes de provenance. Retransplantés, ils s'ajoutaient à ceux que
    # le gabarit repose lui-même — la section « engagements » affichait
    # deux fois « formulation de l'engagement tarifaire ». Ces marques
    # appartiennent au gabarit, pas au contenu : il les remet où il faut.
    bloc = re.sub(r'<p class="(?:atelier|prov)">.*?</p>', '', bloc, flags=re.S)
    # La colonne latérale de la page reprise n'a rien à faire dans une
    # section : celle-ci est posée une fois, à sa place, par le gabarit.
    # Quatre exemplaires traînaient encore après la correction du
    # chevauchement, un par bloc transplanté.
    bloc = re.sub(r'<aside\b.*?</aside>', '', bloc, flags=re.S)
    # Le fragment « TripAdvisor / Avis voyageurs » est un reste sans avis :
    # Mélanie l'a marqué « à supprimer ou connecter les vrais avis Google »
    # (fil #8506). Le mur d'avis Google du gabarit tient déjà ce rôle.
    bloc = re.sub(r'<h[34][^>]*>\s*TripAdvisor\s*</h[34]>\s*'
                  r'(?:<p[^>]*>\s*Avis voyageurs\s*</p>\s*)?', '', bloc, flags=re.S | re.I)
    # Et ce qui a déjà servi ne ressert pas.
    for vu in _PRIS:
        if vu and vu in bloc:
            bloc = bloc.replace(vu, '')
    if texte(bloc):
        _PRIS.append(bloc)
    # Un morceau découpé au milieu d'une page emporte des fermetures dont
    # l'ouverture est restée derrière : recollé dans une section, ce </div>
    # ferme la gouttière avant l'heure et le texte part au bord de l'écran.
    bloc = _circ.equilibrer(bloc)

    # Pas de borne sur les titres : la section « équipe » enchaîne quatre H3
    # de même niveau — un titre de bloc puis ses trois sous-blocs — et s'y
    # arrêter perdait « Des experts passionnés par leur pays », « Connaissant
    # parfaitement le terrain » et « À taille humaine et authentiques ».
    # C'est le retrait des appels au devis, plus bas, qui réglait le doublon.
    for motif in (r'<section[^>]*>(?:(?!</section>).)*?<div class="devis">.*?</section>',
                  r'<div class="devis">.*?</div>\s*</div>\s*</div>'):
        bloc = re.sub(motif, '', bloc, flags=re.S)
    return bloc


def _cle(x):
    """Un titre réduit à ce qui permet de le reconnaître : la casse et la
    ponctuation de fin ne distinguent pas deux fois le même titre."""
    return re.sub(r'[\s.:!?…]+$', '', texte(x)).casefold()


def sans_titre_repete(corps, *titres):
    """Retire du bloc les titres qui redisent celui de la section.

    Les blocs viennent de la page en ligne AVEC leur propre titre. Posés
    dans une section qui porte déjà le sien, ils le donnaient à lire deux
    fois de suite : « Notre histoire / Une aventure née d'un regard
    curieux » puis, trois lignes plus bas, « Notre histoire / Une aventure
    née d'un regard curieux ». La page reprise laissait en plus traîner un
    « Notre Histoire » seul, sans rien après — une étiquette, pas un titre.

    On ne retire QUE l'égalité stricte : un titre qui dit autre chose,
    même de près, reste. C'est du dédoublonnage, pas de la réécriture.
    """
    cles = {_cle(t) for t in titres if t}

    def juger(m):
        return '' if _cle(m.group(2)) in cles else m.group(0)

    return re.sub(r'<(h[1-4]|p)\b[^>]*>(.*?)</\1>', juger, corps, flags=re.S)


def section(surtitre, titre, corps, fond=False):
    # « creme » est le fond doré de la charte : Mélanie l'a demandé pour les
    # engagements, fil #8511. « True » reste le gris clair d'alternance.
    variante = {'creme': ' pg-sec--creme', True: ' pg-sec--fond'}.get(fond, '')
    return ('<section class="pg-sec%s"><div class="wrap">'
            '<p class="eyebrow">%s</p><h2>%s</h2>%s</div></section>'
            % (variante, H.escape(surtitre), H.escape(titre),
               sans_titre_repete(corps, surtitre, titre)))


def accroche(agence):
    """La phrase de positionnement, qui suit le H1 sur la page actuelle.

    « Notre structure franco-égyptienne s'appuie sur des années de terrain… »
    Sept agences sur sept en ont une : c'est la section la plus universelle du
    marché, et la seule chose que la page dit d'elle-même avant d'entrer dans
    le détail. Une première version la perdait — elle ne vit ni dans un chapô
    ni dans une section, seulement collée sous le titre.
    """
    # On ne cherche que dans le CORPS : la même phrase sert de méta
    # description, et le repli l'y attrapait — avec le « "> » qui ferme
    # l'attribut, resté visible en bout de ligne sur la page.
    corps = agence[agence.find('<body'):] or agence
    m = re.search(r'Agence francophone en Égypte\\s*</[^>]+>\\s*<([a-z]+)[^>]*>(.*?)</\\1>',
                  corps, re.S)
    if m and 'franco-égyptienne' in m.group(2):
        return texte(m.group(2))
    m = re.search(r'(Notre structure franco-égyptienne[^<]{40,400})', corps)
    return H.unescape(m.group(1)).strip() if m else ''


# Les titres qui servent d'ancre dans la page reprise, dans l'ordre. Chaque
# bloc s'arrête au suivant : c'est ce qui empêche un morceau de partir deux
# fois.
ANCRES = ('Notre histoire', 'Notre engagement envers vous',
          'Une équipe locale engagée', 'Contact initial',
          'Des voyages flexibles', 'Le Figaro', 'FAQ - Questions')


# ---------------------------------------------------------------------------
# La mise en page
# ---------------------------------------------------------------------------
#
# Le montage produisait un balisage juste et une page illisible : sur les
# soixante-deux classes du corps, CINQ n'avaient aucune règle — « atout »
# treize fois, « atelier » six, « prov », « chiffres », « garanties ». Les
# trois piliers, les quatre médias, les étapes de la méthode : tout tombait
# en <h3> et <p> empilés sur 1180 px de large, soit cent quarante signes par
# ligne, la moitié droite vide. Une page « montée » n'est pas une page
# « mise en page ».
#
# Tout est scopé sous « .pg-sec » : le moule ne définit pour cette classe
# que le fond et les marges, mais une règle d'élément nue perdrait contre
# n'importe laquelle des siennes. Deux niveaux suffisent et évitent la
# surenchère.
SCRIPT_AGENCE = (
    '<script>(function(){'
    'var doux=window.matchMedia&&window.matchMedia("(prefers-reduced-motion: reduce)").matches;'

    # L'apparition au défilement, si et seulement si on a de quoi la faire
    # proprement. Sans observateur, on ne cache rien.
    'if(!doux&&"IntersectionObserver" in window){'
    'document.documentElement.className+=" js-anim";'
    'var io=new IntersectionObserver(function(es){es.forEach(function(e){'
    'if(e.isIntersecting){e.target.className+=" vu";io.unobserve(e.target)}})},'
    '{rootMargin:"0px 0px -12% 0px",threshold:.08});'
    'Array.prototype.forEach.call(document.querySelectorAll(".rev"),function(n){io.observe(n)});'
    # Et quoi qu'il arrive, tout finit par s'afficher. Un observateur qui
    # ne se déclenche pas laisserait des blocs invisibles pour de bon : le
    # défaut le plus coûteux d'une animation à l'apparition, parce qu'il
    # ne se voit pas chez celui qui l'écrit.
    'setTimeout(function(){Array.prototype.forEach.call('
    'document.querySelectorAll(".rev:not(.vu)"),function(n){n.className+=" vu"})},4000);'
    '}'

    # Le carrousel. Les flèches poussent le ruban d'une vignette ; le
    # défilement automatique s'arrête au survol, au clavier et quand
    # l'onglet passe derrière.
    'var c=document.querySelector("[data-carr]");if(!c)return;'
    'var piste=c.querySelector("[data-piste]"),'
    'prec=c.querySelector("[data-carr-prec]"),suiv=c.querySelector("[data-carr-suiv]"),'
    'pause=c.querySelector("[data-carr-pause]"),arrete=doux,dedans=false,minuteur=null;'
    'function pas(){var d=piste.querySelector(".carr__d");'
    'return d?d.getBoundingClientRect().width+16:320}'
    'function pousser(sens){'
    'var fin=piste.scrollWidth-piste.clientWidth-2;'
    'if(sens>0&&piste.scrollLeft>=fin){piste.scrollLeft=0;return}'
    'if(sens<0&&piste.scrollLeft<=2){piste.scrollLeft=fin;return}'
    'piste.scrollLeft+=sens*pas()}'
    'prec.addEventListener("click",function(){pousser(-1)});'
    'suiv.addEventListener("click",function(){pousser(1)});'
    'pause.addEventListener("click",function(){arrete=!arrete;'
    'pause.setAttribute("aria-pressed",arrete?"true":"false");'
    'pause.textContent=arrete?"Lecture":"Pause"});'
    'c.addEventListener("mouseenter",function(){dedans=true});'
    'c.addEventListener("mouseleave",function(){dedans=false});'
    'c.addEventListener("focusin",function(){dedans=true});'
    'c.addEventListener("focusout",function(){dedans=false});'
    'piste.addEventListener("keydown",function(e){'
    'if(e.key==="ArrowRight"){e.preventDefault();pousser(1)}'
    'if(e.key==="ArrowLeft"){e.preventDefault();pousser(-1)}});'
    'if(doux){pause.textContent="Lecture";pause.setAttribute("aria-pressed","true")}'
    'minuteur=setInterval(function(){'
    'if(!arrete&&!dedans&&!document.hidden)pousser(1)},5000);'
    '})();</script>'
)


FEUILLE_AGENCE = (
    '<style data-agence="mise-en-page">'

    # La mesure de lecture. C'est la correction qui se voit le plus : une
    # colonne de texte qui court sur toute la largeur ne se lit pas.
    '.pg-sec .wrap>p,.pg-sec .wrap>ul,.pg-sec .wrap>ol{max-width:60ch}'
    '.pg-sec .wrap>h2+p,.pg-sec .lede{max-width:56ch}'
    '.pg-sec .lede{margin:0 0 4px;font-size:1.14rem;line-height:1.6;color:var(--nuit-900)}'
    '.pg-sec .cit{margin:2px 0 18px;padding:0 0 0 16px;border-left:3px solid var(--or);'
    'font-size:1.16rem;line-height:1.55;color:var(--nuit-900);max-width:52ch}'
    '.pg-sec .wrap>h3,.pg-sec .wrap>h4{margin:28px 0 6px;font-family:"Archivo",system-ui,sans-serif;'
    'font-size:1.12rem;font-weight:700;line-height:1.3;color:var(--nuit-900)}'
    '.pg-sec .wrap>h3+p,.pg-sec .wrap>h4+p{margin-top:0}'

    # Les chiffres-clés. Ils étaient en paragraphes courants : « 3493
    # voyageurs accompagnés » se lisait comme une phrase perdue.
    '.pg-sec .chiffres{display:flex;flex-wrap:wrap;gap:14px;margin:24px 0 20px;padding:0;max-width:none}'
    '.pg-sec .chiffres b{display:flex;flex-direction:column;gap:2px;min-width:170px;'
    'background:#fff;border:1px solid var(--ligne);border-top:3px solid var(--or);'
    'border-radius:var(--r-l);padding:18px 22px;'
    'font-family:"Manrope",sans-serif;font-size:2rem;font-weight:800;'
    'line-height:1.1;color:var(--nuit-900);font-variant-numeric:tabular-nums}'
    '.pg-sec .chiffres b span{font-size:.8rem;font-weight:700;letter-spacing:.08em;'
    'text-transform:uppercase;color:var(--teal-txt)}'

    # Les atouts : la grille de cartes. « auto-fit » plutôt qu'un nombre fixe
    # de colonnes, parce que les suites vont de deux à quatre selon la
    # section, et qu'une colonne vide est pire qu'une colonne de moins.
    '.pg-sec .atouts{display:grid;grid-template-columns:repeat(auto-fit,minmax(270px,1fr));'
    # Chaque carte à sa hauteur. Étirées sur la plus haute, les trois
    # cartes d'une ligne de l'équipe — une ligne de texte chacune —
    # s'alignaient sur une carte de sept lignes : 70 % de blanc dans
    # trois cartes sur quatre.
    'gap:18px;margin:26px 0 0;align-items:start}'
    '.pg-sec .atout{background:#fff;border:1px solid var(--ligne);border-radius:var(--r-l);'
    'padding:24px;margin:0}'
    '.pg-sec--fond .atout,.pg-sec--creme .atout{background:#fff}'
    '.pg-sec .atout h3{margin:0 0 8px;font-size:1.08rem;line-height:1.3;'
    'font-weight:700;color:var(--nuit-900)}'
    '.pg-sec .atout p{margin:0;max-width:none;color:var(--texte);line-height:1.65}'

    # Les étapes. Un parcours se numérote : « Contact initial » puis
    # « Programme interactif » ne disaient pas qu'il y avait un ordre.
    '.pg-sec .atouts--etapes{counter-reset:etape}'
    '.pg-sec .atouts--etapes .atout{counter-increment:etape;padding-top:22px}'
    '.pg-sec .atouts--etapes .atout::before{content:counter(etape);display:grid;'
    'place-items:center;width:34px;height:34px;margin:0 0 12px;border-radius:50%;'
    'background:var(--or-fond);color:#7A5605;'
    'font-family:"Manrope",sans-serif;font-weight:800;font-size:.95rem}'

    # La presse. Le nom du média est l'information, le titre de l'article
    # vient après : on inverse donc la hiérarchie typographique.
    '.pg-sec .atouts--presse{grid-template-columns:repeat(auto-fit,minmax(210px,1fr))}'
    '.pg-sec .atouts--presse .atout{padding:20px 22px}'
    '.pg-sec .atouts--presse .atout h3{margin:0 0 6px;'
    'font-family:"Manrope",sans-serif;font-size:.8rem;font-weight:800;'
    'letter-spacing:.1em;text-transform:uppercase;color:var(--teal-txt)}'
    '.pg-sec .atouts--presse .atout p{font-size:1rem;color:var(--nuit-900);font-weight:500}'

    # Les mentions juridiques : des lignes, pas des puces.
    '.pg-sec .garanties{list-style:none;margin:22px 0 0;padding:0;max-width:640px;'
    'background:#fff;border:1px solid var(--ligne);border-radius:var(--r-l)}'
    '.pg-sec .garanties li{padding:14px 22px;border-bottom:1px solid var(--ligne);'
    'color:var(--texte);line-height:1.5}'
    '.pg-sec .garanties li:last-child{border-bottom:0}'
    '.pg-sec .garanties b{color:var(--nuit-900)}'

    # D'où vient le bloc. C'est une note de travail : elle doit se lire
    # comme une légende, pas comme une phrase de la page.
    '.pg-sec .prov{margin:18px 0 0;padding:0 0 0 12px;border-left:2px solid var(--ligne);'
    'font-size:.86rem;line-height:1.5;color:#5B6870}'
    '.pg-sec .prov a{color:var(--teal-txt)}'

    # Ce qui manque encore, et qu'on ne devine pas.
    '.pg-sec .atelier{display:flex;align-items:flex-start;gap:10px;margin:18px 0 0;'
    'padding:12px 16px;max-width:62ch;border:1px dashed var(--or);border-radius:10px;'
    'background:var(--or-fond);color:#7A5605;font-size:.92rem;line-height:1.5}'
    '.pg-sec .aremplir{flex:0 0 auto;border:0;background:#7A5605;color:#fff;'
    'border-radius:999px;padding:2px 10px;'
    'font-family:"Manrope",sans-serif;font-size:.7rem;font-weight:800;'
    'letter-spacing:.06em;text-transform:uppercase}'

    # L'équipe : les fiches suivent la forme des cartes du site — fond
    # blanc, filet, même rayon — pour ne pas introduire un objet de plus.
    '.pg-sec .equipe{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));'
    'gap:18px;margin:26px 0 0}'
    '.pg-sec .pers{background:#fff;border:1px solid var(--ligne);'
    'border-radius:var(--r-l);padding:24px}'
    '.pg-sec .pers h3{margin:0 0 4px;font-size:1.14rem;color:var(--nuit-900)}'
    '.pg-sec .pers__r{margin:0 0 12px;font-family:"Manrope",sans-serif;font-size:14px;'
    'font-weight:700;letter-spacing:.04em;text-transform:uppercase;color:var(--teal-txt)}'
    '.pg-sec .pers p{margin:0;max-width:none;color:var(--texte);line-height:1.65}'

    # Texte et photo côte à côte. La colonne de texte garde sa mesure de
    # lecture ; l'image prend le reste, et passe dessous sous 860 px.
    '.pg-sec .duo{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,.78fr);'
    'gap:34px;align-items:start;margin:22px 0 0}'
    '.pg-sec .duo__t>p{max-width:none}'
    '.pg-sec .duo__i{margin:0}'
    '.pg-sec .duo__i img{display:block;width:100%;height:auto;border-radius:var(--r-l)}'
    '.pg-sec .duo__i figcaption{margin:10px 2px 0;font-size:.86rem;line-height:1.45;color:#5B6870}'
    '@media (max-width:860px){.pg-sec .duo{grid-template-columns:1fr;gap:22px}}'

    # Le carrousel. « scroll-snap » suffit : la molette, le doigt et les
    # flèches poussent le même ruban, et il reste utilisable sans script.
    '.pg-sec--photos{background:var(--nuit-900);color:#D4E5E8}'
    '.pg-sec--photos h2{color:#fff}'
    '.pg-sec--photos .eyebrow{color:var(--or)}'
    '.pg-sec--photos .lede{color:#BBD4D9}'
    '.carr{position:relative;margin:26px 0 0}'
    '.carr__piste{display:flex;gap:16px;margin:0;padding:0 0 10px;list-style:none;'
    'overflow-x:auto;scroll-snap-type:x mandatory;scroll-behavior:smooth;'
    'scrollbar-width:thin;scrollbar-color:rgba(255,255,255,.35) transparent}'
    '.carr__piste:focus-visible{outline:3px solid var(--or);outline-offset:4px;border-radius:var(--r-l)}'
    '.carr__d{flex:0 0 clamp(240px,32vw,380px);scroll-snap-align:start;margin:0}'
    '.carr__d img{display:block;width:100%;height:auto;aspect-ratio:3/2;object-fit:cover;'
    'border-radius:var(--r-l);background:#0b3f4a}'
    '.carr__d span{display:block;margin:10px 2px 0;font-size:.86rem;line-height:1.45;color:#BBD4D9}'
    '.carr__nav{display:flex;gap:10px;align-items:center;margin:16px 0 0}'
    '.carr__b{min-width:44px;min-height:44px;padding:0 14px;border-radius:999px;'
    'border:1px solid rgba(255,255,255,.4);background:transparent;color:#fff;cursor:pointer;'
    'font-family:"Manrope",sans-serif;font-size:1.1rem;font-weight:700;line-height:1}'
    '.carr__b--stop{font-size:.84rem;letter-spacing:.06em;text-transform:uppercase}'
    '.carr__b:hover{background:rgba(255,255,255,.12)}'
    '.carr__b:focus-visible{outline:3px solid var(--or);outline-offset:2px}'

    # L'apparition au défilement. L'état AU REPOS est visible : si le script
    # ne tourne pas, ou si la personne a demandé moins d'animations, la page
    # s'affiche entière. C'est le script qui pose « js-anim », et seulement
    # s'il a le droit d'animer — une section cachée en attendant un
    # observateur qui ne vient jamais, c'est une page blanche.
    'html.js-anim .pg-sec .rev{opacity:0;transform:translateY(14px);'
    'transition:opacity .55s ease,transform .55s ease}'
    'html.js-anim .pg-sec .rev.vu{opacity:1;transform:none}'
    'html.js-anim .pg-sec .rev.vu>*:nth-child(2){transition-delay:.07s}'
    'html.js-anim .pg-sec .rev.vu>*:nth-child(3){transition-delay:.14s}'
    'html.js-anim .pg-sec .rev.vu>*:nth-child(4){transition-delay:.21s}'
    '@media (prefers-reduced-motion:reduce){'
    'html.js-anim .pg-sec .rev{opacity:1;transform:none;transition:none}'
    '.carr__piste{scroll-behavior:auto}}'

    '@media (max-width:640px){'
    '.pg-sec .chiffres b{min-width:0;flex:1 1 100%;font-size:1.7rem}'
    '.pg-sec .atout,.pg-sec .pers{padding:20px}'
    '}'
    '</style>'
)

# Le nom court de la variante de grille, lu sur le surtitre de la section.
# Il est lu là et pas posé au montage parce que les blocs viennent de la
# page reprise : le gabarit sait ce qu'est la section, le bloc ne le sait pas.
VARIANTES = {
    'Comment ça se passe': ' atouts--etapes',
    'Ils parlent de nous': ' atouts--presse',
}


def _fin_de_div(h, debut):
    """La position juste après le </div> qui ferme le div ouvert en `debut`.

    Compté en profondeur : un « .*?</div> » s'arrête au premier </div>
    rencontré, qui n'est pas forcément le bon.
    """
    profondeur = 0
    for t in re.finditer(r'<(/?)div\b[^>]*>', h[debut:]):
        profondeur += 1 if not t.group(1) else -1
        if profondeur == 0:
            return debut + t.end()
    return -1


def grouper_atouts(bloc, variante=''):
    """Enferme chaque suite de frères « atout » dans une grille.

    Ils sortent du montage comme des div frères posés à plat dans la
    gouttière : sans conteneur, aucune règle de grille ne peut les
    atteindre, et ils s'empilent sur toute la largeur.
    """
    out, i = [], 0
    while True:
        d = bloc.find('<div class="atout"', i)
        if d < 0:
            out.append(bloc[i:])
            break
        out.append(bloc[i:d])
        j, dernier = d, -1
        while bloc.startswith('<div class="atout"', j):
            f = _fin_de_div(bloc, j)
            if f < 0:
                break
            dernier = f
            j = f
            while j < len(bloc) and bloc[j] in ' \n\t\r':
                j += 1
        if dernier < 0:                       # div non fermé : on ne touche à rien
            out.append(bloc[d:d + 18])
            i = d + 18
            continue
        out.append('<div class="atouts%s rev">%s</div>' % (variante, bloc[d:dernier]))
        i = j
    return ''.join(out)


# ---------------------------------------------------------------------------
# Les photos
# ---------------------------------------------------------------------------
#
# Toutes viennent de la médiathèque de l'agence — aucune n'est empruntée
# ailleurs, aucune n'est ajoutée au site. La légende est le texte
# alternatif que l'agence a elle-même écrit sur l'image : c'est la seule
# légende qu'on ait le droit d'afficher, et c'est aussi ce qui la rend
# accessible. Les images sans texte alternatif sont écartées — en inventer
# un reviendrait à écrire à la place de la cliente.
#
# Relevé dans la médiathèque le 22/09/2026, format « large » (1024 px).
SITE_IMG = 'https://authentiquegypte.com/wp-content/uploads/'

PHOTOS = [
    (4967, '2025/06/Couple-dans-un-marche-en-Egypte-1024x683.png',
     'Couple dans un marché en Egypte', 1024, 683),
    (1561, '2023/11/e235bfb4-54a3-41cf-9f55-f2ca30fc8a91-1-1024x680.jpg',
     'Dahabeya', 1024, 680),
    (5416, '2025/07/mohamad-sameh-FGPo7AOnvv8-unsplash-1024x683.jpg',
     'Bédouins dans le désert', 1024, 683),
    (2400, '2023/11/Siwa_Oasis_sunset_on_Maraqi_Egypt-1024x577.webp',
     'oasis de siwa', 1024, 577),
    (5520, '2025/07/peggy-anke-YxpoB3bvlZQ-unsplash-1024x683.jpg',
     'Au bord du lagoon de la mer rouge', 1024, 683),
    (5121, '2025/06/raimond-klavins-8j3FvUT6yM4-unsplash-1024x683.jpg',
     'Monastère Sainte-Catherine, Raimond Klavins', 1024, 683),
    (4965, '2025/06/Photo-dune-famille-dans-le-desert-Egyptiens-1024x683.png',
     'Photo d’une famille dans le désert Egyptiens', 1024, 683),
    (2143, '2023/11/peter-ragheb-naYLQxASRTE-unsplash-1024x768.webp',
     'Désert dans l’Oasis de Fayoum', 1024, 768),
    (3138, '2023/11/WhatsApp-Image-2024-02-22-at-17.03.03-1024x768.webp',
     'Voyage culturel en Egypte', 1024, 768),
    (5119, '2025/06/DSC00493-1024x684.jpg', 'Guesthouse', 1024, 684),
]

# La photo qui accompagne le récit des débuts.
PHOTO_HISTOIRE = (5523, '2025/07/DSC00551_01-scaled-e1751464241518-1024x683.jpg',
                  'Spiritualité au sommet du mont Moïse au lever du soleil', 1024, 683)


def image(photo, classe='', paresseuse=True):
    """Une image de la médiathèque, avec ses dimensions.

    Les dimensions sont posées pour que le navigateur réserve la place
    avant de charger : sans elles, chaque photo qui arrive pousse le texte
    vers le bas et la page saute sous le curseur.
    """
    _, chemin, texte_alt, l, h = photo
    return ('<img%s src="%s%s" alt="%s" width="%d" height="%d"%s decoding="async">'
            % (' class="%s"' % classe if classe else '', SITE_IMG, chemin,
               H.escape(texte_alt), l, h, ' loading="lazy"' if paresseuse else ''))


def duo(corps, photo):
    """Un texte et une photo côte à côte.

    Une section de prose seule laisse la moitié droite de l'écran vide :
    c'est ce qui donnait à la page son air de document Word.
    """
    return ('<div class="duo"><div class="duo__t">%s</div>'
            '<figure class="duo__i">%s<figcaption>%s</figcaption></figure></div>'
            % (corps, image(photo), H.escape(photo[2])))


def carrousel():
    """Le carrousel de photos, en défilement à l'accroché.

    Pas de bibliothèque : « scroll-snap » fait le travail, la molette et le
    doigt marchent d'origine, et les deux flèches ne font que pousser le
    ruban. Une page qui charge un carrousel de cinquante kilo-octets pour
    montrer dix photos a déjà perdu.

    Le défilement automatique s'arrête au survol, au clavier, quand l'onglet
    passe à l'arrière-plan, et ne démarre jamais si la personne a demandé
    moins d'animations.
    """
    vignettes = ''.join(
        '<li class="carr__d">%s<span>%s</span></li>' % (image(p), H.escape(p[2]))
        for p in PHOTOS)
    return (
        '<section class="pg-sec pg-sec--photos"><div class="wrap">'
        '<p class="eyebrow">En images</p>'
        '<h2>Nos voyages en photos</h2>'
        '<p class="lede">Dix images prises pendant nos séjours, du Sinaï aux oasis.</p>'
        '<div class="carr" data-carr>'
        '<ul class="carr__piste" data-piste tabindex="0" role="region" '
        'aria-label="Photos de nos voyages">%s</ul>'
        '<div class="carr__nav">'
        '<button class="carr__b" type="button" data-carr-prec aria-label="Photo précédente">‹</button>'
        '<button class="carr__b carr__b--stop" type="button" data-carr-pause '
        'aria-pressed="false">Pause</button>'
        '<button class="carr__b" type="button" data-carr-suiv aria-label="Photo suivante">›</button>'
        '</div></div></div></section>' % vignettes)


def poser_schema(h):
    """Le balisage structuré d'une page agence.

    Le moule est une page destination : son JSON-LD décrivait « Voyage au
    Caire » — un TouristDestination, avec un fil d'ariane Accueil ›
    Destinations › Voyage au Caire, et la liste des attractions de Gizeh.
    Transplanté tel quel sur la page agence, il annonçait aux moteurs une
    page qui n'existe pas. Un balisage faux est pire qu'aucun balisage :
    celui-ci se remplace, il ne se supprime pas.

    Rien n'est inventé : la raison sociale, le SIRET et le siège viennent
    des mentions légales, le reste de l'en-tête du site.
    """
    graphe = {
        '@context': 'https://schema.org',
        '@graph': [
            {'@type': 'BreadcrumbList', 'itemListElement': [
                {'@type': 'ListItem', 'position': 1, 'name': 'Accueil',
                 'item': 'https://authentiquegypte.com/'},
                {'@type': 'ListItem', 'position': 2, 'name': 'L’agence',
                 'item': 'https://authentiquegypte.com/qui-sommes-nous/'}]},
            {'@type': 'TravelAgency',
             'name': 'Authentique Égypte',
             'legalName': 'OREYA',
             'url': 'https://authentiquegypte.com/',
             'email': 'contact@authentiquegypte.com',
             'telephone': '+20 106 661 9098',
             'areaServed': {'@type': 'Country', 'name': 'Égypte'},
             'availableLanguage': ['fr', 'ar', 'en'],
             'taxID': SIRET,
             'address': {'@type': 'PostalAddress',
                         'streetAddress': '17 Avenue Gambetta',
                         'postalCode': '82000',
                         'addressLocality': 'Montauban',
                         'addressCountry': 'FR'}},
        ],
    }
    rendu = ('<script type="application/ld+json">%s</script>'
             % json.dumps(graphe, ensure_ascii=False, separators=(',', ':')))
    h, combien = re.subn(r'<script type="application/ld\+json">.*?</script>',
                         lambda _: rendu, h, count=1, flags=re.S)
    if not combien:
        h = h.replace('</head>', rendu + '</head>', 1)
    # Un moule peut en porter plusieurs : ceux qui restent décrivent encore
    # la destination du moule, on les retire.
    tete, _, reste = h.partition(rendu)
    reste = re.sub(r'<script type="application/ld\+json">.*?</script>', '', reste, flags=re.S)
    return tete + rendu + reste


def _normaliser_titres(bloc):
    """Trois défauts de titre que la page reprise transporte.

    1. Un titre de carte rendu en <h2>. Deux des trois piliers sortent de
       l'accueil en <h2> et le troisième en <h3> : côte à côte, deux titres
       plus petits que le voisin, et un <h2> imbriqué sous le <h2> de
       section. Tout titre de carte est un <h3>.
    2. Un titre suivi immédiatement d'un autre titre de même niveau ou
       plus haut ne porte rien : c'est une étiquette de la page d'origine,
       pas un titre. « FAQ - Questions fréquentes » posé juste sous « Les
       questions qu'on nous pose » en est une.
    3. Un paragraphe entièrement entre guillemets est une citation, et se
       lit comme telle.
    """
    bloc = re.sub(r'(<div class="atout"[^>]*>\s*)<h[12]([^>]*)>(.*?)</h[12]>',
                  lambda m: '%s<h3%s>%s</h3>' % (m.group(1), m.group(2), m.group(3)),
                  bloc, flags=re.S)
    bloc = re.sub(r'<h([34])\b[^>]*>[^<]*</h\1>\s*(?=<h[1-3]\b)', '', bloc)
    bloc = re.sub(r'<p(?![^>]*class="(?:atelier|prov|eyebrow|lede)")[^>]*>\s*'
                  r'(&quot;|"|«)(.{10,300}?)(&quot;|"|»)\s*</p>',
                  lambda m: '<p class="cit">%s%s%s</p>' % (m.group(1), m.group(2), m.group(3)),
                  bloc, flags=re.S)
    return bloc


def sans_paragraphe_repete(h):
    """Un même paragraphe ne se lit pas deux fois dans la page.

    La date de fondation arrivait par deux chemins : la table des réponses
    de Mélanie, qui la pose sous les chiffres, et la page reprise, qui la
    porte aussi dans le bloc « engagement ». Aucun des deux n'a tort ; les
    deux ensemble donnent à lire la même phrase deux fois.

    On ne compare que des paragraphes ENTIERS et longs : deux phrases
    courtes identiques (« Le Caire », une légende) peuvent légitimement se
    répéter. Et on laisse le mur d'avis tranquille — il duplique ses cartes
    exprès, c'est ce qui fait tourner la boucle.
    """
    vus = set()

    def juger(m):
        t = _cle(m.group(1))
        if len(t) < 60:
            return m.group(0)
        if t in vus:
            return ''
        vus.add(t)
        return m.group(0)

    out, i = [], 0
    for m in re.finditer(r'<section\b.*?</section>', h, re.S):
        out.append(h[i:m.start()])
        bloc = m.group(0)
        if 'class="mur' not in bloc:
            bloc = re.sub(r'<p(?![^>]*class=)[^>]*>(.*?)</p>', juger, bloc, flags=re.S)
        out.append(bloc)
        i = m.end()
    out.append(h[i:])
    return ''.join(out)


def mettre_en_page(h):
    """Passe de mise en page, section par section.

    Elle ne touche pas aux mots : elle groupe, elle range, elle habille.
    """
    out, i = [], 0
    for m in re.finditer(r'<section class="pg-sec[^"]*">.*?</section>', h, re.S):
        surtitre = re.search(r'<p class="eyebrow">([^<]*)</p>', m.group(0))
        variante = VARIANTES.get(texte(surtitre.group(1)) if surtitre else '', '')
        out.append(h[i:m.start()])
        out.append(_normaliser_titres(grouper_atouts(m.group(0), variante)))
        i = m.end()
    out.append(h[i:])
    h = ''.join(out)
    # Les autres objets qui arrivent en bloc apparaissent de la même façon.
    for classe in ('chiffres', 'equipe', 'garanties', 'duo', 'carr'):
        h = h.replace('class="%s"' % classe, 'class="%s rev"' % classe)
    return h


def fiche_equipe(prenom, role, bio):
    """Une personne de l'équipe, telle que Mélanie l'a décrite."""
    return ('<article class="pers">'
            '<h3>%s</h3><p class="pers__r">%s</p><p>%s</p>'
            '</article>' % (H.escape(prenom), H.escape(role), H.escape(bio)))


def monter(moule, agence, accueil, chapo=''):
    """Les douze sections, dans l'ordre du marché."""
    del _PRIS[:]
    s = []
    phrase = accroche(agence)

    # 2. En bref. Mélanie a donné l'année et le nombre de voyageurs ; la note
    #    Google, elle, reste au conditionnel dans sa réponse — on affiche donc
    #    le nombre d'avis, qui est publié, et pas une note qu'on ne peut pas
    #    vérifier.
    avis = re.search(r'(\d+)\s+avis Google', agence) or re.search(r'(\d+)\s+avis Google', accueil)
    chiffres = ('<p class="chiffres">'
                '<b>%s <span>voyageurs accompagnés</span></b>'
                '%s</p>'
                % (H.escape(MELANIE['voyageurs']),
                   '<b>%s <span>avis Google</span></b>' % H.escape(avis.group(1)) if avis else ''))
    # Le chapô du hero disait DÉJÀ cette phrase, à trois cents pixels de
    # là : la reprendre en tête de « En bref » donnait à lire deux fois le
    # même paragraphe. On ne la retire que si le hero la porte vraiment —
    # sinon elle disparaîtrait de la page, et c'est la seule phrase qui dit
    # ce qu'est l'agence.
    lede = ('<p class="lede">%s</p>' % H.escape(phrase)
            if phrase and texte(phrase) != texte(chapo) else '')
    s.append(section('En bref', 'L’agence en quelques repères',
                     lede + chiffres
                     + '<p>%s</p>' % H.escape(MELANIE['fondation'])
                     + a_remplir('note')))

    # 3. L'histoire, telle qu'elle est écrite, avec sa date.
    hist = bloc_apres(agence, 'Notre histoire', bornes=ANCRES)
    if hist:
        # La date de fondation est déjà donnée en tête, sous les chiffres :
        # la répéter ici la faisait lire deux fois à trois cents pixels
        # d'intervalle, et une troisième fois en fin de section.
        s.append(section('Notre histoire', 'Une aventure née d’un regard curieux',
                         duo(hist, PHOTO_HISTOIRE), fond=True))

    # 4. Les trois piliers, rapatriés de l'accueil où ils sont déjà rédigés.
    piliers = bloc_apres(accueil, 'Privées')
    if piliers:
        s.append(section('Notre approche', 'Ce qui fait un voyage avec nous',
                         piliers + source('https://authentiquegypte.com/',
                                          'la page d’accueil du site')))

    # 4bis. Les photos. La page n'en portait qu'une, celle du hero : dix
    #       sections de prose d'affilée, sur un métier qui se vend par
    #       l'image. Elles viennent toutes de la médiathèque de l'agence.
    s.append(carrousel())

    # 5. L'équipe. C'était le manque le plus net face au marché — quatre
    #    agences et demie sur sept montrent des visages et des noms. Mélanie a
    #    donné les deux siens, leur rôle et leur parcours.
    eq = bloc_apres(agence, 'Une équipe locale engagée', bornes=ANCRES)
    fiches = ('<div class="equipe">%s</div>'
              % ''.join(fiche_equipe(*x) for x in MELANIE['equipe']))
    s.append(section('Qui vous répond', 'Notre équipe',
                     eq + fiches + '<p>%s</p>' % H.escape(MELANIE['equipe_note']),
                     fond=True))

    # 6. La méthode. Rare sur le marché — une agence et demie sur sept.
    meth = bloc_apres(agence, 'Contact initial', bornes=ANCRES)
    if meth:
        s.append(section('Comment ça se passe', 'De votre premier message au départ',
                         meth + a_remplir('delai')))

    # 7. Les engagements, sur le fond doré du site — Mélanie l'a demandé.
    eng = bloc_apres(agence, 'Des voyages flexibles', bornes=ANCRES)
    if eng:
        s.append(section('Nos engagements', 'Un voyage local, souple et respectueux',
                         eng + a_remplir('tarif'), fond='creme'))

    # 8. Les garanties. Uniquement ce qui est publié aux mentions légales.
    # « Notre engagement envers vous » parle du statut juridique, des
    # garanties et de la sécurité des paiements : il était jusqu'ici avalé
    # par la section « histoire », où il ne voulait rien dire.
    engagement = bloc_apres(agence, 'Notre engagement envers vous', bornes=ANCRES)
    juridique = (engagement + '<ul class="garanties">'
                 '<li><b>Authentique Égypte (OREYA)</b></li>'
                 '<li>SIRET&nbsp;: %s</li>'
                 '<li>Siège social&nbsp;: %s</li></ul>%s'
                 % (H.escape(SIRET), H.escape(SIEGE),
                    source(MENTIONS, 'les mentions légales du site')))
    s.append(section('Garanties', 'Qui nous sommes, juridiquement',
                     juridique + a_remplir('licence') + a_remplir('garanties')
                     + a_remplir('bureau')))

    # 10. La presse : l'atout que personne d'autre n'a. Elle remonte.
    presse = bloc_apres(agence, 'Le Figaro', bornes=ANCRES)
    if presse:
        s.append(section('Ils parlent de nous', 'La presse et les plateformes', presse))

    # 11. La FAQ de la page, 12. les avis et l'appel au projet, pris au moule
    #     qui les porte déjà dans la forme validée.
    faq = bloc_apres(agence, 'FAQ - Questions', bornes=ANCRES)
    if faq:
        s.append(section('Avant de nous écrire', 'Les questions qu’on nous pose',
                         faq, fond=True))
    for debut in ('Ce que disent', 'Ce séjour vous tente'):
        bloc = moule.section_par_h2(debut)
        if not bloc:
            continue
        # Le moule conclut sur « Ce séjour vous tente ? » : il n'y a pas de
        # séjour sur une page agence.
        bloc = re.sub(r'(<h2[^>]*>)Ce séjour vous tente[^<]*(</h2>)',
                      lambda m: '%sParlons de votre projet.%s' % (m.group(1), m.group(2)),
                      bloc)
        s.append(bloc)
    return s


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--moule', required=True)
    p.add_argument('--site', required=True)
    p.add_argument('--sortie', required=True)
    p.add_argument('--essai', action='store_true')
    a = p.parse_args()

    src = os.path.abspath(a.site)
    moule = _circ.Moule(os.path.abspath(a.moule))
    with open(os.path.join(src, 'agence-qui-sommes-nous.html'), encoding='utf-8') as f:
        agence = f.read()
    accueil = ''
    for nom in os.listdir(src):
        if nom.startswith('accueil-'):
            with open(os.path.join(src, nom), encoding='utf-8') as f:
                accueil = f.read()

    page = _circ.lire_page(agence)
    tete = _circ.poser_tete(moule.tete, page, 'Agence')
    corps = monter(moule, agence, accueil, page.get('chapo', ''))
    tete = tete.replace('</head>', FEUILLE_AGENCE + '</head>', 1)
    h = _bleu.unifier(tete + ''.join(corps) + moule.pied)
    h = sans_paragraphe_repete(mettre_en_page(h))
    h = h.replace('</body>', SCRIPT_AGENCE + '</body>', 1)
    h = poser_schema(h)

    manquants = len(re.findall(r'class="aremplir"', h))
    print('→ %d section(s) montées, %d emplacement(s) « à remplir »' % (len(corps), manquants))
    for cle, quoi in A_REMPLIR.items():
        print('   %-11s %s' % (cle, quoi))
    print('\nAucune garantie affichée sans preuve : ni Atout France, ni APST, ni RCP,')
    print('ni numéro de licence — tant que l’agence ne les a pas confirmés.')
    if not a.essai:
        os.makedirs(a.sortie, exist_ok=True)
        with open(os.path.join(a.sortie, 'agence-qui-sommes-nous.html'), 'w',
                  encoding='utf-8') as f:
            f.write(h)
        print('\nécrit %s (%d octets)' % (a.sortie, len(h)))


if __name__ == '__main__':
    main()
