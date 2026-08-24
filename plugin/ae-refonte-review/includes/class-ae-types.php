<?php
/**
 * Les deux types de contenu de la refonte.
 *
 * Tous deux sont `public => false`. Conséquences voulues : absents des
 * sitemaps (Yoast lit `public`), de la recherche interne, des archives,
 * des flux et du sélecteur de menus. Seul `ae_maquette` est
 * `publicly_queryable` pour disposer d'une URL — l'accès à cette URL est
 * ensuite filtré par capacité (voir AE_Refonte_Rendu).
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

class AE_Refonte_Types {

	const MAQUETTE = 'ae_maquette';
	const NOTE     = 'ae_note';

	/** Les états possibles d'une maquette dans le parcours de relecture. */
	const ETATS = array(
		'a_produire'   => 'À produire',
		'a_revoir'     => 'À revoir',
		'en_relecture' => 'En relecture',
		'validee'      => 'Validée',
	);

	/** Les types de demande que la cliente peut déposer. */
	const TYPES_NOTE = array(
		'texte'      => 'Texte',
		'couleur'    => 'Couleur',
		'image'      => 'Image',
		'espacement' => 'Mise en page',
		'autre'      => 'Autre',
	);

	/** Le cycle de vie d'une demande. */
	const STATUTS_NOTE = array(
		'ouverte'  => 'Ouverte',
		'en_cours' => 'En cours',
		'traitee'  => 'Traitée',
		'refusee'  => 'Non retenue',
	);

	public static function init() {
		add_action( 'init', array( __CLASS__, 'enregistrer' ) );
	}

	public static function enregistrer() {
		register_post_type(
			self::MAQUETTE,
			array(
				'labels'              => array(
					'name'          => 'Maquettes',
					'singular_name' => 'Maquette',
					'add_new_item'  => 'Ajouter une maquette',
					'edit_item'     => 'Modifier la maquette',
				),
				'public'              => false,
				'publicly_queryable'  => true,
				'exclude_from_search' => true,
				'show_ui'             => true,
				'show_in_menu'        => false, // rattaché au menu du plugin
				'show_in_nav_menus'   => false,
				'show_in_rest'        => false,
				'has_archive'         => false,
				'hierarchical'        => false,
				'rewrite'             => array(
					'slug'       => 'refonte',
					'with_front' => false,
				),
				'query_var'           => false,
				'capability_type'     => 'post',
				'map_meta_cap'        => true,
				'supports'            => array( 'title', 'page-attributes' ),
			)
		);

		register_post_type(
			self::NOTE,
			array(
				'labels'              => array(
					'name'          => 'Demandes',
					'singular_name' => 'Demande',
				),
				'public'              => false,
				'publicly_queryable'  => false,
				'exclude_from_search' => true,
				'show_ui'             => false, // écran d'administration dédié
				'show_in_nav_menus'   => false,
				'show_in_rest'        => false,
				'has_archive'         => false,
				'rewrite'             => false,
				'query_var'           => false,
				'capability_type'     => 'post',
				'map_meta_cap'        => true,
				'supports'            => array( 'title', 'editor', 'author' ),
			)
		);
	}

	/**
	 * Le parcours de relecture : les maquettes dans l'ordre voulu.
	 *
	 * @return WP_Post[]
	 */
	public static function parcours() {
		return get_posts(
			array(
				'post_type'      => self::MAQUETTE,
				'post_status'    => array( 'publish', 'draft', 'private' ),
				'posts_per_page' => -1,
				'orderby'        => array(
					'menu_order' => 'ASC',
					'title'      => 'ASC',
				),
			)
		);
	}

	/**
	 * Compte les demandes non traitées d'une maquette.
	 *
	 * @param int $maquette_id
	 * @return int
	 */
	public static function compter_notes_ouvertes( $maquette_id ) {
		$notes = get_posts(
			array(
				'post_type'      => self::NOTE,
				'post_status'    => 'publish',
				'posts_per_page' => -1,
				'fields'         => 'ids',
				'meta_query'     => array(
					array(
						'key'   => '_ae_maquette',
						'value' => (int) $maquette_id,
					),
					array(
						'key'     => '_ae_statut',
						'value'   => array( 'ouverte', 'en_cours' ),
						'compare' => 'IN',
					),
				),
			)
		);

		return count( $notes );
	}
}
