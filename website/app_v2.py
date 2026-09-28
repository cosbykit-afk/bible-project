#!/usr/bin/env python3
"""Bible translation-builder website — v2 corpus port.

Faithful port of app.py (v1) to the normalized bible_v2.db corpus.
Behavior preserved exactly:
- bible_v2.db opened READ-ONLY (corpus).
- website/app.db holds app_user, translation, other_option (unchanged schema).
- Per-word choices: website/user_data/translation_<id>.choices, 264,217
  bytes, ONE BYTE PER WORD at offset (word_id - 1); the byte is the item
  number of the word's drop-down, rebuilt identically on every call as
  [KJV renderings | Young's-computed renderings | this translation's Other
  options]. word_id values are stable across the v1->v2 migration.
- Routes, forms, redirects, export format, and choice-file format unchanged.

What changed vs app.py:
- Queries read the normalized v2 tables (verses, root_form, morph_patterns/
  morph_segments, strongs_sources, lexicon_* child tables) instead of the
  v1 flat columns and ' | '/' ‖ ' blobs. Child-table row order preserves the
  v1 blob item order, so drop-downs render identically.
- Mount-prefix aware: every link/form/redirect goes through u(), driven by
  the WSGI SCRIPT_NAME (set by PrefixMiddleware from the X-Script-Name
  header Apache sends, or an explicit SCRIPT_NAME). This fixes the /bible
  "Books" link bug the v1 app has live.
- word detail additionally shows the parsed morphology segments and glosses,
  which only exist because of normalization; YLT contexts and found verses
  render from their child tables with resolved verse references.
"""
import html
import os
import sqlite3
from flask import Flask, request, redirect, render_template_string, Response, g

BASE = os.path.dirname(os.path.abspath(__file__))
BIBLE_DB = os.environ.get('BIBLE_DB', os.path.join(os.path.dirname(BASE), 'bible_v2.db'))
APP_DB = os.environ.get('APP_DB', os.path.join(BASE, 'app.db'))
SCHEMA = os.path.join(BASE, 'schema.sql')

app = Flask(__name__)

# ---------------------------------------------------------------- mount prefix
class PrefixMiddleware:
    """Honor the mount point Apache serves us under. Apache sets
    X-Script-Name (RequestHeader set X-Script-Name /bible); explicit
    SCRIPT_NAME env wins when set (local dev / staging)."""
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app
    def __call__(self, environ, start_response):
        prefix = (os.environ.get('SCRIPT_NAME')
                  or environ.get('HTTP_X_SCRIPT_NAME', ''))
        environ['SCRIPT_NAME'] = prefix.rstrip('/')
        return self.wsgi_app(environ, start_response)

app.wsgi_app = PrefixMiddleware(app.wsgi_app)

def u(path):
    """Prefix-aware URL: '/verse/1/1/1' -> '/bible/verse/1/1/1' under /bible."""
    root = (request.script_root or '').rstrip('/')
    return root + path

# ---------------------------------------------------------------- databases
def bible():
    if 'bible' not in g:
        con = sqlite3.connect(f'file:{BIBLE_DB}?mode=ro', uri=True)
        con.row_factory = sqlite3.Row
        g.bible = con
    return g.bible

def appdb():
    if 'appdb' not in g:
        need_init = not os.path.exists(APP_DB)
        con = sqlite3.connect(APP_DB)
        con.row_factory = sqlite3.Row
        if need_init:
            con.executescript(open(SCHEMA).read())
            con.commit()
        g.appdb = con
    return g.appdb

@app.teardown_appcontext
def close_dbs(exc):
    for k in ('bible', 'appdb'):
        con = g.pop(k, None)
        if con is not None:
            con.close()

# ---------------------------------------------------------------- helpers
def book_name(n):
    r = bible().execute('SELECT name_en FROM books WHERE book_id=?', (n,)).fetchone()
    return r['name_en'] if r else f'Book {n}'

def current_translation():
    tid = request.args.get('t')
    if tid and tid.isdigit():
        r = appdb().execute('SELECT * FROM translation WHERE translation_id=?', (tid,)).fetchone()
        if r:
            return r
    return None

