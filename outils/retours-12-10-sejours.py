#!/usr/bin/env python3
"""Les pages de séjour, sur les commentaires de Mélanie du 12 octobre.

    WP_AUTH='compte:mdp' python3 outils/retours-12-10-sejours.py --essai
    WP_AUTH='compte:mdp' python3 outils/retours-12-10-sejours.py --appliquer [--seul 1168]

CE QUI VAUT POUR LES TREIZE SÉJOURS — demandé sur une page ou plusieurs,
mais c'est le même gabarit partout :

  - la ligne sous les boutons du haut (« Devis gratuit… » et ses deux
    pictogrammes) est retirée : 13010-13012, 13042-13044, 13064-13066,
    13094-13096, 13136-13138 ;
  - « Avant de boucler le sac » (les équipements) et « Le bon format »
    (combien de temps prévoir) sont retirés : 13032, 13038, 13050, 13055,
    13059, 13077, 13130 ;
  - le premier paragraphe n'est plus en gras ; seuls les lieux qu'il cite
    le sont (13002, 13013, 13048, 13062, 13101) ;
  - la section « Qui vous accompagne » reçoit deux boutons : personnaliser
    le séjour, nous écrire sur WhatsApp (13025, 13131) ;
  - pendant la relecture (mode commentaire de l'extension), toutes les
    questions de la FAQ sont dépliées : l'extension capte les clics, le
    bouton « Voir les autres questions » ne pouvait donc pas s'ouvrir
    (12940, 13028).

Puis, séjour par séjour, les corrections de contenu qu'elle a dictées —
repas, étapes, inclus, FAQ, photos. Les prix et les durées sont alignés
sur tout le site par un outil à part (prix-durees-1210.py), parce qu'ils
paraissent aussi sur les cartes des autres pages.
"""

import argparse
import importlib.util
import os
import re
import sys
import time

import requests

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
import jours as J  # noqa: E402

spec = importlib.util.spec_from_file_location('faqr', os.path.join(ICI, 'faq-reparee.py'))
FAQR = importlib.util.module_from_spec(spec)
spec.loader.exec_module(FAQR)

SITE = 'https://authentiquegypte.com'
UP = SITE + '/wp-content/uploads/'
WA = 'https://wa.me/201066619098'

STYLE = (
    '<style data-retours="12-10-sejours">'
    # Le premier paragraphe était en demi-gras sur toute sa longueur.
    '.elementor-template-canvas .pg .prose__tete.prose__tete{font-weight:400}'
    '.elementor-template-canvas .pg .prose__tete b{font-weight:700}'
    '.elementor-template-canvas .pg .guide__act{display:flex;flex-wrap:wrap;gap:12px;margin:24px 0 0}'
    # Relecture : l'extension capte les clics, on déplie tout pour elle.
    'body.aec-mode section[data-plie] .faq__rub{display:grid!important}'
    'body.aec-mode section[data-plie] .faq__q--plus{display:block!important}'
    'body.aec-mode .faq__plus{display:none!important}'
    '</style>')

LIEUX_GRAS = ['pyramides de Gizeh', 'Grand Musée égyptien', 'Abou Simbel', 'Abu Simbel',
              'Louxor', 'Assouan', 'Karnak', 'Philae', 'Kom Ombo', 'Edfou', 'Nil',
              'mer Rouge', 'Mer Rouge', 'Hurghada', 'Siwa', 'désert blanc', 'Désert Blanc',
              'désert noir', 'Bahariya', 'Fayoum', 'Wadi El Rayan', 'Wadi Al-Hitan',
              'mont Sinaï', 'Mont Sinaï', 'mont Moïse', 'Sainte-Catherine', 'Dahab',
              'Le Caire', 'lac Nasser', 'Lac Nasser', 'Nubie', 'vallée des Rois']


class Journal(list):
    def note(self, quoi, ok=True):
        self.append(('' if ok else '✗ ') + quoi)


# ================================================================ communs
def communs(h, j):
    n = len(re.findall(r'<p class="hero__conf">.*?</p>', h, re.S))
    h = re.sub(r'<p class="hero__conf">.*?</p>', '', h, flags=re.S)
    if n:
        j.note('ligne « Devis gratuit » retirée')
    for eb in ('Avant de boucler le sac', 'Le bon format'):
        h, ok = J.retirer_section(h, eb)
        if ok:
            j.note('« %s » retiré' % eb)
    # gras : les lieux du premier paragraphe, trois au plus
    m = re.search(r'<p class="prose__tete">(.*?)</p>', h, re.S)
    if m and '<b>' not in m.group(1):
        t, mis = m.group(1), 0
        for lieu in LIEUX_GRAS:
            if mis >= 3:
                break
            k = re.search(r'(?<![\w>])%s(?![\w<])' % re.escape(lieu), t)
            if k:
                t = t[:k.start()] + '<b>' + lieu + '</b>' + t[k.end():]
                mis += 1
        h = h[:m.start(1)] + t + h[m.end(1):]
        j.note('premier paragraphe : %d lieu(x) en gras' % mis)
    if 'guide__act' not in h and '<p class="guide__intro">' in h:
        h = re.sub(r'(<p class="guide__intro">.*?</p>)',
                   r'\1<p class="guide__act"><a class="btn btn--or" href="%s/sur-mesure/">'
                   r'Personnaliser ce séjour</a><a class="btn btn--verre" href="%s">'
                   r'Nous écrire sur WhatsApp</a></p>' % (SITE, WA), h, count=1, flags=re.S)
        j.note('boutons de contact sous « Qui vous accompagne »')
    if 'data-retours="12-10-sejours"' not in h:
        i = h.find('<main')
        i = h.find('>', i) + 1
        h = h[:i] + STYLE + h[i:]
    return h


