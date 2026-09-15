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
        les pages d'essai, préfixées par le type de page qu'elles montrent
        — accueil, programme, circuit — pour qu'on sache ce qu'on ouvre

La page « Refonte · 0 · Sommaire », posée par outils/sommaire-cms.py, reste
au rang 0 sous la mère : elle n'appartient à aucun dossier, elle les liste.

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
    ('reference', 'Refonte · 7 · Maquettes de référence', 7),
]

# Les familles déployées par outils/deployer-refonte.py. Le rangement leur
# donne un rang et un préfixe de titre ; le dossier est retrouvé par son slug,
# qui ne bouge pas. « Réf » est en dernier : ce sont des pages d'essai, pas
# des livrables, et elles n'ont pas à s'intercaler entre deux familles du site.
FAMILLES = [
    ('refonte-destinations',   3, 'Refonte · 3 · Destinations', 'Destination'),
    ('refonte-profils',        4, 'Refonte · 4 · Profils de voyageur', 'Profil'),
    ('refonte-guides',         5, 'Refonte · 5 · Guides et articles', 'Guide'),
    ('refonte-institutionnel', 6, 'Refonte · 6 · Pages institutionnelles', 'Page'),
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
SOMMAIRE = 'refonte-sommaire'

# Le type de page qu'une maquette de référence donne à voir, reconnu dans
# son slug — pas dans son titre : le titre, ce script le réécrit, et au
# passage suivant il ne retrouverait plus le mot qu'il vient d'en retirer.
#
# Chaque type est un vrai sous-dossier de « Maquettes de référence », et non
# plus un préfixe de titre : le dossier porte le type, la page ne porte que
# son nom. Le rang ordonne les sous-dossiers entre eux.
TYPES_REFERENCE = [
    (1, 'Home', 'refonte-ref-home', re.compile(r'accueil|home')),
    (2, 'Circuits', 'refonte-ref-circuits', re.compile(r'circuit|famille|categorie')),
    (3, 'Programmes', 'refonte-ref-programmes', re.compile(r'programme|sejour|voyage')),
]


def type_de_reference(page):
    """Le type d'une maquette de référence, son sous-dossier et son nom.

    Le type se lit dans le slug, qui ne bouge jamais. Le titre, lui, est
    réécrit à chaque passage : y chercher « programme » après l'en avoir
    retiré reclasserait la page en « Autre » dès le deuxième tour.

    Les motifs se chevauchent — « refonte-programme-oasis-de-siwa » contient
    « programme » et « refonte-circuit-test-… » contient « circuit » — donc
    l'ordre de TYPES_REFERENCE tranche, et le premier qui répond gagne.
    """
    nu = re.sub(r'^Refonte · (?:R[ée]f · )?(?:[^·]+ · )?', '', titre_de(page)).strip()
    for rang, nom, slug, motif in TYPES_REFERENCE:
        if motif.search(page['slug']):
            return rang, nom, slug, sans_redite(nom, nu)
    return 9, 'Autre', '', nu


def sans_redite(nom, nu):
    """Le nom d'une maquette sans répéter le type qu'on vient d'annoncer.

    « Circuit test — D'Alexandrie » sous le type Circuit devient
    « D'Alexandrie » ; « Accueil (version du 10/09) » devient « version du
    10/09 ». Mais un nom qui se réduirait à rien est gardé tel quel :
    « HOME » reste « HOME », c'est ce qui le distingue de l'autre accueil.
    """
    singulier = nom.rstrip('s')
    reste = re.sub(r'^%s\w{0,2}\b[^—–:-]{0,12}[—–:-]\s*' % singulier, '', nu, flags=re.I)
    if reste == nu:
        reste = re.sub(r'^%s\w{0,2}\b\s*' % singulier, '', nu, flags=re.I)
    entier = re.fullmatch(r'\((.+)\)', reste.strip())
    if entier:
        reste = entier.group(1)
    return reste.strip() or nu
ORDRE_CIRCUITS = ['Croisières en Égypte', 'Déserts et Oasis égyptiens',
                  'Mer rouge et plongée', 'Découverte du Sinaï',
                  'Voyage culturel en Égypte']


def texte(x):
    return re.sub(r'\s+', ' ', H.unescape(re.sub(r'<[^>]+>', ' ', x))).strip()


def nom_nu(titre):
    """Le nom d'une fiche, sans le préfixe ni la marque posés ici.

    Le script est relancé après chaque déploiement : il doit lire ses
    propres titres sans se laisser abuser par ce qu'il y a lui-même
    écrit, sinon « — doublon /slug » devient une part du nom et les deux
    pages sœurs cessent de se ressembler.
    """
    nu = re.sub(r'^Refonte · (?:[^·]+ · )?', '', titre)
    return re.sub(r'\s*—\s*doublon\s+/\S*$', '', nu).strip()


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

    dossiers = [d for d in dep.appel(
        'GET', '/pages?parent=%d&per_page=50&status=any&context=edit' % MERE)
        if d['slug'] != SOMMAIRE]
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
            vus.setdefault(nom_nu(titre_de(page)), []).append(page['id'])
    doublons = {i for ids in vus.values() if len(ids) > 1 for i in ids}

    print('\n→ Séjours, groupés par circuit')
    rang = 0
    for nom in ORDRE_CIRCUITS:
        for page in sorted(par_circuit[nom],
                           key=lambda x: (nom_nu(titre_de(x)), x['slug'])):
            rang += 1
            propre = nom_nu(titre_de(page))
            if page['id'] in doublons:
                propre += ' — doublon /%s' % page['slug'].replace('refonte-programme-', '')
            titre = 'Refonte · %s · %s' % (COURTS[nom], propre)
            if poser(page, titre, d_sejours['id'], rang, a.essai):
                changes += 1
            print('   %-72s id %d' % (titre[:72], page['id']))
    for page in orphelines:
        rang += 1
        print('   %-72s id %d  (circuit non lu)' % (titre_de(page)[:72], page['id']))

    # Les maquettes de référence vont dans un sous-dossier par type de page.
    # Le dossier porte le type, la page ne porte plus que son nom : sans cela
    # « Réf · Home · HOME » répète deux fois la même information.
    print('\n→ Maquettes de référence, en sous-dossiers par type de page')
    # Les pages se lisent dans le dossier ET dans ses sous-dossiers : une
    # fois rangées elles ne sont plus filles directes, et sans cette descente
    # le script les perdrait de vue dès le passage suivant.
    connus = {slug for _, _, slug, _ in TYPES_REFERENCE}
    plates = []
    for e in enfants[d_ref['id']]:
        if e['slug'] in connus:
            plates += dep.appel(
                'GET', '/pages?parent=%d&per_page=50&status=any&context=edit' % e['id'])
        else:
            plates.append(e)
    refs = [(type_de_reference(p), p) for p in plates]
    for rang, nom, slug, motif in TYPES_REFERENCE:
        lot = sorted((x for x in refs if x[0][0] == rang), key=lambda x: x[0][3])
        if not lot:
            continue                    # pas de dossier vide : rien à y ranger
        titre = 'Refonte · Réf · %d · %s' % (rang, nom)
        if a.essai:
            sous = next((d for d in dep.appel(
                'GET', '/pages?slug=%s&status=any&per_page=1&context=edit' % slug) or []
                if True), None)
            sid = sous['id'] if sous else 0
        else:
            sous, _ = dep.poser_page(slug, {'title': titre, 'parent': d_ref['id'],
                                            'menu_order': rang, 'status': 'draft'})
            sid = sous['id']
        print('   %-64s id %s' % (titre, sid or '—'))
        for n, ((_, _, _, propre), page) in enumerate(lot, 1):
            t = 'Refonte · Réf · %s' % propre
            if poser(page, t, sid, n, a.essai):
                changes += 1
            print('      %-68s id %d' % (t[:68], page['id']))
    orphelins = [x for x in refs if x[0][0] == 9]
    for (_, _, _, propre), page in orphelins:
        print('      %-68s id %d  (type non lu)' % (titre_de(page)[:68], page['id']))

    # Les autres familles : destinations, profils, guides, institutionnelles.
    # Elles n'ont pas de sous-groupe — une liste alphabétique suffit à s'y
    # retrouver — mais elles reçoivent le préfixe de leur famille, pour que le
    # titre reste lisible seul, hors de son dossier, dans une recherche.
    for slug, rang, titre, prefixe in FAMILLES:
        d = next((x for x in dossiers if x['slug'] == slug), None)
        if not d:
            continue
        if poser(d, titre, MERE, rang, a.essai):
            changes += 1
        pages = sorted(enfants.get(d['id'], []), key=lambda x: nom_nu(titre_de(x)))
        print('\n→ %s (%d)' % (titre, len(pages)))
        for n, page in enumerate(pages, 1):
            t = 'Refonte · %s · %s' % (prefixe, nom_nu(titre_de(page)))
            if poser(page, t, d['id'], n, a.essai):
                changes += 1
            print('   %-72s id %d' % (t[:72], page['id']))

    print('\n%d page(s) %s. Rien n\'a été publié ni supprimé.'
          % (changes, 'à ranger' if a.essai else 'rangée(s)'))


if __name__ == '__main__':
    main()
