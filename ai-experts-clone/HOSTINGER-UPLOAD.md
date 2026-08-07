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

## Nach dem Upload prüfen

1. `https://ai-experts.network/de/`
2. `https://ai-experts.network/en/`
3. `https://ai-experts.network/kontakt/`
4. Sprachumschalter DE/EN
5. Alle sieben Redirect-Pfade aus `.htaccess`
6. Bilder, Fonts und Navigation auf Desktop und Mobilgeräten
7. Canonical- und Hreflang-Tags

## Noch offen: Kontaktformular

Die sichtbaren Contact-Form-7-Formulare stammen aus WordPress. Ihre
JavaScript-Konfiguration verwendet weiterhin die WordPress-REST-API des
Originalsystems. Wenn dieses WordPress abgeschaltet wird, können die statischen
Formulare keine Nachrichten mehr übermitteln.

Vor der endgültigen Umschaltung muss deshalb entweder:

- ein neuer Formular-Endpunkt eingerichtet werden,
- ein externer Formulardienst eingebunden werden oder
- ein `mailto:`-Fallback mit der gewünschten Empfängeradresse eingesetzt werden.

Die Empfängeradresse beziehungsweise der gewünschte Formulardienst ist im
Projekt noch nicht festgelegt.

