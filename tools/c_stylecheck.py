#!/usr/bin/env python3
#-----------------------------------------------------------------------
# Titel		:	c_stylecheck.py
#-----------------------------------------------------------------------
# Sprache	:	Python
# Datum		:	08.10.2026
# Autor		:	Diveturtle93
# Projekt	:	Coding_Styleguide
# Quelle	:
#-----------------------------------------------------------------------

# Beschreibung
#-----------------------------------------------------------------------
# Prueft C-Dateien (.c/.h) gegen docs/C_CODING_STYLE.md
# Aufruf:
#   py tools/c_stylecheck.py                      -> alle Ordner neben diesem Repo
#   py tools/c_stylecheck.py ../STM32_Canbus      -> einzelner Ordner
#   py tools/c_stylecheck.py ../EAuto_* ../IMD_*  -> beliebige Ordner / Glob-Muster
#   py tools/c_stylecheck.py ../STM32_Millis/millis.h   -> einzelne Datei
#   py tools/c_stylecheck.py -r                   -> Reports nach reports/c/<JJJJMMTT>_<Projekt>.txt
#   py tools/c_stylecheck.py -r -f                -> Reports nur fuer Projekte mit Befunden
#   py tools/c_stylecheck.py -c                   -> alle C-Reports in reports/c/ loeschen
#   py tools/c_stylecheck.py -c out               -> alle C-Reports in out/c/ loeschen
#
# Optionen:
#   -r / --report [DIR]  je Projekt einen Report DIR/c/<JJJJMMTT>_<Projekt>.txt schreiben (Standard: reports/),
#                        dazu immer DIR/c/<JJJJMMTT>_Uebersicht.txt ueber alle Projekte
#   -f / --findings-only mit -r nur Reports fuer Projekte mit Befunden schreiben, die Uebersicht
#                        enthaelt weiterhin alle Projekte
#   -c / --clean [DIR]   alle Reports DIR/c/<JJJJMMTT>_*.txt loeschen, egal welches Projekt
#                        (Standard: reports/), mit -r werden danach neue Reports geschrieben
#   -q / --quiet         Dateien ohne Befund nicht anzeigen
#   -s / --summary       nur Zusammenfassung je Kategorie
#   -x / --exclude REGEX zusaetzliche Pfade ausschliessen (mehrfach moeglich)
#   --no-default-exclude HAL/CMSIS-Dateien und Submodule mitpruefen, CubeMX-Dateien vollstaendig pruefen
#
# Ein Projekt ist jeder Ordner, der als Pfad angegeben oder per Glob gefunden wird.
#
# Automatisch uebersprungen: .git/, Drivers/, Middlewares/, CMSIS/, Debug/, Release/, build/,
# HAL-/Startup-/System-Dateien, syscalls.c, sysmem.c sowie Git-Submodule aus der .gitmodules
# des Projekts (werden separat geprueft).
#
# Von STM32CubeMX generierte Dateien ("USER CODE BEGIN") werden nur zwischen
# USER CODE BEGIN und USER CODE END geprueft, ohne den Bereich "Header" und ohne
# Pruefungen der Dateistruktur (Kopfblock, Abschnitte, Header, Debug-Symbole, Reihenfolge, Include-Abschnitte,
# Typedefs und Variablen ausserhalb der Variablen-Abschnitte).
#
# Projekt-Einstellungen (optional): Datei .stylecheck im Projektordner (gemeinsam mit py_stylecheck.py)
#   [stylecheck]                  -> gilt fuer C und Python
#   exclude = Lib, Test           -> diese Ordner zusaetzlich ausschliessen
#   [c]                           -> gilt nur fuer C, ergaenzt [stylecheck]
#   include = Core, Application   -> nur diese Ordner pruefen
#   types = uart_status           -> zusaetzlich bekannte Typen (nicht im Projekt definiert)
# Ordner oder Dateien werden relativ zum Projektordner angegeben, mehrere mit Komma getrennt.
#
# Typen von Variablen und Parametern: Gemeldet wird ein Typ, den es im Projekt nicht gibt (z. B. Tippfehler),
# mit dem aehnlichsten bekannten Typ. Bekannt sind Standard-Typen, Typedefs und struct/enum/union-Tags aus
# allen .c/.h-Dateien des Projekts, auch aus den ausgeschlossenen (HAL, CMSIS, Middleware, Submodule).
# Ohne HAL-Header im Projekt gelten bekannte Namen von HAL/LL, CMSIS, FatFs und FreeRTOS.
#
# Rueckgabewert: 0 = keine Befunde, 1 = Befunde vorhanden, 2 = keine Dateien gefunden
#-----------------------------------------------------------------------

# Einfuegen der standard Module
#-----------------------------------------------------------------------
import difflib
import glob
import os
import re
import sys
#-----------------------------------------------------------------------

# Einfuegen der externen Module
#-----------------------------------------------------------------------

#-----------------------------------------------------------------------

# Einfuegen der eigenen Module
#-----------------------------------------------------------------------
from stylecheck_common import (
	COMMENT_COL,
	VALUE_COL,
	VERSION_KEYS,
	Issue,
	Language,
	checkBlankLines,
	checkHead,
	checkOrder,
	checkRequiredSections,
	checkSectionForm,
	checkVarSections,
	debugSections,
	projectList,
	readLines,
	run,
	sectionEnd,
	sectionName,
	short,
	tabcol,
)
#-----------------------------------------------------------------------

# Definiere Debug-Symbole
#-----------------------------------------------------------------------
DEBUG_C_STYLECHECK								= False
#-----------------------------------------------------------------------

# Konstanten definieren
#-----------------------------------------------------------------------
SEP												= "//" + "-" * 70			# Trennlinie, 72 Zeichen

# Generierte bzw. fremde Dateien (STM32CubeMX, HAL, CMSIS, Build-Ausgaben)
DEFAULT_EXCLUDE									= [
	r"[\\/]\.git[\\/]",
	r"[\\/](Drivers|Middlewares|CMSIS|Debug|Release|build)[\\/]",
	r"stm32\w*_hal(?!_msp\.c$)",
	r"system_stm32",
	r"startup_",
	r"syscalls\.c$",
	r"sysmem\.c$",
]

