# Retours de Mélanie du 12 octobre — 197 fils

Traités le 12 octobre. **198 fils clos** (les 197 du jour et trois de
septembre auxquels elle a répondu), **2 laissés ouverts** pour une précision.
Réponses : `outils/repondre-1210.py`. Plugin : 630 fils, 606 clos, 24
ouverts.

## Ce qui a été fait, par outil

| Outil | Pages | Ce qu'il fait |
|---|---|---|
| `retours-12-10-sejours.py` | 13 séjours | Ligne « Devis gratuit » du haut retirée ; « Avant de boucler le sac » et « Le bon format » retirés ; gras limité aux lieux ; boutons sous « Qui vous accompagne » ; FAQ dépliée en mode relecture. Puis séjour par séjour : repas, étapes, inclus, FAQ, photos (pyramides-Nil, croisière en famille, roadtrip, Pyramides-Louxor-mer Rouge, Siwa, désert blanc, dahabeya, Sainte-Catherine). |
| `jours.py` | — | Bibliothèque : titre, étapes, pastilles d'un jour, ajout d'un jour avec sa ligne de sommaire. |
| `prix-durees-1210.py` | 26 pages | Fayoum 295 €, Pyramides-Nil 1 495 €, désert blanc 680 €, Siwa 695 €, Sainte-Catherine 445 €, croisière en famille 1 690 €, Nubie 1 190 € ; roadtrip 6 jours, Siwa 4, Pyramides-Louxor 8 — sur la page du séjour et sur toutes ses cartes. |
| `retours-12-10-accueil.py` | accueil | Carte d'Égypte dessinée en SVG (`carte-egypte-svg.py`, Natural Earth) au lieu des tuiles pixelisées ; composeur translucide ; titres et tirets. |
| `retours-12-10-global.py` | 60 pages | 51 jours au lieu de 45 ; bandeau « Sur mesure » bleu avec WhatsApp ; « Pourquoi nous » en cartes blanches ; surtitre « Passer du profil au voyage » retiré. |
| `categories-1210.py` | 8 pages | Roadtrip et Pyramides-Louxor en Culturel / Famille / Mer Rouge, case « En famille » ; séjours « en famille » en tête de la page famille ; Nubie sur Assouan ; parcours de la croisière en famille sans Abou Simbel. |
| `profils-1210.py` | couple, famille, solo | Blocs « Ce que … adorent » refaits (bulles bleues, photos, boutons) ; guides famille en cartes ; tuile PMR. |
| `croisieres-1210.py` | 5 pages | Filtre « Croisière » Nil / lac Nasser ; durée 3 à 4 nuits ; tuile Sinaï avec sa photo. |
| `agence-1210.py` | brouillon 9126 | Les seize remarques ; le brouillon reçoit les feuilles communes qu'il n'avait pas. **Toujours pas en ligne : attend le go de Rémi.** |
| `nubie-1210.py` | /programs/decouverte-de-la-nubie/ | Passée au nouveau gabarit (sauvegarde `sauvegarde/avant-mise-en-ligne/2026-10-12/programs-1337.json`), avec le jour par jour de l'ancienne page — qui décrit un autre voyage — pour qu'elle le corrige. |
| `retouches-1210.py` | 2 séjours | Espace parasite après apostrophe, pastille « Guide privé bédouin ». |

## Ce qu'il faut savoir

- **« Je n'arrive pas à cliquer » sur « Voir les autres questions »** : ce
  n'était pas le site. En mode commentaire, l'extension de relecture capte
  tous les clics (`commentaires.js`, l. 699-702). La FAQ se déplie
  désormais d'elle-même quand ce mode est actif.
- **Plusieurs remarques portaient sur des brouillons** (`?page_id=8926`,
  `8927`, `8583`, `8586`, `8588`) restés dans leur état d'avant le 7 octobre :
  boutons d'avis, voile. Sur les pages en ligne, c'était déjà corrigé. À
  trancher par Rémi : mettre ces brouillons à la corbeille pour qu'elle ne
  relise plus que le site.
- **Nubie : 1 190 €** (commentaire 13123, sur la page en ligne, 7 h 54) et
  non 1 290 € (12969, sur le brouillon, 7 h 03). Désert blanc : 680 € remplace
  les 520 € du 5 octobre.
- **Photo de Mélanie** sur « L'agence » : celle envoyée deux fois le 5 octobre
  à 17 h 39, juste avant celle de Hend — choisie sur ce contexte, à confirmer.
- **Pyramides et croisière sur le Nil** : Kom Ombo est maintenant au jour 4 ;
  le jour 5 porte toujours « Kom Ombo et navigation vers Edfou ». Question
  posée dans la réponse.

## Restés ouverts

