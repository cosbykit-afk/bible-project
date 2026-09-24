#!/usr/bin/env python3
"""Verse-by-verse YLT word alignment via the KJV bridge (U-1, 2026-09-24).

Three bridge methods share the YLT<->KJV Needleman-Wunsch step
(exact 2, stem 1.5, fuzzy>=0.85 -> 1, mismatch -1, gap -1):

  baseline   KJV word -> every Hebrew word in the verse sharing any
             Strong's number (the 2026-09-22 method).
  anchored   Phase 1: one-to-one anchors on exact single-Strong's matches
             (a KJV word carrying exactly one Strong's S claims the
             unclaimed Hebrew word whose Strong's is exactly S, nearest
             by relative verse position; each side used at most once).
             Phase 2 (gap-fill): KJV words with no anchor fall back to
             the baseline loose rule.
  propagated anchored bridge + root-family propagation: a Hebrew word with
             blank Strong's copies the YLT renderings of an aligned
             in-verse sibling sharing its (root_id, root_form_seq).
             Copied rows are labeled 'propagated'; all other rows
             'bridged'.

Usage:
  python3 build_ylt_align.py --eval [--gold path]
      Score the three methods on the hand-aligned gold set
      (default gold: eval/ylt_gold.tsv). No DB writes.
  python3 build_ylt_align.py --method {baseline,anchored,propagated}
      Full run over all verses; (re)creates ylt_renderings
      (word_id, ylt_word, ylt_word_pos, label).

Status: COMPUTED best-effort, NOT authoritative (see NOTATION_LEDGER U-1).
"""
import sqlite3, re, string, difflib, sys, csv
from collections import defaultdict

ROOT = '/home/hatch/workspace/bible-project'
DB = f'{ROOT}/bible.db'
GOLD_DEFAULT = f'{ROOT}/eval/ylt_gold.tsv'

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
    """Needleman-Wunsch; returns list of (y_idx, k_idx) aligned pairs (s>0)."""
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

# ---------------------------------------------------------------- data ----
def load_data(cur):
    ylt = {(r['book'], r['chapter'], r['verse']): r['text']
           for r in cur.execute('SELECT book, chapter, verse, text FROM ylt_verses')}
    kjv = defaultdict(list)
    for r in cur.execute('SELECT book, chapter, verse, kjv_pos, kjv_word, strongs'
                         ' FROM kjv_words ORDER BY book, chapter, verse, kjv_pos'):
        kjv[(r['book'], r['chapter'], r['verse'])].append(
            (r['kjv_word'], set(multi_strongs(r['strongs']))))
    heb = defaultdict(list)
    cols = [x[1] for x in cur.execute('PRAGMA table_info(words)')]
    have_roots = 'root_id' in cols and 'root_form_seq' in cols
    sel = ('SELECT word_id, book, chapter, verse, word_pos, strongs'
           + (', root_id, root_form_seq' if have_roots else '') +
           ' FROM words ORDER BY book, chapter, verse, word_pos')
    for r in cur.execute(sel):
        heb[(r['book'], r['chapter'], r['verse'])].append({
            'word_id': r['word_id'], 'word_pos': r['word_pos'],
            'strongs': set(multi_strongs(r['strongs'])),
            'root': (r['root_id'], r['root_form_seq']) if have_roots
                    and r['root_id'] else None,
        })
    return ylt, kjv, heb

# -------------------------------------------------------------- bridges ---
def bridge_baseline(kw, hw):
    """KJV word index -> set of Hebrew word_ids sharing any Strong's."""
    k2h = defaultdict(set)
    for i, (_, ks) in enumerate(kw):
        if not ks: continue
        for w in hw:
            if w['strongs'] and (ks & w['strongs']):
                k2h[i].add(w['word_id'])
    return k2h

