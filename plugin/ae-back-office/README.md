# AE Back-office — contenus rangés par gabarit

Remplace « Articles » et « Pages » par un écran unique **Contenus**, rangé par
gabarit, et masque les entrées de menu qui ne servent pas à faire vivre le site.

## Le problème

WordPress sépare Articles et Pages parce que c'est ainsi qu'il stocke les
choses, pas parce que c'est ainsi qu'on travaille. Sur ce site, un *guide
pratique* est un article et une *destination* est une page — mais un guide
ressemble beaucoup plus à un autre guide qu'à la page d'accueil.

On range donc par **gabarit** : le modèle de page, le rôle dans le site. Le type
de contenu WordPress redevient ce qu'il est, un détail technique.

## Le vocabulaire

C'est celui des maquettes de refonte, volontairement : deux nomenclatures qui se
contredisent, c'est une source d'erreurs de plus.

| Gabarit | Ce que c'est |
|---|---|
| 🏠 Accueil | La page d'accueil |
| 🗂 Catégorie de séjours | Croisière, désert, culturel, mer Rouge, Sinaï |
| 🧭 Voyage | Les itinéraires vendus — l'unité d'achat |
| 📍 Destination | Les pages géographiques : Le Caire, Louxor, désert Blanc… |
| 👥 Qui part | Famille, couple, solo, mobilité réduite |
| 📚 Hub des guides | La page qui liste les guides |
| 📄 Guide pratique | Les articles |
| ✉️ Devis | La demande de devis |
| 🏛 Agence | Qui sommes-nous |
| ⚖️ Mentions et légal | Mentions légales, confidentialité, CGV |
| 🎨 Maquette de refonte | Les pages de la zone de refonte |
| ⚙️ Technique | Newsletter, remerciements, pages de service |
| ❓ Non rangé | À classer à la main |

Le classement est **déduit automatiquement** : type de contenu, page d'accueil et
page des articles désignées par WordPress, parent, puis motifs de slug. Relevé sur
le contenu réel du site au 24/08/2026 : **61 contenus classés, 0 non rangé.**

Un classement posé à la main (✋) devient définitif : le recalcul ne l'écrase
jamais.

## Le menu simplifié

Restent visibles par défaut : **Tableau de bord · Contenus · Médiathèque ·
Refonte · Apparence · Extensions · Comptes · Réglages · Yoast SEO · Elementor ·
Modèles Elementor**. Tout le reste est masqué.

Trois garde-fous, parce qu'un back-office amputé se retourne toujours contre
celui qui l'a amputé :

1. **Le masquage est cosmétique.** `remove_menu_page()` retire une entrée de
   menu, jamais une capacité. Qui connaît l'adresse d'un écran masqué y accède
   toujours.
2. **Un interrupteur permanent** dans la barre du haut : *Menu simplifié ⇄ Menu
   complet*. Le réglage est par compte — personne n'impose sa vue aux autres.
3. **Réglages → Back-office simplifié** liste tous les identifiants de menu
   relevés sur le site, avec leur état, et laisse modifier la liste gardée.

Désactiver le plugin restitue le back-office d'origine à l'identique.

## Ce que le plugin ne touche pas

Aucun contenu, aucune URL publique, aucun réglage du site, aucun front-end. Il
n'écrit qu'une méta de classement (`_ae_gabarit`) et une préférence par compte
(`abo_tout_voir`).

## Installation

`./outils/construire.sh` à la racine du dépôt → `dist/ae-back-office.zip`, puis
Extensions → Ajouter → Téléverser → Activer. Le rangement se fait à l'activation.
