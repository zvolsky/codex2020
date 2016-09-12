# -*- coding: utf-8 -*-

"""Dependent on pydal, but independent on the (rest of) Web2py framework.
The exception is use of current., which makes possible calls from Web2py framework without additional parameters;
    implicit parameter set via current. is always handled at the beginning of the func
"""

import datetime
import hashlib

from gluon import current

from c_db import PublLengths
from c_utils import ean_to_fbi, suplemental_fbi
from dal_utils import answer_by_ean, answer_by_hash, get_library

if False:  # for IDE only, need web2py/__init__.py
    from web2py.gluon import current


def counter_and_commit(param):
    param['cnt_total'] += 1
    if not param['cnt_total'] % 100:
        print param['cnt_total']
        do_commit()


def do_commit(db=None):
    if db is None:
        db = current.db
    db.commit()


def update_or_insert_answer(ean, md5publ, fastinfo=None, marc=None, md5marc=None, marcrec=None, z39stamp=None, md5redirects=None, src_quality=10, db=None):
    if db is None:
        db = current.db

    def exists_update():
        if row:                           # same ean or same significant data -> same book
            if not marc or row.md5marc != md5marc:    # yes, same book, but changed info
                if not row.fastinfo or src_quality >= row.src_quality:
                    answer['fastinfo'] = fastinfo  # update fastinfo only if empty or we have better quality (>) or we have have same quality newer (=) source
                db.answer[row.id] = answer
                #touched.append((row.id, marcrec, record, row.fastinfo or ''))  # or '': to distinguish update (not None) from insert (None)
            return True  # row exists, stop next actions
            # TODO: indexovat podle answer + cycle přes všechny kopie v owned_book?

    if marc:
        md5marc = hashlib.md5(marc).hexdigest()
        z39stamp = z39stamp or datetime.datetime.utcnow()
    else:
        md5marc = z39stamp = None
    answer = dict(md5publ=md5publ, md5marc=md5marc, z39stamp=z39stamp, marc=marc,
                  ean=ean, rik=ean_to_fbi(ean),
                  country=marcrec and marcrec.country[:PublLengths.country],
                  year_from=marcrec and marcrec.pubyears[0], year_to=marcrec and marcrec.pubyears[1],
                  src_quality=src_quality, needindex=True)

    flds = (db.answer.id, db.answer.md5marc, db.answer.fastinfo, db.answer.src_quality)
    if ean:
        row = answer_by_ean(db, ean, flds)
        if exists_update():         # row exists...
            return False, row.id    # ...do not continue to find (using significant data) and do not insert

    # not found by isbn/ean
    row = answer_by_hash(db, md5publ, flds, md5redirects=md5redirects)
    if exists_update():
        return False, row.id
    else:                           # row doesn't exist yet
        answer['fastinfo'] = fastinfo
        answer['rik2'] = suplemental_fbi()
        row_id = db.answer.insert(**answer)  # ...insert it
        #touched.append((row_id, marcrec, record, None))
        return True, row_id    # True means new added rec ( + 1 into inserted count and so on .. )


def update_or_insert_owned_book(answer_id, fastinfo, cnt, db=None):
    if db is None:
        db = current.db

    owned_book = {'answer_id': answer_id, 'fastinfo': fastinfo, 'cnt': cnt, 'found_at_last': True}
    row = db(db.owned_book.answer_id == answer_id).select().first()
    if row:
        db.owned_book[row.id] = owned_book
        return row.id
    else:
        return db.owned_book.insert(**owned_book)


def update_or_insert_impressions(answer_id, owned_book_id, impression_gen, db=None):
    if db is None:
        db = current.db

    old_impressions = db(db.impression.owned_book_id == owned_book_id).select()
    len_old = len(old_impressions)
    for pos, impression in enumerate(impression_gen):
        impression['answer_id'] = answer_id
        impression['owned_book_id'] = owned_book_id
        impression['iorder'] = pos
        if pos >= len_old:
            db.impression.insert(**impression)
        else:
            db.impression[old_impressions[pos].id] = impression

def load_redirects(db=None):
    if db is None:
        db = current.db

    redirects = db().select(db.import_redirect.md5publ_computed, db.import_redirect.md5publ_final)
    return {redir.md5publ_computed: redir.md5publ_final for redir in redirects}


def load_places(db=None):
    if db is None:
        db = current.db

    places = db().select(db.place.id, db.place.place)
    return {place.place: place.id for place in places}


def place_to_place_id(places_dict, place, db=None):
    # see bellow: if db is None: db = current.db
    if not place:
        return None
    place_id = places_dict.get(place)
    if not place_id:
        if db is None:
            db = current.db
        place_id = db.place.insert(place=place)
        places_dict[place] = place_id
    return place_id

def set_imp_proc(library_id, proc=2.0, db=None):
    if db is None:
        db = current.db

    library = db.library[library_id]
    if proc > library.imp_proc:
        db.library[library_id] = {'imp_proc': min(proc, 100.0)}
        db.commit()


def set_imp_finished(library_id, db=None):
    set_imp_proc(library_id, proc=100.0, db=db)
