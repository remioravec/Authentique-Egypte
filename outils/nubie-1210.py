#!/usr/bin/env python3
"""« Découverte de la Nubie » passe au nouveau gabarit (13122).

    WP_AUTH='compte:mdp' python3 outils/nubie-1210.py --essai [--vers fichier.html]
    WP_AUTH='compte:mdp' python3 outils/nubie-1210.py --appliquer

Mélanie, le 12 octobre, sur la page en ligne : « la page complète du
programme n'est pas à jour, pouvez-vous la mettre à jour, et je vous
donnerai les commentaires ». C'était la seule page de séjour restée dans
l'ancienne maquette Elementor.

Elle avait été écartée de la bascule du 2 octobre parce que son brouillon
(8583) n'a pas de jour par jour, et que celui de la page en ligne décrit un
autre voyage — dix journées entre Le Caire, Louxor, Edfou et Kom Ombo, sans
Assouan ni Nubie (docs/arbitrages-contenu.md). Mélanie demande justement à
voir la page au nouveau format pour corriger ce déroulé : on le reprend tel
qu'il est en ligne, mis en forme, pour qu'elle le commente journée par
journée.

Sur le brouillon, elle avait aussi laissé (12969-12983) :
  prix → 1 190 € (13123, sur la page en ligne, après 1 290 € sur le
  brouillon le même matin) ; voile trop prononcé ; « il manque la
  description de la Nubie » ; la ligne « Devis gratuit… » ; « le texte
  n'est pas comme sur les autres pages » ; « où est le jour par jour ? » ;
  six photos de la galerie à enlever ; les avis « pas au même format que
  sur les autres programmes ».

Le brouillon datait d'avant les retouches communes : il reçoit les feuilles
d'une page de séjour à jour, le mur d'avis des autres programmes, la FAQ
repliée, puis les corrections du 12 octobre communes à tous les séjours.
La bascule suit la procédure du 2 octobre : sauvegarde, gabarit
elementor_canvas, Elementor réduit au silence.
"""

import argparse
import datetime
import html as H
import importlib.util
import json
import os
import re
import sys
import time

import requests

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(ICI)
sys.path.insert(0, ICI)
import jours as J  # noqa: E402


def charger(nom, f):
    spec = importlib.util.spec_from_file_location(nom, os.path.join(ICI, f))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


SEJ = charger('sej1210', 'retours-12-10-sejours.py')
PRIX = charger('prix1210', 'prix-durees-1210.py')
GLOB = charger('glob1210', 'retours-12-10-global.py')
BASC = charger('bascule', 'deux-destinations.py')

SITE = 'https://authentiquegypte.com'
B = SITE + '/wp-json/wp/v2/'
CIBLE, BROUILLON, MODELE = 1337, 8583, 1168

CHAPO = ('Au sud d’Assouan, la Nubie déroule ses villages aux maisons peintes de couleurs vives, le long du Nil et '
         'du lac Nasser. On y rencontre les habitants, on y goûte la cuisine nubienne, et l’on y découvre les temples '
         'd’Abou Simbel et de Philae.')


def jours_anciens(vieux):
    """Les dix journées de la page Elementor, telles qu'elles sont."""
    out = []
    morceaux = re.split(r'<!-- Jour \d+ -->', vieux)[1:]
    for m in morceaux:
        t = re.search(r'Jour \d+ : ([^\n<]+)', m)
        img = re.search(r'<img src="([^"]+)"\s+alt="([^"]*)"', m)
        ps = [H.unescape(re.sub(r'<[^>]+>', '', p)).strip() for p in re.findall(r'<p>(.*?)</p>', m, re.S)]
        ps = [p for p in ps if p]
        titre = t.group(1).strip() if t else ''
        if ps and ps[0] == titre:
            ps = ps[1:]
        texte = ' '.join(ps).lower()
        pas = []
        if 'nuit à bord' in texte or 'croisière' in texte and 'bateau' in texte:
            pas.append('Bateau')
        elif 'nuit à l' in texte or 'hôtel' in texte:
            pas.append('Hôtel')
        if 'petit-déjeuner' in texte:
            pas.append('Petit-déjeuner')
        if re.search(r'déjeuner(?! libre)', texte.replace('petit-déjeuner', '')):
            pas.append('Déjeuner')
        if re.search(r'dîner(?! libre)', texte):
            pas.append('Dîner')
        out.append((titre, img.group(1) if img else None, img.group(2) if img else '', ps, pas))
    return out


def section_jours(jj):
    nav = ''.join('<li><span class="jpjs__n">J%d</span><a href="#jour-%d">%s</a></li>' % (n, n, H.escape(t))
                  for n, (t, *_r) in enumerate(jj, 1))
    corps = []
    for n, (t, img, alt, ps, pas) in enumerate(jj, 1):
        photo = ''
        if img:
            photo = ('<a class="etape__photo" data-lb href="%s" data-alt="%s" aria-label="Agrandir la photo : %s">'
                     '<img src="%s" alt="%s" decoding="async" loading="lazy"></a>' % (img, H.escape(alt), H.escape(alt),
                                                                                       img, H.escape(alt)))
        corps.append('<div class="jour" id="jour-%d"><div class="jour__tete"><h3>%s</h3><span class="jour__no">Jour %d'
                     '</span></div><article class="etape" id="etape-%d" data-lieu="">%s<ul class="etape__pts">%s</ul>'
                     '%s</article></div>'
                     % (n, H.escape(t), n, n, photo, ''.join('<li>%s</li>' % H.escape(p) for p in ps),
                        '<p class="jico">%s</p>' % ''.join(J.pastille(x) for x in pas) if pas else ''))
    return ('<section><p class="eyebrow">Dans le détail</p><h2 id="t-jpj">Le séjour jour par jour</h2>'
            '<nav class="jpjs" aria-label="Les étapes du séjour"><div class="jpjs__t"><p>Les étapes</p></div>'
            '<ol class="jpjs__l">%s</ol></nav>%s</section>' % (nav, ''.join(corps)))


