<?php
/**
 * Plugin Name:       AE Refonte — relecture et annotations
 * Plugin URI:        https://github.com/remioravec/Authentique-Egypte
 * Description:       Zone de refonte étanche : les maquettes vivent dans un type de contenu privé, invisible du site public. La cliente les parcourt, les annote élément par élément et propose des corrections (texte, couleur, image). Les demandes sont lisibles en back-office et par l'API REST.
 * Version:           0.1.0
 * Requires at least: 6.0
 * Requires PHP:      7.4
 * Author:            Rémi Oravec
 * Text Domain:       ae-refonte
 *
 * ------------------------------------------------------------------
 * GARANTIE DE NON-IMPACT SUR LE SITE EN LIGNE
 * ------------------------------------------------------------------
 * Ce plugin ne modifie AUCUN contenu existant. Il n'ajoute ni filtre
 * ni action sur les types `page`, `post`, `programs`, sur les menus,
 * sur le thème ou sur Elementor. Tout ce qu'il crée vit dans deux
 * types de contenu qui lui appartiennent :
 *
 *   ae_maquette  les pages de refonte      public=false
 *   ae_note      les demandes de la cliente public=false
 *
 * Ces deux types sont `public => false` : ils sont donc absents des
 * sitemaps (Yoast inclus), de la recherche interne, des menus, des
 * archives et des flux. Les URL /refonte/... répondent 404 à toute
 * personne qui n'a pas la capacité `ae_view_refonte`.
 *
 * Désactiver le plugin fait disparaître la zone de refonte sans
 * toucher une ligne du site en ligne.
 * ------------------------------------------------------------------
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

define( 'AE_REFONTE_VERSION', '0.1.0' );
define( 'AE_REFONTE_FILE', __FILE__ );
define( 'AE_REFONTE_DIR', plugin_dir_path( __FILE__ ) );
define( 'AE_REFONTE_URL', plugin_dir_url( __FILE__ ) );

/** Dossier des fichiers HTML de maquette, surchargeable depuis wp-config.php. */
if ( ! defined( 'AE_REFONTE_MAQUETTES_DIR' ) ) {
	define( 'AE_REFONTE_MAQUETTES_DIR', AE_REFONTE_DIR . 'maquettes/' );
}

require_once AE_REFONTE_DIR . 'includes/class-ae-roles.php';
require_once AE_REFONTE_DIR . 'includes/class-ae-types.php';
require_once AE_REFONTE_DIR . 'includes/class-ae-isolation.php';
require_once AE_REFONTE_DIR . 'includes/class-ae-rendu.php';
require_once AE_REFONTE_DIR . 'includes/class-ae-rest.php';
require_once AE_REFONTE_DIR . 'includes/class-ae-admin.php';
require_once AE_REFONTE_DIR . 'includes/class-ae-notifications.php';

/**
 * Point d'entrée : instancie les modules une fois WordPress chargé.
 */
function ae_refonte_init() {
	AE_Refonte_Types::init();
	AE_Refonte_Isolation::init();
	AE_Refonte_Rendu::init();
	AE_Refonte_Rest::init();
	AE_Refonte_Admin::init();
	AE_Refonte_Notifications::init();
}
add_action( 'plugins_loaded', 'ae_refonte_init' );

/**
 * Activation : crée le rôle relecteur, donne les capacités aux admins,
 * enregistre les types puis régénère les permaliens pour que /refonte/
 * réponde immédiatement.
 */
function ae_refonte_activation() {
	AE_Refonte_Roles::installer();
	AE_Refonte_Types::enregistrer();
	flush_rewrite_rules();
}
register_activation_hook( __FILE__, 'ae_refonte_activation' );

/**
 * Désactivation : on retire les règles de réécriture, rien d'autre.
 * Les rôles, maquettes et notes sont conservés — une désactivation
 * accidentelle ne doit rien détruire.
 */
function ae_refonte_desactivation() {
	flush_rewrite_rules();
}
register_deactivation_hook( __FILE__, 'ae_refonte_desactivation' );
