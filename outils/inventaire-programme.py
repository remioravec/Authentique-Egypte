#!/usr/bin/env python3
"""
L'inventaire daté d'une fiche séjour — la source de vérité du contenu.

Ticket O1 du plan `docs/plan-pages-programme.md`.

Ce module ne rend rien et ne réécrit rien : il RELÈVE. Il lit la fiche
telle que le site la sert, en résout chaque image jusqu'à son original,
mesure sa taille réelle, et note ce qui se contredit. Le générateur de
page ne travaille QUE sur ce fichier : il ne fait plus de requête, il ne
devine plus rien, et deux générations donnent le même résultat.

Trois choses que l'extraction d'août ratait, et qui sont ici :

1. **Les réponses de la FAQ.** Les huit questions vivent dans un bloc
   HTML personnalisé dont une seule réponse est rendue ; les sept autres
   sont dans un objet JavaScript (`const contents = { tab2: ` … ` }`).
   Elles existent, elles sont du contenu de la cliente, on les reprend.
2. **La taille réelle des images.** Le corps de la fiche ne sert que des
   vignettes de 300 px. L'original fait 1000 px pour les photos de Siwa
   et 2560 px pour les autres ; l'image à la une fait 1920 px. Sans
   cette mesure, on ne peut pas savoir ce qui sera flou.
3. **L'image à la une.** Elle n'est pas dans le corps de la page : elle
   se lit par `featured_media`. C'est la couverture choisie par la
   cliente, et elle n'apparaissait nulle part.

    outils/inventaire-programme.py excursion-a-loasis-de-siwa
    outils/inventaire-programme.py --tous
    outils/inventaire-programme.py <slug> --montrer      (n'écrit rien)

Écrit `docs/programmes/<slug>.json`. Lecture seule côté site.
"""

import argparse
import html as H
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from importlib.machinery import SourceFileLoader

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = 'https://authentiquegypte.com'
API = SITE + '/wp-json/wp/v2'
SORTIE = os.path.join(RACINE, 'docs', 'programmes')
CACHE = os.path.join(SORTIE, '_medias.json')

_ex = SourceFileLoader('extraire', os.path.join(RACINE, 'outils', 'extraire.py')).load_module()

# La catégorie de séjours d'un programme, d'après sa catégorie WordPress.
# Le fil d'Ariane de la fiche ne porte que « Accueil › titre » : il ne
# dit pas la famille. Elle se lit dans les catégories du contenu.
CATEGORIES = {
    'deserts-et-oasis': ('Déserts et Oasis égyptiens', SITE + '/nos-sejours-egypte/desert-egypte/'),
    'croisiere-sur-le-nil': ('Croisières en Égypte', SITE + '/nos-sejours-egypte/croisieres-en-egypte/'),
    'mer-rouge-et-plongee': ('Mer rouge et plongée', SITE + '/nos-sejours-egypte/mer-rouge/'),
    'sinai': ('Découverte du Sinaï', SITE + '/nos-sejours-egypte/sinai-moise-et-saint-catherine/'),
    'culturel': ('Voyage culturel en Égypte', SITE + '/nos-sejours-egypte/voyage-culturel-en-egypte/'),
}
CATEGORIE_DEFAUT = ('Nos séjours en Égypte', SITE + '/nos-sejours-egypte/')

# Les fiches dont la famille ne se déduit pas de la catégorie WordPress
# (elles n'en portent pas, ou portent un profil de voyageur).
FAMILLE_FORCEE = {
    'lever-du-soleil-monastere-et-nuit-a-sainte-catherine': 'sinai',
    'sainte-catherine': 'sinai',
    'campement-au-coeur-du-mont-moise': 'sinai',
    'itineraire-sinai-sainte-catherine-mont-moise-et-mer-rouge': 'sinai',
    'pyramides-et-croisiere-sur-le-nil': 'croisiere-sur-le-nil',
    'croisiere-sur-le-lac-nasser': 'croisiere-sur-le-nil',
    'le-caire-et-croisiere-sur-un-bateau-a-voile': 'croisiere-sur-le-nil',
    'decouverte-de-la-nubie': 'culturel',
    'roadtrip-en-egypte': 'culturel',
    'pyramides-louxor-et-mer-rouge-en-famille': 'culturel',
    'mer-rouge': 'mer-rouge-et-plongee',
    'excursion-a-loasis-de-siwa': 'deserts-et-oasis',
    'excursion-a-loasis-de-fayoum': 'deserts-et-oasis',
    'excursion-dans-le-desert-blanc': 'deserts-et-oasis',
}

