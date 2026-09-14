#!/usr/bin/env python3
"""
Pose la couche UX/UI validée le 14/09 sur les pages du gabarit « programme ».

    ./outils/gabarit-ux.py --site maquettes/site --sortie maquettes/site-ux \\
        [--inventaire docs/inventaire.json] [--seulement slug,slug]

Ce qui est ajouté à chaque fiche, et d'où vient chaque phrase :

    héros            une ligne de réassurance (devis 48 h, aucune carte
                     bancaire, assistance 24h/24) — FAQ de la page
    panneau devis    les inclus de la fiche, Mélanie, un formulaire à trois
                     champs qui compose un message WhatsApp prérempli, les
                     garanties, le lien vers la fiche Google, le partage
    navigation       les ancres des sections réellement présentes
    étapes           un picto par type d'étape (arrivée, route, lever, visite)
    carte            un point de la carte ouvre la journée correspondante
    tarif            paiement, annulation et « pourquoi ce prix » — FAQ
    quand partir     les douze mois, températures et affluence relevées sur
                     authentiquegypte.com/quand-partir-en-egypte, et la
                     recommandation du type de séjour de la fiche
    agence           le portrait de Mélanie et sa citation — qui-sommes-nous —
                     puis les titres de presse qui parlent de l'agence
    couleur          tous les bleus ramenés sur la teinte du bleu de marque

Rien n'est inventé : les textes ajoutés sont repris du site en ligne, et ce
qui manque porte le marqueur « à remplir ». Aucune page en ligne n'est
touchée : l'outil écrit des fichiers, le dépôt en brouillon se fait ensuite
avec outils/ranger-brouillons.py ou outils/surcharger-brouillons.py.
"""

import argparse
import base64
import colorsys
import glob
import html as H
import json
import os
import re
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(RACINE, 'maquettes', 'assets')

DEVIS = 'https://authentiquegypte.com/sur-mesure/'
WHATSAPP = 'https://wa.me/201066619098'
QUI = 'https://authentiquegypte.com/qui-sommes-nous/'
QUAND_PARTIR = 'https://authentiquegypte.com/quand-partir-en-egypte/'
GOOGLE = 'https://search.google.com/local/reviews?placeid=ChIJOZOsXzk5WBQRMujsdlYsBy8'
BLEU = '#079DB6'          # le bleu de marque, teinte de référence
MOIS = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet',
        'août', 'septembre', 'octobre', 'novembre', 'décembre']

# Relevé le 14/09/2026 sur authentiquegypte.com/quand-partir-en-egypte :
# (abréviation, températures, conditions, affluence)
CALENDRIER = [
    ('janv.', '15-22', 'excellent, doux', 'faible'),
    ('févr.', '16-24', 'excellent', 'faible'),
    ('mars', '19-27', 'très bon, début de saison', 'modérée'),
    ('avril', '23-32', 'chaud mais supportable', 'forte (vacances)'),
    ('mai', '26-36', 'chaud', 'modérée'),
    ('juin', '29-39', 'très chaud, mer rouge seulement', 'faible'),
    ('juil.', '31-41', 'caniculaire, éviter circuits', 'faible'),
    ('août', '30-40', 'caniculaire, mer rouge possible', 'faible'),
    ('sept.', '27-37', 'encore chaud mais supportable', 'modérée'),
    ('oct.', '24-32', 'très bon', 'forte (vacances)'),
    ('nov.', '20-28', 'excellent, climat idéal', 'faible'),
    ('déc.', '17-25', 'très bon', 'forte (vacances)'),
]

# La recommandation par type de séjour, même source. mois = ceux mis en avant.
CALMES = ("Janvier, février et novembre sont les mois les plus calmes, "
          "hors vacances scolaires.")

SAISONS = {
    'desert': ("Exploration du désert : <b>octobre à mars</b>, journées "
               "supportables, nuits fraîches. " + CALMES, [9, 10, 11, 0, 1, 2]),
    'nil': ("Croisière sur le Nil : <b>octobre à avril</b>, climat doux, "
            "visites confortables. " + CALMES, [9, 10, 11, 0, 1, 2, 3]),
    'caire': ("Séjour au Caire : <b>novembre à mars</b>, températures "
              "agréables en ville. " + CALMES, [10, 11, 0, 1, 2]),
    'rouge': ("Séjour balnéaire en mer Rouge : <b>toute l’année</b>. Plongée : "
              "toute l’année (combinaison). Snorkeling et farniente : "
              "<b>avril à novembre</b>.", [3, 4, 5, 6, 7, 8, 9, 10]),
    'famille': ("Voyage en famille : <b>avril, octobre et décembre</b> "
                "correspondent aux vacances scolaires et offrent de bonnes "
                "conditions climatiques, mais il faut anticiper car l’affluence "
                "est forte.", [3, 9, 11]),
    'general': ("La période idéale se situe <b>entre octobre et avril</b> : "
                "températures douces, climat agréable et rythme adapté pour les "
                "visites. " + CALMES, [9, 10, 11, 0, 1, 2, 3]),
}

# Ordre de décision : le premier thème dont un mot-clé apparaît l'emporte.
THEMES = [
    ('famille', ('en famille', 'enfants')),
    ('desert', ('désert', 'oasis', 'siwa', 'fayoum', 'sinaï', 'moïse',
                'sainte-catherine', 'bédouin', 'bahariya', 'dakhla')),
    ('nil', ('croisière', 'nil', 'nubie', 'dahabeya', 'felouque',
             'louxor', 'assouan')),
    ('rouge', ('mer rouge', 'plongée', 'snorkeling', 'hurghada', 'marsa alam')),
    ('caire', ('le caire', 'gizeh', 'saqqara')),
]

PRESSE = ['Le Figaro', 'Le Figaro Madame', 'Marie Claire', 'Partir.com',
          'Evaneos', 'TripAdvisor']


