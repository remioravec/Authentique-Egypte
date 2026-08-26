# Retours de Mélanie sur les maquettes

Relevé de l'extension **AE Commentaires**, le 26/08/2026. **76 retours, tous ouverts.**

Chaque retour est resitué dans la maquette : le type d'élément visé, la carte ou la section qui le porte, et le texte sur lequel Mélanie a cliqué. 75 des 76 sélecteurs se retrouvent tels quels dans les fichiers du dépôt.

## Les images : il n'y en a aucune

**Aucun fichier n'est joint.** Vérifié des deux côtés : les 76 commentaires ont un champ image vide, et la médiathèque du site ne contient aucun téléversement depuis le 30/11/2025.

Les 7 retours qui parlent d'image la demandent **en toutes lettres** — « ajouter photo », « changer la photo ». Mélanie a marqué les emplacements, elle n'a pas fourni les visuels.

Le mécanisme d'envoi fonctionne : testé de bout en bout, collage d'une capture, bouton « joindre », glisser-déposer, jusqu'à 10 Mo, et l'identifiant de l'image part bien avec le commentaire.

### Les 7 emplacements en attente d'un visuel

| # | Page | Demande | Où exactement | Image en place |
|---|---|---|---|---|
| 1 | Accueil | changer l'image | Pyramides, croisière et mer Rouge | `Destination-033.jpg` |
| 2 | Catégorie — Voyage dans le désert | ajouter photo | Grande traversée des oasis en 4x4 | `Desert-blanc-dEgypte-2.png` |
| 3 | Catégorie — Voyage dans le désert | ajouter photo | Oasis de Fayoum et vallée des Baleines | `Voyage-sur-mesure-a-Fayoum-en-Egypte.png` |
| 4 | Catégorie — Voyage dans le désert | changer la photo | Le désert se combine bien | `gonzalo-pedroviejo-gomez-_Ex6joK1ebQ-unsplash.jpg` |
| 5 | Catégorie — Voyage dans le désert | ajouter photo | Oasis de Dakhla et de Kharga | `Oasis-de-Dakhla-4.png` |
| 6 | Catégorie — Voyage dans le désert | changer la photo | Le désert se combine bien | `peggy-anke-YxpoB3bvlZQ-unsplash.jpg` |
| 7 | Devis — Demande de devis | changer cette photo | Ce qui vous attire en Égypte | `peggy-anke-YxpoB3bvlZQ-unsplash.jpg` |

**Ce qu'il faut demander à Mélanie :** les 7 fichiers, numérotés comme ce tableau. Sans eux ces emplacements restent en l'état — c'est le seul point des 76 retours qui soit complètement bloqué.

## Tous les retours, page par page

### Accueil

1 retours · <https://authentiquegypte.com/?page_id=7643> · `maquettes/index.html`

**1. changer l'image**

- Où : image — dans « Pyramides, croisière et mer Rouge »
- Fichier actuel : `Destination-033.jpg` — alt « Pyramides de Gizeh à dos de dromadaire »
- <sub>`#liste > article:nth-of-type(4) > div:nth-of-type(1) > img:nth-of-type(1)`</sub>

### Catégorie — Voyage dans le désert

21 retours · <https://authentiquegypte.com/?page_id=7644> · `maquettes/categorie-desert.html`

**1. juste mettre écolodge**

- Où : fragment de texte — dans « Oasis de Siwa — la dernière oasis berbère »
- Texte cliqué : « Écolodge en kershef »
- <sub>`#liste > article:nth-of-type(1) > div:nth-of-type(2) > div:nth-of-type(1) > span:nth-of-type(2)`</sub>

**2. enlever cette partie**

- Où : bloc — dans « La route, avant le programme »
- Texte cliqué : « Ce qui décide vraiment La route, avant le programme Siwa, c’est dix heures de désert depuis Le Caire. Fayoum, un »
- **Précision de Mélanie** : remplacer par un lien qui renvoie sur une demande de devis par exemple
- <sub>`body > main:nth-of-type(1) > section:nth-of-type(3) > div:nth-of-type(1)`</sub>

**3. que a fayoum oui, pour le reste il faut des autorisations ainsi nous proposons dans des eco lodges et hotels uniquement**

