#!/usr/bin/env python3
"""
Le gabarit d'une page CATÉGORIE — « type de séjour ».

Même discipline que `gabarit-programme.py`, et elle n'est pas
négociable : ce script ne lit QUE des inventaires datés
(`docs/categories/` pour la page, `docs/programmes/` pour les fiches
qu'elle range) et la maquette d'accueil validée. Aucune requête réseau,
aucune donnée écrite à la main, chaque libellé d'interface rattaché à
une décision du registre.

Ce que la page catégorie doit faire, et que la fiche ne fait pas :
**aider à choisir**. Elle porte donc les seuls chiffres qui départagent
quatre séjours d'une même famille — la durée annoncée et le prix de
départ — et un filtre par durée qui fonctionne sans JavaScript.

Ces chiffres ne sont PAS sur la page catégorie du site : ils vivent dans
les fiches. C'est le seul endroit du projet où l'on assemble deux
inventaires, et chaque valeur reste celle de sa fiche, à la lettre.

    outils/gabarit-categorie.py --categorie desert-egypte
    outils/gabarit-categorie.py --tous
"""

import argparse
import json
import os
import re
import sys
from importlib.machinery import SourceFileLoader

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATEGORIES = os.path.join(RACINE, 'docs', 'categories')
PROGRAMMES = os.path.join(RACINE, 'docs', 'programmes')
MAQUETTES = os.path.join(RACINE, 'maquettes')

_g = SourceFileLoader('gabp', os.path.join(RACINE, 'outils',
                                           'gabarit-programme.py')).load_module()
e, ico, image, bloc = _g.e, _g.ico, _g.image, _g.bloc
SITE, DEVIS, WHATSAPP = _g.SITE, _g.DEVIS, _g.WHATSAPP

# Les libellés que NOUS écrivons. Comme pour les fiches : chacun porte sa
# décision, et l'agent contrôle contenu signale tout ce qui n'est pas ici
# ni dans l'inventaire.
INTERFACE = {
    'eyebrow_famille': 'Type de séjour',                            # D49
    'sejours': 'séjours',                                           # D49
    'un_sejour': 'séjour',                                          # D49
    'depuis': 'À partir de',                                        # D6
    'titre_liste': 'Les séjours de cette famille',                  # D49
    'eyebrow_liste': 'Au choix',                                    # D49
    'titre_filtre': 'Combien de jours voulez-vous partir ?',        # D50
    'filtre_tous': 'Tous',                                          # D50
    'filtre_aide': 'Le filtre agit sur les cartes ci-dessous, sans recharger la page.',  # D50
    'filtre_vide': 'Aucun séjour de cette durée dans cette famille.',   # D50
    'voir': 'Voir le séjour',                                       # D49
    'duree_min': 'Durée annoncée',                                  # D49
    'prix_des': 'Dès',                                              # D49
    'prix_absent': 'Prix sur devis',                                # D51
    'source_fiches': 'Durées et prix relevés sur les fiches du site le ',  # D49
    'titre_pourquoi': '',   # celui de la page : arguments.titre
    'eyebrow_pourquoi': 'Pourquoi nous',                            # D49
    'eyebrow_edito': 'Sur mesure',                                  # D49
    'titre_faq': 'Ce qu’on nous demande sur cette famille',    # D6
    'eyebrow_faq': 'Avant de choisir',                              # D6
    'titre_familles': 'Les autres types de séjours',                # D49
    'eyebrow_familles': 'Continuer',                                # D49
    'cta_devis': 'Construire mon séjour',                           # D18
    'cta_whatsapp': 'Poser une question sur WhatsApp',              # D18
}

# Les tranches du filtre. Elles ne sont pas choisies au hasard : ce sont
# les trois formes que prennent réellement les séjours du site — une
# journée, un week-end, un circuit.
TRANCHES = [('court', 'Une journée', lambda n: n <= 1),
            ('moyen', 'De 2 à 3 jours', lambda n: 2 <= n <= 3),
            ('long', '4 jours et plus', lambda n: n >= 4)]


