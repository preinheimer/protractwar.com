<?php
/*
 * Classic hit counter, shown in the footer of index.html as <img src="counter.php">.
 *
 * Each hit appends one byte to the hits file, and the file's size is the count. Appends (O_APPEND) are atomic on a
 * local filesystem, so simultaneous hits never overwrite each other and no locking is needed. Two visitors at the
 * same instant may be shown the same number; neither hit is lost.
 *
 * The file is data/hits at the project root, outside the docroot so it isn't served, and ignored by git so a
 * deploy never resets it (see README). To start from a number: head -c 12345 /dev/zero > data/hits
 */
declare(strict_types=1);

const DIGITS = 6;    // pad to at least this many digits, odometer-style

// override with SetEnv PROTRACTWAR_HITS_FILE (Apache) or the environment (local testing)
$file = $_SERVER['PROTRACTWAR_HITS_FILE'] ?? (getenv('PROTRACTWAR_HITS_FILE') ?: dirname(__DIR__) . '/data/hits');

$count = null;
$fh = @fopen($file, 'ab');
if ($fh !== false) {
    if (@fwrite($fh, '1') === 1 && fflush($fh)) {
        $count = fstat($fh)['size'];    // includes our byte, and any that landed just before it
    }
    fclose($fh);
}
if ($count === null) {
    error_log("protractwar counter: can't append to $file");
}

$text = $count === null ? str_repeat('-', DIGITS) : str_pad((string) $count, DIGITS, '0', STR_PAD_LEFT);

// odometer: white digits on dark drums, shaded top and bottom so they look rounded
$cw = 18; $ch = 26; $gap = 2; $pad = 3;
$w = $pad * 2 + strlen($text) * ($cw + $gap) - $gap;
$h = $ch + $pad * 2;
$cells = '';
foreach (str_split($text) as $i => $digit) {
    $x = $pad + $i * ($cw + $gap);
    $cells .= sprintf(
        '<rect x="%d" y="%d" width="%d" height="%d" rx="2" fill="url(#drum)"/>'
        . '<text x="%.1f" y="%.1f" font-size="19" font-weight="700" fill="#fff" text-anchor="middle" '
        . 'font-family="Helvetica, Arial, sans-serif">%s</text>',
        $x, $pad, $cw, $ch, $x + $cw / 2, $pad + $ch / 2 + 6.8, $digit
    );
}

header('Content-Type: image/svg+xml; charset=utf-8');
header('Cache-Control: no-store, max-age=0');    // every page view fetches it again, reloads included
header('Expires: 0');
echo <<<SVG
<svg xmlns="http://www.w3.org/2000/svg" width="$w" height="$h" viewBox="0 0 $w $h">
<defs><linearGradient id="drum" x1="0" y1="0" x2="0" y2="1">
<stop offset="0" stop-color="#05080b"/><stop offset=".22" stop-color="#2e3640"/><stop offset=".5" stop-color="#3a434e"/>
<stop offset=".78" stop-color="#2e3640"/><stop offset="1" stop-color="#05080b"/></linearGradient></defs>
<rect width="$w" height="$h" rx="4" fill="#1d232b"/>$cells
</svg>
SVG;
