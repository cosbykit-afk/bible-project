OSHB word list — README
============================
Directory: ~/workspace/bible-project/worker-out/oshb/
Built: 2026-09-20. Parser: parse_oshb.py (rerunnable; reads the XML below).

SOURCE
------
Open Scriptures Hebrew Bible (morphhb)
  https://github.com/openscriptures/morphhb
  commit 3d15126fb1ef74867fc1434be1942e837932691f (2024-08-27)
Parsed files: wlc/*.xml, one per book (39 books). wlc/VerseMap.xml was used
only as a reference for versification differences; it is not in the TSV.

LICENSE (verified from the repo itself — free, constraint satisfied)
--------------------------------------------------------------------
LICENSE.md (repo root) states:

  "This work is based on *The Westminster Leningrad Codex*, which is in the
  public domain.
   ...
   Creative Commons Attribution 4.0 International (CC BY 4.0)
   ... Attribution — You must attribute the work as follows: 'Original work
   of the Open Scriptures Hebrew Bible available at
   https://github.com/openscriptures/morphhb'."

README.md (repo root) confirms the split:
  "Lemma and morphology data are licensed under a Creative Commons
  Attribution 4.0 International license. ... The text of the WLC remains in
  the Public Domain."

So: the Hebrew text (WLC) is public domain; the lemma/morphology annotation
is CC-BY-4.0. Nothing copyrighted was downloaded or included. Any downstream
use of the lemma/morph/strongs columns must carry the attribution above.

FILES
-----
- oshb_words.tsv — 306,785 data rows + header, UTF-8, tab-separated, 15 MB.
  Columns: book_num | chapter | verse | word_pos | strongs | morph |
           pointed | unpointed
- parse_oshb.py — the parser that produced the TSV (stdlib only).
- parse_stats.json — aggregate counters from the parse run.
- parse_errors.log — empty (no parse errors).

COLUMN DEFINITIONS
------------------
- book_num: 1-39 in standard Protestant order
  (1 Genesis … 39 Malachi; full mapping in parse_oshb.py BOOKMAP/NAMES).
  Derived from each file's <div type="book" osisID="..."> (e.g. Gen -> 1).
- chapter, verse: integers from the verse's osisID (e.g. Gen.1.1).
  IMPORTANT: chapter:verse follow OSHB's own Masoretic (WLC) versification,
  which differs from KJV numbering in places — see "Versification" below.
- word_pos: 1-based position of the word within the verse, counting <w>
  elements in XML document order (which is the reading order). Includes the
  nested qere <w> elements: a ketiv word and its qere get consecutive
  positions (ketiv first). Verified: every verse's positions are exactly
  1..N with no gaps (checked over all 23,213 verses).
- strongs: OSHB @lemma normalized — every run of digits becomes "H"+digits;
  multiple numbers would be joined with ";" (never occurred: no lemma in the
  corpus contains two numbers; "1254 a" is number + disambiguation letter,
  not two numbers). Empty when the lemma has no digits (see below).
- morph: OSHB @morph verbatim (e.g. HR/Ncfsa; Aramaic forms start with "A",
  e.g. ANcmsd/Td). Every word has one.
- pointed: the <w> text exactly as in OSHB, including its "/" morpheme
  separators (e.g. "בְּ/רֵאשִׁית"). Maqqef/paseq/sof-pasuq are separate <seg>
  elements and are NOT merged into this text.
- unpointed: only codepoints U+05D0–U+05EA (א–ת, incl. final forms), in
  order, no separators or spaces (e.g. "בראשית").

TOTALS
------
- Words: 306,785. Verses: 23,213. Books: 39. Chapters: 929.
- Words with a Strong's number: 300,808 (98.052%).
- Words with no lemma/strongs: 5,977 (1.948%). Every word HAS a lemma
  attribute (no_lemma_attr = 0); these 5,977 have prefix-only lemmas with no
  digits and hence no Strong's number — standalone proclitics, e.g.
  lemma="l" (4,413×, preposition לְ), "b" (1,362×), "m" (92×), "c/l" (74×),
  "c/b" (16×), "k" (9×), "c/m" (6×), "s/l" (2×), "i", "i/l", "m/l" (1× each).
- multi-number lemmas: 0 in the whole corpus (the ";" join never triggers).
- Words with no morph: 0.

PER-BOOK WORD COUNTS (book_num: name — words)
  1 Genesis 20629 | 2 Exodus 16726 | 3 Leviticus 11955 | 4 Numbers 16422
  5 Deuteronomy 14320 | 6 Joshua 10083 | 7 Judges 9905 | 8 Ruth 1306
  9 1 Samuel 13335 | 10 2 Samuel 11130 | 11 1 Kings 13186 | 12 2 Kings 12354
  13 1 Chronicles 10790 | 14 2 Chronicles 13354 | 15 Ezra 3791
  16 Nehemiah 5336 | 17 Esther 3057 | 18 Job 8399 | 19 Psalms 19657
  20 Proverbs 6984 | 21 Ecclesiastes 2999 | 22 Song of Solomon 1255
  23 Isaiah 16988 | 24 Jeremiah 21976 | 25 Lamentations 1564
  26 Ezekiel 18866 | 27 Daniel 6035 | 28 Hosea 2386 | 29 Joel 958
  30 Amos 2045 | 31 Obadiah 292 | 32 Jonah 688 | 33 Micah 1400 | 34 Nahum 562
  35 Habakkuk 672 | 36 Zephaniah 769 | 37 Haggai 601 | 38 Zechariah 3134
  39 Malachi 876

ARAMAIC SECTIONS (Daniel 2:4b–7:28; Ezra 4:8–6:18, 7:12–26; Jer 10:11; Gen 31:47)
--------------------------------------------------------------------------------
4,948 words have morph starting with "A" (Aramaic). OSHB does NOT use a
separate lemma numbering for Aramaic: Aramaic lemmas use the same numeric
format as Hebrew (they are Strong's Hebrew-dictionary numbers, which include
the Aramaic entries), so they were normalized identically ("H"+digits).
The Hebrew/Aramaic distinction lives in the morph prefix, not the lemma.
Five samples (ref | lemma | morph | pointed | strongs):
  Dan 2:5  | 6032   | AVqrmsa    | עָנֵה       | H6032
  Dan 2:5  | 560    | AC/Vqrmsa  | וְ/אָמַר    | H560
  Gen 31:47| 3026 a | ANp        | יְגַר        | H3026
  Gen 31:47| 3026 b | ANp        | שָׂהֲדוּתָא   | H3026
  Ezra 4:8 | 7348 b | ANp        | רְחוּם       | H7348
  Ezra 4:8 | 5922   | AR         | עַל         | H5922
  Ezra 4:8 | c/8124 | AC/Np      | וְ/שִׁמְשַׁי  | H8124
(12 samples total in parse_stats.json "aramaic_samples".)
Verified transition: Dan 2:4 word 4 אֲרָמִית is still Hebrew morph (HNgfsa);
words 5+ switch to A- morphs (ANcmsd/Td, AR/Ncmpa, AVqv2ms, …).

PARSING ANOMALIES
-----------------
1. Ketiv/Qere. 1,268 <w type="x-ketiv"> words; each is followed by
   <note type="variant"><rdg type="x-qere"> containing the qere <w>(s).
   Both ketiv and qere are emitted as rows, ketiv first, consecutive
   word_pos (e.g. Ps 51:4: pos1 הרבה ketiv HVha, pos2 הֶרֶב qere HVhv2ms).
   Counts differ (1,278 qere words) because: 6 ketiv notes have an EMPTY
   qere (e.g. Ruth 3:5-area ketiv אם with <rdg type="x-qere"/>); 16 notes
   expand 1 ketiv word to 2 qere words (e.g. Ps 10:14 חלכאים →
   חֵיל כָּאִים); 9 notes contract 2 ketiv words to 1 qere word.
2. Maqqef splits. Words joined by maqqef are separate <w> elements with a
   <seg type="x-maqqef"> between them (42,577 maqqef segs); each side is its
   own TSV row (e.g. עַל and הָאָרֶץ). Likewise 2,278 x-paseq segs and
   23,192 x-sof-pasuq segs sit between words and are not attached to them.
   Rare segs also present: x-samekh (1,981), x-pe (1,181), x-reversednun
   (9, Num 10:35-36 / Ps 107), x-suspended (4: Judg 18:30, Ps 80:14,
   Job 38:13,15), x-large (4), x-small (3).
3. Versification. OSHB follows the Masoretic (WLC) versification:
   23,213 verses total. KJV/ESV numbering has 23,145 (per-chapter ESV table
   cross-checked; difference +68 fully reconciled):
     Psalms 2527 vs 2461 (+66): Psalm superscriptions are verses in the MT
       (long ones even two verses, e.g. Ps 51:1-2); KJV leaves them
       unnumbered. VerseMap.xml documents these (its Psalm pre-verse
       mappings are approximate — see its own XML comment).
     Numbers 1289 (+1): ch25 19v18, ch30 17v16.
     1 Samuel 811 (+1): ch21 16v15, ch23 28v29, ch24 23v22.
     1 Kings 817 (+1): ch22 54v53 (ch4/ch5 boundary shift is count-neutral).
     1 Chronicles 943 (+1): ch12 41v40 (ch5/ch6 boundary shift count-neutral).
     Nehemiah 405 (−1): ch7 72v73, ch9 37v38, ch10 40v39.
     Isaiah 1291 (−1): ch8 23v22 (8:23 = KJV 9:1), ch9 20v21,
       ch64 11v12 (KJV splits WLC 63:19).
   No verse sub-numbering (no "3a/3b") anywhere; every chapter's verses are
   sequential 1..N with no gaps or duplicates (asserted in the parse).
   wlc/VerseMap.xml in the source repo is the WLC↔KJV crosswalk.
4. The @n attribute (e.g. n="1.0.0") is NOT reading order — per the OSHB
   README it records cantillation divisions. Reading order = document order,
   which is what word_pos uses. The attribute was ignored.
5. OSHB <w> ids (e.g. id="01LXS", first two chars = book number) were not
   carried into the TSV; book_num+chapter+verse+word_pos is the key.

BUGS FOUND AND FIXED DURING THE BUILD (disclosed per project policy)
--------------------------------------------------------------------
- Namespace comparison built "...namespace}}seg" (double brace) → 0 words
  parsed; fixed.
- ElementTree iterparse 'start' events do not reliably have el.text
  (expat chunk buffering); word text is now captured at the 'end' event via
  itertext(). An early run silently dropped text on 404 words because of
  this — caught by the empty-pointed check, fixed, re-verified to 0.
- unpointed() lower bound was typed as U+0590 instead of U+05D0, so vowel
  points/accents leaked into the unpointed column; fixed to explicit
  '\u05d0'..'\u05ea' escapes and re-verified (0 non-alefbet chars).
Final TSV re-validated: 306,785 rows, 8 fields each, word_pos exactly 1..N
per verse, strongs all match H\d+(;H\d+)*, unpointed pure א–ת.

ATTRIBUTION (required by CC-BY-4.0 for the lemma/morph/strongs columns)
------------------------------------------------------------------------
"Original work of the Open Scriptures Hebrew Bible available at
https://github.com/openscriptures/morphhb"
