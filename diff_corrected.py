#!/usr/bin/env python3
"""Corrected diff: Prophets sheets have NO header row; data starts at row 1."""
import openpyxl, csv, json, re
from collections import Counter

OUT = '/home/hatch/workspace/bible-project/worker-out/canon'
HEB = re.compile(r'[\u05d0-\u05ea]')
def letters(s): return ''.join(HEB.findall(s or ''))

canon_key = {}
with open(f'{OUT}/canon_words.csv', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        b = int(r['book'])
        if b >= 6:
            canon_key[(b, int(r['chapter']), int(r['verse']), int(r['word_pos']))] = (r['word_pointed'], r['letters'])

wp = openpyxl.load_workbook('/tmp/bible/Prophets.xlsx', read_only=True, data_only=True)
total = 0; match = 0; mism = []; mismatch_verses = set(); junk = []
sheet_info = {}
for name in wp.sheetnames:
    wsh = wp[name]
    nr = wsh.max_row; nc = wsh.max_column
    sheet_info[name] = (nr, nc)
    if nc > 13:
        junk.append(f'{name}: {nc} columns; only first 13 used, rest ignored as junk')
    plist = []
    for r in wsh.iter_rows(min_row=1, values_only=True):  # NO header row
        if r[2] is None or r[3] is None or r[4] is None:  # skip stray junk rows (Hosea)
            continue
        plist.append((int(r[2]), int(r[3]), int(r[4]), r[5] or '', r[6] or ''))
    ppos = {}
    for (b, ch, v, pointed, novow) in plist:
        key = (b, ch, v)
        ppos[key] = ppos.get(key, 0) + 1
        total += 1
        c = canon_key.get((b, ch, v, ppos[key]))
        if c is None:
            mism.append(('NO_CANON', name, b, ch, v, ppos[key]))
            continue
        if c[0] == pointed and c[1] == letters(novow):
            match += 1
        else:
            mismatch_verses.add((b, ch, v))
            if len(mism) < 30:
                mism.append(('DIFF', name, b, ch, v, ppos[key], c[0], pointed, c[1], letters(novow)))

print(f'compared: {total}, exact: {match} ({100*match/max(total,1):.4f}%), mismatches: {len(mism)}, verses affected: {len(mismatch_verses)}')
for m in mism[:20]:
    print(' ', str(m)[:220])
for j in junk: print('JUNK:', j)
# row-count comparison per book
cb = Counter(k[0] for k in canon_key)
pb = Counter()
for name in wp.sheetnames:
    wsh = wp[name]
    for r in wsh.iter_rows(min_row=1, values_only=True):
        if r[2] is not None: pb[int(r[2])] += 1
print('book counts canon-vs-prophets:', {b: (cb[b], pb[b]) for b in sorted(set(cb) | set(pb))})
with open(f'{OUT}/diff_corrected.json', 'w') as f:
    json.dump({'compared': total, 'exact': match, 'pct': 100*match/max(total,1),
               'mismatches': len(mism), 'verses_affected': len(mismatch_verses),
               'junk': junk, 'sheet_info': sheet_info,
               'mismatch_samples': [list(m) for m in mism[:30]]}, f, indent=2, ensure_ascii=False)
print('DONE')
