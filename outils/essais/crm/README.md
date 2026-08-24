# Banc d'essai du CRM des demandes

Rend l'écran **Demandes** du plugin `ae-back-office` hors de WordPress,
puis le pilote dans un vrai navigateur. Le HTML testé est celui que la
cliente verra : `generer.php` appelle `ABO_Demandes::ecran()` pour de
bon, avec des doublures pour les quelques fonctions du cœur.

```sh
cd outils/essais/crm
php generer.php                      # écrit index.html depuis le plugin
cp ../../../plugin/ae-back-office/assets/css/admin.css .
cp ../../../plugin/ae-back-office/assets/js/demandes.js .
SP="$(cd ../.. && pwd)/essais" node test.js    # parcours complet
SP="$(cd ../.. && pwd)/essais" node etroit.js  # 1280 / 900 / 390 px
```

`test.js` vérifie le glisser-déposer, l'ouverture de la fiche au clic et
au clavier, l'ajout d'une note, le changement de colonne par le
sélecteur, la fermeture par Échap, et l'absence de débordement.
`jeu.json` contient les fiches d'essai — dont un nom et une adresse
volontairement très longs, qui sont ce qui casse une carte.

Les fichiers produits (`index.html`, `*.png`, les copies de `admin.css`
et `demandes.js`) ne sont pas versionnés.
