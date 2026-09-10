#!/usr/bin/env python3
"""
Le gabarit « programme » — ticket O4 du plan `docs/plan-pages-programme.md`.

Il coule une fiche séjour dans la mise en page validée par la SERP
(bandeau, repères, jour par jour illustré, tarif, inclusions, infos
pratiques, FAQ, avis, appel au devis, séjours proches) avec les
couleurs, les polices et les boutons d'Authentique Égypte.

Trois règles tiennent tout le fichier :

1. **Rien ne s'écrit ici.** Le texte vient de l'inventaire de la fiche
   (`docs/programmes/<slug>.json`) ou de la maquette d'accueil validée
   (`maquettes/index.html`). Les seules chaînes du gabarit sont dans
   `INTERFACE`, chacune rattachée à une décision du registre.
2. **Aucune image n'est agrandie.** Chaque image est servie dans son
   original, avec le `srcset` de ses tailles réelles, et sa boîte est
   bornée par ce que l'image peut donner. `outils/verif/images.js` le
   vérifie au pixel.
3. **Aucune requête réseau.** Tout est lu sur le disque : deux
   générations successives donnent le même fichier.

    outils/gabarit-programme.py --programme excursion-a-loasis-de-siwa
    outils/gabarit-programme.py --tous
"""

import argparse
import html as H
import json
import math
import os
import re
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAQUETTES = os.path.join(RACINE, 'maquettes')
PROGRAMMES = os.path.join(RACINE, 'docs', 'programmes')

SITE = 'https://authentiquegypte.com'
DEVIS = SITE + '/sur-mesure/'
WHATSAPP = 'https://wa.me/201066619098'

e = H.escape


# ------------------------------------------------------------------ interface
#
# Les seules chaînes que le gabarit écrit. Chacune porte le numéro de la
# décision qui l'autorise dans docs/programmes/registre-decisions.md.
# L'agent CONTRÔLE CONTENU reçoit cette liste : ce qui n'y est pas et
# qui n'est pas dans l'inventaire est une invention.

def _fr(t):
    """L'espace insécable avant ? ! : ; — typographie française.

    Elle ne s'applique qu'aux libellés que NOUS écrivons. Le contenu de
    la cliente garde son espacement, comme il garde ses fautes (D17).
    """
    return re.sub(r' ([?!:;»])', '\u00a0\\1', t).replace('« ', '«\u00a0')


INTERFACE = {
    'ariane_accueil': 'Accueil',                                   # D6
    'ariane_sejours': 'Nos séjours en Égypte',                     # D6
    'depuis': 'À partir de',                                       # D6
    'par_personne': 'par personne',                                # D6
    'cta_devis': 'Personnaliser ce séjour',                        # D18
    'cta_whatsapp': 'Poser une question sur WhatsApp',             # D18
    'cta_devis_court': 'Demander mon devis',                       # D18
    'delai': 'Réponse sous 48 h, hors vendredi et samedi',         # D3
    'agence': 'Agence locale basée au Caire',                      # D3
    'sans_cb': 'Aucune carte bancaire demandée à cette étape.',    # D8
    'eyebrow_sejour': 'Le séjour',                                 # D6
    'titre_etapes': 'Les étapes de votre séjour',                  # D6
    'eyebrow_etapes': 'Le fil du voyage',                          # D6
    'titre_deroule': 'Le séjour jour par jour',                    # D6
    'eyebrow_deroule': 'Dans le détail',                           # D6
    'titre_tarif': 'Tarif par personne',                           # D6
    'eyebrow_tarif': 'Budget',                                     # D6
    'titre_inclusions': 'Ce que le prix comprend',                 # D6
    'inclus': 'Le programme inclus',                               # D17 (orthographe de la source)
    'exclus': "N'inclus pas",                                      # D17 (orthographe de la source)
    'titre_pratique': 'Les questions qui reviennent avant de partir',   # D6
    'eyebrow_pratique': 'Avant de réserver',                       # D6
    'titre_faq': 'Tout savoir sur ce séjour',                      # D6
    'eyebrow_faq': 'La destination',                               # D6
    'titre_avis': 'Ce que disent les voyageurs',                   # D6
    'avis_source': 'Publié sur Google',                            # D30 (libellé du widget)
    'avis_releve': 'Relevé sur la fiche le',                       # D11
    'avis_arret': 'Reprendre le défilement',                       # D30
    'avis_marche': 'Mettre en pause le défilement',                # D30
    'eyebrow_avis': 'Avis Google',                                 # D11
    'titre_devis': 'Ce séjour vous tente ? Ajustons-le à vos dates.',   # D8
    'devis_points': [                                              # D8
        'Devis gratuit, détaillé jour par jour, sans engagement',
        'Guide égyptologue francophone et chauffeur privatif',
        "Acompte seulement une fois l'itinéraire validé",
    ],
    'titre_proches': 'Ces séjours se combinent bien',              # D5
    'tous_sejours': 'Voir tous nos séjours en Égypte',             # D5
    'reponse_attendue': 'Réponse à rédiger — question posée sur la page actuelle, sans réponse.',  # D1
    'photos': 'Photos du séjour',                                  # D6
    'titre_verifier': 'À vérifier avec l\'agence avant mise en ligne',   # D19
    'releve_du': 'Relevé sur la fiche actuelle le',                # D19
    # --- modules d'attention, doctrine NavBoost (D24)
    'eyebrow_bref': 'La réponse courte',                           # D24
    'titre_bref': 'Ce séjour en quatre chiffres',                  # D24
    'source_fiche': 'Relevé sur la fiche du site le',              # D24
    'eyebrow_duree': 'Le bon format',                              # D24
    'eyebrow_valise': 'Avant de boucler le sac',                   # D24
    'valise_aide': 'Cochez au fur et à mesure, la liste reste sur cet écran.',  # D24
    'valise_reste': 'Il reste',                                    # D24
    'valise_fini': 'Votre sac est prêt.',                          # D24
    # --- votre guide (D26)
    'eyebrow_guide': 'Qui vous accompagne',                        # D26
    'titre_guide': 'Votre guide, votre chauffeur, et personne d\'autre',  # D26
    'guide_privatif': 'Ce séjour est privatif : vous ne partagez ni le guide, '
                      'ni le véhicule.',                           # D41
    'guide_seul': 'Ce séjour est privatif : vous ne partagez pas votre guide.',  # D41
    'guide_neutre': 'Ce que la fiche prévoit pour vous accompagner :',  # D41
    'titre_equipe': 'Les visages derrière votre séjour',            # D26
    'equipe_aide': 'Faites défiler pour rencontrer toute l\'équipe.',  # D26
    'precedent': 'Personne précédente',                            # D26
    'suivant': 'Personne suivante',                                # D26
    # --- carte (D25)
    'eyebrow_carte': 'Où vous allez',                              # D25
    'titre_carte': 'Le trajet, étape par étape',                   # D25
    'carte_note': 'Points placés à leurs coordonnées réelles. Fond de carte : ',   # D25
    # --- repères de trajet (D27)
    'titre_sommaire': 'Le fil du séjour',                           # D25
    'source_trajets': 'Les distances et les temps de route sont calculés par nos soins '
                      'sur les données OpenStreetMap, entre les lieux que la fiche nomme. '
                      'Ils situent le trajet : ils ne remplacent pas le programme de '
                      'l\'agence. Les durées écrites par la fiche sont reprises telles quelles.',
}


INTERFACE = {k: ([_fr(x) for x in v] if isinstance(v, list) else _fr(v))
             for k, v in INTERFACE.items()}


# ------------------------------------------------------------------ icônes

ICONES = {
    'horloge': '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    'euro': '<path d="M17 6.5A6 6 0 0 0 7 12a6 6 0 0 0 10 5.5M5 10h8M5 14h8"/>',
    'pas': '<path d="M4 20c4-1 5-6 5-6l3-9 3 9s1 5 5 6"/><path d="M9 14h6"/>',
    'voiture': '<path d="M5 11l1.5-4.5A2 2 0 0 1 8.4 5h7.2a2 2 0 0 1 1.9 1.5L19 11M4 11h16v6h-2a2 2 0 1 1-4 0H10a2 2 0 1 1-4 0H4z"/>',
    'guide': '<circle cx="12" cy="8" r="3.5"/><path d="M5 20a7 7 0 0 1 14 0"/>',
    'maison': '<path d="M4 11l8-7 8 7v9H4z"/><path d="M10 20v-6h4v6"/>',
    'pin': '<path d="M12 21s6-5.5 6-11a6 6 0 1 0-12 0c0 5.5 6 11 6 11z"/><circle cx="12" cy="10" r="2.2"/>',
    'lit': '<path d="M3 18V8M3 12h18v6M7 12V9h6v3"/>',
    'repas': '<path d="M7 3v7a2 2 0 0 0 4 0V3M9 3v18M17 3c-2 2-3 5-3 8h3v10"/>',
    'coche': '<path d="M5 12l4.5 4.5L19 7"/>',
    'croix': '<path d="M6 6l12 12M18 6L6 18"/>',
    'etoile': '<path d="M12 3l2.7 5.8 6.3.7-4.7 4.3 1.3 6.2L12 17l-5.6 3 1.3-6.2L3 9.5l6.3-.7z"/>',
    'bulle': '<path d="M4 6a3 3 0 0 1 3-3h10a3 3 0 0 1 3 3v8a3 3 0 0 1-3 3H9l-5 4z"/>',
    'bouclier': '<path d="M12 3l7 3v6c0 4.5-3 7.5-7 9-4-1.5-7-4.5-7-9V6z"/>',
    'fleche': '<path d="M4 12h13M12 6l6 6-6 6"/>',
    'pause': '<path d="M9 5v14M15 5v14"/>',
}


def texte_nu(h):
    return re.sub(r'\s+', ' ', H.unescape(re.sub(r'<[^>]+>', ' ', h or ''))).strip()


def faq_par(inv, motif):
    """La question de la fiche qui correspond au motif, et sa réponse."""
    for f in inv['faq']:
        if re.search(motif, f['q'], re.I) and f['reponse_html']:
            return f
    return None


def items_de(reponse_html):
    """Les points d'une réponse, découpés « intitulé : détail »."""
    lot = []
    for brut in re.findall(r'<li>(.*?)</li>', reponse_html or '', re.S):
        m = re.match(r'\s*<strong>(.*?)</strong>\s*(.*)$', brut, re.S)
        if m:
            # Le « : » de la fiche est SA ponctuation : on le garde tel
            # qu'elle l'écrit, ESPACE COMPRISE — « Vêtements : couches »
            # et non « Vêtements: couches » — au lieu de le raboter.
            detail = texte_nu(m.group(2))
            if detail[:1] in ':;!?':
                detail = ' ' + detail
            lot.append((texte_nu(m.group(1)), detail))
        elif texte_nu(brut):
            lot.append((texte_nu(brut), ''))
    return lot


def blocs_reponse(reponse_html):
    """Les blocs d'une réponse, DANS L'ORDRE : paragraphes et listes.

    Une réponse de la fiche n'est pas toujours « une phrase puis une
    liste ». Celle de la fiche famille en compte sept : deux listes,
    chacune avec son intertitre, puis trois paragraphes dont un lien.
    Ramasser tous les `<li>` d'un coup fusionnait les deux listes en une
    seule et jetait le reste — et comme la question est sortie de
    l'accordéon (D24), ce reste n'était plus nulle part sur la page.
    """
    lot = []
    for m in re.finditer(r'<(p|ul|ol)\b[^>]*>(.*?)</\1>', reponse_html or '', re.S):
        if m.group(1) == 'p':
            if texte_nu(m.group(2)):
                lot.append(('p', m.group(2).strip()))
        else:
            items = items_de('<ul>%s</ul>' % m.group(2))
            if items:
                lot.append(('liste', items))
    return lot


def conseil_de(reponse_html):
    """La ligne « Conseil : … » que la fiche pose en fin de réponse.

    Son intitulé fait partie de la phrase : le retirer laissait un
    conseil qui ne dit plus qu'il en est un."""
    m = re.search(r'<p>\s*<strong>\s*(Conseil)\s*:?\s*</strong>\s*(.*?)</p>',
                  reponse_html or '', re.S | re.I)
    return ('%s : %s' % (m.group(1), texte_nu(m.group(2)))) if m else ''


GOOGLE_G = (
    '<path fill="#4285F4" d="M45.12 24.5c0-1.56-.14-3.06-.4-4.5H24v8.51h11.84c-.51 2.75-2.06 '
    '5.08-4.39 6.64v5.52h7.11c4.16-3.83 6.56-9.47 6.56-16.17z"/>'
    '<path fill="#34A853" d="M24 46c5.94 0 10.92-1.97 14.56-5.33l-7.11-5.52c-1.97 1.32-4.49 '
    '2.1-7.45 2.1-5.73 0-10.58-3.87-12.31-9.07H4.34v5.7C7.96 41.07 15.4 46 24 46z"/>'
    '<path fill="#FBBC05" d="M11.69 28.18C11.25 26.86 11 25.45 11 24s.25-2.86.69-4.18v-5.7H4.34'
    'C2.85 17.09 2 20.45 2 24s.85 6.91 2.34 9.88l7.35-5.7z"/>'
    '<path fill="#EA4335" d="M24 10.75c3.23 0 6.13 1.11 8.41 3.29l6.31-6.31C34.91 4.18 29.93 2 '
    '24 2 15.4 2 7.96 6.93 4.34 14.12l7.35 5.7c1.73-5.2 6.58-9.07 12.31-9.07z"/>')


def google(taille=20):
    """Le G de Google, en attribution de la source d'un avis.

    Ce n'est pas une décoration : c'est ce que le widget de la fiche
    affiche déjà, et c'est la seule chose que la source autorise à dire.
    La NOTE, elle, n'existe nulle part dans le relevé — ni globale, ni
    par avis — donc aucune étoile n'est dessinée (D30)."""
    return ('<svg class="gg" aria-hidden="true" width="%d" height="%d" viewBox="0 0 48 48">%s</svg>'
            % (taille, taille, GOOGLE_G))


def ico(nom, taille=18, classe=''):
    c = ' class="%s"' % classe if classe else ''
    return (f'<svg{c} aria-hidden="true" width="{taille}" height="{taille}" viewBox="0 0 24 24" '
            f'fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" '
            f'stroke-linejoin="round">{ICONES[nom]}</svg>')


def libelle_repere(valeur):
    """L'étiquette au-dessus d'un repère.

    Elle nomme la NATURE de la valeur, elle ne l'invente pas : « Rythme
    adapté » est un rythme, « Guide privatif » un guide. Quatre repères
    étiquetés « Sur place » à la suite ne disaient rien à personne."""
    v = valeur.lower()
    if 'jour' in v or 'nuit' in v:
        return 'Durée'
    if 'rythme' in v:
        return 'Rythme'
    if 'chauffeur' in v or 'véhicule' in v or 'transfert' in v:
        return 'Transport'
    if 'guide' in v:
        return 'Guide'
    if 'héberg' in v or 'hôtel' in v or 'lodge' in v or 'camp' in v:
        return 'Hébergement'
    if 'repas' in v or 'pension' in v:
        return 'Repas'
    return 'Sur place'


def icone_repere(libelle):
    l = libelle.lower()
    if 'jour' in l or 'nuit' in l:
        return 'horloge'
    if 'rythme' in l:
        return 'pas'
    if 'chauffeur' in l or 'véhicule' in l:
        return 'voiture'
    if 'guide' in l:
        return 'guide'
    if 'héberg' in l or 'famili' in l:
        return 'maison'
    return 'coche'


# ------------------------------------------------------------------ images

def image(entree, largeur_boite, hauteur_boite=None, sizes='100vw', priorite=False,
          classe='', legende_alt=None):
    """Une balise <img> qui ne peut pas être floue.

    `largeur_boite` est la largeur maximale, en pixels CSS, que la boîte
    donnera à l'image sur un grand écran. On n'y sert jamais une image
    plus petite : si l'original ne suit pas, c'est l'appelant qui doit
    réduire la boîte. `width` et `height` sont posés pour que le
    navigateur réserve la place et ne fasse pas sauter la page.
    """
    if not entree:
        return ''
    src = entree['src_original']
    alt = legende_alt if legende_alt is not None else (entree.get('alt') or '')
    att = ['src="%s"' % e(src), 'alt="%s"' % e(alt), 'decoding="async"']
    if entree.get('srcset'):
        att.append('srcset="%s"' % e(entree['srcset']))
        att.append('sizes="%s"' % e(sizes))
    if entree.get('largeur'):
        att.append('width="%d"' % entree['largeur'])
    if entree.get('hauteur'):
        att.append('height="%d"' % entree['hauteur'])
    att.append('fetchpriority="high"' if priorite else 'loading="lazy"')
    if classe:
        att.append('class="%s"' % classe)
    return '<img ' + ' '.join(att) + '>'


def plus_grande(images, sauf=()):
    lot = [x for x in images if x['base'] not in sauf and (x.get('largeur') or 0) > 0]
    return max(lot, key=lambda x: x['largeur']) if lot else None


# ------------------------------------------------------------------ accueil validé

def accueil():
    """Les blocs repris de l'accueil — depuis son INVENTAIRE, pas depuis
    la maquette.

    La maquette `maquettes/index.html` avait été promue source pour vingt
    pages sans jamais être confrontée à l'accueil en ligne. L'agent
    contrôle contenu du 09/09/2026 l'a fait : sur treize questions de la
    cliente, cinq étaient reprises, toutes reformulées, dont deux sans
    aucune source — un budget « 1 400 à 2 200 € pour 12 à 14 jours »
    qui n'existe nulle part, et une politique de zones (« nous
    n'organisons pas de séjour près de la frontière libyenne ») qui
    contredisait le séjour à Siwa vendu par la même page.

    On lit donc `docs/accueil.json`, relevé daté de la page en ligne, et
    les treize questions de la cliente s'affichent telles qu'elle les
    écrit — la seule retouche étant le visa passé à 30 €, qu'elle a
    demandé (backlog C1) et qui est déclarée dans l'inventaire.

    L'équipe reste vide tant que l'accueil ne nomme personne : les
    quatre prénoms de la maquette n'ont pas de source."""
    chemin = os.path.join(RACINE, 'docs', 'accueil.json')
    if not os.path.exists(chemin):
        sys.exit("l'inventaire de l'accueil manque : lancez outils/inventaire-accueil.py")
    with open(chemin, encoding='utf-8') as f:
        inv = json.load(f)
    pratique = [{'q': q['q'], 'html': q['reponse_html'], 'groupe': g['titre']}
                for g in inv['groupes'] for q in g['questions']]
    return {'pratique': pratique, 'etapes': [], 'equipe': inv.get('equipe') or [],
            'accueil': inv}


# ------------------------------------------------------------------ blocs communs

def bloc(nom):
    with open(os.path.join(MAQUETTES, 'assets', 'blocs', nom), encoding='utf-8') as f:
        return f.read().rstrip('\n')


# ------------------------------------------------------------------ feuille de style

