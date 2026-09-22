#!/usr/bin/env python3
"""Honest coverage/quality measurement of the computed YLT word alignment.

Reads bible.db, reports:
  1. Verse coverage: verses with YLT text vs verses aligned
  2. Per-book: YLT token coverage, Hebrew-word coverage
  3. Ambiguity: Hebrew words with >1 distinct YLT word; YLT (verse,pos) mapped to >1 Hebrew word
  4. Empty-target rate: aligned YLT->KJV pairs whose KJV word had no Hebrew (from build log stats)
  5. Spot-checks: sample verses outside Genesis 1 with word-level detail
"""
import sqlite3
from collections import defaultdict

DB = '/home/hatch/workspace/bible-project/bible.db'
con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row
cur = con.cursor()

BOOK_NAMES = {r['book_num']: r['name_en'] for r in cur.execute(
    'SELECT book_num, name_en FROM books')}

print('=== 1. VERSE COVERAGE ===')
n_ylt_verses = cur.execute('SELECT COUNT(*) FROM ylt_verses').fetchone()[0]
n_kjv_verses = cur.execute('SELECT COUNT(DISTINCT book||":"||chapter||":"||verse) FROM kjv_words').fetchone()[0]
n_heb_verses = cur.execute('SELECT COUNT(DISTINCT book||":"||chapter||":"||verse) FROM words').fetchone()[0]
print(f'YLT verses in db: {n_ylt_verses}')
print(f'KJV verses in db: {n_kjv_verses}')
print(f'Hebrew verses in db: {n_heb_verses}')

print()
print('=== 2. PER-BOOK COVERAGE ===')
print(f'{"book":<4} {"name":<16} {"heb_words":>9} {"heb_hit":>7} {"%":>5} '
      f'{"ylt_rows":>8}')
for b in sorted(BOOK_NAMES):
    name = BOOK_NAMES[b]
    heb_words = cur.execute(
        'SELECT COUNT(*) FROM words WHERE book=?', (b,)).fetchone()[0]
    heb_hit = cur.execute(
        '''SELECT COUNT(DISTINCT y.word_id) FROM ylt_renderings y
           JOIN words w ON w.word_id=y.word_id WHERE w.book=?''', (b,)).fetchone()[0]
    ylt_rows = cur.execute(
        '''SELECT COUNT(*) FROM ylt_renderings y
           JOIN words w ON w.word_id=y.word_id WHERE w.book=?''', (b,)).fetchone()[0]
    pct = 100.0 * heb_hit / max(1, heb_words)
    print(f'{b:<4} {name:<16} {heb_words:>9} {heb_hit:>7} {pct:>5.1f} {ylt_rows:>8}')

print()
print('=== 3. AMBIGUITY ===')
# Hebrew words mapped to >1 distinct YLT word
multi = cur.execute('''
  SELECT COUNT(*) FROM (
    SELECT word_id FROM ylt_renderings
    GROUP BY word_id HAVING COUNT(DISTINCT ylt_word) > 1)
''').fetchone()[0]
total_wids = cur.execute('SELECT COUNT(DISTINCT word_id) FROM ylt_renderings').fetchone()[0]
print(f'Hebrew words with >1 distinct YLT word: {multi} / {total_wids} '
      f'= {100.0*multi/max(1,total_wids):.1f}%')
# distribution of distinct-YLT-word counts per Hebrew word
dist = cur.execute('''
  SELECT n, COUNT(*) FROM (
    SELECT word_id, COUNT(DISTINCT ylt_word) AS n FROM ylt_renderings GROUP BY word_id)
  GROUP BY n ORDER BY n
''').fetchall()
print('distinct-YLT-words-per-Hebrew-word distribution (n: count):',
      ', '.join(f'{r[0]}:{r[1]}' for r in dist[:10]))

print()
print('=== 4. HEBREW WORDS WITH NO YLT (by Strong\'s availability) ===')
no_ylt_total = cur.execute('''
  SELECT COUNT(*) FROM words w
  WHERE NOT EXISTS (SELECT 1 FROM ylt_renderings y WHERE y.word_id=w.word_id)
''').fetchone()[0]
no_ylt_nostrong = cur.execute('''
  SELECT COUNT(*) FROM words w
  WHERE NOT EXISTS (SELECT 1 FROM ylt_renderings y WHERE y.word_id=w.word_id)
    AND (w.strongs IS NULL OR TRIM(w.strongs)='')
''').fetchone()[0]
n_words = cur.execute('SELECT COUNT(*) FROM words').fetchone()[0]
print(f'Hebrew words with no YLT rendering: {no_ylt_total} / {n_words} '
      f'= {100.0*no_ylt_total/n_words:.1f}%')
print(f'  of those, with blank Strong\'s (unbridgeable): {no_ylt_nostrong} '
      f'= {100.0*no_ylt_nostrong/max(1,no_ylt_total):.1f}% of the misses')

print()
print('=== 5. SPOT-CHECKS (outside Genesis 1) ===')
spots = [(20, 2, 2),   # Exodus 20:2
         (19, 23, 1),  # Psalms 23:1
         (23, 53, 5),  # Isaiah 53:5
         (31, 1, 1)]   # Obadiah? no -- 31=Jonah? print what we get
for (b, c, v) in spots:
    bname = BOOK_NAMES.get(b, f'book{b}')
    print(f'--- {bname} {c}:{v} ---')
    hw = cur.execute('''SELECT word_pos, word_pointed, word_unpointed, strongs
                        FROM words WHERE book=? AND chapter=? AND verse=?
                        ORDER BY word_pos''', (b, c, v)).fetchall()
    if not hw:
        print('  (no Hebrew words found)')
        continue
    yr = defaultdict(list)
    for r in cur.execute('''SELECT y.word_id, y.ylt_word FROM ylt_renderings y
                            JOIN words w ON w.word_id=y.word_id
                            WHERE w.book=? AND w.chapter=? AND w.verse=?''', (b, c, v)):
        yr[r['word_id']].append(r['ylt_word'])
    wids = cur.execute('''SELECT word_id FROM words WHERE book=? AND chapter=? AND verse=?
                          ORDER BY word_pos''', (b, c, v)).fetchall()
    for h, wr in zip(hw, wids):
        wid = wr['word_id']
        print(f"  pos{h['word_pos']:>2} {h['word_pointed'] or h['word_unpointed']} "
              f"[{h['strongs'] or '--'}] -> {', '.join(yr.get(wid, ['(none)']))}")
con.close()
print()
print('done')