# ================================================================ outils
def inclus_ajout(h, texte_li, j):
    i = h.find('<div class="incl__col incl__col--oui">')
    k = h.find('</ul>', i)
    if i < 0 or k < 0:
        j.note('inclus introuvables', False)
        return h
    if texte_li in h[i:k]:
        return h
    svg = re.search(r'<li>(<svg.*?</svg>)<span>', h[i:k], re.S).group(1)
    h = h[:k] + '<li>%s<span>%s</span></li>' % (svg, texte_li) + h[k:]
    j.note('inclus : « %s »' % texte_li)
    return h


def inclus_remplacer(h, avant, apres, j):
    i = h.find('<div class="incl__col incl__col--oui">')
    k = h.find('</ul>', i)
    zone = h[i:k]
    if '<span>%s</span>' % avant not in zone:
        j.note('inclus « %s » introuvable' % avant, False)
        return h
    h = h[:i] + zone.replace('<span>%s</span>' % avant, '<span>%s</span>' % apres, 1) + h[k:]
    j.note('inclus : « %s » → « %s »' % (avant, apres))
    return h


def guide_ligne(h, avant, apres, j):
    """Les lignes de la section « Qui vous accompagne »."""
    a = h.find('<ul class="guide__r">')
    b = h.find('</ul>', a)
    if a < 0 or '<span>%s</span>' % avant not in h[a:b]:
        j.note('« %s » introuvable dans Qui vous accompagne' % avant, False)
        return h
    h = h[:a] + h[a:b].replace('<span>%s</span>' % avant, '<span>%s</span>' % apres, 1) + h[b:]
    j.note('Qui vous accompagne : « %s »' % apres)
    return h


def galerie(h):
    a, b = J.bornes(h, '<section class="galerie"', 'section')
    return a, b, re.findall(r'<a data-lb .*?</a>', h[a:b], re.S)


def galerie_retirer(h, rangs, j):
    a, b, items = galerie(h)
    garde = [x for n, x in enumerate(items, 1) if n not in rangs]
    tete = re.match(r'<section[^>]*>', h[a:b]).group(0)
    if not garde:
        j.note('galerie retirée (toutes ses photos)')
        return h[:a] + h[b:]
    j.note('galerie : photo(s) %s retirée(s)' % ', '.join(map(str, sorted(rangs))))
    return h[:a] + tete + ''.join(garde) + '</section>' + h[b:]


def vignette(fichier, alt, l, ht, tailles=()):
    src = UP + fichier
    base, ext = os.path.splitext(src.replace('-scaled', ''))
    ss = ', '.join('%s-%s%s %sw' % (base, t, ext, t.split('x')[0]) for t in tailles)
    return ('<a data-lb href="%s" data-alt="%s"><img src="%s" alt="%s" decoding="async"%s '
            'sizes="(max-width:860px) 45vw, 370px" width="%d" height="%d" loading="lazy"></a>'
            % (src, alt, src, alt, ' srcset="%s"' % ss if ss else '', l, ht))


def galerie_remplacer(h, rang, nouvelle, j):
    a, b, items = galerie(h)
    vieux = items[rang - 1]
    j.note('galerie : photo %d remplacée' % rang)
    return h[:a] + h[a:b].replace(vieux, nouvelle, 1) + h[b:]


def faq_retirer(h, questions, j):
    for q in questions:
        m = re.search(r'<details class="faq__q[^"]*"><summary>%s</summary>' % re.escape(q), h)
        if not m:
            j.note('FAQ « %s » introuvable' % q, False)
            continue
        f = h.find('</details>', m.end()) + len('</details>')
        h = h[:m.start()] + h[f:]
        j.note('FAQ : « %s » retirée' % q)
    return h


def faq_ajouter(h, paires, j):
    i = h.find('<div class="faq__rub">')
    k = h.find('</p>', i) + 4
    ajout = ''.join('<details class="faq__q"><summary>%s</summary><div class="faq__r">%s</div></details>'
                    % (q, r) for q, r in paires)
    j.note('FAQ : %d question(s) ajoutée(s)' % len(paires))
    return h[:k] + ajout + h[k:]


def faq_reponse(h, question, nouvelle, j):
    m = re.search(r'<summary>%s</summary><div class="faq__r">' % re.escape(question), h)
    if not m:
        j.note('FAQ « %s » introuvable' % question, False)
        return h
    f = FAQR.fin_div(h, m.end() - len('<div class="faq__r">'))
    h = h[:m.end()] + nouvelle + h[f - len('</div>'):]
    j.note('FAQ : réponse « %s » reprise' % question)
    return h


def faq_replier(h, j):
    h, info = FAQR.corriger(h)
    if info:
        j.note('FAQ repliée : %(questions)d questions, %(rubriques)s' % info)
    return h


