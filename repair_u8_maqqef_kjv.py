#!/usr/bin/env python3
"""U-8: repair the maqqef-split KJV alignment gap.

Context (NOTATION_LEDGER.md U-8): 258,209/264,217 words carry Strong's but
only 204,701 have a KJV rendering. Diagnosis (u8_diagnosis.json) buckets the
53,508-word gap:
  - 4,945 maqqef-split words (strongs_source='oshb-split'): REPAIRABLE.
    The crosswalk kept the LAST paired component's Strong's on the word, but
    the KJV+Strong's source tags English words with the OTHER components'
    Strong's (e.g. וַֽיְהִי־כֵֽן׃ kept H3651; KJV "was" is tagged H1961).
  - 45,582 words whose Strong's appears on no KJV word in the verse: NOT
    repairable — the KJV+Strong's dataset genuinely tags those English words
    with a different Strong's (phrase-level tagging); guessing would be
    fabrication.
  - 2,106 words in verses missing from the KJV dataset (versification
    offsets, e.g. Gen 32:33 = KJV 32:32): NOT repaired here (needs a
    verified verse-remap, a separate item).
  - 875 Aramaic words: same untranslatable-implicitly class as the 45,582.

Repair: for each maqqef-split word WITH Strong's but ZERO kjv_renderings
rows, propagate KJV tokens matched via the OSHB-split sub-token Strong's
alignments to the parent word_id. Existing kjv_renderings rows are never
modified or deleted; new rows carry method='maqqef-component' (existing
rows are backfilled method='direct') so the table stays honest about
which rows came from the repair.

The sub-token pairing is reproduced by re-running the crosswalk's own
align_verse machinery (copied verbatim from assemble_bible.py, 2026-09-24
crosswalk) against the same worker-out/oshb/oshb_words.tsv, so the
component Strong's are the crosswalk's own pairings, not a new guess.

Reads:  --db (working copy of bible.db), worker-out/oshb/oshb_words.tsv,
         worker-out/kjv/kjv_words.tsv is NOT re-read (kjv_words table is
         already in the DB and is left untouched).
Writes: kjv_renderings only (new `method` column + INSERTs).
Raw Kit parse columns and the words table are NEVER touched.

Usage: repair_u8_maqqef_kjv.py --db PATH [--limit N] [--dry-run]
  --limit N  repair at most N gap maqqef words (slice test)
  --dry-run  compute and report, write nothing
"""
import argparse, csv, difflib, re, sqlite3, sys

# ---------------------------------------------------------------------------
# Copied verbatim from assemble_bible.py (2026-09-24 crosswalk) so the
# component pairings are identical to the ones the crosswalk used.
# ---------------------------------------------------------------------------
HNUM = re.compile(r'H0*(\d+)')
def norm_strongs(s):
    if not s: return None
    s = str(s).strip().upper().replace(' ', '')
    m = re.match(r'^H?0*(\d+)$', s)
    if m: return f'H{int(m.group(1))}'
    return None
def multi_strongs(s):
    out = []
    for tok in re.split(r'[;,/|\s]+', str(s or '')):
        n = norm_strongs(tok)
        if n and n not in out: out.append(n)
    return out
VERSE_REMAP = {(19, 17, 17): (19, 17, 1), (23, 27, 22): (23, 27, 1),
               (24, 28, 23): (24, 28, 1), (25, 2, 23): (25, 2, 1)}
MAQQEF = '־'
SOFIT_FOLD = {'ך': 'כ', 'ם': 'מ', 'ן': 'נ', 'ף': 'פ', 'ץ': 'צ'}
def cons_key(s):
    return ''.join(SOFIT_FOLD.get(ch, ch) for ch in (s or '') if 'א' <= ch <= 'ת')
def find_unconsumed(key, owords, consumed, bkeys):
    if not key:
        return None
    for j, (used, bk) in enumerate(zip(consumed, bkeys)):
        if not used and bk == key:
            return j
    return None
def align_verse(cwords, owords):
    pseudo = []
    for w in cwords:
        pt = w['word_pointed'] or ''
        if MAQQEF in pt:
            comps = [cons_key(p) for p in pt.split(MAQQEF)]
            if len(comps) > 1 and all(comps):
                for ci, ck in enumerate(comps):
                    pseudo.append((w, ck, ci, len(comps)))
                continue
        pseudo.append((w, cons_key(w['letters']), 0, 1))
    a = [p[1] for p in pseudo]
    b = [cons_key(r['unpointed']) for r in owords]
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    out = []
    consumed = [False] * len(owords)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'equal':
            for i, j in zip(range(i1, i2), range(j1, j2)):
                consumed[j] = True
                out.append((pseudo[i], owords[j], '1to1'))
        elif tag == 'replace':
            ca = ''.join(a[i1:i2]); cb = ''.join(b[j1:j2])
            if ca == cb and ca:
                if (i2 - i1) == (j2 - j1):
                    for i, j in zip(range(i1, i2), range(j1, j2)):
                        consumed[j] = True
                        out.append((pseudo[i], owords[j], 'replace'))
                else:
                    for i in range(i1, i2):
                        best = max(range(j1, j2), key=lambda j: len(b[j]))
                        consumed[best] = True
                        out.append((pseudo[i], owords[best], 'replace'))
            else:
                for i in range(i1, i2):
                    j = find_unconsumed(a[i], owords, consumed, b)
                    if j is not None:
                        consumed[j] = True
                        out.append((pseudo[i], owords[j], 'fallback'))
                    else:
                        out.append((pseudo[i], None, 'unmapped'))
        elif tag == 'delete':
            for i in range(i1, i2):
                j = find_unconsumed(a[i], owords, consumed, b)
                if j is not None:
                    consumed[j] = True
                    out.append((pseudo[i], owords[j], 'fallback'))
                else:
                    out.append((pseudo[i], None, 'unmapped'))
    return out
