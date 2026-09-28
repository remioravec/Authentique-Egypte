<?php
/**
 * Plugin Name:       AE Commentaires — relecture façon Google Docs
 * Plugin URI:        https://github.com/remioravec/Authentique-Egypte
 * Description:       Un calque de commentaires sur n'importe quelle page du site. On active le mode commentaire, on clique sur l'élément à changer, on écrit — avec une image si besoin. Les fils s'épinglent sur la page, se répondent et se résolvent. Invisible pour les visiteurs.
 * Version:           1.2.1
 * Requires at least: 6.0
 * Requires PHP:      7.4
 * Author:            Rémi Oravec
 * Text Domain:       ae-commentaires
 *
 * ------------------------------------------------------------------
 * CE QUE FAIT CE PLUGIN
 * ------------------------------------------------------------------
 * Le même geste que Google Docs ou Figma : un bouton, un clic sur
 * l'élément, on écrit. Pas de formulaire, pas de type à choisir, pas
 * de champ obligatoire. Une épingle numérotée reste sur l'élément, le
 * fil s'ouvre au clic, on répond, on résout.
 *
 * Il agit sur TOUTE page du site — pages en ligne, brouillons de
 * refonte, articles, voyages. Le commentaire est ancré à l'élément par
 * un sélecteur CSS, son texte de secours et une position relative,
 * de sorte qu'il retrouve sa place même si la page change un peu.
 *
 * ------------------------------------------------------------------
 * CE QU'IL NE FAIT PAS
 * ------------------------------------------------------------------
 * Il ne modifie aucun contenu, aucune URL, aucun réglage. Le calque
 * n'est chargé que pour un compte connecté qui a la capacité
 * `aec_commenter` : un visiteur ne reçoit ni script, ni style, ni
 * donnée. Les commentaires vivent dans un type de contenu privé,
 * hors sitemap, hors recherche, hors flux.
 *
 * Désactiver le plugin fait disparaître le calque sans rien toucher
 * au site.
 * ------------------------------------------------------------------
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

define( 'AEC_VERSION', '1.2.1' );
define( 'AEC_FILE', __FILE__ );
define( 'AEC_DIR', plugin_dir_path( __FILE__ ) );
define( 'AEC_URL', plugin_dir_url( __FILE__ ) );

require_once AEC_DIR . 'includes/class-aec-roles.php';
require_once AEC_DIR . 'includes/class-aec-types.php';
require_once AEC_DIR . 'includes/class-aec-rest.php';
require_once AEC_DIR . 'includes/class-aec-front.php';
require_once AEC_DIR . 'includes/class-aec-admin.php';
require_once AEC_DIR . 'includes/class-aec-courriel.php';

function aec_init() {
	AEC_Types::init();
	AEC_Rest::init();
	AEC_Front::init();
	AEC_Admin::init();
	AEC_Courriel::init();
}
add_action( 'plugins_loaded', 'aec_init' );

function aec_activation() {
	AEC_Roles::installer();
	AEC_Types::enregistrer();
	flush_rewrite_rules();
}

/**
 * À la désactivation, on retire les envois encore programmés.
 *
 * Sans cela, un courriel préparé juste avant la coupure partirait au
 * réveil du plugin, des jours plus tard, pour des remarques que tout le
 * monde a oubliées.
 */
function aec_desactivation() {
	foreach ( get_users( array( 'fields' => array( 'ID' ) ) ) as $u ) {
		$quand = wp_next_scheduled( AEC_Courriel::TACHE, array( (int) $u->ID ) );
		if ( $quand ) {
			wp_unschedule_event( $quand, AEC_Courriel::TACHE, array( (int) $u->ID ) );
		}
	}
}
register_deactivation_hook( __FILE__, 'aec_desactivation' );
register_activation_hook( __FILE__, 'aec_activation' );
