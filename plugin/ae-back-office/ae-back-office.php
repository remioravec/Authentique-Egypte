<?php
/**
 * Plugin Name:       AE Back-office — contenus rangés par gabarit
 * Plugin URI:        https://github.com/remioravec/Authentique-Egypte
 * Description:       Remplace « Articles » et « Pages » par un écran unique « Contenus », rangé par gabarit (accueil, catégorie, voyage, destination, guide, devis, agence…). Masque les entrées de menu inutiles pour ne laisser que l'essentiel : contenus, médiathèque, apparence, extensions, comptes, réglages.
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
require_once ABO_DIR . 'includes/class-abo-menu.php';

function abo_init() {
	ABO_Gabarits::init();
	ABO_Contenus::init();
	ABO_Menu::init();
}
add_action( 'plugins_loaded', 'abo_init' );

/**
 * Activation : on range une première fois tout le contenu existant.
 * L'opération est en lecture seule côté contenu — elle n'écrit qu'une
 * méta de classement.
 */
function abo_activation() {
	ABO_Gabarits::ranger_tout();
}
register_activation_hook( __FILE__, 'abo_activation' );
