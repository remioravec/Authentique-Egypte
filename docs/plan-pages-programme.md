# Plan de refonte des pages programme — gabarit « programme »

Rédigé le 09/09/2026 à partir du dépôt, de la page live Siwa et des outils de contrôle. Ce plan est écrit pour être **exécuté ticket par ticket** (Opus 5), chaque ticket portant sa source, ses règles, ses contrôles et son critère d'acceptation. Rien ne se déclare : tout se mesure.

---

## 0. En une page

**Ce qu'on fait.** Les 14 fiches `programs` du site sont coulées dans le gabarit « programme » — l'UX de la page circuit concurrente (hero, repères, panneau collant, jour par jour illustré, tarifs, inclusions, infos pratiques, FAQ, appel, séjours proches) avec la charte Authentique Égypte. **Le contenu est celui de la page live, mot pour mot, image pour image.** Seule la mise en page change.

**Ce qu'on ne fait pas.** On ne touche à rien qui soit en ligne : ni les 14 fiches `programs`, ni un menu, ni une redirection, ni un réglage, ni la médiathèque. Le travail vit dans le dépôt (`maquettes/`, `outils/`, `docs/`) et, côté site, uniquement dans des **pages brouillon** sous « Refonte 2026 », servies par le gabarit Elementor Canvas, invisibles d'un visiteur anonyme (404) et absentes du sitemap. C'est le dispositif déjà en place pour les 67 pages de refonte, vérifié le 24/08 (`docs/retours-client/2026-08-24-melanie.md`).

**Les trois verdicts obligatoires.** Une page programme n'est finie que si elle porte, sur son dernier commit, trois rapports rangés dans `docs/controles/<slug>/` :

| Contrôle | Qui | Outil | Verdict attendu |
|---|---|---|---|
| Fidélité du contenu | agent `controle-contenu` | `outils/verif/controle-contenu.py` | **FIDÈLE** |
| Cohérence et pertinence | agent `qualite` | `outils/verif/qualite.js` | **CONFORME** |
| Images et lisibilité (nouveau) | agent `qualite` | `outils/verif/images.py` + `outils/verif/lisibilite.js` | **CONFORME** |

Un verdict REFUSÉ ou À CORRIGER ne se discute pas : on corrige le **générateur** (jamais le HTML à la main), on régénère, on repasse les trois contrôles. Les deux agents ne modifient jamais une page.

**L'ordre.** 1) Outillage (tickets O) → 2) la page pilote Siwa, section par section (tickets S) → 3) les 13 autres fiches par le même protocole (tickets P) → 4) déploiement en brouillon et non-régression (tickets D) → 5) livraison à Mélanie (ticket L).

---

## 1. Cadre et interdits

### 1.1 Périmètre : les 14 fiches

| id | slug | titre | image à la une (media id) | brouillon « voyage » existant |
|---:|---|---|---:|---:|
| 5515 | itineraire-sinai-sainte-catherine-mont-moise-et-mer-rouge | Du littoral de la mer Rouge aux montagnes du Sinaï | 5520 | 7941 |
| 5412 | campement-au-coeur-du-mont-moise | Coucher de soleil et nuit sur le mont Moïse | 5413 | 7935 |
| 5864 | lever-du-soleil-monastere-et-nuit-a-sainte-catherine | Lever du soleil, monastère et nuit à Sainte-Catherine | 5117 | 7943 |
| 5109 | sainte-catherine | Lever du soleil, monastère et nuit à Sainte-Catherine (doublon) | 5117 | 7948 |
| 1369 | roadtrip-en-egypte | Roadtrip en Égypte sur mesure | 668 | 7947 |
| 1198 | croisiere-sur-le-lac-nasser | Croisière sur le lac Nasser | 1336 | 7936 |
| 2393 | excursion-a-loasis-de-siwa | Voyage à l'Oasis de Siwa — **pilote** | 2400 | 7939 |
| 1337 | decouverte-de-la-nubie | Découverte de la Nubie | 246 | 7937 |
| 1408 | le-caire-et-croisiere-sur-un-bateau-a-voile | Le Caire et croisière sur un bateau à voile | 1561 | 7942 |
| 1168 | pyramides-et-croisiere-sur-le-nil | Pyramides et croisière sur le Nil | 663 | 7945 |
| 540 | mer-rouge | Pyramides, croisière et mer rouge en famille | 6461 | 7944 |
| 7336 | pyramides-louxor-et-mer-rouge-en-famille | Pyramides, Louxor et mer rouge en famille | 6461 | 7946 |
| 2054 | excursion-a-loasis-de-fayoum | Excursion à l'Oasis de Fayoum | 2143 | 7938 |
| 2193 | excursion-dans-le-desert-blanc | Excursion dans le désert blanc | 2141 | 7940 |

Relevé REST du 09/09/2026 (`/wp-json/wp/v2/programs`). Deux fiches partagent l'image à la une 5117 (les deux Sainte-Catherine), deux autres la 6461 (mer-rouge et pyramides-louxor). C'est un fait de la source, pas une erreur du gabarit : il est repris tel quel et signalé.

### 1.2 Où vit le travail

| Quoi | Où | Règle |
|---|---|---|
| Le générateur | `outils/gabarit-programme.py` | Seul endroit où la mise en page s'écrit. Une correction se fait ici, jamais dans un HTML produit. |
| L'inventaire d'une fiche | `docs/programmes/<slug>.json` | Produit par `outils/inventaire-programme.py` (ticket O1). Versionné. C'est la **source de vérité** du contenu, datée. |
| Le HTML produit | `maquettes/site/programme-<slug>.html` | Préfixe `programme-`, pour ne pas écraser les `voyage-<slug>.html` du gabarit précédent, qui restent jusqu'à validation. |
| Les rapports de contrôle | `docs/controles/<slug>/<AAAA-MM-JJ>-<controle>.md` | Un fichier par passage. Le dernier fait foi. |
| Le registre des décisions | `docs/programmes/registre-decisions.md` | Chaque ajout d'interface, chaque écart accepté, avec sa source et sa date. **Ce qui n'y est pas est une invention.** |
| Les questions à la cliente | `docs/programmes/questions-melanie.md` | Tout ce que la source ne permet pas de trancher. Une page se produit quand même, marquée. |
| La maquette pilote | `maquettes/programme-siwa.html` | Régénérée par le générateur ; c'est le moule de référence du gabarit une fois validée. |

### 1.3 Les interdits, sans exception

1. **Aucune écriture sur `/wp-json/wp/v2/programs`, `/media`, `/menus`, `/settings`.** Le déploiement n'appelle que `/pages`, en `status: draft`, sous « Refonte 2026 ». Le script refuse tout autre statut.
2. **Aucune phrase réécrite, raccourcie, complétée.** Une coquille de la source reste une coquille ; elle va dans `questions-melanie.md`.
3. **Aucun chiffre qui ne vienne pas de la source** (prix, durée, jours, dates, avis). Un chiffre repris d'une autre page du site (accueil, widget d'avis) porte sa provenance dans le registre.
4. **Aucune image étrangère à la fiche**, hors ajouts d'interface inscrits au registre (logo, cartes des séjours proches). L'image à la une fait partie de la fiche.
5. **Aucune image agrandie au-delà de sa taille réelle** (règle de pixelisation, §4 O2).
6. **Aucune classe inventée** : le gabarit programme est le moule ; les mêmes classes portent les mêmes blocs sur les 14 pages.
7. **Aucun HTML produit modifié à la main.** Si une page a besoin d'un cas particulier, il s'écrit dans le générateur, sous condition explicite sur le slug, et se lit dans l'inventaire.
8. **Aucune page déclarée finie sans les trois rapports.**

