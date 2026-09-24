#!/usr/bin/env python3
"""Assemble /home/hatch/workspace/bible-project/bible.db from canonical + worker outputs.
Fails soft: missing worker files are recorded as gaps, the rest still builds.
"""
import csv, json, os, re, sqlite3, random

ROOT = '/home/hatch/workspace/bible-project'
WO = f'{ROOT}/worker-out'
CANON = f'{WO}/canon'
DB = f'{ROOT}/bible.db'
HNUM = re.compile(r'H0*(\d+)')

def norm_strongs(s):
    """Normalize a strongs token to H<number> form; return None if not parseable."""
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

gaps = []
def gap(msg):
    gaps.append(msg); print('GAP:', msg)

if os.path.exists(DB): os.remove(DB)
con = sqlite3.connect(DB)
cur = con.cursor()

cur.executescript('''
CREATE TABLE books(book_num INTEGER PRIMARY KEY, name_en TEXT, name_he TEXT);
CREATE TABLE words(
  word_id INTEGER PRIMARY KEY,
  orig_word_id TEXT,
  book INTEGER, chapter INTEGER, verse INTEGER, word_pos INTEGER,
  word_pointed TEXT, word_unpointed TEXT, letters TEXT,
  prefix1 TEXT, prefix2 TEXT, prefix3 TEXT, base_word TEXT, suffix1 TEXT, suffix2 TEXT,
  strongs TEXT, strongs_source TEXT, morph TEXT, is_aramaic INTEGER DEFAULT 0);
CREATE TABLE kjv_words(book INTEGER, chapter INTEGER, verse INTEGER, kjv_pos INTEGER,
  kjv_word TEXT, strongs TEXT);
CREATE TABLE kjv_renderings(word_id INTEGER, kjv_word TEXT, kjv_strongs TEXT);
CREATE TABLE ylt_verses(book INTEGER, chapter INTEGER, verse INTEGER, text TEXT);
CREATE TABLE glosses(strongs TEXT, source TEXT, gloss TEXT);
CREATE INDEX idx_words_ref ON words(book, chapter, verse);
CREATE INDEX idx_words_strongs ON words(strongs);
CREATE INDEX idx_kjv_ref ON kjv_words(book, chapter, verse);
CREATE INDEX idx_ylt_ref ON ylt_verses(book, chapter, verse);
CREATE INDEX idx_gloss_s ON glosses(strongs);
''')

# ---- books ----
with open(f'{CANON}/canon_books.csv', encoding='utf-8') as f:
    books = list(csv.DictReader(f))
cur.executemany('INSERT INTO books VALUES (?,?,?)',
                [(int(b['book_num']), b['name_en'], b['name_he']) for b in books])

# ---- canonical words ----
words = []
with open(f'{CANON}/canon_words.csv', encoding='utf-8') as f:
    for i, r in enumerate(csv.DictReader(f), start=1):
        words.append({
            'word_id': i, 'orig_word_id': r['id'], 'book': int(r['book']),
            'chapter': int(r['chapter']), 'verse': int(r['verse']),
            'word_pos': int(r['word_pos']), 'word_pointed': r['word_pointed'],
            'word_unpointed': r['no_vowel_raw'], 'letters': r['letters'],
            'prefix1': r['prefix1'], 'prefix2': r['prefix2'], 'prefix3': r['prefix3'],
            'base_word': r['base_word'], 'suffix1': r['suffix1'], 'suffix2': r['suffix2'],
            'strongs': norm_strongs(r['strongs']), 'strongs_source': 'kit' if r['strongs'].strip() else None,
            'morph': None, 'is_aramaic': 0})
aram = set()
try:
    with open(f'{CANON}/aramaic_word_ids.txt') as f:
        aram = set(int(x) for x in f.read().split())
except FileNotFoundError:
    gap('aramaic_word_ids.txt missing; is_aramaic left 0')
for w in words:
    if w['word_id'] in aram: w['is_aramaic'] = 1
cur.executemany('''INSERT INTO words(word_id,orig_word_id,book,chapter,verse,word_pos,
  word_pointed,word_unpointed,letters,prefix1,prefix2,prefix3,base_word,suffix1,suffix2,
  strongs,strongs_source,morph,is_aramaic)
  VALUES (:word_id,:orig_word_id,:book,:chapter,:verse,:word_pos,:word_pointed,
  :word_unpointed,:letters,:prefix1,:prefix2,:prefix3,:base_word,:suffix1,:suffix2,
  :strongs,:strongs_source,:morph,:is_aramaic)''', words)
