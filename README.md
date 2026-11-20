# protractwar.com

Static promo site for Protractwar.

## Layout

- `docroot/` — public web root (served by Apache). Generated; don't hand-edit `index.html`.
- `bin/` — Python build scripts.
- `src/` — generated rules and maps HTML/PDFs (Letter, A4, and dyslexia-friendly versions of each), and the OpenDyslexic font.
- `noweb/apache/protractwar.com.conf` — Apache vhost.

## Building

Run the scripts from any directory:

```sh
python3 bin/build_protractwar.py   # -> src/protractwar-rules*.html
python3 bin/build_maps.py          # -> src/protractwar-maps*.html
python3 bin/build_protractor.py    # -> src/protractwar-protractor*.html (cut-out protractors, Letter + A4)
python3 bin/build_pdfs.py          # -> src/*.pdf via headless Chrome (set CHROME=... if needed); checks page counts
python3 bin/build_site.py          # -> docroot/index.html + docroot/*.pdf
python3 bin/build_play.py          # -> docroot/play.html (from src/play.template.html)
```

Each document is built in four variants: Letter, A4 (`-a4`), and dyslexia-friendly (`-dyslexic`, set in
OpenDyslexic, SIL OFL — see `src/fonts/opendyslexic/LICENSE`) in both sizes. The dyslexic rules are three pages
instead of two, because OpenDyslexic is much wider. The site's Letter/A4 toggle picks a default from the browser
locale and remembers the visitor's choice.

`docroot/play.html` is an online two-player (same device) version of the game. It isn't linked from the main page
and carries `noindex`. `bin/build_play.py` embeds the printed map's blob geometry so its "Printed map" matches the
PDF; the page can also generate random maps.

## Hit counter

The footer shows a classic odometer hit counter: `<img src="counter.php">`, no JavaScript. `docroot/counter.php`
appends one byte to `data/hits` per hit, and the file's size is the count. Appends are atomic, so no locking is
needed. `data/` sits outside the docroot (not served) and git ignores its contents, so deploys never reset the count.
It needs mod_php (`apt install libapache2-mod-php`); the vhost only lets PHP run for `counter.php`, and refuses it
outright if PHP isn't loaded. One-time setup on the server:

```sh
cd /var/www/protractwar.com
touch data/hits && sudo chown www-data data/hits
# optional: start from a number instead of 0
head -c 12345 /dev/zero | sudo -u www-data tee data/hits > /dev/null
```

Only the file needs to be writable by Apache, not the directory. If it can't be written the counter shows dashes
and logs to Apache's error log.

## Deploying

Copy the project to `/var/www/protractwar.com`, then:

```sh
ln -s /var/www/protractwar.com/noweb/apache/protractwar.com.conf /etc/apache2/sites-available/protractwar.com.conf
a2enmod ssl rewrite headers expires deflate
a2ensite protractwar.com
apachectl configtest && systemctl reload apache2
```

The site is now live over plain HTTP. The HTTPS vhosts are skipped until the cert exists.
Get the cert, then reload. Apache turns on HTTPS and HTTP starts redirecting:

```sh
certbot certonly --webroot -w /var/www/protractwar.com/docroot \
  -d protractwar.com -d www.protractwar.com \
  --deploy-hook "systemctl reload apache2"
systemctl reload apache2
```
