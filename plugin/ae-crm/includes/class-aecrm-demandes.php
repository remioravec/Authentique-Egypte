<?php
/**
 * Les demandes : type de contenu, captation, purge.
 *
 * Cette classe ne connaît rien de l'affichage. Elle capte, elle range,
 * elle relit.
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

class AECRM_Demandes {

	const TYPE  = 'ae_demande';
	const TACHE = 'aecrm_purge_quotidienne';

	const OPTION_PURGE = 'abo_purge_demandes';

	/**
	 * Les clés de méta gardent leur ancien préfixe `_abo_`.
	 *
	 * Ce plugin succède au module « Demandes » de AE Back-office. Les
	 * demandes déjà reçues portent ces clés-là. Les renommer pour la
	 * cohérence du nom aurait imposé une migration — donc un risque de
	 * perte — pour un bénéfice nul côté agence. Les données d'un
	 * client passent avant l'élégance d'un préfixe.
	 */
	const META_CHAMPS     = '_abo_champs';
	const META_STATUT     = '_abo_statut';
	const META_JOURNAL    = '_abo_journal';
	const META_FORMULAIRE = '_abo_formulaire';
	const META_COURRIEL   = '_abo_courriel';
	const META_PAGE       = '_abo_page';

	const STATUTS = array(
		'nouvelle' => 'Nouvelle',
		'en_cours' => 'En cours',
		'traitee'  => 'Traitée',
		'archivee' => 'Archivée',
	);

	public static function init() {
		add_action( 'init', array( __CLASS__, 'enregistrer_type' ) );

		// WPForms, toutes versions : l'action existe aussi sur Lite.
		add_action( 'wpforms_process_complete', array( __CLASS__, 'capter' ), 10, 4 );

		add_action( self::TACHE, array( __CLASS__, 'purger' ) );

		// La tâche est posée à l'activation ; on la remet si elle a été
		// perdue — une mise à jour manuelle par FTP saute le hook.
		if ( is_admin() && ! wp_next_scheduled( self::TACHE ) ) {
			wp_schedule_event( time() + HOUR_IN_SECONDS, 'daily', self::TACHE );
		}
	}

	public static function enregistrer_type() {
		register_post_type(
			self::TYPE,
			array(
				'labels'              => array(
					'name'          => 'Demandes',
					'singular_name' => 'Demande',
				),
				'public'              => false,
				'publicly_queryable'  => false,
				'exclude_from_search' => true,
				'show_ui'             => false, // écran dédié
				'show_in_nav_menus'   => false,
				'show_in_rest'        => false,
				'has_archive'         => false,
				'rewrite'             => false,
				'query_var'           => false,
				'capability_type'     => 'post',
				'map_meta_cap'        => true,
				'supports'            => array( 'title' ),
			)
		);
	}

	/* ---------------------------------------------------------------- */
	/* Captation                                                         */
	/* ---------------------------------------------------------------- */

	/**
	 * Enregistre une soumission WPForms.
	 *
	 * @param array $champs     Les champs remplis, indexés par identifiant.
	 * @param array $soumission Données brutes de WPForms.
	 * @param array $formulaire Configuration du formulaire.
	 * @param int   $entree_id  Identifiant d'entrée (0 sur la version gratuite).
	 */
	public static function capter( $champs, $soumission, $formulaire, $entree_id = 0 ) {
		// `wpforms_process_complete` se déclenche APRÈS validation et
		// APRÈS envoi des notifications. C'est une action, pas un
		// filtre : rien d'ici ne remonte à WPForms.
		//
		// Reste le cas d'une erreur de notre côté : elle interromprait
		// l'affichage de la confirmation, après un envoi pourtant
		// réussi. On l'attrape plutôt que de la laisser passer.
		try {
			self::capter_vraiment( $champs, $soumission, $formulaire, $entree_id );
		} catch ( Throwable $e ) {
			error_log( '[ae-crm] captation de la demande impossible : ' . $e->getMessage() );
		}
	}

	private static function capter_vraiment( $champs, $soumission, $formulaire, $entree_id ) {
		if ( ! is_array( $champs ) ) {
			return;
		}

		$propres  = array();
		$nom      = '';
		$courriel = '';

		foreach ( $champs as $champ ) {
			$valeur = isset( $champ['value'] ) ? $champ['value'] : '';
			if ( is_array( $valeur ) ) {
				$valeur = implode( ', ', array_filter( $valeur, 'is_scalar' ) );
			}
			$valeur = trim( (string) $valeur );
			if ( '' === $valeur ) {
				continue;
			}

			$type = isset( $champ['type'] ) ? $champ['type'] : 'text';

			$propres[] = array(
				'nom'    => sanitize_text_field( (string) ( isset( $champ['name'] ) ? $champ['name'] : 'Champ' ) ),
				'valeur' => sanitize_textarea_field( $valeur ),
				'type'   => sanitize_key( $type ),
			);

			if ( 'email' === $type && '' === $courriel ) {
				$courriel = sanitize_email( $valeur );
			}
			if ( 'name' === $type && '' === $nom ) {
				$nom = sanitize_text_field( $valeur );
			}
		}

		if ( empty( $propres ) ) {
			return;
		}

		$titre_formulaire = sanitize_text_field( (string) (
			isset( $formulaire['settings']['form_title'] )
				? $formulaire['settings']['form_title']
				: ( isset( $formulaire['id'] ) ? $formulaire['id'] : 'Formulaire' )
		) );

		$intitule = trim( $nom . ( $courriel ? ' — ' . $courriel : '' ) );
		if ( '' === $intitule ) {
			$intitule = $titre_formulaire;
		}

		$id = wp_insert_post(
			array(
				'post_type'   => self::TYPE,
				'post_status' => 'publish',
				'post_title'  => $intitule,
			),
			true
		);

		if ( is_wp_error( $id ) ) {
			error_log( '[ae-crm] enregistrement refusé : ' . $id->get_error_message() );
			return;
		}

		update_post_meta( $id, self::META_CHAMPS, $propres );
		update_post_meta( $id, self::META_STATUT, 'nouvelle' );
		update_post_meta( $id, self::META_FORMULAIRE, $titre_formulaire );
		update_post_meta( $id, '_abo_formulaire_id', (int) ( isset( $formulaire['id'] ) ? $formulaire['id'] : 0 ) );
		update_post_meta( $id, '_abo_entree_wpforms', (int) $entree_id );
		update_post_meta( $id, self::META_COURRIEL, $courriel );
		update_post_meta( $id, self::META_PAGE, esc_url_raw( (string) (
			isset( $soumission['page_url'] ) ? $soumission['page_url'] : wp_get_referer()
		) ) );
	}

	/* ---------------------------------------------------------------- */
	/* Lecture                                                           */
	/* ---------------------------------------------------------------- */

	/** Toutes les demandes, mises en forme pour l'écran. */
	public static function toutes( $limite = 300 ) {
		$posts = get_posts( array(
			'post_type'      => self::TYPE,
			'post_status'    => 'publish',
			'posts_per_page' => (int) $limite,
			'orderby'        => 'date',
			'order'          => 'DESC',
		) );

		$fiches = array();

		foreach ( $posts as $post ) {
			$champs  = get_post_meta( $post->ID, self::META_CHAMPS, true );
			$journal = get_post_meta( $post->ID, self::META_JOURNAL, true );
			$statut  = get_post_meta( $post->ID, self::META_STATUT, true );
			if ( ! isset( self::STATUTS[ $statut ] ) ) {
				$statut = 'nouvelle';
			}

			$fiches[] = array(
				'id'         => $post->ID,
				'titre'      => $post->post_title,
				'statut'     => $statut,
				'formulaire' => (string) get_post_meta( $post->ID, self::META_FORMULAIRE, true ),
				'courriel'   => (string) get_post_meta( $post->ID, self::META_COURRIEL, true ),
				'page'       => (string) get_post_meta( $post->ID, self::META_PAGE, true ),
				'date'       => get_the_date( 'j M Y, H:i', $post ),
				'depuis'     => human_time_diff( get_post_time( 'U', true, $post ) ),
				'champs'     => is_array( $champs ) ? $champs : array(),
				'journal'    => is_array( $journal ) ? $journal : array(),
				'suppr'      => wp_nonce_url(
					admin_url( 'admin-post.php?action=aecrm_supprimer&demande=' . $post->ID ),
					'aecrm_demande_' . $post->ID
				),
			);
		}

		return $fiches;
	}

	public static function compter( $statut = '' ) {
		$args = array(
			'post_type'      => self::TYPE,
			'post_status'    => 'publish',
			'posts_per_page' => -1,
			'fields'         => 'ids',
		);
		if ( $statut ) {
			$args['meta_query'] = array(
				array(
					'key'   => self::META_STATUT,
					'value' => $statut,
				),
			);
		}

		return count( get_posts( $args ) );
	}

	/* ---------------------------------------------------------------- */
	/* Écriture                                                          */
	/* ---------------------------------------------------------------- */

	public static function deplacer( $id, $statut ) {
		update_post_meta( $id, self::META_STATUT, $statut );

		return self::journaliser( $id, sprintf( 'déplacée en « %s »', self::STATUTS[ $statut ] ) );
	}

	/** Ajoute une ligne au journal de suivi d'une fiche. */
	public static function journaliser( $id, $message ) {
		$journal = get_post_meta( $id, self::META_JOURNAL, true );
		if ( ! is_array( $journal ) ) {
			$journal = array();
		}

		$utilisateur = wp_get_current_user();
		$ligne = array(
			'auteur'  => $utilisateur->display_name,
			'message' => $message,
			'date'    => current_time( 'mysql' ),
		);

		$journal[] = $ligne;
		update_post_meta( $id, self::META_JOURNAL, $journal );

		return $ligne;
	}

	/**
	 * Purge des demandes trop anciennes. Rien n'est purgé si le délai
	 * n'a pas été réglé.
	 */
	public static function purger() {
		$jours = (int) get_option( self::OPTION_PURGE, 0 );
		if ( $jours < 1 ) {
			return;
		}

		$vieilles = get_posts( array(
			'post_type'      => self::TYPE,
			'post_status'    => 'publish',
			'posts_per_page' => 200,
			'fields'         => 'ids',
			'date_query'     => array(
				array( 'before' => $jours . ' days ago' ),
			),
		) );

		foreach ( $vieilles as $id ) {
			wp_delete_post( $id, true );
		}
	}
}
