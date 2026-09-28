<?php
/**
 * Les deux crochets enfin écoutés.
 *
 * `aec_fil_ouvert` et `aec_reponse_ajoutee` étaient émis depuis le
 * début, et personne ne s'y branchait : aucun courriel n'est jamais
 * parti. C'est la moitié du problème que la version 1.1.0 corrige —
 * l'autre moitié étant les signaux posés sur le site.
 *
 * CE QUI PART, ET À QUI
 *
 *   un fil ouvert   → à l'équipe (ceux qui modèrent), jamais à l'auteur
 *   une réponse     → à l'auteur du fil, et aux autres qui y ont parlé
 *
 * On ne s'écrit jamais à soi-même : celui qui vient d'écrire ne reçoit
 * pas son propre message. Sans cette règle, répondre à quelqu'un vous
 * renvoie votre propre texte, et l'outil perd sa crédibilité au premier
 * échange.
 *
 * LE GROUPEMENT
 *
 * Une relecture se fait par salves : cent quatorze remarques en trois
 * jours, parfois vingt sur une même page en dix minutes. Un courriel
 * par remarque serait un envoi toutes les trente secondes, et la boîte
 * de réception deviendrait le problème plutôt que la solution.
 *
 * Chaque destinataire a donc un délai de grâce : le premier message
 * programme un envoi différé, et tout ce qui arrive pendant l'attente
 * s'y ajoute. Un seul courriel part, qui dit « sept nouvelles remarques
 * sur trois pages », avec le détail et les liens.
 *
 * L'OPTION DE SILENCE
 *
 * Chaque compte peut couper ses courriels depuis son profil. C'est une
 * case, pas un réglage caché : quelqu'un qui reçoit un message non
 * désiré doit pouvoir l'arrêter lui-même, sans passer par nous.
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

class AEC_Courriel {

	/** La file d'attente d'un destinataire, en méta utilisateur. */
	const FILE = '_aec_courriel_file';

	/** La case « je ne veux pas de courriel », en méta utilisateur. */
	const SILENCE = '_aec_courriel_silence';

	/** L'événement planifié qui vide la file. */
	const TACHE = 'aec_envoyer_courriels';

	/**
	 * Le délai de groupement. Quinze minutes : assez long pour qu'une
	 * salve de relecture tienne dans un seul envoi, assez court pour
	 * qu'une question posée le matin n'attende pas l'après-midi.
	 */
	const GRACE = 900;

	public static function init() {
		add_action( 'aec_fil_ouvert', array( __CLASS__, 'sur_fil' ), 10, 1 );
		add_action( 'aec_reponse_ajoutee', array( __CLASS__, 'sur_reponse' ), 10, 2 );
		add_action( self::TACHE, array( __CLASS__, 'vider' ), 10, 1 );

		// La case dans le profil, visible par l'intéressé et par un admin.
		add_action( 'show_user_profile', array( __CLASS__, 'champ_profil' ) );
		add_action( 'edit_user_profile', array( __CLASS__, 'champ_profil' ) );
		add_action( 'personal_options_update', array( __CLASS__, 'enregistrer_profil' ) );
		add_action( 'edit_user_profile_update', array( __CLASS__, 'enregistrer_profil' ) );
	}

	/* ---------------------------------------------------------------- */
	/* Qui reçoit quoi                                                   */
	/* ---------------------------------------------------------------- */

	/** Les comptes qui modèrent : l'équipe. */
	private static function equipe() {
		$ids = array();
		foreach ( get_users( array( 'fields' => array( 'ID' ) ) ) as $u ) {
			if ( user_can( $u->ID, AEC_Roles::CAP_MODERER ) ) {
				$ids[] = (int) $u->ID;
			}
		}

		return $ids;
	}

	/** Tous ceux qui ont parlé dans ce fil : l'auteur et les répondants. */
	private static function participants( $fil ) {
		$ids = array( (int) $fil->post_author );
		foreach ( AEC_Types::reponses( $fil->ID ) as $reponse ) {
			$ids[] = (int) $reponse->post_author;
		}

		return array_values( array_unique( $ids ) );
	}

	public static function sur_fil( $fil ) {
		// Une remarque neuve appelle l'équipe, pas celui qui l'écrit.
		self::empiler( self::equipe(), $fil, $fil, (int) $fil->post_author );
	}

	public static function sur_reponse( $reponse, $fil ) {
		$vers = array_merge( self::participants( $fil ), self::equipe() );
		self::empiler( $vers, $reponse, $fil, (int) $reponse->post_author );
	}

	/* ---------------------------------------------------------------- */
	/* La file                                                           */
	/* ---------------------------------------------------------------- */

	private static function empiler( $vers, $message, $fil, $auteur_id ) {
		foreach ( array_unique( array_map( 'intval', $vers ) ) as $id ) {
			// Jamais à soi-même, jamais à qui a demandé le silence.
			if ( ! $id || $id === (int) $auteur_id ) {
				continue;
			}
			if ( get_user_meta( $id, self::SILENCE, true ) ) {
				continue;
			}

			$file = get_user_meta( $id, self::FILE, true );
			$file = is_array( $file ) ? $file : array();
			$file[] = array(
				'fil'    => (int) $fil->ID,
				'texte'  => wp_strip_all_tags( $message->post_content ),
				'auteur' => get_the_author_meta( 'display_name', $auteur_id ),
				'post'   => (int) get_post_meta( $fil->ID, '_aec_post', true ),
				'url'    => (string) get_post_meta( $fil->ID, '_aec_url', true ),
				'quand'  => time(),
			);
			// On borne : une salve démesurée ne doit pas gonfler la méta.
			update_user_meta( $id, self::FILE, array_slice( $file, -60 ) );

			// Le premier message programme l'envoi ; les suivants s'y
			// ajoutent sans avancer ni reculer l'échéance.
			if ( ! wp_next_scheduled( self::TACHE, array( $id ) ) ) {
				wp_schedule_single_event( time() + self::GRACE, self::TACHE, array( $id ) );
			}
		}
	}

	/* ---------------------------------------------------------------- */
	/* L'envoi                                                           */
	/* ---------------------------------------------------------------- */

	public static function vider( $utilisateur_id ) {
		$utilisateur_id = (int) $utilisateur_id;
		$file = get_user_meta( $utilisateur_id, self::FILE, true );
		if ( ! is_array( $file ) || ! $file ) {
			return;
		}
		delete_user_meta( $utilisateur_id, self::FILE );

		$utilisateur = get_userdata( $utilisateur_id );
		if ( ! $utilisateur || ! is_email( $utilisateur->user_email ) ) {
			return;
		}

		$pages = array();
		foreach ( $file as $entree ) {
			$cle = $entree['post'] ?: $entree['url'];
			$pages[ $cle ][] = $entree;
		}

		$n     = count( $file );
		$sujet = sprintf(
			/* translators: 1: nombre de remarques, 2: nombre de pages */
			_n( '%1$d nouvelle remarque sur la refonte', '%1$d nouvelles remarques sur la refonte', $n, 'aec' ),
			$n
		);
		if ( count( $pages ) > 1 ) {
			$sujet .= sprintf( ' (%d pages)', count( $pages ) );
		}

		$lignes = array( sprintf( 'Bonjour %s,', $utilisateur->display_name ), '' );
		foreach ( $pages as $cle => $entrees ) {
			$post_id = is_numeric( $cle ) ? (int) $cle : 0;
			$titre   = $post_id ? get_the_title( $post_id ) : (string) $cle;
			$lien    = $post_id ? get_permalink( $post_id ) : home_url( (string) $cle );
			$lignes[] = sprintf( '## %s', $titre );
			foreach ( $entrees as $e ) {
				$texte = wp_trim_words( $e['texte'], 30, '…' );
				$lignes[] = sprintf( '  %s : « %s »', $e['auteur'], $texte );
				$lignes[] = sprintf( '  %s#aec-%d', $lien, $e['fil'] );
			}
			$lignes[] = '';
		}
		$lignes[] = 'Chaque lien ouvre la page directement sur la remarque.';
		$lignes[] = '';
		$lignes[] = sprintf(
			'Pour ne plus recevoir ces messages : %s (case « Relecture »).',
			admin_url( 'profile.php' )
		);

		wp_mail( $utilisateur->user_email, $sujet, implode( "\n", $lignes ) );
	}

	/* ---------------------------------------------------------------- */
	/* La case du profil                                                 */
	/* ---------------------------------------------------------------- */

	public static function champ_profil( $utilisateur ) {
		if ( ! user_can( $utilisateur->ID, AEC_Roles::CAP_COMMENTER ) ) {
			return;
		}
		$silence = (bool) get_user_meta( $utilisateur->ID, self::SILENCE, true );
		?>
		<h2>Relecture</h2>
		<table class="form-table" role="presentation">
			<tr>
				<th scope="row">Courriels</th>
				<td>
					<label>
						<input type="checkbox" name="aec_silence" value="1" <?php checked( $silence ); ?>>
						Ne pas me prévenir par courriel des nouvelles remarques et réponses
					</label>
					<p class="description">
						Les messages sont regroupés&nbsp;: au plus un courriel par quart d'heure,
						qui rassemble tout ce qui est arrivé entre-temps.
					</p>
				</td>
			</tr>
		</table>
		<?php
	}

	public static function enregistrer_profil( $utilisateur_id ) {
		if ( ! current_user_can( 'edit_user', $utilisateur_id ) ) {
			return;
		}
		if ( isset( $_POST['aec_silence'] ) ) {
			update_user_meta( $utilisateur_id, self::SILENCE, 1 );
		} else {
			delete_user_meta( $utilisateur_id, self::SILENCE );
		}
	}
}
