#!/usr/bin/env python3
"""Rend docs/backlog.json en tableau lisible dans docs/backlog.md."""

import json
import os

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ETATS = {
    'fait': '✅ Fait',
    'en_cours': '🔵 En cours',
    'a_arbitrer': '🟠 À arbitrer',
    'a_produire': '⬜ À produire',
    'a_fournir': '🟡 En attente cliente',
}
PORTEURS = {'remi': 'Rémi', 'cliente': 'Mélanie', 'partage': 'les deux'}
LOTS = {
    'process': 'Process et non-régression',
    'design': 'Design',
    'fonctionnel': 'Fonctionnel',
    'contenu': 'Contenu',
    'photos': 'Photos',
    'back-office': 'Back-office',
    'dette': 'Dette relevée de notre côté',
}


def main():
    donnees = json.load(open(os.path.join(RACINE, 'docs', 'backlog.json'), encoding='utf-8'))
    tickets = donnees['tickets']

    lignes = ['# Backlog de la refonte', '']
    lignes.append('> Source : %s' % donnees['source'])
    lignes.append('> Mise à jour : %s — généré depuis `docs/backlog.json` par '
                  '`outils/backlog-md.py`, ne pas éditer à la main.' % donnees['maj'])
    lignes.append('')

    compte = {}
    for t in tickets:
        compte[t['etat']] = compte.get(t['etat'], 0) + 1
    lignes.append('| État | Nombre |')
    lignes.append('|---|---:|')
    for cle, libelle in ETATS.items():
        if compte.get(cle):
            lignes.append('| %s | %d |' % (libelle, compte[cle]))
    lignes.append('| **Total** | **%d** |' % len(tickets))
    lignes.append('')

    for lot, titre in LOTS.items():
        du_lot = [t for t in tickets if t['lot'] == lot]
        if not du_lot:
            continue
        lignes.append('## %s' % titre)
        lignes.append('')
        for t in du_lot:
            lignes.append('### %s — %s' % (t['id'], t['titre']))
            lignes.append('')
            lignes.append('**%s** · porteur : %s' % (ETATS[t['etat']], PORTEURS[t['porteur']]))
            lignes.append('')
            lignes.append('*Demande :* %s' % t['demande'])
            lignes.append('')
            lignes.append('*Où on en est :* %s' % t['reponse'])
            lignes.append('')

    chemin = os.path.join(RACINE, 'docs', 'backlog.md')
    with open(chemin, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lignes))
    print('docs/backlog.md — %d tickets' % len(tickets))


if __name__ == '__main__':
    main()
