<?php
/**
 * L'écran « Contenus » : pages, articles et voyages au même endroit,
 * rangés par gabarit.
 *
 * Le back-office de WordPress sépare Articles et Pages parce que c'est
 * ainsi qu'il stocke les choses, pas parce que c'est ainsi qu'on
 * travaille. Sur ce site, un « guide pratique » est un article et une
 * « destination » est une page — mais un guide ressemble beaucoup plus
 * à un autre guide qu'à la page d'accueil. On range donc par gabarit,
 * et le type de contenu devient un détail technique.
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

class ABO_Contenus {

	const MENU = 'ae-contenus';

	public static function init() {
		add_action( 'admin_menu', array( __CLASS__, 'menu' ), 9 );
		add_action( 'admin_enqueue_scripts', array( __CLASS__, 'styles' ) );
		add_action( 'admin_post_abo_ranger', array( __CLASS__, 'action_ranger' ) );
		add_action( 'admin_post_abo_gabarit', array( __CLASS__, 'action_gabarit' ) );
	}

	public static function menu() {
		add_menu_page(
			'Contenus',
			'Contenus',
			'edit_posts',
			self::MENU,
			array( __CLASS__, 'ecran' ),
			'dashicons-portfolio',
			3
		);
	}

	public static function styles( $page ) {
		if ( false === strpos( (string) $page, self::MENU ) ) {
			return;
		}
		wp_enqueue_style( 'abo-admin' );
	}

	/* ---------------------------------------------------------------- */
	/* Lecture                                                           */
	/* ---------------------------------------------------------------- */

	/**
	 * Tous les contenus, rangés par gabarit, dans l'ordre du vocabulaire.
	 *
	 * @param string $recherche
	 * @return array<string,WP_Post[]>
	 */
	private static function par_gabarit( $recherche = '' ) {
		$types = ABO_Gabarits::types();
		if ( post_type_exists( 'ae_maquette' ) ) {
			$types[] = 'ae_maquette';
		}

		$args = array(
			'post_type'      => $types,
			'post_status'    => array( 'publish', 'draft', 'pending', 'private', 'future' ),
			'posts_per_page' => -1,
			'orderby'        => 'title',
			'order'          => 'ASC',
		);
		if ( '' !== $recherche ) {
			$args['s'] = $recherche;
		}

		$rangs = array_fill_keys( array_keys( ABO_Gabarits::VOCABULAIRE ), array() );

		foreach ( get_posts( $args ) as $post ) {
			$rangs[ ABO_Gabarits::du( $post ) ][] = $post;
		}

		return array_filter( $rangs, static function ( $liste ) {
			return ! empty( $liste );
		} );
	}

	/* ---------------------------------------------------------------- */
	/* Affichage                                                         */
	/* ---------------------------------------------------------------- */

	public static function ecran() {
		$recherche = isset( $_GET['s'] ) ? sanitize_text_field( wp_unslash( $_GET['s'] ) ) : '';
		$filtre    = isset( $_GET['gabarit'] ) ? sanitize_key( wp_unslash( $_GET['gabarit'] ) ) : '';
		$rangs     = self::par_gabarit( $recherche );
		$total     = array_sum( array_map( 'count', $rangs ) );
		?>
		<div class="wrap abo">
			<h1 class="wp-heading-inline">Contenus</h1>
			<a href="<?php echo esc_url( admin_url( 'post-new.php?post_type=page' ) ); ?>" class="page-title-action">Nouvelle page</a>
			<a href="<?php echo esc_url( admin_url( 'post-new.php?post_type=post' ) ); ?>" class="page-title-action">Nouveau guide</a>
			<hr class="wp-header-end">

			<?php if ( isset( $_GET['range'] ) ) : ?>
				<div class="notice notice-success is-dismissible"><p>Contenus reclassés.</p></div>
			<?php endif; ?>

			<p class="abo-intro">
				Pages, guides et voyages au même endroit, rangés par <strong>gabarit</strong> —
				c'est-à-dire par modèle de page. Le type de contenu WordPress (page ou article)
				devient un détail : ce qui compte, c'est le rôle de la page dans le site.
			</p>

			<form method="get" class="abo-barre">
				<input type="hidden" name="page" value="<?php echo esc_attr( self::MENU ); ?>">
				<p class="search-box">
					<label class="screen-reader-text" for="abo-s">Rechercher</label>
					<input type="search" id="abo-s" name="s" value="<?php echo esc_attr( $recherche ); ?>" placeholder="Rechercher un contenu">
					<button class="button">Rechercher</button>
				</p>
			</form>

			<div class="abo-onglets">
				<a class="abo-onglet <?php echo '' === $filtre ? 'actif' : ''; ?>"
					href="<?php echo esc_url( add_query_arg( array( 'page' => self::MENU, 's' => $recherche ), admin_url( 'admin.php' ) ) ); ?>">
					Tout <span><?php echo (int) $total; ?></span>
				</a>
				<?php foreach ( $rangs as $gabarit => $liste ) : ?>
					<a class="abo-onglet <?php echo $filtre === $gabarit ? 'actif' : ''; ?>"
						href="<?php echo esc_url( add_query_arg( array( 'page' => self::MENU, 'gabarit' => $gabarit, 's' => $recherche ), admin_url( 'admin.php' ) ) ); ?>">
						<?php echo esc_html( ABO_Gabarits::libelle( $gabarit ) ); ?>
						<span><?php echo count( $liste ); ?></span>
					</a>
				<?php endforeach; ?>
			</div>

			<?php if ( empty( $rangs ) ) : ?>
				<p>Aucun contenu pour cette recherche.</p>
			<?php endif; ?>

			<?php foreach ( $rangs as $gabarit => $liste ) : ?>
				<?php
				if ( $filtre && $filtre !== $gabarit ) {
					continue;
				}
				$entree = ABO_Gabarits::VOCABULAIRE[ $gabarit ];
				?>
				<section class="abo-bloc" id="g-<?php echo esc_attr( $gabarit ); ?>">
					<header>
						<h2><?php echo esc_html( $entree['icone'] . ' ' . $entree['nom'] ); ?>
							<span class="abo-compte"><?php echo count( $liste ); ?></span></h2>
						<p><?php echo esc_html( $entree['aide'] ); ?></p>
					</header>

					<table class="widefat striped abo-table">
						<thead>
							<tr>
								<th>Titre</th>
								<th style="width:110px">État</th>
								<th style="width:120px">Type</th>
								<th style="width:150px">Modifié</th>
								<th style="width:230px">Gabarit</th>
							</tr>
						</thead>
						<tbody>
						<?php foreach ( $liste as $post ) : ?>
							<?php
							$type   = get_post_type_object( $post->post_type );
							$manuel = (bool) get_post_meta( $post->ID, ABO_Gabarits::META_MAIN, true );
							?>
							<tr>
								<td>
									<strong><a href="<?php echo esc_url( get_edit_post_link( $post->ID ) ); ?>">
										<?php echo esc_html( $post->post_title ?: '(sans titre)' ); ?>
									</a></strong>
									<div class="row-actions">
										<span><a href="<?php echo esc_url( get_edit_post_link( $post->ID ) ); ?>">Modifier</a> | </span>
										<span><a href="<?php echo esc_url( get_permalink( $post->ID ) ); ?>" target="_blank" rel="noreferrer">Voir</a></span>
									</div>
									<code class="abo-slug">/<?php echo esc_html( $post->post_name ); ?>/</code>
								</td>
								<td>
									<span class="abo-etat abo-etat--<?php echo esc_attr( $post->post_status ); ?>">
										<?php
										$etats = array(
											'publish' => 'En ligne',
											'draft'   => 'Brouillon',
											'private' => 'Privé',
											'pending' => 'En attente',
											'future'  => 'Programmé',
										);
										echo esc_html( $etats[ $post->post_status ] ?? $post->post_status );
										?>
									</span>
								</td>
								<td class="abo-type"><?php echo esc_html( $type ? $type->labels->singular_name : $post->post_type ); ?></td>
								<td class="abo-date"><?php echo esc_html( get_the_modified_date( 'j M Y', $post ) ); ?></td>
								<td>
									<form method="post" action="<?php echo esc_url( admin_url( 'admin-post.php' ) ); ?>" class="abo-choix">
										<?php wp_nonce_field( 'abo_gabarit_' . $post->ID ); ?>
										<input type="hidden" name="action" value="abo_gabarit">
										<input type="hidden" name="post" value="<?php echo esc_attr( $post->ID ); ?>">
										<select name="gabarit" onchange="this.form.submit()">
											<?php foreach ( ABO_Gabarits::VOCABULAIRE as $cle => $v ) : ?>
												<option value="<?php echo esc_attr( $cle ); ?>" <?php selected( $gabarit, $cle ); ?>>
													<?php echo esc_html( $v['icone'] . ' ' . $v['nom'] ); ?>
												</option>
											<?php endforeach; ?>
										</select>
										<?php if ( $manuel ) : ?>
											<span class="abo-manuel" title="Classé à la main : le rangement automatique ne le touchera pas">✋</span>
										<?php endif; ?>
									</form>
								</td>
							</tr>
						<?php endforeach; ?>
						</tbody>
					</table>
				</section>
			<?php endforeach; ?>

			<form method="post" action="<?php echo esc_url( admin_url( 'admin-post.php' ) ); ?>" class="abo-pied">
				<?php wp_nonce_field( 'abo_ranger' ); ?>
				<input type="hidden" name="action" value="abo_ranger">
				<button class="button">Reclasser automatiquement</button>
				<span class="description">
					Recalcule le gabarit de chaque contenu. Les classements posés à la main (✋)
					ne sont pas touchés.
				</span>
			</form>
		</div>
		<?php
	}

	/* ---------------------------------------------------------------- */
	/* Actions                                                           */
	/* ---------------------------------------------------------------- */

	public static function action_ranger() {
		check_admin_referer( 'abo_ranger' );
		if ( ! current_user_can( 'edit_posts' ) ) {
			wp_die( 'Action non autorisée.' );
		}

		ABO_Gabarits::ranger_tout();
		wp_safe_redirect( admin_url( 'admin.php?page=' . self::MENU . '&range=1' ) );
		exit;
	}

	public static function action_gabarit() {
		$post_id = isset( $_POST['post'] ) ? (int) $_POST['post'] : 0;
		check_admin_referer( 'abo_gabarit_' . $post_id );

		if ( ! current_user_can( 'edit_post', $post_id ) ) {
			wp_die( 'Action non autorisée.' );
		}

		$gabarit = isset( $_POST['gabarit'] ) ? sanitize_key( wp_unslash( $_POST['gabarit'] ) ) : '';
		if ( isset( ABO_Gabarits::VOCABULAIRE[ $gabarit ] ) ) {
			update_post_meta( $post_id, ABO_Gabarits::META, $gabarit );
			// Un choix à la main devient définitif : le recalcul l'épargne.
			update_post_meta( $post_id, ABO_Gabarits::META_MAIN, 1 );
		}

		wp_safe_redirect( wp_get_referer() ?: admin_url( 'admin.php?page=' . self::MENU ) );
		exit;
	}
}