# ----------------------------------------------------------------- outils HTML

def ico(chemin, taille=16):
    return ('<svg aria-hidden="true" width="%d" height="%d" viewBox="0 0 24 24" '
            'fill="none" stroke="currentColor" stroke-width="1.7" '
            'stroke-linecap="round" stroke-linejoin="round">%s</svg>'
            % (taille, taille, chemin))


I = {
    'check': ico('<path d="M5 12l4.5 4.5L19 7"/>'),
    'home': ico('<path d="M4 11l8-7 8 7v9H4z"/><path d="M10 20v-6h4v6"/>'),
    'car': ico('<path d="M5 11l1.5-4.5A2 2 0 0 1 8.4 5h7.2a2 2 0 0 1 1.9 1.5L19 11M4 11h16v6h-2a2 2 0 1 1-4 0H10a2 2 0 1 1-4 0H4z"/>'),
    'sun': ico('<circle cx="12" cy="12" r="4"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9l2.1 2.1M17 17l2.1 2.1M4.9 19.1L7 17M17 7l2.1-2.1"/>'),
    'walk': ico('<path d="M4 20c4-1 5-6 5-6l3-9 3 9s1 5 5 6"/><path d="M9 14h6"/>'),
    'land': ico('<path d="M3 21h18M5 21V10l7-6 7 6v11M10 21v-5h4v5"/>'),
    'user': ico('<circle cx="12" cy="8" r="3.5"/><path d="M5 20a7 7 0 0 1 14 0"/>'),
    'shield': ico('<path d="M12 3l7 3v6c0 4.5-3 7.5-7 9-4-1.5-7-4.5-7-9V6z"/><path d="M9 12l2 2 4-4"/>'),
    'phone': ico('<path d="M5 4h4l2 5-2.5 1.5a11 11 0 0 0 5 5L15 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2"/>'),
    'card': ico('<rect x="3" y="6" width="18" height="12" rx="2"/><path d="M3 10h18"/>'),
    'cal': ico('<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/>'),
    'chat': ico('<path d="M4 6a3 3 0 0 1 3-3h10a3 3 0 0 1 3 3v8a3 3 0 0 1-3 3H9l-5 4z"/>'),
    'mail': ico('<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/>'),
    'lien': ico('<path d="M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1"/><path d="M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1"/>'),
    'fleche': ico('<path d="M5 12h14M13 6l6 6-6 6"/>'),
    'lit': ico('<path d="M3 17V8M3 16h18M3 12h13a5 5 0 0 1 5 4v1"/>'
               '<circle cx="7.5" cy="9.5" r="1.6"/>', 15),
    'repas': ico('<path d="M7 3v7a2 2 0 0 0 4 0V3M9 3v18M17 3c-2 2-3 5-3 8h3v10"/>', 15),
    'avion': ico('<path d="M10 3l2 7 8 2-8 2-2 7-2-7-8-2 8-2z"/>', 15),
    'horloge': ico('<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>', 15),
}

GOOGLE_SVG = (
    '<svg class="gg" aria-hidden="true" width="16" height="16" viewBox="0 0 48 48">'
    '<path fill="#4285F4" d="M45.12 24.5c0-1.56-.14-3.06-.4-4.5H24v8.51h11.84c-.51 2.75-2.06 5.08-4.39 6.64v5.52h7.11c4.16-3.83 6.56-9.47 6.56-16.17z"/>'
    '<path fill="#34A853" d="M24 46c5.94 0 10.92-1.97 14.56-5.33l-7.11-5.52c-1.97 1.32-4.49 2.1-7.45 2.1-5.73 0-10.58-3.87-12.31-9.07H4.34v5.7C7.96 41.07 15.4 46 24 46z"/>'
    '<path fill="#FBBC05" d="M11.69 28.18C11.25 26.86 11 25.45 11 24s.25-2.86.69-4.18v-5.7H4.34C2.85 17.09 2 20.45 2 24c0 3.55.85 6.91 2.34 9.88l7.35-5.7z"/>'
    '<path fill="#EA4335" d="M24 10.75c3.23 0 6.13 1.11 8.41 3.29l6.31-6.31C34.91 4.18 29.93 2 24 2 15.4 2 7.96 6.93 4.34 14.12l7.35 5.7c1.73-5.2 6.58-9.07 12.31-9.07z"/></svg>')


class Journal:
    """Compte ce qui a été posé, et ce qui manquait sur la page."""

    def __init__(self, nom):
        self.nom, self.pose, self.absent = nom, [], []

    def dire(self):
        return '%-46s %2d blocs%s' % (
            self.nom[:46], len(self.pose),
            '' if not self.absent else '  (sans %s)' % ', '.join(self.absent))


def poser(h, motif, remplacement, journal, etiquette, flags=0, obligatoire=True):
    """Remplace une occurrence unique. Une ancre absente n'est pas une erreur
    quand le bloc est facultatif : la fiche ne porte simplement pas la
    section."""
    trouves = re.findall(motif, h, flags)
    if not trouves:
        if obligatoire:
            raise SystemExit('%s : ancre « %s » introuvable' % (journal.nom, etiquette))
        journal.absent.append(etiquette)
        return h
    if len(trouves) > 1:
        raise SystemExit('%s : ancre « %s » trouvée %d fois'
                         % (journal.nom, etiquette, len(trouves)))
    journal.pose.append(etiquette)
    return re.sub(motif, remplacement, h, count=1, flags=flags)


def fin_de_balise(h, depart, balise):
    """Index juste après la balise fermante qui correspond à celle ouverte en
    `depart`, en tenant compte de l'imbrication."""
    ouvre, ferme = '<%s' % balise, '</%s>' % balise
    profondeur, i = 0, depart
    while i < len(h):
        a, b = h.find(ouvre, i), h.find(ferme, i)
        if b < 0:
            raise SystemExit('balise <%s> non fermée' % balise)
        if 0 <= a < b:
            profondeur += 1
            i = a + len(ouvre)
        else:
            profondeur -= 1
            i = b + len(ferme)
            if profondeur == 0:
                return i
    raise SystemExit('balise <%s> non fermée' % balise)