def remplacer(h, avant, apres, j, quoi, n=1):
    k = h.count(avant)
    if not k:
        j.note('%s : introuvable' % quoi, False)
        return h
    j.note(quoi)
    return h.replace(avant, apres, n if n else k)


# ================================================================ séjours
def pyramides_nil(h, j):                                          # 1168
    h = J.points(h, 1, ['Accueil à l’aéroport du Caire par notre représentant. Transfert à votre hôtel aux Pyramides.',
                        'Nuit à l’hôtel.'])
    h = J.pastilles(h, 1, ['Hôtel'])
    j.note('J1 : dîner retiré (13015, 13016)')
    h = J.titre(h, 2, 'Pyramides de <b>Gizeh</b> et <b>nouveau Musée égyptien</b>')
    h = J.sous_titre(h, 2, 'Découverte des pyramides de <b>Gizeh</b> et du <b>nouveau Musée égyptien</b>')
    h = J.points(h, 2, ['Commencez votre journée par une visite des pyramides de <b>Gizeh</b>, incluant la Grande '
                        'Pyramide de Khéops, la pyramide de Khéphren, la pyramide de Mykérinos et le <b>Sphinx</b>. '
                        'Ensuite, visitez le <b>nouveau Musée égyptien</b> (GEM).',
                        'Transfert à l’aéroport avec votre représentant. Vol interne pour <b>Assouan</b>. '
                        'Accueil et transfert à votre hôtel.'])
    h = J.pastilles(h, 2, ['Hôtel', 'Petit-déjeuner', 'Déjeuner'])
    j.note('J2 : petit-déjeuner et déjeuner, le nouveau Musée égyptien en gras (13017)')
    h = J.titre(h, 3, 'Temple de <b>Philae</b> et route vers <b>Abou Simbel</b>')
    h = J.sous_titre(h, 3, 'Temple de <b>Philae</b>, puis route vers <b>Abou Simbel</b>')
    h = J.points(h, 3, ['Visite du temple de <b>Philae</b>, puis route pour <b>Abou Simbel</b> (3h30 de route).',
                        'option: Spectacle son et lumière aux temples d’<b>Abou Simbel</b>.'])
    h = J.pastilles(h, 3, ['Hôtel', 'Petit-déjeuner'])
    j.note('J3 : Philae puis Abou Simbel, son et lumière en option (13018)')
    h = J.titre(h, 4, 'Temples d’<b>Abou Simbel</b> et embarquement')
    h = J.points(h, 4, ['Visite des temples d’<b>Abou Simbel</b>.',
                        'Retour sur <b>Assouan</b> (3h30 de route) et embarquement sur le bateau.',
                        'Navigation et visite du temple de <b>Kom Ombo</b>.',
                        'Nuit à bord du bateau.'])
    for n in (4, 5, 6):
        h = J.pastilles(h, n, ['Bateau de croisière 5*', 'Tout inclus à bord, sauf boissons'])
    j.note('J4 : Abou Simbel, retour à Assouan, embarquement, Kom Ombo (13019) ; '
           'à bord : tout inclus sauf boissons (13020)')
    h = inclus_ajout(h, 'Le vol interne', j)                                    # 13024
    h = galerie_remplacer(h, 4, vignette('2023/11/pyramides-scaled.jpg', 'Les pyramides de Gizeh',
                                         2560, 1707, ('300x200', '768x512', '1024x683')), j)  # 13014
    h = remplacer(h, 'Les bateaux offrent des cabines confortables, des repas soignés, et des espaces communs conviviaux.',
                  'Les bateaux offrent des cabines confortables, une piscine à bord, des repas sous forme de buffet '
                  'pour un large choix, et des animations le soir : spectacle de danse, tour de magie.',
                  j, 'FAQ : buffet, piscine, animations (13026)')
    m = re.search(r'(<summary>Ce séjour convient-il aux familles et aux couples \?</summary><div class="faq__r"><p>)(.*?)(</p>)', h, re.S)
    if m and 'piscine' not in m.group(2):
        h = h[:m.end(2)] + ' À bord, la pension est complète, avec une piscine et des animations le soir.' + h[m.end(2):]
        j.note('FAQ familles : pension complète, piscine, animations (13027)')
    return h