# Les intitulés d'intendance : ils ferment une étape, ils ne la titrent pas.
MENTION = re.compile(r'^(petit-?déjeuner|déjeuner|dîner|diner|nuit\b|repas)\b', re.I)
MARQUEUR_INCL = re.compile(r"^(le programme inclu|inclus\b|n'inclu|non[- ]inclus)", re.I)
DEBUT_AVIS = re.compile(r'(agence de voyage sur mesure en egypte|\d+\s*avis\s*google)', re.I)
PRIX = re.compile(r"[AÀ]\s*partir\s*de\s*([\d\s ]{2,8})\s*€\s*/?\s*(personne|pers\.?)?", re.I)
AVIS = re.compile(r'(\d{1,4})\s*avis\s*Google', re.I)


def texte_nu(h):
    h = re.sub(r'<[^>]+>', ' ', h or '')
    return re.sub(r'\s+', ' ', H.unescape(h)).strip()


def lire(url, brut=False):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (inventaire-programme)'})
    donnee = urllib.request.urlopen(req, timeout=90).read().decode('utf-8', 'replace')
    return donnee if brut else json.loads(donnee)


# ------------------------------------------------------------------ images

def base_image(url):
    """Le nom de fichier de l'ORIGINAL : sans la taille, sans -scaled."""
    nom = urllib.parse.unquote(url.split('?')[0].rsplit('/', 1)[-1])
    nom = re.sub(r'-\d{2,4}x\d{2,4}(?=\.\w+$)', '', nom)
    # WordPress sert l'original d'une grande image sous « -scaled » : le
    # corps de la page pointe DSC00493-300x201.jpg, la médiathèque
    # DSC00493-scaled.jpg. C'est le même fichier.
    return re.sub(r'-scaled(?=\.\w+$)', '', nom)


class Medias:
    """Résout un nom de fichier vers sa fiche média : original et tailles.

    Le cache est versionné : une image ne change pas de taille, et sans
    lui l'inventaire des 14 fiches referait deux cents requêtes.
    """

    def __init__(self):
        self.cache = {}
        if os.path.exists(CACHE):
            with open(CACHE, encoding='utf-8') as f:
                self.cache = json.load(f)
        self.neuf = 0

    def enregistrer(self):
        os.makedirs(SORTIE, exist_ok=True)
        with open(CACHE, 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, ensure_ascii=False, indent=1, sort_keys=True)

    def par_id(self, ident):
        cle = 'id:%d' % ident
        if cle in self.cache:
            return self.cache[cle]
        try:
            m = lire('%s/media/%d?_fields=id,source_url,alt_text,media_details' % (API, ident))
        except Exception:
            self.cache[cle] = None
            return None
        self.cache[cle] = self._fiche(m)
        self.neuf += 1
        return self.cache[cle]

    def par_nom(self, base):
        cle = 'nom:' + base.lower()
        if cle in self.cache:
            return self.cache[cle]
        souche = re.sub(r'\.\w+$', '', base)
        trouve = None
        try:
            lot = lire('%s/media?search=%s&per_page=5&_fields=id,source_url,alt_text,media_details'
                       % (API, urllib.parse.quote(souche)))
            for m in lot:
                if base_image(m['source_url']).lower() == base.lower():
                    trouve = m
                    break
            if trouve is None and lot:
                # Une image recadrée porte un suffixe de version
                # (« -scaled-e1750597600417 ») : la souche suffit.
                for m in lot:
                    if souche.lower()[:22] in base_image(m['source_url']).lower():
                        trouve = m
                        break
        except Exception:
            trouve = None
        self.cache[cle] = self._fiche(trouve) if trouve else None
        self.neuf += 1
        return self.cache[cle]

    @staticmethod
    def _fiche(m):
        if not m:
            return None
        d = m.get('media_details', {}) or {}
        tailles = {}
        for nom, t in (d.get('sizes') or {}).items():
            if t.get('width') and t.get('source_url'):
                tailles[nom] = {'url': t['source_url'], 'largeur': t['width'], 'hauteur': t.get('height')}
        return {'id': m['id'], 'url': m['source_url'], 'alt': (m.get('alt_text') or '').strip(),
                'largeur': d.get('width'), 'hauteur': d.get('height'), 'tailles': tailles}


