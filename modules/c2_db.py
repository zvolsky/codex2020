# -*- coding: utf-8 -*-

import hashlib
import random
import string

from gluon import current

from mzutils import slugify


class PublLengths(object):
    title = 255
    uniformtitle = 255
    author = 200
    isbn = 20
    series = 100
    subjects = 255
    categories = 100
    addedentries = 255
    publ_location = 255
    notes = 255
    physicaldescription = 255
    publisher = 255
    pubyear = 100
    country = 3

    # for indexes (index tables idx..)
    iword = 16
    ishort = 3
    ilong = 60
    irole = 3

    question_min = 3
    question = 60


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

    fastinfo = make_fastinfo(c2_parsed.title, c2_parsed.author, c2_parsed.publisher, c2_parsed.pubyear)
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

def ean_to_rik(ean):
    """convert last numbers of EAN into (reverted) rik or creates a random one
    rik is designed to find books easier without barcode readers
    """
    return ean[:-6:-1] if (ean and len(ean) >= 5) else ''.join(random.choice(string.digits) for _ in range(5))

def publ_hash(title, author, publisher, pubyear):
    src = '%s|%s|%s|%s' % (title, author, publisher, pubyear)
    if type(src) == unicode:
        src = src.encode('utf-8')
    return hashlib.md5(src).hexdigest()

def answer_by_ean(db, ean, flds):
    """return: row or None
    """
    if ean[:3] == '977':  # can have everything in [10:12] position
        return db(db.answer.ean.startswith(ean[:10])).select(*flds).first()
    else:
        return db(db.answer.ean == ean).select(*flds).first()

def answer_by_hash(db, md5publ, flds):
    """return: row or None
    """
    return db(db.answer.md5publ == md5publ).select(*flds).first()

def make_fastinfo(title, author, publisher, pubyear):
    return 'T' + title + '\nA' + author + '\nP' + publisher + '\nY' + pubyear

def get_libstyle():
    """provides information about allowed/disabled fields
    from session.libstyle if present
    and direct from db if session.libstyle is missing yet
    """
    if current.session.libstyle:
        return current.session.libstyle

    db = current.db
    library = db(db.library.id == current.auth.library_id).select().first()

    libstyle = []
    libstyle.append('I' if library.st_imp_id else ' ')
    libstyle.append('O' if library.st_imp_ord else ' ')
    libstyle.append(str(library.st_imp_rik) if 2 <= library.st_imp_rik <= 5 else '3')
    libstyle.append('B' if library.st_imp_bc else ' ')
    libstyle.append('P' if library.st_imp_pl else ' ')
    libstyle.append('g' if library.st_imp_sg else ' ')
    libstyle.append(str(len(library.st_imp_sgsep)))      # 1 char length of sg separator
    libstyle.append((library.st_imp_sgsep + '   ')[:3])  # 3 char content of sg separator
    libstyle.append(library.st_imp_sgmod1 or ' ')
    libstyle.append(library.st_imp_sgmod2 or ' ')
    libstyle.append('G' if library.st_tit_sg else ' ')
    libstyle.append('s' if library.st_imp_st else ' ')
    libstyle.append('S' if library.st_tit_st else ' ')

    # session.libstyle = 'IO.BPg......GsS'  # character position IS important
    current.session.libstyle = libstyle = ''.join(libstyle)
    assert len(libstyle) == 15
    return libstyle

def finish_bill(bill_id):
    """will finish the opened bill
    """
    db = current.db
    session = current.session
    cnt_imp = db(db.impr_hist.bill_id == bill_id).count()   # warning: after removing impression as Mistake later, this count can stay higher
    db.bill[bill_id] = dict(cnt_imp=cnt_imp, imp_added=datetime.datetime.utcnow())
    if 'bill' in session:
        del session.bill
