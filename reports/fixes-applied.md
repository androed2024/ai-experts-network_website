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
