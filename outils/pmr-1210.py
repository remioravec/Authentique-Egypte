#!/usr/bin/env python3
"""Les questions sur le handicap, page Voyage PMR (fil 10446).

    WP_AUTH='compte:mdp' python3 outils/pmr-1210.py [--appliquer]

Mélanie, en septembre : « mettre plus de questions selon le handicap : est-ce
que le voyageur peut se lever, fauteuil roulant, machine respiratoire… ». On
attendait ses réponses. Elles sont, pour l'essentiel, déjà sur le site : le
guide « Voyager en Égypte en fauteuil roulant » dit ce que l'agence
organise (chambres et cabines PMR, véhicules à rampe sur demande,
accompagnant aidant en option, sites accessibles en partie). Les réponses
s'en tiennent à cela, et à une règle générale pour les appareils
respiratoires : on le signale, et l'accord se demande à la compagnie
aérienne. Rien n'est promis que le guide ne promette déjà.
"""
import argparse, importlib.util, os, re, requests

ICI = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('faqr', os.path.join(ICI, 'faq-reparee.py'))
FAQR = importlib.util.module_from_spec(spec); spec.loader.exec_module(FAQR)
URL = 'https://authentiquegypte.com/wp-json/wp/v2/pages/5095'
GUIDE = 'https://authentiquegypte.com/voyager-en-egypte-fauteuil-roulant/'

QUESTIONS = [
    ('Je ne peux pas me lever, ou très peu : le voyage est-il possible ?',
     '<p>Oui. Nous choisissons des <b>chambres et des cabines PMR</b>, avec rampe ou ascenseur et salle de bain '
     'adaptée, et un <b>véhicule équipé d’une rampe</b> sur demande, selon les disponibilités. Un accompagnant '
     'aidant peut vous assister pour les transferts. Dites-nous simplement si vous pouvez faire quelques pas : '
     'nous adaptons les visites en conséquence.</p>'),
    ('Fauteuil roulant manuel ou électrique : qu’est-ce que cela change ?',
     '<p>Précisez-le dans votre demande, avec les <b>dimensions et le poids du fauteuil</b> : le véhicule, '
     'l’hôtel et la cabine sont choisis en fonction. Certains sites ne sont accessibles qu’en partie (esplanade '
     'de Gizeh avec assistance, rampes à Louxor et à Karnak) ; le détail est dans <a href="%s">notre guide du '
     'voyage en fauteuil roulant</a>.</p>' % GUIDE),
    ('Je voyage avec un appareil respiratoire : comment l’organiser ?',
     '<p>Signalez-le <b>dès votre demande</b>. Nous vérifions avec chaque hôtel et chaque bateau l’accès à une '
     'prise près du lit, et nous adaptons les trajets. Pour le vol, l’autorisation de l’appareil se demande à '
     'la <b>compagnie aérienne</b>, avec votre médecin.</p>'),
    ('Un accompagnant peut-il m’aider au quotidien ?',
     '<p>Oui, en option : en plus du guide francophone, un <b>accompagnant aidant</b> peut vous assister pour les '
     'déplacements, les transferts et le quotidien.</p>'),
]

a = argparse.ArgumentParser(); a.add_argument('--appliquer', action='store_true'); a = a.parse_args()
s = requests.Session(); s.verify = '/root/.ccr/ca-bundle.crt'; s.auth = tuple(os.environ['WP_AUTH'].split(':', 1))
h = s.get(URL, params={'context': 'edit'}, timeout=300).json()['content']['raw']
if QUESTIONS[0][0] in h:
    raise SystemExit('Déjà fait.')
i = h.find('<div class="faq__rub">'); k = h.find('</p>', i) + 4
h = h[:k] + ''.join('<details class="faq__q"><summary>%s</summary><div class="faq__r">%s</div></details>' % q
                    for q in QUESTIONS) + h[k:]
h, info = FAQR.corriger(h)
print('FAQ PMR : %(questions)d questions, %(rubriques)s' % info)
if a.appliquer:
    print('écrit :', s.post(URL, json={'content': h}, timeout=600).status_code)
