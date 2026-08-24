<?php
/**
 * Le vocabulaire des gabarits, et le rangement automatique.
 *
 * Un gabarit, c'est un modèle de page : tout ce qui partage une
 * structure et un rôle. C'est le même vocabulaire que les maquettes de
 * refonte, volontairement — ranger le back-office avec les mots de la
 * refonte évite d'avoir deux nomenclatures qui se contredisent.
 *
 * Le classement est stocké en méta `_ae_gabarit`. Il est déduit
 * automatiquement, et modifiable à la main : un choix manuel n'est
 * jamais écrasé par un recalcul.
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

class ABO_Gabarits {

	const META      = '_ae_gabarit';
	const META_MAIN = '_ae_gabarit_manuel';

	/**
	 * Le vocabulaire. L'ordre compte : c'est celui de l'écran Contenus,
	 * du plus structurant au plus périphérique.
	 */
	const VOCABULAIRE = array(
		'accueil'     => array( 'nom' => 'Accueil', 'icone' => '🏠', 'aide' => 'La page d\'accueil du site.' ),
		'categorie'   => array( 'nom' => 'Catégorie de séjours', 'icone' => '🗂', 'aide' => 'Les familles de séjours : croisière, désert, culturel, mer Rouge, Sinaï.' ),
		'voyage'      => array( 'nom' => 'Voyage', 'icone' => '🧭', 'aide' => 'Les itinéraires vendus, un par page. C\'est l\'unité d\'achat.' ),
		'destination' => array( 'nom' => 'Destination', 'icone' => '📍', 'aide' => 'Les pages géographiques : Le Caire, Louxor, le désert Blanc…' ),
		'qui-part'    => array( 'nom' => 'Qui part', 'icone' => '👥', 'aide' => 'Famille, couple, solo, mobilité réduite.' ),
		'hub-guides'  => array( 'nom' => 'Hub des guides', 'icone' => '📚', 'aide' => 'La page qui liste les guides pratiques.' ),
		'guide'       => array( 'nom' => 'Guide pratique', 'icone' => '📄', 'aide' => 'Les articles : quand partir, formalités, sécurité…' ),
		'devis'       => array( 'nom' => 'Devis', 'icone' => '✉️', 'aide' => 'La page de demande de devis.' ),
		'agence'      => array( 'nom' => 'Agence', 'icone' => '🏛', 'aide' => 'Qui sommes-nous, l\'équipe, les engagements.' ),
		'legal'       => array( 'nom' => 'Mentions et légal', 'icone' => '⚖️', 'aide' => 'Mentions légales, confidentialité, CGV.' ),
		'maquette'    => array( 'nom' => 'Maquette de refonte', 'icone' => '🎨', 'aide' => 'Les pages de la zone de refonte, invisibles du public.' ),
		'technique'   => array( 'nom' => 'Technique', 'icone' => '⚙️', 'aide' => 'Newsletter, remerciements, pages de service.' ),
		'autre'       => array( 'nom' => 'Non rangé', 'icone' => '❓', 'aide' => 'À classer à la main.' ),
	);

	/** Les types de contenu réunis dans l'écran Contenus. */
	public static function types() {
		$types = array( 'page', 'post' );

		foreach ( array( 'programs' ) as $extra ) {
			if ( post_type_exists( $extra ) ) {
				$types[] = $extra;
			}
		}

		/**
		 * Permet d'ajouter un type de contenu à l'écran Contenus.
		 *
		 * @param string[] $types
		 */
		return apply_filters( 'abo_types_contenu', $types );
	}

	public static function init() {
		// Un enregistrement met le classement à jour, sauf s'il a été
		// fixé à la main.
		add_action( 'save_post', array( __CLASS__, 'au_fil_de_l_eau' ), 20, 2 );
	}

	public static function au_fil_de_l_eau( $post_id, $post ) {
		if ( wp_is_post_revision( $post_id ) || wp_is_post_autosave( $post_id ) ) {
			return;
		}
		if ( ! in_array( $post->post_type, self::types(), true )
			&& 'ae_maquette' !== $post->post_type ) {
			return;
		}
		if ( get_post_meta( $post_id, self::META_MAIN, true ) ) {
			return; // classement fixé à la main, on n'y touche pas
		}

		update_post_meta( $post_id, self::META, self::deduire( $post ) );
	}

	/**
	 * Le gabarit d'un contenu, déduit de ce qu'on sait de lui.
	 *
	 * L'ordre des tests va du plus certain au plus approximatif.
	 *
	 * @param WP_Post $post
	 * @return string
	 */
	public static function deduire( $post ) {
		$slug = $post->post_name;

		// 1. Le type de contenu tranche à lui seul dans trois cas.
		if ( 'ae_maquette' === $post->post_type ) {
			return 'maquette';
		}
		if ( 'programs' === $post->post_type ) {
			return 'voyage';
		}
		if ( 'post' === $post->post_type ) {
			return 'guide';
		}

		// 2. Les pages que WordPress désigne lui-même.
		if ( (int) get_option( 'page_on_front' ) === (int) $post->ID ) {
			return 'accueil';
		}
		if ( (int) get_option( 'page_for_posts' ) === (int) $post->ID ) {
			return 'hub-guides';
		}

		// 3. Les pages de la zone de refonte, reconnaissables au parent.
		$mere = get_page_by_path( 'refonte-2026' );
		if ( $mere && (int) $post->post_parent === (int) $mere->ID ) {
			return 'maquette';
		}

		// 4. Une page fille de « Nos séjours » est une catégorie de séjours.
		//    Ce test passe avant celui du slug : /mer-rouge/ est fille de
		//    « Nos séjours », c'est donc une catégorie, quand bien même son
		//    slug ressemble à celui d'une page destination.
		$sejours = get_page_by_path( 'nos-sejours-egypte' );
		if ( $sejours ) {
			if ( (int) $post->ID === (int) $sejours->ID
				|| (int) $post->post_parent === (int) $sejours->ID ) {
				return 'categorie';
			}
		}

		// 5. Le slug, du motif le plus spécifique au plus large.
		$motifs = array(
			'legal'       => array( 'mentions-legales', 'confidentialite', 'cgv', 'politique-de-' ),
			'devis'       => array( 'sur-mesure', 'devis', 'demande-de-devis', 'contact' ),
			'agence'      => array( 'qui-sommes-nous', 'notre-agence', 'a-propos', 'equipe' ),
			'hub-guides'  => array( 'notre-blog', 'blog', 'guides-pratiques', 'actualites' ),
			'technique'   => array( 'newsletter', 'merci', 'remerciement', 'desinscription' ),
			'qui-part'    => array( 'voyage-en-famille', 'voyage-en-couple', 'voyage-solo', 'voyage-pmr' ),
			'destination' => array( 'voyage-a-', 'voyage-au-', 'desert-blanc', 'desert-noir', 'lac-nasser', 'mont-sinai', 'mer-rouge' ),
		);

		foreach ( $motifs as $gabarit => $fragments ) {
			foreach ( $fragments as $fragment ) {
				if ( false !== strpos( $slug, $fragment ) ) {
					return $gabarit;
				}
			}
		}

		return 'autre';
	}

	/**
	 * Range tout le contenu du site. Ne touche pas aux classements manuels.
	 *
	 * @return array<string,int> le compte par gabarit
	 */
	public static function ranger_tout() {
		$types = self::types();
		if ( post_type_exists( 'ae_maquette' ) ) {
			$types[] = 'ae_maquette';
		}

		$posts = get_posts(
			array(
				'post_type'      => $types,
				'post_status'    => 'any',
				'posts_per_page' => -1,
			)
		);

		$compte = array();
		foreach ( $posts as $post ) {
			if ( get_post_meta( $post->ID, self::META_MAIN, true ) ) {
				$gabarit = get_post_meta( $post->ID, self::META, true ) ?: 'autre';
			} else {
				$gabarit = self::deduire( $post );
				update_post_meta( $post->ID, self::META, $gabarit );
			}
			$compte[ $gabarit ] = ( $compte[ $gabarit ] ?? 0 ) + 1;
		}

		return $compte;
	}

	/** Le gabarit d'un contenu, avec repli sur la déduction. */
	public static function du( $post ) {
		$gabarit = get_post_meta( $post->ID, self::META, true );
		if ( $gabarit && isset( self::VOCABULAIRE[ $gabarit ] ) ) {
			return $gabarit;
		}

		return self::deduire( $post );
	}

	/** Libellé lisible, icône comprise. */
	public static function libelle( $gabarit ) {
		$entree = self::VOCABULAIRE[ $gabarit ] ?? self::VOCABULAIRE['autre'];

		return $entree['icone'] . ' ' . $entree['nom'];
	}
}
