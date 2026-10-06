#!/usr/bin/env python3
"""« L'agence » reprise sur les dix remarques de Mélanie.

    WP_AUTH='compte:mdp' python3 outils/agence-refaite.py --essai
    WP_AUTH='compte:mdp' python3 outils/agence-refaite.py --appliquer
    WP_AUTH='compte:mdp' python3 outils/agence-refaite.py --mettre-en-ligne

Rémi a fait remettre l'ancienne version de /qui-sommes-nous/ en ligne le
4 octobre. En relisant le brouillon, on comprend pourquoi : six
« à remplir » y étaient encore visibles, la partie « Comment ça se passe »
s'arrêtait à la deuxième étape sur cinq, et deux mentions de chantier
(« Source : la page d'accueil du site ») traînaient dans le corps du texte.

Mélanie a laissé dix remarques sur ce brouillon. Elles sont toutes traitées
ici, et elles disent exactement ce qui manquait :

  12333 la note Google → 4,9 sur 5, 24 avis, le chiffre relevé et vérifié
  12336 « pourquoi mettre la source ? » → les deux mentions retirées
  12337 « ajouter une catégorie : testés et approuvés » → sa carte, ses mots
  12338 la galerie « En images » → retirée
  12340 « ajouter image » sur Hend → aucune photo de l'équipe dans la
        médiathèque. Les deux cartes reçoivent un monogramme, et la photo
        prendra sa place le jour où l'agence en fournit une.
  12342 « refaire cette partie totalement » → Notre histoire, réécrite
  12343 « il manque la prise de contact, envoi devis, modification,
        validation, préparation pré-voyage » → les cinq étapes, dans l'ordre
  12344 « la même forme que les autres faq du site » → le bloc faqu du site
  12345 le bouton de devis → un vrai bouton vers /sur-mesure/
  12346 « les commentaires comme sur les autres pages » → le mur d'avis des
        pages de destination, avec les liens Google et TripAdvisor

Au passage : Marie Claire et TripAdvisor étaient dans la presse de l'ancienne
page et avaient disparu du brouillon ; les six références redeviennent des
liens. Et le « Confiez l'organisation… » générique cède la place au texte que
porte déjà l'accueil.

--mettre-en-ligne bascule ensuite /qui-sommes-nous/ sur ce contenu, après
sauvegarde de ce qui s'y trouve.
"""

import argparse
import base64
import datetime
import json
import os
import re
import time

import requests

SITE = 'https://authentiquegypte.com'
RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAUVE = os.path.join(RACINE, 'sauvegarde', 'avant-mise-en-ligne')
BROUILLON = 9126
CIBLE = 105
MODELE_AVIS = 5229          # /voyage-a-fayoum/, d'où l'on clone le mur d'avis

# ----------------------------------------------------------------- 12342
HISTOIRE = '''<section class="pg-sec pg-sec--fond"><div class="wrap">\
<p class="eyebrow">Notre histoire</p><h2>D’un premier voyage à une \
équipe au Caire</h2><div class="duo rev"><div class="duo__t">\
<p class="">Mélanie vivait en Inde quand elle est venue en Égypte \
pour la première fois. Elle y est retournée, puis elle y est \
restée.</p>\
<p class="">En 2019, plutôt que de monter une structure seule, elle \
commence à organiser des séjours avec une agence égyptienne du \
Caire. Les guides, les chauffeurs et les maisons d’hôtes étaient \
déjà là&nbsp;: ce sont eux qui font le voyage.</p>\
<p class="">La société française est enregistrée en 2024, \
pour que les voyageurs aient un interlocuteur de ce côté-ci de la \
Méditerranée et un contrat de droit français. Depuis le \
début, 3 493 voyageurs sont passés par nous.</p>\
<p class="">Ce qui n’a pas changé depuis 2019&nbsp;: chaque \
itinéraire se construit au cas par cas, avec les mêmes partenaires \
locaux, et personne ne part sans savoir qui l’attend à \
l’aéroport.</p>\
</div><figure class="duo__i"><img src="https://authentiquegypte.com/wp-content\
/uploads/2025/07/DSC00551_01-scaled-e1751464241518-1024x683.jpg" \
alt="Lever du soleil au sommet du mont Moïse" width="1024" height="683" \
loading="lazy" decoding="async"><figcaption>Lever du soleil au sommet du mont \
Moïse</figcaption></figure></div></div></section>'''

