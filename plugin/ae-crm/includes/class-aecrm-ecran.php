<?php
/**
 * L'écran « Demandes » : le pipeline, les cartes, la fiche client.
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

class AECRM_Ecran {

	const MENU = 'ae-demandes';

	/**
	 * Le suffixe de page renvoyé par add_menu_page().
	 *
	 * On compare le hook exact plutôt que de chercher le mot « demandes »
	 * dans la chaîne : deviner le nom d'un écran, c'est charger ses
	 * fichiers sur un écran voisin, ou pas du tout sur le bon.
	 */
	private static $ecran = '';

	public static function init() {
		add_action( 'admin_menu', array( __CLASS__, 'menu' ), 9 );
		add_action( 'admin_enqueue_scripts', array( __CLASS__, 'assets' ) );
		add_action( 'wp_ajax_aecrm_deplacer', array( __CLASS__, 'ajax_deplacer' ) );
		add_action( 'wp_ajax_aecrm_note', array( __CLASS__, 'ajax_note' ) );
		add_action( 'admin_post_aecrm_supprimer', array( __CLASS__, 'action_supprimer' ) );
	}

	public static function menu() {
		$nouvelles = AECRM_Demandes::compter( 'nouvelle' );
		$titre     = 'Demandes';
		if ( $nouvelles ) {
			$titre .= sprintf(
				' <span class="awaiting-mod"><span class="pending-count">%d</span></span>',
				$nouvelles
			);
		}

		self::$ecran = add_menu_page(
			'Demandes',
			$titre,
			'edit_posts',
			self::MENU,
			array( __CLASS__, 'afficher' ),
			'dashicons-email-alt',
			4
		);
	}

	public static function assets( $page ) {
		if ( ! self::$ecran || $page !== self::$ecran ) {
			return;
		}

		// La date du fichier plutôt que la version du plugin : une
		// retouche de CSS est visible sans changer de version, et aucun
		// cache — LiteSpeed compris — ne peut servir l'ancienne.
		$css = AECRM_DIR . 'assets/css/crm.css';
		$js  = AECRM_DIR . 'assets/js/crm.js';

		wp_enqueue_style(
			'aecrm',
			AECRM_URL . 'assets/css/crm.css',
			array(),
			file_exists( $css ) ? (string) filemtime( $css ) : AECRM_VERSION
		);
		wp_enqueue_script(
			'aecrm',
			AECRM_URL . 'assets/js/crm.js',
			array(),
			file_exists( $js ) ? (string) filemtime( $js ) : AECRM_VERSION,
			true
		);
		wp_localize_script( 'aecrm', 'AE_CRM', array(
			'ajax'    => admin_url( 'admin-ajax.php' ),
			'nonce'   => wp_create_nonce( 'aecrm' ),
			'statuts' => AECRM_Demandes::STATUTS,
		) );
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

		return '<svg class="crm-i" viewBox="0 0 15 15" fill="none" stroke="currentColor" '
			. 'stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
			. $traits[ $nom ] . '</svg>';
	}

	/** Initiales d'un intitulé, pour la pastille. */
	public static function initiales( $texte ) {
		$texte  = trim( preg_replace( '/[\x{2014}\x{2013}<>@].*/u', '', (string) $texte ) );
		$mots   = preg_split( '/[\s._-]+/u', $texte, -1, PREG_SPLIT_NO_EMPTY );
		$sortie = '';
		foreach ( array_slice( (array) $mots, 0, 2 ) as $mot ) {
			$sortie .= mb_strtoupper( mb_substr( $mot, 0, 1 ) );
		}

		return $sortie ? $sortie : '?';
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
	 * On cherche le renseignement le plus parlant pour l'agence —
	 * budget, voyageurs, durée, dates — plutôt qu'un décompte de champs,
	 * qui ne dit rien à personne.
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

	/* ---------------------------------------------------------------- */
	/* Rendu                                                             */
	/* ---------------------------------------------------------------- */

	public static function afficher() {
		$fiches   = AECRM_Demandes::toutes();
		$colonnes = array_fill_keys( array_keys( AECRM_Demandes::STATUTS ), array() );
		foreach ( $fiches as $fiche ) {
			$colonnes[ $fiche['statut'] ][] = $fiche;
		}

		$wpforms = defined( 'WPFORMS_VERSION' );
		$pro     = $wpforms && class_exists( 'WPForms_Pro' );
		?>
		<div class="wrap crm">
			<h1 class="wp-heading-inline">Demandes</h1>
			<hr class="wp-header-end">

			<?php
			// Si la feuille de style n'est pas arrivée, l'écran s'affiche
			// nu et rien ne l'explique. Ce bandeau est masqué PAR la
			// feuille elle-même : il n'apparaît donc que si elle manque.
			?>
			<div class="crm-panne notice notice-error"><p>
				<strong>La feuille de style de cet écran ne s'est pas chargée.</strong>
				Le tableau s'affiche donc sans mise en forme. Videz le cache
				(LiteSpeed&nbsp;→&nbsp;<em>Purger tout</em>) puis rechargez avec
				<kbd>Ctrl</kbd>+<kbd>Maj</kbd>+<kbd>R</kbd>. Si cela persiste,
				réinstallez l'extension.
			</p></div>

			<?php if ( ! $wpforms ) : ?>
				<div class="notice notice-warning inline"><p>
					<strong>WPForms n'est pas actif</strong> : aucune nouvelle demande ne peut
					être captée. Les demandes déjà enregistrées restent visibles ci-dessous.
				</p></div>
			<?php elseif ( ! $pro ) : ?>
				<p class="crm-intro">
					WPForms <strong>Lite</strong> n'enregistre pas les soumissions — son écran
					« Entries » est une page de vente. Cet écran les conserve au moment où le
					formulaire est validé. <strong>Le formulaire et l'envoi du courriel ne sont
					pas modifiés</strong> : la captation se greffe après, en lecture seule.
				</p>
			<?php endif; ?>

			<?php if ( ! $fiches ) : ?>
				<div class="crm-vide">
					<p><strong>Aucune demande pour l'instant.</strong></p>
					<p>
						Les demandes envoyées depuis les formulaires du site apparaîtront ici,
						dans la colonne <em>Nouvelle</em>. Elles continueront d'arriver par
						courriel comme aujourd'hui : cet écran s'ajoute, il ne remplace rien.
					</p>
				</div>
			<?php endif; ?>

			<div class="crm-tableau" id="crm-tableau">
				<?php foreach ( AECRM_Demandes::STATUTS as $cle => $libelle ) : ?>
					<section class="crm-col<?php echo empty( $colonnes[ $cle ] ) ? ' crm-col--vide' : ''; ?>"
						data-statut="<?php echo esc_attr( $cle ); ?>">
						<header>
							<span class="crm-pastille"><?php echo esc_html( $libelle ); ?></span>
							<span class="crm-n"><?php echo count( $colonnes[ $cle ] ); ?></span>
						</header>
						<div class="crm-pile" data-statut="<?php echo esc_attr( $cle ); ?>">
							<?php foreach ( $colonnes[ $cle ] as $fiche ) : ?>
								<?php
								list( $fond, $encre )   = self::teinte( $fiche['titre'] );
								list( $ffond, $fencre ) = self::teinte( $fiche['formulaire'] );
								$nom = trim( preg_replace( '/\s*\x{2014}.*$/u', '', $fiche['titre'] ) );
								?>
								<article class="crm-carte" draggable="true" tabindex="0" role="button"
									data-id="<?php echo esc_attr( $fiche['id'] ); ?>"
									aria-label="Ouvrir la fiche de <?php echo esc_attr( $nom ); ?>">
									<header>
										<span class="crm-ava" style="background:<?php echo esc_attr( $fond ); ?>;color:<?php echo esc_attr( $encre ); ?>"><?php
											echo esc_html( self::initiales( $fiche['titre'] ) );
										?></span>
										<h3><?php echo esc_html( $nom ); ?></h3>
										<span class="crm-cpt"<?php echo $fiche['journal'] ? '' : ' hidden'; ?> title="Notes de suivi"><?php
											echo self::icone( 'bulle' ); // phpcs:ignore WordPress.Security.EscapingOutput
											?><span class="crm-cpt-n"><?php echo count( $fiche['journal'] ); ?></span>
										</span>
									</header>
									<div class="crm-lignes">
										<p class="crm-ligne">
											<?php echo self::icone( 'dossier' ); // phpcs:ignore WordPress.Security.EscapingOutput ?>
											<span class="crm-tag" style="background:<?php echo esc_attr( $ffond ); ?>;color:<?php echo esc_attr( $fencre ); ?>"><?php
												echo esc_html( $fiche['formulaire'] ? $fiche['formulaire'] : 'Formulaire' );
											?></span>
										</p>
										<p class="crm-ligne">
											<?php echo self::icone( 'diese' ); // phpcs:ignore WordPress.Security.EscapingOutput ?>
											<span><?php echo esc_html( self::chiffre( $fiche['champs'] ) ); ?></span>
										</p>
										<?php if ( $fiche['courriel'] ) : ?>
											<p class="crm-ligne">
												<?php echo self::icone( 'personne' ); // phpcs:ignore WordPress.Security.EscapingOutput ?>
												<span class="crm-puce"><span class="crm-ava crm-ava--mini"
													style="background:<?php echo esc_attr( $fond ); ?>;color:<?php echo esc_attr( $encre ); ?>"><?php
													echo esc_html( self::initiales( $fiche['titre'] ) );
												?></span><span class="crm-puce-txt"><?php
													echo esc_html( $fiche['courriel'] );
												?></span></span>
											</p>
										<?php endif; ?>
										<p class="crm-ligne">
											<?php echo self::icone( 'horloge' ); // phpcs:ignore WordPress.Security.EscapingOutput ?>
											<span>il y a <?php echo esc_html( $fiche['depuis'] ); ?></span>
										</p>
									</div>
								</article>
							<?php endforeach; ?>
							<p class="crm-col-vide">Déposez une fiche ici</p>
						</div>
					</section>
				<?php endforeach; ?>
			</div>

			<?php $purge = (int) get_option( AECRM_Demandes::OPTION_PURGE, 0 ); ?>
			<p class="description crm-rgpd">
				Ces fiches contiennent des données personnelles, dans un type de contenu privé
				invisible du site public.
				<?php if ( $purge ) : ?>
					Purge automatique après <strong><?php echo (int) $purge; ?> jours</strong>.
				<?php else : ?>
					<strong>Aucune purge automatique n'est réglée</strong> —
					<a href="<?php echo esc_url( admin_url( 'admin.php?page=' . AECRM_Reglages::MENU ) ); ?>">à définir dans les réglages</a>.
				<?php endif; ?>
			</p>
		</div>

		<!-- Fiche client, remplie côté navigateur -->
		<div class="crm-tiroir" id="crm-tiroir" hidden>
			<div class="crm-voile" data-fermer></div>
			<aside class="crm-panneau" role="dialog" aria-modal="true" aria-label="Fiche de demande"></aside>
		</div>

		<script type="application/json" id="crm-fiches"><?php
			echo wp_json_encode( $fiches );
		?></script>
		<?php
	}

	/* ---------------------------------------------------------------- */
	/* Actions                                                           */
	/* ---------------------------------------------------------------- */

	public static function ajax_deplacer() {
		check_ajax_referer( 'aecrm', 'nonce' );

		$id     = isset( $_POST['demande'] ) ? (int) $_POST['demande'] : 0;
		$statut = isset( $_POST['statut'] ) ? sanitize_key( wp_unslash( $_POST['statut'] ) ) : '';

		if ( ! current_user_can( 'edit_posts' ) || AECRM_Demandes::TYPE !== get_post_type( $id ) ) {
			wp_send_json_error( array( 'message' => 'Action non autorisée.' ), 403 );
		}
		if ( ! isset( AECRM_Demandes::STATUTS[ $statut ] ) ) {
			wp_send_json_error( array( 'message' => 'Colonne inconnue.' ), 400 );
		}

		AECRM_Demandes::deplacer( $id, $statut );

		wp_send_json_success( array( 'id' => $id, 'statut' => $statut ) );
	}

	public static function ajax_note() {
		check_ajax_referer( 'aecrm', 'nonce' );

		$id      = isset( $_POST['demande'] ) ? (int) $_POST['demande'] : 0;
		$message = isset( $_POST['message'] ) ? sanitize_textarea_field( wp_unslash( $_POST['message'] ) ) : '';

		if ( ! current_user_can( 'edit_posts' ) || AECRM_Demandes::TYPE !== get_post_type( $id ) ) {
			wp_send_json_error( array( 'message' => 'Action non autorisée.' ), 403 );
		}
		if ( '' === trim( $message ) ) {
			wp_send_json_error( array( 'message' => 'Note vide.' ), 400 );
		}

		wp_send_json_success( AECRM_Demandes::journaliser( $id, $message ) );
	}

	public static function action_supprimer() {
		$id = isset( $_GET['demande'] ) ? (int) $_GET['demande'] : 0;
		check_admin_referer( 'aecrm_demande_' . $id );

		if ( ! current_user_can( 'delete_posts' ) || AECRM_Demandes::TYPE !== get_post_type( $id ) ) {
			wp_die( 'Action non autorisée.' );
		}

		wp_delete_post( $id, true );
		wp_safe_redirect( admin_url( 'admin.php?page=' . self::MENU ) );
		exit;
	}
}
