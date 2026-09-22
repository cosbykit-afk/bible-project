#!/usr/bin/env python3
"""Bible translation-builder website.

- bible.db is opened READ-ONLY (corpus: Hebrew words, KJV/YLT data, lexicon).
- website/app.db holds users, named translations, and multi-value "Other"
  rendering options.
- Per-word choices live in a flat index file per translation:
  website/user_data/translation_<id>.choices -- 264,217 bytes, ONE BYTE PER
  WORD, byte at offset (word_id - 1). The byte is the item number of the
  word's drop-down that was selected: 0 = default (no choice); the rest
  index into the word's drop-down list, rebuilt identically on every call
  as [KJV renderings | Young's-computed renderings | this translation's
  Other options]. "Other" is multi-value: every custom rendering the user
  adds becomes a new drop-down item.
"""
import html
import os
import sqlite3
from flask import Flask, request, redirect, url_for, render_template_string, jsonify, Response, g

BASE = os.path.dirname(os.path.abspath(__file__))
BIBLE_DB = os.path.join(os.path.dirname(BASE), 'bible.db')
APP_DB = os.path.join(BASE, 'app.db')
SCHEMA = os.path.join(BASE, 'schema.sql')

app = Flask(__name__)

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
    r = bible().execute('SELECT name_en FROM books WHERE book_num=?', (n,)).fetchone()
    return r['name_en'] if r else f'Book {n}'

def split_renderings(s):
    return [t for t in (s or '').split(' | ') if t]

def current_translation():
    tid = request.args.get('t')
    if tid and tid.isdigit():
        r = appdb().execute('SELECT * FROM translation WHERE translation_id=?', (tid,)).fetchone()
        if r:
            return r
    return None

# ---------------------------------------------------------------- choice index: 1 byte per word
# Each translation gets a flat file website/user_data/translation_<id>.choices:
# 264,217 bytes, byte at offset (word_id - 1). The byte is the item number of
# the word's drop-down that was selected: 0 = default (no choice); the rest
# index into dropdown_items(word), rebuilt identically on every call as
# [KJV renderings | Young's-computed renderings | this translation's Other
# options]. "Other" is multi-value: each custom rendering the user adds
# becomes a row in other_option and a new drop-down item.
N_WORDS = 264217
USER_DATA = os.path.join(BASE, 'user_data')
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

def dropdown_items(w, others):
    """The word's drop-down list, built identically on every call. The list
    index IS the byte value stored in the choices file (0 = default)."""
    items = [('— default —', None)]
    for t in split_renderings(w['kjv_renderings'])[:12]:
        items.append((f'KJV: {t}', t))
    for t in split_renderings(w['ylt_renderings_computed'])[:12]:
        items.append((f"Young's (computed): {t}", t))
    for o in others:
        items.append((f"Other: {o['text']}", o['text']))
    return items[:MAX_ITEMS]

def word_with_lex(wid):
    return bible().execute('''SELECT w.*, l.kjv_renderings, l.ylt_renderings_computed
                              FROM words w LEFT JOIN lexicon l
                                ON l.root_id=w.root_id AND l.root_form_seq=w.root_form_seq
                                   AND l.vowel_seq=w.root_vowel_seq
                              WHERE w.word_id=?''', (wid,)).fetchone()

def resolve_choice(w, others, byte):
    """Byte -> chosen rendering text, or None for default/stale."""
    items = dropdown_items(w, others)
    if 0 < byte < len(items):
        return items[byte][1]
    return None

