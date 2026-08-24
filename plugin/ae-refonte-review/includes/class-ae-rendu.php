<?php
/**
 * Rendu d'une maquette sur /refonte/<slug>/.
 *
 * Le HTML n'est pas stocké en base : il vit dans un fichier du dépôt, sous
 * `maquettes/`. La maquette WordPress ne porte que le titre, l'ordre dans le
 * parcours, l'état et le nom du fichier. Mettre une maquette à jour revient
 * donc à déployer un fichier, pas à toucher la base.
 *
 * Le fichier est servi tel quel, avec deux transformations :
 *   1. les liens locaux (index.html, categorie.html…) et, en option, les URL
 *      du site en ligne qu'une maquette remplace, pointent vers le parcours ;
 *   2. le calque de relecture est injecté avant </body>.
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

class AE_Refonte_Rendu {

	public static function init() {
		add_action( 'template_redirect', array( __CLASS__, 'servir' ), 5 );
	}

	/**
	 * Chemin absolu du fichier de maquette, ou false si introuvable.
	 *
	 * Le nom de fichier est nettoyé puis vérifié : il doit rester dans le
	 * dossier des maquettes et se terminer par .html. Aucune traversée de
	 * répertoire n'est possible.
	 *
	 * @param int $maquette_id
	 * @return string|false
	 */
	public static function fichier( $maquette_id ) {
		$nom = (string) get_post_meta( $maquette_id, '_ae_fichier', true );
		if ( '' === $nom ) {
			return false;
		}

		$nom = basename( $nom );
		if ( ! preg_match( '/^[A-Za-z0-9._-]+\.html$/', $nom ) ) {
			return false;
		}

		$chemin = AE_REFONTE_MAQUETTES_DIR . $nom;

		return file_exists( $chemin ) ? $chemin : false;
	}

	/**
	 * Table de correspondance « ce qui est écrit dans le HTML » → « URL du parcours ».
	 *
	 * @return array<string,string>
	 */
	private static function table_liens() {
		$table     = array();
		$rerouter  = (bool) get_option( 'ae_refonte_rerouter_liens', true );

		foreach ( AE_Refonte_Types::parcours() as $maquette ) {
			$url = get_permalink( $maquette );

			$fichier = basename( (string) get_post_meta( $maquette->ID, '_ae_fichier', true ) );
			if ( '' !== $fichier ) {
				$table[ $fichier ] = $url;
			}

			// URL du site en ligne que cette maquette remplacera, si renseignée.
			$cible = trim( (string) get_post_meta( $maquette->ID, '_ae_url_cible', true ) );
			if ( $rerouter && '' !== $cible ) {
				$table[ $cible ] = $url;
			}
		}

		return $table;
	}

	/**
	 * Réécrit les liens du HTML pour que le parcours tienne debout.
	 *
	 * On ne touche qu'au contenu des attributs href : une chaîne comme
	 * « index.html » citée dans un commentaire ou un texte reste intacte.
	 *
	 * @param string $html
	 * @return string
	 */
	private static function reecrire_liens( $html ) {
		$table = self::table_liens();
		if ( empty( $table ) ) {
			return $html;
		}

		return preg_replace_callback(
			'/href=(["\'])([^"\']*)\1/',
			static function ( $m ) use ( $table ) {
				$cible = $m[2];

				if ( isset( $table[ $cible ] ) ) {
					return 'href="' . esc_url( $table[ $cible ] ) . '"';
				}

				// Tolère l'absence ou la présence du slash final sur les URL absolues.
				$variante = rtrim( $cible, '/' );
				foreach ( $table as $depuis => $vers ) {
					if ( rtrim( $depuis, '/' ) === $variante && false !== strpos( $depuis, '://' ) ) {
						return 'href="' . esc_url( $vers ) . '"';
					}
				}

				return $m[0];
			},
			$html
		);
	}

	/**
	 * Ramène les ressources locales des maquettes à leur URL réelle.
	 *
	 * Les maquettes pointent vers `assets/charte.css`, chemin valable
	 * quand on ouvre le fichier dans un navigateur mais pas depuis
	 * /refonte/<slug>/. On le remplace par l'URL servie par le plugin.
	 *
	 * @param string $html
	 * @return string
	 */
	private static function reecrire_ressources( $html ) {
		$base = AE_REFONTE_URL . 'maquettes/';

		return preg_replace_callback(
			'/\b(href|src)=(["\'])(?!https?:|\/\/|data:|#)([^"\']+)\2/i',
			static function ( $m ) use ( $base ) {
				// Les liens vers une autre maquette ont déjà été traités.
				if ( preg_match( '/\.html($|[?#])/i', $m[3] ) ) {
					return $m[0];
				}

				return $m[1] . '="' . esc_url( $base . ltrim( $m[3], './' ) ) . '"';
			},
			$html
		);
	}

	/**
	 * Le bloc de configuration lu par le calque de relecture.
	 *
	 * @param WP_Post $maquette
	 * @return string
	 */
	private static function config( $maquette ) {
		$parcours = array();
		foreach ( AE_Refonte_Types::parcours() as $p ) {
			$parcours[] = array(
				'id'      => $p->ID,
				'titre'   => $p->post_title,
				'url'     => get_permalink( $p ),
				'etat'    => get_post_meta( $p->ID, '_ae_etat', true ) ?: 'a_revoir',
				'ouverte' => AE_Refonte_Types::compter_notes_ouvertes( $p->ID ),
			);
		}

		$utilisateur = wp_get_current_user();

		$config = array(
			'racine'     => esc_url_raw( rest_url( AE_Refonte_Rest::NAMESPACE_REST ) ),
			'nonce'      => wp_create_nonce( 'wp_rest' ),
			'maquette'   => $maquette->ID,
			'etat'       => get_post_meta( $maquette->ID, '_ae_etat', true ) ?: 'a_revoir',
			'parcours'   => $parcours,
			'types'      => AE_Refonte_Types::TYPES_NOTE,
			'statuts'    => AE_Refonte_Types::STATUTS_NOTE,
			'etats'      => AE_Refonte_Types::ETATS,
			'peutGerer'  => AE_Refonte_Roles::peut_gerer(),
			'peutAnnoter' => AE_Refonte_Roles::peut_annoter(),
			'moi'        => array(
				'id'  => $utilisateur->ID,
				'nom' => $utilisateur->display_name,
			),
		);

		return '<script id="ae-refonte-config" type="application/json">'
			. wp_json_encode( $config )
			. '</script>';
	}

	/**
	 * Intercepte l'affichage d'une maquette et sert le fichier HTML.
	 */
	public static function servir() {
		if ( ! is_singular( AE_Refonte_Types::MAQUETTE ) ) {
			return;
		}

		// Toute personne sans la capacité de lecture voit un 404 ordinaire :
		// rien n'indique qu'une zone de refonte existe.
		if ( ! AE_Refonte_Roles::peut_voir() ) {
			global $wp_query;
			$wp_query->set_404();
			status_header( 404 );
			nocache_headers();
			include get_query_template( '404' );
			exit;
		}

		$maquette = get_queried_object();
		$chemin   = self::fichier( $maquette->ID );

		if ( ! $chemin ) {
			wp_die(
				esc_html(
					sprintf(
						'Maquette « %s » : fichier HTML introuvable. Renseignez le nom du fichier dans la fiche, et vérifiez qu\'il est bien déployé dans %s',
						$maquette->post_title,
						AE_REFONTE_MAQUETTES_DIR
					)
				),
				'Maquette introuvable',
				array( 'response' => 500 )
			);
		}

		$html = file_get_contents( $chemin ); // phpcs:ignore WordPress.WP.AlternativeFunctions
		$html = self::reecrire_liens( $html );
		$html = self::reecrire_ressources( $html );

		$tete = '<meta name="robots" content="noindex,nofollow,noarchive">';
		$html = preg_replace( '/<head(\s[^>]*)?>/i', '$0' . $tete, $html, 1 );

		$calque  = self::config( $maquette );
		$calque .= '<link rel="stylesheet" href="' . esc_url( AE_REFONTE_URL . 'assets/css/calque.css?v=' . AE_REFONTE_VERSION ) . '">';
		$calque .= '<script src="' . esc_url( AE_REFONTE_URL . 'assets/js/calque.js?v=' . AE_REFONTE_VERSION ) . '" defer></script>';

		if ( false !== stripos( $html, '</body>' ) ) {
			$html = preg_replace( '/<\/body>/i', $calque . '</body>', $html, 1 );
		} else {
			$html .= $calque;
		}

		header( 'Content-Type: text/html; charset=utf-8' );
		echo $html; // phpcs:ignore WordPress.Security.EscapingOutput -- fichier de maquette maîtrisé, versionné dans le dépôt.
		exit;
	}
}
