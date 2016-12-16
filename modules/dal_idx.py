# -*- coding: utf-8 -*-

import re
import simplejson

from mzutils import slugify

from gluon import current

from c_utils import Answer, make_fastinfo
from c_db import PublLengths


IDX_CHUNK = 15


def idx_main(db=None):
    """
        index books which have set answer.needindex
    """
    if db is None:
        db = current.db

    while True:
        answers = db(db.answer.needindex == True).select(
                db.answer.id, db.answer.fastinfo,
                limitby=(0, IDX_CHUNK))
        if not answers:   # nothing more to index
            break
        for answer in answers:
            idx_row(answer)
        db.commit()


def idx_row(answer, db=None):
    """
        answer: db.answer.id, .fastinfo
    """
    if db is None:
        db = current.db

    def old_gen():
        # idx_join: answer_id, idx_long_id, role
        # idx_long: category, item
        old_recs = db(db.idx_join.answer_id == answer.id).select(
                db.idx_join.ALL, db.idx_long.category, db.idx_long.item,
                join=db.idx_long.on(db.idx_long.id == db.idx_join.idx_long_id),
                orderby=db.idx_join.id)
        for old_rec in old_recs:
            yield old_rec

    def save_to_long_idx(category, item):
        rows = db((db.idx_long.category == category) & (db.idx_long.item == item)).select(db.idx_long.id)
        if rows:
            return rows[0].id
        return db.idx_long.insert(category=category, item=item)

    def get_idx_words_and_save():
        title_string = ''
        for new_idx_rec in new_idx_recs:
            if new_idx_rec['category'].upper() == 'T':
                title_string += '-' + new_idx_rec['item']

        words = []
        re.sub('\\-+', '-', title_string.strip('-'))
        for pos, char in enumerate(title_string):
            if char == '-':
                words.append(title_string[:pos+1:pos+1+PublLengths.iword])

        save_to_word_idx(words)

    def save_to_word_idx(words):
        word_cnt = len(words)
        rows = db(db.idx_word.answer_id == answer_id).select(db.idx_word.id, db.idx_word.word)
        if rows == word_cnt:
            for pos, row in enumerate(rows):
                if row['word'] != words[pos]:
                    break
            else:
                return   # no difference
        # any difference -> rewrite all
        for pos, row in enumerate(rows[:word_cnt]):
            db.idx_word[row['id']] = dict(answer_id=answer_id, word=words[pos])
        for word in words[word_cnt:]:
            db.idx_word.insert(answer_id=answer_id, word=word)

        # TODO: zkontroluj + debug

    new_idx_recs = get_new_idx_recs(answer)
    get_idx_words_and_save()
    o_gen = old_gen()
    additional = False
    for new_idx_rec in new_idx_recs:
        if not additional:
            try:
                old = o_gen.next()
            except StopIteration:
                additional = True
            else:
                if (new_idx_rec['role'] != old.idx_join.role or
                        new_idx_rec['category'] != old.idx_long.category or
                        new_idx_rec['item'] != old.idx_long.item):   # differs -> rewrite it
                    long_id = save_to_long_idx(new_idx_rec['category'], new_idx_rec['item'])
                    db.idx_join[old.idx_join.id] = dict(idx_long_id=long_id, role=new_idx_rec['role'])
        if additional:
            long_id = save_to_long_idx(new_idx_rec['category'], new_idx_rec['item'])
            db.idx_join.insert(answer_id=answer.id, idx_long_id=long_id, role=new_idx_rec['role'])
    if not additional:
        for old in o_gen:  # there were more rows as we will have now -> delete remaining rows
            del db.idx_join[old.idx_join.id]
    db.answer[answer.id] = dict(needindex=False)


