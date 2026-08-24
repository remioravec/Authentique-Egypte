<?php
/**
 * Le type de contenu qui porte les commentaires.
 *
 * Un fil est un `ae_commentaire` de parent 0 ; une réponse est un
 * `ae_commentaire` dont le parent est le fil. C'est la hiérarchie
 * native de WordPress, donc rien à inventer pour ordonner ou compter.
 *
 * Le type est `public => false` : absent des sitemaps (Yoast lit
 * `public`), de la recherche interne, des archives et des flux.
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

class AEC_Types {

	const TYPE = 'ae_commentaire';

	public static function init() {
		add_action( 'init', array( __CLASS__, 'enregistrer' ) );
	}

	public static function enregistrer() {
		register_post_type(
			self::TYPE,
			array(
				'labels'              => array(
					'name'          => 'Commentaires de relecture',
					'singular_name' => 'Commentaire',
				),
				'public'              => false,
				'publicly_queryable'  => false,
				'exclude_from_search' => true,
				'show_ui'             => false,
				'show_in_nav_menus'   => false,
				'show_in_rest'        => false,
				'has_archive'         => false,
				'hierarchical'        => true,
				'rewrite'             => false,
				'query_var'           => false,
				'capability_type'     => 'post',
				'map_meta_cap'        => true,
				'supports'            => array( 'editor', 'author', 'page-attributes' ),
			)
		);
	}

	/**
	 * Clé stable d'une page.
	 *
	 * On préfère l'identifiant du contenu quand il existe : une page
	 * qui change de slug garde ses commentaires. L'URL ne sert que de
	 * repli, pour l'accueil ou une archive.
	 *
	 * @param string $url
	 * @return string
	 */
	public static function normaliser_url( $url ) {
		$morceaux = wp_parse_url( $url );
		$chemin   = $morceaux['path'] ?? '/';

		// On garde page_id et p, qui identifient un brouillon ; on jette
		// le reste (preview, nonce, utm…), qui change à chaque visite.
		$garde = array();
		if ( ! empty( $morceaux['query'] ) ) {
			parse_str( $morceaux['query'], $params );
			foreach ( array( 'page_id', 'p', 'post_type' ) as $cle ) {
				if ( isset( $params[ $cle ] ) ) {
					$garde[ $cle ] = sanitize_text_field( $params[ $cle ] );
				}
			}
		}

		$normalisee = '/' . trim( $chemin, '/' );
		if ( '/' !== $normalisee ) {
			$normalisee .= '/';
		}
		if ( $garde ) {
			ksort( $garde );
			$normalisee .= '?' . http_build_query( $garde );
		}

		return $normalisee;
	}

	/**
	 * Les fils d'une page.
	 *
	 * @param int    $post_id
	 * @param string $url
	 * @param string $statut  ouvert | resolu | tous
	 * @return WP_Post[]
	 */
	public static function fils( $post_id = 0, $url = '', $statut = 'tous' ) {
		$meta = array( 'relation' => 'AND' );

		if ( $post_id > 0 ) {
			$meta[] = array(
				'key'   => '_aec_post',
				'value' => (int) $post_id,
			);
		} else {
			$meta[] = array(
				'key'   => '_aec_url',
				'value' => self::normaliser_url( $url ),
			);
		}

		if ( 'tous' !== $statut ) {
			$meta[] = array(
				'key'   => '_aec_statut',
				'value' => $statut,
			);
		}

		return get_posts(
			array(
				'post_type'      => self::TYPE,
				'post_status'    => 'publish',
				'post_parent'    => 0,
				'posts_per_page' => -1,
				'orderby'        => 'date',
				'order'          => 'ASC',
				'meta_query'     => $meta,
			)
		);
	}

	/** Les réponses d'un fil, dans l'ordre. */
	public static function reponses( $fil_id ) {
		return get_posts(
			array(
				'post_type'      => self::TYPE,
				'post_status'    => 'publish',
				'post_parent'    => (int) $fil_id,
				'posts_per_page' => -1,
				'orderby'        => 'date',
				'order'          => 'ASC',
			)
		);
	}
}
