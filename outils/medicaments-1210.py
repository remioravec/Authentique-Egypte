#!/usr/bin/env python3
"""Voyager avec ses médicaments, dans le guide des vaccins (fil 10829).

    WP_AUTH='compte:mdp' python3 outils/medicaments-1210.py [--appliquer]

Mélanie : « ajouter les médicaments interdits et les médicaments à avoir avec
ordonnance ». Il n'existe pas de liste officielle publiée en français : le
ministère belge des Affaires étrangères (relayé par mesvaccins.net, mis à jour
le 26 novembre 2025) donne la règle, les autorités britanniques la même, et
le tramadol est le cas connu. La section donne la règle, l'exemple sûr, et la
démarche — sans inventer de liste.
"""
import argparse, os, re, requests

URL = 'https://authentiquegypte.com/wp-json/wp/v2/posts/5746'
SOURCE = 'https://www.mesvaccins.net/web/news/11965-voyages-en-egypte-et-medicaments'
TITRE = 'Voyager avec ses médicaments : ordonnance et produits interdits'
SECTION = (
    '<h2 id="s8b">%s</h2>'
    '<p>En Égypte, <b>certains médicaments vendus librement ou sur ordonnance en France sont classés comme '
    'stupéfiants</b>. Les faire entrer dans le pays demande une <b>autorisation préalable du ministère égyptien de la '
    'Santé</b> ; sans elle, le médicament peut être confisqué et le voyageur poursuivi. Le cas le plus connu est le '
    '<b>tramadol</b>, un antidouleur : ne l’emportez pas sans cette autorisation.</p>'
    '<p>Pour tout traitement personnel :</p><ul>'
    '<li>emportez l’<b>ordonnance</b>, et une <b>attestation de votre médecin</b> qui confirme que le médicament vous '
    'est prescrit ;</li>'
    '<li>gardez les médicaments dans leur <b>emballage d’origine</b>, en quantité adaptée à la durée du séjour ;</li>'
    '<li>en cas de doute sur un médicament (antidouleur, anxiolytique, somnifère, traitement à base de codéine ou de '
    'morphine), renseignez-vous avant le départ auprès de l’<b>ambassade d’Égypte</b> et de votre médecin.</li></ul>'
    '<p class="note">Source : ministère des Affaires étrangères de Belgique, relayé par '
    '<a href="%s" rel="noopener" target="_blank">mesvaccins.net</a>.</p>' % (TITRE, SOURCE))

a = argparse.ArgumentParser(); a.add_argument('--appliquer', action='store_true'); a = a.parse_args()
s = requests.Session(); s.verify = '/root/.ccr/ca-bundle.crt'; s.auth = tuple(os.environ['WP_AUTH'].split(':', 1))
h = s.get(URL, params={'context': 'edit'}, timeout=300).json()['content']['raw']
if 'id="s8b"' in h:
    raise SystemExit('Déjà fait.')
m = re.search(r'<h[23][^>]*id="s9"', h)
h = h[:m.start()] + SECTION + h[m.start():]
h = h.replace('<li><a href="#s9">', '<li><a href="#s8b">%s</a></li><li><a href="#s9">' % TITRE, 1)
print('section ajoutée avant « Mon conseiller santé », et dans le sommaire')
if a.appliquer:
    print('écrit :', s.post(URL, json={'content': h}, timeout=600).status_code)
