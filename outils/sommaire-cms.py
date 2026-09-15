#!/usr/bin/env python3
"""
Construit le sommaire de la refonte et le pose dans le CMS, en brouillon.

    WP_AUTH='compte:mot de passe' ./outils/sommaire-cms.py [--sortie DIR] [--essai]

Le back-office de WordPress liste les pages à plat : passé une vingtaine de
brouillons, on ne retrouve plus rien. Ce script relève l'arbre réel sous
« Refonte 2026 » et en fait une page d'entrée — une par famille, chaque
séjour sous son circuit, avec pour chacune son identifiant, son poids, un
lien d'aperçu et un lien d'édition.

Rien n'est inventé : tout vient de l'API, à l'instant du relevé. La page
est posée en brouillon sous la mère, au rang 0 pour arriver en tête, et
n'est jamais publiée. Relancé, le script met à jour la même page.
"""

import argparse
import datetime
import html as H
import os
import re
import sys
import time
from importlib.machinery import SourceFileLoader

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dep = SourceFileLoader('dep', os.path.join(RACINE, 'outils', 'deployer.py')).load_module()
vers = SourceFileLoader('vers', os.path.join(RACINE, 'outils', 'vers-page-wp.py')).load_module()

MERE = 7642
SLUG = 'refonte-sommaire'
TITRE = 'Refonte · 0 · Sommaire — toutes les pages'
SITE = dep.SITE

MOIS = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet',
        'août', 'septembre', 'octobre', 'novembre', 'décembre']

# Ce que dit chaque dossier, en une ligne, sous son titre.
# Ce que dit chaque dossier, en une ligne, sous son titre. La clé est le
# SLUG du dossier, pas son rang : les rangs changent quand une famille
# s'ajoute, et une légende attachée à un rang finirait par décrire la
# mauvaise famille — c'est arrivé, « pages d'essai » s'est retrouvé sous
# les destinations le jour où elles ont pris le n° 3.
LEGENDES = {
    'refonte-types-de-s-jour': 'Les pages qui listent les séjours : la page mère et les cinq circuits.',
    'refonte-programmes': 'Les quatorze fiches séjour, groupées par circuit.',
    'refonte-destinations': 'Une page par lieu : ce qu’on y voit, quand y aller, combien de temps.',
    'refonte-profils': 'Les pages qui répondent à « je pars seul, en couple, en famille, en fauteuil ».',
    'refonte-guides': 'Les articles du blog et le sommaire qui les rassemble.',
    'refonte-institutionnel': 'L’accueil, l’agence, les mentions légales.',
    'refonte-maquettes-de-r-f-rence': 'Les pages d’essai qui ont servi à caler la charte et le gabarit.',
}


def titre_de(page):
    t = page['title']
    return t['raw'] if isinstance(t, dict) else t.get('rendered', '')


def poids(page):
    """Le poids du contenu stocké, en kilo-octets."""
    c = page.get('content', {})
    brut = c.get('raw') or c.get('rendered') or ''
    return max(1, round(len(brut.encode('utf-8')) / 1024))


Q = '/pages?parent=%d&per_page=100&status=any&context=edit&orderby=menu_order&order=asc'


def relever():
    """L'arbre sous « Refonte 2026 », tel qu'il est en ligne.

    Rend, par dossier, la liste de ses pages sous forme (groupe, page, nom).
    Un dossier peut contenir des sous-dossiers — c'est le cas des maquettes
    de référence, rangées par type : Home, Circuits, Programmes. Le groupe
    est alors le nom du sous-dossier, et non plus un morceau du titre de la
    page, puisque c'est justement le dossier qui porte le type.
    """
    dossiers = []
    for d in dep.appel('GET', Q % MERE):
        entrees = []
        for e in dep.appel('GET', Q % d['id']):
            petits = dep.appel('GET', Q % e['id'])
            if petits:
                for p in petits:
                    entrees.append((nom_dossier(titre_de(e)), p, nom_page(titre_de(p))))
            else:
                groupe, nom = groupe_de(titre_de(e))
                entrees.append((groupe, e, nom))
        if entrees:              # pas une page posée seule sous la mère
            dossiers.append((d, entrees))
    return dossiers


