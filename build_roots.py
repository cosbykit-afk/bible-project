#!/usr/bin/env python3
"""Bible project: (1) replace Kit's old Strong's research with OSHB values on the
105 conflicts; (2) generate the new root-based numbering system.

Root numbering: every distinct unpointed base word gets a sequential root_id
(Hebrew alphabetical order). Beneath each root, every distinct
(prefix1,prefix2,prefix3,suffix1,suffix2) combination gets a form_seq.
A word's number is root_id.form_seq, e.g. 4217.3.
"""
import csv, difflib, json, re, shutil, sqlite3

ROOT = '/home/hatch/workspace/bible-project'
DB = f'{ROOT}/bible.db'
WO = f'{ROOT}/worker-out'

shutil.copy(DB, DB + '.bak-20260921')
print('backup written')

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

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row
cur = con.cursor()

# ---------- 1. flip Kit's conflicting Strong's to OSHB ----------
VERSE_REMAP = {(19, 17, 17): (19, 17, 1), (23, 27, 22): (23, 27, 1),
               (24, 28, 23): (24, 28, 1), (25, 2, 23): (25, 2, 1)}
words = [dict(r) for r in cur.execute(
    'SELECT word_id, book, chapter, verse, word_pos, letters, strongs, strongs_source FROM words')]
oshb_by_verse = {}
with open(f'{WO}/oshb/oshb_words.tsv', encoding='utf-8') as f:
    for r in csv.DictReader(f, delimiter='\t'):
        oshb_by_verse.setdefault((int(r['book_num']), int(r['chapter']), int(r['verse'])), []).append(r)
for v in oshb_by_verse.values():
    v.sort(key=lambda r: int(r['word_pos']))
canon_by_verse = {}
for w in words:
    canon_by_verse.setdefault((w['book'], w['chapter'], w['verse']), []).append(w)
for v in canon_by_verse.values():
    v.sort(key=lambda x: x['word_pos'])

def align_verse(cwords, owords):
    a = [w['letters'] for w in cwords]
    b = [r['unpointed'] for r in owords]
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    out = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'equal':
            for i, j in zip(range(i1, i2), range(j1, j2)):
                out.append((cwords[i], owords[j]))
        elif tag == 'replace':
            ca = ''.join(a[i1:i2]); cb = ''.join(b[j1:j2])
            if ca == cb and ca:
                for i in range(i1, i2):
                    best = max(range(j1, j2), key=lambda j: len(b[j]))
                    out.append((cwords[i], owords[best]))
    return out

flips = []
for ckey, cwords in canon_by_verse.items():
    owords = oshb_by_verse.get(VERSE_REMAP.get(ckey, ckey))
    if not owords: continue
    for w, orow in align_verse(cwords, owords):
        ostr = multi_strongs(orow['strongs'])
        ostrongs = ostr[0] if ostr else None
        if w['strongs_source'] == 'kit' and w['strongs'] and ostrongs and w['strongs'] != ostrongs:
            flips.append((ostrongs, w['word_id'], w['strongs']))
print('conflicts to flip:', len(flips))
cur.executemany("UPDATE words SET strongs=?, strongs_source='oshb' WHERE word_id=?",
                [(o, wid) for o, wid, _ in flips])
con.commit()
n_kit = cur.execute("SELECT COUNT(*) FROM words WHERE strongs_source='kit'").fetchone()[0]
print('rows still carrying Kit-era strongs_source=kit:', n_kit)

# ---------- 2. root numbering ----------
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
# root key: unpointed base word; the 7 paseq rows fall back to their own unpointed form
cur.execute('''
INSERT INTO root_entry(root, word_count)
SELECT key, COUNT(*) FROM (
  SELECT CASE WHEN base_word IS NULL OR base_word='' THEN word_unpointed ELSE base_word END AS key
  FROM words)
GROUP BY key ORDER BY key''')
n_roots = cur.execute('SELECT COUNT(*) FROM root_entry').fetchone()[0]
print('root entries:', n_roots)

cur.execute('''
INSERT INTO root_form(root_id, form_seq, prefix1, prefix2, prefix3, suffix1, suffix2, word_count)
SELECT root_id, ROW_NUMBER() OVER (PARTITION BY r.root_id ORDER BY
    COALESCE(w.prefix1,''), COALESCE(w.prefix2,''), COALESCE(w.prefix3,''),
    COALESCE(w.suffix1,''), COALESCE(w.suffix2,'')),
  w.prefix1, w.prefix2, w.prefix3, w.suffix1, w.suffix2, COUNT(*)
FROM words w
JOIN root_entry r ON r.root = CASE WHEN w.base_word IS NULL OR w.base_word='' THEN w.word_unpointed ELSE w.base_word END
GROUP BY r.root_id, COALESCE(w.prefix1,''), COALESCE(w.prefix2,''), COALESCE(w.prefix3,''),
         COALESCE(w.suffix1,''), COALESCE(w.suffix2,'')''')
