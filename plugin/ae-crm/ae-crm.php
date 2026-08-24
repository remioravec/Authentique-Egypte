<?php
/**
 * Plugin Name:       AE CRM — les demandes reçues
 * Plugin URI:        https://github.com/remioravec/Authentique-Egypte
 * Description:       Conserve les demandes envoyées par les formulaires du site — que WPForms Lite n'enregistre pas — et les présente en pipeline : quatre colonnes, une carte par demande qu'on fait glisser de l'une à l'autre, la fiche client au clic. Le formulaire et l'envoi du courriel ne sont pas modifiés.
 * Version:           1.0.0
 * Requires at least: 6.0
 * Requires PHP:      7.4
 * Author:            Rémi Oravec
 * Text Domain:       ae-crm
 *
 * ------------------------------------------------------------------
 * POURQUOI CE PLUGIN EXISTE SÉPARÉMENT
 * ------------------------------------------------------------------
 * Les demandes étaient un module de « AE Back-office ». Deux écrans y
 * partageaient une feuille de style qu'un seul déclarait : ouvert
 * directement, le tableau s'affichait entièrement nu. Le symptôme est
 * anodin, la leçon ne l'est pas — un outil dont l'agence se sert tous
 * les jours ne doit dépendre de rien d'autre pour fonctionner.
 *
 * Ce plugin est donc autonome. Il ne suppose la présence d'aucune
 * autre extension, charge ses propres fichiers, et fonctionne seul.
 *
 * ------------------------------------------------------------------
 * CE QU'IL NE FAIT PAS
 * ------------------------------------------------------------------
 * Il ne modifie AUCUN formulaire et AUCUN courriel. Il écoute
 * `wpforms_process_complete`, une action qui se déclenche APRÈS que
 * WPForms a validé la soumission et envoyé ses notifications. Une
 * action, pas un filtre : rien de ce qui est fait ici ne remonte à
 * WPForms. Le désactiver ne change rien à la réception des demandes
 * par courriel — on perd seulement l'archive.
 *
 * ------------------------------------------------------------------
 * DONNÉES PERSONNELLES
 * ------------------------------------------------------------------
 * Ces enregistrements contiennent noms, adresses et numéros. Ils
 * vivent dans un type de contenu privé, invisible du site public,
 * exclu de la recherche, des flux et des plans de site. Une durée de
 * conservation est réglable ; tant qu'elle ne l'est pas, rien n'est
 * supprimé — une purge silencieuse par défaut serait pire que pas de
 * purge du tout.
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

define( 'AECRM_VERSION', '1.0.0' );
define( 'AECRM_FILE', __FILE__ );
define( 'AECRM_DIR', plugin_dir_path( __FILE__ ) );
define( 'AECRM_URL', plugin_dir_url( __FILE__ ) );

require_once AECRM_DIR . 'includes/class-aecrm-demandes.php';
require_once AECRM_DIR . 'includes/class-aecrm-ecran.php';
require_once AECRM_DIR . 'includes/class-aecrm-reglages.php';

function aecrm_init() {
	AECRM_Demandes::init();
	AECRM_Ecran::init();
	AECRM_Reglages::init();
}
add_action( 'plugins_loaded', 'aecrm_init' );

/**
 * Le module « Demandes » de l'ancien AE Back-office se retire.
 *
 * Les deux ont vécu ensemble : si l'ancienne version est encore
 * installée, chaque formulaire envoyé serait enregistré DEUX fois et
 * deux entrées « Demandes » apparaîtraient dans le menu. On le
 * débranche plutôt que de compter sur une désinstallation manuelle.
 *
 * Priorité 20 : après que abo_init() a posé ses greffons.
 */
function aecrm_debrancher_ancien() {
	if ( ! class_exists( 'ABO_Demandes' ) ) {
		return;
	}

	remove_action( 'wpforms_process_complete', array( 'ABO_Demandes', 'capter' ), 10 );
	remove_action( 'admin_menu', array( 'ABO_Demandes', 'menu' ), 9 );
	remove_action( 'admin_enqueue_scripts', array( 'ABO_Demandes', 'assets' ) );
	remove_action( 'init', array( 'ABO_Demandes', 'enregistrer_type' ) );
	remove_action( 'abo_purge_quotidienne', array( 'ABO_Demandes', 'purger' ) );
}
add_action( 'plugins_loaded', 'aecrm_debrancher_ancien', 20 );

function aecrm_activation() {
	AECRM_Demandes::enregistrer_type();

	if ( ! wp_next_scheduled( AECRM_Demandes::TACHE ) ) {
		wp_schedule_event( time() + HOUR_IN_SECONDS, 'daily', AECRM_Demandes::TACHE );
	}
}
register_activation_hook( __FILE__, 'aecrm_activation' );

/**
 * Désactivation : on retire la tâche de purge. Les demandes déjà
 * enregistrées sont conservées — désactiver un plugin ne doit jamais
 * effacer les données d'un client.
 */
function aecrm_desactivation() {
	$prochaine = wp_next_scheduled( AECRM_Demandes::TACHE );
	if ( $prochaine ) {
		wp_unschedule_event( $prochaine, AECRM_Demandes::TACHE );
	}
}
register_deactivation_hook( __FILE__, 'aecrm_desactivation' );