def mer_rouge(h, j):                                              # 540
    h = pyramides_jours_communs(h, j)
    h = J.titre(h, 3, 'Découverte d’<b>Assouan</b>')
    h = J.sous_titre(h, 3, 'Découverte d’<b>Assouan</b>')
    h = J.points(h, 3, ['Visite du temple d’Isis : le temple de <b>Philae</b>.',
                        'Déjeuner, puis visite du monastère de Saint-Siméon à dos de dromadaire.',
                        'Embarquement sur le bateau. Nuit à bord.'])
    h = J.pastilles(h, 3, ['Bateau de croisière 5*', 'Petit-déjeuner', 'Déjeuner', 'Dîner'], hebergement=None)
    j.note('J3 : Abou Simbel remplacé par la découverte d’Assouan (13081, 13082)')
    h = J.titre(h, 4, 'Matinée libre et navigation vers <b>Kom Ombo</b>')
    h = J.points(h, 4, ['Matinée libre à <b>Assouan</b>.',
                        'Navigation vers <b>Kom Ombo</b> avec déjeuner à bord. Arrivée en fin de journée.'])
    h = J.pastilles(h, 4, ['Bateau de croisière 5*', 'Petit-déjeuner', 'Déjeuner', 'Dîner'])
    j.note('J4 : matinée libre au lieu de Philae, trois repas (13083, 13084)')
    pts = J.lire_points(h, 5)
    h = J.points(h, 5, pts + ['En fin de journée, navigation jusqu’au temple d’<b>Edfou</b>.'])
    h = J.pastilles(h, 5, ['Bateau de croisière 5*', 'Petit-déjeuner', 'Déjeuner', 'Dîner'])
    j.note('J5 : trois repas, navigation jusqu’à Edfou (13085, 13086)')
    h = J.titre(h, 6, '<b>Edfou</b>, temples de <b>Louxor</b> et <b>Karnak</b>')
    h = J.sous_titre(h, 6, 'Temple d’<b>Edfou</b>, puis <b>Louxor</b> et <b>Karnak</b>')
    h = J.points(h, 6, ['Visite du temple d’<b>Edfou</b>, puis navigation jusqu’à <b>Louxor</b>.',
                        'Découverte du temple de <b>Louxor</b>, puis du temple de <b>Karnak</b>.',
                        'option: Le soir, spectacle son et lumière au temple de <b>Karnak</b>.'])
    h = J.pastilles(h, 6, ['Bateau de croisière 5*', 'Petit-déjeuner', 'Déjeuner', 'Dîner'])
    j.note('J6 : Edfou et navigation jusqu’à Louxor, montgolfière retirée (13087)')
    h = J.titre(h, 7, 'Vallée des Rois et route vers la mer Rouge')
    h = J.points(h, 7, ['option: Tôt le matin, vol en montgolfière au-dessus de la rive ouest.',
                        'Visite de la vallée des Rois et du temple d’Hatchepsout.',
                        'Transfert vers la mer Rouge et installation à votre hôtel à <b>Hurghada</b>.'])
    h = J.pastilles(h, 7, ['Hôtel 5* à Hurghada', 'Petit-déjeuner'])
    j.note('J7 : montgolfière en option, vallée des Rois, Hatchepsout, transfert (13088)')
    h = J.ajouter_jour(h, 'Transfert à l’aéroport de <b>Hurghada</b>',
                       ['Petit-déjeuner, puis transfert à l’aéroport de <b>Hurghada</b> pour votre vol de retour.'],
                       ['Petit-déjeuner'], 'hurghada')
    j.note('J9 ajouté : transfert à l’aéroport, petit-déjeuner (13089)')
    h = inclus_ajout(h, 'Le vol interne', j)                                    # 13090
    h = galerie_retirer(h, {4, 5}, j)                                           # 13072, 13073
    # La FAQ : les questions qu'elle a dictées remplacent celles de la plongée (13091-13093).
    h = faq_retirer(h, ['Quand partir en Mer Rouge ?', 'Snorkeling ou plongée bouteille ?', 'Où poser sa base ?',
                        'Comment respecter les récifs pendant le snorkeling ?', 'Quel niveau / encadrement prévoir ?',
                        'Le snorkeling convient-il aux familles, et quelles précautions prendre ?',
                        'Est-ce dangereux de venir en Égypte ?', 'Ai-je besoin d’un visa pour voyager en Égypte ?',
                        'Dois-je faire des vaccins ?'], j)
    h = faq_ajouter(h, [
        ('Quels sont les jours de départ des croisières ?',
         '<p>Les croisières partent le <b>lundi, le mercredi et le vendredi</b>.</p>'),
        ('L’itinéraire est-il adapté aux enfants ?',
         '<p>Oui, l’itinéraire est adapté à <b>tous les âges</b>.</p>'),
        ('Avons-nous un guide pendant la croisière ?',
         '<p>Oui : vous avez un <b>guide privé pendant toute la croisière</b>.</p>'),
        ('Peut-on prévoir des sièges auto ou des lits bébé ?',
         '<p>Oui, il est possible d’ajouter des <b>sièges auto</b> ou des <b>lits bébé</b> pour les enfants.</p>'),
        ('Peut-on avoir une chambre familiale ?',
         '<p>Oui. À l’hôtel, une <b>chambre familiale</b> est possible. À bord du bateau, une <b>suite familiale</b> '
         'ou <b>deux cabines communicantes</b>, côte à côte, selon les disponibilités.</p>'),
        ('Faut-il des vaccins pour ce voyage ?',
         '<p><b>Aucun vaccin</b> n’est obligatoire pour ce voyage.</p>'),
        ('Faut-il un visa ?',
         '<p>Oui : un <b>visa de 30 €</b>, pour les adultes comme pour les enfants. Il se prend '
         '<b>sur place, à l’arrivée</b>.</p>'),
        ('Est-ce sûr de voyager avec des enfants ?',
         '<p>Oui. Les sites visités, et les zones qui les entourent, ne présentent <b>aucun problème de '
         'sécurité</b>.</p>'),
    ], j)
    h = faq_replier(h, j)
    # Ce n'est pas un séjour « Mer rouge et plongée », c'est un voyage en famille (13097, 13098).
    h = re.sub(r'<span class="pill"><svg(?:(?!</svg>).)*</svg>Mer rouge et plongée</span>', '', h, flags=re.S)
    h = h.replace('href="%s/nos-sejours-egypte/mer-rouge/">Mer rouge et plongée</a>' % SITE,
                  'href="%s/voyage-en-famille-en-egypte/">Voyage en famille</a>' % SITE)
    h = h.replace('"name": "Mer rouge et plongée", "item": "%s/nos-sejours-egypte/mer-rouge/"' % SITE,
                  '"name": "Voyage en famille", "item": "%s/voyage-en-famille-en-egypte/"' % SITE)
    j.note('rangé en « Voyage en famille », plus en « Mer rouge et plongée » (13097, 13098)')
    return h


