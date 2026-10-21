<?php
/**
 * Vue d'ensemble en back-office.
 *
 * Le travail se fait sur la page, pas ici. Cet écran sert à deux
 * choses seulement : voir d'un coup tout ce qui est ouvert, et
 * récupérer les commandes de lecture à distance.
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

class RLC_Admin {

	const MENU = 'relecture';

	public static function init() {
		add_action( 'admin_menu', array( __CLASS__, 'menu' ) );
		add_action( 'admin_init', array( __CLASS__, 'enregistrer_parcours' ) );
	}

	/* ---------------------------------------------------------------- */
	/* Le parcours à relire                                              */
	/* ---------------------------------------------------------------- */

	/** L'option qui garde l'adresse de la page mère du parcours. */
	const OPTION_PARCOURS = 'rlc_parcours';

	/**
	 * La page mère du parcours, ou null.
	 *
	 * Ses pages enfants (publiées, brouillons ou privées) apparaissent dans
	 * le navigateur de pages du calque même sans commentaire : c'est la
	 * liste de ce qu'on veut faire relire. Vide par défaut.
	 */
	public static function page_parcours() {
		$chemin = trim( (string) get_option( self::OPTION_PARCOURS, '' ), '/' );
		return $chemin ? get_page_by_path( $chemin ) : null;
	}

	public static function enregistrer_parcours() {
		if ( ! isset( $_POST['rlc_parcours_nonce'] ) || ! current_user_can( RLC_Roles::CAP_MODERER ) ) {
			return;
		}
		check_admin_referer( 'rlc_parcours', 'rlc_parcours_nonce' );
		$chemin = isset( $_POST['rlc_parcours'] ) ? sanitize_text_field( wp_unslash( $_POST['rlc_parcours'] ) ) : '';
		// On accepte une adresse complète : on n'en garde que le chemin.
		$chemin = trim( (string) wp_parse_url( $chemin, PHP_URL_PATH ), '/' );
		update_option( self::OPTION_PARCOURS, $chemin, false );
		add_settings_error( 'rlc', 'rlc_parcours', $chemin && ! get_page_by_path( $chemin )
			? 'Aucune page à cette adresse : le parcours reste vide.'
			: 'Parcours enregistré.', $chemin && ! get_page_by_path( $chemin ) ? 'warning' : 'success' );
	}

	/**
	 * La pastille ne compte plus les fils ouverts, mais ceux qui
	 * attendent l'équipe.
	 *
	 * Sur une longue relecture, beaucoup de fils restent « ouverts » alors
	 * qu'ils portent déjà notre réponse et attendent le client. Une
	 * pastille qui les compte ne dit rien de ce qu'il y a à faire ;
	 * celle-ci compte les fils dont le dernier mot ne vient pas de
	 * l'équipe — c'est-à-dire ceux où la balle est dans notre camp.
	 */
	public static function menu() {
		$fils = get_posts( array(
			'post_type'      => RLC_Types::TYPE,
			'post_status'    => 'publish',
			'post_parent'    => 0,
			'posts_per_page' => -1,
			'meta_query'     => array( array( 'key' => '_rlc_statut', 'value' => 'ouvert' ) ),
		) );

		$a_traiter = 0;
		foreach ( $fils as $fil ) {
			if ( RLC_Types::attend_equipe( $fil ) ) {
				$a_traiter++;
			}
		}

		$titre = 'Relecture';
		if ( $a_traiter ) {
			$titre .= sprintf( ' <span class="awaiting-mod"><span class="pending-count">%d</span></span>', $a_traiter );
		}

		add_menu_page(
			'Relecture',
			$titre,
			RLC_Roles::CAP_COMMENTER,
			self::MENU,
			array( __CLASS__, 'ecran' ),
			'dashicons-format-chat',
			5
		);
	}

	/**
	 * Les trois vues de l'écran, et celle qu'on ouvre par défaut.
	 *
	 * Des centaines de fils, clos pour la plupart, affichés à la suite :
	 * on ne retrouverait plus ce qui reste à faire. On ne supprime pas les
	 * fils clos pour autant — ils portent les réponses, et une remarque
	 * rouverte doit retrouver son histoire. On les range.
	 */
	const VUES = array(
		'equipe' => 'Pour nous',
		'ouvert' => 'Ouverts',
		'resolu' => 'Traités',
		'tout'   => 'Tout',
	);

	public static function ecran() {
		$vue = isset( $_GET['etat'] ) ? sanitize_key( wp_unslash( $_GET['etat'] ) ) : 'equipe';
		if ( ! isset( self::VUES[ $vue ] ) ) {
			$vue = 'equipe';
		}

		$tous = get_posts( array(
			'post_type'      => RLC_Types::TYPE,
			'post_status'    => 'publish',
			'post_parent'    => 0,
			'posts_per_page' => -1,
			'orderby'        => 'date',
			'order'          => 'DESC',
		) );

		$comptes = array( 'equipe' => 0, 'ouvert' => 0, 'resolu' => 0, 'tout' => count( $tous ) );
		$fils    = array();
		foreach ( $tous as $fil ) {
			$etat   = get_post_meta( $fil->ID, '_rlc_statut', true ) === 'resolu' ? 'resolu' : 'ouvert';
			$equipe = RLC_Types::attend_equipe( $fil );
			$comptes[ $etat ]++;
			if ( $equipe ) {
				$comptes['equipe']++;
			}
			$garde = ( 'tout' === $vue ) || ( 'equipe' === $vue ? $equipe : $etat === $vue );
			if ( $garde ) {
				$fils[] = $fil;
			}
		}

		$par_page = array();
		foreach ( $fils as $fil ) {
			$post_id = (int) get_post_meta( $fil->ID, '_rlc_post', true );
			$url     = get_post_meta( $fil->ID, '_rlc_url', true );
			$cle     = $post_id ?: $url;
			$par_page[ $cle ]['titre'] = $post_id ? get_the_title( $post_id ) : $url;
			$par_page[ $cle ]['url']   = $post_id ? get_permalink( $post_id ) : home_url( $url );
			$par_page[ $cle ]['fils'][] = $fil;
		}

		// La page qui a le plus à traiter passe en tête : c'est par elle
		// qu'on commence, pas par celle dont le titre vient en premier.
		uasort( $par_page, function ( $a, $b ) {
			return count( $b['fils'] ) <=> count( $a['fils'] );
		} );

		$nonce = wp_create_nonce( 'wp_rest' );
		?>
		<div class="wrap">
			<h1>Relecture</h1>

			<p style="max-width:74ch">
				Les commentaires se posent <strong>sur les pages elles-mêmes</strong> : ouvrez une
				page du site en étant connecté, cliquez sur la bulle en bas à droite, puis sur
				l'élément à changer. Cet écran n'est qu'une vue d'ensemble.
			</p>

			<ul class="subsubsub">
				<?php $sep = count( self::VUES ); foreach ( self::VUES as $cle => $nom ) : ?>
					<li>
						<a href="<?php echo esc_url( add_query_arg( array( 'page' => self::MENU, 'etat' => $cle ), admin_url( 'admin.php' ) ) ); ?>"
						   class="<?php echo $cle === $vue ? 'current' : ''; ?>"
						   <?php echo $cle === $vue ? 'aria-current="page"' : ''; ?>>
							<?php echo esc_html( $nom ); ?>
							<span class="count">(<?php echo (int) $comptes[ $cle ]; ?>)</span>
						</a><?php echo --$sep ? ' |' : ''; ?>
					</li>
				<?php endforeach; ?>
			</ul>
			<div style="clear:both"></div>

			<?php if ( empty( $fils ) ) : ?>
				<div class="notice notice-info inline"><p>
					<?php if ( 'equipe' === $vue && $comptes['tout'] ) : ?>
						Rien qui attende de nous. <?php echo (int) $comptes['ouvert']; ?> fil(s)
						restent ouverts, mais chacun porte déjà notre réponse : ils sont en
						attente du client.
					<?php elseif ( 'ouvert' === $vue && $comptes['tout'] ) : ?>
						Rien à traiter : les <?php echo (int) $comptes['resolu']; ?> commentaires
						sont tous clos.
					<?php elseif ( $comptes['tout'] ) : ?>
						Aucun commentaire dans cette vue.
					<?php else : ?>
						Aucun commentaire pour l'instant.
						<a href="<?php echo esc_url( home_url( '/' ) ); ?>">Ouvrir le site</a> et poser le premier.
					<?php endif; ?>
				</p></div>
			<?php endif; ?>

			<?php foreach ( $par_page as $page ) : ?>
				<h2 style="margin-top:28px">
					<a href="<?php echo esc_url( $page['url'] ); ?>" target="_blank" rel="noreferrer">
						<?php echo esc_html( $page['titre'] ); ?>
					</a>
					<span class="count">(<?php echo count( $page['fils'] ); ?>)</span>
				</h2>
				<table class="widefat striped">
					<thead><tr>
						<th style="width:70px">Fil</th>
						<th>Commentaire</th>
						<th style="width:180px">Élément visé</th>
						<th style="width:140px">Auteur</th>
						<th style="width:100px">État</th>
					</tr></thead>
					<tbody>
					<?php foreach ( $page['fils'] as $fil ) : ?>
						<?php $d = RLC_Rest::formater( $fil ); ?>
						<tr>
							<td>
								<a href="<?php echo esc_url( $page['url'] . '#rlc-' . $fil->ID ); ?>" target="_blank" rel="noreferrer">
									#<?php echo (int) $fil->ID; ?>
								</a>
							</td>
							<td>
								<?php echo wp_kses_post( wpautop( $d['message'] ) ); ?>
								<?php if ( $d['image'] ) : ?>
									<a href="<?php echo esc_url( $d['image'] ); ?>" target="_blank" rel="noreferrer">
										<img src="<?php echo esc_url( $d['image'] ); ?>" alt="" style="max-width:180px;height:auto;display:block;margin-top:6px;border-radius:4px">
									</a>
								<?php endif; ?>
								<?php foreach ( $d['reponses'] as $reponse ) : ?>
									<p style="border-left:3px solid #dcdcde;padding-left:10px;margin:8px 0 0">
										<strong><?php echo esc_html( $reponse['auteur'] ); ?> :</strong>
										<?php echo esc_html( $reponse['message'] ); ?>
									</p>
								<?php endforeach; ?>
							</td>
							<td>
								<?php if ( $d['ancre'] ) : ?>
									<em>« <?php echo esc_html( wp_trim_words( $d['ancre'], 8, '…' ) ); ?> »</em>
								<?php endif; ?>
								<?php if ( $d['largeur'] ) : ?>
									<br><span class="description"><?php echo (int) $d['largeur']; ?> px de large</span>
								<?php endif; ?>
							</td>
							<td>
								<?php echo esc_html( $d['auteur'] ); ?><br>
								<span class="description"><?php echo esc_html( mysql2date( 'j M, H:i', $fil->post_date ) ); ?></span>
							</td>
							<td>
								<?php if ( 'resolu' === $d['statut'] ) : ?>
									<span style="color:#1d6b34;font-weight:600">✓ Résolu</span>
								<?php elseif ( RLC_Types::attend_equipe( $fil ) ) : ?>
									<span style="color:#8a5700;font-weight:600">● Pour nous</span>
								<?php else : ?>
									<span style="color:#606a73;font-weight:600">○ En attente du client</span>
								<?php endif; ?>
							</td>
						</tr>
					<?php endforeach; ?>
					</tbody>
				</table>
			<?php endforeach; ?>

			<?php if ( RLC_Roles::peut_moderer() ) : $mere = self::page_parcours(); ?>
				<h2 style="margin-top:34px">Parcours à relire</h2>
				<?php settings_errors( 'rlc' ); ?>
				<form method="post" style="max-width:74ch">
					<?php wp_nonce_field( 'rlc_parcours', 'rlc_parcours_nonce' ); ?>
					<p>
						Les pages enfants de cette page apparaissent dans le navigateur du calque,
						même sans commentaire. Laisser vide pour ne lister que les pages commentées.
					</p>
					<p>
						<label for="rlc_parcours" class="screen-reader-text">Adresse de la page mère</label>
						<input type="text" id="rlc_parcours" name="rlc_parcours" class="regular-text code"
						       placeholder="refonte" value="<?php echo esc_attr( get_option( self::OPTION_PARCOURS, '' ) ); ?>">
						<?php submit_button( 'Enregistrer', 'secondary', 'submit', false ); ?>
					</p>
					<?php if ( $mere ) : ?>
						<p class="description">Page mère : <strong><?php echo esc_html( $mere->post_title ); ?></strong>.</p>
					<?php endif; ?>
				</form>
			<?php endif; ?>

			<h2 style="margin-top:34px">Lecture à distance</h2>
			<p style="max-width:74ch">
				Les commentaires se lisent depuis l'extérieur avec un mot de passe d'application,
				sans recopie. Le format <code>md</code> rend un digest lisible tel quel.
			</p>
			<p><textarea readonly rows="4" class="large-text code" onclick="this.select()"># Tout, en digest lisible
curl -u 'identifiant:mot de passe application' \
  '<?php echo esc_url( rest_url( RLC_Rest::NS . '/tout?format=md' ) ); ?>'

# Seulement ce qui reste ouvert, en JSON
curl -u 'identifiant:mot de passe application' \
  '<?php echo esc_url( rest_url( RLC_Rest::NS . '/tout?statut=ouvert' ) ); ?>'</textarea></p>
		</div>
		<?php
	}
}
