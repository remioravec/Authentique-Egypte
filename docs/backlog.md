# Backlog de la refonte

> Source : Retour de Mélanie du 24/08/2026, complété par nos propres relevés sur le site en ligne
> Mise à jour : 2026-08-24 — généré depuis `docs/backlog.json` par `outils/backlog-md.py`, ne pas éditer à la main.

| État | Nombre |
|---|---:|
| ✅ Fait | 11 |
| 🔵 En cours | 4 |
| 🟠 À arbitrer | 6 |
| ⬜ À produire | 1 |
| 🟡 En attente cliente | 6 |
| **Total** | **28** |

## Process et non-régression

### P1 — Appel de cadrage lundi

**🟠 À arbitrer** · porteur : les deux

*Demande :* Reprendre les bases du projet au téléphone avant d'aller plus loin.

*Où on en est :* Point bloquant côté cliente. Ordre du jour proposé dans docs/retours-client/2026-08-24-melanie.md.

### P2 — Garantir que la refonte ne perturbe pas le site en ligne

**✅ Fait** · porteur : Rémi

*Demande :* Préserver le fonctionnement de l'ancien site pendant la transition ; ne perdre aucune page ni fonctionnalité.

*Où on en est :* Les maquettes sont des pages BROUILLON, gabarit Elementor Canvas, sous une page mère dédiée. Vérifié après déploiement : 404 en accès anonyme, absentes du sitemap Yoast, et les 60 URL publiques du site répondent toujours 200. Aucune page existante, aucun menu, aucune redirection n'a été touché.

### P3 — Pages de l'ancien site qui ne fonctionnent plus

**🔵 En cours** · porteur : Mélanie

*Demande :* « Certaines pages de l'ancien site ne fonctionnent déjà plus correctement. »

*Où on en est :* Balayage des 60 URL publiques (pages, articles, programmes) : toutes en 200, aucune erreur. Une seule anomalie relevée : /programs/oasis-de-daklha/ redirige en 301 vers la catégorie désert, alors que ce séjour est listé comme une offre. Il nous faut la liste précise des pages concernées : « ne fonctionne plus » peut vouloir dire mise en page cassée, formulaire muet ou lenteur, ce qu'un contrôle de code HTTP ne voit pas.

### T1 — Charte partagée entre les gabarits

**✅ Fait** · porteur : Rémi

*Demande :* Relevé de notre côté.

*Où on en est :* Les quatre premières maquettes embarquaient chacune une copie de la charte : « les couleurs sont à revoir » aurait voulu dire huit modifications. La charte vit maintenant dans maquettes/assets/charte.css, chargée par les nouveaux gabarits. Reste à y ramener les quatre premières maquettes.

### T2 — Ramener les 4 premières maquettes sur la charte partagée

**⬜ À produire** · porteur : Rémi

*Demande :* Suite de T1.

*Où on en est :* index, categorie-desert, produit-siwa et article-quand-partir gardent leur CSS en propre. À migrer, avec contrôle visuel avant/après — elles sont déployées et validées, on ne les touche pas à l'aveugle.

## Design

### D1 — Polices non adaptées au mobile

**🔵 En cours** · porteur : Rémi

*Demande :* « Les polices ne sont pas adaptées à la version mobile. »

*Où on en est :* Plancher typographique mobile posé dans la charte partagée : corps à 17 px, plus rien sous 15 px, cibles tactiles à 44 px, titres resserrés. Appliqué aux quatre nouveaux gabarits. Reste à confirmer par Mélanie sur son propre téléphone, et à étendre aux quatre maquettes de la première salve.

### D2 — Couleurs à revoir

**🟠 À arbitrer** · porteur : Mélanie

*Demande :* « Les couleurs sont à revoir. »

