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
    return ('<p class="prov">Repris de <a href="%s" target="_blank" rel="noopener">%s</a>.</p>'
            % (url, H.escape(quoi)))


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


def section(surtitre, titre, corps, fond=False):
    # « creme » est le fond doré de la charte : Mélanie l'a demandé pour les
    # engagements, fil #8511. « True » reste le gris clair d'alternance.
    variante = {'creme': ' pg-sec--creme', True: ' pg-sec--fond'}.get(fond, '')
    return ('<section class="pg-sec%s"><div class="wrap">'
            '<p class="eyebrow">%s</p><h2>%s</h2>%s</div></section>'
            % (variante, H.escape(surtitre), H.escape(titre), corps))


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
ANCRES = ('Notre histoire', 'Une équipe locale engagée', 'Contact initial',
          'Des voyages flexibles', 'Le Figaro', 'FAQ - Questions')


# Les fiches de l'équipe n'existaient pas dans la charte : elles suivent la
# forme des cartes du site — fond blanc, filet, même rayon — pour ne pas
# introduire un objet de plus.
FEUILLE_EQUIPE = (
    '<style data-agence="equipe">'
    '.equipe{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));'
    'gap:20px;margin:26px 0 0}'
    '.pers{background:#fff;border:1px solid var(--ligne);border-radius:var(--r-l);'
    'padding:22px}'
    '.pers h3{margin:0 0 4px;font-size:1.08rem;color:var(--nuit-900)}'
    '.pers__r{margin:0 0 10px;font-family:"Manrope",sans-serif;font-size:14px;'
    'font-weight:700;letter-spacing:.04em;text-transform:uppercase;color:#116676}'
    '.pers p{margin:0;color:var(--texte);line-height:1.65}'
    '</style>')


def fiche_equipe(prenom, role, bio):
    """Une personne de l'équipe, telle que Mélanie l'a décrite."""
    return ('<article class="pers">'
            '<h3>%s</h3><p class="pers__r">%s</p><p>%s</p>'
            '</article>' % (H.escape(prenom), H.escape(role), H.escape(bio)))


def monter(moule, agence, accueil):
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
    s.append(section('En bref', 'L’agence en quelques repères',
                     ('<p class="lede">%s</p>' % H.escape(phrase) if phrase else '')
                     + chiffres
                     + '<p>%s</p>' % H.escape(MELANIE['fondation'])
                     + a_remplir('note')))

    # 3. L'histoire, telle qu'elle est écrite, avec sa date.
    hist = bloc_apres(agence, 'Notre histoire', bornes=ANCRES)
    if hist:
        s.append(section('Notre histoire', 'Une aventure née d’un regard curieux',
                         hist + '<p>%s</p>' % H.escape(MELANIE['fondation']), fond=True))

    # 4. Les trois piliers, rapatriés de l'accueil où ils sont déjà rédigés.
    piliers = bloc_apres(accueil, 'Privées')
    if piliers:
        s.append(section('Notre approche', 'Ce qui fait un voyage avec nous',
                         piliers + source('https://authentiquegypte.com/',
                                          'la page d’accueil du site')))

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
    juridique = ('<ul class="garanties">'
                 '<li><b>Authentique Égypte (OREYA)</b></li>'
                 '<li>SIRET&nbsp;: %s</li>'
                 '<li>Siège social&nbsp;: %s</li></ul>%s'
                 % (H.escape(SIRET), H.escape(SIEGE),
                    source(MENTIONS, 'les mentions légales du site')))
    s.append(section('Garanties', 'Qui nous sommes, juridiquement',
                     juridique + a_remplir('licence') + a_remplir('garanties')))

    # 9. Les bureaux.
    s.append(section('Où nous trouver', 'Nos bureaux', a_remplir('bureau'), fond=True))

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
    corps = monter(moule, agence, accueil)
    tete = tete.replace('</head>', FEUILLE_EQUIPE + '</head>', 1)
    h = _bleu.unifier(tete + ''.join(corps) + moule.pied)

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
