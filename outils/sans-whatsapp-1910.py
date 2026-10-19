#!/usr/bin/env python3
"""Plus aucun bouton WhatsApp : les demandes passent par le formulaire (Mélanie, 19 octobre).

    WP_AUTH='compte:mdp' python3 outils/sans-whatsapp-1910.py --essai
    WP_AUTH='compte:mdp' python3 outils/sans-whatsapp-1910.py --appliquer

Décidé au point du 15 octobre (notes Gemini) : « Supprimer les boutons
WhatsApp et ajouter des formulaires par email pour clarifier la gestion des
demandes voyageurs ». Les demandes arrivaient sur le WhatsApp personnel de
Mélanie, sans trace ni mesure. Le 19 octobre : « je reçois toujours les
demandes via WhatsApp, pouvez-vous le corriger au plus vite ? »

Sur chaque page (les 61 de outils/cibles.py, plus le programme « Le Caire,
Rosette et canal de Suez » publié par Mélanie le 15 octobre) :
  - « WhatsApp +20 106 661 9098 », dans le bandeau du haut et le pied de
    page, devient « Formulaire de demande », vers /sur-mesure/#formulaire ;
  - dans la FAQ des pages de catégorie, « Contactez-nous directement sur
    WhatsApp » devient « … par le formulaire de demande » ;
  - les boutons « Poser une question / Nous écrire sur WhatsApp », le lien
    « Une question ? WhatsApp » du panneau de devis et le bouton WhatsApp de
    la barre mobile sont retirés : chacun était le second bouton, à côté
    d'un bouton qui mène déjà au formulaire.
Les liens « Partager sur WhatsApp » (wa.me/?text=…) restent : ils servent à
envoyer la page à un proche, pas à écrire à l'agence.

Et surtout le formulaire « Recevoir mon devis » des pages de séjour : un
script l'interceptait pour ouvrir WhatsApp avec un message prérempli à
Mélanie (« Bonjour Mélanie, je souhaite un devis pour… »). C'est lui qui
envoyait les demandes sur son téléphone. Le script est retiré : le
formulaire part vers /sur-mesure/#formulaire, où WPForms reçoit la demande
préremplie (outils/relais-devis.py) et l'envoie par e-mail.

La bulle flottante vient de l'extension Chaty, réglée sur ce seul numéro
WhatsApp : elle est désactivée (pas supprimée ; réactivable dans Extensions).

Chaque contenu est sauvegardé avant écriture dans
sauvegarde/avant-mise-en-ligne/<date>/sans-whatsapp/.
"""

import argparse
import collections
import datetime
import importlib.util
import json
import os
import re
import time

import requests

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(ICI)
spec = importlib.util.spec_from_file_location('cibles', os.path.join(ICI, 'cibles.py'))
CIBLES = importlib.util.module_from_spec(spec)
spec.loader.exec_module(CIBLES)
SITE = CIBLES.SITE
FORMULAIRE = SITE + '/sur-mesure/#formulaire'
EN_PLUS = [('programs', 13538, SITE + '/programs/le-caire-rosette-et-canal-de-suez/')]
CHATY = 'chaty/cht-icons'

LIEN = re.compile(r'<a\b[^>]*href="https://wa\.me/201066619098[^"]*"[^>]*>(.*?)</a>', re.S)