- Où : paragraphe — dans « Dort-on vraiment sous la tente ? »
- Texte cliqué : « Dans le désert Blanc, le désert Noir et sur la traversée des oasis, oui : bivouac monté par l’équipe, matelas, duvets, r »
- <sub>`#devis > div:nth-of-type(1) > div:nth-of-type(1) > details:nth-of-type(3) > div:nth-of-type(1) > p:nth-of-type(1)`</sub>

**4. changer la phrase**

- Où : lien — dans « Bivouac, écolodge ou aller-retour dans la journée ? »
- Texte cliqué : « décrivez-nous votre groupe sur WhatsApp »
- <sub>`body > main:nth-of-type(1) > section:nth-of-type(4) > div:nth-of-type(1) > p:nth-of-type(3) > a:nth-of-type(1)`</sub>

**5. a ajouter**

- Où : fragment de texte — dans « Oasis de Siwa — la dernière oasis berbère »
- Texte cliqué : « à valider par l’équipe »
- <sub>`body > main:nth-of-type(1) > section:nth-of-type(2) > div:nth-of-type(1) > p:nth-of-type(2) > span:nth-of-type(1)`</sub>

**6. ajouter photo**

- Où : image — dans « Grande traversée des oasis en 4x4 »
- Fichier actuel : `Desert-blanc-dEgypte-2.png` — alt « Piste de sable dans le désert occidental »
- <sub>`#liste > article:nth-of-type(5) > div:nth-of-type(1) > img:nth-of-type(1)`</sub>

**7. ajouter photo**

- Où : image — dans « Oasis de Fayoum et vallée des Baleines »
- Fichier actuel : `Voyage-sur-mesure-a-Fayoum-en-Egypte.png` — alt « Falaises et lac Qarun dans l'oasis de Fayoum »
- <sub>`#liste > article:nth-of-type(3) > div:nth-of-type(1) > img:nth-of-type(1)`</sub>

**8. pas possible en PMR enlever totalement**

- Où : entête de colonne — dans « Bivouac, écolodge ou aller-retour dans la journée ? »
- Texte cliqué : « Accessibilité PMR »
- <sub>`body > main:nth-of-type(1) > section:nth-of-type(4) > div:nth-of-type(1) > table:nth-of-type(1) > tbody:nth-of-type(1) > tr:nth-of-type(7) > th:nth-of-type(1)`</sub>

**9. changer la photo**

- Où : image — dans « Le désert se combine bien »
- Fichier actuel : `gonzalo-pedroviejo-gomez-_Ex6joK1ebQ-unsplash.jpg` — alt « Montagnes du Sinaï »
- <sub>`body > main:nth-of-type(1) > section:nth-of-type(6) > div:nth-of-type(1) > div:nth-of-type(1) > a:nth-of-type(4) > div:nth-of-type(1) > img:nth-of-type(1)`</sub>

**10. a enlever**

- Où : fragment de texte — dans « Nos séjours »
- Texte cliqué : « Agence locale · Le Caire, Égypte »
- <sub>`body > footer:nth-of-type(1) > div:nth-of-type(1) > div:nth-of-type(2) > span:nth-of-type(2)`</sub>

**11. enlever car Dakhla ne va pas bien en terme de sécurité en ce moment**

- Où : entête de colonne — dans « Bivouac, écolodge ou aller-retour dans la journée ? »
- Texte cliqué : « Écolodge »
- <sub>`body > main:nth-of-type(1) > section:nth-of-type(4) > div:nth-of-type(1) > table:nth-of-type(1) > thead:nth-of-type(1) > tr:nth-of-type(1) > th:nth-of-type(4)`</sub>

**12. le budget a augmenté 590 euros par personne tout inclus**

- Où : cellule — dans « Bivouac, écolodge ou aller-retour dans la journée ? »
- Texte cliqué : « 460 € »
- <sub>`body > main:nth-of-type(1) > section:nth-of-type(4) > div:nth-of-type(1) > table:nth-of-type(1) > tbody:nth-of-type(1) > tr:nth-of-type(8) > td:nth-of-type(2)`</sub>

**13. ajouter photo**

- Où : image — dans « Oasis de Dakhla et de Kharga »
- Fichier actuel : `Oasis-de-Dakhla-4.png` — alt « Palmeraie de l'oasis de Dakhla »
- <sub>`#liste > article:nth-of-type(4) > div:nth-of-type(1) > img:nth-of-type(1)`</sub>