INC_SECTIONS									= [
	"// Einfuegen der standard Include-Dateien",
	"// Einfuegen der STM Include-Dateien",
	"// Einfuegen der eigenen Include-Dateien",
]
GUARD_SECTION									= "// Sicherheitssymbol"
DEBUG_SECTION									= "// Definiere Debug-Symbole"
DEBUG_NAME										= re.compile(r"//\s*\w+\s+Debug[\s-]*Symbol", re.I)
VERSION_SECTION									= "// Version definieren"	# genau einmal im Projekt
VAR_SECTION										= "// Variablen definieren"
VAR_INC_SECTION									= "// Variablen einbinden"
CONST_SECTION									= "// Konstanten definieren"
GLOBAL_SECTION									= "// Definiere globale Variablen"
FUNC_SECTION									= "// Funktionen definieren"
HEADER_SECTIONS									= [GUARD_SECTION, "// Dateiheader definieren", VERSION_SECTION, CONST_SECTION, GLOBAL_SECTION, FUNC_SECTION]
TYPEDEF_NAME									= re.compile(r"//.*typedef", re.I)
FIXED_SECTIONS									= set(INC_SECTIONS + HEADER_SECTIONS + [DEBUG_SECTION, VAR_SECTION, VAR_INC_SECTION])
FUNC_HEAD										= re.compile(r"^(?!typedef|#|return|else|static inline)[A-Za-z_][\w\s\*]*?\b([A-Za-z_]\w*)(\s*)\((.*)\)\s*(;)?\s*$")
KEYWORDS										= {"if", "for", "while", "switch", "return", "sizeof", "else"}

# CubeMX-Dateien: nur Bereiche zwischen USER CODE BEGIN/END pruefen
USER_CODE										= re.compile(r"^\s*/\*\s*USER CODE (BEGIN|END)\s+(.+?)\s*\*/\s*$")
USER_CODE_SKIP									= {"Header"}
MARKER_CAT										= "USER CODE Marker"

# Include-Abschnitt je Art des Includes
INC_KIND										= {"standard": INC_SECTIONS[0], "stm": INC_SECTIONS[1], "eigene": INC_SECTIONS[2]}
INCLUDE											= re.compile(r'^\s*#\s*include\s*([<"])([^>"]+)[>"]')
STD_HEADER										= re.compile(r"^(assert|complex|ctype|errno|fenv|float|inttypes|iso646|limits|locale|math|setjmp|signal|stdalign|stdarg|stdatomic|stdbool|stddef|stdint|stdio|stdlib|stdnoreturn|string|tgmath|threads|time|uchar|wchar|wctype)\.h$")
STM_HEADER										= re.compile(r"^(main|stm32\w*|core_cm\w*|cmsis\w*|adc|can|crc|dac|dcmi|dma|dma2d|eth|fatfs|fmc|fsmc|gpio|i2c|i2s|iwdg|lptim|ltdc|quadspi|rng|rtc|sai|sdio|sdmmc|spi|tim|uart|usart|usb_device|usb_host|usbd_\w+|wwdg)\.h$", re.I)

# Pruefungen der Dateistruktur, im USER-CODE-Modus nicht sinnvoll
FILE_CATS										= {"Kopfblock", "Abschnitte", "Header", "Debug-Symbole", "Reihenfolge", "Include im falschen Abschnitt", "Include ausserhalb der Include-Abschnitte",
													"Typedef in .c-Datei", "Variable ausserhalb der Variablen-Abschnitte"}

# switch/case: Fall-through-Markierung (FALLTHROUGH_LIKE: abweichend geschrieben), Blockende, case-Marke
FALLTHROUGH										= re.compile(r"^\s*// fall through - \S.*$")
FALLTHROUGH_LIKE								= re.compile(r"^\s*(//\s*fall(s)?[ -]?thr(ough|u)\b.*|__attribute__\s*\(\(\s*fallthrough\s*\)\)\s*;.*|\[\[fallthrough\]\]\s*;.*)$", re.I)
TERMINATOR										= re.compile(r"^\s*(break|continue|return\b.*|goto\s+\w+)\s*;$")
LABEL											= re.compile(r"^\s*(case\b.*|default\s*):\s*$")

# Typen von Variablen und Parametern: Standard-Typen, im Projekt definierte Typen (inkl. HAL/CMSIS/Middleware unter Drivers/ usw.)
TYPE_CAT										= "Typ nicht definiert"
BUILTIN_WORDS									= {"void", "char", "short", "int", "long", "float", "double", "signed", "unsigned", "_Bool", "bool"}
STD_TYPES										= {"size_t", "ssize_t", "ptrdiff_t", "wchar_t", "wint_t", "max_align_t", "char16_t", "char32_t", "intptr_t", "uintptr_t",
													"intmax_t", "uintmax_t", "va_list", "FILE", "fpos_t", "time_t", "clock_t", "div_t", "ldiv_t", "lldiv_t", "sig_atomic_t",
													"jmp_buf", "mbstate_t", "struct tm"}
STD_TYPE										= re.compile(r"^u?int(_least|_fast)?(8|16|32|64)_t$")
QUALIFIERS										= {"static", "extern", "const", "volatile", "register", "auto", "inline", "restrict", "_Atomic", "_Thread_local",
													"__IO", "__I", "__O", "__IM", "__OM", "__IOM", "__weak", "__WEAK", "__packed", "__PACKED", "__inline", "__INLINE",
													"__STATIC_INLINE", "__STATIC_FORCEINLINE", "__ALIGN_BEGIN", "__ALIGN_END", "__USED", "__UNUSED", "__NO_RETURN"}
DECL_KEYWORDS									= KEYWORDS | {"goto", "case", "default", "break", "continue", "do", "typedef", "asm", "__asm"}
TYPE_FUNC_HEAD									= re.compile(r"^(?!typedef\b)[A-Za-z_][\w\s\*]*?\b([A-Za-z_]\w*)\s*\((.*)\)\s*;?\s*$")

