# Registre des décisions — gabarit programme

Chaque ligne est un ajout d'interface, un réemploi de contenu ou un écart accepté, avec sa source et sa date. **Ce qui n'est pas ici est une invention** : l'agent contrôle contenu le signale, et c'est voulu.

Statuts : `acté` (décision prise), `à trancher` (recommandation posée, attend Rémi), `attente cliente`.

| n° | Date | Quoi | Source ou décision | Sections | Statut |
|---|---|---|---|---|---|
| D1 | 09/09/2026 | Les questions FAQ **sans réponse** sur la page live sont affichées, avec un marqueur `.aremplir` « Réponse à rédiger » dans le corps du `details` ; elles ne vont pas dans le JSON-LD FAQPage. | Recommandation du plan (§3.2) : une question posée sur la page est du contenu. | S11, S0 | à trancher |
| D2 | 09/09/2026 | Le logo du site dans l'entête et le pied. | Blocs communs `maquettes/assets/blocs/`. | S15 | acté |
| D3 | 09/09/2026 | « Réponse sous 48 h (hors vendredi et samedi) » dans le hero, le panneau et l'appel final ; aucune promesse « 24 h ». | Retour Mélanie n° 21 du 26/08 (« 48h hors week end ») ; backlog C3. | S1, S6, S12 | acté |
| D4 | 09/09/2026 | Bloc interlocutrice du panneau collant et photo de l'appel final : **générique** (« L'équipe d'Authentique Égypte, Le Caire », photo d'équipe `DSC00581-1.jpg` de l'accueil) tant que la cliente n'a pas validé prénom et photo. | Recommandation du plan. La photo vient de la page d'accueil du site (maquette validée), pas de la fiche. | S6, S12 | à trancher |
| D5 | 09/09/2026 | Retrait des liens de thèmes « Voyage en couple / en famille » de la présentation ; un seul lien « Tous nos séjours <catégorie> ». Titre des séjours proches : « Ces séjours se combinent bien », identique sur les 14 pages. | Recommandation du plan : le maillage relève du plan de liens, pas du gabarit. | S3, S13 | à trancher |
| D6 | 09/09/2026 | Titres de section propres au gabarit : « Les étapes de votre séjour », « Points forts », « Itinéraire jour par jour », « Tarif par personne », « Informations pratiques », « Questions fréquentes ». Ce sont des étiquettes de mise en page, pas du contenu. | Gabarit programme (UX de la page circuit concurrente). | S4, S5, S7, S8, S10, S11 | acté |
| D7 | 09/09/2026 | « Points forts » = **réemploi** de la première liste à puces de la réponse FAQ « Qu'est-ce qui rend <lieu> unique ? ». Sans cette liste dans la source, la section n'est pas rendue. | Contenu de la fiche, déplacé. | S5 | acté |
| D8 | 09/09/2026 | Bloc « Ce séjour vous tente ? Ajustons-le à vos dates. » et ses trois points (devis gratuit détaillé jour par jour ; guide égyptologue francophone et chauffeur privatif ; acompte une fois l'itinéraire validé). | Bande devis du site refondu, `outils/gabarit-voyage.py` `bande_devis()`, déjà sur les 59 pages livrées. | S8, S7 (carte latérale) | acté |
| D9 | 09/09/2026 | Les quatre confirmations de l'appel final (délai, guide privatif, chauffeur et véhicule sécurisé, aucune carte bancaire demandée). | Réassurance du site refondu (accueil validé, bande devis). | S12 | acté |
| D10 | 09/09/2026 | Infos pratiques (3 groupes), réassurance en 3 points, H2 « Voyagez autrement… » et « Pouvons-nous vous accompagner ? » : repris de **`maquettes/index.html`** (accueil validé), jamais de l'accueil live. Visa à 30 €. | Backlog C1 (25 € → 30 €), état zéro Z4. | S10, S12 | acté |
| D11 | 09/09/2026 | Nombre d'avis Google affiché = celui du widget Trustindex de la page live, lu à l'inventaire et daté (`avis_google`). Relevé du 09/09/2026 : 23. Aucun chiffre en dur dans le générateur. | Widget de la page live ; backlog C4 (chiffres réels attendus). | S1, S6, S12 | acté |
| D12 | 09/09/2026 | Libellé « 45 jours avant le départ » dans les infos pratiques. | FAQ paiement de l'accueil validé. | S10 | acté |
| D13 | 09/09/2026 | Cartes des séjours proches : titre, image, prix des fiches sœurs de la même catégorie (page catégorie du site refondu + inventaires sœurs). Trois cartes maximum. | Gabarit ; images étrangères à la fiche mais propres au site. | S13 | acté |
| D14 | 09/09/2026 | Hero en composition « image contenue » quand l'image réelle est plus étroite que l'écran : image nette au centre, fond = la même image floutée. Aucune image étrangère. | État zéro Z9 (pixelisation). | S1 | acté |
| D15 | 09/09/2026 | Une image de la source n'est jamais utilisée deux fois entre hero, jours et galerie ; les jours sans image restent sans image ; une vignette 300 px ne va que dans une boîte ≤ 300 px. | Plan §5 S7. | S1, S7 | acté |
| D16 | 09/09/2026 | Les 14 pages programme sont déployées dans un dossier « Refonte · Programmes », à côté des 14 brouillons « voyage » qui restent en place jusqu'à validation. | Recommandation du plan (§3.2). | D1 | à trancher |
| D17 | 09/09/2026 | Les fautes de la source (« N'inclus pas », « Le programme inclus ») sont conservées telles quelles et listées dans `questions-melanie.md`. | Règle du projet : on ne réécrit pas. | S9 | acté |
| D18 | 09/09/2026 | Bouton « Personnaliser ce séjour » (devis) et « Poser une question sur WhatsApp » ; barre mobile avec le même bouton. | Libellés d'interface du gabarit ; correction de « Personaliser ». | S1, S6, S8, S14 | acté |
