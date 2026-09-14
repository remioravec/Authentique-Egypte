#!/usr/bin/env python3
"""
Range la zone « Refonte 2026 » du back-office en deux familles lisibles.

    WP_AUTH='compte:mot de passe' ./outils/ranger-back-office.py \\
        --site maquettes/site [--essai]

Le back-office trie les pages par titre : c'est le titre qui porte le
rangement, pas seulement le rang. Trois dossiers, numérotés pour se suivre :

    Refonte · 1 · Circuits — pages catégorie
        la page mère « Nos séjours », puis les cinq circuits, chacun suivi
        du nombre de séjours qu'il contient
    Refonte · 2 · Séjours — fiches programme
        les quatorze fiches, chacune préfixée par son circuit, de sorte que
        la liste se lit par groupes sans rien déplier
    Refonte · 3 · Maquettes de référence
        la home, la page programme « UX concurrent », le circuit test

Le circuit d'un séjour n'est pas deviné : il est lu dans le fil d'Ariane de
la fiche, qui vient du site en ligne. Rien n'est publié, rien n'est
supprimé : seuls le titre, le parent et le rang des brouillons changent.
"""

import argparse
import html as H
import os
import re
import sys
from importlib.machinery import SourceFileLoader

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dep = SourceFileLoader('dep', os.path.join(RACINE, 'outils', 'deployer.py')).load_module()

MERE = 7642

DOSSIERS = [
    ('circuits', 'Refonte · 1 · Circuits — pages catégorie', 1),
    ('sejours', 'Refonte · 2 · Séjours — fiches programme', 2),
    ('reference', 'Refonte · 3 · Maquettes de référence', 3),
]

# Le nom court d'un circuit, tel qu'il servira de préfixe aux séjours.
COURTS = {
    'Croisières en Égypte': 'Croisières',
    'Déserts et Oasis égyptiens': 'Désert',
    'Mer rouge et plongée': 'Mer rouge',
    'Découverte du Sinaï': 'Sinaï',
    'Voyage culturel en Égypte': 'Culturel',
}
# La page catégorie qui porte chaque circuit, par fragment de slug.
PAGES_CIRCUIT = {
    'Croisières en Égypte': 'croisieres-en-egypte',
    'Déserts et Oasis égyptiens': 'desert-egypte',
    'Mer rouge et plongée': 'mer-rouge',
    'Découverte du Sinaï': 'sinai',
    'Voyage culturel en Égypte': 'voyage-culturel',
}
HUB = 'nos-sejours'
ORDRE_CIRCUITS = ['Croisières en Égypte', 'Déserts et Oasis égyptiens',
                  'Mer rouge et plongée', 'Découverte du Sinaï',
                  'Voyage culturel en Égypte']


def texte(x):
    return re.sub(r'\s+', ' ', H.unescape(re.sub(r'<[^>]+>', ' ', x))).strip()


def titre_de(page):
    t = page['title']
    return t['raw'] if isinstance(t, dict) else t


def circuit_des_fiches(site):
    """Le circuit de chaque fiche, lu dans sa pastille et son fil d'Ariane."""
    circuits = {}
    for nom in sorted(os.listdir(site)):
        if not nom.startswith('programme-') or not nom.endswith('.html'):
            continue
        with open(os.path.join(site, nom), encoding='utf-8') as f:
            h = f.read()
        pastille = re.search(r'<span class="pill">(.*?)</span>', h, re.S)
        nom_circuit = texte(pastille.group(1)) if pastille else ''
        if nom_circuit not in COURTS:
            ariane = re.findall(r'<li[^>]*>\s*<a [^>]*>(.*?)</a>', h, re.S)
            nom_circuit = next((texte(x) for x in ariane if texte(x) in COURTS), '')
        circuits[nom[len('programme-'):-len('.html')]] = nom_circuit
    return circuits