# Typen von HAL, CMSIS, FatFs und FreeRTOS, falls deren Header nicht im Projekt liegen (Bibliotheken ohne Drivers/)
HAL_MARKER										= "HAL_StatusTypeDef"		# im Projekt gefunden -> HAL-Header vorhanden
EXT_TYPES										= {"IRQn_Type", "FlagStatus", "ITStatus", "FunctionalState", "ErrorStatus",
													"FATFS", "FIL", "DIR", "FILINFO", "FRESULT", "BYTE", "WORD", "DWORD", "QWORD", "UINT", "TCHAR", "FSIZE_t", "LBA_t",
													"TaskHandle_t", "QueueHandle_t", "SemaphoreHandle_t", "TimerHandle_t", "EventGroupHandle_t", "StreamBufferHandle_t",
													"MessageBufferHandle_t", "TickType_t", "BaseType_t", "UBaseType_t", "StackType_t", "TaskFunction_t"}
EXT_TYPE										= re.compile(r"^(HAL|LL|GPIO|UART|USART|CAN|FDCAN|SPI|I2C|I2S|TIM|ADC|DAC|DMA|DMA2D|RTC|IWDG|WWDG|CRC|RNG|ETH|FLASH|PWR|RCC|"
													r"EXTI|SAI|SD|MMC|SDMMC|QSPI|OSPI|LTDC|DSI|DCMI|FMC|FSMC|SDRAM|SRAM|NOR|NAND|LPTIM|USB|PCD|HCD|USBD|USBH|CEC|SPDIFRX|"
													r"JPEG|MDIOS|SMBUS|IRDA|SMARTCARD|HASH|CRYP|DFSDM|NVIC|SCB|SysTick|CoreDebug|DBGMCU|SYSCFG|MPU|ITM|DWT|TPI|FPU)_\w*TypeDef$"
													r"|^os[A-Z]\w*$")
#-----------------------------------------------------------------------

# Variablen definieren
#-----------------------------------------------------------------------

#-----------------------------------------------------------------------

# Naechste nicht leere Zeile nach Zeile i
#-----------------------------------------------------------------------
def nextCodeLine (lines, i):
	return next((x for x in lines[i + 1:] if x.strip()), "")
#-----------------------------------------------------------------------

# Naechste Anweisung nach Zeile i: ueberspringt Leerzeilen, Kommentare, Praeprozessor-
# Zeilen und alternative if-Bedingungen in #if/#ifdef-Zweigen
#-----------------------------------------------------------------------
def nextStatement (L, i):
	crossedPp = False
	for x in L[i + 1:]:
		s = stripCode(x).strip()
		if not s:
			continue
		if s.startswith("#"):
			crossedPp = True
			continue
		if crossedPp and re.match(r"(if|else if)\s*\(.*\)$", s):
			continue
		return s
	return ""
#-----------------------------------------------------------------------

# Code ohne Strings, Zeichenkonstanten und //-Kommentar
#-----------------------------------------------------------------------
def stripCode (l):
	code = re.sub(r'"(\\.|[^"])*"', '""', l)
	code = re.sub(r"'(\\.|[^'])*'", "''", code)
	return re.sub(r"//.*", "", code).rstrip()
#-----------------------------------------------------------------------

# Zeilenindex der schliessenden } zum Block, dessen { in Zeile start steht, None = nicht gefunden
#-----------------------------------------------------------------------
def blockEnd (L, start):
	depth = 0
	for j in range(start, len(L)):
		c = stripCode(L[j])
		depth += c.count("{") - c.count("}")
		if depth == 0:
			return j
	return None
#-----------------------------------------------------------------------

# case-Block: break gehoert in den Block, ohne break/return vor der naechsten Marke braucht er "// fall through - <Begruendung>"
#-----------------------------------------------------------------------
def checkCaseBlock (L, i, add):
	start = next(j for j in range(i + 1, len(L)) if L[j].strip())
	end = blockEnd(L, start)
	if end is None:
		return

	after = stripCode(next((x for x in L[end + 1:] if stripCode(x).strip()), "")).strip()
	if re.match(r"break\s*;$", after):
		add(i + 1, "break ausserhalb des case-Blocks", short(L[i]))
		return
	if not LABEL.match(after):
		return

	body = [j for j in range(start + 1, end) if L[j].strip()]
	if not body:
		return

	# Markierung im Kommentarblock am Ende des Blocks, die Begruendung darf ueber mehrere Zeilen gehen
	k = len(body)
	while k > 0 and L[body[k - 1]].strip().startswith("//"):
		k -= 1
	if any(FALLTHROUGH.match(L[j]) for j in body[k:]):
		return
	like = next((j for j in body[k:] + body[-1:] if FALLTHROUGH_LIKE.match(L[j])), None)
	if like is not None:
		add(like + 1, "Fall-through-Markierung nicht '// fall through - <Begruendung>'", short(L[like]))
		return

	lastCode = next((stripCode(L[j]) for j in reversed(body) if stripCode(L[j]).strip()), "")
	if TERMINATOR.match(lastCode):
		return
	add(i + 1, "case ohne break (Fall-through nicht markiert)", short(L[i]))
#-----------------------------------------------------------------------

# Funktion endet mit Trennlinie (#endif und Leerzeilen davor erlaubt), danach Leerzeile oder Dateiende
# i: Zeile des Funktionskopfs, die { steht in der naechsten nicht leeren Zeile
#-----------------------------------------------------------------------
def checkFuncEnd (L, i, name, add):
	start = next(j for j in range(i + 1, len(L)) if L[j].strip())
	end = blockEnd(L, start)
	if end is None:
		return

	k = next((j for j in range(end + 1, len(L)) if L[j].strip() and not re.match(r"\s*#\s*endif\b", L[j])), None)
	if k is None or L[k] != SEP:
		add(end + 1, "Funktion ohne Trennlinie danach", f"Funktion {name} ()")
	elif k + 1 < len(L) and L[k + 1].strip():
		add(k + 2, "Abschnitte", f"keine Leerzeile nach Funktion {name} ()")
