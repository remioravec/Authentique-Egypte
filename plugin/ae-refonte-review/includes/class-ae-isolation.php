<?php
/**
 * Étanchéité de la zone de refonte.
 *
 * L'essentiel de l'isolation est structurel : les deux types de contenu
 * sont `public => false`, donc déjà hors sitemap, hors recherche et hors
 * menus. Cette classe pose les ceintures et bretelles qui restent :
 * en-têtes noindex, exclusion explicite des sitemaps Yoast et WordPress,
 * et désactivation du cache LiteSpeed sur les URL de refonte.
 *
 * Aucun filtre de cette classe ne s'applique à un contenu qui n'appartient
 * pas au plugin : chaque méthode commence par vérifier le type.
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

class AE_Refonte_Isolation {

	public static function init() {
		add_filter( 'wp_robots', array( __CLASS__, 'robots' ) );
		add_filter( 'wpseo_sitemap_exclude_post_type', array( __CLASS__, 'yoast_exclure_type' ), 10, 2 );
		add_filter( 'wp_sitemaps_post_types', array( __CLASS__, 'core_exclure_type' ) );
		add_action( 'template_redirect', array( __CLASS__, 'sans_cache' ), 1 );
	}

	/** Sommes-nous sur une URL de maquette ? */
	private static function est_maquette() {
		return is_singular( AE_Refonte_Types::MAQUETTE );
	}

	/**
	 * noindex, nofollow sur toute maquette. Sans effet ailleurs.
	 *
	 * @param array $robots
	 * @return array
	 */
	public static function robots( $robots ) {
		if ( ! self::est_maquette() ) {
			return $robots;
		}

		$robots['noindex']     = true;
		$robots['nofollow']    = true;
		$robots['noarchive']   = true;
		$robots['nosnippet']   = true;
		$robots['noimageindex'] = true;

		return $robots;
	}

	/**
	 * Exclusion du sitemap Yoast.
	 *
	 * @param bool   $exclure
	 * @param string $type
	 * @return bool
	 */
	public static function yoast_exclure_type( $exclure, $type ) {
		if ( AE_Refonte_Types::MAQUETTE === $type || AE_Refonte_Types::NOTE === $type ) {
			return true;
		}

		return $exclure;
	}

	/**
	 * Exclusion du sitemap natif de WordPress.
	 *
	 * @param array $types
	 * @return array
	 */
	public static function core_exclure_type( $types ) {
		unset( $types[ AE_Refonte_Types::MAQUETTE ], $types[ AE_Refonte_Types::NOTE ] );

		return $types;
	}

	/**
	 * Une maquette ne doit jamais être servie depuis un cache : elle est
	 * personnalisée (annotations de la relectrice connectée) et sa mise en
	 * cache risquerait de fuiter vers un visiteur anonyme.
	 */
	public static function sans_cache() {
		if ( ! self::est_maquette() ) {
			return;
		}

		nocache_headers();
		header( 'X-Robots-Tag: noindex, nofollow, noarchive', true );

		// LiteSpeed Cache — présent sur l'hébergement Hostinger du site.
		do_action( 'litespeed_control_set_nocache', 'zone de refonte, contenu privé' );

		if ( ! defined( 'DONOTCACHEPAGE' ) ) {
			define( 'DONOTCACHEPAGE', true );
		}
	}
}