# ----------------------------------------------------------------- 12337
TESTES = ('<div class="atout"><h3>Testés et approuvés</h3><p>Nous '
          'visitons les hébergements avant de les proposer, et nous '
          'travaillons avec des guides et des chauffeurs que nous connaissons. '
          'Rien n’entre dans un itinéraire sans être passé '
          'par là.</p></div>')

# ----------------------------------------------------------------- 12343
ETAPES = [
    ('Prise de contact',
     'Vous nous écrivez ce que vous avez en tête. Un expert local '
     'vous répond sous 48 h, hors vendredi et samedi.'),
    ('Envoi du devis',
     'Un itinéraire écrit, jour par jour, avec les hébergements, '
     'les transferts et le prix par personne. Gratuit et sans engagement.'),
    ('Modifications',
     'Vous dites ce qui ne va pas : une étape de trop, un rythme '
     'trop soutenu, un budget à ajuster. On reprend autant de fois '
     'qu’il le faut.'),
    ('Validation',
     'Quand l’itinéraire vous convient, nous réservons : '
     'hébergements, transferts, vols intérieurs, guides.'),
    ('Préparation avant le départ',
     'Vous recevez un guide de voyage détaillé, avec les '
     'informations pratiques et vos contacts sur place. Un représentant '
     'local reste joignable 24 h/24 pendant le séjour.'),
]

# ----------------------------------------------------------------- presse
PRESSE = [
    ('Le Figaro', 'Voyage en famille en Égypte',
     'https://www.lefigaro.fr/economie/voyage-en-famille-en-egypte-l-expertise'
     '-d-une-agence-locale-20240726'),
    ('Partir.com', 'Fiche agence Authentique Égypte',
     'https://www.partir.com/agence-voyage/authentique-egypte/'),
    ('Le Figaro Madame', 'Adresses Incontournables',
     'https://adresses-incontournables.madame.lefigaro.fr/besoin-evasion/'
     'authentique-egypte/'),
    ('Evaneos', 'Profil agence Égypte',
     'https://www.evaneos.fr/egypte/voyage/agences/69152-melanie/'),
    ('Marie Claire', 'Adresses Incontournables',
     'https://www.marieclaire.fr/adresses-incontournables/authentique-egypte/'),
    ('TripAdvisor', 'Avis voyageurs',
     'https://www.tripadvisor.fr/Attraction_Review-g294201-d15316887-Reviews-'
     'Authentique_Egypte-Cairo_Cairo_Governorate.html'),
]

# ----------------------------------------------------------------- 12329
LEDE = ('Nos agents vivent en Égypte&nbsp;: ce sont eux qui réservent '
        'l’hôtel à Gizeh, le bateau à Assouan et le guide '
        'à Sainte-Catherine, et qui restent joignables pendant votre '
        'séjour. C’est ce qui permet d’ajuster une étape en '
        'cours de route.')

STYLE = (
    '<style id="agence-css">'
    '.pg .etapes{list-style:none;margin:26px 0 0;padding:0;display:grid;'
    'gap:12px;counter-reset:et;max-width:840px}'
    '.pg .etapes li{counter-increment:et;display:grid;'
    'grid-template-columns:auto 1fr;gap:4px 16px;align-items:baseline;'
    'padding:16px 20px;background:#fff;border:1px solid var(--ligne,#E4E4EA);'
    'border-radius:var(--r-m,14px)}'
    '.pg .etapes li::before{content:counter(et);grid-row:span 2;'
    'display:grid;place-items:center;width:30px;height:30px;border-radius:50%;'
    'background:var(--teal-fond,#BEE6F1);color:var(--nuit-900,#094D60);'
    'font-weight:700;font-size:.9rem}'
    '.pg .etapes b{font-size:1.02rem;color:var(--nuit-900,#094D60)}'
    '.pg .etapes span{font-size:.98rem;line-height:1.7;'
    'color:var(--texte,#5D5D5D)}'
    '.pg .pers{display:grid;grid-template-columns:auto 1fr;gap:4px 16px;'
    'align-items:start}'
    '.pg .pers__m{grid-row:span 3;display:grid;place-items:center;width:52px;'
    'height:52px;border-radius:50%;background:var(--teal-fond,#BEE6F1);'
    'color:var(--nuit-900,#094D60);font-family:"Archivo",system-ui,sans-serif;'
    'font-weight:700;font-size:1.25rem}'
    '.pg .presse a{text-decoration:none;color:inherit;display:block;height:100%}'
    '.pg .presse a:hover h3{text-decoration:underline}'
    '.pg .duo__i img,.pg figure img{max-width:100%;height:auto;display:block}'
    '.pg .duo{display:grid;gap:24px;align-items:start}'
    '@media (min-width:860px){.pg .duo{grid-template-columns:1fr 1fr}}'
    '@media (max-width:560px){.pg .etapes li{grid-template-columns:1fr}'
    '.pg .etapes li::before{grid-row:auto}}'
    '</style>')


