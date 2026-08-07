# Audit des statischen Klons von ai-experts.network

Audit-Datum: 27. Juli 2026  
Original: <https://ai-experts.network>  
Klon: <https://ai-experts.11mind.com>  
Bewerteter Zustand: vor technischen Korrekturen

## Executive Summary

**Gesamturteil: NO-GO für den unmittelbaren Domainumzug.**

Der Klon ist technisch erreichbar und enthält den größten Teil der im April 2026
gesicherten Struktur. Er bildet den aktuellen Stand des Originals vom
27. Juli 2026 jedoch nicht vollständig ab. Besonders problematisch sind sieben
fehlende sprachneutrale Original-URLs, 45 kaputte Linkvorkommen zu fünf dieser
Ziele, erhebliche Inhaltsabweichungen auf FAQ-, Team- und einzelnen
Leistungsseiten sowie die weiterhin bestehende Abhängigkeit der
Kontaktformulare vom WordPress-REST-Backend des Originals.

Positiv: Für die lokalen HTML-/CSS-Dateireferenzen wurden keine fehlenden
Dateien gefunden. Alle aktiv referenzierten CSS- und JavaScript-Dateien sowie
lokalen Fonts sind vorhanden und über den Klon mit HTTP 200 erreichbar.
2115 seitenbezogene Asset-Vorkommen sind byte-identisch, 19 eindeutige
Originalbilder haben im Klon eine gleich dimensionierte lokale Entsprechung.

## Kennzahlen

| Kennzahl | Ergebnis |
|---|---:|
| Erfasste Originalseiten | 63 |
| Erfasste Klonseiten im Link-Crawl | 66, davon 5 mit HTTP 404 |
| Gemappte Originalpfade | 63 |
| Fehlende/404-Originalpfade im Klon | **7** |
| Kaputte interne Linkvorkommen im Klon | **45** |
| Eindeutige kaputte Linkziele im Klon | **5** |
| Kritische Textvergleiche | **23** |
| Mittlere Textvergleiche | **39** |
| Niedrige Textvergleiche | 1 |
| Eindeutig fehlende aktive Original-Assets | 2 Flaggenbilder |
| Kaputte lokale HTML-/CSS-Assetpfade | 0 |
| Kaputte geladene Bilder/CSS/JS | 0 |
| Vollständige Desktop-Bildpaare | 63 von 63 |
| Tablet-Bildpaare | 51 von 63 |
| Mobile-Bildpaare | 20 von 63 |
| Erzeugte Pixel-Diffs | 132 |
| Visuell kritisch (alle auswertbaren Viewports) | 29 |
| Visuell mittel (alle auswertbaren Viewports) | 27 |

Die Tablet-/Mobile-Lücken entstanden, nachdem weitere Browsernavigation zu
beiden Domains durch die Browser-Sicherheitsrichtlinie blockiert wurde.
Desktop ist vollständig. Die HTTP-, Struktur-, Text-, Link- und Assetdaten sind
von dieser Einschränkung nicht betroffen.

## Methode und Archiv

- Startpunkte: `/de/`, `/en/` und zusätzlich der ausdrücklich geforderte
  sprachneutrale Pfad `/kontakt/` auf beiden Domains.
- Interne Links wurden bis zu einem Sicherheitslimit von 200 Seiten verfolgt.
- Erfasst wurden HTTP-Status, Weiterleitungen, Titel, Meta Description,
  H1/H2, Canonical, Hreflang, Navigation, Footer, Formulare, interne und externe
  Links, Bilder und weitere Assets.
- Sichtbarer Text wurde mit Unicode NFKC, Whitespace-Kollaps und Entfernung
  unsichtbarer Zeichen normalisiert. Kurze Cookie-/Tracking-Texte wurden aus
  dem Inhaltsvergleich entfernt.
- Assets wurden nach Status, Content-Type, Dateigröße, Bildmaßen und SHA-256
  verglichen. Abweichend benannte, aber gleich dimensionierte lokale Bilder
  wurden als äquivalent erkannt.
- Das Original-HTML wurde unter
  [`original-archive/html/`](original-archive/html/) in seiner Pfadstruktur
  archiviert. Vollständige Seitendaten und Asset-Hashes stehen in
  [`original-pages.json`](original-pages.json).