def nom_dossier(titre):
    """Le nom d'un sous-dossier, sans les préfixes de rangement."""
    t = re.sub(r'^Refonte\s*·\s*', '', titre)
    t = re.sub(r'^R[ée]f\s*·\s*', '', t)
    return re.sub(r'^\d+\s*·\s*', '', t).strip()


def nom_page(titre):
    """Le nom d'une page rangée dans un sous-dossier : le dossier dit déjà
    de quel type elle est, le titre n'a plus à le répéter."""
    t = re.sub(r'^Refonte\s*·\s*(?:R[ée]f\s*·\s*)?', '', titre)
    return re.sub(r'\s*—\s*doublon\s+/\S*$', '', t).strip()


def numero(titre):
    """Le rang que porte le titre du dossier : « Refonte · 2 · … » → 2."""
    m = re.search(r'·\s*(\d+)\s*·', titre)
    return int(m.group(1)) if m else 9


def nom_court(titre):
    """Le titre sans son préfixe de rangement."""
    t = re.sub(r'^Refonte\s*·\s*\d+\s*·\s*', '', titre)
    return re.sub(r'^Refonte\s*·\s*', '', t)


def groupe_de(titre):
    """Le groupe d'une page et son nom, lus dans le titre posé par le rangement.

    Trois formes coexistent sous « Refonte 2026 », et une seule des trois
    porte un groupe qui vaille un intertitre :

        Refonte · Circuits · 3 · Mer rouge      → pas de groupe, « Mer rouge »
        Refonte · Réf · Accueil · HOME          → groupe « Accueil »
        Refonte · Sinaï · Mont Moïse            → groupe « Sinaï »

    La marque « — doublon /slug » que le rangement ajoute aux deux fiches
    sœurs est retirée ici : c'est une annotation, pas une part du nom, et
    la garder empêcherait justement de reconnaître les deux sœurs.
    """
    nu = re.sub(r'^Refonte\s*·\s*', '', titre)
    nu = re.sub(r'\s*—\s*doublon\s+/\S*$', '', nu).strip()

    plat = re.match(r'^[^·]+·\s*\d+\s*·\s*(.+)$', nu)
    if plat:                                   # les circuits, déjà numérotés
        return '', plat.group(1).strip()

    reference = re.match(r'^R[ée]f\s*·\s*([^·]+?)\s*·\s*(.+)$', nu)
    if reference:
        return reference.group(1).strip(), reference.group(2).strip()

    sejour = re.match(r'^([^·]+?)\s*·\s*(.+)$', nu)
    return (sejour.group(1).strip(), sejour.group(2).strip()) if sejour else ('', nu)


def e(x):
    return H.escape(str(x), quote=True)


def ligne(page, nom, doublon=False):
    i = page['id']
    marque = '<em>doublon</em>' if doublon else ''
    return (
        '<li class="page">'
        '<span class="page__nom">%s%s</span>'
        '<span class="page__meta"><code>#%d</code><span>%d ko</span></span>'
        '<span class="page__act">'
        '<a class="b b--v" href="%s/?page_id=%d" target="_blank" rel="noopener">Aperçu</a>'
        '<a class="b" href="%s/wp-admin/post.php?post=%d&amp;action=edit" target="_blank" rel="noopener">Modifier</a>'
        '</span></li>' % (e(nom), marque, i, poids(page), SITE, i, SITE, i)
    )


