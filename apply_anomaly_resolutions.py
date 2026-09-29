#!/usr/bin/env python3
"""Apply the OSHB-verified unpointed/letters anomaly resolutions
(anomaly_resolutions.json) to the primary words columns of bible_v2.db.

Research state (2026-09-28/29): anomaly_resolutions.json holds 129
OSHB-verbatim-evidenced corrections for corrupt words.unpointed/letters
(108 truncation-at-maqaf, 20 wrong-row-data, 1 token-split-misalignment;
128 high / 1 medium confidence, 0 unresolved), staged in word_variants
(seq 1 = v1-stored, seq 2 = resolved in v1 convention, seq 3 = resolved in
academic convention) but NOT applied to words.

What this does, for the 128 HIGH-confidence word_ids only (the 1
medium-confidence record, word 104753, stays variants-only):
  1. UPDATE words SET unpointed=resolved_unpointed_v1conv,
     letters=resolved_letters_v1conv. The _v1conv forms preserve the
     v1-medial/hyphen-minus column convention per the file's _meta note
     (applying the OSHB-verbatim forms directly would break it).
  2. Re-derive root assignments with the same grouping rules as
     build_roots2.py/build_roots3.py: the root key is the corrected
     unpointed base (no new manual base_word exists, so the whole
     corrected unpointed form is the key -- the same fallback the
     builders used when base_word was empty); the affix tuple is carried
     over unchanged from the word's current root_form row (affixes were
     not adjudicated); the vowel tier keys on the unchanged pointed
     string. Existing root_entry/root_form/root_vowel IDs are fixed
     (no renumbering); new entries are APPENDED only when a corrected
     base/affix-tuple/pointed has no row. words.root_id/root_form_seq/
     root_vowel_seq are re-pointed; word_counts and the lowest-word_id
     example_pointed/example_unpointed are recomputed for touched rows.
     Old roots left at word_count 0 are kept (no renumbering) and logged.
  3. Rebuild the lexicon child cells for every touched root_vowel group
     (groups that gained or lost a word) with the exact cell computations
     of build_lexicon.py / build_lexicon_ylt.py:
       kjv_renderings: distinct KJV words, (-count, word) order
       ylt_renderings_computed: distinct YLT words, (-count, word.lower()) order
       ylt_contexts: sorted verses present in ylt_verses, (seq, verse_id, text)
       found_verses: sorted verses
     Only touched groups are rewritten (precedent: repair_u8_lexicon.py,
     repair_u9_lexicon.py); child rows are rewritten only when the
     recomputed cell differs.
  4. Verification (also in verify_anomaly.py, which diffs against the
     pristine backup): PRAGMA foreign_key_check = 0; every applied value
     equals its word_variants seq-2 staged value (128/128); the
     migrate_v2.py candidate-derivation rule reproduces the applied
     values (127/128 -- word 71448 has empty pointed by design, its value
     was already correct and unchanged; see the resolution note).

Idempotent: re-running re-verifies preconditions (already-resolved values
are accepted), recomputes identical targets, and writes nothing new.
Backups: the caller backs up bible_v2.db and runs this against a work
copy (--db). This script never touches bible.db (v1) or the website.

Usage: apply_anomaly_resolutions.py --db PATH [--dry-run] [--limit N]
"""
import argparse, json, os, sqlite3, sys
from collections import Counter, defaultdict

BASE = os.path.dirname(os.path.abspath(__file__))
RESOLUTIONS = os.path.join(BASE, 'anomaly_resolutions.json')
SKIP_WID = 104753  # the single medium-confidence record: variants-only

AFF = ['prefix1', 'prefix2', 'prefix3', 'suffix1', 'suffix2']
DISP = ['prefix1_disp', 'prefix2_disp', 'prefix3_disp', 'suffix1_disp', 'suffix2_disp']