*Où on en est :* La charte actuelle a été relevée sur le site en ligne (or #FBB50E, bleu #167FA4). Trop large pour être traité à l'aveugle : à préciser élément par élément, ce que le sélecteur de couleur de l'outil d'annotation permet directement.

### D3 — Page de demande de devis : design différent

**✅ Fait** · porteur : Rémi

*Demande :* « La page de demande de devis ne me convient pas et devrait avoir un design différent. »

*Où on en est :* Gabarit produit. Le formulaire unique devient quatre écrans courts avec barre d'avancement ; le courriel n'est demandé qu'en dernier, une fois trois écrans investis. Une phrase de récapitulation se réécrit à chaque choix. Un panneau collant répond à « qu'est-ce qui se passe si j'envoie ? », question que la page en ligne laisse sans réponse. Validation et confirmation testées.

### D4 — Pages Destinations : design à revoir

**✅ Fait** · porteur : Rémi

*Demande :* « Les pages Destinations sont également à revoir au niveau du design. »

*Où on en est :* Gabarit destination produit (Voyage au Caire). Réponse en tête sur le nombre de jours, sites classés par temps de visite, tableau 2/3/4 jours, ruban de saison, cinq liens de corps vers les destinations voisines — la page en ligne n'en avait aucun. Le bloc d'offres est au milieu, pas en pied.

### D5 — Page Qui sommes-nous : style différent du reste

**✅ Fait** · porteur : Rémi

*Demande :* « La page Qui sommes-nous a un style assez différent du reste du site. »

*Où on en est :* Gabarit produit, et le fond du reproche est traité : la page utilise désormais la charte partagée, les mêmes cartes et le même bloc devis que le reste du site. Ajouté un bloc « ce que nous ne faisons pas », qui manque au site. Dix-neuf marqueurs jaunes signalent ce qui doit venir de l'agence : bios, photos de l'équipe, chiffres réels, récit.

### D6 — Pages du blog

**✅ Fait** · porteur : Rémi

*Demande :* « Même chose pour les pages du blog. »

*Où on en est :* Hub des guides produit. Classement par moment de préparation (je choisis / je réserve / ma valise / sur place) au lieu de l'antichronologie par défaut de WordPress. Filtre à quatre entrées, compteurs calculés, trois parcours de lecture. Trois cases vides signalent trois guides très demandés qui n'existent pas : budget, pourboires, eau.

### D7 — Plus de photos dans l'article de test

**✅ Fait** · porteur : Rémi

*Demande :* « Sur la page de test d'un article, il faudrait ajouter davantage de photos afin de rendre la page plus attractive. »

*Où on en est :* Article passé de 4 à 9 photos : une bande de trois vignettes après le calendrier (Le Caire, Assouan, Siwa, avec leur fenêtre de saison) et deux images pleine largeur de plus (Gizeh, lac Nasser).

## Fonctionnel

### F1 — Composez votre Égypte : sélection multiple

**✅ Fait** · porteur : Rémi

*Demande :* « Il serait intéressant de pouvoir sélectionner plusieurs éléments dans chaque catégorie. »

*Où on en est :* Fait. OU à l'intérieur d'une colonne, ET entre les colonnes : « en famille ou en couple » + « le Nil ou le désert ». Désélection au second clic, bouton Tout effacer. Comportement vérifié.

## Contenu

### C1 — Prix du visa : 25 € → 30 €

**✅ Fait** · porteur : Rémi

*Demande :* « Remplacer le prix du visa de 25 € par 30 €. »

*Où on en est :* Corrigé dans la FAQ de l'accueil et dans les données structurées.

### C2 — Ajouter tous les séjours

**🟡 En attente cliente** · porteur : les deux

*Demande :* « Ajouter tous les séjours : actuellement, seulement 8 sont visibles en ligne. »

*Où on en est :* Le site compte 14 programmes. 6 manquent sur la maquette d'accueil : Pyramides Louxor et mer Rouge en famille · Lever du soleil monastère et nuit à Sainte-Catherine · Coucher de soleil et nuit sur le mont Moïse · Excursion à l'Oasis de Fayoum · Roadtrip en Égypte sur mesure · Découverte de la Nubie. Pour les ajouter il nous faut, pour chacun : prix à partir de, durée, photo de couverture et rattachement à une des cinq familles.

### C3 — Retirer « devis en 24 h gratuit »

**🔵 En cours** · porteur : Mélanie

*Demande :* « Retirer devis en 24 h gratuit. »

*Où on en est :* Le bandeau du hero est retiré. La promesse des 24 h apparaît encore à trois endroits : le bandeau haut « Réponse sous 24 h », la liste du bloc devis « Réponse d'une personne de l'équipe sous 24 h », et le panneau des pages voyage « Devis gratuit · réponse sous 24 h ». À trancher : on retire tout, ou seulement l'engagement chiffré du hero.

### C4 — Note et nombre d'avis Google, voyageurs accompagnés

**🟡 En attente cliente** · porteur : Mélanie

*Demande :* « Ajouter la note et le nombre d'avis Google / voyageurs accompagnés à l'endroit prévu. »

*Où on en est :* Les chiffres de la maquette étaient inventés (4,9/5 sur 217 avis, 1 400 voyageurs) : remplacés par des marqueurs jaunes « à remplir » pour qu'aucun chiffre faux ne parte en ligne. Les trois témoignages affichés sont eux aussi des exemples. Chiffres réels attendus.

### C5 — Trois guides très demandés qui n’existent pas

**🟠 À arbitrer** · porteur : les deux

*Demande :* Relevé en construisant le hub.

*Où on en est :* Budget réel d'un voyage, pourboires et argent liquide, manger et boire sans mauvaise surprise. Les trois reviennent dans presque chaque demande de devis et aucune page du site n'y répond. Emplacements réservés dans le hub.

## Photos

### PH1 — Pyramides, croisière et mer Rouge : photo de couverture

**🟡 En attente cliente** · porteur : Mélanie

*Demande :* « Pour Pyramides, croisière et mer Rouge, la photo actuelle est à changer. »

*Où on en est :* Carte marquée en rouge sur la maquette (visible en mode Maillage). Photo de remplacement attendue.

### PH2 — De la mer Rouge aux montagnes du Sinaï : photo et programme

**🟡 En attente cliente** · porteur : Mélanie

*Demande :* « La photo ne correspond pas à l'itinéraire et le programme n'est pas à jour par rapport au nouveau design. »

*Où on en est :* Carte marquée. Photo et déroulé à jour attendus.

### PH3 — Lever du soleil au mont Sinaï : photo

**🔵 En cours** · porteur : Mélanie

*Demande :* « L'itinéraire Charm el-Cheikh → Mont Moïse → Sainte-Catherine ne correspond pas à la photo actuelle. »

*Où on en est :* L'itinéraire affiché sur la carte est corrigé et mentionne bien Sainte-Catherine. La photo est marquée, remplacement attendu.

## Back-office

### B1 — Back-office simplifié, contenus rangés par gabarit

**✅ Fait** · porteur : Rémi

*Demande :* Masquer l'inutile de WordPress, réunir pages et articles, ranger par gabarit, garder médiathèque, extensions, thèmes et administration.

*Où on en est :* Extension ae-back-office. Écran unique « Contenus » qui réunit pages, guides et voyages, rangés par gabarit avec le vocabulaire des maquettes. Classement déduit automatiquement : relevé sur le contenu réel du site, 61 contenus classés, 0 non rangé. Un classement posé à la main devient définitif. Menu réduit à Tableau de bord, Contenus, Médiathèque, Refonte, Apparence, Extensions, Comptes, Réglages, Yoast et Elementor. Le masquage est cosmétique — aucune capacité retirée — et un interrupteur « Menu simplifié / complet » vit en permanence dans la barre du haut, réglable compte par compte. Ajouté à la demande : WPForms, Voyages et Comptes restent dans le menu (les gardes acceptent un joker, `wpforms*` couvrant tous ses sous-écrans).

### B2 — Voir les demandes clientes malgré WPForms Lite

**✅ Fait** · porteur : Rémi

*Demande :* « Laisser WPForms, pour voir les demandes clients. »

*Où on en est :* WPForms Lite n'enregistre pas les soumissions : son écran Entries est une page de vente, les demandes partent uniquement par courriel. Garder le menu ne montrait donc rien. L'extension écoute désormais wpforms_process_complete — action présente aussi sur la version gratuite — et conserve chaque soumission en base : tous les champs, le formulaire d'origine, la page de départ, un bouton Répondre et un état (nouvelle / en cours / traitée / archivée), avec pastille de compte dans le menu. L'envoi du courriel continue normalement. Captation testée sur une soumission simulée : détection du nom et du courriel, cases à cocher aplaties, champs vides ignorés, balise injectée neutralisée. Durée de conservation réglable, sans purge par défaut.

## Dette relevée de notre côté

### X1 — La fiche Siwa décrit le Sinaï

**🟡 En attente cliente** · porteur : Mélanie

*Demande :* Relevé de notre côté, pas dans le retour.

*Où on en est :* Le déroulé de /programs/excursion-a-loasis-de-siwa/ décrit le départ de Sharm el-Sheikh, l'ascension du mont Moïse et le monastère Sainte-Catherine : c'est le programme du séjour Sinaï, copié sur la fiche Siwa. Trois durées coexistent : 4 jours dans la présentation, 3 jours minimum dans l'encart de prix, un déroulé de 2 jours. Rien n'a été réécrit dans la maquette : le vrai déroulé est attendu.

### X2 — FAQ Siwa : 8 questions, 1 réponse

**🟡 En attente cliente** · porteur : Mélanie

*Demande :* Relevé de notre côté.

*Où on en est :* Huit questions sont posées sur la page en ligne, une seule a une réponse rédigée. Une FAQ vide fait plus de mal que pas de FAQ du tout. À noter aussi : la page affirme que Siwa est classée au patrimoine mondial de l'UNESCO ; elle figure sur la liste indicative, elle n'est pas inscrite.

### X3 — Deux programmes portent exactement le même titre

**🟠 À arbitrer** · porteur : les deux

*Demande :* Relevé de notre côté.

*Où on en est :* « Lever du soleil, monastère et nuit à Sainte-Catherine » existe en deux exemplaires (/programs/sainte-catherine/ et /programs/lever-du-soleil-monastere-et-nuit-a-sainte-catherine/). Deux pages qui visent la même recherche se prennent des positions l'une à l'autre. À fusionner ou à différencier.

### X4 — Le séjour Dakhla n'a pas de page

**🟠 À arbitrer** · porteur : les deux

*Demande :* Relevé de notre côté.

*Où on en est :* /programs/oasis-de-daklha/ redirige en 301 vers la catégorie désert : l'offre est listée mais la page n'existe pas. Soit on écrit la fiche, soit on retire l'itinéraire du catalogue.

### X5 — Siwa et Dakhla n'ont pas de page destination

**🟠 À arbitrer** · porteur : Rémi

*Demande :* Relevé de notre côté.

*Où on en est :* Le désert Blanc, le désert Noir et Fayoum ont chacun leur page géographique ; Siwa et Dakhla non. Le maillage de la page catégorie pointe donc vers l'itinéraire faute de mieux.