CSS = r"""
/* =====================================================================
   GABARIT PROGRAMME — Authentique Égypte
   Couleurs, polices et formes : maquettes/assets/charte.css, à
   l'identique. Rien n'est inventé ici, tout est composé.

   Trois contraintes tenues par construction, et mesurées par
   outils/verif/lisibilite.js :
     · les marges de section prennent leurs valeurs dans une échelle
       (88/72/64/56/48/40 au bureau, 56/48/40/32/28 sur mobile) ;
     · aucun texte ne descend sous 15 px sur mobile ;
     · le gris de texte secondaire passe à #5A6069, qui donne 6,3:1 sur
       blanc quand le --gris de la charte n'en donne que 4,4:1.
   ===================================================================== */

/* Deux VARIABLES ajoutées à la charte, et aucune autre teinte de marque :
   un gris de texte qui passe 4,5:1 sur blanc (le --gris de la charte
   n'en donne que 4,4) et un or assombri pour les étoiles, qui atteint
   3:1 sur fond clair là où l'or de marque plafonne à 1,8. Les valeurs
   dérivées qui suivent (bruns de la note de production, verts et rouges
   des inclusions) sont celles de la charte ou leurs teintes de texte. */
.pg{--pg-max:1180px;--gris-lis:#5A6069;--or-fonce:#C08600;--ligne-pg:#E7E9EE}
.pg .wrap{width:min(100% - 40px,var(--pg-max));margin-inline:auto}
.pg h2{font-family:"Archivo",sans-serif;font-weight:600;letter-spacing:-.7px;
  font-size:clamp(1.6rem,2.6vw,2.15rem);line-height:1.18;margin:0 0 18px;color:var(--noir)}
.pg h3{font-family:"Archivo",sans-serif;font-weight:600;letter-spacing:-.3px;margin:0;color:var(--noir)}
.pg p{margin:0 0 1em}
.pg .eyebrow{color:var(--teal-txt)}
/* Nos règles arrivent après la charte : sans ces trois lignes, le titre
   du bloc devis repasse en noir sur le bleu profond (2,4:1 mesuré). */
.pg .devis h2,.pg .pg-sec--nuit h2{color:#fff}
.pg .eyebrow--clair{color:var(--or)}
.pg .devis li,.pg .devis p{color:#C3D5DA}
.pg-sec{padding:72px 0}
.pg-sec--serre{padding:56px 0}
.pg-sec--fond{background:var(--fond)}
.pg-sec--creme{background:var(--or-fond)}
.pg-sec--nuit{background:var(--nuit-900);color:#D7E4EA}
.pg-sec--nuit h2,.pg-sec--nuit h3{color:#fff}

/* ---------- bandeau de tête ---------- */
.pg .hero{position:relative;background:var(--nuit-900);overflow:hidden}
/* La photo nette ne dépasse jamais sa largeur réelle (--une-l) ; le
   flou derrière remplit le reste. Sans --une-l, rien ne borne : c'est
   le cas des couvertures de 1920 px, qui couvrent tout sans être
   étirées. */
.pg .hero__flou{position:absolute;inset:0;overflow:hidden}
.pg .hero__flou img{width:100%;height:100%;object-fit:cover;
  filter:blur(30px) saturate(1.15);transform:scale(1.15)}
/* overflow:hidden et min-height:0 ne sont pas décoratifs : l'image est
   un élément de GRILLE, et un élément de grille garde sa hauteur
   intrinsèque (min-height:auto). Une couverture portrait débordait donc
   de sa bande par le bas, hors du voile. */
.pg .hero__fond{position:absolute;inset:0;display:grid;justify-items:center;overflow:hidden}
.pg .hero__fond img{width:min(100%,var(--une-l,100%));height:100%;min-height:0;
  object-fit:cover}
/* Le voile couvre le BANDEAU ENTIER, pas la seule bande de photo nette :
   sinon la moitié basse du bandeau mobile restait en pleine lumière.
   Son plancher d'opacité est mesuré, pas choisi : le texte le plus
   clair du bandeau (#DCEAF0, 15 px) doit tenir 4,5:1 sur la photo la
   plus claire possible, et outils/verif/lisibilite.js le vérifie sur
   les pixels rendus, désormais, au lieu de renoncer devant une photo. */
/* Le voile est DIRIGÉ, pas uniforme : sombre là où le texte se pose,
   presque transparent là où la photo doit se voir. Un voile uniforme
   assez fort pour tenir 4,5:1 sous le chapô éteignait toute la photo ;
   un voile uniforme assez léger pour la laisser vivre descendait le H1
   à 2,79:1. Les deux couches ci-dessous font le travail chacune de son
   côté — l'une couche le bas-gauche où vivent le titre, le prix et les
   boutons, l'autre assied le bas du bandeau sur la section suivante —
   et outils/verif/lisibilite.js les mesure sur les pixels rendus. */
.pg .hero::after{content:"";position:absolute;inset:0;background:
  linear-gradient(96deg,rgba(5,35,50,.90) 0%,rgba(5,35,50,.84) 38%,
  rgba(5,35,50,.42) 68%,rgba(5,35,50,.20) 100%),
  linear-gradient(180deg,rgba(6,42,58,.34) 0%,rgba(6,42,58,0) 26%,
  rgba(5,35,50,.30) 72%,rgba(5,35,50,.80) 100%)}
/* z-index:1 est indispensable : ::after est le DERNIER enfant peint de
   .hero, donc il passe par-dessus le texte tant que celui-ci ne monte
   pas d'un cran. Sans cette ligne, le titre et les deux boutons partent
   sous le voile. */
.pg .hero__in{position:relative;z-index:1;padding:24px 0 56px}
.pg .hero .ariane{color:#C6DCE6;padding-top:0}
.pg .hero .ariane a{color:var(--or-clair)}
.pg .hero .ariane li::after{color:rgba(255,255,255,.45)}
.pg .hero .ariane [aria-current]{color:#fff}
.pg .hero__pills{display:flex;flex-wrap:wrap;gap:8px;margin:20px 0 18px}
/* Un voile BLANC translucide sur une photo claire ne fait qu'éclaircir
   le fond du texte blanc : les jetons tombaient à 4,03:1 sur mobile,
   mesuré au pixel. Le voile devient sombre — même effet de verre, mais
   il travaille dans le bon sens. */
.pg .pill{display:inline-flex;align-items:center;gap:7px;font-family:"Manrope",sans-serif;
  font-size:.84rem;font-weight:600;color:#fff;background:rgba(5,35,50,.82);
  border:1px solid rgba(255,255,255,.34);backdrop-filter:blur(8px);border-radius:var(--r-pill);padding:7px 14px}
.pg .hero h1{color:#fff;font-size:clamp(2rem,4.4vw,3.15rem);line-height:1.08;margin:0 0 14px;
  max-width:18ch;text-shadow:0 2px 20px rgba(0,0,0,.45);text-wrap:balance}
.pg .hero__chapo{color:#fff;font-size:1.12rem;line-height:1.6;max-width:54ch;margin:0 0 28px;
  font-weight:400;text-shadow:0 1px 12px rgba(0,0,0,.45)}
.pg .hero__bas{display:flex;flex-wrap:wrap;align-items:center;gap:16px 28px}
.pg .hero__prix{background:rgba(5,35,50,.72);backdrop-filter:blur(10px);
  border:1px solid rgba(255,255,255,.30);border-radius:var(--r-m);padding:12px 20px;color:#fff;
  font-family:"Manrope",sans-serif}
.pg .hero__prix small{display:block;font-size:.82rem;color:#fff}
.pg .hero__prix b{display:block;font-size:1.85rem;font-weight:700;letter-spacing:-1px;line-height:1.15}
.pg .hero__prix i{font-style:normal;font-size:.84rem;color:#DCEAF0}
.pg .hero__act{display:flex;flex-wrap:wrap;gap:12px}
.pg .btn--verre{background:rgba(255,255,255,.15);color:#fff;border-color:rgba(255,255,255,.42);
  backdrop-filter:blur(8px)}
.pg .btn--verre:hover{background:rgba(255,255,255,.28);border-color:#fff}
/* Le bouton de devis de l'entête commune : la règle .nav>a de la charte
   (0-1-1) écrase la couleur de .btn--or (0-1-0) et laisse un bleu sur
   fond or, à 2,7:1. On rétablit le contraste sans toucher à la charte. */
.entete .nav>a.btn--or{color:var(--nuit-900)}

/* ---------- repères ---------- */
.pg .reperes{background:var(--fond-2);border-bottom:1px solid var(--ligne-pg)}
/* Une grille à colonnes automatiques laissait le huitième repère seul
   sur une deuxième ligne, calé à gauche sous le premier. En flex, la
   dernière ligne se centre et l'orphelin cesse d'en être un. */
.pg .reperes ul{list-style:none;margin:0;padding:24px 0;display:flex;flex-wrap:wrap;
  justify-content:center;gap:20px 24px}
.pg .reperes li{flex:1 1 150px;max-width:230px}
.pg .reperes li{display:flex;flex-direction:column;align-items:center;text-align:center;gap:7px;
  font-family:"Manrope",sans-serif}
.pg .reperes li svg{color:var(--teal-txt)}
.pg .reperes small{font-size:.8rem;letter-spacing:.09em;text-transform:uppercase;color:var(--gris-lis)}
.pg .reperes b{font-size:.98rem;color:var(--nuit-900);font-weight:700;line-height:1.35}

/* ---------- deux colonnes ---------- */
.pg .deux{display:grid;grid-template-columns:minmax(0,1fr) 348px;gap:56px;
  padding:64px 0;align-items:start}
.pg .deux>.corps{min-width:0;display:grid;gap:56px}
.pg .prose{font-size:1.06rem;line-height:1.8;color:var(--texte);max-width:62ch}
.pg .prose p:last-child{margin-bottom:0}
.pg .prose strong{color:var(--nuit-900);font-weight:600}

/* ---------- note de production : ce qui est à trancher ---------- */


/* ---------- réponse encadrée : le module minimum de la doctrine ---------- */
.pg .bref{background:linear-gradient(135deg,var(--nuit-900) 0%,#0E6288 100%);
  border-radius:var(--r-l);padding:32px 34px;color:#fff;position:relative;overflow:hidden}
.pg .bref::after{content:"";position:absolute;right:-70px;top:-70px;width:220px;height:220px;
  border-radius:50%;background:radial-gradient(circle,rgba(251,181,14,.30),transparent 68%)}
.pg .bref .eyebrow{color:var(--or-clair)}
.pg .bref h2{color:#fff;margin-bottom:24px;position:relative}
.pg .bref__l{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));
  gap:22px 28px;margin:0;position:relative}
.pg .bref__l div{display:grid;gap:6px}
.pg .bref__l dt{display:flex;align-items:center;gap:8px;font-family:"Manrope",sans-serif;
  font-size:.86rem;letter-spacing:.06em;text-transform:uppercase;color:#D8E8F1;margin:0}
.pg .bref__l dt svg{color:var(--or-clair)}
.pg .bref__l dd{margin:0;font-family:"Manrope",sans-serif;line-height:1.35}
.pg .bref__l dd b{display:block;font-size:1.65rem;font-weight:800;letter-spacing:-.8px;color:#fff}
.pg .bref__l dd span{display:block;font-size:.92rem;color:#D8E8F1;margin-top:4px;line-height:1.5}
.pg .bref__src{position:relative;margin:26px 0 0;font-family:"Manrope",sans-serif;
  font-size:.86rem;color:#C3DAE7}

/* ---------- module : le bon format de séjour ---------- */
.pg .mod__aide{margin:-6px 0 18px;font-family:"Manrope",sans-serif;font-size:.96rem;
  color:var(--gris-lis)}
.pg .mod__apres{margin:18px 0 0;font-size:1rem;line-height:1.7;color:var(--texte)}
.pg .mod--valise .valise+.mod__intro{margin-top:22px}
.pg .mod--valise .mod__intro a,.pg .mod__apres a{color:var(--teal-txt);text-decoration:underline;
  text-underline-offset:3px}
.pg .mod__intro{font-family:"Manrope",sans-serif;font-size:1.02rem;color:var(--nuit-900);
  font-weight:600;margin:0 0 20px;max-width:62ch}
.pg .mod__conseil{display:flex;gap:11px;align-items:flex-start;margin:20px 0 0;padding:16px 18px;
  background:var(--or-fond);border-radius:var(--r-m);font-family:"Manrope",sans-serif;
  font-size:.98rem;color:#6B4B04;line-height:1.6;max-width:64ch}
.pg .mod__conseil svg{flex:0 0 auto;color:#B8860B;margin-top:2px}
.pg .duree{position:relative}
.pg .duree__r{position:absolute;opacity:0;pointer-events:none}
.pg .duree__ong{display:flex;flex-wrap:wrap;gap:10px;margin:0 0 18px}
.pg .duree__o{font-family:"Manrope",sans-serif;font-weight:700;font-size:.98rem;
  padding:12px 22px;border-radius:var(--r-pill);border:1.5px solid var(--ligne-pg);
  background:#fff;color:var(--nuit-900);cursor:pointer;transition:all .2s var(--ease);
  min-height:44px;display:inline-flex;align-items:center}
.pg .duree__o:hover{border-color:var(--teal);color:var(--teal-txt)}
.pg .duree__o:focus-visible{outline:3px solid var(--or);outline-offset:3px}
.pg .duree__c{display:none;background:var(--teal-fond);border:1px solid #CDE9EA;
  border-radius:var(--r-l);padding:24px 26px}
.pg .duree__c b{display:block;font-family:"Manrope",sans-serif;font-size:1.25rem;font-weight:800;
  color:var(--teal-txt);letter-spacing:-.4px;margin-bottom:8px}
.pg .duree__c p{margin:0;font-size:1.04rem;line-height:1.7;color:var(--texte);max-width:60ch}
/* Sans CSS ni JavaScript, les trois formats restent lisibles à la suite :
   c'est le mode dégradé qu'impose la doctrine. */
.pg .duree__r:nth-of-type(1):checked~.duree__ong .duree__o:nth-child(1),
.pg .duree__r:nth-of-type(2):checked~.duree__ong .duree__o:nth-child(2),
.pg .duree__r:nth-of-type(3):checked~.duree__ong .duree__o:nth-child(3),
.pg .duree__r:nth-of-type(4):checked~.duree__ong .duree__o:nth-child(4)
  {background:var(--nuit-900);border-color:var(--nuit-900);color:#fff}
.pg .duree__r:nth-of-type(1):checked~.duree__p .duree__c:nth-child(1),
.pg .duree__r:nth-of-type(2):checked~.duree__p .duree__c:nth-child(2),
.pg .duree__r:nth-of-type(3):checked~.duree__p .duree__c:nth-child(3),
.pg .duree__r:nth-of-type(4):checked~.duree__p .duree__c:nth-child(4){display:block}

/* ---------- module : la liste à cocher ---------- */
.pg .valise{list-style:none;margin:0;padding:0;display:grid;gap:10px}
.pg .valise label{display:flex;gap:14px;align-items:flex-start;background:#fff;
  border:1px solid var(--ligne-pg);border-radius:var(--r-m);padding:16px 18px;cursor:pointer;
  transition:border-color .2s var(--ease),background .2s var(--ease);min-height:44px}
.pg .valise label:hover{border-color:var(--teal)}
.pg .valise input{position:absolute;opacity:0;width:0;height:0}
.pg .valise__b{flex:0 0 auto;width:24px;height:24px;border-radius:7px;border:2px solid var(--ligne);
  display:grid;place-items:center;color:transparent;transition:all .18s var(--ease);margin-top:1px}
.pg .valise input:checked+.valise__b{background:var(--teal-txt);border-color:var(--teal-txt);color:#fff}
.pg .valise input:focus-visible+.valise__b{outline:3px solid var(--or);outline-offset:3px}
.pg .valise__t{font-size:1.02rem;line-height:1.55;color:var(--texte)}
.pg .valise__t b{color:var(--noir);font-family:"Manrope",sans-serif;font-weight:700}
.pg .valise__t span{display:block;color:var(--gris-lis);font-size:.98rem;margin-top:2px}
.pg .valise input:checked~.valise__t{opacity:.55;text-decoration:line-through;
  text-decoration-color:var(--ligne)}
.pg .valise__etat{margin:16px 0 0;font-family:"Manrope",sans-serif;font-size:.98rem;
  color:var(--gris-lis)}
.pg .valise__etat b{color:var(--teal-txt);font-weight:800}

/* ---------- votre guide : le texte, puis le carrousel de l'équipe ---------- */
.pg .guide{display:grid;grid-template-columns:1.15fr 1fr;gap:52px;align-items:center;
  margin:0 0 44px}
.pg .guide__intro{font-size:1.12rem;line-height:1.7;color:#C9DDE7;max-width:44ch;margin:0}
.pg .guide__r{list-style:none;margin:0;padding:0;display:grid;gap:14px}
.pg .guide__r li{display:flex;gap:13px;align-items:center;font-family:"Manrope",sans-serif;
  font-size:1.02rem;color:#fff}
.pg .guide__r svg{flex:0 0 auto;color:var(--or)}

/* Le carrousel d'équipe. Il défile nativement : glissement au doigt,
   flèches du clavier sur la piste (d'où le tabindex). Les deux boutons
   sont posés par le script et seulement si la piste déborde — sans
   JavaScript, on ne montre pas des commandes mortes. */
.pg .carr{border-top:1px solid rgba(255,255,255,.16);padding-top:34px}
.pg .carr__tete{display:flex;align-items:center;justify-content:space-between;gap:20px;
  margin:0 0 22px}
.pg .carr__tete h3{font-size:1.22rem;color:#fff;letter-spacing:-.2px}
.pg .carr__nav{display:flex;gap:10px;flex:0 0 auto}
.pg .carr__b{width:44px;height:44px;border-radius:50%;display:grid;place-items:center;
  background:rgba(255,255,255,.09);border:1px solid rgba(255,255,255,.3);color:#fff;
  cursor:pointer;transition:background .18s,border-color .18s}
.pg .carr__b:hover{background:var(--or);border-color:var(--or);color:var(--nuit-900)}
.pg .carr__b[disabled]{opacity:.38;cursor:default}
.pg .carr__b[disabled]:hover{background:rgba(255,255,255,.09);border-color:rgba(255,255,255,.3);
  color:#fff}
.pg .carr__b:first-child svg{transform:rotate(180deg)}
/* La barre de défilement reste VISIBLE par défaut : sans JavaScript,
   les boutons n'existent pas, et entre 861 et 1040 px deux personnes
   étaient alors hors d'atteinte à la souris. Le script, lui, pose la
   classe « js » et prend le relais avec ses deux boutons. */
.pg .carr__p{display:flex;gap:18px;overflow-x:auto;scroll-snap-type:x mandatory;
  scroll-behavior:smooth;scrollbar-width:thin;scrollbar-color:rgba(255,255,255,.4) transparent;
  padding:2px 2px 10px}
.pg .carr.js .carr__p{scrollbar-width:none;padding-bottom:2px}
.pg .carr.js .carr__p::-webkit-scrollbar{display:none}
.pg .carr__p:focus-visible{outline:2px solid var(--or);outline-offset:4px;border-radius:var(--r-m)}
/* Quatre cartes exactement dans la largeur : au bureau la piste ne
   déborde pas, les boutons restent donc cachés. */
.pg .carr__c{flex:0 0 calc((100% - 54px)/4);scroll-snap-align:start;
  background:linear-gradient(160deg,rgba(255,255,255,.11),rgba(255,255,255,.05));
  border:1px solid rgba(255,255,255,.18);border-radius:var(--r-l);padding:26px 24px 24px}
.pg .carr__m{width:60px;height:60px;border-radius:50%;background:var(--or);color:var(--nuit-900);
  display:grid;place-items:center;font-family:"Manrope",sans-serif;font-weight:800;
  font-size:1.4rem;margin:0 0 16px}
.pg .carr__c b{font-family:"Manrope",sans-serif;font-size:1.16rem;color:#fff;display:block;
  font-weight:700}
/* L'or de la charte donne 3,64:1 sur le composite de la carte
   (rgb 38,100,128) : sous le seuil de 4,5. Cet or éclairci en donne
   4,81 et reste le même or. */
.pg .carr__r{display:block;color:#FFD97F;font-family:"Manrope",sans-serif;font-size:.98rem;
  font-weight:600;margin-top:3px}
.pg .carr__f{list-style:none;margin:14px 0 0;padding:14px 0 0;display:grid;gap:7px;
  border-top:1px solid rgba(255,255,255,.16)}
.pg .carr__f li{font-size:.97rem;line-height:1.5;color:#CFE2EC}
.pg .carr__aide{margin:16px 0 0;font-family:"Manrope",sans-serif;font-size:.95rem;
  color:#A9C6D6;display:none}

/* ---------- carte de repérage : un bandeau large dans la lecture ---------- */
.pg .carte{--carte-mer:#DCEBF2;--carte-nil:#4FA3C7;--carte-terre:#F2E3C4;--carte-cote:#CBAE7C;
  margin:0;background:#fff;border:1px solid var(--ligne-pg);border-radius:var(--r-l);
  padding:22px 24px;box-shadow:var(--ombre)}
.pg .carte figcaption{padding:0}
.pg .carte__tete{display:flex;flex-direction:column}
.pg .carte__tete .eyebrow{order:-1}
.pg .carte h3{font-size:1.12rem;margin:0 0 16px;letter-spacing:-.3px}
.pg .carte .eyebrow{margin-bottom:8px}
.pg .carte__svg{display:block;width:100%;height:auto;border-radius:var(--r-m);
  border:1px solid var(--ligne-2)}
.pg .carte__d{fill:var(--nuit-900);stroke:#fff;stroke-width:3}
.pg .carte__halo{fill:var(--or);opacity:0;transition:opacity .25s var(--ease)}
.pg .carte__n{fill:#fff;font-family:"Manrope",sans-serif;font-size:14px;font-weight:800;
  text-anchor:middle}
.pg .carte__lbl{fill:var(--nuit-900);font-family:"Manrope",sans-serif;font-size:19px;font-weight:700;
  paint-order:stroke;stroke:rgba(255,255,255,.94);stroke-width:6px;stroke-linejoin:round}
.pg .carte__pt--titre .carte__d{fill:#fff;stroke:var(--rouge);stroke-width:3.6}
.pg .carte__pt--titre .carte__lbl{fill:var(--rouge)}
.pg .carte__pt.on .carte__halo{opacity:.35}
.pg .carte__pt.on .carte__d{fill:var(--or);stroke:var(--nuit-900)}
.pg .carte__pt.on .carte__n{fill:var(--nuit-900)}
.pg .carte__route{opacity:.9}
/* ---------- sommaire collant : où l'on en est dans le déroulé ---------- */
.pg .somm{background:#fff;border:1px solid var(--ligne-pg);border-radius:var(--r-l);padding:18px 16px}
.pg .somm__t{font-family:"Manrope",sans-serif;font-size:.8rem;letter-spacing:.12em;
  text-transform:uppercase;color:var(--gris-lis);margin:0 0 12px;padding:0 6px}
.pg .somm ol{list-style:none;margin:0;padding:0;display:grid;gap:2px;counter-reset:none}
.pg .somm a{display:grid;grid-template-columns:24px 1fr;gap:12px;align-items:baseline;
  font-family:"Manrope",sans-serif;font-size:.95rem;padding:9px 8px;border-radius:var(--r-s);
  transition:background .2s var(--ease);min-height:44px;align-content:center}
.pg .somm a:hover{background:var(--fond)}
.pg .somm li.on a{background:var(--or-fond)}
.pg .somm__n{width:24px;height:24px;border-radius:50%;background:var(--fond);color:var(--nuit-900);
  display:grid;place-items:center;font-size:.8rem;font-weight:800;align-self:center}
.pg .somm li.on .somm__n{background:var(--or);color:var(--nuit-900)}
.pg .somm b{color:var(--noir);font-weight:700;display:block;line-height:1.35}
.pg .somm span span{color:var(--gris-lis);font-size:.92rem;display:block;line-height:1.45;
  margin-top:2px}
.pg .carte__hors{display:flex;gap:9px;align-items:flex-start;margin:14px 0 0;padding:12px 14px;
  background:var(--rouge-fond);border-radius:var(--r-m);font-family:"Manrope",sans-serif;
  font-size:.92rem;color:#8A2F1C;line-height:1.5}
.pg .carte__hors svg{flex:0 0 auto;margin-top:2px}
.pg .carte__note{margin:14px 0 0;font-family:"Manrope",sans-serif;font-size:.86rem;
  color:var(--gris-lis);line-height:1.5;max-width:62ch}
.pg .carte__ech path{stroke:var(--nuit-900);stroke-width:3;stroke-linecap:butt;opacity:.75}
.pg .carte__ech text{fill:var(--nuit-900);font-family:"Manrope",sans-serif;font-size:15px;
  font-weight:700;text-anchor:middle;paint-order:stroke;stroke:rgba(255,255,255,.9);
  stroke-width:4px;opacity:.9}
/* La carte est dessinée une fois en 560 unités de large et affichée à
   deux tailles très différentes : 780 px dans la colonne de lecture,
   350 px sur un téléphone. Les textes du dessin sont donc redimensionnés
   par média, sinon ils sortent illisibles d'un côté ou énormes de l'autre. */
@media (min-width:861px){
  .pg .carte__lbl{font-size:12px;stroke-width:3.4px}
  .pg .carte__n{font-size:8px}
  .pg .carte__d{r:5.5px;stroke-width:1.8}
  .pg .carte__halo{r:13px}
  .pg .carte__ech text{font-size:9px;stroke-width:2.6px}
  .pg .carte__ech path{stroke-width:1.8}
  .pg .carte__route{stroke-width:2.4;stroke-dasharray:6 4}
}

/* ---------- repères d'étape : ce que dit la fiche, ce qu'on a mesuré ---------- */
.pg .reps{display:flex;flex-wrap:wrap;gap:9px;margin:0 0 18px}
.pg .rep{display:inline-flex;align-items:center;gap:7px;font-family:"Manrope",sans-serif;
  font-size:.9rem;font-weight:600;border-radius:var(--r-pill);padding:7px 14px;cursor:help}
/* Ce que la fiche écrit : plein, c'est la parole de l'agence. */
.pg .rep--fiche{background:var(--nuit-900);color:#fff}
.pg .rep--fiche svg{color:var(--or)}
/* Ce que nous avons calculé : en trait, pour qu'on ne confonde pas. */
.pg .rep--calc{background:#fff;color:var(--nuit-900);border:1.5px dashed var(--teal)}
.pg .rep--calc svg{color:var(--teal-txt)}
.pg .reps__src{margin:26px 0 0;padding:16px 18px;background:var(--fond);border-radius:var(--r-m);
  font-family:"Manrope",sans-serif;font-size:.9rem;color:var(--gris-lis);line-height:1.6;
  max-width:66ch}

/* ---------- fil d'Ariane sous le bandeau ---------- */
.pg .ariane--sous{border-bottom:1px solid var(--ligne-2);background:#fff}

/* ---------- galerie ---------- */
/* Cinq photos en trois colonnes avec une grande en 2×2 laissent une
   case vide en bas à droite. En QUATRE colonnes, la grande occupe
   exactement la moitié gauche et les quatre autres la moitié droite :
   le cadre est plein. Les autres comptes tiennent en trois colonnes
   sans case orpheline au milieu. */
.pg .galerie{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-bottom:12px}
.pg .galerie--5{grid-template-columns:repeat(4,1fr)}
.pg .galerie a{display:block;aspect-ratio:3/2;border-radius:var(--r-m);overflow:hidden;
  background:var(--fond)}
.pg .galerie img{width:100%;height:100%;object-fit:cover;display:block;
  transition:transform .5s var(--ease)}
.pg .galerie a:hover img{transform:scale(1.05)}
.pg .galerie a:first-child{grid-column:span 2;grid-row:span 2;aspect-ratio:auto}

/* ---------- les étapes en un coup d'œil ---------- */
.pg .apercu{background:var(--teal-fond);border:1px solid #CDE9EA;border-radius:var(--r-l);
  padding:28px 30px}
.pg .apercu h2{font-size:1.32rem;margin-bottom:16px}
.pg .apercu ol{list-style:none;margin:0;padding:0;display:grid;gap:8px}
.pg .apercu li{display:flex;gap:14px;align-items:baseline;background:rgba(255,255,255,.72);
  border-radius:var(--r-m);padding:12px 16px}
.pg .apercu .n{flex:0 0 auto;font-family:"Manrope",sans-serif;font-weight:800;font-size:.82rem;
  color:#fff;background:var(--teal-txt);border-radius:var(--r-pill);padding:3px 10px;letter-spacing:.03em}
.pg .apercu span.t{font-family:"Manrope",sans-serif;font-size:1rem;font-weight:600;
  color:var(--nuit-900);line-height:1.45}

/* ---------- jour par jour ---------- */
.pg .jour__tete{display:flex;align-items:center;gap:14px;margin:0 0 26px;padding:0 0 18px;
  border-bottom:2px solid var(--or)}
.pg .jour__no{order:-1;font-family:"Manrope",sans-serif;font-weight:800;font-size:.84rem;
  letter-spacing:.06em;color:var(--nuit-900);background:var(--or);border-radius:var(--r-pill);
  padding:6px 14px;flex:0 0 auto}
.pg .jour__tete h3{font-size:clamp(1.25rem,2vw,1.5rem)}
.pg .etape+.etape{margin-top:56px}
/* display:block est indispensable, pas cosmétique : la photo est portée
   par un <a>, donc un élément EN LIGNE, sur lequel une marge verticale
   est purement ignorée. La marge basse était déclarée à 40 px et
   l'écart mesuré au navigateur valait zéro. */
.pg .etape__photo{display:block;border-radius:var(--r-l);overflow:hidden;background:var(--fond);
  margin:0 0 36px;aspect-ratio:16/9}
.pg .etape__photo+*{margin-top:0}
.pg .etape__photo img{width:100%;height:100%;object-fit:cover;display:block;transition:transform .6s var(--ease)}
.pg .etape__photo:hover img{transform:scale(1.03)}
.pg .etape h4{font-family:"Archivo",sans-serif;font-size:1.24rem;font-weight:600;color:var(--noir);
  margin:0 0 18px;letter-spacing:-.3px;display:flex;align-items:center;gap:10px}
.pg .etape h4 svg{color:var(--teal-txt);flex:0 0 auto}
.pg .etape p{color:var(--texte);font-size:1.04rem;line-height:1.8;max-width:62ch}
.pg .mentions{display:flex;flex-wrap:wrap;gap:9px;margin:18px 0 0;padding:0}
.pg .jour>.mentions{margin-top:24px;padding-top:18px;border-top:1px solid var(--ligne-2)}
.pg .mention{display:inline-flex;align-items:center;gap:7px;font-family:"Manrope",sans-serif;
  font-size:.88rem;font-weight:600;color:var(--teal-txt);background:var(--teal-fond);
  border-radius:var(--r-pill);padding:7px 14px}

/* ---------- panneau collant ---------- */
/* min-width:0 : sans cela le bouton WhatsApp, que la charte empêche de
   revenir à la ligne, pousse la carte à 384 px dans une colonne de 348
   et fait dépasser le panneau de 36 px hors de la grille de la page. */
.pg .pan{position:sticky;top:88px;display:grid;gap:14px;min-width:0}
.pg .pan .btn{white-space:normal;text-align:center;line-height:1.35}
.pg .pan__carte{background:#fff;border:1px solid var(--ligne-pg);border-radius:var(--r-l);
  box-shadow:var(--ombre);padding:24px}
.pg .pan__prix small{display:block;font-family:"Manrope",sans-serif;font-size:.84rem;color:var(--gris-lis)}
.pg .pan__prix b{font-family:"Manrope",sans-serif;font-size:2.1rem;font-weight:800;color:var(--noir);
  letter-spacing:-1.2px;line-height:1.1}
.pg .pan__prix i{font-style:normal;font-family:"Manrope",sans-serif;font-size:.86rem;color:var(--gris-lis)}
.pg .pan__liste{list-style:none;margin:18px 0;padding:16px 0;border-top:1px solid var(--ligne-2);
  border-bottom:1px solid var(--ligne-2);display:grid;gap:11px;font-family:"Manrope",sans-serif;
  font-size:.96rem;color:var(--nuit-900)}
.pg .pan__liste li{display:flex;gap:11px;align-items:center}
.pg .pan__liste svg{color:var(--teal-txt);flex:0 0 auto}
.pg .pan__act{display:grid;gap:10px}
.pg .pan__note{font-family:"Manrope",sans-serif;font-size:.86rem;color:var(--gris-lis);
  margin:14px 0 0;text-align:center;line-height:1.5}
.pg .pan__avis{display:flex;flex-wrap:wrap;justify-content:center;align-items:baseline;gap:5px 9px;
  margin:14px 0 0;padding:14px 0 0;border-top:1px solid var(--ligne-2);
  font-family:"Manrope",sans-serif;font-size:.92rem;color:var(--gris-lis);text-align:center}
.pg .pan__avis .gg{flex:0 0 auto;align-self:center}
.pg .pan__avis b{color:var(--noir)}
.pg .pan__conf{background:var(--or-fond);border:1px solid #F6DEB0;border-radius:var(--r-l);padding:18px;
  font-family:"Manrope",sans-serif;font-size:.9rem;color:#6B4B04;display:grid;gap:6px;text-align:center}
.pg .pan__conf b{color:var(--noir);font-size:1rem}
.pg .pan__conf .et{color:var(--or-fonce);letter-spacing:.12em;font-size:1rem}

/* ---------- tarif ---------- */
.pg .tarif{border:1px solid var(--teal);border-radius:var(--r-l);overflow:hidden;
  font-family:"Manrope",sans-serif;max-width:520px}
.pg .tarif__ligne{display:flex;justify-content:space-between;align-items:center;gap:16px;
  padding:18px 22px;background:var(--teal-fond);color:var(--teal-txt);font-size:1rem;font-weight:600}
.pg .tarif__ligne b{font-size:1.45rem;font-weight:800;color:var(--noir);letter-spacing:-.8px}
.pg .tarif__ligne b small{font-size:.82rem;font-weight:500;color:var(--gris-lis);letter-spacing:0}
.pg .note{font-family:"Manrope",sans-serif;font-size:.9rem;color:var(--gris-lis);
  margin:14px 0 0;line-height:1.6;max-width:68ch}

/* ---------- inclusions ---------- */
.pg .incl{display:grid;grid-template-columns:1fr 1fr;gap:28px}
.pg .incl__col{border:1px solid var(--ligne-pg);border-radius:var(--r-l);padding:24px 26px;background:#fff}
.pg .incl__col--oui{background:var(--vert-fond);border-color:#CFE6D8}
.pg .incl__col--non{background:var(--fond);border-color:var(--ligne-pg)}
.pg .incl h3{display:flex;align-items:center;gap:10px;font-size:1.1rem;margin:0 0 16px}
.pg .incl__col--oui h3 svg{color:var(--vert)}
.pg .incl__col--non h3 svg{color:var(--rouge)}
.pg .incl ul{list-style:none;margin:0;padding:0;display:grid;gap:12px;font-size:1rem;color:var(--texte)}
.pg .incl li{display:flex;gap:11px;align-items:flex-start;line-height:1.55}
.pg .incl li svg{flex:0 0 auto;margin-top:3px}
.pg .incl__col--oui li svg{color:var(--vert)}
.pg .incl__col--non li svg{color:var(--rouge)}

/* ---------- accordéons : les deux FAQ ---------- */
.pg .faqs{display:grid;grid-template-columns:1.25fr 1fr;gap:44px;align-items:start}
/* La colonne de gauche porte huit questions, celle de droite cinq :
   sans cela, la seconde s'arrête à mi-hauteur et laisse un vide. */
.pg .faqs>div:last-child{position:sticky;top:88px}
.pg .acc{display:grid;gap:12px}
.pg .acc details{background:#fff;border:1px solid var(--ligne-pg);border-radius:var(--r-m);
  overflow:hidden;transition:border-color .2s var(--ease),box-shadow .2s var(--ease)}
.pg .acc details[open]{border-color:var(--or);box-shadow:var(--ombre)}
.pg .acc summary{list-style:none;cursor:pointer;display:flex;align-items:center;gap:14px;
  padding:18px 20px;font-family:"Archivo",sans-serif;font-weight:600;font-size:1.04rem;
  color:var(--noir);letter-spacing:-.2px;line-height:1.4;min-height:44px}
.pg .acc summary::-webkit-details-marker{display:none}
.pg .acc summary::after{content:"";flex:0 0 auto;margin-left:auto;width:22px;height:22px;
  background:var(--or-fond);border-radius:50%;position:relative;transition:transform .25s var(--ease)}
.pg .acc summary::before{content:"";position:absolute;right:29px;width:10px;height:2px;
  background:#7A5605;border-radius:2px}
.pg .acc details[open] summary::after{transform:rotate(180deg);background:var(--or)}
.pg .acc summary:hover{color:var(--teal-txt)}
.pg .acc summary span.q{flex:1}
.pg .acc__plus{position:relative;flex:0 0 auto;margin-left:auto;width:24px;height:24px;
  border-radius:50%;background:var(--or-fond);display:grid;place-items:center;
  transition:background .2s var(--ease),transform .25s var(--ease);color:#7A5605}
.pg .acc details[open] .acc__plus{background:var(--or);color:var(--nuit-900);transform:rotate(45deg)}
.pg .acc__plus::before,.pg .acc__plus::after{content:"";position:absolute;background:currentColor;border-radius:2px}
.pg .acc__plus::before{width:11px;height:2px}
.pg .acc__plus::after{width:2px;height:11px}
.pg .acc summary::after,.pg .acc summary::before{content:none}
.pg .acc__c{padding:0 20px 20px;color:var(--texte);font-size:1rem;line-height:1.75;max-width:64ch}
.pg .acc__c :last-child{margin-bottom:0}
.pg .acc__c p{margin:0 0 .85em}
.pg .acc__c ul{list-style:none;margin:0 0 .9em;padding:0;display:grid;gap:9px}
.pg .acc__c ul li{position:relative;padding-left:22px}
.pg .acc__c ul li::before{content:"";position:absolute;left:2px;top:.62em;width:7px;height:7px;
  border-radius:50%;background:var(--or)}
.pg .acc__c strong{color:var(--nuit-900);font-weight:600}
/* Les réponses de la cliente portent parfois leurs propres titres. Sans
   interligne, un H3 de deux lignes se serre à 1,25 — sous le plancher. */
.pg .acc__c h3,.pg .acc__c h4{font-size:1.05rem;line-height:1.45;margin:18px 0 8px}
.pg .acc__c h3:first-child,.pg .acc__c h4:first-child{margin-top:0}
.pg .acc__c a{color:var(--teal-txt);text-decoration:underline;text-underline-offset:3px}
.pg .acc__vide{color:#7A5605;background:var(--or-fond);border:1px dashed var(--or);
  border-radius:var(--r-s);padding:10px 14px;font-family:"Manrope",sans-serif;font-size:.94rem}

/* ---------- le mur d'avis : deux colonnes qui défilent ----------
   La boucle repose sur une règle simple : chaque colonne porte DEUX
   fois ses cartes et remonte de la moitié exacte de sa hauteur. D'où la
   marge sur les cartes plutôt qu'un `gap` sur la piste — un `gap`
   n'existe qu'ENTRE les enfants, la moitié de la hauteur tomberait
   alors un demi-écart trop haut et la boucle sauterait à chaque tour.
   La marge est portée par un <article>, donc un élément de bloc : elle
   s'applique (ce n'est pas le cas d'un <a>, voir .etape__photo). */
.pg .mur__tete{display:flex;flex-wrap:wrap;align-items:flex-end;gap:16px 28px;margin:0 0 26px}
.pg .mur__tete>div:first-child{flex:1 1 340px}
.pg .mur__tete h2{margin:0}
.pg .mur__cpt{margin:0;font-family:"Manrope",sans-serif;line-height:1.45}
.pg .mur__cpt b{display:block;font-size:1.05rem;color:var(--noir);font-weight:700}
.pg .mur__cpt small{display:block;font-size:.94rem;color:var(--gris-lis);margin-top:2px}
/* La case est le bouton : le défilement s'arrête donc sans JavaScript,
   comme l'exige le critère 2.2.2. Elle reste dans le flux du clavier,
   seulement dérobée à l'œil. */
.pg .mur__stop{position:absolute;width:1px;height:1px;margin:-1px;padding:0;border:0;
  overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
.pg .mur__btn{display:inline-flex;align-items:center;gap:9px;min-height:44px;padding:0 18px;
  border-radius:var(--r-pill);border:1px solid var(--ligne-pg);background:#fff;cursor:pointer;
  font-family:"Manrope",sans-serif;font-size:.96rem;font-weight:600;color:var(--gris-lis);
  transition:border-color .18s,color .18s}
.pg .mur__btn:hover{border-color:var(--nuit);color:var(--nuit-900)}
.pg .mur__btn svg{color:var(--or-fonce)}
.pg .mur__btn .b{display:none}
.pg .mur__stop:checked~.mur__tete .mur__btn .a{display:none}
.pg .mur__stop:checked~.mur__tete .mur__btn .b{display:inline}
.pg .mur__stop:focus-visible~.mur__tete .mur__btn{outline:2px solid var(--teal-txt);
  outline-offset:3px}

.pg .mur{display:grid;grid-template-columns:1fr 1fr;gap:26px;align-items:start}
/* Chaque colonne est un PANNEAU encadré, et la fenêtre de défilement est
   à l'intérieur. Deux raisons, et la seconde est un défaut mesuré :
   la fenêtre est la colonne et non la grille, sinon une grille à une
   colonne sur téléphone effacerait cinq avis sur dix ; et le cadre est
   séparé de la fenêtre parce que le fondu qui adoucit les bords ronge
   tout ce qu'il traverse, cadre compris. Sans lui, sur téléphone, la
   carte coupée en bas du premier panneau et celle coupée en haut du
   second se lisaient comme une seule — le texte d'un voyageur suivi de
   la signature d'un autre. */
.pg .mur__c{background:var(--fond-2);border:1px solid var(--ligne-pg);
  border-radius:var(--r-l);padding:18px}
.pg .mur__f{height:664px;overflow:hidden;
  -webkit-mask-image:linear-gradient(180deg,transparent,#000 48px,#000 calc(100% - 48px),transparent);
  mask-image:linear-gradient(180deg,transparent,#000 48px,#000 calc(100% - 48px),transparent)}
/* display:flow-root n'est pas cosmétique. Sans lui, la marge basse de
   la DERNIÈRE carte fusionne à travers .mur__p puis .mur__d — ni l'un
   ni l'autre n'ayant bordure, padding ou contexte de formatage — et la
   piste mesure 2×période − 22 px. La moitié tombait alors 11 px trop
   haut : la boucle sautait à chaque tour, mesuré sur les deux colonnes
   et aux trois largeurs. */
.pg .mur__d{display:flow-root;animation:mur var(--d,90s) linear infinite;will-change:transform}
.pg .mur__c:nth-child(2) .mur__d{animation-direction:reverse}
@keyframes mur{from{transform:translateY(0)}to{transform:translateY(-50%)}}
/* Trois façons d'arrêter : le bouton, le survol, le focus clavier. */
.pg .mur:hover .mur__d,.pg .mur:focus-within .mur__d,
.pg .mur__stop:checked~.mur .mur__d{animation-play-state:paused}
.pg .mur__a{background:#fff;border:1px solid var(--ligne-pg);border-radius:var(--r-l);
  padding:24px;margin:0 0 22px;box-shadow:0 2px 10px rgba(16,32,48,.05)}
.pg .mur__q{display:block;font-family:"Archivo",serif;font-size:2.4rem;line-height:.6;
  color:var(--or);margin:6px 0 12px}
.pg .mur__a blockquote{margin:0;font-size:1rem;line-height:1.7;color:var(--texte)}
.pg .mur__a footer{display:flex;align-items:center;gap:12px;font-family:"Manrope",sans-serif;
  font-size:.9rem;color:var(--gris-lis);border-top:1px solid var(--ligne-2);
  padding-top:14px;margin-top:16px}
.pg .mur__a footer b{color:var(--noir);display:block;font-weight:700}
.pg .ini{width:38px;height:38px;border-radius:50%;background:var(--nuit);color:#fff;display:grid;
  place-items:center;font-weight:700;font-size:.9rem;flex:0 0 auto}
/* Le G de Google porte ses propres couleurs : il lui faut un rond clair
   et non le bleu nuit des initiales, sinon le bleu du logo s'y noie. */
.pg .ini--g{background:#fff;border:1px solid var(--ligne-pg);box-shadow:0 1px 2px rgba(16,32,48,.06)}
/* Le mur au repos : plus d'animation, la liste entière. Deux cas, la
   même règle — et elle est déclarée APRÈS les blocs responsives, à la
   fin de la feuille, sinon « height:420px » du bloc mobile revenait
   par-dessus « overflow:visible » et le mur débordait de 2 500 px sur
   la suite de la page. */

/* ---------- séjours proches ---------- */
.pg .proches{display:grid;grid-template-columns:repeat(3,1fr);gap:24px}
.pg .proches a{display:block;color:inherit;text-decoration:none}
.pg .proches__img{aspect-ratio:4/3;border-radius:var(--r-l);overflow:hidden;background:var(--fond);
  margin:0 0 14px}
.pg .proches__img img{width:100%;height:100%;object-fit:cover;display:block;transition:transform .5s var(--ease)}
.pg .proches a:hover img{transform:scale(1.05)}
.pg .proches h3{font-size:1.08rem;line-height:1.35;margin:0 0 6px}
.pg .proches a:hover h3{color:var(--teal-txt)}
.pg .proches p{font-family:"Manrope",sans-serif;font-size:.94rem;color:var(--gris-lis);margin:0}
.pg .proches p b{color:var(--noir);font-size:1.02rem}
.pg .proches__tous{text-align:center;margin:32px 0 0}

/* ---------- barre mobile ---------- */
.pg-mob{display:none;position:fixed;left:0;right:0;bottom:0;z-index:70;background:#fff;
  border-top:1px solid var(--ligne-pg);box-shadow:0 -6px 22px rgba(11,81,112,.15);
  padding:10px 16px calc(10px + env(safe-area-inset-bottom));align-items:center;gap:14px}
.pg-mob .p{font-family:"Manrope",sans-serif;line-height:1.25;flex:1;min-width:0}
.pg-mob .p small{display:block;font-size:.86rem;color:var(--gris-lis)}
.pg-mob .p b{font-size:1.15rem;color:var(--noir);font-weight:800;letter-spacing:-.5px}
.pg-mob .p i{font-style:normal;font-size:.86rem;color:var(--gris-lis)}

/* ---------- visionneuse ---------- */
.pg-lb{position:fixed;inset:0;z-index:120;background:rgba(5,25,35,.94);display:none;
  align-items:center;justify-content:center;padding:24px}
.pg-lb[open],.pg-lb.on{display:flex}
.pg-lb img{max-width:min(100%,1400px);max-height:88vh;border-radius:var(--r-m);display:block}
.pg-lb button{position:absolute;top:18px;right:18px;background:rgba(255,255,255,.16);color:#fff;
  border:1px solid rgba(255,255,255,.4);border-radius:var(--r-pill);padding:11px 20px;
  font-family:"Manrope",sans-serif;font-weight:700;font-size:1rem;min-height:44px}

/* =====================================================================
   RESPONSIVE — les marges restent dans l'échelle mobile 56/48/40/32/28
   ===================================================================== */

@media (max-width:1040px){
  .pg .guide{grid-template-columns:1fr;gap:32px}
  .pg .carr__c{flex-basis:calc((100% - 18px)/2.2)}
  .pg .carr__aide{display:block}
  .pg .bref{padding:28px 24px}
  /* Le prix est dans le bandeau, 200 px plus haut, et dans la barre du
     bas : trois fois sur un écran de téléphone, c'est deux fois de trop. */
  .pg .pan__prix{display:none}
  .pg .carte{padding:16px}
  /* minmax(0,1fr) et non 1fr : un « 1fr » nu laisse la colonne grandir
     jusqu'au contenu le plus large. Le bouton WhatsApp, que la charte
     empêche de revenir à la ligne, portait ainsi la colonne à 386 px
     dans une page de 350 — 16 px de défilement horizontal, mesurés. */
  .pg .deux{grid-template-columns:minmax(0,1fr);gap:40px;padding:48px 0}
  .pg .devis__act .btn{white-space:normal;text-align:center;line-height:1.35}
  .pg .pan{position:static;order:-1}
  .pg .faqs{grid-template-columns:1fr;gap:48px}
  .pg .faqs>div:last-child{position:static}
  .pg .proches{grid-template-columns:1fr 1fr}
  .pg .incl{grid-template-columns:1fr;gap:20px}
}
@media (max-width:860px){
  /* Le bandeau mobile : la photo occupe le premier écran en entier et
     le titre se pose dedans, dans son bas. Sa hauteur est BORNÉE à
     470 px, et ce n'est pas un choix esthétique : au-delà, un écran
     étroit et haut réclame à l'image plus de pixels qu'elle n'en a
     (mesuré ×1,34 en densité 2 sur une photo de 1920 px) et la photo
     devient floue. À 470 px, le facteur retombe à 0,87. */
  .pg .hero{background:var(--nuit-900)}
  /* Sur téléphone le texte prend toute la largeur : le voile dirigé
     n'a plus de côté où s'effacer, il redevient vertical.
     Le flou garde toute la hauteur ; seule la photo NETTE se limite à
     la bande que sa propre définition permet. */
  /* Sur mobile le texte occupe TOUTE la hauteur du bandeau : le creux
     du voile à 22 % laissait le chapô à 4,02:1 et le « À partir de » à
     4,17:1, mesurés au pixel. Il n'y a pas de zone sans texte où
     s'éclaircir. */
  .pg .hero::after{background:
    linear-gradient(180deg,rgba(6,42,58,.68) 0%,rgba(6,42,58,.66) 22%,
    rgba(5,35,50,.82) 58%,rgba(5,35,50,.95) 100%)}
  .pg .hero__fond{position:absolute;top:0;left:0;right:0;height:var(--une-h,470px)}
  .pg .hero__in{padding:14px 0 34px}
  /* Le bloc titre se colle au BAS de la photo, quelle que soit la
     longueur du titre : la marge automatique fait le calcul, pas moi. */
  .pg .hero__in>.wrap{display:flex;flex-direction:column;min-height:456px}
  .pg .hero .ariane{padding-bottom:0}
  .pg .hero .ariane ol{flex-wrap:nowrap;overflow-x:auto;overscroll-behavior-x:contain;
    scrollbar-width:none;-ms-overflow-style:none}
  .pg .hero .ariane ol::-webkit-scrollbar{display:none}
  .pg .hero .ariane li{white-space:nowrap}
  .pg .hero__pills{margin:auto 0 16px;gap:7px}
  .pg .hero h1{font-size:2.15rem;max-width:14ch}
  .pg .hero__chapo{margin-bottom:0}
  .pg .hero__bas{margin-top:28px}
  .pg .hero__bas{gap:14px}
  .pg .hero__prix,.pg .hero__act{width:100%}
  .pg .hero__act .btn{flex:1}
  .pg-sec{padding:48px 0}
  .pg-sec--serre{padding:40px 0}
  .pg .deux{padding:40px 0;gap:32px}
  .pg .deux>.corps{gap:48px}
  .pg-mob{display:flex}
  .pg .proches{grid-template-columns:1fr}
  /* Les deux fenêtres se rangent l'une sous l'autre : sans une
     gouttière franche, la carte coupée en bas de la première et celle
     coupée en haut de la seconde se lisent comme une seule, avec le
     texte d'un voyageur et la signature d'un autre. */
  .pg .mur{grid-template-columns:1fr;gap:22px}
  .pg .mur__f{height:420px}
  .pg .carr__c{flex-basis:86%}
  .pg .galerie{grid-template-columns:1fr 1fr}
  .pg .galerie a:first-child{grid-column:span 2;grid-row:auto;aspect-ratio:3/2}
  .pg .hero__in{padding:24px 0 40px}
}
@media (max-width:600px){
  /* Plancher mobile : rien sous 15 px. Le retour du 24/08 portait
     précisément là-dessus, et l'outil de lisibilité le vérifie. */
  .pg .reperes small,.pg .hero__prix small,.pg .hero__prix i,.pg .pan__prix small,
  .pg .pan__prix i,.pg .pan__note,.pg .note,.pg .proches p,.pg .mur__a footer,
  .pg .pg-mob .p small,.pg .pan__conf,.pg .mention,.pg .pill,.pg .acc__vide{font-size:.95rem}
  .pg .reperes b,.pg .pan__liste,.pg .apercu span.t{font-size:1rem}
  .pg .ariane,.pg .eyebrow,.pg .apercu .n,.pg .jour__no,.pg .tarif__ligne b small,
  .pg .mur .ini,.pg .acc__c,.pg .devis__act small,
  .pg .rep,.pg .reps__src,.pg .carte__note,.pg .carte__hors,.pg .somm,
  .pg .somm span span,.pg .somm__t,.pg .valise__t span,.pg .carr__f li,.pg .carr__aide,
  .pg .pan__avis{font-size:.95rem}
  .pg .duree__c{padding:20px}
  .pg-mob .p small{font-size:.95rem}
  .pg .eyebrow{letter-spacing:.1em}
  .pg .hero h1{font-size:1.95rem;letter-spacing:-.8px}
  .pg .hero__chapo{font-size:1.05rem}
  .pg .apercu{padding:22px}
  .pg .incl__col,.pg .pan__carte{padding:20px}
  .pg .acc summary{font-size:1.02rem;padding:16px 18px}
  .pg .acc__c{padding:0 18px 18px}
  .pg .etape+.etape{margin-top:44px}
  .pg .etape__photo{margin-bottom:32px}
  body{padding-bottom:84px}
}
@media (prefers-reduced-motion:reduce){.pg *,.pg *::before,.pg *::after{transition:none!important}}

/* ---------- le mur au repos ----------
   Deux situations où le défilement dessert la lecture, et la même
   réponse : la liste entière, sans mouvement.

   · mouvement réduit : le visiteur l'a demandé ;
   · sous 861 px : mesurées à 390 px, huit des dix cartes sont plus
     hautes que la fenêtre. Le lecteur qui met en pause au milieu d'un
     avis n'avait aucun moyen d'en voir la fin — il fallait relancer et
     attendre un tour de soixante secondes. Un bouton de pause qui ne
     sert à rien ne remplit pas le critère 2.2.2.

   Ces règles viennent en FIN de feuille : à spécificité égale, c'est la
   dernière qui gagne, et les blocs responsives sont au-dessus. */
@media (prefers-reduced-motion:reduce),(max-width:860px){
  .pg .mur__f{height:auto;overflow:visible;-webkit-mask-image:none;mask-image:none}
  .pg .mur__d{animation:none}
  .pg .mur__p[aria-hidden]{display:none}
  .pg .mur__btn,.pg .mur__stop{display:none}
}
"""