**14. attention au fond du logo**

- Où : image — dans « Nos séjours »
- Fichier actuel : `cropped-Screenshot_20231015_082741_Instagram-removebg-preview-1.webp` — alt « Authentique Égypte »
- <sub>`body > footer:nth-of-type(1) > div:nth-of-type(1) > div:nth-of-type(1) > div:nth-of-type(1) > img:nth-of-type(1)`</sub>

**15. ils dorment a chaque fois dans des guest houses hotels SAUF à fayoum ils peuvent dormir dans un campement**

- Où : entête de colonne — dans « Bivouac, écolodge ou aller-retour dans la journée ? »
- Texte cliqué : « Où l’on dort »
- <sub>`body > main:nth-of-type(1) > section:nth-of-type(4) > div:nth-of-type(1) > table:nth-of-type(1) > tbody:nth-of-type(1) > tr:nth-of-type(3) > th:nth-of-type(1)`</sub>

**16. pas de bivouac juste écrire Bahareya**

- Où : entête de colonne — dans « Bivouac, écolodge ou aller-retour dans la journée ? »
- Texte cliqué : « Bivouac »
- <sub>`body > main:nth-of-type(1) > section:nth-of-type(4) > div:nth-of-type(1) > table:nth-of-type(1) > thead:nth-of-type(1) > tr:nth-of-type(1) > th:nth-of-type(3)`</sub>

**17. a mettre la couleur de fond en évidence**

- Où : lien — dans « Voyage dans le désert en Égypte »
- Texte cliqué : « Obtenir mon devis »
- <sub>`body > header:nth-of-type(1) > div:nth-of-type(1) > nav:nth-of-type(1) > a:nth-of-type(2)`</sub>

**18. enlever le mot désert**

- Où : lien — dans « Ce qu'on nous demande le plus »
- Texte cliqué : « Demander mon devis désert »
- <sub>`#devis > div:nth-of-type(1) > div:nth-of-type(2) > div:nth-of-type(2) > a:nth-of-type(1)`</sub>

**19. changer la photo**

- Où : image — dans « Le désert se combine bien »
- Fichier actuel : `peggy-anke-YxpoB3bvlZQ-unsplash.jpg` — alt « Littoral de la mer Rouge »
- <sub>`body > main:nth-of-type(1) > section:nth-of-type(6) > div:nth-of-type(1) > div:nth-of-type(1) > a:nth-of-type(3) > div:nth-of-type(1) > img:nth-of-type(1)`</sub>

**20. attention au fond du logo**

- Où : image — dans « Voyage dans le désert en Égypte »
- Fichier actuel : `cropped-Screenshot_20231015_082741_Instagram-removebg-preview-1.webp` — alt « Authentique Égypte »
- <sub>`body > header:nth-of-type(1) > div:nth-of-type(1) > a:nth-of-type(1) > img:nth-of-type(1)`</sub>

**21. 48h* hors week end**

- Où : gras — dans « (non retrouvé dans la maquette) »
- Texte cliqué : « Réponse sous 24 h »
- <sub>`body > div:nth-of-type(2) > div:nth-of-type(1) > span:nth-of-type(1) > strong:nth-of-type(1)`</sub>

### Guide — Quand partir en Égypte

23 retours · <https://authentiquegypte.com/?page_id=7646> · `maquettes/article-quand-partir.html`

**1. j'aimerai que ces blog descendent lorsque nous défilons la page**

- Où : bloc — dans « Votre voyage, à la bonne saison »
- Texte cliqué : « Votre voyage, à la bonne saison Donnez-nous vos dates : nous vous disons ce qui est confortable à cette périod »
- <sub>`body > main:nth-of-type(1) > div:nth-of-type(1) > div:nth-of-type(1) > aside:nth-of-type(1) > div:nth-of-type(1) > div:nth-of-type(1)`</sub>

**2. avril c'est ok**

- Où : b — dans « Le calendrier mois par mois »
- Texte cliqué : « fin mars »
- <sub>`body > main:nth-of-type(1) > div:nth-of-type(1) > div:nth-of-type(1) > article:nth-of-type(1) > figure:nth-of-type(6) > figcaption:nth-of-type(1) > b:nth-of-type(1)`</sub>

**3. a enlever**

