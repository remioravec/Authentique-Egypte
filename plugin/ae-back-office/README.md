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

## Les demandes clientes

**WPForms Lite n'enregistre pas les soumissions.** Son écran « Entries » est une
page de vente vers la version payante : les demandes partent uniquement par
courriel. Un courriel classé en indésirable, un envoi bloqué par l'hébergeur, et
la demande est perdue sans laisser de trace.

L'écran **Demandes** écoute `wpforms_process_complete` — une action qui se
déclenche aussi sur la version gratuite — et conserve chaque soumission en base.
Il ne remplace pas l'envoi du courriel, il s'y ajoute comme filet.

L'écran se lit comme un CRM : quatre colonnes — *Nouvelle · En cours · Traitée ·
Archivée* — et une carte par demande, qu'on **fait glisser d'une colonne à
l'autre**. Le déplacement est enregistré aussitôt ; si le serveur refuse, la
carte revient d'où elle vient plutôt que de mentir sur son état.

Une carte porte l'essentiel sans qu'on l'ouvre : la personne, le formulaire
d'origine, le renseignement le plus parlant qu'elle a laissé — budget, nombre de
voyageurs, durée, dates — son adresse, et l'ancienneté de la demande. La couleur
de pastille est calculée à partir du nom : la même personne garde la sienne d'une
colonne à l'autre et d'un jour à l'autre.

**Au clic — ou à Entrée, les cartes sont focalisables — la fiche client s'ouvre**
dans un tiroir latéral : tous les champs remplis, la page d'origine, un bouton
**Répondre** qui ouvre le courriel prérempli, un sélecteur de colonne (le chemin
clavier, et le seul praticable sur téléphone où le glisser-déposer natif
n'existe pas), et un journal de suivi interne où l'agence note ses relances.
Échap referme.

Le nombre de nouvelles demandes s'affiche en pastille dans le menu.

Sur un écran étroit les quatre colonnes restent côte à côte et le tableau défile
horizontalement — un pipeline se lit d'un coup d'œil ; en dessous de 960 px, on
empile.

**Données personnelles.** Ces enregistrements contiennent noms, adresses et
numéros. Ils vivent dans un type de contenu privé, invisible du site public. Une
durée de conservation est réglable dans Réglages → Back-office simplifié ; tant
qu'elle n'est pas choisie, **rien n'est supprimé** — une purge silencieuse par
défaut serait pire que pas de purge du tout.

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