- Screenshots wurden mit 1440×1200, 768×1200 und 390×1200 erstellt. Vorhandene
  Paare wurden pixelweise verglichen.

## URL-Mapping

Die vollständige Tabelle steht in
[`url-comparison.csv`](url-comparison.csv).

### Fehlende oder falsche Originalpfade

| Originalpfad | Klonstatus | Bewertung |
|---|---:|---|
| `/unser-ansatz/` | 404 | kritisch |
| `/ki-expertinnen/` | 404 | kritisch |
| `/ki-workshops-kompetenzaufbau/` | 404 | kritisch |
| `/ki-strategieberatung-bedarfsanalyse/` | 404 | kritisch |
| `/ki-executive-coaching-change/` | 404 | kritisch |
| `/ki-umsetzung-automatisierung/` | 404 | kritisch |
| `/ki-keynotes/` | 404 | kritisch |

Das Original nutzt diese sprachneutralen URLs als interne Einstiege und leitet
sie auf die deutsche Sprachversion weiter. Der Klon hat nur die Dateien unter
`/de/.../` und `/en/.../`. Fünf der fehlenden Pfade werden im Klon selbst noch
45-mal verlinkt.

`/` und `/kontakt/` sind im Klon vorhanden, verwenden aber clientseitige
Weiterleitungen auf `/de/` beziehungsweise `/de/kontakt/index.html`. Für den
Domainumzug sind serverseitige 301/308-Weiterleitungen robuster und
suchmaschinenfreundlicher.

## Textvergleich

Details und fehlende/zusätzliche Textblöcke stehen in
[`text-diff-summary.md`](text-diff-summary.md).

### Kritische Inhaltsabweichungen

- `/de/faq/` — Ähnlichkeit 15,5 %.
- `/en/faq/` — Ähnlichkeit 44,7 %.
- `/en/leistungen/` — Ähnlichkeit 56,2 %.
- Deutsche Teamprofile mit kritischer Abweichung:
  Andreas Rödenbeck, Kristin Goas Osés, Mario Levenhagen, Meike Quentin,
  René Goebels und Stephan Grandy.
- Englische Teamprofile mit kritischer Abweichung:
  Kristin Goas Osés, Mario Levenhagen, Meike Quentin, René Goebels und
  Stephan Grandy.
- Die sieben sprachneutralen URLs sind im Klon nicht inhaltsgleich, da sie 404
  liefern.

Die übrigen 39 mittleren Abweichungen betreffen überwiegend Startseiten,
Leistungsseiten, Team-Stadtarchive, Datenschutz und Netzwerkseiten. Das Muster
zeigt, dass sich das Original seit dem Klonzeitpunkt substanziell
weiterentwickelt hat.

### Struktur und Metadaten

- Meta Descriptions stimmen bei den direkt gemappten Inhaltsseiten weitgehend
  überein.
- Zehn Seitentitel weichen ab; fünf davon sind die 404-Seiten. Weitere
  Abweichungen betreffen die Redirect-Stubs und lokalisierte englische Titel.
- Auf fünf fehlenden Seiten erscheint im Klon `404 Not Found` als H1.
- 56 lokale HTML-Dateien enthalten Canonical-Tags zur Originaldomain. Für eine
  Staging-Domain kann das beabsichtigt sein; nach dem Domainumzug sind diese
  Canonicals korrekt, sofern Pfad und Inhalt existieren.
- Die statischen Dateien enthalten 700 strukturierte `link`-Referenzen zur
  Originaldomain, darunter Canonical, Hreflang, WordPress REST/oEmbed, Feeds,
  Shortlinks und EditURI.

## Bilder und Assets

Die vollständige seitenbezogene Tabelle steht in
[`assets-comparison.csv`](assets-comparison.csv). Die lokale
Dateiauflösung, einschließlich CSS-`url(...)` und Fonts, steht in
[`local-asset-check.csv`](local-asset-check.csv).

Ergebnis:

- Kein vom Klon geladenes Bild ist kaputt.
- Keine geladene CSS- oder JavaScript-Datei liefert einen Fehler.
- Keine lokal referenzierte Fontdatei fehlt.
- Keine lokale HTML-/CSS-Assetreferenz zeigt auf eine nicht vorhandene Datei.
- Zwei auf dem Original aktive TranslatePress-Flaggenbilder (`de_DE.png`,
  `en_US.png`) werden im Klon nicht geladen. Der Klon ersetzt den sichtbaren
  Sprachumschalter durch Text `DE | EN`; funktional ist das äquivalent, visuell
  aber nicht exakt.