NAV = '''
<div style="margin:10px 0;padding:8px;background:#f4f1e8;border:1px solid #ccc">
<a href="/">Books</a>
{% if trans %} | working on translation: <b>{{trans['name']}}</b>
  (<a href="/translations?t={{trans['translation_id']}}">switch</a>){% endif %}
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
    return render_template_string(PAGE, title=title, body=body, trans=trans)

# ---------------------------------------------------------------- routes
@app.route('/')
def index():
    books = bible().execute('SELECT book_num, name_en, name_he FROM books ORDER BY book_num').fetchall()
    items = ''.join(
        f'<li><a href="/book/{b["book_num"]}">{b["name_en"]}</a> <span class="heb">{b["name_he"]}</span></li>'
        for b in books)
    body = f'<ul>{items}</ul><p><a href="/translations">My translations</a></p>'
    return render('Hebrew Bible — build your translation', body, current_translation())

@app.route('/book/<int:n>')
def book(n):
    trans = current_translation()
    chaps = bible().execute('SELECT DISTINCT chapter FROM words WHERE book=? ORDER BY chapter', (n,)).fetchall()
    items = ''.join(f'<li><a href="/chapter/{n}/{c["chapter"]}{tqs(trans)}">Chapter {c["chapter"]}</a></li>'
                    for c in chaps)
    return render(f'{book_name(n)} — chapters', f'<ul>{items}</ul>', trans)

def tqs(trans):
    return f'?t={trans["translation_id"]}' if trans else ''

@app.route('/chapter/<int:n>/<int:c>')
def chapter(n, c):
    trans = current_translation()
    verses = bible().execute(
        'SELECT DISTINCT verse FROM words WHERE book=? AND chapter=? ORDER BY verse', (n, c)).fetchall()
    items = ''.join(
        f'<li><a href="/verse/{n}/{c}/{v["verse"]}{tqs(trans)}">Verse {v["verse"]}</a></li>'
        for v in verses)
    return render(f'{book_name(n)} {c} — verses', f'<ul>{items}</ul>', trans)

@app.route('/verse/<int:n>/<int:c>/<int:v>')
def verse(n, c, v):
    trans = current_translation()
    b = bible()
    words = b.execute('''SELECT w.*, l.kjv_renderings, l.ylt_renderings_computed
                         FROM words w LEFT JOIN lexicon l
                           ON l.root_id=w.root_id AND l.root_form_seq=w.root_form_seq
                              AND l.vowel_seq=w.root_vowel_seq
                         WHERE w.book=? AND w.chapter=? AND w.verse=?
                         ORDER BY w.word_pos''', (n, c, v)).fetchall()
    tid = trans['translation_id'] if trans else None
    choice_bytes = read_choices(tid) if tid else None
    others = other_options(tid) if tid else []
    parts = []
    if not trans:
        parts.append('<p><b><a href="/translations">Pick or create a translation</a></b> '
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
            ctl = f'''<form method="post" action="/choice{tqs(trans)}" style="display:inline">