# ------------------------------------------------------------------ données

def charger(dossier, slug):
    with open(os.path.join(dossier, slug + '.json'), encoding='utf-8') as f:
        return json.load(f)


def duree_annoncee(fiche):
    """La durée que la FICHE annonce à côté de son prix.

    Plusieurs fiches en annoncent plus d'une, et elles se contredisent —
    c'est relevé dans `anomalies.md`. Celle qui compte ici est celle qui
    porte « minimum », la formulation commerciale ; à défaut, la
    première. On n'en fabrique aucune."""
    lot = fiche.get('durees') or []
    for d in lot:
        if 'minimum' in d.lower():
            return d
    return lot[0] if lot else ''


def jours_de(texte):
    m = re.search(r'(\d+)\s*jours?', texte or '', re.I)
    return int(m.group(1)) if m else None


def sejours_de(inv):
    """Les séjours de la famille, enrichis de leur fiche."""
    lot = []
    for c in inv['sejours']:
        chemin = os.path.join(PROGRAMMES, c['slug'] + '.json')
        fiche = charger(PROGRAMMES, c['slug']) if os.path.exists(chemin) else {}
        duree = duree_annoncee(fiche)
        lot.append({
            'slug': c['slug'],
            'url': c['url'],
            # Le titre de la carte est celui de la page catégorie ; le H1
            # de la fiche peut différer, et c'est la fiche qui fait foi
            # quand les deux existent.
            'titre': (fiche.get('h1') or c['titre']),
            'titre_liste': c['titre'],
            'image': c.get('image'),
            'prix': (fiche.get('prix') or {}).get('texte') or '',
            'suffixe': (fiche.get('prix') or {}).get('suffixe') or '',
            'duree': duree,
            'jours': jours_de(duree),
            'chapo': fiche.get('chapo') or '',
            'inclus': (fiche.get('inclus') or [])[:3],
            'inclus_tous': fiche.get('inclus') or [],
            'releve': fiche.get('releve') or inv['releve'],
        })
    return lot


def tranche_de(s):
    for cle, _, test in TRANCHES:
        if s['jours'] is not None and test(s['jours']):
            return cle
    return ''


# ------------------------------------------------------------------ sections

