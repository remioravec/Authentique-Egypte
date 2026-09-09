#!/usr/bin/env python3
"""
L'inventaire daté de la page d'accueil — la source qui manquait.

`maquettes/index.html` a été promue SOURCE pour vingt pages : les deux
générateurs y lisent les questions pratiques, le bloc équipe et les
étapes du parcours, et les recopient sur chaque fiche et chaque page
famille. Or cette maquette n'avait jamais été confrontée à l'accueil en
ligne. L'agent contrôle contenu du 09/09/2026 l'a fait, et a trouvé :
sur treize questions de la cliente, cinq sont reprises, toutes
reformulées, dont deux sans aucune source — un budget « 1 400 à
2 200 € » qui n'existe nulle part, et une politique de zones qui
contredit le catalogue de la même page.

Ce module relève donc l'accueil EN LIGNE, comme on relève une fiche :

- les **treize questions** de l'accordéon, en trois groupes, avec leurs
  réponses telles que la cliente les écrit ;
- ses **blocs éditoriaux** — « Voyagez autrement… », « Avec les locaux,
  les expériences sont toujours », « Créez un voyage qui vous
  ressemble », « Pouvons-nous vous accompagner ? » ;
- ses **quatre arguments** et leurs textes.

Ce qu'il ne relève pas, il ne l'invente pas : l'accueil en ligne ne
présente **aucune personne nommée**. Les quatre prénoms de la maquette
n'ont donc pas de source.

    outils/inventaire-accueil.py

Écrit `docs/accueil.json`. Lecture seule côté site.
"""

import html as H
import json
import os
import re
from importlib.machinery import SourceFileLoader

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SORTIE = os.path.join(RACINE, 'docs')
ID_ACCUEIL = 38

_p = SourceFileLoader('invp', os.path.join(RACINE, 'outils',
                                           'inventaire-programme.py')).load_module()
_c = SourceFileLoader('invc', os.path.join(RACINE, 'outils',
                                           'inventaire-categorie.py')).load_module()

# Les corrections que la cliente a demandées et que l'accueil en ligne ne
# porte pas encore. Chacune est datée et tracée ; il n'y en a pas
# d'autre, et toute autre différence avec la source est une faute.
CORRECTIONS = [
    # (motif, remplacement, source)
    (re.compile(r'\b25\s*€'), '30 €',
     'retour Mélanie du 24/08/2026, backlog C1 : le visa est passé à 30 €'),
]


def corriger(texte):
    for motif, vers, _ in CORRECTIONS:
        texte = motif.sub(vers, texte)
    return texte


def groupes(contenu):
    """Les treize questions, dans leurs trois groupes."""
    titres = [(m.start(), H.unescape(_p.texte_nu(m.group(1))))
              for m in re.finditer(r'<h2[^>]*>(.*?)</h2>', contenu, re.S)]
    lot = []
    for rang, (debut, titre) in enumerate(titres):
        fin = titres[rang + 1][0] if rang + 1 < len(titres) else len(contenu)
        questions = _c.faq(contenu[debut:fin])
        if questions:
            for q in questions:
                q['reponse_html'] = corriger(q['reponse_html'])
            lot.append({'titre': titre, 'questions': questions})
    return lot


def bloc(contenu, amorce):
    return _c.bloc_texte(contenu, amorce)


def arguments(contenu):
    """« Avec les locaux… » : trois arguments, titre ET texte."""
    titre = ''
    m = re.search(r'<h2[^>]*>((?:(?!</h2>).)*?Avec les locaux(?:(?!</h2>).)*?)</h2>',
                  contenu, re.S)
    if m:
        titre = H.unescape(_p.texte_nu(m.group(1)))
    lot = []
    # L'accueil n'utilise pas le même composant que les pages catégorie :
    # ici le titre est un `h3.title` et le texte un `p.icon-box-description`.
    for x in re.finditer(r'<h3 class="title">(.*?)</h3>\s*'
                         r'<p class="icon-box-description">(.*?)</p>', contenu, re.S):
        lot.append({'titre': H.unescape(_p.texte_nu(x.group(1))),
                    'texte': H.unescape(_p.texte_nu(x.group(2)))})
    return {'titre': titre, 'points': lot}


def anomalies(inv):
    a = []
    n = sum(len(g['questions']) for g in inv['groupes'])
    if n < 5:
        a.append('%d question(s) seulement relevée(s) sur l\'accueil' % n)
    if not inv['arguments']['points']:
        a.append('les arguments de l\'accueil n\'ont pas été relevés')
    for cle in ('voyagez_autrement', 'creez_un_voyage', 'appel_final'):
        if not inv.get(cle):
            a.append('bloc éditorial manquant : ' + cle)
    return a


def main():
    p = _p.lire('%s/pages/%d?_fields=id,slug,link,title,content,modified_gmt,yoast_head_json'
                % (_p.API, ID_ACCUEIL))
    contenu = p['content']['rendered']
    y = p.get('yoast_head_json') or {}
    h1 = re.search(r'<h1[^>]*>(.*?)</h1>', contenu, re.S)
    releve = __import__('datetime').date.today().isoformat()

    inv = {
        'id': p['id'], 'slug': p['slug'], 'url': p['link'], 'releve': releve,
        'modified_gmt': p.get('modified_gmt'),
        'title_seo': (y.get('title') or '').strip(),
        'meta_description': (y.get('description') or '').strip(),
        'h1': H.unescape(_p.texte_nu(h1.group(1))) if h1 else '',
        'groupes': groupes(contenu),
        'arguments': arguments(contenu),
        'voyagez_autrement': bloc(contenu, 'Voyagez autrement'),
        'creez_un_voyage': bloc(contenu, 'Créez un voyage'),
        'appel_final': bloc(contenu, 'Pouvons-nous vous accompagner'),
        'corrections': [{'motif': m.pattern, 'vers': v, 'source': s}
                        for m, v, s in CORRECTIONS],
        'equipe': [],   # l'accueil en ligne ne nomme personne : on n'invente pas
    }
    inv['anomalies'] = anomalies(inv)

    os.makedirs(SORTIE, exist_ok=True)
    with open(os.path.join(SORTIE, 'accueil.json'), 'w', encoding='utf-8') as f:
        json.dump(inv, f, ensure_ascii=False, indent=1)
    print('accueil : %d groupe(s), %d question(s), %d argument(s)'
          % (len(inv['groupes']), sum(len(g['questions']) for g in inv['groupes']),
             len(inv['arguments']['points'])))
    for g in inv['groupes']:
        print('   %-28s %d question(s)' % (g['titre'][:28], len(g['questions'])))
    for x in inv['anomalies']:
        print('    ⚠ ' + x)


if __name__ == '__main__':
    main()
