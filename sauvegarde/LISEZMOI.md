# Sauvegarde avant mise en ligne

`avant-mise-en-ligne/<date>.tar.gz` est l'état du site **avant** que la
refonte ne remplace le contenu des pages en ligne. Une archive par
bascule. Décompresser avec `tar xzf <date>.tar.gz`.

## Ce qu'elle contient

- `<type>-<id>.json` — les 57 contenus en ligne visés par la bascule.
  Pour chacun : le contenu brut, le gabarit, le titre, le slug, la page
  mère, le statut, l'image à la une, l'ordre de menu, les méta Yoast,
  les méta du thème, et l'enregistrement entier rendu par l'API en
  contexte d'édition. De quoi remettre la page exactement en l'état.
- `brouillons/<id>.json` — les 57 pages de refonte telles qu'elles sont
  parties, pour savoir ce qui a été posé et quand.
- `hors-refonte/pages-<id>.json` — les quatre pages en ligne que la
  refonte ne touche pas : `/qui-sommes-nous/`, `/sur-mesure/`,
  `/newsletter/`, `/mentions-legales-agence-voyage-egypte/`.
- `MANIFESTE.json` — la date, le décompte, l'empreinte SHA-1 de chaque
  fichier, et la liste des couples brouillon → cible avec le gabarit
  d'avant.

## Ce qu'elle ne contient pas

Ce n'est pas une sauvegarde de base de données. Elle couvre exactement
ce que la bascule modifie — le contenu et le gabarit des 57 cibles — et
rien d'autre : ni les menus, ni les réglages du thème, ni la
médiathèque, ni les extensions, ni les commandes. Pour un filet
complet, doubler avec une sauvegarde serveur (UpdraftPlus, ou l'export
de l'hébergeur) le jour de la bascule.

## Revenir en arrière

    WP_AUTH='compte:mot de passe' ./outils/mise-en-ligne.py --revenir

Reprend la sauvegarde la plus récente et remet, pour chaque cible, son
contenu et son gabarit d'avant. Le titre, le slug et les méta Yoast
n'ayant jamais été touchés par la bascule, ils n'ont rien à retrouver.
