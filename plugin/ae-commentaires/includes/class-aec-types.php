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

	/* ---------------------------------------------------------------- */
	/* Ce qui est lu, et ce qui ne l'est pas                             */
	/* ---------------------------------------------------------------- */

	/**
	 * La clé où chaque compte range ce qu'il a déjà vu.
	 *
	 * Un tableau { id du fil => date de la dernière réponse vue }, en
	 * horodatage GMT. On ne stocke pas « lu / non lu » par réponse :
	 * une date par fil suffit, ne grossit pas avec la discussion, et
	 * survit à la suppression d'une réponse.
	 */
	const VU = '_aec_vu';

	public static function vu( $utilisateur_id = 0 ) {
		$utilisateur_id = $utilisateur_id ?: get_current_user_id();
		$vu = get_user_meta( $utilisateur_id, self::VU, true );

		return is_array( $vu ) ? $vu : array();
	}

	public static function marquer_vu( $fil_id, $utilisateur_id = 0 ) {
		$utilisateur_id = $utilisateur_id ?: get_current_user_id();
		if ( ! $utilisateur_id ) {
			return;
		}
		$vu = self::vu( $utilisateur_id );
		$vu[ (int) $fil_id ] = time();
		// On ne garde pas la trace des fils disparus : la table resterait
		// à grossir pour rien.
		update_user_meta( $utilisateur_id, self::VU, array_slice( $vu, -400, null, true ) );
	}

	/**
	 * Combien de réponses ce compte n'a pas encore vues sur ce fil.
	 *
	 * Les siennes ne comptent pas : on ne se notifie pas soi-même. C'est
	 * la règle qui évite le compteur qui monte dès qu'on répond.
	 */
	public static function non_lues( $fil_id, $utilisateur_id = 0 ) {
		$utilisateur_id = $utilisateur_id ?: get_current_user_id();
		if ( ! $utilisateur_id ) {
			return 0;
		}
		$vu = self::vu( $utilisateur_id );
		$depuis = isset( $vu[ (int) $fil_id ] ) ? (int) $vu[ (int) $fil_id ] : 0;

		$n = 0;
		foreach ( self::reponses( $fil_id ) as $reponse ) {
			if ( (int) $reponse->post_author === (int) $utilisateur_id ) {
				continue;
			}
			if ( (int) get_post_time( 'U', true, $reponse ) > $depuis ) {
				$n++;
			}
		}

		return $n;
	}

	/**
	 * Les réponses non lues de TOUS les fils, en une requête.
	 *
	 * non_lues() interroge la base une fois par fil. Appelée depuis
	 * /pages, qui parcourt les trois cents fils du site, elle faisait
	 * trois cents requêtes à chaque chargement de page. Ici on demande
	 * toutes les réponses d'un coup et on compte en mémoire.
	 *
	 * @return array { id du fil => nombre de réponses non lues }
	 */
	public static function non_lues_toutes( $utilisateur_id = 0 ) {
		global $wpdb;

		$utilisateur_id = $utilisateur_id ?: get_current_user_id();
		if ( ! $utilisateur_id ) {
			return array();
		}

		$lignes = $wpdb->get_results( $wpdb->prepare(
			"SELECT post_parent AS fil, post_date_gmt
			 FROM {$wpdb->posts}
			 WHERE post_type = %s AND post_status = 'publish'
			   AND post_parent > 0 AND post_author <> %d",
			self::TYPE,
			$utilisateur_id
		) );

		$vu = self::vu( $utilisateur_id );
		$n  = array();
		foreach ( $lignes as $ligne ) {
			$fil    = (int) $ligne->fil;
			$depuis = isset( $vu[ $fil ] ) ? (int) $vu[ $fil ] : 0;
			if ( strtotime( $ligne->post_date_gmt . ' UTC' ) > $depuis ) {
				$n[ $fil ] = ( isset( $n[ $fil ] ) ? $n[ $fil ] : 0 ) + 1;
			}
		}

		return $n;
	}

	/**
	 * Le fil attend-il une réponse de l'équipe ?
	 *
	 * Vrai quand il est ouvert et que le dernier mot revient à quelqu'un
	 * qui ne modère pas. C'est la seule mesure qui dise « la balle est
	 * dans notre camp » : compter tous les fils ouverts mélange ce qu'on
	 * doit traiter et ce qu'on a déjà renvoyé à la relectrice.
	 */
	public static function attend_equipe( $fil ) {
		$fil = is_object( $fil ) ? $fil : get_post( (int) $fil );
		if ( ! $fil || 'resolu' === get_post_meta( $fil->ID, '_aec_statut', true ) ) {
			return false;
		}
		$reponses = self::reponses( $fil->ID );
		$dernier  = $reponses ? end( $reponses ) : $fil;

		return ! user_can( (int) $dernier->post_author, AEC_Roles::CAP_MODERER );
	}
}