def debut_de_section(h, index):
    """Index du <section> qui contient `index`."""
    return h.rfind('<section', 0, index)


# ----------------------------------------------------------------- lecture de la fiche

def titre_fiche(h):
    m = re.search(r'<h1>(.*?)</h1>', h, re.S)
    return H.unescape(re.sub(r'<[^>]+>', '', m.group(1))).strip() if m else ''


def prix_fiche(h):
    m = re.search(r'<div class="hero__prix"><small>[^<]*</small><b>([^<]*)</b>', h)
    return H.unescape(m.group(1)).strip() if m else ''


def inclus_panneau(h, maxi=4):
    """Quatre inclus de la fiche pour le panneau, un par famille : le guide,
    le chauffeur, le transport, l'assistance. On complète avec les plus
    courts si une famille manque."""
    bloc = re.search(r'<div class="incl__col incl__col--oui">.*?</ul>', h, re.S)
    if not bloc:
        bloc = re.search(r'<ul class="pan__liste">.*?</ul>', h, re.S)
    if not bloc:
        return []
    items = [H.unescape(x).strip() for x in re.findall(r'<span>([^<]+)</span>', bloc.group(0))]
    familles = (('guide',), ('chauffeur',), ('transfert', 'transport', '4x4', 'véhicule'),
                ('assistance', 'h24', '24h'))
    choisis = []
    for mots in familles:
        for it in items:
            bas = it.lower()
            if it not in choisis and any(m in bas for m in mots):
                choisis.append(it)
                break
    for it in sorted(items, key=len):
        if len(choisis) >= maxi:
            break
        if it not in choisis:
            choisis.append(it)
    choisis = [x for x in items if x in choisis][:maxi]
    return choisis


def theme_fiche(h, titre):
    """Le thème sert à choisir la recommandation de saison. Il se lit sur le
    contenu PROPRE de la fiche, jamais sur le méga-menu ni le pied de page qui
    nomment tous les séjours du site. Chaque zone pèse selon ce qu'elle dit du
    séjour : le titre d'abord, puis le fil d'ariane et le chapeau, enfin
    l'introduction. Un mot du titre l'emporte sur dix mots du corps."""
    bas = titre.lower()
    # Deux titres tranchent seuls : un séjour annoncé « en famille » se cale sur
    # les vacances scolaires, un séjour sur mesure n'a pas de saison propre.
    if 'en famille' in bas or 'enfants' in bas:
        return 'famille'
    if 'sur mesure' in bas or 'roadtrip' in bas or 'lac nasser' in bas:
        return 'general'
    # Une fiche qui annonce à la fois la mer Rouge et la montagne ou le désert
    # ne relève d'aucune des deux lignes du guide : on sert la recommandation
    # générale, vraie pour le pays entier, plutôt qu'une moitié du séjour.
    if 'mer rouge' in bas and any(m in bas for m in ('sinaï', 'désert', 'montagne')):
        return 'general'
    zones = [(titre, 6)]
    for motif, poids in ((r'<nav class="ariane"[^>]*>(.*?)</nav>', 4),
                         (r'<p class="hero__chapo">(.*?)</p>', 3),
                         (r'<meta name="description" content="([^"]*)"', 2),
                         (r'<div class="prose">(.*?)</div>', 1)):
        m = re.search(motif, h, re.S)
        if m:
            zones.append((m.group(1), poids))
    zones = [(H.unescape(re.sub(r'<[^>]+>', ' ', t)).lower(), p) for t, p in zones]
    scores = {}
    for cle, mots in THEMES:
        scores[cle] = sum(poids * texte.count(mot) for texte, poids in zones for mot in mots)
    ordre = [c for c, _ in THEMES]
    meilleur = max(ordre, key=lambda c: (scores[c], -ordre.index(c)))
    return meilleur if scores[meilleur] else 'general'



def privatif(h):
    m = re.search(r'<p class="guide__intro">(.*?)</p>', h, re.S)
    if not m:
        return ''
    txt = H.unescape(re.sub(r'<[^>]+>', '', m.group(1))).strip()
    return txt if txt.lower().startswith('ce séjour est privatif') else ''


def reponse_faq(h, motif):
    """La réponse de la FAQ de la fiche, mot pour mot. Rien n'est reformulé :
    ces phrases sont celles du client."""
    for bloc in re.findall(r'<details[^>]*>.*?</details>', h, re.S):
        q = re.search(r'<span class="q">(.*?)</span>', bloc, re.S)
        if not q or not re.search(motif, _texte(q.group(1)), re.I):
            continue
        corps = bloc[bloc.find('acc__c'):]
        phrases = [_texte(x) for x in re.findall(r'<p>(.*?)</p>', corps, re.S)]
        phrases = [x for x in phrases if x]
        if phrases:
            return re.sub(r'\s+([,.])', r'\1', ' '.join(phrases))
    return ''


def phrase_fiche(h, motif):
    """Une phrase de la fiche repérée par un fragment, rendue telle quelle."""
    m = re.search(r'>([^<>]*%s[^<>]*)<' % motif, h)
    return _texte(m.group(1)) if m else ''


CHAPOS_CREUX = ('votre programme de voyage', 'les étapes de votre séjour',
                'nos étapes', 'votre séjour')


