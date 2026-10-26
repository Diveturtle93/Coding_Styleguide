# Coding_Styleguide

Verbindliche Coding Styles und Dokumentationsregeln für die Projekte von **Diveturtle93**, dazu Skripte, die Quelldateien dagegen prüfen.

## Beschreibung

Die Regeln legen fest, wie C- und Python-Dateien aufgebaut und formatiert sind und welche Dokumente ein Repository braucht. Die Prüfskripte laufen über alle Projekte neben diesem Repo und melden jede Abweichung mit Datei, Zeile und Kategorie, auf Wunsch als Report je Projekt.

## Inhalt

| Datei | Inhalt |
|---|---|
| [docs/C_CODING_STYLE.md](docs/C_CODING_STYLE.md) | Regeln für C-Dateien (`.c` / `.h`), geprüft von [tools/c_stylecheck.py](tools/c_stylecheck.py) |
| [docs/PYTHON_CODING_STYLE.md](docs/PYTHON_CODING_STYLE.md) | Regeln für Python-Dateien (`.py`), geprüft von [tools/py_stylecheck.py](tools/py_stylecheck.py) |
| [docs/DOCUMENTATION_STYLE.md](docs/DOCUMENTATION_STYLE.md) | Regeln für die Dokumentation (`.md`) und die Versionierung, geprüft von [tools/doc_check.py](tools/doc_check.py) |
| [docs/templates/SECURITY.md](docs/templates/SECURITY.md) | Optionale Vorlage für die Sicherheitsrichtlinie, wird als `.github/SECURITY.md` in ein Projekt kopiert |
| [tools/](tools/README.md) | Prüfskripte: Aufruf, Optionen, Reports und Projekteinstellungen (`.stylecheck`) |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Aufbau und Ablauf der Prüfskripte |
| [CHANGELOG.md](CHANGELOG.md) | Änderungen je Version |

## Verwendung

Das Repo wird neben die zu prüfenden Projekte geklont:

```
own/
├── Coding_Styleguide/
├── STM32_Canbus/
└── EAuto_BMS/
```

```sh
py tools/c_stylecheck.py          # alle Ordner neben diesem Repo prüfen
py tools/py_stylecheck.py -q      # nur Python-Dateien mit Befund anzeigen
py tools/doc_check.py -q          # Dokumentation aller Projekte prüfen
```

Alle Optionen, Reports und Projekteinstellungen stehen in der [Tool-Beschreibung](tools/README.md).

## Abhängigkeiten

- Python 3.10 oder neuer (`py_stylecheck.py` erkennt `match` / `case` über `ast.Match`), keine weiteren Pakete

## Lizenz

Dieses Projekt steht unter der [GPL-3.0 Lizenz](LICENSE).