def poser(page, titre, parent, rang, essai):
    if (titre_de(page) == titre and page['parent'] == parent
            and page['menu_order'] == rang):
        return False
    if not essai:
        dep.appel('POST', '/pages/%d' % page['id'],
                  {'title': titre, 'parent': parent, 'menu_order': rang})
    return True


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--site', required=True, help='dossier des fiches (maquettes/site)')
    p.add_argument('--essai', action='store_true', help='montrer sans rien écrire')
    a = p.parse_args()

    circuits = circuit_des_fiches(os.path.abspath(a.site))
    if not circuits:
        raise SystemExit('aucune fiche programme dans %s' % a.site)

    dossiers = dep.appel('GET', '/pages?parent=%d&per_page=50&status=any&context=edit' % MERE)
    enfants = {}
    for d in dossiers:
        enfants[d['id']] = dep.appel(
            'GET', '/pages?parent=%d&per_page=50&status=any&context=edit' % d['id'])

    def dossier_de(fragment):
        for d in dossiers:
            if fragment in d['slug'] or fragment in titre_de(d).lower():
                return d
        return None

    d_sejours = dossier_de('programme')
    d_circuits = dossier_de('type') or dossier_de('categorie')
    d_ref = dossier_de('reference') or dossier_de('maquette')
    if not (d_sejours and d_circuits and d_ref):
        raise SystemExit('les trois dossiers de « Refonte 2026 » n\'ont pas été retrouvés')

    fiches = enfants[d_sejours['id']]
    par_circuit = {c: [] for c in ORDRE_CIRCUITS}
    orphelines = []
    for f in fiches:
        base = f['slug'].replace('refonte-programme-', '')
        cle = next((v for k, v in circuits.items() if k.startswith(base)), '')
        (par_circuit[cle] if cle in par_circuit else orphelines).append(f)

    changes = 0
    print('→ Dossiers')
    for cle, titre, rang in DOSSIERS:
        d = {'circuits': d_circuits, 'sejours': d_sejours, 'reference': d_ref}[cle]
        if poser(d, titre, MERE, rang, a.essai):
            changes += 1
        print('   %-46s id %d' % (titre, d['id']))

    print('\n→ Circuits')
    for page in enfants[d_circuits['id']]:
        base = page['slug'].replace('refonte-famille-', '')
        if base.startswith(HUB):
            titre, rang = 'Refonte · Circuits · 0 · Nos séjours (page mère)', 0
        else:
            nom = next((c for c, frag in PAGES_CIRCUIT.items() if base.startswith(frag)), '')
            if not nom:
                continue
            rang = ORDRE_CIRCUITS.index(nom) + 1
            n = len(par_circuit[nom])
            titre = 'Refonte · Circuits · %d · %s (%d séjour%s)' % (
                rang, nom, n, 's' if n > 1 else '')
        if poser(page, titre, d_circuits['id'], rang, a.essai):
            changes += 1
        print('   %-62s id %d' % (titre[:62], page['id']))

    # Deux fiches peuvent porter le même titre : ce sont les pages en double
    # relevées par le contrôle qualité, deux URL pour un seul contenu. Dans une
    # liste de back-office elles seraient indiscernables : on ajoute leur
    # adresse et on dit que c'en est un.
    vus = {}
    for lot in par_circuit.values():
        for page in lot:
            vus.setdefault(re.sub(r'^Refonte · (?:[^·]+ · )?', '', titre_de(page)), []).append(page['id'])
    doublons = {i for ids in vus.values() if len(ids) > 1 for i in ids}

    print('\n→ Séjours, groupés par circuit')
    rang = 0
    for nom in ORDRE_CIRCUITS:
        for page in sorted(par_circuit[nom], key=lambda x: titre_de(x)):
            rang += 1
            propre = re.sub(r'^Refonte · (?:[^·]+ · )?', '', titre_de(page))
            if page['id'] in doublons:
                propre += ' — doublon /%s' % page['slug'].replace('refonte-programme-', '')
            titre = 'Refonte · %s · %s' % (COURTS[nom], propre)
            if poser(page, titre, d_sejours['id'], rang, a.essai):
                changes += 1
            print('   %-72s id %d' % (titre[:72], page['id']))
    for page in orphelines:
        rang += 1
        print('   %-72s id %d  (circuit non lu)' % (titre_de(page)[:72], page['id']))

    print('\n%d page(s) %s. Rien n\'a été publié ni supprimé.'
          % (changes, 'à ranger' if a.essai else 'rangée(s)'))


if __name__ == '__main__':
    main()