#-----------------------------------------------------------------------

# Art eines Includes: <...> oder C-Standardbibliothek = standard, HAL/CMSIS/CubeMX = stm, sonst eigene
# genHeaders: Basisnamen (klein) der von CubeMX erzeugten .h-Dateien im Projekt
#-----------------------------------------------------------------------
def includeKind (bracket, header, genHeaders):
	base = os.path.basename(header)
	if bracket == "<" or STD_HEADER.match(base):
		return "standard"
	if STM_HEADER.match(base) or base.lower() in genHeaders:
		return "stm"
	return "eigene"
#-----------------------------------------------------------------------

# Jeder Include steht im passenden Include-Abschnitt
#-----------------------------------------------------------------------
def checkIncludes (L, genHeaders, add):
	owner = {}
	for i in range(len(L) - 1):
		if L[i].startswith("// ") and L[i + 1] == SEP:
			end = next((j for j in range(i + 2, len(L)) if L[j] == SEP), len(L))
			for j in range(i + 2, end):
				owner.setdefault(j, L[i])

	for i, l in enumerate(L):
		m = INCLUDE.match(l)
		if not m:
			continue
		want = INC_KIND[includeKind(m.group(1), m.group(2), genHeaders)]
		have = owner.get(i)
		if have == want:
			continue
		if have in INC_SECTIONS:
			add(i + 1, "Include im falschen Abschnitt", f"{short(l)}  ->  '{sectionName(want)}'")
		else:
			add(i + 1, "Include ausserhalb der Include-Abschnitte", short(l))
#-----------------------------------------------------------------------

# Header mit passender .c-Datei braucht 'Definiere Debug-Symbole' mit DEBUG_<NAME> in #ifdef DEBUG
# pos: Zeilenindizes der Debug-Abschnitte, falsch benannte zaehlen mit (Name wird unter "Abschnitte" gemeldet)
#-----------------------------------------------------------------------
def checkDebugSymbols (L, pos, name, add):
	if not pos:
		add(0, "Debug-Symbole", f"Abschnitt '{sectionName(DEBUG_SECTION)}' fehlt (passende .c-Datei vorhanden)")
		return

	checkSectionForm(L, pos[0], SEP, add, subsection)
	sym =re.compile(rf"^(//)?\s*#define\s+DEBUG_{name}\b")
	inIfdef = False
	for l in L[pos[0] + 1:]:
		if re.match(r"#ifdef\s+DEBUG\b", l):
			inIfdef = True
		elif l.startswith("#endif"):
			inIfdef = False
		elif inIfdef and sym.match(l):
			return
	add(pos[0] + 1, "Debug-Symbole", f"'#define DEBUG_{name}' innerhalb von '#ifdef DEBUG' fehlt")
#-----------------------------------------------------------------------

# Zeilenindizes der Typedef-Abschnitte (beschreibender Name mit "Typedef", danach Trennlinie)
#-----------------------------------------------------------------------
def typedefSections (L):
	return [i for i, l in enumerate(L[:-1]) if TYPEDEF_NAME.match(l) and L[i + 1] == SEP]
#-----------------------------------------------------------------------

# Block ab Zeile j ist eine Funktion (#if / #ifdef davor erlaubt)
#-----------------------------------------------------------------------
def isFuncBlock (L, j):
	while j < len(L) and re.match(r"\s*#\s*(if|ifdef|ifndef|elif)\b", L[j]):
		j += 1
	if j >= len(L):
		return False
	fm = FUNC_HEAD.match(stripCode(L[j]))
	return bool(fm) and fm.group(1) not in KEYWORDS and fm.group(4) is None and nextCodeLine(L, j).strip() == "{"
#-----------------------------------------------------------------------

# Unterabschnitt: Zeile k direkt nach einer schliessenden Trennlinie setzt den Abschnitt fort
# - "typedef" (weitere Typdefinition, Kommentarzeilen davor erlaubt) oder
# - "// <Name>" mit Trennlinie danach, kein Abschnitt mit festem Namen und keine Funktion
# Rueckgabe: Zeilenindex der oeffnenden Trennlinie des Unterabschnitts, sonst None
#-----------------------------------------------------------------------
def subsection (L, k):
	j = k
	while j < len(L) and L[j].startswith("//") and L[j] != SEP:
		j += 1
	if j < len(L) and L[j].startswith("typedef"):
		return k - 1
	if k + 1 < len(L) and L[k + 1] == SEP and re.match(r"// \S", L[k]) and L[k] != SEP \
			and L[k] not in FIXED_SECTIONS and not isFuncBlock(L, k + 2):
		return k + 1
	return None
#-----------------------------------------------------------------------

# .c-Datei: keine Typedefs, Variablen auf Dateiebene nur in den Variablen-Abschnitten
#-----------------------------------------------------------------------
def checkCVariables (L, add):
	# Zeilen innerhalb der Variablen-Abschnitte, inkl. Unterabschnitte
	allowed = set()
	for i, l in enumerate(L):
		if l in (VAR_SECTION, VAR_INC_SECTION) and i + 1 < len(L) and L[i + 1] == SEP:
			end = sectionEnd(L, i + 1, SEP, subsection)
			allowed.update(range(i + 2, len(L) if end is None else end))

	depth = 0
	inBlock = False
	for i, l in enumerate(L):
		# /* */-Kommentare (CubeMX) ueberspringen
		if inBlock:
			inBlock = "*/" not in l
			continue
		code = re.sub(r"/\*.*?\*/", "", stripCode(l))
		if "/*" in code:
			inBlock = True
			code = code[:code.index("/*")]

		atTop = depth == 0
		depth += code.count("{") - code.count("}")
		s = code.strip()
		if not atTop or not s or s.startswith("#") or (i > 0 and L[i - 1].rstrip().endswith("\\")):
			continue

		if re.match(r"typedef\b", s):
			add(i + 1, "Typedef in .c-Datei", short(l))
			continue

		# Variable: Typ und Name, danach '=' oder ';', vor dem '=' keine Klammern
		head = s.split("=", 1)[0]
		if not re.match(r"[A-Za-z_][\w\s\*]*?[\s\*]\**[A-Za-z_]\w*\s*(\[[^\]]*\]\s*)*;?$", head):
			continue
		if "=" not in s and not s.endswith(";"):
			continue
		if i not in allowed:
			add(i + 1, "Variable ausserhalb der Variablen-Abschnitte", short(l))
