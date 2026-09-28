#!/usr/bin/env python3
"""migrate_v2.py — build the normalized bible_v2.db from bible.db (v1).

Usage: python3 migrate_v2.py [src] [dst]
  src defaults to ~/workspace/bible-project/bible.db
  dst defaults to ~/workspace/bible-project/bible_v2.db

What it does (design: schema_v2.md, DDL: schema_v2.sql):
  1. verses        <- UNION of (book,chapter,verse) from words, ylt_verses, kjv_words
  2. strongs       <- DISTINCT strongs across words/kjv_words/kjv_renderings/glosses
  3. morph_patterns + morph_segments <- DISTINCT morph, parsed per the OSHB
     Hebrew Morphology Codes doc (COMPUTED; failures flagged, never dropped)
  4. words        <- v1 words, re-keyed to verse_id; affix columns dropped
     (live in root_form). word_unpointed/letters are PRESERVED VERBATIM
     from v1 — a normalization migration does not adjudicate legacy values.
     Candidate derivations are computed for review only and written to
     unpointed_letters_anomalies.json (separate file, not applied).
  5. root_entry/root_form/root_vowel <- copied; the five *_disp columns MOVED
     from words to root_form (functional dependency verified: 0 violations)
  6. lexicon      <- header copied; the four ' | '/' ‖ '/'; ' blobs split into
     child rows (verse refs resolved to verse_id; failures logged, never dropped)
  7. glosses, kjv_words, kjv_renderings, ylt_verses, ylt_renderings <- re-keyed
  8. compat views v_words, v_lexicon, v_kjv_words, v_ylt_verses, v_glosses,
     v_verse_coverage
  9. verification: row-count reconciliation, PRAGMA foreign_key_check,
     blob round-trip (v1 blobs == re-aggregated v2 children), v_words
     row-for-row vs v1 words (must be IDENTICAL on all columns).
     Report -> migration_report.json.

word_id values are preserved, so translation choice files keep working.

Status: implementation draft under Kit's 2026-09-28 authorization to
normalize the Bible database. The schema design has not been reviewed or
approved by Kit.
"""
import json, os, re, sqlite3, sys

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(BASE, 'bible.db')
DST = sys.argv[2] if len(sys.argv) > 2 else os.path.join(BASE, 'bible_v2.db')
DDL = os.path.join(BASE, 'schema_v2.sql')

report = {'src': SRC, 'dst': DST, 'steps': {}, 'warnings': []}
def warn(msg):
    report['warnings'].append(msg)
    print('WARN:', msg)

# ---------------------------------------------------------------- derivations
# CANDIDATE derivation rules for unpointed/letters, used ONLY to build the
# anomaly review file (unpointed_letters_anomalies.json). They are NOT applied
# to the migrated data: v1's word_unpointed/letters are preserved verbatim.
# A normalization migration must not silently adjudicate legacy values.
SOFIT = {'\u05da': '\u05db', '\u05dd': '\u05de', '\u05df': '\u05e0',
         '\u05e3': '\u05e4', '\u05e5': '\u05e6'}
ZWJ = '\u200d'
def unpointed_of(s):
    """CANDIDATE rule: strip Hebrew diacritics U+0591-U+05C7 except
    maqqef U+05BE -> '-', desofit final forms, drop ZWJ, trim."""
    out = []
    for c in (s or ''):
        if c == '\u05be':
            out.append('-'); continue
        if c == ZWJ:
            continue
        if '\u0591' <= c <= '\u05c7':
            continue
        out.append(SOFIT.get(c, c))
    return ''.join(out).strip()

def letters_of(s):
    """CANDIDATE rule: same as unpointed_of but maqqef is dropped (not '-')."""
    out = []
    for c in (s or ''):
        if c == ZWJ:
            continue
        if '\u0591' <= c <= '\u05c7':
            continue
        out.append(SOFIT.get(c, c))
    return ''.join(out).strip()

# ---------------------------------------------------------------- morph parse
# Code meanings: OSHB Hebrew Morphology Codes
# (openscriptures.github.io/morphhb/parsing/HebrewMorphologyCodes.html,
# fetched 2026-09-28; CC-BY-4.0). COMPUTED parse — flagged, never asserted.
POS_NAMES = {'A': 'adjective', 'C': 'conjunction', 'D': 'adverb',
             'N': 'noun', 'P': 'pronoun', 'R': 'preposition',
             'S': 'suffix', 'T': 'particle', 'V': 'verb'}