---

## 2. État zéro mesuré (09/09/2026)

Ce qui existe : `maquettes/programme-siwa.html` (997 lignes, généré par `gabarit-programme.py` depuis `docs/extraits.json` et la page d'accueil live) et `maquettes/programme-alexandrie-abou-simbel.html` (le circuit concurrent coulé dans le moule voyage, démonstration d'UX — pas une page à livrer).

### 2.1 Ce que disent les outils sur la maquette Siwa

`node outils/verif/qualite.js maquettes/programme-siwa.html` → **CONFORME** (0 bloquant, 0 majeur, 0 mineur ; 1 H1, 2 438 mots, 14 images, 14 accordéons, 6 appels à l'action, 4 éléments collants).

`outils/verif/controle-contenu.py <live Siwa> maquettes/programme-siwa.html --coupe Trustindex --zone "Voyage à l" --fin "Siwa se combine"` → **REFUSÉ**. Après tri du bruit d'habillage (menu, pied, titres d'autres séjours), les écarts réels :

| # | Écart | Gravité | Cause | Traité par |
|---|---|---|---|---|
| Z1 | 6 questions de la FAQ absentes (« Comment s'y rendre depuis Le Caire ? », « Quelle est la meilleure période ? »…) | bloquant selon la règle | Choix du générateur : ne montrer que les questions ayant une réponse rédigée (dette X2 : 8 questions, 1 réponse) | Décision à inscrire au registre **ou** afficher les questions avec un marqueur « réponse attendue ». Recommandation : les afficher marquées, une question posée sur la page live est du contenu. |
| Z2 | 7 images de la source non reprises : `DSC00493`, `DSC00535`, `DSC00611`, `DSC00528-scaled-e1750597600417` (originaux disponibles en pleine taille), `mohamad-sameh-…`, `raimond-klavins-…` (seule la vignette 300×200 existe, l'original répond 404), logo (habillage) | bloquant | Le générateur lit `docs/extraits.json`, pas les images | O1 + S7 |
| Z3 | L'**image à la une** de la fiche (`Siwa_Oasis_sunset_on_Maraqi_Egypt.webp`, media 2400, alt « oasis de siwa ») n'apparaît nulle part | bloquant | Non lue (elle n'est pas dans le corps de la page) | O1 + S1 |
| Z4 | Visa « 25 € » dans les infos pratiques | **bloquant : chiffre faux** | Bloc repris de l'accueil **live**, alors que la maquette d'accueil validée porte 30 € (backlog C1) | O4 : les infos pratiques viennent de `maquettes/index.html`, pas du site live |
| Z5 | « 45 jours avant le départ », « 23 avis Google » | à sourcer | 45 j : FAQ paiement de l'accueil ; 23 : widget Trustindex de la page live, relevé du 09/09 | Registre + O4 (le nombre d'avis se lit, ne se code pas en dur) |
| Z6 | « Personaliser ce séjour » (4 occurrences) | majeur : faute | Libellé du générateur | O4 |
| Z7 | 5 images hors source : logo, photo d'équipe `DSC00581-1.jpg` (accueil), 3 cartes de séjours proches | à inscrire | Ajouts d'interface | Registre |
| Z8 | Titre « Siwa se combine, ou se remplace », liens de thèmes « Voyage en couple / en famille », mention « Mélanie, votre interlocutrice » | à inscrire ou à retirer | Écrits par le générateur | Registre (décision Rémi) |

### 2.2 Ce que les outils ne voient pas encore

| # | Constat | Mesure | Gravité |
|---|---|---|---|
| Z9 | **Pixelisation du hero.** Les 5 PNG Siwa font 1000 × 667. Le hero est en pleine largeur, 560 à 760 px de haut. | À 1360 px : agrandissement × 1,36. À 1920 px : × 1,92. En Retina, × 2,7 à × 3,8. | bloquant |
| Z10 | Les photos « jour par jour » (1000 px sur une boîte de 720 px) et les vignettes latérales sont nettes ; les cartes des séjours proches reprennent des PNG de catégorie de tailles inconnues. | À mesurer par O2 | — |
| Z11 | **Titres d'étapes tronqués.** `.etapes-carte span{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}` coupe les titres longs sur bureau : du contenu de la source devient illisible. | Visible sur « Arrivée chez votre hôte… » selon la largeur | majeur |
| Z12 | **Rythme vertical hétérogène.** Sections à 52/60/70 px de padding selon le bloc (`.deux` 52, `.jpj` 60/70, `.tarifs-sec` 60, `.prat` 70, `.final` 70, `.simil` 60) alors que la charte définit `.section{padding:clamp(50px,6vw,88px) 0}`. | Relevé CSS | majeur |
| Z13 | Textes sous le plancher mobile (15 px) : `.reperes small` .7rem, `.pan__note` .76rem, `.acc__t` .72rem, `.hero__prix small` .72rem, `.simil__tag` .74rem, `.pan__equipe small` .7rem. La charte n'a de plancher que pour ses propres classes ; le CSS du gabarit programme n'est pas couvert par `outils/mobile.py`. | À mesurer par O3 à 390 px | majeur |
| Z14 | Contraste des textes posés sur photo (hero : chapô à 86 % de blanc sur dégradé) : non mesuré. | O3 | à mesurer |
| Z15 | Le hero n'a ni `srcset` ni `sizes` ; toutes les images sont servies en une seule taille. | — | mineur (performance), sans effet sur la netteté tant que Z9 n'est pas résolu |

### 2.3 Ce que la source elle-même a de faux (à ne pas corriger, à signaler)

- **X1** : le déroulé de la fiche Siwa décrit le Sinaï (Sharm el-Sheikh, mont Moïse, Sainte-Catherine). Trois durées coexistent : 4 jours (présentation), 3 jours minimum (encart de prix), déroulé de 2 jours.
- **X2** : 8 questions de FAQ, 1 réponse ; affirmation UNESCO inexacte.
- **X3** : deux fiches au titre identique (5109 et 5864), même image à la une.
- **PH1–PH3** (retour du 24/08) : photos de couverture à changer sur trois programmes ; aucune photo reçue à ce jour (retour du 26/08 : 0 fichier joint).
- `docs/images-cassees.txt` : dix images `-576x1024.jpg` référencées par le site répondent 404.

Règle : la page se produit **fidèle à la source**, l'anomalie est écrite dans `questions-melanie.md` avec le sélecteur de l'élément, et un marqueur `.aremplir` (charte) est posé **à côté**, jamais à la place, du contenu douteux.

---

## 3. Sources de vérité et registre des décisions

### 3.1 Les cinq sources, dans l'ordre de priorité

1. **La page live de la fiche** — `https://authentiquegypte.com/programs/<slug>/`, capturée en HTML dans `docs/sources/<slug>-<date>.html` (dossier à ajouter au `.gitignore`, comme `docs/extraits.json` ; la capture reste locale, l'inventaire qui en sort est versionné). Textes, listes, FAQ, prix, durées, images du corps.
2. **L'API REST** — `/wp-json/wp/v2/programs/<id>` pour `featured_media`, `title`, `excerpt`, `modified_gmt` ; `/wp-json/wp/v2/media/<id>` pour `source_url`, `media_details.width/height/sizes`, `alt_text`. C'est la seule façon d'avoir l'image à la une et la **taille réelle** de chaque image.
3. **La maquette d'accueil validée** — `maquettes/index.html` — pour les trois groupes d'infos pratiques (organisation, réservation, paiement), la réassurance et le texte d'agence. **Jamais l'accueil live** (Z4).
4. **Les blocs communs** — `maquettes/assets/blocs/entete.html` et `pied.html`, injectés par `outils/blocs.py`. Le gabarit programme doit entrer dans sa table `PAGE_COURANTE`.
5. **Le registre des décisions** — pour tout ce qui n'est ni 1, ni 2, ni 3, ni 4.

### 3.2 Le registre des décisions (`docs/programmes/registre-decisions.md`)

Format d'une ligne : `D<n> · <date> · <quoi> · <source ou décision de qui> · <sections concernées>`. Amorcé avec ce que l'état zéro a relevé (voir le fichier). Un ajout d'interface non inscrit est traité comme une invention par l'agent contrôle contenu : c'est voulu.

Les décisions déjà à prendre par Rémi avant S1 :

| Décision | Options | Recommandation |
|---|---|---|
| Questions FAQ sans réponse (Z1) | (a) masquer · (b) afficher avec marqueur « réponse attendue » | (b) — fidélité, et Mélanie voit ce qu'il manque |
| Photo et prénom de l'interlocutrice (Z8) | (a) garder « Mélanie » + photo d'équipe de l'accueil · (b) bloc générique « L'équipe d'Authentique Égypte » | (b) tant que la cliente n'a pas validé prénom et photo |
| Liens de thèmes couple / famille (Z8) | garder / retirer | Retirer : ce maillage relève du plan de liens, pas du gabarit |
| Titre des séjours proches (Z8) | « <Titre court> se combine, ou se remplace » / « Ces séjours se combinent bien » | Le second, identique sur les 14 pages, inscrit comme titre de gabarit |
| Promesse de délai | « Réponse sous 48 h (hors vendredi et samedi) » | Garder : retour Mélanie n° 21 du 26/08 (« 48h hors week-end ») ; C3 retire les 24 h |
| Brouillons côté site | (a) remplacer les 14 brouillons « voyage » · (b) dossier « Refonte · Programmes » à côté | (b) — comparaison possible, aucun lien envoyé à Mélanie ne meurt |

---

## 4. Outillage à livrer avant la première page (tickets O)

Chaque ticket O se termine par un test sur la fiche Siwa et un commit propre. Aucune page ne se produit avant O1–O5.

### O1 — `outils/inventaire-programme.py` : l'inventaire daté d'une fiche

**Entrée** : un slug (ou `--tous`). **Sortie** : `docs/programmes/<slug>.json` + `docs/sources/<slug>-<date>.html`.

Structure du JSON, tous les champs obligatoires (vides autorisés, jamais absents) :

```
{
 "slug", "id", "url", "releve": "AAAA-MM-JJ", "modified_gmt",
 "title_seo", "meta_description", "h1",
 "chapo": "<texte>",                     // le premier H2 éditorial (« L'Oasis de Siwa : … »)
 "presentation": ["<p>", …],             // « Vue d'ensemble »
 "prix": {"texte": "595 €", "valeur": 595, "unite": "personne", "libelle_source": "À partir de  595 € / Personne"},
 "reperes": ["3 jours minimum", "Guide privatif", …],   // liste du panneau, dans l'ordre de la source
 "durees": ["4 jours", "3 jours minimum", "2 jours (déroulé)"],  // TOUTES les durées trouvées, pour la cohérence
 "jours": [{"titre": "Jour 1 : …", "etapes": [{"titre", "p": [...]}], "mentions": [...]}],
 "inclus": [...], "exclus": [...],
 "faq": [{"q", "reponse_html" | null}],   // une question sans réponse garde reponse_html: null
 "images": [{"src_original", "src_page", "alt", "largeur", "hauteur", "poids", "role": "une|corps|galerie", "position": n, "etat": "ok|vignette-seule|404"}],
 "image_une": {...},                     // depuis featured_media, avec largeur/hauteur réelles
 "avis_google": {"nombre": 23, "source": "widget Trustindex de la page", "releve": "AAAA-MM-JJ"},
 "categorie": {"nom", "url"},            // depuis le fil d'Ariane de la page live
 "anomalies": ["durées contradictoires : 4 jours / 3 jours minimum / déroulé 2 jours", …],
 "ecartes": [...]                         // habillage non repris (menu, widgets), pour l'agent contrôle contenu
}
```

Règles :
- **Images** : chaque `src` de la page est ramené à son original (suffixe `-300x200` retiré, `elementor/thumbs/<condensé>` résolu via `/wp/v2/media?search=<base>`), puis **mesuré** (HEAD + lecture de l'en-tête PNG/JPEG/WebP, ou `media_details`). Un original qui répond 404 donne `etat: "vignette-seule"` avec la taille de la vignette. Rien n'est deviné.
- Le découpage réutilise `outils/extraire.py` (il sait lire l'HTML aplati d'Elementor) ; on ne réécrit pas un parseur.
- `anomalies` est calculé : durées multiples, prix multiples, FAQ sans réponse, image en doublon avec une autre fiche, titre en doublon (X3), images 404.
- Sortie console : une ligne par fiche — mots, jours, images (nettes / vignettes / 404), FAQ (avec / sans réponse), anomalies.

**Acceptation** : les 14 JSON existent ; pour Siwa, `images` compte 12 entrées + `image_une` ; `faq` compte 8 questions dont 1 avec réponse ; `anomalies` contient les trois durées.

### O2 — `outils/verif/images.py` : netteté, provenance, poids

**Entrée** : la page produite, l'inventaire de la fiche. **Sortie** : rapport + `--json`.

Pour chaque `<img>` : taille réelle (mesurée, cache local des en-têtes), boîte rendue à 390 / 1360 / 1920 px (Playwright, `getBoundingClientRect`, `object-fit` pris en compte : la largeur utile d'un `cover` est `max(boîte.w, boîte.h × ratio)`), et le **facteur d'agrandissement** = largeur utile / largeur réelle.

| Seuil | Verdict |
|---|---|
| facteur > 1,0 à 1360 px | **bloquant** (l'image est agrandie sur l'écran de référence) |
| facteur > 1,25 à 1920 px | majeur |
| facteur > 1,0 à 1920 px, ou > 0,5 en Retina (DPR 2) | mineur, listé pour la demande de HD |
| image hors inventaire et hors registre | bloquant (provenance) |
| image de l'inventaire au rôle `corps` non reprise | majeur (à justifier au registre) |
| suffixe `-NNNxNNN` ou `elementor/thumbs` dans le `src` | majeur (déjà dans `qualite.js`, repris ici avec la mesure) |
| `alt` vide ou nom de fichier | mineur |
| poids > 400 Ko sur une image sous 1 200 px de large | mineur |
| même fichier deux fois sur la page hors galerie/lightbox | mineur |

**Acceptation** : sur la maquette Siwa actuelle, le rapport sort Z9 en bloquant (hero × 1,36) et Z2/Z3 en majeur/bloquant. Sur la page régénérée après S1 et S7, CONFORME.

### O3 — `outils/verif/lisibilite.js` : espacement, lisibilité, contraste

Même socle que `qualite.js` (hors ligne, 1360 et 390 px, réseau coupé). Mesures par `getComputedStyle` et `getBoundingClientRect` :

| Mesure | Seuil | Gravité |
|---|---|---|
| Taille de police de tout élément textuel visible | ≥ 15 px à 390 px, ≥ 14 px à 1360 px (charte : plancher mobile) | majeur |
| Interligne | ≥ 1,35 pour le corps, ≥ 1,1 pour les titres | majeur |
| Longueur de ligne des paragraphes (`p`, `li` de plus de 60 caractères) | 45 à 80 caractères par ligne à 1360 px | majeur au-delà de 90, mineur entre 80 et 90 |
| Contraste texte / fond (fond uni) | ≥ 4,5:1 (≥ 3:1 pour ≥ 24 px ou ≥ 19 px gras) | majeur |
| Contraste texte sur image (hero, badges) | échantillonnage du pixel derrière chaque mot via `canvas` sur l'image rendue + dégradé : ≥ 4,5:1 sur 95 % des échantillons | majeur |
| Chevauchement de deux frères visibles (rectangles qui se recouvrent hors positionnement volontaire `absolute/sticky`) | 0 | bloquant |
| Texte tronqué (`text-overflow: ellipsis` effectif : `scrollWidth > clientWidth`) | 0 sur du contenu de la source | **bloquant** (Z11 : c'est une altération) |
| Cible tactile (liens, boutons, `summary`) à 390 px | ≥ 44 × 44 px | majeur |
| Padding vertical des sections de premier niveau | dans l'échelle {40, 48, 64, 88} px (bureau) et {32, 40, 48} (mobile) ; écart maximal entre deux sections voisines : un cran | majeur (Z12) |
| Espacement entre blocs frères d'une même colonne | dans l'échelle {8, 12, 16, 20, 24, 32, 48} | mineur |
| Débordement horizontal | 0 (déjà dans `qualite.js`) | majeur |
| Zone collante qui masque du contenu à 390 px (barre mobile sur le pied) | 0 | majeur |

Le rapport suit le format des agents (BLOQUANTS / MAJEURS / MINEURS, localisés par sélecteur). **Acceptation** : sur la maquette Siwa actuelle il sort Z11, Z12, Z13 ; il ne sort rien sur `maquettes/index.html` (page validée) hors mineurs documentés.

### O4 — `outils/gabarit-programme.py` : refonte du générateur

Le générateur passe de « fiche `extraits.json` + accueil live » à « inventaire `docs/programmes/<slug>.json` + accueil validé ». Liste fermée des changements :

1. `--programme <slug>` lit l'inventaire ; `--tous` produit les 14 pages dans `maquettes/site/programme-<slug>.html` ; Siwa produit aussi `maquettes/programme-siwa.html`.
2. Les infos pratiques (3 accordéons), la réassurance (3 points) et le texte d'agence viennent de `maquettes/index.html` (parseur sur les classes de la maquette, pas sur `.jkit-accordion`). Plus aucune requête réseau à la génération.
3. Le jeu d'images est celui de l'inventaire, **originaux uniquement**, affectés par rôle (§5, S1 et S7). Une image `vignette-seule` n'est jamais placée dans une boîte plus large que sa taille réelle.
4. `Personaliser` → `Personnaliser`, partout.
5. Le nombre d'avis vient de `avis_google.nombre` de l'inventaire et porte `data-source` et `title="Relevé le …"` ; aucun chiffre en dur dans le code.
6. FAQ : selon la décision Z1 ; par défaut, toutes les questions de la source, celles sans réponse avec un marqueur `.aremplir` « réponse à rédiger » dans le corps du `details`.
7. Étapes : `white-space: normal`, plus d'ellipse (Z11).
8. Rythme : toutes les sections de premier niveau portent la classe `.section` de la charte (padding unique) ; les espacements internes prennent l'échelle de O3.
9. Plancher mobile : le CSS du gabarit est réécrit pour qu'aucune taille ne descende sous `.9rem` (15,3 px) à 600 px ou moins ; les classes `.hero__prix small`, `.reperes small`, `.acc__t`, `.pan__note`, `.pan__equipe small`, `.simil__tag`, `.pan__prix small` reçoivent une règle `@media (max-width:600px)`.
10. Hero : voir S1 (taille bornée par l'image réelle, `srcset`/`sizes` construits depuis `media_details.sizes`).
11. Toutes les chaînes d'interface (titres de section du gabarit, libellés de boutons, notes) sont regroupées dans un dictionnaire `INTERFACE` en tête de fichier, chaque entrée commentée avec son numéro de décision `D<n>`. L'agent contrôle contenu reçoit ce dictionnaire comme liste des ajouts d'interface acceptés.
12. Sortie déterministe : deux générations successives donnent le même fichier (`diff` vide), pour que `git diff` ne montre que les vrais changements.
13. Le bilan console liste, par page : jours, étapes, images placées / non placées (avec la raison), FAQ avec / sans réponse, anomalies de l'inventaire, chaînes d'interface utilisées.

**Acceptation** : `outils/gabarit-programme.py --programme excursion-a-loasis-de-siwa` régénère la maquette, `git diff` lisible, et les trois outils de vérification passent (après S1–S15).

### O5 — `outils/verif/controle-contenu.py` : rendre le rapport lisible

1. `--bruit <fichier>` : une liste de phrases d'habillage (entête, pied, méga-menu, titres des autres séjours) à écarter automatiquement des « manquantes » et « inventées ». Générée une fois depuis `maquettes/assets/blocs/*.html` par un petit script, versionnée dans `outils/verif/bruit-habillage.txt`.
2. `--interface <fichier json>` : le dictionnaire `INTERFACE` du générateur ; ses chaînes sortent des « inventées » et vont dans « ajouts d'interface ».
3. `--inventaire <json>` : le jeu d'images de référence inclut `image_une` et les originaux ; les images du registre (logo, cartes sœurs) ne sont plus « hors source ».
4. Les nombres : le motif ignore les `100%` de CSS (déjà retirés avec `<style>`, mais le `html{font-size:100%}` inline de la source passe) — ne compter que les nombres présents dans le texte visible.
5. Rapport écrit dans `docs/controles/<slug>/<date>-contenu.md` avec `--rapport`.

**Acceptation** : sur la page Siwa régénérée, couverture ≥ 98 % des phrases de la fiche (hors habillage), 0 altérée, 0 inventée hors interface, images de la source reprises 12/12 + à la une, 0 nombre perdu, 0 nombre ajouté hors registre.

### O6 — `outils/deployer-site.py` : le dossier « Refonte · Programmes »

1. Nouveau gabarit `programme` dans `DOSSIERS`, titre « Refonte · Programmes », slug de page `refonte-programme-<slug>`, fichier `maquettes/site/programme-<slug>.html`.
2. `--simuler` : affiche ce qui serait posé, n'appelle rien.
3. Garde-fou : le script refuse de s'exécuter si un contenu contient `status":"publish` ou si `WP_AUTH` est absent ; il vérifie après chaque page que la réponse porte `status: draft`.
4. Contrôle de non-régression intégré (voir D2), exécuté automatiquement en fin de déploiement.

### O7 — `outils/verif/tout.sh <slug>` : la chaîne complète

Enchaîne, dans l'ordre et avec arrêt au premier REFUSÉ : `controle-contenu.py` → `qualite.js` → `images.py` → `lisibilite.js`, écrit les quatre rapports dans `docs/controles/<slug>/`, affiche les quatre verdicts sur une ligne. C'est la commande que chaque ticket S et P appelle en dernier.

### O8 — `outils/blocs.py` et `outils/mobile.py`

`PAGE_COURANTE` reçoit `programme-siwa.html` (bouton « Nos séjours » allumé, catégorie de la fiche) ; le bloc AE-MOBILE est injecté dans les pages programme comme dans les autres.

---

## 5. Le gabarit, section par section (tickets S)

Chaque ticket S se traite **sur la page pilote Siwa**, dans le générateur, et se termine par `outils/verif/tout.sh excursion-a-loasis-de-siwa`. Une section n'est validée que si les quatre verdicts ne régressent pas. L'ordre suit la lecture de la page.

Vocabulaire : *source* = où vient le contenu ; *moule* = classes et DA ; *exactitude* = ce que contrôle contenu doit retrouver ; *lisibilité* = ce que O3 doit mesurer ; *images* = ce que O2 doit mesurer ; *acceptation* = le critère de sortie.

### S0 — `<head>`, données structurées, blocs communs

- **Source** : `title_seo` et `meta_description` de la fiche (Yoast, tels quels, la marque en suffixe comme sur le site). JSON-LD `TouristTrip` (nom, images de l'inventaire, `itinerary` = les jours, `offers` = prix), `FAQPage` (**seulement les questions avec réponse**, une FAQPage avec réponses vides serait fausse), `BreadcrumbList` (accueil → Nos séjours → catégorie de la fiche → fiche).
- **Moule** : polices Archivo/Manrope, `charte.css` par `<link>` (pas de copie inline : T1/T2 du backlog), entête et pied par `blocs.py`.
- **Exactitude** : la catégorie du fil d'Ariane est celle de la page live (`categorie` de l'inventaire), pas une constante « Déserts et Oasis ».
- **Acceptation** : `qualite.js` : 1 H1, description présente ; JSON-LD valide (`python3 -c "json.loads"` sur chaque bloc) ; `blocs.py --verifier` passe.

### S1 — Hero

- **Source** : H1 = titre de la fiche ; chapô = `chapo` (le H2 éditorial) ; prix = `prix.texte` ; pilules = catégorie + les repères de durée et de guide de `reperes` ; **image = `image_une`** (c'est la couverture choisie par la cliente), repli sur la plus grande image `corps` si `image_une` est absente ou 404.
- **Moule** : `.hero`, `.hero__in`, `.hero__pills`, `.hero__prix`, `.hero__conf`, `.hero__act`. Boutons or (devis) et verre (WhatsApp).
- **Images (Z9)** : la hauteur du hero est **bornée par l'image** : `height: min(82vh, 760px, <hauteur réelle> px)` et la largeur utile ne dépasse pas la largeur réelle. Concrètement : si l'image fait moins de 1 360 px de large, le hero passe en composition « image contenue » : l'image nette au centre dans un cadre `max-width: <largeur réelle>`, et le fond de la section est **la même image** floutée (`filter: blur(24px)`, `scale(1.1)`), ce qui reste fidèle (aucune image étrangère) et supprime l'agrandissement. `srcset` depuis `media_details.sizes`, `sizes="100vw"`. Facteur d'agrandissement mesuré ≤ 1,0 à 1360 px.
- **Lisibilité** : contraste du H1 et du chapô sur le dégradé ≥ 4,5:1 (O3 échantillonne) ; sinon renforcer le dégradé bas (`rgba(5,35,50,.85)`), jamais réduire le texte. H1 ≤ 16ch de large ; chapô ≤ 56ch. Plancher mobile sur `.hero__prix small`.
- **Exactitude** : « Réponse sous 48 h (hors vendredi et samedi) » = D3 ; « N avis Google » = `avis_google.nombre` avec `title` daté ; le libellé « / Personne » suit la casse de la source (« / Personne » sur Siwa).
- **Acceptation** : O2 CONFORME sur le hero à 1360 et 1920 ; contraste mesuré ; contrôle contenu retrouve H1, chapô, prix.

### S2 — Repères

- **Source** : `prix` + `reperes` dans l'ordre de la source. Pas de libellé inventé : l'étiquette au-dessus de chaque valeur est « À partir de » pour le prix, « Durée » pour l'item qui contient « jour », sinon le mot-clé de l'item lui-même (pas « Sur mesure », qui est une invention).
- **Moule** : `.reperes` en grille de 6 → 3 → 2 colonnes. Icônes SVG inline du dictionnaire `ICONES`.
- **Lisibilité** : `small` ≥ 15 px sur mobile (Z13) ; hauteur des cellules alignée (grille `align-items: stretch`).
- **Acceptation** : chaque item de `reperes` apparaît une fois et une seule ; aucun mot hors source dans la section (contrôle contenu, section isolée avec `--zone`/`--fin`).

### S3 — Présentation

- **Source** : H2 = `chapo` (le titre éditorial de la fiche), paragraphes = `presentation` (« Vue d'ensemble ») dans l'ordre, sauts de ligne restitués par `para()` sans toucher au texte.
- **Moule** : `.prose`, `p.lede` sur le premier paragraphe. La rangée `.themes` est retirée ou limitée selon D5 (recommandation : un seul lien, « Tous nos séjours <catégorie> », vers la catégorie de la fiche).
- **Lisibilité** : 60 à 75 caractères par ligne à 1360 px (`max-width: 68ch`) ; interligne 1,75 (charte).
- **Acceptation** : 100 % des phrases de « Vue d'ensemble » reprises telles quelles.

### S4 — Les étapes

- **Source** : les titres d'étapes du déroulé (`jours[].etapes[].titre`), avec le numéro de jour. Le titre de section « Les étapes de votre séjour » est un titre de gabarit (registre D6).
- **Moule** : `.etapes-carte`, `ol` en deux colonnes.
- **Lisibilité (Z11)** : titres sur plusieurs lignes, jamais tronqués. O3 vérifie `scrollWidth ≤ clientWidth` sur chaque `span`.
- **Acceptation** : autant de `li` que d'étapes titrées de l'inventaire ; texte identique ; 0 troncature.

### S5 — Points forts

- **Source** : la première liste à puces de la réponse FAQ « Qu'est-ce qui rend <lieu> unique ? » quand elle existe (c'est ce que fait le générateur aujourd'hui ; à inscrire au registre D7 comme **réemploi** d'un contenu de la source, pas comme invention). Si la fiche n'a pas cette liste : **la section n'est pas rendue**. Pas de points forts rédigés.
- **Moule** : `.forts`, deux colonnes, coche teal.
- **Acceptation** : chaque `li` se retrouve mot pour mot dans la FAQ de la source ; section absente sur les fiches sans liste (bilan du générateur le dit).

### S6 — Panneau collant

- **Source** : prix, `reperes`, D3 (délai), D4 (bloc interlocutrice : générique ou nommé), `avis_google`, réassurance en trois points de `maquettes/index.html`.
- **Moule** : `.pan` (`position: sticky; top: 84px`), `.pan__carte`, `.pan__liste`, `.pan__note`, `.pan__equipe`, `.pan__act`, `.pan__conf`. Sur mobile, le panneau passe **au-dessus** du contenu (`order: -1`) : vérifier que ce n'est pas en doublon avec la barre mobile (S14) — le panneau mobile garde prix + repères, la barre garde le bouton.
- **Lisibilité** : `.pan__note`, `.pan__equipe small`, `.pan__conf` ≥ 15 px mobile ; le panneau ne dépasse pas la hauteur de la fenêtre à 1360 × 900 (sinon `top` recalculé ou photo retirée) ; O3 : aucune zone collante ne recouvre un titre.
- **Images** : la photo d'équipe (si D4 = nommé) vient de `maquettes/index.html`, taille réelle mesurée, boîte ≤ taille réelle.
- **Acceptation** : O3 sans majeur sur `.pan` ; contrôle contenu : `reperes` et prix retrouvés, réassurance = celle de l'accueil validé.

### S7 — Jour par jour

- **Source** : `jours[]` : titre du jour (« Jour N : … » → badge `J N` + H3 = le reste du titre, **sans réécriture** ; si la source n'a pas de « Jour N », le titre entier est le H3 et le badge suit l'ordre), étapes (H4 + paragraphes), mentions (nuit, repas) en chips. Lieu : seulement s'il est présent dans le titre après un tiret, sinon rien (pas de déduction).
- **Images** : une photo par jour, prise dans les images `corps` de l'inventaire **dans l'ordre de la page live**, originaux uniquement. Règles : une image n'est utilisée qu'une fois entre hero, jours et galerie latérale ; s'il y a plus de jours que d'images, les derniers jours n'ont pas de photo (pas de recyclage, pas de répétition — Z10) ; une `vignette-seule` de 300 px va dans la galerie latérale (boîtes de 4/3 sous 300 px) ou nulle part, jamais en photo de jour (boîte 720 px).
- **Moule** : `.jpj`, `.jpj__grille` (rail 44 px · colonne 720 px · côté 280 px+), `.jour`, `.jour__photo` (hauteur `clamp(240px, 34vw, 420px)`, `object-fit: cover`), `.jour__badge`, `.etape`, `.mentions`, `.rail` (points d'ancre), `.cote` (galerie 2 × 2 + carte d'appel).
- **Lisibilité** : colonne de texte ≤ 720 px = 65–75 caractères ; `.jour + .jour` = 56 px (un cran de l'échelle : 48 ou 64, choisir 64) ; le rail est masqué sous 1000 px ; les chips ≥ 15 px mobile.
- **Exactitude** : contrôle contenu sur la zone « Itinéraire jour par jour » → 100 % des phrases du déroulé ; les libellés « Jour N » de la source retrouvés.
- **Acceptation** : O2 CONFORME sur toutes les `.jour__photo` et `.cote__photos` ; 12 images de la source utilisées ou justifiées dans le bilan (« non placée : vignette 300 px, boîte trop large »).

### S8 — Tarif et bloc « Ajustons-le »

- **Source** : `prix` ; le tableau de tarifs par base (2, 4, 6 personnes) **n'existe pas** sur les fiches du site — la section rend une seule ligne « À partir de », sans inventer de paliers. Le bloc « Ce séjour vous tente ? Ajustons-le à vos dates. » et ses trois points sont ceux de la bande devis du site refondu (`gabarit-voyage.py`, `bande_devis()`), inscrits au registre D8.
- **Moule** : `.tarifs-sec`, `.tarif`, `.adapter`.
- **Acceptation** : un seul nombre en euros dans la section, égal à `prix.valeur`.

### S9 — Inclus / non inclus

- **Source** : `inclus`, `exclus`, dans l'ordre et avec les titres de la source (« Le programme inclus », « N'inclus pas » — orthographe de la source conservée, signalée dans `questions-melanie.md`).
- **Moule** : `.incl.incl--oui` / `.incl.incl--non`, coche verte, croix rouge (contraste ≥ 3:1 des icônes).
- **Acceptation** : nombre de `li` = nombre d'items ; 0 altération.

### S10 — Informations pratiques + « Pourquoi nous »

- **Source** : `maquettes/index.html` (S3.1 point 3) — trois groupes (organisation, réservation, paiement) avec leurs questions et réponses HTML, la réassurance en trois points, le H2 « Voyagez autrement… » et son paragraphe. Visa à **30 €**.
- **Moule** : `.acc` (un par groupe, `p.acc__t` en étiquette), `details/summary` fermés, `.pourquoi`.
- **Lisibilité** : `.acc__t` ≥ 15 px mobile ; `summary` ≥ 44 px de haut ; réponses ≤ 75ch.
- **Exactitude** : contrôle contenu **avec l'accueil validé comme seconde source** (`--source2 maquettes/index.html` à ajouter à O5 si nécessaire, sinon passage séparé sur la zone). Aucun chiffre de l'accueil live.
- **Acceptation** : 0 « 25 € » ; chaque question et réponse identique à la maquette d'accueil.

### S11 — Questions fréquentes

- **Source** : `faq[]` de la fiche, toutes les questions, dans l'ordre. Réponses HTML propres (`p`, `ul`, `strong` conservés). Question sans réponse : selon D1, marqueur `.aremplir` « Réponse à rédiger — question présente sur la page actuelle sans réponse ».
- **Moule** : `.acc.faq`, première question ouverte.
- **Exactitude** : contrôle contenu, « QUESTIONS FAQ MANQUANTES : 0 ».
- **Acceptation** : 8/8 questions sur Siwa ; JSON-LD FAQPage n'inclut que celles avec réponse.

### S12 — Appel final

- **Source** : H2 « Pouvons-nous vous accompagner ? » et texte d'agence de `maquettes/index.html` ; photo et badge selon D4 ; les quatre confirmations (délai, guide privatif, chauffeur et véhicule, aucune carte bancaire) sont celles de la réassurance du site refondu (registre D9).
- **Moule** : `.final`, `.final__grille`, `.final__photo`, `.final__badge`.
- **Images** : photo 340 × 425 (`aspect-ratio 4/5`) — taille réelle ≥ 340 px de large, sinon boîte réduite.
- **Acceptation** : O2 et O3 CONFORMES ; contrôle contenu : texte = accueil validé.

### S13 — Séjours proches

- **Source** : les cartes de la page **catégorie** de la fiche dans le site refondu (`maquettes/site/categorie-<slug>.html`, gabarit validé) — titre, image, prix « à partir de », lien — en excluant la fiche elle-même, trois cartes maximum, plus le lien « Voir tous nos séjours <catégorie> ». Titre de section selon D5.
- **Images** : celles des cartes de catégorie, taille réelle mesurée ; boîte `.simil__img` 4/3 ≤ taille réelle.
- **Exactitude** : les prix des cartes sont ceux des fiches sœurs (leur inventaire), pas ceux de la maquette produit-siwa d'août.
- **Acceptation** : 3 cartes, 3 images nettes, 3 prix retrouvés dans les inventaires sœurs.

### S14 — Barre mobile, visionneuse, scripts

- **Source** : titre court (H1), prix ; bouton « Personnaliser ce séjour ».
- **Moule** : `.resa-mob` (fixe, bas), lightbox `#lb` du moule voyage, scripts d'apparition `[data-rev]`, rail actif au défilement.
- **Lisibilité** : la barre ne masque pas la dernière section (`body{padding-bottom:78px}`) ; `qualite.js` 0 erreur JS ; O3 : aucune zone collante sur un titre à 390 px.
- **Acceptation** : `qualite.js` CONFORME à 390 px ; la visionneuse ouvre bien l'**original** de chaque image (href = `src_original`).

### S15 — Entête et pied

- **Source** : blocs communs. Rien à écrire : `outils/blocs.py` injecte, `PAGE_COURANTE` allume « Nos séjours » et la catégorie de la fiche (O8).
- **Acceptation** : `blocs.py --verifier` passe sur les 14 pages programme ; retour Mélanie n° 10/14/20 du 26/08 (fond du logo, mention « Agence locale · Le Caire ») déjà traités dans les blocs, vérifiés présents.

---

## 6. Protocole de production d'une page (tickets P)

Le même enchaînement pour les 14 fiches, Siwa d'abord. Aucune étape ne se saute ; chaque étape écrit sa trace.

```
P0  Inventaire        outils/inventaire-programme.py <slug>
                      → docs/programmes/<slug>.json ; lire "anomalies", les copier dans questions-melanie.md
P1  Génération        outils/gabarit-programme.py --programme <slug>
                      → maquettes/site/programme-<slug>.html ; lire le bilan (images non placées, FAQ sans réponse)
P2  Blocs + mobile    outils/blocs.py && outils/mobile.py maquettes/site/programme-<slug>.html
P3  Contrôle contenu  agent controle-contenu : source = URL live, produit = la page,
                      --bruit outils/verif/bruit-habillage.txt --interface <INTERFACE.json> --inventaire docs/programmes/<slug>.json
                      → verdict FIDÈLE exigé
P4  Contrôle qualité  agent qualite : qualite.js + images.py + lisibilite.js, puis lecture
                      → verdicts CONFORME exigés
P5  Correction        chaque défaut → une correction dans gabarit-programme.py (ou l'inventaire si l'extraction est en cause),
                      jamais dans le HTML ; retour en P1
P6  Chaîne complète   outils/verif/tout.sh <slug> → 4 rapports dans docs/controles/<slug>/
P7  Commit            un commit par page : « Programme <titre court> : <n> jours, <n> images, 3 contrôles verts »
                      + les rapports + l'inventaire + les questions
P8  Déploiement       WP_AUTH=… outils/deployer-site.py --gabarit programme --simuler, puis sans --simuler
                      → page brouillon refonte-programme-<slug>, id noté dans docs/liens-a-relire.md
P9  Non-régression    D2, automatique en fin de P8
```

Règle d'arrêt : si P3 ou P4 est REFUSÉ trois fois de suite sur le **même** défaut, on s'arrête et on écrit le cas dans `questions-melanie.md` ou dans le registre — c'est une décision, pas un bug.

### Les invocations des deux agents

Agent **contrôle contenu** (après P2) :

> Contrôle la page `maquettes/site/programme-<slug>.html` contre sa source `https://authentiquegypte.com/programs/<slug>/`. Options : `--coupe Trustindex --bruit outils/verif/bruit-habillage.txt --interface outils/interface-programme.json --inventaire docs/programmes/<slug>.json`. Les ajouts d'interface acceptés sont ceux du registre `docs/programmes/registre-decisions.md` ; les infos pratiques et la réassurance viennent de `maquettes/index.html` (seconde source). Rends le rapport au format de l'agent, écris-le dans `docs/controles/<slug>/<date>-contenu.md`.

Agent **qualité** (après P3 FIDÈLE) :

> Juge la page `maquettes/site/programme-<slug>.html`. Intention : fiche séjour, requête « <titre> », maquette de référence `maquettes/programme-siwa.html`. Passe `qualite.js`, puis `images.py --inventaire docs/programmes/<slug>.json`, puis `lisibilite.js`, à 1360 et 390 px. Lis ensuite la page : promesse tenue (title / H1 / chapô / déroulé parlent du même voyage), fil de lecture, chiffres cohérents (les durées de l'inventaire), mobile. Rends le rapport au format de l'agent, écris-le dans `docs/controles/<slug>/<date>-qualite.md`.

Les deux agents ne modifient rien ; leurs rapports sont l'entrée de P5.

---

## 7. Ordre de production des 14 fiches et cas particuliers

L'ordre va du plus simple au plus chargé, pour que le générateur rencontre les cas rares une fois le tronc commun validé.

| # | slug | Pourquoi à ce rang | Particularités connues |
|---|---|---|---|
| 1 | excursion-a-loasis-de-siwa | **Pilote** : toutes les sections, contenu déjà relevé | X1 (déroulé Sinaï), X2 (FAQ), 3 durées, 2 vignettes-seules, image à la une jamais utilisée |
| 2 | excursion-dans-le-desert-blanc | 657 mots, 4 images : la plus courte | Vérifie le comportement « plus de jours que d'images » |
| 3 | excursion-a-loasis-de-fayoum | 722 mots, 5 images | — |
| 4 | pyramides-louxor-et-mer-rouge-en-famille | 846 mots, 11 images, image à la une partagée avec mer-rouge | PH1 : photo de couverture à changer (attendue) |
| 5 | mer-rouge | 924 mots, 12 images ; slug identique à la catégorie mer-rouge | Le slug de page brouillon porte le gabarit (`refonte-programme-mer-rouge`) |
| 6 | pyramides-et-croisiere-sur-le-nil | 997 mots, 12 images | Vérifier les `-576x1024` cassées (`images-cassees.txt`) |
| 7 | le-caire-et-croisiere-sur-un-bateau-a-voile | 1 069 mots, 10 images | — |
| 8 | decouverte-de-la-nubie | 1 394 mots, 15 images | — |
| 9 | croisiere-sur-le-lac-nasser | 1 423 mots, 19 images | Plus d'images que de jours : galerie latérale à étendre ? (décision, pas d'invention) |
| 10 | roadtrip-en-egypte | 1 435 mots, 14 images | Déroulé peut-être sans « Jour N » : cas du titre entier en H3 |
| 11 | lever-du-soleil-monastere-et-nuit-a-sainte-catherine | 2 615 mots, 13 images | X3 (doublon), PH3 (photo) |
| 12 | sainte-catherine | Identique au 11 | **Produire quand même**, à l'identique, et poser la question X3 (fusion ou différenciation) — ne pas trancher à la place de la cliente |
| 13 | campement-au-coeur-du-mont-moise | 3 684 mots, 16 images | Long déroulé : longueur de ligne et rythme à surveiller |
| 14 | itineraire-sinai-sainte-catherine-mont-moise-et-mer-rouge | 5 014 mots, 20 images : la plus lourde | PH2 (photo + programme à mettre à jour) ; la page brouillon 7941 était « maquette dessinée » |

Après la fiche 14 : `outils/gabarit-programme.py --tous` puis `for s in …; do outils/verif/tout.sh $s; done` — les 14 pages doivent sortir vertes **dans la même passe**, sinon le générateur a un cas particulier non écrit.

---

## 8. Déploiement en brouillon et non-régression (tickets D)

### D1 — Déployer

`WP_AUTH='compte:mot de passe d application' outils/deployer-site.py --gabarit programme --simuler` puis sans `--simuler`. Résultat attendu : 14 pages `refonte-programme-<slug>` sous « Refonte · Programmes », toutes `draft`, gabarit `elementor_canvas`. Les 14 brouillons « voyage » ne sont pas touchés (D6 du registre).

### D2 — Non-régression, après chaque déploiement (automatique dans O6)

| Contrôle | Attendu |
|---|---|
| Les 14 URL `/programs/<slug>/` publiques | 200, `modified_gmt` **inchangé** par rapport à l'inventaire |
| Les 60 URL publiques du site (liste de `docs/inventaire.json`) | 200 |
| Accès anonyme aux 14 brouillons (`?page_id=`) | 404 |
| Sitemap Yoast | aucune URL `refonte-` |
| `/wp-json/wp/v2/programs` | 14 entrées, mêmes ids, mêmes `featured_media` |
| Menus (`/wp-json/wp/v2/menus` si exposé, sinon comparaison de l'entête live) | identiques |

Le rapport s'écrit dans `docs/controles/deploiement-<date>.md`. Un seul écart → le déploiement est signalé comme suspect et on s'arrête.

### D3 — Rendu dans WordPress

Sur trois pages (Siwa, lac Nasser, Sinaï), vérifier connecté : polices chargées, panneau collant vivant (`overflow-x: clip` de `vers-page-wp.py`), barre mobile, visionneuse, aucune règle du thème qui gagne (`.elementor-kit-4658`). Captures à 1360 et 390 dans `docs/controles/<slug>/<date>-wp-*.png`.

---

## 9. Livraison à Mélanie (ticket L)

1. `docs/liens-a-relire.md` : nouvelle section « Programmes — 14 pages », un lien brouillon par fiche, en face du lien de la page actuelle et du brouillon « voyage » précédent.
2. `docs/programmes/questions-melanie.md` mis au propre : une question par ligne, numérotée, avec la page, l'élément et ce qu'on attend (un chiffre, une photo HD, un choix). Contiendra au minimum : X1, X2, X3, PH1–PH3, le prénom et la photo de l'interlocutrice, les originaux HD des images sous 1 360 px, les images 404, la promesse de délai.
3. `docs/plan-refonte.md` : le dossier « Refonte · Programmes » ajouté au tableau.
4. Le message de livraison tient en dix lignes : ce qui est en brouillon, comment relire (extension AE Commentaires, touche C), ce qu'on attend d'elle.

---

## 10. Annexes

### A. Grille des seuils (référence unique, reprise par O2 et O3)

| Domaine | Règle |
|---|---|
| Images | facteur d'agrandissement ≤ 1,0 à 1360 px (bloquant au-delà) ; ≤ 1,25 à 1920 px ; Retina relevé en mineur ; aucune vignette `-NNNxNNN` ; `alt` descriptif |
| Typographie | corps 17 px / 1,75 (charte) ; plancher 15 px mobile, 14 px bureau ; titres H1 `clamp(2.1rem,4.6vw,3.4rem)` ; 45–80 caractères par ligne |
| Contraste | 4,5:1 texte courant, 3:1 grands textes et icônes porteuses de sens |
| Espacement | sections {40, 48, 64, 88} bureau / {32, 40, 48} mobile ; blocs {8, 12, 16, 20, 24, 32, 48} ; un cran d'écart maximum entre voisins |
| Tactile | 44 × 44 px minimum à 390 px |
| Structure | 1 H1 ; H2 → H3 → H4 sans saut ; 0 section vide ; 0 titre orphelin ; 0 texte tronqué ; 0 débordement |
| Conversion | au moins un appel devis visible sans défiler à 1360 et à 390 ; panneau collant présent |

### B. Format d'un rapport de contrôle rangé dans `docs/controles/`

En-tête : outil, version (hash du commit), page, source, date, commande exacte. Corps : le format de l'agent (verdict, BLOQUANTS, MAJEURS, MINEURS, « ce qui est bien »). Pied : le JSON brut de l'outil, replié dans un `<details>`. Un rapport sans commande reproductible n'est pas un rapport.

### C. Prompt type pour un ticket S (à donner à Opus 5)

> Tu travailles sur le dépôt Authentique-Égypte, branche `<branche>`, ticket **S<n> — <nom>** du plan `docs/plan-pages-programme.md` (§5). Lis d'abord le ticket, le registre `docs/programmes/registre-decisions.md` et l'inventaire `docs/programmes/excursion-a-loasis-de-siwa.json`. Modifie **uniquement** `outils/gabarit-programme.py` (et son CSS), régénère `maquettes/programme-siwa.html`, puis lance `outils/verif/tout.sh excursion-a-loasis-de-siwa`. Lance ensuite l'agent `controle-contenu` puis l'agent `qualite` avec les invocations du §6. Si un verdict n'est pas vert, corrige le générateur et recommence ; n'édite jamais le HTML produit ; n'écris aucune phrase, aucun chiffre, aucune image qui ne vienne pas de l'inventaire, de `maquettes/index.html` ou du registre. Termine par un commit qui nomme la section, le défaut corrigé et les verdicts, et colle les trois rapports dans `docs/controles/excursion-a-loasis-de-siwa/`.

### D. Convention de commit

Une ligne de titre en français, à l'indicatif, qui dit ce qui change pour la page (« Programme Siwa : hero borné par l'image réelle, 12 images de la source placées »), un corps qui cite le ticket (`S1`, `O2`…) et les verdicts. Un commit par ticket. Jamais de HTML produit modifié à la main dans un commit.

### E. Ce que ce plan ne couvre pas

- Les pages catégorie, destination, guides : gabarits déjà livrés, hors périmètre.
- La rédaction des contenus manquants (FAQ Siwa, déroulé Siwa réel, 6 séjours absents de l'accueil) : c'est à la cliente ; le plan les rend visibles, il ne les écrit pas.
- Le passage en ligne (publication, redirections, remplacement des fiches `programs`) : une autre phase, avec un autre plan, après validation cliente.
