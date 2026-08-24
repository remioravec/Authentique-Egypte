# Banc d'essai du CRM

Rend l'écran **Demandes** du plugin `ae-crm` hors de WordPress, avec **les
vraies feuilles de style de l'admin du site**, puis le pilote dans un
navigateur. Ce sont ces feuilles-là qui écrasent les styles d'un plugin :
tester sans elles, c'est tester dans le vide.

```sh
./preparer.sh                                   # récupère les CSS + génère index.html
SP="$(cd .. && pwd)" node test.js               # parcours complet
```

`generer.php` appelle `AECRM_Ecran::afficher()` pour de bon, avec des doublures
pour les fonctions du cœur : le HTML testé est celui que la cliente verra.

Ce que `test.js` vérifie, au-delà du fonctionnement :

- **une alerte est un échec.** Une erreur avalée par un `.catch()` se manifeste
  à la cliente par une fenêtre `alert()`, et le navigateur de test les rejetait
  silencieusement. C'est ainsi qu'un compteur de notes cassé était passé.
- **le bandeau de panne.** La feuille est bloquée exprès, et le test exige que
  l'écran le dise.
- **la résistance à l'admin WordPress** : taille, graisse, casse et arrondis
  des cartes mesurés une fois les feuilles du cœur chargées.
- **aucun débordement**, avec un nom et une adresse volontairement très longs
  dans `jeu.json` — c'est ce qui casse une carte.

Les fichiers produits (`index.html`, `*.png`, les CSS récupérées, les copies de
`crm.css` et `crm.js`) ne sont pas versionnés.
