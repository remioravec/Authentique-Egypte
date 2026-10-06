# Décisions de contenu à prendre — Authentique Égypte

Relevé du 5 octobre 2026, sur le site en ligne. Chaque point a été vérifié
page par page ; les chiffres viennent du contenu réellement servi, pas d'une
estimation.

Ce document ne liste que ce qui **demande une décision de Mélanie**. Tout ce
qui pouvait être corrigé sans arbitrage l'a été le 5 octobre (filtre à
facettes réparé, avertissement de chantier retiré, degrés Celsius, accents,
textes alternatifs repris de la médiathèque quand elle en avait).

---

## 1 · Deux programmes affichent le contenu d'un autre séjour

**`/programs/mer-rouge/` — « Pyramides, croisière et mer rouge en famille »**

La page vend un séjour famille. Elle affiche :

- un déroulé jour par jour **identique mot pour mot** à celui de
  `/programs/pyramides-et-croisiere-sur-le-nil/` ;
- une check-list d'équipement de **plongée** : « Snorkeling : masque ajusté,
  tuba confortable, palmes adaptées », « Plongée : selon certification +
  ordinateur et parachute de palier », « Hiver : 5 mm recommandé » ;
- une FAQ de plongée : « Snorkeling ou plongée bouteille ? », « Quel niveau /
  encadrement prévoir ? », « Comment respecter les récifs ? » ;
- une galerie montrant l'oasis de Siwa et le mont Sinaï ;
- un fil d'Ariane qui annonce « Mer rouge et plongée ».

**À décider :** quel déroulé va sur cette page, et où part la valise de
plongée (page mer Rouge dédiée, ou nulle part).

**`/programs/croisiere-sur-le-lac-nasser/`**

Le titre et le texte annoncent une croisière sur le lac Nasser, avec Abou
Simbel et Wadi el-Seboua. Le déroulé fait dix jours, se passe en maison
d'hôtes et en lodge, comprend une « excursion dans le désert et visite d'une
oasis secrète », et **ne comporte aucune navigation**. Wadi el-Seboua n'y est
jamais visité. Le premier titre de jour est « Désert et oasis en Égypte —
Arrivée à Assouan », c'est-à-dire celui d'un autre séjour.

**À décider :** remettre le déroulé de la croisière, ou changer la promesse
de la page.

---

## 2 · Les durées annoncées ne correspondent pas aux déroulés

Mesuré sur les treize programmes. Dix sont en écart.

| Programme | Durée affichée | Déroulé réel | Prix |
|---|---|---|---|
| Pyramides, Louxor et mer rouge en famille | 12 jours | J1 → J8 | 1 485 € |
| Croisière sur le lac Nasser | 4 jours minimum | J1 → J10 | 1 595 € |
| Mer rouge | 9 jours minimum | J1 → J8 | 1 485 € |
| Le Caire et croisière sur un bateau à voile | 3 jours | J1 → J8 | 1 895 € |
| Roadtrip en Égypte | 5 jours minimum | J1 → J9 | 1 635 € |
| Pyramides et croisière sur le Nil | 6 jours minimum | J1 → J8 | 1 195 € |
| Excursion à l'oasis de Siwa | 3 jours minimum | J1 seulement | 595 € |
| Campement au cœur du mont Moïse | 2 jours | J1 seulement | 290 € |
| Excursion à l'oasis de Fayoum | 1 jour minimum | J1 → J2 | 185 € |
| Excursion dans le désert blanc | 2 jours minimum | J1 → J3 | 415 € |

Deux séjours partagent en plus le même prix de 1 485 € et le même déroulé de
huit jours, en annonçant l'un 9 jours et l'autre 12.

**À décider :** pour chaque séjour, quelle durée fait foi. Une fois tranché,
la durée sera reprise automatiquement partout — panneau, cartes, filtres.

---

## 3 · Deux pages pour un même séjour

`/programs/sainte-catherine/` et
`/programs/lever-du-soleil-monastere-et-nuit-a-sainte-catherine/` ont le même
titre, la même description, le même texte et le même prix (320 €). Chacune se
déclare canonique d'elle-même, et les deux sont listées côte à côte sur la
page des séjours.

**À décider :** laquelle garde l'adresse, l'autre étant redirigée vers elle.

---

## 4 · Le montant du visa n'est pas le même d'une page à l'autre

- Trente-deux pages, dans leur FAQ : « il peut être obtenu à l'arrivée
  (25 € en espèces ou CB) ».
- `/passeport-egypte/` : « 25 dollars américains » pour l'e-visa, « 30 USD »
  sur place.

Monnaie et montant diffèrent. C'est une information que le voyageur prépare
avant de partir.

**À décider :** le montant et la monnaie exacts, à la date du jour.

---

## 5 · Les périodes conseillées se contredisent dans une même page

| Page | Section « Quand partir ? » | FAQ de la même page |
|---|---|---|
| `/voyage-a-louxor/` | croisière sur le Nil : octobre à avril | de novembre à mars |
| `/voyage-au-caire/` | séjour au Caire : novembre à mars | octobre à avril |

