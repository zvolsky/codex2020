# -*- coding: utf-8 -*-

"""From proprietary import call:
    - param=init_param() and init_import(param, cnt_total) before the import
    - import functions:
        -- added, answer_id = update_or_insert_answer()
        -- owned_book_id = update_or_insert_owned_book()
        -- update_or_insert_impressions()
    - counter_and_commit_if_100(param, added) with each imported book;
            added is (1st tuple item of the) result from update_or_insert_answer()
    - finished(param) after the import

Dependent on pydal, but independent on the (rest of) Web2py framework.
    The exception is use of current., which makes possible calls from Web2py framework without additional parameters;
    implicit parameter set via current. is always handled at the beginning of the func
"""

import datetime
import hashlib

from gluon import current

from c_db import PublLengths
from c_utils import ean_to_fbi, suplemental_fbi
from dal_idx import idx_row
from dal_utils import answer_by_ean, answer_by_hash, get_library

if False:  # for IDE only, need web2py/__init__.py
    from web2py.gluon import current


# temporary setting - TODO: use better setting after we will allow more sources in single application
extsrc = current.db().select(current.db.extsrc.id, orderby=current.db.extsrc.id).first()
extsrc_id = extsrc.id if extsrc else None


def init_param():
    """
        initialize record counts and table dictionaries for places/locations and (md5publ)redirects
    """
    param = {}
    param['cnt_done'] = param['cnt_new'] = 0
    param['redirects'] = load_redirects()  # dict: md5publ -> md5publ(main) if book was joined with other (was/will be implemented later)
    param['places'] = load_places()        # dict: place -> (place_id)
    return param


def init_import(param, cnt_total=None, db=None):
    """
        initialize the import in database
    """
    if db is None:
        db = current.db

    library_id = param['_library_id']
    if cnt_total is None:
        st_imp_rik = db(db.library.id == library_id).select().first().st_imp_rik
        cnt_total = int(0.5 * 10 ** st_imp_rik)
    param['cnt_total'] = cnt_total
    db.library[library_id] = dict(imp_total=cnt_total, imp_done=0, imp_new=0, imp_proc=0.0)
    db.commit()


def set_proc(library_id, proc, db=None):
    if db is None:
        db = current.db

    db.library[library_id] = dict(imp_proc=proc)
    db.commit()


def counter_and_commit_if_100(param, added):
    """
        increment the counter and commit at the chunk (of length 100 rows) end
        added - (1st tuple item of the) result from update_or_insert_answer()
    """
    param['cnt_new'] += added
    param['cnt_done'] += 1
    if not param['cnt_done'] % 100:
        do_commit(param['_library_id'], param)


def finished(param, db=None, session=None):
    """
        commit yet uncommitted books and set imp_proc=100.0
    """
    if db is None:
        db = current.db
    if session is None:
        session = current.session

    if session.import_run_id:
        db.import_run[session.import_run_id] = dict(finished=datetime.datetime.utcnow(), cnt_total=param['cnt_done'], cnt_new=param['cnt_new'])
            # we do not prefer use cnt_total, because it can be just an estimate based on rik size inside; so cnt_done could be better
        del session.import_run_id
    do_commit(param['_library_id'], param, finished=True)


def cancel_import(library_id=None, db=None, auth=None, scheduler=None):
    """
        used by link in views/upload/running.html
    """
    if db is None:
        db = current.db
    if auth is None:
        auth = current.auth
    if scheduler is None:
        scheduler = current.scheduler

    if library_id is None:
        library_id = auth.library_id

    running = db((db.import_run.finished == None) & (db.import_run.library_id == library_id)).select(
            orderby=~db.import_run.started)
    for imp in running:
        imp.update_record(failed=True, finished=datetime.datetime.utcnow())
        if imp.scheduler_task_id:
            scheduler.stop_task(imp.scheduler_task_id)
        # we do not prefer use cnt_total, because it can be just an estimate based on rik size inside; so cnt_done could be better
    do_commit(auth.library_id, None, finished=True)


def do_commit(library_id, param, finished=False, db=None):
    if db is None:
        db = current.db

    if param:   # proc before 2.0% can be used before main processing, example: db.library[auth.library_id] = dict(imp_proc=0.3)
        upd = dict(imp_done=param['cnt_done'], imp_new=param['cnt_new'], imp_proc=100.0 if finished else max(2.0, min(99.9, 100.0 * param['cnt_done'] / param['cnt_total'])))
        if finished:
            upd['last_import'] = datetime.datetime.utcnow()
    else:  # ie. if cancel!
        upd = dict(imp_proc=100.0)
    db.library[library_id] = upd
    db.commit()


