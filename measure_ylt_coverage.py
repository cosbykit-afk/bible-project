#!/usr/bin/env python3
"""Exact coverage/quality measurement of the computed YLT word alignment.

Reads bible.db read-only. Reports with exact numerators/denominators
(no rounded-up percentages):
  1. Verse coverage: verses with YLT text vs verses aligned
  2. YLT token mapping: % of YLT tokens (in aligned verses) reaching Hebrew
  3. Hebrew-word hit rate: % of Hebrew words (in aligned verses) with >=1 row
  4. Miss analysis: share of missed Hebrew words with blank Strong's
  5. Per-book Hebrew hit-rate table + min/max range
  6. Ambiguity: % of hit Hebrew words with >1 distinct YLT word
  7. Label breakdown (bridged vs propagated)
  8. Spot-checks outside Genesis 1

Status: the alignment measured here is COMPUTED best-effort, NOT authoritative.
"""
import sqlite3
import sys
from collections import defaultdict

sys.path.insert(0, '/home/hatch/workspace/bible-project')
from build_ylt_align import tokenize

DB = '/home/hatch/workspace/bible-project/bible.db'
con = sqlite3.connect('file:' + DB + '?mode=ro', uri=True)
con.row_factory = sqlite3.Row
cur = con.cursor()

BOOK_NAMES = {r['book_num']: r['name_en'] for r in cur.execute(
    'SELECT book_num, name_en FROM books')}

n_words = cur.execute('SELECT COUNT(*) FROM words').fetchone()[0]

print('=== 1. VERSE COVERAGE ===')
n_ylt_verses = cur.execute('SELECT COUNT(*) FROM ylt_verses').fetchone()[0]
n_aligned_verses = cur.execute(
    '''SELECT COUNT(DISTINCT w.book||':'||w.chapter||':'||w.verse)
       FROM ylt_renderings y JOIN words w ON w.word_id=y.word_id''').fetchone()[0]
print(f'YLT verses in db: {n_ylt_verses}')
print(f'verses with >=1 alignment row: {n_aligned_verses}')

print()
print('=== 2. YLT TOKEN MAPPING (exact) ===')
# denominator: YLT tokens in verses that have >=1 alignment row
vset = {tuple(r) for r in cur.execute(
    '''SELECT DISTINCT w.book, w.chapter, w.verse FROM ylt_renderings y
       JOIN words w ON w.word_id=y.word_id''')}
tot_toks = 0
for r in cur.execute('SELECT book, chapter, verse, text FROM ylt_verses'):
    if (r['book'], r['chapter'], r['verse']) in vset:
        tot_toks += len(tokenize(r['text']))
mapped_toks = cur.execute(
    '''SELECT COUNT(DISTINCT w.book||':'||w.chapter||':'||w.verse||':'||y.ylt_word_pos)
       FROM ylt_renderings y JOIN words w ON w.word_id=y.word_id
       WHERE y.label='bridged' ''').fetchone()[0]
print(f'YLT tokens mapped to Hebrew: {mapped_toks} / {tot_toks} '
      f'= {100.0*mapped_toks/max(1,tot_toks):.4f}%')

print()
print('=== 3. HEBREW-WORD HIT RATE (exact) ===')
heb_in_v = cur.execute(
    '''SELECT COUNT(*) FROM words w
       WHERE EXISTS (SELECT 1 FROM ylt_verses t
                     WHERE t.book=w.book AND t.chapter=w.chapter AND t.verse=w.verse)
         AND EXISTS (SELECT 1 FROM ylt_renderings y
                     JOIN words w2 ON w2.word_id=y.word_id
                     WHERE w2.book=w.book AND w2.chapter=w.chapter AND w2.verse=w.verse)'''
).fetchone()[0]
heb_hit = cur.execute(
    'SELECT COUNT(DISTINCT word_id) FROM ylt_renderings').fetchone()[0]
print(f'Hebrew words with >=1 YLT row: {heb_hit} / {heb_in_v} '
      f'= {100.0*heb_hit/max(1,heb_in_v):.4f}%  (of {n_words} total words in db)')