- 19 eindeutige Originalbilder sind im Klon lokal mit gleichen Maßen und
  gleicher Dateigröße vorhanden, obwohl der Binärhash abweicht.
- Drei eindeutige CSS-/JS-Ressourcen sind pfadäquivalent, aber inhaltlich
  versionsverschieden: Complianz JavaScript, TranslatePress CSS und
  Popup-Maker CSS.

## Linkprüfung

Die vollständige Liste steht in
[`link-check.csv`](link-check.csv).

- 1784 geprüfte interne Linkvorkommen liefern HTTP 200.
- 45 Linkvorkommen sind kaputt und verteilen sich auf fünf sprachneutrale
  Leistungsziele.
- Die statischen `<a>`-Links des Crawls zeigen nicht direkt auf
  `ai-experts.network`.
- Im gerenderten Cookie-Dialog erzeugt Complianz jedoch weiterhin einen Link
  zur Cookie Policy auf der Originaldomain.
- Insgesamt enthalten 58 Klondateien 2403 textuelle Vorkommen von
  `ai-experts.network`. Viele davon sind SEO-/WordPress-Metadaten, mehrere sind
  jedoch aktive Laufzeit-Endpunkte.
- Die vollständigen externen Links stehen seitenweise in
  [`original-pages.json`](original-pages.json) und
  [`clone-pages.json`](clone-pages.json). Im Original wurden 10, im Klon 19
  eindeutige externe HTTP(S)-Ziele erfasst; die zusätzlichen Ziele stammen vor
  allem aus Cookie-Dokumentation.

## Sprachumschalter

Die sichtbaren DE-/EN-Links auf den Hauptseiten funktionieren und bleiben auf
der Klondomain. Der Klon verwendet lokale `index.html`-Pfade. Die Hreflang-Tags
zeigen hingegen weiterhin auf das Original. Das ist als Staging-Canonical
vertretbar, muss aber beim finalen Hosting mit der tatsächlich bedienten
Domain und allen vorhandenen Pfaden übereinstimmen.

## Formularprüfung

Die Kontaktseiten enthalten weiterhin die WordPress-Contact-Form-7-Formulare:

- Deutsch: 3 Formulare auf `/de/kontakt/`.
- Englisch: 3 Formulare auf `/en/kontakt/`.
- Die Feldstruktur entspricht dem gesicherten Original weitgehend.

**Kritisch:** Die JavaScript-Konfiguration sendet an
`https://ai-experts.network/{sprache}/wp-json/contact-form-7/v1` und weitere
WordPress-/Popup-/Complianz-Endpunkte. Solange das Original-WordPress läuft,
kann dies scheinbar funktionieren. Nach dessen Abschaltung ist der statische
Klon nicht funktional gleichwertig und Formularübermittlungen schlagen fehl.
Ein Formular wurde im Audit bewusst nicht abgeschickt.

Pragmatische Lösungen:

1. Bevorzugt: kleines serverloses Formular-Backend mit Spam-Schutz und
   E-Mail-Zustellung, dessen Endpoint im Klon konfiguriert wird.
2. Alternativ: externer Formulardienst mit eigener Datenschutzprüfung.
3. Minimaler Fallback: gut sichtbarer `mailto:`-Kontakt mit vorausgefülltem
   Betreff und Hinweis, dass keine Formulardaten gespeichert werden.

## Visueller Vergleich

Die Rohbilder liegen unter:

- [`screenshots/original/`](screenshots/original/)
- [`screenshots/clone/`](screenshots/clone/)
- [`screenshots/diff/`](screenshots/diff/)

Die Messwerte stehen in
[`visual-comparison.csv`](visual-comparison.csv).

### Desktop, vollständig

- 17 kritisch
- 16 mittel
- 9 niedrig
- 21 identisch oder vernachlässigbar

Kritische Desktop-Abweichungen konzentrieren sich auf Startseiten, mehrere
Teamprofile und Team-Stadtarchive. Die Leistungsseiten zeigen meist mittlere
Abweichungen. Die 404-Seiten sind visuell eindeutig.

### Tablet und Mobile

