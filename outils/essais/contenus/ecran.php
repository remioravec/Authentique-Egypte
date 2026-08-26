<?php
/** Rend le vrai écran Contenus hors de WordPress. */
define( 'ABSPATH', __DIR__ );
$PAGES = json_decode( file_get_contents( __DIR__ . '/pages.json' ), true );
$PAR_ID = array(); $PAR_SLUG = array();
foreach ( $PAGES as $p ) { $PAR_ID[ $p['ID'] ] = $p; $PAR_SLUG[ $p['post_name'] ] = $p; }
$_GET = array();

function get_page_by_path( $c ) { global $PAR_SLUG; return isset( $PAR_SLUG[ $c ] ) ? (object) $PAR_SLUG[ $c ] : null; }
function get_post_ancestors( $id ) {
	global $PAR_ID; $out = array(); $vu = array();
	while ( isset( $PAR_ID[ $id ] ) && $PAR_ID[ $id ]['post_parent'] && ! isset( $vu[ $id ] ) ) {
		$vu[ $id ] = 1; $id = $PAR_ID[ $id ]['post_parent']; $out[] = $id;
	}
	return $out;
}
function get_option( $c, $d = false ) { return $c === 'page_on_front' ? 38 : ( $c === 'page_for_posts' ? 2368 : $d ); }
function get_post_meta() { return ''; } function update_post_meta() {}
function post_type_exists( $t ) { return $t === 'programs'; }
function add_action() {} function add_filter() {}
function apply_filters( $h, $v ) { return $v; } function do_action() {}
function wp_kses_post( $v ) { return $v; } function number_format_i18n( $n ) { return $n; }
function get_posts( $a = array() ) {
	global $PAGES;
	$out = array();
	foreach ( $PAGES as $p ) {
		$p['post_title'] = $p['titre']; $p['post_status'] = $p['statut'];
		$out[] = (object) $p;
	}
	usort( $out, function ( $x, $y ) { return strcasecmp( $x->post_title, $y->post_title ); } );
	return $out;
}
function get_post_type_object( $t ) {
	return (object) array( 'labels' => (object) array( 'singular_name' => $t === 'post' ? 'Guide' : ( $t === 'programs' ? 'Voyage' : 'Page' ) ) );
}
function get_edit_post_link( $id ) { return '/wp-admin/post.php?post=' . $id . '&action=edit'; }
function get_permalink( $id ) { return 'https://authentiquegypte.com/?page_id=' . $id; }
function get_the_modified_date( $f, $p ) { return '24 août 2026'; }
function admin_url( $c = '' ) { return '/wp-admin/' . $c; }
function add_query_arg( $a, $u = '' ) { return $u . '?' . http_build_query( array_filter( $a, 'strlen' ) ); }
function esc_url( $v ) { return htmlspecialchars( (string) $v, ENT_QUOTES, 'UTF-8' ); }
function esc_attr( $v ) { return htmlspecialchars( (string) $v, ENT_QUOTES, 'UTF-8' ); }
function esc_html( $v ) { return htmlspecialchars( (string) $v, ENT_QUOTES, 'UTF-8' ); }
function esc_textarea( $v ) { return esc_html( $v ); }
function sanitize_text_field( $v ) { return $v; } function sanitize_key( $v ) { return $v; }
function wp_unslash( $v ) { return $v; } function wp_nonce_field() {}
function selected( $a, $b ) { echo $a === $b ? ' selected' : ''; }
function submit_button() {} function wp_enqueue_style() {} function register_setting() {}
function add_menu_page() {} function add_submenu_page() {} function current_user_can() { return true; }

require __DIR__ . '/../../../plugin/ae-back-office/includes/class-abo-gabarits.php';
require __DIR__ . '/../../../plugin/ae-back-office/includes/class-abo-contenus.php';

ob_start(); ABO_Contenus::ecran(); $corps = ob_get_clean();
$css = file_get_contents( __DIR__ . '/../../../plugin/ae-back-office/assets/css/admin.css' );
file_put_contents( __DIR__ . '/ecran.html',
 '<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8"><style>'
 . 'body{background:#f0f0f1;margin:0;font-family:-apple-system,"Segoe UI",Roboto,sans-serif;font-size:13px}'
 . '.wrap{margin:10px 20px;padding:16px 22px}h1{font-size:23px;font-weight:400}'
 . 'hr.wp-header-end{display:none}.page-title-action{display:inline-block;padding:5px 10px;border:1px solid #2271b1;border-radius:3px;color:#2271b1;text-decoration:none;margin-left:6px}'
 . '.widefat{width:100%;border-collapse:collapse;background:#fff;border:1px solid #c3c4c7}'
 . '.widefat th,.widefat td{padding:9px 12px;text-align:left;border-bottom:1px solid #f0f0f1}'
 . '.striped tbody tr:nth-child(odd){background:#f6f7f7}.button{padding:5px 11px;border:1px solid #2271b1;border-radius:3px;color:#2271b1;background:#f6f7f7}'
 . $css . '</style></head><body>' . $corps . '</body></html>' );
echo "ecran.html écrit (" . strlen( $corps ) . " octets de corps)\n";
