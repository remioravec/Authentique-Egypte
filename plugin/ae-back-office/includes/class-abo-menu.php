<?php
/**
 * Simplification du menu d'administration.
 *
 * Principe : on garde ce qui sert à faire vivre le site, on masque le
 * reste. Rien n'est verrouillé — `remove_menu_page()` retire une entrée
 * de menu, jamais une capacité. Un interrupteur « Tout afficher » vit
 * en permanence dans la barre d'administration, et le réglage est par
 * personne : il n'impose rien aux autres comptes.
 *
 * Ce qui reste par défaut :
 *   Tableau de bord · Contenus · Demandes · Voyages · Médiathèque
 *   Relecture · WPForms · Apparence · Extensions · Comptes · Réglages
 *   Yoast SEO · Elementor
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

class ABO_Menu {

	const OPTION_GARDES  = 'abo_menus_gardes';
	const META_TOUT_VOIR = 'abo_tout_voir';

	/**
	 * Les entrées gardées par défaut, par identifiant de menu.
	 * Tout ce qui n'est pas dans cette liste est masqué.
	 */
	const GARDES_DEFAUT = array(
		'index.php',                            // Tableau de bord
		'ae-contenus',                          // notre écran unifié
		'ae-demandes',                          // les demandes reçues par formulaire
		'edit.php?post_type=programs',          // les voyages, dans leur écran natif
		'upload.php',                           // Médiathèque
		'ae-commentaires',                      // extension de relecture
		'wpforms*',                             // WPForms et tous ses sous-écrans
		'themes.php',                           // Apparence
		'plugins.php',                          // Extensions
		'users.php',                            // Comptes
		'options-general.php',                  // Réglages
		'wpseo*',                               // Yoast SEO
		'elementor',                            // Elementor
		'edit.php?post_type=elementor_library', // Modèles Elementor
	);

	/**
	 * Sous-entrées masquées à l'intérieur d'un menu gardé.
	 * Format : menu parent => [sous-entrées].
	 */
	const SOUS_MASQUES = array(
		'themes.php' => array( 'theme-editor.php' ),
		'index.php'  => array( 'update-core.php' ),
	);

	public static function init() {
		add_action( 'admin_menu', array( __CLASS__, 'nettoyer' ), 999 );
		add_action( 'admin_bar_menu', array( __CLASS__, 'interrupteur' ), 999 );
		add_action( 'admin_post_abo_tout_voir', array( __CLASS__, 'basculer' ) );
		add_action( 'admin_menu', array( __CLASS__, 'reglages' ) );
		add_action( 'admin_init', array( __CLASS__, 'enregistrer_reglages' ) );
	}

	/** Le compte courant a-t-il demandé à tout voir ? */
	public static function tout_voir() {
		return (bool) get_user_meta( get_current_user_id(), self::META_TOUT_VOIR, true );
	}

	/** La liste des menus gardés, réglable. */
	public static function gardes() {
		$gardes = get_option( self::OPTION_GARDES );
		if ( ! is_array( $gardes ) || empty( $gardes ) ) {
			$gardes = self::GARDES_DEFAUT;
		}

		/**
		 * Permet d'ajouter ou de retirer une entrée gardée.
		 *
		 * @param string[] $gardes
		 */
		return apply_filters( 'abo_menus_gardes', $gardes );
	}

	/**
	 * Une entrée est-elle gardée ?
	 *
	 * Une garde qui se termine par « * » vaut pour tout ce qui commence
	 * ainsi : `wpforms*` garde l'écran principal et ses sous-écrans, sans
	 * qu'il faille les énumérer ni deviner comment l'extension les nomme
	 * d'une version à l'autre.
	 *
	 * @param string   $identifiant
	 * @param string[] $gardes
	 * @return bool
	 */
	public static function est_garde( $identifiant, $gardes ) {
		foreach ( $gardes as $garde ) {
			if ( '*' === substr( $garde, -1 ) ) {
				if ( 0 === strpos( $identifiant, substr( $garde, 0, -1 ) ) ) {
					return true;
				}
				continue;
			}
			if ( $identifiant === $garde ) {
				return true;
			}
		}

		return false;
	}

	public static function nettoyer() {
		if ( self::tout_voir() ) {
			return;
		}

		global $menu;

		$gardes = self::gardes();
		// Notre propre page de réglages doit rester joignable.
		$gardes[] = 'abo-reglages';

		foreach ( (array) $menu as $entree ) {
			$identifiant = $entree[2] ?? '';
			if ( '' === $identifiant ) {
				continue;
			}
			// Les séparateurs portent un identifiant « separator… ».
			if ( 0 === strpos( $identifiant, 'separator' ) ) {
				continue;
			}
			if ( self::est_garde( $identifiant, $gardes ) ) {
				continue;
			}
			remove_menu_page( $identifiant );
		}

		foreach ( self::SOUS_MASQUES as $parent => $enfants ) {
			foreach ( $enfants as $enfant ) {
				remove_submenu_page( $parent, $enfant );
			}
		}
	}

	/**
	 * L'interrupteur dans la barre d'administration. Il est toujours
	 * là : on ne masque jamais sans laisser la clé sur la porte.
	 */
	public static function interrupteur( $barre ) {
		if ( ! is_admin() || ! current_user_can( 'edit_posts' ) ) {
			return;
		}

		$actif = self::tout_voir();
		$url   = wp_nonce_url(
			admin_url( 'admin-post.php?action=abo_tout_voir' ),
			'abo_tout_voir'
		);

		$barre->add_node(
			array(
				'id'    => 'abo-tout-voir',
				'title' => $actif ? '◉ Menu complet' : '◎ Menu simplifié',
				'href'  => $url,
				'meta'  => array(
					'title' => $actif
						? 'Revenir au menu simplifié'
						: 'Afficher toutes les entrées de menu de WordPress',
				),
			)
		);
	}

	public static function basculer() {
		check_admin_referer( 'abo_tout_voir' );

		$utilisateur = get_current_user_id();
		if ( ! $utilisateur ) {
			wp_die( 'Action non autorisée.' );
		}

		if ( self::tout_voir() ) {
			delete_user_meta( $utilisateur, self::META_TOUT_VOIR );
		} else {
			update_user_meta( $utilisateur, self::META_TOUT_VOIR, 1 );
		}

		wp_safe_redirect( wp_get_referer() ?: admin_url() );
		exit;
	}

	/* ---------------------------------------------------------------- */
	/* Réglages                                                          */
	/* ---------------------------------------------------------------- */

	public static function reglages() {
		add_submenu_page(
			'options-general.php',
			'Back-office simplifié',
			'Back-office simplifié',
			'manage_options',
			'abo-reglages',
			array( __CLASS__, 'ecran_reglages' )
		);
	}

	public static function enregistrer_reglages() {

		register_setting(
			'abo',
			self::OPTION_GARDES,
			array(
				'sanitize_callback' => static function ( $valeur ) {
					$lignes = preg_split( '/\r\n|\r|\n/', (string) $valeur );
					$propre = array();
					foreach ( $lignes as $ligne ) {
						$ligne = trim( $ligne );
						if ( '' !== $ligne ) {
							$propre[] = $ligne;
						}
					}

					return $propre ?: self::GARDES_DEFAUT;
				},
			)
		);
	}

	public static function ecran_reglages() {
		global $menu;
		$gardes = self::gardes();
		?>
		<div class="wrap">
			<h1>Back-office simplifié</h1>

			<p style="max-width:70ch">
				Les entrées de menu listées ci-dessous restent visibles ; toutes les autres sont
				masquées. Le masquage est <strong>cosmétique</strong> : aucune capacité n'est
				retirée, et l'interrupteur « Menu simplifié / Menu complet » de la barre du haut
				rend tout visible en un clic, compte par compte.
			</p>

			<form method="post" action="options.php">
				<?php settings_fields( 'abo' ); ?>
				<table class="form-table">
					<tr>
						<th scope="row"><label for="abo-gardes">Entrées gardées</label></th>
						<td>
							<textarea id="abo-gardes" name="<?php echo esc_attr( self::OPTION_GARDES ); ?>"
								rows="12" cols="50" class="large-text code"><?php
								echo esc_textarea( implode( "\n", $gardes ) );
							?></textarea>
							<p class="description">
					Un identifiant par ligne. Une ligne qui se termine par <code>*</code> vaut pour
					tout ce qui commence ainsi — <code>wpforms*</code> garde l'écran principal et
					ses sous-écrans. Videz le champ pour revenir à la liste par défaut.
				</p>
						</td>
					</tr>
				</table>
				<?php submit_button(); ?>
			</form>

			<h2>Les identifiants disponibles</h2>
			<p class="description">Relevés sur ce site, dans l'ordre du menu.</p>
			<table class="widefat striped" style="max-width:640px">
				<thead><tr><th>Entrée</th><th style="width:280px">Identifiant</th><th style="width:80px">État</th></tr></thead>
				<tbody>
				<?php foreach ( (array) $menu as $entree ) : ?>
					<?php
					$identifiant = $entree[2] ?? '';
					if ( '' === $identifiant || 0 === strpos( $identifiant, 'separator' ) ) {
						continue;
					}
					$nom = trim( wp_strip_all_tags( $entree[0] ?? $identifiant ) );
					$nom = preg_replace( '/\d+$/', '', $nom );
					?>
					<tr>
						<td><?php echo esc_html( $nom ); ?></td>
						<td><code><?php echo esc_html( $identifiant ); ?></code></td>
						<td><?php echo self::est_garde( $identifiant, $gardes ) ? '✅' : '—'; ?></td>
					</tr>
				<?php endforeach; ?>
				</tbody>
			</table>
		</div>
		<?php
	}
}
