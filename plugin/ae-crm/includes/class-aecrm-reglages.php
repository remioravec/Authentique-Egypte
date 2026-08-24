<?php
/**
 * Réglages : la durée de conservation des demandes.
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

class AECRM_Reglages {

	const MENU = 'aecrm-reglages';

	public static function init() {
		add_action( 'admin_menu', array( __CLASS__, 'menu' ), 11 );
		add_action( 'admin_init', array( __CLASS__, 'declarer' ) );
	}

	public static function menu() {
		add_submenu_page(
			AECRM_Ecran::MENU,
			'Réglages des demandes',
			'Réglages',
			'manage_options',
			self::MENU,
			array( __CLASS__, 'afficher' )
		);
	}

	public static function declarer() {
		register_setting( 'aecrm', AECRM_Demandes::OPTION_PURGE, array(
			'type'              => 'integer',
			'sanitize_callback' => array( __CLASS__, 'nettoyer_jours' ),
			'default'           => 0,
		) );
	}

	public static function nettoyer_jours( $valeur ) {
		$jours = (int) $valeur;

		return max( 0, min( 3650, $jours ) );
	}

	public static function afficher() {
		$jours  = (int) get_option( AECRM_Demandes::OPTION_PURGE, 0 );
		$total  = AECRM_Demandes::compter();
		$suivant = wp_next_scheduled( AECRM_Demandes::TACHE );
		?>
		<div class="wrap">
			<h1>Réglages des demandes</h1>

			<form method="post" action="options.php">
				<?php settings_fields( 'aecrm' ); ?>
				<table class="form-table" role="presentation">
					<tr>
						<th scope="row"><label for="aecrm-purge">Conservation</label></th>
						<td>
							<input type="number" id="aecrm-purge" min="0" max="3650" class="small-text"
								name="<?php echo esc_attr( AECRM_Demandes::OPTION_PURGE ); ?>"
								value="<?php echo (int) $jours; ?>"> jours
							<p class="description" style="max-width:70ch">
								Les demandes contiennent des données personnelles — noms, adresses,
								numéros. Passé ce délai, elles sont supprimées automatiquement, et
								cette durée vaut politique de conservation.
								<strong>0 = aucune purge</strong> : rien n'est supprimé tant qu'un
								délai n'a pas été choisi. Une suppression silencieuse par défaut
								serait pire que pas de purge du tout.
							</p>
						</td>
					</tr>
				</table>
				<?php submit_button(); ?>
			</form>

			<h2>État</h2>
			<table class="widefat striped" style="max-width:640px">
				<tbody>
					<tr>
						<td>Demandes enregistrées</td>
						<td><strong><?php echo (int) $total; ?></strong></td>
					</tr>
					<tr>
						<td>WPForms</td>
						<td><?php
							if ( ! defined( 'WPFORMS_VERSION' ) ) {
								echo '<strong>inactif</strong> — aucune nouvelle demande ne peut être captée';
							} else {
								echo 'actif, version ' . esc_html( WPFORMS_VERSION );
								echo class_exists( 'WPForms_Pro' ) ? ' (Pro)' : ' (Lite)';
							}
						?></td>
					</tr>
					<tr>
						<td>Prochaine purge</td>
						<td><?php
							if ( ! $jours ) {
								echo 'aucune — la conservation est illimitée';
							} elseif ( $suivant ) {
								echo esc_html( wp_date( 'j M Y, H:i', $suivant ) );
							} else {
								echo '<strong>tâche absente</strong> — désactivez puis réactivez l’extension';
							}
						?></td>
					</tr>
				</tbody>
			</table>
		</div>
		<?php
	}
}
