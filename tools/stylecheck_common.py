#-----------------------------------------------------------------------
# Titel		:	stylecheck_common.py
#-----------------------------------------------------------------------
# Sprache	:	Python
# Datum		:	14.10.2026
# Autor		:	Diveturtle93
# Projekt	:	Coding_Styleguide
# Quelle	:
#-----------------------------------------------------------------------

# Beschreibung
#-----------------------------------------------------------------------
# Gemeinsam genutzter Code von c_stylecheck.py, py_stylecheck.py und doc_check.py:
# Befunde, Einlesen, Pruefungen von Kopfblock und Abschnitten, Reihenfolge,
# Projekt-Einstellungen (.stylecheck), Kommandozeile, Reports und Uebersicht
#-----------------------------------------------------------------------

# Einfuegen der standard Module
#-----------------------------------------------------------------------
import argparse
import collections
import configparser
import datetime
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

#-----------------------------------------------------------------------

# Definiere Debug-Symbole
#-----------------------------------------------------------------------
DEBUG_STYLECHECK_COMMON							= False
#-----------------------------------------------------------------------

# Version definieren
#-----------------------------------------------------------------------
STYLECHECK_COMMON_MAJOR							= 1
STYLECHECK_COMMON_MINOR							= 1
STYLECHECK_COMMON_PATCH							= 0
STYLECHECK_COMMON_DEV							= 0
#-----------------------------------------------------------------------

# Konstanten definieren
#-----------------------------------------------------------------------
CONFIG_FILE										= ".stylecheck"				# Projekt-Einstellungen (C und Python)
CONFIG_SECTIONS									= ("stylecheck", "c", "py", "doc")	# [stylecheck] gilt fuer beide Sprachen, [doc] fuer doc_check.py
LEGACY_CONFIG_FILES								= (".c_stylecheck", ".py_stylecheck")	# alte Dateinamen, nur noch Warnung
EXCLUDED_REPOS									= ("Diveturtle93",)			# Repos, die von keinem Check geprueft werden (GitHub-Profil)
TAB_WIDTH										= 4							# Tabbreite
COMMENT_COL										= 77						# Spalte der Zeilenkommentare
HEAD_COL										= 13						# Spalte des : im Kopfblock
VALUE_COL										= 49						# Spalte der Werte (#define, Konstanten) und Positionsangaben (union/enum)
OVERVIEW_NAME									= "Uebersicht"				# <JJJJMMTT>_Uebersicht.txt
HEAD_KEYS										= ["Titel", "Sprache", "Datum", "Autor", "Projekt", "Quelle"]
VERSION_KEYS									= ["MAJOR", "MINOR", "PATCH", "DEV"]
#-----------------------------------------------------------------------

# Ein Befund: Zeile (0 = ganze Datei), Kategorie, Zusatzinfo
#-----------------------------------------------------------------------
class Issue:
	# Befund anlegen
	def __init__ (self, line, cat, info=""):
		self.line = line
		self.cat = cat
		self.info = info
#-----------------------------------------------------------------------

# Beschreibung einer Sprache fuer run()
# name, key, rules, exts: Anzeigename, Abschnitt in .stylecheck und Report-Unterordner, Regeln, Dateiendungen
# versionSection: Zeile des Abschnitts 'Version definieren', der genau einmal im Projekt steht, None = nicht pruefen
# defaultExclude, excludeHelp: automatische Ausschluesse (Regex) und Hilfetext zu --no-default-exclude
# checkProject: (Basisordner, [(Datei, nur USER CODE)]) -> [(Datei, [Issue])]
# isGenerated: (Datei) -> nur USER CODE pruefen, None = keine generierten Dateien
# checkWhole: (Basisordner, [(Datei, nur USER CODE)], Ergebnis von checkProject) -> [Issue] fuer das ganze Projekt
# allDirs: jeder angegebene Ordner ist ein Projekt, auch ohne passende Dateien
# configKeys: erlaubte Eintraege im eigenen Abschnitt der .stylecheck
#-----------------------------------------------------------------------
class Language:
	# Sprache anlegen
	def __init__ (self, name, key, rules, exts, versionSection, defaultExclude, excludeHelp, checkProject, isGenerated=None,
			checkWhole=None, allDirs=False, configKeys=("exclude", "include")):
		self.name = name
		self.key = key
		self.rules = rules
		self.exts = exts
		self.versionSection = versionSection
		self.defaultExclude = defaultExclude
		self.excludeHelp = excludeHelp
		self.checkProject = checkProject
		self.isGenerated = isGenerated
		self.checkWhole = checkWhole
		self.allDirs = allDirs
		self.configKeys = configKeys