def hero(inv, sejours):
    """Le bandeau. Même construction que sur une fiche : la photo n'est
    jamais étirée au-delà de sa taille réelle, le flou remplit le reste,
    le voile est dirigé vers le texte."""
    une = plus_grande(sejours)
    large = (une.get('largeur') or 0) if une else 0
    haut = (une.get('hauteur') or 0) if une else 0
    style = (' style="--une-l:%dpx;--une-h:%dpx"'
             % (large, max(300, min(470, haut // 2)) if haut else 470)) if large else ''
    o = ['<section class="hero"%s>' % style]
    if une:
        o.append('<div class="hero__flou" data-flou="oui" aria-hidden="true">%s</div>'
                 % image(une, large or 1920, sizes='100vw'))
        o.append('<div class="hero__fond">%s</div>'
                 % image(une, min(1920, large) or 1920, priorite=True,
                         sizes=('(max-width:%dpx) 100vw, %dpx' % (large, large))
                         if 0 < large < 1920 else '100vw'))
    o.append('<div class="hero__in"><div class="wrap">')
    pills = ['%d %s' % (len(sejours), INTERFACE['sejours'] if len(sejours) > 1
                        else INTERFACE['un_sejour'])]
    bornes = fourchette(sejours)
    if bornes:
        pills.append(bornes)
    o.append('<div class="hero__pills">' + ''.join(
        '<span class="pill">%s%s</span>' % (ico('pin' if not i else 'horloge', 15), e(p))
        for i, p in enumerate(pills)) + '</div>')
    o.append('<h1>%s</h1>' % e(inv['h1']))
    edito = inv.get('editorial') or {}
    if edito.get('paragraphes'):
        o.append('<p class="hero__chapo">%s</p>' % e(edito['paragraphes'][0]))
    o.append('<div class="hero__bas"><div class="hero__act">'
             f'<a class="btn btn--or" href="{DEVIS}">{e(INTERFACE["cta_devis"])}</a>'
             f'<a class="btn btn--verre" href="{WHATSAPP}">{ico("bulle", 18)} '
             f'{e(INTERFACE["cta_whatsapp"])}</a></div></div>')
    o.append('</div></div></section>')
    return '\n'.join(o)


def plus_grande(sejours):
    lot = [s['image'] for s in sejours if s.get('image') and s['image'].get('largeur')]
    return max(lot, key=lambda x: x['largeur']) if lot else None


def fourchette(sejours):
    """« De 1 à 4 jours » : les durées réellement annoncées, rien d'autre."""
    jours = sorted({s['jours'] for s in sejours if s['jours']})
    if not jours:
        return ''
    if len(jours) == 1:
        return '%d jour%s' % (jours[0], 's' if jours[0] > 1 else '')
    return 'de %d à %d jours' % (jours[0], jours[-1])


def prix_mini(sejours):
    lot = []
    for s in sejours:
        m = re.search(r'([\d\s ]+)\s*€', s['prix'] or '')
        if m:
            lot.append((int(re.sub(r'\D', '', m.group(1))), s['prix']))
    return min(lot)[1] if lot else ''


def commun(sejours):
    """Ce que TOUS les séjours de la famille incluent, mot pour mot.

    Répéter le nom de la famille dans les repères, à 40 px sous le titre
    qui le porte déjà, n'apprenait rien. Une prestation que les quatre
    fiches promettent, si.  L'intersection est faite sur le texte exact
    des inclusions : rien n'est rapproché à la louche."""
    lots = [{x.strip() for x in (s.get('inclus_tous') or [])} for s in sejours]
    lots = [x for x in lots if x]
    if len(lots) != len(sejours) or not lots:
        return ''
    partage = set.intersection(*lots)
    if not partage:
        return ''
    return sorted(partage, key=len)[0]


def reperes(inv, sejours):
    lignes = []
    part = commun(sejours)
    if part:
        lignes.append((_g.icone_repere(_g.libelle_repere(part)),
                       'Sur tous les séjours', part))
    mini = prix_mini(sejours)
    if mini:
        lignes.append(('euro', INTERFACE['depuis'], mini))
    bornes = fourchette(sejours)
    if bornes:
        lignes.append(('horloge', INTERFACE['duree_min'], bornes[0].upper() + bornes[1:]))
    lignes.append(('bulle', 'Séjours', '%d au choix' % len(sejours)))
    o = ['<section class="reperes"><div class="wrap"><ul>']
    for icone, label, valeur in lignes:
        o.append('<li>%s<small>%s</small><b>%s</b></li>'
                 % (ico(icone, 22), e(label), e(valeur)))
    o.append('</ul></div></section>')
    return '\n'.join(o)


def liste(inv, sejours):
    """Les séjours, et le filtre par durée.

    Le filtre est le module d'attention de cette page : sur une famille,
    la question du visiteur n'est pas « lequel est le plus beau » mais
    « combien de jours puis-je partir ». Il est en CSS pur — des boutons
    radio et des règles `:checked` — donc il fonctionne sans JavaScript,
    n'injecte rien au clic et ne décale pas la page (D50).

    Il n'est rendu que si CHAQUE séjour porte une durée annoncée : un
    filtre qui ferait disparaître une carte faute de donnée mentirait
    sur le catalogue."""
    if not sejours:
        return ''
    complet = all(s['jours'] for s in sejours)
    tranches = [(cle, nom) for cle, nom, test in TRANCHES
                if any(s['jours'] and test(s['jours']) for s in sejours)]
    filtrable = complet and len(sejours) > 2 and len(tranches) > 1

    o = ['<section class="pg-sec" id="sejours"><div class="wrap">',
         '<p class="eyebrow">%s</p><h2>%s</h2>' % (e(INTERFACE['eyebrow_liste']),
                                                   e(INTERFACE['titre_liste']))]
    if filtrable:
        o.append('<div class="filtre">')
        o.append('<p class="filtre__t" id="filtre-t">%s</p>' % e(INTERFACE['titre_filtre']))
        o.append('<div class="filtre__o" role="group" aria-labelledby="filtre-t">')
        for i, (cle, nom) in enumerate([('tous', INTERFACE['filtre_tous'])] + tranches):
            o.append('<input class="filtre__r filtre__r--%s" type="radio" name="duree" '
                     'id="f-%s"%s><label class="filtre__l" for="f-%s">%s</label>'
                     % (cle, cle, ' checked' if i == 0 else '', cle, e(nom)))
        o.append('</div>')
        o.append('<p class="filtre__aide">%s</p>' % e(INTERFACE['filtre_aide']))
        o.append('</div>')

    o.append('<div class="cartes cartes--%d">' % len(sejours))
    for s in sejours:
        o.append(carte(s))
    o.append('</div>')
    o.append('<p class="cartes__src">%s%s.</p>'
             % (e(INTERFACE['source_fiches']),
                e(_g.date_fr(max(s['releve'] for s in sejours)))))
    o.append('</div></section>')
    return '\n'.join(o)


def carte(s):
    o = ['<article class="carte" data-duree="%s">' % e(tranche_de(s))]
    if s.get('image'):
        # La boîte fait au plus 380 px : toutes les photos de carte sont
        # au-delà, aucune n'est agrandie.
        o.append('<a class="carte__img" href="%s" tabindex="-1" aria-hidden="true">%s</a>'
                 % (e(s['url']), image(s['image'], 380,
                                       sizes='(max-width:860px) 100vw, 380px')))
    o.append('<div class="carte__c">')
    o.append('<h3><a href="%s">%s</a></h3>' % (e(s['url']), e(s['titre'])))
    if s['chapo']:
        o.append('<p class="carte__ch">%s</p>' % e(s['chapo']))
    puces = []
    if s['duree']:
        puces.append(( 'horloge', s['duree']))
    for x in s['inclus'][:2]:
        puces.append((_g.icone_repere(_g.libelle_repere(x)), x))
    if puces:
        o.append('<ul class="carte__p">%s</ul>'
                 % ''.join('<li>%s<span>%s</span></li>' % (ico(i, 15), e(t)) for i, t in puces))
    o.append('<div class="carte__b">')
    if s['prix']:
        o.append('<span class="carte__prix"><small>%s</small><b>%s</b>%s</span>'
                 % (e(INTERFACE['prix_des']), e(s['prix']),
                    ('<i>%s</i>' % e(s['suffixe'])) if s['suffixe'] else ''))
    else:
        o.append('<span class="carte__prix carte__prix--vide">%s</span>'
                 % e(INTERFACE['prix_absent']))
    o.append('<a class="btn btn--fantome btn--sm" href="%s">%s</a>' % (e(s['url']),
                                                                      e(INTERFACE['voir'])))
    o.append('</div></div></article>')
    return '\n'.join(o)


def pourquoi(inv):
    a = inv.get('arguments') or {}
    if not a.get('points'):
        return ''
    icones = ['etoile', 'bouclier', 'pin', 'guide', 'coche', 'maison']
    o = ['<section class="pg-sec pg-sec--fond"><div class="wrap">',
         '<p class="eyebrow">%s</p>' % e(INTERFACE['eyebrow_pourquoi'])]
    if a.get('titre'):
        o.append('<h2>%s</h2>' % e(a['titre']))
    o.append('<ul class="args">')
    for i, p in enumerate(a['points']):
        o.append('<li>%s<b>%s</b></li>' % (ico(icones[i % len(icones)], 22), e(p)))
    o.append('</ul></div></section>')
    return '\n'.join(o)


def editorial(inv):
    x = inv.get('editorial') or {}
    paras = (x.get('paragraphes') or [])[1:]      # le premier est le chapô du bandeau
    if not x.get('titre') or not paras:
        return ''
    o = ['<section class="pg-sec"><div class="wrap"><div class="edito">',
         '<div><p class="eyebrow">%s</p><h2>%s</h2></div><div class="prose">'
         % (e(INTERFACE['eyebrow_edito']), e(x['titre']))]
    for p in paras:
        o.append('<p>%s</p>' % e(p))
    o.append('</div></div></div></section>')
    return '\n'.join(o)


def faqs(inv, home):
    """Les questions de la page, et les cinq questions pratiques de
    l'accueil validé — les mêmes que sur les fiches (D10)."""
    def accordeon(items, premier_ouvert=True):
        out = ['<div class="acc">']
        for i, it in enumerate(items):
            ouvert = ' open' if (i == 0 and premier_ouvert) else ''
            out.append('<details%s><summary><span class="q">%s</span>'
                       '<span class="acc__plus"></span></summary>'
                       '<div class="acc__c">%s</div></details>'
                       % (ouvert, e(it['q']), it['html']))
        out.append('</div>')
        return ''.join(out)

    fiche = [{'q': f['q'], 'html': f['reponse_html']} for f in inv['faq']]
    pratique = [{'q': x['q'], 'html': x['html']} for x in home['pratique']]
    if not fiche and not pratique:
        return ''
    o = ['<section class="pg-sec pg-sec--fond"><div class="wrap"><div class="faqs">']
    if fiche:
        o.append('<div><p class="eyebrow">%s</p><h2>%s</h2>%s</div>'
                 % (e(INTERFACE['eyebrow_faq']), e(INTERFACE['titre_faq']), accordeon(fiche)))
    if pratique:
        o.append('<div><p class="eyebrow">%s</p><h2>%s</h2>%s</div>'
                 % (e(_g.INTERFACE['eyebrow_pratique']), e(_g.INTERFACE['titre_pratique']),
                    accordeon(pratique, premier_ouvert=False)))
    o.append('</div></div></section>')
    return '\n'.join(o)


def familles(inv, autres):
    if not autres:
        return ''
    o = ['<section class="pg-sec pg-sec--serre"><div class="wrap">',
         '<p class="eyebrow" style="text-align:center">%s</p>' % e(INTERFACE['eyebrow_familles']),
         '<h2 style="text-align:center">%s</h2><div class="fams">'
         % e(INTERFACE['titre_familles'])]
    for a in autres:
        img = ''
        une = plus_grande(a['sejours'])
        if une:
            img = ('<div class="fams__img">%s</div>'
                   % image(une, 340, sizes='(max-width:860px) 100vw, 340px'))
        o.append('<a href="%s">%s<h3>%s</h3><p>%d %s</p></a>'
                 % (e(a['url']), img, e(a['h1']), len(a['sejours']),
                    e(INTERFACE['sejours'] if len(a['sejours']) > 1 else INTERFACE['un_sejour'])))
    o.append('</div></div></section>')
    return '\n'.join(o)


def ariane(inv):
    return ('<div class="wrap"><ol>'
            f'<li><a href="{SITE}/">{e(_g.INTERFACE["ariane_accueil"])}</a></li>'
            f'<li><a href="{SITE}/nos-sejours-egypte/">'
            f'{e(_g.INTERFACE["ariane_sejours"])}</a></li>'
            f'<li><span aria-current="page">{e(inv["h1"])}</span></li></ol></div>')


# ------------------------------------------------------------------ style

CSS = r"""
/* ---------- page catégorie ---------- */
.pg .filtre{background:var(--fond-2);border:1px solid var(--ligne-pg);border-radius:var(--r-l);
  padding:20px 22px;margin:0 0 28px}
.pg .filtre__t{margin:0 0 14px;font-family:"Manrope",sans-serif;font-weight:700;
  font-size:1.04rem;color:var(--nuit-900)}
.pg .filtre__o{display:flex;flex-wrap:wrap;gap:10px}
.pg .filtre__r{position:absolute;width:1px;height:1px;margin:-1px;padding:0;border:0;
  overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
.pg .filtre__l{display:inline-flex;align-items:center;min-height:44px;padding:0 20px;
  border-radius:var(--r-pill);border:1px solid var(--ligne);background:#fff;cursor:pointer;
  font-family:"Manrope",sans-serif;font-weight:600;font-size:.98rem;color:var(--gris-lis);
  transition:border-color .18s,color .18s,background .18s}
.pg .filtre__l:hover{border-color:var(--nuit);color:var(--nuit-900)}
.pg .filtre__r:checked+.filtre__l{background:var(--nuit);border-color:var(--nuit);color:#fff}
.pg .filtre__r:focus-visible+.filtre__l{outline:2px solid var(--teal-txt);outline-offset:3px}
.pg .filtre__aide{margin:14px 0 0;font-family:"Manrope",sans-serif;font-size:.95rem;
  color:var(--gris-lis)}
/* Le filtre en CSS pur : chaque bouton radio commande l'affichage des
   cartes qui ne portent pas sa tranche. Rien n'est injecté au clic,
   rien ne se recharge, et sans JavaScript tout fonctionne. */
.pg .filtre__r--court:checked~.filtre__aide~*,
.pg .filtre__r--moyen:checked~.filtre__aide~*{display:block}
.pg .filtre{position:relative}
.pg .filtre:has(.filtre__r--court:checked)~.cartes .carte:not([data-duree="court"]),
.pg .filtre:has(.filtre__r--moyen:checked)~.cartes .carte:not([data-duree="moyen"]),
.pg .filtre:has(.filtre__r--long:checked)~.cartes .carte:not([data-duree="long"]){display:none}

/* En flex et non en grille : une grille à colonnes automatiques laisse
   la quatrième carte seule et calée à gauche sur une deuxième rangée.
   La dernière rangée se centre, et quatre cartes se rangent en deux
   fois deux plutôt qu'en trois plus une. */
.pg .cartes{display:flex;flex-wrap:wrap;justify-content:center;gap:26px}
/* C'est la BASE qui décide du nombre par rangée, pas la largeur
   maximale : un max-width ne fait que borner la croissance, il ne
   provoque aucun retour à la ligne. Quatre cartes se rangeaient donc
   trois plus une malgré la règle. */
.pg .carte{flex:1 1 300px;max-width:calc((100% - 52px)/3)}
.pg .cartes--1 .carte{flex-basis:560px;max-width:560px}
.pg .cartes--2 .carte,.pg .cartes--4 .carte{flex-basis:calc((100% - 26px)/2);
  max-width:calc((100% - 26px)/2)}
.pg .carte{display:flex;flex-direction:column;background:#fff;border:1px solid var(--ligne-pg);
  border-radius:var(--r-l);overflow:hidden;box-shadow:0 2px 10px rgba(16,32,48,.05)}
.pg .carte__img{display:block;aspect-ratio:16/10;background:var(--fond);overflow:hidden}
.pg .carte__img img{width:100%;height:100%;object-fit:cover;display:block}
.pg .carte__c{display:flex;flex-direction:column;gap:12px;padding:22px;flex:1}
.pg .carte h3{font-size:1.18rem;line-height:1.4}
.pg .carte h3 a{color:inherit;text-decoration:none}
.pg .carte h3 a:hover{color:var(--teal-txt)}
.pg .carte__ch{margin:0;font-size:1rem;line-height:1.6;color:var(--gris-lis)}
.pg .carte__p{list-style:none;margin:0;padding:0;display:grid;gap:8px}
.pg .carte__p li{display:flex;gap:10px;align-items:flex-start;font-family:"Manrope",sans-serif;
  font-size:.98rem;color:var(--texte)}
.pg .carte__p svg{flex:0 0 auto;color:var(--teal-txt);margin-top:2px}
.pg .carte__b{margin-top:auto;padding-top:16px;border-top:1px solid var(--ligne-2);
  display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:12px}
.pg .carte__prix{font-family:"Manrope",sans-serif;line-height:1.25;color:var(--gris-lis)}
.pg .carte__prix small{display:block;font-size:.9rem}
.pg .carte__prix b{font-size:1.32rem;color:var(--nuit-900);font-weight:800}
.pg .carte__prix i{font-style:normal;font-size:.9rem;margin-left:4px}
.pg .carte__prix--vide{font-size:.98rem;font-weight:600;color:var(--gris-lis)}
.pg .cartes__src{margin:20px 0 0;font-family:"Manrope",sans-serif;font-size:.95rem;
  color:var(--gris-lis)}

.pg .args{list-style:none;margin:0;padding:0;display:grid;
  grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:18px}
.pg .args li{display:flex;gap:14px;align-items:center;background:#fff;
  border:1px solid var(--ligne-pg);border-radius:var(--r-l);padding:20px 22px}
.pg .args svg{flex:0 0 auto;color:var(--or-fonce)}
.pg .args b{font-family:"Manrope",sans-serif;font-size:1.04rem;color:var(--nuit-900);
  line-height:1.35}

.pg .edito{display:grid;grid-template-columns:.9fr 1.1fr;gap:48px;align-items:start}
.pg .edito h2{margin:0}
.pg .edito .prose p{font-size:1.06rem;line-height:1.75;color:var(--texte)}
.pg .edito .prose p:last-child{margin-bottom:0}

.pg .fams{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:24px}
.pg .fams a{display:block;color:inherit;text-decoration:none}
.pg .fams__img{border-radius:var(--r-l);overflow:hidden;aspect-ratio:16/10;
  background:var(--fond);margin:0 0 14px}
.pg .fams__img img{width:100%;height:100%;object-fit:cover;display:block}
.pg .fams h3{font-size:1.1rem;line-height:1.4}
.pg .fams a:hover h3{color:var(--teal-txt)}
.pg .fams p{margin:4px 0 0;font-family:"Manrope",sans-serif;font-size:.95rem;
  color:var(--gris-lis)}

@media (max-width:1040px){
  .pg .edito{grid-template-columns:1fr;gap:24px}
  .pg .carte,.pg .cartes--2 .carte,.pg .cartes--4 .carte{flex-basis:calc((100% - 26px)/2);
    max-width:calc((100% - 26px)/2)}
}
@media (max-width:700px){
  .pg .carte,.pg .cartes--1 .carte,.pg .cartes--2 .carte,
  .pg .cartes--4 .carte{flex-basis:100%;max-width:100%}
}
@media (max-width:600px){
  .pg .filtre__aide,.pg .cartes__src,.pg .carte__ch,.pg .fams p,
  .pg .carte__prix small,.pg .carte__prix i{font-size:.95rem}
  .pg .filtre{padding:18px}
  .pg .carte__c{padding:20px}
}
"""


# ------------------------------------------------------------------ page

def page(inv, sejours, home, autres, chemin_charte='assets/charte.css'):
    titre = re.sub(r'\s*[-|]\s*Voyage en Égypte sur mesure\s*$', '',
                   inv['title_seo'] or '').strip() or inv['h1']
    corps = '\n'.join(x for x in [
        hero(inv, sejours),
        reperes(inv, sejours),
        '<nav class="ariane ariane--sous" aria-label="Fil d\'Ariane">%s</nav>' % ariane(inv),
        liste(inv, sejours),
        pourquoi(inv),
        editorial(inv),
        faqs(inv, home),
        _g.avis(inv),
        _g.bande_devis(home),
        familles(inv, autres),
    ] if x)
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(titre)}</title>
<meta name="description" content="{e(inv['meta_description'], quote=True)}">
<meta name="robots" content="noindex,nofollow">
<link rel="icon" href="{SITE}/wp-content/uploads/2026/08/authentique-egypte-logo-transparent.webp">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Archivo:wght@300;400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{chemin_charte}">
<style>{_g.CSS}{CSS}</style>
{json_ld(inv, sejours)}
</head>
<body>
{bloc('entete.html')}
<main class="pg">
{corps}
</main>
{bloc('pied.html')}
<script>{_g.SCRIPT}</script>
</body>
</html>
"""


def json_ld(inv, sejours):
    """La liste des séjours de la famille, et rien de plus.

    Aucun prix n'est déclaré ici : le prix d'une fiche est déclaré par la
    fiche, une seule fois, à sa source."""
    items = [{'@type': 'ListItem', 'position': i + 1, 'name': s['titre'], 'url': s['url']}
             for i, s in enumerate(sejours)]
    if not items:
        return ''
    d = {'@context': 'https://schema.org', '@type': 'CollectionPage',
         'name': inv['h1'], 'url': inv['url'],
         'mainEntity': {'@type': 'ItemList', 'numberOfItems': len(items),
                        'itemListElement': items}}
    return ('<script type="application/ld+json">'
            + json.dumps(d, ensure_ascii=False) + '</script>')


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--categorie', default='')
    p.add_argument('--tous', action='store_true')
    a = p.parse_args()

    # Les fichiers en « _ » sont des réservoirs (les photos de toutes les
    # familles), pas des familles.
    dispo = sorted(x[:-5] for x in os.listdir(CATEGORIES)
                   if x.endswith('.json') and not x.startswith('_'))
    slugs = dispo if a.tous else ([a.categorie] if a.categorie else [])
    if not slugs:
        sys.exit('usage : gabarit-categorie.py --categorie <slug> | --tous')

    home = _g.accueil()
    toutes = {s: charger(CATEGORIES, s) for s in dispo}
    os.makedirs(os.path.join(MAQUETTES, 'site'), exist_ok=True)

    # Une page famille montre les photos des AUTRES familles dans son
    # pied de page : le contrôle de netteté a besoin de les connaître
    # toutes, sinon il les prend pour des images étrangères.
    ensemble = {'slug': '_familles',
                'images': [c['image'] for x in toutes.values()
                           for c in x['sejours'] if c.get('image')],
                'image_une': None}
    with open(os.path.join(CATEGORIES, '_images.json'), 'w', encoding='utf-8') as f:
        json.dump(ensemble, f, ensure_ascii=False, indent=1)

    for slug in slugs:
        inv = toutes[slug]
        sejours = sejours_de(inv)
        autres = [dict(toutes[s], sejours=sejours_de(toutes[s]))
                  for s in dispo if s != slug and toutes[s]['sejours']]
        chemin = os.path.join(MAQUETTES, 'site', 'famille-%s.html' % slug)
        with open(chemin, 'w', encoding='utf-8') as f:
            f.write(_g.vers_le_live(page(inv, sejours, home, autres, '../assets/charte.css')))
        print('%-34s %d séjour(s) · %d question(s) · %d avis · %s'
              % (slug, len(sejours), len(inv['faq']),
                 len(inv['avis_google']['temoignages']), os.path.relpath(chemin, RACINE)))
        for x in inv['anomalies']:
            print('    ⚠ ' + x)


if __name__ == '__main__':
    main()