# ---------------------------------------------------------------- choice index: 1 byte per word
# website/user_data/translation_<id>.choices: 264,217 bytes, byte at offset
# (word_id - 1). The byte is the item number of the word's drop-down that was
# selected: 0 = default (no choice); the rest index into dropdown_items(),
# rebuilt identically on every call as [KJV renderings | Young's-computed
# renderings | this translation's Other options].
N_WORDS = 264217
USER_DATA = os.environ.get('USER_DIR', os.path.join(BASE, 'user_data'))
MAX_ITEMS = 255    # must fit in one byte
MAX_OTHERS = 230   # headroom so KJV + Young's items always fit in the byte

def choices_path(tid):
    return os.path.join(USER_DATA, f'translation_{tid}.choices')

def read_choices(tid):
    """Whole choice file as a mutable bytearray (zeros = all default)."""
    p = choices_path(tid)
    if not os.path.exists(p):
        return bytearray(N_WORDS)
    with open(p, 'rb') as f:
        data = f.read()
    if len(data) < N_WORDS:
        data += b'\x00' * (N_WORDS - len(data))
    return bytearray(data[:N_WORDS])

def write_choice(tid, word_id, val):
    os.makedirs(USER_DATA, exist_ok=True)
    p = choices_path(tid)
    if not os.path.exists(p):
        with open(p, 'wb') as f:
            f.write(b'\x00' * N_WORDS)
    with open(p, 'r+b') as f:
        f.seek(word_id - 1)
        f.write(bytes([val & 0xFF]))

def other_options(tid):
    return appdb().execute(
        'SELECT * FROM other_option WHERE translation_id=? ORDER BY idx', (tid,)).fetchall()

# ---------------------------------------------------------------- lexicon child tables (cached)
_LEX_CACHE = {}
def lex_renderings():
    """(kjv_map, ylt_map): (root_id, root_form_seq, vowel_seq) -> ordered
    rendering lists. Cached per corpus path; the corpus is read-only so the
    cache never goes stale. Row order matches the v1 blob item order."""
    if BIBLE_DB not in _LEX_CACHE:
        kjv, ylt = {}, {}
        db = bible()
        for rid, fs, vs, t in db.execute(
                'SELECT root_id, root_form_seq, vowel_seq, rendering'
                ' FROM lexicon_kjv_rendering'
                ' ORDER BY root_id, root_form_seq, vowel_seq, seq'):
            kjv.setdefault((rid, fs, vs), []).append(t)
        for rid, fs, vs, t in db.execute(
                'SELECT root_id, root_form_seq, vowel_seq, rendering'
                ' FROM lexicon_ylt_rendering'
                ' ORDER BY root_id, root_form_seq, vowel_seq, seq'):
            ylt.setdefault((rid, fs, vs), []).append(t)
        _LEX_CACHE[BIBLE_DB] = (kjv, ylt)
    return _LEX_CACHE[BIBLE_DB]

def dropdown_items(w, others):
    """The word's drop-down list, built identically on every call. The list
    index IS the byte value stored in the choices file (0 = default)."""
    kjv_map, ylt_map = lex_renderings()
    key = (w['root_id'], w['root_form_seq'], w['root_vowel_seq'])
    items = [('— default —', None)]
    for t in kjv_map.get(key, [])[:12]:
        items.append((f'KJV: {t}', t))
    for t in ylt_map.get(key, [])[:12]:
        items.append((f"Young's (computed): {t}", t))
    for o in others:
        items.append((f"Other: {o['text']}", o['text']))
    return items[:MAX_ITEMS]

# ---------------------------------------------------------------- v2 word queries
# (v2 words has no affix/base columns; they come from root_form/root_entry)
WORD_COLS = '''w.word_id, w.word_pos, w.pointed, w.unpointed, w.letters,
    rf.prefix1, rf.prefix2, rf.prefix3, e.root AS base_word, rf.suffix1, rf.suffix2,
    rf.prefix1_disp, rf.prefix2_disp, rf.prefix3_disp,
    rf.suffix1_disp, rf.suffix2_disp,
    w.strongs, ss.source AS strongs_source,
    m.pattern AS morph, m.parse_status AS morph_status,
    w.is_aramaic, w.root_id, w.root_form_seq, w.root_vowel_seq,
    (w.root_id || '.' || w.root_form_seq || '.' || w.root_vowel_seq) AS root_code,
    v.book_id, v.chapter, v.verse'''
