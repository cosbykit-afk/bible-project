#!/usr/bin/env python3
"""Bible project root numbering, take 2 (set-based + Python dicts, no slow correlated UPDATEs)."""
import sqlite3

DB = '/home/hatch/workspace/bible-project/bible.db'
con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row
cur = con.cursor()

# clean the 9 junk rows: strongs_source='kit' but unparseable/empty strongs
cur.execute("UPDATE words SET strongs_source=NULL WHERE strongs_source='kit' AND (strongs IS NULL OR strongs='')")
print('junk kit rows cleaned:', cur.rowcount)

rows = cur.execute(
    'SELECT word_id, word_pointed, word_unpointed, base_word, prefix1, prefix2, prefix3, suffix1, suffix2'
    ' FROM words').fetchall()

def key(r):
    b = r['base_word']
    return b if b else r['word_unpointed']

def aff(r):
    return (r['prefix1'] or '', r['prefix2'] or '', r['prefix3'] or '',
            r['suffix1'] or '', r['suffix2'] or '')

roots = {}
for r in rows:
    k = key(r)
    e = roots.setdefault(k, {'count': 0, 'forms': {}})
    e['count'] += 1
    a = aff(r)
    f = e['forms'].setdefault(a, {'count': 0, 'ex_id': None, 'ex_p': None, 'ex_u': None})
    f['count'] += 1
    if f['ex_id'] is None or r['word_id'] < f['ex_id']:
        f['ex_id'] = r['word_id']; f['ex_p'] = r['word_pointed']; f['ex_u'] = r['word_unpointed']

ordered = sorted(roots.keys())
print('distinct roots:', len(ordered))

cur.executescript('''
DROP TABLE IF EXISTS root_form;
DROP TABLE IF EXISTS root_entry;
CREATE TABLE root_entry(root_id INTEGER PRIMARY KEY, root TEXT UNIQUE NOT NULL, word_count INTEGER NOT NULL);
CREATE TABLE root_form(
  root_id INTEGER NOT NULL REFERENCES root_entry(root_id),
  form_seq INTEGER NOT NULL,
  prefix1 TEXT, prefix2 TEXT, prefix3 TEXT, suffix1 TEXT, suffix2 TEXT,
  word_count INTEGER NOT NULL,
  example_pointed TEXT, example_unpointed TEXT,
  PRIMARY KEY(root_id, form_seq));
''')
cur.executemany('INSERT INTO root_entry(root_id, root, word_count) VALUES (?,?,?)',
                [(i + 1, k, roots[k]['count']) for i, k in enumerate(ordered)])

form_rows = []
word_upd = []
for i, k in enumerate(ordered):
    rid = i + 1
    e = roots[k]
    for seq, a in enumerate(sorted(e['forms'].keys()), 1):
        f = e['forms'][a]
        form_rows.append((rid, seq, a[0], a[1], a[2], a[3], a[4], f['count'], f['ex_p'], f['ex_u']))
    # word updates for this root: handled in the single pass below

# one pass over words for the UPDATE payload
root_id_of = {k: i + 1 for i, k in enumerate(ordered)}
seq_of = {}
for i, k in enumerate(ordered):
    rid = i + 1
    for seq, a in enumerate(sorted(roots[k]['forms'].keys()), 1):
        seq_of[(rid, a)] = seq
for r in rows:
    k = key(r); a = aff(r); rid = root_id_of[k]; seq = seq_of[(rid, a)]
    word_upd.append((rid, seq, f'{rid}.{seq}', r['word_id']))

cur.executemany(
    'INSERT INTO root_form(root_id, form_seq, prefix1, prefix2, prefix3, suffix1, suffix2, word_count, example_pointed, example_unpointed)'
    ' VALUES (?,?,?,?,?,?,?,?,?,?)', form_rows)

cols = [x[1] for x in cur.execute('PRAGMA table_info(words)')]
for c, typ in [('root_id', 'INTEGER'), ('root_form_seq', 'INTEGER'), ('root_code', 'TEXT')]:
    if c not in cols:
        cur.execute(f'ALTER TABLE words ADD COLUMN {c} {typ}')
cur.executemany('UPDATE words SET root_id=?, root_form_seq=?, root_code=? WHERE word_id=?', word_upd)
cur.execute('CREATE INDEX IF NOT EXISTS idx_words_root ON words(root_id, root_form_seq)')
con.commit()

print('root_entry:', cur.execute('SELECT COUNT(*) FROM root_entry').fetchone()[0])
print('root_form:', cur.execute('SELECT COUNT(*) FROM root_form').fetchone()[0])
print('words w/o root:', cur.execute('SELECT COUNT(*) FROM words WHERE root_id IS NULL').fetchone()[0])
print('root word sum:', cur.execute('SELECT SUM(word_count) FROM root_entry').fetchone()[0])
print('form word sum:', cur.execute('SELECT SUM(word_count) FROM root_form').fetchone()[0])
r = cur.execute("SELECT root_id, root, word_count FROM root_entry WHERE root='מלכ'").fetchone()
print('root מלכ ->', dict(r))
for f in cur.execute('SELECT form_seq, prefix1, prefix2, prefix3, suffix1, suffix2, word_count, example_unpointed FROM root_form WHERE root_id=? ORDER BY form_seq', (r['root_id'],)):
    print('   ', dict(f))
print('root 1:', cur.execute('SELECT root FROM root_entry WHERE root_id=1').fetchone()[0])
print('last root:', cur.execute('SELECT root FROM root_entry ORDER BY root_id DESC LIMIT 1').fetchone()[0])
print('distinct root_codes:', cur.execute('SELECT COUNT(DISTINCT root_code) FROM words').fetchone()[0])