#-----------------------------------------------------------------------

# Alle in einem C-Text definierten Typen: Typedefs (struct/enum/union, einfache Typen, Funktionszeiger)
# und Tags mit Definition oder Vorwaertsdeklaration ("struct Name", "enum Name", "union Name")
#-----------------------------------------------------------------------
def typeNames (text):
	text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
	text = re.sub(r"//[^\n]*", "", text)
	text = re.sub(r'"(\\.|[^"\\\n])*"', '""', text)
	names = {f"{m.group(1)} {m.group(2)}" for m in re.finditer(r"\b(struct|enum|union)\s+([A-Za-z_]\w*)\s*[{;]", text)}
	for m in re.finditer(r"\btypedef\b", text):
		# Bis zum ; ausserhalb von Klammern
		depth = 0
		j = m.end()
		while j < len(text) and not (text[j] == ";" and depth == 0):
			depth += (text[j] in "{(") - (text[j] in "})")
			j += 1
		body = text[m.end():j]

		fp = re.search(r"\(\s*\*\s*([A-Za-z_]\w*)\s*\)", body)
		if "}" not in body and fp:
			names.add(fp.group(1))
			continue
		decl = body[body.rindex("}") + 1:] if "}" in body else body
		decl = re.sub(r"__attribute__\s*\(\(.*?\)\)|\[[^\]]*\]", " ", decl)
		for part in decl.split(","):
			ids = re.findall(r"[A-Za-z_]\w*", part)
			if ids:
				names.add(ids[-1])
	return names
#-----------------------------------------------------------------------

# Typen aller .c/.h-Dateien unterhalb eines Ordners, inkl. ausgeschlossener (HAL, CMSIS, Submodule)
#-----------------------------------------------------------------------
def projectTypes (base):
	names = set()
	for p in glob.glob(os.path.join(base, "**", "*.[ch]"), recursive=True):
		with open(p, "rb") as f:
			names |= typeNames(f.read().decode("utf-8", errors="replace"))
	return names
#-----------------------------------------------------------------------

# Typ einer Deklaration "Typ Name" (ohne Initialisierung), None = keine Deklaration
# Rueckgabe: "uint8_t", "unsigned int", "struct Name", ...
#-----------------------------------------------------------------------
def declType (head):
	head = re.sub(r"__attribute__\s*\(\(.*\)\)|\[[^\]]*\]", " ", head)
	head = re.sub(r":\s*\w+\s*$", "", head)									# Bitfeld
	if not re.fullmatch(r"[\w\s\*]+", head):
		return None
	words = [w for w in re.findall(r"\b[A-Za-z_]\w*", head) if w not in QUALIFIERS]
	if len(words) < 2 or any(w in DECL_KEYWORDS for w in words):
		return None
	words = words[:-1]
	if words[0] in ("struct", "enum", "union"):
		return " ".join(words) if len(words) == 2 else None
	if all(w in BUILTIN_WORDS for w in words):
		return " ".join(words)
	return words[0] if len(words) == 1 else None
#-----------------------------------------------------------------------

# Typ bekannt: Standard-Typ, im Projekt definiert oder (ohne HAL-Header im Projekt) Typ von HAL/CMSIS/FatFs/FreeRTOS
#-----------------------------------------------------------------------
def typeAllowed (t, known):
	if all(w in BUILTIN_WORDS for w in t.split()) or t in STD_TYPES or STD_TYPE.match(t) or t in known:
		return True
	return HAL_MARKER not in known and (t in EXT_TYPES or bool(EXT_TYPE.match(t)))
#-----------------------------------------------------------------------

# Typ von Variablen (Dateiebene, lokal, struct-Member, for-Schleife) und Parametern ist im Projekt definiert
# known: Typen im Projekt und Eintraege aus [c] types, Befund mit dem aehnlichsten bekannten Typ
#-----------------------------------------------------------------------
def checkTypes (L, known, add):
	# Befund, wenn die Deklaration einen unbekannten Typ hat
	def check (head, i):
		t = declType(head)
		if t is None or typeAllowed(t, known):
			return
		similar = difflib.get_close_matches(t, known, n=1, cutoff=0.7)
		hint = f" (aehnlich: {similar[0]})" if similar else ""
		add(i + 1, TYPE_CAT, f"{t}{hint}: {short(L[i])}")

	depth = 0
	inBlock = False
	stmtStart = True														# naechste Codezeile beginnt eine Anweisung
	for i, l in enumerate(L):
		# /* */-Kommentare (CubeMX) ueberspringen
		if inBlock:
			if "*/" not in l:
				continue
			inBlock = False
			l = l[l.index("*/") + 2:]
		code = re.sub(r"/\*.*?\*/", " ", stripCode(l))
		if "/*" in code:
			inBlock = True
			code = code[:code.index("/*")]
		s = code.strip()
		if not s or s.startswith("#") or (i > 0 and L[i - 1].rstrip().endswith("\\")):
			continue

		atTop = depth == 0
		depth += s.count("{") - s.count("}")
		start = stmtStart
		stmtStart = s[-1] in ";{}:"

		# Parameter von Funktionsdefinitionen und Prototypen, unbenannte Parameter und Funktionszeiger nicht
		fm = TYPE_FUNC_HEAD.match(code) if atTop and start else None
		if fm and fm.group(1) not in KEYWORDS:
			if "(" not in fm.group(2):
				for p in fm.group(2).split(","):
					check(p, i)
			continue

		fl = re.search(r"\bfor\s*\(([^;]*);", s)
		if fl:
			check(re.split(r"[=,]", fl.group(1), maxsplit=1)[0], i)
		elif start and (s.endswith(";") or "=" in s):
			check(re.split(r"[=,;]", s, maxsplit=1)[0], i)