def affkey(row):
    return tuple(row[c] or '' for c in AFF)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--db', required=True)
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--limit', type=int, default=None,
                    help='slice-test: only process the first N word_ids')
    a = ap.parse_args()

    with open(RESOLUTIONS, encoding='utf-8') as f:
        data = json.load(f)
    assert '_meta' in data, 'resolutions file missing _meta'
    recs = [(int(k), v) for k, v in data.items() if k != '_meta']
    high = [(k, v) for k, v in recs if v['confidence'] == 'high']
    med = [(k, v) for k, v in recs if v['confidence'] != 'high']
    assert len(high) == 128, f'expected 128 high-confidence, got {len(high)}'
    assert len(med) == 1 and med[0][0] == SKIP_WID, f'unexpected non-high set: {[k for k,_ in med]}'
    print(f'resolutions: 128 high (apply), 1 medium (word {SKIP_WID}, variants-only)')
    if a.limit:
        high = high[:a.limit]
        print(f'slice-test: first {len(high)} word_ids')

    con = sqlite3.connect(a.db)
    con.row_factory = sqlite3.Row
    con.execute('PRAGMA foreign_keys=ON')
    cur = con.cursor()

    # ---- 1. preconditions + primary column updates ----
    wsel = ('SELECT w.word_id, w.unpointed, w.letters, w.pointed, w.root_id,'
            ' w.root_form_seq, w.root_vowel_seq,'
            + ', '.join(f'f.{c}' for c in AFF + DISP)
            + ' FROM words w JOIN root_form f'
            ' ON f.root_id=w.root_id AND f.form_seq=w.root_form_seq'
            ' WHERE w.word_id=?')
    words_upd = []      # (unpointed, letters, word_id)
    pre_ok = pre_already = 0
    info = {}           # wid -> dict with current cols + resolution
    for wid, v in high:
        r = cur.execute(wsel, (wid,)).fetchone()
        assert r is not None, f'word {wid} missing from words'
        new_u = v['resolved_unpointed_v1conv']
        new_l = v['resolved_letters_v1conv']
        assert new_u is not None and new_l is not None, f'word {wid}: missing _v1conv value'
        cur_u, cur_l = r['unpointed'], r['letters']
        if (cur_u, cur_l) == (new_u, new_l):
            pre_already += 1
        else:
            assert (cur_u, cur_l) == (v['v1_unpointed'], v['v1_letters']), (
                f'word {wid}: current {(cur_u, cur_l)} != v1 {(v["v1_unpointed"], v["v1_letters"])}')
            pre_ok += 1
            words_upd.append((new_u, new_l, wid))
        info[wid] = {'row': r, 'new_u': new_u, 'new_l': new_l,
                     'old_key': (r['root_id'], r['root_form_seq'], r['root_vowel_seq'])}
    print(f'preconditions: {pre_ok} to update, {pre_already} already applied')

    # ---- 2. root re-derivation ----
    root_id_of = {r['root']: r['root_id'] for r in cur.execute('SELECT root_id, root FROM root_entry')}
    next_root_id = max(root_id_of.values()) + 1
    def get_root_id(base):
        nonlocal next_root_id
        rid = root_id_of.get(base)
        if rid is None:
            rid = next_root_id; next_root_id += 1
            root_id_of[base] = rid
            cur.execute('INSERT INTO root_entry(root_id, root, word_count) VALUES (?,?,0)', (rid, base))
        return rid

    form_seq_of = {}
    for r in cur.execute('SELECT root_id, form_seq, ' + ', '.join(AFF) + ' FROM root_form'):
        form_seq_of[(r['root_id'], affkey(r))] = r['form_seq']
    def get_form_seq(rid, tkey, disp_vals):
        key = (rid, tkey)
        fs = form_seq_of.get(key)
        if fs is None:
            fs = (cur.execute('SELECT COALESCE(MAX(form_seq),0) FROM root_form WHERE root_id=?',
                              (rid,)).fetchone()[0] or 0) + 1
            form_seq_of[key] = fs
            cols = ['root_id', 'form_seq'] + AFF + DISP + ['word_count']
            cur.execute(
                f'INSERT INTO root_form({",".join(cols)}) VALUES ('
                + ','.join('?' * len(cols)) + ')',
                (rid, fs) + tkey + disp_vals + (0,))
        return fs

    vowel_seq_of = {}
    for r in cur.execute('SELECT root_id, root_form_seq, vowel_seq, vowel_pattern FROM root_vowel'):
        vowel_seq_of[(r['root_id'], r['root_form_seq'], r['vowel_pattern'])] = r['vowel_seq']
    def get_vowel_seq(rid, fs, pointed):
        key = (rid, fs, pointed or '')
        vs = vowel_seq_of.get(key)
        if vs is None:
            vs = (cur.execute('SELECT COALESCE(MAX(vowel_seq),0) FROM root_vowel'
                              ' WHERE root_id=? AND root_form_seq=?', (rid, fs)).fetchone()[0] or 0) + 1
            vowel_seq_of[key] = vs
            cur.execute('INSERT INTO root_vowel(root_id, root_form_seq, vowel_seq, vowel_pattern, word_count)'
                        ' VALUES (?,?,?,?,0)', (rid, fs, vs, pointed))
        return vs

    root_upd = []       # (root_id, form_seq, vowel_seq, word_id)
    touched_roots, touched_forms, touched_vowels = set(), set(), set()
    new_roots, new_forms, new_vowels = [], [], []
    moves = []          # (wid, old_root_code, new_root_code)
    for wid, v in high:
        d = info[wid]
        r = d['row']
        new_base = d['new_u']
        tkey = affkey(r)
        disp_vals = tuple(r[c] for c in DISP)
        rid = get_root_id(new_base)
        fs = get_form_seq(rid, tkey, disp_vals)
        vs = get_vowel_seq(rid, fs, r['pointed'])
        old_key = d['old_key']
        new_key = (rid, fs, vs)
        d['new_key'] = new_key
        if old_key != new_key:
            root_upd.append((rid, fs, vs, wid))
            moves.append((wid, f'{old_key[0]}.{old_key[1]}.{old_key[2]}',
                          f'{rid}.{fs}.{vs}'))
        touched_roots.update([old_key[0], rid])
        touched_forms.update([(old_key[0], old_key[1]), (rid, fs)])
        touched_vowels.update([old_key, new_key])
    print(f'root re-derivation: {len(root_upd)} words re-pointed, {len(moves)} moves logged')

    if not a.dry_run:
        if words_upd:
            cur.executemany('UPDATE words SET unpointed=?, letters=? WHERE word_id=?', words_upd)
        if root_upd:
            cur.executemany(
                'UPDATE words SET root_id=?, root_form_seq=?, root_vowel_seq=? WHERE word_id=?',
                root_upd)

    # ---- word_counts + examples on touched rows ----
    for rid in touched_roots:
        n = cur.execute('SELECT COUNT(*) FROM words WHERE root_id=?', (rid,)).fetchone()[0]
        if not a.dry_run:
            cur.execute('UPDATE root_entry SET word_count=? WHERE root_id=?', (n, rid))
    for rid, fs in touched_forms:
        n = cur.execute('SELECT COUNT(*) FROM words WHERE root_id=? AND root_form_seq=?',
                        (rid, fs)).fetchone()[0]
        ex = cur.execute('SELECT pointed, unpointed FROM words WHERE root_id=? AND root_form_seq=?'
                         ' ORDER BY word_id LIMIT 1', (rid, fs)).fetchone()
        if not a.dry_run:
            cur.execute('UPDATE root_form SET word_count=?, example_pointed=?, example_unpointed=?'
                        ' WHERE root_id=? AND form_seq=?',
                        (n, ex['pointed'] if ex else None, ex['unpointed'] if ex else None, rid, fs))
    for rid, fs, vs in touched_vowels:
        n = cur.execute('SELECT COUNT(*) FROM words WHERE root_id=? AND root_form_seq=?'
                        ' AND root_vowel_seq=?', (rid, fs, vs)).fetchone()[0]
        if not a.dry_run:
            cur.execute('UPDATE root_vowel SET word_count=? WHERE root_id=? AND root_form_seq=?'
                        ' AND vowel_seq=?', (n, rid, fs, vs))
    # lexicon headers for any new root_vowel rows
    if not a.dry_run:
        cur.execute('INSERT OR IGNORE INTO lexicon(root_id, root_form_seq, vowel_seq)'
                    ' SELECT root_id, root_form_seq, vowel_seq FROM root_vowel')

    # ---- 3. lexicon cells for touched groups ----
    # group membership (all words; recompute touched only)
    groups = defaultdict(set)
    for r in cur.execute('SELECT word_id, root_id, root_form_seq, root_vowel_seq FROM words'):
        groups[(r['root_id'], r['root_form_seq'], r['root_vowel_seq'])].add(r['word_id'])
    kjv = defaultdict(Counter)
    for wid, kw in cur.execute('SELECT word_id, kjv_word FROM kjv_renderings'):
        kjv[wid][kw] += 1
    yltw = defaultdict(Counter)
    for wid, yw in cur.execute('SELECT word_id, ylt_word FROM ylt_renderings'):
        yltw[wid][yw] += 1
    books = {r['book_id']: r['name_en'] for r in cur.execute('SELECT book_id, name_en FROM books')}
    ylt_text = {r['verse_id']: r['text'] for r in cur.execute('SELECT verse_id, text FROM ylt_verses')}
    wverse = {}
    wverse_by_bcv = {}
    for r in cur.execute('SELECT w.word_id, v.book_id, v.chapter, v.verse, v.verse_id'
                         ' FROM words w JOIN verses v ON v.verse_id=w.verse_id'):
        wverse[r['word_id']] = (r['book_id'], r['chapter'], r['verse'], r['verse_id'])
        wverse_by_bcv[(r['book_id'], r['chapter'], r['verse'])] = r['verse_id']

    def ref(b, c, v):
        return f"{books.get(b, b)} {c}:{v}"

    lex_updates = {'kjv': 0, 'ylt': 0, 'ctx': 0, 'fv': 0}
    for g in sorted(touched_vowels):
        members = groups.get(g, set())
        # kjv_renderings: exact build_lexicon.py ordering
        c = Counter()
        for wid in members:
            c.update(kjv.get(wid, ()))
        kjv_list = [w for w, _ in sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))]
        # ylt_renderings_computed: exact build_lexicon_ylt.py ordering
        cy = Counter()
        for wid in members:
            cy.update(yltw.get(wid, ()))
        ylt_list = [w for w, _ in sorted(cy.items(), key=lambda kv: (-kv[1], kv[0].lower()))]
        # ylt_contexts / found_verses: exact build_lexicon.py verse handling
        verses = sorted({wverse[wid][:3] for wid in members if wid in wverse})
        ctx_rows = [(i, wverse_by_bcv[(b, ch, v)], ylt_text[wverse_by_bcv[(b, ch, v)]])
                    for i, (b, ch, v) in enumerate(verses)
                    if (b, ch, v) in wverse_by_bcv and wverse_by_bcv[(b, ch, v)] in ylt_text]
        fv_rows = [wverse_by_bcv[(b, ch, v)] for (b, ch, v) in verses if (b, ch, v) in wverse_by_bcv]

        if a.dry_run:
            continue
        # compare + rewrite child tables only on change
        old_k = [r[0] for r in cur.execute(
            'SELECT rendering FROM lexicon_kjv_rendering WHERE root_id=? AND root_form_seq=?'
            ' AND vowel_seq=? ORDER BY seq', g)]
        if old_k != kjv_list:
            cur.execute('DELETE FROM lexicon_kjv_rendering WHERE root_id=? AND root_form_seq=?'
                        ' AND vowel_seq=?', g)
            cur.executemany('INSERT INTO lexicon_kjv_rendering VALUES (?,?,?,?,?)',
                            [(g[0], g[1], g[2], i, w) for i, w in enumerate(kjv_list)])
            lex_updates['kjv'] += 1
        old_y = [r[0] for r in cur.execute(
            'SELECT rendering FROM lexicon_ylt_rendering WHERE root_id=? AND root_form_seq=?'
            ' AND vowel_seq=? ORDER BY seq', g)]
        if old_y != ylt_list:
            cur.execute('DELETE FROM lexicon_ylt_rendering WHERE root_id=? AND root_form_seq=?'
                        ' AND vowel_seq=?', g)
            cur.executemany('INSERT INTO lexicon_ylt_rendering VALUES (?,?,?,?,?)',
                            [(g[0], g[1], g[2], i, w) for i, w in enumerate(ylt_list)])
            lex_updates['ylt'] += 1
        old_c = [(r[0], r[1]) for r in cur.execute(
            'SELECT verse_id, context_text FROM lexicon_ylt_context WHERE root_id=?'
            ' AND root_form_seq=? AND vowel_seq=? ORDER BY seq', g)]
        new_c = [(vid, txt) for _, vid, txt in ctx_rows]
        if old_c != new_c:
            cur.execute('DELETE FROM lexicon_ylt_context WHERE root_id=? AND root_form_seq=?'
                        ' AND vowel_seq=?', g)
            cur.executemany('INSERT INTO lexicon_ylt_context VALUES (?,?,?,?,?,?)',
                            [(g[0], g[1], g[2], i, vid, txt) for i, vid, txt in ctx_rows])
            lex_updates['ctx'] += 1
        old_f = [r[0] for r in cur.execute(
            'SELECT verse_id FROM lexicon_found_verse WHERE root_id=? AND root_form_seq=?'
            ' AND vowel_seq=? ORDER BY rowid', g)]
        if old_f != fv_rows:
            cur.execute('DELETE FROM lexicon_found_verse WHERE root_id=? AND root_form_seq=?'
                        ' AND vowel_seq=?', g)
            cur.executemany('INSERT INTO lexicon_found_verse VALUES (?,?,?,?)',
                            [(g[0], g[1], g[2], vid) for vid in fv_rows])
            lex_updates['fv'] += 1
    print(f'lexicon touched groups: {len(touched_vowels)}; cells rewritten: {lex_updates}')

    # ---- 4. in-script verification ----
    # applied values == staged word_variants seq 2 (v1 convention)
    var2 = {r['word_id']: (r['unpointed'], r['letters']) for r in cur.execute(
        "SELECT word_id, unpointed, letters FROM word_variants WHERE variant_seq=2"
        " AND convention='v1-medial'")}
    mism = [wid for wid, v in high
            if var2.get(wid) != (v['resolved_unpointed_v1conv'], v['resolved_letters_v1conv'])]
    assert not mism, f'resolved values differ from staged seq-2 variants: {mism[:5]}'
    if not a.dry_run:
        dbsig = [(wid,
                  cur.execute('SELECT unpointed, letters FROM words WHERE word_id=?',
                              (wid,)).fetchone()) for wid, _ in high]
        bad = [wid for wid, r in dbsig
               if (r['unpointed'], r['letters']) != var2[wid]]
        assert not bad, f'applied values differ from staged variants: {bad[:5]}'
        print(f'verification: applied == staged word_variants seq2 for {len(high)}/{len(high)}')
    else:
        print(f'verification (dry-run): resolved == staged seq2 for {len(high) - len(mism)}/{len(high)}')
    fk = cur.execute('PRAGMA foreign_key_check').fetchall()
    assert not fk, f'FK violations: {fk[:5]}'
    print('verification: 0 FK violations')
    # root/lexicon count reconciliation
    n_words = cur.execute('SELECT COUNT(*) FROM words').fetchone()[0]
    assert n_words == 264217, n_words
    for tbl, col, grp in [('root_entry', 'word_count', 'root_id'),
                          ('root_form', 'word_count', 'root_id, form_seq'),
                          ('root_vowel', 'word_count', 'root_id, root_form_seq, vowel_seq')]:
        s = cur.execute(f'SELECT SUM({col}) FROM {tbl}').fetchone()[0]
        assert s == n_words, f'{tbl} word sum {s} != {n_words}'
    print('verification: root word_counts reconcile to 264,217')

    if a.dry_run:
        con.rollback()
        print('dry-run: rolled back, wrote nothing')
    else:
        con.commit()
        print('committed')
    # moves log to stdout for the record
    print('--- moves (word_id old_root_code -> new_root_code) ---')
    for wid, o, n in moves:
        print(f'{wid} {o} -> {n}')
    # abandoned roots
    abandoned = []
    for rid in sorted(touched_roots):
        n = cur.execute('SELECT word_count FROM root_entry WHERE root_id=?', (rid,)).fetchone()[0]
        if n == 0:
            root = cur.execute('SELECT root FROM root_entry WHERE root_id=?', (rid,)).fetchone()[0]
            abandoned.append((rid, root))
    print(f'--- abandoned roots (word_count 0): {len(abandoned)} ---')
    for rid, root in abandoned:
        print(f'{rid} {root!r}')
    con.close()

if __name__ == '__main__':
    main()