# ---------------------------------------------------------------------------
# end of copied crosswalk machinery
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--db', required=True)
    ap.add_argument('--oshb', default='/home/hatch/workspace/bible-project/worker-out/oshb/oshb_words.tsv')
    ap.add_argument('--limit', type=int, default=None)
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()

    con = sqlite3.connect(a.db)
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    cols = [r[1] for r in cur.execute('PRAGMA table_info(kjv_renderings)')]
    if 'method' not in cols:
        if not a.dry_run:
            cur.execute('ALTER TABLE kjv_renderings ADD COLUMN method TEXT')
            cur.execute("UPDATE kjv_renderings SET method='direct' WHERE method IS NULL")
            con.commit()
        print('added method column; existing rows -> direct')

    existing = set((r[0], r[1]) for r in
                   cur.execute('SELECT word_id, kjv_word FROM kjv_renderings'))

    # gap maqqef words: Strong's present, zero renderings, maqqef in pointed
    gap = [dict(r) for r in cur.execute('''SELECT w.word_id, w.book, w.chapter, w.verse,
        w.word_pos, w.word_pointed, w.letters, w.strongs
      FROM words w LEFT JOIN kjv_renderings k ON k.word_id = w.word_id
      WHERE w.strongs IS NOT NULL AND k.word_id IS NULL
        AND w.word_pointed LIKE '%־%' ORDER BY w.word_id''')]
    print(f'gap maqqef words: {len(gap)}')
    if a.limit:
        gap = gap[:a.limit]
        print(f'slice: first {len(gap)}')

    # OSHB by verse
    oshb_by_verse = {}
    with open(a.oshb, encoding='utf-8') as f:
        for r in csv.DictReader(f, delimiter='\t'):
            key = (int(r['book_num']), int(r['chapter']), int(r['verse']))
            oshb_by_verse.setdefault(key, []).append(r)
    for v in oshb_by_verse.values():
        v.sort(key=lambda r: int(r['word_pos']))

    # KJV words by verse: list of (kjv_word, strongs_set, strongs_raw)
    kjv_by_verse = {}
    for b, ch, v, kw, ks in cur.execute(
            'SELECT book, chapter, verse, kjv_word, strongs FROM kjv_words'):
        kjv_by_verse.setdefault((b, ch, v), []).append((kw, set(multi_strongs(ks)), ks))

    new_rows = []
    stats = {'words_repaired': 0, 'rows_added': 0, 'words_no_kjv_match': 0,
             'words_no_pairing': 0, 'extra_strongs_total': 0}
    seen_new = set()
    for w in gap:
        ckey = (w['book'], w['chapter'], w['verse'])
        owords = oshb_by_verse.get(VERSE_REMAP.get(ckey, ckey))
        if not owords:
            stats['words_no_pairing'] += 1
            continue
        pairs = align_verse([w], owords)
        extra = set()
        for (pw, key, ci, nc), orow, how in pairs:
            if orow is None:
                continue
            for s in multi_strongs(orow['strongs']):
                if s != w['strongs']:
                    extra.add(s)
        if not extra:
            stats['words_no_pairing'] += 1
            continue
        stats['extra_strongs_total'] += len(extra)
        added_here = 0
        for s in sorted(extra):
            for kw, ks, ks_raw in kjv_by_verse.get(ckey, []):
                if s in ks and (w['word_id'], kw) not in existing \
                        and (w['word_id'], kw) not in seen_new:
                    new_rows.append((w['word_id'], kw, ks_raw, 'maqqef-component'))
                    seen_new.add((w['word_id'], kw))
                    added_here += 1
        if added_here:
            stats['words_repaired'] += 1
            stats['rows_added'] += added_here
        else:
            stats['words_no_kjv_match'] += 1

    print('stats:', stats)
    if a.dry_run:
        print('dry-run: wrote nothing; sample new rows:')
        for r in new_rows[:20]:
            print(' ', r)
    else:
        cur.executemany(
            'INSERT INTO kjv_renderings(word_id, kjv_word, kjv_strongs, method)'
            ' VALUES (?,?,?,?)', new_rows)
        con.commit()
        print(f'inserted {len(new_rows)} rows')
    con.close()

if __name__ == '__main__':
    main()