- 12964 (L'agence, « reformater ») et 13071 (Sainte-Catherine, « à enlever ») :
  les bulles pointent la page entière, aucun élément désigné.

## Le soir : les 24 fils restés ouverts

Question de Rémi : « On peut avancer sans Mélanie ? » Oui pour 18 sur 24.
Réponses : `outils/repondre-1210b.py`. Plugin : 633 fils, 627 clos, **6
ouverts** (après les trois commentaires de 16 h sur l'accueil, ci-dessous).

| Outil | Fils | Ce qu'il fait |
|---|---|---|
| `photos-1210.py` | 10744, 10438, 10761, 10816, 10854, 10856 | Tuiles Culturel (colonnes de temple) et Désert (désert blanc) ; une photo par journée prise dans la médiathèque, jamais deux fois la même dans un séjour ; photo de fond des guides « hors des sentiers battus » (Siwa) et « 10 choses à ne pas faire » (pyramides) ; photo de la mer Rouge sous « Plongée ». |
| `complements-1210.py` | 10820, 9527, 9504, 10438 | Carte « arnaques » du blog : couple dans un souk au lieu du visuel publicitaire ; carte du roadtrip sur la page Assouan : villages nubiens au lieu de Karnak ; fort Qaitbay et Montaza sous « Que voir à Alexandrie ? » ; cinq journées de plus illustrées d'après leur titre. |
| `bateaux-1210.py` | 10748 | Page Croisières : « Pourquoi nous » remplacé par « Felouque, dahabeya ou bateau à moteur ? » (durées et textes repris du guide des croisières). |
| `pmr-1210.py` | 10446 | Quatre questions sur le handicap dans la FAQ PMR, réponses tirées du seul guide fauteuil roulant du site. |
| `medicaments-1210.py` | 10829 | Partie « Voyager avec ses médicaments » dans le guide vaccins : la règle, l'exemple du tramadol, ordonnance et boîtes d'origine ; source : Affaires étrangères belges via mesvaccins.net (26/11/2025). Il n'existe pas de liste officielle égyptienne. |

Clos sans changement de page : 10746, 10751 (photo du Sinaï déjà posée),
9526, 9543, 10846 (photos déjà en place), 10738 (prix sur les 14 cartes),
12674 (photos d'avis Google : impossible à reprendre).

### Ce qui attend Mélanie

- 10809 : une photo de Bahariya (seule journée de programme sans photo).
- 10855 : une photo d'atelier, poterie ou hiéroglyphes.
- 9504, 9506 : bibliothèque, catacombes et colonne de Pompée à Alexandrie.
- 12964, 13071 : bulles posées sur la page entière (l'outil les a accrochées
  au code invisible de Google Tag Manager), rien ne dit quel bloc est visé.

### À relire par Mélanie

- Les réponses PMR et la partie médicaments.
- La carte « bateau à moteur » montre le Nil à Assouan, faute de photo de
  bateau à moteur.
- La photo du « désert noir » est celle que la médiathèque nomme ainsi.

### Vu en passant

« Nos séjours » montre deux cartes au même titre, « Lever du soleil,
monastère et nuit à Sainte-Catherine » : 445 € (/programs/sainte-catherine/)
et 320 € (/programs/lever-du-soleil-monastere-et-nuit-a-sainte-catherine/).
Doublon à trancher.

## 16 h : trois commentaires sur l'accueil

`outils/accueil-1210b.py`, réponses dans `repondre-1210b.py`, fils clos.

- 13514 « la carte est trop grande » : carte à gauche, six vignettes à
  droite (trois par ligne) sur ordinateur ; 518 px de haut au lieu de 990.
  Écritures de la carte grossies d'autant. Mobile inchangé.
- 13515 « modifier le texte » : « Nos destinations en Égypte ».
- 13516 « le fond est pas assez transparent » : composeur à 55 % de blanc
  (78 % avant), intitulés gris foncés pour la lisibilité.

## Le soir : la barre de recherche du hero (demande de Rémi)

`outils/barre-recherche-1210.py`, sauvegarde de l'accueil avant
changement dans `sauvegarde/avant-mise-en-ligne/2026-10-12/` (hors dépôt).

Sur le modèle d'une barre de moteur de voyage envoyée par Rémi :
- trois champs côte à côte, « Vous partez », « Ce qui vous attire », « Vous
  avez », chacun avec sa valeur (« Indifférent » par défaut) ; un clic ouvre
  ses pastilles (plusieurs choix), une croix le vide ;
- une loupe ronde dorée, avec le nombre de séjours trouvés dès qu'un choix
  est fait ;
- la barre est à cheval sur le hero et la section « Nos itinéraires » :
  moitié-moitié sur ordinateur (44 px de chaque côté), 64 px de débord sur
  téléphone, où les champs s'empilent et le bouton dit « Voir les séjours ».

Le filtrage ne change pas : mêmes pastilles, même script, phrase lue par les
lecteurs d'écran et « Tout effacer » conservés hors écran. Le titre
« Composez votre Égypte » disparaît, comme sur le modèle.

Puis, à la demande de Rémi (« l'image du hero plus grosse ») : plus d'air
au-dessus du titre et sous le texte. Sur ordinateur, le hero passe de 271 à
443 px de haut et montre la felouque en entier ; sur téléphone, +44 px.
Et le paragraphe du hero (« Vous nous dites… ») limité à 34 em, aligné à
gauche : quatre lignes sur ordinateur au lieu de deux en pleine largeur.