def reparer_source(h, journal):
    """Défauts venus des fiches en ligne, réparables sans réécrire un mot.
    Relevés par l'agent qualité le 14/09."""
    faits = []

    # 1. Le garde-fou de la carte écrivait en rouge, sur la page publique, un
    #    message destiné au constructeur. Il devient une note d'atelier, visible
    #    comme telle, au-dessus du déroulé qu'elle met en cause.
    hors = re.search(r'<p class="carte__hors">(.*?)</p>', h, re.S)
    if hors:
        h = h.replace(hors.group(0), '')
        note = ('<p class="atelier"><span class="aremplir">à remplacer</span> '
                + H.escape(_texte(hors.group(1)))
                + ' — le déroulé ci-dessous ne correspond pas au séjour annoncé.</p>')
        i = h.find('<h2 id="t-jpj">')
        if i < 0:
            i = h.find('<h2>Le séjour jour par jour</h2>')
        if i >= 0:
            fin = h.find('</h2>', i) + len('</h2>')
            h = h[:fin] + note + h[fin:]
            # la carte place des points d'un autre séjour : on la retire
            carte = re.search(r'<figure class="carte">.*?</figure>', h, re.S)
            if carte:
                h = h.replace(carte.group(0), '')
        faits.append('déroulé signalé')

    # 2. Un chapeau qui n'annonce rien : « Votre programme de voyage ».
    def chapo(m):
        txt = _texte(m.group(1)).rstrip(' :')
        if txt.lower() in CHAPOS_CREUX:
            return ''
        return '<p class="hero__chapo">%s</p>' % H.escape(txt)

    h, n = re.subn(r'<p class="hero__chapo">(.*?)</p>', chapo, h, flags=re.S)
    if n:
        faits.append('chapeau')

    # 3. Un titre de journée cassé au découpage : « et 6 : Libre exploration… ».
    h, n = re.subn(r'(<div class="jour__tete"><h3>)\s*et\s+\d+\s*:\s*', r'\1', h)
    if n:
        faits.append('titre de journée réparé')

    # 4. La même fiche voisine proposée deux fois.
    bloc = re.search(r'<div class="proches">.*?</div>\s*</div>\s*</section>', h, re.S)
    if bloc:
        cartes = re.findall(r'<article class="proche".*?</article>', bloc.group(0), re.S)
        vus, garde = set(), []
        for c in cartes:
            t = re.search(r'<h3>(.*?)</h3>', c, re.S)
            cle = _texte(t.group(1)) if t else c
            if cle in vus:
                continue
            vus.add(cle)
            garde.append(c)
        if len(garde) < len(cartes):
            neuf_bloc = bloc.group(0)
            for c in cartes:
                neuf_bloc = neuf_bloc.replace(c, '', 1)
            neuf_bloc = neuf_bloc.replace('<div class="proches">',
                                          '<div class="proches">' + ''.join(garde), 1)
            h = h.replace(bloc.group(0), neuf_bloc)
            faits.append('séjours voisins dédoublonnés')

    # 5. Les numéros de la carte suivaient l'ordre du dessin, pas celui du
    #    voyage : le point 1 menait au jour 2. On les renumérote sur l'étape
    #    qu'ils ouvrent.
    etapes = [m.group(1).split() for m in re.finditer(r'<article class="etape"[^>]*data-lieu="([^"]*)"', h)]
    if etapes:
        points = list(re.finditer(r'<g class="carte__pt[^"]*"[^>]*data-lieu="([^"]*)"[^>]*>(.*?)</g>', h, re.S))
        rang = {}
        for m in points:
            lieux = m.group(1).split()
            cible = next((i for i, e in enumerate(etapes) if any(x in e for x in lieux)), 99)
            rang[m.group(0)] = cible
        ordre = sorted((g for g in rang if re.search(r'<text[^>]*>\d+</text>', g)), key=lambda g: rang[g])
        change = False
        for i, g in enumerate(ordre, start=1):
            neuf_g = re.sub(r'(<text[^>]*>)\d+(</text>)', r'\g<1>%d\g<2>' % i, g)
            if neuf_g != g:
                h = h.replace(g, neuf_g, 1)
                change = True
        if change:
            faits.append('carte renumérotée')

    # 6. Une fiche sans prix n'avait aucun appel à l'action collant sur mobile.
    if '<div class="pg-mob">' not in h:
        prix = prix_fiche(h)
        barre = ('<div class="pg-mob">'
                 + ('<span class="p"><small>À partir de</small><b>%s</b> <i>/ pers.</i></span>' % H.escape(prix) if prix else '')
                 + '<a class="btn btn--or btn--sm" href="' + DEVIS + '">Demander mon devis</a></div>')
        h = h.replace('</body>', barre + '</body>', 1)
        faits.append('barre mobile')

    journal.pose.extend(faits)
    return h


# ----------------------------------------------------------------- les blocs