def corps(dossiers):
    total = sum(len(k) for _, k in dossiers)
    aujourdhui = datetime.date.today()

    out = []
    out.append('<header class="tete">')
    out.append('<p class="eyebrow">Authentique Égypte · WordPress</p>')
    out.append('<h1>Refonte 2026, rangée et cliquable</h1>')
    out.append('<p class="chapo">Les %d pages de la refonte, toutes en brouillon sous '
               '« Refonte 2026 », rangées par type dans l’ordre où on les parcourt : '
               'les circuits, les séjours, les destinations, les profils de voyageur, '
               'les guides, les pages institutionnelles. Aucune page publiée n’est '
               'touchée.</p>' % total)
    # Le compteur se lit sur les dossiers réellement présents : figé sur trois
    # familles, il annonçait « 9 références » le jour où le rang 3 est passé
    # aux destinations.
    out.append('<p class="chiffres">%s<b>0 <span>publiée</span></b></p>' % ''.join(
        '<b>%d <span>%s</span></b>' % (len(k), e(nom_court(titre_de(d)).split(' —')[0].lower()))
        for d, k in dossiers))
    out.append('<p class="avis">Les deux liens demandent d’être connecté au back-office. '
               '<b>Aperçu</b> ouvre la page telle que la verra le visiteur, '
               '<b>Modifier</b> ouvre l’éditeur.</p>')
    out.append('</header>')

    for d, enfants in dossiers:
        n = numero(titre_de(d))
        out.append('<section class="dossier"><div class="dossier__tete">'
                   '<span class="num">%d</span><h2>%s</h2>'
                   '<span class="cpt">%d page%s</span></div>'
                   % (n, e(nom_court(titre_de(d))), len(enfants),
                      's' if len(enfants) > 1 else ''))
        if d['slug'] in LEGENDES:
            out.append('<p class="legende">%s</p>' % e(LEGENDES[d['slug']]))
        out.append('<ol class="pages">')

        # Deux fiches peuvent porter le même nom : ce sont les pages en
        # double relevées par le contrôle qualité. Dans une liste elles
        # seraient indiscernables, on ajoute leur adresse.
        vus = {}
        for _, p, nom in enfants:
            vus.setdefault(nom, []).append(p['id'])
        doubles = {i for ids in vus.values() if len(ids) > 1 for i in ids}

        groupe = None
        for g, p, nom in enfants:
            if g and g != groupe:
                out.append('<li class="groupe"><span>%s</span></li>' % e(g))
                groupe = g
            if p['id'] in doubles:
                nom += ' · /%s' % re.sub(r'^refonte-(?:programme|famille)-', '', p['slug'])
            out.append(ligne(p, nom, p['id'] in doubles))
        out.append('</ol></section>')

    out.append('<footer class="pied">')
    out.append('<p><b>Ce qui reste à trancher avec Mélanie :</b> les durées annoncées qui '
               'ne collent pas au nombre de jours écrits, les trois fiches dont '
               'l’itinéraire n’existe pas dans le contenu d’origine, et le choix de la '
               'page à garder entre les deux Sainte-Catherine, marquées « doublon ».</p>')
    out.append('<p>Relevé sur le CMS le %d %s %d. La taille indiquée est celle du '
               'contenu stocké.</p>' % (aujourdhui.day, MOIS[aujourdhui.month - 1],
                                        aujourdhui.year))
    out.append('</footer>')
    return '\n'.join(out)