WORD_JOINS = '''FROM words w
    JOIN verses v ON v.verse_id=w.verse_id
    JOIN root_entry e ON e.root_id=w.root_id
    JOIN root_form rf ON rf.root_id=w.root_id AND rf.form_seq=w.root_form_seq
    LEFT JOIN strongs_sources ss ON ss.source_id=w.strongs_source_id
    LEFT JOIN morph_patterns m ON m.pattern_id=w.morph_pattern_id'''

def word_with_lex(wid):
    return bible().execute(
        f'SELECT {WORD_COLS} {WORD_JOINS} WHERE w.word_id=?', (wid,)).fetchone()

def resolve_choice(w, others, byte):
    """Byte -> chosen rendering text, or None for default/stale."""
    items = dropdown_items(w, others)
    if 0 < byte < len(items):
        return items[byte][1]
    return None

def morph_segments_html(wid):
    rows = bible().execute('''SELECT s.seq, s.code, s.pos_name, s.stem_name, s.conj_name,
        s.type_name, s.person_name, s.gender_name, s.number_name, s.state_name,
        m.parse_status
        FROM words w
        JOIN morph_patterns m ON m.pattern_id=w.morph_pattern_id
        JOIN morph_segments s ON s.pattern_id=m.pattern_id
        WHERE w.word_id=? ORDER BY s.seq''', (wid,)).fetchall()
    if not rows:
        return ''
    if rows[0]['parse_status'] != 'parsed':
        return '<i>morphology pattern not parsed (see raw pattern above)</i>'
    out = ['<ul>']
    for r in rows:
        feats = [x for x in (r['stem_name'], r['conj_name'], r['type_name'],
                             r['person_name'], r['gender_name'],
                             r['number_name'], r['state_name']) if x]
        out.append(f'<li><b>{html.escape(r["pos_name"])}</b> '
                   f'({html.escape(r["code"])}): {html.escape(", ".join(feats))}</li>')
    out.append('</ul>')
    return ''.join(out)

NAV = '''
<div style="margin:10px 0;padding:8px;background:#f4f1e8;border:1px solid #ccc">
<a href="{{u0}}/">Books</a>
{% if trans %} | working on translation: <b>{{trans['name']}}</b>
  (<a href="{{u0}}/translations?t={{trans['translation_id']}}">switch</a>){% endif %}
</div>'''

PAGE = '''<!doctype html><html><head><meta charset="utf-8">
<title>{{title}}</title>
<style>
body{font-family:Georgia,serif;max-width:900px;margin:0 auto;padding:12px;line-height:1.5}
.heb{direction:rtl;font-size:1.6em}
.wordbox{border:1px solid #ddd;margin:8px 0;padding:8px;background:#fff}
select,input[type=text]{font-size:1em;max-width:220px}
.saved{color:green;font-size:.9em}
table{border-collapse:collapse} td,th{border:1px solid #ccc;padding:4px 8px}
</style></head><body>''' + NAV + '''
<h1>{{title}}</h1>
{{body|safe}}
</body></html>'''

def render(title, body, trans=None):
    return render_template_string(PAGE, title=title, body=body, trans=trans,
                                   u0=request.script_root or '')

# ---------------------------------------------------------------- routes
@app.route('/')
def index():
    books = bible().execute('SELECT book_id, name_en, name_he FROM books ORDER BY book_id').fetchall()
    items = ''.join(
        f'<li><a href="{u("/book/" + str(b["book_id"]))}">{html.escape(b["name_en"])}</a> '
        f'<span class="heb">{b["name_he"]}</span></li>'
        for b in books)
    body = f'<ul>{items}</ul><p><a href="{u("/translations")}">My translations</a></p>'
    return render('Hebrew Bible — build your translation', body, current_translation())

@app.route('/book/<int:n>')
def book(n):
    trans = current_translation()
    chaps = bible().execute('''SELECT DISTINCT v.chapter FROM verses v
        WHERE v.book_id=? AND EXISTS (SELECT 1 FROM words w WHERE w.verse_id=v.verse_id)
        ORDER BY v.chapter''', (n,)).fetchall()
    items = ''.join(f'<li><a href="{u("/chapter/" + str(n) + "/" + str(c["chapter"]) + tqs(trans))}">'
                    f'Chapter {c["chapter"]}</a></li>' for c in chaps)
    return render(f'{book_name(n)} — chapters', f'<ul>{items}</ul>', trans)

