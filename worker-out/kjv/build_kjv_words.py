#!/usr/bin/env python3
"""Build kjv_words.tsv from the CrossWire SWORD KJV module (zText, v3.1).

Source: https://www.crosswire.org/ftpmirror/pub/sword/packages/rawzip/KJV.zip
License (from the module's own mods.d/kjv.conf, fetched from crosswire.org):
  "Any copyright that might be obtained for this effort is held by CrossWire
   Bible Society (c) 2003-2023 and CrossWire Bible Society hereby grants a
   general public license to use this text for any purpose."
  DistributionLicense=GPL ; TextSource=https://gitlab.com/crosswire-bible-society/kjv

zText decode: per jsword ZVerseBackend (crosswire.org SVN):
  ot.bzv : per-verse 10-byte LE recs: blockNum u32, verseStart u32, verseSize u16
  ot.bzs : per-block 12-byte LE recs: blockStart u32, blockSize u32, uncompSize u32
  ot.bzz : concatenated zlib blocks (CompressType=ZIP)

Record walk (KJV versification order): importer milestone, per book:
  <div type="book" sID osisID="Gen"> + <title type="main"> (dropped),
  per chapter: <chapter sID osisID="Gen.1"> + <title type="chapter"> (dropped),
  verse records; chapter eID markers ride at the end of a chapter's last verse;
  book eID <div> rides at the end of the book's last verse.

OSIS -> words:
  <w lemma="strong:H07225">phrase</w> : every English word in the phrase carries
      the phrase's Strong's number(s); multi-number lemmas ("strong:H0853
      strong:H01254") become comma-separated.
  <transChange type="added"> : added (italicized) words, kept, empty strongs.
  <divineName>Lord</divineName> : uppercased to LORD (as printed in KJV).
  <title type="psalm"> / <title type="acrostic"> (canonical): kept with verse 1.
  <title type="main"> / <title type="chapter"> : dropped (not verse text).
  <note type="study"> (footnotes w/ catchWord+rdg) : dropped entirely.
  <inscription>, <foreign> : content kept.
  <milestone>, x-milestone <div>, chapter eID markers : dropped.

Output: kjv_words.tsv
  book_num<TAB>chapter<TAB>verse<TAB>kjv_pos<TAB>kjv_word<TAB>strongs
"""
import json
import os
import re
import struct
import sys
import zipfile
import zlib
from collections import Counter
from html import unescape

HERE = os.path.dirname(os.path.abspath(__file__))
ZIP_PATH = sys.argv[1] if len(sys.argv) > 1 else "/tmp/kjv.zip"
OUT_PATH = os.path.join(HERE, "kjv_words.tsv")

BOOK_ABBR = {'Gen': 1, 'Exod': 2, 'Lev': 3, 'Num': 4, 'Deut': 5, 'Josh': 6,
             'Judg': 7, 'Ruth': 8, '1Sam': 9, '2Sam': 10, '1Kgs': 11,
             '2Kgs': 12, '1Chr': 13, '2Chr': 14, 'Ezra': 15, 'Neh': 16,
             'Esth': 17, 'Job': 18, 'Ps': 19, 'Prov': 20, 'Eccl': 21,
             'Song': 22, 'Isa': 23, 'Jer': 24, 'Lam': 25, 'Ezek': 26,
             'Dan': 27, 'Hos': 28, 'Joel': 29, 'Amos': 30, 'Obad': 31,
             'Jonah': 32, 'Mic': 33, 'Nah': 34, 'Hab': 35, 'Zeph': 36,
             'Hag': 37, 'Zech': 38, 'Mal': 39}

STRIP_CHARS = " \t.,;:!?\"'()[]{}<>«»‹›—–-–‐‑“”‘’…*†‡¶§\u00a0"