def bloc_panneau(h, journal, titre, prix, live):
    inclus = inclus_panneau(h)
    reponse = phrase_fiche(h, 'Réponse sous 48')
    sans_cb = phrase_fiche(h, 'Aucune carte bancaire')
    liste = ''
    if inclus:
        liste = ('<ul class="pan__inclus">'
                 + ''.join('<li>%s<span>%s</span></li>' % (I['check'], H.escape(x)) for x in inclus)
                 + '</ul>')
    options = ('<option value="">Quand partir ?</option>'
               + ''.join('<option>%s</option>' % m.capitalize() for m in MOIS))
    form = (
        liste
        + '<div class="pan__qui"><img class="pan__av" src="{AVATAR}" alt="" width="36" height="36">'
          '<span><b>Mélanie</b><small>' + H.escape(reponse or 'Réponse sous 48 h') + '</small></span></div>'
          '<form class="pan__form" action="' + DEVIS + '" method="get" data-devis '
          'data-sejour="' + H.escape(titre) + '" data-prix="' + H.escape(prix) + '">'
          '<select aria-label="Période souhaitée">' + options + '</select>'
          '<input type="number" min="1" max="12" placeholder="Voyageurs" aria-label="Nombre de voyageurs">'
          '<input class="pan__l2" type="text" placeholder="Vos envies (facultatif)" aria-label="Vos envies">'
          '<button class="btn btn--or btn--bloc" type="submit">Recevoir mon devis</button>'
          '</form>'
          '<p class="pan__note">' + H.escape(sans_cb or 'Aucune carte bancaire demandée à cette étape.') + '</p>'
          '<a class="pan__wa" href="' + WHATSAPP + '">' + I['chat'] + ' Une question ? WhatsApp</a>')
    h = poser(h, r'<div class="pan__act">.*?</div>', form, journal, 'panneau devis', re.S)

    garanties = ('<ul class="pan__gar">'
                 '<li>' + I['shield'] + '<span>Enregistrée en France</span></li>'
                 '<li>' + I['shield'] + '<span>Licence en Égypte</span></li>'
                 '<li>' + I['phone'] + '<span>Assistance 24h/24</span></li></ul>')
    h = poser(h, r'<p class="pan__note">Réponse sous 48 h[^<]*<br>[^<]*</p>',
              garanties, journal, 'garanties')

    partage = H.escape('%s avec Authentique Égypte : %s' % (titre, live))
    avis = ('<p class="pan__avis"><a href="' + GOOGLE + '" target="_blank" rel="noopener">'
            + GOOGLE_SVG + '<b>23 avis Google</b></a>'
            '<span class="pan__part"><span>Partager</span>'
            '<a href="https://wa.me/?text=' + partage + '" target="_blank" rel="noopener" '
            'aria-label="Partager sur WhatsApp" title="WhatsApp">' + I['chat'] + '</a>'
            '<a href="mailto:?subject=' + H.escape(titre) + '&amp;body='
            + H.escape('Regarde ce programme : ' + live) + '" aria-label="Partager par e-mail" '
            'title="E-mail">' + I['mail'] + '</a>'
            '<button type="button" data-copier="' + live + '" aria-label="Copier le lien" '
            'title="Copier le lien">' + I['lien'] + '</button></span></p>')
    return poser(h, r'<p class="pan__avis">.*?</p>', avis, journal, 'avis et partage', re.S)


def bloc_ancres(h, journal):
    """Les ancres des sections réellement présentes, en tête de colonne."""
    presentes = [(i, t) for i, t in (('t-vue', 'Vue d’ensemble'), ('t-quand', 'Quand partir'),
                                     ('t-jpj', 'Jour par jour'), ('t-tarif', 'Tarif'),
                                     ('t-faq', 'Questions'))
                 if 'id="%s"' % i in h]
    if len(presentes) < 2:
        journal.absent.append('navigation')
        return h
    nav = ('<nav class="pg-anc" aria-label="Sections de la page">'
           + ''.join('<a href="#%s">%s</a>' % (i, t) for i, t in presentes)
           + '</nav>')
    if '<nav class="somm"' in h:
        return poser(h, r'<nav class="somm"', nav + '<nav class="somm"', journal, 'navigation')
    depart = h.find('<aside class="pan">')
    fin = fin_de_balise(h, depart, 'aside')
    journal.pose.append('navigation')
    return h[:fin - len('</aside>')] + nav + h[fin - len('</aside>'):]


def bloc_etapes(h, journal):
    """Un picto par type d'étape dans l'aperçu du séjour."""
    def picto(m):
        t = m.group(2).lower()
        cle = ('home' if any(x in t for x in ('arriv', 'retour', 'guesthouse', 'hôte', 'nuit')) else
               'sun' if any(x in t for x in ('lever', 'coucher')) else
               'walk' if any(x in t for x in ('ascension', 'descente', 'marche', 'randonn')) else
               'land' if any(x in t for x in ('visite', 'monast', 'temple', 'musée', 'site')) else 'car')
        return '%s<span class="ic">%s</span><span class="t">%s</span>' % (m.group(1), I[cle], m.group(2))

    h2, n = re.subn(r'(<li><span class="n">J\d+</span>)<span class="t">([^<]+)</span>', picto, h)
    (journal.pose if n else journal.absent).append('pictos étapes')
    return h2


# Les étiquettes qui ouvrent une ligne d'étape et valent une information de
# service plutôt qu'un moment du séjour. Relevées sur les 14 fiches.
META = (('hébergement', 'lit'), ('hebergement', 'lit'), ('nuit', 'lit'),
        ('repas', 'repas'), ('petit-déjeuner', 'repas'), ('déjeuner', 'repas'),
        ('dîner', 'repas'), ('vol', 'avion'), ('transport', 'car'),
        ('transfert', 'car'), ('durée', 'horloge'), ('temps de trajet', 'horloge'))


def _texte(fragment):
    return H.unescape(re.sub(r'<[^>]+>', '', fragment)).strip()


def _pareil(a, b):
    net = lambda x: re.sub(r'\s+', ' ', x.lower()).strip(' .:;!?')
    return net(a) == net(b)


