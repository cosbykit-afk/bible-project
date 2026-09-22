#!/usr/bin/env python3
"""Parse Open Scriptures Hebrew Bible (morphhb) WLC XML into a flat TSV word list.

Reads /tmp/morphhb-check/wlc/*.xml (39 books), extracts every <w> element in
document order, and writes:
  book_num, chapter, verse, word_pos, strongs, morph, pointed, unpointed
plus aggregate stats printed as JSON to stdout.

Rules (documented in README.txt):
- word_pos: 1-based, sequential <w> elements in XML document order per verse,
  including the nested qere <w> (qere immediately follows its ketiv in doc order).
- strongs: all digit runs in @lemma, each prefixed 'H', joined by ';'.
  Aramaic lemmas use the same numeric format in OSHB (distinguished by morph
  starting with 'A'); recorded as-is, not force-fit.
- pointed: raw <w> text (keeps OSHB '/' morpheme separators).
- unpointed: codepoints U+05D0..U+05EA only, in order.
- seg elements (maqqef, sof pasuq, paseq, samekh/pe, etc.) are NOT attached to
  words; their counts are reported as stats.
"""
import xml.etree.ElementTree as ET
import re, os, json, collections

SRC = '/tmp/morphhb-check/wlc'
OUT = '/home/hatch/workspace/bible-project/worker-out/oshb'
NS = '{http://www.bibletechnologies.net/2003/OSIS/namespace}'

BOOKMAP = {'Gen':1,'Exod':2,'Lev':3,'Num':4,'Deut':5,'Josh':6,'Judg':7,'Ruth':8,
 '1Sam':9,'2Sam':10,'1Kgs':11,'2Kgs':12,'1Chr':13,'2Chr':14,'Ezra':15,'Neh':16,
 'Esth':17,'Job':18,'Ps':19,'Prov':20,'Eccl':21,'Song':22,'Isa':23,'Jer':24,
 'Lam':25,'Ezek':26,'Dan':27,'Hos':28,'Joel':29,'Amos':30,'Obad':31,'Jonah':32,
 'Mic':33,'Nah':34,'Hab':35,'Zeph':36,'Hag':37,'Zech':38,'Mal':39}
BOOKNAMES = {1:'Genesis',2:'Exodus',3:'Leviticus',4:'Numbers',5:'Deuteronomy',
 6:'Joshua',7:'Judges',8:'Ruth',9:'1 Samuel',10:'2 Samuel',11:'1 Kings',
 12:'2 Kings',13:'1 Chronicles',14:'2 Chronicles',15:'Ezra',16:'Nehemiah',
 17:'Esther',18:'Job',19:'Psalms',20:'Proverbs',21:'Ecclesiastes',
 22:'Song of Solomon',23:'Isaiah',24:'Jeremiah',25:'Lamentations',26:'Ezekiel',
 27:'Daniel',28:'Hosea',29:'Joel',30:'Amos',31:'Obadiah',32:'Jonah',
 33:'Micah',34:'Nahum',35:'Habakkuk',36:'Zephaniah',37:'Haggai',
 38:'Zechariah',39:'Malachi'}
ABBR = {v:k for k,v in BOOKMAP.items()}

def norm_strongs(lemma):
    if not lemma:
        return ''
    nums = re.findall(r'\d+', lemma)
    return ';'.join('H' + n for n in nums)

def unpointed(text):
    return ''.join(c for c in (text or '') if '\u05d0' <= c <= '\u05ea')  # U+05D0..U+05EA

def n_key(n):
    try:
        return tuple(int(x) for x in n.split('.'))
    except Exception:
        return None

stats = {
    'total_words': 0,
    'per_book': collections.Counter(),
    'per_book_verses': collections.Counter(),
    'total_verses': 0,
    'no_lemma_attr': 0,          # lemma attribute missing or empty
    'lemma_no_digits': 0,        # lemma present but no digit run (e.g. 'b','l')
    'lemma_no_digits_samples': collections.Counter(),
    'no_morph': 0,
    'multi_strongs': 0,
    'multi_strongs_samples': [],
    'ketiv': 0,
    'qere': 0,
    'aramaic_words': 0,         # morph startswith 'A'
    'aramaic_samples': [],
    'words_outside_verse': 0,
    'words_outside_verse_samples': [],
    'ws_in_pointed': 0,          # tabs/newlines found in word text (sanitized)
    'empty_pointed': 0,
    'empty_unpointed': 0,
    'seg_types': collections.Counter(),
    'verse_dupes': 0,
    'books_seen': [],
}
seen_verses = set()
aram_seen_lemmas = set()

def parse_osisid(ref):
    # 'Gen.1.1' -> ('Gen',1,1)
    parts = ref.split('.')
    return parts[0], int(parts[1]), int(parts[2])

os.makedirs(OUT, exist_ok=True)
out_path = os.path.join(OUT, 'oshb_words.tsv')

