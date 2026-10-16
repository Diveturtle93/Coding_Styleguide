# Architektur Coding_Styleguide

Das Repository besteht aus den Regeln (`docs/*_STYLE.md`) und zwei Prüfern in `tools/`, die Quelldateien in den Nachbar-Repos gegen diese Regeln prüfen. Beide Prüfer laufen nach demselben Ablauf: Projekte finden, jede Datei prüfen, Befunde sammeln, ausgeben oder als Report schreiben. Dieser Ablauf und alles, was beide Sprachen gleich prüfen, liegt in `stylecheck_common.py`. Die Prüfer enthalten nur die Regeln ihrer Sprache.

## Komponenten

```mermaid
flowchart LR
    subgraph Regeln[docs]
        CS[C_CODING_STYLE.md]
        PS[PYTHON_CODING_STYLE.md]
    end
    subgraph tools
        C[c_stylecheck.py<br/>C-Regeln]
        P[py_stylecheck.py<br/>Python-Regeln]
        K[stylecheck_common.py<br/>Ablauf, gemeinsame Prüfungen,<br/>Reports, Version des Repos]
    end
    subgraph Projekt[geprüftes Projekt]
        SRC[.c / .h / .py]
        CFG[.stylecheck]
        GM[.gitmodules]
    end
    R[(reports/c/<br/>reports/py/)]

    CS -. beschreibt .-> C
    PS -. beschreibt .-> P
    C -- "run(Language)" --> K
    P -- "run(Language)" --> K
    K --> SRC
    K --> CFG
    K --> GM
    K --> R
```

| Modul | Datei(en) | Aufgabe |
|-------|-----------|---------|
| Gemeinsamer Code | `tools/stylecheck_common.py` | `run()` mit Kommandozeile, Projektsuche (`collectProjects`, `projectSettings`), Ausgabe, Reports und Übersicht. Gemeinsame Prüfungen: Zeilenenden (`readLines`), Kopfblock (`checkHead`), Abschnittsform, Pflicht- und Variablen-Abschnitte, Debug-Abschnitt, Reihenfolge (`checkOrder`) und Version je Projekt (`checkProjectVersion`). Enthält den Abschnitt `Version definieren` des Repositories |
| C-Prüfer | `tools/c_stylecheck.py` | Prüft `.c`/`.h` zeilenweise mit regulären Ausdrücken (Header, Formatierung, `switch`/`case`, Ausrichtung). Erkennt von STM32CubeMX erzeugte Dateien und prüft dort nur die `USER CODE`-Bereiche |
| Python-Prüfer | `tools/py_stylecheck.py` | Prüft `.py` mit `ast` (Imports, Funktionen, Klassen, Abschnitte) und `tokenize` (Kommentare, Strings, Anweisungen) |
| Regeln | `docs/C_CODING_STYLE.md`, `docs/PYTHON_CODING_STYLE.md`, `docs/DOCUMENTATION_STYLE.md` | Maßgebliche Beschreibung. Der Prüfer setzt um, was dort steht, nicht umgekehrt |
| Projekteinstellungen | `.stylecheck` im geprüften Projekt | Zusätzliche Aus- und Einschlüsse, `[stylecheck]` für beide Sprachen, `[c]` und `[py]` je Sprache |

Jeder Prüfer beschreibt seine Sprache mit einem `Language`-Objekt: Name, Regeldatei, Dateiendungen, Zeile des Versionsabschnitts, automatische Ausschlüsse, eine Funktion `checkProject`, die alle Dateien eines Projekts prüft, und optional `isGenerated` für erzeugte Dateien.

## Datenfluss

Ablauf eines Aufrufs, am Beispiel `py tools/c_stylecheck.py -r`. `py_stylecheck.py` läuft genauso, nur mit eigenem `checkProject`.

```mermaid
sequenceDiagram
    participant Run as run(Language)
    participant Coll as collectProjects()
    participant Set as projectSettings()
    participant Chk as checkProject() / checkFile()
    participant Ver as checkProjectVersion()
    participant Rep as buildReport() / buildOverview()

    Run->>Coll: Pfade / Glob-Muster (Standard: alle Ordner neben dem Repo)
    loop je Projektordner
        Coll->>Set: .gitmodules und .stylecheck lesen
        Set-->>Coll: Aus- und Einschlüsse
        Coll->>Coll: listFiles(), Ausschlüsse und -x anwenden, CubeMX-Dateien markieren
    end
    Coll-->>Run: {Projekt: [Ordner, [(Datei, nur USER CODE)], als Ordner angegeben]}
    loop je Projekt
        Run->>Chk: Dateien des Projekts
        Chk-->>Run: [(Datei, [Issue(Zeile, Kategorie, Info)])]
        Run->>Ver: nur wenn der Ordner angegeben wurde
        Ver-->>Run: Befunde für das Projekt, mehrfache Abschnitte bei den Dateien
    end
    alt mit -r
        Run->>Rep: Befunde je Projekt
        Rep-->>Run: reports/c/<JJJJMMTT>_<Projekt>.txt und _Uebersicht.txt
    else ohne -r
        Run->>Run: Befunde auf der Konsole (-q, -s)
    end
    Run-->>Run: Rückgabewert 0 / 1 / 2
```

- Ein Befund ist immer ein `Issue` mit Zeile (`0` = ganze Datei bzw. ganzes Projekt), Kategorie und Zusatzinfo. Ausgabe, Report und Übersicht arbeiten nur mit diesen Listen.
- Reports werden als ASCII mit CRLF geschrieben. Ein Report vom selben Tag wird überschrieben.

## Erweiterung

- **Neue Prüfung für eine Sprache:** in `checkFile()` des passenden Prüfers mit `add(zeile, "Kategorie", "Info")` einen Befund melden. Gilt sie für beide Sprachen, gehört sie als Funktion nach `stylecheck_common.py`. Die Regel steht vorher im zugehörigen `docs/*_STYLE.md`.
- **Neue Einstellung in `.stylecheck`:** in `projectSettings()` auswerten. Unbekannte Abschnitte und Einträge erzeugen dort eine Warnung, ein neuer Abschnitt muss deshalb in `CONFIG_SECTIONS` eingetragen werden. `[doc]` steht dort schon für das geplante `doc_check.py` und wird von den Stylechecks überlesen.
- **Neuer Prüfer** (z. B. `doc_check.py`): ein `Language`-Objekt mit eigenem `key` (Abschnitt in `.stylecheck` und Report-Unterordner) und eigenem `checkProject` anlegen und `run()` aufrufen. Optionen, Reports und Übersicht kommen damit automatisch.
- **Version:** Das Repository hat nach `docs/DOCUMENTATION_STYLE.md` Abschnitt 6 genau eine Version. Sie steht im Abschnitt `Version definieren` von `stylecheck_common.py` (`STYLECHECK_COMMON_*`).