SCRIPT = r"""
(function(){
  // Visionneuse : la photo s'ouvre dans sa taille d'origine.
  var lb=document.getElementById('pg-lb'), img=lb&&lb.querySelector('img');
  if(lb){
    document.querySelectorAll('[data-lb]').forEach(function(a){
      a.addEventListener('click',function(ev){
        ev.preventDefault();
        img.src=a.getAttribute('href'); img.alt=a.getAttribute('data-alt')||'';
        lb.classList.add('on'); lb.querySelector('button').focus();
      });
    });
    // removeAttribute et non src='' : un src vide se résout en l'URL
    // de la PAGE, que le navigateur re-télécharge alors comme image.
    function fermer(){ lb.classList.remove('on'); img.removeAttribute('src'); }
    lb.addEventListener('click',function(ev){ if(ev.target===lb||ev.target.tagName==='BUTTON') fermer(); });
    document.addEventListener('keydown',function(ev){ if(ev.key==='Escape') fermer(); });
  }

  // Les onglets de durée fonctionnent en CSS pur ; le clavier a besoin
  // d'une ligne de plus, les libellés n'étant pas des boutons.
  document.querySelectorAll('.duree__o').forEach(function(l){
    l.addEventListener('keydown',function(ev){
      if(ev.key==='Enter'||ev.key===' '){ ev.preventDefault(); l.click(); }
    });
  });

  // La liste d'équipement coche nativement ; le compteur est un confort.
  var valise=document.getElementById('valise'), etat=document.getElementById('valise-etat');
  if(valise&&etat){
    var cases=valise.querySelectorAll('input[type=checkbox]');
    var gabarit=etat.innerHTML;
    function compter(){
      var reste=0; cases.forEach(function(c){ if(!c.checked) reste++; });
      etat.innerHTML = reste ? gabarit.replace(/<b>\d+<\/b>/,'<b>'+reste+'</b>')
                                     .replace(/élément(s?) à/, (reste>1?'éléments à':'élément à'))
                             : '\u2713 ' + VALISE_FINI;
    }
    cases.forEach(function(c){ c.addEventListener('change',compter); });
    compter();
  }

  // Le carrousel de l'équipe glisse déjà au doigt et aux flèches du
  // clavier ; les deux boutons sont un confort, et on ne les montre que
  // s'il y a vraiment quelque chose à faire défiler.
  var piste=document.getElementById('equipe');
  if(piste){
    // La classe dit « le script est là » : la barre de défilement peut
    // s'effacer, les boutons prennent le relais.
    piste.closest('.carr').classList.add('js');
    var nav=document.querySelector('.carr__nav');
    var bts=nav?nav.querySelectorAll('.carr__b'):[];
    function pas(){ var c=piste.querySelector('.carr__c');
      return c?c.getBoundingClientRect().width+18:320; }
    function etat(){
      var deborde=piste.scrollWidth>piste.clientWidth+4;
      if(nav) nav.hidden=!deborde;
      if(!deborde) return;
      var fin=piste.scrollWidth-piste.clientWidth-2;
      bts[0].disabled=piste.scrollLeft<=2;
      bts[1].disabled=piste.scrollLeft>=fin;
    }
    bts.forEach(function(b){
      b.addEventListener('click',function(){
        piste.scrollBy({left:pas()*(+b.dataset.carr),behavior:'smooth'});
      });
    });
    piste.addEventListener('scroll',etat,{passive:true});
    window.addEventListener('resize',etat);
    etat();
  }

  // La carte suit la lecture : l'étape qu'on lit s'allume sur la carte.
  var pts=document.querySelectorAll('.carte__pt'), lignes=document.querySelectorAll('.carte__l li');
  var etapes=document.querySelectorAll('.etape[data-lieu]');
  if(pts.length&&etapes.length&&'IntersectionObserver' in window){
    function porte(el,lieu){ return (' '+el.dataset.lieu+' ').indexOf(' '+lieu+' ')>=0; }
    function allumer(lieu){
      pts.forEach(function(g){ g.classList.toggle('on', porte(g,lieu)); });
      lignes.forEach(function(l){ l.classList.toggle('on', porte(l,lieu)); });
    }
    var vues=new Map();
    var obs=new IntersectionObserver(function(entrees){
      entrees.forEach(function(x){ vues.set(x.target, x.isIntersecting?x.intersectionRatio:0); });
      var meilleur=null, score=0;
      vues.forEach(function(v,k){ if(v>score){ score=v; meilleur=k; } });
      if(meilleur) allumer(meilleur.dataset.lieu);
    },{rootMargin:'-25% 0px -45% 0px',threshold:[0,.25,.5,1]});
    etapes.forEach(function(x){ obs.observe(x); });
  }
})();
"""