def recomposer_etape(segments, titre_jour, titre_existant=''):
    """Le gabarit aplatit en paragraphes ce qui était une liste à puces sur le
    site : une phrase par ligne. On rend la structure, sans toucher aux mots —
    une puce par ligne, un titre d'étape quand la première ligne en tient lieu,
    « Hébergement : … » et « En option : … » en étiquettes."""
    lignes = [re.sub(r'^\s*[•·–-]\s*', '', x.strip()) for x in segments if _texte(x)]
    if not lignes:
        return None

    titre = ''
    if not titre_existant and len(_texte(lignes[0])) <= 80 \
            and not re.match(r'^[A-Za-zÀ-ÿ\'’ -]{3,28}\s*:', _texte(lignes[0])):
        premiere = lignes.pop(0)
        # Cette première ligne répète souvent le titre du jour : on ne l'affiche
        # pas deux fois, l'information reste portée par ce titre.
        titre = '' if _pareil(_texte(premiere), titre_jour) else premiere
    elif titre_existant and _pareil(_texte(lignes[0]), titre_existant):
        lignes.pop(0)
    if not lignes:
        return None

    points, metas = [], []
    for ligne in lignes:
        txt = _texte(ligne)
        eti = re.match(r'^([A-Za-zÀ-ÿ\'’ -]{3,28})\s*:\s*(.+)$', txt, re.S)
        if eti:
            nom, valeur = eti.group(1).strip(), eti.group(2).strip()
            cle = nom.lower()
            picto = next((ic for m, ic in META if cle.startswith(m)), '')
            if picto:
                metas.append((nom, valeur, picto))
                continue
            if cle.startswith('en option'):
                points.append(('option', valeur))
                continue
        points.append(('', ligne))

    bloc = ''
    if titre:
        bloc += '<h4 class="etape__t">%s</h4>' % titre
    if points:
        bloc += '<ul class="etape__pts">' + ''.join(
            ('<li class="etape__opt"><span class="etape__eti">En option</span>%s</li>' % t)
            if genre == 'option' else ('<li>%s</li>' % t)
            for genre, t in points) + '</ul>'
    if metas:
        bloc += '<p class="etape__meta">' + ''.join(
            '<span class="etape__sv">%s<b>%s</b><i>%s</i></span>' % (I[ic], H.escape(nom), H.escape(val))
            for nom, val, ic in metas) + '</p>'
    return bloc or None


def fusionner_jours(h, journal):
    """Deux blocs « jour » de suite portant le même titre et le même numéro : la
    fiche en ligne les a en double. On garde un seul en-tête, les étapes des
    deux blocs se suivent. Aucun contenu n'est perdu."""
    vu = [None]

    def couper(m):
        cle = (_texte(m.group(1)), m.group(2).strip())
        double = (cle == vu[0])
        vu[0] = cle
        return '' if double else m.group(0)

    motif = (r'</div>\s*<div class="jour">\s*<div class="jour__tete">'
             r'<h3>(.*?)</h3><span class="jour__no">([^<]*)</span></div>')
    # le premier en-tête sert de référence, il n'est pas précédé d'un </div> de jour
    premier = re.search(r'<div class="jour__tete"><h3>(.*?)</h3><span class="jour__no">([^<]*)</span></div>', h, re.S)
    if premier:
        vu[0] = (_texte(premier.group(1)), premier.group(2).strip())
    h2, n = re.subn(motif, couper, h, flags=re.S)
    (journal.pose if n else journal.absent).append('jours en double')
    return h2


def bloc_recit(h, journal):
    entetes = [(m.start(), _texte(m.group(1)))
               for m in re.finditer(r'<div class="jour__tete"><h3>(.*?)</h3>', h, re.S)]

    def refaire(m):
        art = m.group(0)
        # Une étape sans photo ni texte n'est qu'un conteneur vide : elle
        # creusait un blanc de 40 px au milieu du déroulé. On la retire, sauf
        # si un lien pointe dessus.
        if '<img' not in art and not re.search(r'<p[^>]*>\s*\S', art):
            ident = re.search(r'id="([^"]+)"', art)
            if not ident or ('href="#%s"' % ident.group(1)) not in h:
                return ''
        # Seuls les paragraphes NUS portent le récit. Ceux qui ont une classe
        # (mentions de repas du gabarit) sont laissés où ils sont : les effacer
        # faisait disparaître « Petit-déjeuner, déjeuner et dîner inclus ».
        nus = [x for x in re.finditer(r'<p>(.*?)</p>', art, re.S)]
        if not nus:
            return art
        segments = []
        for para in nus:
            segments += re.split(r'<br\s*/?>', para.group(1))
        debut, fin = nus[0].start(), nus[0].end()
        titre_jour = ''
        for pos, t in entetes:
            if pos < m.start():
                titre_jour = t
        h4 = re.search(r'<h4[^>]*>(.*?)</h4>', art[:debut], re.S)
        neuf = recomposer_etape(segments, titre_jour, _texte(h4.group(1)) if h4 else '')
        if neuf is None:
            return art
        # le bloc remplace le premier paragraphe nu, les suivants disparaissent
        refait = art[:debut] + neuf + art[fin:]
        for autre in nus[1:]:
            refait = refait.replace(autre.group(0), '', 1)
        return refait

    h2, n = re.subn(r'<article class="etape".*?</article>', refaire, h, flags=re.S)
    (journal.pose if n else journal.absent).append('étapes en liste')
    return h2


def bloc_carte(h, journal):
    pin = ico('<path d="M12 21s-6-5.5-6-11a6 6 0 0 1 12 0c0 5.5-6 11-6 11z"/>'
              '<circle cx="12" cy="10" r="2.5"/>', 15)
    aide = ('<p class="carte__aide">' + pin
            + ' Cliquez une étape sur la carte pour lire la journée.</p>')
    return poser(h, '(<figcaption class="carte__tete">)', '\\1' + aide, journal,
                 'carte cliquable', obligatoire=False)


