# Mitarbeit an <Name>

Diese Datei beschreibt, wie Änderungen in <Name> kommen: Branch, CHANGELOG-Eintrag,
Versionierung und Prüfung vor dem Merge. Grundlage ist der
[Documentation Style](https://github.com/Diveturtle93/Coding_Styleguide/blob/main/docs/DOCUMENTATION_STYLE.md).

## Branches

| Branch | Inhalt | `_DEV` |
|---|---|---|
| `main` | getaggter Release-Stand | 0 |
| `develop` | letztes Release plus unveröffentlichte Änderungen | 1 |

- Neue Funktionen und Änderungen kommen auf `develop`.
- Ein Fehler kann direkt in `main` behoben werden, siehe [Versionierung](#versionierung).

## Dokumentation

- Wird eine Schnittstelle geändert, werden README und CHANGELOG im selben Commit angepasst.
- Fachdokumente liegen in `docs/` und werden in der README unter `## Dokumente` verlinkt.
- Diagramme als Mermaid im Markdown, Bilder nur wenn nötig in `docs/img/`, Beispielcode in `examples/`.

## CHANGELOG

Jede Änderung, die für Nutzer sichtbar ist, bekommt einen Eintrag unter `## [Unveröffentlicht]`:

- ein Satz pro Änderung, aus Sicht des Nutzers, keine Commit-Liste
- nur die vorkommenden Kategorien, in dieser Reihenfolge: `Hinzugefügt`, `Geändert`, `Behoben`, `Entfernt`

## Versionierung

Die Version folgt [Semantic Versioning](https://semver.org/lang/de/) und steht einmal im Repository
im Abschnitt `Version definieren` (`_MAJOR`, `_MINOR`, `_PATCH`, `_DEV`) in `<Datei>`.
Tags haben die Form `<X.Y.Z>`.

| Teil | wird erhöht, wenn … |
|---|---|
| MAJOR | die API nicht mehr kompatibel ist |
| MINOR | eine neue Funktion dazukommt und die API unverändert bleibt |
| PATCH | ein Fehler ohne API-Änderung behoben wird |

- Auf `develop` wird die Nummer nicht im Voraus erhöht.
- Release: [Documentation Style, 6.2](https://github.com/Diveturtle93/Coding_Styleguide/blob/main/docs/DOCUMENTATION_STYLE.md#62-release)
- Patch in `main`: [Documentation Style, 6.3](https://github.com/Diveturtle93/Coding_Styleguide/blob/main/docs/DOCUMENTATION_STYLE.md#63-patch-in-main)

## Prüfung

Vor dem Merge laufen `doc_check.py` und die Stylechecks aus dem
[Coding_Styleguide](https://github.com/Diveturtle93/Coding_Styleguide/blob/main/tools/README.md) ohne Befund.
Einstellungen für dieses Repository stehen in der `.stylecheck`.

## Checkliste

- [ ] Schnittstellen-Änderung: README und CHANGELOG im selben Commit angepasst
- [ ] CHANGELOG-Eintrag unter `## [Unveröffentlicht]`
- [ ] Neue Fachdokumente in `docs/` und in der README verlinkt
- [ ] Versions-Defines nicht im Voraus erhöht, `_DEV` auf `develop` 1 und auf `main` 0
- [ ] `doc_check.py` und Stylechecks ohne Befund
