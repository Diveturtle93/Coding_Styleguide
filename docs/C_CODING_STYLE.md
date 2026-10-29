# C Coding Style

Verbindlicher Layout- und Formatierungsstandard fuer alle C-Dateien (`.c` / `.h`) in den Projekten von **Diveturtle93**.

---

## 1. Allgemeine Regeln

| Regel | Festlegung |
|---|---|
| Einrueckung | **Tabs**, Tabbreite **4** |
| Zeilenende | CRLF |
| Zeichensatz | reines ASCII – Umlaute werden als `ae`, `oe`, `ue`, `ss` geschrieben |
| Sprache Kommentare | Deutsch |
| Kommentarstil | nur `//`, nach `//` immer ein Leerzeichen, keine `/* */`-Bloecke (Ausnahme: `#endif /* INC_<NAME>_H_ */`) |
| Doxygen | **nicht** verwenden |
| `extern "C"` | **nicht** verwenden |
| Klammerstil | Allman (jede `{` und `}` in eigener Zeile) |

### Trennlinie

Die Trennlinie besteht aus `//` gefolgt von **70** Bindestrichen (72 Zeichen gesamt):

```c
//----------------------------------------------------------------------
```

### Abschnitte

Jeder Abschnitt einer Datei hat immer dieselbe Form:

```c
// <Abschnittsname>
//----------------------------------------------------------------------
<Inhalt>
//----------------------------------------------------------------------
```

- Zwischen zwei Abschnitten steht genau **eine Leerzeile**.
- Die Include-Abschnitte werden **immer** angelegt, auch wenn sie leer sind (dann steht eine Leerzeile zwischen den Linien). Alle anderen Abschnitte stehen nur dort, wo sie Inhalt haben.
- Ein Abschnitt endet erst an einer Trennlinie, auf die eine Leerzeile folgt. Die Leerzeile trennt Abschnitte, die Trennlinie allein trennt Bloecke innerhalb eines Abschnitts.
- Mehrere Typdefinitionen innerhalb eines Abschnitts werden nur durch eine Trennlinie getrennt (ohne Leerzeile), die naechste Zeile beginnt mit `typedef` oder mit einem Kommentar zur Typdefinition.
- **Unterabschnitte**: Ein Abschnitt darf in benannte Bloecke geteilt werden. Der Unterabschnitt folgt direkt auf die schliessende Trennlinie, ohne Leerzeile, und hat dieselbe Form wie ein Abschnitt. Er gehoert zum Abschnitt davor, z. B. zaehlen Variablen darin als in `Variablen definieren` stehend. Eine Beschreibung zum Unterabschnitt steht als Kommentar im Block, nicht zwischen zwei weiteren Trennlinien.
- Abschnitte mit festem Namen (z. B. `Variablen einbinden`, `Konstanten definieren`) und Funktionen sind nie Unterabschnitte, vor ihnen steht immer eine Leerzeile.
- Die Form wird fuer alle Abschnitte mit festem Namen und fuer die Typedef-Abschnitte geprueft.

```c
// Variablen definieren
//----------------------------------------------------------------------
static uint8_t zaehler = 0;													// Interner Zaehler
//----------------------------------------------------------------------
// Definiere Zellenarray Spannungen
//----------------------------------------------------------------------
// Werte je Modul
uint16_t cellvoltage[LTC6811_DEVICES][LTC6811_CELLS] = {0};					// Gemessene Zellspannungen
//----------------------------------------------------------------------

// Initialisiere Beispiel
```

---

## 2. Dateikopf

Jede Datei (`.c` und `.h`) beginnt mit diesem Kopfblock. Alle Doppelpunkte stehen mit Tabs ausgerichtet auf **Spalte 13** (Tabbreite 4), zwischen `:` und Wert steht **ein Tab**.

```c
//----------------------------------------------------------------------
// Titel	:	<dateiname>.h
//----------------------------------------------------------------------
// Sprache	:	C
// Datum	:	TT.MM.JJJJ
// Autor	:	Diveturtle93
// Projekt	:	<Projektname>
// Quelle	:	<optional: URL / Herkunft, sonst leer>
//----------------------------------------------------------------------
```

- **Titel** – exakter Dateiname inkl. Endung
- **Datum** – Erstellungsdatum im Format `TT.MM.JJJJ`
- **Quelle** – Zeile ist immer vorhanden, darf leer bleiben

---

## 3. Header-Datei (`.h`)