#-----------------------------------------------------------------------

# Variablen definieren
#-----------------------------------------------------------------------

#-----------------------------------------------------------------------

# Spalte (1-basiert) eines Zeichens bei Tabbreite 4
#-----------------------------------------------------------------------
def tabcol (line, idx):
	col = 0
	for ch in line[:idx]:
		col = (col // TAB_WIDTH + 1) * TAB_WIDTH if ch == "\t" else col + 1
	return col + 1
#-----------------------------------------------------------------------

# Zeile fuer die Ausgabe kuerzen
#-----------------------------------------------------------------------
def short (l):
	return l.strip()[:80]
#-----------------------------------------------------------------------

# Name eines Abschnitts ohne Kommentarzeichen ("// Name" bzw. "# Name" -> "Name")
#-----------------------------------------------------------------------
def sectionName (l):
	return re.sub(r"^(//|#)\s*", "", l.strip())
#-----------------------------------------------------------------------

# Dateiinhalt dekodieren und Zeilenenden pruefen, Rueckgabe: (Zeilen ohne CR, nur ASCII)
#-----------------------------------------------------------------------
def readLines (raw, add):
	try:
		text = raw.decode("ascii")
		asciiOk = True
	except UnicodeDecodeError:
		text = raw.decode("utf-8", errors="replace")
		asciiOk = False

	rawLines = text.split("\n")
	lfLines = [i + 1 for i, l in enumerate(rawLines[:-1]) if not l.endswith("\r")]
	if lfLines:
		if len(lfLines) == len(rawLines) - 1:
			add(0, "Zeilenende", "nur LF statt CRLF")
		else:
			for n in lfLines:
				add(n, "Zeilenende", "LF statt CRLF")
	return [l[:-1] if l.endswith("\r") else l for l in rawLines], asciiOk
#-----------------------------------------------------------------------

# Kopfblock pruefen, Zeile 1 darf eine Shebang-Zeile sein
# cmt: Kommentarzeichen ("//" oder "#"), language: erwarteter Wert von "Sprache"
#-----------------------------------------------------------------------
def checkHead (L, fname, cmt, sep, language, add):
	off = 1 if L[0].startswith("#!") else 0
	if off >= len(L) or L[off] != sep:
		add(off + 1, "Kopfblock", f"Zeile {off + 1} ist keine Trennlinie")

	for k in HEAD_KEYS:
		found = [(i, l) for i, l in enumerate(L[:off + 12]) if re.match(rf"{cmt}\s*{k}\b", l)]
		if not found:
			add(0, "Kopfblock", f"'{k}' fehlt")
			continue

		i, l = found[0]
		hm = re.match(rf"{cmt} {k}(\t+):", l)
		if not hm:
			add(i + 1, "Kopfblock", f"'{k}' Format abweichend: {short(l)}")
		elif tabcol(l, hm.end() - 1) != HEAD_COL:
			add(i + 1, "Kopfblock", f"'{k}' Doppelpunkt nicht auf Spalte {HEAD_COL}: {short(l)}")
		if k == "Titel" and not l.rstrip().endswith(fname):
			add(i + 1, "Kopfblock", f"Titel != Dateiname: {short(l)}")
		if k == "Sprache" and language not in l:
			add(i + 1, "Kopfblock", f"Sprache nicht {language}: {short(l)}")
		if k == "Datum" and not re.search(r"\d\d\.\d\d\.\d{4}", l):
			add(i + 1, "Kopfblock", f"Datum nicht TT.MM.JJJJ: {short(l)}")
		if k == "Autor" and "Diveturtle93" not in l:
			add(i + 1, "Kopfblock", f"Autor: {short(l)}")

	# Die Version steht nur noch im Abschnitt 'Version definieren', einmal im Repository
	for i, l in enumerate(L[:off + 12]):
		if re.match(rf"{cmt}\s*Version\s*:", l):
			add(i + 1, "Kopfblock", f"'Version' gehoert nicht mehr in den Kopfblock: {short(l)}")
#-----------------------------------------------------------------------

# Zeilenindex der schliessenden Trennlinie eines Abschnitts, None = nicht gefunden
# i: Zeile der oeffnenden Trennlinie
# cont(L, k): prueft, ob Zeile k direkt nach einer Trennlinie den Abschnitt fortsetzt (Unterabschnitt)
# Rueckgabe von cont: Zeilenindex der oeffnenden Trennlinie des naechsten Blocks, sonst None
#-----------------------------------------------------------------------
def sectionEnd (L, i, sep, cont=None):
	while True:
		end = next((j for j in range(i + 1, len(L)) if L[j] == sep), None)
		if end is None or not cont or end + 1 >= len(L):
			return end
		nxt = cont(L, end + 1)
		if nxt is None:
			return end
		i = nxt
#-----------------------------------------------------------------------

# Abschnittsform: Name, Trennlinie, Inhalt, Trennlinie, danach Leerzeile oder Dateiende
# cont: Unterabschnitte erkennen (siehe sectionEnd)
#-----------------------------------------------------------------------
def checkSectionForm (L, i, sep, add, cont=None):
	name = sectionName(L[i])
	if i + 1 >= len(L) or L[i + 1] != sep:
		add(i + 1, "Abschnitte", f"'{name}' ohne Trennlinie danach")
		return

	end = sectionEnd(L, i + 1, sep, cont)
	if end is None:
		add(i + 1, "Abschnitte", f"'{name}' ohne abschliessende Trennlinie")
	elif end + 1 < len(L) and L[end + 1].strip():
		add(end + 2, "Abschnitte", f"keine Leerzeile nach Abschnitt '{name}'")
#-----------------------------------------------------------------------

# Zwischen zwei Abschnitten genau eine Leerzeile: nach einer Trennlinie hoechstens eine Leerzeile vor weiterem Inhalt
#-----------------------------------------------------------------------
def checkBlankLines (L, sep, add):
	for i in range(len(L) - 2):
		if L[i] == sep and not L[i + 1].strip() and not L[i + 2].strip() and any(x.strip() for x in L[i + 3:]):
			add(i + 3, "Abschnitte", "mehr als eine Leerzeile zwischen Abschnitten")
#-----------------------------------------------------------------------

# Pflichtabschnitte (Include- bzw. Import-Abschnitte): vorhanden, nicht doppelt, Abschnittsform
# similar: Anfang abweichend geschriebener Abschnittsnamen ("// Einfuegen" bzw. "# Einfuegen")
# cont: Unterabschnitte erkennen (siehe sectionEnd)
#-----------------------------------------------------------------------
def checkRequiredSections (L, sections, similar, sep, add, cont=None):
	for s in sections:
		pos = [i for i, l in enumerate(L) if l == s]
		if not pos:
			other = [i + 1 for i, l in enumerate(L) if l.startswith(similar) and l not in sections]
			add(other[0] if other else 0, "Abschnitte", f"fehlt/abweichend: '{sectionName(s)}'")
		for i in pos[1:]:
			add(i + 1, "Abschnitte", f"doppelt: '{sectionName(s)}'")
		for i in pos:
			checkSectionForm(L, i, sep, add, cont)
#-----------------------------------------------------------------------

# "Variablen definieren" ist Pflicht (required=False: optional), "Variablen einbinden" optional (Schreibweise + Form)
# cont: Unterabschnitte erkennen (siehe sectionEnd)
#-----------------------------------------------------------------------
def checkVarSections (L, varSection, varIncSection, cmt, sep, add, required=True, cont=None):
	var = [(i, l) for i, l in enumerate(L) if re.match(rf"{cmt}\s*Variable", l, re.I)]
	defs = [i for i, l in var if l == varSection]
	incs = [i for i, l in var if l == varIncSection]
	for i, l in var:
		if l not in (varSection, varIncSection) and re.match(rf"{cmt}\s*Variable\w*\s+einbinden", l, re.I):
			add(i + 1, "Abschnitte", f"Variablen-Abschnitt heisst '{l.strip()}' statt '{sectionName(varIncSection)}'")
	if not defs:
		other = [i for i, l in var if l != varIncSection]
		if other:
			add(other[0] + 1, "Abschnitte", f"Variablen-Abschnitt heisst '{L[other[0]].strip()}' statt '{sectionName(varSection)}'")
		elif required:
			add(0, "Abschnitte", f"fehlt: '{sectionName(varSection)}'")
	for sec, pos in ((varSection, defs), (varIncSection, incs)):
		for i in pos[1:]:
			add(i + 1, "Abschnitte", f"doppelt: '{sectionName(sec)}'")
		for i in pos:
			checkSectionForm(L, i, sep, add, cont)
#-----------------------------------------------------------------------

# Debug-Abschnitt suchen und falsche Namen melden, Rueckgabe: Zeilenindizes aller Debug-Abschnitte
#-----------------------------------------------------------------------
def debugSections (L, section, pattern, add):
	for i, l in enumerate(L):
		if pattern.match(l) and l != section:
			add(i + 1, "Abschnitte", f"Debug-Abschnitt heisst '{l.strip()}' statt '{sectionName(section)}'")
	return [i for i, l in enumerate(L) if l == section or pattern.match(l)]
#-----------------------------------------------------------------------

# Reihenfolge der Abschnitte: anchors = [(Zeilenindex, Rang, Name)] in Dateireihenfolge
# Gemeldet werden nur Abschnitte ausserhalb der laengsten korrekt sortierten Folge
#-----------------------------------------------------------------------
def checkOrder (anchors, add):
	n = len(anchors)
	best = [1] * n
	prev = [-1] * n
	for i in range(n):
		for j in range(i):
			if anchors[j][1] <= anchors[i][1] and best[j] + 1 > best[i]:
				best[i] = best[j] + 1
				prev[i] = j

	keep = set()
	end = max(range(n), key=lambda i: (best[i], i)) if n else -1
	while end >= 0:
		keep.add(end)
		end = prev[end]

	for i, (line, rank, label) in enumerate(anchors):
		if i in keep:
			continue
		later = next((a for j, a in enumerate(anchors[:i]) if j in keep and a[1] > rank), None)
		if later:
			add(line + 1, "Reihenfolge", f"'{label}' steht nach '{later[2]}'")
			continue
		earlier = next((a for j, a in enumerate(anchors) if j > i and j in keep and a[1] < rank), None)
		if earlier:
			add(line + 1, "Reihenfolge", f"'{label}' steht vor '{earlier[2]}'")
#-----------------------------------------------------------------------

# Alle Dateien mit einer der Endungen in einer Datei- oder Ordnerangabe
#-----------------------------------------------------------------------
def listFiles (path, exts):
	if os.path.isfile(path):
		return [path] if path.endswith(exts) else []
	return sorted(p for e in exts for p in glob.glob(os.path.join(path, "**", "*" + e), recursive=True))
#-----------------------------------------------------------------------

# Ordnerangabe vereinheitlichen: Schraegstriche, klein, ohne fuehrendes/abschliessendes /
#-----------------------------------------------------------------------
def normDir (d):
	return d.strip().replace("\\", "/").strip("/").lower()
#-----------------------------------------------------------------------

# Projekt-Einstellungen: ([auszuschliessende Ordner], [zu pruefende Ordner]), relativ zum Projekt
# submodules: Pfade aus .gitmodules ausschliessen
# lang: Sprachabschnitt der Einstellungsdatei ("c", "py" oder "doc"), ergaenzt [stylecheck]
# keys: erlaubte Eintraege im Sprachabschnitt, warn: Warnungen ausgeben (False bei wiederholtem Lesen)
#-----------------------------------------------------------------------
def projectSettings (base, submodules, lang, keys=("exclude", "include"), warn=True):
	excl = []
	incl = []
	gitmodules = os.path.join(base, ".gitmodules")
	if submodules and os.path.isfile(gitmodules):
		with open(gitmodules, encoding="utf-8", errors="replace") as f:
			excl += [m.group(1) for m in re.finditer(r"^\s*path\s*=\s*(.+?)\s*$", f.read(), re.M)]

	for old in LEGACY_CONFIG_FILES:
		if warn and os.path.isfile(os.path.join(base, old)):
			print(f"Warnung: {os.path.join(base, old)} wird nicht mehr gelesen, Einstellungen nach {CONFIG_FILE} verschieben", file=sys.stderr)

	cfgPath = os.path.join(base, CONFIG_FILE)
	if os.path.isfile(cfgPath):
		cfg = configparser.ConfigParser(inline_comment_prefixes=("#", ";"))
		cfg.read(cfgPath, encoding="utf-8-sig")								# BOM von Windows-Editoren erlauben
		for name in cfg.sections():
			if warn and name not in CONFIG_SECTIONS:
				print(f"Warnung: {cfgPath}: unbekannter Abschnitt '[{name}]'", file=sys.stderr)
		for name in ("stylecheck", lang):
			if not cfg.has_section(name):
				continue
			sec = cfg[name]
			for k in sec:
				if warn and k not in (keys if name == lang else ("exclude", "include")):
					print(f"Warnung: {cfgPath}: unbekannter Eintrag '{k}' in [{name}]", file=sys.stderr)
			excl += sec.get("exclude", "").split(",")
			incl += sec.get("include", "").split(",")
	return [normDir(d) for d in excl if d.strip()], [normDir(d) for d in incl if d.strip()]
#-----------------------------------------------------------------------

# Liegt die Datei (relativ zum Projekt) in einem der Ordner?
#-----------------------------------------------------------------------
def inDirs (rel, dirs):
	return any(rel == d or rel.startswith(d + "/") for d in dirs)
#-----------------------------------------------------------------------

# Pfade/Globs zu Projekten aufloesen: {Projektname: [Basisordner, [(Datei, nur USER CODE)], als Ordner angegeben]}
# lang: Sprache fuer .stylecheck und Dateiendungen, defaults: Git-Submodule ueberspringen und
# isGenerated anwenden, quiet: Ordner ohne passende Dateien nicht melden
#-----------------------------------------------------------------------
def collectProjects (targets, excludes, lang, defaults=True, quiet=False):
	projects = collections.OrderedDict()
	seen = set()
	for t in targets:
		matches = glob.glob(t) or ([t] if os.path.exists(t) else [])
		if not matches:
			print(f"Warnung: '{t}' nicht gefunden", file=sys.stderr)
		for m in sorted(matches):
			m = os.path.abspath(m)
			base = m if os.path.isdir(m) else os.path.dirname(m)
			proj = os.path.basename(base)
			if proj.lower() in (r.lower() for r in EXCLUDED_REPOS):			# auch bei ausdruecklicher Angabe
				continue

			# Einstellungen nur fuer Projektordner, nicht fuer einzeln angegebene Dateien
			exclDirs, inclDirs = projectSettings(base, defaults, lang.key, lang.configKeys) if os.path.isdir(m) else ([], [])
			for p in listFiles(m, lang.exts):
				p = os.path.abspath(p)
				if p in seen or any(re.search(x, p, re.I) for x in excludes):
					continue
				rel = normDir(os.path.relpath(p, base))
				if inDirs(rel, exclDirs) or (inclDirs and not inDirs(rel, inclDirs)):
					continue
				seen.add(p)
				userCode = bool(defaults and lang.isGenerated and lang.isGenerated(p))
				projects.setdefault(proj, [base, [], False])[1].append((p, userCode))
			if os.path.isdir(m) and (proj in projects or lang.allDirs):
				projects.setdefault(proj, [base, [], True])[2] = True
			elif os.path.isdir(m) and not quiet:
				print(f"Hinweis: {proj}: keine Dateien zu pruefen", file=sys.stderr)
	return projects
#-----------------------------------------------------------------------

# Abschnitt 'Version definieren' steht genau einmal im Projekt (generierte Dateien zaehlen nicht)
# Mehrfache Abschnitte werden bei den Dateien in results gemeldet, Rueckgabe: Befunde fuer das ganze Projekt
#-----------------------------------------------------------------------
def checkProjectVersion (lang, files, results):
	found = []
	for p, userCode in files:
		if userCode:
			continue
		with open(p, "rb") as f:
			lines = f.read().decode("utf-8", errors="replace").splitlines()
		found += [(p, i + 1) for i, l in enumerate(lines) if l.rstrip() == lang.versionSection]

	name = sectionName(lang.versionSection)
	if not found:
		return [Issue(0, "Version", f"Abschnitt '{name}' fehlt im Projekt")]
	if len(found) > 1:
		issues = dict(results)
		for p, line in found:
			issues[p].append(Issue(line, "Version", f"Abschnitt '{name}' steht {len(found)}-mal im Projekt statt einmal"))
			issues[p].sort(key=lambda x: x.line)
	return []
#-----------------------------------------------------------------------

# Alle Reports <JJJJMMTT>_*.txt im Ordner loeschen (auch die Uebersicht), Rueckgabe: Anzahl
#-----------------------------------------------------------------------
def cleanReports (reportDir):
	if not os.path.isdir(reportDir):
		print(f"Hinweis: Report-Ordner '{reportDir}' nicht vorhanden", file=sys.stderr)
		return 0

	pattern = re.compile(r"^\d{8}_.+\.txt$", re.I)
	count = 0
	for f in sorted(os.listdir(reportDir)):
		path = os.path.join(reportDir, f)
		if pattern.match(f) and os.path.isfile(path):
			os.remove(path)
			print(f"geloescht: {os.path.relpath(path)}")
			count += 1
	return count
#-----------------------------------------------------------------------

# Einen Befund als Ausgabezeile formatieren, whole: Angabe fuer Befunde ohne Zeile (ganze Datei bzw. Projekt)
#-----------------------------------------------------------------------
def formatIssue (issue, whole="Datei"):
	where = f"Z.{issue.line:5}" if issue.line else f"{whole:7}"
	info = f"  ->  {issue.info}" if issue.info else ""
	return f"  {where}  [{issue.cat}]{info}"
#-----------------------------------------------------------------------

# Ueberschrift je Datei, userCode: Dateien, die nur in den USER CODE Bereichen geprueft wurden
#-----------------------------------------------------------------------
def fileTitle (p, base, iss, userCode):
	mode = ", nur USER CODE" if p in userCode else ""
	return f"{os.path.relpath(p, base)}  ({len(iss)} Befunde{mode})"
#-----------------------------------------------------------------------

# Befunde je Kategorie als Textzeilen
#-----------------------------------------------------------------------
def categoryLines (total):
	if not total:
		return []
	return ["", "Befunde je Kategorie", "-" * 72] + [f"{n:6}  {c}" for c, n in total.most_common()]
#-----------------------------------------------------------------------

# Report-Text fuer ein Projekt erzeugen, projIssues: Befunde fuer das ganze Projekt
#-----------------------------------------------------------------------
def buildReport (lang, proj, base, results, projIssues, userCode):
	total = collections.Counter(x.cat for _, iss in results for x in iss)
	total.update(x.cat for x in projIssues)
	clean = sum(1 for _, i in results if not i)
	mode = f", {len(userCode)} nur USER CODE" if lang.isGenerated else ""

	out = []
	out.append("=" * 72)
	out.append(f"Style-Report : {proj}")
	out.append(f"Ordner       : {base}")
	out.append(f"Erstellt     : {datetime.datetime.now():%d.%m.%Y %H:%M}")
	out.append(f"Regeln       : {lang.rules}")
	out.append(f"Geprueft     : {len(results)} Dateien, davon {clean} ohne Befund{mode}")
	out.append(f"Befunde      : {sum(total.values())}")
	out.append("=" * 72)
	out += categoryLines(total)

	if projIssues:
		out.append("")
		out.append("-" * 72)
		out.append(f"Projekt  ({len(projIssues)} Befunde)")
		out.append("-" * 72)
		out += [formatIssue(x, "Projekt") for x in projIssues]

	for p, iss in results:
		out.append("")
		out.append("-" * 72)
		out.append(fileTitle(p, base, iss, userCode))
		out.append("-" * 72)
		if not iss:
			out.append("  keine Befunde")
		out += [formatIssue(x) for x in iss]
	out.append("")
	return "\n".join(out)
#-----------------------------------------------------------------------

# Uebersicht ueber alle Projekte erzeugen
# rows: [(Projekt, Dateien, Dateien ohne Befund, Befunde, Report geschrieben)]
#-----------------------------------------------------------------------
def buildOverview (lang, rows, total):
	out = []
	out.append("=" * 72)
	out.append(f"Uebersicht   : {lang.name}")
	out.append(f"Erstellt     : {datetime.datetime.now():%d.%m.%Y %H:%M}")
	out.append(f"Regeln       : {lang.rules}")
	out.append(f"Projekte     : {len(rows)}, davon {sum(1 for r in rows if not r[3])} ohne Befund")
	out.append(f"Dateien      : {sum(r[1] for r in rows)}, davon {sum(r[2] for r in rows)} ohne Befund")
	out.append(f"Befunde      : {sum(r[3] for r in rows)}")
	out.append("=" * 72)

	out.append("")
	out.append(f"{'Projekt':34} {'Dateien':>8} {'ohne Bef.':>10} {'Befunde':>8}  Report")
	out.append("-" * 72)
	for proj, nFiles, nClean, nIssues, written in rows:
		out.append(f"{proj:34} {nFiles:8} {nClean:10} {nIssues:8}  {'ja' if written else '-'}")
	out += categoryLines(total)
	out.append("")
	return "\n".join(out)
#-----------------------------------------------------------------------

# Text als Report-Datei schreiben (ASCII, CRLF)
#-----------------------------------------------------------------------
def writeReport (path, text):
	with open(path, "w", encoding="ascii", errors="replace", newline="\r\n") as f:
		f.write(text)
#-----------------------------------------------------------------------

# Kommandozeile auswerten und Projekte pruefen, lang: Language
# Rueckgabe: 0 = keine Befunde, 1 = Befunde vorhanden, 2 = keine Dateien gefunden
#-----------------------------------------------------------------------
def run (lang):
	# Nicht-ASCII-Zeichen aus geprueften Dateien duerfen die Ausgabe nicht abbrechen
	sys.stdout.reconfigure(errors="replace")

	here = os.path.dirname(os.path.abspath(__file__))
	repoDir = os.path.dirname(here)
	ownDir = os.path.dirname(repoDir)
	defaultTarget = os.path.join(ownDir, "*")
	defaultReports = os.path.join(repoDir, "reports")

	ap = argparse.ArgumentParser(description=f"Prueft {lang.name}-Dateien gegen {lang.rules}")
	ap.add_argument("paths", nargs="*", help=f"Ordner, Dateien oder Glob-Muster (Standard: {defaultTarget})")
	ap.add_argument("-r", "--report", nargs="?", const=defaultReports, metavar="DIR",
		help=f"je Projekt Report DIR/{lang.key}/<JJJJMMTT>_<Projekt>.txt und eine Uebersicht schreiben (Standard: {defaultReports})")
	ap.add_argument("-f", "--findings-only", action="store_true",
		help="mit -r nur Reports fuer Projekte mit Befunden schreiben, die Uebersicht enthaelt alle Projekte")
	ap.add_argument("-c", "--clean", nargs="?", const=defaultReports, metavar="DIR",
		help=f"alle {lang.name}-Reports in DIR/{lang.key}/ loeschen (Standard: {defaultReports}), mit -r danach neu schreiben")
	ap.add_argument("-q", "--quiet", action="store_true", help="Dateien ohne Befund nicht anzeigen")
	ap.add_argument("-s", "--summary", action="store_true", help="nur Zusammenfassung ausgeben")
	ap.add_argument("-x", "--exclude", action="append", default=[], metavar="REGEX", help="zusaetzlich ausschliessen")
	ap.add_argument("--no-default-exclude", action="store_true", help=lang.excludeHelp)
	args = ap.parse_args()

	if args.clean:
		print(f"{cleanReports(os.path.join(args.clean, lang.key))} Reports geloescht")
		if not args.report:
			return 0

	defaults = not args.no_default_exclude
	excludes = args.exclude + (lang.defaultExclude if defaults else [])
	projects = collectProjects(args.paths or [defaultTarget], excludes, lang, defaults, not args.paths)
	if not projects:
		print(f"Keine {'/'.join(lang.exts)}-Dateien gefunden.")
		return 2

	reportDir = os.path.join(args.report, lang.key) if args.report else None
	if reportDir:
		os.makedirs(reportDir, exist_ok=True)
	datePrefix = datetime.date.today().strftime("%Y%m%d")

	total = collections.Counter()
	nFiles = 0
	nClean = 0
	rows = []
	for proj, (base, files, isFolder) in projects.items():
		results = lang.checkProject(base, files)

		# Die Version und checkWhole gelten fuer das Projekt, nur pruefbar, wenn der ganze Ordner angegeben ist
		projIssues = []
		if isFolder and lang.versionSection:
			projIssues += checkProjectVersion(lang, files, results)
		if isFolder and lang.checkWhole:
			projIssues += lang.checkWhole(base, files, results)
		userCode = {p for p, uc in files if uc}
		nIssues = sum(len(i) for _, i in results) + len(projIssues)
		nFiles += len(results)
		nClean += sum(1 for _, i in results if not i)
		total.update(x.cat for x in projIssues)
		total.update(x.cat for _, iss in results for x in iss)

		if reportDir:
			written = nIssues > 0 or not args.findings_only
			rows.append((proj, len(results), sum(1 for _, i in results if not i), nIssues, written))
			if not written:
				print(f"{proj:30} {0:6} Befunde  -> kein Report")
				continue
			path = os.path.join(reportDir, f"{datePrefix}_{proj}.txt")
			writeReport(path, buildReport(lang, proj, base, results, projIssues, userCode))
			print(f"{proj:30} {nIssues:6} Befunde  -> {os.path.relpath(path)}")
			continue

		if args.summary:
			continue
		if projIssues:
			print(f"\n### {proj}  ({len(projIssues)} Befunde im Projekt)")
			for x in projIssues:
				print(formatIssue(x, "Projekt"))
		for p, iss in results:
			if args.quiet and not iss:
				continue
			print(f"\n### {proj}/{fileTitle(p, base, iss, userCode)}")
			for x in iss:
				print(formatIssue(x))

	if reportDir:
		path = os.path.join(reportDir, f"{datePrefix}_{OVERVIEW_NAME}.txt")
		writeReport(path, buildOverview(lang, rows, total))
		print(f"{'Uebersicht':30} {len(rows):6} Projekte -> {os.path.relpath(path)}")

	print("\n=== Befunde je Kategorie ===")
	for c, n in total.most_common():
		print(f"{n:6}  {c}")
	print(f"\nGeprueft: {len(projects)} Projekte, {nFiles} Dateien, davon {nClean} ohne Befund")
	return 1 if total else 0
#-----------------------------------------------------------------------