def bridge_anchored(kw, hw, gapfill='loose', cap=None):
    """One-to-one exact-Strong's anchors, then gap-fill.

    gapfill policy:
      'loose'     unanchored KJV words use the baseline rule (any Hebrew word)
      'unclaimed' unanchored KJV words map only to unclaimed Hebrew words
      'strict'    single-Strong's KJV words are anchor-or-nothing;
                  multi/zero-Strong's KJV words use the baseline rule
    cap: if set, gap-fill keeps only Hebrew words whose relative verse
      position is within `cap` of the KJV word's relative position.
    """
    n, m = len(kw), len(hw)
    claimed = set()
    anchors = {}
    single_no_anchor = set()
    for i, (_, ks) in enumerate(kw):
        if len(ks) != 1:
            continue
        s = next(iter(ks))
        best, best_d = None, None
        for w in hw:
            if w['word_id'] in claimed:
                continue
            if w['strongs'] == {s}:
                d = abs(i / max(1, n) - (w['word_pos'] - 1) / max(1, m))
                if best is None or d < best_d or (d == best_d and
                        w['word_pos'] < best['word_pos']):
                    best, best_d = w, d
        if best is not None:
            claimed.add(best['word_id'])
            anchors[i] = {best['word_id']}
        else:
            single_no_anchor.add(i)

    def gap_candidates(i, ks, unclaimed_only=False):
        out = set()
        for w in hw:
            if unclaimed_only and w['word_id'] in claimed:
                continue
            if w['strongs'] and (ks & w['strongs']):
                if cap is not None:
                    d = abs(i / max(1, n) - (w['word_pos'] - 1) / max(1, m))
                    if d > cap:
                        continue
                out.add(w['word_id'])
        return out

    k2h = dict(anchors)
    if gapfill == 'loose':
        for i, (_, ks) in enumerate(kw):
            if i in k2h or not ks:
                continue
            hit = gap_candidates(i, ks)
            if hit:
                k2h[i] = hit
    elif gapfill == 'unclaimed':
        for i, (_, ks) in enumerate(kw):
            if i in k2h or not ks:
                continue
            hit = gap_candidates(i, ks, unclaimed_only=True)
            if hit:
                k2h[i] = hit
    elif gapfill == 'strict':
        for i, (_, ks) in enumerate(kw):
            if i in k2h or not ks or i in single_no_anchor:
                continue
            hit = gap_candidates(i, ks)
            if hit:
                k2h[i] = hit
    else:
        raise ValueError(gapfill)
    return k2h

# ------------------------------------------------------------ one verse ----
DIVINE_GUARD = {'H3068': {'jehovah', 'lord'}}  # Strong's -> allowed YLT tokens (lowercased)

def align_verse(v, yt_text, kw, hw, method, heb_strongs=None):
    """Return list of (word_id, ylt_word, ylt_word_pos, label)."""
    yt = tokenize(yt_text)
    if method == 'baseline':
        k2h = bridge_baseline(kw, hw)
    elif method == 'anchored':
        k2h = bridge_anchored(kw, hw, gapfill='loose', cap=0.20)
    elif method == 'anchored_strict':
        k2h = bridge_anchored(kw, hw, gapfill='strict')
    elif method in ('anchored_loose', 'anchored_guard'):
        k2h = bridge_anchored(kw, hw, gapfill='loose')
    elif method == 'anchored_unclaimed':
        k2h = bridge_anchored(kw, hw, gapfill='unclaimed')
    elif method.startswith('anchored_cap'):
        k2h = bridge_anchored(kw, hw, gapfill='loose',
                              cap=float(method.split('cap')[1]) / 100.0)
    elif method in ('propagated', 'propagated_guard'):
        k2h = bridge_anchored(kw, hw, gapfill='loose', cap=0.20)
    else:
        raise ValueError(method)
    pairs = align(yt, [k for k, _ in kw])
    rows = []
    bridged_wids = defaultdict(list)   # wid -> [(ylt_word, ylt_word_pos)]
    for yi, ki in pairs:
        wids = k2h.get(ki)
        if not wids:
            continue
        for wid in wids:
            rows.append((wid, yt[yi], yi + 1, 'bridged'))
            bridged_wids[wid].append((yt[yi], yi + 1))
    if method in ('propagated', 'propagated_guard'):
        for w in hw:
            wid = w['word_id']
            if w['strongs'] or wid in bridged_wids or w['root'] is None:
                continue
            sibs = [w2 for w2 in hw
                    if w2['word_id'] != wid and w2['root'] == w['root']
                    and w2['word_id'] in bridged_wids]
            if not sibs:
                continue
            sib = min(sibs, key=lambda s: (abs(s['word_pos'] - w['word_pos']),
                                           s['word_pos']))
            for yw, yp in bridged_wids[sib['word_id']]:
                rows.append((wid, yw, yp, 'propagated'))
    if method in ('anchored_guard', 'propagated_guard') and heb_strongs:
        kept = []
        for wid, yw, yp, lab in rows:
            allow = DIVINE_GUARD.get(heb_strongs.get(wid))
            if allow is not None and norm_word(yw) not in allow:
                continue
            kept.append((wid, yw, yp, lab))
        rows = kept
    return rows

