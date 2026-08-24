# AE Refonte — relecture et annotations

Zone de refonte étanche pour authentiquegypte.com, plus l'outil qui permet à la
cliente de parcourir les maquettes et de demander des changements élément par
élément.

## Ce que le plugin ne fait pas

C'est le point le plus important du cahier des charges : **le site en ligne
n'est jamais touché.**

- Aucun filtre, aucune action sur `page`, `post`, `programs`, les menus, le
  thème Astra ou Elementor.
- Tout vit dans deux types de contenu qui appartiennent au plugin :
  `ae_maquette` (les pages de refonte) et `ae_note` (les demandes).
- Ces deux types sont `public => false` : donc absents des sitemaps (Yoast
  comme WordPress), de la recherche interne, des menus, des archives et des
  flux.
- Les URL `/refonte/…` répondent **404** à toute personne sans la capacité
  `ae_view_refonte` — un visiteur, un robot ou un client non connecté ne peut
  pas savoir que la zone existe.
- Désactiver le plugin fait disparaître la zone de refonte sans modifier une
  ligne du site.

## Installation

1. `./outils/construire.sh` à la racine du dépôt → `dist/ae-refonte-review.zip`
2. Extensions → Ajouter → Téléverser une extension → activer.
3. Refonte → Maquettes → Ajouter : un titre, le fichier HTML servi, l'ordre
   dans le parcours, et éventuellement l'URL du site en ligne que la maquette
   remplacera.
4. Utilisateurs → Ajouter : créer le compte de la cliente avec le rôle
   **Relecteur refonte**, puis lui envoyer l'URL de la première maquette.

## Comment la cliente s'en sert

Une barre flottante en bas de chaque maquette :

| Élément | Ce qu'il fait |
|---|---|
| ‹ Précédente / Suivante › | avance dans le parcours de relecture |
| liste déroulante | saute à n'importe quelle maquette, avec son nombre de demandes ouvertes |
| pastille d'état | À produire · À revoir · En relecture · Validée |
| **Annoter** | passe en mode annotation : survoler surligne l'élément, cliquer ouvre le formulaire |
| **Demandes** | ouvre le panneau latéral avec tout le fil de la page |

Le formulaire type la demande — **Texte** (avec le texte de remplacement
proposé, pré-rempli avec l'existant), **Couleur** (sélecteur de couleur),
**Image** (envoi d'un remplacement), **Mise en page**, **Autre** — et
enregistre la largeur d'écran au moment de l'annotation, ce qui permet de
distinguer une remarque mobile d'une remarque bureau.

Chaque demande pose une épingle numérotée sur l'élément visé. L'ancrage est
double : sélecteur CSS, plus le texte de l'élément en secours si la maquette
est retouchée entre-temps.

## Côté agence

**Refonte → Demandes** : tableau filtrable par maquette, statut et type, avec
la proposition (texte, pastille de couleur, image), le fil de réponses et le
changement de statut. Export CSV et JSON en un clic.

## API REST

Namespace `ae-refonte/v1`. C'est ce qui ferme la boucle de travail : les
demandes sont lisibles depuis l'extérieur, sans recopie manuelle.

| Route | Méthode | Capacité |
|---|---|---|
| `/maquettes` | GET | `ae_view_refonte` |
| `/maquettes/<id>` | PATCH | `ae_manage_refonte` |
| `/notes` | GET, POST | `ae_view_refonte` / `ae_add_note` |
| `/notes/<id>` | PATCH, DELETE | auteur ou `ae_manage_refonte` |
| `/notes/<id>/reponses` | POST | `ae_add_note` |
| `/media` | POST | `ae_add_note` |
| `/export?format=json\|csv` | GET | `ae_manage_refonte` |

```bash
curl -u 'identifiant:mot-de-passe-application' \
  'https://authentiquegypte.com/wp-json/ae-refonte/v1/export'
```

## Capacités

| Capacité | Rôle « Relecteur refonte » | Éditeur | Administrateur |
|---|:--:|:--:|:--:|
| `ae_view_refonte` | ✓ | ✓ | ✓ |
| `ae_add_note` | ✓ | ✓ | ✓ |
| `ae_manage_refonte` | — | — | ✓ |

Le rôle relecteur n'a ni `edit_posts`, ni `upload_files`, ni accès au
back-office : il ne peut rien casser sur le site en ligne. L'envoi d'image
passe par un point REST dédié qui n'accepte que les formats image et n'élève
la capacité que le temps de l'appel.

## Où vit le HTML

Pas en base : dans `maquettes/*.html`, versionné dans le dépôt. La fiche
WordPress ne porte que le titre, l'ordre, l'état et le nom du fichier. Mettre
une maquette à jour, c'est déployer un fichier — jamais une migration.