STYLE = """
:root{--bleu:#079DB6;--bleu-fond:#E3F3F8;--bleu-nuit:#0A5E70;--or:#FBB50E;--or-fond:#FDF0D6;
 --papier:#FFFFFF;--fond:#F4F7F9;--noir:#0E1519;--texte:#3D4A51;--gris:#6B7A82;
 --ligne:#DFE7EB;--rouge:#B4402A;--rouge-fond:#FBEBE6}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--papier:#121A1E;--fond:#0B1114;
 --noir:#EAF1F4;--texte:#C3CFD5;--gris:#8FA0A8;--ligne:#222F35;--bleu-fond:#0D3038;--or-fond:#33280C;--rouge-fond:#331A14}}
:root[data-theme="dark"]{--papier:#121A1E;--fond:#0B1114;--noir:#EAF1F4;--texte:#C3CFD5;--gris:#8FA0A8;
 --ligne:#222F35;--bleu-fond:#0D3038;--or-fond:#33280C;--rouge-fond:#331A14}
*,*::before,*::after{box-sizing:border-box}
body{margin:0;background:var(--fond);color:var(--texte);font-family:"Archivo",system-ui,-apple-system,sans-serif;font-size:16px;line-height:1.6}
.wrap{width:min(100% - 32px,1060px);margin-inline:auto;padding-block:clamp(28px,5vw,56px)}
a{color:inherit}
header.tete{display:grid;gap:14px;margin:0 0 clamp(26px,4vw,44px)}
.eyebrow{margin:0;font-family:"Manrope",sans-serif;font-size:.76rem;font-weight:800;letter-spacing:.16em;text-transform:uppercase;color:var(--bleu)}
h1{margin:0;font-size:clamp(1.7rem,3.4vw,2.5rem);font-weight:700;letter-spacing:-1px;line-height:1.12;color:var(--noir);text-wrap:balance}
.chapo{margin:0;max-width:70ch;font-size:1.04rem}
.chiffres{display:flex;flex-wrap:wrap;gap:10px;margin:4px 0 0;font-family:"Manrope",sans-serif}
.chiffres b{display:inline-flex;align-items:baseline;gap:7px;background:var(--papier);border:1px solid var(--ligne);
 border-top:3px solid var(--bleu);border-radius:10px;padding:9px 14px;font-size:1.25rem;font-weight:700;color:var(--noir)}
.chiffres b span{font-size:.76rem;font-weight:700;letter-spacing:.09em;text-transform:uppercase;color:var(--gris)}
.avis{margin:0;padding:12px 16px;border-left:3px solid var(--or);background:var(--or-fond);color:#7A5605;
 border-radius:0 8px 8px 0;font-family:"Manrope",sans-serif;font-size:.94rem;line-height:1.5}
.dossier{margin:0 0 clamp(26px,4vw,40px)}
.dossier__tete{display:flex;align-items:center;gap:12px;padding:0 0 10px;border-bottom:2px solid var(--bleu)}
.dossier__tete h2{margin:0;font-size:clamp(1.12rem,2vw,1.35rem);font-weight:700;letter-spacing:-.4px;color:var(--noir);flex:1}
.num{width:30px;height:30px;flex:0 0 auto;border-radius:50%;background:var(--bleu);color:#fff;display:grid;place-items:center;
 font-family:"Manrope",sans-serif;font-weight:800;font-size:.92rem}
.cpt{font-family:"Manrope",sans-serif;font-size:.76rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--gris);white-space:nowrap}
.legende{margin:10px 0 0;font-size:.94rem;color:var(--gris);max-width:68ch}
ol.pages{list-style:none;margin:6px 0 0;padding:0}
li.groupe{margin:18px 0 6px;font-family:"Manrope",sans-serif;font-size:.74rem;font-weight:800;letter-spacing:.12em;text-transform:uppercase;color:var(--bleu)}
li.groupe span{display:inline-block;padding:0 0 3px;border-bottom:2px solid var(--bleu-fond)}
li.page{display:flex;flex-wrap:wrap;align-items:center;gap:8px 14px;padding:11px 2px;border-bottom:1px solid var(--ligne)}
li.page:last-child{border-bottom:0}
.page__nom{flex:1 1 320px;min-width:0;font-size:1rem;color:var(--noir);font-weight:500}
.page__nom em{display:inline-block;margin-left:8px;font-style:normal;font-family:"Manrope",sans-serif;font-size:.7rem;font-weight:800;
 letter-spacing:.08em;text-transform:uppercase;background:var(--rouge-fond);color:var(--rouge);padding:2px 8px;border-radius:999px}
.page__meta{display:inline-flex;align-items:baseline;gap:10px;font-family:"Manrope",sans-serif;font-size:.8rem;color:var(--gris)}
.page__meta code{font-family:"Manrope",sans-serif;font-weight:700;color:var(--bleu)}
.page__act{display:inline-flex;gap:8px}
.b{display:inline-flex;align-items:center;justify-content:center;min-height:40px;padding:0 16px;border-radius:999px;
 border:1px solid var(--ligne);background:var(--papier);text-decoration:none;font-family:"Manrope",sans-serif;
 font-size:.84rem;font-weight:700;color:var(--noir);white-space:nowrap}
.b:hover{border-color:var(--bleu);color:var(--bleu)}
.b--v{background:var(--bleu);border-color:var(--bleu);color:#fff}
.b--v:hover{background:var(--bleu-nuit);border-color:var(--bleu-nuit);color:#fff}
.b:focus-visible{outline:3px solid var(--or);outline-offset:2px}
footer.pied{margin:clamp(30px,5vw,50px) 0 0;padding:18px 0 0;border-top:1px solid var(--ligne);font-size:.94rem;color:var(--gris);display:grid;gap:10px}
footer.pied b{color:var(--noir)}
@media (max-width:640px){.page__act{width:100%}.b{flex:1}.page__meta{order:3}}
"""

