# Aktualisierung der kritischen Inhalte

Datum: 7. August 2026

Quelle war das beim Audit am 27. Juli 2026 gesicherte Original-HTML unter
`reports/original-archive/html/`.

## Aktualisierte Seiten

- `/de/faq/`
- `/de/team/andreas-rodenbeck/`
- `/de/team/kristin-goas-oses/`
- `/de/team/mario-levenhagen/`
- `/de/team/meike-quentin/`
- `/de/team/rene-goebels/`
- `/de/team/stephan-grandy/`
- `/en/faq/`
- `/en/leistungen/`
- `/en/team/kristin-goas-oses/`
- `/en/team/mario-levenhagen/`
- `/en/team/meike-quentin/`
- `/en/team/rene-goebels/`
- `/en/team/stephan-grandy/`

Auf jeder Seite wurde ausschließlich der `<main>`-Bereich durch den
archivierten Originalstand ersetzt. Asset- und Seitenlinks wurden auf lokale
Dateien umgeschrieben. Header, Footer, Seitendesign und globale Skripte blieben
erhalten.

## Zusätzlich ausgeführte technische Korrekturen

- `.htaccess` für Hostinger mit den sieben sprachneutralen 301-Redirects
  ergänzt.
- Den ungeschützten Aufruf `cmplzScriptLoaded()` in 54 statischen HTML-Dateien
  abgesichert, damit die Seiten ohne das ursprüngliche WordPress-Complianz-
  Laufzeitsystem keinen JavaScript-Fehler auslösen.
- Das vorhandene AI-Experts-SVG als `/favicon.svg` bereitgestellt und in allen
  58 HTML-Dateien referenziert; der zuvor beobachtete Favicon-404 entfällt.
- Upload-Hinweise in `ai-experts-clone/HOSTINGER-UPLOAD.md` ergänzt.

## Verifikation

- Haupttext aller 14 aktualisierten Seiten entspricht normalisiert exakt dem
  archivierten Originalstand.
- Keine aktualisierte Hauptsektion verweist auf `ai-experts.network`.
- Keine fehlenden lokalen Bilder, Fonts, CSS- oder JavaScript-Dateien.
- 1512 lokale Linkvorkommen zeigen auf vorhandene Dateien.
- 0 fehlende lokale Linkziele.
- 0 direkte HTML-Links zur Originaldomain.
- Lokale Browserprüfung von `/de/faq/`, `/en/leistungen/` und
  `/de/team/mario-levenhagen/` erfolgreich; keine kaputten Bilder.
- Nach Absicherung des Complianz-Aufrufs entstand beim erneuten Laden kein
  neuer entsprechender Browserfehler.

Maschinenlesbare Details:

- `reports/critical-content-update.json`
- `reports/post-fix-link-check.csv`
- `reports/local-asset-check.csv`

## Weiterhin offen

Die Contact-Form-7-Formulare sind visuell vorhanden, aber weiterhin von der
WordPress-REST-API des Originals abhängig. Für eine dauerhafte Lösung werden
eine Empfängeradresse und die Entscheidung zwischen neuem Backend, externem
Formulardienst oder `mailto:` benötigt.