print(f'words: {len(words)}, aramaic: {len(aram)}')
by_ref = {(w['book'], w['chapter'], w['verse'], w['word_pos']): w for w in words}

# ---- OSHB crosswalk ----
# Kit's versification is WLC-like (verse sets differ from OSHB by only 12 verses).
# Four chapters place verse 1 at the end under a bogus number; remap those.
# Token alignment per verse, in two stages:
#   Stage 1 (difflib): canonical tokens containing maqqef (U+05BE) are expanded
#     into their components BEFORE difflib, because OSHB splits maqqef-joined
#     words into separate tokens. Each component then pairs 1:1 with its own
#     OSHB token and that component's own Strong's. The word keeps the LAST
#     paired component's Strong's (the content word; also the old
#     longest-token choice in the common case), tagged strongs_source=
#     'oshb-split' for honesty. Comparison is on normalized consonantal keys:
#     Hebrew letters only, final forms (sofit) folded to regular, so the
#     canonical letters' final-folding vs OSHB's final forms no longer
#     mismatches. Canonical tokens with internal space/paseq (ketiv/qere
#     doubles, paseq rows) reduce to their consonantal component and match
#     OSHB's first component token via the same keys.
#   Stage 2 (fallback): residual 'delete'/'replace-mismatch' blocks get a
#     fallback pass matching each canonical token against still-unmatched
#     OSHB tokens in the same verse by EXACT normalized-consonant equality
#     only (no fuzzy guessing), tagged strongs_source='oshb-fallback'.
# strongs_conflicts logic is unchanged from the previous build.
import difflib
VERSE_REMAP = {(19, 17, 17): (19, 17, 1), (23, 27, 22): (23, 27, 1),
               (24, 28, 23): (24, 28, 1), (25, 2, 23): (25, 2, 1)}
MAQQEF = '־'
SOFIT_FOLD = {'ך': 'כ', 'ם': 'מ', 'ן': 'נ', 'ף': 'פ', 'ץ': 'צ'}
def cons_key(s):
    """Normalized consonantal key: Hebrew letters only, finals folded."""
    return ''.join(SOFIT_FOLD.get(ch, ch) for ch in (s or '') if 'א' <= ch <= 'ת')
oshb_path = f'{WO}/oshb/oshb_words.tsv'
stats = {'oshb_rows': 0, 'verses_aligned': 0, 'mapped_1to1': 0, 'mapped_replace': 0,
         'mapped_fallback': 0, 'canon_tokens_unmapped': 0, 'letters_match': 0,
         'strongs_filled': 0, 'stage2_fills': 0, 'split_words': 0,
         'split_words_mapped': 0, 'strongs_conflicts': 0, 'no_lemma_on_mapped': 0,
         'aramaic_agree': 0, 'aramaic_oshb_not_kit': 0, 'aramaic_kit_not_oshb': 0}
