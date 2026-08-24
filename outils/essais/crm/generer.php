<?php
/**
 * Rend l'écran réel du plugin hors de WordPress, avec des doublures
 * pour les quelques fonctions du cœur qu'il appelle. Le HTML testé est
 * donc celui que la cliente verra, pas une copie faite à la main.
 */
define( 'ABSPATH', __DIR__ );
define( 'HOUR_IN_SECONDS', 3600 );

$JEU = json_decode( file_get_contents( __DIR__ . '/jeu.json' ), true );

function get_posts( $a ) {
	global $JEU;
	$sortie = array();
	foreach ( $JEU as $f ) {
		$sortie[] = (object) array( 'ID' => $f['id'], 'post_title' => $f['titre'] );
	}
	return $sortie;
}
function get_post_meta( $id, $cle, $u = false ) {
	global $JEU;
	foreach ( $JEU as $f ) {
		if ( $f['id'] != $id ) { continue; }
		$carte = array(
			'_abo_champs' => $f['champs'], '_abo_journal' => $f['journal'],
			'_abo_statut' => $f['statut'], '_abo_formulaire' => $f['formulaire'],
			'_abo_courriel' => $f['courriel'], '_abo_page' => $f['page'], '_abo_image' => 0,
		);
		return isset( $carte[ $cle ] ) ? $carte[ $cle ] : '';
	}
	return '';
}
function get_the_date( $f, $p ) { global $JEU; foreach ( $JEU as $x ) { if ( $x['id'] == $p->ID ) return $x['date']; } return ''; }
function get_post_time( $f, $g, $p ) { return $p->ID; }
function human_time_diff( $u ) { global $JEU; foreach ( $JEU as $x ) { if ( $x['id'] == $u ) return $x['depuis']; } return ''; }
function wp_nonce_url( $u, $a ) { return '#'; }
function admin_url( $c = '' ) { return '/wp-admin/' . $c; }
function get_option( $c, $d = false ) { return 0; }
function esc_attr( $v ) { return htmlspecialchars( (string) $v, ENT_QUOTES, 'UTF-8' ); }
function esc_html( $v ) { return htmlspecialchars( (string) $v, ENT_QUOTES, 'UTF-8' ); }
function esc_url( $v ) { return $v; }
function wp_json_encode( $v ) { return json_encode( $v, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES ); }
function wp_trim_words( $t, $n, $plus ) {
	$m = preg_split( '/\s+/u', trim( (string) $t ), -1, PREG_SPLIT_NO_EMPTY );
	return count( $m ) <= $n ? implode( ' ', $m ) : implode( ' ', array_slice( $m, 0, $n ) ) . $plus;
}
function add_action() {} function wp_next_scheduled() { return true; } function wp_schedule_event() {}

require __DIR__ . '/../../../plugin/ae-back-office/includes/class-abo-demandes.php';

ob_start();
ABO_Demandes::ecran();
$corps = ob_get_clean();

$page = '<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8">'
. '<link rel="stylesheet" href="admin.css">'
. '<style>body{font-family:-apple-system,system-ui,sans-serif;background:#f0f0f1;margin:0}'
. '.wrap{padding:20px 24px}h1{font-size:23px;font-weight:400;margin:0 0 12px}'
. 'hr.wp-header-end{display:none}.notice{display:none}'
. '.button{display:inline-block;padding:6px 12px;border:1px solid #2271b1;border-radius:3px;'
. 'background:#f6f7f7;color:#2271b1;text-decoration:none;font-size:13px;cursor:pointer}'
. '.button-primary{background:#2271b1;color:#fff;border-color:#2271b1}'
. 'textarea,select{font-family:inherit}.description{color:#646970;font-size:13px}</style></head><body>'
. $corps
. '<script>window.ABO_DEMANDES={ajax:"/ajax",nonce:"n",statuts:'
. json_encode( ABO_Demandes::STATUTS, JSON_UNESCAPED_UNICODE ) . '};'
. 'window.__appels=[];'
. 'window.fetch=function(u,o){var b=new URLSearchParams(o.body);'
. 'window.__appels.push(b.get("action")+":"+b.get("demande")+"→"+(b.get("statut")||b.get("message")));'
. 'return Promise.resolve({json:function(){return Promise.resolve({success:true,'
. 'data:{auteur:"Rémi",message:b.get("message")||"",date:"maintenant"}});}});};'
. '</script><script src="demandes.js"></script></body></html>';

file_put_contents( __DIR__ . '/index.html', $page );
echo "index.html régénéré depuis le plugin (" . strlen( $page ) . " octets)\n";
