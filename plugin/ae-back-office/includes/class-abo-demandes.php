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
		$filtre = isset( $_GET['statut'] ) ? sanitize_key( wp_unslash( $_GET['statut'] ) ) : '';

		$args = array(
			'post_type'      => self::TYPE,
			'post_status'    => 'publish',
			'posts_per_page' => 100,
			'orderby'        => 'date',
			'order'          => 'DESC',
		);
		if ( $filtre && isset( self::STATUTS[ $filtre ] ) ) {
			$args['meta_query'] = array(
				array(
					'key'   => '_abo_statut',
					'value' => $filtre,
				),
			);
		}

		$demandes = get_posts( $args );
		$wpforms  = defined( 'WPFORMS_VERSION' );
		$pro      = $wpforms && class_exists( 'WPForms_Pro' );
		?>
		<div class="wrap abo">
			<h1>Demandes</h1>

			<?php if ( ! $wpforms ) : ?>
				<div class="notice notice-warning"><p>
					WPForms n'est pas actif : aucune demande ne peut être captée.
				</p></div>
			<?php elseif ( ! $pro ) : ?>
				<p class="abo-intro">
					WPForms <strong>Lite</strong> n'enregistre pas les soumissions — son écran
					« Entries » est une page de vente, et les demandes partent uniquement par
					courriel. Cet écran les conserve en base au moment où le formulaire est
					validé : un courriel classé en indésirable ne fait plus perdre une demande.
					L'envoi du courriel, lui, continue normalement.
				</p>
			<?php endif; ?>

			<div class="abo-onglets">
				<a class="abo-onglet <?php echo '' === $filtre ? 'actif' : ''; ?>"
					href="<?php echo esc_url( admin_url( 'admin.php?page=' . self::MENU ) ); ?>">
					Toutes <span><?php echo (int) self::compter(); ?></span>
				</a>
				<?php foreach ( self::STATUTS as $cle => $libelle ) : ?>
					<a class="abo-onglet <?php echo $filtre === $cle ? 'actif' : ''; ?>"
						href="<?php echo esc_url( admin_url( 'admin.php?page=' . self::MENU . '&statut=' . $cle ) ); ?>">
						<?php echo esc_html( $libelle ); ?> <span><?php echo (int) self::compter( $cle ); ?></span>
					</a>
				<?php endforeach; ?>
			</div>

			<?php if ( empty( $demandes ) ) : ?>
				<p>Aucune demande <?php echo $filtre ? 'dans cet état' : 'pour l\'instant'; ?>.</p>
			<?php endif; ?>

			<?php foreach ( $demandes as $demande ) : ?>
				<?php
				$champs   = get_post_meta( $demande->ID, '_abo_champs', true );
				$statut   = get_post_meta( $demande->ID, '_abo_statut', true ) ?: 'nouvelle';
				$courriel = get_post_meta( $demande->ID, '_abo_courriel', true );
				$origine  = get_post_meta( $demande->ID, '_abo_page', true );
				?>
				<section class="abo-demande abo-demande--<?php echo esc_attr( $statut ); ?>">
					<header>
						<h2>
							<?php echo esc_html( $demande->post_title ); ?>
							<span class="abo-etat abo-etat--<?php echo esc_attr( 'nouvelle' === $statut ? 'draft' : 'publish' ); ?>">
								<?php echo esc_html( self::STATUTS[ $statut ] ?? $statut ); ?>
							</span>
						</h2>
						<p>
							<?php echo esc_html( get_post_meta( $demande->ID, '_abo_formulaire', true ) ); ?>
							· <?php echo esc_html( get_the_date( 'j M Y, H:i', $demande ) ); ?>
							<?php if ( $origine ) : ?>
								· <a href="<?php echo esc_url( $origine ); ?>" target="_blank" rel="noreferrer">page d'origine</a>
							<?php endif; ?>
						</p>
					</header>

					<?php if ( is_array( $champs ) ) : ?>
						<dl class="abo-champs">
							<?php foreach ( $champs as $champ ) : ?>
								<div>
									<dt><?php echo esc_html( $champ['nom'] ); ?></dt>
									<dd><?php echo nl2br( esc_html( $champ['valeur'] ) ); ?></dd>
								</div>
							<?php endforeach; ?>
						</dl>
					<?php endif; ?>

					<footer>
						<?php if ( $courriel ) : ?>
							<a class="button button-primary"
								href="<?php echo esc_url( 'mailto:' . $courriel . '?subject=' . rawurlencode( 'Votre voyage en Égypte' ) ); ?>">
								Répondre
							</a>
						<?php endif; ?>

						<form method="post" action="<?php echo esc_url( admin_url( 'admin-post.php' ) ); ?>">
							<?php wp_nonce_field( 'abo_demande_' . $demande->ID ); ?>
							<input type="hidden" name="action" value="abo_demande_statut">
							<input type="hidden" name="demande" value="<?php echo esc_attr( $demande->ID ); ?>">
							<select name="statut" onchange="this.form.submit()">
								<?php foreach ( self::STATUTS as $cle => $libelle ) : ?>
									<option value="<?php echo esc_attr( $cle ); ?>" <?php selected( $statut, $cle ); ?>>
										<?php echo esc_html( $libelle ); ?>
									</option>
								<?php endforeach; ?>
							</select>
						</form>

						<form method="post" action="<?php echo esc_url( admin_url( 'admin-post.php' ) ); ?>"
							onsubmit="return confirm('Supprimer définitivement cette demande ?')">
							<?php wp_nonce_field( 'abo_demande_' . $demande->ID ); ?>
							<input type="hidden" name="action" value="abo_demande_suppr">
							<input type="hidden" name="demande" value="<?php echo esc_attr( $demande->ID ); ?>">
							<button class="button-link abo-suppr">Supprimer</button>
						</form>
					</footer>
				</section>
			<?php endforeach; ?>

			<?php $purge = (int) get_option( self::OPTION_PURGE, 0 ); ?>
			<p class="description" style="margin-top:26px;max-width:70ch">
				Ces enregistrements contiennent des données personnelles. Ils vivent dans un type de
				contenu privé, invisible du site public.
				<?php if ( $purge ) : ?>
					Purge automatique après <strong><?php echo (int) $purge; ?> jours</strong>.
				<?php else : ?>
					<strong>Aucune purge automatique n'est réglée</strong> — à définir dans
					<a href="<?php echo esc_url( admin_url( 'options-general.php?page=abo-reglages' ) ); ?>">Réglages → Back-office simplifié</a>.
				<?php endif; ?>
			</p>
		</div>
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
