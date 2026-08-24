<?php
/**
 * Plugin Name:       AE Back-office — contenus rangés par gabarit
 * Plugin URI:        https://github.com/remioravec/Authentique-Egypte
 * Description:       Remplace « Articles » et « Pages » par un écran unique « Contenus », rangé par gabarit (accueil, catégorie, voyage, destination, guide, devis, agence…). Conserve les demandes reçues par formulaire, que WPForms Lite n'enregistre pas. Masque les entrées de menu inutiles pour ne laisser que l'essentiel : contenus, demandes, voyages, médiathèque, WPForms, apparence, extensions, comptes, réglages.
 * Version:           0.1.0
 * Requires at least: 6.0
 * Requires PHP:      7.4
 * Author:            Rémi Oravec
 * Text Domain:       ae-back-office
 *
 * ------------------------------------------------------------------
 * CE QUE CE PLUGIN NE FAIT PAS
 * ------------------------------------------------------------------
 * Il ne touche à AUCUN contenu, à aucune URL publique, à aucun
 * réglage du site. Il n'agit que sur l'affichage du back-office,
 * et seulement pour les comptes concernés.
 *
 * Le masquage est cosmétique : `remove_menu_page()` retire une entrée
 * de menu, jamais une capacité. Une personne qui connaît l'adresse
 * d'un écran masqué y accède toujours — c'est voulu, rien n'est
 * verrouillé. Un interrupteur « Tout afficher » est présent en
 * permanence dans la barre d'administration.
 *
 * Désactiver le plugin restitue le back-office d'origine à
 * l'identique. Le rangement par gabarit est conservé en base
 * (méta `_ae_gabarit`) et se recalcule tout seul si besoin.
 * ------------------------------------------------------------------
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

define( 'ABO_VERSION', '0.1.0' );
define( 'ABO_FILE', __FILE__ );
define( 'ABO_DIR', plugin_dir_path( __FILE__ ) );
define( 'ABO_URL', plugin_dir_url( __FILE__ ) );

require_once ABO_DIR . 'includes/class-abo-gabarits.php';
require_once ABO_DIR . 'includes/class-abo-contenus.php';
require_once ABO_DIR . 'includes/class-abo-demandes.php';
require_once ABO_DIR . 'includes/class-abo-menu.php';

function abo_init() {
	ABO_Gabarits::init();
	ABO_Contenus::init();
	ABO_Demandes::init();
	ABO_Menu::init();
}
add_action( 'plugins_loaded', 'abo_init' );

/**
 * La feuille de style commune, enregistrée une fois pour toutes.
 *
 * Elle était auparavant déclarée par l'écran « Contenus », qui s'en
 * servait le premier. « Demandes » partageait le fichier sans le
 * déclarer : l'écran s'affichait donc entièrement nu dès qu'on
 * l'ouvrait sans être passé par l'autre. Un fichier partagé
 * s'enregistre au démarrage, et chaque écran demande ce dont il a
 * besoin — jamais l'inverse.
 */
function abo_enregistrer_styles() {
	wp_register_style( 'abo-admin', ABO_URL . 'assets/css/admin.css', array(), ABO_VERSION );
}
add_action( 'admin_enqueue_scripts', 'abo_enregistrer_styles', 5 );

/**
 * Activation : on range une première fois tout le contenu existant.
 * L'opération est en lecture seule côté contenu — elle n'écrit qu'une
 * méta de classement.
 */
function abo_activation() {
	ABO_Demandes::enregistrer_type();
	ABO_Gabarits::ranger_tout();
}

/**
 * Désactivation : on retire la tâche de purge. Les demandes déjà
 * enregistrées sont conservées.
 */
function abo_desactivation() {
	$prochaine = wp_next_scheduled( 'abo_purge_quotidienne' );
	if ( $prochaine ) {
		wp_unschedule_event( $prochaine, 'abo_purge_quotidienne' );
	}
}
register_deactivation_hook( __FILE__, 'abo_desactivation' );
register_activation_hook( __FILE__, 'abo_activation' );