def decode_records():
    z = zipfile.ZipFile(ZIP_PATH)
    base = "modules/texts/ztext/kjv/ot"
    comp = z.read(base + ".bzv")
    idx = z.read(base + ".bzs")
    txt = z.read(base + ".bzz")
    n_blocks = len(idx) // 12
    blocks = []
    for b in range(n_blocks):
        blockStart, blockSize, uncompSize = struct.unpack_from("<III", idx, b * 12)
        data = zlib.decompress(txt[blockStart:blockStart + blockSize])
        assert len(data) == uncompSize, f"block {b} size mismatch"
        blocks.append(data)
    n = len(comp) // 10
    recs = []
    for i in range(n):
        blockNum, verseStart, verseSize = struct.unpack_from("<IIH", comp, i * 10)
        if verseSize == 0:
            recs.append("")
        else:
            recs.append(blocks[blockNum][verseStart:verseStart + verseSize]
                         .decode("utf-8", errors="replace"))
    return recs


def verse_words(text, stats):
    """OSIS verse-entry text -> list of (word, strongs)."""
    t = text
    # 1. drop study notes entirely (they duplicate verse words in catchWord)
    t = re.sub(r"<note\b.*?</note>", " ", t, flags=re.S | re.I)
    # 2. drop non-canonical titles (book/chapter headings); keep psalm/acrostic
    t = re.sub(r'<title\b[^>]*type="(main|chapter)"[^>]*>.*?</title>', " ",
               t, flags=re.S | re.I)
    # 3. divineName -> uppercase (printed KJV: LORD)
    t = re.sub(r"<divineName>(.*?)</divineName>",
               lambda m: unescape(m.group(1)).upper(), t, flags=re.S | re.I)
    # 4. drop milestones / x-milestone divs / chapter eID markers (keep other text)
    t = re.sub(r"<milestone[^>]*/>", " ", t, flags=re.I)
    t = re.sub(r'<div\b[^>]*type="x-milestone"[^>]*/>', " ", t, flags=re.I)
    t = re.sub(r"<chapter\b[^>]*>", " ", t, flags=re.I)
    t = re.sub(r'<div\b[^>]*type="book"[^>]*>', " ", t, flags=re.I)
    # 5. keep content of canonical titles, inscriptions, foreign words
    t = re.sub(r'<title\b[^>]*type="psalm"[^>]*>(.*?)</title>', r" \1 ", t,
               flags=re.S | re.I)
    t = re.sub(r'<title\b[^>]*type="acrostic"[^>]*>(.*?)</title>', r" \1 ", t,
               flags=re.S | re.I)
    t = re.sub(r"<inscription>(.*?)</inscription>", r" \1 ", t, flags=re.S | re.I)
    t = re.sub(r"<foreign\b[^>]*>(.*?)</foreign>", r" \1 ", t, flags=re.S | re.I)
    t = re.sub(r"<div\b[^>]*/>", " ", t)  # self-closing divs (bookGroup, etc.)
    # 6. keyed phrases -> per-word placeholders \x01NUMS\x02word
    def wsub(m):
        attrs, inner = m.group(1), m.group(2)
        nums = []
        lm = re.search(r'lemma="([^"]*)"', attrs)
        if lm:
            for tok in lm.group(1).split():
                if tok.startswith("strong:"):
                    nums.append(tok[7:].upper())
        inner = re.sub(r"<[^>]*>", "", inner)  # nested tags (divineName already upper)
        inner = unescape(inner)
        out = []
        for w in inner.split():
            out.append(f"\x01{','.join(nums)}\x02{w}")
        stats["keyed_phrases"] += 1
        stats["keyed_words"] += len(out)
        if len(nums) > 1:
            stats["multi_strongs"] += len(out)
        return " " + " ".join(out) + " "
    t = re.sub(r"<w\b([^>]*)>(.*?)</w>", wsub, t, flags=re.S | re.I)
    # 7. added words -> placeholders with empty strongs
    def asub(m):
        inner = re.sub(r"<[^>]*>", "", m.group(1))
        inner = unescape(inner)
        out = [f"\x01\x02{w}" for w in inner.split()]
        stats["added_words"] += len(out)
        return " " + " ".join(out) + " "
    t = re.sub(r'<transChange\b[^>]*type="added"[^>]*>(.*?)</transChange>',
               asub, t, flags=re.S | re.I)
    t = re.sub(r"<transChange\b[^>]*>(.*?)</transChange>", r" \1 ", t, flags=re.S | re.I)
    # 8. strip any leftover tags, unescape entities
    leftover = re.findall(r"<[^>]*>", t)
    for lt in set(leftover):
        stats["leftover_tags"][lt[:60]] += 1
    t = re.sub(r"<[^>]*>", " ", t)
    t = unescape(t)
    # 9. tokenize
    words = []
    for tok in t.split():
        m = re.match(r"\x01([^\x02]*)\x02(.*)$", tok, re.S)
        if m:
            strongs, w = m.group(1), m.group(2)
        else:
            strongs, w = "", tok
            stats["bare_words"] += 1
        w = w.strip(STRIP_CHARS)
        if not w:
            if m and m.group(1):
                stats["punct_only_keyed"] += 1
            continue
        words.append((w, strongs))
    return words