def clear_before_import(incremental=False, db=None, auth=None, session=None):
    if db is None:
        db = current.db
    if auth is None:
        auth = current.auth
    if session is None:
        session = current.session

    if 'imp_done' in session:
        del session['imp_done']
    db.library[auth.library_id] = dict(imp_done=0, imp_new=0, imp_proc=0.0, imp_total=0)
    import_run_id = db.import_run.insert(library_id=auth.library_id, incremental=incremental, started=datetime.datetime.utcnow())
    db.commit()
    return import_run_id


def update_or_insert_answer(ean, md5publ, fastinfo, marc=None, md5marc=None, marcrec=None, z39stamp=None, md5redirects=None, src_quality=10,
                            delayed_indexing=True, db=None):
    """
    Args:
        marcrec is recommended ! It should be marcrec object from Marc parsing or suplementary object with attrs country (char 3), pubyears ((integer, integer), pls provide both same in case of single year)
    Returns tuple: (bool, answer_id) ; bool is True if the row wasn't yet in answer table and so it was inserted
    """
    if db is None:
        db = current.db

    class EmptyClass(object):
        pass

    def exists_update():
        if row:                           # same ean or same significant data -> same book
            if not marc or row.md5marc != md5marc:    # yes, same book, but changed info
                if not row.fastinfo or src_quality >= row.src_quality:
                    answer['fastinfo'] = fastinfo  # update fastinfo only if empty or we have better quality (>) or we have have same quality newer (=) source
                if ean and row.rik and row.rik != answer['rik']:  # suplemental rik was used earlier, but now we know the real ean
                    db.rik2.insert(rik2=row.rik)                  # we cannot give the suplemental one away because some library can use it (have it written in the book)
                db.answer[row.id] = answer
                #touched.append((row.id, marcrec, record, row.fastinfo or ''))  # or '': to distinguish update (not None) from insert (None)
                if not delayed_indexing:
                    idx_row(db.answer[row.id])
            return True  # row exists, stop next actions
            # TODO: indexovat podle answer + cycle přes všechny kopie v owned_book?

    if marc:
        md5marc = hashlib.md5(marc).hexdigest()
        z39stamp = z39stamp or datetime.datetime.utcnow()
    else:
        md5marc = z39stamp = None
    answer = dict(extsrc_id=extsrc_id, md5publ=md5publ, md5marc=md5marc, z39stamp=z39stamp, marc=marc,
                  ean=ean, rik=ean_to_fbi(ean) or suplemental_fbi(),
                  country=marcrec and marcrec.country[:PublLengths.country],
                  year_from=marcrec and marcrec.pubyears[0], year_to=marcrec and marcrec.pubyears[1],
                  src_quality=src_quality, needindex=delayed_indexing)

    flds = (db.answer.id, db.answer.md5marc, db.answer.fastinfo, db.answer.rik, db.answer.src_quality)
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
        row_id = db.answer.insert(**answer)  # ...insert it
        #touched.append((row_id, marcrec, record, None))
        if not delayed_indexing:
            # problem: answer is dict, we cannot pass it (alternative: convert to Storage)
            answer_for_idx = EmptyClass()
            answer_for_idx.id = row_id
            answer_for_idx.fastinfo = fastinfo
            idx_row(answer_for_idx)
        return True, row_id    # True means new added rec ( + 1 into inserted count and so on .. )


def update_or_insert_owned_book(answer_id, fastinfo, cnt, db=None, auth=None):
    if db is None:
        db = current.db
    if auth is None:
        auth = current.auth

    owned_book = {'library_id': auth.library_id, 'answer_id': answer_id, 'fastinfo': fastinfo, 'cnt': cnt, 'found_at_last': True}
    row = db(db.owned_book.answer_id == answer_id).select().first()
    if row:
        db.owned_book[row.id] = owned_book
        return row.id
    else:
        return db.owned_book.insert(**owned_book)


def update_or_insert_impressions(answer_id, owned_book_id, impression_gen, db=None, auth=None):
    """
    Args:
        impression_gen: see import_codex.py for the example of impression generator
    """
    if db is None:
        db = current.db
    if auth is None:
        auth = current.auth

    old_impressions = db(db.impression.owned_book_id == owned_book_id).select()
    len_old = len(old_impressions)
    for pos, impression in enumerate(impression_gen):
        impression['library_id'] = auth.library_id
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

'''
def set_imp_proc(library_id, proc=2.0, db=None):
    if db is None:
        db = current.db

    library = db.library[library_id]
    if proc > library.imp_proc:
        db.library[library_id] = {'imp_proc': min(proc, 100.0)}
        db.commit()


def set_imp_finished(library_id, db=None):
    set_imp_proc(library_id, proc=100.0, db=db)
'''
