<?php
/**
 * Notification par courriel à chaque demande déposée.
 *
 * Volontairement minimal : un message par demande, vers une seule adresse
 * réglable. Le contenu de la demande est repris tel quel pour qu'on puisse
 * y répondre sans ouvrir le back-office.
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

class AE_Refonte_Notifications {

	public static function init() {
		add_action( 'ae_refonte_note_creee', array( __CLASS__, 'prevenir' ) );
	}

	/**
	 * @param WP_Post $note
	 */
	public static function prevenir( $note ) {
		$destinataire = get_option( 'ae_refonte_email', get_option( 'admin_email' ) );
		if ( ! is_email( $destinataire ) ) {
			return;
		}

		$donnees     = AE_Refonte_Rest::formater_note( $note );
		$maquette    = get_the_title( $donnees['maquette'] );
		$url         = get_permalink( $donnees['maquette'] ) . '#ae-note-' . $note->ID;
		$type        = AE_Refonte_Types::TYPES_NOTE[ $donnees['type'] ] ?? $donnees['type'];

		$sujet = sprintf( '[Refonte] %s — %s', $maquette, $type );

		$corps = array(
			sprintf( 'Nouvelle demande de %s sur la maquette « %s ».', $donnees['auteur'], $maquette ),
			'',
			sprintf( 'Type : %s', $type ),
		);

		if ( $donnees['ancre'] ) {
			$corps[] = sprintf( 'Élément visé : « %s »', $donnees['ancre'] );
		}
		if ( $donnees['largeur'] ) {
			$corps[] = sprintf( 'Vu sur un écran de %d px de large', $donnees['largeur'] );
		}

		$corps[] = '';
		$corps[] = wp_strip_all_tags( $donnees['message'] );

		if ( $donnees['valeur'] ) {
			$corps[] = '';
			$corps[] = sprintf( 'Proposition : %s', $donnees['valeur'] );
		}
		if ( $donnees['media'] ) {
			$corps[] = sprintf( 'Image proposée : %s', $donnees['media'] );
		}

		$corps[] = '';
		$corps[] = sprintf( 'Voir sur la maquette : %s', $url );

		wp_mail( $destinataire, $sujet, implode( "\n", $corps ) );
	}
}
