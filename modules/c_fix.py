# -*- coding: utf-8 -*-

from pymarc import MARCReader

from marc_dialects import MarcFrom_AlephCz
from c_marc import marcrec_to_fastinfo_and_hash
from dal_import import extsrc_id

from gluon import current


def all_fix(db=None):
    if db is None:
        db = current.db

    def do_commit():
        db.commit()
        print('done: %s, missing fastinfo: %s, fixed md5publ: %s' % (pos, cnt_fastinfo, cnt_md5publ))

    cnt_fastinfo = cnt_md5publ = 0
    rows = db().iterselect(db.answer.id, db.answer.marc, db.answer.fastinfo, db.answer.md5publ, db.answer.extsrc_id, db.answer.src_quality)
    extsrc_qualities = {extsrc.id: extsrc.src_quality for extsrc in db().select(db.extsrc.id, db.extsrc.src_quality)}
    for pos, row in enumerate(rows):
        fix_fastinfo_from_marc(row, extsrc_qualities)

        if not pos % 1000:
            do_commit()
    do_commit()


def fix_fastinfo_from_marc(row, extsrc_qualities):
    if not row.marc:
        return
    if not row.extsrc_id:
        row.update_record(extsrc_id=extsrc_id)
    if extsrc_qualities[row.extsrc_id] < row.src_quality:
        return

    for record in MARCReader(row.marc, to_unicode=True):
        assert record.as_marc() == row.marc
        marcrec = MarcFrom_AlephCz(record)
        fastinfo, md5publ = marcrec_to_fastinfo_and_hash(marcrec)
        print fastinfo
        import pdb;pdb.set_trace()