- Où : fragment de texte — dans « Nos séjours »
- Texte cliqué : « Agence locale · Le Caire, Égypte »
- <sub>`body > footer:nth-of-type(1) > div:nth-of-type(1) > div:nth-of-type(2) > span:nth-of-type(2)`</sub>

**4. enlever cette phrase**

- Où : paragraphe — dans « Le calendrier mois par mois »
- Texte cliqué : « Chaque ligne renvoie vers les séjours concernés : c’est là que se joue le passage du guide à la réservation. »
- <sub>`body > main:nth-of-type(1) > div:nth-of-type(1) > div:nth-of-type(1) > article:nth-of-type(1) > p:nth-of-type(3)`</sub>

**5. et février mais février et décembre pas de mer rouge**

- Où : paragraphe — dans « Quelle période privilégier pour un voyage en famille ? »
- Texte cliqué : « Avril, octobre et décembre correspondent aux vacances scolaires et offrent de bonnes conditions climatiques, mais il fau »
- <sub>`body > main:nth-of-type(1) > div:nth-of-type(1) > div:nth-of-type(1) > article:nth-of-type(1) > div:nth-of-type(7) > details:nth-of-type(4) > div:nth-of-type(1) > p:nth-of-type(1)`</sub>

**6. supprimer totalement ce tableau**

- Où : entête de colonne — dans « Le calendrier mois par mois »
- Texte cliqué : « Profil voyageur »
- <sub>`body > main:nth-of-type(1) > div:nth-of-type(1) > div:nth-of-type(1) > article:nth-of-type(1) > table:nth-of-type(3) > thead:nth-of-type(1) > tr:nth-of-type(1) > th:nth-of-type(1)`</sub>

**7. enlever cette phrase**

- Où : figcaption — dans « Le calendrier mois par mois »
- Texte cliqué : « D’octobre à avril, les visites se font sans contrainte d’horaire — c’est la fenêtre de la croisière. »
- <sub>`body > main:nth-of-type(1) > div:nth-of-type(1) > div:nth-of-type(1) > article:nth-of-type(1) > figure:nth-of-type(2) > figcaption:nth-of-type(1)`</sub>

**8. a ajouter**

- Où : fragment de texte — dans « Le calendrier mois par mois »
- Texte cliqué : « Source et date des normales à préciser »
- <sub>`body > main:nth-of-type(1) > div:nth-of-type(1) > div:nth-of-type(1) > article:nth-of-type(1) > p:nth-of-type(1) > span:nth-of-type(1)`</sub>

**9. remplacer le mot**

- Où : fragment de texte — dans « Le calendrier mois par mois »
- Texte cliqué : « Caniculaire »
- <sub>`body > main:nth-of-type(1) > div:nth-of-type(1) > div:nth-of-type(1) > article:nth-of-type(1) > div:nth-of-type(3) > span:nth-of-type(4)`</sub>

**10. octobre à avril**

- Où : fragment de texte — dans « Le calendrier mois par mois »
- Texte cliqué : « Novembre à mars »
- <sub>`body > main:nth-of-type(1) > div:nth-of-type(1) > div:nth-of-type(1) > article:nth-of-type(1) > table:nth-of-type(2) > tbody:nth-of-type(1) > tr:nth-of-type(2) > td:nth-of-type(1) > span:nth-of-type(1)`</sub>

**11. juste marquer qu'il fait chaud**

- Où : fragment de texte — dans « Le calendrier mois par mois »
- Texte cliqué : « Caniculaire, mer Rouge possible »
- <sub>`body > main:nth-of-type(1) > div:nth-of-type(1) > div:nth-of-type(1) > article:nth-of-type(1) > table:nth-of-type(1) > tbody:nth-of-type(1) > tr:nth-of-type(8) > td:nth-of-type(2) > span:nth-of-type(1)`</sub>

**12. a supprimer**

- Où : figcaption — dans « Le calendrier mois par mois »
- Texte cliqué : « En ville, la fenêtre est la plus large du pays : novembre à mars, sans la chaleur qui rend les sites pénibles à midi. »
- <sub>`body > main:nth-of-type(1) > div:nth-of-type(1) > div:nth-of-type(1) > article:nth-of-type(1) > figure:nth-of-type(4) > figcaption:nth-of-type(1)`</sub>

**13. juste marquer qu'il fait chaud**

