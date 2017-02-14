# -*- coding: utf-8 -*-

import datetime
import hashlib

from pymarc import MARCReader    # pymarc from PyPI, see setup.py about problems

from books import isxn_to_ean
from c_db import PublLengths
from c_utils import publ_hash, make_fastinfo
from dal_import import update_or_insert_answer, load_redirects
from marc_dialects import MarcFrom_AlephCz


def parse_Marc_and_updatedb(results, z39stamp=None):
    '''
    touched = []
    '''
    inserted = 0
    md5redirects = load_redirects()  # dict: md5publ -> md5publ(main) if book was joined with other (was/will be implemented later)
    for r in results:
        for record in MARCReader(r.data, to_unicode=True):  # will return 1 record
            inserted += updatedb(record, z39stamp=z39stamp, md5redirects=md5redirects)
    duration_marc = datetime.datetime.utcnow()

    '''
    for answer_id, marcrec, record, fastinfo in touched:
        if fastinfo is not None:
            del_idxs(answer_id)  # delete related indexes before re-creating them
        create_idxs(answer_id, marcrec, record, fastinfo)
    '''

    return len(results), inserted, duration_marc


def updatedb(record, z39stamp=None, md5redirects=None):
    marc = record.as_marc()
    md5marc = hashlib.md5(marc).hexdigest()   # pryč

    marcrec = MarcFrom_AlephCz(record)
    fastinfo, md5publ = marcrec_to_fastinfo_and_hash(marcrec)

    isbn = marcrec.isbn[:PublLengths.isbn]
    ean = isxn_to_ean(isbn)

    added, _answer_id = update_or_insert_answer(ean, md5publ, fastinfo, marc=marc, md5marc=md5marc, marcrec=marcrec, z39stamp=z39stamp, md5redirects=md5redirects,
                                                src_quality=marcrec.src_quality, delayed_indexing=False)
                                                # disable delayed_indexing because user need see results
    return added

    '''
    def exists_update():
        if row:                           # same ean or same significant data -> same book
            if row.md5marc != md5marc:    # yes, same book, but changed info
                db.answer[row.id] = answer
                touched.append((row.id, marcrec, record, row.fastinfo or ''))  # or '': to be sure to distinguish from insert
            return True  # row exists, stop next actions
    #-------------------
    answer = dict(md5publ=md5publ, md5marc=md5marc, z39stamp=z39stamp or datetime.datetime.utcnow(), ean=ean, marc=marc,
                  country=marcrec.country[:PublLengths.country],
                  year_from=marcrec.pubyears[0], year_to=marcrec.pubyears[1])

    flds = (db.answer.id, db.answer.md5marc, db.answer.fastinfo)
    if ean:
        row = answer_by_ean(db, ean, flds)
        if exists_update():   # row exists...
            return False      # ...do not continue to find (using significant data) and do not insert
    # not found by isbn/ean
    row = answer_by_hash(db, md5publ, flds)
    if exists_update():
        return False
    else:                                    # row doesn't exist...
        answer['rik'] = ean_to_fbi(ean)
        row_id = db.answer.insert(**answer)  # ...insert it
        touched.append((row_id, marcrec, record, None))
        return True  # True -> + 1 into inserted count
    '''


def marcrec_to_fastinfo_and_hash(marcrec):
    fastinfo = make_fastinfo(marcrec)
    md5publ = publ_hash(marcrec.title, marcrec.subtitles, marcrec.authors, marcrec.publisher, marcrec.pubyear, author_need_normalize=True)
    return fastinfo, md5publ



'''
author, _full = normalize_authors(author, string_surnamed=True)

def make_fastinfo(title, author, pubplace=None, publisher=None, pubyear=None, subtitle=None, keys=None):


    fastinfo, md5publ = publ_fastinfo_and_hash(nazev, auth_surnamed, auth_full, pubplace, publisher, pubyear, subtitle=podnazev,
                                               keys=klsl)

def publ_fastinfo_and_hash(title, surnamed_author, author, pubplace, publisher, pubyear, subtitle=None, keys=None):
    return (make_fastinfo(title, author, pubplace=pubplace, publisher=publisher, pubyear=pubyear, subtitle=subtitle, keys=keys),
            publ_hash(title, surnamed_author, publisher, pubyear, subtitle=subtitle))
'''