#!/usr/bin/env python3
"""Bible project numbering, take 3: add the third tier (vowel pattern).
Syntax: root.fix.vowel  ->  root_id.root_form_seq.root_vowel_seq
root_vowel groups distinct pointed (vocalized) forms beneath each (root, form) pair,
numbered by Unicode sort of the pointed string. Deterministic."""
import shutil, sqlite3

DB = '/home/hatch/workspace/bible-project/bible.db'
shutil.copy2(DB, DB + '.bak-20260921-rootfixvowel')
print('backup written')

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row
cur = con.cursor()

rows = cur.execute(
    'SELECT word_id, root_id, root_form_seq, word_pointed FROM words').fetchall()
assert all(r['root_id'] and r['root_form_seq'] for r in rows), 'tier 1/2 missing on some words'

groups = {}
for r in rows:
    g = groups.setdefault((r['root_id'], r['root_form_seq']), {})
    p = r['word_pointed'] or ''
    g[p] = g.get(p, 0) + 1
print('distinct (root, form) groups:', len(groups))
print('distinct (root, form, vowel) patterns:', sum(len(g) for g in groups.values()))

cur.executescript('''
DROP TABLE IF EXISTS root_vowel;
CREATE TABLE root_vowel(
  root_id INTEGER NOT NULL,
  root_form_seq INTEGER NOT NULL,
  vowel_seq INTEGER NOT NULL,
  vowel_pattern TEXT NOT NULL,
  word_count INTEGER NOT NULL,
  PRIMARY KEY(root_id, root_form_seq, vowel_seq),
  FOREIGN KEY(root_id, root_form_seq) REFERENCES root_form(root_id, form_seq));
''')

vowel_rows = []
word_upd = []
vseq_of = {}
for (rid, fseq), g in groups.items():
    for seq, p in enumerate(sorted(g.keys()), 1):
        vseq_of[(rid, fseq, p)] = seq
        vowel_rows.append((rid, fseq, seq, p, g[p]))
for r in rows:
    p = r['word_pointed'] or ''
    vs = vseq_of[(r['root_id'], r['root_form_seq'], p)]
    word_upd.append((vs, f"{r['root_id']}.{r['root_form_seq']}.{vs}", r['word_id']))

cur.executemany(
    'INSERT INTO root_vowel(root_id, root_form_seq, vowel_seq, vowel_pattern, word_count)'
    ' VALUES (?,?,?,?,?)', vowel_rows)

cols = [x[1] for x in cur.execute('PRAGMA table_info(words)')]
if 'root_vowel_seq' not in cols:
    cur.execute('ALTER TABLE words ADD COLUMN root_vowel_seq INTEGER')
cur.executemany('UPDATE words SET root_vowel_seq=?, root_code=? WHERE word_id=?', word_upd)
cur.execute('CREATE INDEX IF NOT EXISTS idx_words_root3 ON words(root_id, root_form_seq, root_vowel_seq)')
con.commit()

print('root_vowel rows:', cur.execute('SELECT COUNT(*) FROM root_vowel').fetchone()[0])
print('words w/o vowel tier:', cur.execute('SELECT COUNT(*) FROM words WHERE root_vowel_seq IS NULL').fetchone()[0])
print('vowel word sum:', cur.execute('SELECT SUM(word_count) FROM root_vowel').fetchone()[0])
print('distinct root_codes:', cur.execute('SELECT COUNT(DISTINCT root_code) FROM words').fetchone()[0])
n2 = cur.execute("SELECT COUNT(*) FROM words WHERE root_code NOT LIKE '%.%.%'").fetchone()[0]
print('root_codes not three-part:', n2)
print('sample:', cur.execute("SELECT root_code, word_pointed, word_unpointed FROM words WHERE root_id=19247 AND root_form_seq=42 LIMIT 5").fetchall())
con.close()
print('done')