- Où : fragment de texte — dans « Le calendrier mois par mois »
- Texte cliqué : « Caniculaire, éviter circuits »
- <sub>`body > main:nth-of-type(1) > div:nth-of-type(1) > div:nth-of-type(1) > article:nth-of-type(1) > table:nth-of-type(1) > tbody:nth-of-type(1) > tr:nth-of-type(7) > td:nth-of-type(2) > span:nth-of-type(1)`</sub>

**14. fond du logo**

- Où : image — dans « Quand partir en Égypte ? Météo et périodes idéales selon vos envies »
- Fichier actuel : `cropped-Screenshot_20231015_082741_Instagram-removebg-preview-1.webp` — alt « Authentique Égypte »
- <sub>`body > header:nth-of-type(1) > div:nth-of-type(1) > a:nth-of-type(1) > img:nth-of-type(1)`</sub>

**15. pas février mais mars**

- Où : paragraphe — dans « Quand éviter la foule ? »
- Texte cliqué : « Janvier, février et novembre sont les mois les plus calmes, hors vacances scolaires. »
- <sub>`body > main:nth-of-type(1) > div:nth-of-type(1) > div:nth-of-type(1) > article:nth-of-type(1) > div:nth-of-type(7) > details:nth-of-type(2) > div:nth-of-type(1) > p:nth-of-type(1)`</sub>

**16. et février sauf si mer rouge**

- Où : fragment de texte — dans « Le calendrier mois par mois »
- Texte cliqué : « Avril, octobre, décembre »
- <sub>`body > main:nth-of-type(1) > div:nth-of-type(1) > div:nth-of-type(1) > article:nth-of-type(1) > table:nth-of-type(2) > tbody:nth-of-type(1) > tr:nth-of-type(5) > td:nth-of-type(1) > span:nth-of-type(1)`</sub>

**17. attention au logo**

- Où : image — dans « Nos séjours »
- Fichier actuel : `cropped-Screenshot_20231015_082741_Instagram-removebg-preview-1.webp` — alt « Authentique Égypte »
- <sub>`body > footer:nth-of-type(1) > div:nth-of-type(1) > div:nth-of-type(1) > div:nth-of-type(1) > img:nth-of-type(1)`</sub>

**18. a mettre en couleur jaune foncé**

- Où : lien — dans « Quand partir en Égypte ? Météo et périodes idéales selon vos envies »
- Texte cliqué : « Obtenir mon devis »
- <sub>`body > header:nth-of-type(1) > div:nth-of-type(1) > nav:nth-of-type(1) > a:nth-of-type(3)`</sub>

**19. nous pouvons adapter les visites si ils souhaitent visiter Le Caire, ou louxor ou aswan**

- Où : paragraphe — dans « Est-ce possible de voyager en été ? »
- Texte cliqué : « Oui, mais il vaut mieux privilégier la mer Rouge : la plongée est possible toute l’année avec une combinaison, tandis qu »
- <sub>`body > main:nth-of-type(1) > div:nth-of-type(1) > div:nth-of-type(1) > article:nth-of-type(1) > div:nth-of-type(7) > details:nth-of-type(3) > div:nth-of-type(1) > p:nth-of-type(1)`</sub>

**20. non en soit octobre mai**

- Où : lien — dans « Le calendrier mois par mois »
- Texte cliqué : « Le CaireNovembre à mars »
- <sub>`body > main:nth-of-type(1) > div:nth-of-type(1) > div:nth-of-type(1) > article:nth-of-type(1) > div:nth-of-type(4) > a:nth-of-type(1)`</sub>

**21. enlever agence locale )) et mettre la date de la mise à jour**

- Où : fragment de texte — dans « Quand partir en Égypte ? Météo et périodes idéales selon vos envies »
- Texte cliqué : « L’équipe d’Authentique ÉgypteAgence locale basée au Caire · Mis à jour le JJ mois 2026 »
- <sub>`body > main:nth-of-type(1) > section:nth-of-type(1) > div:nth-of-type(2) > div:nth-of-type(1) > span:nth-of-type(2)`</sub>

**22. non ce sont les mois de janvier mars mai et novembre**

- Où : b — dans « Le calendrier mois par mois »
- Texte cliqué : « janvier, février et novembre »
- <sub>`#reponse > p:nth-of-type(2) > b:nth-of-type(1)`</sub>

