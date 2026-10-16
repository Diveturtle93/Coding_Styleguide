#!/usr/bin/env python3
#-----------------------------------------------------------------------
# Titel		:	doc_check.py
#-----------------------------------------------------------------------
# Sprache	:	Python
# Datum		:	16.10.2026
# Autor		:	Diveturtle93
# Projekt	:	Coding_Styleguide
# Quelle	:
#-----------------------------------------------------------------------

# Beschreibung
#-----------------------------------------------------------------------
# Prueft die Dokumentation (.md) eines Projekts gegen docs/DOCUMENTATION_STYLE.md
# Geprueft wird bisher die Vollstaendigkeit: Pflichtdateien der Repo-Klasse,
# per [doc] require verlangte Dokumente, Lizenz, Ablage, Ordner-README und
# relative Links. Die Gliederung von README, CHANGELOG, ARCHITECTURE und
# RUNBOOK folgt.
# Aufruf:
#   py tools/doc_check.py                          -> alle Ordner neben diesem Repo
#   py tools/doc_check.py ../STM32_Canbus          -> einzelner Ordner
#   py tools/doc_check.py "../EAuto_*"             -> beliebige Ordner / Glob-Muster
#   py tools/doc_check.py -r                       -> Reports nach reports/doc/<JJJJMMTT>_<Projekt>.txt
#
# Optionen wie c_stylecheck.py und py_stylecheck.py (-r, -f, -c, -q, -s, -x, --no-default-exclude)
#
# Projekt-Einstellungen (optional): Datei .stylecheck im Projektordner
#   [doc]
#   class = werkzeug              -> Repo-Klasse, wenn sie sich nicht aus dem Namen ergibt
#   require = architecture, runbook   -> zusaetzlich verlangte Dokumente (architecture, runbook, adr)
#   exclude = Manual              -> diese Ordner/Dateien nicht pruefen, ergaenzt [stylecheck]
#
# Rueckgabewert: 0 = keine Befunde, 1 = Befunde vorhanden, 2 = keine Projekte gefunden
#-----------------------------------------------------------------------

# Einfuegen der standard Module
#-----------------------------------------------------------------------
import configparser
import os
import re
import sys
import urllib.parse
#-----------------------------------------------------------------------

# Einfuegen der externen Module
#-----------------------------------------------------------------------

#-----------------------------------------------------------------------

# Einfuegen der eigenen Module
#-----------------------------------------------------------------------
from stylecheck_common import (
	CONFIG_FILE,
	Issue,
	Language,
	inDirs,
	normDir,
	projectSettings,
	run,
)
#-----------------------------------------------------------------------

# Definiere Debug-Symbole
#-----------------------------------------------------------------------
DEBUG_DOC_CHECK									= False
#-----------------------------------------------------------------------

# Konstanten definieren
#-----------------------------------------------------------------------
CONFIG_KEYS										= ("exclude", "class", "require")	# erlaubte Eintraege in [doc]

# Repo-Klassen (Eintrag in [doc] class -> Name im Documentation Style)
CLASSES											= {
	"bibliothek": "Bibliothek",
	"firmware": "Firmware-Anwendung",
	"werkzeug": "PC-Werkzeug",
	"referenz": "Referenz",
	"ausgenommen": "ausgenommen",
}

# Klasse aus dem Repo-Namen, der erste passende Anfang gilt
CLASS_BY_NAME									= [
	("STM32F7_", "firmware"),
	("STM32_", "bibliothek"),
	("IMD_", "bibliothek"),
	("EAuto_", "firmware"),
]

REQUIRED_FILES									= ("README.md", "CHANGELOG.md")	# Pflicht in jeder Klasse ausser ausgenommen
LICENSE_FILE									= "LICENSE"
ROOT_FILES										= ("README.md", "CHANGELOG.md", "ARCHITECTURE.md", "RUNBOOK.md")	# erlaubte .md im Hauptverzeichnis
ADR_DIR											= "docs/adr"
ADR_NAME										= re.compile(r"^\d{4}-.+\.md$")

