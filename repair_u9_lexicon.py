#!/usr/bin/env python3
"""U-9 follow-up: rebuild lexicon.kjv_renderings for the root_vowel entries
affected by the verse-remap KJV repair.

Same approach as repair_u8_lexicon.py: build_lexicon.py rebuilds the whole
lexicon table from scratch, which would destroy the ylt_renderings_computed
column it does not know about. This script instead recomputes the
kjv_renderings cell ONLY for the affected (root_id, root_form_seq,
vowel_seq) groups — those containing at least one word with a
method='verse-remap' rendering — using the exact same cell computation as
build_lexicon.py (distinct KJV words, most frequent first, ' | '-separated),
and UPDATEs those rows in place. All other lexicon columns and rows are
untouched.

Usage: repair_u9_lexicon.py --db PATH [--dry-run]
"""
import argparse, sqlite3
from collections import Counter, defaultdict

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--db', required=True)
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()
    con = sqlite3.connect(a.db)
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    repaired_wids = [r[0] for r in cur.execute(
        "SELECT DISTINCT word_id FROM kjv_renderings WHERE method='verse-remap'")]
    print('repaired word_ids:', len(repaired_wids))

    groups = defaultdict(set)
    for r in cur.execute(
            'SELECT word_id, root_id, root_form_seq, root_vowel_seq FROM words'):
        groups[(r['root_id'], r['root_form_seq'], r['root_vowel_seq'])].add(r['word_id'])
    affected = [g for g, wids in groups.items()
                if any(w in wids for w in set(repaired_wids))]
    print('affected lexicon groups:', len(affected))

    kjv = defaultdict(Counter)
    for wid, kw in cur.execute('SELECT word_id, kjv_word FROM kjv_renderings'):
        kjv[wid][kw] += 1

    updates = []
    empty_to_filled = 0
    changed = 0
    for g in affected:
        wids = groups[g]
        c = Counter()
        for wid in wids:
            c.update(kjv.get(wid, ()))
        # exact cell computation from build_lexicon.py
        cell = ' | '.join(w for w, _ in sorted(c.items(), key=lambda kv: (-kv[1], kv[0])))
        old = cur.execute(
            'SELECT kjv_renderings FROM lexicon WHERE root_id=? AND root_form_seq=? AND vowel_seq=?',
            g).fetchone()
        old_cell = old['kjv_renderings'] if old else None
        if old_cell != cell:
            changed += 1
            if not old_cell:
                empty_to_filled += 1
            updates.append((cell,) + g)
    print(f'groups needing update: {changed} (empty->filled: {empty_to_filled})')
    if updates and not a.dry_run:
        cur.executemany(
            'UPDATE lexicon SET kjv_renderings=? WHERE root_id=? AND root_form_seq=? AND vowel_seq=?',
            updates)
        con.commit()
        print('updated', cur.execute('SELECT changes()').fetchone()[0], 'rows (last statement)')
    elif a.dry_run:
        print('dry-run: wrote nothing; sample:')
        for u in updates[:5]:
            print(' ', u[1:], '->', u[0][:120])
    con.close()

if __name__ == '__main__':
    main()
