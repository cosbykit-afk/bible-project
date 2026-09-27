#!/usr/bin/env python3
"""U-9: repair the versification-offset KJV alignment gap.

Context (NOTATION_LEDGER.md U-9): 2,106 Strong's-carrying words sit in 206
Hebrew verses whose reference has no same-reference kjv_words rows (MT-vs-KJV
versification offsets, e.g. Gen 32:33 = KJV 32:32; Ex 7:26-29 = KJV 8:1-4;
Joel 4 = KJV 3; verse-1-at-end canon quirks Isa 27:22/Jer 28:23/Lam 2:23).
The direct alignment in assemble_bible.py only pairs same-reference verses,
so these words got zero KJV renderings.

Repair: pair each Hebrew word in a remapped verse to KJV rows in the VERIFIED
remap target verse using the exact normalized Strong's-sharing logic from
assemble_bible.py:

    for w in words:
        if not w['strongs']: continue
        for kw, ks in kjv_by_verse.get((w['book'], w['chapter'], w['verse']), []):
            if w['strongs'] in ks:
                rend.append((w['word_id'], kw, ','.join(ks)))

except the verse key is the verified remap target instead of the same
reference. kjv_strongs is stored as the normalized set joined by comma
(sorted for determinism — assemble_bible.py joined a set in arbitrary
order; the set CONTENT is identical). New rows carry method='verse-remap'.

Existing kjv_renderings rows are NEVER modified or deleted. Any new
(word_id, kjv_word) pair already present in the table (any method) is
skipped and counted, so no new row collides with an existing pair.
Words with no Strong's are skipped (no pairing possible); words whose
Strong's matches no KJV row in the remap target keep zero renderings.

The verse-remap table is the verified TSV produced by the U-9 diagnosis
(passed via --remap; adjudication in the U-9 ledger entry). Verses absent
from the TSV (Job 40:30, Psalm 39:14 if unmapped; the three no-Strong's
anomalies Josh 4:32 / Ruth 8:18 / 2Chr 36:32) are untouched.

Writes: kjv_renderings only (INSERTs with method='verse-remap').
The words table, kjv_words, and every other table are NEVER touched.

Usage: repair_u9_verse_remap_kjv.py --db PATH [--remap TSV] [--limit N] [--dry-run]
  --db PATH    working copy of bible.db (never operate on the live file)
  --remap TSV  verified verse-remap TSV (default: ./u9_verse_remap.tsv)
  --limit N    repair at most N remapped verses (slice test)
  --dry-run    compute and report, write nothing
"""
import argparse, csv, re, sqlite3, sys

def norm_strongs(s):
    """Copied from assemble_bible.py: normalize a Strong's token to H<num>."""
    if not s: return None
    s = str(s).strip().upper().replace(' ', '')
    m = re.match(r'^H?0*(\d+)$', s)
    if m: return f'H{int(m.group(1))}'
    return None

def multi_strongs(s):
    """Copied from assemble_bible.py: split multi-Strong's into normalized set."""
    out = []
    for tok in re.split(r'[;,/|\s]+', str(s or '')):
        n = norm_strongs(tok)
        if n and n not in out: out.append(n)
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--db', required=True)
    ap.add_argument('--remap', default='u9_verse_remap.tsv')
    ap.add_argument('--limit', type=int, default=None)
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()

    remap = []  # (heb_book, heb_ch, heb_v, kjv_ch, kjv_v)
    with open(a.remap, encoding='utf-8') as f:
        for r in csv.DictReader(f, delimiter='\t'):
            remap.append((int(r['heb_book']), int(r['heb_chapter']),
                          int(r['heb_verse']), int(r['kjv_chapter']),
                          int(r['kjv_verse'])))
    print(f'remap entries: {len(remap)}')
    if a.limit:
        remap = remap[:a.limit]
        print(f'slice: first {len(remap)} verses')

    con = sqlite3.connect(a.db)
    cur = con.cursor()
    cols = [r[1] for r in cur.execute('PRAGMA table_info(kjv_renderings)')]
    if 'method' not in cols:
        sys.exit('refusing: kjv_renderings has no method column (run repair_u8 first)')

    existing = set((r[0], r[1]) for r in
                   cur.execute('SELECT word_id, kjv_word FROM kjv_renderings'))

    # KJV words by verse: (kjv_word, normalized-strongs set), same as assembler
    kjv_by_verse = {}
    for b, ch, v, kw, ks in cur.execute(
            'SELECT book, chapter, verse, kjv_word, strongs FROM kjv_words'):
        kjv_by_verse.setdefault((b, ch, v), []).append((kw, set(multi_strongs(ks))))

    # Hebrew words by verse (words.strongs already normalized at build)
    heb_by_verse = {}
    for wid, b, ch, v, s in cur.execute(
            'SELECT word_id, book, chapter, verse, strongs FROM words'):
        heb_by_verse.setdefault((b, ch, v), []).append((wid, s))

    new_rows, seen_new = [], set()
    stats = {'verses': 0, 'words_considered': 0, 'words_no_strongs': 0,
             'words_repaired': 0, 'words_no_match': 0, 'rows_added': 0,
             'rows_skipped_existing': 0, 'rows_skipped_intradup': 0}
    for hb, hc, hv, kc, kv in remap:
        stats['verses'] += 1
        kjv_rows = kjv_by_verse.get((hb, kc, kv), [])
        for wid, s in heb_by_verse.get((hb, hc, hv), []):
            if not s:
                stats['words_no_strongs'] += 1
                continue
            stats['words_considered'] += 1
            added = 0
            for kw, ks in kjv_rows:
                if s in ks:
                    if (wid, kw) in existing:
                        stats['rows_skipped_existing'] += 1
                        continue
                    if (wid, kw) in seen_new:
                        # same English token repeated in the KJV verse with a
                        # Strong's set containing s: one row per (word,kjv_word)
                        # is enough; the assembler's per-token duplicates are
                        # not reproduced.
                        stats['rows_skipped_intradup'] += 1
                        continue
                    new_rows.append((wid, kw, ','.join(sorted(ks)), 'verse-remap'))
                    seen_new.add((wid, kw))
                    added += 1
            if added:
                stats['words_repaired'] += 1
                stats['rows_added'] += added
            else:
                stats['words_no_match'] += 1

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
        print(f'inserted {len(new_rows)} verse-remap rows')
    con.close()

if __name__ == '__main__':
    main()
