# -*- coding: utf-8 -*-

import hashlib

from pymarc import MARCReader    # pymarc z PyPI

from books import isxn_to_ean
from c2020 import smartquery, world_get
from marcfrom import MarcFrom_AlephCz


@auth.requires_login()
def get_status():
    """called from find() action and via setInterval/ajax
    maybe this can be redesigned as a component, using LOAD() and web2py_component(url,id) function
    """
    find_status = ''
    questions = db((db.question.live == True) & (db.question.auth_user_id == auth.user_id)).select(
            db.question.id, db.question.question, db.question.answered,
            db.question.known, db.question.we_have, orderby=db.question.id)
    if questions:
        some_ready = False
        status_rows = []
        for q in questions:
            cls = 'list-group-item '
            if q.answered:
                cls += 'list-group-item-success active'
                some_ready = True
            else:
                cls += 'disabled'
            status_rows.append(A(SPAN(q.we_have or 0, _class="badge"), SPAN(q.known or 0, _class="badge"), q.question, _href='#', _class=cls))
        if some_ready:
            hint = T("Vyber vyhledanou knihu ke katalogizaci nebo zadej další")
        else:
            hint = T("Počkej na vyhledání předchozího zadání nebo zadej další knihu ke zpracování")
        find_status = SPAN(hint, _class="help-block") + DIV(*status_rows, _class="list-group", _style="max-width: 500px;")
    return find_status

@auth.requires_login()
def find():
    form = SQLFORM(db.question)
    if form.process().accepted:
        warning, results = world_get(form.vars.question)
        if warning:
            response.flash = warning
        else:
            inserted = 0
            for r in results:
                for record in MARCReader(r.data, to_unicode=True):  # will return 1 record
                    inserted += updatedb(record)
            retrieved = len(results)
            db.question[form.vars.id] = {'answered': datetime.datetime.now(), 'retrieved': retrieved, 'inserted': inserted}
            response.flash = T('%s staženo, z toho nových: %s') % (retrieved, inserted)
    return dict(form=form, find_status=get_status())

def xfind():
    #link('js/codex2020/katalogizace/publikace')
    rc, user_key = redis_user(auth)
    form = SQLFORM.factory(
            Field('starter', 'string', length=20, label=T("Zkus najít podle"),
                comment=T("počáteční 2-3 slova názvu nebo sejmi EAN čarový kód pro vyhledání publikace")))
    if form.process().accepted:
        fnd = form.vars.starter  # .strip() ?
        if fnd and len(fnd) >= 3:
            qkey = user_key + 'Q'
            rc.rpush(qkey, fnd)
        else:
            response.flash = T("Zadej alespoň 3 znaky pro vyhledání.")
    questions = []
    for q in rc.lrange(user_key + 'Q', 0, -1):
        is_in_hash = True if 'neco' in q else False
        questions.append((q, is_in_hash))
    return dict(form=form, questions=questions)
    # LSET nesmysl + LREM pro odstranění zprostřed

def xxx():
    if False:
        if False:
            warning, results = world_get(fnd)
            if warning:
                response.flash = warning
            else:
                inserted = 0
                for r in results:
                    for record in MARCReader(r.data, to_unicode=True):  # will return 1 record
                        inserted += updatedb(record)
                response.flash = T('%s staženo, z toho nových: %s') % (len(results), inserted)
        else:
            response.flash = T("Zadej alespoň 3 znaky pro vyhledání.")
    return dict(form=form)

# internal
def updatedb(record):
    def exists_update():
        if row:
            if row.md5marc != md5marc:    # same ean, changed info
                db.answer[row.id] = answer
                # TODO: delete related answer_join
                # TODO: update answer_join, answer_idx
            return True  # row exists, stop next actions

    marc = record.as_marc()
    md5marc = hashlib.md5(marc).hexdigest()

    marcrec = MarcFrom_AlephCz(record)
    md5publ = hashlib.md5(('%s|%s|%s|%s' % (marcrec.title, marcrec.joined_authors(), marcrec.publisher, marcrec.pubyear)).encode('utf-8')).hexdigest()

    isbn = marcrec.isbn[:PublLengths.isbn]
    ean = isxn_to_ean(isbn)

    answer = dict(md5publ=md5publ, md5marc=md5marc, ean=ean, marc=marc,
                  country=marcrec.country[:PublLengths.country],
                  year_from=marcrec.pubyears[0], year_to=marcrec.pubyears[1])

    #---------
    new = dict(ean=ean, title=marcrec.title[:PublLengths.title], isbn=isbn[:PublLengths.isbn],
            uniformtitle=(record.uniformtitle() or '')[:PublLengths.uniformtitle],
            series=marcrec.series[:PublLengths.series],
            subjects='; '.join(marcrec.subjects)[:PublLengths.subjects],
            categories='; '.join(map(lambda r:r[0] + (' ('+r[1]+')' if r[1] else ''), marcrec.categories))[:PublLengths.categories],
            addedentries='; '.join(fld.value() for fld in (record.addedentries() or []))[:PublLengths.addedentries],
            publ_location='; '.join(fld.value() for fld in (record.location() or []))[:PublLengths.publ_location],
            notes='; '.join(fld.value() for fld in (record.notes() or []))[:PublLengths.notes],
            physicaldescription='; '.join(fld.value() for fld in (record.physicaldescription() or []))[:PublLengths.physicaldescription],
            publisher=marcrec.publisher[:PublLengths.publisher],
            pubyear=marcrec.pubyear[:PublLengths.pubyear],
            author=marcrec.author[:PublLengths.author],
            )
    db.publication.insert(**new)
    #---------

    if ean:
        if ean[:3] == '977':  # can have everything in [10:12] position
            row = db(db.answer.ean.startswith(ean[:10])).select(db.answer.id, db.answer.md5marc).first()
        else:
            row = db(db.answer.ean == ean).select(db.answer.id, db.answer.md5marc).first()
        if exists_update():
            return False
    # no isbn/ean
    row = db(db.answer.md5publ == md5publ).select(db.answer.id, db.answer.md5marc).first()
    if exists_update():
        return False
    else:
        db.answer.insert(**answer)
        # TODO: update answer_join, answer_idx
        return True