Reihenfolge der Abschnitte (Pflicht, fett = immer vorhanden):

1. **Dateikopf**
2. **Sicherheitssymbol** – `#pragma once`
3. **Dateiheader definieren** – Include-Guard `INC_<NAME>_H_`
4. **Einfuegen der standard Include-Dateien** – `<stdint.h>`, `<stdbool.h>`, …
5. **Einfuegen der STM Include-Dateien** – `"main.h"`, `"can.h"`, …
6. **Einfuegen der eigenen Include-Dateien**
7. Definiere Debug-Symbole – `DEBUG_<NAME>` innerhalb von `#ifdef DEBUG` (gleicher Name fuer ein oder mehrere Symbole). **Pflicht, wenn eine gleichnamige `.c`-Datei existiert** (`canbus.h` + `canbus.c` → `DEBUG_CANBUS`); ein auskommentiertes Symbol zaehlt als vorhanden
8. Version definieren – `<NAME>_MAJOR`, `_MINOR`, `_PATCH`, `_DEV`. Steht **genau einmal im Repository**, in einem Header (siehe unten)
9. Konstanten definieren – alle weiteren `#define`, auch die, die Typedefs benutzen (z. B. Arraygroessen). Weitere `#define`-Abschnitte mit eigener Ueberschrift stehen hier
10. Typedefs (Abschnittsname beschreibend, z. B. `Typedefines definieren`, `Definiere Statemaschine Typedefines`)
11. Definiere globale Variablen (`extern`)
12. Funktionen definieren – Prototypen
13. **Abschluss** – `#endif /* INC_<NAME>_H_ */` + Trennlinie

Die Abschnitte 7 bis 12 sind optional. Die Reihenfolge wird geprueft; fehlende Abschnitte sind erlaubt, die vorhandenen muessen aber in dieser Reihenfolge stehen. Typedef-Abschnitte werden an `Typedef` im Namen erkannt. Die Defines stehen vor den Typedefs, weil ein Typedef nur Defines nutzen kann, die vorher definiert sind. Umgekehrt duerfen Makros Typen nutzen, die erst danach definiert werden (z. B. `sizeof(Beispiel_TypeDef)`), da der Praeprozessor ein Makro erst dort einsetzt, wo es verwendet wird. Stehen Prototypen im Header, gehoeren sie in `Funktionen definieren`.

`<NAME>` ist der Dateiname in Grossbuchstaben ohne Endung (`canbus.h` → `INC_CANBUS_H_`, `CANBUS_MAJOR`, `DEBUG_CANBUS`).