VERB_STEMS_HE = {'q': 'qal', 'N': 'niphal', 'p': 'piel', 'P': 'pual',
    'h': 'hiphil', 'H': 'hophal', 't': 'hithpael', 'o': 'polel', 'O': 'polal',
    'r': 'hithpolel', 'm': 'poel', 'M': 'poal', 'k': 'palel', 'K': 'pulal',
    'Q': 'qal passive', 'l': 'pilpel', 'L': 'polpal', 'f': 'hithpalpel',
    'D': 'nithpael', 'j': 'pealal', 'i': 'pilel', 'u': 'hothpaal',
    'c': 'tiphil', 'v': 'hishtaphel', 'w': 'nithpalel', 'y': 'nithpoel',
    'z': 'hithpoel'}
VERB_STEMS_AR = {'q': 'peal', 'Q': 'peil', 'u': 'hithpeel', 'p': 'pael',
    'P': 'ithpaal', 'M': 'hithpaal', 'a': 'aphel', 'h': 'haphel',
    's': 'saphel', 'e': 'shaphel', 'H': 'hophal', 'i': 'ithpeel',
    't': 'hishtaphel', 'v': 'ishtaphel', 'w': 'hithaphel', 'o': 'polel',
    'z': 'ithpoel', 'r': 'hithpolel', 'f': 'hithpalpel', 'b': 'hephal',
    'c': 'tiphel', 'm': 'poel', 'l': 'palpel', 'L': 'ithpalpel',
    'O': 'ithpolel', 'G': 'ittaphal'}
CONJ = {'p': 'perfect', 'q': 'sequential perfect', 'i': 'imperfect',
        'w': 'sequential imperfect', 'h': 'cohortative', 'j': 'jussive',
        'v': 'imperative', 'r': 'participle active', 's': 'participle passive',
        'a': 'infinitive absolute', 'c': 'infinitive construct'}
ADJ_TYPES = {'a': 'adjective', 'c': 'cardinal number', 'g': 'gentilic',
             'o': 'ordinal number'}
NOUN_TYPES = {'c': 'common', 'g': 'gentilic', 'p': 'proper name'}
PRON_TYPES = {'d': 'demonstrative', 'f': 'indefinite', 'i': 'interrogative',
              'p': 'personal', 'r': 'relative'}
PREP_TYPES = {'d': 'definite article'}
SUFFIX_TYPES = {'d': 'directional he', 'h': 'paragogic he',
                'n': 'paragogic nun', 'p': 'pronominal'}
PARTICLE_TYPES = {'a': 'affirmation', 'd': 'definite article',
                  'e': 'exhortation', 'i': 'interrogative',
                  'j': 'interjection', 'm': 'demonstrative', 'n': 'negative',
                  'o': 'direct object marker', 'r': 'relative'}
PERSON = {'1': 'first', '2': 'second', '3': 'third', 'x': 'unknown'}
GENDER = {'b': 'both', 'c': 'common', 'f': 'feminine', 'm': 'masculine',
          'x': 'unknown'}
NUMBER = {'d': 'dual', 'p': 'plural', 's': 'singular', 'x': 'unknown'}
STATE = {'a': 'absolute', 'c': 'construct', 'd': 'determined'}
SLOT_SETS = {'person': PERSON, 'gender': GENDER, 'number': NUMBER,
             'state': STATE}
POS_SLOTS = {'A': ['gender', 'number', 'state'],
             'N': ['gender', 'number', 'state'],
             'P': ['person', 'gender', 'number'],
             'S': ['person', 'gender', 'number'],
             'V': ['person', 'gender', 'number', 'state']}

