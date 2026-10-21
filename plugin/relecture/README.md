# Relecture — commentaires sur les pages

Une extension WordPress pour faire relire un site par un client, comme on
commente un Google Docs : un bouton, un clic sur l'élément à changer, un
texte (avec une image si besoin). Une épingle numérotée reste sur
l'élément ; on répond, on résout.

## Ce qu'elle fait

- **Sur toute page du site** : pages en ligne, brouillons, articles,
  contenus personnalisés. Le commentaire est ancré à l'élément (sélecteur
  CSS, texte de secours, position relative) : il retrouve sa place même si
  la page change un peu. La largeur d'écran est notée : une remarque posée
  sur téléphone se distingue d'une remarque posée sur ordinateur.
- **Invisible pour les visiteurs** : le calque n'est chargé que pour un
  compte connecté qui a la capacité `rlc_commenter`. Un visiteur ne reçoit
  ni script, ni style, ni donnée.
- **Ne modifie rien** : aucun contenu, aucune URL, aucun réglage du site.
  Les commentaires vivent dans un type de contenu privé (`rlc_commentaire`),
  hors sitemap, hors recherche, hors flux. Désactiver l'extension fait
  disparaître le calque.

## Installation chez un nouveau client

1. Extensions › Ajouter › Téléverser : `relecture.zip`, puis Activer.
2. Créer le compte du client avec le rôle **Relecteur** : il peut commenter,
   joindre une image et répondre, sans accès au back-office ni droit de
   modifier le site.
3. Lui envoyer l'adresse du site : une fois connecté, il voit la bulle en
   bas à droite.
4. Facultatif — **Relecture › Parcours à relire** : l'adresse d'une page
   mère (par exemple `refonte`). Ses pages enfants, même en brouillon,
   apparaissent dans le navigateur de pages du calque, commentées ou non.

## Le geste

- Bouton ou touche **C** : le mode commentaire s'active. Le survol souligne
  l'élément, un clic ouvre la bulle.
- Une image se colle (Ctrl+V) ou se dépose dans le champ.
- **Ctrl+Entrée** envoie, **Échap** ferme.
- Le panneau latéral liste les fils de la page, filtrables (ouverts,
  traités, tous), et un navigateur mène aux autres pages commentées.
- En mode commentaire, le calque capte tous les clics de la page (un clic
  pose une bulle) : pour cliquer normalement sur un lien ou un bouton du
  site, on sort du mode.

## Qui fait quoi

| Capacité | Rôles | Permet |
|---|---|---|
| `rlc_commenter` | Relecteur, Auteur, Éditeur, Administrateur | ouvrir un fil, répondre, joindre une image |
| `rlc_moderer` | Éditeur, Administrateur | supprimer les fils des autres, régler le parcours |

Le rôle **Relecteur** n'a ni `edit_posts`, ni `upload_files`, ni accès au
back-office : il ne peut rien modifier sur le site. L'envoi d'image passe
par un point REST dédié qui n'accepte que les formats image et n'élève la
capacité que le temps de l'appel.

## Courriels

- Un fil ouvert prévient l'équipe (les comptes qui modèrent), jamais son
  auteur.
- Une réponse prévient l'auteur du fil et ceux qui y ont parlé.
- Personne ne reçoit son propre message.
- Les envois sont **groupés** : le premier message ouvre un délai d'un
  quart d'heure, tout ce qui arrive pendant l'attente part dans le même
  courriel (« 7 nouvelles remarques sur Nom du site (3 pages) »), avec un
  lien direct vers chaque remarque.
- Chaque compte peut couper ses courriels depuis son profil (case
  « Relecture »).

Les courriels partent par `wp_mail` : sur un hébergement qui n'envoie pas
bien, brancher une extension SMTP.

## L'écran Relecture (back-office)

Le travail se fait sur les pages ; l'écran n'est qu'une vue d'ensemble,
rangée par page, la plus chargée en tête :

- **Pour nous** : les fils dont le dernier mot vient du client (la pastille
  du menu les compte) ;
- **Ouverts**, **Traités**, **Tout**.

## Lecture à distance (API REST)

Avec un mot de passe d'application (Profil › Mots de passe d'application) :

```bash
# Tout, en digest lisible
curl -u 'identifiant:mot de passe application' \
  'https://votre-site.fr/wp-json/relecture/v1/tout?format=md'

# Seulement ce qui reste ouvert, en JSON
curl -u 'identifiant:mot de passe application' \
  'https://votre-site.fr/wp-json/relecture/v1/tout?statut=ouvert'
```

| Méthode | Route | Rôle |
|---|---|---|
| GET | `/relecture/v1/tout` | tous les fils (`format=md`, `statut=ouvert\|resolu`) |
| GET | `/relecture/v1/fils?post=ID&url=/chemin/&statut=` | les fils d'une page |
| POST | `/relecture/v1/fils` | ouvrir un fil |
| POST | `/relecture/v1/fils/{id}/reponses` | répondre (rouvre un fil résolu) |
| PATCH | `/relecture/v1/fils/{id}` | `{"statut":"resolu"}` ou `{"statut":"ouvert"}` |
| DELETE | `/relecture/v1/fils/{id}` | supprimer un fil |
| POST | `/relecture/v1/fils/{id}/vu` | marquer les réponses comme lues |
| POST | `/relecture/v1/image` | joindre une image |
| GET | `/relecture/v1/pages` | les pages commentées et le parcours |

Répondre rouvre un fil : pour répondre puis clore, faire la réponse
d'abord, le PATCH ensuite.

## Crochets

- `rlc_fil_ouvert` ( WP_Post $fil ) — un fil vient d'être ouvert ;
- `rlc_reponse_ajoutee` ( WP_Post $reponse, WP_Post $fil ) — une réponse
  vient d'être postée.

## Prérequis

WordPress 6.0+, PHP 7.4+. Testé avec Elementor (le calque se retire de
l'éditeur et de son aperçu) et avec des thèmes qui stylent agressivement
`button` et `input` : toutes les règles du calque sont préfixées et
blindées.
