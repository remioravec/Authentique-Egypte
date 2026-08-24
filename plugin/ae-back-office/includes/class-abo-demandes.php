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

	/* ---------------------------------------------------------------- */
	/* Présentation                                                      */
	/* ---------------------------------------------------------------- */

	/** Icônes en ligne, au trait, sur une grille de 15. */
	private static function icone( $nom ) {
		$traits = array(
			'dossier'  => '<path d="M2.5 5.5A1.5 1.5 0 0 1 4 4h7a1.5 1.5 0 0 1 1.5 1.5v6A1.5 1.5 0 0 1 11 13H4a1.5 1.5 0 0 1-1.5-1.5v-6Z"/><path d="M5.5 4V3a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1v1"/>',
			'diese'    => '<path d="M6 2.5 4.5 13M10.5 2.5 9 13M2.5 5.5h11M2 10h11"/>',
			'personne' => '<circle cx="7.5" cy="5" r="2.5"/><path d="M2.5 13.5a5 5 0 0 1 10 0"/>',
			'horloge'  => '<circle cx="7.5" cy="7.5" r="5.5"/><path d="M7.5 4.5v3.2l2.2 1.3"/>',
			'bulle'    => '<path d="M13 8.5A2.5 2.5 0 0 1 10.5 11H5l-2.5 2V4a1.5 1.5 0 0 1 1.5-1.5h6.5A2.5 2.5 0 0 1 13 5v3.5Z"/>',
		);

		if ( empty( $traits[ $nom ] ) ) {
			return '';
		}

		return '<svg class="abo-i" viewBox="0 0 15 15" fill="none" stroke="currentColor" '
			. 'stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
			. $traits[ $nom ] . '</svg>';
	}

	/** Initiales d'un intitulé, pour la pastille. */
	public static function initiales( $texte ) {
		$texte  = trim( preg_replace( '/[\x{2014}\x{2013}<>@].*/u', '', (string) $texte ) );
		$mots   = preg_split( '/[\s._-]+/u', $texte, -1, PREG_SPLIT_NO_EMPTY );
		$sortie = '';
		foreach ( array_slice( $mots, 0, 2 ) as $mot ) {
			$sortie .= mb_strtoupper( mb_substr( $mot, 0, 1 ) );
		}

		return $sortie ?: '?';
	}

	/**
	 * Couleur de pastille, déduite de l'intitulé.
	 *
	 * Toujours la même pour le même nom : la personne reste
	 * reconnaissable d'une colonne à l'autre, et d'un jour à l'autre.
	 */
	public static function teinte( $texte ) {
		$fonds  = array( '#E8F2FB', '#FDF0E4', '#FBEAF0', '#EAF6EE', '#F0EDFB', '#E6F5F5', '#FBF3E0' );
		$encres = array( '#0A4B78', '#8A5700', '#9B2C55', '#1D6B34', '#4A3B96', '#0F6E73', '#7A5605' );
		$index  = abs( crc32( (string) $texte ) ) % count( $fonds );

		return array( $fonds[ $index ], $encres[ $index ] );
	}

	/**
	 * La ligne « chiffre » d'une carte.
	 *
	 * On cherche le champ le plus parlant pour l'agence — budget,
	 * voyageurs, durée, dates — plutôt qu'un compte de champs, qui ne
	 * dit rien à personne.
	 */
	public static function chiffre( $champs ) {
		$pistes = '/budget|montant|prix|personne|voyageur|adulte|enfant|dur[\x{e9}e]e|jour|date|p[\x{e9}e]riode/iu';

		foreach ( $champs as $champ ) {
			if ( preg_match( $pistes, $champ['nom'] ) ) {
				return wp_trim_words( $champ['valeur'], 8, '…' );
			}
		}

		$n = count( $champs );

		return $n . ' champ' . ( $n > 1 ? 's' : '' );
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
							<span class="abo-pastille"><?php echo esc_html( $libelle ); ?></span>
							<span class="abo-n"><?php echo count( $colonnes[ $cle ] ); ?></span>
						</header>
						<div class="abo-pile" data-statut="<?php echo esc_attr( $cle ); ?>">
							<?php foreach ( $colonnes[ $cle ] as $fiche ) : ?>
								<?php
								list( $fond, $encre )   = self::teinte( $fiche['titre'] );
								list( $ffond, $fencre ) = self::teinte( $fiche['formulaire'] );
								$nom = trim( preg_replace( '/\s*\x{2014}.*$/u', '', $fiche['titre'] ) );
								?>
								<article class="abo-fiche" draggable="true" tabindex="0" role="button"
									data-id="<?php echo esc_attr( $fiche['id'] ); ?>"
									aria-label="Ouvrir la fiche de <?php echo esc_attr( $nom ); ?>">
									<header>
										<span class="abo-ava" style="background:<?php echo esc_attr( $fond ); ?>;color:<?php echo esc_attr( $encre ); ?>"><?php
											echo esc_html( self::initiales( $fiche['titre'] ) );
										?></span>
										<h3><?php echo esc_html( $nom ); ?></h3>
										<?php if ( $fiche['journal'] ) : ?>
											<span class="abo-cpt" title="Notes de suivi"><?php
												echo self::icone( 'bulle' ); // phpcs:ignore WordPress.Security.EscapingOutput
												echo esc_html( count( $fiche['journal'] ) );
											?></span>
										<?php endif; ?>
									</header>
									<div class="abo-lignes">
										<p class="abo-ligne">
											<?php echo self::icone( 'dossier' ); // phpcs:ignore WordPress.Security.EscapingOutput ?>
											<span class="abo-tag" style="background:<?php echo esc_attr( $ffond ); ?>;color:<?php echo esc_attr( $fencre ); ?>"><?php
												echo esc_html( $fiche['formulaire'] );
											?></span>
										</p>
										<p class="abo-ligne">
											<?php echo self::icone( 'diese' ); // phpcs:ignore WordPress.Security.EscapingOutput ?>
											<span><?php echo esc_html( self::chiffre( $fiche['champs'] ) ); ?></span>
										</p>
										<?php if ( $fiche['courriel'] ) : ?>
											<p class="abo-ligne">
												<?php echo self::icone( 'personne' ); // phpcs:ignore WordPress.Security.EscapingOutput ?>
												<span class="abo-chip"><span class="abo-ava abo-ava--mini"
													style="background:<?php echo esc_attr( $fond ); ?>;color:<?php echo esc_attr( $encre ); ?>"><?php
													echo esc_html( self::initiales( $fiche['titre'] ) );
												?></span><span class="abo-chip-txt"><?php
													echo esc_html( $fiche['courriel'] );
												?></span></span>
											</p>
										<?php endif; ?>
										<p class="abo-ligne">
											<?php echo self::icone( 'horloge' ); // phpcs:ignore WordPress.Security.EscapingOutput ?>
											<span>il y a <?php echo esc_html( $fiche['depuis'] ); ?></span>
										</p>
									</div>
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