#-----------------------------------------------------------------------

# Positionen der bekannten Abschnitte fuer die Reihenfolgepruefung
#-----------------------------------------------------------------------
def orderAnchors (L, isHeader, guard, firstFunc):
	anchors = []

	# Erste Zeile, auf die pred zutrifft, als Anker eintragen
	def first (pred, rank, label):
		pos = next((i for i, l in enumerate(L) if pred(l)), None)
		if pos is not None:
			anchors.append((pos, rank, label))

	first(lambda l: re.match(r"//\s*Titel\b", l), 0, "Kopfblock")
	if isHeader:
		first(lambda l: l == "#pragma once", 1, sectionName(GUARD_SECTION))
		first(lambda l: l == f"#ifndef {guard}", 2, "Dateiheader definieren")
	for k, s in enumerate(INC_SECTIONS):
		first(lambda l, s=s: l == s, 3 + k, sectionName(s))

	if isHeader:
		first(lambda l: l == DEBUG_SECTION or DEBUG_NAME.match(l), 6, sectionName(DEBUG_SECTION))
		first(lambda l: l == VERSION_SECTION, 7, sectionName(VERSION_SECTION))

		# Typedef-Abschnitte haben beschreibende Namen, es zaehlen alle
		for i in typedefSections(L):
			anchors.append((i, 8, sectionName(L[i])))
		first(lambda l: l == CONST_SECTION, 9, sectionName(CONST_SECTION))
		first(lambda l: l == GLOBAL_SECTION, 10, sectionName(GLOBAL_SECTION))
		first(lambda l: l == FUNC_SECTION, 11, sectionName(FUNC_SECTION))
		first(lambda l: l == f"#endif /* {guard} */", 12, "Abschluss")
	else:
		first(lambda l: l == VAR_SECTION, 6, sectionName(VAR_SECTION))
		first(lambda l: l == VAR_INC_SECTION, 7, sectionName(VAR_INC_SECTION))
		if firstFunc:
			anchors.append((firstFunc[0], 8, f"Funktion {firstFunc[1]} ()"))

	anchors.sort(key=lambda a: a[0])
	return anchors
#-----------------------------------------------------------------------

# Zeilenindizes innerhalb der USER CODE Bereiche (ohne Markerzeilen und USER_CODE_SKIP)
# Rueckgabe: (Menge der Zeilenindizes, [Issue fuer fehlerhafte Marker])
#-----------------------------------------------------------------------
def userCodeLines (L):
	active = set()
	markers = []
	openMarker = None
	for i, l in enumerate(L):
		m = USER_CODE.match(l)
		if not m:
			if openMarker and openMarker[1] not in USER_CODE_SKIP:
				active.add(i)
			continue

		kind, name = m.groups()
		if kind == "BEGIN":
			if openMarker:
				markers.append(Issue(i + 1, MARKER_CAT, f"BEGIN {name} vor END {openMarker[1]}"))
			openMarker = (i, name)
		else:
			if not openMarker or openMarker[1] != name:
				markers.append(Issue(i + 1, MARKER_CAT, f"END {name} ohne passendes BEGIN"))
			openMarker = None

	if openMarker:
		markers.append(Issue(openMarker[0] + 1, MARKER_CAT, f"BEGIN {openMarker[1]} ohne END"))
	return active, markers
#-----------------------------------------------------------------------

# Basisnamen (klein) aller .c-Dateien unterhalb eines Ordners, inkl. ausgeschlossener
#-----------------------------------------------------------------------
def cBasenames (base):
	files = glob.glob(os.path.join(base, "**", "*.c"), recursive=True)
	return {os.path.splitext(os.path.basename(p))[0].lower() for p in files}
#-----------------------------------------------------------------------

