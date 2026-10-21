#!/usr/bin/env python3
"""Tire de ae-commentaires une extension de relecture vierge, pour n'importe quel client.

    python3 outils/extraire-relecture.py            # écrit plugin/relecture/ et plugin/relecture.zip

Rémi, le 21 octobre : « sors-moi le plugin de relecture, vierge et sans
indications d'Authentique Égypte, pour l'avoir sur plusieurs clients ».

Ce qui change par rapport à ae-commentaires 1.2.1 :
  - les noms : préfixe `aec` → `rlc`, espace REST `relecture/v1`, type de
    contenu `rlc_commentaire`, rôle `rlc_relecteur`, capacités
    `rlc_commenter` / `rlc_moderer`, dossier et domaine `relecture` ;
  - la palette : l'or et le bleu nuit de la marque cèdent la place à une
    palette neutre (ambre pour les épingles, ardoise pour les boutons) ;
  - les textes : « En attente d'Authentique Égypte » devient « En attente du
    client », l'objet des courriels porte le nom du site au lieu de « la
    refonte », « la relectrice » devient « le client » ;
  - le parcours à relire n'est plus la page « refonte-2026 » en dur : c'est
    un réglage de l'écran Relecture (adresse de la page mère, vide par
    défaut) ;
  - l'en-tête : version 1.0.0, sans lien vers le dépôt du client.

Chaque remplacement est vérifié : s'il ne trouve pas son texte, le script
s'arrête plutôt que de livrer une extension à moitié renommée.
"""

import os
import re
import shutil
import sys
import zipfile

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(ICI)
SOURCE = os.path.join(RACINE, 'plugin', 'ae-commentaires')
CIBLE = os.path.join(RACINE, 'plugin', 'relecture')
ZIP = os.path.join(RACINE, 'plugin', 'relecture.zip')
VERSION = '1.0.0'

FICHIERS = {
    'ae-commentaires.php': 'relecture.php',
    'README.md': 'README.md',
    'assets/css/commentaires.css': 'assets/css/relecture.css',
    'assets/js/commentaires.js': 'assets/js/relecture.js',
    'includes/class-aec-admin.php': 'includes/class-rlc-admin.php',
    'includes/class-aec-courriel.php': 'includes/class-rlc-courriel.php',
    'includes/class-aec-front.php': 'includes/class-rlc-front.php',
    'includes/class-aec-rest.php': 'includes/class-rlc-rest.php',
    'includes/class-aec-roles.php': 'includes/class-rlc-roles.php',
    'includes/class-aec-types.php': 'includes/class-rlc-types.php',
}