def section_brute(h, deb, fin, bornes=False):
    i = h.find(deb)
    if i < 0:
        return None
    k = h.find(fin, i)
    if k < 0:
        return None
    k += len(fin)
    return (i, k) if bornes else h[i:k]


def section(h, repere):
    """(début, fin) de la section qui contient ce repère."""
    i = h.find(repere)
    if i < 0:
        return None
    d = h.rfind('<section', 0, i)
    f = h.find('</section>', i)
    if d < 0 or f < 0:
        return None
    return d, f + len('</section>')


def remplacer(h, repere, neuf, j, cle):
    b = section(h, repere)
    if not b:
        return h
    j[cle] = j.get(cle, 0) + 1
    return h[:b[0]] + neuf + h[b[1]:]


def corriger(h, mur):
    j = {}

    # chantier et mentions de source (12336)
    h, n = re.subn(r'<p class="atelier">(?:(?!</p>).)*?</p>\s*', '', h, flags=re.S)
    j['12336 à remplir retirés'] = n
    h, n = re.subn(r'<p class="prov">(?:(?!</p>).)*?</p>\s*', '', h, flags=re.S)
    j['12336 sources retirées'] = n

    # la note, vérifiée (12333)
    h, n = re.subn(r'<b>23 <span>avis Google</span></b>',
                   '<b>4,9/5 <span>sur 24 avis Google</span></b>', h)
    j['12333 note'] = n

    # la quatrième approche (12337)
    b = section(h, 'Ce qui fait un voyage avec nous')
    if b:
        seg = h[b[0]:b[1]]
        if 'Testés et approuvés' not in seg:
            k = seg.rfind('</div></div></div></section>')
            if k < 0:
                k = seg.rfind('</div>', 0, seg.rfind('</div></div></section>'))
            seg = seg.replace('</div><p class="prov"', '</div><p class="prov"')
            k = seg.rfind('</div></div></div>')
            seg = seg[:k] + TESTES + seg[k:]
            h = h[:b[0]] + seg + h[b[1]:]
            j['12337 testés et approuvés'] = 1

    # la galerie (12338)
    b = section(h, 'Nos voyages en photos')
    if b:
        h = h[:b[0]] + h[b[1]:]
        j['12338 galerie retirée'] = 1

    # l'histoire (12342)
    h = remplacer(h, 'Une aventure née', HISTOIRE, j, '12342 histoire réécrite')

    # les cinq étapes (12343)
    etapes = ''.join('<li><b>%s</b><span>%s</span></li>' % (t, d)
                     for t, d in ETAPES)
    bloc = ('<section class="pg-sec"><div class="wrap">'
            '<p class="eyebrow">Comment ça se passe</p>'
            '<h2>De votre premier message au départ</h2>'
            '<ol class="etapes rev">' + etapes + '</ol></div></section>')
    h = remplacer(h, 'De votre premier message au départ', bloc, j,
                  '12343 cinq étapes')

    # « Vit entre Le Caire et l'Égypte » ne veut rien dire
    h, n = re.subn(
        r'Vit entre Le Caire et l(?:&#x27;|’)\u00c9gypte, et adore',
        'Install\u00e9e au Caire, elle adore', h)
    j['équipe : phrase corrigée'] = n

    # les monogrammes de l'équipe (12340)
    def monogramme(m):
        return ('<article class="pers"><span class="pers__m" aria-hidden="true">'
                '%s</span><h3>%s</h3>' % (m.group(1)[0], m.group(1)))

    h, n = re.subn(r'<article class="pers"><h3>([^<]+)</h3>', monogramme, h)
    j['12340 monogrammes'] = n

    # la FAQ au format du site (12344), le bouton (12345) et le générique
    b = section(h, 'Les questions qu’on nous pose')
    if b:
        seg = h[b[0]:b[1]]
        qr = re.findall(r'<h3 class="mef-q">(.*?)</h3>\s*<p class="">(.*?)</p>',
                        seg, re.S)
        if qr:
            faq = ''.join(
                '<details class="faq__q"><summary>%s</summary>'
                '<div class="faq__r"><p>%s</p></div></details>' % (q, r)
                for q, r in qr)
            neuf = ('<section class="pg-sec pg-sec--fond"><div class="wrap">'
                    '<p class="eyebrow">Avant de nous écrire</p>'
                    '<h2 id="t-faq">Les questions qu’on nous pose</h2>'
                    '<div class="faqu">' + faq + '</div></div></section>'
                    '<section class="pg-sec"><div class="wrap">'
                    '<h2>Voyagez autrement avec une agence qui vous met en '
                    'lien avec des acteurs locaux en Égypte.</h2>'
                    '<p class="lede">' + LEDE + '</p>'
                    '<p><a class="btn btn--or" href="' + SITE + '/sur-mesure/">'
                    'Demander mon devis</a></p></div></section>')
            h = h[:b[0]] + neuf + h[b[1]:]
            j['12344 FAQ au format du site'] = len(qr)
            j['12345 bouton de devis'] = 1

    # la presse, six références et des liens
    b = section(h, 'La presse et les plateformes')
    if b:
        cartes = ''.join(
            '<div class="atout"><a href="%s" target="_blank" rel="noopener">'
            '<h3>%s</h3><p>%s</p></a></div>' % (u, n2, s)
            for n2, s, u in PRESSE)
        neuf = ('<section class="pg-sec"><div class="wrap">'
                '<p class="eyebrow">Ils parlent de nous</p>'
                '<h2>La presse et les plateformes</h2>'
                '<div class="atouts atouts--presse presse rev">' + cartes
                + '</div></div></section>')
        h = h[:b[0]] + neuf + h[b[1]:]
        j['presse : six références, en liens'] = len(PRESSE)

    # le mur d'avis des autres pages (12346)
    b = section(h, 'aria-labelledby="t-avis"')
    if b and mur:
        h = h[:b[0]] + mur + h[b[1]:]
        j['12346 mur d avis cloné'] = 1

    # 12263 · la carte bancaire, retirée partout ailleurs
    h, n = re.subn(r'<small>Aucune carte bancaire(?:(?!</small>).)*?</small>',
                   '', h, flags=re.S)
    j['12263 carte bancaire'] = n

    # les feuilles de style qui manquent à ce gabarit
    if 'id="agence-css"' not in h:
        i = h.find('<main')
        h = h[:i] + STYLE + h[i:]
        j['feuille de style'] = 1

    return h, {k: v for k, v in j.items() if v}


