#!/usr/bin/env python3
"""
Déploie tout le site repris en brouillon sous « Refonte 2026 », rangé par type.

    WP_AUTH='compte:mot de passe' ./outils/deployer-refonte.py \\
        --site DIR [--seulement prefixe] [--essai]

Un dossier par type de page, numéroté pour que le back-office les affiche
dans l'ordre. Le nom de fichier porte le type : `guide-quand-partir.html`
va dans les guides, `destination-lac-nasser.html` dans les destinations.

Rien n'est publié, rien n'est supprimé. Relancé, l'outil met à jour les
mêmes pages : la reconnaissance se fait sur le slug, et WordPress tronque
les slugs longs, donc une page déjà en ligne est retrouvée par préfixe
plutôt que par égalité stricte — sans quoi chaque passage créerait un
doublon des fiches au nom à rallonge.

Chaque écriture est relue. Le serveur rend parfois une réponse vide, et une
page laissée à moitié à jour ne se voit pas autrement qu'à l'œil.
"""

import argparse
import os
import re
import sys
import time
from importlib.machinery import SourceFileLoader

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dep = SourceFileLoader('dep', os.path.join(RACINE, 'outils', 'deployer.py')).load_module()
conv = SourceFileLoader('conv', os.path.join(RACINE, 'outils', 'vers-page-wp.py')).load_module()

MERE = 7642

# Un dossier par GABARIT, et son titre dit ce qu'il contient. « Circuit »
# et « programme » ne se distinguaient pas à la lecture — les deux parlent
# de séjours. Le titre tranche désormais : l'un LISTE, l'autre est la FICHE
# d'un seul séjour, avec son prix et son itinéraire.
#
# Un dossier par GABARIT, et rien d'autre. Le back-office se lit alors
# comme la refonte se pense : chaque dossier réunit des pages sœurs, bâties
# sur le même moule, qu'on peut donc comparer l'une à l'autre sans les
# chercher. Le hub blog quitte les guides — il porte le gabarit circuit,
# eux le gabarit article — et l'accueil comme la page agence reçoivent leur
# dossier plutôt que de flotter parmi les dossiers, où l'œil les prenait
# pour des rubriques vides.
#
# préfixe de fichier → (rang du dossier, titre du dossier, slug du dossier)
TYPES = [
    ('famille-',     1, 'Refonte · 1 · Gabarit circuit — les pages qui LISTENT des séjours', 'refonte-types-de-s-jour'),
    ('programme-',   2, 'Refonte · 2 · Gabarit programme — la FICHE d’un séjour, prix et itinéraire', 'refonte-programmes'),
    ('destination-', 3, 'Refonte · 3 · Gabarit destination — un lieu', 'refonte-destinations'),
    ('qui-part-',    4, 'Refonte · 4 · Gabarit qui part — un profil de voyageur', 'refonte-profils'),
    ('guide-',       5, 'Refonte · 5 · Gabarit guide — les articles du blog', 'refonte-guides'),
    ('hub-',         6, 'Refonte · 6 · Gabarit blog — le sommaire des guides', 'refonte-blog'),
    ('accueil-',     7, 'Refonte · 7 · Gabarit accueil', 'refonte-accueil'),
    ('agence-',      8, 'Refonte · 8 · Gabarit qui sommes-nous', 'refonte-agence'),
]

# Ce qui ne fait plus partie de la refonte, et qu'il ne faut donc pas
# redéployer. Les fichiers sources restent dans le dépôt — on ne supprime
# rien — mais l'outil ne les repose plus : sans cette liste, chaque
# déploiement ressuscitait les mentions légales et l'ancienne page d'accueil
# que l'agence avait fait retirer, le lendemain de leur mise à la corbeille.
HORS_REFONTE = ('legal-',)

# L'accueil garde la version que Rémi a choisie le 10/09 : son dossier est
# créé et la page y est rangée, mais son CONTENU n'est jamais réécrit. Le
# fichier local en porte une autre, plus ancienne.
NE_PAS_REECRIRE = ('accueil-',)

# Plus de page posée seule sous la mère : chaque gabarit a son dossier.
SEULES = {}

