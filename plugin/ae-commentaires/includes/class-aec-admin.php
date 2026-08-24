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

class AEC_Admin {

	const MENU = 'ae-commentaires';

	public static function init() {
		add_action( 'admin_menu', array( __CLASS__, 'menu' ) );
	}

	public static function menu() {
		$ouverts = count( get_posts( array(
			'post_type'      => AEC_Types::TYPE,
			'post_status'    => 'publish',
			'post_parent'    => 0,
			'posts_per_page' => -1,
			'fields'         => 'ids',
			'meta_query'     => array( array( 'key' => '_aec_statut', 'value' => 'ouvert' ) ),
		) ) );

		$titre = 'Relecture';
		if ( $ouverts ) {
			$titre .= sprintf( ' <span class="awaiting-mod"><span class="pending-count">%d</span></span>', $ouverts );
		}

		add_menu_page(
			'Relecture',
			$titre,
			AEC_Roles::CAP_COMMENTER,
			self::MENU,
			array( __CLASS__, 'ecran' ),
			'dashicons-format-chat',
			5
		);
	}

	public static function ecran() {
		$fils = get_posts( array(
			'post_type'      => AEC_Types::TYPE,
			'post_status'    => 'publish',
			'post_parent'    => 0,
			'posts_per_page' => -1,
			'orderby'        => 'date',
			'order'          => 'DESC',
		) );

		$par_page = array();
		foreach ( $fils as $fil ) {
			$post_id = (int) get_post_meta( $fil->ID, '_aec_post', true );
			$url     = get_post_meta( $fil->ID, '_aec_url', true );
			$cle     = $post_id ?: $url;
			$par_page[ $cle ]['titre'] = $post_id ? get_the_title( $post_id ) : $url;
			$par_page[ $cle ]['url']   = $post_id ? get_permalink( $post_id ) : home_url( $url );
			$par_page[ $cle ]['fils'][] = $fil;
		}

		$nonce = wp_create_nonce( 'wp_rest' );
		?>
		<div class="wrap">
			<h1>Relecture</h1>

			<p style="max-width:74ch">
				Les commentaires se posent <strong>sur les pages elles-mêmes</strong> : ouvrez une
				page du site en étant connecté, cliquez sur la bulle en bas à droite, puis sur
				l'élément à changer. Cet écran n'est qu'une vue d'ensemble.
			</p>

			<?php if ( empty( $fils ) ) : ?>
				<div class="notice notice-info inline"><p>
					Aucun commentaire pour l'instant.
					<a href="<?php echo esc_url( home_url( '/' ) ); ?>">Ouvrir le site</a> et poser le premier.
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
						<?php $d = AEC_Rest::formater( $fil ); ?>
						<tr>
							<td>
								<a href="<?php echo esc_url( $page['url'] . '#aec-' . $fil->ID ); ?>" target="_blank" rel="noreferrer">
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
								<?php else : ?>
									<span style="color:#8a5700;font-weight:600">● Ouvert</span>
								<?php endif; ?>
							</td>
						</tr>
					<?php endforeach; ?>
					</tbody>
				</table>
			<?php endforeach; ?>

			<h2 style="margin-top:34px">Lecture à distance</h2>
			<p style="max-width:74ch">
				Les commentaires se lisent depuis l'extérieur avec un mot de passe d'application,
				sans recopie. Le format <code>md</code> rend un digest lisible tel quel.
			</p>
			<p><textarea readonly rows="4" class="large-text code" onclick="this.select()"># Tout, en digest lisible
curl -u 'identifiant:mot de passe application' \
  '<?php echo esc_url( rest_url( AEC_Rest::NS . '/tout?format=md' ) ); ?>'

# Seulement ce qui reste ouvert, en JSON
curl -u 'identifiant:mot de passe application' \
  '<?php echo esc_url( rest_url( AEC_Rest::NS . '/tout?statut=ouvert' ) ); ?>'</textarea></p>
		</div>
		<?php
	}
}