# Textes propres au projet, fichier par fichier : (avant, après). Appliqués AVANT le renommage des préfixes.
TEXTES = {
    'ae-commentaires.php': [
        (" * Plugin Name:       AE Commentaires — relecture façon Google Docs\n"
         " * Plugin URI:        https://github.com/remioravec/Authentique-Egypte\n",
         " * Plugin Name:       Relecture — commentaires sur les pages\n"),
        (" * Version:           1.2.1\n", " * Version:           %s\n" % VERSION),
        (" * Text Domain:       ae-commentaires\n", " * Text Domain:       relecture\n"),
        ("refonte, articles, voyages.", "refonte, articles, contenus personnalisés."),
        ("define( 'AEC_VERSION', '1.2.1' );", "define( 'AEC_VERSION', '%s' );" % VERSION),
        ("require_once AEC_DIR . 'includes/class-aec-roles.php';\n"
         "require_once AEC_DIR . 'includes/class-aec-types.php';\n"
         "require_once AEC_DIR . 'includes/class-aec-rest.php';\n"
         "require_once AEC_DIR . 'includes/class-aec-front.php';\n"
         "require_once AEC_DIR . 'includes/class-aec-admin.php';\n"
         "require_once AEC_DIR . 'includes/class-aec-courriel.php';",
         "require_once AEC_DIR . 'includes/class-rlc-roles.php';\n"
         "require_once AEC_DIR . 'includes/class-rlc-types.php';\n"
         "require_once AEC_DIR . 'includes/class-rlc-rest.php';\n"
         "require_once AEC_DIR . 'includes/class-rlc-front.php';\n"
         "require_once AEC_DIR . 'includes/class-rlc-admin.php';\n"
         "require_once AEC_DIR . 'includes/class-rlc-courriel.php';"),
    ],
    'includes/class-aec-front.php': [
        ("AEC_URL . 'assets/css/commentaires.css'", "AEC_URL . 'assets/css/relecture.css'"),
        ("AEC_URL . 'assets/js/commentaires.js'", "AEC_URL . 'assets/js/relecture.js'"),
    ],
    'includes/class-aec-admin.php': [
        ("	 * Sur trois cents fils, quatre-vingt-dix restaient « ouverts » dont\n"
         "	 * soixante portaient déjà notre réponse et attendaient la\n"
         "	 * relectrice. Une pastille à 90 ne dit rien de ce qu'il y a à faire ;\n",
         "	 * Sur une longue relecture, beaucoup de fils restent « ouverts » alors\n"
         "	 * qu'ils portent déjà notre réponse et attendent le client. Une\n"
         "	 * pastille qui les compte ne dit rien de ce qu'il y a à faire ;\n"),
        ("	 * Deux cents fils dont cent quarante clos, tous affichés à la suite :\n"
         "	 * on ne retrouvait plus ce qui restait à faire.",
         "	 * Des centaines de fils, clos pour la plupart, affichés à la suite :\n"
         "	 * on ne retrouverait plus ce qui reste à faire."),
        ("attente d'Authentique Égypte.", "attente du client."),
        ("○ En attente d'Authentique Égypte", "○ En attente du client"),
    ],
    'includes/class-aec-courriel.php': [
        (" * Une relecture se fait par salves : cent quatorze remarques en trois\n"
         " * jours, parfois vingt sur une même page en dix minutes.",
         " * Une relecture se fait par salves : des dizaines de remarques en\n"
         " * quelques jours, parfois vingt sur une même page en dix minutes."),
        (" * `aec_fil_ouvert` et `aec_reponse_ajoutee` étaient émis depuis le\n"
         " * début, et personne ne s'y branchait : aucun courriel n'est jamais\n"
         " * parti. C'est la moitié du problème que la version 1.1.0 corrige —\n"
         " * l'autre moitié étant les signaux posés sur le site.\n",
         " * `aec_fil_ouvert` et `aec_reponse_ajoutee` sont émis à chaque fil\n"
         " * ouvert et à chaque réponse : cette classe s'y branche pour prévenir\n"
         " * par courriel.\n"),
        ("		$sujet = sprintf(\n"
         "			/* translators: 1: nombre de remarques, 2: nombre de pages */\n"
         "			_n( '%1$d nouvelle remarque sur la refonte', '%1$d nouvelles remarques sur la refonte', $n, 'aec' ),\n"
         "			$n\n"
         "		);",
         "		$sujet = sprintf(\n"
         "			/* translators: 1: nombre de remarques, 2: nom du site */\n"
         "			_n( '%1$d nouvelle remarque sur %2$s', '%1$d nouvelles remarques sur %2$s', $n, 'relecture' ),\n"
         "			$n,\n"
         "			wp_specialchars_decode( get_bloginfo( 'name' ), ENT_QUOTES )\n"
         "		);"),
    ],
    'includes/class-aec-rest.php': [
        ("la relectrice n'a pas accès au back-office", "le client n'a pas accès au back-office"),
        ("Appelé quand la relectrice ouvre un fil.", "Appelé quand le client ouvre un fil."),
        ("ni la relectrice, qui avait vu", "ni le client, qui avait vu"),
        ("	 * On y ajoute les brouillons de refonte même sans commentaire :\n"
         "	 * c'est le parcours qu'on veut faire relire.",
         "	 * On y ajoute les pages du parcours à relire, même sans commentaire :\n"
         "	 * les enfants de la page mère choisie dans l'écran Relecture."),
        ("		// Le parcours de refonte, même vierge de commentaires.\n"
         "		$mere = get_page_by_path( 'refonte-2026' );\n"
         "		if ( $mere ) {",
         "		// Le parcours à relire, même vierge de commentaires.\n"
         "		$mere = AEC_Admin::page_parcours();\n"
         "		if ( $mere ) {"),
    ],
    'includes/class-aec-types.php': [
        ("ce qu'on a déjà renvoyé à la relectrice.", "ce qu'on a déjà renvoyé au client."),
    ],
    'assets/js/commentaires.js': [
        ("// Le rappel qui manquait. La relectrice n'a pas accès au",
         "// Le rappel qui manquait. Le client n'a pas accès au"),
    ],
    'assets/css/commentaires.css': [
        ("   le kit Elementor du site émet `.elementor-kit-4658 button {…}`,\n"
         "   qui vaut 0-1-1 et écrase toute règle de composant en 0-1-0 —\n"
         "   quel que soit l'ordre de chargement, une classe l'emportant\n"
         "   toujours sur un élément. Mesuré : sans préfixe, les boutons\n"
         "   sortaient en fond teal, radius 3 px, majuscules, 61 px de haut.\n",
         "   un kit Elementor émet par exemple `.elementor-kit-123 button {…}`,\n"
         "   qui vaut 0-1-1 et écrase toute règle de composant en 0-1-0 —\n"
         "   quel que soit l'ordre de chargement, une classe l'emportant\n"
         "   toujours sur un élément. Sans préfixe, les boutons prendraient\n"
         "   le fond, le rayon, la casse et la hauteur des boutons du thème.\n"),
        ("La relectrice n'a pas accès au back-office", "Le client n'a pas accès au back-office"),
        # palette neutre : ambre pour ce qu'on pointe, ardoise pour ce qu'on actionne
        ("  --aec-or: #FBB50E;\n  --aec-nuit: #0B5170;\n  --aec-nuit-clair: #0d648b;\n  --aec-bleu: #167FA4;\n",
         "  --aec-or: #F5A400;\n  --aec-nuit: #26323F;\n  --aec-nuit-clair: #3A4858;\n  --aec-bleu: #1A6FD1;\n"),
        ("  --aec-ombre: 0 4px 12px rgba(11,81,112,.14), 0 18px 44px rgba(11,81,112,.20);",
         "  --aec-ombre: 0 4px 12px rgba(22,30,40,.14), 0 18px 44px rgba(22,30,40,.20);"),
        ("box-shadow: 0 0 0 3px rgba(251,181,14,.26);", "box-shadow: 0 0 0 3px rgba(245,164,0,.26);"),
    ],
}