<input type="hidden" name="word_id" value="{wid}">
<input type="hidden" name="next" value="/verse/{n}/{c}/{v}{tqs(trans)}">
<select name="item">{''.join(opts)}</select>
<input type="text" name="other_txt" placeholder="new Other rendering (optional)">
<button type="submit">save</button>
{'<span class="saved">\u2713</span>' if cur else ''}
</form>'''
        parts.append(f'''<div class="wordbox"><span class="heb">{w['word_pointed'] or w['word_unpointed']}</span>
 <a href="/word/{wid}{tqs(trans)}" style="font-size:.85em">detail</a><br>{ctl}</div>''')
    nav = ''
    if trans:
        nav = (f'<p><a href="/reading/{trans["translation_id"]}/{n}/{c}/{v}">reading view</a> | '
               f'<a href="/export/{trans["translation_id"]}">export translation</a></p>')
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
    return redirect(request.form.get('next', '/'))

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
        return redirect(f'/translations?t={cur.lastrowid}')
    trans = current_translation()
    rows = db.execute('SELECT * FROM translation ORDER BY updated_at DESC').fetchall()
    items = []
    for r in rows:
        tid = r['translation_id']
        n_chosen = sum(1 for x in read_choices(tid) if x) if os.path.exists(choices_path(tid)) else 0
        n_other = db.execute('SELECT COUNT(*) c FROM other_option WHERE translation_id=?', (tid,)).fetchone()['c']
        items.append(
            f'<li><a href="/verse/1/1/1?t={tid}">{html.escape(r["name"])}</a>'
            f' <span style="color:#666">{html.escape(r["description"])}'
            f' (updated {r["updated_at"]}; {n_chosen} words chosen, {n_other} Other options)</span>'
            f' | <a href="/export/{tid}">export</a></li>')
    body = f'''<ul>{''.join(items)}</ul>
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
    words = bible().execute(
        '''SELECT w.word_id, w.word_pointed, w.word_unpointed,
                  l.kjv_renderings, l.ylt_renderings_computed
           FROM words w LEFT JOIN lexicon l
             ON l.root_id=w.root_id AND l.root_form_seq=w.root_form_seq
                AND l.vowel_seq=w.root_vowel_seq
           WHERE w.book=? AND w.chapter=? AND w.verse=? ORDER BY w.word_pos''',
        (n, c, v)).fetchall()
    out = []
    for w in words:
        txt = resolve_choice(w, others, choices[w['word_id'] - 1])
        heb = w['word_pointed'] or w['word_unpointed']
        if txt:
            out.append(f'<span title="{html.escape(heb)}">{html.escape(txt)}</span>')
        else:
            out.append(f'<span class="heb" title="no choice yet">{heb}</span>')
    body = f'<p style="font-size:1.3em">{" ".join(out)}</p>'
    body += f'<p><a href="/verse/{n}/{c}/{v}?t={tid}">back to verse</a></p>'
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
    verses = b.execute('''SELECT DISTINCT book, chapter, verse FROM words ORDER BY book, chapter, verse''').fetchall()
    for vr in verses:
        words = b.execute(
            '''SELECT w.word_id, w.word_pointed, w.word_unpointed,
                      l.kjv_renderings, l.ylt_renderings_computed
               FROM words w LEFT JOIN lexicon l
                 ON l.root_id=w.root_id AND l.root_form_seq=w.root_form_seq
                    AND l.vowel_seq=w.root_vowel_seq
               WHERE w.book=? AND w.chapter=? AND w.verse=? ORDER BY w.word_pos''',
            (vr['book'], vr['chapter'], vr['verse'])).fetchall()
        parts = []
        for w in words:
            txt = resolve_choice(w, others, choices[w['word_id'] - 1])
            parts.append(txt if txt else f'[{w["word_pointed"] or w["word_unpointed"]}]')
        lines.append(f'{book_name(vr["book"])} {vr["chapter"]}:{vr["verse"]}\n{" ".join(parts)}\n')
    return Response('\n'.join(lines), mimetype='text/plain',
                    headers={'Content-Disposition': f'attachment; filename=translation_{tid}.txt'})

@app.route('/word/<int:wid>')
def word_detail(wid):
    trans = current_translation()
    b = bible()
    w = b.execute('SELECT * FROM words WHERE word_id=?', (wid,)).fetchone()
    if not w:
        return 'Unknown word', 404
    lex = b.execute('''SELECT * FROM lexicon WHERE root_id=? AND root_form_seq=? AND vowel_seq=?''',
                    (w['root_id'], w['root_form_seq'], w['root_vowel_seq'])).fetchone()
    letters = (w['letters'] or '').strip()
    letter_list = ' \u00b7 '.join(letters.split()) if letters else '(no letter data)'
    rows = [
        ('Pointed', w['word_pointed']),
        ('Unpointed', w['word_unpointed']),
        ('Letters', f'<span class="heb">{letter_list}</span>'),
        ('Root code', w['root_code']),
        ('Strong\u2019s', f"{w['strongs'] or '(none)'} <span style='color:#666'>source: {w['strongs_source'] or '?'}</span>"),
        ('Morphology', w['morph'] or '(none)'),
        ('KJV renderings', '<br>'.join(split_renderings(lex['kjv_renderings'])) if lex and lex['kjv_renderings'] else '(none)'),
        ('Young\u2019s renderings (computed)', '<br>'.join(split_renderings(lex['ylt_renderings_computed'])) if lex and lex['ylt_renderings_computed'] else '(none)'),
        ('YLT verse contexts', (lex['ylt_contexts'] or '(none)')[:2000] if lex else '(none)'),
        ('Found verses', (lex['found_verses'] or '(none)')[:1500] if lex else '(none)'),
    ]
    body = '<table>' + ''.join(f'<tr><th>{k}</th><td>{v or "(none)"}</td></tr>' for k, v in rows) + '</table>'
    body += f'<p><a href="/verse/{w["book"]}/{w["chapter"]}/{w["verse"]}{tqs(trans)}">back to verse</a></p>'
    return render(f'Word {wid} — {w["word_pointed"] or w["word_unpointed"]}', body, trans)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5057, debug=False)