print()
print('=== 4. MISS ANALYSIS ===')
miss_total = heb_in_v - heb_hit
miss_nostrong = cur.execute(
    '''SELECT COUNT(*) FROM words w
       WHERE (w.strongs IS NULL OR TRIM(w.strongs)='')
         AND NOT EXISTS (SELECT 1 FROM ylt_renderings y WHERE y.word_id=w.word_id)
         AND EXISTS (SELECT 1 FROM ylt_renderings y
                     JOIN words w2 ON w2.word_id=y.word_id
                     WHERE w2.book=w.book AND w2.chapter=w.chapter
                       AND w2.verse=w.verse)''').fetchone()[0]
print(f'missed Hebrew words: {miss_total}')
print(f'  of those, blank Strong\'s (unbridgeable by Strong\'s): {miss_nostrong} '
      f'= {100.0*miss_nostrong/max(1,miss_total):.4f}% of misses')

print()
print('=== 5. PER-BOOK HEBREW HIT RATE ===')
rates = []
print(f'{"book":<4} {"name":<16} {"heb_words":>9} {"heb_hit":>7} {"hit%":>8} '
      f'{"ylt_rows":>8}')
for b in sorted(BOOK_NAMES):
    name = BOOK_NAMES[b]
    hw = cur.execute('SELECT COUNT(*) FROM words WHERE book=?', (b,)).fetchone()[0]
    hit = cur.execute(
        '''SELECT COUNT(DISTINCT y.word_id) FROM ylt_renderings y
           JOIN words w ON w.word_id=y.word_id WHERE w.book=?''', (b,)).fetchone()[0]
    rows = cur.execute(
        '''SELECT COUNT(*) FROM ylt_renderings y
           JOIN words w ON w.word_id=y.word_id WHERE w.book=?''', (b,)).fetchone()[0]
    pct = 100.0 * hit / max(1, hw)
    rates.append(pct)
    print(f'{b:<4} {name:<16} {hw:>9} {hit:>7} {pct:>8.2f} {rows:>8}')
print(f'per-book hit-rate range: {min(rates):.2f}% .. {max(rates):.2f}%')

print()
print('=== 6. AMBIGUITY (exact) ===')
multi = cur.execute('''
  SELECT COUNT(*) FROM (
    SELECT word_id FROM ylt_renderings
    GROUP BY word_id HAVING COUNT(DISTINCT ylt_word) > 1)
''').fetchone()[0]
print(f'hit Hebrew words with >1 distinct YLT word: {multi} / {heb_hit} '
      f'= {100.0*multi/max(1,heb_hit):.4f}%')

print()
print('=== 7. ROW LABELS ===')
for lab, cnt in cur.execute(
        'SELECT label, COUNT(*) FROM ylt_renderings GROUP BY label'):
    print(f'  {lab}: {cnt}')
n_rows = cur.execute('SELECT COUNT(*) FROM ylt_renderings').fetchone()[0]
print(f'  total rows: {n_rows}')

print()
print('=== 8. SPOT-CHECKS (outside Genesis 1) ===')
for (b, c, v) in [(20, 2, 2), (19, 23, 1), (23, 53, 5)]:
    bname = BOOK_NAMES.get(b, f'book{b}')
    print(f'--- {bname} {c}:{v} ---')
    hw = cur.execute('''SELECT word_id, word_pos, word_pointed, word_unpointed, strongs
                        FROM words WHERE book=? AND chapter=? AND verse=?
                        ORDER BY word_pos''', (b, c, v)).fetchall()
    if not hw:
        print('  (no Hebrew words found)')
        continue
    yr = defaultdict(list)
    for r in cur.execute('''SELECT y.word_id, y.ylt_word, y.label FROM ylt_renderings y
                            JOIN words w ON w.word_id=y.word_id
                            WHERE w.book=? AND w.chapter=? AND w.verse=?''', (b, c, v)):
        yr[r['word_id']].append(f"{r['ylt_word']}[{r['label']}]")
    for h in hw:
        print(f"  pos{h['word_pos']:>2} {h['word_pointed'] or h['word_unpointed']} "
              f"[{h['strongs'] or '--'}] -> {', '.join(yr.get(h['word_id'], ['(none)']))}")
con.close()
print()
print('done')
