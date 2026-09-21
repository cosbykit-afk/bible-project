#!/usr/bin/env python3
"""Build the lexicon table: per ROOT_VOWEL entry, the KJV renderings,
YLT verse contexts, and the verse list where the form is found.

YLT is verse-level in our sources (U-1), so the Young's column honestly
carries the YLT verse texts for verses where the form occurs, not a
per-word gloss. KJV renderings are word-level (kjv_renderings alignment),
ordered by frequency then alphabetically."""
import sqlite3
from collections import Counter, defaultdict

DB = '/home/hatch/workspace/bible-project/bible.db'
con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row
cur = con.cursor()

books = {r['book_num']: r['name_en'] for r in cur.execute('SELECT book_num, name_en FROM books')}
ylt = {(r['book'], r['chapter'], r['verse']): r['text']
       for r in cur.execute('SELECT book, chapter, verse, text FROM ylt_verses')}

kjv = defaultdict(Counter)
for r in cur.execute('SELECT word_id, kjv_word FROM kjv_renderings'):
    kjv[r['word_id']][r['kjv_word']] += 1

groups = {}
for r in cur.execute('SELECT word_id, root_id, root_form_seq, root_vowel_seq,'
                     ' book, chapter, verse FROM words'):
    g = groups.setdefault((r['root_id'], r['root_form_seq'], r['root_vowel_seq']),
                          {'verses': set(), 'kjv': Counter()})
    g['verses'].add((r['book'], r['chapter'], r['verse']))
    g['kjv'].update(kjv.get(r['word_id'], ()))
print('groups:', len(groups))

def ref(b, c, v):
    return f"{books.get(b, b)} {c}:{v}"

rows = []
for (rid, fseq, vseq), g in groups.items():
    verses = sorted(g['verses'])
    kjv_cell = ' | '.join(w for w, _ in sorted(g['kjv'].items(),
                                               key=lambda kv: (-kv[1], kv[0])))
    ylt_cell = ' \u2016 '.join(f"{ref(b, c, v)} \u2014 {ylt[(b, c, v)]}"
                               for (b, c, v) in verses if (b, c, v) in ylt)
    verses_cell = '; '.join(ref(b, c, v) for (b, c, v) in verses)
    rows.append((rid, fseq, vseq, kjv_cell, ylt_cell, verses_cell))

cur.executescript('''
DROP TABLE IF EXISTS lexicon;
CREATE TABLE lexicon(
  root_id INTEGER NOT NULL,
  root_form_seq INTEGER NOT NULL,
  vowel_seq INTEGER NOT NULL,
  kjv_renderings TEXT NOT NULL DEFAULT '',
  ylt_contexts TEXT NOT NULL DEFAULT '',
  found_verses TEXT NOT NULL DEFAULT '',
  PRIMARY KEY(root_id, root_form_seq, vowel_seq),
  FOREIGN KEY(root_id, root_form_seq, vowel_seq)
    REFERENCES root_vowel(root_id, root_form_seq, vowel_seq));
''')
cur.executemany(
    'INSERT INTO lexicon(root_id, root_form_seq, vowel_seq, kjv_renderings, ylt_contexts, found_verses)'
    ' VALUES (?,?,?,?,?,?)', rows)
con.commit()

print('lexicon rows:', cur.execute('SELECT COUNT(*) FROM lexicon').fetchone()[0])
print('root_vowel rows:', cur.execute('SELECT COUNT(*) FROM root_vowel').fetchone()[0])
print('with kjv:', cur.execute("SELECT COUNT(*) FROM lexicon WHERE kjv_renderings<>''").fetchone()[0])
print('with ylt:', cur.execute("SELECT COUNT(*) FROM lexicon WHERE ylt_contexts<>''").fetchone()[0])
s = cur.execute('SELECT kjv_renderings, found_verses FROM lexicon'
                ' WHERE root_id=19247 AND root_form_seq=42 AND vowel_seq=1').fetchone()
print('sample 19247.42.1 kjv:', s['kjv_renderings'][:120])
print('sample 19247.42.1 verses:', s['found_verses'][:120])
con.close()
print('done')