TETE = (
    '<title>Refonte 2026 · Back-office</title>\n'
    '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
    '<link href="https://fonts.googleapis.com/css2?family=Archivo:wght@400;500;600;700'
    '&family=Manrope:wght@500;600;700;800&display=swap" rel="stylesheet">\n'
)


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--sortie', help='dossier où écrire aussi la page en local')
    p.add_argument('--essai', action='store_true', help='construire sans rien poser')
    a = p.parse_args()

    dossiers = relever()
    if not dossiers:
        raise SystemExit('aucun dossier sous « Refonte 2026 »')

    page = TETE + '<style>' + STYLE + '</style>\n<body>\n<div class="wrap">\n' \
        + corps(dossiers) + '\n</div>\n</body>'

    for d, enfants in dossiers:
        print('   %-46s %2d page(s)' % (nom_court(titre_de(d))[:46], len(enfants)))

    if a.sortie:
        os.makedirs(a.sortie, exist_ok=True)
        chemin = os.path.join(a.sortie, 'index.html')
        with open(chemin, 'w', encoding='utf-8') as f:
            f.write(page)
        print('\n→ écrit %s (%d octets)' % (chemin, len(page.encode('utf-8'))))

    if a.essai:
        print('\nEssai : rien n’a été posé sur le CMS.')
        return

    contenu = vers.convertir(page)
    attendu = len(re.findall(r'\?page_id=\d+', contenu))
    champs = {'title': TITRE, 'parent': MERE, 'menu_order': 0, 'status': 'draft',
              'template': 'elementor_canvas', 'content': contenu}

    # L'écriture est relue. Le serveur rend parfois une réponse vide : sans
    # ce contrôle le script annonçait « mise à jour » alors que la page en
    # ligne n'avait pas bougé, et l'écart ne se voyait qu'à l'œil.
    for essai in range(4):
        try:
            reponse, action = dep.poser_page(SLUG, champs)
        except SystemExit as motif:
            print('   reprise %d/3 — %s' % (essai + 1, str(motif).splitlines()[0]))
            time.sleep(2 ** essai)
            continue
        relu = dep.appel('GET', '/pages/%d?context=edit' % reponse['id'])
        if len(re.findall(r'\?page_id=\d+', relu['content']['raw'])) == attendu:
            print('\n→ Sommaire %s : #%d  %s/?page_id=%d  (%d aperçus relus)'
                  % (action, reponse['id'], SITE, reponse['id'], attendu))
            return
        print('   reprise %d/3 — la page en ligne ne porte pas les %d aperçus'
              % (essai + 1, attendu))
        time.sleep(2 ** essai)
    raise SystemExit('le sommaire n’a pas pu être écrit sur le CMS')


if __name__ == '__main__':
    main()