def pyramides_jours_communs(h, j):
    """J1 et J2, identiques sur les deux séjours de croisière."""
    h = J.points(h, 1, ['Accueil à l’aéroport du Caire par notre représentant. Transfert à votre hôtel aux Pyramides.',
                        'Nuit à l’hôtel.'])
    h = J.pastilles(h, 1, ['Hôtel'])
    j.note('J1 : pas de dîner (13078, 13079)')
    h = J.titre(h, 2, 'Pyramides de <b>Gizeh</b> et <b>nouveau Musée égyptien</b>')
    h = J.sous_titre(h, 2, 'Découverte des pyramides de <b>Gizeh</b> et du <b>nouveau Musée égyptien</b>')
    h = J.points(h, 2, ['Commencez votre journée par une visite des pyramides de <b>Gizeh</b>, incluant la Grande '
                        'Pyramide de Khéops, la pyramide de Khéphren, la pyramide de Mykérinos et le <b>Sphinx</b>. '
                        'Ensuite, visitez le <b>nouveau Musée égyptien</b> (GEM).',
                        'Transfert à l’aéroport avec votre représentant. Vol interne pour <b>Assouan</b>. '
                        'Accueil et transfert à votre hôtel.'])
    h = J.pastilles(h, 2, ['Hôtel', 'Petit-déjeuner', 'Déjeuner'])
    j.note('J2 : petit-déjeuner et déjeuner (13080)')
    return h


def roadtrip(h, j):                                               # 1369
    h = J.points(h, 1, [p for p in J.lire_points(h, 1) if 'spectacle son et lumières' not in p])
    j.note('J1 : son et lumière retiré (13103)')
    h = J.titre(h, 2, 'Découverte des pyramides de <b>Gizeh</b> et du <b>nouveau Musée égyptien</b>')
    h = J.points(h, 2, ['Commencez votre journée par une visite des pyramides de <b>Gizeh</b>, incluant la Grande '
                        'Pyramide de Khéops, la pyramide de Khéphren, la pyramide de Mykérinos et le <b>Sphinx</b>.',
                        'Ensuite, visitez le <b>nouveau Musée égyptien</b> (GEM), qui réunit les trésors de l’ancienne '
                        'Égypte, dont ceux de Toutankhamon.',
                        'Transfert à l’aéroport avec votre représentant. Vol interne pour <b>Assouan</b>. '
                        'Accueil et transfert à votre hôtel.'])
    j.note('J2 : le nouveau Musée égyptien (13104)')
    h = J.points(h, 3, J.lire_points(h, 3) + ['option: Felouque sur le Nil pour découvrir les villages nubiens.'])
    h = J.pastilles(h, 3, ['Hôtel', 'Petit-déjeuner', 'Déjeuner'])
    j.note('J3 : felouque en option, petit-déjeuner et déjeuner (13105, 13107, 13108)')
    h = J.points(h, 4, [p for p in J.lire_points(h, 4) if J.texte(p) != 'Route pour Louxor'])
    h = J.pastilles(h, 4, ['Hôtel', 'Petit-déjeuner'])
    j.note('J4 : petit-déjeuner (13106)')
    h = J.pastilles(h, 5, ['Hôtel', 'Petit-déjeuner'])
    j.note('J5 : petit-déjeuner (13109)')
    h = J.pastilles(h, 6, ['Hôtel', 'Petit-déjeuner'])
    j.note('J6 : petit-déjeuner (13111)')
    pts = [p for p in J.lire_points(h, 7) if J.texte(p) != 'Plage de Hurghada']
    pts = [('Route pour <b>Hurghada</b> (4h30 de route).' if J.texte(p) == 'Route pour Hurghada' else p) for p in pts]
    h = J.points(h, 7, pts)
    h = J.pastilles(h, 7, ['Hôtel', 'Petit-déjeuner', 'Dîner'])
    j.note('J7 : « Plage de Hurghada » retiré, 4h30 de route, petit-déjeuner et dîner (13110, 13112)')
    h = J.pastilles(h, 8, ['Hôtel', 'Pension complète'])
    j.note('J8 : pension complète et nuit à l’hôtel au lieu de « Bateau » (13113)')
    h = J.points(h, 9, [p for p in J.lire_points(h, 9)
                        if 'FAQ Le Caire' not in p and 'dernière journée' not in p])
    j.note('J9 : deux lignes retirées (13114, 13115)')
    h = galerie_retirer(h, {1, 2, 3, 4}, j)                                     # 13116-13119
    h = inclus_ajout(h, 'Le vol interne', j)                                    # 13121
    # « Quand partir » : à la fin (13120)
    a, b = J.bornes(h, '<section class="quand">', 'section')
    bloc = h[a:b]
    h = h[:a] + h[b:]
    c, d = J.bornes(h, '<div class="corps">', 'div')
    h = h[:d - len('</div>')] + bloc + h[d - len('</div>'):]
    j.note('« Quand partir » déplacé à la fin (13120)')
    return h