# Renommage des identifiants, dans tous les fichiers, APRÈS les textes.
PREFIXES = [
    ('ae-commentaires/v1', 'relecture/v1'),
    ('ae-commentaires', 'relecture'),
    ('ae_commentaire', 'rlc_commentaire'),
    ('ae_relecteur', 'rlc_relecteur'),
    ('AEC', 'RLC'),
    ('aec', 'rlc'),
]

PARCOURS_PHP = '''
	/* ---------------------------------------------------------------- */
	/* Le parcours à relire                                              */
	/* ---------------------------------------------------------------- */

	/** L'option qui garde l'adresse de la page mère du parcours. */
	const OPTION_PARCOURS = 'rlc_parcours';

	/**
	 * La page mère du parcours, ou null.
	 *
	 * Ses pages enfants (publiées, brouillons ou privées) apparaissent dans
	 * le navigateur de pages du calque même sans commentaire : c'est la
	 * liste de ce qu'on veut faire relire. Vide par défaut.
	 */
	public static function page_parcours() {
		$chemin = trim( (string) get_option( self::OPTION_PARCOURS, '' ), '/' );
		return $chemin ? get_page_by_path( $chemin ) : null;
	}

	public static function enregistrer_parcours() {
		if ( ! isset( $_POST['rlc_parcours_nonce'] ) || ! current_user_can( RLC_Roles::CAP_MODERER ) ) {
			return;
		}
		check_admin_referer( 'rlc_parcours', 'rlc_parcours_nonce' );
		$chemin = isset( $_POST['rlc_parcours'] ) ? sanitize_text_field( wp_unslash( $_POST['rlc_parcours'] ) ) : '';
		// On accepte une adresse complète : on n'en garde que le chemin.
		$chemin = trim( (string) wp_parse_url( $chemin, PHP_URL_PATH ), '/' );
		update_option( self::OPTION_PARCOURS, $chemin, false );
		add_settings_error( 'rlc', 'rlc_parcours', $chemin && ! get_page_by_path( $chemin )
			? 'Aucune page à cette adresse : le parcours reste vide.'
			: 'Parcours enregistré.', $chemin && ! get_page_by_path( $chemin ) ? 'warning' : 'success' );
	}
'''