def image_inventaire(medias, url_page, alt_page, role, position):
    """Une entrée d'image : l'original, sa taille réelle, son état."""
    base = base_image(url_page)
    m = medias.par_nom(base)
    entree = {'role': role, 'position': position, 'base': base,
              'src_page': url_page, 'alt_page': (alt_page or '').strip()}
    if not m or not m.get('largeur'):
        entree.update({'src_original': url_page, 'largeur': None, 'hauteur': None,
                       'alt': (alt_page or '').strip(), 'media_id': None,
                       'tailles': {}, 'etat': 'non-resolue'})
        return entree
    entree.update({'src_original': m['url'], 'largeur': m['largeur'], 'hauteur': m['hauteur'],
                   'alt': m['alt'] or (alt_page or '').strip(), 'media_id': m['id'],
                   'tailles': m['tailles'], 'etat': 'ok'})
    return entree


def srcset(entree):
    """Le srcset de l'image : ses tailles réelles, même cadrage.

    WordPress fabrique une vignette CARRÉE de 150 px (`thumbnail`) qui
    n'a pas les proportions de l'original. Servie dans un srcset, le
    navigateur peut la choisir pour une petite boîte et afficher un
    cadrage différent de celui qu'on a validé. On ne garde que les
    tailles dont le rapport largeur/hauteur suit l'original à 2 % près.
    """
    lot = {}
    ref = ((entree.get('largeur') or 0) / (entree.get('hauteur') or 1)) if entree.get('hauteur') else 0
    for t in (entree.get('tailles') or {}).values():
        if not t['largeur'] or t['largeur'] > (entree.get('largeur') or 0):
            continue
        if ref and t.get('hauteur'):
            if abs((t['largeur'] / t['hauteur']) - ref) / ref > 0.02:
                continue
        lot[t['largeur']] = t['url']
    if entree.get('largeur'):
        lot[entree['largeur']] = entree['src_original']
    return ', '.join('%s %dw' % (u, l) for l, u in sorted(lot.items()))


# ------------------------------------------------------------------ contenu

def faq_du_bloc(contenu):
    """Les questions/réponses de la FAQ à onglets.

    Les huit questions sont des boutons ; une seule réponse est rendue
    dans le HTML, les huit vivent dans un objet JavaScript. Elles sont
    du contenu écrit par la cliente : on les reprend toutes.
    """
    questions = [texte_nu(m.group(1)) for m in
                 re.finditer(r'data-tab="tab\d+"[^>]*>(.*?)</button>', contenu, re.S)]
    reponses = {}
    # Le nom de l'objet change d'une fiche à l'autre — « contents » sur
    # Siwa, « faqData » sur la Nubie — et le conteneur aussi
    # (faq-container / faq-section). On ne s'appuie donc ni sur l'un ni
    # sur l'autre : on cherche les réponses par leur forme.
    for obj in re.finditer(r'const\s+\w+\s*=\s*\{(.*?)\}\s*;', contenu, re.S):
        for m in re.finditer(r'(tab\d+)\s*:\s*`(.*?)`\s*(?:,|$)', obj.group(1), re.S):
            reponses.setdefault(m.group(1), m.group(2))
    onglets = re.findall(r'data-tab="(tab\d+)"', contenu)

    faq = []
    for i, q in enumerate(questions):
        cle = onglets[i] if i < len(onglets) else None
        brut = reponses.get(cle, '')
        # Le titre est répété en <h3> dans la réponse : il est déjà le
        # libellé de la question, on ne l'affiche pas deux fois.
        corps = re.sub(r'<h3[^>]*>.*?</h3>', '', brut, count=1, flags=re.S)
        corps = re.sub(r'\s+', ' ', corps).strip()
        faq.append({'q': q, 'reponse_html': corps or None,
                    'source': 'onglet JavaScript de la fiche' if corps else None})
    return faq