# Les liens relatifs des maquettes — « index.html », « devis.html »… — ne
# mènent nulle part une fois la page dans WordPress. Mesurés : 44 à 58
# pages les portent, dans le méga-menu, l'entête et le pied. Chaque entrée
# du menu était donc morte.
#
# On les réécrit au déploiement plutôt que dans le dépôt : le nom de
# fichier reste la vérité côté maquette, et la cible suit le CMS. Quand la
# refonte porte la page, le lien va vers SON brouillon — la relecture reste
# dans la refonte au lieu d'éjecter vers le site en ligne. À défaut, il va
# vers l'adresse en ligne, vérifiée une à une (les trois premières
# redirigent : on pose la destination finale, pas la redirection).
LIENS = {
    'index.html':            ('accueil-', 'https://authentiquegypte.com/'),
    'devis.html':            (None, 'https://authentiquegypte.com/sur-mesure/'),
    'blog.html':             ('hub-', 'https://authentiquegypte.com/notre-blog/'),
    'qui-sommes-nous.html':  ('agence-', 'https://authentiquegypte.com/qui-sommes-nous/'),
    'categorie.html':        ('famille-croisieres-en-egypte',
                              'https://authentiquegypte.com/nos-sejours-egypte/croisieres-en-egypte/'),
    'categorie-desert.html': ('famille-desert-egypte',
                              'https://authentiquegypte.com/nos-sejours-egypte/desert-egypte/'),
    'destination.html':      ('destination-voyage-au-caire',
                              'https://authentiquegypte.com/voyage-au-caire/'),
    'legal.html':            (None,
                              'https://authentiquegypte.com/mentions-legales-agence-voyage-egypte/'),
}


def carte_des_liens(*relevés):
    """Chaque lien de maquette vers sa destination réelle.

    On cherche dans TOUS les relevés : l'accueil et la page agence n'ont pas
    de dossier — ce sont des filles directes de la mère — et un premier jet
    qui ne lisait que les dossiers renvoyait le menu vers le site en ligne
    pour ces deux-là précisément, celles qu'on veut le plus relire.
    """
    carte = {}
    for fichier, (prefixe, secours) in LIENS.items():
        cible = secours
        if prefixe:
            for relevé in relevés:
                trouve = next((p for slug, p in sorted(relevé.items())
                               if slug.startswith('refonte-' + prefixe)), None)
                if trouve:
                    cible = '%s/?page_id=%d' % (dep.SITE, trouve['id'])
                    break
        carte[fichier] = cible
        carte['../' + fichier] = cible
    return carte


def poser_liens(contenu, carte):
    """Remplace les liens de maquette, et EUX SEULS.

    Une réécriture large attraperait « https://…/index.html » d'un site
    tiers : on n'agit que sur la valeur exacte de l'attribut.
    """
    n = 0
    for depart, arrivee in carte.items():
        motif = 'href="%s"' % depart
        n += contenu.count(motif)
        contenu = contenu.replace(motif, 'href="%s"' % arrivee)
    return contenu, n


# Le nom lisible d'une page, quand le titre du fichier ne suffit pas.
def titre_de_page(nom, html):
    """Le titre de la page, pris dans son <title> ou son <h1>."""
    for motif in (r'<title>(.*?)</title>', r'<h1[^>]*>(.*?)</h1>'):
        m = re.search(motif, html, re.S | re.I)
        if m:
            t = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', m.group(1))).strip()
            t = re.sub(r'\s*[|–—-]\s*Authentique\s*Égypte.*$', '', t, flags=re.I)
            if t:
                return t[:120]
    return nom


def prefixe_seul(nom):
    """Le préfixe d'une page unique — sans dossier —, ou None."""
    for prefixe in SEULES:
        if nom.startswith(prefixe):
            return prefixe
    return None


def type_de(nom):
    if any(nom.startswith(x) for x in HORS_REFONTE):
        return None
    for prefixe, rang, titre, slug in TYPES:
        if nom.startswith(prefixe):
            return prefixe, rang, titre, slug
    return None


