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
| 🗂 Gabarit circuit | Les pages qui **listent** des séjours : la page mère et les cinq circuits |
| 🧭 Gabarit programme | La **fiche** d'un séjour : son prix, ses étapes, ce qui est inclus |
| 📍 Gabarit destination | Un lieu : Le Caire, Louxor, le désert Blanc… |
| 👥 Gabarit qui part | Famille, couple, solo, mobilité réduite |
| 📄 Gabarit guide | Les articles du blog |
| 📚 Gabarit blog | Le sommaire qui rassemble les guides |
| 🏠 Gabarit accueil | La page d'accueil |
| 🏛 Gabarit qui sommes-nous | L'agence, l'équipe, les engagements |
| ✉️ Devis | La demande de devis |
| ⚖️ Mentions et légal | Mentions légales, confidentialité, CGV |
| 🎨 Maquette de référence | Les gabarits dessinés à la main |
| 📁 Dossier de rangement | Une page qui ne sert qu'à en contenir d'autres |
| ⚙️ Technique | Newsletter, remerciements, pages de service |
| ❓ Non rangé | À classer à la main |

L'ordre de ce tableau est celui de l'écran, et c'est **exactement celui du
sommaire de la refonte** : deux listes qui disent la même chose dans deux ordres
différents, on ne peut plus les comparer.

*Circuit* et *programme* portaient jusqu'ici les noms « catégorie de séjours » et
« voyage » — deux mots qui ne disaient pas lequel liste et lequel vend. Les clés
techniques n'ont pas bougé (`categorie`, `voyage`) : un classement posé à la main
s'y réfère, les renommer l'aurait perdu.

Le classement est **déduit automatiquement** : type de contenu, page d'accueil et
page des articles désignées par WordPress, parent, puis motifs de slug. Relevé sur
le contenu réel du site au 22/09/2026 : **134 contenus, dont les 58 pages de la
refonte rangées dans les huit gabarits du sommaire, 3 non rangés côté site en
ligne.**

Un classement posé à la main (✋) devient définitif : le recalcul ne l'écrase
jamais.

## Les demandes clientes

Elles ne sont plus gérées ici : elles ont leur
propre extension, **AE CRM**, qui fonctionne sans celle-ci. Le menu *Demandes*
reste dans la liste des entrées gardées, l'écran vient simplement d'ailleurs.

Si une ancienne version de cette extension est encore installée quelque part,
AE CRM débranche son module au démarrage — sans quoi chaque formulaire envoyé
serait enregistré deux fois.

## Le menu simplifié

Restent visibles par défaut : **Tableau de bord · Contenus · Demandes · Voyages ·
Médiathèque · Relecture · WPForms · Apparence · Extensions · Comptes · Réglages ·
Yoast SEO · Elementor · Modèles Elementor**. Tout le reste est masqué.

Une entrée gardée qui se termine par `*` vaut pour tout ce qui commence ainsi :
`wpforms*` garde l'écran principal et ses sous-écrans, sans qu'il faille les
énumérer ni deviner comment l'extension les nomme d'une version à l'autre.

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