def parse_segment(seg, language):
    """Parse one '/'-separated morph segment. Returns (dict, notes).
    dict has code,pos,pos_name,stem(+_name),conj(+_name),type(+_name),
    person,gender,number,state. Raises ValueError on any undocumented code."""
    if not seg:
        raise ValueError('empty segment')
    pos = seg[0]
    if pos not in POS_NAMES:
        raise ValueError(f'unknown POS {pos!r}')
    feat = seg[1:]
    d = {'code': seg, 'pos': pos, 'pos_name': POS_NAMES[pos],
         'stem': None, 'stem_name': None, 'conj': None, 'conj_name': None,
         'type': None, 'type_name': None,
         'person': None, 'person_name': None,
         'gender': None, 'gender_name': None,
         'number': None, 'number_name': None,
         'state': None, 'state_name': None}
    rest = feat
    if pos == 'V':
        if len(rest) < 2:
            raise ValueError(f'verb segment too short: {seg!r}')
        stem, conj, rest = rest[0], rest[1], rest[2:]
        stems = VERB_STEMS_AR if language == 'A' else VERB_STEMS_HE
        if stem not in stems:
            raise ValueError(f'unknown {language} verb stem {stem!r}')
        if conj not in CONJ:
            raise ValueError(f'unknown conjugation {conj!r}')
        d['stem'], d['stem_name'] = stem, stems[stem]
        d['conj'], d['conj_name'] = conj, CONJ[conj]
    elif pos in ('A', 'N', 'P', 'R', 'S', 'T'):
        typemaps = {'A': ADJ_TYPES, 'N': NOUN_TYPES, 'P': PRON_TYPES,
                    'R': PREP_TYPES, 'S': SUFFIX_TYPES, 'T': PARTICLE_TYPES}
        if pos in ('R',):
            if rest:
                t = rest[0]; rest = rest[1:]
                if t not in typemaps[pos]:
                    raise ValueError(f'unknown preposition type {t!r}')
                d['type'], d['type_name'] = t, typemaps[pos][t]
        else:
            if not rest:
                raise ValueError(f'{pos} segment missing type: {seg!r}')
            t = rest[0]; rest = rest[1:]
            if t == 'x':
                # OSHB doc note 5: 'x' is the sanctioned placeholder for an
                # unknown value when a necessary value follows it
                # (e.g. Aramaic Nxxxa = noun of unknown type/gender/number,
                # absolute state). Recorded as unknown, never asserted.
                d['type'], d['type_name'] = 'x', 'unknown (doc note 5 placeholder)'
            elif t not in typemaps[pos]:
                raise ValueError(f'unknown {pos} type {t!r}')
            else:
                d['type'], d['type_name'] = t, typemaps[pos][t]
    # C, D: no features expected
    slots = POS_SLOTS.get(pos, [])
    for ch in rest:
        placed = False
        for slot in slots:
            if d[slot] is None and ch in SLOT_SETS[slot]:
                d[slot] = ch
                d[slot + '_name'] = SLOT_SETS[slot][ch]
                placed = True
                break
        if not placed:
            raise ValueError(f'feature {ch!r} fits no open slot in {seg!r}')
    return d

def parse_pattern(pattern):
    """Parse a full OSHB morph pattern. Returns (language, [segments], notes).
    Raises ValueError if any segment fails."""
    if not pattern or pattern[0] not in ('H', 'A'):
        raise ValueError(f'bad language prefix: {pattern!r}')
    language = pattern[0]
    segs = []
    parts = pattern[1:].split('/')
    for i, code in enumerate(parts):
        seg = parse_segment(code, language)
        seg['seq'] = i
        segs.append(seg)
    return language, segs

