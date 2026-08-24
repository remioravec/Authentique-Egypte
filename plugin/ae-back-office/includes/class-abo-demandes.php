<?php
/**
 * Les demandes reçues par formulaire.
 *
 * ------------------------------------------------------------------
 * POURQUOI CET ÉCRAN EXISTE
 * ------------------------------------------------------------------
 * WPForms Lite — la version installée sur ce site — **n'enregistre pas
 * les soumissions**. Son écran « Entries » est une page de vente vers
 * la version payante : les demandes partent uniquement par courriel.
 * Un courriel qui arrive en indésirable, un envoi bloqué par
 * l'hébergeur, et la demande est perdue sans laisser de trace.
 *
 * Ce module écoute `wpforms_process_complete`, une action qui se
 * déclenche aussi sur la version gratuite, et conserve chaque
 * soumission dans la base. Il ne remplace pas l'envoi du courriel : il
 * s'ajoute, comme filet.
 * ------------------------------------------------------------------
 *
 * DONNÉES PERSONNELLES — ces enregistrements contiennent des noms, des
 * adresses et des numéros. Ils sont stockés dans un type de contenu
 * privé, invisible du site public. Une purge automatique est réglable
 * (Réglages → Back-office simplifié) et vaut politique de conservation.
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

class ABO_Demandes {

	const TYPE   = 'ae_demande';
	const MENU   = 'ae-demandes';
	const OPTION_PURGE = 'abo_purge_demandes';

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

		add_action( 'admin_menu', array( __CLASS__, 'menu' ), 9 );
		add_action( 'admin_post_abo_demande_statut', array( __CLASS__, 'action_statut' ) );
		add_action( 'admin_post_abo_demande_suppr', array( __CLASS__, 'action_supprimer' ) );
		add_action( 'wp_ajax_abo_deplacer', array( __CLASS__, 'ajax_deplacer' ) );
		add_action( 'wp_ajax_abo_note', array( __CLASS__, 'ajax_note' ) );
		add_action( 'admin_enqueue_scripts', array( __CLASS__, 'assets' ) );
		add_action( 'abo_purge_quotidienne', array( __CLASS__, 'purger' ) );

		if ( ! wp_next_scheduled( 'abo_purge_quotidienne' ) ) {
			wp_schedule_event( time() + HOUR_IN_SECONDS, 'daily', 'abo_purge_quotidienne' );
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
		// Ce greffon s'exécute APRÈS que WPForms a validé la soumission et
		// envoyé ses notifications : `wpforms_process_complete` est une
		// action, pas un filtre, et rien de ce qu'on fait ici ne remonte à
		// WPForms. Le formulaire et le courriel sont donc intacts.
		//
		// Reste le cas d'une erreur de notre côté : elle interromprait
		// l'affichage de la confirmation, après un envoi pourtant réussi.
		// On l'attrape et on la journalise plutôt que de la laisser passer.
		try {
			self::capter_vraiment( $champs, $soumission, $formulaire, $entree_id );
		} catch ( Throwable $e ) {
			error_log( '[ae-back-office] captation de la demande impossible : ' . $e->getMessage() );
		}
	}

	private static function capter_vraiment( $champs, $soumission, $formulaire, $entree_id ) {
		if ( ! is_array( $champs ) ) {
			return;
		}

		$propres = array();
		$nom     = '';
		$courriel = '';

		foreach ( $champs as $champ ) {
			$valeur = $champ['value'] ?? '';
			if ( is_array( $valeur ) ) {
				$valeur = implode( ', ', array_filter( $valeur, 'is_scalar' ) );
			}
			$valeur = trim( (string) $valeur );
			if ( '' === $valeur ) {
				continue;
			}

			$type = $champ['type'] ?? 'text';

			$propres[] = array(
				'nom'    => sanitize_text_field( (string) ( $champ['name'] ?? 'Champ' ) ),
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

		$titre_formulaire = sanitize_text_field(
			(string) ( $formulaire['settings']['form_title'] ?? ( $formulaire['id'] ?? 'Formulaire' ) )
		);

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
			return;
		}

		update_post_meta( $id, '_abo_champs', $propres );
		update_post_meta( $id, '_abo_statut', 'nouvelle' );
		update_post_meta( $id, '_abo_formulaire', $titre_formulaire );
		update_post_meta( $id, '_abo_formulaire_id', (int) ( $formulaire['id'] ?? 0 ) );
		update_post_meta( $id, '_abo_entree_wpforms', (int) $entree_id );
		update_post_meta( $id, '_abo_courriel', $courriel );
		update_post_meta( $id, '_abo_page', esc_url_raw( (string) ( $soumission['page_url'] ?? wp_get_referer() ) ) );
	}

	/* ---------------------------------------------------------------- */
	/* Écran                                                             */
	/* ---------------------------------------------------------------- */

	public static function menu() {
		$nouvelles = self::compter( 'nouvelle' );
		$titre     = 'Demandes';
		if ( $nouvelles ) {
			$titre .= sprintf(
				' <span class="awaiting-mod"><span class="pending-count">%d</span></span>',
				$nouvelles
			);
		}

		add_menu_page(
			'Demandes',
			$titre,
			'edit_posts',
			self::MENU,
			array( __CLASS__, 'ecran' ),
			'dashicons-email-alt',
			4
		);
	}

	public static function assets( $page ) {
		if ( false === strpos( (string) $page, self::MENU ) ) {
			return;
		}
		wp_enqueue_script( 'abo-demandes', ABO_URL . 'assets/js/demandes.js', array(), ABO_VERSION, true );
		wp_localize_script( 'abo-demandes', 'ABO_DEMANDES', array(
			'ajax'    => admin_url( 'admin-ajax.php' ),
			'nonce'   => wp_create_nonce( 'abo_demandes' ),
			'statuts' => self::STATUTS,
		) );
	}

	/** Déplacement d'une fiche d'une colonne à l'autre. */
	public static function ajax_deplacer() {
		check_ajax_referer( 'abo_demandes', 'nonce' );

		$id     = isset( $_POST['demande'] ) ? (int) $_POST['demande'] : 0;
		$statut = isset( $_POST['statut'] ) ? sanitize_key( wp_unslash( $_POST['statut'] ) ) : '';

		if ( ! current_user_can( 'edit_posts' ) || self::TYPE !== get_post_type( $id ) ) {
			wp_send_json_error( array( 'message' => 'Action non autorisée.' ), 403 );
		}
		if ( ! isset( self::STATUTS[ $statut ] ) ) {
			wp_send_json_error( array( 'message' => 'Colonne inconnue.' ), 400 );
		}

		update_post_meta( $id, '_abo_statut', $statut );
		self::journaliser( $id, sprintf( 'déplacée en « %s »', self::STATUTS[ $statut ] ) );

		wp_send_json_success( array( 'id' => $id, 'statut' => $statut ) );
	}

	/** Ajout d'une note interne sur une fiche. */
	public static function ajax_note() {
		check_ajax_referer( 'abo_demandes', 'nonce' );

		$id      = isset( $_POST['demande'] ) ? (int) $_POST['demande'] : 0;
		$message = isset( $_POST['message'] ) ? sanitize_textarea_field( wp_unslash( $_POST['message'] ) ) : '';

		if ( ! current_user_can( 'edit_posts' ) || self::TYPE !== get_post_type( $id ) ) {
			wp_send_json_error( array( 'message' => 'Action non autorisée.' ), 403 );
		}
		if ( '' === trim( $message ) ) {
			wp_send_json_error( array( 'message' => 'Note vide.' ), 400 );
		}

		$note = self::journaliser( $id, $message );
		wp_send_json_success( $note );
	}

	/**
	 * Ajoute une ligne au journal d'une fiche.
	 *
	 * @param int    $id
	 * @param string $message
	 * @return array
	 */
	private static function journaliser( $id, $message ) {
		$journal = get_post_meta( $id, '_abo_journal', true );
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
		update_post_meta( $id, '_abo_journal', $journal );

		return $ligne;
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
					'key'   => '_abo_statut',
					'value' => $statut,
				),
			);
		}

		return count( get_posts( $args ) );
	}

	public static function ecran() {
		$demandes = get_posts( array(
			'post_type'      => self::TYPE,
			'post_status'    => 'publish',
			'posts_per_page' => 300,
			'orderby'        => 'date',
			'order'          => 'DESC',
		) );

		// Toutes les fiches partent au navigateur : l'ouverture d'une fiche
		// et le glisser-déposer se font sans aller-retour serveur.
		$fiches = array();
		$colonnes = array_fill_keys( array_keys( self::STATUTS ), array() );

		foreach ( $demandes as $demande ) {
			$champs  = get_post_meta( $demande->ID, '_abo_champs', true );
			$journal = get_post_meta( $demande->ID, '_abo_journal', true );
			$statut  = get_post_meta( $demande->ID, '_abo_statut', true ) ?: 'nouvelle';
			if ( ! isset( self::STATUTS[ $statut ] ) ) {
				$statut = 'nouvelle';
			}
			$media = (int) get_post_meta( $demande->ID, '_abo_image', true );

			$fiche = array(
				'id'         => $demande->ID,
				'titre'      => $demande->post_title,
				'statut'     => $statut,
				'formulaire' => get_post_meta( $demande->ID, '_abo_formulaire', true ),
				'courriel'   => get_post_meta( $demande->ID, '_abo_courriel', true ),
				'page'       => get_post_meta( $demande->ID, '_abo_page', true ),
				'date'       => get_the_date( 'j M Y, H:i', $demande ),
				'depuis'     => human_time_diff( get_post_time( 'U', true, $demande ) ),
				'champs'     => is_array( $champs ) ? $champs : array(),
				'journal'    => is_array( $journal ) ? $journal : array(),
				'suppr'      => wp_nonce_url(
					admin_url( 'admin-post.php?action=abo_demande_suppr&demande=' . $demande->ID ),
					'abo_demande_' . $demande->ID
				),
			);

			$colonnes[ $statut ][] = $fiche;
			$fiches[ $demande->ID ] = $fiche;
		}

		$wpforms = defined( 'WPFORMS_VERSION' );
		$pro     = $wpforms && class_exists( 'WPForms_Pro' );
		?>
		<div class="wrap abo abo-crm">
			<h1 class="wp-heading-inline">Demandes</h1>
			<hr class="wp-header-end">

			<?php if ( ! $wpforms ) : ?>
				<div class="notice notice-warning inline"><p>
					WPForms n'est pas actif : aucune demande ne peut être captée.
				</p></div>
			<?php elseif ( ! $pro ) : ?>
				<p class="abo-intro">
					WPForms <strong>Lite</strong> n'enregistre pas les soumissions — son écran
					« Entries » est une page de vente. Cet écran les conserve au moment où le
					formulaire est validé. <strong>Le formulaire et l'envoi du courriel ne sont
					pas modifiés</strong> : la captation se greffe après, en lecture seule.
				</p>
			<?php endif; ?>

			<div class="abo-kanban" id="abo-kanban">
				<?php foreach ( self::STATUTS as $cle => $libelle ) : ?>
					<section class="abo-col" data-statut="<?php echo esc_attr( $cle ); ?>">
						<header>
							<h2><?php echo esc_html( $libelle ); ?></h2>
							<span class="abo-n"><?php echo count( $colonnes[ $cle ] ); ?></span>
						</header>
						<div class="abo-pile" data-statut="<?php echo esc_attr( $cle ); ?>">
							<?php foreach ( $colonnes[ $cle ] as $fiche ) : ?>
								<article class="abo-fiche" draggable="true" data-id="<?php echo esc_attr( $fiche['id'] ); ?>">
									<h3><?php echo esc_html( $fiche['titre'] ); ?></h3>
									<p class="abo-meta">
										<?php echo esc_html( $fiche['formulaire'] ); ?> ·
										il y a <?php echo esc_html( $fiche['depuis'] ); ?>
									</p>
									<?php
									$resume = '';
									foreach ( $fiche['champs'] as $champ ) {
										if ( in_array( $champ['type'], array( 'textarea', 'text' ), true )
											&& mb_strlen( $champ['valeur'] ) > 20 ) {
											$resume = $champ['valeur'];
											break;
										}
									}
									?>
									<?php if ( $resume ) : ?>
										<p class="abo-resume"><?php echo esc_html( wp_trim_words( $resume, 16, '…' ) ); ?></p>
									<?php endif; ?>
									<footer>
										<span class="abo-puces"><?php echo count( $fiche['champs'] ); ?> champs</span>
										<?php if ( $fiche['journal'] ) : ?>
											<span class="abo-puces"><?php echo count( $fiche['journal'] ); ?> note<?php echo count( $fiche['journal'] ) > 1 ? 's' : ''; ?></span>
										<?php endif; ?>
									</footer>
								</article>
							<?php endforeach; ?>
							<p class="abo-col-vide">Déposez une fiche ici</p>
						</div>
					</section>
				<?php endforeach; ?>
			</div>

			<?php $purge = (int) get_option( self::OPTION_PURGE, 0 ); ?>
			<p class="description abo-rgpd">
				Ces fiches contiennent des données personnelles, dans un type de contenu privé
				invisible du site public.
				<?php if ( $purge ) : ?>
					Purge automatique après <strong><?php echo (int) $purge; ?> jours</strong>.
				<?php else : ?>
					<strong>Aucune purge automatique n'est réglée</strong> —
					<a href="<?php echo esc_url( admin_url( 'options-general.php?page=abo-reglages' ) ); ?>">à définir dans les réglages</a>.
				<?php endif; ?>
			</p>
		</div>

		<!-- Tiroir de fiche, rempli côté navigateur -->
		<div class="abo-tiroir" id="abo-tiroir" hidden>
			<div class="abo-voile" data-fermer></div>
			<aside class="abo-panneau" role="dialog" aria-modal="true" aria-label="Fiche de demande"></aside>
		</div>

		<script type="application/json" id="abo-fiches"><?php
			echo wp_json_encode( array_values( $fiches ) );
		?></script>
		<?php
	}

	/* ---------------------------------------------------------------- */
	/* Actions                                                           */
	/* ---------------------------------------------------------------- */

	public static function action_statut() {
		$id = isset( $_POST['demande'] ) ? (int) $_POST['demande'] : 0;
		check_admin_referer( 'abo_demande_' . $id );

		if ( ! current_user_can( 'edit_posts' ) || self::TYPE !== get_post_type( $id ) ) {
			wp_die( 'Action non autorisée.' );
		}

		$statut = isset( $_POST['statut'] ) ? sanitize_key( wp_unslash( $_POST['statut'] ) ) : '';
		if ( isset( self::STATUTS[ $statut ] ) ) {
			update_post_meta( $id, '_abo_statut', $statut );
		}

		wp_safe_redirect( wp_get_referer() ?: admin_url( 'admin.php?page=' . self::MENU ) );
		exit;
	}

	public static function action_supprimer() {
		$id = isset( $_POST['demande'] ) ? (int) $_POST['demande'] : 0;
		check_admin_referer( 'abo_demande_' . $id );

		if ( ! current_user_can( 'delete_posts' ) || self::TYPE !== get_post_type( $id ) ) {
			wp_die( 'Action non autorisée.' );
		}

		wp_delete_post( $id, true );
		wp_safe_redirect( wp_get_referer() ?: admin_url( 'admin.php?page=' . self::MENU ) );
		exit;
	}

	/**
	 * Purge des demandes trop anciennes. Rien n'est purgé si le délai
	 * n'a pas été réglé : une suppression silencieuse par défaut serait
	 * pire que pas de purge du tout.
	 */
	public static function purger() {
		$jours = (int) get_option( self::OPTION_PURGE, 0 );
		if ( $jours < 1 ) {
			return;
		}

		$vieilles = get_posts(
			array(
				'post_type'      => self::TYPE,
				'post_status'    => 'publish',
				'posts_per_page' => 200,
				'fields'         => 'ids',
				'date_query'     => array(
					array( 'before' => $jours . ' days ago' ),
				),
			)
		);

		foreach ( $vieilles as $id ) {
			wp_delete_post( $id, true );
		}
	}
}
