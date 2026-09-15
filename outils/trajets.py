#!/usr/bin/env python3
"""
Les distances et les temps de route entre les lieux d'un séjour.

La fiche dit « départ dans l'après-midi », elle ne dit jamais combien de
kilomètres. Ces deux chiffres-là manquent à quiconque prépare un
voyage — et ils ne s'inventent pas.

Ils sont donc CALCULÉS sur un jeu de routes public, **OSRM sur les
données OpenStreetMap**, entre les coordonnées réelles des lieux que la
fiche nomme, et rangés avec leur source et la date du relevé. Le
gabarit les affiche en le disant : ce sont nos chiffres, pas une
promesse de l'agence.

Deux garde-fous :

- ce qui vient de la FICHE prime toujours. Quand elle écrit « la marche
  dure entre 2h30 et 3h00 », c'est cette phrase qui s'affiche, pas un
  calcul ;
- une route introuvable ne devient jamais une estimation. Elle est
  absente, et c'est tout.

    outils/trajets.py excursion-a-loasis-de-siwa
    outils/trajets.py --tous

Écrit `docs/programmes/_trajets.json`, versionné, relu par le gabarit.
"""

import json
import os
import sys
import time
import urllib.request
from importlib.machinery import SourceFileLoader

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROGRAMMES = os.path.join(RACINE, 'docs', 'programmes')
SORTIE = os.path.join(PROGRAMMES, '_trajets.json')
OSRM = 'https://router.project-osrm.org/route/v1/driving/%s,%s;%s,%s?overview=false'
SOURCE = 'OSRM sur données OpenStreetMap (router.project-osrm.org)'

_gab = SourceFileLoader('gab', os.path.join(RACINE, 'outils', 'gabarit-programme.py')).load_module()


def router(depart, arrivee):
    """Un trajet routier entre deux lieux du répertoire, ou rien."""
    a, b = _gab.LIEUX[depart], _gab.LIEUX[arrivee]
    url = OSRM % (a[1], a[2], b[1], b[2])
    try:
        with urllib.request.urlopen(
                urllib.request.Request(url, headers={'User-Agent': 'trajets-authentique-egypte'}),
                timeout=90) as r:
            d = json.loads(r.read().decode())
    except Exception as err:
        print('   route introuvable %s → %s (%s)' % (depart, arrivee, err))
        return None
    if d.get('code') != 'Ok' or not d.get('routes'):
        print('   route introuvable %s → %s' % (depart, arrivee))
        return None
    route = d['routes'][0]
    km, minutes = round(route['distance'] / 1000), round(route['duration'] / 60)
    if not km or not minutes:
        return None
    # Contrôle de vraisemblance. Entre le monastère Sainte-Catherine et
    # le sommet du mont Moïse, le calculateur rendait 23 km en 2 h 45,
    # soit 8 km/h : il avait routé une VOITURE sur un sentier de
    # montagne. Un chiffre pareil affiché sur une page de vente est pire
    # que pas de chiffre du tout. Hors de la plage 20–120 km/h, on ne
    # publie pas, et on dit pourquoi.
    vitesse = km / (minutes / 60)
    if vitesse < 20 or vitesse > 120:
        return {'douteux': True, 'km': km, 'minutes': minutes,
                'raison': 'vitesse moyenne de %d km/h : ce tronçon n\'est probablement '
                          'pas routier' % round(vitesse)}
    return {'km': km, 'minutes': minutes}


def paires(inv):
    """Les couples de lieux successifs réellement décrits par le déroulé."""
    suite = [x['cle'] for x in _gab.lieux_du_sejour(inv) if x['origine'] == 'deroule']
    return [(suite[i], suite[i + 1]) for i in range(len(suite) - 1)]


def main():
    if not os.path.exists(PROGRAMMES):
        sys.exit('aucun inventaire : lancez outils/inventaire-programme.py')
    if '--tous' in sys.argv:
        slugs = sorted(x[:-5] for x in os.listdir(PROGRAMMES)
                       if x.endswith('.json') and not x.startswith('_'))
    elif len(sys.argv) > 1:
        slugs = [sys.argv[1]]
    else:
        sys.exit('usage : trajets.py <slug> | --tous')

    table = {}
    if os.path.exists(SORTIE):
        with open(SORTIE, encoding='utf-8') as f:
            table = json.load(f).get('trajets', {})

    releve = __import__('datetime').date.today().isoformat()
    neufs = 0
    for slug in slugs:
        chemin = os.path.join(PROGRAMMES, slug + '.json')
        if not os.path.exists(chemin):
            continue
        with open(chemin, encoding='utf-8') as f:
            inv = json.load(f)
        lot = paires(inv)
        print('%-52s %d trajet(s)' % (slug[:52], len(lot)))
        for depart, arrivee in lot:
            cle = depart + '>' + arrivee
            if cle in table:
                continue
            r = router(depart, arrivee)
            neufs += 1
            time.sleep(1.2)                     # on ne martèle pas un service public
            if r:
                r.update({'source': SOURCE, 'releve': releve})
                table[cle] = r
                print('   %-22s → %-22s %5d km · %3d min%s' %
                      (depart, arrivee, r['km'], r['minutes'],
                       '  ⚠ écarté : ' + r['raison'] if r.get('douteux') else ''))

    with open(SORTIE, 'w', encoding='utf-8') as f:
        json.dump({'source': SOURCE, 'releve': releve, 'trajets': table}, f,
                  ensure_ascii=False, indent=1, sort_keys=True)
    print('\n%d trajet(s) au total, %d relevé(s) aujourd\'hui.' % (len(table), neufs))


if __name__ == '__main__':
    main()
