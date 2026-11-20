# protractwar.com

Static promo site for Protractwar.

## Layout

- `docroot/` — public web root (served by Apache). Generated; don't hand-edit `index.html`.
- `bin/` — Python build scripts.
- `src/` — rules and maps HTML and the PDFs printed from them.
- `noweb/apache/protractwar.com.conf` — Apache vhost.

## Building

Run the scripts from any directory:

```sh
python3 bin/build_protractwar.py   # -> src/protractwar.html
python3 bin/build_maps.py          # -> src/protractwar_maps.html
# print both to src/Protractwar.pdf and src/Protractwar_Maps.pdf with headless Chrome
python3 bin/build_site.py          # -> docroot/index.html + docroot/*.pdf
```

## Deploying

Copy the project to `/var/www/protractwar.com`, then:

```sh
ln -s /var/www/protractwar.com/noweb/apache/protractwar.com.conf /etc/apache2/sites-available/protractwar.com.conf
a2enmod ssl rewrite headers expires deflate
a2ensite protractwar.com
apachectl configtest && systemctl reload apache2
```