# Eine Datei pruefen, Rueckgabe: Liste von Issue, sortiert nach Zeile
# cNames: Basisnamen der .c-Dateien im Projekt (zusaetzlich: Ordner der Datei und ../Src)
# genHeaders: Basisnamen der von CubeMX erzeugten .h-Dateien im Projekt
# userCode: nur Zeilen zwischen USER CODE BEGIN/END pruefen (CubeMX-Dateien)
# types: bekannte Typen (im Projekt definiert und [c] types), None = Typen nicht pruefen
#-----------------------------------------------------------------------
def checkFile (path, cNames=None, genHeaders=None, userCode=False, types=None):
	raw = open(path, "rb").read()
	issues = []

	# Befund hinzufuegen
	def add (line, cat, info=""):
		issues.append(Issue(line, cat, info))

	L, asciiOk = readLines(raw, add)
	fname = os.path.basename(path)
	isHeader = fname.endswith(".h")
	name = os.path.splitext(fname)[0].upper()

	checkHead(L, fname, "//", SEP, "C", add)
	checkRequiredSections(L, INC_SECTIONS, "// Einfuegen", SEP, add, subsection)
	checkIncludes(L, genHeaders or set(), add)
	checkBlankLines(L, SEP, add)
	if types is not None:
		checkTypes(L, types, add)

	# Debug-Symbole (ein Name, egal ob ein oder mehrere Symbole)
	debugPos = debugSections(L, DEBUG_SECTION, DEBUG_NAME, add)

	if isHeader:
		guard = f"INC_{name}_H_"
		if "#pragma once" not in L:
			add(0, "Header", "#pragma once fehlt")
		elif GUARD_SECTION not in L:
			idx = L.index("#pragma once")
			add(max(idx - 1, 1), "Header", f"Abschnittsname '{L[max(idx - 2, 0)].strip()}' statt '{sectionName(GUARD_SECTION)}'")
		if f"#ifndef {guard}" not in L:
			found = [(i, l) for i, l in enumerate(L) if l.startswith("#ifndef")][:1]
			add(found[0][0] + 1 if found else 0, "Header", f"Include-Guard nicht {guard}")
		if f"#endif /* {guard} */" not in L:
			found = [i for i, l in enumerate(L) if l.startswith("#endif")]
			add(found[-1] + 1 if found else 0, "Header", f"'#endif /* {guard} */' fehlt")

		tail = [(i, l) for i, l in enumerate(L) if l.strip()]
		if not tail or tail[-1][1] != SEP:
			add(tail[-1][0] + 1 if tail else 0, "Header", "Datei endet nicht mit Trennlinie")
		if VERSION_SECTION in L:
			missing = [v for v in VERSION_KEYS if not any(re.match(rf"#define\s+{name}_{v}\b", l) for l in L)]
			if missing:
				add(L.index(VERSION_SECTION) + 1, "Version", f"Versions-Defines fehlen: {', '.join(name + '_' + v for v in missing)}")
		hasProto = any(re.match(r"^\w[\w\s\*]*\s\*?\w+\s*\(.*\)\s*;", l) for l in L)
		if hasProto and FUNC_SECTION not in L:
			add(0, "Header", "Abschnitt 'Funktionen definieren' fehlt")

		d = os.path.dirname(os.path.abspath(path))
		local = cBasenames(d) | cBasenames(os.path.join(os.path.dirname(d), "Src"))
		if name.lower() in (cNames or set()) | local:
			checkDebugSymbols(L, debugPos, name, add)
		elif debugPos:
			checkSectionForm(L, debugPos[0], SEP, add, subsection)

		# Optionale Abschnitte mit festem Namen und Typedef-Abschnitte (ohne die Unterabschnitte)
		for s in HEADER_SECTIONS:
			if s in L:
				checkSectionForm(L, L.index(s), SEP, add, subsection)
		for i in typedefSections(L):
			if not (i > 0 and L[i - 1] == SEP):
				checkSectionForm(L, i, SEP, add, subsection)
	else:
		checkVarSections(L, VAR_SECTION, VAR_INC_SECTION, "//", SEP, add, required=False, cont=subsection)
		checkCVariables(L, add)
		if VERSION_SECTION in L:
			add(L.index(VERSION_SECTION) + 1, "Version", f"Abschnitt '{sectionName(VERSION_SECTION)}' gehoert in eine .h-Datei")

	# Zeilenweise Pruefungen
	inBlock = False
	firstFunc = None
	posDepth = 0
	posPending = False
	for i, l in enumerate(L):
		n = i + 1
		s = l.strip()
		if not asciiOk and any(ord(c) > 127 for c in l):
			add(n, "Nicht-ASCII", short(l))
		if s.startswith("//-") and l != SEP:
			add(n, "Trennlinie falsche Laenge", f"{len(l)} statt {len(SEP)} Zeichen")
		if re.match(r"^\t* +[\t ]*\S", l) and not inBlock:
			add(n, "Einrueckung mit Leerzeichen", short(l))
		if "/*" in l and not re.match(r"#endif /\* .* \*/", s):
			add(n, "/* */-Kommentar", short(l))
		if "/*" in l and "*/" not in l:
			inBlock = True
		if "*/" in l:
			inBlock = False
		if re.search(r"/\*\*|///|[@\\](brief|param|return)\b", l):
			add(n, "Doxygen", short(l))
		if 'extern "C"' in l:
			add(n, 'extern "C"', short(l))
		if re.match(r"//[^\s\-/]", s):
			add(n, "Kommentar ohne Leerzeichen nach //", short(l))
		if s == "//":
			# Leere Kommentarzeile nur innerhalb eines Kommentarblocks erlaubt
			isCmt = lambda j: 0 <= j < len(L) and L[j].strip().startswith("//") and not L[j].strip().startswith("//-")
			if not (isCmt(i - 1) and isCmt(i + 1)):
				add(n, "leerer Kommentar")

		# Code ohne Kommentare und Strings
		code = re.sub(r'"(\\.|[^"])*"', '""', l)
		code = re.sub(r"//.*", "", code).rstrip()

		if code.endswith("{") and code.strip() != "{" and not re.search(r"=\s*\{$", code) and not inBlock:
			add(n, "K&R-Klammer (nicht Allman)", short(l))
		if re.match(r"\s*(case\b.*|default\s*):\s*$", code):
			# Mehrere Marken untereinander erlaubt, nur die letzte braucht den Block
			# Ausnahme: direkt folgendes einzelnes "return ...;" oder "break;" braucht keinen Block
			nxt = re.sub(r"//.*", "", nextCodeLine(L, i)).strip()
			if nxt != "{" and not re.match(r"(case\b.*|default\s*):$", nxt) and not re.match(r"(return\b.*|break\s*);$", nxt):
				add(n, "case ohne { }-Block", short(l))
			elif nxt == "{":
				checkCaseBlock(L, i, add)
		if re.match(r"\s*switch\s*\(", code):
			# Nur default auf der obersten Ebene zaehlt, nicht das eines verschachtelten switch
			depth = 0
			found = False
			for x in L[i + 1:]:
				c = stripCode(x)
				if depth == 1 and re.match(r"\s*default\s*:", c):
					found = True
				depth += c.count("{") - c.count("}")
				if depth <= 0 and "}" in c:
					break
			if not found:
				add(n, "switch ohne default", short(l))
		if re.match(r"\s*(if|else if|for|while)\s*\(.*\)\s*$", code) or re.match(r"\s*else\s*$", code):
			nxt = nextStatement(L, i)
			isIf = re.match(r"\s*(if|else)\b", code)
			if nxt != "{" and not (isIf and re.match(r"return\b.*;$", nxt)):
				add(n, "if/else/for ohne { }", short(l))
		if re.search(r"\b(if|for|while|switch|return)\(", code):
			add(n, "kein Leerzeichen nach Schluesselwort", short(l))

		# Funktionsdefinition / Prototyp (nur am Zeilenanfang)
		fm = FUNC_HEAD.match(code)
		if fm and fm.group(1) not in KEYWORDS:
			isDef = fm.group(4) is None and nextCodeLine(L, i).strip() == "{"
			isProto = fm.group(4) == ";"
			if isDef or isProto:
				if fm.group(2) == "":
					add(n, "kein Leerzeichen vor ( bei Deklaration/Definition", short(l))
				if fm.group(3).strip() == "":
					add(n, "leere Parameterliste statt (void)", short(l))
			if isDef:
				if firstFunc is None:
					firstFunc = (i, fm.group(1))

				# #if / #ifdef zwischen Trennlinie und Funktion sind erlaubt
				k = i
				while k > 0 and re.match(r"\s*#\s*(if|ifdef|ifndef|elif)\b", L[k - 1]):
					k -= 1
				prev = L[max(0, k - 2):k]
				if not (len(prev) == 2 and prev[1] == SEP and re.match(r"// \S", prev[0])):
					add(n, "Funktion ohne Kommentar+Trennlinie davor", short(l))
				checkFuncEnd(L, i, fm.group(1), add)

		# Name eines #define in GROSSBUCHSTABEN, CubeMX-Pins (<NAME>_Pin, <NAME>_GPIO_Port) ausgenommen
		nm = re.match(r"\s*#\s*define\s+(\w+)", code)
		if nm and not re.fullmatch(r"[A-Z0-9_]+(_Pin|_Port)?", nm.group(1)):
			add(n, "Define-Name nicht GROSSBUCHSTABEN", nm.group(1))

		# Wert eines #define auf Spalte 49
		dm = re.match(r"\s*#\s*define\s+\w+(\([^)]*\))?([ \t]+)(?=[^\s/])", code)
		if dm:
			col = tabcol(l, dm.end())
			if col != VALUE_COL and tabcol(l, dm.start(2)) < VALUE_COL - 1:
				add(n, f"Define-Wert nicht auf Spalte {VALUE_COL}", f"Spalte {col}: {short(l)}")
			if " " in dm.group(2):
				add(n, "Define-Wert mit Leerzeichen statt Tabs ausgerichtet", short(l))

		# union/enum-Block: Member duerfen eine Positionsangabe auf Spalte 49 haben
		inPos = posDepth > 0
		if re.match(r"\s*(typedef\s+)?(union|enum)\b", code) and not code.endswith(";"):
			posPending = True
		if posPending or posDepth > 0:
			posDepth += code.count("{") - code.count("}")
			if "{" in code:
				posPending = False

		# Zeilenkommentar hinter Code, in union/enum zuerst die Positionsangabe
		cm = re.search(r"\S(\s+)//", l)
		if cm and not s.startswith("//") and '"' not in l[:cm.start() + 1]:
			# Je Kommentar: Ende davor, Position von //, Leerraum davor
			found = [(cm.start() + 1, cm.end() - 2, cm.group(1))]
			if inPos:
				cm2 = re.search(r"\S(\s+)//", l[cm.end():])
				if cm2:
					found.append((cm.end() + cm2.start() + 1, cm.end() + cm2.end() - 2, cm2.group(1)))
			if len(found) == 2 or (inPos and tabcol(l, found[0][1]) == VALUE_COL):
				wants = [VALUE_COL, COMMENT_COL]
			else:
				wants = [COMMENT_COL]
			for (start, pos, space), want in zip(found, wants):
				col = tabcol(l, pos)
				before = l[:start].strip()
				ctx = f"{before[:40]}{' ...' if len(before) > 40 else ''}  {l[pos:].strip()[:40]}"
				if col != want and tabcol(l, start) < want - 1:
					add(n, f"Zeilenkommentar nicht auf Spalte {want}", f"Spalte {col}: {ctx}")
				if " " in space:
					add(n, "Kommentar mit Leerzeichen statt Tabs ausgerichtet", ctx)

	# Reihenfolge der Abschnitte
	checkOrder(orderAnchors(L, isHeader, f"INC_{name}_H_", firstFunc), add)

	# USER-CODE-Modus: Befunde nur aus den Bereichen, Zeilenende-Befund fuer die ganze Datei bleibt
	if userCode:
		active, markers = userCodeLines(L)
		issues = [x for x in issues if x.cat not in FILE_CATS
			and ((x.line - 1) in active or (x.line == 0 and x.cat == "Zeilenende"))] + markers

	issues.sort(key=lambda x: x.line)
	return issues