def main():
    recs = decode_records()
    print(f"records: {len(recs)}")
    stats = Counter()
    stats["leftover_tags"] = Counter()
    rows = []
    book_num = ch = v = None
    seq = []  # (book_num, ch, v) for verification
    for e in recs:
        if not e.strip():
            continue
        if "x-importer" in e:
            continue
        # structural state updates (sID markers only; note "osisID" contains
        # "sID" as a substring, so require whitespace before sID to exclude
        # eID end-markers)
        for m in re.finditer(r'<div\b[^>]*type="book"[^>]*>', e):
            tag = m.group(0)
            if re.search(r"\ssID\s*=", tag):
                om = re.search(r'osisID="([A-Za-z0-9]+)"', tag)
                abbr = om.group(1) if om else None
                assert abbr in BOOK_ABBR, f"unknown book abbr {abbr}"
                book_num = BOOK_ABBR[abbr]
                ch = None
                v = 0
        for m in re.finditer(r"<chapter\b[^>]*\ssID\s*=[^>]*>", e):
            tag = m.group(0)
            om = re.search(r'osisID="[A-Za-z0-9]+\.(\d+)"', tag)
            assert om, f"chapter without osisID: {tag[:80]}"
            ch = int(om.group(1))
            v = 0
        words = verse_words(e, stats)
        if words:
            assert book_num is not None and ch is not None, \
                f"verse before book/chapter set: {e[:80]}"
            v += 1
            seq.append((book_num, ch, v))
            for pos, (w, s) in enumerate(words, 1):
                rows.append((book_num, ch, v, pos, w, s))

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write("book_num\tchapter\tverse\tkjv_pos\tkjv_word\tstrongs\n")
        for r in rows:
            # kjv_word/strongs contain no tabs by construction; guard anyway
            f.write("\t".join(str(x).replace("\t", " ") for x in r) + "\n")

    n_strongs = sum(1 for r in rows if r[5])
    print(f"verses: {len(seq)}, word rows: {len(rows)}, "
          f"with Strong's: {n_strongs} ({100.0*n_strongs/len(rows):.2f}%)")
    print(f"keyed phrases: {stats['keyed_phrases']}, keyed words: {stats['keyed_words']}, "
          f"multi-strongs words: {stats['multi_strongs']}")
    print(f"added words: {stats['added_words']}, bare words: {stats['bare_words']}, "
          f"punct-only keyed dropped: {stats['punct_only_keyed']}")
    if stats["leftover_tags"]:
        print("leftover tags:", dict(stats["leftover_tags"]))
    json.dump({"verses": len(seq), "rows": len(rows), "with_strongs": n_strongs,
               "keyed_phrases": stats["keyed_phrases"],
               "keyed_words": stats["keyed_words"],
               "multi_strongs": stats["multi_strongs"],
               "added_words": stats["added_words"],
               "bare_words": stats["bare_words"],
               "leftover_tags": dict(stats["leftover_tags"])},
              open(os.path.join(HERE, "parse_stats.json"), "w"), indent=1)
    json.dump(seq, open("/tmp/kjv_sword_seq.json", "w"))


if __name__ == "__main__":
    main()
