#!/usr/bin/env python3
"""Extract Strong's-keyed glosses from openscriptures/HebrewLexicon XML.

Sources:
  - BrownDriverBriggs.xml  -> via LexicalIndex.xml (xref strong -> bdb id)
  - HebrewStrong.xml       -> entries already keyed by id="H<n>"
Output: glosses.tsv  (strongs<TAB>source<TAB>gloss), UTF-8
"""
import os, re, html
from collections import OrderedDict, defaultdict
from lxml import etree

SRC = '/tmp/lexfetch'
NS = 'http://openscriptures.github.com/morphhb/namespace'
N = lambda tag: '{%s}%s' % (NS, tag)

def plain(el, skip_tags=frozenset()):
    """Concatenate text/tails, omitting subtrees whose local tag is in skip_tags."""
    out = []
    def walk(node, suppressed):
        tag = node.tag.rsplit('}', 1)[-1] if isinstance(node.tag, str) else ''
        sup = suppressed or tag in skip_tags
        if not sup and node.text:
            out.append(node.text)
        for child in node:
            walk(child, sup)
            if not sup and child.tail:
                out.append(child.tail)
    walk(el, False)
    return out

def norm(s):
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def def_texts(container):
    """All <def> descendant texts of container, in document order."""
    return [norm(''.join(plain(d))) for d in container.iter(N('def'))]

def bdb_gloss(entry):
    # drop status element from any fallback text
    for st in entry.iter(N('status')):
        st.getparent().remove(st)
    senses = list(entry.iter(N('sense')))
    if senses:
        parts = []
        # any top-level <def> before first sense? (direct children of entry)
        top = [d for d in entry.iterchildren(N('def'))]
        if top:
            parts.append(', '.join(norm(''.join(plain(d))) for d in top))
        for sn in senses:
            ds = def_texts(sn)
            if ds:
                parts.append(', '.join(ds))
        if parts:
            return '; '.join(parts)
    else:
        ds = [d for d in entry.iter(N('def'))]
        if ds:
            return '; '.join(norm(''.join(plain(d))) for d in ds)
    # cross-reference fallback: plain entry text (status already removed)
    t = norm(''.join(plain(entry)))
    t = re.sub(r'\s*\b(done|ref)\.?$', '', t)  # safety: stray status text
    return t

# ---- parse BDB entries ----
print('parsing BrownDriverBriggs.xml ...')
tree = etree.parse(os.path.join(SRC, 'BrownDriverBriggs.xml'))
root = tree.getroot()
bdb = {}
for e in root.iter(N('entry')):
    bdb[e.get('id')] = e
print('  BDB entries:', len(bdb))

# ---- LexicalIndex: strong -> [bdb ids] in document order ----
print('parsing LexicalIndex.xml ...')
litree = etree.parse(os.path.join(SRC, 'LexicalIndex.xml'))
strong2bdb = defaultdict(list)
non_numeric_strong = []
for xref in litree.getroot().iter(N('xref')):
    s, b = xref.get('strong'), xref.get('bdb')
    if s and not s.isdigit():
        non_numeric_strong.append((s, b)); continue
    if s and b and b not in strong2bdb[int(s)]:
        strong2bdb[int(s)].append(b)
print('  strongs with bdb mapping:', len(strong2bdb))
print('  non-numeric strong attrs skipped:', len(non_numeric_strong), non_numeric_strong)

bdb_rows = OrderedDict()
bdb_missing_map = []
bdb_missing_entry = []
bdb_nogloss = []
for n in sorted(strong2bdb):
    glosses = []
    for bid in strong2bdb[n]:
        e = bdb.get(bid)
        if e is None:
            bdb_missing_entry.append((n, bid)); continue
        g = bdb_gloss(e)
        if g:
            glosses.append(g)
        else:
            bdb_nogloss.append((n, bid))
    if glosses:
        bdb_rows['H%d' % n] = '; '.join(glosses)
    else:
        bdb_missing_map.append(n)

# ---- Strong's Hebrew ----
print("parsing HebrewStrong.xml ...")
stree = etree.parse(os.path.join(SRC, 'HebrewStrong.xml'))
strong_rows = OrderedDict()
strong_nogloss = []
for e in stree.getroot().iter(N('entry')):
    eid = e.get('id')
    m = e.find(N('meaning'))
    if m is not None:
        g = norm(''.join(plain(m)))
    else:
        u = e.find(N('usage'))
        g = norm(''.join(plain(u))) if u is not None else ''
    if not g:
        so = e.find(N('source'))
        g = norm(''.join(plain(so))) if so is not None else ''
    if g:
        strong_rows[eid] = g
    else:
        strong_nogloss.append(eid)
print('  Strong entries with gloss:', len(strong_rows))

# ---- write TSV ----
out = '/home/hatch/workspace/bible-project/worker-out/lexicons/glosses.tsv'
with open(out, 'w', encoding='utf-8', newline='') as f:
    f.write('strongs\tsource\tgloss\n')
    def keyfn(s): return int(s[1:])
    for s in sorted(set(list(bdb_rows) + list(strong_rows)), key=keyfn):
        if s in bdb_rows:
            f.write('%s\tbdb\t%s\n' % (s, bdb_rows[s].replace('\t', ' ')))
        if s in strong_rows:
            f.write('%s\tstrongs_he\t%s\n' % (s, strong_rows[s].replace('\t', ' ')))

nrows = sum(1 for _ in open(out, encoding='utf-8')) - 1
print('wrote', out, '-', nrows, 'data rows')
print('BDB strongs covered:', len(bdb_rows))
print('BDB strongs with no usable gloss:', len(bdb_missing_map))
print('BDB xref targets not in BrownDriverBriggs.xml:', len(bdb_missing_entry), bdb_missing_entry[:10])
print('BDB entries yielding empty gloss:', len(bdb_nogloss), bdb_nogloss[:10])
print('Strong entries with empty gloss:', len(strong_nogloss), strong_nogloss[:10])
# coverage ranges
def rng(nums):
    return min(nums), max(nums), len(nums)
bn = [int(s[1:]) for s in bdb_rows]; sn = [int(s[1:]) for s in strong_rows]
print('BDB H-range:', rng(bn), 'missing H in 1..8674:', [n for n in range(1,8675) if n not in set(bn)][:25], '... total missing:', 8674-len(set(bn)))
print('Strong H-range:', rng(sn), 'missing:', [n for n in range(1,8675) if n not in set(sn)])
