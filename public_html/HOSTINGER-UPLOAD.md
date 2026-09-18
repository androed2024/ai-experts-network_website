# Upload zu Hostinger

Dieser Ordner ist als statische Website vorbereitet.

## Was hochgeladen wird

Den **Inhalt** dieses Ordners in den `public_html`-Ordner der Domain hochladen,
nicht den übergeordneten Projektordner und nicht den Ordner `reports`.

Wichtig: Die versteckte Datei `.htaccess` muss ebenfalls hochgeladen werden.
Sie enthält die Weiterleitungen für die sprachneutralen URLs des Originals.

Hostinger empfiehlt, Website-Dateien im `public_html`-Ordner der jeweiligen
Domain abzulegen. Am einfachsten kann der Inhalt als ZIP-Datei hochgeladen und
direkt in `public_html` entpackt werden.

Wichtig beim Entpacken im Hostinger-Dateimanager: Wenn der Dateimanager bereits
den Pfad `.../ai-experts.network/public_html/` anzeigt, muss als Ziel der
**aktuelle Ordner** (`.`) gewählt werden. Nicht erneut `public_html` als
Unterordner anlegen oder auswählen. Andernfalls landen die Dateien fälschlich
unter `public_html/public_html/` und werden von der Domain nicht ausgeliefert.

## Nach dem Upload prüfen

1. `https://ai-experts.network/de/`
2. `https://ai-experts.network/en/`
3. `https://ai-experts.network/kontakt/`
4. Sprachumschalter DE/EN
5. Alle sieben Redirect-Pfade aus `.htaccess`
6. Bilder, Fonts und Navigation auf Desktop und Mobilgeräten
7. Canonical- und Hreflang-Tags

## Kontaktformular

Das deutsche und englische Kontaktformular verwenden den lokalen PHP-Endpunkt
`/contact-submit.php`. Dieser muss direkt im produktiven `public_html` liegen.
Das zugehörige Browserskript befindet sich unter
`/assets/js/contact-form-mail.js`. Nachrichten werden an
`info@ai-experts.network` gesendet.

Nach jedem Deployment sind mindestens folgende Prüfungen erforderlich:

1. `https://ai-experts.network/contact-submit.php` liefert bei einem normalen
   Browseraufruf JSON mit HTTP-Status 405 statt einer 404-Seite.
2. Der Quelltext der Kontaktseite lädt `/assets/js/contact-form-mail.js`.
3. Eine echte Testnachricht wird über DE und EN versendet.