def sans_bloc_faq(contenu):
    """Le contenu débarrassé du bloc FAQ, lu à part.

    Le bloc porte sa propre feuille de style et son propre script : les
    laisser ferait passer du CSS pour du texte de la fiche. On coupe du
    <style> qui l'ouvre jusqu'à la fin du <script> qui le ferme.
    """
    i = contenu.find('data-tab="tab')
    if i < 0:
        return contenu
    debut = contenu.rfind('<style', 0, i)
    if debut < 0:
        debut = contenu.rfind('<div', 0, i)
    obj = contenu.find('tab2', i)
    fin = contenu.find('</script>', obj if obj > 0 else i)
    fin = (fin + 9) if fin > 0 else contenu.find('</div>', i) + 6
    return contenu[:debut] + contenu[fin:]


def avis_google(contenu):
    m = AVIS.search(texte_nu(contenu))
    return int(m.group(1)) if m else None


BRUIT_AVIS = re.compile(r'^(trustindex|écrire un avis|publié sur google|\d+\s*avis|authentique egypte)', re.I)


def temoignages(ecartes):
    """Les avis Google affichés sur la fiche, auteur par auteur.

    Ils sont écartés du corps — c'est un widget — mais ils sont réels et
    datés : la maquette d'août affichait trois faux témoignages, ceux-ci
    sont ceux que le visiteur lit aujourd'hui sur la page."""
    lot, auteur = [], None
    for t in ecartes:
        t = (t or '').strip()
        if not t or BRUIT_AVIS.match(t):
            continue
        if auteur is None and len(t) <= 40 and not t.endswith(('.', '!', '?')):
            auteur = t
            continue
        if auteur is not None:
            if len(t.split()) >= 6:
                lot.append({'auteur': auteur, 'texte': t})
                auteur = None
            else:
                auteur = t
    return lot


def blocs_du_contenu(contenu):
    d = _ex.Decoupeur()
    d.feed(contenu)
    d.flux()
    return _ex.nettoyer(d.blocs)


def retirer_avis(blocs):
    """Le widget d'avis Google n'est pas du contenu de la fiche.

    Il s'ouvre sur le nom de l'agence et son compte d'avis, et se ferme
    au bloc de prix qui le suit. Les avis retirés sont rendus à part :
    l'agent CONTRÔLE CONTENU doit savoir qu'ils ont été écartés, pas
    perdus."""
    garde, ecartes, dans = [], [], False
    for b in blocs:
        t = b.get('texte', '')
        if not dans and b['type'] == 'p' and DEBUT_AVIS.search(t):
            dans = True
        if dans:
            if b['type'] == 'p' and PRIX.search(t):
                dans = False
            else:
                ecartes.append(t or b['type'])
                continue
        garde.append(b)
    return garde, ecartes


