# Banc d'essai de l'écran Contenus

Rend le vrai écran du plugin hors de WordPress, avec les **vraies pages
du site**, puis le regarde dans un navigateur.

```sh
cd outils/essais/contenus
php test.php                                  # le classement, gabarit par gabarit
php ecran.php                                 # écrit ecran.html
SP="$(cd .. && pwd)" node vue.js              # compte les blocs, les tableaux, les lignes
```

## Pourquoi il existe

Une refonte de cet écran est partie en production avec le tableau des
pages purement et simplement absent, et la barre d'onglets affichée deux
fois. `php -l` ne voit rien : le PHP était valide, c'est le HTML produit
qui était faux. Seul un rendu réel le montre.

`vue.js` vérifie donc ce qui se compte : deux onglets de zone, une barre
de gabarits par zone, autant de tableaux que de blocs, et le total des
lignes égal au nombre de contenus.

`pages.json` est un relevé daté des pages du site — identifiant, slug,
parent, type, état. Aucun contenu, donc rien de personnel. Il se
régénère depuis l'API quand la structure du site change.
