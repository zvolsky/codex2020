# -*- coding: utf-8 -*-

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

def create_idxs(answer_id, marcrec, record, old_fastinfo=''):
    fastinfo = 'T' + marcrec.title + '\nA' + marcrec.author + '\nP' + marcrec.publisher + '\nY' + marcrec.pubyear
    if fastinfo != old_fastinfo:
        db = current.db
        db.answer[answer_id] = {'fastinfo': fastinfo}

    data = get_idx_data(marcrec, record)
    added_words = []
    parts = data['title_parts']
    if parts:
        add_title(answer_id, added_words, parts[0], ign_chars=data['title_ignore_chars'])  # 'T'
        add_titles(answer_id, added_words, parts[1:])  # 'T'
    add_title(answer_id, added_words, data['uniformtitle'])      # 'T'
    add_long2(answer_id, data['series'], 'S')
    add_short(answer_id, data['language_orig'], 'l')
    # iterables
    for lang in data['languages']:
        add_short(answer_id, lang, 'L')
    add_long_iter(answer_id, data['subjects'], 'K')
    add_long_iter(answer_id, data['categories'], 'C')
    add_auth(answer_id, data['authorities'])  # 'A'
    add_long_iter(answer_id, data['addedentries'], 'a')
    add_long_iter(answer_id, data['locations'], 'O')
    add_long_iter(answer_id, data['publishers_by_name'], 'P')
    add_long_iter(answer_id, data['publishers_by_place'], 'P')

def get_idx_data(marcrec, record):
    """get data for indexes as a dictionary
    """
    return {
        'title_ignore_chars': marcrec.title_ignore_chars,
        'title_parts': marcrec.title_parts,
        'uniformtitle': record.uniformtitle(),
        'series': marcrec.series,
        'language_orig': marcrec.language_orig,
        # iterables
        'subjects': marcrec.subjects,
        'categories': map(lambda r:r[0] + (' ('+r[1]+')' if r[1] else ''), marcrec.categories),
        'authorities': marcrec.authorities,
        'addedentries': [fld.value() for fld in (record.addedentries() or [])],  # puvodci, TODO: improve format
        'locations': [fld.value() for fld in (record.location() or [])],  # TODO: does exist? meaning? improve format
        'publishers_by_place': marcrec.publishers_by_place,
        'publishers_by_name': marcrec.publishers_by_name,
        'languages': marcrec.languages,
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