def famille(h, j):                                                # 7336
    h = J.points(h, 1, ['Accueil à l’aéroport du Caire par notre représentant. Transfert à votre hôtel aux Pyramides.',
                        'Nuit à l’hôtel.'])
    h = J.pastilles(h, 1, ['Hôtel'])
    j.note('J1 : pas de dîner (13124)')
    h = J.points(h, 2, J.lire_points(h, 2) + ['Nuit à l’hôtel.'])
    h = J.pastilles(h, 2, ['Hôtel', 'Petit-déjeuner', 'Déjeuner'])
    j.note('J2 : petit-déjeuner, déjeuner, nuit à l’hôtel (13125)')
    pts = J.lire_points(h, 3)
    pts = [('Après-midi libre : balade à vélo, cours de poterie, atelier de hiéroglyphes ou felouque sur le Nil.'
            if 'Après midi libre' in p else p) for p in pts]
    pts.append('option: Tôt le matin, vol en montgolfière au-dessus de la rive ouest.')
    h = J.points(h, 3, pts)
    j.note('J3 : vélo, atelier de hiéroglyphes, montgolfière en option (13126)')
    lieu = 'Hôtel 5* ou hôtel boutique à <b>Hurghada</b> (ou El Gouna, El Quseir, Marsa Alam)'
    for n in (5, 6):
        h = J.pastilles(h, n, ['Hôtel 5* ou hôtel boutique à Hurghada'], hebergement=lieu)
    j.note('J5-J6 : hôtel 5* ou boutique, Hurghada ou El Gouna, El Quseir, Marsa Alam (13127, 13128)')
    h = J.ajouter_jour(h, 'Journée libre à <b>Hurghada</b>',
                       ['Journée libre pour profiter de la mer Rouge et des installations de votre hôtel.'],
                       ['Hôtel 5* ou hôtel boutique à Hurghada', 'Pension complète'], 'hurghada')
    h = J.ajouter_jour(h, 'Transfert à l’aéroport de <b>Hurghada</b>',
                       ['Petit-déjeuner, puis transfert à l’aéroport de <b>Hurghada</b> pour votre vol de retour.'],
                       ['Petit-déjeuner'], 'hurghada')
    j.note('J7 journée libre en pension complète, J8 transfert à l’aéroport (13129)')
    h = inclus_ajout(h, 'Le vol interne', j)
    h = faq_retirer(h, ['Snorkeling ou plongée bouteille ?', 'Où poser sa base ?',
                        'Comment respecter les récifs pendant le snorkeling ?',
                        'Quel niveau / encadrement prévoir ?'], j)          # 13132-13135
    h = faq_replier(h, j)
    return h


SIWA_JOURS = [
    ('Arrivée à <b>Siwa</b>', 'siwa', 'SIWA-JOUR-1.jpeg', (1280, 853), ('300x200', '768x512', '1024x682'),
     ['Arrivée à <b>Siwa</b> et enregistrement à l’hôtel.', 'Petit-déjeuner.',
      'Visite de Gabal Al Mawta, la montagne des morts, et du vieux village de Shali.',
      'Coucher de soleil sur l’île de Fatnas.', 'Dîner et nuit à l’hôtel.'],
     ['Hôtel', 'Petit-déjeuner', 'Dîner']),
    ('Lacs salés et temples de <b>Siwa</b>', 'siwa', 'SIWA-J2-scaled.jpg', (2560, 1707),
     ('300x200', '768x512', '1024x683'),
     ['Petit-déjeuner.', 'Les lacs salés, puis la source de Cléopâtre.',
      'Le temple d’Amon, et le temple d’Alexandre.', 'Dîner et nuit à l’hôtel.'],
     ['Hôtel', 'Petit-déjeuner', 'Dîner']),
    ('La Grande Mer de Sable', 'siwa', 'Siwa_Oasis_sunset_on_Maraqi_Egypt.webp', (1920, 1081), (),
     ['Petit-déjeuner.', 'Gabal Dakrur, puis traversée des dunes de la Grande Mer de Sable.',
      'Les sources chaudes et froides de Bir Wahed, et du sandboarding.',
      'Pause détente face au coucher de soleil.', 'Dîner et nuit sur place.'],
     ['Hôtel', 'Petit-déjeuner', 'Dîner']),
    ('Retour au <b>Caire</b>', 'le-caire', None, None, (),
     ['Petit-déjeuner, puis retour au <b>Caire</b>.'],
     ['Petit-déjeuner']),
]