# ------------------------------------------------------------------ sections

def hero(inv):
    une = inv.get('image_une') or plus_grande(inv['images'])
    pills = [inv['categorie']['nom']]
    for r in inv['reperes']:
        if re.search(r'jour|nuit|guide', r, re.I):
            pills.append(r)
    # La photo de couverture n'a pas la même taille d'une fiche à
    # l'autre : 1920 px sur Siwa, 1280 sur « Pyramides, Louxor et mer
    # rouge ». Servie en plein écran, la seconde était agrandie de 31 %
    # sur téléphone — mesuré, pas supposé.
    #
    # Elle n'est donc JAMAIS étirée au-delà de sa taille réelle : elle
    # est centrée à sa largeur, et ce qui reste de part et d'autre est la
    # même photo, floutée. Une image floutée ne peut pas être floue :
    # c'est ce qui permet de remplir l'écran sans mentir sur la netteté
    # (D14). Sur téléphone, la bande est ramenée à ce que la hauteur de
    # la photo permet à densité 2.
    large = (une.get('largeur') or 0) if une else 0
    haut = (une.get('hauteur') or 0) if une else 0
    etroite = bool(une) and 0 < large < 1920
    style = ''
    if large:
        style = ' style="--une-l:%dpx;--une-h:%dpx"' % (
            large, max(300, min(470, haut // 2)) if haut else 470)
    o = ['<section class="hero"%s>' % style]
    if une:
        # Le flou est posé sur TOUTE la hauteur du bandeau, toujours, et
        # pas seulement derrière une couverture étroite. Sur mobile la
        # photo nette n'occupe qu'une bande (--une-h) : sous cette bande
        # apparaissait la photo BRUTE, non assombrie, avec une couture
        # nette en travers des boutons — 50 px sur le désert Blanc,
        # 160 px sur la fiche famille, mesurés.
        o.append('<div class="hero__flou" data-flou="oui" aria-hidden="true">%s</div>'
                 % image(une, large or 1920, sizes='100vw'))
        o.append('<div class="hero__fond">' +
                 image(une, min(1920, large) or 1920, priorite=True,
                       sizes=('(max-width:%dpx) 100vw, %dpx' % (large, large))
                       if etroite else '100vw') + '</div>')
    o.append('<div class="hero__in"><div class="wrap">')
    o.append('<div class="hero__pills">' + ''.join(
        '<span class="pill">%s%s</span>' % (
            ico(icone_repere(p), 15) if p != inv['categorie']['nom'] else ico('pin', 15), e(p))
        for p in pills[:4]) + '</div>')
    o.append('<h1>%s</h1>' % e(inv['h1']))
    if inv['chapo']:
        o.append('<p class="hero__chapo">%s</p>' % e(inv['chapo']))
    o.append('<div class="hero__bas">')
    if inv['prix']['texte']:
        o.append('<div class="hero__prix"><small>%s</small><b>%s</b><i>%s</i></div>'
                 % (e(INTERFACE['depuis']), e(inv['prix']['texte']), e(suffixe_prix(inv))))
    o.append('<div class="hero__act">'
             f'<a class="btn btn--or" href="{DEVIS}">{e(INTERFACE["cta_devis"])}</a>'
             f'<a class="btn btn--verre" href="{WHATSAPP}">{ico("bulle", 18)} {e(INTERFACE["cta_whatsapp"])}</a>'
             '</div>')
    o.append('</div></div></div></section>')
    return '\n'.join(o)


def ariane_ol(inv):
    return '<div class="wrap">' + ariane(inv) + '</div>'


def ariane(inv):
    return ('<ol>'
            f'<li><a href="{SITE}/">{e(INTERFACE["ariane_accueil"])}</a></li>'
            f'<li><a href="{SITE}/nos-sejours-egypte/">{e(INTERFACE["ariane_sejours"])}</a></li>'
            f'<li><a href="{e(inv["categorie"]["url"])}">{e(inv["categorie"]["nom"])}</a></li>'
            f'<li><span aria-current="page">{e(inv["h1"])}</span></li></ol>')


def reperes(inv):
    """La bande de repères sous le bandeau.

    Deux règles apprises sur les fiches autres que Siwa :

    · la DURÉE annoncée par l'encart de prix (« 6 jours minimum ») n'est
      pas toujours dans les repères. Elle ne s'affichait alors nulle
      part : un chiffre de la cliente, perdu. Elle est ajoutée quand les
      repères ne la portent pas déjà ;
    · quand les repères de la fiche sont, mot pour mot, sa liste
      d'inclusions — c'est le cas de « Pyramides, Louxor et mer rouge en
      famille » — les afficher revient à donner trois fois la même liste
      sur la même page. On ne garde alors que le prix et la durée.
    """
    memes = ([x.strip().lower() for x in inv['reperes']]
             == [x.strip().lower() for x in inv.get('inclus') or []]) and bool(inv['reperes'])
    lot = [] if memes else list(inv['reperes'])
    # La durée annoncée n'est ajoutée QUE si les repères n'en portent
    # aucune. La fiche Siwa en annonce deux qui se contredisent (« 4
    # jours » et « 3 jours minimum ») : deux tuiles « DURÉE » côte à côte
    # donneraient la contradiction pour une caractéristique. Elle est
    # l'affaire du bandeau de vérification, qui la nomme (D19).
    if not any(re.search(r'\d+\s*(jours?|nuits?)', r, re.I) for r in lot):
        for d in inv.get('durees') or []:
            lot.insert(0, d)
            break

    o = ['<section class="reperes"><div class="wrap"><ul>']
    if inv['prix']['texte']:
        o.append('<li>%s<small>%s</small><b>%s</b></li>'
                 % (ico('euro', 22), e(INTERFACE['depuis']), e(inv['prix']['texte'])))
    for r in lot:
        o.append('<li>%s<small>%s</small><b>%s</b></li>'
                 % (ico(icone_repere(r), 22), e(libelle_repere(r)), e(r)))
    o.append('</ul></div></section>')
    return '\n'.join(o)


def presentation(inv):
    if not inv['presentation']:
        return ''
    o = ['<section>', '<p class="eyebrow">%s</p>' % e(INTERFACE['eyebrow_sejour'])]
    # Le chapô est déjà sous le titre, dans le bandeau : le répéter en
    # H2 le donnait deux fois sur le même écran. La fiche a son propre
    # intitulé de section (« Vue d'ensemble ») : c'est celui-là.
    titre = inv.get('presentation_titre') or inv['chapo']
    if titre:
        o.append('<h2>%s</h2>' % e(titre))
    o.append('<div class="prose">' + ''.join('<p>%s</p>' % e(p) for p in inv['presentation']) + '</div>')
    o.append('</section>')
    return '\n'.join(o)


def apercu(inv):
    """Les titres d'étapes du déroulé, en un coup d'œil. Rien d'écrit."""
    titres = [(j, et) for j in inv['jours'] for et in j['etapes'] if et['titre']]
    if len(titres) < 2:
        return ''
    o = ['<section class="apercu">', '<h2>%s</h2><ol>' % e(INTERFACE['titre_etapes'])]
    for i, (j, et) in enumerate(titres, start=1):
        o.append('<li><span class="n">%s</span><span class="t">%s</span></li>'
                 % (('J%s' % rang_jour(j)) if j['numerote'] else ('%d' % i), e(et['titre'])))
    o.append('</ol></section>')
    return '\n'.join(o)


# Les durées que la FICHE écrit elle-même : « 2h30 et 3h00 », « 8 à 10
# heures ». Elles priment sur tout calcul, et s'affichent comme ce
# qu'elles sont — la parole de l'agence.
DUREE_FICHE = re.compile(
    r'\b(\d{1,2}\s*h\s*\d{2}(?:\s*(?:et|à|a)\s*\d{1,2}\s*h\s*\d{2})?'
    r'|\d{1,2}\s*(?:à|a)\s*\d{1,2}\s*heures?'
    r'|\d{1,3}\s*minutes?'
    r'|\d{1,2}\s*heures?)\b', re.I)
DIST_FICHE = re.compile(r'\b(\d{1,4}\s*km)\b', re.I)
# « le départ se fait vers 1h00 » est une HEURE, « la marche dure entre
# 2h30 et 3h00 » est une durée. Les deux s'écrivent pareil. Sans ces
# deux filtres, la page affichait « 1h00 » et « 12h00 » comme des temps
# de trajet — des chiffres faux sur une page qui vend un voyage.
AVANT_HEURE = re.compile(r"(vers|d[èe]s|aux alentours de|[àa] partir de|départ [àa]|[àa])\s*$", re.I)
AVANT_DUREE = re.compile(r"(dur[ée]e?|durent|s['’]effectue|effectue\s+en|compter|pr[ée]voir"
                         r"|pendant|au bout de|marche\s+(?:de|qui)|trajet\s+de|route\s+de"
                         r"|ascension\s+de|descente\s+\w+\s+en|environ).{0,28}$", re.I)


def charger_trajets():
    """Les trajets relevés par `outils/trajets.py`, s'il y en a."""
    chemin = os.path.join(PROGRAMMES, '_trajets.json')
    if not os.path.exists(chemin):
        return {}
    with open(chemin, encoding='utf-8') as f:
        return json.load(f).get('trajets', {})


def duree_lisible(minutes):
    h, m = divmod(int(minutes), 60)
    if not h:
        return '%d min' % m
    return '%d h' % h if not m else '%d h %02d' % (h, m)


def reperes_etape(et, depuis, vers, trajets):
    """Les repères d'une étape : ce que la fiche dit, ce qu'on a mesuré.

    Deux origines, deux allures, jamais mélangées. Un chiffre calculé
    porte sa source et sa date dans son infobulle ; un chiffre écarté
    par le contrôle de vraisemblance n'apparaît pas."""
    chips = []
    texte = ' '.join([et.get('titre', '')] + et.get('paragraphes', []))
    for motif, icone, quoi in ((DUREE_FICHE, 'horloge', 'Durée'), (DIST_FICHE, 'pas', 'Distance')):
        for m in motif.finditer(texte):
            avant = texte[max(0, m.start() - 60):m.start()]
            if quoi == 'Durée':
                if AVANT_HEURE.search(avant) or not AVANT_DUREE.search(avant):
                    continue                    # une heure de la journée, pas une durée
            valeur = re.sub(r'\s+', ' ', m.group(1)).strip()
            chips.append('<span class="rep rep--fiche" title="%s annoncée par la fiche du site">'
                         '%s%s</span>' % (e(quoi), ico(icone, 14), e(valeur)))
            break
    if depuis and vers and depuis != vers:
        t = trajets.get(depuis + '>' + vers)
        if t and not t.get('douteux'):
            chips.append('<span class="rep rep--calc" title="%s — relevé le %s">%s%s</span>'
                         % (e(t['source']), e(date_fr(t['releve'])), ico('voiture', 14),
                            e('%d km · %s de route' % (t['km'], duree_lisible(t['minutes'])))))
    return ('<p class="reps">' + ''.join(chips) + '</p>') if chips else ''


def mentions_html(lot):
    """Les repas et les nuits, là où la fiche les écrit.

    Elles ferment l'étape qu'elles concernent : les remonter au jour
    entier faisait perdre à quelle étape on dort et où l'on mange."""
    if not lot:
        return ''
    return ('<p class="mentions">' + ''.join(
        '<span class="mention">%s%s</span>'
        % (ico('lit' if re.search(r'nuit|héberg', m, re.I) else 'repas', 14), e(m))
        for m in lot) + '</p>')




# ------------------------------------------------------------------ carte

# Les coordonnées sont des faits géographiques, pas du contenu : elles
# ne sont ni écrites ni interprétées, elles situent des lieux que la
# fiche NOMME. Un lieu absent du texte n'apparaît jamais sur la carte.
# nom · longitude · latitude · motif de détection · décalage vertical du
# libellé · côté où l'écrire ('d' à droite du point, 'g' à gauche).
# Le monastère et le sommet sont à quatre kilomètres l'un de l'autre :
# leurs points se touchent à cette échelle. Les coordonnées restent
# exactes, seuls les LIBELLÉS s'écartent.
LIEUX = {
    'le-caire':          ('Le Caire',        31.236, 30.044, r'\ble caire\b|\bcaire\b',   -8, 'g'),
    'siwa':              ('Oasis de Siwa',   25.519, 29.203, r'\bsiwa\b',                    0, 'd'),
    'alexandrie':        ('Alexandrie',      29.919, 31.200, r'\balexandrie\b',            -10, 'g'),
    'marsa-matrouh':     ('Marsa Matrouh',   27.237, 31.353, r'marsa\s*matrouh',            -10, 'd'),
    'bahariya':          ('Bahariya',        28.858, 28.349, r'bahariya|baharia',             0, 'g'),
    'farafra':           ('Farafra',         27.972, 27.058, r'farafra',                      0, 'g'),
    'desert-blanc':      ('Désert Blanc',    27.850, 27.250, r'd[ée]sert\s+blanc',          16, 'g'),
    'fayoum':            ('Fayoum',          30.844, 29.310, r'fayoum',                       8, 'g'),
    'louxor':            ('Louxor',          32.640, 25.687, r'louxor|louqsor',               0, 'd'),
    'assouan':           ('Assouan',         32.899, 24.089, r'assouan|aswan',                0, 'd'),
    'abou-simbel':       ('Abou Simbel',     31.626, 22.337, r'abou\s*simbel|abu\s*simbel',  0, 'g'),
    'hurghada':          ('Hurghada',        33.812, 27.257, r'hurghada',                     0, 'd'),
    'charm-el-cheikh':   ('Charm el-Cheikh', 34.330, 27.915, r'sharm\s*el[- ]?sheikh|charm\s*el[- ]?cheikh', 22, 'd'),
    'dahab':             ('Dahab',           34.513, 28.501, r'\bdahab\b',                   2, 'd'),
    'sainte-catherine':  ('Sainte-Catherine', 33.938, 28.556, r'sainte[- ]catherine',        -16, 'd'),
    'mont-moise':        ('Mont Moïse',      33.975, 28.470, r'mont\s+mo[ïi]se|gebel\s+moussa', 4, 'd'),
}

# Le fond de carte vient de Natural Earth 1:50m (domaine public),
# extrait une fois par `outils/carte-egypte.py` et versionné. Le tracé
# dessiné à la main de la première version était joli et faux.
def fond_de_carte():
    chemin = os.path.join(RACINE, 'outils', 'carte-egypte.json')
    if not os.path.exists(chemin):
        return None
    with open(chemin, encoding='utf-8') as f:
        return json.load(f)


# Le dessin fait TOUJOURS 560 unités de large, quel que soit le séjour
# cadré : c'est ce qui permet d'écrire une seule fois la taille des
# libellés, et qu'ils sortent lisibles sur les quatorze fiches.
LARGEUR_CARTE = 560.0
# Largeur moyenne d'un caractère du libellé, en unités du dessin. La
# police vaut 19 unités dans le cas le plus serré (l'affichage mobile,
# où la carte est réduite le plus fort) et un caractère de Manrope en
# occupe un peu plus de la moitié. Sert à savoir si une étiquette sort
# du cadre — et, si elle sort, à la basculer de l'autre côté avant
# d'élargir la carte, qui s'aplatirait.
LARGEUR_CAR = 10.0
# L'Égypte s'étend du 22e au 32e parallèle : une carte qui la cadre en
# entier tient dans ce rapport. On garde le cadrage entre ces bornes,
# sinon un séjour très étalé d'est en ouest donne un bandeau plat.
RAPPORT = (1.45, 2.35)                          # largeur / hauteur admissibles
BORNES = (23.4, 38.6, 21.2, 32.5)               # jusqu'où le cadrage peut s'ouvrir


def cadrer(lons, lats):
    """La fenêtre de la carte : les lieux, de la marge, et un rapport
    de forme tenable."""
    lo1, lo2, la1, la2 = min(lons), max(lons), min(lats), max(lats)
    mx = max((lo2 - lo1) * 0.22, 1.7)
    my = max((la2 - la1) * 0.30, 1.4)
    lo1, lo2 = lo1 - mx * 1.4, lo2 + mx * 1.9   # de la place pour les libellés
    la1, la2 = la1 - my, la2 + my

    for _ in range(40):
        cos_lat = math.cos(math.radians((la1 + la2) / 2))
        rapport = ((lo2 - lo1) * cos_lat) / (la2 - la1)
        if rapport > RAPPORT[1] and (la1 > BORNES[2] or la2 < BORNES[3]):
            manque = ((lo2 - lo1) * cos_lat / RAPPORT[1] - (la2 - la1)) / 2
            la1, la2 = max(BORNES[2], la1 - manque), min(BORNES[3], la2 + manque)
        elif rapport < RAPPORT[0] and (lo1 > BORNES[0] or lo2 < BORNES[1]):
            manque = ((la2 - la1) * RAPPORT[0] / cos_lat - (lo2 - lo1)) / 2
            lo1, lo2 = max(BORNES[0], lo1 - manque), min(BORNES[1], lo2 + manque)
        else:
            break
    cos_lat = math.cos(math.radians((la1 + la2) / 2))
    echelle = LARGEUR_CARTE / ((lo2 - lo1) * cos_lat)
    return {'lo1': lo1, 'la2': la2, 'cos': cos_lat, 'echelle': echelle,
            'larg': round(LARGEUR_CARTE, 1), 'haut': round((la2 - la1) * echelle, 1)}


def projeter(lon, lat, c):
    return (round((lon - c['lo1']) * c['cos'] * c['echelle'], 1),
            round((c['la2'] - lat) * c['echelle'], 1))


def trace(points, c, fermer=False):
    if not points:
        return ''
    d = 'M' + ' L'.join('%s %s' % projeter(x, y, c) for x, y in points)
    return d + (' Z' if fermer else '')


def lieu_de(texte):
    """Le lieu que ce texte nomme EN PREMIER.

    L'ordre du texte, pas l'ordre du répertoire : une étape qui commence
    par « l'ascension du mont Moïse » et cite le monastère de
    Sainte-Catherine trois lignes plus bas parle du mont, pas du
    monastère."""
    t = (texte or '').lower()
    trouve = None
    for cle, fiche in LIEUX.items():
        m = re.search(fiche[3], t, re.I)
        if m and (trouve is None or m.start() < trouve[0]):
            trouve = (m.start(), cle)
    return trouve[1] if trouve else ''


def nom_du_lieu(cle, inv):
    """Le nom d'un lieu, tel que la FICHE l'écrit.

    Le répertoire porte « Charm el-Cheikh », l'orthographe employée par
    l'agence en août ; cette fiche-ci écrit « Sharm el-Sheikh ». D25 dit
    que les lieux sont ceux que la fiche NOMME : c'est donc sa graphie
    qui s'affiche, sur la carte comme au sommaire, et le répertoire ne
    sert plus qu'à reconnaître le lieu et à le placer."""
    label, _, _, motif = LIEUX[cle][:4]
    # La PLUS LONGUE des graphies employées, pas la première rencontrée :
    # le motif accepte « le caire » comme « caire », et « Arrivée au
    # Caire » figurant avant « Le Caire » dans la fiche, la carte
    # affichait « Caire » tout court.
    formes = [m.group(0).strip() for m in re.finditer(motif, texte_du_sejour(inv), re.I)]
    if formes:
        forme = max(formes, key=len)
        if forme.lower() != label.lower() and len(forme) >= len(label) - 3:
            return forme[0].upper() + forme[1:]
    return label


def texte_du_sejour(inv):
    """Tout ce que la fiche écrit, en un seul bloc, pour y chercher."""
    if '_texte' not in inv:
        bouts = [inv.get('h1') or '', inv.get('chapo') or '']
        bouts += inv.get('presentation') or []
        # La FAQ écrit « Le Caire : pyramides, sphinx » là où le déroulé
        # écrit « Arrivée au Caire » : c'est la même fiche, et la
        # graphie la plus complète est celle qu'on affiche.
        for f in inv.get('faq') or []:
            bouts += [f.get('q') or '', texte_nu(f.get('reponse_html') or '')]
        for j in inv['jours']:
            bouts.append(j['titre'])
            for et in j['etapes']:
                bouts.append(et['titre'])
                bouts += et['paragraphes']
        inv['_texte'] = ' '.join(x for x in bouts if x)
    return inv['_texte']


def lieux_du_sejour(inv):
    """Les lieux nommés par le séjour, dans l'ordre où on les rencontre.

    Deux origines, et la distinction porte une affirmation lourde : un
    lieu « annoncé » est un lieu que le TITRE DU SÉJOUR promet et que le
    déroulé ne décrit jamais. Sur la fiche Siwa, c'est vrai de Siwa
    elle-même — le déroulé y décrit le Sinaï — et la carte le montre au
    lieu de le taire.

    C'est donc une affirmation sur le contenu de la cliente, et elle
    doit être juste. Elle ne l'était pas : les titres de jours étaient
    comptés comme des annonces, et comme un lieu déjà vu n'était plus
    repris, « Arrivée au Caire » suffisait à classer Le Caire parmi les
    absents — sur une fiche où le déroulé parle du Caire pendant deux
    jours. Le titre d'un jour fait partie du déroulé : il le décrit, il
    ne l'annonce pas. Et un lieu vu d'abord dans le titre du séjour puis
    décrit ensuite n'est plus un absent : il est PROMU."""
    ordre, rang_par_cle = [], {}

    def ajoute(cle, origine, etape='', rang_dom=0):
        if not cle:
            return
        if cle in rang_par_cle:
            x = ordre[rang_par_cle[cle]]
            if origine == 'deroule' and x['origine'] != 'deroule':
                x.update({'origine': 'deroule', 'etape': etape, 'rang_dom': rang_dom})
            return
        rang_par_cle[cle] = len(ordre)
        ordre.append({'cle': cle, 'origine': origine, 'etape': etape,
                      'rang_dom': rang_dom})

    # Ce que le séjour ANNONCE : son titre, et lui seul.
    for mot in re.split(r'\s*[-–—]\s*', inv['h1']):
        ajoute(lieu_de(mot), 'titre')
    # Ce que le séjour DÉCRIT : ses étapes, titre du jour compris. Une
    # étape muette reste là où la précédente s'est arrêtée — on ne se
    # téléporte pas entre deux paragraphes.
    dernier, rang = '', 0
    for j in inv['jours']:
        for i, et in enumerate(j['etapes']):
            rang += 1
            bouts = ([j['titre']] if i == 0 else []) + [et['titre']] + et['paragraphes']
            cle = lieu_de(' '.join(x for x in bouts if x)) or dernier
            if cle:
                dernier = cle
                ajoute(cle, 'deroule', et['titre'] or j['titre'], rang)
    return ordre


def index_etapes(inv):
    """Le sommaire du déroulé, collant à côté du texte.

    Il tient le même rôle que la carte : savoir où l'on en est. Chaque
    ligne mène à son étape et s'allume avec elle."""
    lot = [x for x in lieux_du_sejour(inv) if x['origine'] == 'deroule']
    if len(lot) < 2:
        return ''
    o = ['<nav class="somm" aria-label="%s"><p class="somm__t">%s</p><ol>'
         % (e(INTERFACE['titre_sommaire']), e(INTERFACE['titre_sommaire']))]
    for i, x in enumerate(lot, start=1):
        o.append('<li data-lieu="%s"><a href="#etape-%d"><span class="somm__n">%d</span>'
                 '<span><b>%s</b>%s</span></a></li>'
                 % (e(x['cle']), x['rang_dom'], i, e(nom_du_lieu(x['cle'], inv)),
                    ('<span>%s</span>' % e(x['etape'])) if x['etape'] else ''))
    o.append('</ol></nav>')
    return '\n'.join(o)


def carte(inv):
    """La carte de repérage : où mène ce séjour, étape par étape.

    Le cadrage suit le séjour : on montre la région qu'il traverse, avec
    assez de pays autour pour qu'on se situe. Les lieux sont ceux que la
    fiche NOMME, à leurs coordonnées réelles ; le trait de côte et le Nil
    viennent de Natural Earth."""
    fond = fond_de_carte()
    lot = lieux_du_sejour(inv)
    if not fond or len(lot) < 2:
        return ''
    etapes = [x for x in lot if x['origine'] == 'deroule']

    # Deux lieux distants de quatre kilomètres — le monastère et le
    # sommet — sont le MÊME point à l'échelle d'un pays. On les réunit
    # plutôt que de les superposer ou de les écarter, ce qui reviendrait
    # à mentir sur leurs coordonnées.
    groupes = []
    for x in lot:
        fiche = LIEUX[x['cle']]
        pose = False
        for g in groupes:
            if (abs(g['lon'] - fiche[1]) < 0.12 and abs(g['lat'] - fiche[2]) < 0.12
                    and g['deroule'] == (x['origine'] == 'deroule')):
                g['cles'].append(x['cle'])
                g['noms'].append(nom_du_lieu(x['cle'], inv))
                g['etapes'].append(x['etape'])
                if x in etapes:
                    g['rangs'].append(etapes.index(x) + 1)
                pose = True
                break
        if not pose:
            groupes.append({'cles': [x['cle']], 'noms': [nom_du_lieu(x['cle'], inv)],
                            'lon': fiche[1], 'lat': fiche[2],
                            'dy': fiche[4] if len(fiche) > 4 else 0,
                            'cote': fiche[5] if len(fiche) > 5 else 'd',
                            'etapes': [x['etape']],
                            'rangs': [etapes.index(x) + 1] if x in etapes else [],
                            'deroule': x['origine'] == 'deroule'})

    def poser(c):
        pts = []
        for g in groupes:
            px, py = projeter(g['lon'], g['lat'], c)
            rangs = g['rangs']
            # Un point qui réunit plusieurs lieux ne porte que le
            # premier sur la carte : « Sainte-Catherine · Mont Moïse »
            # écrit en toutes lettres occupait 60 % de la largeur du
            # dessin. Le sommaire, lui, les nomme tous les deux.
            pts.append({'cle': g['cles'][0], 'cles': ' '.join(g['cles']),
                        'nom': g['noms'][0],
                        'noms': ' · '.join(g['noms']), 'x': px, 'y': py, 'dy': g['dy'],
                        'cote': g['cote'], 'etape': g['etapes'][0], 'deroule': g['deroule'],
                        'rang': rangs[0] if rangs else 0,
                        'rangs': ('%d-%d' % (rangs[0], rangs[-1])) if len(rangs) > 1
                                 else (str(rangs[0]) if rangs else '')})
        return pts

    # Le cadrage s'élargit jusqu'à ce que les libellés tiennent dedans :
    # « Sainte-Catherine · Mont Moïse » écrit à droite d'un point de la
    # côte du Sinaï sortait du dessin.
    lons = [g['lon'] for g in groupes]
    lats = [g['lat'] for g in groupes]
    c = cadrer(lons, lats)
    for _ in range(4):
        pts = poser(c)
        # Premier recours : un libellé qui sort à droite passe à gauche,
        # et l'inverse. C'est gratuit, et ça évite d'élargir le cadre.
        for q in pts:
            large = len(q['nom']) * LARGEUR_CAR + 18
            if q['cote'] == 'd' and q['x'] + large > LARGEUR_CARTE and q['x'] - large > 0:
                q['cote'] = 'g'
            elif q['cote'] == 'g' and q['x'] - large < 0 and q['x'] + large < LARGEUR_CARTE:
                q['cote'] = 'd'
        deborde_d = max([q['x'] + 18 + len(q['nom']) * LARGEUR_CAR
                         for q in pts if q['cote'] == 'd'] + [0]) - LARGEUR_CARTE
        deborde_g = -min([q['x'] - 18 - len(q['nom']) * LARGEUR_CAR
                          for q in pts if q['cote'] == 'g'] + [0])
        if deborde_d < 4 and deborde_g < 4:
            break
        par_degre = c['echelle'] * c['cos']
        lons = lons + [max(lons) + max(deborde_d, 0) / par_degre,
                       min(lons) - max(deborde_g, 0) / par_degre]
        c = cadrer(lons, lats)
        cotes = {q['cle']: q['cote'] for q in pts}
        for g in groupes:
            g['cote'] = cotes.get(g['cles'][0], g['cote'])
    larg, haut = c['larg'], c['haut']
    route = [q for q in pts if q['deroule']]

    # L'échelle : une barre dont on sait ce qu'elle vaut.
    for km in (1000, 500, 200, 100, 50, 20):
        px_km = c['echelle'] / 111.0
        if km * px_km < larg * 0.34:
            barre = (km, round(km * px_km, 1))
            break
    else:
        barre = (20, round(20 * c['echelle'] / 111.0, 1))

    o = ['<figure class="carte">',
         '<figcaption class="carte__tete"><h3>%s</h3><p class="eyebrow">%s</p></figcaption>'
         % (e(INTERFACE['titre_carte']), e(INTERFACE['eyebrow_carte'])),
         '<svg viewBox="0 0 %s %s" role="img" aria-label="%s" class="carte__svg">'
         % (larg, haut, e('Carte situant les étapes du séjour en Égypte')),
         '<rect width="%s" height="%s" fill="var(--carte-mer)"/>' % (larg, haut),
         '<path d="%s" fill="var(--carte-terre)" stroke="var(--carte-cote)" stroke-width="1.6"/>'
         % trace(fond['contour'], c, True)]
    for anneau in fond.get('nasser', []):
        o.append('<path d="%s" fill="var(--carte-nil)" opacity=".85"/>'
                 % trace(anneau, c, True))
    for troncon in fond.get('nil', []):
        o.append('<path d="%s" fill="none" stroke="var(--carte-nil)" stroke-width="2.6" '
                 'stroke-linecap="round" stroke-linejoin="round"/>' % trace(troncon, c))

    if len(route) > 1:
        o.append('<path class="carte__route" d="%s" fill="none" stroke="var(--or)" '
                 'stroke-width="4" stroke-dasharray="10 7" stroke-linecap="round"/>'
                 % ('M' + ' L'.join('%s %s' % (q['x'], q['y']) for q in route)))

    for q in pts:
        droite = q['cote'] == 'd'
        cl = 'carte__pt' + ('' if q['deroule'] else ' carte__pt--titre')
        o.append('<g class="%s" id="pt-%s" data-lieu="%s">' % (cl, e(q['cle']), e(q['cles'])))
        o.append('<circle class="carte__halo" cx="%s" cy="%s" r="22"/>' % (q['x'], q['y']))
        o.append('<circle class="carte__d" cx="%s" cy="%s" r="9"/>' % (q['x'], q['y']))
        if q['rangs']:
            o.append('<text class="carte__n" x="%s" y="%s">%s</text>'
                     % (q['x'], q['y'] + 4.8, e(q['rangs'])))
        o.append('<text class="carte__lbl" x="%s" y="%s" text-anchor="%s">%s</text>'
                 % (q['x'] + (18 if droite else -18), q['y'] + 7.5 + q['dy'] * 1.8,
                    'start' if droite else 'end', e(q['nom'])))
        o.append('</g>')

    ex, ey = round(larg * 0.045, 1), round(haut * 0.955, 1)
    o.append('<g class="carte__ech"><path d="M%s %s h%s" /><text x="%s" y="%s">%d km</text></g>'
             % (ex, ey, barre[1], round(ex + barre[1] / 2, 1), round(ey - 4, 1), barre[0]))
    o.append('</svg>')

    hors = [q['nom'] for q in pts if not q['deroule']]
    if hors:
        o.append('<p class="carte__hors">%s%s</p>'
                 % (ico('etoile', 14),
                    e('Annoncé par le titre du séjour, absent du déroulé : ' + ', '.join(hors))))
    o.append('<figcaption class="carte__note">%s %s</figcaption></figure>'
             % (e(INTERFACE['carte_note']), e(fond['source'])))
    return '\n'.join(o)


# ------------------------------------------------------------------ modules d'attention
#
# Doctrine NavBoost, étape 3 bis d'`operationnel-contenu` : deux leviers
# seulement, gagner le clic et terminer la session. Le module ne se
# choisit pas par goût, il se lit dans le relevé SERP du 09/09/2026 sur
# « voyage oasis de siwa egypte » :
#
#   · un AI Overview au-dessus du premier organique  → réponse encadrée
#     et chiffre daté, renforcés ;
#   · cinq pages de paragraphes, aucun outil          → la place est
#     libre pour un module qui répond à la variable de la requête ;
#   · la variable de cette requête est la DURÉE — « Combien de temps
#     prévoir » est à la fois une question de la fiche et une recherche
#     associée de la SERP                             → sélecteur ;
#   · « Autres questions posées » : trois des quatre sont déjà répondues
#     par la fiche                                    → FAQ conservée.
#
# Les six règles de construction sont tenues : aucune dépendance, le
# module fonctionne sans JavaScript (le sélecteur est en CSS pur, la
# liste en cases natives), rien de ce qui compte n'est injecté au clic,
# les éléments sont accessibles au clavier, la mise en page ne bouge
# pas, et TOUTES les données sortent de la fiche de la cliente.


def en_bref(inv):
    """La réponse encadrée : ce qu'un visiteur veut savoir en dix secondes.

    Quatre chiffres, tous relevés sur la fiche, tous datés. C'est aussi
    ce qu'un modèle de langue recopie quand il cite une page."""
    lignes = []
    if inv['prix']['texte']:
        lignes.append(('euro', INTERFACE['depuis'], inv['prix']['texte'],
                       suffixe_prix(inv).lstrip('/ ')))
    duree = next((r for r in inv['reperes'] if re.search(r'jour|nuit', r, re.I)), '')
    if duree:
        lignes.append(('horloge', 'Durée', duree, ''))
    trajet = faq_par(inv, r"s'y rendre|comment venir|acc[eè]s")
    if trajet:
        m = re.search(r'<strong>(.*?)</strong>', trajet['reponse_html'], re.S)
        if m:
            phrase = texte_nu(m.group(1))
            chiffre = re.search(r'(\d+\s*[àa]\s*\d+\s*heures?|\d+\s*h)', phrase)
            lignes.append(('voiture', 'Depuis Le Caire',
                           chiffre.group(1) if chiffre else phrase,
                           phrase if chiffre else ''))
    etapes = sum(len(j['etapes']) for j in inv['jours'])
    if etapes:
        lignes.append(('pin', 'Étapes au programme', str(etapes), ''))
    if not lignes:
        return ''
    o = ['<section class="bref">',
         '<p class="eyebrow">%s</p>' % e(INTERFACE['eyebrow_bref']),
         '<h2>%s</h2>' % e(INTERFACE['titre_bref']),
         '<dl class="bref__l">']
    for icone, label, valeur, detail in lignes:
        o.append('<div><dt>%s%s</dt><dd><b>%s</b>%s</dd></div>'
                 % (ico(icone, 18), e(label), e(valeur),
                    ('<span>%s</span>' % e(detail)) if detail else ''))
    o.append('</dl><p class="bref__src">%s %s</p></section>'
             % (e(INTERFACE['source_fiche']), e(date_fr(inv['releve']))))
    return '\n'.join(o)


def selecteur_duree(inv):
    """Le module de la requête : « combien de jours prévoir ».

    Trois formats, leurs descriptions et le conseil final viennent de la
    réponse que la fiche donne déjà. Rien n'est ajouté : la question est
    seulement sortie de l'accordéon, où personne ne la déplie."""
    f = faq_par(inv, r'combien de temps|dur[ée]e')
    if not f:
        return ''
    # « Excursion d'une journée » ne porte pas de chiffre et reste une
    # durée : filtrer sur les chiffres effaçait purement l'option la
    # plus courte du séjour, et la question étant sortie de l'accordéon,
    # elle n'existait plus nulle part.
    lot = items_de(f['reponse_html'])
    if len(lot) < 2:
        return ''
    # Le <p> ENTIER, pas seulement son <strong>. La fiche écrit « Durée
    # recommandée : 3 à 4 jours pour profiter pleinement du site. » ;
    # s'arrêter au gras coupait quatre mots de la cliente.
    defaut = 1 if len(lot) > 1 else 0
    # Tout ce que la réponse dit AUTOUR de la liste : l'intro, les
    # remarques, le conseil. Sortie de l'accordéon, la question n'a plus
    # d'autre endroit où le dire.
    autour = [(g, c) for g, c in blocs_reponse(f['reponse_html']) if g == 'p']

    o = ['<section class="mod mod--duree">',
         '<p class="eyebrow">%s</p>' % e(INTERFACE['eyebrow_duree']),
         '<h2>%s</h2>' % e(f['q'])]
    if autour and not re.match(r'\s*conseil\s*:', texte_nu(autour[0][1]), re.I):
        o.append('<p class="mod__intro">%s</p>' % autour.pop(0)[1])
    o.append('<div class="duree">')
    for i, (t, _) in enumerate(lot):
        o.append('<input class="duree__r" type="radio" name="duree" id="duree-%d"%s>'
                 % (i, ' checked' if i == defaut else ''))
    o.append('<div class="duree__ong" role="tablist">')
    for i, (t, _) in enumerate(lot):
        o.append('<label class="duree__o" for="duree-%d" tabindex="0">%s</label>' % (i, e(t)))
    o.append('</div><div class="duree__p">')
    for i, (t, d) in enumerate(lot):
        o.append('<div class="duree__c"><b>%s</b><p>%s</p></div>' % (e(t), e(d)))
    o.append('</div></div>')
    for _, corps in autour:
        nu = texte_nu(corps)
        if re.match(r'\s*conseil\s*:', nu, re.I):
            o.append('<p class="mod__conseil">%s<span>%s</span></p>' % (ico('etoile', 16), e(nu)))
        else:
            o.append('<p class="mod__apres">%s</p>' % corps)
    o.append('</section>')
    return '\n'.join(o)


def liste_valise(inv):
    """La liste d'équipement de la fiche, rendue cochable.

    Cases natives : elle fonctionne sans une ligne de JavaScript, et le
    compteur n'est qu'un confort par-dessus."""
    f = faq_par(inv, r'[ée]quipements?|emporter|valise')
    if not f:
        return ''
    lot = items_de(f['reponse_html'])
    if len(lot) < 3:
        return ''
    blocs = blocs_reponse(f['reponse_html'])
    o = ['<section class="mod mod--valise">',
         '<p class="eyebrow">%s</p>' % e(INTERFACE['eyebrow_valise']),
         '<h2>%s</h2>' % e(f['q']),
         '<div id="valise">']
    aide_posee = False
    for genre, corps in blocs:
        if genre == 'p':
            nu = texte_nu(corps)
            if re.match(r'\s*conseil\s*:', nu, re.I):
                o.append('<p class="mod__conseil">%s<span>%s</span></p>' % (ico('etoile', 16), e(nu)))
                continue
            # Le HTML de la cliente passe tel quel, comme dans
            # l'accordéon : son lien reste un lien.
            o.append('<p class="mod__intro">%s</p>' % corps)
            if not aide_posee:
                o.append('<p class="mod__aide">%s</p>' % e(INTERFACE['valise_aide']))
                aide_posee = True
            continue
        o.append('<ul class="valise">')
        for t, d in corps:
            o.append('<li><label><input type="checkbox">'
                     '<span class="valise__b" aria-hidden="true">%s</span>'
                     '<span class="valise__t"><b>%s</b>%s</span></label></li>'
                     % (ico('coche', 14), e(t), ('<span>%s</span>' % e(d)) if d else ''))
        o.append('</ul>')
    o.append('</div>')
    o.append('<p class="valise__etat" id="valise-etat" role="status">%s <b>%d</b> %s</p>'
             % (e(INTERFACE['valise_reste']), len(lot),
                e('éléments à préparer' if len(lot) > 1 else 'élément à préparer')))
    o.append('</section>')
    return '\n'.join(o)


def intro_guide(roles):
    """La phrase d'accroche de la section guide, et rien de plus.

    « Ni le rythme » ne s'appuyait sur aucune ligne de la fiche :
    l'agent contrôle contenu l'a relevé comme une affirmation sur le
    produit, et il a raison. Ce qui reste est ce que les inclusions
    disent en toutes lettres — un guide privatif, un chauffeur privatif —
    et la phrase se règle sur ce qui a été trouvé (D41)."""
    genres = {g for g, _ in roles}
    if 'guide' in genres and 'voiture' in genres:
        return INTERFACE['guide_privatif']
    if 'guide' in genres:
        return INTERFACE['guide_seul']
    return INTERFACE['guide_neutre']


def votre_guide(inv, home):
    """Qui accompagne, d'après ce que la fiche inclut et ce que l'accueil
    validé dit de l'équipe. Aucun nom, aucune expérience inventés.

    L'équipe passe d'une pile de trois cartes à un carrousel des quatre
    personnes de l'accueil : chacune a la place de porter son métier ET
    son détail — l'ancienneté et les langues d'Hossam tenaient sur une
    ligne grise de 15 px, elles sont maintenant lisibles.

    Le carrousel défile nativement (glissement au doigt, flèches du
    clavier sur la piste). Les deux boutons sont un confort ajouté par
    le script, et ils n'apparaissent que si la piste déborde vraiment :
    sans JavaScript, la page reste entière."""
    roles = []
    for item in inv.get('inclus', []):
        if re.search(r'\bguide\b', item, re.I):
            roles.append(('guide', item))
        elif re.search(r'chauffeur|v[ée]hicule|transfert', item, re.I):
            roles.append(('voiture', item))
        elif re.search(r'assistance|h24|24', item, re.I):
            roles.append(('bouclier', item))
    if not roles:
        return ''
    o = ['<section class="pg-sec pg-sec--nuit"><div class="wrap">',
         '<div class="guide">',
         '<div><p class="eyebrow eyebrow--clair">%s</p>' % e(INTERFACE['eyebrow_guide']),
         '<h2>%s</h2>' % e(INTERFACE['titre_guide']),
         '<p class="guide__intro">%s</p></div>' % e(intro_guide(roles)),
         '<ul class="guide__r">']
    for icone, item in roles:
        o.append('<li>%s<span>%s</span></li>' % (ico(icone, 18), e(item)))
    o.append('</ul></div>')

    equipe = home.get('equipe', [])
    if equipe:
        o.append('<div class="carr">')
        o.append('<div class="carr__tete"><h3>%s</h3>'
                 '<div class="carr__nav" hidden>'
                 '<button type="button" class="carr__b" data-carr="-1" '
                 'aria-controls="equipe" aria-label="%s">%s</button>'
                 '<button type="button" class="carr__b" data-carr="1" '
                 'aria-controls="equipe" aria-label="%s">%s</button>'
                 '</div></div>'
                 % (e(INTERFACE['titre_equipe']), e(INTERFACE['precedent']),
                    ico('fleche', 18), e(INTERFACE['suivant']), ico('fleche', 18)))
        o.append('<div class="carr__p" id="equipe" tabindex="0" role="group" aria-label="%s">'
                 % e(INTERFACE['titre_equipe']))
        for g in equipe:
            # Le rôle de l'accueil s'écrit « métier — détail — détail ».
            # On ne réécrit rien : on coupe sur le tiret de la source et
            # on donne à chaque morceau sa place.
            bouts = [x.strip() for x in re.split(r'\s+—\s+', g['role']) if x.strip()]
            metier, details = (bouts[0], bouts[1:]) if bouts else (g['role'], [])
            o.append('<article class="carr__c">'
                     '<span class="carr__m" aria-hidden="true">%s</span>'
                     '<b>%s</b><span class="carr__r">%s</span>%s</article>'
                     % (e(g['initiale']), e(g['nom']), e(metier),
                        ('<ul class="carr__f">%s</ul>'
                         % ''.join('<li>%s</li>' % e(d) for d in details)) if details else ''))
        o.append('</div>')
        o.append('<p class="carr__aide">%s</p>' % e(INTERFACE['equipe_aide']))
        o.append('</div>')
    o.append('</div></section>')
    return '\n'.join(o)



def galerie(inv):
    """Les photos de la fiche qui n'illustrent aucune étape.

    Sur la fiche Siwa ce sont les cinq vues de l'oasis, posées en tête de
    page. Elles font 1000 px : dans une grille de trois colonnes, aucune
    boîte ne dépasse 370 px, elles restent nettes partout."""
    prises = {et['image']['base'] for j in inv['jours'] for et in j['etapes']
              if et.get('image')}
    if inv.get('image_une'):
        prises.add(inv['image_une']['base'])
    reste = [x for x in inv['images'] if x['base'] not in prises]
    if not reste:
        return ''
    o = ['<section class="galerie%s">' % (' galerie--5' if len(reste) == 5 else '')]
    for x in reste:
        o.append('<a data-lb href="%s" data-alt="%s">%s</a>'
                 % (e(x['src_original']), e(x['alt']),
                    image(x, 370, sizes='(max-width:860px) 45vw, 370px')))
    o.append('</section>')
    return '\n'.join(o)


def rang_jour(j):
    """Le numéro que la FICHE donne à ce jour, pas le nôtre.

    La fiche « Pyramides, Louxor et mer rouge en famille » numérote
    1, 2, 3, 6, 7, 7, 8 : elle saute les jours 4 et 5 et écrit deux fois
    « Jour 7 ». Renuméroter en continu changeait quatre chiffres de la
    cliente et effaçait le trou — personne ne l'aurait plus vu. On
    affiche ce qu'elle écrit ; l'anomalie, elle, est dans le bandeau."""
    m = re.match(r'\s*jours?\s*(\d+)', j.get('titre_source') or '', re.I)
    return m.group(1) if m else str(j['n'])


def numero_jour(j):
    return 'Jour %s' % rang_jour(j)


def deroule(inv):
    if not inv['jours']:
        return ''
    trajets = charger_trajets()
    o = ['<section>', '<p class="eyebrow">%s</p>' % e(INTERFACE['eyebrow_deroule']),
         '<h2>%s</h2>' % e(INTERFACE['titre_deroule'])]
    dernier_lieu = ''
    rang_dom = 0
    calcule = False
    # D15 : une photo de la source ne sert jamais deux fois. La fiche
    # famille répète son jour 7 à l'identique, photo comprise ; le
    # doublon serait le nôtre, pas le sien.
    photos_vues = set()
    for j in inv['jours']:
        o.append('<div class="jour">')
        # Le numéro est écrit APRÈS le titre et remonté par la mise en
        # page : un titre suivi de rien est signalé comme orphelin.
        o.append('<div class="jour__tete"><h3>%s</h3>%s</div>'
                 % (e(j['titre']),
                    ('<span class="jour__no">%s</span>' % e(numero_jour(j))) if j['numerote'] else ''))
        for et in j['etapes']:
            precedent = dernier_lieu
            # Le titre du jour nomme souvent le seul lieu de l'étape
            # (« Arrivée au Caire ») : il compte, comme dans la carte.
            bouts = ([j['titre']] if et is j['etapes'][0] else []) + [et['titre']] + et['paragraphes']
            lieu = lieu_de(' '.join(x for x in bouts if x)) or dernier_lieu
            dernier_lieu = lieu or dernier_lieu
            rang_dom += 1
            o.append('<article class="etape" id="etape-%d"%s>'
                     % (rang_dom, ' data-lieu="%s"' % e(lieu) if lieu else ''))
            if et.get('image') and et['image']['base'] not in photos_vues:
                photos_vues.add(et['image']['base'])
                img = et['image']
                # La boîte fait au plus 780 px : toutes les photos du
                # déroulé sont au-delà, aucune n'est agrandie.
                # Une photo sans alt donnerait un lien sans nom : le
                # titre de l'étape le nomme.
                nom = img['alt'] or et['titre'] or j['titre']
                o.append('<a class="etape__photo" data-lb href="%s" data-alt="%s" aria-label="%s">%s</a>'
                         % (e(img['src']), e(img['alt']), e('Agrandir la photo : ' + nom),
                            image({'src_original': img['src'], 'alt': img['alt'],
                                   'srcset': img.get('srcset', ''), 'largeur': img.get('largeur'),
                                   'hauteur': img.get('hauteur')},
                                  780, sizes='(max-width:1040px) 100vw, 780px')))
            if et['titre']:
                o.append('<h4>%s%s</h4>' % (ico('pin', 17), e(et['titre'])))
            reps = reperes_etape(et, precedent, lieu, trajets)
            if 'rep--calc' in reps:
                calcule = True
            o.append(reps)
            for p in et['paragraphes']:
                o.append('<p>%s</p>' % e(p))
            o.append(mentions_html(et.get('mentions')))
            o.append('</article>')
        o.append(mentions_html(j['mentions']))
        o.append('</div>')
    # D27 : un chiffre que NOUS calculons ne s'affiche pas sans dire d'où
    # il vient. L'infobulle ne suffit pas — au doigt, elle n'existe pas.
    if calcule:
        o.append('<p class="reps__src">%s</p>' % e(INTERFACE['source_trajets']))
    o.append('</section>')
    return '\n'.join(o)


def tarif(inv):
    if not inv['prix']['texte']:
        return ''
    return ('<section><p class="eyebrow">%s</p><h2>%s</h2>'
            '<div class="tarif"><div class="tarif__ligne"><span>%s</span>'
            '<b>%s <small>%s</small></b></div></div></section>'
            % (e(INTERFACE['eyebrow_tarif']), e(INTERFACE['titre_tarif']), e(INTERFACE['depuis']),
               e(inv['prix']['texte']), e(suffixe_prix(inv))))


def a_verifier(inv):
    """Le bandeau des anomalies ne s'affiche plus sur la page (D48).

    Le relevé, lui, continue : l'inventaire cherche toujours les durées
    qui ne concordent pas, les jours en double, la numérotation à trous
    et le déroulé qui parle d'un autre lieu. Ces anomalies s'impriment à
    chaque génération et vivent dans `docs/programmes/questions-melanie.md`.
    Rien n'est cessé de chercher, c'est la SORTIE qui a changé de place :
    elle va à l'agence, plus au visiteur.

    Le corollaire de D19 reste : tant qu'une anomalie porte sur le
    déroulé, l'itinéraire n'entre pas dans les données structurées. Ne
    plus montrer un doute ne le lève pas."""
    return ''


def suffixe_prix(inv):
    """« / Personne » : la formulation de la fiche, pas la nôtre."""
    return inv['prix'].get('suffixe') or INTERFACE['par_personne']


def inclusions(inv):
    if not inv['inclus'] and not inv['exclus']:
        return ''
    o = ['<section><h2>%s</h2><div class="incl">' % e(INTERFACE['titre_inclusions'])]
    o.append('<div class="incl__col incl__col--oui"><h3>%s%s</h3><ul>%s</ul></div>'
             % (ico('coche', 20), e(INTERFACE['inclus']),
                ''.join('<li>%s<span>%s</span></li>' % (ico('coche', 16), e(x)) for x in inv['inclus'])))
    o.append('<div class="incl__col incl__col--non"><h3>%s%s</h3><ul>%s</ul></div>'
             % (ico('croix', 20), e(INTERFACE['exclus']),
                ''.join('<li>%s<span>%s</span></li>' % (ico('croix', 16), e(x)) for x in inv['exclus'])))
    o.append('</div></section>')
    return '\n'.join(o)


def panneau(inv):
    o = ['<aside class="pan"><div class="pan__carte">']
    if inv['prix']['texte']:
        o.append('<p class="pan__prix" style="margin:0"><small>%s</small><b>%s</b> <i>%s</i></p>'
                 % (e(INTERFACE['depuis']), e(inv['prix']['texte']), e(suffixe_prix(inv))))
    # Ce que le séjour comprend, au même endroit que le prix : c'est là
    # qu'on décide. La bande du haut les répète, et c'est voulu — l'une
    # se lit en arrivant, l'autre au moment de cliquer.
    if inv['reperes']:
        o.append('<ul class="pan__liste">' + ''.join(
            '<li>%s<span>%s</span></li>' % (ico(icone_repere(r), 16), e(r))
            for r in inv['reperes']) + '</ul>')
    o.append('<div class="pan__act">'
             f'<a class="btn btn--or btn--bloc" href="{DEVIS}">{e(INTERFACE["cta_devis"])}</a>'
             f'<a class="btn btn--wa btn--bloc" href="{WHATSAPP}">{ico("bulle", 17)} {e(INTERFACE["cta_whatsapp"])}</a>'
             '</div>')
    o.append('<p class="pan__note">%s<br>%s</p>' % (e(INTERFACE['delai']), e(INTERFACE['sans_cb'])))
    n = (inv.get('avis_google') or {}).get('nombre')
    if n:
        # Cinq étoiles pleines seraient une NOTE, et la fiche n'en donne
        # aucune : ni note globale, ni note par avis. Le G de Google dit
        # la source, ce que le relevé porte vraiment (D30).
        o.append('<p class="pan__avis">%s'
                 '<b>%d avis Google</b> <span>%s</span></p>'
                 % (google(18), n, e(INTERFACE['agence'])))
    o.append('</div>')
    o.append(index_etapes(inv))
    o.append('</aside>')
    return '\n'.join(o)


def faqs(inv, home):
    """Les deux colonnes de questions : celles du site, celles de la fiche."""
    def accordeon(items, premier_ouvert=True):
        out = ['<div class="acc">']
        for i, it in enumerate(items):
            ouvert = ' open' if (i == 0 and premier_ouvert) else ''
            corps = it['html'] or ('<p class="acc__vide">%s</p>' % e(INTERFACE['reponse_attendue']))
            out.append('<details%s><summary><span class="q">%s</span><span class="acc__plus"></span>'
                       '</summary><div class="acc__c">%s</div></details>'
                       % (ouvert, e(it['q']), corps))
        out.append('</div>')
        return ''.join(out)

    pratique = [{'q': x['q'], 'html': x['html']} for x in home['pratique']]
    # Deux questions sont sorties de l'accordéon : elles sont devenues
    # des modules, plus haut dans la page. Le contenu reste entier, il
    # est seulement présenté là où il sert.
    promues = {(faq_par(inv, r'combien de temps|dur[ée]e') or {}).get('q'),
               (faq_par(inv, r'[ée]quipements?|emporter|valise') or {}).get('q')}
    fiche = [{'q': f['q'], 'html': f['reponse_html']}
             for f in inv['faq'] if f['q'] not in promues]
    if not pratique and not fiche:
        return ''
    o = ['<section class="pg-sec pg-sec--fond"><div class="wrap"><div class="faqs">']
    if fiche:
        o.append('<div><p class="eyebrow">%s</p><h2>%s</h2>%s</div>'
                 % (e(INTERFACE['eyebrow_faq']), e(INTERFACE['titre_faq']), accordeon(fiche)))
    if pratique:
        o.append('<div><p class="eyebrow">%s</p><h2>%s</h2>%s</div>'
                 % (e(INTERFACE['eyebrow_pratique']), e(INTERFACE['titre_pratique']),
                    accordeon(pratique, premier_ouvert=False)))
    o.append('</div></div></section>')
    return '\n'.join(o)


def avis(inv):
    """Le mur d'avis : deux colonnes qui défilent en continu.

    Les dix témoignages du widget de la fiche vont de 78 à 619
    caractères. Un carrousel horizontal aurait aligné les dix cartes sur
    la plus haute et laissé du vide sous les neuf autres ; deux colonnes
    verticales laissent chaque avis à sa longueur, et le mouvement
    montre qu'il y en a plus que ce que l'écran porte.

    Trois contraintes tenues :

    - **on peut l'arrêter.** WCAG 2.2.2 : tout mouvement automatique de
      plus de cinq secondes doit pouvoir être mis en pause. Le bouton
      est une case à cocher native, donc il fonctionne sans JavaScript ;
      le survol et le focus clavier arrêtent aussi le défilement, et
      `prefers-reduced-motion` supprime l'animation, les dix avis
      restant alors simplement empilés ;
    - **la boucle est invisible.** Chaque colonne porte deux fois ses
      cartes et remonte d'exactement la moitié de sa hauteur. L'écart
      entre cartes est une marge, jamais un `gap` : un `gap` aurait
      laissé un demi-écart de décalage à chaque tour ;
    - **rien n'est ajouté au contenu.** Aucune étoile : la fiche affiche
      un nombre d'avis, jamais une note. La seconde copie de chaque
      colonne est `aria-hidden` — elle sert la boucle, pas la lecture.
    """
    a = inv.get('avis_google') or {}
    lot = a.get('temoignages') or []
    if not lot:
        return ''

    # Répartition : chaque avis va dans la colonne la plus courte, ce qui
    # garde l'ordre de la source et équilibre les deux hauteurs.
    colonnes = [[], []]
    poids = [0, 0]
    for t in lot:
        i = 0 if poids[0] <= poids[1] else 1
        colonnes[i].append(t)
        poids[i] += hauteur_avis(t['texte'])

    # Pas d'aria-label sur la case : le nom accessible d'une commande
    # doit CONTENIR son texte visible (critère 2.5.3), or celui-ci change
    # avec l'état. Le label le fournit donc lui-même, et l'étiquette
    # cachée par display:none sort du nom, comme il se doit.
    o = ['<section class="pg-sec" aria-labelledby="t-avis"><div class="wrap">',
         '<input type="checkbox" id="mur-stop" class="mur__stop">',
         '<div class="mur__tete">',
         '<div><p class="eyebrow">%s</p><h2 id="t-avis">%s</h2></div>'
         % (e(INTERFACE['eyebrow_avis']), e(INTERFACE['titre_avis']))]
    droite = []
    if a.get('nombre'):
        droite.append('<b>%s</b>' % e('%d avis Google sur l\'agence' % a['nombre']))
    if a.get('releve'):
        droite.append('<small>%s %s</small>'
                      % (e(INTERFACE['avis_releve']), e(date_fr(a['releve']))))
    if droite:
        o.append('<p class="mur__cpt">%s</p>' % ''.join(droite))
    o.append('<label class="mur__btn" for="mur-stop">%s'
             '<span class="a">%s</span><span class="b">%s</span></label>'
             % (ico('pause', 15), e(INTERFACE['avis_marche']), e(INTERFACE['avis_arret'])))
    o.append('</div>')

    o.append('<div class="mur">')
    for colonne in colonnes:
        if not colonne:
            continue
        # 26 px par seconde : la vitesse de lecture confortable relevée
        # sur les murs d'avis. La durée suit donc la hauteur réelle de la
        # colonne, sinon la colonne courte filerait deux fois plus vite.
        duree = max(40, round(sum(hauteur_avis(t['texte']) for t in colonne) / 26))
        o.append('<div class="mur__c"><div class="mur__f">'
                 '<div class="mur__d" style="--d:%ds">' % duree)
        for copie in (0, 1):
            o.append('<div class="mur__p"%s>' % (' aria-hidden="true"' if copie else ''))
            for t in colonne:
                o.append(carte_avis(t))
            o.append('</div>')
        o.append('</div></div></div>')
    o.append('</div></div></section>')
    return '\n'.join(o)


MOIS_FR = ('janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet',
           'août', 'septembre', 'octobre', 'novembre', 'décembre')


def date_fr(iso):
    """« 2026-09-09 » se lit « 9 septembre 2026 ».

    C'est une date de RELEVÉ, écrite par nous : elle suit donc la
    typographie française, comme tout libellé d'interface (D17)."""
    m = re.match(r'(\d{4})-(\d{2})-(\d{2})$', str(iso or ''))
    if not m:
        return str(iso or '')
    an, mois, jour = int(m.group(1)), int(m.group(2)), int(m.group(3))
    return '%d%s %s %d' % (jour, 'er' if jour == 1 else '', MOIS_FR[mois - 1], an)


def hauteur_avis(texte):
    """La hauteur d'une carte, en pixels, estimée à la génération.

    Elle ne sert qu'à deux choses : équilibrer les colonnes et donner à
    chacune la durée qui produit la même vitesse. Un à-peu-près suffit —
    62 caractères par ligne dans une colonne de 560 px, 27 px de ligne."""
    import math
    return 166 + math.ceil(len(texte) / 62.0) * 27


def carte_avis(t):
    """Une carte d'avis. La signature porte le G de Google et non les
    initiales de l'auteur : ce qui compte au pied d'un témoignage, c'est
    d'où il vient — et c'est ce que le widget de la fiche montre."""
    return ('<article class="mur__a"><span class="mur__q" aria-hidden="true">&#8220;</span>'
            '<blockquote>%s</blockquote>'
            '<footer><span class="ini ini--g">%s</span>'
            '<span><b>%s</b>%s</span></footer></article>'
            % (e(t['texte']), google(21), e(t['auteur']), e(INTERFACE['avis_source'])))



def bande_devis(home):
    points = ''.join('<li>%s<span>%s</span></li>' % (ico('coche', 17), e(p))
                     for p in INTERFACE['devis_points'])
    return ('<section class="pg-sec"><div class="wrap"><div class="devis">'
            '<div><p class="eyebrow eyebrow--clair">Votre projet</p>'
            f'<h2>{e(INTERFACE["titre_devis"])}</h2><ul>{points}</ul></div>'
            '<div class="devis__act">'
            f'<a class="btn btn--or btn--bloc" href="{DEVIS}">{e(INTERFACE["cta_devis_court"])}</a>'
            f'<a class="btn btn--wa btn--bloc" href="{WHATSAPP}">{e(INTERFACE["cta_whatsapp"])}</a>'
            f'<small>{e(INTERFACE["sans_cb"])}</small></div></div></div></section>')


def proches(inv, voisins):
    if not voisins:
        return ''
    o = ['<section class="pg-sec pg-sec--serre"><div class="wrap">',
         '<h2 style="text-align:center">%s</h2><div class="proches">' % e(INTERFACE['titre_proches'])]
    for v in voisins:
        img = ''
        if v.get('image'):
            img = ('<div class="proches__img">%s</div>'
                   % image(v['image'], 380, sizes='(max-width:860px) 100vw, 380px'))
        prix = ('<p>%s <b>%s</b></p>' % (e(INTERFACE['depuis']), e(v['prix']))) if v.get('prix') else ''
        o.append('<a href="%s">%s<h3>%s</h3>%s</a>' % (e(v['url']), img, e(v['titre']), prix))
    o.append('</div><div class="proches__tous">'
             f'<a class="btn btn--fantome" href="{SITE}/nos-sejours-egypte/">'
             f'{e(INTERFACE["tous_sejours"])}</a></div></div></section>')
    return '\n'.join(o)


def barre_mobile(inv):
    if not inv['prix']['texte']:
        return ''
    # Le titre du séjour ne tient pas dans la barre et se faisait couper
    # par une ellipse : une phrase amputée est un défaut, pas une mise en
    # page. Il est juste au-dessus, en H1 ; la barre porte le prix.
    return ('<div class="pg-mob"><span class="p"><small>%s</small><b>%s</b> <i>/ pers.</i></span>'
            '<a class="btn btn--or btn--sm" href="%s">%s</a></div>'
            % (e(INTERFACE['depuis']), e(inv['prix']['texte']), DEVIS, e(INTERFACE['cta_devis_court'])))


# ------------------------------------------------------------------ voisins

def voisins_de(inv, tous):
    """Les séjours de la même famille, lus dans leurs inventaires.

    Rien n'est recopié d'une maquette : titre, prix et photo viennent de
    la fiche voisine elle-même."""
    out = []
    for autre in tous:
        if autre['slug'] == inv['slug'] or autre['categorie']['nom'] != inv['categorie']['nom']:
            continue
        img = autre.get('image_une') or plus_grande(autre['images'])
        out.append({'url': autre['url'], 'titre': autre['h1'],
                    'prix': autre['prix']['texte'], 'image': img})
    return out[:3]


# ------------------------------------------------------------------ données structurées

def json_ld(inv):
    trip = {'@context': 'https://schema.org', '@type': 'TouristTrip', 'name': inv['h1'],
            'description': inv['meta_description'], 'url': inv['url'],
            'image': [x['src_original'] for x in
                      ([inv['image_une']] if inv.get('image_une') else []) + inv['images']][:6],
            'provider': {'@type': 'TravelAgency', 'name': 'Authentique Égypte', 'url': SITE + '/'}}
    etapes = [et for j in inv['jours'] for et in j['etapes'] if et['titre']]
    # Le déroulé de cette fiche décrit peut-être un autre séjour : tant
    # que la cliente ne l'a pas confirmé, on ne le déclare pas à Google.
    if any('déroulé' in x for x in inv.get('anomalies', [])):
        etapes = []
    if etapes:
        trip['itinerary'] = {'@type': 'ItemList', 'numberOfItems': len(etapes),
                             'itemListElement': [{'@type': 'ListItem', 'position': i + 1,
                                                  'name': et['titre']} for i, et in enumerate(etapes)]}
    if inv['prix']['valeur']:
        trip['offers'] = {'@type': 'Offer', 'price': inv['prix']['valeur'], 'priceCurrency': 'EUR',
                          'availability': 'https://schema.org/InStock',
                          'seller': {'@type': 'TravelAgency', 'name': 'Authentique Égypte'}}
    lot = [trip]
    repondues = [f for f in inv['faq'] if f['reponse_html']]
    if repondues:
        lot.append({'@context': 'https://schema.org', '@type': 'FAQPage',
                    'mainEntity': [{'@type': 'Question', 'name': f['q'],
                                    'acceptedAnswer': {'@type': 'Answer',
                                                       'text': re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', f['reponse_html'])).strip()}}
                                   for f in repondues]})
    lot.append({'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': 1, 'name': INTERFACE['ariane_accueil'], 'item': SITE + '/'},
        {'@type': 'ListItem', 'position': 2, 'name': INTERFACE['ariane_sejours'],
         'item': SITE + '/nos-sejours-egypte/'},
        {'@type': 'ListItem', 'position': 3, 'name': inv['categorie']['nom'],
         'item': inv['categorie']['url']},
        {'@type': 'ListItem', 'position': 4, 'name': inv['h1'], 'item': inv['url']}]})
    return ('<script type="application/ld+json">'
            + json.dumps(lot, ensure_ascii=False) + '</script>')


# ------------------------------------------------------------------ page

def page(inv, home, voisins, chemin_charte='assets/charte.css'):
    titre = re.sub(r'\s*[-|]\s*Voyage en Égypte sur mesure\s*$', '', inv['title_seo']).strip()
    titre = titre or inv['h1']
    corps = '\n'.join(x for x in [
        hero(inv),
        reperes(inv),
        '<nav class="ariane ariane--sous" aria-label="Fil d\'Ariane">%s</nav>' % ariane_ol(inv),
        '<div class="wrap"><div class="deux"><div class="corps">',
        a_verifier(inv), presentation(inv), galerie(inv),
        selecteur_duree(inv), apercu(inv), carte(inv), deroule(inv),
        tarif(inv), inclusions(inv), liste_valise(inv),
        '</div>', panneau(inv), '</div></div>',
        votre_guide(inv, home),
        faqs(inv, home),
        avis(inv),
        bande_devis(home),
        proches(inv, voisins),
    ] if x)

    fini = json.dumps(INTERFACE['valise_fini'], ensure_ascii=False)
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(titre)} — Authentique Égypte</title>
<meta name="description" content="{e(inv['meta_description'], quote=True)}">
<meta name="robots" content="noindex,nofollow">
<link rel="icon" href="{SITE}/wp-content/uploads/2026/08/authentique-egypte-logo-transparent.webp">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Archivo:wght@300;400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{chemin_charte}">
<style>{CSS}</style>
{json_ld(inv)}
</head>
<body>
{bloc('entete.html')}
<main class="pg">
{corps}
</main>
{bloc('pied.html')}
{barre_mobile(inv)}
<div class="pg-lb" id="pg-lb" role="dialog" aria-modal="true" aria-label="{e(INTERFACE['photos'])}">
  <button type="button">Fermer</button><img alt="">
</div>
<script>var VALISE_FINI={fini};{SCRIPT}</script>
</body>
</html>
"""


# ------------------------------------------------------------------ liens live

LIENS_LIVE = {
    'index.html': SITE + '/', 'qui-sommes-nous.html': SITE + '/qui-sommes-nous/',
    'devis.html': DEVIS, 'blog.html': SITE + '/notre-blog/',
    'categorie.html': SITE + '/nos-sejours-egypte/croisieres-en-egypte/',
    'categorie-desert.html': SITE + '/nos-sejours-egypte/desert-egypte/',
    'destination.html': SITE + '/voyage-au-caire/',
    'produit-siwa.html': SITE + '/programs/excursion-a-loasis-de-siwa/',
    'article-quand-partir.html': SITE + '/quand-partir-en-egypte/',
}


def vers_le_live(h):
    for rel, live in LIENS_LIVE.items():
        h = h.replace('href="%s"' % rel, 'href="%s"' % live)
    return h


# ------------------------------------------------------------------ interface json

def ecrire_interface():
    """La liste des chaînes du gabarit, pour l'agent CONTRÔLE CONTENU."""
    plat = []
    for v in INTERFACE.values():
        plat += v if isinstance(v, list) else [v]
    chemin = os.path.join(RACINE, 'outils', 'interface-programme.json')
    with open(chemin, 'w', encoding='utf-8') as f:
        json.dump(sorted(set(plat)), f, ensure_ascii=False, indent=1)
    return chemin


def charger(slug):
    chemin = os.path.join(PROGRAMMES, slug + '.json')
    if not os.path.exists(chemin):
        sys.exit('inventaire manquant : %s — lancez outils/inventaire-programme.py %s' % (chemin, slug))
    with open(chemin, encoding='utf-8') as f:
        return json.load(f)


def ecrire_anomalies(tous):
    """Le relevé des anomalies, hors de la page.

    Il s'affichait autrefois en tête de chaque page, dans un bandeau
    « À vérifier avec l'agence » (D19). Rémi l'a retiré : une page qui
    vend un voyage n'est pas un cahier de relecture. Le relevé, lui,
    continue — et il lui fallait un endroit. Le voici, refait à chaque
    génération, toutes fiches confondues, avec la date de chaque relevé.
    """
    lignes = ['# Anomalies relevées sur les fiches',
              '',
              'Écrit par `outils/gabarit-programme.py` à chaque génération. **Ce fichier ne se',
              "modifie pas à la main** : il redit ce que l'inventaire trouve, et rien d'autre.",
              "Ce que l'agence doit trancher est repris en questions dans",
              '`questions-melanie.md`.',
              '']
    total = 0
    for inv in sorted(tous, key=lambda x: x['slug']):
        if not inv.get('anomalies'):
            continue
        total += len(inv['anomalies'])
        lignes.append('## %s' % inv['h1'])
        lignes.append('')
        lignes.append('`%s` — relevé du %s' % (inv['slug'], date_fr(inv['releve'])))
        lignes.append('')
        for x in inv['anomalies']:
            lignes.append('- %s' % x)
        lignes.append('')
    saines = [x['slug'] for x in tous if not x.get('anomalies')]
    if saines:
        lignes += ['## Fiches sans anomalie', '',
                   ', '.join('`%s`' % x for x in sorted(saines)), '']
    lignes.insert(6, '**%d anomalie%s sur %d fiche%s.**'
                  % (total, 's' if total > 1 else '',
                     len(tous) - len(saines), 's' if len(tous) - len(saines) > 1 else ''))
    lignes.insert(7, '')
    chemin = os.path.join(PROGRAMMES, 'anomalies.md')
    with open(chemin, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lignes).rstrip() + '\n')
    return chemin


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--programme', default='')
    p.add_argument('--tous', action='store_true')
    a = p.parse_args()

    dispo = sorted(x[:-5] for x in os.listdir(PROGRAMMES)
                   if x.endswith('.json') and not x.startswith('_'))
    if a.tous:
        slugs = dispo
    elif a.programme:
        slugs = [a.programme]
    else:
        sys.exit('usage : gabarit-programme.py --programme <slug> | --tous')

    tous = [charger(s) for s in dispo]
    home = accueil()
    if not home['pratique']:
        sys.exit("les questions pratiques n'ont pas été lues dans maquettes/index.html")

    os.makedirs(os.path.join(MAQUETTES, 'site'), exist_ok=True)
    for slug in slugs:
        inv = charger(slug)
        voisins = voisins_de(inv, tous)

        # La page de référence du gabarit vit à la racine des maquettes ;
        # les 14 pages produites vivent dans maquettes/site/.
        for chemin, charte in ((os.path.join(MAQUETTES, 'site', 'programme-%s.html' % slug[:60]),
                                '../assets/charte.css'),):
            h = vers_le_live(page(inv, home, voisins, charte))
            with open(chemin, 'w', encoding='utf-8') as f:
                f.write(h)
        if slug == 'excursion-a-loasis-de-siwa':
            ref = os.path.join(MAQUETTES, 'programme-siwa.html')
            with open(ref, 'w', encoding='utf-8') as f:
                f.write(vers_le_live(page(inv, home, voisins, 'assets/charte.css')))

        images = 1 if inv.get('image_une') else 0
        images += sum(1 for j in inv['jours'] for et in j['etapes'] if et.get('image'))
        images += len(voisins)
        print('%-52s %d étape(s) · %d image(s) posée(s) · FAQ %d + %d · %d voisin(s)'
              % (slug[:52], sum(len(j['etapes']) for j in inv['jours']), images,
                 len(inv['faq']), len(home['pratique']), len(voisins)))
        for x in inv['anomalies']:
            print('    ⚠ ' + x)

    print('\ninterface du gabarit : ' + os.path.relpath(ecrire_interface(), RACINE))
    print('anomalies des fiches : ' + os.path.relpath(ecrire_anomalies(tous), RACINE))


if __name__ == '__main__':
    main()
