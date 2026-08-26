#!/usr/bin/env python3
"""
Ramène le contenu d'une page WordPress à une structure lisible.

Le site mélange trois écritures : du Gutenberg propre pour les articles,
du HTML aplati par Elementor pour les pages et les séjours, et des
listes à puces qui servent tantôt de programme, tantôt de fil d'Ariane.
On ne peut pas verser ça tel quel dans un gabarit.

Ce module ne réécrit rien et n'invente rien : il découpe, il nomme, et
il jette ce qui n'est pas du contenu (fils d'Ariane, boutons, blocs de
réassurance répétés sur toutes les pages).

    ./outils/extraire.py            extrait tout dans docs/extraits.json
    ./outils/extraire.py <slug>     montre le résultat pour une page
"""

import html as _html
import json
import os
import re
import sys
from html.parser import HTMLParser

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Ces intitulés reviennent sur toutes les pages : ce sont des blocs de
# gabarit, pas du contenu. Les garder reviendrait à les recopier
# soixante et une fois.
BRUIT = (
    'voyage sur mesure en egypte', 'home', 'accueil', 'votre voyage en égypte sur mesure',
    'experts locaux', 'guides égyptologues', 'véhicule sécurisé et chauffeur certifiés',
    'voyage 100% sur mesure', 'nous contacter', 'demander un devis', 'réserver',
    'en savoir plus', 'lire la suite', 'partager', 'newsletter',
    'éditer article', 'découvrir le voyage', 'voir le détail', 'aller plus loin',
    'à explorer également :', 'faq', 'nos séjours', 'personnaliser ce séjour',
)

PRIX = re.compile(r'(?:à\s*partir\s*de\s*)?([\d\s ]{2,7})\s*€\s*(?:/\s*(?:pers|personne)\w*)?', re.I)
DUREE = re.compile(r'\b(\d{1,2})\s*(?:jours?|nuits?)\b', re.I)