def deroule(blocs):
    """Le jour par jour : un titre d'étape ouvre une étape, un titre
    « Jour N » ouvre un jour. La fiche n'écrit pas toujours les jours ;
    dans ce cas tout le déroulé est un seul jour, et on le dit."""
    jours, jour, etape = [], None, None
    dans = False
    for b in blocs:
        t = b['type']
        if t == 'h2' and re.search(r'étapes|itinéraire|programme|déroul', b['texte'], re.I):
            dans = True
            continue
        if t == 'h2' and dans:
            break
        if not dans:
            continue
        if t == 'liste' and any(MARQUEUR_INCL.match(i) for i in b.get('items', [])):
            break                      # le déroulé s'arrête où commencent les inclusions
        if t == 'titre_etape':
            m = re.match(r'^Jour\s*(\d+)\s*:?\s*(.*)$', b['texte'], re.I)
            if m or jour is None:
                jour = {'n': len(jours) + 1,
                        'titre_source': b['texte'],
                        'titre': (m.group(2).strip() if m and m.group(2) else b['texte']),
                        'numerote': bool(m), 'etapes': [], 'mentions': []}
                jours.append(jour)
                etape = None
                if not m:
                    etape = {'titre': b['texte'], 'paragraphes': [], 'image': None, 'mentions': []}
                    jour['etapes'].append(etape)
            else:
                etape = {'titre': b['texte'], 'paragraphes': [], 'image': None, 'mentions': []}
                jour['etapes'].append(etape)
            continue
        if jour is None:
            continue
        if t == 'p':
            if re.match(r'^FAQ\b', b['texte']) or PRIX.match(b['texte']):
                continue
            if etape is None:
                etape = {'titre': '', 'paragraphes': [], 'image': None, 'mentions': []}
                jour['etapes'].append(etape)
            etape['paragraphes'].append(b['texte'])
        elif t == 'image' and etape is not None and etape['image'] is None:
            etape['image'] = {'src': b['src'], 'alt': b['alt']}
        elif t == 'image' and etape is None:
            etape = {'titre': '', 'paragraphes': [], 'image': {'src': b['src'], 'alt': b['alt']},
                     'mentions': []}
            jour['etapes'].append(etape)
        elif t == 'liste':
            # « Dîner · Nuit en guesthouse » closent l'étape où la fiche
            # les écrit, pas la journée entière : les remonter au jour
            # perdait à quelle étape on dort et où l'on mange.
            items = [i for i in b.get('items', []) if MENTION.match(i)]
            cible = etape['mentions'] if etape is not None else jour['mentions']
            for i in items:
                if i not in cible:
                    cible.append(i)
    return jours


def presentation(blocs):
    """Le titre éditorial (premier H2), le titre de la section de
    présentation tel que la fiche l'écrit, et ses paragraphes."""
    chapo, titre, paras, dans = '', '', [], False
    for b in blocs:
        if b['type'] == 'h2':
            if not chapo and not re.search(r"vue d'ensemble", b['texte'], re.I):
                chapo = b['texte']
                continue
            dans = bool(re.search(r"vue d'ensemble|présentation", b['texte'], re.I))
            if dans:
                titre = b['texte']
            elif paras:
                break
            continue
        if dans and b['type'] == 'p':
            paras.append(b['texte'])
    return chapo, titre, paras


def reperes(blocs):
    for b in reversed(blocs):
        if b['type'] == 'liste' and any(re.search(r'jours?\s*minimum|guide|chauffeur', i, re.I)
                                        for i in b.get('items', [])):
            return b['items']
    return []


def prix(blocs, contenu):
    for b in blocs:
        if b['type'] == 'p':
            m = PRIX.search(b['texte'])
            if m:
                brut = re.sub(r'\s+', ' ', m.group(1)).strip()
                libelle = re.sub(r'\s+', ' ', m.group(0)).strip()
                return {'libelle_source': libelle,
                        'texte': brut + ' €', 'valeur': int(re.sub(r'\D', '', brut) or 0),
                        'unite': (m.group(2) or 'personne').lower(),
                        # « / Personne » : la formulation de la fiche, gardée
                        # telle quelle plutôt que remplacée par la nôtre.
                        'suffixe': libelle.split('€', 1)[1].strip() if '€' in libelle else ''}
    m = PRIX.search(texte_nu(contenu))
    if m:
        brut = re.sub(r'\s+', ' ', m.group(1)).strip()
        return {'libelle_source': re.sub(r'\s+', ' ', m.group(0)).strip(),
                'texte': brut + ' €', 'valeur': int(re.sub(r'\D', '', brut) or 0), 'unite': 'personne'}
    return {'libelle_source': '', 'texte': '', 'valeur': 0, 'unite': ''}


