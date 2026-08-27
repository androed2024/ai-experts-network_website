# Nach dem Audit ausgeführte technische Korrekturen

Datum: 27. Juli 2026

Grundlage war der zuvor fertiggestellte Vorher-Bericht
[`clone-audit.md`](clone-audit.md). Es wurden keine Inhalte, Bilder,
Formulare oder Designs aktualisiert.

## 1. Kaputte relative Leistungslinks korrigiert

In sechs deutschen HTML-Dateien zeigten insgesamt 45 Linkvorkommen mit
`../../ki-.../index.html` aus dem Verzeichnis `/de/.../` versehentlich auf
sprachneutrale Root-Pfade. Diese Ziele lieferten im veröffentlichten Klon 404.

Die Referenzen wurden auf `../ki-.../index.html` geändert und zeigen damit auf
die vorhandenen Dateien unter `/de/`.

Geänderte Dateien:

- `ai-experts-clone/de/leistungen/index.html` — 5 Vorkommen
- `ai-experts-clone/de/ki-workshops-kompetenzaufbau/index.html` — 8 Vorkommen
- `ai-experts-clone/de/ki-strategieberatung-bedarfsanalyse/index.html` — 8 Vorkommen
- `ai-experts-clone/de/ki-executive-coaching-change/index.html` — 8 Vorkommen
- `ai-experts-clone/de/ki-umsetzung-automatisierung/index.html` — 8 Vorkommen
- `ai-experts-clone/de/ki-keynotes/index.html` — 8 Vorkommen

Vorher: 45 fehlerhafte `../../ki-...`-Referenzen.  
Nachher: 0.

## 2. Sprachneutrale Originalpfade als Redirects ergänzt

In `ai-experts-clone/nginx.conf` wurden 301-Weiterleitungen ergänzt:

- `/unser-ansatz/` → `/de/unser-ansatz/`
- `/ki-expertinnen/` → `/de/ki-expertinnen/`
- `/ki-workshops-kompetenzaufbau/` → `/de/ki-workshops-kompetenzaufbau/`
- `/ki-strategieberatung-bedarfsanalyse/` → `/de/ki-strategieberatung-bedarfsanalyse/`
- `/ki-executive-coaching-change/` → `/de/ki-executive-coaching-change/`
- `/ki-umsetzung-automatisierung/` → `/de/ki-umsetzung-automatisierung/`
- `/ki-keynotes/` → `/de/ki-keynotes/`

Damit bleibt das URL-Verhalten des Originals für die im Audit gefundenen
sprachneutralen Einstiege erhalten.

## Verifikation

- `docker compose config` konnte die Compose-/Nginx-Einbindung strukturell
  auflösen.
- Der Zugriff auf den lokalen Docker-Daemon wurde von der
  Ausführungsumgebung nicht freigegeben; ein laufender Container konnte daher
  nicht neu geladen oder per HTTP geprüft werden.
- Eine statische Nachprüfung aller `<a href>`-Ziele im lokalen Klon ergab:
  - 1512 lokale Linkvorkommen: Ziel vorhanden
  - 90 externe Linkvorkommen
  - 0 fehlende lokale Linkziele
  - 0 direkte `<a>`-Links zur Originaldomain
- Die maschinenlesbare Nachprüfung steht in
  [`post-fix-link-check.csv`](post-fix-link-check.csv).

## Bewusst nicht geändert

- Keine Aktualisierung der abweichenden Texte oder Profile.
- Keine Design- oder Layoutänderung.
- Keine Formularumstellung; hierfür muss zuerst ein dauerhaftes Ziel
  (serverloser Endpoint, externer Dienst oder `mailto:`-Fallback) festgelegt
  werden.
- Keine Entfernung der WordPress-/Originaldomain-Laufzeitkonfiguration.
- Keine Änderung von Canonical oder Hreflang, da diese beim finalen
  Domain-Cutover bewusst auf die Zieldomain abgestimmt werden müssen.
- Keine Deployment- oder Produktionsänderung.

Die Go/No-Go-Einschätzung des Vorher-Berichts bleibt trotz der Linkkorrekturen
**NO-GO**, bis Inhalte und Formularfunktion aktualisiert wurden.

## Ergänzung vom 7. August 2026

Die 14 tatsächlich kritisch abweichenden Inhaltsseiten wurden anschließend aus
dem archivierten Originalstand aktualisiert. Einzelheiten und Validierung stehen
in [`content-update.md`](content-update.md).

Zusätzlich wurden eine Hostinger-kompatible `.htaccess` und Upload-Hinweise
ergänzt. Die Formularfunktion bleibt als letzter kritischer Funktionspunkt
offen. Für deren Umstellung wird noch die gewünschte Empfängeradresse oder der
gewünschte Formulardienst benötigt.

## Ergänzung vom 26. August 2026: Kontaktformulare entkoppelt