class Decoupeur(HTMLParser):
    """Aplatit le HTML en une suite de blocs nommés."""

    GARDES = {'h1', 'h2', 'h3', 'h4', 'p', 'li', 'figcaption', 'blockquote', 'td', 'th'}
    IGNORE = {'script', 'style', 'button', 'nav', 'svg', 'form', 'select', 'option'}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.blocs = []
        self.pile = []
        self.tampon = []
        self.ignore = 0
        self.liste = None
        # Le site — un HTML aplati par Elementor — laisse du texte NU
        # entre les balises (`</p>Un véhicule privé…`) et met les titres
        # d'étapes dans des <a tabindex="0"> d'accordéon. Sans ces deux
        # rattrapages, toute la chair des itinéraires disparaissait.
        self.libre = []
        self.titre_a = None
        # Les tableaux : ils étaient purement et simplement jetés. Le
        # calendrier mois par mois de « quand partir », qui est le cœur
        # de la page, disparaissait avec eux.
        self.tableau = None
        self.ligne = None
        self.entete = False

    BLOCS_FLUX = {'p', 'div', 'section', 'article', 'ul', 'ol', 'table',
                  'h1', 'h2', 'h3', 'h4', 'h5', 'iframe', 'figure', 'br'}

    def flux(self):
        """Verse le texte nu accumulé comme un paragraphe à part entière."""
        texte = re.sub(r'\s+', ' ', ''.join(self.libre)).strip()
        self.libre = []
        if len(texte) <= 2 or texte.lower() in BRUIT:
            return
        # Le chrome du site n'est pas du contenu : l'état des accordéons
        # (« ▼ 02 »), les crochets de shortcode, les libellés de bouton.
        if '▼' in texte or re.fullmatch(r'\[[^\]]+\]', texte):
            return
        if re.match(r'^composer mon voyage', texte, re.I):
            return
        self.blocs.append({'type': 'p', 'texte': texte})

    def handle_starttag(self, balise, attrs):
        a = dict(attrs)
        if balise in self.IGNORE:
            self.ignore += 1
            return
        if self.ignore:
            return
        if balise in self.BLOCS_FLUX:
            self.flux()
        if balise == 'a' and 'tabindex' in a:
            self.flux()
            self.titre_a = []
            return
        if balise == 'img':
            src = a.get('src', '')
            if src and not src.startswith('data:'):
                self.blocs.append({'type': 'image', 'src': src, 'alt': a.get('alt', '').strip()})
            return
        if balise in ('ul', 'ol'):
            self.liste = []
            return
        if balise == 'table':
            self.tableau = {'type': 'tableau', 'entetes': [], 'lignes': []}
            return
        if balise == 'thead':
            self.entete = True
            return
        if balise == 'tr':
            self.ligne = []
            return
        if balise in self.GARDES:
            self.vider()
            self.pile.append(balise)

    def handle_endtag(self, balise):
        if balise in self.IGNORE:
            self.ignore = max(0, self.ignore - 1)
            return
        if self.ignore:
            return
        if balise == 'a' and self.titre_a is not None:
            texte = re.sub(r'\s+', ' ', ''.join(self.titre_a)).strip()
            self.titre_a = None
            if texte and texte.lower() not in BRUIT:
                self.blocs.append({'type': 'titre_etape', 'texte': texte})
            return
        if balise in self.BLOCS_FLUX:
            self.flux()
        if balise in ('ul', 'ol'):
            self.vider()
            items = [x for x in (self.liste or []) if x]
            if items:
                self.blocs.append({'type': 'liste', 'items': items})
            self.liste = None
            return
        if balise == 'thead':
            self.entete = False
            return
        if balise == 'tr':
            self.vider()
            if self.tableau is not None and self.ligne:
                if self.entete and not self.tableau['entetes']:
                    self.tableau['entetes'] = self.ligne
                else:
                    self.tableau['lignes'].append(self.ligne)
            self.ligne = None
            return
        if balise == 'table':
            self.vider()
            if self.tableau and (self.tableau['lignes'] or self.tableau['entetes']):
                # Sans en-tête déclaré, la première ligne en tient lieu.
                if not self.tableau['entetes'] and len(self.tableau['lignes']) > 1:
                    self.tableau['entetes'] = self.tableau['lignes'].pop(0)
                self.blocs.append(self.tableau)
            self.tableau = None
            return
        if balise in self.GARDES and self.pile and self.pile[-1] == balise:
            self.vider()
            self.pile.pop()

    def handle_data(self, texte):
        if self.ignore:
            return
        if self.titre_a is not None:
            self.titre_a.append(texte)
            return
        if self.pile:
            self.tampon.append(texte)
        elif self.liste is None and self.tableau is None:
            self.libre.append(texte)

    def vider(self):
        if not self.pile or not self.tampon:
            self.tampon = []
            return
        texte = re.sub(r'\s+', ' ', ''.join(self.tampon)).strip()
        self.tampon = []
        balise = self.pile[-1]
        if balise in ('td', 'th') and self.ligne is not None:
            self.ligne.append(texte)
            return
        if not texte or texte.lower() in BRUIT:
            return
        if balise == 'li':
            if self.liste is not None:
                self.liste.append(texte)
            return
        self.blocs.append({'type': balise, 'texte': texte})


def nettoyer(blocs):
    """Retire les répétitions et les blocs vides de sens."""
    sortie, vus = [], set()
    for b in blocs:
        if b['type'] in ('p', 'h2', 'h3', 'h4', 'figcaption', 'blockquote'):
            t = b['texte']
            if len(t) < 3:
                continue
            cle = (b['type'], t.lower())
            if cle in vus:
                continue
            vus.add(cle)
        sortie.append(b)
    return sortie