def durees(blocs, chapo, paras):
    """Toutes les durées écrites sur la fiche. Trois valeurs différentes
    sur la même page, c'est la cliente qui tranche, pas nous."""
    vues = []
    for source in [chapo] + paras + [b.get('texte', '') for b in blocs if b['type'] in ('p', 'liste')]:
        for m in re.finditer(r'\b(\d{1,2})\s*(jours?|nuits?)\b', source or '', re.I):
            v = '%s %s' % (m.group(1), m.group(2).lower())
            if v not in vues:
                vues.append(v)
    for b in blocs:
        if b['type'] == 'liste':
            for i in b.get('items', []):
                for m in re.finditer(r'\b(\d{1,2})\s*(jours?|nuits?)\s*(minimum)?', i, re.I):
                    v = ('%s %s %s' % (m.group(1), m.group(2).lower(), m.group(3) or '')).strip()
                    if v not in vues:
                        vues.append(v)
    return vues


# ------------------------------------------------------------------ assemblage

def inventorier(slug, medias, releve):
    lot = lire('%s/programs?slug=%s' % (API, urllib.parse.quote(slug)))
    if not lot:
        sys.exit('fiche introuvable : ' + slug)
    d = lot[0]
    contenu = d['content']['rendered']
    y = d.get('yoast_head_json', {}) or {}

    faq = faq_du_bloc(contenu)
    nb_avis = avis_google(contenu)
    corps = sans_bloc_faq(contenu)
    blocs = blocs_du_contenu(corps)
    blocs, avis_ecartes = retirer_avis(blocs)

    chapo, titre_presentation, paras = presentation(blocs)
    jours = deroule(blocs)
    inclus, exclus = _ex.reperer_inclusions(blocs)

    # --- images : le corps, puis l'image à la une
    images, position = [], 0
    vues = set()
    for b in blocs:
        if b['type'] != 'image':
            continue
        base = base_image(b['src'])
        if base in vues:
            continue
        vues.add(base)
        position += 1
        images.append(image_inventaire(medias, b['src'], b['alt'], 'corps', position))
    une = None
    if d.get('featured_media'):
        m = medias.par_id(d['featured_media'])
        if m:
            une = {'role': 'une', 'position': 0, 'base': base_image(m['url']), 'src_page': '',
                   'alt_page': '', 'src_original': m['url'], 'largeur': m['largeur'],
                   'hauteur': m['hauteur'], 'alt': m['alt'], 'media_id': m['id'],
                   'tailles': m['tailles'], 'etat': 'ok'}
    for e in images + ([une] if une else []):
        e['srcset'] = srcset(e)

    # l'image de chaque étape, ramenée à son entrée d'inventaire
    par_base = {e['base']: e for e in images}
    for j in jours:
        for et in j['etapes']:
            if et['image']:
                e = par_base.get(base_image(et['image']['src']))
                et['image'] = {'base': e['base'], 'src': e['src_original'], 'alt': e['alt'],
                               'largeur': e['largeur'], 'hauteur': e['hauteur'],
                               'srcset': e['srcset']} if e else None

    famille = FAMILLE_FORCEE.get(slug)
    if not famille:
        for cid in d.get('categories', []):
            for s, _ in CATEGORIES.items():
                famille = famille or (s if str(cid) else None)
    cat = CATEGORIES.get(famille, CATEGORIE_DEFAUT)

    inv = {
        'slug': slug, 'id': d['id'], 'url': d['link'], 'releve': releve,
        'modified_gmt': d.get('modified_gmt', ''),
        'title_seo': H.unescape(y.get('title', '') or ''),
        'meta_description': H.unescape(y.get('description', '') or ''),
        'h1': texte_nu(d['title']['rendered']),
        'chapo': chapo,
        'presentation_titre': titre_presentation,
        'presentation': paras,
        'prix': prix(blocs, contenu),
        'reperes': reperes(blocs),
        'durees': durees(blocs, chapo, paras),
        'jours': jours,
        'inclus': inclus, 'exclus': exclus,
        'faq': faq,
        'images': images, 'image_une': une,
        'avis_google': {'nombre': nb_avis, 'source': 'widget Google de la fiche', 'releve': releve,
                        'temoignages': temoignages(avis_ecartes)},
        'categorie': {'nom': cat[0], 'url': cat[1]},
        'ecartes': avis_ecartes,
        'anomalies': [],
    }
    inv['anomalies'] = anomalies(inv)
    return inv


