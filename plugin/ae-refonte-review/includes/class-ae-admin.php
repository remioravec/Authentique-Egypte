<?php
/**
 * Back-office de la refonte.
 *
 * Un menu de premier niveau « Refonte », avec :
 *   – le parcours des maquettes (liste native du type de contenu) ;
 *   – un tableau des demandes, filtrable par maquette, statut et type ;
 *   – les réglages (adresse de notification, reroutage des liens).
 *
 * La fiche d'une maquette porte trois champs : le fichier HTML servi,
 * l'URL du site en ligne qu'elle remplacera, et son état dans le parcours.
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

class AE_Refonte_Admin {

	const MENU = 'ae-refonte';

	public static function init() {
		add_action( 'admin_menu', array( __CLASS__, 'menu' ) );
		add_action( 'add_meta_boxes', array( __CLASS__, 'boites' ) );
		add_action( 'save_post_' . AE_Refonte_Types::MAQUETTE, array( __CLASS__, 'enregistrer_maquette' ), 10, 2 );
		add_action( 'admin_init', array( __CLASS__, 'reglages' ) );
		add_action( 'admin_post_ae_refonte_statut', array( __CLASS__, 'changer_statut' ) );
	}

	public static function menu() {
		add_menu_page(
			'Refonte',
			'Refonte',
			AE_Refonte_Roles::CAP_GERER,
			self::MENU,
			array( __CLASS__, 'ecran_demandes' ),
			'dashicons-art',
			58
		);

		add_submenu_page( self::MENU, 'Demandes', 'Demandes', AE_Refonte_Roles::CAP_GERER, self::MENU, array( __CLASS__, 'ecran_demandes' ) );

		add_submenu_page(
			self::MENU,
			'Maquettes',
			'Maquettes',
			AE_Refonte_Roles::CAP_GERER,
			'edit.php?post_type=' . AE_Refonte_Types::MAQUETTE
		);

		add_submenu_page( self::MENU, 'Réglages', 'Réglages', AE_Refonte_Roles::CAP_GERER, self::MENU . '-reglages', array( __CLASS__, 'ecran_reglages' ) );
	}

	/* ---------------------------------------------------------------- */
	/* Fiche maquette                                                    */
	/* ---------------------------------------------------------------- */

	public static function boites() {
		add_meta_box(
			'ae-refonte-maquette',
			'Maquette',
			array( __CLASS__, 'boite_maquette' ),
			AE_Refonte_Types::MAQUETTE,
			'normal',
			'high'
		);
	}

	public static function boite_maquette( $post ) {
		wp_nonce_field( 'ae_refonte_maquette', 'ae_refonte_maquette_nonce' );

		$fichier = get_post_meta( $post->ID, '_ae_fichier', true );
		$cible   = get_post_meta( $post->ID, '_ae_url_cible', true );
		$etat    = get_post_meta( $post->ID, '_ae_etat', true ) ?: 'a_revoir';

		$disponibles = glob( AE_REFONTE_MAQUETTES_DIR . '*.html' ) ?: array();
		?>
		<p>
			<label for="ae_fichier"><strong>Fichier HTML servi</strong></label><br>
			<select name="ae_fichier" id="ae_fichier" style="min-width:340px">
				<option value="">— choisir —</option>
				<?php foreach ( $disponibles as $chemin ) : ?>
					<?php $nom = basename( $chemin ); ?>
					<option value="<?php echo esc_attr( $nom ); ?>" <?php selected( $fichier, $nom ); ?>>
						<?php echo esc_html( $nom ); ?>
					</option>
				<?php endforeach; ?>
			</select><br>
			<span class="description">
				Déposé dans <code><?php echo esc_html( AE_REFONTE_MAQUETTES_DIR ); ?></code>.
				<?php if ( empty( $disponibles ) ) : ?>
					<strong>Aucun fichier trouvé : déployez d'abord le dossier <code>maquettes/</code>.</strong>
				<?php endif; ?>
			</span>
		</p>

		<p>
			<label for="ae_url_cible"><strong>Page du site en ligne remplacée</strong></label><br>
			<input type="url" name="ae_url_cible" id="ae_url_cible" class="regular-text" style="min-width:340px"
				value="<?php echo esc_attr( $cible ); ?>" placeholder="https://authentiquegypte.com/…"><br>
			<span class="description">
				Facultatif. Renseignée, les liens du parcours qui pointent vers cette URL sont redirigés
				vers la maquette, pour que la navigation de relecture reste cohérente. Le site en ligne
				n'est jamais modifié.
			</span>
		</p>

		<p>
			<label for="ae_etat"><strong>État</strong></label><br>
			<select name="ae_etat" id="ae_etat">
				<?php foreach ( AE_Refonte_Types::ETATS as $cle => $libelle ) : ?>
					<option value="<?php echo esc_attr( $cle ); ?>" <?php selected( $etat, $cle ); ?>>
						<?php echo esc_html( $libelle ); ?>
					</option>
				<?php endforeach; ?>
			</select>
		</p>

		<p>
			<strong>Ordre dans le parcours :</strong> champ « Ordre » du bloc <em>Attributs</em>.
			<?php if ( 'auto-draft' !== $post->post_status ) : ?>
				<br><strong>URL de relecture :</strong>
				<a href="<?php echo esc_url( get_permalink( $post ) ); ?>" target="_blank" rel="noreferrer">
					<?php echo esc_html( get_permalink( $post ) ); ?>
				</a>
			<?php endif; ?>
		</p>
		<?php
	}

	public static function enregistrer_maquette( $post_id, $post ) {
		if ( defined( 'DOING_AUTOSAVE' ) && DOING_AUTOSAVE ) {
			return;
		}
		if ( ! isset( $_POST['ae_refonte_maquette_nonce'] )
			|| ! wp_verify_nonce( sanitize_key( wp_unslash( $_POST['ae_refonte_maquette_nonce'] ) ), 'ae_refonte_maquette' ) ) {
			return;
		}
		if ( ! current_user_can( 'edit_post', $post_id ) ) {
			return;
		}

		$fichier = isset( $_POST['ae_fichier'] ) ? basename( sanitize_file_name( wp_unslash( $_POST['ae_fichier'] ) ) ) : '';
		update_post_meta( $post_id, '_ae_fichier', $fichier );

		$cible = isset( $_POST['ae_url_cible'] ) ? esc_url_raw( wp_unslash( $_POST['ae_url_cible'] ) ) : '';
		update_post_meta( $post_id, '_ae_url_cible', $cible );

		$etat = isset( $_POST['ae_etat'] ) ? sanitize_key( wp_unslash( $_POST['ae_etat'] ) ) : 'a_revoir';
		if ( ! array_key_exists( $etat, AE_Refonte_Types::ETATS ) ) {
			$etat = 'a_revoir';
		}
		update_post_meta( $post_id, '_ae_etat', $etat );
	}

	/* ---------------------------------------------------------------- */
	/* Écran des demandes                                                */
	/* ---------------------------------------------------------------- */

	public static function ecran_demandes() {
		$maquette = isset( $_GET['maquette'] ) ? (int) $_GET['maquette'] : 0;
		$statut   = isset( $_GET['statut'] ) ? sanitize_key( wp_unslash( $_GET['statut'] ) ) : '';
		$type     = isset( $_GET['type'] ) ? sanitize_key( wp_unslash( $_GET['type'] ) ) : '';

		$meta = array();
		if ( $maquette ) {
			$meta[] = array(
				'key'   => '_ae_maquette',
				'value' => $maquette,
			);
		}
		if ( $statut && array_key_exists( $statut, AE_Refonte_Types::STATUTS_NOTE ) ) {
			$meta[] = array(
				'key'   => '_ae_statut',
				'value' => $statut,
			);
		}
		if ( $type && array_key_exists( $type, AE_Refonte_Types::TYPES_NOTE ) ) {
			$meta[] = array(
				'key'   => '_ae_type',
				'value' => $type,
			);
		}

		$args = array(
			'post_type'      => AE_Refonte_Types::NOTE,
			'post_status'    => 'publish',
			'posts_per_page' => -1,
			'orderby'        => 'date',
			'order'          => 'DESC',
		);
		if ( $meta ) {
			$args['meta_query'] = $meta;
		}

		$notes    = get_posts( $args );
		$parcours = AE_Refonte_Types::parcours();
		?>
		<div class="wrap">
			<h1>Demandes de la relecture</h1>

			<p>
				Export :
				<a class="button" href="<?php echo esc_url( rest_url( AE_Refonte_Rest::NAMESPACE_REST . '/export?format=csv&_wpnonce=' . wp_create_nonce( 'wp_rest' ) ) ); ?>">CSV</a>
				<a class="button" href="<?php echo esc_url( rest_url( AE_Refonte_Rest::NAMESPACE_REST . '/export?_wpnonce=' . wp_create_nonce( 'wp_rest' ) ) ); ?>">JSON</a>
			</p>

			<form method="get" style="margin:14px 0">
				<input type="hidden" name="page" value="<?php echo esc_attr( self::MENU ); ?>">
				<select name="maquette">
					<option value="0">Toutes les maquettes</option>
					<?php foreach ( $parcours as $m ) : ?>
						<option value="<?php echo esc_attr( $m->ID ); ?>" <?php selected( $maquette, $m->ID ); ?>>
							<?php echo esc_html( $m->post_title ); ?>
						</option>
					<?php endforeach; ?>
				</select>
				<select name="statut">
					<option value="">Tous les statuts</option>
					<?php foreach ( AE_Refonte_Types::STATUTS_NOTE as $cle => $lib ) : ?>
						<option value="<?php echo esc_attr( $cle ); ?>" <?php selected( $statut, $cle ); ?>><?php echo esc_html( $lib ); ?></option>
					<?php endforeach; ?>
				</select>
				<select name="type">
					<option value="">Tous les types</option>
					<?php foreach ( AE_Refonte_Types::TYPES_NOTE as $cle => $lib ) : ?>
						<option value="<?php echo esc_attr( $cle ); ?>" <?php selected( $type, $cle ); ?>><?php echo esc_html( $lib ); ?></option>
					<?php endforeach; ?>
				</select>
				<button class="button">Filtrer</button>
			</form>

			<table class="widefat striped">
				<thead>
					<tr>
						<th style="width:150px">Maquette</th>
						<th style="width:90px">Type</th>
						<th>Demande</th>
						<th style="width:220px">Proposition</th>
						<th style="width:130px">Auteur</th>
						<th style="width:220px">Statut</th>
					</tr>
				</thead>
				<tbody>
				<?php if ( empty( $notes ) ) : ?>
					<tr><td colspan="6">Aucune demande pour ces critères.</td></tr>
				<?php endif; ?>
				<?php foreach ( $notes as $note ) : ?>
					<?php
					$donnees   = AE_Refonte_Rest::formater_note( $note );
					$url_page  = get_permalink( $donnees['maquette'] );
					?>
					<tr>
						<td>
							<a href="<?php echo esc_url( $url_page . '#ae-note-' . $note->ID ); ?>" target="_blank" rel="noreferrer">
								<?php echo esc_html( get_the_title( $donnees['maquette'] ) ); ?>
							</a>
							<?php if ( $donnees['largeur'] ) : ?>
								<br><span class="description"><?php echo esc_html( $donnees['largeur'] ); ?> px de large</span>
							<?php endif; ?>
						</td>
						<td><?php echo esc_html( AE_Refonte_Types::TYPES_NOTE[ $donnees['type'] ] ?? $donnees['type'] ); ?></td>
						<td>
							<?php echo wp_kses_post( wpautop( $donnees['message'] ) ); ?>
							<?php if ( $donnees['ancre'] ) : ?>
								<p class="description">Sur : « <?php echo esc_html( $donnees['ancre'] ); ?> »</p>
							<?php endif; ?>
							<?php foreach ( $donnees['reponses'] as $reponse ) : ?>
								<p style="border-left:3px solid #ccd0d4;padding-left:10px;margin:6px 0">
									<strong><?php echo esc_html( $reponse['auteur'] ); ?> :</strong>
									<?php echo esc_html( $reponse['message'] ); ?>
								</p>
							<?php endforeach; ?>
						</td>
						<td>
							<?php if ( 'couleur' === $donnees['type'] && $donnees['valeur'] ) : ?>
								<span style="display:inline-block;width:16px;height:16px;vertical-align:-3px;border:1px solid #ccc;background:<?php echo esc_attr( $donnees['valeur'] ); ?>"></span>
								<code><?php echo esc_html( $donnees['valeur'] ); ?></code>
							<?php elseif ( $donnees['valeur'] ) : ?>
								<em><?php echo esc_html( $donnees['valeur'] ); ?></em>
							<?php endif; ?>
							<?php if ( $donnees['media'] ) : ?>
								<a href="<?php echo esc_url( $donnees['media'] ); ?>" target="_blank" rel="noreferrer">
									<img src="<?php echo esc_url( $donnees['media'] ); ?>" alt="" style="max-width:180px;height:auto;display:block;margin-top:6px">
								</a>
							<?php endif; ?>
						</td>
						<td>
							<?php echo esc_html( $donnees['auteur'] ); ?><br>
							<span class="description"><?php echo esc_html( mysql2date( 'j M Y, H:i', $note->post_date ) ); ?></span>
						</td>
						<td>
							<form method="post" action="<?php echo esc_url( admin_url( 'admin-post.php' ) ); ?>">
								<?php wp_nonce_field( 'ae_refonte_statut_' . $note->ID ); ?>
								<input type="hidden" name="action" value="ae_refonte_statut">
								<input type="hidden" name="note" value="<?php echo esc_attr( $note->ID ); ?>">
								<input type="hidden" name="retour" value="<?php echo esc_attr( admin_url( 'admin.php?page=' . self::MENU ) ); ?>">
								<select name="statut">
									<?php foreach ( AE_Refonte_Types::STATUTS_NOTE as $cle => $lib ) : ?>
										<option value="<?php echo esc_attr( $cle ); ?>" <?php selected( $donnees['statut'], $cle ); ?>><?php echo esc_html( $lib ); ?></option>
									<?php endforeach; ?>
								</select>
								<button class="button button-small">Appliquer</button>
							</form>
						</td>
					</tr>
				<?php endforeach; ?>
				</tbody>
			</table>
		</div>
		<?php
	}

	public static function changer_statut() {
		$note_id = isset( $_POST['note'] ) ? (int) $_POST['note'] : 0;

		check_admin_referer( 'ae_refonte_statut_' . $note_id );

		if ( ! AE_Refonte_Roles::peut_gerer() ) {
			wp_die( 'Action non autorisée.' );
		}

		$statut = isset( $_POST['statut'] ) ? sanitize_key( wp_unslash( $_POST['statut'] ) ) : '';
		if ( array_key_exists( $statut, AE_Refonte_Types::STATUTS_NOTE ) && AE_Refonte_Types::NOTE === get_post_type( $note_id ) ) {
			update_post_meta( $note_id, '_ae_statut', $statut );
		}

		$retour = isset( $_POST['retour'] ) ? esc_url_raw( wp_unslash( $_POST['retour'] ) ) : admin_url( 'admin.php?page=' . self::MENU );
		wp_safe_redirect( $retour );
		exit;
	}

	/* ---------------------------------------------------------------- */
	/* Réglages                                                          */
	/* ---------------------------------------------------------------- */

	public static function reglages() {
		register_setting( 'ae_refonte', 'ae_refonte_email', array( 'sanitize_callback' => 'sanitize_email' ) );
		register_setting( 'ae_refonte', 'ae_refonte_rerouter_liens', array( 'sanitize_callback' => 'absint' ) );
	}

	public static function ecran_reglages() {
		?>
		<div class="wrap">
			<h1>Réglages de la refonte</h1>
			<form method="post" action="options.php">
				<?php settings_fields( 'ae_refonte' ); ?>
				<table class="form-table">
					<tr>
						<th scope="row"><label for="ae_refonte_email">Notifications</label></th>
						<td>
							<input type="email" class="regular-text" id="ae_refonte_email" name="ae_refonte_email"
								value="<?php echo esc_attr( get_option( 'ae_refonte_email', get_option( 'admin_email' ) ) ); ?>">
							<p class="description">Adresse prévenue à chaque nouvelle demande déposée sur une maquette.</p>
						</td>
					</tr>
					<tr>
						<th scope="row">Navigation de relecture</th>
						<td>
							<label>
								<input type="checkbox" name="ae_refonte_rerouter_liens" value="1"
									<?php checked( 1, (int) get_option( 'ae_refonte_rerouter_liens', 1 ) ); ?>>
								Rediriger, dans les maquettes, les liens vers les pages du site en ligne qui ont
								déjà une maquette
							</label>
							<p class="description">
								N'agit qu'à l'intérieur des pages <code>/refonte/</code>. Le site en ligne
								n'est jamais modifié.
							</p>
						</td>
					</tr>
				</table>
				<?php submit_button(); ?>
			</form>

			<h2>Zone de refonte</h2>
			<p>
				Les maquettes vivent dans un type de contenu privé. Elles sont absentes des sitemaps,
				de la recherche interne, des menus et des archives, et répondent 404 à toute personne
				sans la capacité <code>ae_view_refonte</code>. Aucun contenu existant n'est modifié.
			</p>
			<p>
				Pour donner l'accès à la cliente : créez-lui un compte avec le rôle
				<strong>Relecteur refonte</strong>, puis envoyez-lui l'URL de la première maquette.
			</p>
		</div>
		<?php
	}
}