# Dokumente, die ein Projekt per [doc] require verlangt
OPTIONAL_DOCS									= {
	"architecture": "ARCHITECTURE.md",
	"runbook": "RUNBOOK.md",
	"adr": ADR_DIR,
}

DOC_LIMIT										= 3							# mehr Dokumente in einem Ordner -> Ordner-README
TOOL_LIMIT										= 2							# so viele ausfuehrbare Werkzeuge -> Ordner-README
SCRIPT_EXTS										= (".sh", ".bat", ".cmd", ".ps1")	# immer ausfuehrbar, .py nur mit Shebang oder __main__

# HAL, CMSIS, Middleware, Build-Ausgaben, virtuelle Umgebungen und Caches
EXCLUDE_DIRS									= (
	"Drivers", "Middlewares", "CMSIS", "Debug", "Release", "build", "dist",
	"venv", "env", "site-packages", "node_modules", "__pycache__",
)
DEFAULT_EXCLUDE									= [r"[\\/](" + "|".join(EXCLUDE_DIRS) + r")[\\/]"]

FENCE											= re.compile(r"^\s{0,3}(`{3,}|~{3,})")
INLINE_CODE										= re.compile(r"(`+).*?\1")
LINK_INLINE										= re.compile(r"\]\(\s*<?([^)\s>]+)>?(?:\s+[\"'(][^)]*)?\)")
LINK_REF										= re.compile(r"^\s{0,3}\[[^\]]+\]:\s*<?([^\s>]+)>?")
LINK_HTML										= re.compile(r"\b(?:src|href)\s*=\s*[\"']([^\"']+)[\"']", re.I)
URL_SCHEME										= re.compile(r"^[a-z][a-z0-9+.-]*:", re.I)	# http:, mailto:, auch Laufwerk C:
#-----------------------------------------------------------------------

# Variablen definieren
#-----------------------------------------------------------------------

#-----------------------------------------------------------------------

# Tatsaechlicher Name eines Eintrags im Ordner, auch bei abweichender Schreibweise, None = nicht vorhanden
#-----------------------------------------------------------------------
def findName (folder, name):
	try:
		names = os.listdir(folder)
	except OSError:
		return None
	if name in names:
		return name
	return next((n for n in names if n.lower() == name.lower()), None)
#-----------------------------------------------------------------------

# Einstellungen aus [doc]: (Klasse oder None, [verlangte Dokumente])
#-----------------------------------------------------------------------
def docSettings (base):
	cfgPath = os.path.join(base, CONFIG_FILE)
	if not os.path.isfile(cfgPath):
		return None, []

	cfg = configparser.ConfigParser(inline_comment_prefixes=("#", ";"))
	cfg.read(cfgPath, encoding="utf-8-sig")
	if not cfg.has_section("doc"):
		return None, []
	sec = cfg["doc"]
	cls = sec.get("class", "").strip().lower() or None
	require = [r.strip().lower() for r in sec.get("require", "").split(",") if r.strip()]
	return cls, require
#-----------------------------------------------------------------------

# Repo-Klasse aus [doc] class oder dem Repo-Namen, None = nicht ableitbar
#-----------------------------------------------------------------------
def repoClass (base):
	cls, _ = docSettings(base)
	if cls:
		return cls
	name = os.path.basename(base)
	return next((c for prefix, c in CLASS_BY_NAME if name.startswith(prefix)), None)
#-----------------------------------------------------------------------

# Zeilen ausserhalb von Codebloecken: [(Zeilenindex, Zeile)]
#-----------------------------------------------------------------------
def textLines (L):
	out = []
	fence = None
	for i, l in enumerate(L):
		m = FENCE.match(l)
		if fence:
			if m and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence) and not l.strip()[len(m.group(1)):].strip():
				fence = None
			continue
		if m:
			fence = m.group(1)
			continue
		out.append((i, l))
	return out