def anomalies(inv):
    a = []
    if len(inv['durees']) > 1:
        a.append('durées contradictoires sur la fiche : ' + ' / '.join(inv['durees']))
    sans = [f['q'] for f in inv['faq'] if not f['reponse_html']]
    if sans:
        a.append('%d question(s) de FAQ sans réponse : %s' % (len(sans), ' · '.join(sans)))
    if not inv['image_une']:
        a.append("la fiche n'a pas d'image à la une")
    elif (inv['image_une'].get('largeur') or 0) < 1360:
        a.append("image à la une de %s px de large : trop petite pour un bandeau plein écran"
                 % inv['image_une'].get('largeur'))
    petites = [e['base'] for e in inv['images'] if (e.get('largeur') or 0) < 720]
    if petites:
        a.append('images sans original au-delà de 720 px : ' + ', '.join(petites))
    perdues = [e['base'] for e in inv['images'] if e['etat'] != 'ok']
    if perdues:
        a.append('images non résolues dans la médiathèque : ' + ', '.join(perdues))
    if not inv['prix']['valeur']:
        a.append('aucun prix lu sur la fiche')
    if not any(j['numerote'] for j in inv['jours']):
        a.append("le déroulé ne numérote pas ses jours : tout est rendu comme un seul jour")
    if not inv['jours']:
        a.append('aucun déroulé jour par jour trouvé')
    # Le déroulé parle-t-il du lieu annoncé par le titre ? Sur la fiche
    # Siwa il décrit le Sinaï : c'est le programme d'un autre séjour,
    # recopié. Un contrôle de mots suffit à le voir, et il vaut pour les
    # quatorze fiches.
    # Deux jours qui portent le MÊME titre sont soit un doublon de
    # saisie, soit une étape manquante. Sur la fiche « Pyramides, Louxor
    # et mer rouge en famille », les jours 5 et 6 s'appellent tous les
    # deux « De Louxor à la Mer Rouge » : le voyageur qui compte ses
    # nuits ne s'y retrouve pas, et nous n'avons pas à trancher à sa
    # place.
    # Le numéro cité est celui que la FICHE écrit (« Jour 7 »), jamais
    # notre rang de lecture : c'est le sien que l'agence doit retrouver.
    def numero(j):
        m = re.match(r'\s*jours?\s*(\d+)', j.get('titre_source') or '', re.I)
        return m.group(1) if m else str(j['n'])

    vus = {}
    for j in inv['jours']:
        cle = ' '.join((j['titre'] or '').lower().split())
        if cle:
            vus.setdefault(cle, []).append(j)
    for titre, lot in vus.items():
        if len(lot) > 1:
            rangs = [numero(j) for j in lot]
            a.append('le titre « %s » revient %d fois, %s'
                     % (lot[0]['titre'], len(lot),
                        'au jour %s' % rangs[0] if len(set(rangs)) == 1
                        else 'aux jours ' + ' et '.join(rangs)))
    # La durée annoncée par l'encart de prix contre le nombre de jours
    # réellement décrits. « 6 jours minimum » sur un déroulé de huit
    # jours, « 2 jours minimum » sur trois : le voyageur qui compare un
    # prix à une durée se trompe, et l'agence ne le voit pas.
    # Au moins deux jours numérotés : en deçà, le déroulé n'est pas un
    # jour par jour et la comparaison ne veut rien dire.
    if len(inv['jours']) > 1 and all(j.get('numerote') for j in inv['jours']):
        decrits = len(inv['jours'])
        ecarts = [d for d in (inv.get('durees') or [])
                  if re.search(r'(\d+)\s*jours?', d, re.I)
                  and int(re.search(r'(\d+)\s*jours?', d, re.I).group(1)) != decrits]
        if ecarts:
            a.append('durée annoncée « %s » pour %d jours décrits dans le déroulé'
                     % (' » et « '.join(ecarts), decrits))

    # Une numérotation à trous est une anomalie à part entière : la
    # fiche famille passe du jour 3 au jour 6.
    suite = [numero(j) for j in inv['jours'] if (j.get('titre_source') or '')]
    chiffres = [int(x) for x in suite if x.isdigit()]
    if len(chiffres) > 1:
        manquants = [n for n in range(min(chiffres), max(chiffres) + 1) if n not in chiffres]
        if manquants:
            a.append('le déroulé saute %s : la fiche numérote %s'
                     % ('le jour ' + str(manquants[0]) if len(manquants) == 1
                        else 'les jours ' + ', '.join(str(x) for x in manquants),
                        ', '.join(suite)))

    lieu = lieu_du_titre(inv['h1'])
    corps = ' '.join(p for j in inv['jours'] for et in j['etapes']
                     for p in et['paragraphes']).lower()
    if lieu and corps and lieu.lower() not in corps:
        a.append('le déroulé ne mentionne jamais « %s », le lieu du titre : '
                 'vérifier que le programme est bien celui de ce séjour' % lieu)
    return a