conflicts = []
stage2_fill_samples = []
canon_unmapped_verses = []
try:
    oshb_by_verse = {}
    with open(oshb_path, encoding='utf-8') as f:
        for r in csv.DictReader(f, delimiter='\t'):
            stats['oshb_rows'] += 1
            key = (int(r['book_num']), int(r['chapter']), int(r['verse']))
            oshb_by_verse.setdefault(key, []).append(r)
    for v in oshb_by_verse.values():
        v.sort(key=lambda r: int(r['word_pos']))
    canon_by_verse = {}
    for w in words:
        canon_by_verse.setdefault((w['book'], w['chapter'], w['verse']), []).append(w)
    for v in canon_by_verse.values():
        v.sort(key=lambda x: x['word_pos'])

    def find_unconsumed(key, owords, consumed, bkeys):
        if not key:
            return None
        for j, (used, bk) in enumerate(zip(consumed, bkeys)):
            if not used and bk == key:
                return j
        return None

    def align_verse(cwords, owords):
        # Stage 1: expand maqqef tokens into components before difflib.
        # Returns list of ((word, comp_key, comp_idx, n_comps), orow|None, how).
        pseudo = []
        for w in cwords:
            pt = w['word_pointed'] or ''
            if MAQQEF in pt:
                comps = [cons_key(p) for p in pt.split(MAQQEF)]
                if len(comps) > 1 and all(comps):
                    for ci, ck in enumerate(comps):
                        pseudo.append((w, ck, ci, len(comps)))
                    continue
            pseudo.append((w, cons_key(w['letters']), 0, 1))
        a = [p[1] for p in pseudo]
        b = [cons_key(r['unpointed']) for r in owords]
        sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
        out = []
        consumed = [False] * len(owords)
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == 'equal':
                for i, j in zip(range(i1, i2), range(j1, j2)):
                    consumed[j] = True
                    out.append((pseudo[i], owords[j], '1to1'))
            elif tag == 'replace':
                ca = ''.join(a[i1:i2]); cb = ''.join(b[j1:j2])
                if ca == cb and ca:
                    if (i2 - i1) == (j2 - j1):
                        for i, j in zip(range(i1, i2), range(j1, j2)):
                            consumed[j] = True
                            out.append((pseudo[i], owords[j], 'replace'))
                    else:
                        for i in range(i1, i2):
                            best = max(range(j1, j2), key=lambda j: len(b[j]))
                            consumed[best] = True
                            out.append((pseudo[i], owords[best], 'replace'))
                else:
                    # Stage 2 fallback: exact normalized-consonant match only
                    for i in range(i1, i2):
                        j = find_unconsumed(a[i], owords, consumed, b)
                        if j is not None:
                            consumed[j] = True
                            out.append((pseudo[i], owords[j], 'fallback'))
                        else:
                            out.append((pseudo[i], None, 'unmapped'))
            elif tag == 'delete':
                for i in range(i1, i2):
                    j = find_unconsumed(a[i], owords, consumed, b)
                    if j is not None:
                        consumed[j] = True
                        out.append((pseudo[i], owords[j], 'fallback'))
                    else:
                        out.append((pseudo[i], None, 'unmapped'))
            # 'insert': OSHB-only tokens (qere alternates etc.) stay
            # unconsumed so the Stage 2 fallback can still claim them
        return out

    for ckey, cwords in canon_by_verse.items():
        okey = VERSE_REMAP.get(ckey, ckey)
        owords = oshb_by_verse.get(okey)
        if not owords:
            canon_unmapped_verses.append(ckey)
            continue
        stats['verses_aligned'] += 1
        agg = {}
        for (w, key, ci, nc), orow, how in align_verse(cwords, owords):
            agg.setdefault(w['word_id'], {'w': w, 'pairs': []})['pairs'].append(
                (key, orow, how, ci, nc))
        for w in cwords:
            entry = agg.get(w['word_id'])
            plist = entry['pairs'] if entry else []
            n_comps = plist[0][4] if plist else 1
            is_split = n_comps > 1
            if is_split:
                stats['split_words'] += 1
            mapped = [(key, orow, how, ci) for (key, orow, how, ci, nc) in plist
                      if orow is not None]
            for (key, orow, how, ci) in mapped:
                stats['mapped_1to1' if how == '1to1'
                      else ('mapped_replace' if how == 'replace' else 'mapped_fallback')] += 1
                if w['letters'] == orow['unpointed']:
                    stats['letters_match'] += 1
                ostr = multi_strongs(orow['strongs'])
                if not (ostr and ostr[0]):
                    stats['no_lemma_on_mapped'] += 1
            if not mapped:
                stats['canon_tokens_unmapped'] += 1
                continue
            if is_split:
                stats['split_words_mapped'] += 1
            # Representative OSHB row: LAST paired component (content word)
            rep = max(mapped, key=lambda t: t[3])[1]
            ostr = multi_strongs(rep['strongs'])
            ostrongs = ostr[0] if ostr else None
            if w['strongs'] and ostrongs and w['strongs'] != ostrongs:
                stats['strongs_conflicts'] += 1
                if len(conflicts) < 50:
                    conflicts.append((w['word_id'], w['book'], w['chapter'], w['verse'],
                                      w['word_pos'], w['word_pointed'], w['strongs'], ostrongs))
            elif not w['strongs'] and ostrongs:
                w['strongs'] = ostrongs
                if is_split or any(h == 'fallback' for (_, _, h, _) in mapped):
                    w['strongs_source'] = 'oshb-split' if is_split else 'oshb-fallback'
                    stats['stage2_fills'] += 1
                    if len(stage2_fill_samples) < 60:
                        stage2_fill_samples.append({
                            'word_id': w['word_id'], 'book': w['book'],
                            'chapter': w['chapter'], 'verse': w['verse'],
                            'word_pos': w['word_pos'], 'word_pointed': w['word_pointed'],
                            'strongs': ostrongs, 'strongs_source': w['strongs_source'],
                            'components': [
                                {'comp_idx': ci, 'comp_consonants': key,
                                 'oshb_unpointed': orow['unpointed'],
                                 'oshb_strongs': (multi_strongs(orow['strongs']) or [None])[0],
                                 'how': how}
                                for (key, orow, how, ci) in mapped]})
                else:
                    w['strongs_source'] = 'oshb'
                    stats['strongs_filled'] += 1
            if rep.get('morph'):
                w['morph'] = rep['morph']
                o_ar = rep['morph'].startswith('A')
                if o_ar and w['is_aramaic']: stats['aramaic_agree'] += 1
                elif o_ar and not w['is_aramaic']: stats['aramaic_oshb_not_kit'] += 1
                elif not o_ar and w['is_aramaic']: stats['aramaic_kit_not_oshb'] += 1
    cur.executemany('UPDATE words SET strongs=?, strongs_source=?, morph=? WHERE word_id=?',
                    [(w['strongs'], w['strongs_source'], w['morph'], w['word_id']) for w in words])
