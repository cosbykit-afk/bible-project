#!/usr/bin/env python3
"""Verse-by-verse YLT word alignment via the KJV bridge.

Method (COMPUTED, best-effort -- see NOTATION_LEDGER.md U-1):
  1. Per verse: Hebrew words in word_pos order, each with a Strong's set.
  2. KJV words in kjv_pos order with Strong's sets (kjv_words table).
  3. KJV -> Hebrew: a KJV word maps to the Hebrew word(s) in the same verse
     sharing a Strong's number (exact normalized match).
  4. YLT verse text tokenized in order; monolingual Needleman-Wunsch
     alignment YLT <-> KJV (exact 2, stem 1.5, fuzzy>=0.85 -> 1, mismatch -1,
     gap -1).
  5. Compose: YLT word -> KJV word -> Hebrew word_id(s).

Output: ylt_renderings(word_id, ylt_word, ylt_word_pos).
Hebrew words with no Strong's (or no aligned YLT token) get no rows --
this is reported, not interpolated.
"""
import sqlite3, re, string, difflib
from collections import defaultdict

DB = '/home/hatch/workspace/bible-project/bible.db'

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

STRIP = string.punctuation + '\u2014\u2013\u2018\u2019\u201c\u201d\u00ab\u00bb'

def tokenize(text):
    toks = []
    for raw in text.split():
        t = raw.strip(STRIP)
        if t: toks.append(t)
    return toks

def norm_word(w):
    return w.lower().strip(STRIP)

def stem(w):
    w = norm_word(w)
    for suf in ('ing', 'eth', 'est', 'es', 'ed', "'s", 's'):
        if len(w) > len(suf) + 2 and w.endswith(suf):
            return w[:-len(suf)]
    return w

def sim(a, b):
    na, nb = norm_word(a), norm_word(b)
    if not na or not nb: return -1
    if na == nb: return 2.0
    if stem(a) == stem(b): return 1.5
    r = difflib.SequenceMatcher(None, na, nb).ratio()
    if r >= 0.85: return 1.0
    return -1.0

def align(ys, ks):
    """Needleman-Wunsch; returns list of (y_idx, k_idx) aligned pairs."""
    m, n = len(ys), len(ks)
    GAP = -1.0
    dp = [[0.0]*(n+1) for _ in range(m+1)]
    for i in range(1, m+1): dp[i][0] = dp[i-1][0] + GAP
    for j in range(1, n+1): dp[0][j] = dp[0][j-1] + GAP
    for i in range(1, m+1):
        for j in range(1, n+1):
            dp[i][j] = max(dp[i-1][j] + GAP, dp[i][j-1] + GAP,
                           dp[i-1][j-1] + sim(ys[i-1], ks[j-1]))
    pairs = []
    i, j = m, n
    while i > 0 and j > 0:
        s = sim(ys[i-1], ks[j-1])
        if dp[i][j] == dp[i-1][j-1] + s:
            if s > 0: pairs.append((i-1, j-1))
            i -= 1; j -= 1
        elif dp[i][j] == dp[i-1][j] + GAP:
            i -= 1
        else:
            j -= 1
    pairs.reverse()
    return pairs

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row
cur = con.cursor()

ylt = {(r['book'], r['chapter'], r['verse']): r['text']
       for r in cur.execute('SELECT book, chapter, verse, text FROM ylt_verses')}
kjv = defaultdict(list)
for r in cur.execute('SELECT book, chapter, verse, kjv_pos, kjv_word, strongs'
                     ' FROM kjv_words ORDER BY book, chapter, verse, kjv_pos'):
    kjv[(r['book'], r['chapter'], r['verse'])].append(
        (r['kjv_word'], set(multi_strongs(r['strongs']))))
heb = defaultdict(list)
for r in cur.execute('SELECT word_id, book, chapter, verse, word_pos, strongs'
                     ' FROM words ORDER BY book, chapter, verse, word_pos'):
    heb[(r['book'], r['chapter'], r['verse'])].append(
        (r['word_id'], set(multi_strongs(r['strongs']))))

rows = []
stats = dict(verses=0, ylt_toks=0, ylt_aligned=0, heb_words=0, heb_hit=0)
spot = []
for v in sorted(set(ylt) & set(kjv) & set(heb)):
    stats['verses'] += 1
    hw = heb[v]                       # [(word_id, strongs_set)]
    kw = kjv[v]                       # [(kjv_word, strongs_set)]
    yt = tokenize(ylt[v])
    stats['ylt_toks'] += len(yt); stats['heb_words'] += len(hw)
    # KJV -> Hebrew via shared Strong's
    k2h = defaultdict(set)
    for i, (_, ks) in enumerate(kw):
        if not ks: continue
        for wid, hs in hw:
            if hs and (ks & hs): k2h[i].add(wid)
    pairs = align(yt, [k for k, _ in kw])
    hit_words = set()
    for yi, ki in pairs:
        wids = k2h.get(ki)
        if not wids: continue
        stats['ylt_aligned'] += 1
        for wid in wids:
            rows.append((wid, yt[yi], yi + 1)); hit_words.add(wid)
    stats['heb_hit'] += len(hit_words)
    if len(spot) < 8 and len(yt) > 6:
        spot.append((v, yt, [k for k, _ in kw], pairs, k2h, hw))

cur.executescript('''
DROP TABLE IF EXISTS ylt_renderings;
CREATE TABLE ylt_renderings(word_id INTEGER, ylt_word TEXT, ylt_word_pos INTEGER);
CREATE INDEX idx_ylt_renderings_wid ON ylt_renderings(word_id);
''')
cur.executemany('INSERT INTO ylt_renderings VALUES (?,?,?)', rows)
con.commit()

print('verses aligned:', stats['verses'])
print('ylt tokens:', stats['ylt_toks'], 'aligned to hebrew:', stats['ylt_aligned'],
      f"= {100*stats['ylt_aligned']/max(1,stats['ylt_toks']):.1f}%")
print('hebrew words:', stats['heb_words'], 'with >=1 ylt word:', stats['heb_hit'],
      f"= {100*stats['heb_hit']/max(1,stats['heb_words']):.1f}%")
print('ylt_renderings rows:', cur.execute('SELECT COUNT(*) FROM ylt_renderings').fetchone()[0])
print()
for v, yt, kt, pairs, k2h, hw in spot:
    wid_of = {wid: idx for idx, (wid, _) in enumerate(hw)}
    line = []
    for yi, ki in pairs:
        wids = sorted(k2h.get(ki, ()))
        tags = ','.join(str(wid_of[w]) for w in wids)
        line.append(f'{yt[yi]}~{kt[ki]}~H[{tags}]')
    print(f'{v}: ' + ' '.join(line))
con.close()
print('done')