def nettoyer(h, compte):
    def un(m):
        texte = re.sub(r'<[^>]+>', '', m.group(1)).strip()
        if texte.startswith('WhatsApp +20'):
            compte['coordonnées → formulaire'] += 1
            return '<a href="%s">Formulaire de demande</a>' % FORMULAIRE
        compte['bouton retiré : ' + (texte or '(icône)')] += 1
        return ''
    h = LIEN.sub(un, h)
    # LE formulaire dont parle Mélanie : « Recevoir mon devis », sur chaque séjour. Un script
    # l'interceptait et ouvrait WhatsApp avec un message prérempli. Sans lui, le formulaire part
    # vers /sur-mesure/ (champs nommés par relais-devis.py, qui préremplit WPForms) : envoi par e-mail.
    h, n = re.subn(r"  // Devis : le formulaire compose un message WhatsApp.*?\}\);\}\n(?=  // Copier le lien)", '', h,
                   flags=re.S)
    if n:
        compte['devis du séjour : interception WhatsApp retirée'] += n
    h, n = re.subn(r'(<form class="pan__form" action="https://authentiquegypte\.com/sur-mesure/)(")', r'\1#formulaire\2', h)
    if n:
        compte['devis du séjour : arrivée sur le formulaire'] += n
    # la phrase de FAQ des pages de catégorie : « Contactez-nous directement sur WhatsApp pour… »
    h, n = re.subn(r'sur <strong>WhatsApp</strong>', 'par le <a href="%s">formulaire de demande</a>' % FORMULAIRE, h)
    if n:
        compte['FAQ : « sur WhatsApp » → formulaire'] += n
    return h


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--essai', action='store_true')
    p.add_argument('--appliquer', action='store_true')
    a = p.parse_args()
    s = requests.Session()
    s.verify = '/root/.ccr/ca-bundle.crt'
    s.auth = tuple(os.environ['WP_AUTH'].split(':', 1))
    dos = os.path.join(RACINE, 'sauvegarde', 'avant-mise-en-ligne', datetime.date.today().isoformat(), 'sans-whatsapp')

    cibles = [(c['type'], c['cible'], c['url']) for c in CIBLES.toutes()] + EN_PLUS
    total = {}
    restes = []
    for typ, pid, url in cibles:
        api = '%s/wp-json/wp/v2/%s/%d' % (SITE, typ, pid)
        d = s.get(api, params={'context': 'edit'}, timeout=300).json()
        if 'content' not in d:
            print('  ? %s %d illisible' % (typ, pid))
            continue
        h = d['content']['raw']
        compte = collections.Counter()
        h2 = nettoyer(h, compte)
        # ce qui parle encore de WhatsApp une fois les liens traités
        visible = re.sub(r'<(style|script)\b.*?</\1>', '', h2, flags=re.S)
        sans_partage = re.sub(r'<a\b[^>]*wa\.me/\?text[^>]*>.*?</a>', '', visible, flags=re.S)
        for m in re.finditer(r'>([^<]*WhatsApp[^<]*)<', sans_partage):
            restes.append((url.replace(SITE, ''), m.group(1).strip()))
        if not compte:
            continue
        for k, v in compte.items():
            total[k] = total.get(k, 0) + v
        print('%-8s %-6d %-58s %s' % (typ, pid, url.replace(SITE, ''), sum(compte.values())))
        if a.appliquer:
            os.makedirs(dos, exist_ok=True)
            json.dump({'type': typ, 'id': pid, 'contenu': h}, open(os.path.join(dos, '%s-%d.json' % (typ, pid)), 'w'),
                      ensure_ascii=False)
            for essai in range(4):
                try:
                    r = s.post(api, json={'content': h2}, timeout=600)
                    print('         écrit :', r.status_code)
                    break
                except requests.RequestException:
                    time.sleep(2 ** essai)
    print()
    for k, v in sorted(total.items(), key=lambda x: -x[1]):
        print('%4d  %s' % (v, k))
    if restes:
        print('\nMentions de WhatsApp restantes (texte, pas des liens) :')
        for u, t in restes:
            print('  %-50s %s' % (u, t))

    etat = s.get('%s/wp-json/wp/v2/plugins/%s' % (SITE, CHATY), timeout=120).json().get('status')
    print('\nChaty :', etat)
    if a.appliquer and etat == 'active':
        r = s.post('%s/wp-json/wp/v2/plugins/%s' % (SITE, CHATY), json={'status': 'inactive'}, timeout=120)
        print('Chaty désactivée :', r.status_code, r.json().get('status'))


if __name__ == '__main__':
    main()
