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
}


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
    """Les blocs repris de la maquette d'accueil VALIDÉE.

    Jamais de l'accueil en ligne : celui-ci porte encore le visa à 25 €,
    corrigé à 30 € dans la maquette (backlog C1)."""
    with open(os.path.join(MAQUETTES, 'index.html'), encoding='utf-8') as f:
        h = f.read()

    pratique = []
    zone = h[h.find('Cinq réponses avant de nous écrire'):]
    for m in re.finditer(r'<details[^>]*><summary>(.*?)</summary>\s*'
                         r'<div class="faq__c">(.*?)</div>\s*</details>', zone, re.S):
        # Le libellé est du HTML : ses entités (&nbsp;) doivent être
        # rendues en texte AVANT d'être ré-échappées, sinon le visiteur
        # lit « en ce moment&nbsp;? » en toutes lettres.
        pratique.append({'q': H.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', m.group(1))).strip()),
                         'html': re.sub(r'\s+', ' ', m.group(2)).strip()})

    etapes = []
    zone = h[h.find("Quatre étapes, et vous n'avancez jamais"):]
    for m in re.finditer(r'<div class="etape"><i class="pt"></i>\s*<h3>(.*?)</h3>\s*<p>(.*?)</p>\s*'
                         r'<span class="quand">(.*?)</span>', zone, re.S):
        etapes.append({'titre': m.group(1).strip(), 'texte': m.group(2).strip(),
                       'quand': m.group(3).strip()})

    return {'pratique': pratique, 'etapes': etapes[:4]}


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
.pg .hero__fond{position:absolute;inset:0}
.pg .hero__fond img{width:100%;height:100%;object-fit:cover}
.pg .hero__fond::after{content:"";position:absolute;inset:0;background:
  linear-gradient(180deg,rgba(6,42,58,.62) 0%,rgba(6,42,58,.30) 34%,rgba(5,35,50,.88) 100%)}