except FileNotFoundError:
    gap('oshb_words.tsv missing; Strong_Num crosswalk not performed')
print('oshb crosswalk:', json.dumps(stats))
print('canon verses with no OSHB counterpart:', canon_unmapped_verses)
with open(f'{ROOT}/oshb_crosswalk_report.json', 'w') as f:
    json.dump({'stats': stats, 'conflict_samples': conflicts,
               'stage2_fill_samples': stage2_fill_samples,
               'unmapped_verses': canon_unmapped_verses,
               'notes': ('pair-level counters (mapped_1to1/mapped_replace/mapped_fallback) '
                         'count maqqef components, not canonical words; '
                         'canon_tokens_unmapped counts canonical words with no OSHB pairing; '
                         'strongs_source oshb-split = word kept last paired maqqef component\'s '
                         'Strong\'s; oshb-fallback = word paired via exact-consonant fallback')}, f,
              indent=2, ensure_ascii=False)

# ---- KJV ----
kjv_path = f'{WO}/kjv/kjv_words.tsv'
kjv_verse_fallback = f'{WO}/kjv/kjv_verses.tsv'
n_kjv = 0; n_render = 0; words_with_render = set()
try:
    kjv_by_verse = {}
    with open(kjv_path, encoding='utf-8') as f:
        rd = csv.DictReader(f, delimiter='\t')
        rows = []
        for r in rd:
            b, ch, v = int(r['book_num']), int(r['chapter']), int(r['verse'])
            rows.append((b, ch, v, int(r['kjv_pos']), r['kjv_word'], r['strongs']))
            kjv_by_verse.setdefault((b, ch, v), []).append((r['kjv_word'], multi_strongs(r['strongs'])))
    cur.executemany('INSERT INTO kjv_words VALUES (?,?,?,?,?,?)', rows)
    n_kjv = len(rows)
    # align: hebrew word -> kjv words in same verse sharing its Strong's
    rend = []
    for w in words:
        if not w['strongs']: continue
        for kw, ks in kjv_by_verse.get((w['book'], w['chapter'], w['verse']), []):
            if w['strongs'] in ks:
                rend.append((w['word_id'], kw, ','.join(ks)))
                words_with_render.add(w['word_id'])
    cur.executemany('INSERT INTO kjv_renderings VALUES (?,?,?)', rend)
    n_render = len(rend)
except FileNotFoundError:
    if os.path.exists(kjv_verse_fallback):
        gap('kjv_words.tsv missing; only verse-level KJV available (kjv_verses.tsv present but not ingested into word schema)')
    else:
        gap('no KJV data found at all')
print(f'kjv words: {n_kjv}, renderings: {n_render}, hebrew words with >=1 rendering: {len(words_with_render)}')