def siwa(h, j):                                                   # 2393
    # Le jour par jour était celui de Sainte-Catherine, photos comprises (13052).
    a = h.find('<p class="eyebrow">Dans le détail</p>')
    s = h.rfind('<section', 0, a)
    e = s + J.bornes(h[s:], h[s:s + 9], 'section')[1]
    nav = ''.join('<li><span class="jpjs__n">J%d</span><a href="#jour-%d">%s</a></li>' % (n, n, J.texte(t))
                  for n, (t, *_rest) in enumerate(SIWA_JOURS, 1))
    corps = []
    for n, (t, lieu, img, dims, tailles, pts, pas) in enumerate(SIWA_JOURS, 1):
        photo = ''
        if img:
            src = UP + '2025/09/' + img if img.startswith('SIWA') else UP + '2023/11/' + img
            base, ext = os.path.splitext(src)
            ss = ''
            photo = ('<a class="etape__photo" data-lb href="%s" data-alt="Oasis de Siwa" aria-label="Agrandir la '
                     'photo : Oasis de Siwa"><img src="%s" alt="Oasis de Siwa" decoding="async"%s '
                     'sizes="(max-width:1040px) 100vw, 780px" width="%d" height="%d" loading="lazy"></a>'
                     % (src, src, ' srcset="%s"' % ss if ss else '', dims[0], dims[1]))
        corps.append('<div class="jour" id="jour-%d"><div class="jour__tete"><h3>%s</h3><span class="jour__no">'
                     'Jour %d</span></div><article class="etape" id="etape-%d" data-lieu="%s">%s<ul class="etape__pts">'
                     '%s</ul><p class="jico">%s</p></article></div>'
                     % (n, t, n, n, lieu, photo, ''.join(J.li(p) for p in pts),
                        ''.join(J.pastille(x) for x in pas)))
    section = ('<section><p class="eyebrow">Dans le détail</p><h2 id="t-jpj">Le séjour jour par jour</h2>'
               '<nav class="jpjs" aria-label="Les étapes du séjour"><div class="jpjs__t"><p>Les étapes</p>'
               '<a href="#t-carte">Voir la carte de l’itinéraire</a></div><ol class="jpjs__l">%s</ol></nav>%s</section>'
               % (nav, ''.join(corps)))
    h = h[:s] + section + h[e:]
    j.note('jour par jour remplacé par le sien : 4 jours, photos de Siwa (13051, 13052)')
    # l'aperçu « Les étapes de votre séjour » listait aussi Sainte-Catherine
    if '<section class="apercu">' in h:
        a, b = J.bornes(h, '<section class="apercu">', 'section')
        h = h[:a] + h[b:]
        j.note('aperçu des étapes de Sainte-Catherine retiré')
    h = remplacer(h, '<p class="hero__chapo">L&#x27;Oasis de Siwa : Une oasis préservée aux trésors cachés</p>',
                  '<p class="hero__chapo">Aux portes de la Grande Mer de Sable, près de la frontière libyenne, '
                  'Siwa est une oasis de palmiers et de sources. On y visite le temple d’Amon, où Alexandre le '
                  'Grand vint consulter l’oracle, la vieille cité de Shali, les lacs salés et la source de '
                  'Cléopâtre.</p>', j, 'texte de présentation de Siwa (13045)')
    h = re.sub(r'(<p class="prose__tete">.*?</p>)<p>Ce programme de 4 jours à l’oasis de Siwa.*?</p>', r'\1', h,
               count=1, flags=re.S)
    j.note('second paragraphe retiré (13049)')
    h = guide_ligne(h, 'Guide privatif', 'Guide privé bédouin', j)
    h = inclus_remplacer(h, 'Guide privatif', 'Guide privé bédouin', j)          # 13054
    for t in ('<li><strong>En excursion organisée</strong>: la solution la plus simple avec guide et véhicule adapté</li>',
              '<li><strong>En camping</strong>: possibilité de bivouac dans le désert environnant</li>'):
        h = remplacer(h, t, '', j, 'FAQ : « %s » retiré' % J.texte(t)[:30])     # 13056, 13057
    # le même texte, sans balises, dans les données structurées de la FAQ
    h = h.replace(' En excursion organisée : la solution la plus simple avec guide et véhicule adapté', '')
    h = h.replace(' En camping : possibilité de bivouac dans le désert environnant', '')
    h = re.sub(r'<p>(?:<strong>)?À noter(?:</strong>)? ?: Siwa offre aussi des possibilités de camping sous les '
               r'étoiles dans le désert environnant\.</p>', '', h)
    j.note('FAQ : camping sous les étoiles retiré (13058)')
    return h


