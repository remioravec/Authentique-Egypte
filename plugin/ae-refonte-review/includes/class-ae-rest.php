<?php
/**
 * API REST de la refonte : /wp-json/ae-refonte/v1/…
 *
 *   GET    /maquettes                  le parcours et son état
 *   PATCH  /maquettes/<id>             changer l'état d'une maquette
 *   GET    /notes                      les demandes (filtres maquette/statut/type)
 *   POST   /notes                      déposer une demande
 *   PATCH  /notes/<id>                 modifier une demande
 *   DELETE /notes/<id>                 supprimer une demande
 *   POST   /notes/<id>/reponses        répondre dans le fil
 *   POST   /media                      envoyer une image de remplacement
 *   GET    /export?format=json|csv     tout récupérer d'un coup
 *
 * C'est ce dernier point qui ferme la boucle de travail : les demandes
 * déposées par la cliente sont lisibles directement depuis l'extérieur,
 * sans recopie manuelle.
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

class AE_Refonte_Rest {

	const NAMESPACE_REST = 'ae-refonte/v1';

	public static function init() {
		add_action( 'rest_api_init', array( __CLASS__, 'enregistrer_routes' ) );
	}

	public static function enregistrer_routes() {
		$ns = self::NAMESPACE_REST;

		register_rest_route(
			$ns,
			'/maquettes',
			array(
				'methods'             => WP_REST_Server::READABLE,
				'callback'            => array( __CLASS__, 'lire_maquettes' ),
				'permission_callback' => array( __CLASS__, 'peut_voir' ),
			)
		);

		register_rest_route(
			$ns,
			'/maquettes/(?P<id>\d+)',
			array(
				'methods'             => 'PATCH',
				'callback'            => array( __CLASS__, 'modifier_maquette' ),
				'permission_callback' => array( __CLASS__, 'peut_gerer' ),
				'args'                => array(
					'etat' => array(
						'required'          => true,
						'validate_callback' => static function ( $v ) {
							return array_key_exists( $v, AE_Refonte_Types::ETATS );
						},
					),
				),
			)
		);

		register_rest_route(
			$ns,
			'/notes',
			array(
				array(
					'methods'             => WP_REST_Server::READABLE,
					'callback'            => array( __CLASS__, 'lire_notes' ),
					'permission_callback' => array( __CLASS__, 'peut_voir' ),
				),
				array(
					'methods'             => WP_REST_Server::CREATABLE,
					'callback'            => array( __CLASS__, 'creer_note' ),
					'permission_callback' => array( __CLASS__, 'peut_annoter' ),
				),
			)
		);

		register_rest_route(
			$ns,
			'/notes/(?P<id>\d+)',
			array(
				array(
					'methods'             => 'PATCH',
					'callback'            => array( __CLASS__, 'modifier_note' ),
					'permission_callback' => array( __CLASS__, 'peut_annoter' ),
				),
				array(
					'methods'             => WP_REST_Server::DELETABLE,
					'callback'            => array( __CLASS__, 'supprimer_note' ),
					'permission_callback' => array( __CLASS__, 'peut_annoter' ),
				),
			)
		);

		register_rest_route(
			$ns,
			'/notes/(?P<id>\d+)/reponses',
			array(
				'methods'             => WP_REST_Server::CREATABLE,
				'callback'            => array( __CLASS__, 'repondre' ),
				'permission_callback' => array( __CLASS__, 'peut_annoter' ),
			)
		);

		register_rest_route(
			$ns,
			'/media',
			array(
				'methods'             => WP_REST_Server::CREATABLE,
				'callback'            => array( __CLASS__, 'envoyer_media' ),
				'permission_callback' => array( __CLASS__, 'peut_annoter' ),
			)
		);

		register_rest_route(
			$ns,
			'/export',
			array(
				'methods'             => WP_REST_Server::READABLE,
				'callback'            => array( __CLASS__, 'exporter' ),
				'permission_callback' => array( __CLASS__, 'peut_gerer' ),
			)
		);
	}

	/* ---------------------------------------------------------------- */
	/* Permissions                                                       */
	/* ---------------------------------------------------------------- */

	public static function peut_voir() {
		return AE_Refonte_Roles::peut_voir()
			? true
			: new WP_Error( 'ae_refonte_interdit', 'Accès réservé à la relecture de la refonte.', array( 'status' => 403 ) );
	}

	public static function peut_annoter() {
		return AE_Refonte_Roles::peut_annoter()
			? true
			: new WP_Error( 'ae_refonte_interdit', 'Vous ne pouvez pas déposer de demande.', array( 'status' => 403 ) );
	}

	public static function peut_gerer() {
		return AE_Refonte_Roles::peut_gerer()
			? true
			: new WP_Error( 'ae_refonte_interdit', 'Réservé à l\'administration de la refonte.', array( 'status' => 403 ) );
	}

	/**
	 * Une demande n'est modifiable que par son auteur, ou par l'administration.
	 *
	 * @param WP_Post $note
	 * @return bool
	 */
	private static function peut_toucher_note( $note ) {
		return AE_Refonte_Roles::peut_gerer() || (int) $note->post_author === get_current_user_id();
	}

	/* ---------------------------------------------------------------- */
	/* Maquettes                                                         */
	/* ---------------------------------------------------------------- */

	public static function lire_maquettes() {
		$sortie = array();

		foreach ( AE_Refonte_Types::parcours() as $m ) {
			$sortie[] = array(
				'id'      => $m->ID,
				'titre'   => $m->post_title,
				'url'     => get_permalink( $m ),
				'fichier' => get_post_meta( $m->ID, '_ae_fichier', true ),
				'cible'   => get_post_meta( $m->ID, '_ae_url_cible', true ),
				'etat'    => get_post_meta( $m->ID, '_ae_etat', true ) ?: 'a_revoir',
				'ouverte' => AE_Refonte_Types::compter_notes_ouvertes( $m->ID ),
				'ordre'   => (int) $m->menu_order,
			);
		}

		return rest_ensure_response( $sortie );
	}

	public static function modifier_maquette( WP_REST_Request $requete ) {
		$id = (int) $requete['id'];
		if ( AE_Refonte_Types::MAQUETTE !== get_post_type( $id ) ) {
			return new WP_Error( 'ae_refonte_introuvable', 'Maquette introuvable.', array( 'status' => 404 ) );
		}

		update_post_meta( $id, '_ae_etat', sanitize_key( $requete['etat'] ) );

		return rest_ensure_response(
			array(
				'id'   => $id,
				'etat' => get_post_meta( $id, '_ae_etat', true ),
			)
		);
	}

	/* ---------------------------------------------------------------- */
	/* Demandes                                                          */
	/* ---------------------------------------------------------------- */

	/**
	 * Met une demande en forme pour l'API.
	 *
	 * @param WP_Post $note
	 * @return array
	 */
	public static function formater_note( $note ) {
		$media_id = (int) get_post_meta( $note->ID, '_ae_media', true );

		return array(
			'id'         => $note->ID,
			'maquette'   => (int) get_post_meta( $note->ID, '_ae_maquette', true ),
			'type'       => get_post_meta( $note->ID, '_ae_type', true ) ?: 'autre',
			'statut'     => get_post_meta( $note->ID, '_ae_statut', true ) ?: 'ouverte',
			'message'    => $note->post_content,
			'valeur'     => get_post_meta( $note->ID, '_ae_valeur', true ),
			'selecteur'  => get_post_meta( $note->ID, '_ae_selecteur', true ),
			'ancre'      => get_post_meta( $note->ID, '_ae_ancre', true ),
			'x'          => (float) get_post_meta( $note->ID, '_ae_x', true ),
			'y'          => (float) get_post_meta( $note->ID, '_ae_y', true ),
			'largeur'    => (int) get_post_meta( $note->ID, '_ae_viewport', true ),
			'media'      => $media_id ? wp_get_attachment_url( $media_id ) : '',
			'media_id'   => $media_id,
			'auteur'     => get_the_author_meta( 'display_name', $note->post_author ),
			'auteur_id'  => (int) $note->post_author,
			'date'       => get_post_time( 'c', true, $note ),
			'reponses'   => self::lire_reponses( $note->ID ),
		);
	}

	private static function lire_reponses( $note_id ) {
		$brut = get_post_meta( $note_id, '_ae_reponses', true );
		if ( ! is_array( $brut ) ) {
			return array();
		}

		return array_values( $brut );
	}

	public static function lire_notes( WP_REST_Request $requete ) {
		$meta = array();

		if ( $requete->get_param( 'maquette' ) ) {
			$meta[] = array(
				'key'   => '_ae_maquette',
				'value' => (int) $requete->get_param( 'maquette' ),
			);
		}
		if ( $requete->get_param( 'statut' ) ) {
			$meta[] = array(
				'key'     => '_ae_statut',
				'value'   => array_map( 'sanitize_key', (array) $requete->get_param( 'statut' ) ),
				'compare' => 'IN',
			);
		}
		if ( $requete->get_param( 'type' ) ) {
			$meta[] = array(
				'key'     => '_ae_type',
				'value'   => array_map( 'sanitize_key', (array) $requete->get_param( 'type' ) ),
				'compare' => 'IN',
			);
		}

		$args = array(
			'post_type'      => AE_Refonte_Types::NOTE,
			'post_status'    => 'publish',
			'posts_per_page' => -1,
			'orderby'        => 'date',
			'order'          => 'ASC',
		);
		if ( $meta ) {
			$args['meta_query'] = $meta;
		}

		$sortie = array();
		foreach ( get_posts( $args ) as $note ) {
			$sortie[] = self::formater_note( $note );
		}

		return rest_ensure_response( $sortie );
	}

	public static function creer_note( WP_REST_Request $requete ) {
		$maquette_id = (int) $requete->get_param( 'maquette' );

		if ( AE_Refonte_Types::MAQUETTE !== get_post_type( $maquette_id ) ) {
			return new WP_Error( 'ae_refonte_maquette', 'Maquette inconnue.', array( 'status' => 400 ) );
		}

		$message = trim( (string) $requete->get_param( 'message' ) );
		if ( '' === $message ) {
			return new WP_Error( 'ae_refonte_vide', 'Le message est obligatoire.', array( 'status' => 400 ) );
		}

		$type = sanitize_key( (string) $requete->get_param( 'type' ) );
		if ( ! array_key_exists( $type, AE_Refonte_Types::TYPES_NOTE ) ) {
			$type = 'autre';
		}

		$note_id = wp_insert_post(
			array(
				'post_type'    => AE_Refonte_Types::NOTE,
				'post_status'  => 'publish',
				'post_author'  => get_current_user_id(),
				'post_title'   => wp_trim_words( $message, 10, '…' ),
				'post_content' => wp_kses_post( $message ),
			),
			true
		);

		if ( is_wp_error( $note_id ) ) {
			return $note_id;
		}

		update_post_meta( $note_id, '_ae_maquette', $maquette_id );
		update_post_meta( $note_id, '_ae_type', $type );
		update_post_meta( $note_id, '_ae_statut', 'ouverte' );
		update_post_meta( $note_id, '_ae_selecteur', sanitize_text_field( (string) $requete->get_param( 'selecteur' ) ) );
		update_post_meta( $note_id, '_ae_ancre', sanitize_text_field( (string) $requete->get_param( 'ancre' ) ) );
		update_post_meta( $note_id, '_ae_x', (float) $requete->get_param( 'x' ) );
		update_post_meta( $note_id, '_ae_y', (float) $requete->get_param( 'y' ) );
		update_post_meta( $note_id, '_ae_viewport', (int) $requete->get_param( 'largeur' ) );
		update_post_meta( $note_id, '_ae_valeur', sanitize_text_field( (string) $requete->get_param( 'valeur' ) ) );

		$media_id = (int) $requete->get_param( 'media_id' );
		if ( $media_id && 'attachment' === get_post_type( $media_id ) ) {
			update_post_meta( $note_id, '_ae_media', $media_id );
		}

		// La maquette repasse en relecture dès qu'une demande y est déposée.
		if ( 'validee' === get_post_meta( $maquette_id, '_ae_etat', true ) ) {
			update_post_meta( $maquette_id, '_ae_etat', 'a_revoir' );
		}

		$note = get_post( $note_id );
		do_action( 'ae_refonte_note_creee', $note );

		return rest_ensure_response( self::formater_note( $note ) );
	}

	public static function modifier_note( WP_REST_Request $requete ) {
		$note = get_post( (int) $requete['id'] );

		if ( ! $note || AE_Refonte_Types::NOTE !== $note->post_type ) {
			return new WP_Error( 'ae_refonte_introuvable', 'Demande introuvable.', array( 'status' => 404 ) );
		}
		if ( ! self::peut_toucher_note( $note ) ) {
			return new WP_Error( 'ae_refonte_interdit', 'Cette demande ne vous appartient pas.', array( 'status' => 403 ) );
		}

		// Le statut ne se change que côté administration.
		$statut = $requete->get_param( 'statut' );
		if ( null !== $statut ) {
			if ( ! AE_Refonte_Roles::peut_gerer() ) {
				return new WP_Error( 'ae_refonte_interdit', 'Le statut est géré par l\'agence.', array( 'status' => 403 ) );
			}
			$statut = sanitize_key( $statut );
			if ( array_key_exists( $statut, AE_Refonte_Types::STATUTS_NOTE ) ) {
				update_post_meta( $note->ID, '_ae_statut', $statut );
			}
		}

		$message = $requete->get_param( 'message' );
		if ( null !== $message && '' !== trim( $message ) ) {
			wp_update_post(
				array(
					'ID'           => $note->ID,
					'post_title'   => wp_trim_words( $message, 10, '…' ),
					'post_content' => wp_kses_post( $message ),
				)
			);
		}

		$valeur = $requete->get_param( 'valeur' );
		if ( null !== $valeur ) {
			update_post_meta( $note->ID, '_ae_valeur', sanitize_text_field( $valeur ) );
		}

		return rest_ensure_response( self::formater_note( get_post( $note->ID ) ) );
	}

	public static function supprimer_note( WP_REST_Request $requete ) {
		$note = get_post( (int) $requete['id'] );

		if ( ! $note || AE_Refonte_Types::NOTE !== $note->post_type ) {
			return new WP_Error( 'ae_refonte_introuvable', 'Demande introuvable.', array( 'status' => 404 ) );
		}
		if ( ! self::peut_toucher_note( $note ) ) {
			return new WP_Error( 'ae_refonte_interdit', 'Cette demande ne vous appartient pas.', array( 'status' => 403 ) );
		}

		wp_delete_post( $note->ID, true );

		return rest_ensure_response( array( 'supprimee' => $note->ID ) );
	}

	public static function repondre( WP_REST_Request $requete ) {
		$note = get_post( (int) $requete['id'] );

		if ( ! $note || AE_Refonte_Types::NOTE !== $note->post_type ) {
			return new WP_Error( 'ae_refonte_introuvable', 'Demande introuvable.', array( 'status' => 404 ) );
		}

		$message = trim( (string) $requete->get_param( 'message' ) );
		if ( '' === $message ) {
			return new WP_Error( 'ae_refonte_vide', 'La réponse est vide.', array( 'status' => 400 ) );
		}

		$utilisateur = wp_get_current_user();
		$reponses    = get_post_meta( $note->ID, '_ae_reponses', true );
		if ( ! is_array( $reponses ) ) {
			$reponses = array();
		}

		$reponses[] = array(
			'auteur'    => $utilisateur->display_name,
			'auteur_id' => $utilisateur->ID,
			'message'   => wp_kses_post( $message ),
			'date'      => gmdate( 'c' ),
		);

		update_post_meta( $note->ID, '_ae_reponses', $reponses );

		do_action( 'ae_refonte_reponse_ajoutee', $note, end( $reponses ) );

		return rest_ensure_response( self::formater_note( get_post( $note->ID ) ) );
	}

	/* ---------------------------------------------------------------- */
	/* Média                                                             */
	/* ---------------------------------------------------------------- */

	/**
	 * Reçoit une image de remplacement proposée par la relectrice.
	 *
	 * La relectrice n'a pas `upload_files` : on élève temporairement le
	 * filtre de capacité, le temps de l'appel, et seulement pour les types
	 * image. Le fichier est marqué pour qu'on le retrouve.
	 */
	public static function envoyer_media( WP_REST_Request $requete ) {
		$fichiers = $requete->get_file_params();

		if ( empty( $fichiers['fichier'] ) ) {
			return new WP_Error( 'ae_refonte_media', 'Aucun fichier reçu.', array( 'status' => 400 ) );
		}

		$fichier = $fichiers['fichier'];
		$type    = wp_check_filetype( $fichier['name'] );
		$permis  = array( 'jpg', 'jpeg', 'png', 'webp', 'gif', 'avif' );

		if ( ! in_array( strtolower( (string) $type['ext'] ), $permis, true ) ) {
			return new WP_Error( 'ae_refonte_media', 'Formats acceptés : JPG, PNG, WEBP, GIF, AVIF.', array( 'status' => 400 ) );
		}

		require_once ABSPATH . 'wp-admin/includes/file.php';
		require_once ABSPATH . 'wp-admin/includes/media.php';
		require_once ABSPATH . 'wp-admin/includes/image.php';

		$elever = static function ( $caps, $cap ) {
			if ( 'upload_files' === $cap ) {
				return array( AE_Refonte_Roles::CAP_ANNOTER );
			}

			return $caps;
		};
		add_filter( 'map_meta_cap', $elever, 10, 2 );
		$piece_jointe = media_handle_sideload(
			array(
				'name'     => $fichier['name'],
				'tmp_name' => $fichier['tmp_name'],
			),
			0
		);
		remove_filter( 'map_meta_cap', $elever, 10 );

		if ( is_wp_error( $piece_jointe ) ) {
			return $piece_jointe;
		}

		update_post_meta( $piece_jointe, '_ae_refonte_proposition', 1 );

		return rest_ensure_response(
			array(
				'id'  => $piece_jointe,
				'url' => wp_get_attachment_url( $piece_jointe ),
			)
		);
	}

	/* ---------------------------------------------------------------- */
	/* Export                                                            */
	/* ---------------------------------------------------------------- */

	public static function exporter( WP_REST_Request $requete ) {
		$notes = get_posts(
			array(
				'post_type'      => AE_Refonte_Types::NOTE,
				'post_status'    => 'publish',
				'posts_per_page' => -1,
				'orderby'        => 'date',
				'order'          => 'ASC',
			)
		);

		$lignes = array();
		foreach ( $notes as $note ) {
			$ligne                 = self::formater_note( $note );
			$ligne['maquette_nom'] = get_the_title( $ligne['maquette'] );
			$lignes[]              = $ligne;
		}

		if ( 'csv' !== $requete->get_param( 'format' ) ) {
			return rest_ensure_response( $lignes );
		}

		$colonnes = array( 'id', 'maquette_nom', 'type', 'statut', 'message', 'valeur', 'selecteur', 'ancre', 'media', 'auteur', 'date' );
		$sortie   = fopen( 'php://temp', 'r+' );
		fputcsv( $sortie, $colonnes );

		foreach ( $lignes as $ligne ) {
			$plate = array();
			foreach ( $colonnes as $colonne ) {
				$plate[] = isset( $ligne[ $colonne ] ) ? $ligne[ $colonne ] : '';
			}
			fputcsv( $sortie, $plate );
		}

		rewind( $sortie );
		$csv = stream_get_contents( $sortie );
		fclose( $sortie );

		$reponse = new WP_REST_Response( $csv );
		$reponse->header( 'Content-Type', 'text/csv; charset=utf-8' );
		$reponse->header( 'Content-Disposition', 'attachment; filename="demandes-refonte.csv"' );

		return $reponse;
	}
}