def preparer(S, journal):
    def lire(chemin):
        for essai in range(5):
            r = S.get(B + chemin, params={'context': 'edit'}, timeout=300)
            if r.status_code < 300:
                return r.json()
            time.sleep(2 ** essai)
        raise SystemExit('lecture refusée : ' + chemin)

    brouillon = lire('pages/%d' % BROUILLON)['content']['raw']
    vieux = lire('programs/%d' % CIBLE)
    modele = lire('programs/%d' % MODELE)['content']['raw']

    man = json.load(open(os.path.join(BASC.SAUVE, '2026-10-02', 'MANIFESTE.json')))
    vers = {c['brouillon']: c['url'] for c in man['couples']}
    h, manquants = BASC.liens(BASC.nettoyer(BASC.nu(brouillon)), vers)
    if manquants:
        journal.append('liens ?page_id non réécrits : %s' % sorted(manquants))

    # les feuilles d'une page de séjour à jour qui manquent au brouillon
    ici = {m.group(1) for m in re.finditer(r'<style([^>]*)>', h)}
    ajout = ''.join(m.group(0) for m in re.finditer(r'<style([^>]*)>.*?</style>', modele, re.S)
                    if m.group(1) and m.group(1) not in ici and '12-10' not in m.group(1))
    i = h.find('<main')
    i = h.find('>', i) + 1
    h = h[:i] + ajout + h[i:]
    journal.append('feuilles d’une page de séjour à jour : %d' % ajout.count('<style'))

    # le chapô : la Nubie
    h, k = re.subn(r'<p class="hero__chapo">.*?</p>', '<p class="hero__chapo">%s</p>' % CHAPO, h, count=1, flags=re.S)
    if not k:
        h = h.replace('</h1>', '</h1><p class="hero__chapo">%s</p>' % CHAPO, 1)
    journal.append('description de la Nubie (12971)')
    # le paragraphe de présentation, au format des autres pages (12975)
    h = re.sub(r'(<h2 id="t-vue">Vue d&#x27;ensemble</h2><div class="prose">)<p>', r'\1<p class="prose__tete">', h,
               count=1)
    # six photos de trop (12977-12982)
    h = SEJ.galerie_retirer(h, {7, 8, 9, 10, 11, 12}, journal)
    h = re.sub(r'<span class="galerie__plus">[^<]*</span>', '', h)
    # le jour par jour (12976), repris de la page en ligne
    jj = jours_anciens(vieux['content']['raw'])
    a, b = J.bornes(h, '<section class="galerie"', 'section')
    h = h[:b] + section_jours(jj) + h[b:]
    journal.append('jour par jour : %d journées reprises de la page en ligne' % len(jj))
    # les avis au format des autres programmes (12983)
    m = re.search(r'<section class="pg-sec" aria-labelledby="t-avis">.*?</section>', modele, re.S)
    a = h.find('<section class="pg-sec" aria-labelledby="t-avis">')
    if m and a >= 0:
        h = h[:a] + m.group(0) + h[h.find('</section>', a) + len('</section>'):]
        journal.append('mur d’avis des autres programmes')
    # la FAQ repliée comme ailleurs
    h = SEJ.faq_replier(h, journal)
    # les corrections du 12 octobre communes aux séjours et au site
    h = SEJ.communs(h, journal)
    h, _ = GLOB.corriger(h)
    h, n = PRIX.page_du_sejour(h, 'decouverte-de-la-nubie')
    h = h.replace('<li>895 € / Personne</li>', '<li>À partir de 1 190 € par personne</li>')
    journal.append('prix 1 190 € (%d emplacements)' % n)
    return h, vieux


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--essai', action='store_true')
    p.add_argument('--appliquer', action='store_true')
    p.add_argument('--vers')
    a = p.parse_args()
    S = requests.Session()
    S.verify = '/root/.ccr/ca-bundle.crt'
    S.auth = tuple(os.environ['WP_AUTH'].split(':', 1))
    journal = SEJ.Journal()
    h, vieux = preparer(S, journal)
    for x in journal:
        print('  ' + x)
    for marque, n in (('<main', 1), ('<header class="entete"', 1), ('<footer class="pied"', 1), ('<h1', 1)):
        if h.count(marque) != n:
            raise SystemExit('%d × %s, attendu %d' % (h.count(marque), marque, n))
    if a.vers:
        open(a.vers, 'w', encoding='utf-8').write(h)
    if not a.appliquer:
        return
    d = os.path.join(BASC.SAUVE, datetime.date.today().isoformat())
    os.makedirs(d, exist_ok=True)
    f = os.path.join(d, 'programs-%d.json' % CIBLE)
    json.dump({'contenu': vieux['content']['raw'], 'modele': vieux.get('template') or '',
               'titre': vieux['title']['raw'], 'slug': vieux['slug']}, open(f, 'w'), ensure_ascii=False, indent=1)
    print('sauvegardé :', os.path.relpath(f, RACINE))
    r = S.post(B + 'programs/%d' % CIBLE, json={'content': '<!-- wp:html -->\n' + h + '\n<!-- /wp:html -->',
                                                'template': BASC.CANVAS}, timeout=600)
    print('écrit :', r.status_code)
    print('Elementor :', S.post(B + 'programs/%d' % CIBLE, json={'meta': {BASC.CLE: ''}}, timeout=180).status_code)


if __name__ == '__main__':
    main()
