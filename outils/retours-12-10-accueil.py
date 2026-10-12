#!/usr/bin/env python3
"""L'accueil, sur les commentaires de Mélanie du 12 octobre.

    WP_AUTH='compte:mdp' python3 outils/retours-12-10-accueil.py --essai
    WP_AUTH='compte:mdp' python3 outils/retours-12-10-accueil.py --appliquer

  12936 « un fond transparent pour voir l'image, ou réduire » — le bloc
        « Composez votre Égypte » devient translucide et plus compact.
  12937 « une autre carte ? les écritures sont pixelisées » — la carte
        Leaflet et ses tuiles laissent la place à une carte dessinée (SVG,
        outils/carte-egypte-svg.py) : nette sur tous les écrans, chaque
        destination reste un lien.
  12938 « changer le texte » — « Six des régions que nous faisons
        découvrir » : la carte en montre neuf.
  12941 « enlever les tirets » — dans le texte du haut.
  12997, 12998 « enlever » — le titre « Quatre étapes, et vous n'avancez
        jamais à l'aveugle » et « Vous ne payez rien tant que… » : la
        section garde son nom, « Comment ça se passe ».

12939 (51 jours), 12940 (la FAQ en relecture) et 12999 (les boutons
d'avis) valent pour tout le site : outils/retours-12-10-global.py.
"""

import argparse
import os
import subprocess
import sys
import time

import requests

ICI = os.path.dirname(os.path.abspath(__file__))
URL = 'https://authentiquegypte.com/wp-json/wp/v2/pages/38'

STYLE = (
    '<style data-retours="12-10-accueil">'
    '.elementor-template-canvas .compo.compo{background:rgba(255,255,255,.78);'
    '-webkit-backdrop-filter:blur(8px);backdrop-filter:blur(8px);padding:22px 26px 20px}'
    '.elementor-template-canvas .compo.compo .compo__t{margin:0 0 16px}'
    '.carte-eg__svg{display:block;width:100%;height:auto;border-radius:18px;border:1px solid var(--ligne,#E4E4EA)}'
    '.ce-mer{fill:#D6EDF2}.ce-voisin{fill:#F4F1EA;stroke:#D9D2C3;stroke-width:1}'
    '.ce-egypte{fill:#F3E3BF;stroke:#C9A15A;stroke-width:1.6}'
    '.ce-eau{fill:#8CCBDA;stroke:#5AA9BE;stroke-width:.8}'
    '.ce-nil{fill:none;stroke:#3C9CB6;stroke-width:2.4;stroke-linecap:round;stroke-linejoin:round}'
    '.ce-mer-t{fill:#4E8FA3;font:italic 15px "Manrope",sans-serif;letter-spacing:.06em;text-anchor:middle}'
    '.ce-pays{fill:#9A9182;font:13px "Manrope",sans-serif;letter-spacing:.12em;text-transform:uppercase;text-anchor:middle}'
    '.ce-egypte-t{fill:#B98C3D;font:700 22px "Manrope",sans-serif;letter-spacing:.4em;text-anchor:middle;opacity:.55}'
    '.ce-lieu circle{fill:#094D60;stroke:#fff;stroke-width:3;transition:fill .2s}'
    '.ce-lieu text{fill:#094D60;font:700 15px "Manrope",sans-serif;paint-order:stroke;stroke:#fff;stroke-width:4px;stroke-linejoin:round}'
    '.ce-lieu:hover circle,.ce-lieu:focus circle{fill:#ECAA24}'
    '.ce-lieu:hover text,.ce-lieu:focus text{text-decoration:underline}'
    '.ce-lieu:focus{outline:none}.ce-lieu:focus-visible circle{stroke:#ECAA24;stroke-width:5}'
    '@media (max-width:640px){.ce-lieu text{font-size:24px;stroke-width:6px}.ce-lieu circle{r:10}'
    '.ce-mer-t{font-size:22px}.ce-pays{font-size:19px}.ce-egypte-t{font-size:30px}}'
    '.carte-eg figcaption{text-align:right;font-size:11px;opacity:.5;margin:8px 0 0}'
    '</style>')


def remplacer(h, avant, apres, quoi, journal):
    if avant not in h:
        raise SystemExit('Introuvable : ' + quoi)
    journal.append(quoi)
    return h.replace(avant, apres, 1)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--essai', action='store_true')
    p.add_argument('--appliquer', action='store_true')
    p.add_argument('--natural-earth', default='/tmp/claude-0/ne')
    a = p.parse_args()

    s = requests.Session()
    s.verify = '/root/.ccr/ca-bundle.crt'
    s.auth = tuple(os.environ['WP_AUTH'].split(':', 1))
    h = s.get(URL, params={'context': 'edit'}, timeout=300).json()['content']['raw']
    if 'data-retours="12-10-accueil"' in h:
        print('Déjà fait.')
        return
    j = []

    h = remplacer(h, 'fait les réservations — hébergements, transferts, vols internes — et reste joignable sur place.',
                  'fait les réservations (hébergements, transferts, vols internes) et reste joignable sur place.',
                  '12941 tirets retirés', j)
    h = remplacer(h, 'Six des régions que nous faisons découvrir', 'Neuf destinations, d’Alexandrie au lac Nasser',
                  '12938 titre de la carte', j)

    svg = subprocess.run([sys.executable, '-I', os.path.join(ICI, 'carte-egypte-svg.py'), a.natural_earth],
                         capture_output=True, text=True, check=True).stdout
    lien = '<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.css">'
    d = h.find(lien + '<figure class="carte-eg">')
    f = h.find('</script>', h.find('<script id="carte-eg-js">', d)) + len('</script>')
    if d < 0 or f < len('</script>'):
        raise SystemExit('Carte introuvable')
    h = (h[:d] + '<figure class="carte-eg">' + svg +
         '<figcaption>Fond de carte : Natural Earth</figcaption></figure>' + h[f:])
    j.append('12937 carte dessinée à la place des tuiles')

    h = remplacer(h, '<p class="eyebrow">Comment ça se passe</p><h2 style="margin-bottom:16px">Quatre étapes, et vous '
                     'n\'avancez jamais à l\'aveugle</h2><p class="lede" style="margin-bottom:44px">Vous ne payez rien '
                     'tant que l\'itinéraire ne vous convient pas.</p>',
                  '<h2 style="margin-bottom:40px">Comment ça se passe</h2>',
                  '12997, 12998 titre et sous-titre retirés', j)

    i = h.find('<main')
    i = h.find('>', i) + 1
    h = h[:i] + STYLE + h[i:]
    j.append('12936 composeur translucide et plus compact')

    for x in j:
        print('  ' + x)
    if a.appliquer:
        for essai in range(4):
            try:
                r = s.post(URL, json={'content': h}, timeout=600)
                print('écrit :', r.status_code)
                break
            except requests.RequestException:
                time.sleep(2 ** essai)


if __name__ == '__main__':
    main()
