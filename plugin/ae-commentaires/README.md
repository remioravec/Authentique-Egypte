# AE Commentaires — relecture façon Google Docs

Un calque de commentaires sur **n'importe quelle page du site**. Le geste est
celui de Google Docs et de Figma : un bouton, un clic sur l'élément, on écrit.

## Le geste

1. **Activer** — la bulle en bas à droite, ou la touche <kbd>C</kbd>.
2. **Survoler** — l'élément sous le curseur se souligne en bleu.
3. **Cliquer** — une bulle s'ouvre au point cliqué, avec un simple champ de
   texte. Pas de type à choisir, pas de champ obligatoire, pas de formulaire.
4. **Écrire** — et joindre une image si besoin : bouton, glisser-déposer, ou
   **coller une capture d'écran** directement dans le champ.
5. **Envoyer** — bouton, ou <kbd>Ctrl</kbd>+<kbd>Entrée</kbd>.

Une épingle numérotée reste sur l'élément. Au clic, le fil s'ouvre : les
réponses, un champ pour répondre, **Résoudre** et **Supprimer**. Répondre à un
fil résolu le rouvre — la conversation reprend là où elle s'était arrêtée.

Le panneau latéral liste tous les fils de la page, filtrables *à traiter / tous*,
et donne la liste des pages à relire avec leur nombre de fils ouverts.

## L'ancrage

Un commentaire est attaché trois fois, du plus précis au plus robuste :

| | |
|---|---|
| **Sélecteur CSS** | le chemin exact de l'élément depuis `<body>` |
| **Texte de l'élément** | 120 caractères, pour le retrouver si la structure bouge |
| **Position relative** | où dans la boîte de l'élément, en fraction de sa largeur et de sa hauteur |

S'y ajoute la **largeur d'écran** au moment du commentaire : une remarque posée
à 390 px se distingue d'une remarque posée à 1440 px, ce qui répond seul aux
retours du type « ce n'est pas adapté au mobile ».

## Où ça marche

Sur **toute page du site** : pages en ligne, brouillons de refonte, articles,
voyages. Rien à déclarer, rien à configurer.

Le calque n'est chargé que pour un compte connecté qui a la capacité
`aec_commenter`. **Un visiteur ne reçoit ni script, ni style, ni donnée** — le
calque n'existe pas pour lui.

Le plugin se tient à l'écart de l'éditeur Elementor, des flux et des impressions.

## Les comptes

| Capacité | Relecteur | Auteur | Éditeur | Administrateur |
|---|:--:|:--:|:--:|:--:|
| `aec_commenter` — commenter, répondre, joindre | ✓ | ✓ | ✓ | ✓ |
| `aec_moderer` — supprimer les fils des autres | — | — | ✓ | ✓ |

Le rôle **Relecteur** n'a ni `edit_posts`, ni `upload_files`, ni accès au
back-office : il ne peut rien modifier sur le site. L'envoi d'image passe par un
point REST dédié qui n'accepte que les formats image et n'élève la capacité que
le temps de l'appel.

Pour donner l'accès à la cliente : Comptes → Ajouter, rôle **Relecteur**, puis
lui envoyer l'adresse d'une page. C'est tout.

## Lecture à distance

C'est ce qui ferme la boucle de travail : les commentaires se lisent depuis
l'extérieur, sans recopie.

```bash
# Tout, en digest lisible tel quel
curl -u 'identifiant:mot de passe application' \
  'https://authentiquegypte.com/wp-json/ae-commentaires/v1/tout?format=md'

# Seulement ce qui reste ouvert, en JSON
curl -u 'identifiant:mot de passe application' \
  'https://authentiquegypte.com/wp-json/ae-commentaires/v1/tout?statut=ouvert'
```

Le format `md` rend un document groupé par page, avec pour chaque fil son
numéro, son état, l'élément visé, le sélecteur, la largeur d'écran, le message,
l'image jointe et les réponses.

### Toutes les routes

Namespace `ae-commentaires/v1`.

| Route | Méthode | Ce qu'elle fait |
|---|---|---|
| `/fils?post=&url=&statut=` | GET | les fils d'une page |
| `/fils` | POST | ouvrir un fil |
| `/fils/<id>` | PATCH · DELETE | résoudre ou rouvrir · supprimer |
| `/fils/<id>/reponses` | POST | répondre |
| `/image` | POST | joindre une image |
| `/pages` | GET | les pages qui portent des fils |
| `/tout?format=json\|md` | GET | tout, d'un coup |

## Ce que le plugin ne touche pas

Aucun contenu, aucune URL, aucun réglage, aucun menu. Les commentaires vivent
dans un type de contenu privé (`ae_commentaire`), hors sitemap, hors recherche
interne, hors archives et hors flux. Un fil est un enregistrement de parent 0,
une réponse est son enfant : c'est la hiérarchie native de WordPress.

Désactiver l'extension fait disparaître le calque sans rien toucher au site.

## Installation

`./outils/construire.sh` → `dist/ae-commentaires.zip`, puis Extensions →
Ajouter → Téléverser → Activer.

> **Si `ae-refonte-review` est installé, supprimez-le.** Cette extension le
> remplace : l'ancienne ne fonctionnait que sur huit maquettes servies depuis
> ses propres fichiers, et demandait de choisir un type de demande avant
> d'écrire. Celle-ci marche partout et ne demande rien.