Tablet: 51 auswertbare Paare.  
Mobile: 20 auswertbare Paare.

Weitere Navigation zu beiden Domains wurde nach dem Hauptlauf von der
Browser-Sicherheitsrichtlinie blockiert. Die fehlenden Paare sind in
`visual-comparison.csv` explizit als nicht auswertbar markiert und wurden nicht
als visuelle Gleichheit gewertet.

## Kritische Findings

1. Sieben vom Original erreichbare sprachneutrale Seiten fehlen im Klon.
2. 45 interne Linkvorkommen führen zu fünf 404-Zielen.
3. 23 Seitenvergleiche haben kritische Textabweichungen; besonders FAQ und
   Teamprofile.
4. Die Formulare hängen vom bald möglicherweise nicht mehr verfügbaren
   WordPress-REST-Backend ab.
5. 17 von 63 vollständigen Desktop-Vergleichen sind visuell kritisch.
6. Laufzeitkonfigurationen für Contact Form 7, Popup Maker und Complianz zeigen
   weiter auf die Originalinstallation.

## Mittlere Findings

1. 39 Seiten haben relevante, aber nicht vollständig zerstörende
   Textabweichungen.
2. 16 Desktop-Seiten und weitere auswertbare Tablet-/Mobile-Seiten zeigen
   deutliche Layout- oder Inhaltsverschiebungen.
3. Drei CSS-/JS-Ressourcen sind gegenüber dem aktuellen Original
   versionsverschieden.
4. `/` und `/kontakt/` verwenden clientseitige statt serverseitige
   Weiterleitungen.
5. WordPress-REST-, oEmbed-, Feed-, Shortlink- und EditURI-Metadaten sind in
   statischen Seiten weiterhin enthalten.

## Niedrige Findings

1. Der Sprachumschalter verwendet Text statt der beiden Originalflaggen.
2. Kleine Abstände, Font-Rendering und Pixelunterschiede bleiben auf mehreren
   ansonsten ähnlichen Seiten.
3. Einzelne englische Seitentitel sind im Klon übersetzt, während das aktuelle
   Original deutsche Titel ausliefert.

## Konkrete Fix-Empfehlungen

### Priorität 0 – vor Domainumzug

1. Die sieben sprachneutralen Pfade serverseitig auf passende `/de/`-Ziele
   umleiten oder als echte Seiten bereitstellen.
2. Die 45 kaputten Linkvorkommen auf sprachlokale, vorhandene Ziele umschreiben.
3. Aktuellen Inhalt für FAQ, Teamprofile, Startseiten und `/en/leistungen/`
   vom archivierten Originalstand übernehmen und erneut vergleichen.
4. Das Kontaktformular auf einen vom Original unabhängigen Endpoint umstellen
   oder einen klaren `mailto:`-Fallback einsetzen.
5. Vor Abschaltung des Originals mindestens die kritisch abweichenden
   Originalseiten und ihre aktuellen Bilder erneut sichern.

### Priorität 1

1. Nicht benötigte WordPress-Laufzeitkonfigurationen und REST/oEmbed/Feed-
   Metadaten aus dem statischen Export entfernen.
2. Complianz/Popup-Maker nur behalten, wenn die Komponenten ohne WordPress
   vollständig lokal funktionieren; andernfalls durch eine statische,
   datenschutzkonforme Lösung ersetzen.
3. Canonical und Hreflang beim Cutover automatisiert auf die finale Domain
   ausrichten und alle Zielpfade mit HTTP 200 prüfen.
4. Serverbasierte 301/308-Redirects für `/` und `/kontakt/` konfigurieren.
5. Nach Inhaltsaktualisierung den kompletten Screenshot-Diff erneut ausführen.

## Go/No-Go

**NO-GO.** Der Klon sollte die Originaldomain noch nicht ersetzen.

Ein Go ist vertretbar, sobald mindestens:

- alle sieben fehlenden Pfade auf funktionierende 200-/301-/308-Ziele führen,
- keine internen Links mehr 404 liefern,
- FAQ, Teamprofile, Startseiten und englische Leistungsseite aktualisiert sind,
- das Kontaktformular ohne Original-WordPress funktioniert,
- ein erneuter Desktop-/Tablet-/Mobile-Vergleich keine kritischen
  Inhalts- oder Layoutlücken mehr zeigt.

