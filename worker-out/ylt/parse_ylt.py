#!/usr/bin/env python3
"""Parse ebible.org engylt USFM (Old Testament books, GEN..MAL) into ylt_verses.tsv.

Source: https://ebible.org/Scriptures/engylt_usfm.zip  (Young's Literal Translation, public domain)
Output: ylt_verses.tsv with header book_num<TAB>chapter<TAB>verse<TAB>text

The engylt USFM is unusually clean: only \\id, \\h, \\toc1-3, \\mt1, \\c, \\p, \\v
markers occur in the 39 OT files (verified by marker survey 2026-09-20). No
footnotes, cross-references, or character markers (\\w/\\nd/\\add) are present.
The parser still defensively strips any stray markers.
"""
import os
import re
import glob

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
USFM_DIR = os.path.join(OUT_DIR, "usfm")

BOOK_ORDER = [
    "GEN", "EXO", "LEV", "NUM", "DEU", "JOS", "JDG", "RUT",
    "1SA", "2SA", "1KI", "2KI", "1CH", "2CH", "EZR", "NEH",
    "EST", "JOB", "PSA", "PRO", "ECC", "SNG", "ISA", "JER",
    "LAM", "EZK", "DAN", "HOS", "JOL", "AMO", "OBA", "JON",
    "MIC", "NAM", "HAB", "ZEP", "HAG", "ZEC", "MAL",
]
BOOK_NUM = {code: i + 1 for i, code in enumerate(BOOK_ORDER)}
BOOK_NAMES = {
    "GEN": "Genesis", "EXO": "Exodus", "LEV": "Leviticus", "NUM": "Numbers",
    "DEU": "Deuteronomy", "JOS": "Joshua", "JDG": "Judges", "RUT": "Ruth",
    "1SA": "1 Samuel", "2SA": "2 Samuel", "1KI": "1 Kings", "2KI": "2 Kings",
    "1CH": "1 Chronicles", "2CH": "2 Chronicles", "EZR": "Ezra", "NEH": "Nehemiah",
    "EST": "Esther", "JOB": "Job", "PSA": "Psalms", "PRO": "Proverbs",
    "ECC": "Ecclesiastes", "SNG": "Song of Solomon", "ISA": "Isaiah",
    "JER": "Jeremiah", "LAM": "Lamentations", "EZK": "Ezekiel", "DAN": "Daniel",
    "HOS": "Hosea", "JOL": "Joel", "AMO": "Amos", "OBA": "Obadiah",
    "JON": "Jonah", "MIC": "Micah", "NAM": "Nahum", "HAB": "Habakkuk",
    "ZEP": "Zephaniah", "HAG": "Haggai", "ZEC": "Zechariah", "MAL": "Malachi",
}

RE_CHAPTER = re.compile(r"^\\c\s+(\d+)\s*$")
RE_VERSE = re.compile(r"^\\v\s+(\d+)\s?(.*)$")
RE_KNOWN_LINE = re.compile(r"^\\(id|h|toc\d|mt\d|c|p|v)\b")
RE_STRAY_MARKER = re.compile(r"\\[a-zA-Z]+\d*\*?")


def clean(text):
    text = RE_STRAY_MARKER.sub("", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def parse_file(path):
    """Return list of (chapter, verse, text)."""
    rows = []
    chapter = None
    anomalies = []
    with open(path, encoding="utf-8-sig") as f:
        for lineno, raw in enumerate(f, 1):
            line = raw.strip()
            if not line:
                continue
            m = RE_CHAPTER.match(line)
            if m:
                chapter = int(m.group(1))
                continue
            m = RE_VERSE.match(line)
            if m:
                if chapter is None:
                    anomalies.append(f"line {lineno}: verse before any chapter")
                    continue
                verse = int(m.group(1))
                text = clean(m.group(2))
                rows.append((chapter, verse, text))
                continue
            if not RE_KNOWN_LINE.match(line):
                anomalies.append(f"line {lineno}: unexpected line: {line[:80]!r}")
    return rows, anomalies


def main():
    out_path = os.path.join(OUT_DIR, "ylt_verses.tsv")
    per_book = []
    total = 0
    all_anomalies = []
    with open(out_path, "w", encoding="utf-8") as out:
        out.write("book_num\tchapter\tverse\ttext\n")
        for code in BOOK_ORDER:
            matches = sorted(glob.glob(os.path.join(USFM_DIR, f"*-{code}engylt.usfm")))
            if not matches:
                raise SystemExit(f"ERROR: no USFM file found for {code}")
            path = matches[0]
            rows, anomalies = parse_file(path)
            book_num = BOOK_NUM[code]
            seen = set()
            empty = 0
            for chapter, verse, text in rows:
                key = (chapter, verse)
                if key in seen:
                    all_anomalies.append(f"{code}: duplicate verse {chapter}:{verse}")
                seen.add(key)
                if not text:
                    empty += 1
                    all_anomalies.append(f"{code}: empty text at {chapter}:{verse}")
                out.write(f"{book_num}\t{chapter}\t{verse}\t{text}\n")
            per_book.append((book_num, code, BOOK_NAMES[code], len(rows)))
            total += len(rows)
            all_anomalies.extend(f"{code}: {a}" for a in anomalies)
            print(f"{book_num:2d} {code:3s} {BOOK_NAMES[code]:16s} {len(rows):5d} verses")
    print(f"TOTAL: {total} verses")
    if all_anomalies:
        print("ANOMALIES:")
        for a in all_anomalies:
            print("  " + a)
    else:
        print("No anomalies.")
    with open(os.path.join(OUT_DIR, "per_book_counts.txt"), "w") as f:
        for book_num, code, name, n in per_book:
            f.write(f"{book_num}\t{code}\t{name}\t{n}\n")
        f.write(f"TOTAL\t\t\t{total}\n")


if __name__ == "__main__":
    main()