#-----------------------------------------------------------------------

# Von STM32CubeMX generierte Datei (enthaelt USER CODE Marker)
#-----------------------------------------------------------------------
def isGenerated (path):
	with open(path, "rb") as f:
		return b"USER CODE BEGIN" in f.read()
#-----------------------------------------------------------------------

# Basisnamen (klein) der von CubeMX erzeugten .h-Dateien unterhalb eines Ordners, inkl. ausgeschlossener
#-----------------------------------------------------------------------
def generatedHeaders (base):
	files = glob.glob(os.path.join(base, "**", "*.h"), recursive=True)
	return {os.path.basename(p).lower() for p in files if isGenerated(p)}
#-----------------------------------------------------------------------

# Projekt pruefen, die Basisnamen der .c-Dateien, erzeugten .h-Dateien und Typen werden einmal je Projekt bestimmt
#-----------------------------------------------------------------------
def checkProject (base, files):
	cNames = cBasenames(base)
	genHeaders = generatedHeaders(base)
	types = projectTypes(base) | set(projectList(base, "c", "types"))
	return [(p, checkFile(p, cNames, genHeaders, uc, types)) for p, uc in files]
#-----------------------------------------------------------------------

# Hauptprogramm
#-----------------------------------------------------------------------
if __name__ == "__main__":
	sys.exit(run(Language("C", "c", "docs/C_CODING_STYLE.md", (".c", ".h"), VERSION_SECTION, DEFAULT_EXCLUDE,
		"HAL/CMSIS-Dateien und Submodule mitpruefen, CubeMX-Dateien vollstaendig pruefen", checkProject, isGenerated,
		configKeys=("exclude", "include", "types"))))
#-----------------------------------------------------------------------
