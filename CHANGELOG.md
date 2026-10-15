# Changelog

Alle nennenswerten Änderungen an diesem Projekt werden hier dokumentiert.
Format nach [Keep a Changelog](https://keepachangelog.com/de/1.1.0/),
Versionierung nach [Semantic Versioning](https://semver.org/lang/de/).

## [Unveröffentlicht]

### Hinzugefügt
- Documentation Style (`DOCUMENTATION_STYLE.md`) mit Repo-Klassen, Pflichtdokumenten, Vorlagen für README, CHANGELOG, ARCHITECTURE, RUNBOOK und ADR sowie Regeln zur Versionierung.
- `ARCHITECTURE.md` beschreibt Aufbau und Ablauf der Prüfskripte.
- `CHANGELOG.md` mit den Änderungen je Version.
- Stylechecks melden, wenn der Abschnitt `Version definieren` in einem Projekt fehlt oder mehrfach vorkommt (in C außerdem, wenn er in einer `.c`-Datei steht), und eine noch vorhandene Zeile `Version` im Kopfblock.
- `tools/stylecheck_common.py` enthält den gemeinsamen Code beider Prüfer.
- C-Stylecheck meldet Includes im falschen Include-Abschnitt, Funktionen ohne Trennlinie danach, `break;` hinter einem case-Block und `#define`-Namen, die nicht in Großbuchstaben stehen.
- Beide Stylechecks melden mehr als eine Leerzeile zwischen zwei Abschnitten.
- C und Python Coding Style: Regeln für das Leerzeichen nach `//` und für leere Kommentarzeilen; C: Zuordnung der Includes zu den Abschnitten.

### Geändert
- README nach der Gliederung für Referenz-Repos: Beschreibung, Inhalt, Verwendung und Abhängigkeiten.
- Eine Version pro Repository: Die Zeile `Version` entfällt im Dateikopf, der Abschnitt `Version definieren` steht nur noch einmal im Repository (C Coding Style, Python Coding Style).
- Der Abschnitt `Version definieren` ist pro Datei nicht mehr Pflicht. Wo er steht, müssen `_MAJOR`, `_MINOR`, `_PATCH` und `_DEV` vollständig sein.
- Die Prüfer verwenden eine gemeinsame Version (`STYLECHECK_COMMON_*` in `tools/stylecheck_common.py`) statt je einer eigenen.
- C-Dateien: `Sprache` im Kopfblock muss `C` enthalten, die Include-Abschnitte werden wie in Python auf ihre Form geprüft.
- C und Python Coding Style: Funktionsnamen dürfen Wörter mit `_` trennen (`ADC_Bremsdruck`, `ltc6811_write`). Geprüft werden nur noch die Namen von `#define` (C) und Klassen (Python).
- C-Stylecheck: Als Fall-through-Markierung zählt nur noch `// fall through - <Begruendung>`, andere Schreibweisen werden gemeldet.

### Behoben
- C-Stylecheck: Das `default` eines verschachtelten `switch` zählt nicht mehr für den äußeren.
- Beide Stylechecks erkennen gemischte Einrückung aus Tabs und Leerzeichen, nicht nur führende Leerzeichen.

## [1.0.0] - 2026-10-14

### Hinzugefügt
- Erste versionierte Veröffentlichung, übernommen aus dem Repository `Diveturtle93`.
- C Coding Style (`C_CODING_STYLE.md`) für `.c`- und `.h`-Dateien.
- Python Coding Style (`PYTHON_CODING_STYLE.md`) für `.py`-Dateien.
- `tools/c_stylecheck.py` prüft C-Dateien gegen den C Coding Style.
- `tools/py_stylecheck.py` prüft Python-Dateien gegen den Python Coding Style.
- Reports je Projekt und eine Übersicht über alle Projekte (`-r`, `-f`, `-c`).
- Projekteinstellungen über die Datei `.stylecheck` im geprüften Projekt.
- Automatische Ausschlüsse für HAL, CMSIS, Build-Ordner, Git-Submodule und virtuelle Python-Umgebungen; von STM32CubeMX erzeugte Dateien werden nur in den `USER CODE`-Bereichen geprüft.

[Unveröffentlicht]: https://github.com/Diveturtle93/Coding_Styleguide/compare/1.0.0...HEAD
[1.0.0]: https://github.com/Diveturtle93/Coding_Styleguide/releases/tag/1.0.0