def ecrire(page_id, champs, marqueur, attendu, etiquette):
    """Une écriture relue. Rend True si la page en ligne porte bien le contenu."""
    for essai in range(3):
        try:
            dep.appel('POST', '/pages/%d' % page_id, champs)
        except SystemExit as motif:
            print('      reprise %d/2 — %s' % (essai + 1, str(motif).splitlines()[0][:60]))
            time.sleep(2 ** essai)
            continue
        relu = dep.appel('GET', '/pages/%d?context=edit' % page_id)['content']['raw']
        if len(re.findall(marqueur, relu)) == attendu:
            return True
        print('      reprise %d/2 — %s : %d au lieu de %d'
              % (essai + 1, etiquette, len(re.findall(marqueur, relu)), attendu))
        time.sleep(2 ** essai)
    return False


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--site', required=True, help='dossier des pages à déployer')
    p.add_argument('--seulement', help='ne traiter que les fichiers de ce préfixe')
    p.add_argument('--essai', action='store_true', help='montrer sans rien écrire')
    a = p.parse_args()

    source = os.path.abspath(a.site)
    retenu = (lambda f: not a.seulement or f.startswith(a.seulement))
    fichiers = sorted(f for f in os.listdir(source)
                      if f.endswith('.html') and type_de(f) and retenu(f))
    seules = sorted(f for f in os.listdir(source)
                    if f.endswith('.html') and prefixe_seul(f) and retenu(f))
    if not fichiers and not seules:
        raise SystemExit('aucun fichier reconnu dans %s' % source)

    # Les pages déjà en ligne, pour les retrouver au lieu d'en créer des doubles.
    print('→ Relevé de la zone')
    Q = '/pages?parent=%d&per_page=100&status=any&context=edit&_fields=id,title,slug,parent'
    existantes = {}
    dossiers_en_ligne = {}
    existantes_mere = {}
    for d in dep.appel('GET', Q % MERE):
        dossiers_en_ligne[d['slug']] = d
        existantes_mere[d['slug']] = d
        for e in dep.appel('GET', Q % d['id']):
            existantes[e['slug']] = e
            for pt in dep.appel('GET', Q % e['id']):
                existantes[pt['slug']] = pt
    print('   %d dossier(s), %d page(s) déjà en ligne' % (len(dossiers_en_ligne), len(existantes)))

    print('\n→ Dossiers de type')
    dossiers = {}
    for _, rang, titre, slug in TYPES:
        if slug in dossiers:
            continue
        if a.essai:
            d = dossiers_en_ligne.get(slug)
            dossiers[slug] = d['id'] if d else 0
        else:
            d, action = dep.poser_page(slug, {'title': titre, 'status': 'draft',
                                              'parent': MERE, 'menu_order': rang})
            dossiers[slug] = d['id']
        print('   %-46s id %s' % (titre, dossiers[slug] or '—'))

    carte = carte_des_liens(existantes, existantes_mere)
    print('\n→ Liens de maquette')
    for fichier in sorted(LIENS):
        print('   %-24s → %s' % (fichier, carte[fichier][:62]))

    print('\n→ Pages')
    par_type = {}
    for f in fichiers:
        par_type.setdefault(type_de(f)[0], []).append(f)

    faits = rates = 0
    for prefixe in [t[0] for t in TYPES]:
        for rang, f in enumerate(par_type.get(prefixe, []), 1):
            base = f[:-len('.html')]
            slug = 'refonte-' + base
            _, _, _, slug_dossier = type_de(f)
            with open(os.path.join(source, f), encoding='utf-8') as fh:
                html = fh.read()
            contenu, morts = poser_liens(conv.convertir(html, source), carte)
            # Une page déjà en ligne ne reçoit que son contenu. Son titre, son
            # dossier et son rang sont l'œuvre de ranger-back-office.py : les
            # réécrire ici depuis le <title> du fichier déferait le rangement
            # à chaque déploiement.
            champs = {'status': 'draft', 'template': 'elementor_canvas',
                      'content': contenu}
            champs_neufs = dict(champs, title=titre_de_page(base, html),
                                parent=dossiers[slug_dossier], menu_order=rang)

            # WordPress tronque les slugs longs : on retrouve la page par
            # préfixe, en prenant le plus long slug existant qui commence
            # comme le nôtre — sinon on créerait un doublon à chaque passage.
            #
            # Mais le préfixe SEUL fait pire que le doublon : « guide-complet »
            # est un préfixe de « guide-complet-des-formalites-… », si bien que
            # deux fichiers différents visaient la même page — l'un écrasant
            # l'autre, et une troisième page restant sur une version périmée.
            # L'égalité stricte passe donc en premier, et le préfixe ne sert
            # que faute de mieux.
            #
            # On cherche aussi parmi les filles directes de la mère : jusqu'ici
            # l'accueil et la page agence y vivaient sans dossier, avec un slug
            # qui ne suit pas la règle — « refonte-accueil-version-artefact ».
            # Sans cette recherche, le passage au rangement par gabarit en
            # aurait créé des doubles au lieu de les déplacer.
            ou = dict(existantes_mere, **existantes)
            if slug in ou:
                page = ou[slug]
            else:
                candidats = [x for x in ou
                             if slug.startswith(x) or x.startswith(slug)
                             or x.startswith('refonte-' + prefixe.rstrip('-'))]
                page = ou[max(candidats, key=len)] if candidats else None

            attendu = len(re.findall(r'<img', contenu))
            if a.essai:
                print('   %-58s %s' % (f[:58],
                      ('→ #%d' % page['id']) if page else '→ à créer'))
                continue
            if page:
                # Le rangement par gabarit : on repose le dossier et le rang
                # à chaque passage, sinon une page déplacée à la main y
                # resterait. Le titre, lui, reste l'œuvre du rangement.
                champs = dict(champs, parent=dossiers[slug_dossier], menu_order=rang)
                # L'accueil garde la version choisie par Rémi : on la range,
                # on ne la réécrit pas.
                if prefixe in NE_PAS_REECRIRE:
                    champs.pop('content', None)
                    champs.pop('template', None)
                    dep.appel('POST', '/pages/%d' % page['id'], champs)
                    ok, attendu = True, 0
                else:
                    ok = ecrire(page['id'], champs, r'<img', attendu, 'images')
                pid = page['id']
            else:
                r = dep.appel('POST', '/pages', dict(champs_neufs, slug=slug))
                pid = r.get('id', 0)
                ok = bool(pid)
            (faits, rates) = (faits + 1, rates) if ok else (faits, rates + 1)
            print('   %-58s #%-6s %s  %d image(s), %d lien(s)'
                  % (f[:58], pid, 'ok' if ok else 'ÉCHEC', attendu, morts))

    # Les pages uniques : filles directes de la mère, à leur rang. Elles
    # n'ont pas de dossier — un dossier d'une seule page ne range rien.
    # Cette table existait sans jamais être lue : la page agence n'était
    # donc jamais redéployée, et gardait la version du jour où on l'avait
    # posée à la main.
    for f in seules:
        rang, titre = SEULES[prefixe_seul(f)]
        slug = 'refonte-' + f[:-len('.html')]
        with open(os.path.join(source, f), encoding='utf-8') as fh:
            html = fh.read()
        contenu, _ = poser_liens(conv.convertir(html, source), carte)
        attendu = len(re.findall(r'<img', contenu))
        candidats = ([slug] if slug in existantes_mere else
                     [x for x in existantes_mere if slug.startswith(x) or x.startswith(slug)])
        page = existantes_mere[max(candidats, key=len)] if candidats else None
        if a.essai:
            print('   %-58s %s' % (f[:58], ('→ #%d' % page['id']) if page else '→ à créer'))
            continue
        champs = {'status': 'draft', 'template': 'elementor_canvas', 'content': contenu}
        if page:
            ok, pid = ecrire(page['id'], champs, r'<img', attendu, 'images'), page['id']
        else:
            r = dep.appel('POST', '/pages', dict(champs, slug=slug, title=titre,
                                                 parent=MERE, menu_order=rang))
            pid = r.get('id', 0)
            ok = bool(pid)
        (faits, rates) = (faits + 1, rates) if ok else (faits, rates + 1)
        print('   %-58s #%-6s %s  %d image(s)'
              % (f[:58], pid, 'ok' if ok else 'ÉCHEC', attendu))

    print('\n%d page(s) déployée(s), %d échec(s). Rien n\'a été publié ni supprimé.'
          % (faits, rates))
    if rates:
        sys.exit(1)


if __name__ == '__main__':
    main()
