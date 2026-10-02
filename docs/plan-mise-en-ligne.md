# Mise en ligne de la refonte — le plan

Site : authentiquegypte.com · WordPress, thème Astra, Elementor, Yoast.
Refonte : 58 pages. Agence : Authentique Égypte, contact Mélanie.

---

## Le principe, et pourquoi

**On ne publie pas les brouillons. On remplace le contenu des pages déjà
en ligne.**

Chaque page garde son URL, son identifiant, ses liens entrants, son
ancienneté et son historique Yoast. Rien ne change d'adresse : aucune
redirection à poser, aucun jus perdu, aucun 404 à surveiller. Les 57
brouillons restent des brouillons et servent d'archive de ce qui est
parti.

L'inverse — publier les brouillons et rediriger l'ancien vers le neuf —
créerait 57 nouvelles URL, 57 redirections à maintenir, et ferait
repartir chaque page de zéro aux yeux de Google. On ne le fait pas.

L'appariement est établi et vérifié : **57 sur 57, aucune cible visée
deux fois**. Il croise trois signaux — le préfixe du slug, le gabarit
qui donne le type de contenu, le titre — plus cinq cas tranchés à la
main : l'accueil, dont la cible s'appelle « HOME » ; les deux
Sainte-Catherine, que le site publie en double ; et `mer-rouge`, qui est
à la fois une famille de séjours et un séjour.

| Gabarit | Type visé | Pages |
|---|---|---|
| circuit (famille de séjours) | `pages` | 6 |
| programme (fiche séjour) | `programs` | 14 |
| destination (un lieu) | `pages` | 9 |
| qui part (un profil) | `pages` | 4 |
| guide (article) | `posts` | 22 |
| blog (sommaire) | `pages` | 1 |
| accueil | `pages` | 1 |
| l'agence *(à restaurer)* | `pages` | 1 |

---

## Phase 0 — Ce qui bloque, et qui le lève

### 0.1 Le gabarit des 57 cibles *(moi, automatique)*

Les 57 cibles tournent en gabarit par défaut (38) ou
`elementor_header_footer` (19). **Aucune n'est en Canvas.** Les pages de
la refonte embarquent leur propre en-tête et leur propre pied : sans
bascule en `elementor_canvas`, le thème ajouterait les siens par-dessus
et le visiteur verrait **deux menus et deux pieds de page sur tout le
site**. L'outil de bascule le fait dans la même écriture que le contenu.
C'est le premier point à vérifier après coup.

### 0.2 « L'agence » est à la corbeille *(moi)*