def main():
    p = argparse.ArgumentParser()
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument('--essai', action='store_true')
    g.add_argument('--appliquer', action='store_true')
    g.add_argument('--mettre-en-ligne', action='store_true')
    a = p.parse_args()

    S = requests.Session(); S.verify = '/root/.ccr/ca-bundle.crt'
    u, m = os.environ['WP_AUTH'].split(':', 1)
    S.headers['Authorization'] = 'Basic ' + base64.b64encode(
        ('%s:%s' % (u, m)).encode()).decode()
    B = SITE + '/wp-json/wp/v2/pages/'

    def lire(pid):
        for essai in range(5):
            r = S.get(B + str(pid), params={'context': 'edit'}, timeout=240)
            if r.status_code < 300:
                return r.json()
            time.sleep(2 ** essai)
        raise SystemExit('lecture refusée sur %d' % pid)

    def ecrire(pid, charge):
        for essai in range(4):
            r = S.post(B + str(pid), json=charge, timeout=600)
            if r.status_code < 300:
                return
            time.sleep(2 ** essai)
        raise SystemExit('écriture refusée sur %d' % pid)

    # le mur d'avis d'une page de destination, et ses feuilles
    modele = (lire(MODELE_AVIS).get('content') or {}).get('raw', '')
    bm = section(modele, 'aria-labelledby="t-avis"')
    mur = modele[bm[0]:bm[1]] if bm else ''
    styles = ''.join(x.group(0) for x in re.finditer(
        r'<style data-(?:faq="unique"|avis="1")>.*?</style>', modele, re.S))
    print('mur d\'avis cloné : %d caractères · feuilles : %d caractères'
          % (len(mur), len(styles)))

    # l'en-tête et le pied doivent être ceux de toutes les autres pages
    be = section_brute(modele, '<header class="entete"', '</header>')
    bp = section_brute(modele, '<footer class="pied"', '</footer>')

    h = (lire(BROUILLON).get('content') or {}).get('raw', '')
    neuf, j = corriger(h, mur)
    for deb, fin, bloc, nom in (('<header class="entete"', '</header>', be,
                                 'en-tête'),
                                ('<footer class="pied"', '</footer>', bp,
                                 'pied')):
        b = section_brute(neuf, deb, fin, bornes=True)
        if b and bloc:
            if neuf[b[0]:b[1]] != bloc:
                neuf = neuf[:b[0]] + bloc + neuf[b[1]:]
                j['%s aligné sur les autres pages' % nom] = 1
    if styles and 'data-faq="unique"' not in neuf:
        i = neuf.find('<main')
        neuf = neuf[:i] + styles + neuf[i:]
        j['feuilles du site'] = 1
    print('%d → %d caractères' % (len(h), len(neuf)))
    for k, v in sorted(j.items()):
        print('   %-36s %d' % (k, v))
    # on compte les éléments, pas les règles de style qui les décrivent
    for mot, att in (('class="aremplir"', 0), ('class="prov"', 0),
                     ('Confiez l', 0), ('Aucune carte bancaire', 0),
                     ('<h1', 1), ('class="faqu"', 1),
                     ('<div class="mur__liens">', 1),
                     ('<section', 13)):
        vu = neuf.count(mot)
        print('   %-36s %d (attendu %d)%s'
              % (mot, vu, att, '' if vu == att else '   ← écart'))

    if a.essai:
        open('/tmp/claude-0/agence-essai.html', 'w').write(neuf)
        return

    ecrire(BROUILLON, {'content': '<!-- wp:html -->\n' + neuf
                       + '\n<!-- /wp:html -->'})
    print('brouillon %d écrit.' % BROUILLON)

    if not a.mettre_en_ligne:
        return

    v = lire(CIBLE)
    jour = datetime.date.today().isoformat()
    d = os.path.join(SAUVE, jour)
    os.makedirs(d, exist_ok=True)
    f = os.path.join(d, 'pages-%d.json' % CIBLE)
    json.dump({'contenu': v['content']['raw'],
               'modele': v.get('template') or '',
               'titre': v['title']['raw'], 'slug': v['slug'],
               'meta': {k: str(x)[:200] for k, x in (v.get('meta') or {}).items()}},
              open(f, 'w'), ensure_ascii=False, indent=1)
    print('sauvegardé : %s' % os.path.relpath(f, RACINE))

    ecrire(CIBLE, {'content': '<!-- wp:html -->\n' + neuf + '\n<!-- /wp:html -->',
                   'template': 'elementor_canvas'})
    ecrire(CIBLE, {'meta': {'_elementor_edit_mode': ''}})
    vu = lire(CIBLE)
    print('en ligne · gabarit %s · _elementor_edit_mode=%r'
          % (vu.get('template'), (vu.get('meta') or {}).get('_elementor_edit_mode')))
    time.sleep(3)
    r = S.get(SITE + '/qui-sommes-nous/', timeout=180)
    t = r.text
    print('/qui-sommes-nous/ %d · %d en-tête · %d pied · %d h1 · %d faqu · '
          '%d liens d avis' % (r.status_code, t.count('<header class="entete"'),
                               t.count('<footer class="pied"'),
                               len(re.findall(r'<h1[\s>]', t)),
                               t.count('class="faqu"'), t.count('mur__lien ')))


if __name__ == '__main__':
    main()
