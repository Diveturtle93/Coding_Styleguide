# Stylecheck-Tools

Die Skripte pruefen Quelldateien und Dokumentation gegen die Regeln von **Diveturtle93**:

| Skript | Prueft | Regeln | Voraussetzung |
|---|---|---|---|
| [c_stylecheck.py](c_stylecheck.py) | `.c` / `.h` | [C Coding Style](../docs/C_CODING_STYLE.md) | Python 3 |
| [py_stylecheck.py](py_stylecheck.py) | `.py` | [Python Coding Style](../docs/PYTHON_CODING_STYLE.md) | Python 3.10+ |
| [doc_check.py](doc_check.py) | Dokumente je Projekt, `.md` | [Documentation Style](../docs/DOCUMENTATION_STYLE.md) | Python 3 |

Gemeinsam genutzter Code (Kommandozeile, Projektsuche, `.stylecheck`, Kopfblock- und Abschnittspruefungen, Reihenfolge, Reports und Uebersicht) liegt in [stylecheck_common.py](stylecheck_common.py). Es wird nicht selbst aufgerufen und muss im selben Ordner wie die Skripte liegen.

Alle Skripte benoetigen keine weiteren Pakete und haben dieselben Optionen. Die Beispiele zeigen `c_stylecheck.py`, fuer Python oder die Dokumentation wird nur der Skriptname getauscht. Was `doc_check.py` anders macht, steht unter [Dokumentation pruefen](#dokumentation-pruefen).

---

## Aufruf

```sh
py tools/c_stylecheck.py                          # alle Ordner neben diesem Repo
py tools/c_stylecheck.py ../STM32_Canbus          # ein Ordner
py tools/c_stylecheck.py "../EAuto_*" ../IMD_*    # beliebige Ordner oder Glob-Muster
py tools/c_stylecheck.py ../STM32_Millis/millis.h # eine Datei
py tools/c_stylecheck.py -q                       # nur Dateien mit Befund anzeigen
py tools/c_stylecheck.py -s                       # nur Zusammenfassung
py tools/c_stylecheck.py ../EAuto_BMS -x openblt  # zusaetzlich Pfade ausschliessen (Regex)
py tools/c_stylecheck.py -r                       # je Projekt Report schreiben
py tools/c_stylecheck.py "../EAuto_*" -r          # Reports fuer andere Ordner
py tools/c_stylecheck.py -r -f                    # Reports nur fuer Projekte mit Befunden
py tools/c_stylecheck.py -c                       # alle Reports der Sprache loeschen
py tools/c_stylecheck.py -c out                   # alle Reports der Sprache in out/ loeschen
py tools/c_stylecheck.py -c -r                    # alte Reports loeschen, danach neu schreiben
py tools/c_stylecheck.py --no-default-exclude     # automatische Ausschluesse abschalten
```

Jeder per Pfad oder Glob gefundene Ordner gilt als eigenes Projekt. Ordner ohne passende Dateien werden beim Standardaufruf stillschweigend uebersprungen.

Der Abschnitt `Version definieren` wird je Projekt geprueft: Er muss genau einmal vorkommen (generierte CubeMX-Dateien zaehlen nicht). Fehlt er, steht im Report ein Befund fuer das ganze Projekt (`Projekt`), steht er mehrfach, wird jede Fundstelle gemeldet. In C muss er in einer `.h`-Datei stehen, in einer `.c`-Datei ist er ein Befund. Wird nur eine einzelne Datei angegeben, entfaellt diese Pruefung. Jedes Skript prueft nur die Dateien seiner Sprache; ein Repo mit C- und Python-Dateien wuerde deshalb je Sprache einen Abschnitt verlangen (kommt heute nicht vor).

Rueckgabewert: `0` = keine Befunde, `1` = Befunde, `2` = keine Dateien gefunden.

---

## Typen von Variablen (C)

`c_stylecheck.py` meldet unter `Typ nicht definiert` Variablen und Parameter, deren Typ es im Projekt nicht gibt, z. B. `RingbufferTypeDef rxRing;`, obwohl der Typedef `RingbufferCANBusTypeDef` heisst. Der Befund nennt den aehnlichsten bekannten Typ (`RingbufferTypeDef (aehnlich: RingbufferCANBusTypeDef)`). Regel: [C Coding Style, Typen von Variablen](../docs/C_CODING_STYLE.md#typen-von-variablen).

- Typedefs und `struct`/`enum`/`union`-Tags werden je Projekt aus allen `.c`/`.h`-Dateien gesammelt, auch aus den automatisch ausgeschlossenen (HAL, CMSIS, Middleware, Submodule). Typen von HAL und FreeRTOS sind damit bekannt, ohne dass diese Dateien geprueft werden.
- Liegen die HAL-Header nicht im Projekt (Bibliotheken ohne `Drivers/`), gelten bekannte Namen von HAL/LL (`<Peripherie>_...TypeDef`, z. B. `CAN_HandleTypeDef`), CMSIS, CMSIS-RTOS (`os...`), FatFs und FreeRTOS als bekannt.
- Typen aus anderen Repos, die nicht als Submodul im Projekt liegen, stehen in `[c] types` der `.stylecheck`.
- Wird eine einzelne Datei angegeben, zaehlen die Typen aus deren Ordner.

---

## Dokumentation pruefen

`doc_check.py` prueft die Regeln aus [Documentation Style, Abschnitt 13](../docs/DOCUMENTATION_STYLE.md#13-automatische-prüfung). Bisher ist das die Vollstaendigkeit, die Gliederung von README, CHANGELOG, ARCHITECTURE und RUNBOOK folgt.

```sh
py tools/doc_check.py                             # alle Ordner neben diesem Repo
py tools/doc_check.py ../STM32_Canbus -q          # ein Projekt, nur Dateien mit Befund
py tools/doc_check.py -r -f                       # Reports nach reports/doc/, nur Projekte mit Befunden
```

Unterschiede zu den Stylechecks:

- Jeder angegebene Ordner ist ein Projekt, auch ohne `.md`-Datei, denn eine fehlende README ist gerade der Befund.
- Befunde zum ganzen Projekt (`Projekt`): Repo-Klasse, Pflichtdateien `README.md` und `CHANGELOG.md`, Dokumente aus `[doc] require`, Fachdokumente im Hauptverzeichnis (`Ablage`) und Ordner ohne README, die mehr als 3 Dokumente oder mindestens 2 ausfuehrbare Werkzeuge (`.py` mit Shebang oder `__main__`, `.sh`, `.bat`, `.cmd`, `.ps1`) enthalten.
- Befunde je `.md`-Datei: relative Links auf fehlende Dateien, in anderer Schreibweise oder aus dem Repository heraus (Links in Codebloecken und Inline-Code zaehlen nicht); in der README im Hauptverzeichnis `## Lizenz` genau dann, wenn eine `LICENSE` vorliegt.
- Repos der Klasse `ausgenommen` werden gelistet, aber nicht geprueft.
- Ein einzeln angegebenes Dokument wird nur auf Links und Lizenz geprueft, die Pruefungen fuer das Projekt entfallen.
- Automatisch ausgeschlossen werden Git-Submodule, versteckte Ordner sowie `Drivers`, `Middlewares`, `CMSIS`, `Debug`, `Release`, `build`, `dist`, virtuelle Umgebungen, `node_modules` und `__pycache__`.

---

## Reports

Mit `-r` wird je Projekt ein Report geschrieben, Standard-Ordner ist `reports/` in diesem Repo. Jede Sprache hat einen eigenen Unterordner:

| Skript | Report-Ordner | Beispiel |
|---|---|---|
| `c_stylecheck.py` | `reports/c/` | `reports/c/20261008_STM32_Canbus.txt` |
| `py_stylecheck.py` | `reports/py/` | `reports/py/20261012_EAuto_Dashboard.txt` |
| `doc_check.py` | `reports/doc/` | `reports/doc/20261016_STM32_Canbus.txt` |

- Ein Report listet je Datei jeden Befund mit Zeilennummer und Kategorie (`Datei` = betrifft die ganze Datei, z. B. fehlender Abschnitt).
- Der Dateiname beginnt mit dem Datum `<JJJJMMTT>`; ein Report vom selben Tag wird ueberschrieben, aeltere bleiben erhalten.
- Zusaetzlich entsteht immer `<JJJJMMTT>_Uebersicht.txt` mit einer Zeile je gepruefem Projekt (Dateien, Befunde, Report geschrieben ja/nein). Die Uebersicht enthaelt auch mit `-f` alle Projekte.
- `-c` loescht alle Reports (`<JJJJMMTT>_*.txt`, jedes Datum, jedes Projekt, auch die Uebersicht) im Unterordner der eigenen Sprache; andere Dateien und die Reports der anderen Sprache bleiben erhalten.

Der Ordner `reports/` steht in der `.gitignore`.

---

## Automatische Ausschluesse

Das Repository `Diveturtle93` (GitHub-Profil) wird von allen Skripten uebersprungen, auch wenn es ausdruecklich angegeben ist, und erscheint nicht in der Uebersicht (`EXCLUDED_REPOS` in `stylecheck_common.py`).

Git-Submodule aus der `.gitmodules` des Projekts und der Ordner `.git` werden immer uebersprungen; Submodule sind eigene Repos und werden dort geprueft. Dazu kommen je Sprache:

**C**

- Ordner `Drivers`, `Middlewares`, `CMSIS` (HAL, CMSIS, Middleware von ST) sowie `Debug`, `Release` und `build` (Build-Ausgaben).
- Dateien `stm32*_hal*` (ausser `stm32*_hal_msp.c`), `system_stm32*`, `startup_*`, `syscalls.c` und `sysmem.c`.
- Von STM32CubeMX generierte Dateien (z. B. unter `Core/`) werden nur zwischen `/* USER CODE BEGIN ... */` und `/* USER CODE END ... */` geprueft. Der Bereich `Header` (ST-Lizenzkopf) und die Pruefungen der Dateistruktur (Kopfblock, Abschnitte, Header, Debug-Symbole, Reihenfolge, Include-Abschnitte, Typedefs und Variablen ausserhalb der Variablen-Abschnitte) entfallen, fehlerhafte Marker werden gemeldet. Im Report sind diese Dateien mit `nur USER CODE` gekennzeichnet.

**Python**

- Ordner fuer virtuelle Umgebungen (`venv`, `.venv`, `env`, `site-packages`), Caches (`__pycache__`, `.tox`, `.mypy_cache`, `.pytest_cache`), Build-Ausgaben (`build`, `dist`) und `node_modules`.

Mit `--no-default-exclude` werden alle diese Dateien vollstaendig geprueft.

---

## Projekteinstellungen (`.stylecheck`)

Projektspezifische Einstellungen stehen optional in der Datei `.stylecheck` im Projektordner. Sie wird von allen Skripten gelesen, ein unbekannter Abschnitt oder Eintrag erzeugt eine Warnung:

| Abschnitt | Gilt fuer |
|---|---|
| `[stylecheck]` | alle Skripte |
| `[c]` | nur `c_stylecheck.py`, ergaenzt `[stylecheck]`. Zusaetzlich `types` (bekannte Typen, die nicht im Projekt definiert sind), siehe [Typen von Variablen](#typen-von-variablen-c) |
| `[py]` | nur `py_stylecheck.py`, ergaenzt `[stylecheck]` |
| `[doc]` | nur `doc_check.py`, ergaenzt `[stylecheck]`. Eintraege `exclude`, `class` (Repo-Klasse) und `require` (zusaetzlich verlangte Dokumente), siehe [Documentation Style, Abschnitt 13](../docs/DOCUMENTATION_STYLE.md#13-automatische-prüfung) |

Ordner oder einzelne Dateien werden relativ zum Projektordner angegeben, mehrere mit Komma getrennt:

```ini
[stylecheck]
exclude = Test                  # fuer C und Python ausschliessen

[c]
exclude = Application/Inc/git.h # nur fuer C zusaetzlich ausschliessen
include = Core, Application     # nur diese Ordner pruefen
types = uart_status             # Typ aus STM32_Basicuart (kein Submodul)

[py]
exclude = openblt               # nur fuer Python zusaetzlich ausschliessen

[doc]
class = werkzeug                # Repo-Klasse, wenn sie sich nicht aus dem Namen ergibt
require = runbook               # RUNBOOK.md muss vorhanden sein
```

Die Datei wird nur angelegt, wenn die automatischen Ausschluesse nicht reichen. Die frueheren Dateien `.c_stylecheck` und `.py_stylecheck` werden nicht mehr gelesen; liegen sie noch im Projekt, gibt das Skript eine Warnung aus.