PARCOURS_ECRAN = '''
			<?php if ( RLC_Roles::peut_moderer() ) : $mere = self::page_parcours(); ?>
				<h2 style="margin-top:34px">Parcours à relire</h2>
				<?php settings_errors( 'rlc' ); ?>
				<form method="post" style="max-width:74ch">
					<?php wp_nonce_field( 'rlc_parcours', 'rlc_parcours_nonce' ); ?>
					<p>
						Les pages enfants de cette page apparaissent dans le navigateur du calque,
						même sans commentaire. Laisser vide pour ne lister que les pages commentées.
					</p>
					<p>
						<label for="rlc_parcours" class="screen-reader-text">Adresse de la page mère</label>
						<input type="text" id="rlc_parcours" name="rlc_parcours" class="regular-text code"
						       placeholder="refonte" value="<?php echo esc_attr( get_option( self::OPTION_PARCOURS, '' ) ); ?>">
						<?php submit_button( 'Enregistrer', 'secondary', 'submit', false ); ?>
					</p>
					<?php if ( $mere ) : ?>
						<p class="description">Page mère : <strong><?php echo esc_html( $mere->post_title ); ?></strong>.</p>
					<?php endif; ?>
				</form>
			<?php endif; ?>
'''


def remplacer(texte, avant, apres, ou):
    if avant not in texte:
        sys.exit('Introuvable dans %s : %r' % (ou, avant[:80]))
    return texte.replace(avant, apres)


def main():
    if os.path.exists(CIBLE):
        shutil.rmtree(CIBLE)
    for src, dst in FICHIERS.items():
        t = open(os.path.join(SOURCE, src), encoding='utf-8').read()
        for avant, apres in TEXTES.get(src, []):
            t = remplacer(t, avant, apres, src)
        if src == 'includes/class-aec-admin.php':
            # le réglage du parcours : sa méthode, son enregistrement, son formulaire
            t = remplacer(t, "		add_action( 'admin_menu', array( __CLASS__, 'menu' ) );\n",
                          "		add_action( 'admin_menu', array( __CLASS__, 'menu' ) );\n"
                          "		add_action( 'admin_init', array( __CLASS__, 'enregistrer_parcours' ) );\n", src)
            t = remplacer(t, "\n	/**\n	 * La pastille ne compte plus", PARCOURS_PHP.replace('RLC_', 'AEC_') +
                          "\n	/**\n	 * La pastille ne compte plus", src)
            t = remplacer(t, "			<h2 style=\"margin-top:34px\">Lecture à distance</h2>",
                          PARCOURS_ECRAN.replace('RLC_', 'AEC_').lstrip('\n') +
                          "\n			<h2 style=\"margin-top:34px\">Lecture à distance</h2>", src)
        for avant, apres in PREFIXES:
            t = t.replace(avant, apres)
        chemin = os.path.join(CIBLE, dst)
        os.makedirs(os.path.dirname(chemin), exist_ok=True)
        open(chemin, 'w', encoding='utf-8').write(t)

    # le README réécrit à part : il parlait du site du client
    open(os.path.join(CIBLE, 'README.md'), 'w', encoding='utf-8').write(README)

    # rien ne doit rester du client ni de l'ancien préfixe
    interdits = re.compile(r'authentique|[ée]gypte|m[ée]lanie|refonte-2026|aec|ae-commentaires|ae_|4658|relectrice',
                           re.I)
    for base, _, noms in os.walk(CIBLE):
        for nom in noms:
            chemin = os.path.join(base, nom)
            for i, ligne in enumerate(open(chemin, encoding='utf-8'), 1):
                m = interdits.search(ligne)
                if m:
                    sys.exit('Reste « %s » : %s:%d' % (m.group(0), os.path.relpath(chemin, RACINE), i))

    if os.path.exists(ZIP):
        os.remove(ZIP)
    with zipfile.ZipFile(ZIP, 'w', zipfile.ZIP_DEFLATED) as z:
        for base, _, noms in os.walk(CIBLE):
            for nom in sorted(noms):
                chemin = os.path.join(base, nom)
                z.write(chemin, os.path.relpath(chemin, os.path.dirname(CIBLE)))
    print('plugin/relecture/ et plugin/relecture.zip (%d fichiers, %d octets)'
          % (sum(len(n) for _, _, n in os.walk(CIBLE)), os.path.getsize(ZIP)))


README = r'''# Relecture — commentaires sur les pages

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
'''

if __name__ == '__main__':
    main()
