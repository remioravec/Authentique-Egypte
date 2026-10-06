#!/usr/bin/env python3
"""La FAQ mal refermée des quatre pages de profil.

    WP_AUTH='compte:mdp' python3 outils/retours-07-faq-nichee.py --essai
    WP_AUTH='compte:mdp' python3 outils/retours-07-faq-nichee.py --appliquer

Sur /voyage-en-famille-en-egypte/, /voyage-en-couple-en-egypte/,
/voyage-solo-en-egypte/ et /voyage-pmr-en-egypte/, une question de la FAQ
n'était pas refermée : son </details> manquait, remplacé par un </div> de
trop. Conséquence visible : tout ce qui suivait — la rubrique « Bon à savoir »
et ses questions — se retrouvait enfermé dans l'accordéon replié de la
question précédente. Personne ne pouvait les lire sans ouvrir « Y a-t-il des
activités adaptées aux adolescents ? ».

C'est mon propre rangement de la FAQ (retours-06-faq.py) qui a laissé ça :
le repérage du bloc comptait les <div> sans vérifier qu'il tombait sur le bon.

La réparation ne touche aucun texte. On relit la section de FAQ balise par
balise avec une pile : les fermetures qui ne correspondent à rien sont
retirées, les ouvertures restées en l'air sont refermées dans l'ordre, juste
avant la fin de la section. Le texte, lui, est recopié tel quel — et on le
vérifie caractère par caractère avant d'écrire.
"""

import argparse
import base64
import os
import re
import time

import requests

SITE = 'https://authentiquegypte.com'
CIBLES = (5035, 5044, 5052, 5095)
BALISES = r'<(section|div|details|article)(?:\s[^>]*)?>|</(section|div|details|article)>'


def non_apparies(h):
    """(fermetures orphelines, ouvertures restées ouvertes) dans le corps."""
    a = h.find('<main')
    b = h.find('</main>', a)
    if b < 0:
        b = len(h)
    pile, orphelines = [], []
    for m in re.finditer(BALISES, h[a:b]):
        if m.group(0).startswith('</'):
            if pile and pile[-1][0] == m.group(2):
                pile.pop()
            else:
                orphelines.append((m.start() + a, m.group(0)))
        else:
            pile.append((m.group(1), m.start() + a))
    return orphelines, pile


def section_faq(h):
    """(début, fin) de la section de FAQ, fin au </section> qui la referme.

    La structure interne est justement cassée : on ne peut pas se fier à une
    profondeur. On repère donc la fin par ce qui suit — la section suivante,
    un commentaire de gabarit, ou la fin du main.
    """
    i = h.find('id="t-faq"')
    if i < 0:
        return None
    d = h.rfind('<section', 0, i)
    if d < 0:
        return None
    for suite in ('</section><section', '</section><!--', '</section></main>',
                  '</section>'):
        k = h.find(suite, i)
        if k > 0:
            return d, k
    return None


def refermer(bloc):
    """Recopie le bloc en retirant les fermetures orphelines, et rend la pile."""
    out, pile, pos = [], [], 0
    for m in re.finditer(BALISES, bloc):
        out.append(bloc[pos:m.start()])
        pos = m.end()
        if m.group(0).startswith('</'):
            t = m.group(2)
            if pile and pile[-1] == t:
                pile.pop()
                out.append(m.group(0))
            else:
                pass  # fermeture orpheline : on la laisse tomber
        else:
            pile.append(m.group(1))
            out.append(m.group(0))
    out.append(bloc[pos:])
    return ''.join(out), pile


def corriger(h):
    bornes = section_faq(h)
    if not bornes:
        return h, 'section de FAQ introuvable'
    d, f = bornes
    bloc = h[d:f]
    neuf, pile = refermer(bloc)
    if neuf == bloc and not pile[1:]:
        return h, 'rien à refermer'
    # la section elle-même reste ouverte : le </section> qui suit la referme
    reste = pile[1:]
    neuf = neuf + ''.join('</%s>' % t for t in reversed(reste))
    texte = lambda s: re.sub(r'<[^>]+>', '', s)
    if texte(neuf) != texte(bloc):
        return h, 'le texte aurait changé — on ne touche à rien'
    return h[:d] + neuf + h[f:], '%d fermeture(s) retirée(s), %d ajoutée(s)' % (
        len(re.findall(BALISES, bloc)) - len(re.findall(BALISES, neuf))
        + len(reste), len(reste))


def main():
    p = argparse.ArgumentParser()
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument('--essai', action='store_true')
    g.add_argument('--appliquer', action='store_true')
    a = p.parse_args()

    S = requests.Session(); S.verify = '/root/.ccr/ca-bundle.crt'
    u, m = os.environ['WP_AUTH'].split(':', 1)
    S.headers['Authorization'] = 'Basic ' + base64.b64encode(
        ('%s:%s' % (u, m)).encode()).decode()
    B = SITE + '/wp-json/wp/v2/pages/'

    a_ecrire = []
    for i in CIBLES:
        d = S.get(B + str(i), params={'context': 'edit'}, timeout=180).json()
        h = (d.get('content') or {}).get('raw', '')
        av_o, av_p = non_apparies(h)
        neuf, mot = corriger(h)
        ap_o, ap_p = non_apparies(neuf)
        print('%-5d %-44s avant %d orphelines / %d ouvertes → après %d / %d'
              % (i, mot, len(av_o), len(av_p), len(ap_o), len(ap_p)))
        if neuf == h:
            continue
        if len(ap_o) > len(av_o) or len(ap_p) > len(av_p):
            raise SystemExit('la page %d serait moins bien refermée' % i)
        a_ecrire.append((i, neuf))

    print('\n%d page(s) à écrire' % len(a_ecrire))
    if a.essai:
        return
    for i, neuf in a_ecrire:
        for essai in range(4):
            r = S.post(B + str(i), json={
                'content': '<!-- wp:html -->\n' + neuf + '\n<!-- /wp:html -->'},
                timeout=300)
            if r.status_code < 300:
                break
            time.sleep(2 ** essai)
        else:
            raise SystemExit('écriture refusée sur %d' % i)
        print('%-5d écrite' % i)


if __name__ == '__main__':
    main()