#-----------------------------------------------------------------------

# Relativen Link pruefen: Ziel vorhanden, im Repository und in gleicher Schreibweise (GitHub unterscheidet sie)
#-----------------------------------------------------------------------
def checkLink (target, path, base, n, add):
	if URL_SCHEME.match(target) or target.startswith(("#", "/")):
		return
	rel = urllib.parse.unquote(re.split(r"[#?]", target)[0])
	if not rel:
		return

	full = os.path.normpath(os.path.join(os.path.dirname(path), rel))
	if full != base and not full.startswith(base + os.sep):
		add(n, "Links", f"'{target}' zeigt aus dem Repository heraus")
		return
	if not os.path.exists(full):
		add(n, "Links", f"'{target}' nicht gefunden")
		return

	parts = os.path.relpath(full, base).split(os.sep)
	real = []
	folder = base
	for p in parts:
		real.append(findName(folder, p) or p)
		folder = os.path.join(folder, real[-1])
	if real != parts:
		add(n, "Links", f"'{target}' Schreibweise abweichend, Datei heisst '{'/'.join(real)}'")
#-----------------------------------------------------------------------

# README im Hauptverzeichnis: '## Lizenz' genau dann, wenn eine LICENSE vorliegt
#-----------------------------------------------------------------------
def checkLicense (text, base, add):
	heads = [i for i, l in text if re.match(r"^##\s+Lizenz\s*$", l)]
	hasLicense = findName(base, LICENSE_FILE) == LICENSE_FILE
	if hasLicense and not heads:
		add(0, "Lizenz", f"{LICENSE_FILE} vorhanden, aber kein Abschnitt '## Lizenz'")
	elif heads and not hasLicense:
		add(heads[0] + 1, "Lizenz", f"'## Lizenz' ohne Datei {LICENSE_FILE}")
#-----------------------------------------------------------------------

# Eine .md-Datei pruefen
#-----------------------------------------------------------------------
def checkFile (path, base):
	issues = []

	# Befund hinzufuegen
	def add (line, cat, info=""):
		issues.append(Issue(line, cat, info))

	with open(path, "rb") as f:
		L = f.read().decode("utf-8", errors="replace").splitlines()
	text = textLines(L)

	for i, l in text:
		code = INLINE_CODE.sub("", l)
		targets = LINK_INLINE.findall(code) + LINK_HTML.findall(code)
		ref = LINK_REF.match(code)
		if ref:
			targets.append(ref.group(1))
		for t in targets:
			checkLink(t, path, base, i + 1, add)

	if os.path.dirname(path) == base and os.path.basename(path) == "README.md":
		checkLicense(text, base, add)

	issues.sort(key=lambda x: x.line)
	return issues
#-----------------------------------------------------------------------

# Projekt pruefen, ausgenommene Repos haben keine Befunde
#-----------------------------------------------------------------------
def checkProject (base, files):
	if repoClass(base) == "ausgenommen":
		return []
	return [(p, checkFile(p, base)) for p, _ in files]
#-----------------------------------------------------------------------

# Ist die Datei ein ausfuehrbares Werkzeug?
#-----------------------------------------------------------------------
def isTool (path):
	if path.lower().endswith(SCRIPT_EXTS):
		return True
	if not path.endswith(".py"):
		return False
	with open(path, "rb") as f:
		src = f.read().decode("utf-8", errors="replace")
	return src.startswith("#!") or bool(re.search(r"^if __name__ == [\"']__main__[\"']", src, re.M))
#-----------------------------------------------------------------------

