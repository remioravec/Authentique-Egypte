<?php
/**
 * API REST : /wp-json/ae-commentaires/v1/…
 *
 *   GET    /fils?post=&url=&statut=     les fils d'une page
 *   POST   /fils                        ouvrir un fil
 *   POST   /fils/<id>/reponses          répondre
 *   PATCH  /fils/<id>                   résoudre ou rouvrir
 *   DELETE /fils/<id>                   supprimer (fil et réponses)
 *   POST   /image                       joindre une image
 *   GET    /pages                       les pages qui portent des fils
 *   GET    /tout?format=json|md         tout, d'un coup
 *
 * Le dernier point est celui qui compte pour le travail à distance :
 * `format=md` rend un digest lisible tel quel, sans mise en forme à
 * refaire, pour reprendre les demandes sans recopie manuelle.
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

class AEC_Rest {

	const NS = 'ae-commentaires/v1';

	public static function init() {
		add_action( 'rest_api_init', array( __CLASS__, 'routes' ) );
	}

	public static function routes() {
		$lecture = array( __CLASS__, 'peut_lire' );
		$ecrire  = array( __CLASS__, 'peut_ecrire' );

		register_rest_route( self::NS, '/fils', array(
			array( 'methods' => WP_REST_Server::READABLE, 'callback' => array( __CLASS__, 'lire_fils' ), 'permission_callback' => $lecture ),
			array( 'methods' => WP_REST_Server::CREATABLE, 'callback' => array( __CLASS__, 'ouvrir' ), 'permission_callback' => $ecrire ),
		) );

		register_rest_route( self::NS, '/fils/(?P<id>\d+)', array(
			array( 'methods' => 'PATCH', 'callback' => array( __CLASS__, 'modifier' ), 'permission_callback' => $ecrire ),
			array( 'methods' => WP_REST_Server::DELETABLE, 'callback' => array( __CLASS__, 'supprimer' ), 'permission_callback' => $ecrire ),
		) );

		register_rest_route( self::NS, '/fils/(?P<id>\d+)/reponses', array(
			'methods' => WP_REST_Server::CREATABLE, 'callback' => array( __CLASS__, 'repondre' ), 'permission_callback' => $ecrire,
		) );

		register_rest_route( self::NS, '/image', array(
			'methods' => WP_REST_Server::CREATABLE, 'callback' => array( __CLASS__, 'image' ), 'permission_callback' => $ecrire,
		) );

		register_rest_route( self::NS, '/pages', array(
			'methods' => WP_REST_Server::READABLE, 'callback' => array( __CLASS__, 'pages' ), 'permission_callback' => $lecture,
		) );

		register_rest_route( self::NS, '/tout', array(
			'methods' => WP_REST_Server::READABLE, 'callback' => array( __CLASS__, 'tout' ), 'permission_callback' => $lecture,
		) );
	}

	public static function peut_lire() {
		return AEC_Roles::peut_commenter()
			? true
			: new WP_Error( 'aec_interdit', 'Réservé à la relecture.', array( 'status' => 403 ) );
	}

	public static function peut_ecrire() {
		return self::peut_lire();
	}

	/* ---------------------------------------------------------------- */
	/* Mise en forme                                                     */
	/* ---------------------------------------------------------------- */

	public static function formater( $fil, $avec_reponses = true ) {
		$image_id = (int) get_post_meta( $fil->ID, '_aec_image', true );

		$donnees = array(
			'id'        => $fil->ID,
			'message'   => $fil->post_content,
			'auteur'    => get_the_author_meta( 'display_name', $fil->post_author ),
			'auteur_id' => (int) $fil->post_author,
			'date'      => get_post_time( 'c', true, $fil ),
			'statut'    => get_post_meta( $fil->ID, '_aec_statut', true ) ?: 'ouvert',
			'selecteur' => get_post_meta( $fil->ID, '_aec_selecteur', true ),
			'ancre'     => get_post_meta( $fil->ID, '_aec_ancre', true ),
			'x'         => (float) get_post_meta( $fil->ID, '_aec_x', true ),
			'y'         => (float) get_post_meta( $fil->ID, '_aec_y', true ),
			'largeur'   => (int) get_post_meta( $fil->ID, '_aec_largeur', true ),
			'url'       => get_post_meta( $fil->ID, '_aec_url', true ),
			'post'      => (int) get_post_meta( $fil->ID, '_aec_post', true ),
			'image'     => $image_id ? wp_get_attachment_url( $image_id ) : '',
		);

		if ( $avec_reponses ) {
			$donnees['reponses'] = array();
			foreach ( AEC_Types::reponses( $fil->ID ) as $reponse ) {
				$rid = (int) get_post_meta( $reponse->ID, '_aec_image', true );
				$donnees['reponses'][] = array(
					'id'        => $reponse->ID,
					'message'   => $reponse->post_content,
					'auteur'    => get_the_author_meta( 'display_name', $reponse->post_author ),
					'auteur_id' => (int) $reponse->post_author,
					'date'      => get_post_time( 'c', true, $reponse ),
					'image'     => $rid ? wp_get_attachment_url( $rid ) : '',
				);
			}
		}

		return $donnees;
	}

	/* ---------------------------------------------------------------- */
	/* Lecture                                                           */
	/* ---------------------------------------------------------------- */

	public static function lire_fils( WP_REST_Request $r ) {
		$fils = AEC_Types::fils(
			(int) $r->get_param( 'post' ),
			(string) $r->get_param( 'url' ),
			sanitize_key( (string) ( $r->get_param( 'statut' ) ?: 'tous' ) )
		);

		return rest_ensure_response( array_map( array( __CLASS__, 'formater' ), $fils ) );
	}

	/**
	 * Les pages qui portent au moins un fil, pour la navigation.
	 * On y ajoute les brouillons de refonte même sans commentaire :
	 * c'est le parcours qu'on veut faire relire.
	 */
	public static function pages() {
		global $wpdb;

		$lignes = $wpdb->get_results(
			"SELECT pm.meta_value AS cle, pm2.meta_value AS post_id, COUNT(*) AS n
			 FROM {$wpdb->postmeta} pm
			 INNER JOIN {$wpdb->posts} p ON p.ID = pm.post_id AND p.post_parent = 0 AND p.post_status = 'publish'
			 LEFT JOIN {$wpdb->postmeta} pm2 ON pm2.post_id = pm.post_id AND pm2.meta_key = '_aec_post'
			 WHERE pm.meta_key = '_aec_url'
			 GROUP BY pm.meta_value, pm2.meta_value"
		);

		$pages = array();
		foreach ( $lignes as $ligne ) {
			$post_id = (int) $ligne->post_id;
			$pages[ $ligne->cle ] = array(
				'url'     => home_url( $ligne->cle ),
				'post'    => $post_id,
				'titre'   => $post_id ? get_the_title( $post_id ) : $ligne->cle,
				'fils'    => (int) $ligne->n,
				'ouverts' => count( AEC_Types::fils( $post_id, $ligne->cle, 'ouvert' ) ),
			);
		}

		// Le parcours de refonte, même vierge de commentaires.
		$mere = get_page_by_path( 'refonte-2026' );
		if ( $mere ) {
			$enfants = get_posts( array(
				'post_type'      => 'page',
				'post_status'    => array( 'publish', 'draft', 'private' ),
				'post_parent'    => $mere->ID,
				'posts_per_page' => -1,
				'orderby'        => 'menu_order',
				'order'          => 'ASC',
			) );
			foreach ( $enfants as $enfant ) {
				$url = AEC_Types::normaliser_url( get_permalink( $enfant ) );
				if ( isset( $pages[ $url ] ) ) {
					continue;
				}
				$pages[ $url ] = array(
					'url'     => get_permalink( $enfant ),
					'post'    => $enfant->ID,
					'titre'   => $enfant->post_title,
					'fils'    => 0,
					'ouverts' => 0,
				);
			}
		}

		return rest_ensure_response( array_values( $pages ) );
	}

	public static function tout( WP_REST_Request $r ) {
		$statut = sanitize_key( (string) ( $r->get_param( 'statut' ) ?: 'tous' ) );

		$args = array(
			'post_type'      => AEC_Types::TYPE,
			'post_status'    => 'publish',
			'post_parent'    => 0,
			'posts_per_page' => -1,
			'orderby'        => 'date',
			'order'          => 'ASC',
		);
		if ( 'tous' !== $statut ) {
			$args['meta_query'] = array( array( 'key' => '_aec_statut', 'value' => $statut ) );
		}

		$fils = array_map( array( __CLASS__, 'formater' ), get_posts( $args ) );

		if ( 'md' !== $r->get_param( 'format' ) ) {
			return rest_ensure_response( $fils );
		}

		// Digest lisible tel quel, groupé par page.
		$par_page = array();
		foreach ( $fils as $fil ) {
			$titre = $fil['post'] ? get_the_title( $fil['post'] ) : $fil['url'];
			$par_page[ $titre ][] = $fil;
		}

		$lignes = array( '# Commentaires de relecture', '' );
		$lignes[] = sprintf( '%d fil%s au total.', count( $fils ), count( $fils ) > 1 ? 's' : '' );
		$lignes[] = '';

		foreach ( $par_page as $titre => $liste ) {
			$lignes[] = '## ' . $titre;
			$lignes[] = '';
			foreach ( $liste as $fil ) {
				$lignes[] = sprintf(
					'### #%d — %s · %s%s',
					$fil['id'],
					'resolu' === $fil['statut'] ? 'résolu' : 'ouvert',
					$fil['auteur'],
					$fil['largeur'] ? sprintf( ' · écran %d px', $fil['largeur'] ) : ''
				);
				if ( $fil['ancre'] ) {
					$lignes[] = sprintf( 'Sur : « %s »', $fil['ancre'] );
				}
				if ( $fil['selecteur'] ) {
					$lignes[] = sprintf( 'Sélecteur : `%s`', $fil['selecteur'] );
				}
				$lignes[] = '';
				$lignes[] = wp_strip_all_tags( $fil['message'] );
				if ( $fil['image'] ) {
					$lignes[] = '';
					$lignes[] = sprintf( 'Image jointe : %s', $fil['image'] );
				}
				foreach ( $fil['reponses'] as $reponse ) {
					$lignes[] = '';
					$lignes[] = sprintf( '> **%s** — %s', $reponse['auteur'], wp_strip_all_tags( $reponse['message'] ) );
				}
				$lignes[] = '';
			}
		}

		$reponse = new WP_REST_Response( implode( "\n", $lignes ) );
		$reponse->header( 'Content-Type', 'text/markdown; charset=utf-8' );

		return $reponse;
	}

	/* ---------------------------------------------------------------- */
	/* Écriture                                                          */
	/* ---------------------------------------------------------------- */

	public static function ouvrir( WP_REST_Request $r ) {
		$message = trim( (string) $r->get_param( 'message' ) );
		if ( '' === $message ) {
			return new WP_Error( 'aec_vide', 'Le commentaire est vide.', array( 'status' => 400 ) );
		}

		$id = wp_insert_post( array(
			'post_type'    => AEC_Types::TYPE,
			'post_status'  => 'publish',
			'post_author'  => get_current_user_id(),
			'post_parent'  => 0,
			'post_content' => wp_kses_post( $message ),
		), true );

		if ( is_wp_error( $id ) ) {
			return $id;
		}

		update_post_meta( $id, '_aec_url', AEC_Types::normaliser_url( (string) $r->get_param( 'url' ) ) );
		update_post_meta( $id, '_aec_post', (int) $r->get_param( 'post' ) );
		update_post_meta( $id, '_aec_selecteur', sanitize_text_field( (string) $r->get_param( 'selecteur' ) ) );
		update_post_meta( $id, '_aec_ancre', sanitize_text_field( (string) $r->get_param( 'ancre' ) ) );
		update_post_meta( $id, '_aec_x', (float) $r->get_param( 'x' ) );
		update_post_meta( $id, '_aec_y', (float) $r->get_param( 'y' ) );
		update_post_meta( $id, '_aec_largeur', (int) $r->get_param( 'largeur' ) );
		update_post_meta( $id, '_aec_statut', 'ouvert' );

		self::attacher_image( $id, (int) $r->get_param( 'image_id' ) );

		$fil = get_post( $id );
		do_action( 'aec_fil_ouvert', $fil );

		return rest_ensure_response( self::formater( $fil ) );
	}

	public static function repondre( WP_REST_Request $r ) {
		$fil = get_post( (int) $r['id'] );
		if ( ! $fil || AEC_Types::TYPE !== $fil->post_type || $fil->post_parent ) {
			return new WP_Error( 'aec_introuvable', 'Fil introuvable.', array( 'status' => 404 ) );
		}

		$message = trim( (string) $r->get_param( 'message' ) );
		if ( '' === $message ) {
			return new WP_Error( 'aec_vide', 'La réponse est vide.', array( 'status' => 400 ) );
		}

		$id = wp_insert_post( array(
			'post_type'    => AEC_Types::TYPE,
			'post_status'  => 'publish',
			'post_author'  => get_current_user_id(),
			'post_parent'  => $fil->ID,
			'post_content' => wp_kses_post( $message ),
		), true );

		if ( is_wp_error( $id ) ) {
			return $id;
		}

		self::attacher_image( $id, (int) $r->get_param( 'image_id' ) );

		// Répondre rouvre un fil résolu : la conversation reprend.
		if ( 'resolu' === get_post_meta( $fil->ID, '_aec_statut', true ) ) {
			update_post_meta( $fil->ID, '_aec_statut', 'ouvert' );
		}

		do_action( 'aec_reponse_ajoutee', get_post( $id ), $fil );

		return rest_ensure_response( self::formater( get_post( $fil->ID ) ) );
	}

	public static function modifier( WP_REST_Request $r ) {
		$fil = get_post( (int) $r['id'] );
		if ( ! $fil || AEC_Types::TYPE !== $fil->post_type ) {
			return new WP_Error( 'aec_introuvable', 'Fil introuvable.', array( 'status' => 404 ) );
		}

		$statut = sanitize_key( (string) $r->get_param( 'statut' ) );
		if ( in_array( $statut, array( 'ouvert', 'resolu' ), true ) ) {
			update_post_meta( $fil->ID, '_aec_statut', $statut );
		}

		return rest_ensure_response( self::formater( get_post( $fil->ID ) ) );
	}

	public static function supprimer( WP_REST_Request $r ) {
		$fil = get_post( (int) $r['id'] );
		if ( ! $fil || AEC_Types::TYPE !== $fil->post_type ) {
			return new WP_Error( 'aec_introuvable', 'Introuvable.', array( 'status' => 404 ) );
		}

		if ( ! AEC_Roles::peut_moderer() && (int) $fil->post_author !== get_current_user_id() ) {
			return new WP_Error( 'aec_interdit', 'Ce commentaire ne vous appartient pas.', array( 'status' => 403 ) );
		}

		// Supprimer un fil emporte ses réponses.
		if ( ! $fil->post_parent ) {
			foreach ( AEC_Types::reponses( $fil->ID ) as $reponse ) {
				wp_delete_post( $reponse->ID, true );
			}
		}
		wp_delete_post( $fil->ID, true );

		return rest_ensure_response( array( 'supprime' => (int) $r['id'] ) );
	}

	/**
	 * Rattache une image téléversée à un fil.
	 *
	 * Un refus était silencieux : le commentaire partait sans son
	 * image et personne ne l'apprenait — ni la relectrice, qui avait vu
	 * sa vignette, ni nous à la relecture. On journalise désormais.
	 */
	private static function attacher_image( $post_id, $image_id ) {
		if ( $image_id > 0 && 'attachment' !== get_post_type( $image_id ) ) {
			error_log( sprintf(
				'[ae-commentaires] image %d refusée sur le fil %d : ce n\'est pas une pièce jointe (%s).',
				$image_id,
				$post_id,
				get_post_type( $image_id ) ? get_post_type( $image_id ) : 'introuvable'
			) );
		}

		if ( $image_id > 0 && 'attachment' === get_post_type( $image_id ) ) {
			update_post_meta( $post_id, '_aec_image', $image_id );
		}
	}

	/**
	 * Reçoit une image — copie d'écran collée, fichier déposé ou choisi.
	 *
	 * Le relecteur n'a pas `upload_files` : on élève la capacité le temps
	 * de l'appel, et seulement après avoir vérifié que le fichier est
	 * bien une image.
	 */
	public static function image( WP_REST_Request $r ) {
		$fichiers = $r->get_file_params();
		if ( empty( $fichiers['fichier'] ) ) {
			return new WP_Error( 'aec_image', 'Aucun fichier reçu.', array( 'status' => 400 ) );
		}

		$fichier = $fichiers['fichier'];
		$type    = wp_check_filetype( $fichier['name'] );
		$permis  = array( 'jpg', 'jpeg', 'png', 'webp', 'gif', 'avif' );

		if ( ! in_array( strtolower( (string) $type['ext'] ), $permis, true ) ) {
			return new WP_Error( 'aec_image', 'Formats acceptés : JPG, PNG, WEBP, GIF, AVIF.', array( 'status' => 400 ) );
		}

		require_once ABSPATH . 'wp-admin/includes/file.php';
		require_once ABSPATH . 'wp-admin/includes/media.php';
		require_once ABSPATH . 'wp-admin/includes/image.php';

		$elever = static function ( $caps, $cap ) {
			return 'upload_files' === $cap ? array( AEC_Roles::CAP_COMMENTER ) : $caps;
		};

		add_filter( 'map_meta_cap', $elever, 10, 2 );
		$piece = media_handle_sideload(
			array( 'name' => $fichier['name'], 'tmp_name' => $fichier['tmp_name'] ),
			0
		);
		remove_filter( 'map_meta_cap', $elever, 10 );

		if ( is_wp_error( $piece ) ) {
			return $piece;
		}

		update_post_meta( $piece, '_aec_piece_jointe', 1 );

		return rest_ensure_response( array(
			'id'  => $piece,
			'url' => wp_get_attachment_url( $piece ),
		) );
	}
}