La page `Refonte · L'agence` (#9126) est complète — 165 Ko, 13 sections,
en-tête et pied — mais elle est à la corbeille, sous un gabarit lui-même
à la corbeille. **La navigation pointe vers elle 44 fois**, sous
« L'agence ». En l'état, ce lien serait un 404 sur toutes les pages.

À faire : la restaurer en brouillon, la rattacher à un gabarit vivant,
lui passer la passe visuelle du 29/09 qu'elle n'a pas reçue, l'apparier
à `/qui-sommes-nous/` (#105). La refonte compte alors 58 pages.
L'outil refuse de basculer tant que ce lien n'a pas de destination.

### 0.3 `/sur-mesure/` n'a pas de refonte *(décision de Rémi)*

Elle reçoit **312 liens** depuis les 57 pages : c'est la destination de
chaque bouton « Demander mon devis ». Elle resterait à l'ancienne mise
en page, au bout de tous les parcours de conversion.

Deux voies : la refondre avant la bascule — c'est une page de
formulaire, aucun gabarit existant ne la couvre, il faut la construire —
ou basculer sans et l'assumer pour un temps. `/newsletter/` et
`/mentions-legales/` ne reçoivent aucun lien depuis la refonte : elles
peuvent attendre.

### 0.4 Le push GitHub est refusé *(Rémi)*

Le droit d'écriture a sauté en cours de session : `git fetch` passe,
`git push` répond 403, y compris pour un commit de 7 octets sur une
branche jetable — ce n'est donc ni la taille ni le contenu. Reconnecter
GitHub depuis https://claude.ai/connect-github et vérifier les droits
d'écriture de l'app Claude sur le dépôt.

---

## Phase 1 — Les contrôles

Quatre agents passent le site au crible, chacun sur son terrain. Leurs
constats sont triés BLOQUANT / IMPORTANT / COSMÉTIQUE, corrigés par un
outil par famille de défauts, et re-contrôlés après correction.

| Agent | Ce qu'il cherche |
|---|---|
| back-office | gabarit des cibles, méta Yoast (vides, doublons, longueurs), traces de brouillon dans le contenu, validité et URL du JSON-LD, images à la une, balisage de l'extension de relecture |
| gabarits | l'ossature exacte de chaque famille, section par section : ce qui manque, ce qui est en trop, ce qui est dans le désordre ; sommaires et ancres ; libellés qui varient d'une page à l'autre |
| URLs et liens | les 286 liens de brouillon et leur remplacement, les liens et images morts, le maillage et les pages orphelines, en-tête et pied rigoureusement identiques d'une page à l'autre |
| visuel front | 1440, 768 et 390 px — la tablette n'avait jamais été contrôlée ; cohérence inter-pages mesurée ; contraste ; interactions (FAQ, filtres, « Lire la suite », menu mobile) ; erreurs JavaScript |

Chaque correction suit la règle de la maison : essai hors ligne d'abord
— équilibre des balises, aucun mot perdu, idempotence — puis déploiement,
puis vérification sur le CMS, puis non-régression sur les pages publiées.

### Ce que le contrôle des URL a déjà sorti *(vérifié de mon côté)*

**Bloquant**

- **34 fils d'Ariane JSON-LD dont le dernier maillon désigne une autre
  page.** 22 guides déclarent finir sur `/quand-partir-en-egypte/`,
  8 destinations sur `/voyage-au-caire/`, 4 profils sur
  `/nos-sejours-egypte/desert-egypte/`. Le maillon a été recopié de
  gabarit en gabarit. Google recevrait, pour 34 URL, un fil d'Ariane qui
  se termine sur la même page — en concurrence avec celui que Yoast émet
  déjà au même endroit. 7 pages n'ont aucun fil d'Ariane structuré alors
  qu'elles en affichent un : les 6 circuits et l'accueil.
- **23 notes de chantier visibles du public.** Les 23 pages de guides et
  le blog portent un paragraphe « Contenu repris de \<lien\>, sans
  réécriture : seule la mise en page change. » Cela ne doit pas partir
  en ligne.
- **286 liens vers des brouillons**, sur les 22 guides, dans l'en-tête,
  le pied et le fil d'Ariane. L'outil de bascule les réécrit déjà, sauf
  `?page_id=9126` traité au 0.2.

**Important**

- **L'accueil pèse 3,78 Mo, dont 3,65 Mo d'images encodées en base64
  dans le contenu** — 96 % du poids de la page, pour 22 images. Elles ne
  sont ni indexables dans Google Images, ni mises en cache séparément,
  ni servies en plusieurs largeurs, et Yoast ne peut en tirer aucune
  `og:image`. C'est la page la plus importante du site. À remonter dans
  la médiathèque.
- **246 liens WhatsApp sans `target="_blank"` ni `rel="noopener"`**,
  alors que tous les autres liens externes les ont. Le clic sort du site
  dans l'onglet courant. C'est le lien de conversion principal.
- **Trois liens atterrissent, via une redirection, sur une page sans
  rapport** : « Visa / passeport » tombe sur l'accueil (3 pages),
  « Assouan » tombe sur la page mère des séjours, et un séjour disparu,
  Dakhla, traîne dans le JSON-LD de 4 pages de profil.
- **`/mont-sinai/` est quasi orpheline** : un seul lien entrant, et elle
  est absente du menu « Destinations » qui liste ses huit sœurs.
- **L'accueil a un en-tête et un pied à part** : logo en base64 au lieu
  du fichier de la médiathèque, bouton du menu déplacé dans l'ordre de
  tabulation, 14 sous-libellés de menu différents, et « Voyage en solo »
  contre « Voyage solo » — qui est une ancre de maillage.
- **Huit pages se lient à elles-mêmes** dans leur corps.
- **L'ancre `#rdv` visée depuis l'accueil n'existe pas** sur
  `/sur-mesure/`.
- **Deux navigations coexisteront** : les pages non refondues gardent le
  menu Elementor actuel, qui contient un séjour disparu, un lien mort
  et aucune des neuf destinations.

**Ce qui est sain, et qui compte** : les 57 cibles répondent toutes 200,
les 404 URL de médias répondent toutes 200, les 253 `srcset` sont
cohérents, les 388 ancres internes trouvent toutes leur destination,
aucune page n'est orpheline, aucun lien relatif, aucune chaîne de
redirection, et Yoast fournit bien le canonical attendu sans concurrent
dans le contenu.

---

## Phase 2 — Le contenu, et l'accord de la cliente

### 2.1 Les 72 fils de relecture

326 fils, 254 clos, 72 ouverts, **0 sans réponse**. Sur 17 fils
vérifiables testés contre le contenu actuel, **15 étaient déjà traités**.
Ils restent ouverts pour une seule raison : Mélanie ne voit pas mes
réponses, l'extension 1.2.1 n'étant pas installée. Le rôle Relecteur
n'a pas de back-office, donc le badge du bureau d'administration ne lui
est jamais apparu.

À faire : vérifier les 72 un par un contre le contenu déployé, clore
ceux qui sont faits avec la preuve, et ne laisser ouverts que ceux qui
attendent vraiment quelque chose d'elle.

### 2.2 Ce qui attend vraiment Mélanie

- **Les photos** — 27 fils. Des lieux sans image, des photos qui ne
  correspondent pas, des photos à remplacer.
- **Quatre séjours sans prix**, nulle part sur le site.
- **Le logo au fond transparent** — celui en service est entièrement
  doré, le bateau et l'eau ont été détourés.
- **Le type de bateau par séjour**, qu'elle demande elle-même d'afficher.
- **Les hébergements et repas** des 13 journées encore muettes.

### 2.3 L'extension 1.2.1

Elle attend d'être téléversée. Elle apporte le badge rouge de non-lus
visible pour le rôle Relecteur, les épingles marquées, un bandeau de
rappel entre pages, et des courriels groupés avec quinze minutes de
grâce. **Sans l'accord écrit de Mélanie, on ne bascule pas.**

---

## Phase 3 — Le relevé d'avant

Aucune URL ne change, donc rien ne devrait bouger côté référencement —
mais il faut pouvoir le prouver. À relever et dater **avant** :

- les 57 titres et descriptions Yoast tels qu'ils sont ;
- le sitemap XML et le `robots.txt` ;
- les positions, les pages indexées et les 404 dans la Search Console ;
- les Core Web Vitals, le poids et le temps de rendu d'une page de
  chaque gabarit ;
- les ancres internes (`#t-vue`, `#t-jpj`, `#t-faq`…) : vérifier
  qu'aucune n'a disparu du nouveau balisage, des liens entrants
  extérieurs peuvent les viser.

Les mêmes mesures à J+1 et à J+7.

---

## Phase 4 — La bascule

Il n'y a pas de préproduction : une page basculée est publique. On
réduit le risque en deux temps.

**Temps 1 — une page témoin par gabarit**, les moins stratégiques :
`/voyage-a-fayoum/`, `/programs/excursion-a-loasis-de-fayoum/`,
`/nos-sejours-egypte/mer-rouge/`, `/voyage-pmr-en-egypte/`,
`/comment-shabiller-en-egypte/`. Puis contrôle **sur le site public**,
pour de vrai : en-tête unique, pied unique, images chargées, liens qui
répondent, rendu aux trois largeurs.

**Temps 2 — le reste**, l'accueil et le blog en dernier.

Entre les deux : vidage des caches et purge du CDN, sans quoi on
contrôle une page d'hier.

### Le déroulé, dans cet ordre et jamais autrement

```
./outils/mise-en-ligne.py --essai         # dit, n'écrit rien
./outils/mise-en-ligne.py --sauvegarder   # le filet
./outils/mise-en-ligne.py --appliquer     # bascule
```

`--appliquer` refuse de démarrer sans sauvegarde du jour, et refuse tant
qu'un lien de brouillon n'a pas de destination.

Fenêtre : heure creuse, et pas un vendredi. Doubler d'une sauvegarde
serveur complète (UpdraftPlus ou l'export de l'hébergeur) le jour même :
la sauvegarde de l'outil couvre exactement ce que la bascule modifie, et
rien d'autre — ni menus, ni réglages du thème, ni médiathèque.

---

## Phase 5 — Après

- Contrôle front des 58 URL publiques, aux trois largeurs.
- Caches vidés, CDN purgé, sitemap soumis, indexation demandée sur les
  pages clés.
- Search Console à J+1 et J+7 : 404, pages exclues, positions.
- Les menus WordPress : vérifier qu'ils pointent toujours là où il faut,
  la refonte embarque sa propre navigation mais le thème garde la sienne
  pour les pages non refondues.

### Revenir en arrière

```
./outils/mise-en-ligne.py --revenir
```

Reprend la sauvegarde la plus récente et remet, pour chaque cible, son
contenu et son gabarit d'avant. Le titre, le slug et les méta Yoast
n'ayant jamais été touchés, ils n'ont rien à retrouver. Dix cibles
tirées au hasard ont été comparées au site : identiques au bit près.

---

## Qui fait quoi

| | |
|---|---|
| **Moi** | restaurer #9126, dépouiller les quatre rapports et corriger, trier les 72 fils, relever l'état d'avant, préparer et exécuter la bascule, contrôler après |
| **Rémi** | reconnecter GitHub, trancher le sort de `/sur-mesure/`, téléverser l'extension 1.2.1, lancer la sauvegarde serveur, donner le feu vert de la fenêtre |
| **Mélanie** | les photos, les quatre prix, le logo transparent, le type de bateau, les hébergements et repas manquants, et son accord écrit |