# Ordner mit mehr als DOC_LIMIT Dokumenten oder mindestens TOOL_LIMIT Werkzeugen brauchen eine README
#-----------------------------------------------------------------------
def checkFolderReadmes (base, add):
	exclDirs, _ = projectSettings(base, True, "doc", CONFIG_KEYS, warn=False)
	for folder, dirs, names in os.walk(base):
		rel = normDir(os.path.relpath(folder, base))
		dirs[:] = sorted(d for d in dirs if not d.startswith(".") and d not in EXCLUDE_DIRS
			and not inDirs(normDir(os.path.join(rel, d)), exclDirs))
		if folder == base:
			continue

		names = [n for n in names if not inDirs(normDir(os.path.join(rel, n)), exclDirs)]
		docs = sum(1 for n in names if n.lower().endswith(".md") and n.lower() != "readme.md")
		tools = sum(1 for n in names if isTool(os.path.join(folder, n)))
		if docs <= DOC_LIMIT and tools < TOOL_LIMIT:
			continue

		shown = os.path.relpath(folder, base).replace(os.sep, "/")
		readme = findName(folder, "README.md")
		if readme is None:
			add(0, "Ordner-README", f"'{shown}/' hat {docs} Dokumente und {tools} Werkzeuge, aber keine README.md")
		elif readme != "README.md":
			add(0, "Ordner-README", f"'{shown}/{readme}' heisst nicht README.md")
#-----------------------------------------------------------------------

# Pruefungen fuer das ganze Projekt: Klasse, Pflichtdateien, [doc] require, Ablage, Ordner-README
#-----------------------------------------------------------------------
def checkWhole (base, files, results):
	issues = []

	# Befund hinzufuegen
	def add (line, cat, info=""):
		issues.append(Issue(line, cat, info))

	cls = repoClass(base)
	_, require = docSettings(base)
	if cls == "ausgenommen":
		return []
	if cls is None:
		add(0, "Klasse", f"nicht aus dem Repo-Namen ableitbar, '[doc] class' in {CONFIG_FILE} setzen")
	elif cls not in CLASSES:
		add(0, "Klasse", f"unbekannte Klasse '{cls}' in {CONFIG_FILE}, erlaubt: {', '.join(CLASSES)}")

	for name in REQUIRED_FILES:
		real = findName(base, name)
		if real is None:
			add(0, "Pflichtdateien", f"'{name}' fehlt")
		elif real != name:
			add(0, "Pflichtdateien", f"'{real}' heisst nicht '{name}'")

	for r in require:
		if r not in OPTIONAL_DOCS:
			add(0, "Einstellungen", f"unbekanntes Dokument '{r}' in [doc] require, erlaubt: {', '.join(OPTIONAL_DOCS)}")
			continue
		name = OPTIONAL_DOCS[r]
		if name == ADR_DIR:
			adrDir = os.path.join(base, *ADR_DIR.split("/"))
			if not any(ADR_NAME.match(n) for n in (os.listdir(adrDir) if os.path.isdir(adrDir) else [])):
				add(0, "Pflichtdateien", f"kein ADR '{ADR_DIR}/NNNN-titel.md' ([doc] require = {r})")
			continue
		real = findName(base, name)
		if real is None:
			add(0, "Pflichtdateien", f"'{name}' fehlt ([doc] require = {r})")
		elif real != name:
			add(0, "Pflichtdateien", f"'{real}' heisst nicht '{name}'")

	rootNames = {n.lower() for n in ROOT_FILES}
	for p, _ in files:
		name = os.path.basename(p)
		if os.path.dirname(p) == base and name.lower() not in rootNames:
			add(0, "Ablage", f"'{name}' gehoert nach docs/")

	checkFolderReadmes(base, add)
	return issues
#-----------------------------------------------------------------------

# Hauptprogramm
#-----------------------------------------------------------------------
if __name__ == "__main__":
	sys.exit(run(Language("Dokumentation", "doc", "docs/DOCUMENTATION_STYLE.md", (".md",), None, DEFAULT_EXCLUDE,
		"HAL, Build-Ordner, virtuelle Umgebungen und Submodule mitpruefen", checkProject,
		checkWhole=checkWhole, allDirs=True, configKeys=CONFIG_KEYS)))
#-----------------------------------------------------------------------
