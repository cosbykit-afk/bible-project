#!/usr/bin/env python3
"""U-7: normalize affix columns to Hebrew letters (display layer).

Reads the raw affix columns (prefix1/prefix2/prefix3/suffix1/suffix2) and
writes NEW display columns (prefix1_disp/.../suffix2_disp) on the words table.
Raw columns are NEVER touched: root_code grouping depends on the exact
original tuples.

Mapping (English glosses -> Hebrew letter):
  'and, but' -> ו   'to, for' -> ל   'in, with, by' -> ב   'from' -> מ
  'as, like' -> כ   'that, which, who, whom' -> ש
  'The, ?' / 'the, ?' -> ה, verified per-row positionally (the word, with
      maqqef stripped, must have ה at the position after the earlier prefixes)
All other values (already-Hebrew letters, maqqef-joined forms like את-ה)
pass through unchanged.

Usage: normalize_affixes.py [--db PATH] [--limit N]
"""
import argparse, re, sqlite3, sys

MAP = {
    'and, but': 'ו',
    'to, for': 'ל',
    'in, with, by': 'ב',
    'from': 'מ',
    'as, like': 'כ',
    'that, which, who, whom': 'ש',
    'The, ?': 'ה',
    'the, ?': 'ה',
}
MAQ = '\u05be'
LATIN = re.compile(r'[A-Za-z]')
DISP = ['prefix1_disp', 'prefix2_disp', 'prefix3_disp', 'suffix1_disp', 'suffix2_disp']
RAW = ['prefix1', 'prefix2', 'prefix3', 'suffix1', 'suffix2']

def stripm(s):
    return (s or '').replace(MAQ, '')

def disp_of(v):
    if v is None or v == '':
        return ''
    return MAP.get(v, v)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--db', default='bible.db')
    ap.add_argument('--limit', type=int, default=0)
    a = ap.parse_args()

    con = sqlite3.connect(a.db)
    cur = con.cursor()
    cols = {r[1] for r in cur.execute('PRAGMA table_info(words)')}
    for d in DISP:
        if d not in cols:
            cur.execute(f'ALTER TABLE words ADD COLUMN {d} TEXT DEFAULT NULL')

    # pre-flight: every Latin-containing raw value must be in the map
    for c in ['prefix1', 'prefix2', 'prefix3']:
        eng = {r[0] for r in cur.execute(
            f"SELECT DISTINCT {c} FROM words WHERE {c} IS NOT NULL AND {c} != ''")}
        unmapped = [v for v in eng if LATIN.search(v) and v not in MAP]
        if unmapped:
            print(f'FATAL: unmapped English-looking values in {c}: {unmapped}',
                  file=sys.stderr)
            sys.exit(1)

    q = ('SELECT word_id, word_unpointed, prefix1, prefix2, prefix3, suffix1, suffix2'
         ' FROM words ORDER BY word_id')
    if a.limit:
        q += f' LIMIT {a.limit}'
    rows = cur.execute(q).fetchall()

    stats = {'rows': 0, 'normalized_rows': 0, 'the_checked': 0, 'the_ok': 0,
             'the_bad': 0, 'latin_left': 0}
    per_value = {}
    bad_rows = []
    for wid, w, p1, p2, p3, s1, s2 in rows:
        stats['rows'] += 1
        raw = [p1, p2, p3, s1, s2]
        disp = [disp_of(v) for v in raw]
        if any((r or '') != d for r, d in zip(raw, disp)):
            stats['normalized_rows'] += 1
        for r, d in zip(raw, disp):
            if r and (r or '') != d:
                per_value.setdefault((r, d), 0)
                per_value[(r, d)] += 1
        # per-row positional check for ה
        for i, pv in enumerate([p1, p2, p3]):
            if pv in ('The, ?', 'the, ?'):
                stats['the_checked'] += 1
                prev = ''.join(stripm(disp[j]) for j in range(i))
                ws = stripm(w)
                if ws[len(prev):len(prev) + 1] == 'ה':
                    stats['the_ok'] += 1
                else:
                    stats['the_bad'] += 1
                    if len(bad_rows) < 20:
                        bad_rows.append((wid, w, p1, p2, p3))
        for d in disp:
            if d and LATIN.search(d):
                stats['latin_left'] += 1
        cur.execute(
            'UPDATE words SET prefix1_disp=?, prefix2_disp=?, prefix3_disp=?,'
            ' suffix1_disp=?, suffix2_disp=? WHERE word_id=?',
            (*disp, wid))
    con.commit()

    n_distinct_before = cur.execute(
        'SELECT COUNT(DISTINCT root_code) FROM words').fetchone()[0]
    print(f'rows processed: {stats["rows"]}')
    print(f'rows with >=1 normalized affix: {stats["normalized_rows"]}')
    print(f"'The, ?'/'the, ?' positional ה check: {stats['the_ok']}/{stats['the_checked']} ok, bad={stats['the_bad']}")
    for b in bad_rows:
        print(f'  HE-BAD {b}')
    print(f'Latin-looking chars left in disp columns: {stats["latin_left"]}')
    print(f'DISTINCT root_code after: {n_distinct_before}')
    print('per-value mapping counts:')
    for (r, d), n in sorted(per_value.items(), key=lambda kv: -kv[1]):
        print(f'  {n:7d}  {r!r} -> {d!r}')
    con.close()

if __name__ == '__main__':
    main()