def tqs(trans):
    return '?t=' + str(trans['translation_id']) if trans else ''

@app.route('/chapter/<int:n>/<int:c>')
def chapter(n, c):
    trans = current_translation()
    verses = bible().execute('''SELECT v.verse FROM verses v
        WHERE v.book_id=? AND v.chapter=? AND EXISTS (SELECT 1 FROM words w WHERE w.verse_id=v.verse_id)
        ORDER BY v.verse''', (n, c)).fetchall()
    items = ''.join(
        f'<li><a href="{u("/verse/" + str(n) + "/" + str(c) + "/" + str(v["verse"]) + tqs(trans))}">Verse {v["verse"]}</a></li>'
        for v in verses)
    return render(f'{book_name(n)} {c} — verses', f'<ul>{items}</ul>', trans)

@app.route('/verse/<int:n>/<int:c>/<int:v>')
def verse(n, c, v):
    trans = current_translation()
    b = bible()
    words = b.execute(f'''SELECT {WORD_COLS} {WORD_JOINS}
        JOIN verses vv ON vv.verse_id=w.verse_id
        WHERE vv.book_id=? AND vv.chapter=? AND vv.verse=?
        ORDER BY w.word_pos''', (n, c, v)).fetchall()
    tid = trans['translation_id'] if trans else None
    choice_bytes = read_choices(tid) if tid else None
    others = other_options(tid) if tid else []
    parts = []
    if not trans:
        parts.append(f'<p><b><a href="{u("/translations")}">Pick or create a translation</a></b> '
                     'to start choosing word renderings.</p>')
    for w in words:
        wid = w['word_id']
        items = dropdown_items(w, others)
        cur = choice_bytes[wid - 1] if choice_bytes is not None else 0
        if cur >= len(items):
            cur = 0  # stale byte (corpus data changed since) -> default
        opts = []
        for i, (label, _text) in enumerate(items):
            sel = ' selected' if i == cur else ''
            opts.append(f'<option value="{i}"{sel}>{html.escape(label)}</option>')
        ctl = ''
        if trans:
            ctl = f'''<form method="post" action="{u("/choice" + tqs(trans))}" style="display:inline">
<input type="hidden" name="word_id" value="{wid}">
<input type="hidden" name="next" value="/verse/{n}/{c}/{v}{tqs(trans)}">
<select name="item">{"".join(opts)}</select>
<input type="text" name="other_txt" placeholder="new Other rendering (optional)">
<button type="submit">save</button>
{"<span class='saved'>✓</span>" if cur else ""}
</form>'''
        parts.append(f'''<div class="wordbox"><span class="heb">{w["pointed"] or w["unpointed"]}</span>
 <a href="{u("/word/" + str(wid) + tqs(trans))}" style="font-size:.85em">detail</a><br>{ctl}</div>''')
    nav = ''
    if trans:
        nav = (f'<p><a href="{u("/reading/" + str(trans["translation_id"]) + "/" + str(n) + "/" + str(c) + "/" + str(v))}">reading view</a> | '
               f'<a href="{u("/export/" + str(trans["translation_id"]))}">export translation</a></p>')
    return render(f'{book_name(n)} {c}:{v}', nav + ''.join(parts), trans)

@app.route('/choice', methods=['POST'])
def choice():
    """Save one byte: the selected drop-down item number for the word.
    A non-empty other_txt adds a new multi-value Other option first."""
    trans = current_translation()
    if not trans:
        return 'No translation selected', 400
    tid = trans['translation_id']
    wid = int(request.form['word_id'])
    db = appdb()
    new_other = request.form.get('other_txt', '').strip()
    others = other_options(tid)
    if new_other:
        match = next((o for o in others if o['text'] == new_other), None)
        if match is None:
            if len(others) >= MAX_OTHERS:
                return f'Other-option limit reached ({MAX_OTHERS})', 400
            idx = max([o['idx'] for o in others] + [0]) + 1
            db.execute('INSERT INTO other_option(translation_id, idx, text) VALUES (?,?,?)',
                       (tid, idx, new_other))
            db.commit()
            others = other_options(tid)
    w = word_with_lex(wid)
    if not w:
        return 'Unknown word', 404
    items = dropdown_items(w, others)
    if new_other:
        item = next(i for i, (lab, txt) in enumerate(items)
                    if txt == new_other and lab.startswith('Other:'))
    else:
        try:
            item = int(request.form.get('item', '0'))
        except ValueError:
            item = 0
        if not 0 <= item < len(items):
            item = 0
    write_choice(tid, wid, item)
    db.execute("UPDATE translation SET updated_at=datetime('now') WHERE translation_id=?", (tid,))
    db.commit()
    return redirect(u(request.form.get('next', '/')))