# ------------------------------------------------------------------ eval ---
def load_gold(path):
    gold = {}          # wid -> set of ylt positions
    verses = set()
    h3068 = set()
    with open(path, encoding='utf-8') as f:
        rd = csv.DictReader(f, delimiter='\t')
        for r in rd:
            wid = int(r['word_id'])
            pos = {int(x) for x in r['ylt_pos'].split(',') if x.strip()}
            gold[wid] = pos
            verses.add((int(r['book']), int(r['chapter']), int(r['verse'])))
            if (r['strongs'] or '').strip().upper() == 'H3068':
                h3068.add(wid)
    return gold, verses, h3068

def eval_method(method, gold, verses, ylt, kjv, heb, heb_strongs=None):
    pred = defaultdict(set)   # wid -> set of ylt positions
    for v in verses:
        for wid, _yw, yp, _lab in align_verse(v, ylt[v], kjv[v], heb[v],
                                              method, heb_strongs):
            pred[wid].add(yp)
    P = {(w, p) for w, ps in pred.items() for p in ps}
    G = {(w, p) for w, ps in gold.items() for p in ps}
    tp = len(P & G)
    prec = tp / len(P) if P else 0.0
    rec = tp / len(G) if G else 0.0
    return {'method': method, 'pred_pairs': len(P), 'gold_pairs': len(G),
            'tp': tp, 'precision': prec, 'recall': rec, 'pred': pred}

def run_eval(gold_path):
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    ylt, kjv, heb = load_data(cur)
    con.close()
    gold, verses, h3068 = load_gold(gold_path)
    heb_strongs = {}
    for v in verses:
        for w in heb[v]:
            s = w['strongs']
            heb_strongs[w['word_id']] = next(iter(s)) if len(s) == 1 else None
    missing = [v for v in verses if v not in ylt or v not in kjv or v not in heb]
    assert not missing, f'gold verses missing data: {missing}'
    print(f'gold: {len(verses)} verses, {len(gold)} words, '
          f'{sum(len(p) for p in gold.values())} pairs; H3068 words: {len(h3068)}')
    results = {}
    methods = ('baseline', 'anchored', 'propagated',
               # --- configuration sweep (appendix; not contenders) ---
               'anchored_loose', 'anchored_strict', 'anchored_unclaimed',
               'anchored_cap15', 'anchored_cap25', 'anchored_cap35',
               'anchored_cap50', 'anchored_guard', 'propagated_guard')
    for method in methods:
        r = eval_method(method, gold, verses, ylt, kjv, heb, heb_strongs)
        results[method] = r
        print(f"{method:>10}: pred={r['pred_pairs']:4d} tp={r['tp']:4d} "
              f"precision={r['precision']:.4f} recall={r['recall']:.4f}")
    print()
    print('H3068 divine-name check (predicted set must equal gold set):')
    for method in methods:
        pred = results[method]['pred']
        bad = 0
        for wid in sorted(h3068):
            if pred.get(wid, set()) != gold[wid]:
                bad += 1
                extra = sorted(pred.get(wid, set()) - gold[wid])
                missed = sorted(gold[wid] - pred.get(wid, set()))
                print(f'  {method}: wid {wid} MISMATCH extra={extra} missed={missed}')
        if bad == 0:
            print(f'  {method}: all {len(h3068)} H3068 words exact '
                  f'(zero drift errors)')
        else:
            # drift = predicted a YLT token the gold says is wrong
            drift = sum(1 for wid in h3068
                        for p in pred.get(wid, set()) if p not in gold[wid])
            print(f'  {method}: {bad}/{len(h3068)} H3068 words differ; '
                  f'drift pairs (wrong YLT word attached): {drift}')
    print()
    print('per-word detail on H3068 + blank-Strong\'s gold words:')
    cur2 = sqlite3.connect(DB)
    cur2.row_factory = sqlite3.Row
    strongs_of = {}
    for r in cur2.execute(
            f'SELECT word_id, strongs FROM words WHERE word_id IN '
            f'({",".join("?" * len(gold))})', list(gold)):
        strongs_of[r['word_id']] = r['strongs']
    cur2.close()
    interesting = sorted(h3068 | {w for w in gold if not strongs_of.get(w)})
    for wid in interesting:
        s = strongs_of.get(wid) or '(blank)'
        exp = sorted(gold[wid])
        got = {m: sorted(results[m]['pred'].get(wid, set()))
               for m in methods}
        mark = {m: 'OK' if set(got[m]) == set(exp) else 'DIFF'
                for m in got}
        print(f'  wid {wid} [{s}] gold={exp}')
        for m in methods:
            print(f'    {m:>10} {mark[m]} pred={got[m]}')
    return results

