#!/usr/bin/env python3
"""Add per-word COMPUTED YLT renderings to the lexicon table.

Source: ylt_renderings (computed via KJV-bridge alignment, see build_ylt_align.py).
These are NOT authoritative Young's glosses -- they are a best-effort computed
mapping, labeled as such. Aggregated per (root_id, root_form_seq, vowel_seq):
distinct YLT words ordered by descending frequency, ' | '-separated, matching
the kjv_renderings style.

New column: ylt_renderings_computed TEXT NOT NULL DEFAULT ''
"""
import sqlite3
from collections import Counter, defaultdict

DB = '/home/hatch/workspace/bible-project/bible.db'
con = sqlite3.connect(DB)
cur = con.cursor()

cols = [r[1] for r in cur.execute('PRAGMA table_info(lexicon)').fetchall()]
if 'ylt_renderings_computed' not in cols:
    cur.execute("ALTER TABLE lexicon ADD COLUMN ylt_renderings_computed TEXT NOT NULL DEFAULT ''")
    con.commit()
    print('column added')
else:
    print('column already exists -- recomputing values')

# Aggregate YLT words per root_vowel key, with frequencies
agg = defaultdict(Counter)
for root_id, form_seq, vowel_seq, ylt_word in cur.execute('''
    SELECT w.root_id, w.root_form_seq, w.root_vowel_seq, y.ylt_word
    FROM ylt_renderings y JOIN words w ON w.word_id = y.word_id'''):
    agg[(root_id, form_seq, vowel_seq)][ylt_word] += 1

print(f'root_vowel keys with >=1 YLT word: {len(agg)}')

rows = []
for key, counter in agg.items():
    # frequency-descending, then alphabetical for ties (deterministic)
    ordered = sorted(counter.items(), key=lambda kv: (-kv[1], kv[0].lower()))
    renderings = ' | '.join(w for w, _ in ordered)
    rows.append((renderings,) + key)

cur.executemany('''UPDATE lexicon SET ylt_renderings_computed=?
                   WHERE root_id=? AND root_form_seq=? AND vowel_seq=?''', rows)
con.commit()

n_pop = cur.execute("SELECT COUNT(*) FROM lexicon WHERE ylt_renderings_computed<>''").fetchone()[0]
n_tot = cur.execute('SELECT COUNT(*) FROM lexicon').fetchone()[0]
print(f'lexicon rows with computed YLT renderings: {n_pop} / {n_tot} '
      f'= {100.0*n_pop/n_tot:.1f}%')

# sample
for r in cur.execute('''SELECT root_id, root_form_seq, vowel_seq, kjv_renderings,
                        substr(ylt_renderings_computed,1,80)
                        FROM lexicon WHERE ylt_renderings_computed<>''
                        LIMIT 3'''):
    print(tuple(r))
con.close()
print('done')