def get_new_idx_recs(answer):
    """
        Args:
            answer: answer.fastinfo
        Returns: [{'role':.., 'category':.., 'item':..}] from parsed .fastinfo
    """
    def add_subtitle(category, item, pos, subtitles):
        item = slugify(item)
        for next_subt in subtitles[pos+1:]:
            if len(item) >= PublLengths.ilong:
                break
            item += '-' + slugify(next_subt)
        new_idx_recs.append({'role': None, 'category': category, 'item': item[:PublLengths.ilong]})

    new_idx_recs = []
    title = ''
    subtitles = []
    for ln in answer.fastinfo.splitlines():
        if ln:
            fld = ln[0]
            if fld == 'T':
                title = ln[1:]
            if fld == 't':
                subtitles = [subtitle.encode('utf-8') for subtitle in simplejson.loads(ln[1:])]
            elif fld == 'A':
                for author in ln[1:].splitlines():
                    author = author.strip()
                    if author:
                        new_idx_recs.append({'role': 'aut', 'category': 'A', 'item': slugify(author)[:PublLengths.ilong]})
    if title:
        add_subtitle('T', title, -1, subtitles)
    for pos, subtitle in enumerate(subtitles):
        add_subtitle('t', subtitle, pos, subtitles)
    return new_idx_recs

# -------------------

def del_idxs(answer_id):
    db = current.db
    db(db.idx_word.id == answer_id).delete()
    db(db.idx_short.id == answer_id).delete()
    db(db.idx_join.id == answer_id).delete()
    # no testing for orphans in idx_long (after idx_join delete), so some cron action would be good

def truncate_idxs():
    db = current.db
    db.idx_join.truncate()
    db.idx_word.truncate()
    db.idx_short.truncate()
    db.idx_long.truncate('CASCADE')
    if db._dbname == 'postgres':
        db.executesql('ALTER SEQUENCE idx_join_id_seq RESTART WITH 1;')
        db.executesql('ALTER SEQUENCE idx_word_id_seq RESTART WITH 1;')
        db.executesql('ALTER SEQUENCE idx_short_id_seq RESTART WITH 1;')
        db.executesql('ALTER SEQUENCE idx_long_id_seq RESTART WITH 1;')
        db.executesql('DROP INDEX IF EXISTS idx_join_answer_id;')
        db.executesql('DROP INDEX IF EXISTS idx_join_idx_long_id;')
        db.executesql('DROP INDEX IF EXISTS idx_short_answer_id;')
        db.executesql('DROP INDEX IF EXISTS idx_word_answer_id;')
        db.executesql('DROP INDEX IF EXISTS idx_long_item;')
        db.executesql('CREATE INDEX idx_long_item ON idx_long (item);')
    db.commit()

def get_idx(answer_id):
    db = current.db
    join_rows = db(db.idx_join.answer_id == answer_id).select()
    word_rows = db(db.idx_word.answer_id == answer_id).select()
    short_rows = db(db.idx_short.answer_id == answer_id).select()
    return join_rows, word_rows, short_rows

def create_idxs(answer_id, c2_parsed, marc_obj, old_fastinfo='', updating=False):
    if updating:
        join_rows, word_rows, short_rows = get_idx(row.id)
    else:
        join_rows = word_rows = short_rows = ()

    #TODO: fix rest for index updating

    # we allow fasinfo rewrite only if we have marc_obj or if fastinfo is empty yet
    #   that way fastinfo can have additional fields (from import maybe, like keywords) which aren't supported with this (simplified) make_fastinfo call
    if marc_obj or not old_fastinfo:
        fastinfo = make_fastinfo(Answer(title=c2_parsed.title, author=c2_parsed.author, subtitles=c2_parsed.subtitle,
                                 pubplace=c2_parsed.pubplace, publisher=c2_parsed.publisher, pubyear=c2_parsed.pubyear))
        if fastinfo.encode('utf8') != old_fastinfo:
            db = current.db
            db.answer[answer_id] = {'fastinfo': fastinfo}

    if marc_obj:
        data = get_idx_data(c2_parsed, marc_obj)
    else:   # TODO: improve indexing for user descriptions (add author,..) / couldn't we run through get_idx_data() too?
        data = {'title_parts': c2_parsed.title}

    added_words = []
    parts = data['title_parts']
    if parts:
        add_title(answer_id, added_words, parts[0], ign_chars=data.get('title_ignore_chars', 0))  # 'T'
        add_titles(answer_id, added_words, parts[1:])  # 'T'
    add_title(answer_id, added_words, data.get('uniformtitle'))      # 'T'
    add_long2(answer_id, data.get('series'), 'S')
    add_short(answer_id, data.get('language_orig'), 'l')
    # iterables
    for lang in data.get('languages', ()):
        add_short(answer_id, lang, 'L')
    add_long_iter(answer_id, data.get('subjects', ()), 'K')
    add_long_iter(answer_id, data.get('categories', ()), 'C')
    add_auth(answer_id, data.get('authorities', ()))  # 'A'
    add_long_iter(answer_id, data.get('addedentries', ()), 'a')
    add_long_iter(answer_id, data.get('locations', ()), 'O')
    add_long_iter(answer_id, data.get('publishers_by_name', ()), 'P')
    add_long_iter(answer_id, data.get('publishers_by_place', ()), 'P')