**23. a la place remplacer par un texte qui redirige a. une demande de devis**

- Où : paragraphe — dans « Le calendrier mois par mois »
- Texte cliqué : « Un itinéraire classique combine Le Caire, une croisière sur le Nil jusqu’à Louxor et Assouan, et 2 à 3 jours de détente »
- <sub>`body > main:nth-of-type(1) > div:nth-of-type(1) > div:nth-of-type(1) > article:nth-of-type(1) > div:nth-of-type(6) > p:nth-of-type(1)`</sub>

### Agence — Qui sommes-nous

6 retours · <https://authentiquegypte.com/?page_id=7657> · `maquettes/qui-sommes-nous.html`

**1. les guides sont free lances, et il y a des intermédiaires, il faudrait supprimer totalement ces 3 parties**

- Où : paragraphe — dans « « Agence locale », concrètement »
- Texte cliqué : « Ce sont des égyptologues diplômés, francophones, avec qui nous travaillons à l’année. Ils ne sont pas attribué »
- <sub>`body > main:nth-of-type(1) > section:nth-of-type(2) > div:nth-of-type(1) > div:nth-of-type(1) > div:nth-of-type(2) > p:nth-of-type(1)`</sub>

**2. Je pense que la page serait à modifier totalement en reprenant les informations déjà données dans le qui sommes nous de l'ancienne version du site**

- Où : bloc — dans « Une agence au Caire, pas un catalogue en ligne »
- Texte cliqué : « Accueil Qui sommes-nous Une agence au Caire, pas un catalogue en ligne Nous vivons en Égypte »
- <sub>`body > main:nth-of-type(1) > section:nth-of-type(1) > div:nth-of-type(2)`</sub>

**3. attention logo - il faudrait mettre avec un fond transparent .**

- Où : bloc — dans « Nos séjours »
- Texte cliqué : « Agence locale basée au Caire. Guides égyptologues francophones, chauffeurs privatifs, itinéraires construits avec vous. »
- <sub>`body > footer:nth-of-type(1) > div:nth-of-type(1) > div:nth-of-type(1) > div:nth-of-type(1)`</sub>

**4. connecter avec les vrais avis google**

- Où : titre H2 — dans « N avis Google, note moyenne note »
- Texte cliqué : « N avis Google, note moyenne note »
- <sub>`body > main:nth-of-type(1) > section:nth-of-type(8) > div:nth-of-type(1) > h2:nth-of-type(1)`</sub>

**5. a supprimer**

- Où : fragment de texte — dans « Nos séjours »
- Texte cliqué : « Agence locale · Le Caire, Égypte »
- <sub>`body > footer:nth-of-type(1) > div:nth-of-type(1) > div:nth-of-type(2) > span:nth-of-type(2)`</sub>

**6. attention logo - il faudrait mettre avec un fond transparent .**

- Où : image — dans « Une agence au Caire, pas un catalogue en ligne »
- Fichier actuel : `cropped-Screenshot_20231015_082741_Instagram-removebg-preview-1.webp` — alt « Authentique Égypte »
- <sub>`body > header:nth-of-type(1) > div:nth-of-type(1) > a:nth-of-type(1) > img:nth-of-type(1)`</sub>

### Devis — Demande de devis

25 retours · <https://authentiquegypte.com/?page_id=7658> · `maquettes/devis.html`

**1. à ajouter a connecter avec les avis google**

- Où : fragment de texte — dans « N avis Google, note moyenne note »
- Texte cliqué : « N »
- <sub>`body > main:nth-of-type(1) > section:nth-of-type(1) > div:nth-of-type(1) > h2:nth-of-type(1) > span:nth-of-type(1)`</sub>

**2. directement le relier à des vrais avis google**

- Où : blockquote — dans « N avis Google, note moyenne note »
- Texte cliqué : « Très beau séjour parfaitement organisé. Interlocuteurs agréables et toujours prêts à rendre service. Je recommande ! »
- <sub>`body > main:nth-of-type(1) > section:nth-of-type(1) > div:nth-of-type(1) > div:nth-of-type(1) > article:nth-of-type(1) > blockquote:nth-of-type(1)`</sub>

**3. changer car le formulaire est assez long - ou a supprimer**