# ---- YLT ----
ylt_path = f'{WO}/ylt/ylt_verses.tsv'
n_ylt = 0
try:
    with open(ylt_path, encoding='utf-8') as f:
        rd = csv.DictReader(f, delimiter='\t')
        rows = [(int(r['book_num']), int(r['chapter']), int(r['verse']), r['text']) for r in rd]
    cur.executemany('INSERT INTO ylt_verses VALUES (?,?,?,?)', rows)
    n_ylt = len(rows)
except FileNotFoundError:
    gap('ylt_verses.tsv missing')
print(f'ylt verses: {n_ylt}')

# ---- glosses ----
gl_path = f'{WO}/lexicons/glosses.tsv'
n_gl = 0
try:
    with open(gl_path, encoding='utf-8') as f:
        rd = csv.DictReader(f, delimiter='\t')
        rows = [(norm_strongs(r['strongs']) or r['strongs'], r['source'], r['gloss']) for r in rd]
    cur.executemany('INSERT INTO glosses VALUES (?,?,?)', rows)
    n_gl = len(rows)
except FileNotFoundError:
    gap('glosses.tsv missing')
print(f'glosses: {n_gl}')

con.commit()

# ---- verification ----
ver = {}
ver['words'] = cur.execute('SELECT COUNT(*) FROM words').fetchone()[0]
ver['words_with_strongs'] = cur.execute("SELECT COUNT(*) FROM words WHERE strongs IS NOT NULL").fetchone()[0]
ver['words_with_kjv'] = cur.execute('SELECT COUNT(DISTINCT word_id) FROM kjv_renderings').fetchone()[0]
ver['words_with_gloss'] = cur.execute(
    'SELECT COUNT(DISTINCT w.word_id) FROM words w JOIN glosses g ON g.strongs=w.strongs').fetchone()[0]
ver['aramaic'] = cur.execute('SELECT COUNT(*) FROM words WHERE is_aramaic=1').fetchone()[0]
ver['kjv_words'] = cur.execute('SELECT COUNT(*) FROM kjv_words').fetchone()[0]
ver['ylt_verses'] = cur.execute('SELECT COUNT(*) FROM ylt_verses').fetchone()[0]
ver['glosses'] = cur.execute('SELECT COUNT(*) FROM glosses').fetchone()[0]
ver['books'] = cur.execute('SELECT COUNT(*) FROM books').fetchone()[0]
print(json.dumps(ver, indent=2))

# ---- 20 random verse spot checks ----
random.seed(20260920)
verses = cur.execute('SELECT DISTINCT book, chapter, verse FROM words').fetchall()
sample = random.sample(verses, 20)
with open(f'{ROOT}/spotcheck.txt', 'w', encoding='utf-8') as f:
    for (b, ch, v) in sorted(sample):
        bn = cur.execute('SELECT name_en FROM books WHERE book_num=?', (b,)).fetchone()[0]
        f.write(f'=== {bn} {ch}:{v} ===\n')
        ws = cur.execute('SELECT word_id, word_pos, word_pointed, word_unpointed, strongs, strongs_source, is_aramaic FROM words WHERE book=? AND chapter=? AND verse=? ORDER BY word_pos', (b, ch, v)).fetchall()
        for wid, wp_, wpt, wuv, st, ssrc, ar in ws:
            rr = cur.execute('SELECT kjv_word FROM kjv_renderings WHERE word_id=?', (wid,)).fetchall()
            gl = cur.execute('SELECT source, substr(gloss,1,90) FROM glosses WHERE strongs=?', (st,)).fetchall() if st else []
            f.write(f'  [{wp_}] {wpt} ({wuv}) strongs={st} src={ssrc} aram={ar}\n')
            if rr: f.write(f'      KJV: {"; ".join(r[0] for r in rr)}\n')
            for gs, gt in gl: f.write(f'      gloss[{gs}]: {gt}\n')
        y = cur.execute('SELECT text FROM ylt_verses WHERE book=? AND chapter=? AND verse=?', (b, ch, v)).fetchone()
        f.write(f'  YLT: {y[0] if y else "MISSING"}\n\n')
print('spotcheck.txt written')

with open(f'{ROOT}/assembly_report.json', 'w') as f:
    json.dump({'verification': ver, 'oshb': stats, 'kjv': {'words': n_kjv, 'renderings': n_render,
               'hebrew_words_rendered': len(words_with_render)}, 'ylt_verses': n_ylt,
               'glosses': n_gl, 'gaps': gaps}, f, indent=2)
print('gaps:', gaps)
print('DONE')