.pg .hero__in{position:relative;padding:24px 0 56px}
.pg .hero .ariane{color:#C6DCE6;padding-top:0}
.pg .hero .ariane a{color:var(--or-clair)}
.pg .hero .ariane li::after{color:rgba(255,255,255,.45)}
.pg .hero .ariane [aria-current]{color:#fff}
.pg .hero__pills{display:flex;flex-wrap:wrap;gap:8px;margin:20px 0 18px}
.pg .pill{display:inline-flex;align-items:center;gap:7px;font-family:"Manrope",sans-serif;
  font-size:.84rem;font-weight:600;color:#fff;background:rgba(255,255,255,.16);
  border:1px solid rgba(255,255,255,.3);backdrop-filter:blur(8px);border-radius:var(--r-pill);padding:7px 14px}
.pg .hero h1{color:#fff;font-size:clamp(2rem,4.4vw,3.15rem);line-height:1.08;margin:0 0 14px;
  max-width:18ch;text-shadow:0 2px 20px rgba(0,0,0,.45);text-wrap:balance}
.pg .hero__chapo{color:#EAF2F6;font-size:1.12rem;line-height:1.6;max-width:54ch;margin:0 0 28px;
  font-weight:400;text-shadow:0 1px 12px rgba(0,0,0,.45)}
.pg .hero__bas{display:flex;flex-wrap:wrap;align-items:center;gap:16px 28px}
.pg .hero__prix{background:rgba(255,255,255,.13);backdrop-filter:blur(10px);
  border:1px solid rgba(255,255,255,.24);border-radius:var(--r-m);padding:12px 20px;color:#fff;
  font-family:"Manrope",sans-serif}
.pg .hero__prix small{display:block;font-size:.82rem;color:#DCEAF0}
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
.pg .reperes ul{list-style:none;margin:0;padding:24px 0;display:grid;
  grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:20px}
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
.pg .verifier{background:var(--or-fond);border:1px dashed var(--or);border-radius:var(--r-l);
  padding:20px 24px;font-family:"Manrope",sans-serif}
.pg .verifier__t{font-weight:800;font-size:1rem;color:#7A5605;margin:0 0 10px;
  display:flex;align-items:center;gap:9px}
.pg .verifier__t::before{content:"!";flex:0 0 auto;width:24px;height:24px;border-radius:50%;
  background:var(--or);color:var(--nuit-900);display:grid;place-items:center;font-size:.9rem}
.pg .verifier ul{list-style:none;margin:0;padding:0;display:grid;gap:8px;color:#6B4B04;
  font-size:.98rem;line-height:1.55;max-width:62ch}
.pg .verifier li{padding-left:18px;position:relative}
.pg .verifier li::before{content:"";position:absolute;left:2px;top:.6em;width:6px;height:6px;
  border-radius:50%;background:#B8860B}
.pg .verifier__d{margin:12px 0 0;font-size:.9rem;color:#8A6100}

/* ---------- galerie ---------- */
/* Cinq photos en trois colonnes avec une grande en 2×2 laissent une
   case vide en bas à droite. En QUATRE colonnes, la grande occupe
   exactement la moitié gauche et les quatre autres la moitié droite :
   le cadre est plein. Les autres comptes tiennent en trois colonnes
   sans case orpheline au milieu. */
.pg .galerie{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
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
.pg .etape+.etape{margin-top:48px}
.pg .etape__photo{border-radius:var(--r-l);overflow:hidden;background:var(--fond);margin:0 0 20px;
  aspect-ratio:16/9}
.pg .etape__photo img{width:100%;height:100%;object-fit:cover;display:block;transition:transform .6s var(--ease)}
.pg .etape__photo:hover img{transform:scale(1.03)}
.pg .etape h4{font-family:"Archivo",sans-serif;font-size:1.2rem;font-weight:600;color:var(--noir);
  margin:0 0 12px;letter-spacing:-.3px;display:flex;align-items:center;gap:10px}
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
.pg .acc__c a{color:var(--teal-txt);text-decoration:underline;text-underline-offset:3px}
.pg .acc__vide{color:#7A5605;background:var(--or-fond);border:1px dashed var(--or);
  border-radius:var(--r-s);padding:10px 14px;font-family:"Manrope",sans-serif;font-size:.94rem}

/* ---------- avis ---------- */
.pg .avis__tete{display:flex;flex-wrap:wrap;align-items:baseline;gap:12px 20px;margin:0 0 28px}
.pg .avis__tete .et{color:var(--or-fonce);letter-spacing:.14em;font-size:1.15rem}
.pg .avis__tete b{font-family:"Manrope",sans-serif;font-size:1.05rem;color:var(--noir)}
.pg .avis__g{display:grid;grid-template-columns:repeat(3,1fr);gap:22px;align-items:start}
.pg .avis__g article{background:#fff;border:1px solid var(--ligne-pg);border-radius:var(--r-l);
  padding:24px;display:flex;flex-direction:column;gap:14px}
.pg .avis__g .et{color:var(--or-fonce);letter-spacing:.14em;font-size:.98rem}
.pg .avis__g blockquote{margin:0;font-size:1rem;line-height:1.7;color:var(--texte);flex:1}
.pg .avis__g footer{display:flex;align-items:center;gap:12px;font-family:"Manrope",sans-serif;
  font-size:.9rem;color:var(--gris-lis);border-top:1px solid var(--ligne-2);padding-top:14px}
.pg .avis__g footer b{color:var(--noir);display:block;font-weight:700}
.pg .ini{width:38px;height:38px;border-radius:50%;background:var(--nuit);color:#fff;display:grid;
  place-items:center;font-weight:700;font-size:.9rem;flex:0 0 auto}

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
  /* Le bandeau : au bureau la photo est le fond du bloc ; sur mobile
     elle devient une bande au-dessus du texte. Sans cela, un écran
     étroit et haut réclame à l'image plus de pixels qu'elle n'en a —
     mesuré ×1,34 à 390 px en densité 2 — et la photo devient floue. */
  .pg .hero__fond{position:relative;aspect-ratio:4/3}
  .pg .hero__fond::after{background:linear-gradient(180deg,rgba(6,42,58,.15) 40%,rgba(5,35,50,.75) 100%)}
  .pg .hero__in{padding:20px 0 40px;background:var(--nuit-900)}
  .pg .hero .ariane{padding-bottom:6px}
  .pg .hero__pills{margin:14px 0 14px;gap:6px}
  .pg .hero__chapo{margin-bottom:22px}
  .pg .hero h1,.pg .hero__chapo{text-shadow:none}
  .pg-sec{padding:48px 0}
  .pg-sec--serre{padding:40px 0}
  .pg .deux{padding:40px 0;gap:32px}
  .pg .deux>.corps{gap:48px}
  .pg-mob{display:flex}
  .pg .proches{grid-template-columns:1fr}
  .pg .avis__g{grid-template-columns:1fr}
  .pg .galerie{grid-template-columns:1fr 1fr}
  .pg .galerie a:first-child{grid-column:span 2;grid-row:auto;aspect-ratio:3/2}
  .pg .hero__in{padding:24px 0 40px}
}
@media (max-width:600px){
  /* Plancher mobile : rien sous 15 px. Le retour du 24/08 portait
     précisément là-dessus, et l'outil de lisibilité le vérifie. */
  .pg .reperes small,.pg .hero__prix small,.pg .hero__prix i,.pg .pan__prix small,
  .pg .pan__prix i,.pg .pan__note,.pg .note,.pg .proches p,.pg .avis__g footer,
  .pg .pg-mob .p small,.pg .pan__conf,.pg .mention,.pg .pill,.pg .acc__vide{font-size:.95rem}
  .pg .reperes b,.pg .pan__liste,.pg .apercu span.t{font-size:1rem}
  .pg .ariane,.pg .eyebrow,.pg .apercu .n,.pg .jour__no,.pg .tarif__ligne b small,
  .pg .avis__g .ini,.pg .acc__c,.pg .devis__act small,.pg .verifier__d{font-size:.95rem}
  .pg-mob .p small{font-size:.95rem}
  .pg .eyebrow{letter-spacing:.1em}
  .pg .hero h1{font-size:1.95rem;letter-spacing:-.8px}
  .pg .hero__chapo{font-size:1.05rem}
  .pg .apercu{padding:22px}
  .pg .incl__col,.pg .pan__carte{padding:20px}
  .pg .acc summary{font-size:1.02rem;padding:16px 18px}
  .pg .acc__c{padding:0 18px 18px}
  .pg .etape+.etape{margin-top:40px}
  body{padding-bottom:84px}
}
@media (prefers-reduced-motion:reduce){.pg *,.pg *::before,.pg *::after{transition:none!important}}
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
    function fermer(){ lb.classList.remove('on'); img.src=''; }
    lb.addEventListener('click',function(ev){ if(ev.target===lb||ev.target.tagName==='BUTTON') fermer(); });
    document.addEventListener('keydown',function(ev){ if(ev.key==='Escape') fermer(); });
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
    o = ['<section class="hero">']
    if une:
        o.append('<div class="hero__fond">' +
                 image(une, 1920, sizes='100vw', priorite=True) + '</div>')
    o.append('<div class="hero__in"><div class="wrap">')
    o.append(ariane(inv))
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


def ariane(inv):
    return ('<nav class="ariane" aria-label="Fil d\'Ariane"><ol>'
            f'<li><a href="{SITE}/">{e(INTERFACE["ariane_accueil"])}</a></li>'
            f'<li><a href="{SITE}/nos-sejours-egypte/">{e(INTERFACE["ariane_sejours"])}</a></li>'
            f'<li><a href="{e(inv["categorie"]["url"])}">{e(inv["categorie"]["nom"])}</a></li>'
            f'<li><span aria-current="page">{e(inv["h1"])}</span></li></ol></nav>')


def reperes(inv):
    o = ['<section class="reperes"><div class="wrap"><ul>']
    if inv['prix']['texte']:
        o.append('<li>%s<small>%s</small><b>%s</b></li>'
                 % (ico('euro', 22), e(INTERFACE['depuis']), e(inv['prix']['texte'])))
    for r in inv['reperes']:
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
                 % (('J%d' % j['n']) if j['numerote'] else ('%d' % i), e(et['titre'])))
    o.append('</ol></section>')
    return '\n'.join(o)


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


def deroule(inv):
    if not inv['jours']:
        return ''
    o = ['<section>', '<p class="eyebrow">%s</p>' % e(INTERFACE['eyebrow_deroule']),
         '<h2>%s</h2>' % e(INTERFACE['titre_deroule'])]
    for j in inv['jours']:
        o.append('<div class="jour">')
        # Le numéro est écrit APRÈS le titre et remonté par la mise en
        # page : un titre suivi de rien est signalé comme orphelin.
        o.append('<div class="jour__tete"><h3>%s</h3>%s</div>'
                 % (e(j['titre']),
                    ('<span class="jour__no">Jour %d</span>' % j['n']) if j['numerote'] else ''))
        for et in j['etapes']:
            o.append('<article class="etape">')
            if et.get('image'):
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
            for p in et['paragraphes']:
                o.append('<p>%s</p>' % e(p))
            o.append(mentions_html(et.get('mentions')))
            o.append('</article>')
        o.append(mentions_html(j['mentions']))
        o.append('</div>')
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
    """Ce que le relevé de la fiche a trouvé de contradictoire.

    Ce bandeau n'est pas du contenu : c'est une note de production,
    visible seulement pendant la relecture, qui met sous les yeux de la
    cliente ce qu'elle seule peut trancher — une durée qui ne concorde
    pas, un déroulé qui parle d'un autre lieu. Sans lui, la page rend
    l'anomalie invisible en la mettant au propre. Décision D19."""
    if not inv.get('anomalies'):
        return ''
    return ('<aside class="verifier"><p class="verifier__t">%s</p><ul>%s</ul>'
            '<p class="verifier__d">%s %s</p></aside>'
            % (e(INTERFACE['titre_verifier']),
               ''.join('<li>%s</li>' % e(x) for x in inv['anomalies']),
               e(INTERFACE['releve_du']), e(inv['releve'])))


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
    if inv['reperes']:
        o.append('<ul class="pan__liste">' + ''.join(
            '<li>%s<span>%s</span></li>' % (ico(icone_repere(r), 17), e(r)) for r in inv['reperes'])
            + '</ul>')
    o.append('<div class="pan__act">'
             f'<a class="btn btn--or btn--bloc" href="{DEVIS}">{e(INTERFACE["cta_devis"])}</a>'
             f'<a class="btn btn--wa btn--bloc" href="{WHATSAPP}">{ico("bulle", 17)} {e(INTERFACE["cta_whatsapp"])}</a>'
             '</div>')
    o.append('<p class="pan__note">%s<br>%s</p>' % (e(INTERFACE['delai']), e(INTERFACE['sans_cb'])))
    o.append('</div>')
    n = (inv.get('avis_google') or {}).get('nombre')
    if n:
        o.append('<div class="pan__conf"><span class="et" aria-hidden="true">★★★★★</span>'
                 '<b>%d avis Google</b><span>%s</span></div>' % (n, e(INTERFACE['agence'])))
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
    fiche = [{'q': f['q'], 'html': f['reponse_html']} for f in inv['faq']]
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
    a = inv.get('avis_google') or {}
    lot = (a.get('temoignages') or [])[:3]
    if not lot:
        return ''
    o = ['<section class="pg-sec"><div class="wrap">',
         '<p class="eyebrow">%s</p><h2>%s</h2>' % (e(INTERFACE['eyebrow_avis']), e(INTERFACE['titre_avis'])),
         '<div class="avis__tete"><span class="et" aria-hidden="true">★★★★★</span>']
    if a.get('nombre'):
        o.append('<b>%d avis Google sur l\'agence</b>' % a['nombre'])
    o.append('</div><div class="avis__g">')
    for t in lot:
        ini = ''.join(x[0].upper() for x in t['auteur'].split()[:2]) or '·'
        o.append('<article><span class="et" aria-hidden="true">★★★★★</span><blockquote>%s</blockquote>'
                 '<footer><span class="ini">%s</span><span><b>%s</b>Avis Google</span></footer></article>'
                 % (e(t['texte']), e(ini), e(t['auteur'])))
    o.append('</div></div></section>')
    return '\n'.join(o)


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
        '<div class="wrap"><div class="deux"><div class="corps">',
        a_verifier(inv), presentation(inv), galerie(inv), apercu(inv), deroule(inv),
        tarif(inv), inclusions(inv),
        '</div>', panneau(inv), '</div></div>',
        faqs(inv, home),
        avis(inv),
        bande_devis(home),
        proches(inv, voisins),
    ] if x)

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
  <button type="button">Fermer</button><img src="" alt="">
</div>
<script>{SCRIPT}</script>
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


if __name__ == '__main__':
    main()
