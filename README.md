# Coding_Styleguide

Verbindliche Coding Styles fuer die Projekte von **Diveturtle93** und Skripte, die Quelldateien dagegen pruefen.

| Sprache | Regeln | Pruefskript |
|---|---|---|
| C (`.c` / `.h`) | [C Coding Style](C_CODING_STYLE.md) | [tools/c_stylecheck.py](tools/c_stylecheck.py) |
| Python (`.py`) | [Python Coding Style](PYTHON_CODING_STYLE.md) | [tools/py_stylecheck.py](tools/py_stylecheck.py) |

## Schnellstart

Das Repo wird neben die zu pruefenden Projekte geklont:

```
own/
├── Coding_Styleguide/
├── STM32_Canbus/
└── EAuto_BMS/
```

```sh
py tools/c_stylecheck.py          # alle Ordner neben diesem Repo pruefen
py tools/py_stylecheck.py -q      # nur Python-Dateien mit Befund anzeigen
```

Alle Optionen, Reports und Projekteinstellungen (`.stylecheck`) stehen in der [Tool-Beschreibung](tools/README.md).

## Lizenz

[GPL-3.0](LICENSE)
