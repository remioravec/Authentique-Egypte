<?php
/** Fait tourner le vrai classifieur du plugin sur les vraies pages. */
define( 'ABSPATH', __DIR__ );
$PAGES = json_decode( file_get_contents( __DIR__ . '/pages.json' ), true );
$PAR_ID = array(); $PAR_SLUG = array();
foreach ( $PAGES as $p ) { $PAR_ID[ $p['ID'] ] = $p; $PAR_SLUG[ $p['post_name'] ] = $p; }

function get_page_by_path( $chemin ) {
	global $PAR_SLUG;
	return isset( $PAR_SLUG[ $chemin ] ) ? (object) $PAR_SLUG[ $chemin ] : null;
}
function get_post_ancestors( $id ) {
	global $PAR_ID;
	$out = array(); $vu = array();
	while ( isset( $PAR_ID[ $id ] ) && $PAR_ID[ $id ]['post_parent'] && ! isset( $vu[ $id ] ) ) {
		$vu[ $id ] = 1; $id = $PAR_ID[ $id ]['post_parent']; $out[] = $id;
	}
	return $out;
}
function get_option( $c, $d = false ) { return $c === 'page_on_front' ? 38 : ( $c === 'page_for_posts' ? 2368 : $d ); }
function get_post_meta( $id, $c, $u = false ) { return ''; }
function update_post_meta() {} function post_type_exists( $t ) { return $t === 'programs'; }
function add_action() {} function add_filter() {} function get_posts() { return array(); }

require __DIR__ . '/../../../plugin/ae-back-office/includes/class-abo-gabarits.php';

$compte = array(); $detail = array();
foreach ( $PAGES as $p ) {
	$post = (object) $p;
	$zone = ABO_Gabarits::zone( $post );
	$gab  = ABO_Gabarits::deduire( $post );
	$cle  = $zone . ' / ' . $gab;
	$compte[ $cle ] = ( $compte[ $cle ] ?? 0 ) + 1;
	$detail[ $cle ][] = $p['post_name'];
}
ksort( $compte );
foreach ( $compte as $cle => $n ) {
	printf( "  %-26s %3d\n", $cle, $n );
	if ( strpos( $cle, 'autre' ) !== false || strpos( $cle, 'maquette' ) !== false ) {
		foreach ( array_slice( $detail[ $cle ], 0, 8 ) as $s ) { echo "        · $s\n"; }
	}
}