@app.route('/translations', methods=['GET', 'POST'])
def translations():
    db = appdb()
    if request.method == 'POST':
        name = request.form.get('name', '').strip() or 'Untitled'
        desc = request.form.get('description', '').strip()
        urow = db.execute('SELECT user_id FROM app_user LIMIT 1').fetchone()
        if not urow:
            cur = db.execute("INSERT INTO app_user(name) VALUES('Kit')")
            uid = cur.lastrowid
        else:
            uid = urow['user_id']
        cur = db.execute('INSERT INTO translation(user_id, name, description) VALUES(?,?,?)',
                         (uid, name, desc))
        db.commit()
        return redirect(u(f'/translations?t={cur.lastrowid}'))
    trans = current_translation()
    rows = db.execute('SELECT * FROM translation ORDER BY updated_at DESC').fetchall()
    items = []
    for r in rows:
        tid = r['translation_id']
        n_chosen = sum(1 for x in read_choices(tid) if x) if os.path.exists(choices_path(tid)) else 0
        n_other = db.execute('SELECT COUNT(*) c FROM other_option WHERE translation_id=?', (tid,)).fetchone()['c']
        items.append(
            f'<li><a href="{u("/verse/1/1/1?t=" + str(tid))}">{html.escape(r["name"])}</a>'
            f' <span style="color:#666">{html.escape(r["description"])}'
            f' (updated {r["updated_at"]}; {n_chosen} words chosen, {n_other} Other options)</span>'
            f' | <a href="{u("/export/" + str(tid))}">export</a></li>')
    body = f'''<ul>{"".join(items)}</ul>
<h2>New translation</h2>
<form method="post"><input type="text" name="name" placeholder="name">
<input type="text" name="description" placeholder="description">
<button type="submit">create</button></form>'''
    return render('My translations', body, trans)

@app.route('/reading/<int:tid>/<int:n>/<int:c>/<int:v>')
def reading(tid, n, c, v):
    trans = appdb().execute('SELECT * FROM translation WHERE translation_id=?', (tid,)).fetchone()
    if not trans:
        return 'Unknown translation', 404
    choices = read_choices(tid)
    others = other_options(tid)
    words = bible().execute(f'''SELECT {WORD_COLS} {WORD_JOINS}
        WHERE v.book_id=? AND v.chapter=? AND v.verse=? ORDER BY w.word_pos''',
        (n, c, v)).fetchall()
    out = []
    for w in words:
        txt = resolve_choice(w, others, choices[w['word_id'] - 1])
        heb = w['pointed'] or w['unpointed']
        if txt:
            out.append(f'<span title="{html.escape(heb)}">{html.escape(txt)}</span>')
        else:
            out.append(f'<span class="heb" title="no choice yet">{heb}</span>')
    body = f'<p style="font-size:1.3em">{" ".join(out)}</p>'
    body += f'<p><a href="{u("/verse/" + str(n) + "/" + str(c) + "/" + str(v) + "?t=" + str(tid))}">back to verse</a></p>'
    return render(f'{trans["name"]} — {book_name(n)} {c}:{v}', body, trans)

@app.route('/export/<int:tid>')
def export(tid):
    trans = appdb().execute('SELECT * FROM translation WHERE translation_id=?', (tid,)).fetchone()
    if not trans:
        return 'Unknown translation', 404
    choices = read_choices(tid)
    others = other_options(tid)
    b = bible()
    lines = [f'# {trans["name"]}', f'# {trans["description"]}', '']
    verses = b.execute('''SELECT v.book_id, v.chapter, v.verse FROM verses v
        WHERE EXISTS (SELECT 1 FROM words w WHERE w.verse_id=v.verse_id)
        ORDER BY v.book_id, v.chapter, v.verse''').fetchall()
    for vr in verses:
        words = b.execute(f'''SELECT {WORD_COLS} {WORD_JOINS}
            WHERE v.book_id=? AND v.chapter=? AND v.verse=? ORDER BY w.word_pos''',
            (vr['book_id'], vr['chapter'], vr['verse'])).fetchall()
        parts = []
        for w in words:
            txt = resolve_choice(w, others, choices[w['word_id'] - 1])
            parts.append(txt if txt else f'[{w["pointed"] or w["unpointed"]}]')
        lines.append(f'{book_name(vr["book_id"])} {vr["chapter"]}:{vr["verse"]}\n{" ".join(parts)}\n')
    return Response('\n'.join(lines), mimetype='text/plain',
                    headers={'Content-Disposition': f'attachment; filename=translation_{tid}.txt'})