Et pour la famille : la FAQ de `/voyage-en-famille-en-egypte/` dit « octobre à
avril », le guide « Quand partir » et les programmes disent « avril, octobre
et décembre ».

**À décider :** une période par destination, reprise partout.

---

## 6 · Seize photos sans texte alternatif

Leur texte alternatif est le nom du fichier (« 6213959105_d7ee5e6528_b »,
« dmitrii-zhodzishskii-5aEHOQrb2Qk-unsplash »…). La médiathèque n'en a pas
non plus. Ce texte est lu à voix haute par les lecteurs d'écran, et il
s'affiche quand l'image ne charge pas.

Deux alt existants sont trompeurs : la carte du séjour famille Nil porte
« Oasis de siwa », la carte « Voyage solo » porte « Dahabeya ».

La liste des seize se trouve dans `docs/alt-a-decrire.json`.

**À décider :** une phrase courte par photo, décrivant ce qu'on y voit.

---

## 7 · Un guide dont l'adresse ne correspond pas au contenu

`/guide-complet-des-formalites-pour-un-voyage-en-egypte-pour-un-francophone/`
annonce un guide des formalités. Son titre de recherche vaut littéralement
« /voyage-egypte-en-famille », et son contenu est un troisième article sur le
voyage en famille, après `/voyager-en-egypte-en-famille/` et
`/voyage-en-famille-en-egypte/`.

**À décider :** garder l'adresse et remettre un contenu de formalités, ou
rediriger vers l'un des deux articles famille.

---

## Ce qui ne dépend pas de Mélanie mais reste bloqué

Les titres et descriptions de recherche passent par Yoast, qui **n'accepte
aucune écriture par l'API** : la requête rend 200 et ne garde rien, vérifié
deux fois. Quarante titres et descriptions sont prêts dans
`docs/yoast-propose.md` et attendent soit une saisie au back-office, soit une
dizaine de lignes de code déclarant ces deux champs à l'API.

Cela concerne aussi neuf guides encore titrés « [Guide 2025] » alors qu'on
est en octobre 2026, et six pages sans description.

---

## Mise à jour du 6 octobre — ces erreurs sont antérieures à la refonte

En cherchant à refondre `/programs/decouverte-de-la-nubie/`, le quatorzième
programme, j'ai trouvé un troisième cas, puis un quatrième. Et surtout : la
sauvegarde du 2 octobre, qui contient l'état exact des pages **avant** la
bascule, montre que ces déroulés étaient déjà là. La refonte a repris
fidèlement le contenu existant ; elle n'a rien interverti.

**`/programs/decouverte-de-la-nubie/` — « Rencontres Nubiennes », 895 €**

La page promet « les temples millénaires d'Abou Simbel », une navigation sur
le Nil et « la richesse culturelle de cette région aux traditions
préservées ». Son déroulé, en dix journées, va du Caire à Louxor, puis Edfou
et Kom Ombo, et revient au Caire. Ni Assouan, ni Abou Simbel, ni la Nubie, ni
aucune navigation. La carte annonce par ailleurs « 5 jours minimum ».

C'est pour cela que cette page n'a pas été refondue avec Alexandrie et le
Désert noir le 6 octobre : son brouillon n'a pas de jour-par-jour, et celui de
la page en ligne ne peut pas servir, puisqu'il décrit un autre voyage.

**`/programs/excursion-a-loasis-de-siwa/` — « Voyage à l'Oasis de Siwa »**

La vue d'ensemble, la carte (Le Caire → Siwa) et les inclus parlent bien de
Siwa. Le jour-par-jour, lui, s'ouvre sur « Le Caire - Oasis de Siwa, Jour 1 »
et décrit un départ « de votre hôtel à Sharm el-Sheikh ou Dahab » vers
Sainte-Catherine, puis l'ascension nocturne du mont Moïse, le lever du soleil
au sommet et la visite du monastère. C'est, mot pour mot, le déroulé de
`/programs/sainte-catherine/`. La sauvegarde du 2 octobre montre le même
texte sur l'ancienne page.

**Ce qu'il faut, et rien d'autre**

Trois déroulés jour par jour, écrits par l'agence :

1. « Découverte de la Nubie » — ce qu'on fait vraiment, jour par jour, et en
   combien de jours (la carte dit 5, le déroulé affiché en dit 10) ;
2. « Voyage à l'Oasis de Siwa » — le vrai déroulé, celui de l'oasis ;
3. « Pyramides, croisière et mer rouge en famille » — ce qui la distingue de
   « Pyramides et croisière sur le Nil », dont elle reprend le déroulé mot
   pour mot.

Tant qu'ils manquent, deux choses n'ont **pas** été touchées, pour ne pas
propager l'erreur : la durée affichée de `/programs/mer-rouge/` (9 jours) et
celle de la croisière sur le lac Nasser (4 jours), toutes deux contredites par
un déroulé qui n'est pas le leur.
