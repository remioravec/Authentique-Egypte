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

## 2 octobre, après-midi — ce que la bascule a appris

La bascule a écrit les 55 cibles sans erreur, et pourtant 39 pages sont
restées à l'ancien dessin, sans menu ni pied. La cause n'était pas dans
l'écriture : sur ces 39, `_elementor_edit_mode` valait `builder` et les
`_elementor_data` n'étaient pas vides. Elementor rend alors SES données et
ignore `post_content`. Le contenu de la refonte était bien en base, et
n'était jamais affiché. Comme le gabarit était déjà passé en
`elementor_canvas`, le menu du thème avait disparu sans être remplacé.

La corrélation était parfaite sur les 55 : les 16 pages sans données
Elementor, et elles seules, rendaient la refonte.

Le remède tient dans `outils/elementor-se-tait.py` : vider
`_elementor_edit_mode`. Les `_elementor_data` ne sont jamais touchées —
elles restent en base, et remettre `builder` suffit à retrouver l'ancienne
page. C'est ce que fait `outils/remettre-comme-avant.py`, cible par cible.

À retenir pour toute bascule future sur ce site : écrire `post_content`
ne suffit pas, il faut vérifier qui, d'Elementor ou de WordPress, rend la
page — et le vérifier sur l'URL publique, pas sur le code de retour de
l'API.