def bloc_tarif(h, journal):
    """Paiement, annulation et « pourquoi ce prix », sous le tarif."""
    i = h.find('<h2 id="t-tarif">')
    if i < 0:
        journal.absent.append('conditions tarif')
        return h
    debut = debut_de_section(h, i)
    fin = fin_de_balise(h, debut, 'section')
    # Chaque phrase vient de la FAQ de cette fiche, sans reformulation.
    # « Oui, » ouvre la réponse d'une FAQ ; hors de sa question, la particule
    # n'a plus de sens. C'est la seule coupe faite dans ces phrases.
    def sans_oui(x):
        x = re.sub(r'^Oui,\s*', '', x)
        return x[:1].upper() + x[1:] if x else x

    morceaux = [sans_oui(x) for x in (reponse_faq(h, r'régler mon voyage'),
                                      reponse_faq(h, r'fractionnable')) if x]
    paiement = ' '.join(morceaux)
    annulation = reponse_faq(h, r'ne peux plus partir')
    pourquoi = ' '.join(x for x in (privatif(h),
                                    phrase_fiche(h, 'Devis gratuit'),
                                    phrase_fiche(h, 'Aucune carte bancaire')) if x)
    volets = [(I['card'], 'Paiement', paiement),
              (I['cal'], 'Annulation', annulation),
              (I['user'], 'Pourquoi ce prix', pourquoi)]
    volets = [v for v in volets if v[2]]
    if not volets:
        journal.absent.append('conditions tarif')
        return h
    cond = ('<div class="tarif__cond">' + ''.join(
        '<article><h3>%s%s</h3><p>%s</p></article>' % (ic, nom, H.escape(txt))
        for ic, nom, txt in volets) + '</div>')
    if 'id="t-faq"' in h:
        cond += '<p class="tarif__lien"><a href="#t-faq">Le détail, question par question</a></p>'
    journal.pose.append('conditions tarif')
    ferme = len('</section>')
    return h[:fin - ferme] + cond + h[fin - ferme:]


def bloc_quand(h, journal, theme):
    texte, phares = SAISONS[theme]

    def niveau(conditions):
        if 'excellent' in conditions or 'très bon' in conditions:
            return 'q-1'
        if 'canicul' in conditions or 'très chaud' in conditions:
            return 'q-3'
        return 'q-2'

    cases = ''.join(
        '<li class="%s%s"><b>%s</b><span class="q-t">%s °C</span>'
        '<span class="q-c">%s</span><small>affluence %s</small></li>'
        % (niveau(cond), ' q-ok' if i in phares else '', mois, temp, cond, aff)
        for i, (mois, temp, cond, aff) in enumerate(CALENDRIER))
    section = (
        '<section class="quand"><p class="eyebrow">La bonne période</p>'
        '<h2 id="t-quand">Quand partir ?</h2>'
        '<p class="quand__intro">' + texte + '</p>'
        '<ol class="quand__frise">' + cases + '</ol>'
        '<p class="quand__leg"><span class="q-1">conseillé</span><span class="q-2">chaud</span>'
        '<span class="q-3">à éviter</span><span class="q-src">Températures et affluence relevées '
        'sur <a href="' + QUAND_PARTIR + '">notre guide quand partir</a>.</span></p></section>')

    # Après le module « combien de temps », sinon après la vue d'ensemble,
    # sinon juste avant le déroulé jour par jour.
    for reperage in (lambda: h.find('<section class="mod mod--duree">'),
                     lambda: debut_de_section(h, h.find('<h2 id="t-vue">')) if 'id="t-vue"' in h else -1):
        depart = reperage()
        if depart >= 0:
            fin = fin_de_balise(h, depart, 'section')
            journal.pose.append('quand partir')
            return h[:fin] + section + h[fin:]
    if 'id="t-jpj"' in h:
        depart = debut_de_section(h, h.find('<h2 id="t-jpj">'))
        journal.pose.append('quand partir')
        return h[:depart] + section + h[depart:]
    journal.absent.append('quand partir')
    return h


def bloc_agence(h, journal, photo):
    """Les deux paragraphes sont ceux d'authentiquegypte.com/qui-sommes-nous,
    mot pour mot. Le rôle de Mélanie n'est écrit nulle part sur le site : on ne
    lui en prête pas un."""
    section = (
        '<section class="pg-sec equipe" id="s-equipe"><div class="wrap">'
        '<p class="eyebrow">L’agence</p><h2 id="t-equipe">Qui vous répond</h2>'
        '<div class="equipe__portrait">'
        '<div class="equipe__photo"><img src="' + photo + '" '
        'alt="Mélanie, Authentique Égypte" width="640" height="800"></div>'
        '<div class="equipe__txt">'
        '<p class="equipe__cit">« Une aventure née d’un regard curieux sur l’Égypte authentique »</p>'
        '<h3>Mélanie</h3>'
        '<p>Tout commence quand Mélanie, alors installée en Inde, tombe sous le charme '
        'de l’Égypte lors d’un premier voyage. Elle décide de s’entourer de '
        'professionnels égyptiens passionnés pour développer une approche humaine '
        'du voyage.</p>'
        '<p>Basée au Caire, notre équipe s’appuie sur un réseau solide de guides '
        'francophones, chauffeurs et spécialistes logistiques.</p>'
        '<a class="btn btn--fantome btn--sm" href="' + QUI + '">Notre histoire</a></div>'
        '</div>'
        '<div class="equipe__bas"><div class="presse"><p class="eyebrow">Ils parlent de nous</p>'
        '<ul>' + ''.join('<li><span>%s</span></li>' % x for x in PRESSE) + '</ul></div></div>'
        '</div></section>')
    depart = h.find('<section class="pg-sec pg-sec--nuit">')
    if depart < 0:
        depart = h.find('<section class="pg-sec" aria-labelledby="t-avis">')
        if depart < 0:
            journal.absent.append('agence')
            return h
        journal.pose.append('agence')
        return h[:depart] + section + h[depart:]
    fin = fin_de_balise(h, depart, 'section')
    journal.pose.append('agence')
    return h[:fin] + section + h[fin:]


# ----------------------------------------------------------------- un seul bleu

TEINTE = colorsys.rgb_to_hls(0x07 / 255, 0x9D / 255, 0xB6 / 255)[0]


def _teinte(r, g, b):
    h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
    if 176 <= h * 360 <= 212 and s >= .12:
        r2, g2, b2 = colorsys.hls_to_rgb(TEINTE, l, s)
        return int(round(r2 * 255)), int(round(g2 * 255)), int(round(b2 * 255))
    return None