Die Version gilt fuer das ganze Repository, nicht fuer eine Datei. Der Abschnitt `Version definieren` steht deshalb nur in einem Header, meist dem Hauptheader der Bibliothek (`canbus.h`, nicht `canbus_ringbuffer.h`). Fehlt er im Repository oder steht er mehrfach, ist das ein Befund. `_DEV` ist auf `develop` 1 und in `main` 0. Release-Ablauf und Tags stehen im [Documentation Style, Abschnitt 6](DOCUMENTATION_STYLE.md#6-versionierung).

Innerhalb von `#ifdef` / `#endif` wird mit einem Tab eingerueckt. Nicht benoetigte Debug-Symbole werden auskommentiert (`//	#define ...`).

### Vorlage

```c
//----------------------------------------------------------------------
// Titel	:	beispiel.h
//----------------------------------------------------------------------
// Sprache	:	C
// Datum	:	08.10.2026
// Autor	:	Diveturtle93
// Projekt	:	Beispiel
// Quelle	:
//----------------------------------------------------------------------

// Sicherheitssymbol
//----------------------------------------------------------------------
#pragma once
//----------------------------------------------------------------------

// Dateiheader definieren
//----------------------------------------------------------------------
#ifndef INC_BEISPIEL_H_
#define INC_BEISPIEL_H_
//----------------------------------------------------------------------

// Einfuegen der standard Include-Dateien
//----------------------------------------------------------------------
#include <stdint.h>
//----------------------------------------------------------------------

// Einfuegen der STM Include-Dateien
//----------------------------------------------------------------------

//----------------------------------------------------------------------

// Einfuegen der eigenen Include-Dateien
//----------------------------------------------------------------------

//----------------------------------------------------------------------

// Definiere Debug-Symbole
//----------------------------------------------------------------------
#ifdef DEBUG
	#define DEBUG_BEISPIEL
#endif
//----------------------------------------------------------------------

// Version definieren
//----------------------------------------------------------------------
#define BEISPIEL_MAJOR							1
#define BEISPIEL_MINOR							0
#define BEISPIEL_PATCH							0
#define BEISPIEL_DEV							1
//----------------------------------------------------------------------

// Konstanten definieren
//----------------------------------------------------------------------
#define TIMEOUT									1000						// Timeout in ms
#define DATEN_LAENGE							8							// Anzahl Datenbytes
//----------------------------------------------------------------------

// Definiere Beispiel Typedefines
//----------------------------------------------------------------------
typedef enum
{
	Aus,																	// 0 Ausgeschaltet
	An,																		// 1 Eingeschaltet
} beispielStates;
//----------------------------------------------------------------------
typedef struct
{
	uint32_t id;															// Identifier
	uint8_t len;															// Datenlaenge
	uint8_t daten[DATEN_LAENGE];											// Datenbytes
} Beispiel_TypeDef;
//----------------------------------------------------------------------
typedef union
{
	struct
	{
		uint8_t Bereit : 1;						// 0						// Signal Bereit
		uint8_t Fehler : 1;						// 1						// Signal Fehler
		uint8_t  : 6;							// 2 - 7
	};

	uint8_t status;								// 1 Byte
} beispielStatus;
//----------------------------------------------------------------------

// Definiere globale Variablen
//----------------------------------------------------------------------
extern Beispiel_TypeDef Main_Beispiel;										// Globale Beispiel-Variable
//----------------------------------------------------------------------

// Funktionen definieren
//----------------------------------------------------------------------
void initBeispiel (void);													// Beispiel initialisieren
uint8_t getBeispiel (uint8_t index);										// Wert zurueckgeben
//----------------------------------------------------------------------

#endif /* INC_BEISPIEL_H_ */
//----------------------------------------------------------------------
```

---

## 4. Quelldatei (`.c`)

Reihenfolge der Abschnitte:

1. **Dateikopf**
2. **Einfuegen der standard Include-Dateien**
3. **Einfuegen der STM Include-Dateien**
4. **Einfuegen der eigenen Include-Dateien** – der eigene Header steht hier
5. Variablen definieren – optional, Variablen nur fuer diese Datei (`static`)
6. Variablen einbinden – optional, globale (externe) Variablen: die im Header mit `extern` bekannt gemachten Variablen bzw. `extern`-Verweise auf Variablen anderer Dateien
7. Funktionen – jede Funktion als eigener Abschnitt

Die Reihenfolge wird geprueft (die erste Funktionsdefinition muss nach den Variablen-Abschnitten stehen).

### Variablen und Typedefs

- In einer `.c`-Datei werden **keine Typedefs** definiert, sie gehoeren in den Header.
- Variablen auf Dateiebene stehen **nur** in `Variablen definieren` oder `Variablen einbinden`, nicht in eigenen Abschnitten. Zur Gliederung (z. B. `Definiere Zellenarray Spannungen`) dienen [Unterabschnitte](#abschnitte).
- Empfohlen (nicht Pflicht, wird nicht geprueft): Jede Variable bekommt einen Zeilenkommentar, wofuer sie da ist (Spalte 77, siehe [Kommentare](#kommentare)). Bei mehrzeiligen Initialisierungen steht der Kommentar in der ersten Zeile.

```c
static uint8_t zaehler = 0;													// Interner Zaehler
const uint8_t tabelle[] =													// Umrechnungstabelle
{
	1, 2, 3,
};
```

In von STM32CubeMX erzeugten Dateien werden Typedefs und Variablen-Abschnitte nicht geprueft.

### Typen von Variablen

Der Typ jeder Variable muss im Projekt definiert sein. Sonst faellt ein Tippfehler oder ein umbenannter Typ erst beim Kompilieren auf:

```c
typedef struct
{
	uint16_t head;															// Kopf des Ringbuffers
} RingbufferCANBusTypeDef;

RingbufferTypeDef rxRing;													// Fehler: Typ heisst RingbufferCANBusTypeDef
```

Als definiert gelten:

- Standard-Typen von C (`int`, `char`, `unsigned long` usw.), `stdint.h` (`uint8_t` usw.) und weitere Typen der Standardbibliothek (`size_t`, `FILE` usw.),
- Typedefs im Projekt, einschliesslich HAL, CMSIS, Middleware und Submodule (`UART_HandleTypeDef`, `TaskHandle_t`),
- `struct <Name>`, `enum <Name>` und `union <Name>`, wenn der Tag im Projekt definiert oder vorwaerts deklariert ist.

Geprueft werden Variablen auf Dateiebene, lokale Variablen, struct-Member, Zaehler in `for` und benannte Parameter (keine Rueckgabetypen, keine Funktionszeiger). Der Befund nennt den aehnlichsten bekannten Typ. In von STM32CubeMX erzeugten Dateien wird nur der USER-CODE-Bereich geprueft.

### Includes

Jeder Include steht im passenden Abschnitt (gilt fuer `.h` und `.c`):

- **standard** – `<...>` und die Header der C-Standardbibliothek (`stdint.h`, `string.h`, …), auch wenn sie mit `"..."` eingebunden werden
- **STM** – HAL/CMSIS (`main.h`, `stm32*.h`), die von STM32CubeMX erzeugten Peripherie-Header (`can.h`, `spi.h`, `gpio.h`, …) und jeder Header im Projekt mit `USER CODE`-Markern
- **eigene** – alle anderen `"..."`-Includes, auch Bibliotheken, die nicht im Projektordner liegen (`millis.h`)

### Funktionsabschnitt

Jede Funktion bekommt einen beschreibenden Kommentar als Abschnittsname und wird von Trennlinien eingeschlossen:

```c
// <Was die Funktion macht>
//----------------------------------------------------------------------
<Rueckgabetyp> <name> (<Parameter>)
{
	...
}
//----------------------------------------------------------------------
```

Wird die Funktion nur bedingt uebersetzt, steht `#if` / `#ifdef` zwischen Trennlinie und Funktionskopf:

```c
// Flash Page ermitteln
//----------------------------------------------------------------------
#ifdef FLASH_PAGE
uint32_t GetPage (uint32_t address)
{
	...
}
#endif
//----------------------------------------------------------------------
```

### Vorlage

```c
//----------------------------------------------------------------------
// Titel	:	beispiel.c
//----------------------------------------------------------------------
// Sprache	:	C
// Datum	:	08.10.2026
// Autor	:	Diveturtle93
// Projekt	:	Beispiel
// Quelle	:
//----------------------------------------------------------------------

// Einfuegen der standard Include-Dateien
//----------------------------------------------------------------------

//----------------------------------------------------------------------

// Einfuegen der STM Include-Dateien
//----------------------------------------------------------------------
#include "main.h"
//----------------------------------------------------------------------

// Einfuegen der eigenen Include-Dateien
//----------------------------------------------------------------------
#include "beispiel.h"
//----------------------------------------------------------------------

// Variablen definieren
//----------------------------------------------------------------------
static uint8_t zaehler = 0;													// Interner Zaehler
//----------------------------------------------------------------------

// Variablen einbinden
//----------------------------------------------------------------------
Beispiel_TypeDef Main_Beispiel;												// Globale Beispiel-Variable
//----------------------------------------------------------------------

// Initialisiere Beispiel
//----------------------------------------------------------------------
void initBeispiel (void)
{
	// Variablen zuruecksetzen
	Main_Beispiel.id = 0;
	Main_Beispiel.len = 0;
	zaehler = 0;
}
//----------------------------------------------------------------------

// Gebe Wert anhand des Index zurueck
//----------------------------------------------------------------------
uint8_t getBeispiel (uint8_t index)
{
	uint8_t ret = 0;

	// Index auswerten
	switch (index)
	{
		case 0:
		{
			ret = Main_Beispiel.len;
			break;
		}
		default:
		{
			break;
		}
	}

	return ret;
}
//----------------------------------------------------------------------
```

---

## 5. Formatierung im Code

### Klammern und Kontrollstrukturen

- Allman-Stil fuer Funktionen, `if`, `else`, `for`, `while`, `switch`, `struct`, `enum`, `union`.
- Nach Schluesselwoertern ein Leerzeichen: `if (`, `for (`, `switch (`, `while (`, `return (`. `sizeof(...)` wird wie ein Funktionsaufruf ohne Leerzeichen geschrieben.
- `if` / `else` **immer** mit geschweiften Klammern.
- Ausnahme: Folgt auf ein `if`, `else if` oder `else` direkt ein einzelnes `return ...;`, sind keine Klammern noetig:
  ```c
  // Beende wenn CAN-Bus aktiv ist
  if (canIsActive)
  	return;

  // Anzahl Nachrichten im Ring zurueckgeben
  if (rxRing.head >= rxRing.tail)
  	return rxRing.head - rxRing.tail;
  else
  	return rxRing.size - (rxRing.tail - rxRing.head);
  ```
- Unterscheidet sich die Bedingung je nach Controller, stehen die alternativen `if`-Zeilen in `#if` / `#ifdef`-Zweigen. Die gemeinsame `{` folgt erst nach dem letzten `#endif`:
  ```c
  #if defined (STM32F1) || defined (STM32G0)
  	if (HAL_OK != HAL_FLASH_Program(FLASH_TYPEPROGRAM_DOUBLEWORD, address, tmp))
  #endif

  #ifdef STM32F7
  	if (HAL_OK != HAL_FLASH_Program(FLASH_TYPEPROGRAM_WORD, address, tmp))
  #endif
  	{
  		status |= FLASH_ERROR_WRITE;
  	}
  ```
- Ein Kommentar zu einem `else`-Zweig steht direkt in der Zeile ueber dem `else`.

```c
// CAN-Nachricht hat extended ID
if (msg->flags.extended == 1)
{
	header.IDE = CAN_ID_EXT;
}
// CAN-Nachricht hat standard ID
else
{
	header.IDE = CAN_ID_STD;
}
```

### `switch` / `case`

- Jeder `case` und `default` bekommt einen eigenen `{ }`-Block.
- Ausnahme: Besteht ein `case` oder `default` nur aus einem einzelnen `return ...;` oder `break;`, sind keine Klammern noetig (wie bei `if`):
  ```c
  switch (state)
  {
  	case STATE_OK:
  		return "OK";
  	case STATE_ERROR:
  		return "Error";
  	case STATE_IDLE:
  		break;
  	default:
  		return "Unbekannt";
  }
  ```
- Mehrere `case`-Marken mit gleichem Code stehen direkt untereinander; nur die **letzte** Marke bekommt den `{ }`-Block.
- `break;` steht **innerhalb** des Blocks.
- `default` ist immer vorhanden.
- Jeder Block endet mit `break;`, `return`, `continue` oder `goto`. Ausnahme: der letzte Block im `switch`.
- Gewolltes Durchfallen (Fall-through) ist erlaubt, muss aber als **letzte Zeile im Block** mit diesem Kommentar markiert werden:
  `// fall through - <Begruendung>`
  Die Schreibweise `fall through` erkennt auch GCC (`-Wimplicit-fallthrough`); hinter dem Bindestrich steht die deutsche Begruendung. Eine laengere Begruendung darf in den folgenden `//`-Zeilen weitergehen, die Markierung ist dann die erste Zeile dieses Kommentarblocks am Ende des Blocks. Ein `break;` nur innerhalb eines `if` zaehlt nicht – auch dann ist die Markierung noetig.
- Mehrere `case`-Marken direkt untereinander brauchen **keine** Markierung.

```c
switch (wert)
{
	case 1:
	case 2:
	{
		// Gemeinsamer Code fuer 1 und 2
		break;
	}
	case 5:
	{
		// Zusaetzlich Code von 3 ausfuehren
		vorbereiten();
		// fall through - Code von 3 ebenfalls ausfuehren
	}
	case 3:
	{
		// Code fuer 3
		break;
	}
	default:
	{
		break;
	}
}
```

### Funktionen

- Deklaration und Definition: Leerzeichen zwischen Name und Klammer – `void setState (uint8_t state)`.
- Aufrufe ohne Leerzeichen – `setState(Ready);`, `HAL_GetTick();`.
- Keine Parameter → `(void)`.

### Kommentare

- **Blockkommentar** ueber einer Anweisungsgruppe: eigene Zeile, gleiche Einrueckung wie der Code.
- Eine leere Kommentarzeile (`//` ohne Text) steht nur innerhalb eines mehrzeiligen Kommentarblocks.
- **Zeilenkommentar** hinter Code (Defines, Enum-Werte, Struct-Member, Variablen, Prototypen): mit Tabs auf **Spalte 77** (Tabbreite 4) ausgerichtet. Ist der Code laenger, reicht ein Tab.
- **Positionsangabe** in `union` und `enum`: Member duerfen vor der Beschreibung einen ersten Kommentar mit Tabs auf **Spalte 49** haben, die Beschreibung folgt auf Spalte 77.
  - `union`: Bitposition (`// 4`, `// 2 - 7`) bzw. Groesse des Gesamtwerts (`// 1 Byte`). Unbenannte Bits und der Gesamtwert haben nur die Positionsangabe.
  - `enum`: Zahlenwert (`// 3`).
- Enum-Werte werden im Kommentar mit ihrem Zahlenwert begonnen: `// 3 Anlasser betaetigt`, oder der Zahlenwert steht als Positionsangabe auf Spalte 49.

```c
	Anlassen,									// 3						// Anlasser betaetigt
		uint8_t Wakeup : 1;						// 7						// Signal Wakeup
	uint8_t systeminput;						// 1 Byte
```

### Leerzeilen

- Zwischen logischen Bloecken innerhalb einer Funktion eine Leerzeile.
- Vor `break;` bzw. `return` darf zur Trennung eine Leerzeile stehen.

### `#define`

- Der Wert steht mit Tabs auf **Spalte 49** (Tabbreite 4). Ist der Name laenger, reicht ein Tab.
- Name in `GROSSBUCHSTABEN` mit `_`.
- Ausnahme: Pin-Defines aus CubeMX behalten ihre Endung `_Pin` bzw. `_Port` (`LED_Pin`, `LED_GPIO_Port`).

```c
#define TIMEOUT									1000						// Timeout in ms
#define WRCFG									0b00000000001				// Write Configuration
```

---

## 6. Namenskonventionen

| Element | Konvention | Beispiel |
|---|---|---|
| Dateien | Kleinbuchstaben, `_` als Trenner | `canbus_ringbuffer.c` |
| Include-Guard | `INC_<DATEI>_H_` | `INC_CANBUS_H_` |
| Versions-Defines | `<DATEI>_MAJOR/_MINOR/_PATCH/_DEV`, einmal im Repository | `MILLIS_MAJOR` |
| Konstanten / Makros | `GROSSBUCHSTABEN` | `ERROR_RESET` |
| Pin-Defines (CubeMX) | `<NAME>_Pin`, `<NAME>_GPIO_Port` | `LED_Pin`, `LED_GPIO_Port` |
| Funktionen | camelCase, Modul-Praefix erlaubt, Woerter duerfen mit `_` getrennt werden | `setState`, `CANwrite`, `ADC_Bremsdruck`, `ltc6811_write` |
| Variablen | camelCase | `sizeRxBuffer`, `timeError` |
| Globale Instanzen | `Main_<Name>` bzw. `<Modul>_<Name>` | `Main_Statemaschine` |
| Struct-Typen | `<Name>_TypeDef` / `<Name>TypeDef` | `CAN_PaketTypeDef` |
| Enum-Werte | PascalCase oder `GROSS_MIT_UNTERSTRICH` | `ReadyToDrive`, `RX_SIZE_8` |

Geprueft werden nur die Namen von `#define` (`GROSSBUCHSTABEN`), die uebrigen Konventionen nicht.

---

## 7. Automatische Pruefung

Das Skript [tools/c_stylecheck.py](../tools/c_stylecheck.py) prueft C-Dateien gegen diesen Standard. Aufruf, Reports, Ausschluesse und Projekteinstellungen sind in [tools/README.md](../tools/README.md) beschrieben.

---

## 8. Checkliste

- [ ] Dateikopf vollstaendig (Titel, Sprache, Datum, Autor, Projekt, Quelle), ohne Version
- [ ] Alle Pflichtabschnitte vorhanden und in der richtigen Reihenfolge
- [ ] Leere Include-Abschnitte trotzdem angelegt
- [ ] `.c`: keine Typedefs, Variablen nur in `Variablen definieren` / `Variablen einbinden`, moeglichst mit Kommentar
- [ ] `.h`: Alle Defines vor den Typedefs (`Version definieren`, dann `Konstanten definieren`)
- [ ] Typen aller Variablen und Parameter im Projekt definiert
- [ ] `.h`: `#pragma once` **und** Include-Guard `INC_<NAME>_H_`
- [ ] Versions-Defines genau einmal im Repository, in einem Header
- [ ] Jede Funktion mit Beschreibungskommentar und Trennlinien
- [ ] Tabs statt Leerzeichen, Allman-Klammern
- [ ] `case`-Bloecke mit `{ }`, `default` vorhanden
- [ ] Kommentare deutsch, ohne Umlaute
- [ ] Kein Doxygen, kein `extern "C"`
