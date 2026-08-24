<?php
/**
 * Rôles et capacités de la zone de refonte.
 *
 * Trois capacités, volontairement distinctes des capacités WordPress :
 *
 *   ae_view_refonte    voir les maquettes sur /refonte/...
 *   ae_add_note        déposer une annotation et répondre dans un fil
 *   ae_manage_refonte  administrer (changer les statuts, exporter, supprimer)
 *
 * Le rôle `ae_relecteur` ne porte que les deux premières. Un compte
 * relecteur ne peut donc rien modifier sur le site en ligne : il n'a ni
 * `edit_posts`, ni `upload_files`, ni accès au back-office au-delà de son
 * profil. L'envoi d'image passe par un point REST dédié qui vérifie
 * `ae_add_note`, pas `upload_files`.
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

class AE_Refonte_Roles {

	const ROLE_RELECTEUR = 'ae_relecteur';

	const CAP_VOIR    = 'ae_view_refonte';
	const CAP_ANNOTER = 'ae_add_note';
	const CAP_GERER   = 'ae_manage_refonte';

	/**
	 * Crée le rôle relecteur et donne les trois capacités aux administrateurs.
	 * Appelée à l'activation ; idempotente.
	 */
	public static function installer() {
		add_role(
			self::ROLE_RELECTEUR,
			'Relecteur refonte',
			array(
				'read'            => true,
				self::CAP_VOIR    => true,
				self::CAP_ANNOTER => true,
			)
		);

		// add_role n'écrase pas un rôle déjà présent : on force les capacités.
		$relecteur = get_role( self::ROLE_RELECTEUR );
		if ( $relecteur ) {
			$relecteur->add_cap( 'read' );
			$relecteur->add_cap( self::CAP_VOIR );
			$relecteur->add_cap( self::CAP_ANNOTER );
		}

		foreach ( array( 'administrator', 'editor' ) as $nom ) {
			$role = get_role( $nom );
			if ( ! $role ) {
				continue;
			}
			$role->add_cap( self::CAP_VOIR );
			$role->add_cap( self::CAP_ANNOTER );
			if ( 'administrator' === $nom ) {
				$role->add_cap( self::CAP_GERER );
			}
		}
	}

	/** L'utilisateur courant peut-il consulter la zone de refonte ? */
	public static function peut_voir() {
		return current_user_can( self::CAP_VOIR );
	}

	/** L'utilisateur courant peut-il annoter ? */
	public static function peut_annoter() {
		return current_user_can( self::CAP_ANNOTER );
	}

	/** L'utilisateur courant administre-t-il la refonte ? */
	public static function peut_gerer() {
		return current_user_can( self::CAP_GERER );
	}
}
