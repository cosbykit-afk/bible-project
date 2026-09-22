#!/usr/bin/env python3
"""Bible translation-builder website.

- bible.db is opened READ-ONLY (corpus: Hebrew words, KJV/YLT data, lexicon).
- website/app.db holds users, named translations, and per-word choices.
- Per Hebrew word, the verse page offers a drop-down: KJV rendering,
  Young's rendering (COMPUTED via KJV-bridge alignment -- labeled as such),
  or Other (user-defined). Choices are saved per named translation.
"""
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

def translation_choices(tid):
    rows = appdb().execute(
        'SELECT word_id, chosen_source, chosen_text FROM translation_choice WHERE translation_id=?',
        (tid,)).fetchall()
    return {r['word_id']: (r['chosen_source'], r['chosen_text']) for r in rows}

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
    choices = translation_choices(trans['translation_id']) if trans else {}
    parts = []
    if not trans:
        parts.append('<p><b><a href="/translations">Pick or create a translation</a></b> '
                     'to start choosing word renderings.</p>')
    for w in words:
        wid = w['word_id']
        kjv_opts = split_renderings(w['kjv_renderings'])
        ylt_opts = split_renderings(w['ylt_renderings_computed'])
        cur_src, cur_txt = choices.get(wid, ('', ''))
        opts = []
        for t in kjv_opts[:12]:
            sel = ' selected' if cur_src == 'kjv' and cur_txt == t else ''
            opts.append(f'<option value="kjv|{t}"{sel}>KJV: {t}</option>')
        for t in ylt_opts[:12]:
            sel = ' selected' if cur_src == 'ylt' and cur_txt == t else ''
            opts.append(f'<option value="ylt|{t}"{sel}>Young\u2019s (computed): {t}</option>')
        sel_other = ' selected' if cur_src == 'other' else ''
        opts.append(f'<option value="other|"{sel_other}>Other\u2026</option>')
        if not cur_src:
            opts.insert(0, '<option value="" selected>\u2014 choose \u2014</option>')
        other_val = cur_txt if cur_src == 'other' else ''
        ctl = ''
        if trans:
            ctl = f'''<form method="post" action="/choice{tqs(trans)}" style="display:inline">
<input type="hidden" name="word_id" value="{wid}">
<input type="hidden" name="next" value="/verse/{n}/{c}/{v}{tqs(trans)}">
<select name="choice" onchange="this.form.other_txt.style.display =
  this.value.startsWith('other|')?'inline':'none'">{''.join(opts)}</select>
<input type="text" name="other_txt" placeholder="your rendering" value="{other_val}"
  style="display:{'inline' if cur_src=='other' else 'none'}">
<button type="submit">save</button>
{'<span class="saved">\u2713</span>' if cur_src else ''}
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
    trans = current_translation()
    if not trans:
        return 'No translation selected', 400
    wid = int(request.form['word_id'])
    raw = request.form.get('choice', '')
    if raw.startswith('other|'):
        src, txt = 'other', request.form.get('other_txt', '').strip()
    elif '|' in raw:
        src, txt = raw.split('|', 1)
    else:
        src, txt = '', ''
    db = appdb()
    if not txt:
        db.execute('DELETE FROM translation_choice WHERE translation_id=? AND word_id=?',
                   (trans['translation_id'], wid))
    else:
        db.execute('''INSERT INTO translation_choice(translation_id, word_id, chosen_source, chosen_text)
                      VALUES(?,?,?,?)
                      ON CONFLICT(translation_id, word_id)
                      DO UPDATE SET chosen_source=excluded.chosen_source,
                                    chosen_text=excluded.chosen_text,
                                    updated_at=datetime('now')''',
                   (trans['translation_id'], wid, src, txt))
        db.execute("UPDATE translation SET updated_at=datetime('now') WHERE translation_id=?",
                   (trans['translation_id'],))
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
    items = ''.join(
        f'<li><a href="/verse/1/1/1?t={r["translation_id"]}">{r["name"]}</a>'
        f' <span style="color:#666">{r["description"]} (updated {r["updated_at"]})</span>'
        f' | <a href="/export/{r["translation_id"]}">export</a></li>' for r in rows)
    body = f'''<ul>{items}</ul>
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
    choices = translation_choices(tid)
    words = bible().execute(
        'SELECT word_id, word_pointed, word_unpointed FROM words WHERE book=? AND chapter=? AND verse=? ORDER BY word_pos',
        (n, c, v)).fetchall()
    out = []
    for w in words:
        ch = choices.get(w['word_id'])
        if ch:
            src, txt = ch
            out.append(f'<span title="{src}: {w["word_pointed"] or w["word_unpointed"]}">{txt}</span>')
        else:
            out.append(f'<span class="heb" title="no choice yet">{w["word_pointed"] or w["word_unpointed"]}</span>')
    body = f'<p style="font-size:1.3em">{" ".join(out)}</p>'
    body += f'<p><a href="/verse/{n}/{c}/{v}?t={tid}">back to verse</a></p>'
    return render(f'{trans["name"]} — {book_name(n)} {c}:{v}', body, trans)

@app.route('/export/<int:tid>')
def export(tid):
    trans = appdb().execute('SELECT * FROM translation WHERE translation_id=?', (tid,)).fetchone()
    if not trans:
        return 'Unknown translation', 404
    choices = translation_choices(tid)
    b = bible()
    lines = [f'# {trans["name"]}', f'# {trans["description"]}', '']
    verses = b.execute('''SELECT DISTINCT book, chapter, verse FROM words ORDER BY book, chapter, verse''').fetchall()
    for vr in verses:
        words = b.execute(
            'SELECT word_id, word_pointed, word_unpointed FROM words WHERE book=? AND chapter=? AND verse=? ORDER BY word_pos',
            (vr['book'], vr['chapter'], vr['verse'])).fetchall()
        parts = []
        for w in words:
            ch = choices.get(w['word_id'])
            parts.append(ch[1] if ch else f'[{w["word_pointed"] or w["word_unpointed"]}]')
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