MOTS_VIDES = {'voyage', 'excursion', 'circuit', 'séjour', 'de', 'du', 'des', 'la', 'le', 'les',
              'a', 'à', 'au', 'aux', 'en', 'et', 'sur', 'dans', 'un', 'une', "l'", 'oasis',
              'mesure', 'égypte', 'egypte', 'découverte', 'croisière', 'lever', 'coucher',
              'soleil', 'nuit', 'campement', 'itinéraire', 'pyramides', 'famille', 'roadtrip'}


def lieu_du_titre(h1):
    """Le nom propre que porte le titre — celui que le déroulé doit citer."""
    for mot in re.split(r"[\s,'’\-]+", h1):
        net = mot.strip("«»\"().:")
        if len(net) > 3 and net.lower() not in MOTS_VIDES and net[:1].isupper():
            return net
    return ''


def bilan(inv):
    img = inv['images']
    hd = sum(1 for e in img if (e.get('largeur') or 0) >= 1360)
    return ('%-52s %2d jour(s) · %2d étape(s) · %2d image(s) (%d ≥ 1360 px) · '
            'FAQ %d/%d répondues · %d inclus / %d exclus · %d anomalie(s)'
            % (inv['slug'][:52], len(inv['jours']),
               sum(len(j['etapes']) for j in inv['jours']), len(img), hd,
               sum(1 for f in inv['faq'] if f['reponse_html']), len(inv['faq']),
               len(inv['inclus']), len(inv['exclus']), len(inv['anomalies'])))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('slug', nargs='?', default='')
    p.add_argument('--tous', action='store_true')
    p.add_argument('--montrer', action='store_true', help="affiche sans écrire")
    p.add_argument('--date', default='', help='date du relevé (défaut : aujourd’hui)')
    a = p.parse_args()

    releve = a.date or __import__('datetime').date.today().isoformat()
    medias = Medias()

    if a.tous:
        slugs = [x['slug'] for x in lire(API + '/programs?per_page=50&_fields=slug')]
    elif a.slug:
        slugs = [a.slug]
    else:
        sys.exit('usage : inventaire-programme.py <slug> | --tous')

    os.makedirs(SORTIE, exist_ok=True)
    for slug in slugs:
        inv = inventorier(slug, medias, releve)
        print(bilan(inv))
        for x in inv['anomalies']:
            print('    ⚠ ' + x)
        if not a.montrer:
            with open(os.path.join(SORTIE, slug + '.json'), 'w', encoding='utf-8') as f:
                json.dump(inv, f, ensure_ascii=False, indent=1)
    medias.enregistrer()
    if not a.montrer:
        print('\n%d inventaire(s) dans docs/programmes/. %d média(s) relevés.' % (len(slugs), medias.neuf))


if __name__ == '__main__':
    main()