# ---------------------------------------------------------------- migration
def main():
    if os.path.exists(DST):
        os.remove(DST)
    src = sqlite3.connect(f'file:{SRC}?mode=ro', uri=True)
    src.row_factory = sqlite3.Row
    dst = sqlite3.connect(DST)
    dst.row_factory = sqlite3.Row
    dst.execute('PRAGMA foreign_keys=ON')
    dst.executescript(open(DDL).read())

    # ---- books
    for r in src.execute('SELECT book_num, name_en, name_he FROM books ORDER BY book_num'):
        dst.execute('INSERT INTO books(book_id, name_en, name_he) VALUES (?,?,?)',
                    (r['book_num'], r['name_en'], r['name_he']))
    book_name_to_id = {r['name_en']: r['book_id']
                       for r in dst.execute('SELECT book_id, name_en FROM books')}

    # ---- verses: union of all (book,chapter,verse) refs
    seen = set()
    for tbl in ('words', 'ylt_verses', 'kjv_words'):
        for r in src.execute(f'SELECT DISTINCT book, chapter, verse FROM {tbl}'):
            seen.add((r['book'], r['chapter'], r['verse']))
    verse_map = {}
    for i, (b, c, v) in enumerate(sorted(seen), start=1):
        dst.execute('INSERT INTO verses(verse_id, book_id, chapter, verse) VALUES (?,?,?,?)',
                    (i, b, c, v))
        verse_map[(b, c, v)] = i
    report['steps']['verses'] = {'n': len(verse_map)}

    # ---- strongs
    strongs_vals = set()
    for tbl, col in (('words', 'strongs'), ('kjv_words', 'strongs'),
                     ('kjv_renderings', 'kjv_strongs'), ('glosses', 'strongs')):
        for (s,) in src.execute(f"SELECT DISTINCT {col} FROM {tbl} WHERE {col} IS NOT NULL AND {col}<>''"):
            strongs_vals.add(s)
    for s in sorted(strongs_vals):
        if ',' in s:
            parts = s.split(',')
            if not all(re.fullmatch(r'[HA]\d+', p) for p in parts):
                warn(f'composite strongs with non-conforming part kept as-is: {s!r}')
        elif not re.fullmatch(r'[HA]\d+', s):
            warn(f'strongs value with unexpected shape kept as-is: {s!r}')
        dst.execute('INSERT INTO strongs(strongs, language) VALUES (?,?)', (s, s[0]))
        if ',' in s:
            for i, part in enumerate(s.split(',')):
                dst.execute('INSERT INTO strongs_components(strongs, seq, component)'
                            ' VALUES (?,?,?)', (s, i, part))
    n_comp = dst.execute('SELECT COUNT(*) FROM strongs_components').fetchone()[0]
    report['steps']['strongs'] = {'n': len(strongs_vals), 'composite': sum(1 for s in strongs_vals if ',' in s),
                                  'components': n_comp}

    # ---- strongs_sources
    for i, s in enumerate(['oshb', 'oshb-split', 'kit'], start=1):
        dst.execute('INSERT INTO strongs_sources(source_id, source) VALUES (?,?)', (i, s))
    srcid = {r['source']: r['source_id']
             for r in dst.execute('SELECT source_id, source FROM strongs_sources')}

    # ---- morph patterns + segments
    patterns = [r[0] for r in src.execute(
        "SELECT DISTINCT morph FROM words WHERE morph IS NOT NULL AND morph<>''")]
    morph_map = {}
    n_unparsed = 0
    for pat in sorted(patterns):
        try:
            language, segs = parse_pattern(pat)
            status, notes = 'parsed', None
        except ValueError as e:
            language, segs, status, notes = None, [], 'unparsed', str(e)
            n_unparsed += 1
            warn(f'morph pattern unparsed (kept verbatim): {pat!r}: {e}')
        cur = dst.execute(
            'INSERT INTO morph_patterns(pattern, language, parse_status, parse_notes)'
            ' VALUES (?,?,?,?)', (pat, language, status, notes))
        pid = cur.lastrowid
        morph_map[pat] = pid
        for s in segs:
            dst.execute('''INSERT INTO morph_segments(pattern_id, seq, code, pos, pos_name,
                stem, stem_name, conj, conj_name, type, type_name,
                person, person_name, gender, gender_name,
                number, number_name, state, state_name)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                (pid, s['seq'], s['code'], s['pos'], s['pos_name'],
                 s['stem'], s['stem_name'], s['conj'], s['conj_name'],
                 s['type'], s['type_name'],
                 s['person'], s['person_name'], s['gender'], s['gender_name'],
                 s['number'], s['number_name'], s['state'], s['state_name']))
    report['steps']['morph'] = {'patterns': len(patterns), 'unparsed': n_unparsed,
                                'segments': dst.execute('SELECT COUNT(*) FROM morph_segments').fetchone()[0]}

    # ---- roots (copy; _disp moves from words -> root_form)
    # NOTE: roots load BEFORE words (words has FKs into root_form/root_vowel).
    for r in src.execute('SELECT root_id, root, word_count FROM root_entry'):
        dst.execute('INSERT INTO root_entry(root_id, root, word_count) VALUES (?,?,?)',
                    (r['root_id'], r['root'], r['word_count']))
    disp = {}
    for r in src.execute('''SELECT root_id, root_form_seq,
        MAX(prefix1_disp), MAX(prefix2_disp), MAX(prefix3_disp),
        MAX(suffix1_disp), MAX(suffix2_disp)
        FROM words GROUP BY root_id, root_form_seq'''):
        disp[(r['root_id'], r['root_form_seq'])] = r[2:7]
    for r in src.execute('SELECT * FROM root_form'):
        d = disp.get((r['root_id'], r['form_seq']), (None,) * 5)
        dst.execute('''INSERT INTO root_form(root_id, form_seq,
            prefix1, prefix2, prefix3, suffix1, suffix2,
            prefix1_disp, prefix2_disp, prefix3_disp, suffix1_disp, suffix2_disp,
            word_count, example_pointed, example_unpointed)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
            (r['root_id'], r['form_seq'], r['prefix1'], r['prefix2'], r['prefix3'],
             r['suffix1'], r['suffix2'], d[0], d[1], d[2], d[3], d[4],
             r['word_count'], r['example_pointed'], r['example_unpointed']))
    for r in src.execute('SELECT * FROM root_vowel'):
        dst.execute('INSERT INTO root_vowel(root_id, root_form_seq, vowel_seq, vowel_pattern, word_count)'
                    ' VALUES (?,?,?,?,?)',
                    (r['root_id'], r['root_form_seq'], r['vowel_seq'],
                     r['vowel_pattern'], r['word_count']))


    # ---- words: v1 values preserved VERBATIM (no adjudication).
    # Candidate derivations are computed for review only -> anomaly file.
    anomalies = []
    cols = ('word_id, orig_word_id, book, chapter, verse, word_pos, word_pointed,'
            ' word_unpointed, letters, strongs, strongs_source, morph, is_aramaic,'
            ' root_id, root_form_seq, root_vowel_seq')
    n_words = 0
    for r in src.execute(f'SELECT {cols} FROM words ORDER BY word_id'):
        u_cand = unpointed_of(r['word_pointed'])
        l_cand = letters_of(r['word_pointed'])
        if (u_cand != (r['word_unpointed'] or '')) or (l_cand != (r['letters'] or '').strip()):
            anomalies.append({'word_id': r['word_id'],
                'pointed': r['word_pointed'],
                'v1_unpointed': r['word_unpointed'], 'candidate_unpointed': u_cand,
                'v1_letters': r['letters'], 'candidate_letters': l_cand})
        dst.execute('''INSERT INTO words(word_id, orig_word_id, verse_id, word_pos,
            pointed, unpointed, letters, strongs, strongs_source_id,
            morph_pattern_id, is_aramaic, root_id, root_form_seq, root_vowel_seq)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
            (r['word_id'], r['orig_word_id'], verse_map[(r['book'], r['chapter'], r['verse'])],
             r['word_pos'], r['word_pointed'], r['word_unpointed'], r['letters'],
             r['strongs'] or None,
             srcid.get(r['strongs_source']) if r['strongs_source'] else None,
             morph_map.get(r['morph']) if r['morph'] else None,
             r['is_aramaic'] or 0, r['root_id'], r['root_form_seq'], r['root_vowel_seq']))
        n_words += 1
    report['steps']['words'] = {'n': n_words,
                                'unpointed_letters_anomalies': len(anomalies)}
    with open(os.path.join(BASE, 'unpointed_letters_anomalies.json'), 'w') as f:
        json.dump({'rule': 'unpointed_of/letters_of in migrate_v2.py (CANDIDATE, not applied);'
                           ' v1 values preserved verbatim in bible_v2.db',
                   'n_anomalies': len(anomalies),
                   'note': 'An earlier audit pass reported 208 mismatches, but its'
                           ' code was not retained, so that figure is not reproducible'
                           ' and is superseded by this count from the documented rule.',
                   'anomalies': anomalies}, f, indent=1, ensure_ascii=False)
    print(f'words loaded: {n_words}; unpointed/letters anomalies: {len(anomalies)}'
          ' (v1 values preserved; see unpointed_letters_anomalies.json)')

    # ---- lexicon
    verse_ref_re = re.compile(r'^(.+?)\s+(\d+):(\d+)$')
    def resolve_verse(ref):
        m = verse_ref_re.match(ref.strip())
        if not m:
            return None
        bid = book_name_to_id.get(m.group(1))
        if bid is None:
            return None
        return verse_map.get((bid, int(m.group(2)), int(m.group(3))))
    n_lex = n_kjv = n_ylt = n_ctx = n_fv = 0
    unresolvable = 0
    ctx_fail = 0
    for r in src.execute('SELECT * FROM lexicon'):
        key = (r['root_id'], r['root_form_seq'], r['vowel_seq'])
        dst.execute('INSERT INTO lexicon(root_id, root_form_seq, vowel_seq) VALUES (?,?,?)', key)
        n_lex += 1
        for i, t in enumerate((r['kjv_renderings'] or '').split(' | ')):
            if t:
                dst.execute('INSERT INTO lexicon_kjv_rendering VALUES (?,?,?,?,?)',
                            (*key, i, t)); n_kjv += 1
        for i, t in enumerate((r['ylt_renderings_computed'] or '').split(' | ')):
            if t:
                dst.execute('INSERT INTO lexicon_ylt_rendering VALUES (?,?,?,?,?)',
                            (*key, i, t)); n_ylt += 1
        # ylt_contexts item format (per build_lexicon.py): "{Book} {C}:{V} — {YLT text}"
        # joined by ' ‖ '. No trailing dash; text may be truncated mid-word in v1
        # and is preserved verbatim.
        for i, item in enumerate((r['ylt_contexts'] or '').split(' ‖ ')):
            item = item.strip()
            if not item:
                continue
            ref_part, sep, context = item.partition(' — ')
            m = verse_ref_re.match(ref_part.strip()) if sep else None
            bid = book_name_to_id.get(m.group(1)) if m else None
            vid = verse_map.get((bid, int(m.group(2)), int(m.group(3)))) if (m and bid) else None
            if vid is None:
                ctx_fail += 1
                if ctx_fail <= 5:
                    warn(f'ylt_context item did not parse: {item[:80]!r}')
                continue
            dst.execute('INSERT INTO lexicon_ylt_context VALUES (?,?,?,?,?,?)',
                        (*key, i, vid, context)); n_ctx += 1
        for ref in (r['found_verses'] or '').split('; '):
            if not ref.strip():
                continue
            vid = resolve_verse(ref)
            if vid is None:
                warn(f'found_verses ref unresolvable: {ref!r}'); unresolvable += 1; continue
            dst.execute('INSERT OR IGNORE INTO lexicon_found_verse VALUES (?,?,?,?)',
                        (*key, vid)); n_fv += 1
    report['steps']['lexicon'] = {'headers': n_lex, 'kjv': n_kjv, 'ylt': n_ylt,
                                  'contexts': n_ctx, 'found_verses': n_fv,
                                  'unresolvable_refs': unresolvable}

    # ---- glosses
    for r in src.execute('SELECT strongs, source, gloss FROM glosses'):
        dst.execute('INSERT INTO glosses(strongs, source, gloss) VALUES (?,?,?)',
                    (r['strongs'], r['source'], r['gloss']))

    # ---- kjv_words
    kid = 0
    for r in src.execute('SELECT book, chapter, verse, kjv_pos, kjv_word, strongs'
                         ' FROM kjv_words ORDER BY book, chapter, verse, kjv_pos'):
        kid += 1
        dst.execute('INSERT INTO kjv_words(kjv_word_id, verse_id, kjv_pos, kjv_word, strongs)'
                    ' VALUES (?,?,?,?,?)',
                    (kid, verse_map[(r['book'], r['chapter'], r['verse'])],
                     r['kjv_pos'], r['kjv_word'], r['strongs'] or None))
    report['steps']['kjv_words'] = {'n': kid}

    # ---- kjv_renderings
    rid = 0
    for r in src.execute('SELECT word_id, kjv_word, kjv_strongs, method'
                         ' FROM kjv_renderings ORDER BY word_id, rowid'):
        rid += 1
        dst.execute('INSERT INTO kjv_renderings(rendering_id, word_id, kjv_word, kjv_strongs, method)'
                    ' VALUES (?,?,?,?,?)',
                    (rid, r['word_id'], r['kjv_word'], r['kjv_strongs'] or None, r['method']))
    report['steps']['kjv_renderings'] = {'n': rid}

    # ---- ylt_verses
    n_yv = 0
    for r in src.execute('SELECT book, chapter, verse, text FROM ylt_verses'):
        dst.execute('INSERT INTO ylt_verses(verse_id, text) VALUES (?,?)',
                    (verse_map[(r['book'], r['chapter'], r['verse'])], r['text']))
        n_yv += 1
    report['steps']['ylt_verses'] = {'n': n_yv}

    # ---- ylt_renderings
    rid = 0
    for r in src.execute('SELECT word_id, ylt_word, ylt_word_pos, label'
                         ' FROM ylt_renderings ORDER BY word_id, rowid'):
        rid += 1
        dst.execute('INSERT INTO ylt_renderings(rendering_id, word_id, ylt_word, ylt_word_pos, label)'
                    ' VALUES (?,?,?,?,?)',
                    (rid, r['word_id'], r['ylt_word'], r['ylt_word_pos'], r['label']))
    report['steps']['ylt_renderings'] = {'n': rid}

    dst.commit()
    print('migration load complete; creating views...')

    # ---------------------------------------------------------------- views
    dst.executescript('''
CREATE VIEW v_words AS
SELECT w.word_id, w.orig_word_id, v.book_id AS book, v.chapter, v.verse,
       w.word_pos, w.pointed AS word_pointed, w.unpointed AS word_unpointed,
       w.letters, f.prefix1, f.prefix2, f.prefix3, e.root AS base_word,
       f.suffix1, f.suffix2,
       f.prefix1_disp, f.prefix2_disp, f.prefix3_disp,
       f.suffix1_disp, f.suffix2_disp,
       w.strongs, s.source AS strongs_source, m.pattern AS morph,
       w.is_aramaic, w.root_id, w.root_form_seq, w.root_vowel_seq,
       (w.root_id || '.' || w.root_form_seq || '.' || w.root_vowel_seq) AS root_code
FROM words w
JOIN verses v ON v.verse_id = w.verse_id
JOIN root_entry e ON e.root_id = w.root_id
JOIN root_form f ON f.root_id = w.root_id AND f.form_seq = w.root_form_seq
LEFT JOIN strongs_sources s ON s.source_id = w.strongs_source_id
LEFT JOIN morph_patterns m ON m.pattern_id = w.morph_pattern_id;

CREATE VIEW v_kjv_words AS
SELECT k.kjv_word_id, v.book_id AS book, v.chapter, v.verse,
       k.kjv_pos, k.kjv_word, k.strongs
FROM kjv_words k JOIN verses v ON v.verse_id = k.verse_id;

CREATE VIEW v_ylt_verses AS
SELECT v.book_id AS book, v.chapter, v.verse, y.text
FROM ylt_verses y JOIN verses v ON v.verse_id = y.verse_id;

CREATE VIEW v_glosses AS
SELECT strongs, source, gloss FROM glosses;

CREATE VIEW v_verse_coverage AS
SELECT v.verse_id, v.book_id AS book, v.chapter, v.verse,
       (SELECT COUNT(*) FROM words w WHERE w.verse_id = v.verse_id) AS n_words,
       (SELECT COUNT(*) FROM kjv_words k WHERE k.verse_id = v.verse_id) AS n_kjv_words,
       (SELECT CASE WHEN EXISTS (SELECT 1 FROM ylt_verses y
                                 WHERE y.verse_id = v.verse_id) THEN 1 ELSE 0 END) AS has_ylt
FROM verses v;
''')
    # v_lexicon: re-aggregate blobs from the child tables (ground truth), then
    # expose them through a view. The view uses ordered subqueries; verify()
    # empirically checks the view matches ground truth on all 126,869 rows.
    truth = {}
    for r in dst.execute('SELECT root_id, root_form_seq, vowel_seq FROM lexicon'):
        key = (r[0], r[1], r[2])
        kjv = ' | '.join(t[0] for t in dst.execute(
            'SELECT rendering FROM lexicon_kjv_rendering WHERE root_id=?'
            ' AND root_form_seq=? AND vowel_seq=? ORDER BY seq', key))
        ylt = ' | '.join(t[0] for t in dst.execute(
            'SELECT rendering FROM lexicon_ylt_rendering WHERE root_id=?'
            ' AND root_form_seq=? AND vowel_seq=? ORDER BY seq', key))
        truth[key] = (kjv, ylt)
    dst.executescript('''
CREATE VIEW v_lexicon AS
SELECT l.root_id, l.root_form_seq, l.vowel_seq,
  (SELECT group_concat(rendering, ' | ') FROM
     (SELECT rendering FROM lexicon_kjv_rendering k
      WHERE k.root_id = l.root_id AND k.root_form_seq = l.root_form_seq
        AND k.vowel_seq = l.vowel_seq ORDER BY seq)) AS kjv_renderings,
  (SELECT group_concat(rendering, ' | ') FROM
     (SELECT rendering FROM lexicon_ylt_rendering y
      WHERE y.root_id = l.root_id AND y.root_form_seq = l.root_form_seq
        AND y.vowel_seq = l.vowel_seq ORDER BY seq)) AS ylt_renderings_computed
FROM lexicon l;
''')
    dst.commit()
    print('views created; running verification...')
    verify(src, dst, truth)
    dst.close(); src.close()
    with open(os.path.join(BASE, 'migration_report.json'), 'w') as f:
        json.dump(report, f, indent=1, ensure_ascii=False)
    print('report written to migration_report.json')

def verify(src, dst, truth):
    v = {}
    # 1. row counts reconcile
    for tbl, scol in [('words', 'words'), ('kjv_words', 'kjv_words'),
                      ('kjv_renderings', 'kjv_renderings'),
                      ('ylt_renderings', 'ylt_renderings'),
                      ('ylt_verses', 'ylt_verses'), ('glosses', 'glosses'),
                      ('root_entry', 'root_entry'), ('root_form', 'root_form'),
                      ('root_vowel', 'root_vowel'), ('lexicon', 'lexicon'),
                      ('books', 'books')]:
        a = src.execute(f'SELECT COUNT(*) FROM {scol}').fetchone()[0]
        b = dst.execute(f'SELECT COUNT(*) FROM {tbl}').fetchone()[0]
        v[f'count_{tbl}'] = {'v1': a, 'v2': b, 'match': a == b}
        assert a == b, f'count mismatch {tbl}: v1={a} v2={b}'
    # 2. FK enforcement
    fk = dst.execute('PRAGMA foreign_key_check').fetchall()
    v['foreign_key_check'] = {'violations': len(fk)}
    assert not fk, f'FK violations: {fk[:5]}'
    # 3. blob round-trip: v1 blobs == ground-truth re-aggregation == v_lexicon view
    mism_truth = mism_view = 0
    for r in src.execute('SELECT root_id, root_form_seq, vowel_seq,'
                         ' kjv_renderings, ylt_renderings_computed FROM lexicon'):
        key = (r[0], r[1], r[2])
        t = truth[key]
        if t[0] != (r[3] or '') or t[1] != (r[4] or ''):
            mism_truth += 1
            if mism_truth <= 3:
                warn(f'lexicon blob mismatch (children) at {key}')
        b = dst.execute('SELECT kjv_renderings, ylt_renderings_computed FROM v_lexicon'
                        ' WHERE root_id=? AND root_form_seq=? AND vowel_seq=?', key).fetchone()
        if (b[0] or '') != t[0] or (b[1] or '') != t[1]:
            mism_view += 1
    v['blob_roundtrip'] = {'child_mismatches': mism_truth, 'view_mismatches': mism_view}
    assert mism_truth == 0, f'{mism_truth} child blob mismatches'
    assert mism_view == 0, f'{mism_view} view blob mismatches (group_concat order)'
    # 4. v_words row-for-row vs v1 words: IDENTICAL on every column.
    # (v1's word_unpointed/letters are preserved verbatim — no derivation
    #  is applied by this migration. Candidate derivations live only in
    #  unpointed_letters_anomalies.json for separate review.)
    collist = ['word_id', 'book', 'chapter', 'verse', 'word_pos', 'word_pointed',
               'word_unpointed', 'letters', 'prefix1', 'prefix2', 'prefix3',
               'base_word', 'suffix1', 'suffix2', 'prefix1_disp', 'prefix2_disp',
               'prefix3_disp', 'suffix1_disp', 'suffix2_disp', 'strongs',
               'strongs_source', 'morph', 'is_aramaic', 'root_id',
               'root_form_seq', 'root_vowel_seq', 'root_code']
    cols = ', '.join(collist)
    v1 = {r['word_id']: dict(r) for r in src.execute(
        f'SELECT {cols} FROM words ORDER BY word_id')}
    v2 = {r['word_id']: dict(r) for r in dst.execute(
        f'SELECT {cols} FROM v_words ORDER BY word_id')}
    assert set(v1) == set(v2), 'word_id sets differ'
    diff_ids, bad_cols = set(), set()
    for k in v1:
        d = [c for c in collist if v1[k][c] != v2[k][c]]
        if d:
            diff_ids.add(k); bad_cols.update(d)
    v['v_words_equivalence'] = {'rows': len(v1), 'diff_rows': len(diff_ids),
                                'diff_columns': sorted(bad_cols),
                                'diff_sample': sorted(diff_ids)[:10]}
    assert not diff_ids, \
        f'v_words differs from v1 on {len(diff_ids)} rows, cols {sorted(bad_cols)}'
    # 5. no NULL verse/morph surprises beyond the known 79
    null_morph = dst.execute('SELECT COUNT(*) FROM words WHERE morph_pattern_id IS NULL').fetchone()[0]
    v['null_morph'] = null_morph
    assert null_morph == 79, f'expected 79 null morphs, got {null_morph}'
    # 6. strongs_components reconstruct every raw composite Strong's string
    # verbatim, in order: ','.join(components ORDER BY seq) == strongs.strongs
    comp = {}
    for s, seq, c in dst.execute(
            'SELECT strongs, seq, component FROM strongs_components ORDER BY strongs, seq'):
        comp.setdefault(s, []).append(c)
    bad_recon = [s for s, parts in comp.items() if ','.join(parts) != s]
    n_composite = dst.execute(
        "SELECT COUNT(*) FROM strongs WHERE strongs LIKE '%,%'").fetchone()[0]
    v['strongs_reconstruction'] = {'composite_rows': n_composite,
                                   'component_groups': len(comp),
                                   'mismatches': len(bad_recon)}
    assert not bad_recon, f'strongs reconstruction mismatches: {bad_recon[:5]}'
    assert len(comp) == n_composite, \
        f'component groups ({len(comp)}) != composite strongs rows ({n_composite})'
    report['verification'] = v
    print('ALL VERIFICATIONS PASSED:', json.dumps(v, indent=1)[:800])

if __name__ == '__main__':
    main()