def sectionner(blocs):
    """Regroupe les blocs sous le titre qui les précède."""
    sections, courante = [], {'titre': '', 'niveau': 2, 'blocs': []}
    for b in blocs:
        if b['type'] in ('h2', 'h3', 'h4'):
            if courante['titre'] or courante['blocs']:
                sections.append(courante)
            courante = {'titre': b['texte'], 'niveau': int(b['type'][1]), 'blocs': []}
        else:
            courante['blocs'].append(b)
    if courante['titre'] or courante['blocs']:
        sections.append(courante)
    return sections


def reperer_prix(blocs):
    for b in blocs:
        if b['type'] == 'p':
            m = PRIX.search(b['texte'])
            if m:
                return re.sub(r'\s+', ' ', m.group(1)).strip() + ' €'
    return ''


def reperer_duree(blocs):
    for b in blocs:
        if b['type'] in ('p', 'h2'):
            m = DUREE.search(b['texte'])
            if m:
                return m.group(0)
        if b['type'] == 'liste':
            for i in b['items']:
                m = DUREE.search(i)
                if m:
                    return m.group(0)
    return ''


def reperer_inclusions(blocs):
    """« Le programme inclus » / « N'inclus pas », tels qu'ils sont écrits."""
    inclus, exclus, cible = [], [], None
    for b in blocs:
        if b['type'] == 'liste':
            for item in b['items']:
                bas = item.lower().strip(" :")
                if bas.startswith('le programme inclu') or bas in ('inclus', 'ce qui est inclus'):
                    cible = inclus
                    continue
                if bas.startswith("n'inclus pas") or bas.startswith('non inclus') or bas.startswith('non-inclus'):
                    cible = exclus
                    continue
                if cible is not None:
                    cible.append(item)
    return inclus, exclus


def extraire(item, type_wp):
    brut = item.get('content', {}).get('raw', '') or ''
    d = Decoupeur()
    d.feed(brut)
    d.flux()
    blocs = nettoyer(d.blocs)

    titre = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', item.get('title', {}).get('raw', ''))).strip()
    titre = _html.unescape(titre)

    # Le chapô : le premier vrai paragraphe, avant tout sous-titre.
    chapo = ''
    for b in blocs:
        if b['type'] in ('h2', 'h3', 'h4'):
            if chapo:
                break
            continue
        if b['type'] == 'p' and len(b['texte']) > 80:
            chapo = b['texte']
            break

    images = []
    for b in blocs:
        if b['type'] == 'image' and b['src'] not in [i['src'] for i in images]:
            images.append({'src': b['src'], 'alt': b['alt']})

    inclus, exclus = reperer_inclusions(blocs)

    return {
        'id': item['id'],
        'type': type_wp,
        'slug': item.get('slug', ''),
        'titre': titre,
        'url': item.get('link', ''),
        'chapo': chapo,
        'sections': sectionner([b for b in blocs if b['type'] != 'image']),
        'images': images,
        'prix': reperer_prix(blocs),
        'duree': reperer_duree(blocs),
        'inclus': inclus,
        'exclus': exclus,
        'mots': sum(len(b.get('texte', '').split()) for b in blocs),
        'tableaux': sum(1 for b in blocs if b['type'] == 'tableau'),
    }


def main():
    source = os.path.join(RACINE, 'docs', 'contenus.json')
    if not os.path.exists(source):
        sys.exit('docs/contenus.json manquant — lancez ./outils/inventaire.py --contenus')
    with open(source, encoding='utf-8') as f:
        brut = json.load(f)

    extraits = []
    for type_wp in ('pages', 'posts', 'programs'):
        for item in brut.get(type_wp, []):
            extraits.append(extraire(item, type_wp))

    if len(sys.argv) > 1:
        for e in extraits:
            if e['slug'] == sys.argv[1]:
                print(json.dumps(e, ensure_ascii=False, indent=1)[:6000])
                return
        sys.exit('slug introuvable : ' + sys.argv[1])

    with open(os.path.join(RACINE, 'docs', 'extraits.json'), 'w', encoding='utf-8') as f:
        json.dump(extraits, f, ensure_ascii=False)
    print('%d contenus extraits.' % len(extraits))


if __name__ == '__main__':
    main()
