# -*- coding: utf-8 -*-

import hashlib

from pymarc import MARCReader    # pymarc z PyPI

from books import isxn_to_ean
from c2020 import smartquery, world_get
from marcfrom import MarcFrom


def find():
    #link('js/codex2020/katalogizace/publikace')
    form = SQLFORM.factory(
            Field('starter', 'string', length=20, label=T("Zkus najít podle"),
                comment=T("počáteční 2-3 slova názvu nebo sejmi EAN čarový kód pro vyhledání publikace")))
    if form.process().accepted:
        fnd = form.vars.starter
        if fnd and len(fnd) >= 3:
            warning, results = world_get(fnd)
            if warning:
                response.flash = warning
            else:
                inserted = 0
                for r in results:
                    for record in MARCReader(r.data, to_unicode=True):  # will return 1 record
                        inserted += updatedb(record)
                response.flash = T('%s staženo, z toho nových: %s' % (len(results), inserted))
        else:
            response.flash = T("Zadej alespoň 3 znaky pro vyhledání.")
    return dict(form=form)

# internal
def updatedb(record):
    def exists_update():
        if row:
            if row.md5marc != md5marc:    # same ean, changed info
                db.answer[row.id] = answer
            return True  # row exists, stop next actions

    marc = record.as_marc()
    md5marc = hashlib.md5(marc).hexdigest()

    marcrec = MarcFrom(record)
    md5publ = hashlib.md5(('%s|%s|%s|%s' % (marcrec.title, marcrec.joined_authors(), marcrec.publisher, marcrec.pubyear)).encode('utf-8')).hexdigest()

    #title = marcrec.title[:PublLengths.title]
    #author = marcrec.author[:PublLengths.author]
    #publisher = marcrec.publisher[:PublLengths.publisher]
    #pubyear = marcrec.pubyear[:PublLengths.pubyear]

    isbn = marcrec.isbn[:PublLengths.isbn]
    ean = isxn_to_ean(isbn)

    answer = dict(md5publ=md5publ, md5marc=md5marc, ean=ean, marc=marc)

    if ean:
        # TODO: 977
        row = db(db.answer.ean == ean).select(db.answer.id, db.answer.md5marc).first()
        if exists_update():
            return False
    # no isbn/ean
    row = db(db.answer.md5publ == md5publ).select(db.answer.id, db.answer.md5marc).first()
    if exists_update():
        return False
    else:
        db.answer.insert(**answer)
        return True

    '''
    if ean:
        if ean[:3] == '977':  # can have everything in [10:12] position
            row = db(db.answer.ean.startswith(ean[:10])).select(
                    db.answer.id, limitby=(0,1), orderby_on_limitby=False).first()
        else:
            row = db(db.answer.ean == ean).select(
                    db.answer.id, limitby=(0,1), orderby_on_limitby=False).first()
    if not row:
        row = db(db.answer.md5 == md5).select(
                db.answer.id, limitby=(0,1), orderby_on_limitby=False).first()

    try:
        new = dict(md5=md5, ean=ean, title=title, isbn=isbn,
                uniformtitle=(record.uniformtitle() or '')[:PublLengths.uniformtitle],
                #subjects=(record.subjects() or '')[:PublLengths.subjects],
                addedentries=(record.addedentries() or '')[:PublLengths.addedentries],
                publ_location=(record.location() or '')[:PublLengths.publ_location],
                #notes=(record.notes() or '')[:PublLengths.notes],
                #physicaldescription=(record.physicaldescription() or '')[:PublLengths.physicaldescription],
                publisher=(record.publisher() or '')[:PublLengths.publisher],
                pubyear=(record.pubyear() or '')[:PublLengths.pubyear],
                author=author, marc=marc
                )
        db.publication.insert(**new)
    except:
        pass

    if row:
        db[row.id] = new
    else:
    '''