@app.route('/word/<int:wid>')
def word_detail(wid):
    trans = current_translation()
    b = bible()
    w = word_with_lex(wid)
    if not w:
        return 'Unknown word', 404
    letters = (w['letters'] or '').strip()
    letter_list = ' · '.join(letters.split()) if letters else '(no letter data)'
    affix_prefix = ' '.join((w[f'prefix{i}_disp'] or '').strip() for i in (1, 2, 3)).strip()
    affix_suffix = ' '.join((w[f'suffix{i}_disp'] or '').strip() for i in (1, 2)).strip()
    affix_parts = []
    if affix_prefix:
        affix_parts.append(f'prefix: {affix_prefix}')
    if affix_suffix:
        affix_parts.append(f'suffix: {affix_suffix}')
    affix_disp = f'<span class="heb">{" / ".join(affix_parts)}</span>' if affix_parts else '(none)'
    # lexicon children for this root vowel; re-aggregate in seq order to
    # reproduce the v1 blobs byte-for-byte (verified lossless in migration)
    kjv_map, ylt_map = lex_renderings()
    key = (w['root_id'], w['root_form_seq'], w['root_vowel_seq'])
    kjv_list = kjv_map.get(key, [])
    ylt_list = ylt_map.get(key, [])
    ctx_rows = b.execute('''SELECT vv.book_id, vv.chapter, vv.verse, c.context_text
        FROM lexicon_ylt_context c JOIN verses vv ON vv.verse_id=c.verse_id
        WHERE c.root_id=? AND c.root_form_seq=? AND c.vowel_seq=?
        ORDER BY c.seq''', key).fetchall()
    ylt_contexts = ' \u2016 '.join(
        f'{book_name(r["book_id"])} {r["chapter"]}:{r["verse"]} \u2014 {r["context_text"]}'
        for r in ctx_rows)
    fv_rows = b.execute('''SELECT vv.book_id, vv.chapter, vv.verse
        FROM lexicon_found_verse f JOIN verses vv ON vv.verse_id=f.verse_id
        WHERE f.root_id=? AND f.root_form_seq=? AND f.vowel_seq=?
        ORDER BY f.rowid''', key).fetchall()
    found_verses = '; '.join(
        f'{book_name(r["book_id"])} {r["chapter"]}:{r["verse"]}' for r in fv_rows)
    rows = [
        ('Pointed', w['pointed']),
        ('Unpointed', w['unpointed']),
        ('Letters', f'<span class="heb">{letter_list}</span>'),
        ('Affixes', affix_disp),
        ('Root code', w['root_code']),
        ('Strong\u2019s', f"{w['strongs'] or '(none)'} "
                          f"<span style='color:#666'>source: {w['strongs_source'] or '?'}</span>"),
        ('Morphology', w['morph'] or '(none)'),
        ('KJV renderings', '<br>'.join(kjv_list) if kjv_list else '(none)'),
        ('Young\u2019s renderings (computed)', '<br>'.join(ylt_list) if ylt_list else '(none)'),
        ('YLT verse contexts', (ylt_contexts or '(none)')[:2000]),
        ('Found verses', (found_verses or '(none)')[:1500]),
    ]
    body = '<table>' + ''.join(f'<tr><th>{k}</th><td>{v or "(none)"}</td></tr>' for k, v in rows) + '</table>'
    body += f'<p><a href="{u("/verse/" + str(w["book_id"]) + "/" + str(w["chapter"]) + "/" + str(w["verse"]) + tqs(trans))}">back to verse</a></p>'
    return render(f'Word {wid} — {w["pointed"] or w["unpointed"]}', body, trans)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', '5057'))
    app.run(host='127.0.0.1', port=port, debug=False)