def unifier_bleus(texte):
    """La page portait quatre bleus. Toute couleur de teinte bleue est ramenée
    sur celle du bleu de marque, à clarté et saturation égales : la couleur
    devient une, les contrastes mesurés ne bougent pas. Le « G » de Google
    n'est pas concerné, il est hors de la plage de teintes."""
    def hexa(m):
        x = m.group(1)
        if len(x) == 3:
            x = ''.join(c * 2 for c in x)
        n = _teinte(int(x[:2], 16), int(x[2:4], 16), int(x[4:], 16))
        return m.group(0) if n is None else '#%02X%02X%02X' % n

    def rgb(m):
        n = _teinte(int(m.group(2)), int(m.group(3)), int(m.group(4)))
        return m.group(0) if n is None else '%s%d,%d,%d' % (m.group(1), *n)

    texte = re.sub(r'#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})(?![0-9a-zA-Z_-])', hexa, texte)
    return re.sub(r'(rgba?\(\s*)(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})', rgb, texte)


# ----------------------------------------------------------------- la page entière

def habiller(h, live, css, js, photo, avatar, nom):
    journal = Journal(nom)
    h = reparer_source(h, journal)
    titre = titre_fiche(h)
    prix = prix_fiche(h)

    # Les ancres de section, posées avant tout ce qui s'y réfère.
    for texte, ident in (('Vue d&#x27;ensemble', 't-vue'),
                         ('Le séjour jour par jour', 't-jpj'),
                         ('Tarif par personne', 't-tarif'),
                         ('Les questions qui reviennent avant de partir', 't-faq')):
        h = poser(h, '<h2>%s</h2>' % texte, '<h2 id="%s">%s</h2>' % (ident, texte),
                  journal, 'ancre ' + ident, obligatoire=False)

    reassurance = [phrase_fiche(h, 'Devis gratuit'),
                   phrase_fiche(h, 'Aucune carte bancaire'),
                   phrase_fiche(h, 'Agence locale')]
    reassurance = [x for x in reassurance if x]
    if reassurance:
        h = poser(h, r'(Poser une question sur WhatsApp</a></div>)(\s*</div></div></div></section>)',
                  '\\1 <p class="hero__conf">'
                  + ''.join('<span>%s%s</span>' % (I['check'], H.escape(x)) for x in reassurance)
                  + '</p>\\2', journal, 'réassurance héros')

    h = bloc_panneau(h, journal, titre, prix, live)
    h = bloc_ancres(h, journal)
    h = bloc_etapes(h, journal)
    h = fusionner_jours(h, journal)
    h = bloc_recit(h, journal)
    h = bloc_carte(h, journal)
    h = bloc_tarif(h, journal)
    h = bloc_quand(h, journal, theme_fiche(h, titre))
    h = bloc_agence(h, journal, photo)
    h = poser(h, '(<p class="mur__cpt">.*?</p>)',
              '\\1<a class="mur__lien btn btn--fantome btn--sm" href="' + GOOGLE
              + '" target="_blank" rel="noopener">Voir les avis sur Google</a>',
              journal, 'lien avis Google', re.S)

    h = unifier_bleus(h)
    h = h.replace('{AVATAR}', avatar)
    tete, reste = h.rsplit('</head>', 1)
    h = tete + '<style id="gabarit-ux">\n' + css + '</style>\n</head>' + reste
    corps, reste = h.rsplit('</body>', 1)
    h = corps + '<script>\n' + js + '</script>\n</body>' + reste
    return h, journal


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--site', required=True, help='dossier des pages du gabarit programme')
    p.add_argument('--sortie', required=True, help='dossier où écrire les pages habillées')
    p.add_argument('--inventaire', default=os.path.join(RACINE, 'docs', 'inventaire.json'))
    p.add_argument('--seulement', default='', help='slugs à traiter, séparés par des virgules')
    a = p.parse_args()

    with open(os.path.join(ASSETS, 'gabarit-ux.css'), encoding='utf-8') as f:
        css = f.read()
    with open(os.path.join(ASSETS, 'gabarit-ux.js'), encoding='utf-8') as f:
        js = f.read()

    def donnee(fichier):
        with open(os.path.join(ASSETS, fichier), 'rb') as f:
            return 'data:image/jpeg;base64,' + base64.b64encode(f.read()).decode('ascii')

    photo, avatar = donnee('equipe-melanie.jpg'), donnee('equipe-melanie-96.jpg')

    liens = {}
    if os.path.exists(a.inventaire):
        with open(a.inventaire, encoding='utf-8') as f:
            for x in json.load(f):
                liens[x['slug']] = x.get('url', '')

    vise = set(a.seulement.split(',')) if a.seulement else None
    os.makedirs(a.sortie, exist_ok=True)
    fichiers = sorted(glob.glob(os.path.join(a.site, 'programme-*.html')))
    if not fichiers:
        raise SystemExit('aucune page « programme-*.html » dans %s' % a.site)

    faits = 0
    for chemin in fichiers:
        nom = os.path.basename(chemin)
        slug = nom[len('programme-'):-len('.html')]
        if vise and slug not in vise:
            continue
        with open(chemin, encoding='utf-8') as f:
            h = f.read()
        live = liens.get(slug) or next(
            (u for s, u in liens.items() if s.startswith(slug[:40])), '')
        if not live:
            live = 'https://authentiquegypte.com/programs/%s/' % slug
        habille, journal = habiller(h, live, css, js, photo, avatar, nom)
        with open(os.path.join(a.sortie, nom), 'w', encoding='utf-8') as f:
            f.write(habille)
        print('   ' + journal.dire(), flush=True)
        faits += 1

    print('\n%d fiches habillées dans %s. Aucune page en ligne touchée.' % (faits, a.sortie))


if __name__ == '__main__':
    main()