def get_idx_data(c2_parsed, marc_obj):
    """get data for indexes as a dictionary
    """
    return {           # TODO: couldn't we stay at (modified) c2_parsed object instead of creating new dict here?
        'title_ignore_chars': c2_parsed.title_ignore_chars,
        'title_parts': c2_parsed.title_parts,
        'uniformtitle': marc_obj.uniformtitle(),
        'series': c2_parsed.series,
        'language_orig': c2_parsed.language_orig,
        # iterables
        'subjects': c2_parsed.subjects,
        'categories': map(lambda r:r[0] + (' ('+r[1]+')' if r[1] else ''), c2_parsed.categories),
        'authorities': c2_parsed.authorities,
        'addedentries': [fld.value() for fld in (marc_obj.addedentries() or ())],  # puvodci, TODO: improve format
        'locations': [fld.value() for fld in (marc_obj.location() or ())],  # TODO: does exist? meaning? improve format
        'publishers_by_place': c2_parsed.publishers_by_place,
        'publishers_by_name': c2_parsed.publishers_by_name,
        'languages': c2_parsed.languages,
    }

def add_titles(answer_id, added_words, titles):
    for title in titles:
        add_title(answer_id, added_words, title)

def add_title(answer_id, added_words, title, ign_chars=0):
    if title:
        parts = title.split(':')
        cnt = len(parts)
        add_long2(answer_id, title, 'T', ign_chars, added_words=added_words)
        if cnt > 1:
            parts = map(lambda p: p.strip(), parts)
            for i in xrange(1, cnt - 1):
                add_long2(answer_id, ' : '.join([parts[i]] + parts[:i] + parts[i+1:]), 'T', 0 if i else ign_chars)

def add_auth(answer_id, authorities):
    for authority in authorities:
        add_long2(answer_id, authority[0], 'A', role=authority[5])

def add_long_iter(answer_id, longs, category):
    for long in longs:
        add_long2(answer_id, long, category)

def add_long2(answer_id, long, category, ign_chars=0, role='', added_words=None):
    if long:
        slugified = add_long(answer_id, long, category, role)
        if ign_chars:
            long = long[ign_chars:].lstrip()  # ign_chars can strip '[(' to avoid next IF to be True
            add_long(answer_id, long, category, role)
        if long[:1] in '[(':
            add_long(answer_id, long[1:].lstrip().replace((']' if long[0] == '[' else ')'), '', 1), category, role)
        if added_words is not None:
            add_words(answer_id, slugified, added_words)

def add_long(answer_id, item, category, role):
    db = current.db
    full = slugify(item, connectChar=' ')
    item = full[:PublLengths.ilong]
    row = db((db.idx_long.item == item) & (db.idx_long.category == category)).select(db.idx_long.id).first()
    if row:
        idx_long_id = row.id
    else:
        idx_long_id = db.idx_long.insert(category=category, item=item)
    db.idx_join.insert(answer_id=answer_id, idx_long_id=idx_long_id, role=role)
    return full

def add_words(answer_id, slugified, added_words):
    db = current.db
    words = slugified.split()
    for i, _dummy in enumerate(words):
        word = ' '.join(words[i:])[:PublLengths.iword]
        if word not in added_words:
            added_words.append(word)
            db.idx_word.insert(answer_id=answer_id, word=word)

def add_short(answer_id, item, category):
    if item:
        db = current.db
        db.idx_short[0] = {'answer_id': answer_id, 'category': category, 'item': item[:PublLengths.ishort]}
        # we ignore slugify, as long as we have only languages here
