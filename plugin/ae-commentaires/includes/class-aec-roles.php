<?php
/**
 * Deux capacités, pas plus.
 *
 *   aec_commenter  ouvrir un fil, répondre, joindre une image
 *   aec_moderer    résoudre et supprimer les fils des autres
 *
 * Le rôle « Relecteur » ne porte que la première. Un compte relecteur
 * n'a ni `edit_posts`, ni `upload_files`, ni accès au back-office : il
 * ne peut rien modifier sur le site. L'envoi d'image passe par un
 * point REST dédié qui vérifie `aec_commenter`, jamais `upload_files`.
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

class AEC_Roles {

	const ROLE = 'ae_relecteur';

	const CAP_COMMENTER = 'aec_commenter';
	const CAP_MODERER   = 'aec_moderer';

	public static function installer() {
		add_role(
			self::ROLE,
			'Relecteur',
			array(
				'read'              => true,
				self::CAP_COMMENTER => true,
			)
		);

		// add_role n'écrase pas un rôle existant : on force les capacités.
		$relecteur = get_role( self::ROLE );
		if ( $relecteur ) {
			$relecteur->add_cap( 'read' );
			$relecteur->add_cap( self::CAP_COMMENTER );
		}

		foreach ( array( 'administrator', 'editor', 'author' ) as $nom ) {
			$role = get_role( $nom );
			if ( ! $role ) {
				continue;
			}
			$role->add_cap( self::CAP_COMMENTER );
			if ( 'author' !== $nom ) {
				$role->add_cap( self::CAP_MODERER );
			}
		}
	}

	public static function peut_commenter() {
		return is_user_logged_in() && current_user_can( self::CAP_COMMENTER );
	}

	public static function peut_moderer() {
		return current_user_can( self::CAP_MODERER );
	}
}