Die Formularübermittlung auf den deutschen und englischen Kontaktseiten wurde
von der nicht mehr vorhandenen WordPress-/Contact-Form-7-API entkoppelt.

Umgesetzt wurden:

- ein lokaler PHP-Endpunkt `ai-experts-clone/contact-submit.php`;
- Versand aller vom Besucher ausgefüllten Formularfelder an
  `info@ai-experts.network`;
- Betreff `Neue Kontakt - Message von <NAME>` mit dem eingegebenen Namen;
- `Reply-To` mit der Absenderadresse des Besuchers, damit direkt geantwortet
  werden kann;
- strukturierter Textinhalt einschließlich Anfrageart, Mitglied, Name,
  E-Mail, Unternehmen, Nachricht und ausgewählten Fragebogenantworten;
- deutsche und englische Erfolgs-, Validierungs- und Fehlermeldungen;
- serverseitige Eingabeprüfung, Schutz gegen Mail-Header-Injection,
  Same-Origin-Prüfung sowie ein unsichtbares Bot-Feld mit Zeitprüfung;
- Anbindung aller drei vorhandenen Contact-Form-7-Formulare je Sprachseite,
  einschließlich der zwei Pop-up-Formulare.

Geänderte bzw. neue Dateien:

- `ai-experts-clone/de/kontakt/index.html`
- `ai-experts-clone/en/kontakt/index.html`
- `ai-experts-clone/assets/js/contact-form-mail.js`
- `ai-experts-clone/contact-submit.php`

Es wurden keine Passwörter oder SMTP-Zugangsdaten in den öffentlich
ausgelieferten Website-Code geschrieben. Der Versand nutzt die PHP-Mailfunktion
des Hostinger-Webhostings mit `info@ai-experts.network` als lokalem Absender.

Verifikation vor dem Deployment:

- JavaScript-Syntaxprüfung mit Node.js erfolgreich;
- Git-Whitespace-Prüfung erfolgreich;
- beide Sprachseiten laden das neue Formularskript;
- serverseitige PHP-Ausführung und tatsächliche Mailzustellung können erst auf
  dem Hostinger-Webspace abschließend geprüft werden, da lokal keine
  PHP-Laufzeit verfügbar ist.

Nach dem Upload ist eine echte Testanfrage je Sprache erforderlich. Dabei sind
Posteingang und gegebenenfalls Spam-Ordner von `info@ai-experts.network` zu
prüfen.

## Ergänzung vom 26. August 2026: Umami-Webanalyse

Der Tracking-Code der Umami-Instanz `analytics.11mind.com` wurde in den
`<head>`-Bereich sämtlicher 58 HTML-Dateien des Klons aufgenommen.

- Website-ID: `72c31409-526b-417d-b6f3-1d2325db9700`
- erfasste Domain: `ai-experts.network`
- Skript wird mit `defer` geladen und blockiert daher nicht das initiale
  Parsen der Seite;
- jede HTML-Datei enthält den Tracking-Code genau einmal.

Die statische Nachprüfung bestätigte 58 von 58 Seiten mit jeweils genau einem
Tracking-Skript innerhalb von `<head>...</head>`. Die Erfassung realer
Seitenaufrufe ist nach dem Upload im Umami-Dashboard zu kontrollieren.

## Ergänzung vom 27. August 2026: Produktionspfad korrigiert

Beim ersten Entpacken in Hostinger wurden die neuen Dateien versehentlich unter
`public_html/public_html/` abgelegt. Die Domain lieferte dadurch weiterhin den
alten Stand aus dem äußeren `public_html` aus. Das alte Contact-Form-7-Skript
versuchte weiterhin die nicht vorhandene WordPress-API aufzurufen; deshalb
blieb das Formular beim Absenden hängen.

Die elf Inhalte des inneren Verzeichnisses wurden anschließend in das äußere,
produktive `public_html` kopiert. Acht Namenskonflikte wurden bewusst durch die
neue Version ersetzt. Der innere Ordner wurde zur Sicherheit zunächst nicht
gelöscht.

Live-Verifikation:

- die deutsche Kontaktseite lädt jetzt `/assets/js/contact-form-mail.js`;
- das Umami-Skript wird ausgeliefert;
- `/contact-submit.php` antwortet über Hostinger PHP 8.3.30;
- ein GET-Aufruf liefert erwartungsgemäß HTTP 405 mit JSON;
- eine absichtlich ungültige POST-Anfrage liefert erwartungsgemäß HTTP 422 und
  löst keine E-Mail aus.

Die tatsächliche E-Mail-Zustellung wurde am 27. August 2026 mit einer echten
deutschen Formularanfrage erfolgreich bestätigt. Die Nachricht traf mit dem
gewünschten Betreff und den strukturierten Formulardaten bei
`info@ai-experts.network` ein.