n_forms = cur.execute('SELECT COUNT(*) FROM root_form').fetchone()[0]
print('root forms:', n_forms)

# example surface forms: lowest word_id per (root_id, affix combo)
cur.execute('''
UPDATE root_form SET example_pointed = (
  SELECT w.word_pointed FROM words w
  JOIN root_entry r ON r.root = CASE WHEN w.base_word IS NULL OR w.base_word='' THEN w.word_unpointed ELSE w.base_word END
  WHERE r.root_id = root_form.root_id
    AND COALESCE(w.prefix1,'') = COALESCE(root_form.prefix1,'')
    AND COALESCE(w.prefix2,'') = COALESCE(root_form.prefix2,'')
    AND COALESCE(w.prefix3,'') = COALESCE(root_form.prefix3,'')
    AND COALESCE(w.suffix1,'') = COALESCE(root_form.suffix1,'')
    AND COALESCE(w.suffix2,'') = COALESCE(root_form.suffix2,'')
  ORDER BY w.word_id LIMIT 1),
example_unpointed = (
  SELECT w.word_unpointed FROM words w
  JOIN root_entry r ON r.root = CASE WHEN w.base_word IS NULL OR w.base_word='' THEN w.word_unpointed ELSE w.base_word END
  WHERE r.root_id = root_form.root_id
    AND COALESCE(w.prefix1,'') = COALESCE(root_form.prefix1,'')
    AND COALESCE(w.prefix2,'') = COALESCE(root_form.prefix2,'')
    AND COALESCE(w.prefix3,'') = COALESCE(root_form.prefix3,'')
    AND COALESCE(w.suffix1,'') = COALESCE(root_form.suffix1,'')
    AND COALESCE(w.suffix2,'') = COALESCE(root_form.suffix2,'')
  ORDER BY w.word_id LIMIT 1)''')

cols = [r[1] for r in cur.execute('PRAGMA table_info(words)')]
for c, typ in [('root_id', 'INTEGER'), ('root_form_seq', 'INTEGER'), ('root_code', 'TEXT')]:
    if c not in cols:
        cur.execute(f'ALTER TABLE words ADD COLUMN {c} {typ}')
cur.execute('''
UPDATE words SET root_id = (
  SELECT root_id FROM root_entry
  WHERE root_entry.root = CASE WHEN words.base_word IS NULL OR words.base_word='' THEN words.word_unpointed ELSE words.base_word END)''')
cur.execute('''
UPDATE words SET root_form_seq = (
  SELECT form_seq FROM root_form
  WHERE root_form.root_id = words.root_id
    AND COALESCE(root_form.prefix1,'') = COALESCE(words.prefix1,'')
    AND COALESCE(root_form.prefix2,'') = COALESCE(words.prefix2,'')
    AND COALESCE(root_form.prefix3,'') = COALESCE(words.prefix3,'')
    AND COALESCE(root_form.suffix1,'') = COALESCE(words.suffix1,'')
    AND COALESCE(root_form.suffix2,'') = COALESCE(words.suffix2,''))''')
cur.execute("UPDATE words SET root_code = root_id || '.' || root_form_seq")
cur.execute('CREATE INDEX IF NOT EXISTS idx_words_root ON words(root_id, root_form_seq)')
con.commit()

# ---------- verification ----------
print('words total:', cur.execute('SELECT COUNT(*) FROM words').fetchone()[0])
print('words missing root_id:', cur.execute('SELECT COUNT(*) FROM words WHERE root_id IS NULL').fetchone()[0])
print('words missing form_seq:', cur.execute('SELECT COUNT(*) FROM words WHERE root_form_seq IS NULL').fetchone()[0])
print('words sum over roots:', cur.execute('SELECT SUM(word_count) FROM root_entry').fetchone()[0])
print('forms sum:', cur.execute('SELECT SUM(word_count) FROM root_form').fetchone()[0])
print('distinct root_codes on words:', cur.execute('SELECT COUNT(DISTINCT root_code) FROM words').fetchone()[0])
r = cur.execute("SELECT root_id, root, word_count FROM root_entry WHERE root='מלכ'").fetchone()
print('root מלכ:', dict(r) if r else None)
for f in cur.execute('SELECT form_seq, prefix1, prefix2, prefix3, suffix1, suffix2, word_count, example_unpointed FROM root_form WHERE root_id=? ORDER BY form_seq LIMIT 12', (r['root_id'],)):
    print('  ', dict(f))
print('first roots alphabetically:', [x[0] for x in cur.execute('SELECT root FROM root_entry ORDER BY root_id LIMIT 5')])
print('done')