def desert_blanc(h, j):                                           # 2193
    h = remplacer(h, '<h1>Excursion dans le désert blanc</h1>', '<h1>Excursion dans le désert blanc et noir</h1>',
                  j, 'titre : désert blanc et noir (13061)')
    pts = J.lire_points(h, 2)
    pts = [('L’exploration se termine au coucher du soleil, avant un dîner et une nuit à l’hôtel.'
            if 'nuit magique sous les étoiles' in p else p) for p in pts]
    h = J.points(h, 2, pts)
    h = J.pastilles(h, 2, ['Hôtel', 'Petit-déjeuner', 'Déjeuner', 'Dîner'])
    h = J.sous_titre(h, 3, 'Petit-déjeuner à l’hôtel.')
    h = J.pastilles(h, 3, ['Petit-déjeuner'])
    j.note('J2-J3 : nuit à l’hôtel au lieu du campement (13060, 13036)')
    h = guide_ligne(h, 'Guide privatif', 'Guide privé bédouin', j)
    h = inclus_remplacer(h, 'Guide privatif', 'Guide privé bédouin', j)          # 13063, 13033, 13034
    h = guide_ligne(h, 'Chauffeur privatif dans un véhicule climatisé', 'Chauffeur privatif en 4x4', j)
    h = inclus_remplacer(h, 'Chauffeur privatif dans un véhicule climatisé', 'Chauffeur privatif en 4x4', j)  # 13035
    h = inclus_ajout(h, 'Les hébergements', j)                                  # 13036
    h = re.sub(r'<li><svg(?:(?!</svg>).)*</svg><span>Conseil : Prévoyez au moins une nuit sur place[^<]*</span></li>', '', h,
               flags=re.S)
    return h


def bateau_voile(h, j):                                           # 1408
    pts = J.lire_points(h, 2)
    pts = [('Ensuite, visitez le <b>nouveau Musée égyptien</b> (GEM), qui réunit les trésors de l’ancienne Égypte, '
            'dont ceux de Toutankhamon.' if 'musée égyptien du Caire' in p else p) for p in pts]
    h = J.points(h, 2, pts)
    h = J.titre(h, 2, 'Découverte des pyramides de <b>Gizeh</b> et du <b>nouveau Musée égyptien</b>')
    j.note('J2 : le nouveau Musée égyptien (13004)')
    h = J.titre(h, 3, 'Temple de <b>Karnak</b> et <b>Edfou</b> (chaque lundi et mercredi)')
    j.note('J3 : chaque lundi et mercredi (13005)')
    h = remplacer(h, '<p class="guide__intro">Ce séjour est privatif\xa0: vous ne partagez ni le guide, ni le véhicule.</p>',
                  '<p class="guide__intro">Ce séjour est privatif au Caire, à Assouan et à Louxor : vous ne partagez ni '
                  'le guide, ni le véhicule. Pendant la croisière, vous naviguez avec un petit groupe francophone.</p>',
                  j, 'privatif à terre, petit groupe francophone à bord (13006)')
    h = h.replace('<h2>Votre guide, votre chauffeur, et personne d&#x27;autre</h2>',
                  '<h2>Votre guide, votre chauffeur, et un petit groupe à bord</h2>', 1)
    return h


def sainte_catherine(h, j):                                       # 5109
    a = h.find('id="etape-7"')
    b = h.find('</article>', a)
    zone = h[a:b]
    neuf = re.sub(r'<span class="jico__e"><svg(?:(?!</svg>).)*</svg>Dîner</span>', '', zone, count=1, flags=re.S)
    if neuf != zone:
        j.note('étape 7 : dîner retiré (13070)')
    return h[:a] + neuf + h[b:]


SEJOURS = {
    1168: pyramides_nil, 540: mer_rouge, 1369: roadtrip, 7336: famille,
    2393: siwa, 2193: desert_blanc, 1408: bateau_voile, 5109: sainte_catherine,
    2054: None, 5864: None, 5412: None, 5515: None, 1198: None,
}


def session():
    s = requests.Session()
    s.verify = '/root/.ccr/ca-bundle.crt'
    s.auth = tuple(os.environ['WP_AUTH'].split(':', 1))
    return s


def requete(s, methode, url, **k):
    for essai in range(4):
        try:
            r = s.request(methode, url, timeout=300, **k)
            if r.status_code < 500:
                return r
        except requests.RequestException:
            pass
        time.sleep(2 ** essai)
    raise SystemExit('Le site ne répond pas : ' + url)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--essai', action='store_true')
    p.add_argument('--appliquer', action='store_true')
    p.add_argument('--seul', type=int)
    p.add_argument('--depuis', help='lire les pages dans ce dossier (prog-ID.html) au lieu du site')
    p.add_argument('--vers', help='écrire le résultat dans ce dossier au lieu du site')
    a = p.parse_args()
    s = session()
    for pid, fonction in SEJOURS.items():
        if a.seul and pid != a.seul:
            continue
        url = '%s/wp-json/wp/v2/programs/%d' % (SITE, pid)
        if a.depuis:
            h = open(os.path.join(a.depuis, 'prog-%d.html' % pid), encoding='utf-8').read()
        else:
            h = requete(s, 'GET', url, params={'context': 'edit'}).json()['content']['raw']
        if 'data-retours="12-10-sejours"' in h:
            print('%-5d déjà fait' % pid)
            continue
        j = Journal()
        h = communs(h, j)
        if fonction:
            h = fonction(h, j)
        print('%-5d' % pid)
        for x in j:
            print('      ' + x)
        if a.vers:
            open(os.path.join(a.vers, 'prog-%d.html' % pid), 'w', encoding='utf-8').write(h)
        if a.appliquer:
            if any(x.startswith('✗') for x in j):
                print('      ✗ une étape a échoué : rien n’est écrit pour cette page')
                continue
            print('      écrit :', requete(s, 'POST', url, json={'content': h}).status_code)


if __name__ == '__main__':
    main()
