<?php
/**
 * Le calque, sur toutes les pages du site.
 *
 * Condition unique : un compte connecté qui a `aec_commenter`. Un
 * visiteur ne reçoit ni script, ni style, ni donnée — le calque
 * n'existe pas pour lui.
 *
 * On se tient à l'écart des contextes où un calque flottant gênerait :
 * l'éditeur Elementor, les flux, les requêtes REST et les impressions.
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

class AEC_Front {

	public static function init() {
		add_action( 'wp_enqueue_scripts', array( __CLASS__, 'charger' ) );
	}

	private static function contexte_valide() {
		if ( is_admin() || is_feed() || is_embed() ) {
			return false;
		}
		if ( defined( 'REST_REQUEST' ) && REST_REQUEST ) {
			return false;
		}
		// Aperçu et éditeur Elementor : on ne se superpose pas à l'outil.
		if ( isset( $_GET['elementor-preview'] ) || isset( $_GET['action'] ) && 'elementor' === $_GET['action'] ) {
			return false;
		}

		return AEC_Roles::peut_commenter();
	}

	public static function charger() {
		if ( ! self::contexte_valide() ) {
			return;
		}

		wp_enqueue_style( 'aec', AEC_URL . 'assets/css/commentaires.css', array(), AEC_VERSION );
		wp_enqueue_script( 'aec', AEC_URL . 'assets/js/commentaires.js', array(), AEC_VERSION, true );

		$utilisateur = wp_get_current_user();
		$objet       = get_queried_object_id();

		wp_localize_script( 'aec', 'AEC', array(
			'racine'     => esc_url_raw( rest_url( AEC_Rest::NS ) ),
			'nonce'      => wp_create_nonce( 'wp_rest' ),
			'post'       => (int) $objet,
			'url'        => esc_url_raw( home_url( add_query_arg( array() ) ) ),
			'titre'      => $objet ? get_the_title( $objet ) : get_bloginfo( 'name' ),
			'peutModerer' => AEC_Roles::peut_moderer(),
			'moi'        => array(
				'id'      => $utilisateur->ID,
				'nom'     => $utilisateur->display_name,
				'initiales' => self::initiales( $utilisateur->display_name ),
			),
		) );
	}

	private static function initiales( $nom ) {
		$mots = preg_split( '/[\s._-]+/', trim( (string) $nom ) );
		$initiales = '';
		foreach ( array_slice( array_filter( $mots ), 0, 2 ) as $mot ) {
			$initiales .= mb_strtoupper( mb_substr( $mot, 0, 1 ) );
		}

		return $initiales ?: '?';
	}
}