- Où : paragraphe — dans « Dites-nous où vous voulez aller »
- Texte cliqué : « Quatre questions courtes. Nous revenons vers vous avec un itinéraire chiffré, jour par jour, hébergements nommés »
- <sub>`body > main:nth-of-type(1) > div:nth-of-type(1) > div:nth-of-type(1) > div:nth-of-type(1) > p:nth-of-type(1)`</sub>

**4. il serait percutant de demander quel type de bateau et expliquer rapidement ces types de bateaux.**

- Où : b — dans « Ce qui vous attire en Égypte »
- Texte cliqué : « Une croisière sur le Nil »
- <sub>`#devis > section:nth-of-type(1) > fieldset:nth-of-type(1) > div:nth-of-type(1) > button:nth-of-type(1) > span:nth-of-type(1) > b:nth-of-type(1)`</sub>

**5. a ajouter**

- Où : fragment de texte — dans « Où vous joindre »
- Texte cliqué : « Lien vers la politique de confidentialité à poser »
- <sub>`#devis > section:nth-of-type(4) > p:nth-of-type(2) > span:nth-of-type(1)`</sub>

**6. le fond du logo se voit il faudrait le fond transparent**

- Où : image — dans « Dites-nous où vous voulez aller »
- Fichier actuel : `cropped-Screenshot_20231015_082741_Instagram-removebg-preview-1.webp` — alt « Authentique Égypte »
- <sub>`body > header:nth-of-type(1) > div:nth-of-type(1) > a:nth-of-type(1) > img:nth-of-type(1)`</sub>

**7. des dates davantage précises et demandes si ces dates sont flexibles, très important**

- Où : bouton — dans « Ce qui vous attire en Égypte »
- Texte cliqué : « Juin → août »
- <sub>`#devis > section:nth-of-type(1) > fieldset:nth-of-type(2) > div:nth-of-type(1) > button:nth-of-type(3)`</sub>

**8. a ajouter**

- Où : fragment de texte — dans « C'est envoyé »
- Texte cliqué : « Maquette : aucun envoi réel. À brancher sur WPForms. »
- <sub>`#merci > p:nth-of-type(3) > span:nth-of-type(1)`</sub>

**9. Rdv appel pour échanger sur le voyage**

- Où : fragment de texte — dans « Ce qui se passe ensuite »
- Texte cliqué : « Un itinéraire jour par jour, hébergements nommés, prix ferme. »
- <sub>`body > main:nth-of-type(1) > div:nth-of-type(1) > div:nth-of-type(1) > aside:nth-of-type(1) > div:nth-of-type(1) > ol:nth-of-type(1) > li:nth-of-type(2) > span:nth-of-type(1)`</sub>

**10. à ajouter a connecter avec les avis google**

- Où : fragment de texte — dans « N avis Google, note moyenne note »
- Texte cliqué : « Note, nombre d’avis et sélection à confirmer par l’agence »
- <sub>`body > main:nth-of-type(1) > section:nth-of-type(1) > div:nth-of-type(1) > p:nth-of-type(2) > span:nth-of-type(1)`</sub>

**11. à ajouter**

- Où : fragment de texte — dans « N avis Google, note moyenne note »
- Texte cliqué : « note »
- <sub>`body > main:nth-of-type(1) > section:nth-of-type(1) > div:nth-of-type(1) > h2:nth-of-type(1) > span:nth-of-type(2)`</sub>

**12. mettre une autre couleur plus fashy**

- Où : lien — dans « Dites-nous où vous voulez aller »
- Texte cliqué : « Obtenir mon devis »
- <sub>`body > header:nth-of-type(1) > div:nth-of-type(1) > nav:nth-of-type(1) > a:nth-of-type(4)`</sub>

**13. enlever cette partie**

- Où : fragment de texte — dans « Nos séjours »
- Texte cliqué : « Agence locale · Le Caire, Égypte »
- <sub>`body > footer:nth-of-type(1) > div:nth-of-type(1) > div:nth-of-type(2) > span:nth-of-type(2)`</sub>

**14. changer cette photo**

- Où : image — dans « Ce qui vous attire en Égypte »
- Fichier actuel : `peggy-anke-YxpoB3bvlZQ-unsplash.jpg` — alt « Lagon de la mer Rouge à Dahab »
- <sub>`#devis > section:nth-of-type(1) > fieldset:nth-of-type(1) > div:nth-of-type(1) > button:nth-of-type(4) > img:nth-of-type(1)`</sub>