with open(out_path, 'w', encoding='utf-8') as out:
    out.write('book_num\tchapter\tverse\tword_pos\tstrongs\tmorph\tpointed\tunpointed\n')
    for abbr, bnum in sorted(BOOKMAP.items(), key=lambda kv: kv[1]):
        path = os.path.join(SRC, abbr + '.xml')
        assert os.path.exists(path), path
        cur_book = None; cur_ch = None
        verse_open = False; v_book = v_ch = v_v = None; word_pos = 0
        in_qere = 0
        verse_n_seq = []
        for ev, el in ET.iterparse(path, events=('start','end')):
            tag = el.tag
            if tag == NS + 'seg' and ev == 'start':
                stats['seg_types'][el.get('type')] += 1
            elif tag == NS + 'div' and ev == 'start' and el.get('type') == 'book':
                cur_book = el.get('osisID')
                assert cur_book == abbr, (path, cur_book)
                stats['books_seen'].append(cur_book)
            elif tag == NS + 'chapter' and ev == 'start':
                b, c, _ = parse_osisid(el.get('osisID') + '.1')
                cur_ch = int(el.get('osisID').split('.')[1])
                assert b == abbr, (path, el.get('osisID'))
            elif tag == NS + 'verse' and ev == 'start' and el.get('osisID') is not None:
                b, c, v = parse_osisid(el.get('osisID'))
                if verse_open:
                    stats['verse_dupes'] += 1  # nested verse open (should not happen)
                verse_open = True; v_book, v_ch, v_v = b, c, v; word_pos = 0
                key = (BOOKMAP[b], c, v)
                if key in seen_verses:
                    stats['verse_dupes'] += 1
                seen_verses.add(key)
                stats['total_verses'] += 1
                stats['per_book_verses'][bnum] += 1
            elif tag == NS + 'verse' and ev == 'end':
                verse_open = False
                el.clear()
            elif tag == NS + 'rdg' and ev == 'start' and el.get('type') == 'x-qere':
                in_qere += 1
            elif tag == NS + 'rdg' and ev == 'end' and el.get('type') == 'x-qere':
                in_qere -= 1
            elif tag == NS + 'w' and ev == 'start':
                if not verse_open:
                    stats['words_outside_verse'] += 1
                    if len(stats['words_outside_verse_samples']) < 5:
                        stats['words_outside_verse_samples'].append(
                            (abbr, cur_ch, el.get('id'), ''))
                    continue
                word_pos += 1
                # stash per-word info; text is captured at the 'end' event
                # (at 'start' el.text is not yet reliably populated)
                el.set('_vpos', str(word_pos))
                el.set('_in_qere', '1' if in_qere else '0')
            elif tag == NS + 'w' and ev == 'end':
                if not verse_open:
                    el.clear(); continue
                word_pos = int(el.get('_vpos'))
                in_q = el.get('_in_qere') == '1'
                lemma = el.get('lemma')
                morph = el.get('morph') or ''
                wtype = el.get('type') or ''
                text = ''.join(el.itertext())  # pointed text incl. any nested segs
                if not lemma:
                    stats['no_lemma_attr'] += 1
                strongs = norm_strongs(lemma)
                if lemma and not strongs:
                    stats['lemma_no_digits'] += 1
                    stats['lemma_no_digits_samples'][lemma] += 1
                if not morph:
                    stats['no_morph'] += 1
                if strongs.count(';') >= 1:
                    stats['multi_strongs'] += 1
                    if len(stats['multi_strongs_samples']) < 10:
                        stats['multi_strongs_samples'].append(
                            (f'{abbr}.{v_ch}.{v_v}', lemma, strongs, text))
                if wtype == 'x-ketiv':
                    stats['ketiv'] += 1
                if in_q:
                    stats['qere'] += 1
                if morph.startswith('A'):
                    stats['aramaic_words'] += 1
                    key = (lemma, morph, text)
                    if key not in aram_seen_lemmas and len(stats['aramaic_samples']) < 12:
                        aram_seen_lemmas.add(key)
                        stats['aramaic_samples'].append(
                            {'ref': f'{abbr} {v_ch}:{v_v}', 'lemma': lemma,
                             'morph': morph, 'pointed': text,
                             'strongs': strongs})
                pointed = text
                if re.search(r'[\t\n\r]', pointed):
                    stats['ws_in_pointed'] += 1
                    pointed = re.sub(r'[\t\n\r]', ' ', pointed)
                up = unpointed(pointed)
                if not pointed:
                    stats['empty_pointed'] += 1
                    if len(stats.get('empty_samples', [])) < 10:
                        stats.setdefault('empty_samples', []).append(
                            (f'{abbr}.{v_ch}.{v_v}', word_pos, lemma, morph))
                if not up:
                    stats['empty_unpointed'] += 1
                out.write(f"{bnum}\t{v_ch}\t{v_v}\t{word_pos}\t{strongs}\t{morph}\t{pointed}\t{up}\n")
                stats['total_words'] += 1
                stats['per_book'][bnum] += 1
                el.clear()
        # end file

# finalize JSON-serializable stats
s = dict(stats)
s['per_book'] = {str(k): v for k, v in sorted(stats['per_book'].items())}
s['per_book_verses'] = {str(k): v for k, v in sorted(stats['per_book_verses'].items())}
s['lemma_no_digits_samples'] = dict(stats['lemma_no_digits_samples'].most_common(20))
s['seg_types'] = dict(stats['seg_types'])
s['books_seen'] = stats['books_seen']
with_strongs = s['total_words'] - s['no_lemma_attr'] - s['lemma_no_digits']
s['words_with_strongs'] = with_strongs
s['pct_with_strongs'] = round(100.0 * with_strongs / s['total_words'], 3)
print(json.dumps(s, ensure_ascii=False, indent=1))
