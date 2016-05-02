# -*- coding: utf-8 -*-


from gluon import current

from c2_db import PublLengths

# export for modules
current.auth = auth
current.db = db


class UNIQUE_QUESTION(object):
    def __init__(self, error_message=T('dotaz už je ve frontě')):
        self.error_message = error_message
    def __call__(self, value):
        if db((db.question.question == value) & (db.question.auth_user_id == auth.user_id) & (db.question.live == True)
              ).select(db.question.id, limitby=(0, 1)):
            return (value, self.error_message)
        else:
            return (value, None)

db.define_table('question',
        Field('auth_user_id', db.auth_user, default=auth.user_id,
              readable=False, writable=False,
              label=T("Uživatel"), comment=T("zadavatel dotazu")),
        Field('question', 'string', length=PublLengths.question,
              requires=[IS_LENGTH(minsize=PublLengths.question_min, maxsize=PublLengths.question,
                            error_message=T("zadej %s až %s znaků") % (PublLengths.question_min, PublLengths.question)),
                        UNIQUE_QUESTION()],
              label=T("Dotaz"), comment=T("zadej počáteční 2-3 slova názvu, nebo sejmi prodejní čarový kód EAN")),
        Field('answered', 'datetime',
              readable=False, writable=False,
              label=T("Dokončeno"), comment=T("čas dokončení zpracování po odpovědi")),
        Field('known', 'integer',
              readable=False, writable=False,
              label=T("Již známo"), comment=T("počet lokálně známých publikací")),
        Field('we_have', 'integer',
              readable=False, writable=False,
              label=T("Vlastněno"), comment=T("počet vyhovujících publikací v knihovně uživatele")),
        Field('retrieved', 'integer',
              readable=False, writable=False,
              label=T("Celkem získáno"), comment=T("počet nalezených publikací")),
        Field('inserted', 'integer',
              readable=False, writable=False,
              label=T("Nově získáno"), comment=T("nových (dosud nestažených)")),
        Field('live', 'boolean', default=True,
              readable=False, writable=False,
              label=T("Nezpracováno"), comment=T("čeká se na odpověď nebo její použití (katalogizaci)")),
        )

db.define_table('answer',
        Field('marc_id', 'integer',  # type integer and default=1(Aleph/cz) as long we do not support more marc dialects
              default=1, label=T("MARC dialekt"), comment=T("dialekt MARC jazyka")),
        Field('md5publ', 'string', length=32,
              label=T("md5publ"), comment=T("md5publ")),
        Field('md5marc', 'string', length=32,
              label=T("md5marc"), comment=T("md5marc")),
        Field('ean', 'string', length=20,
              label=T("Čarový kód EAN"), comment=T("čarový kód, vytištěný na publikaci")),
        Field('country', 'string', length=PublLengths.country,
              label=T("Země vydání"), comment=T("země vydání")),
        Field('year_from', 'integer',
              label=T("vydání od"), comment=T("vydání od roku")),
        Field('year_to', 'integer',
              label=T("vydání do"), comment=T("vydání do roku")),
        Field('marc', 'text',
              label=T("marc"), comment=T("marc")),
        )

db.define_table('idx_long',
        Field('category', 'string', length=1,
              label=T("Kategorie"), comment=T("kategorie (typ) vyhledávacího údaje")),
        Field('item', 'string', length=PublLengths.ilong,
              label=T("Vyhledávací údaj"), comment=T("údaj publikace (dlouhý)")),
        )

db.define_table('idx_join',
        Field('answer_id', db.answer,
              label=T("Odpověď"), comment=T("příslušnost k odpovědi")),
        Field('idx_long_id', db.idx_long,
              label=T("Vyhledávací řetězec"), comment=T("příslušnost k vyhledávacímu řetězci")),
        Field('role', 'string', length=PublLengths.irole,
              label=T("Role"), comment=T("role, pořadí v sérii, apod.")),
        )

db.define_table('idx_short',
        Field('answer_id', db.answer,
              label=T("Publikace"), comment=T("příslušnost k publikaci")),
        Field('category', 'string', length=1,
              label=T("Kategorie"), comment=T("kategorie (typ) vyhledávacího údaje")),
        Field('item', 'string', length=PublLengths.ishort,
              label=T("Vyhledávací údaj"), comment=T("údaj publikace (krátký)")),
        )

db.define_table('idx_word',
        Field('answer_id', db.answer,
              label=T("Publikace"), comment=T("příslušnost k publikaci")),
        Field('word', 'string', length=PublLengths.iword,
              label=T("Vyhledávací údaj"), comment=T("údaj publikace (krátký)")),
        )