**15. ajouter maison d'hôte /guest house ou hotel de charme**

- Où : bloc — dans « Votre façon de voyager »
- Texte cliqué : « Simple et local Confortable, 4★ Haut de gamme, 5★ Un mélange »
- <sub>`#devis > section:nth-of-type(3) > fieldset:nth-of-type(1) > div:nth-of-type(1)`</sub>

**16. écrire demande de devis directement**

- Où : titre H1 — dans « Dites-nous où vous voulez aller »
- Texte cliqué : « Dites-nous où vous voulez aller »
- <sub>`body > main:nth-of-type(1) > div:nth-of-type(1) > div:nth-of-type(1) > div:nth-of-type(1) > h1:nth-of-type(1)`</sub>

**17. attention le fond du logo ne va pas ) opter pour le logo avec fond transparent**

- Où : image — dans « Nos séjours »
- Fichier actuel : `cropped-Screenshot_20231015_082741_Instagram-removebg-preview-1.webp` — alt « Authentique Égypte »
- <sub>`body > footer:nth-of-type(1) > div:nth-of-type(1) > div:nth-of-type(1) > div:nth-of-type(1) > img:nth-of-type(1)`</sub>

**18. 48heures (hors week end vendredi et samedi)**

- Où : italique — dans « Ce qui se passe ensuite »
- Texte cliqué : « délai à confirmer »
- <sub>`body > main:nth-of-type(1) > div:nth-of-type(1) > div:nth-of-type(1) > aside:nth-of-type(1) > div:nth-of-type(1) > ol:nth-of-type(1) > li:nth-of-type(1) > em:nth-of-type(1)`</sub>

**19. enlever les emoji de la barre du menu**

- Où : bouton — dans « Dites-nous où vous voulez aller »
- Texte cliqué : « Destinations »
- <sub>`body > header:nth-of-type(1) > div:nth-of-type(1) > nav:nth-of-type(1) > div:nth-of-type(2) > button:nth-of-type(1)`</sub>

**20. dire que nous les recontactons sous 48 (hors week end) pour organiser un rendez vous par téléphone**

- Où : paragraphe — dans « C'est envoyé »
- Texte cliqué : « mettre, nous revenons vers vous avec un itinéraire chiffré, jour par jour. Si quelque chose manque pour bien v »
- <sub>`#merci > p:nth-of-type(1)`</sub>

**21. mettre des contours**

- Où : input — dans « Où vous joindre »
- <sub>`#prenom`</sub>

**22. mettre une entrée libre**

- Où : bloc — dans « Votre façon de voyager »
- Texte cliqué : « Moins de 1 000 € 1 000 à 1 800 € 1 800 à 2 800 € Plus de 2 800 € »
- <sub>`#devis > section:nth-of-type(3) > fieldset:nth-of-type(2) > div:nth-of-type(1)`</sub>

**23. plus naturel simplement contactez nous via WhatsApp**

- Où : paragraphe — dans « Ce qui se passe ensuite »
- Texte cliqué : « Certaines choses se disent mieux en deux messages qu’en quatre écrans. On répond aussi sur WhatsApp. »
- <sub>`body > main:nth-of-type(1) > div:nth-of-type(1) > div:nth-of-type(1) > aside:nth-of-type(1) > div:nth-of-type(2) > p:nth-of-type(1)`</sub>

**24. nous regardons les disponibilités du programme et ils réservent**

- Où : élément de liste — dans « Ce qui se passe ensuite »
- Texte cliqué : « Vous décidezAcompte seulement une fois l’itinéraire validé. »
- <sub>`body > main:nth-of-type(1) > div:nth-of-type(1) > div:nth-of-type(1) > aside:nth-of-type(1) > div:nth-of-type(1) > ol:nth-of-type(1) > li:nth-of-type(4)`</sub>

**25. ajouter autre et les laisser écrire**

- Où : bloc — dans « Qui part, et combien de temps »
- Texte cliqué : « Mobilité réduite 🕊 Rythme doux Régime alimentaire Aucune »
- <sub>`#devis > section:nth-of-type(2) > fieldset:nth-of-type(3) > div:nth-of-type(1)`</sub>