# -------------------------------------------------------------- full run ---
def run_full(method, limit=None, write=True):
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    ylt, kjv, heb = load_data(cur)
    rows = []
    stats = dict(verses=0, ylt_toks=0, ylt_aligned=0, heb_words=0, heb_hit=0,
                 propagated=0)
    verses = sorted(set(ylt) & set(kjv) & set(heb))
    if limit:
        verses = verses[:limit]
    for v in verses:
        stats['verses'] += 1
        hw = heb[v]; kw = kjv[v]
        vr = align_verse(v, ylt[v], kw, hw, method)
        yt_n = len(tokenize(ylt[v]))
        stats['ylt_toks'] += yt_n
        stats['heb_words'] += len(hw)
        hit = set()
        for wid, _yw, _yp, lab in vr:
            hit.add(wid)
            if lab == 'propagated': stats['propagated'] += 1
        # ylt tokens reaching hebrew: distinct positions among bridged rows
        stats['ylt_aligned'] += len({yp for _w, _y, yp, lab in vr
                                     if lab == 'bridged'})
        stats['heb_hit'] += len(hit)
        rows.extend(vr)
    if write:
        cur.executescript('''
DROP TABLE IF EXISTS ylt_renderings;
CREATE TABLE ylt_renderings(
  word_id INTEGER, ylt_word TEXT, ylt_word_pos INTEGER, label TEXT);
CREATE INDEX idx_ylt_renderings_wid ON ylt_renderings(word_id);
''')
        cur.executemany('INSERT INTO ylt_renderings VALUES (?,?,?,?)', rows)
        con.commit()
    print('method:', method)
    print('verses aligned:', stats['verses'])
    print('ylt tokens:', stats['ylt_toks'], 'aligned to hebrew:',
          stats['ylt_aligned'],
          f"= {100*stats['ylt_aligned']/max(1,stats['ylt_toks']):.2f}%")
    print('hebrew words:', stats['heb_words'], 'with >=1 ylt word:',
          stats['heb_hit'],
          f"= {100*stats['heb_hit']/max(1,stats['heb_words']):.2f}%")
    print('propagated rows:', stats['propagated'])
    if write:
        print('ylt_renderings rows:',
              cur.execute('SELECT COUNT(*) FROM ylt_renderings').fetchone()[0])
    else:
        print('rows (not written):', len(rows))
    con.close()
    print('done')

if __name__ == '__main__':
    if '--eval' in sys.argv:
        gp = sys.argv[sys.argv.index('--eval') + 1] \
            if len(sys.argv) > sys.argv.index('--eval') + 1 and \
            not sys.argv[sys.argv.index('--eval') + 1].startswith('--') \
            else GOLD_DEFAULT
        run_eval(gp)
    elif '--method' in sys.argv:
        mi = sys.argv.index('--method')
        method = sys.argv[mi + 1]
        limit = int(sys.argv[sys.argv.index('--limit') + 1]) \
            if '--limit' in sys.argv else None
        write = '--no-write' not in sys.argv
        run_full(method, limit=limit, write=write)
    else:
        print(__doc__)
        sys.exit(2)
