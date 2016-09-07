# -*- coding: utf-8 -*-

from pymarc import MARCReader    # pymarc from PyPI

from gluon import current
current.db = db  # export for modules

from dal_idx import create_idxs, truncate_idxs
from marc_dialects import MarcFrom_AlephCz


# at this time only marc_id==1 is supported (Aleph/cz records)
def idx_answers():
    """scan through rows and delete and recreate helping info for each; this could run together with web"""
    cnt = 0
    answer_id = -1
    while True:
        rows = db((db.answer.id > answer_id) & (db.answer.marc_id == 1)).select(
                db.answer.id, db.answer.marc, orderby=db.answer.id, limitby=(0, 500))
        if not rows:
            break
        for row in rows:
            index_row(row, updating=True)
            answer_id = row.id
            cnt += 1
        db.commit()
        print cnt

def idx_answers_static():
    """this solution will delete all and then it will create all; this is not suitable for continuously working web"""
    truncate_idxs()

    cnt = 0
    answer_id = -1
    while True:
        rows = db((db.answer.id > answer_id) & (db.answer.marc_id == 1)).select(
                db.answer.id, db.answer.marc, orderby=db.answer.id, limitby=(0, 500))
        if not rows:
            break
        for row in rows:
            index_row(row, updating=False)
            answer_id = row.id
            cnt += 1
        db.commit()
        print cnt

class C2_parsed(object):           # used when we have no marc_obj (locally defined books)
    def __init__(self, fastinfo)   # fastinfo is source here (in indexing the same or similar will be re-generated)
        self.fastinfo = fastinfo
        self.parsed_fastinfo = {}
        for ln in fastinfo.splitlines():
            if len(ln) > 1:
                self.parsed_fastinfo[ln[0]] = ln[1:]

def index_row(row, updating=False)
    if row.marc:
        marc_obj = MARCReader(row.marc, to_unicode=True).next()
        c2_parsed = MarcFrom_AlephCz(marc_obj)   # if marc is source, .fastinfo & .parsed_fastinfo are missing
    else:
        marc_obj = None
        # we use 'marc_obj is None' and non empty row.fastinfo to avoid fastinfo rewrite
        c2_parsed = C2_parsed(row.fastinfo):
        c2_parsed.title = c2_parsed.parsed_fastinfo.get('T')
        c2_parsed.subtitle = c2_parsed.parsed_fastinfo.get('t')
        c2_parsed.author = c2_parsed.parsed_fastinfo.get('A')
        c2_parsed.pubplace = c2_parsed.parsed_fastinfo.get('L')
        c2_parsed.publisher = c2_parsed.parsed_fastinfo.get('P')
        c2_parsed.pubyear = c2_parsed.parsed_fastinfo.get('Y')
    # TODO: add user descriptions here
    # TODO: what if marc is empty and we have user descriptions only?
    create_idxs(row.id, c2_parsed, marc_obj, row.fastinfo, updating=updating)


if __name__ == '__main__':
    idx_answers()
