# Sicherheitsrichtlinie <Name>

Diese Richtlinie beschreibt, wie Sicherheitslücken in <Name> gemeldet werden
und welche Versionen Fehlerbehebungen bekommen.

## Unterstützte Versionen

| Version | Unterstützt |
|---|---|
| neuester Tag in `main` | ja |
| ältere Tags | nein |
| Stand auf `develop` (`_DEV` = 1) | nein |

## Sicherheitslücke melden

Sicherheitslücken bitte **nicht** als öffentliches Issue melden, sondern über
den Reiter **Security** → **Report a vulnerability**.

Die Meldung sollte enthalten:

- Version (Git-Tag oder Versions-Defines)
- Hardware und Platinenrevision, falls zutreffend
- Schritte zum Nachstellen
- mögliche Auswirkung

## Ablauf

1. Eingangsbestätigung innerhalb von <N> Werktagen.
2. Bewertung der Meldung und Rückmeldung, ob sie als Sicherheitslücke gilt.
3. Behebung als Patch-Release in `main` mit neuem Tag und Eintrag im CHANGELOG.
4. Veröffentlichung der Details erst, wenn der Tag gesetzt ist.
